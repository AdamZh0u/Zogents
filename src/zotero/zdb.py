import shutil
from dataclasses import dataclass
from pathlib import Path
from sqlite3 import Connection, connect
from typing import Dict, List

from src.config import CONFIG


def create_conn(fetch: bool = True) -> Connection:
    """
        try create sqlite connection
    :return:
    """
    data_dir = Path(CONFIG["zotero"]["data_dir"])
    src = data_dir / "zotero.sqlite"
    dest = data_dir / "zotero.wrap.sqlite.bak"
    if fetch:
        shutil.copy(src, dest)

    assert dest.exists()
    return connect(str(dest))


def exec_fetchall(sql):
    with create_conn() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        values = cursor.fetchall()
    return values


@dataclass()
class Attachment:
    itemID: int
    key: str
    contentType: str
    relpath: str

    @property
    def abspath(self):
        return Path(CONFIG["zotero"]["data_dir"], self.relpath)

    @property
    def is_attachment_url(self):
        if self.relpath is not None:
            return "attachments:" in self.relpath
        return self.relpath is None


def get_attachments(type: int = -1) -> List[Attachment]:
    """
    all attached files
    :param type:
    :return:
    """
    if type == -1:
        sql = """
            select itemID,key,contentType,path from (
                itemAttachments inner join items using (itemID)
            )
        """
    else:
        raise NotImplementedError()

    values = exec_fetchall(sql)

    res = []
    for itemID, key, contentType, path in values:
        if path is not None:
            relpath = str(Path("storage") / key / path.replace("storage:", ""))
        else:
            relpath = None
        file = Attachment(
            itemID=itemID, key=key, contentType=contentType, relpath=relpath
        )
        res.append(file)
    return res


def get_attachments_by_itemid(*itemID: int) -> List[Attachment]:
    """
    get attached file from itemid
    :param itemID:
    :return:
    """
    itemID_ = ",".join(f"{i}" for i in itemID)
    sql = f"""
    select itemID,contentType,path from itemAttachments
    where itemID IN ({itemID_})
    """
    values = exec_fetchall(sql)
    if len(values) == 0:
        return []

    item_value_map_ = {}
    for value in values:
        item_value_map_[value[0]] = value

    res = []
    item_id_key_map = get_items_key_by_itemid(*list(item_value_map_.keys()))

    for item_id, val in item_value_map_.items():
        path = val[2]  # type:str
        key = item_id_key_map[item_id]
        relpath = str(Path("storage") / key / path.replace("storage:", ""))
        item = Attachment(itemID=item_id, key=key, contentType=val[1], relpath=relpath)
        res.append(item)
    return res


def get_items_key_by_itemid(*itemID: int) -> Dict[int, str]:
    itemID_ = ",".join(f"{i}" for i in itemID)
    sql = f"""
        select itemID,key from items where itemID in ({itemID_})
    """
    values = exec_fetchall(sql)
    items_type = {i[0]: i[1] for i in values}
    return items_type


if __name__ == "__main__":
    print(get_attachments_by_itemid(2045, 2046))
