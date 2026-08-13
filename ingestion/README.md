# Chroma Ingestion Pipeline (course tooling)

Builds the ChromaDB collection that the lab's coding agent uses for
semantic search over this codebase. Ported from the course code-search
app's ingestion pipeline so the resulting collection has the same
structure (chunking strategy, metadata schema, embedding setup).

**This directory is course tooling, not part of the feedback application**,
and it is excluded from its own ingestion — running the script never puts
this pipeline's code into the collection. Also excluded: `SPEC.md` and
`docs/investigation_scenarios.md` (spoilers), plus `.venv`, `instance/`,
`logs/`, and `chroma_data/`.

## What gets ingested

All `.py`, `.md`, and `.txt` files in the repo (code, tests, scripts,
docs, notes), chunked as:

| File type | Strategy | chunk_type |
|---|---|---|
| `.py` | tree-sitter AST: each function/class is an atomic chunk; code between definitions becomes `gap` chunks | `function_definition`, `class_definition`, `gap` |
| `.md` | one chunk per H1–H3 section | `markdown_section` |
| `.txt` | token-bounded paragraphs | `text_paragraph` |

Chunks exceeding 1000 tokens (tiktoken, `text-embedding-3-small` encoding)
are subdivided on line boundaries. Each chunk carries metadata:
`path` (repo-relative), `start_line`, `end_line`, `symbol` (function/class
name or markdown header), `chunk_type`, `language`, `ingested_at`.

## Usage

```bash
pip install -r ingestion/requirements.txt

# With OpenAI embeddings (the course configuration):
OPENAI_API_KEY=sk-... python ingestion/ingest.py

# Without an API key (Chroma's local default embedding function):
python ingestion/ingest.py --provider default
```

Options: `--source` (default: repo root), `--collection` (default:
`code_collection`), `--persist-dir` (default: `./chroma_data`),
`--provider openai|sentence_transformers|default`, `--model`.

The collection records its embedding provider/model in its ChromaDB
metadata, so consumers can re-open it with the matching embedding
function.

## Rebuilding

Re-running the script **adds** chunks (fresh uuid4 IDs each run) — it does
not replace the collection. To rebuild from scratch, delete the persist
directory (or the collection) first:

```bash
rm -rf chroma_data && python ingestion/ingest.py
```
