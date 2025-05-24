import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests

from src.config import CONFIG, get_logger

logger = get_logger()


@dataclass
class Document:
    # {"name": "text","text": "text","indexing_technique": "high_quality","process_rule": {"mode": "automatic"}}
    # source :
    name: Optional[str] = None  # 文档名称
    text: Optional[str] = None  # 文档内容
    indexing_technique: str = "high_quality"  # 索引技术
    doc_form: str = "hierarchical_model"  # text_model /  hierarchical_model /qa_model
    process_rule: Dict[str, Any] = field(
        default_factory=lambda: {
            "mode": "custom",  # 处理规则模式 custom/ automatic
            "rules": {
                "pre_processing_rules": [
                    {"id": "remove_extra_spaces", "enabled": True},
                    {"id": "remove_urls_emails", "enabled": True},
                ],
                "segmentation": {
                    "separator": "\n\n\n",
                    "max_tokens": 4000,
                },
                "parent_mode": "paragraph",  # full-doc 全文召回 / paragraph 段落召回
                "subchunk_segmentation": {
                    "separator": "\n\n",
                    "max_tokens": 500,
                    "chunk_overlap": 50,
                },  # s子分段规则
            },
        }
    )
    # 召回模型 当知识库未设置任何参数的时候，首次上传需要提供以下参数，未提供则使用默认选项：
    retrieval_model: Dict[str, Any] = field(
        default_factory=lambda: {
            "search_method": "hybrid_search",
            "reranking_enable": True,
            "reranking_mode": "reranking_model",
            "reranking_model": {
                "reranking_provider_name": "langgenius/siliconflow/siliconflow",
                "reranking_model_name": "BAAI/bge-reranker-v2-m3",
            },
            "top_k": 8,
            "score_threshold_enabled": True,
            "score_threshold": 0.1,
        }
    )
    embedding_model: str = "text-embedding-3-small"  # text-embedding-3-small
    embedding_model_provider: str = "langgenius/openai"

    @classmethod
    def from_json(cls, json_data: dict):
        return cls(
            name=json_data.get("name"),
            text=json_data.get("text"),
            indexing_technique=json_data.get("indexing_technique", "high_quality"),
            process_rule=json_data.get("process_rule") or cls().process_rule,
            retrieval_model=json_data.get("retrieval_model") or cls().retrieval_model,
            embedding_model=json_data.get("embedding_model", "BAAI/bge-m3"),
            embedding_model_provider=json_data.get(
                "embedding_model_provider", "langgenius/siliconflow/siliconflow"
            ),
        )

    def to_json(self):
        return {
            "name": self.name,
            "text": self.text,
            "indexing_technique": self.indexing_technique,
            "process_rule": self.process_rule,
            "retrieval_model": self.retrieval_model,
            "embedding_model": self.embedding_model,
            "embedding_model_provider": self.embedding_model_provider,
        }

    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"<Document {attrs}>"


@dataclass
class KBConfig:
    api_key: str = CONFIG["dify"]["knowledge_base"]["api_key"]
    base_url: str = CONFIG["dify"]["knowledge_base"]["base_url"]


