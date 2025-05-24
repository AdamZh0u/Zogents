from typing import Dict, Any
from dataclasses import dataclass, field

from src.handler.dify_knowledge_base import DifyKnowledgeBase
from src.config import get_logger

logger = get_logger()


@dataclass
class PipelineConfig:
    kb_name: str = "Files"
    metadata_fields: dict[str, str] = field(
        default_factory=lambda: {
            "itemKey": "string",
            "title": "string",
            "parentItemKey": "string",
            "parentItemTitle": "string",
            "parentItemTags": "string",
            "contentType": "string",
            "relpath": "string",
        }
    )


class Pipeline:
    """
    Pipeline for uploading documents to Dify and updating their metadata.
    Handles dataset/document/metadata id management and batch operations.
    """

    def __init__(self, pipe_config: PipelineConfig = None):
        self.config = pipe_config
        self.dify_kb = DifyKnowledgeBase(dataset_name=self.config.kb_name)
        self.dataset_id: str = self.dify_kb.dataset_id
        self.document_id_dict: Dict[str, Any] = self.dify_kb.documents
        self.metadata_id_dict: Dict[str, Any] = self.dify_kb.metadata

    # def update_all(self):
    #     """
    #     Update all id dictionaries and set dataset_id for the pipeline.
    #     """
    #     self.update_dataset_id_dict()
    #     if self.dataset_id:
    #         self.update_document_id_dict()
    #         self.update_metadata_id_dict()

    def upload_onefile(self, file_path: str, metadata_input: dict):
        """
        Upload a single file and update its metadata.
        Args:
            file_path (str): Local file path
            metadata_input (dict): Metadata to update
        Returns:
            dict: Upload and metadata update results
        """
        if not self.dataset_id:
            logger.error("Dataset ID is not set. Cannot upload file.")
            return None
        res = self.dify_kb.upload_document_by_file(self.dataset_id, file_path)
        document_id = res["document"]["id"]
        # Prepare metadata update list
        metadata_vlist = []
        for item in metadata_input:
            if item in self.metadata_id_dict:
                metadata_vlist.append(
                    {
                        "id": self.metadata_id_dict[item],
                        "name": item,
                        "value": metadata_input[item],
                    }
                )
            else:
                logger.warning(
                    f"Metadata field '{item}' not found in Dify KB, skipping."
                )
        update_res = self.dify_kb.update_document_metadata(
            self.dataset_id, document_id, metadata_vlist
        )
        return {"upload": res["document"]["name"], "update_metadata": update_res}

    def upload_batchfile(self, file_path_list: list, metadata_input: dict):
        """
        Upload a batch of files and update their metadata.
        Args:
            file_path_list (list): List of local file paths
            metadata_input (dict): Metadata to update for each file
        Returns:
            list: Results for each file
        """
        if not self.dataset_id:
            logger.error("Dataset ID is not set. Cannot upload files.")
            return []
        results = []
        for file_path in file_path_list:
            result = self.upload_onefile(file_path, metadata_input)
            logger.info(result)
            results.append(result)
        return results
