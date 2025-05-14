from qdrant_client import QdrantClient
from config import CONFIG

qdrant_client = QdrantClient(
    url=CONFIG["qdrant"]["url"], 
    api_key=CONFIG["qdrant"]["api_key"],
)

print(qdrant_client.get_collections())