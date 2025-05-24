import shutil
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from sqlite3 import Connection, connect
from typing import List, Tuple
from pprint import pprint
from src.config import CONFIG, get_logger

logger = get_logger()


@dataclass(frozen=True)
class ParentItem:
    itemID: int
    key: str
    tags: List[str]
    title: str
    itemTypeID: int

    @staticmethod
    def from_dict(d):
        return ParentItem(
            itemID=d["itemID"],
            key=d["key"],
            tags=d["tags"],
            title=d["title"],
            itemTypeID=d["itemTypeID"],
        )


@dataclass(frozen=True)
class Attachment:
    itemID: int
    itemKey: str
    contentType: str
    relpath: str
    title: str
    parentItem: ParentItem

    @staticmethod
    def from_dict(d):
        return Attachment(
            itemID=d["itemID"],
            itemKey=d["itemKey"],
            contentType=d["contentType"],
            relpath=d["relpath"],
            title=d["title"],
            parentItem=ParentItem.from_dict(d["parentItem"]),
        )

    def to_dict(self):
        return  {
                "itemKey": self.itemKey,
                "title": self.title,
                "parentItemKey": self.parentItem.key,
                "parentItemTitle": self.parentItem.title,
                "parentItemTags": (
                    ", ".join(self.parentItem.tags) if self.parentItem.tags else ""
                ),
                "parentItemType": str(self.parentItem.itemTypeID),
                "relpath": self.relpath,
            }

    @property
    def abspath(self) -> Path:
        """
        Get the absolute path to the attachment file.
        """
        if self.relpath is None:
            return Path("")
        return Path(CONFIG["zotero"]["data_dir"], self.relpath)

    @property
    def is_attachment_url(self) -> bool:
        """
        Check if the attachment is a URL-based attachment.
        """
        if self.relpath is not None:
            return "attachments:" in self.relpath
        return self.relpath is None


class ZoteroConn:
    """
    Zotero database handler. Copies the database once on initialization and provides query methods.
    """

    def __init__(self, zotero_dir: str = None):
        self.data_dir = Path(zotero_dir)
        self.src = self.data_dir / "zotero.sqlite"
        self.dest = self.data_dir / "zotero.wrap.sqlite.bak"
        self.copy_db()
        self.db = self.create_conn()

    def copy_db(self):
        """
        Copy the Zotero database to a backup file for safe read access.
        """
        shutil.copy(self.src, self.dest)
        assert self.dest.exists(), f"Backup Zotero database not found: {self.dest}"

    def create_conn(self) -> Connection:
        """
        Create a connection to the backup Zotero database.
        """
        assert self.dest.exists(), f"Backup Zotero database not found: {self.dest}"
        return connect(str(self.dest))

    def exec_fetchall(self, sql: str) -> List[Tuple]:
        """
        Execute a SQL query and return all results. Returns an empty list on error.
        """
        try:
            with self.db as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                values = cursor.fetchall()
                return values
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []

    def get_parent_items_with_special_tag(
        self, tag_pattern: str = "#%/%"
    ) -> List[ParentItem]:
        """
        Get all parent items with tags matching the given pattern (e.g., #x/xxx).
        Returns a list of ParentItem objects, each with all matching tags.
        由于item 和 tag 一对多的关系， 所以需要使用FULL OUTER JOIN 来获取所有数据
        选取item时过滤掉itemTypeID为1和2的item， annotation = 1, attachment = 2
        """
        sql = f"""
            SELECT items.itemID, tags.name, items.key, items.itemTypeID
            FROM items
            FULL OUTER JOIN itemTags ON items.itemID = itemTags.itemID
            FULL OUTER JOIN tags ON itemTags.tagID = tags.tagID
            WHERE tags.name LIKE '{tag_pattern}%' AND items.itemTypeID NOT IN (1,2)
        """
        values = self.exec_fetchall(sql)
        # Merge all tags for each item
        item_map = {}
        for itemID, tag, itemKey, itemTypeID in values:
            if itemID not in item_map:
                item_map[itemID] = {"key": itemKey, "tags": [], "type": itemTypeID}
            item_map[itemID]["tags"].append(tag)
        res = []
        for itemID, info in item_map.items():
            title = self.get_itemfield_by_itemid(itemID)
            res.append(
                ParentItem(
                    itemID=itemID,
                    key=info["key"],
                    tags=info["tags"],
                    title=title,
                    itemTypeID=info["type"],
                )
            )
        return res

    def get_itemfield_by_itemid(self, itemID: int, fieldID: int = 1) -> str:
        """
        Get the title of an item by its itemID. Default fieldID=1 (title field).
        Returns the title as a string, or None if not found.

        for more fieldID, see https://github.com/sailist/pyzotero-local/blob/master/pyzolocal/beans/enum.py
        """
        sql = f"""
        WITH item_fields AS (
            SELECT itemDataValues.value
            FROM itemData
            JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
            WHERE itemID = {itemID} AND fieldID = {fieldID}
        )
        SELECT value FROM item_fields
        """
        values = self.exec_fetchall(sql)
        if len(values) == 0:
            return None
        return values[0][0]

    def get_attachments_by_parent_item(
        self, parent_item: ParentItem
    ) -> List[Attachment]:
        """
        Get all attachments for a given parent item.
        Returns a list of Attachment objects.
        attachment 的itemTypeID 是3
        """
        sql = f"""
        SELECT itemAttachments.itemID, items.key, itemAttachments.contentType, itemAttachments.path
        FROM itemAttachments
        LEFT JOIN items ON itemAttachments.itemID = items.itemID
        WHERE itemAttachments.parentItemID = {parent_item.itemID}
        """
        attachment_values = self.exec_fetchall(sql)
        res = []
        for itemID, key, contentType, path in attachment_values:
            if path is not None:
                relpath = str(Path("storage") / key / path.replace("storage:", ""))
            else:
                relpath = None

            title = self.get_itemfield_by_itemid(itemID, 1)
            res.append(
                Attachment(
                    itemID=itemID,
                    itemKey=key,
                    contentType=contentType,
                    relpath=relpath,
                    title=title,
                    parentItem=parent_item,
                )
            )
        return res


def main():
    """
    Example usage: Get all parent items with special tags and their attachments.
    """
    conn = ZoteroConn(CONFIG["zotero"]["data_dir"])
    tag_pattern = "#%/%"
    parent_items = conn.get_parent_items_with_special_tag(tag_pattern)
    attachments = []
    for parent_item in parent_items:
        atts = conn.get_attachments_by_parent_item(parent_item)
        attachments.extend(atts)

    pprint(attachments)
    attachments_dict = [asdict(a) for a in attachments]
    with open("data/zdb_attachments.json", "w", encoding="utf-8") as f:
        json.dump(attachments_dict, f, indent=4, ensure_ascii=False)

    with open("data/zdb_attachments.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    attachments = [Attachment.from_dict(a) for a in data]
    pprint(attachments)


if __name__ == "__main__":
    main()
