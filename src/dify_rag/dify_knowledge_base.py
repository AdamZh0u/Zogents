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
    name: Optional[str] = None  # 文档名称
    text: Optional[str] = None  # 文档内容
    indexing_technique: str = "high_quality"  # 索引技术
    process_rule: Dict[str, Any] = field(
        default_factory=lambda: {
            "mode": "custom",  # 处理规则模式
            "rules": {
                "pre_processing_rules": [
                    {"id": "remove_extra_spaces", "enabled": True},
                    {"id": "remove_urls_emails", "enabled": True},
                ],
                "segmentation": {
                    "separator": "---",
                    "max_tokens": 4000,
                },
                "parent_mode": "full-doc",  # full-doc 全文召回 / paragraph 段落召回
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
            "top_k": 9,
            "score_threshold_enabled": True,
            "score_threshold": 0.1,
        }
    )
    embedding_model: str = "BAAI/bge-m3"
    embedding_model_provider: str = "langgenius/siliconflow/siliconflow"

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


class DifyKnowledgeBase:
    # 封装知识库api

    def __init__(self):
        self.api_key = CONFIG["dify"]["knowledge_base"]["api_key"]
        self.base_url = CONFIG["dify"]["knowledge_base"]["base_url"]
        self.headers: dict = {
            "Authorization": f"Bearer {self.api_key}",
        }

    def list_knowledge_base(self):
        # 知识库列表
        url = f"{self.base_url}/datasets"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json())

    def get_knowledge_base(self, dataset_id: str):
        # 查看知识库详情
        url = f"{self.base_url}/datasets/{dataset_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json())

    def list_documents(self, dataset_id: str):
        # 查看知识库文档列表
        url = f"{self.base_url}/datasets/{dataset_id}/documents"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json())

    def upload_document_by_text(self, dataset_id: str, name: str, text: str):
        # 通过文本创建文档，严格参考curl示例
        url = f"{self.base_url}/datasets/{dataset_id}/document/create-by-text"
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
        url = f"{self.base_url}/datasets/{dataset_id}/document/create-by-file"
        # 构造data
        file_name = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        data_dict = Document(name=file_name, text=text).to_json()
        data = {"data": json.dumps(data_dict, ensure_ascii=False)}

        # 构造file
        with open(file_path, "rb") as f:
            file = {"file": (file_name, f)}
            response = requests.post(url, headers=self.headers, data=data, files=file)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.json())

    def get_metadata_idict(self, dataset_id: str):
        """
        获取文档元数据
        :param dataset_id: 知识库ID
        :return: API响应 id, name, type
        """
        url = f"{self.base_url}/datasets/{dataset_id}/metadata"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
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
        url = f"{self.base_url}/datasets/{dataset_id}/documents/metadata"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
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


class Pipeline:
    # 上传文档 -- 获取文档id -- 更新metadata
    def __init__(self):
        self.dify_knowledge_base = DifyKnowledgeBase()
        # dataset
        self.dataset_name: str = "Deego知识库"
        self.dataset_id_dict: Dict[str, Any] = {}  # 知识库名称：id
        # document
        self.document_id_dict: Dict[str, Any] = {}  # 文件名：id
        # metadata
        self.metadata_id_dict: Dict[str, Any] = {}  # 元数据名称：id

    def update_dataset_id_dict(self):
        res = self.dify_knowledge_base.list_knowledge_base()
        for item in res["data"]:
            self.dataset_id_dict[item["name"]] = item["id"]

    def update_document_id_dict(self, dataset_id: str):
        res = self.dify_knowledge_base.list_documents(dataset_id)["data"]
        for item in res:
            self.document_id_dict[item["name"]] = item["id"]

    def update_metadata_id_dict(self, dataset_id: str):
        res = self.dify_knowledge_base.get_metadata_idict(dataset_id)["doc_metadata"]
        for item in res:
            self.metadata_id_dict[item["name"]] = item["id"]

    def update_all(self):
        self.update_dataset_id_dict()
        self.dataset_name = "Deego知识库"
        self.dataset_id = self.dataset_id_dict[self.dataset_name]
        self.update_document_id_dict(self.dataset_id)
        self.update_metadata_id_dict(self.dataset_id)
        return self.dataset_id, self.document_id_dict, self.metadata_id_dict

    def run_onefile(self, file_path: str, metadata_input: dict):
        """
        metadata_input = {
            'permissions':"1",
            "expiration_time": None
        }

        Args:
            file_path (str): 本地文件路径
            metadata_input (dict): 元数据
        """
        self.update_all()
        # 上传文档
        res = self.dify_knowledge_base.upload_document_by_file(
            self.dataset_id, file_path
        )
        self.document_id = res["document"]["id"]

        # 更新metadata
        metadata_vlist = [
            {
                "id": self.metadata_id_dict[item],
                "name": item,
                "value": metadata_input[item],
            }
            for item in metadata_input
        ]
        update_res = self.dify_knowledge_base.update_document_metadata(
            self.dataset_id, self.document_id, metadata_vlist
        )
        return {"upload": res["document"]["name"], "update_metadata": update_res}

    def run_batchfile(self, file_path_list: list, metadata_input: dict):
        self.update_all()
        results = []
        for file_path in file_path_list:
            result = self.run_onefile(file_path, metadata_input)
            logger.info(result)
        return results
