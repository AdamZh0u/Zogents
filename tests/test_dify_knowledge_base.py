import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import os
from src.handler.dify_knowledge_base import DifyKnowledgeBase, Document
from src.pipeline.zdb2dify import Pipeline, PipeConfig


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


class TestZdb2DifyPipeline(unittest.TestCase):
    def setUp(self):
        # Mock all external dependencies before Pipeline instantiation
        self.dkb_patcher = patch('src.pipeline.zdb2dify.DifyKnowledgeBase', autospec=True)
        self.mock_dkb_cls = self.dkb_patcher.start()
        self.mock_dkb = self.mock_dkb_cls.return_value
        
        # Mock properties to avoid HTTP calls
        type(self.mock_dkb).documents = PropertyMock(return_value={"testkey": "docid1"})
        type(self.mock_dkb).metadata = PropertyMock(return_value={"itemKey": 1, "title": 2, "tags": 3})
        self.mock_dkb.dataset_id = "ds1"
        
        # Mock methods
        self.mock_dkb.upload_document_by_file.return_value = "docid1"
        self.mock_dkb.update_document_metadata.return_value = {"code": 200}
        self.mock_dkb.delete_document.return_value = None
        self.mock_dkb.create_metadata.return_value = {"id": 2, "name": "newmeta"}
        
        # Mock ZoteroConn to avoid database dependency
        self.zotero_patcher = patch('src.pipeline.zdb2dify.ZoteroConn')
        self.mock_zotero_cls = self.zotero_patcher.start()
        self.mock_zotero = self.mock_zotero_cls.return_value
        
        self.pipeline = Pipeline(PipeConfig(kb_name="TestKB"))

    def tearDown(self):
        self.dkb_patcher.stop()
        self.zotero_patcher.stop()

    def test_upload_onefile(self):
        dummy_file = "dummy.md"
        metadata_input = {"itemKey": "testkey", "title": "Test Title"}
        
        # Mock Path.exists to return True
        with patch('pathlib.Path.exists', return_value=True):
            res = self.pipeline.upload_onefile(dummy_file, metadata_input)
        
        # zdb2dify.Pipeline.upload_onefile returns doc_id (string), not dict
        self.assertEqual(res, "docid1")
        self.mock_dkb.upload_document_by_file.assert_called_once()
        self.mock_dkb.update_document_metadata.assert_called_once()

    def test_ensure_metadata_fields_exist(self):
        required_fields = {"newfield": "string", "itemKey": "string"}  # itemKey exists, newfield doesn't
        
        self.pipeline.ensure_metadata_fields_exist(required_fields)
        
        # Should only create metadata for fields that don't exist
        self.mock_dkb.create_metadata.assert_called_once_with("ds1", "newfield", "string")


if __name__ == "__main__":
    unittest.main()
