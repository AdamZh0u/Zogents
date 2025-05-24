import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import os
from src.pipeline.zdb2dify import Pipeline, PipeConfig
from src.handler.zotero_database import ParentItem, Attachment


class TestPipeline(unittest.TestCase):
    def setUp(self):
        # Mock all external dependencies before Pipeline instantiation
        self.dkb_patcher = patch('src.pipeline.zdb2dify.DifyKnowledgeBase', autospec=True)
        self.mock_dkb_cls = self.dkb_patcher.start()
        self.mock_dkb = self.mock_dkb_cls.return_value
        
        # Mock properties to avoid HTTP calls
        type(self.mock_dkb).documents = PropertyMock(return_value={"A": "docid1", "B": "docid2"})
        type(self.mock_dkb).metadata = PropertyMock(return_value={
            "itemKey": 1,
            "title": 2,
            "parentItemKey": 3,
            "parentItemTitle": 4,
            "parentItemTags": 5,
            "parentItemType": 6,
            "relpath": 7,
        })
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
        
        self.config = PipeConfig(
            kb_name="TestKB",
            tag_pattern="#test/%",
            archive_path="test_zdb_archive.json",
        )
        self.pipeline = Pipeline(self.config)

    def tearDown(self):
        self.dkb_patcher.stop()
        self.zotero_patcher.stop()
        if os.path.exists(self.config.archive_path):
            os.remove(self.config.archive_path)

    def make_attachment(self, key, tags, title="T", parent_title="PT"):
        parent = ParentItem(
            itemID=1, key="PK", tags=tags, title=parent_title, itemTypeID=0
        )
        return Attachment(
            itemID=1,
            itemKey=key,
            contentType="pdf",
            relpath="a.pdf",
            title=title,
            parentItem=parent,
        )

    def test_diff_attachments(self):
        a1 = self.make_attachment("A", ["t1"])
        a2 = self.make_attachment("B", ["t2"])
        b1 = self.make_attachment("A", ["t3"])
        b2 = self.make_attachment("C", ["t4"])
        current = {a1.itemKey: a1, a2.itemKey: a2}
        archived = {b1.itemKey: b1, b2.itemKey: b2}
        to_upload, to_update, to_delete = self.pipeline.diff_attachments(
            current, archived
        )
        self.assertIn(a2, to_upload)
        self.assertIn(a1, to_update)
        self.assertIn(b2, to_delete)

    def test_apply_sync_actions(self):
        a1 = self.make_attachment("A", ["t1"])
        a2 = self.make_attachment("B", ["t2"])
        
        # Mock upload_onefile to return doc_id
        with patch.object(self.pipeline, 'upload_onefile', return_value="docid1") as mock_upload:
            # Mock Path.exists to return True for file path checks
            with patch('pathlib.Path.exists', return_value=True):
                to_upload = [a2]
                to_update = [a1]
                to_delete = []
                result = self.pipeline.apply_sync_actions(to_upload, to_update, to_delete)
                
                self.assertIn("B", result["upload"])
                self.assertIn("A", result["update"])
                self.mock_dkb.update_document_metadata.assert_called()

    def test_save_and_get_archived_attachments(self):
        a1 = self.make_attachment("A", ["t1"])
        self.pipeline.save_local_archive([a1])
        archived = self.pipeline.get_archived_attachments()
        self.assertIn("A", archived)
        self.assertEqual(archived["A"].itemKey, "A")

    def test_sync_zotero_attachments(self):
        a1 = self.make_attachment("A", ["t1"])
        
        with patch.object(self.pipeline, 'get_current_attachments', return_value={"A": a1}):
            with patch.object(self.pipeline, 'get_archived_attachments', return_value={}):
                with patch.object(self.pipeline, 'apply_sync_actions', 
                                  return_value={"upload": ["A"], "update": [], "delete": []}) as mock_apply:
                    with patch.object(self.pipeline, 'save_local_archive') as mock_save:
                        self.pipeline.sync_zotero_attachments()
                        mock_apply.assert_called()
                        mock_save.assert_called()

    def test_upload_onefile(self):
        # Test the actual upload_onefile method
        dummy_file = "dummy.md"
        metadata_input = {"itemKey": "testkey", "title": "Test Title"}
        
        # Mock Path.exists to return True
        with patch('pathlib.Path.exists', return_value=True):
            res = self.pipeline.upload_onefile(dummy_file, metadata_input)
        
        # upload_onefile returns doc_id (string)
        self.assertEqual(res, "docid1")
        self.mock_dkb.upload_document_by_file.assert_called()
        self.mock_dkb.update_document_metadata.assert_called()


if __name__ == "__main__":
    unittest.main()
