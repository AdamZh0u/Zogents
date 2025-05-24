import unittest
from unittest.mock import MagicMock, patch
import os
from src.handler.dify_knowledge_base import DifyKnowledgeBase, Document
from src.pipeline.files2dify import Pipeline


def ensure_dummy_file(path, content="# Dummy test file\nThis is a test."):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


class TestDifyKnowledgeBase(unittest.TestCase):
    def setUp(self):
        self.dify = DifyKnowledgeBase()
        self.dify.list_knowledge_base = MagicMock(
            return_value={"data": [{"name": "kb1", "id": "id1"}]}
        )
        self.dify.get_knowledge_base = MagicMock(return_value={"data": {"id": "id1"}})
        self.dify.list_documents = MagicMock(
            return_value=[{"name": "doc1", "id": "docid1"}]
        )
        self.dify.upload_document_by_text = MagicMock(
            return_value={"document": {"id": "docid1", "name": "doc1"}}
        )
        self.dify.upload_document_by_file = MagicMock(
            return_value={"document": {"id": "docid2", "name": "doc2"}}
        )
        self.dify.get_metadata_idict = MagicMock(
            return_value={"doc_metadata": [{"id": 1, "name": "tags"}]}
        )
        self.dify.update_document_metadata = MagicMock(return_value={"code": 200})
        self.dify.create_metadata = MagicMock(return_value={"id": 2, "name": "newmeta"})

    def test_list_knowledge_base(self):
        kb_list = self.dify.list_knowledge_base()
        self.assertIn("data", kb_list)
        self.assertEqual(kb_list["data"][0]["name"], "kb1")

    def test_get_knowledge_base(self):
        kb_detail = self.dify.get_knowledge_base("id1")
        self.assertEqual(kb_detail["data"]["id"], "id1")

    def test_list_documents(self):
        docs = self.dify.list_documents("id1")
        self.assertEqual(docs[0]["id"], "docid1")

    def test_upload_document_by_text(self):
        doc = Document(name="dummy.md", text="test")
        res = self.dify.upload_document_by_text("id1", doc.name, doc.text)
        self.assertIn("document", res)

    def test_upload_document_by_file(self):
        res = self.dify.upload_document_by_file("id1", "dummy.md")
        self.assertIn("document", res)

    def test_update_document_metadata(self):
        meta_update = [{"id": 1, "name": "tags", "value": "test_value"}]
        res = self.dify.update_document_metadata("id1", "docid1", meta_update)
        self.assertEqual(res["code"], 200)

    def test_create_metadata(self):
        res = self.dify.create_metadata("id1", "newmeta", "string")
        self.assertEqual(res["name"], "newmeta")


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = Pipeline(kb_name="Zotero")
        self.pipeline.dify_knowledge_base = MagicMock()
        self.pipeline.dataset_id = "id1"
        self.pipeline.metadata_id_dict = {"tags": 1}
        self.pipeline.document_id_dict = {"dummy.md": "docid1"}

    @patch(
        "src.pipelines.files2dify.DifyKnowledgeBase.upload_document_by_file",
        return_value={"document": {"id": "docid1", "name": "dummy.md"}},
    )
    @patch(
        "src.pipelines.files2dify.DifyKnowledgeBase.update_document_metadata",
        return_value={"code": 200},
    )
    def test_upload_onefile(self, mock_update, mock_upload):
        dummy_file = "dummy.md"
        metadata_input = {"tags": "dummy"}
        res = self.pipeline.upload_onefile(dummy_file, metadata_input)
        self.assertIn("upload", res)
        self.assertIn("update_metadata", res)

    @patch(
        "src.pipelines.files2dify.DifyKnowledgeBase.upload_document_by_file",
        return_value={"document": {"id": "docid1", "name": "dummy.md"}},
    )
    @patch(
        "src.pipelines.files2dify.DifyKnowledgeBase.update_document_metadata",
        return_value={"code": 200},
    )
    def test_upload_batchfile(self, mock_update, mock_upload):
        dummy_file = "dummy.md"
        metadata_input = {"tags": "dummy"}
        res = self.pipeline.upload_batchfile([dummy_file], metadata_input)
        self.assertIsInstance(res, list)


if __name__ == "__main__":
    unittest.main()
