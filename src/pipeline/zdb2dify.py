from dataclasses import dataclass, asdict, field
import json
import os

from src.config import CONFIG, get_logger
from src.handler.dify_knowledge_base import DifyKnowledgeBase
from src.handler.zotero_database import ZoteroConn, Attachment
from typing import Dict, Any

logger = get_logger()


@dataclass
class PipeConfig:
    kb_name: str = "Zotero"
    tag_pattern: str = "#%/%"
    zotero_db: str = CONFIG["zotero"]["data_dir"]
    archive_path: str = "data/zdb_attachments.json"
    metadata_fields: dict[str, str] = field(
        default_factory=lambda: {
            "itemKey": "string",
            "title": "string",
            "parentItemKey": "string",
            "parentItemTitle": "string",
            "parentItemTags": "string",
            "parentItemType": "string",
            "relpath": "string",
        }
    )


class Pipeline:
    # upload documents -- get document id -- update metadata
    def __init__(self, pipe_config: PipeConfig = None):
        # dataset
        self.config = pipe_config
        self.zotero_conn = ZoteroConn(zotero_dir=self.config.zotero_db)
        self.dify_kb = DifyKnowledgeBase(dataset_name=self.config.kb_name)
        self.dataset_id: str = self.dify_kb.dataset_id
        self._document_id_dict: Dict[str, Any] = self.dify_kb.documents
        self._metadata_id_dict: Dict[str, Any] = self.dify_kb.metadata

    @property
    def document_id_dict(self):
        self._document_id_dict = self.dify_kb.documents
        return self._document_id_dict

    @property
    def metadata_id_dict(self):
        self._metadata_id_dict = self.dify_kb.metadata
        return self._metadata_id_dict

    def get_current_attachments(self):
        parent_items = self.zotero_conn.get_parent_items_with_special_tag(
            self.config.tag_pattern
        )
        attachments = []
        for parent_item in parent_items:
            attachments.extend(
                self.zotero_conn.get_attachments_by_parent_item(parent_item)
            )
        logger.info(f"Found {len(attachments)} attachments in Zotero")
        return {a.itemKey: a for a in attachments}

    def get_archived_attachments(self):
        if not os.path.exists(self.config.archive_path):
            logger.warning(
                f"Archive file not found: {self.config.archive_path}, create a new one"
            )
            self.save_local_archive([])
            return {}
        with open(self.config.archive_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        attachments = [Attachment.from_dict(a) for a in data]
        logger.info(f"Found {len(attachments)} attachments in archive")
        return {a.itemKey: a for a in attachments}

    def save_local_archive(self, attachments):
        attachments_dict = [asdict(a) for a in attachments]
        with open(self.config.archive_path, "w", encoding="utf-8") as f:
            json.dump(attachments_dict, f, indent=4, ensure_ascii=False)

    def diff_attachments(self, current, archived):
        to_upload = [current[k] for k in current if k not in archived]
        to_update = [
            current[k]
            for k in current
            if k in archived
            and set(current[k].parentItem.tags) != set(archived[k].parentItem.tags)
        ]
        to_delete = [archived[k] for k in archived if k not in current]
        return to_upload, to_update, to_delete

    def upload_onefile(self, file_path: str, metadata_input: dict):
        doc_id = self.dify_kb.upload_document_by_file(self.dataset_id, file_path)
        logger.info(f"Uploaded {file_path} to Dify with doc_id: {doc_id}")

        # 更新metadata
        metadata_vlist = []
        for k, v in metadata_input.items():
            if k in self._metadata_id_dict:
                metadata_vlist.append(
                    {"id": self._metadata_id_dict[k], "name": k, "value": v}
                )
        self.dify_kb.update_document_metadata(self.dataset_id, doc_id, metadata_vlist)
        logger.info(f"Updated metadata for {file_path} in Dify")
        return doc_id

    def apply_sync_actions(self, to_upload, to_update, to_delete):
        # 自动补全metadata
        self.ensure_metadata_fields_exist(self.config.metadata_fields)
        success_items = {"upload": [], "update": [], "delete": []}
        # 上传
        for att in to_upload:
            file_path = att.abspath
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue
            metadata_input = {
                "itemKey": att.itemKey,
                "title": att.title,
                "parentItemKey": att.parentItem.key,
                "parentItemTitle": att.parentItem.title,
                "parentItemTags": (
                    ", ".join(att.parentItem.tags) if att.parentItem.tags else ""
                ),
                "parentItemType": str(att.parentItem.itemTypeID),
                "relpath": att.relpath,
            }
            try:
                doc_id = self.upload_onefile(file_path, metadata_input)
                self.document_id_dict[att.itemKey] = doc_id
                success_items["upload"].append(att.itemKey)
            except Exception as e:
                logger.error(f"Failed to upload {file_path}: {e}")
        # 更新
        for att in to_update:
            doc_id = self.document_id_dict.get(att.itemKey)
            if doc_id:
                try:
                    metadata_vlist = []
                    for k, v in att.parentItem.items():
                        if k in self.metadata_id_dict:
                            metadata_vlist.append(
                                {"id": self.metadata_id_dict[k], "name": k, "value": v}
                            )
                    self.dify_kb.update_document_metadata(
                        self.dataset_id, doc_id, metadata_vlist
                    )
                    logger.info(f"Updated tags for {att.itemKey} in Dify")
                    success_items["update"].append(att.itemKey)
                except Exception as e:
                    logger.error(f"Failed to update tags for {att.itemKey}: {e}")
            else:
                logger.warning(f"No doc_id for {att.itemKey}, skip update.")
        # 删除
        for att in to_delete:
            doc_id = self._document_id_dict.get(att.itemKey)
            if doc_id:
                try:
                    self.dify_kb.delete_document(self.dataset_id, doc_id)
                    logger.info(f"Deleted {att.itemKey} {att.title} from Dify")
                    success_items["delete"].append(att.itemKey)
                except Exception as e:
                    logger.error(f"Failed to delete {att.itemKey}: {e}")
            else:
                logger.warning(f"No doc_id for {att.itemKey}, skip delete.")
        return success_items

    def ensure_metadata_fields_exist(self, required_fields: dict):
        """
        检查Dify KB中是否有所有需要的metadata字段，没有则自动创建。
        required_fields: dict, 例如 {"itemKey": "string", "title": "string", ...}
        """
        for name, type in required_fields.items():
            if name not in self.metadata_id_dict:
                logger.info(
                    f"Metadata field '{name}' not found in Dify KB, creating..."
                )
                self.dify_kb.create_metadata(self.dataset_id, name, type)

    def sync_zotero_attachments(self):
        current = self.get_current_attachments()
        archived = self.get_archived_attachments()
        to_upload, to_update, to_delete = self.diff_attachments(current, archived)
        logger.info(
            f"Found {len(to_upload)} attachments to upload, {len(to_update)} attachments to update, {len(to_delete)} attachments to delete"
        )
        success_items = self.apply_sync_actions(to_upload, to_update, to_delete)
        logger.info(
            f"Successfully synced {len(success_items['upload'])} attachments to upload, {len(success_items['update'])} attachments to update, {len(success_items['delete'])} attachments to delete"
        )

        # 归档逻辑：
        # 1. 本次上传成功的
        # 2. 本次更新成功的
        to_keep_keys = set(success_items["upload"]) | set(success_items["update"])
        # 3. 加上archive中未被删除的
        deleted_keys = set(success_items["delete"])
        for k in archived:
            if k not in deleted_keys:
                to_keep_keys.add(k)
        # 归档这些key对应的Attachment对象
        all_attachments = {**current, **archived}  # 以current为主，补充archive
        to_archive = [all_attachments[k] for k in to_keep_keys if k in all_attachments]
        self.save_local_archive(to_archive)
        logger.info(f"Archived {len(to_archive)} attachments")


if __name__ == "__main__":
    pipe_config = PipeConfig(
        kb_name="Zotero", tag_pattern="#%/%", archive_path="data/zdb.json"
    )
    pipeline = Pipeline(pipe_config)
    pipeline.sync_zotero_attachments()