class DifyKnowledgeBase:
    # 封装知识库api

    def __init__(
        self, dataset_name: Optional[str] = None, kb_config: KBConfig = KBConfig()
    ):
        self.kb_config = kb_config
        self.headers: dict = {
            "Authorization": f"Bearer {self.kb_config.api_key}",
        }
        self.dataset_name: str = dataset_name
        self._datasets: Dict[str, Any] = {}
        self._dataset_id: str = ""
        self._documents: Dict[str, Any] = {}  # itemKey -> document_id
        self._metadata: Dict[str, Any] = {}  # metadata Name -> metadata id

    @property
    def datasets(self) -> Dict[str, Any]:
        res = self.list_knowledge_base()
        self._datasets = {item["name"]: item["id"] for item in res["data"]}
        return self._datasets

    @property
    def dataset_id(self) -> str:
        datasets = self.datasets
        if self.dataset_name in datasets:
            self._dataset_id = datasets[self.dataset_name]
        else:
            logger.info(f"Dataset name is not found in all datasets: {self._datasets}")
            return None
        return self._dataset_id

    @property
    def documents(self) -> Dict[str, Any]:
        res = self.list_documents(self._dataset_id)
        dict_res = {}
        for item in res:
            for fld in item["doc_metadata"]:
                if fld["name"] == "itemKey":
                    key = fld["value"]
                    dict_res[key] = item["id"]
        self._documents = dict_res
        return self._documents

    @property
    def metadata(self) -> Dict[str, Any]:
        res = self.list_metadata(self._dataset_id)
        self._metadata = {item["name"]: item["id"] for item in res}
        return self._metadata

    def list_knowledge_base(self):
        # 知识库列表
        url = f"{self.kb_config.base_url}/datasets"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json())

    def get_knowledge_base(self, dataset_id: str):
        # 查看知识库详情
        url = f"{self.kb_config.base_url}/datasets/{dataset_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json())

    def list_documents(self, dataset_id: str):
        # 查看知识库文档列表
        url = f"{self.kb_config.base_url}/datasets/{dataset_id}/documents"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            res = response.json()
            return res["data"]
        else:
            raise Exception(response.json())

    def list_metadata(self, dataset_id: str):
        """
        获取文档元数据
        :param dataset_id: 知识库ID
        :return: API响应 id, name, type
        """
        url = f"{self.kb_config.base_url}/datasets/{dataset_id}/metadata"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            res = response.json()
            return res["doc_metadata"]
        else:
            raise Exception(response.json())

    def upload_document_by_text(
        self, dataset_id: str, name: str, text: Optional[str] = None
    ):
        # 通过文本创建文档，严格参考curl示例
        url = f"{self.kb_config.base_url}/datasets/{dataset_id}/document/create-by-text"
        self.headers["Content-Type"] = "application/json"
        data = Document(name=name, text=text).to_json()
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json())

    def upload_document_by_file(self, dataset_id: str, file_path: str):
        """
        通过文件创建文档
        :param dataset_id: 知识库ID
        :param file_path: 本地文件路径
        :return: API响应
        """
        url = f"{self.kb_config.base_url}/datasets/{dataset_id}/document/create-by-file"
        # 构造data
        file_name = os.path.basename(file_path)
        data_dict = Document(name=file_name).to_json()
        data = {"data": json.dumps(data_dict, ensure_ascii=False)}

        # 构造file
        with open(file_path, "rb") as f:
            file = {"file": (file_name, f)}
            response = requests.post(url, headers=self.headers, data=data, files=file)
        if response.status_code == 200:
            return response.json()["document"]["id"]
        else:
            raise Exception(response.json())

    def update_document_metadata(
        self, dataset_id: str, document_id: str, metadata_vlist: list
    ):
        """
        更新文档元数据 (可以批量操作)
        :param dataset_id: 知识库ID
        :param document_id: 文档ID
        :param metadata_vdict: 元数据 metadata [{'id':1,'name':name,'value':value}]  id, name, value
        :return: API响应
        """
        url = f"{self.kb_config.base_url}/datasets/{dataset_id}/documents/metadata"
        headers = {
            "Authorization": f"Bearer {self.kb_config.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "operation_data": [
                {
                    "document_id": document_id,
                    "metadata_list": metadata_vlist,
                }
            ]
        }
        data = json.dumps(data, ensure_ascii=False)
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Status: {response.status_code}, Detail: {response.text}")

    def delete_document(self, dataset_id: str, document_id: str):
        """
        删除文档
        :param dataset_id: 知识库ID
        :param document_id: 文档ID
        :return: API响应
        """
        url = f"{self.kb_config.base_url}/datasets/{dataset_id}/documents/{document_id}"
        response = requests.delete(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json())

    def create_metadata(self, dataset_id: str, metadata_name: str, metadata_type: str):
        """
        创建元数据
        :param dataset_id: 知识库ID
        :param metadata_name: 元数据名称
        :param metadata_type: 元数据类型
        """
        url = f"{self.kb_config.base_url}/datasets/{dataset_id}/metadata"
        data = {
            "name": metadata_name,
            "type": metadata_type,
        }
        response = requests.post(url, headers=self.headers, json=data)
        return response.json()
