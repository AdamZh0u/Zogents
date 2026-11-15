from src.config import CONFIG
from src.pipeline.zdb2dify import Pipeline, PipeConfig


def run_zdb2dify():
    pipe_config = PipeConfig(
        kb_name=CONFIG["dify"]["knowledge_base"]["dataset_name"],
        tag_pattern="#%/%",  # Filter attachments by tag pattern
        archive_path="data/zdb_attachments.json"
    )
    pipeline = Pipeline(pipe_config)
    pipeline.sync_zotero_attachments()

if __name__ == "__main__":
    run_zdb2dify()
