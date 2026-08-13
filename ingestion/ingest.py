"""Build the Chroma collection for the feedback-app codebase.

Ingests the repository's .py/.md/.txt files (code + docs) into a ChromaDB
collection with the same chunking strategy and metadata schema as the
course code-search app. This ingestion/ directory itself, and course
materials like SPEC.md, are excluded — see IngestionConfig.

Usage:
    python ingestion/ingest.py                       # OpenAI embeddings (needs OPENAI_API_KEY)
    python ingestion/ingest.py --provider default    # local default embeddings (no API key)
    python ingestion/ingest.py --collection my_name --persist-dir ./chroma_data
"""

import argparse
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

from ingestion.chroma_client import (  # noqa: E402
    ChromaClientManager,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
)
from ingestion.ingestion_service import IngestionService  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", default=str(REPO_ROOT),
        help="directory to ingest (default: this repository)",
    )
    parser.add_argument(
        "--collection", default="code_collection",
        help="ChromaDB collection name (default: code_collection)",
    )
    parser.add_argument(
        "--persist-dir", default="./chroma_data",
        help="ChromaDB persist directory (default: ./chroma_data)",
    )
    parser.add_argument(
        "--provider", default=DEFAULT_PROVIDER,
        choices=["openai", "sentence_transformers", "default"],
        help="embedding provider (default: openai)",
    )
    parser.add_argument(
        "--model", default=None,
        help=f"embedding model name (default: {DEFAULT_MODEL} for openai)",
    )
    args = parser.parse_args()

    load_dotenv(REPO_ROOT / ".env")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    model_name = args.model or (
        DEFAULT_MODEL if args.provider == "openai" else args.provider
    )

    chroma = ChromaClientManager(persist_directory=args.persist_dir)
    service = IngestionService(chroma)

    def on_progress(progress):
        if not progress.is_complete:
            print(
                f"[{progress.processed_files}/{progress.total_files}] "
                f"{progress.current_file}  ({progress.total_chunks} chunks so far)"
            )

    progress = service.ingest_directory(
        args.source,
        args.collection,
        provider=args.provider,
        model_name=model_name,
        progress_callback=on_progress,
    )

    print()
    print(f"Collection:   {args.collection} ({args.provider}/{model_name})")
    print(f"Persist dir:  {args.persist_dir}")
    print(f"Files:        {progress.success_count}/{progress.total_files} succeeded")
    print(f"Chunks:       {progress.total_chunks}")
    if progress.failed_files:
        print("Failed files:")
        for failure in progress.failed_files:
            print(f"  - {failure}")
        sys.exit(1)


if __name__ == "__main__":
    main()
