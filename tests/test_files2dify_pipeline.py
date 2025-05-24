import unittest
from unittest.mock import MagicMock, patch
from src.pipeline.files2dify import Pipeline, PipelineConfig


class TestFiles2DifyPipeline(unittest.TestCase):
    def setUp(self):
        self.config = PipelineConfig(kb_name="Files")
        self.pipeline = Pipeline(self.config)
        self.pipeline.dify_kb = MagicMock()
        self.pipeline.dataset_id = "ds1"
        self.pipeline.document_id_dict = {"dummy.md": "docid1"}
        self.pipeline.metadata_id_dict = {"tags": 1, "itemKey": 2}

    @patch(
        "src.pipeline.files2dify.DifyKnowledgeBase.upload_document_by_file",
        return_value={"document": {"id": "docid1", "name": "dummy.md"}},
    )
    @patch(
        "src.pipeline.files2dify.DifyKnowledgeBase.update_document_metadata",
        return_value={"code": 200},
    )
    def test_upload_onefile(self, mock_update, mock_upload):
        dummy_file = "dummy.md"
        metadata_input = {"tags": "dummy", "itemKey": "k1"}
        res = self.pipeline.upload_onefile(dummy_file, metadata_input)
        self.assertEqual(res["upload"], "dummy.md")
        self.assertEqual(res["update_metadata"]["code"], 200)

    @patch(
        "src.pipeline.files2dify.DifyKnowledgeBase.upload_document_by_file",
        return_value={"document": {"id": "docid1", "name": "dummy.md"}},
    )
    @patch(
        "src.pipeline.files2dify.DifyKnowledgeBase.update_document_metadata",
        return_value={"code": 200},
    )
    def test_upload_batchfile(self, mock_update, mock_upload):
        dummy_file = "dummy.md"
        metadata_input = {"tags": "dummy", "itemKey": "k1"}
        res_batch = self.pipeline.upload_batchfile([dummy_file], metadata_input)
        self.assertIsInstance(res_batch, list)
        self.assertEqual(res_batch[0]["upload"], "dummy.md")

    @patch(
        "src.pipeline.files2dify.DifyKnowledgeBase.upload_document_by_file",
        return_value={"document": {"id": "docid1", "name": "dummy.md"}},
    )
    @patch(
        "src.pipeline.files2dify.DifyKnowledgeBase.update_document_metadata",
        return_value={"code": 200},
    )
    def test_upload_onefile_missing_metadata(self, mock_update, mock_upload):
        dummy_file = "dummy.md"
        metadata_input = {"not_exist": "value"}
        # Should log a warning and skip the field
        with self.assertLogs(level="WARNING") as cm:
            res = self.pipeline.upload_onefile(dummy_file, metadata_input)
        self.assertIn("not found in Dify KB", " ".join(cm.output))
        self.assertEqual(res["upload"], "dummy.md")


if __name__ == "__main__":
    unittest.main()
