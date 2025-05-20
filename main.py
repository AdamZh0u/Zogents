from pyprojroot import here

from src.parse import pipeline
from src.zotero import zdb

itemids = [2045, 2046]

attaches = zdb.get_attachments_by_itemid(*itemids)

pdf_paths = [a.abspath for a in attaches]

max_nst_o3m_config = pipeline.RunConfig(
    use_serialized_tables=False,
    parent_document_retrieval=True,
    llm_reranking=True,
    parallel_requests=25,
    submission_name="Ilia Ris v.4",
    pipeline_details="Custom pdf parsing + vDB + Router + Parent Document Retrieval + reranking + SO CoT; llm = o3-mini",
    answering_model="o3-mini-2025-01-31",
    config_suffix="_max_nst_o3m",
)

root_path = here() / "data" / "test_set"
pl = pipeline.Pipeline(root_path, run_config=max_nst_o3m_config)

pl.parse_pdf_reports_sequential(input_doc_paths=pdf_paths)
pl.serialize_tables(max_workers=5)
pl.merge_reports()
# pipeline.export_reports_to_markdown()
# pipeline.chunk_reports()
# pipeline.create_vector_dbs()
# pipeline.process_questions()
