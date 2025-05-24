import unittest
from unittest.mock import MagicMock, patch
import os
from src.pipeline.zdb2dify import Pipeline, PipeConfig, Attachment, ParentItem


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.config = PipeConfig(
            kb_name="TestKB",
            tag_pattern="#test/%",
            archive_path="test_zdb_archive.json",
        )
        self.pipeline = Pipeline(self.config)
        self.pipeline.dify_kb = MagicMock()
        self.pipeline.dataset_id = "ds1"
        self.pipeline._document_id_dict = {}
        self.pipeline._metadata_id_dict = {
            "itemKey": 1,
            "title": 2,
            "parentItemKey": 3,
            "parentItemTitle": 4,
            "parentItemTags": 5,
            "parentItemType": 6,
            "relpath": 7,
        }

    def tearDown(self):
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

    @patch.object(Pipeline, "upload_onefile", return_value="docid1")
    @patch.object(Pipeline, "ensure_metadata_fields_exist")
    def test_apply_sync_actions(self, mock_ensure, mock_upload):
        a1 = self.make_attachment("A", ["t1"])
        a2 = self.make_attachment("B", ["t2"])
        self.pipeline._document_id_dict["A"] = "docid1"
        self.pipeline.dify_kb.update_document_metadata = MagicMock()
        self.pipeline.dify_kb.delete_document = MagicMock()
        to_upload = [a2]
        to_update = [a1]
        to_delete = []
        result = self.pipeline.apply_sync_actions(to_upload, to_update, to_delete)
        self.assertIn("B", result["upload"])
        self.assertIn("A", result["update"])
        self.pipeline.dify_kb.update_document_metadata.assert_called()

    def test_save_and_get_archived_attachments(self):
        a1 = self.make_attachment("A", ["t1"])
        self.pipeline.save_local_archive([a1])
        archived = self.pipeline.get_archived_attachments()
        self.assertIn("A", archived)
        self.assertEqual(archived["A"].itemKey, "A")

    @patch.object(
        Pipeline,
        "apply_sync_actions",
        return_value={"upload": ["A"], "update": [], "delete": []},
    )
    @patch.object(Pipeline, "get_current_attachments")
    @patch.object(Pipeline, "get_archived_attachments")
    @patch.object(Pipeline, "save_local_archive")
    def test_sync_zotero_attachments(
        self, mock_save, mock_get_archived, mock_get_current, mock_apply
    ):
        a1 = self.make_attachment("A", ["t1"])
        mock_get_current.return_value = {"A": a1}
        mock_get_archived.return_value = {}
        self.pipeline.sync_zotero_attachments()
        mock_apply.assert_called()
        mock_save.assert_called()


if __name__ == "__main__":
    unittest.main()
