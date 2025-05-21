from typing import Dict, Any

from src.dify_knowledge_base import DifyKnowledgeBase
from src.config import get_logger

logger = get_logger()


class Pipeline:
    """
    Pipeline for uploading documents to Dify and updating their metadata.
    Handles dataset/document/metadata id management and batch operations.
    """

    def __init__(self, kb_name: str = "demo"):
        self.dify_knowledge_base = DifyKnowledgeBase()
        self.dataset_name: str = kb_name
        self.dataset_id_dict: Dict[str, Any] = {}
        self.document_id_dict: Dict[str, Any] = {}
        self.metadata_id_dict: Dict[str, Any] = {}
        self.dataset_id: str = None
        self.update_all()

    def update_dataset_id_dict(self) -> Dict[str, Any]:
        """
        Update and return the dataset name-to-id mapping.
        """
        res = self.dify_knowledge_base.list_knowledge_base()
        self.dataset_id_dict = {item["name"]: item["id"] for item in res["data"]}
        if self.dataset_name not in self.dataset_id_dict:
            logger.error(f"Dataset {self.dataset_name} not found")

        else:
            self.dataset_id = self.dataset_id_dict[self.dataset_name]  # 获取知识库id
        return self.dataset_id_dict

    def update_document_id_dict(self) -> Dict[str, Any]:
        """
        Update and return the document name-to-id mapping for the current dataset.
        """
        if not self.dataset_id:
            logger.error("Dataset ID is not set. Cannot update document id dict.")
            return {}
        res = self.dify_knowledge_base.list_documents(self.dataset_id)["data"]
        self.document_id_dict = {item["name"]: item["id"] for item in res}
        return self.document_id_dict

    def update_metadata_id_dict(self) -> Dict[str, Any]:
        """
        Update and return the metadata name-to-id mapping for the current dataset.
        """
        if not self.dataset_id:
            logger.error("Dataset ID is not set. Cannot update metadata id dict.")
            return {}
        res = self.dify_knowledge_base.get_metadata_idict(self.dataset_id)[
            "doc_metadata"
        ]
        self.metadata_id_dict = {item["name"]: item["id"] for item in res}
        return self.metadata_id_dict

    def update_all(self):
        """
        Update all id dictionaries and set dataset_id for the pipeline.
        """
        self.update_dataset_id_dict()
        if self.dataset_id:
            self.update_document_id_dict()
            self.update_metadata_id_dict()

    def run_onefile(self, file_path: str, metadata_input: dict):
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
        res = self.dify_knowledge_base.upload_document_by_file(
            self.dataset_id, file_path
        )
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
        update_res = self.dify_knowledge_base.update_document_metadata(
            self.dataset_id, document_id, metadata_vlist
        )
        return {"upload": res["document"]["name"], "update_metadata": update_res}

    def run_batchfile(self, file_path_list: list, metadata_input: dict):
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
            result = self.run_onefile(file_path, metadata_input)
            logger.info(result)
            results.append(result)
        return results


if __name__ == "__main__":
    pipeline = Pipeline()
    pipeline.run_onefile("test.txt", {"permissions": "1", "expiration_time": None})
    pipeline.run_batchfile(
        ["test.txt", "test2.txt"], {"permissions": "1", "expiration_time": None}
    )
