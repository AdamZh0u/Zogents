from src.config import CONFIG, get_logger
from src.pipelines.files2dify import Pipeline
from src.dify_knowledge_base import DifyKnowledgeBase
from src.zdb import (
    ZoteroDB,
    get_attachements_by_parent_item,
    get_parent_items_with_special_tag,
)

logger = get_logger()


class ZDB2DifyPipeline(Pipeline):
    # 上传文档 -- 获取文档id -- 更新metadata
    def __init__(self, kb_name: str = "kn_name"):
        self.dify_knowledge_base = DifyKnowledgeBase()
        # dataset
        super().__init__(kb_name)

    def upload_zotero_attachments_to_dify(self):
        """
        Read attachments with tags from the Zotero database and upload them to Dify, saving tags as metadata.
        """
        logger.info("Starting upload of Zotero attachments with tags to Dify...")
        db = ZoteroDB()
        tag_pattern = "#%/%"  # or customize as needed
        parent_items = get_parent_items_with_special_tag(db, tag_pattern)
        logger.info(f"Found {len(parent_items)} parent items with special tags.")

        self.update_all()

        for parent_item in parent_items:
            attachments = get_attachements_by_parent_item(db, parent_item)
            logger.info(
                f"Found {len(attachments)} attachments for parent item {parent_item.key} | {parent_item}"
            )
            for attachment in attachments:
                file_path = attachment.abspath
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue
                # Prepare metadata: save tags as a single string or list
                metadata_input = {
                    "tags": (
                        ", ".join(attachment.parentItemTags)
                        if attachment.parentItemTags
                        else ""
                    )
                }
                try:
                    result = self.run_onefile(file_path, metadata_input)
                    logger.info(
                        f"Uploaded {file_path} with tags {metadata_input['tags']}: {result}"
                    )
                except Exception as e:
                    logger.error(f"Failed to upload {file_path}: {e}")


if __name__ == "__main__":
    pipeline = ZDB2DifyPipeline(
        kb_name=CONFIG["dify"]["knowledge_base"]["dataset_name"]
    )
    pipeline.upload_zotero_attachments_to_dify()
