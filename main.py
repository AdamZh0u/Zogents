from src.pipelines.files2dify import Pipeline
from src.pipelines.zdb2dify import ZDB2DifyPipeline
from src.config import CONFIG


def run_files2dify():
    pipeline = Pipeline(
        kb_name=CONFIG["dify"]["knowledge_base"]["dataset_name"],
    )
    pipeline.upload_onefile("test.txt", {"tags": "test/1, test/2"})
    pipeline.upload_batchfile(["test.txt", "test2.txt"], {"tags": "test/1, test/2"})


def run_zdb2dify():
    pipeline = ZDB2DifyPipeline(
        kb_name=CONFIG["dify"]["knowledge_base"]["dataset_name"],
        tag_pattern="#%/%",  # sql regex matching zotero tags like #read/todo
    )
    pipeline.upload_zotero_attachments_to_dify()


if __name__ == "__main__":
    # run_files2dify()
    run_zdb2dify()
