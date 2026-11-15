from dataclasses import dataclass, fields
from typing import Any, Dict, Optional, List

import requests

from src.handler.zotero_database import ZoteroConn
from src.config import CONFIG, get_logger

logger = get_logger()


@dataclass
class NocoDBConfig:
    base_url: str = CONFIG["NOCODB"]["base_url"]
    api_key: str = CONFIG["NOCODB"]["api_key"]
    table_id: str = CONFIG["NOCODB"]["table_id"]


@dataclass
class RecordData:
    itemID: int
    key: str
    tags: List[str]
    itemTypeID: int
    title: Optional[str] = None
    year: Optional[int] = None
    journal: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        allowed = {f.name for f in fields(cls)}  # 白名单
        data = {k: d.get(k) for k in allowed}
        return cls(**data)

    def to_dict(self):
        return {
            "itemID": self.itemID,
            "key": self.key,
            "tags": ", ".join(self.tags),  # 转换为字符串存储 到nocoDB
            "itemTypeID": self.itemTypeID,
            "title": self.title,
            "year": self.year,
            "journal": self.journal,
            "notes": self.notes,
        }


class NocoDB:
    def __init__(self, db_config: NocoDBConfig = NocoDBConfig()):
        self.db_config = db_config
        self.headers = {
            "xc-token": self.db_config.api_key,
        }

    def list_table_records(self):
        # 表格记录列表
        url = (
            f"{self.db_config.base_url}/api/v2/tables/{self.db_config.table_id}/records"
        )
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json())

    def create_table_records(self, data: RecordData):
        # 创建表格记录
        url = (
            f"{self.db_config.base_url}/api/v2/tables/{self.db_config.table_id}/records"
        )
        response = requests.post(url, headers=self.headers, json=[data.to_dict()])
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json())


class Pipeline:
    def __init__(self):
        self.noco = NocoDB()

    def run(self):
        res = self.noco.list_table_records()
        print(res)


def main():
    noco = NocoDB()
    res = noco.list_table_records()
    conn = ZoteroConn(CONFIG["zotero"]["data_dir"])
    tag_pattern = "#%/%"
    parent_items = conn.get_parent_items_with_special_tag(tag_pattern)

    for parent_item in parent_items:
        item = RecordData.from_dict(parent_item.to_dict())
        res = noco.create_table_records(item)
        print(res)


if __name__ == "__main__":
    main()
