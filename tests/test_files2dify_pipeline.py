import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from src.pipeline.files2dify import Pipeline, PipelineConfig


class TestFiles2DifyPipeline(unittest.TestCase):
    def setUp(self):
        # Mock DifyKnowledgeBase before Pipeline instantiation
        self.dkb_patcher = patch('src.pipeline.files2dify.DifyKnowledgeBase', autospec=True)
        self.mock_dkb_cls = self.dkb_patcher.start()
        self.mock_dkb = self.mock_dkb_cls.return_value
        
        # Mock properties to avoid HTTP calls
        type(self.mock_dkb).documents = PropertyMock(return_value={"dummy.md": "docid1"})
        type(self.mock_dkb).metadata = PropertyMock(return_value={"tags": 1, "itemKey": 2})
        self.mock_dkb.dataset_id = "ds1"
        
        # Mock methods
        self.mock_dkb.upload_document_by_file.return_value = {"document": {"id": "docid1", "name": "dummy.md"}}
        self.mock_dkb.update_document_metadata.return_value = {"code": 200}
        
        self.config = PipelineConfig(kb_name="Files")
        self.pipeline = Pipeline(self.config)

    def tearDown(self):
        self.dkb_patcher.stop()

    def test_upload_onefile(self):
        dummy_file = "dummy.md"
        metadata_input = {"tags": "dummy", "itemKey": "k1"}
        res = self.pipeline.upload_onefile(dummy_file, metadata_input)
        self.assertEqual(res["upload"], "dummy.md")
        self.assertEqual(res["update_metadata"]["code"], 200)
        self.mock_dkb.upload_document_by_file.assert_called_once()
        self.mock_dkb.update_document_metadata.assert_called_once()

    def test_upload_batchfile(self):
        dummy_file = "dummy.md"
        metadata_input = {"tags": "dummy", "itemKey": "k1"}
        res_batch = self.pipeline.upload_batchfile([dummy_file], metadata_input)
        self.assertIsInstance(res_batch, list)
        self.assertEqual(res_batch[0]["upload"], "dummy.md")

    def test_upload_onefile_missing_metadata(self):
        dummy_file = "dummy.md"
        metadata_input = {"not_exist": "value"}
        # Should skip the invalid field and still return result
        res = self.pipeline.upload_onefile(dummy_file, metadata_input)
        # The method should still work and return valid result even with invalid metadata
        self.assertEqual(res["upload"], "dummy.md")
        # Check that update_document_metadata was called with empty metadata_vlist
        # since "not_exist" should be filtered out
        self.mock_dkb.update_document_metadata.assert_called_once()
        call_args = self.mock_dkb.update_document_metadata.call_args
        metadata_vlist = call_args[0][2]  # Third argument is metadata_vlist
        self.assertEqual(metadata_vlist, [])

    def test_upload_onefile_no_dataset_id(self):
        # Test when dataset_id is None
        self.mock_dkb.dataset_id = None
        self.pipeline.dataset_id = None
        
        dummy_file = "dummy.md"
        metadata_input = {"tags": "dummy"}
        res = self.pipeline.upload_onefile(dummy_file, metadata_input)
        self.assertIsNone(res)

    def test_upload_batchfile_no_dataset_id(self):
        # Test when dataset_id is None
        self.mock_dkb.dataset_id = None
        self.pipeline.dataset_id = None
        
        dummy_file = "dummy.md"
        metadata_input = {"tags": "dummy"}
        res = self.pipeline.upload_batchfile([dummy_file], metadata_input)
        self.assertEqual(res, [])


if __name__ == "__main__":
    unittest.main()
