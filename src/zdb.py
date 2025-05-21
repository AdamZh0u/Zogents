import shutil
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Connection, connect
from typing import List, Tuple

from src.config import CONFIG, get_logger

logger = get_logger()


class ZoteroDB:
    """
    Zotero database handler. Copies the database once on initialization and provides query methods.
    """

    def __init__(self):
        self.data_dir = Path(CONFIG["zotero"]["data_dir"])
        self.src = self.data_dir / "zotero.sqlite"
        self.dest = self.data_dir / "zotero.wrap.sqlite.bak"
        self.copy_db()

    def copy_db(self):
        """
        Copy the Zotero database to a backup file for safe read access.
        """
        shutil.copy(self.src, self.dest)
        assert self.dest.exists()

    def create_conn(self) -> Connection:
        """
        Create a connection to the backup Zotero database.
        """
        assert self.dest.exists()
        return connect(str(self.dest))

    def exec_fetchall(self, sql: str) -> List[Tuple]:
        """
        Execute a SQL query and return all results. Returns an empty list on error.
        """
        try:
            with self.create_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                values = cursor.fetchall()
                return values
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return []


@dataclass(frozen=True)
class ParentItem:
    itemID: int
    key: str
    tags: List[str]
    title: str


@dataclass(frozen=True)
class Attachment:
    itemID: int
    itemKey: str
    parentItemID: int
    parentItemKey: str
    parentItemTags: List[str]
    contentType: str
    relpath: str

    @property
    def abspath(self) -> Path:
        """
        Get the absolute path to the attachment file.
        """
        return Path(CONFIG["zotero"]["data_dir"], self.relpath)

    @property
    def is_attachment_url(self) -> bool:
        """
        Check if the attachment is a URL-based attachment.
        """
        if self.relpath is not None:
            return "attachments:" in self.relpath
        return self.relpath is None


def get_parent_items_with_special_tag(
    db: ZoteroDB, tag_pattern: str = "#%/%"
) -> List[ParentItem]:
    """
    Get all parent items with tags matching the given pattern (e.g., #x/xxx).
    Returns a list of ParentItem objects, each with all matching tags.
    """
    sql = f"""
    SELECT items.itemID, tags.name, items.key
    FROM items
    JOIN itemTags ON items.itemID = itemTags.itemID
    JOIN tags ON itemTags.tagID = tags.tagID
    WHERE tags.name LIKE '{tag_pattern}%'
    """
    values = db.exec_fetchall(sql)
    # Merge all tags for each item
    item_map = {}
    for itemID, tag, itemKey in values:
        if itemID not in item_map:
            item_map[itemID] = {"key": itemKey, "tags": []}
        item_map[itemID]["tags"].append(tag)
    res = []
    for itemID, info in item_map.items():
        title = get_item_title_by_itemid(db, itemID)
        res.append(
            ParentItem(itemID=itemID, key=info["key"], tags=info["tags"], title=title)
        )
    return res


def get_item_title_by_itemid(db: ZoteroDB, itemID: int, fieldID: int = 1) -> str:
    """
    Get the title of an item by its itemID. Default fieldID=1 (title field).
    Returns the title as a string, or None if not found.
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
    values = db.exec_fetchall(sql)
    if len(values) == 0:
        return None
    return values[0][0]


def get_attachements_by_parent_item(
    db: ZoteroDB, parent_item: ParentItem
) -> List[Attachment]:
    """
    Get all attachments for a given parent item.
    Returns a list of Attachment objects.
    """
    parent_item_id = parent_item.itemID
    parent_item_key = parent_item.key
    parent_item_tags = parent_item.tags
    sql = f"""
    SELECT itemAttachments.itemID,items.key, itemAttachments.contentType,itemAttachments.path
    FROM itemAttachments
    JOIN items ON itemAttachments.itemID = items.itemID
    WHERE itemAttachments.parentItemID = {parent_item_id}
    """
    attachment_values = db.exec_fetchall(sql)
    res = []
    for itemID, key, contentType, path in attachment_values:
        if path is not None:
            relpath = str(Path("storage") / key / path.replace("storage:", ""))
        else:
            relpath = None
        res.append(
            Attachment(
                itemID=itemID,
                itemKey=key,
                parentItemID=parent_item_id,
                parentItemKey=parent_item_key,
                parentItemTags=parent_item_tags,
                contentType=contentType,
                relpath=relpath,
            )
        )
    return res


def main():
    """
    Example usage: Get all parent items with special tags and their attachments.
    """
    db = ZoteroDB()
    tag_pattern = "#%/%"
    parent_items = get_parent_items_with_special_tag(db, tag_pattern)
    attachments = []
    for parent_item in parent_items:
        res = get_attachements_by_parent_item(db, parent_item)
        attachments.extend(res)
    print([attachment.itemKey for attachment in attachments])


if __name__ == "__main__":
    main()
