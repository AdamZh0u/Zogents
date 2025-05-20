import os

from src.dify_rag.dify_knowledge_base import DifyKnowledgeBase, Pipeline

dify_knowledge_base = DifyKnowledgeBase()

# res path
res_dir = "tests/response"
docs_dir = "tests/docs"
if not os.path.exists(res_dir):
    os.makedirs(res_dir, exist_ok=True)
if not os.path.exists(docs_dir):
    os.makedirs(docs_dir, exist_ok=True)


pipeline = Pipeline()
file_path = os.path.join(docs_dir, "dummy.md")
metadata_input = {
    "permissions": "1",
    "expiration_time": None,
}
res = pipeline.run(file_path, metadata_input)
print(res)

# # get knowledge base and write res to tests
# res = dify_knowledge_base.get_knowledge_base()
# res_path = os.path.join(res_dir, "get_knowledge_base.json")
# with open(res_path, "w") as f:
#     json.dump(res, f)

# # list documents and write res to tests
# res = dify_knowledge_base.list_documents()
# res_path = os.path.join(res_dir, "list_documents.json")
# with open(res_path, "w") as f:
#     json.dump(res, f)

# # #
# with open(os.path.join(docs_dir, "dummy.md"), "r") as f:
#     text = f.read()
# doc = Document(name="dummy.md", text=text)
# print(doc.to_json())
# # res = dify_knowledge_base.upload_document_by_text(name="dummy.md", text=text)
# # print(res)


# res = dify_knowledge_base.upload_document_by_file(
#     file_path=os.path.join(docs_dir, "dummy.md")
# )
# print(res)

# res = dify_knowledge_base.update_metadata_list()
# print(res)
