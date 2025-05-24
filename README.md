# Zogents

Zogents is a pipeline toolkit for integrating, processing, and synchronizing documents between a local Zotero database and the Dify knowledge base platform. It supports extracting attachments and metadata from Zotero, processing PDFs, and uploading them (with Zoterotags as metadata) to Dify for further knowledge management and retrieval.

## Features

- **Zotero Integration**:
  - Connects to a local Zotero SQLite database.
  - Extracts items, attachments, and tags, supporting advanced tag-based filtering (e.g., `#w/read`).
- **PDF Processing Pipeline**:
  - Supports batch processing of PDFs, including parsing, table serialization, merging, and chunking.
  - Configurable pipeline steps for custom document workflows.
- **Dify Knowledge Base Integration**:
  - Uploads documents (PDFs or text) to Dify via API.
  - Updates document metadata in Dify, including custom tags from Zotero.
  - Supports batch and single-file operations.
- **Configurable and Extensible**:
  - Modular design for easy extension.
  - Configuration via `config/` and environment variables.

## Project Structure

```
Zogents/
├── main.py                # Example entry point for running the pipeline
├── src/
│   ├── config.py          # Configuration and logger setup
│   ├── dify_knowledge_base.py  # Dify API integration (upload, metadata, etc.)
│   ├── zdb.py             # Zotero database access and query logic
│   └── pipelines/
│       ├── files2dify.py  # Pipeline for uploading local files to Dify
│       └── zdb2dify.py    # Pipeline for syncing Zotero attachments to Dify
├── tests/                 # Test scripts and data
├── config/                # Configuration files (API keys, paths, etc.)
├── data/                  # Example or working data directory
└── README.md              # Project documentation
```

## Quick Start

### 1. Configure

- Set up your `config/` files with Zotero data directory and Dify API credentials.
- Example config keys:
  - `CONFIG["zotero"]["data_dir"]`
  - `CONFIG["dify"]["knowledge_base"]["api_key"]`
  - `CONFIG["dify"]["knowledge_base"]["base_url"]`
  - `CONFIG["dify"]["knowledge_base"]["dataset_name"]`

### 2. Extract and Upload Attachments

Example: Extract all attachments with special tags from Zotero and upload to Dify:

```python
from src.pipelines.zdb2dify import ZDB2DifyPipeline

pipeline = ZDB2DifyPipeline()
pipeline.upload_zotero_attachments_to_dify()
```

### 3. Custom Pipeline Usage

You can also use the lower-level pipeline for local files:

```python
from src.pipelines.files2dify import Pipeline

pipeline = Pipeline(kb_name="YourKnowledgeBaseName")
pipeline.run_onefile("path/to/file.pdf", {"tags": "tag1, tag2"})
```

### 4. Main Pipeline Example

See `main.py` for a full example of extracting PDFs from Zotero and running the document processing pipeline.

## Key Modules

- **src/zdb.py**:
  Handles all interactions with the Zotero SQLite database, including item, attachment, and tag queries.

- **src/dify_knowledge_base.py**:
  Encapsulates Dify API calls for document upload, metadata management, and knowledge base queries.

- **src/pipelines/files2dify.py**:
  Provides a pipeline for uploading local files to Dify and updating their metadata.

- **src/pipelines/zdb2dify.py**:
  Orchestrates the extraction of attachments from Zotero and their upload to Dify, preserving tags as metadata.

## Testing

Test scripts are located in the `tests/` directory.
You can run them with:

```bash
python -m unittest discover tests
```

## Requirements

- Python 3.8+
- requests
- pyprojroot
- (other dependencies, see `pyproject.toml`)

## License

MIT License



- attachementItem
  - itemID
  - itemKey
  - title
  - parentItemID
  - parentItemKey
  - parentItemTags
  - contentType
  - relpath

- process
  - get_parent_items_with_special_tag
  - get_attachements_by_parent_item
  - upload_zotero_attachments_to_dify
  - check_attachment_exists
  - upload_onefile
  - update_all
