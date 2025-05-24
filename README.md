# Zogents

**Zogents** is a robust pipeline toolkit for synchronizing, processing, and managing documents between a local Zotero database and the Dify knowledge base platform. It enables seamless extraction of attachments and metadata from Zotero, and automated upload and metadata management in Dify.

---

## Features

- **Zotero Integration**
  - Connects to a local Zotero SQLite database.
  - Extracts items, attachments, and tags, with advanced tag-based filtering (e.g., `#read/todo`).
- **Dify Knowledge Base Integration**
  - Uploads documents (PDFs or text) to Dify via API.
  - Updates document metadata in Dify, including custom tags from Zotero.
  - Supports batch and single-file operations.
- **Incremental Sync & Archiving**
  - Only uploads/updates new or changed attachments.
  - Maintains a local archive of uploaded/updated items for efficient incremental sync.
- **Configurable & Extensible**
  - Modular pipeline design for easy extension.
  - Configuration via TOML files in `config/`.

---

## Disclaimer

- The author does not recommend or endorse any misuse of this tool for generating academic content, bypassing research integrity, or violating institutional policies.
- You are solely responsible for how you use this software. The author assumes no liability for any consequences arising from its use.

---

## Project Structure

```
Zogents/
├── main.py                      # Example entry point for running the pipeline
├── src/
│   ├── config.py                # Configuration and logger setup
│   ├── handler/
│   │   ├── dify_knowledge_base.py  # Dify API integration (upload, metadata, etc.)
│   │   └── zotero_database.py      # Zotero database access and query logic
│   └── pipeline/
│       ├── files2dify.py        # Pipeline for uploading local files to Dify
│       └── zdb2dify.py          # Pipeline for syncing Zotero attachments to Dify
├── config/
│   ├── config.toml              # Main configuration file
│   └── config.toml.example      # Example config
├── data/                        # Archive and working data directory
├── tests/                       # Unit tests and test data
└── README.md                    # Project documentation
```

---

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure

Edit `config/config.toml` (see `config/config.toml.example`):

```toml
[zotero]
data_dir = "/path/to/your/Zotero/"

[dify.knowledge_base]
dataset_name = "YourKB"
api_key = "your-dify-api-key"
base_url = "https://your-dify-instance/v1"
```

### 3. Run the Pipeline

#### Create tags in Zotero
- Add tags like `#read/todo` to the Zotero items you want to sync

#### Sync Zotero Attachments to Dify

```python
from src.pipeline.zdb2dify import Pipeline, PipeConfig

pipe_config = PipeConfig(
    kb_name="YourKB",
    tag_pattern="#%/%",  # Filter attachments by tag pattern
    archive_path="data/zdb_attachments.json"
)
pipeline = Pipeline(pipe_config)
pipeline.sync_zotero_attachments()
```

#### CLI Example

You can also use `main.py` as a script:

```bash
python main.py
```

---

## Configuration

- All config is loaded from TOML files in `config/`.
- You can set the environment variable `ENV` to switch config profiles (default: `dev`).

---

## Example Data

- Example Zotero item: `tests/data/example_item.json`
- Example archive: `data/zdb_attachments.json`

---

## Requirements

- Python 3.11+
- See `pyproject.toml` for all dependencies (requests, duckdb, pyzotero, etc.)

---

## License

MIT License (see [LICENSE](LICENSE))

---

## Acknowledgements

- [Zotero](https://www.zotero.org/)
- [Dify](https://dify.ai/)
- [PyZotero](https://github.com/urschrei/pyzotero)
- [pyzotero-local](https://github.com/sailist/pyzotero-local)