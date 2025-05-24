from src.pipeline.zdb2dify import Pipeline
from src.config import CONFIG

def run_zdb2dify():
    pipeline = Pipeline(
        kb_name=CONFIG["dify"]["knowledge_base"]["dataset_name"],
        tag_pattern="#%/%",  # sql regex matching zotero tags like #read/todo
    )
    pipeline.sync_zotero_attachments()


if __name__ == "__main__":
    run_zdb2dify()
