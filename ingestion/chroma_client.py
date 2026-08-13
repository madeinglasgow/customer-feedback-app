"""ChromaDB client management.

Ported from the course code-search app (lucasrct/app,
services/chroma_client.py), decoupled from that app's config module: the
persist directory is passed in (or read from CHROMA_PERSIST_DIR).
"""

import os
from typing import Optional, Any, Dict

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "text-embedding-3-small"
DEFAULT_PERSIST_DIR = "./chroma_data"


class ChromaClientManager:
    """Manager for a ChromaDB PersistentClient connection.

    Each collection stores its embedding provider and model name in its
    ChromaDB metadata so the right embedding function is always used,
    regardless of which process or session opens the collection later.
    """

    def __init__(self, persist_directory: Optional[str] = None):
        self._persist_directory = (
            persist_directory
            or os.getenv("CHROMA_PERSIST_DIR", DEFAULT_PERSIST_DIR)
        )
        self._client = chromadb.PersistentClient(path=self._persist_directory)
        self._ef_cache: Dict[str, Any] = {}

    # ── Embedding functions ────────────────────────────────────────────────

    def get_embedding_function(self, provider: str, model_name: str):
        """Return a cached embedding function for the given provider/model."""
        key = f"{provider}:{model_name}"
        if key not in self._ef_cache:
            if provider == "sentence_transformers":
                from chromadb.utils.embedding_functions import (
                    SentenceTransformerEmbeddingFunction,
                )
                self._ef_cache[key] = SentenceTransformerEmbeddingFunction(
                    model_name=model_name
                )
            elif provider == "default":
                from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
                self._ef_cache[key] = DefaultEmbeddingFunction()
            else:  # openai
                self._ef_cache[key] = OpenAIEmbeddingFunction(
                    model_name=model_name,
                    api_key=os.getenv("OPENAI_API_KEY"),
                    api_key_env_var="OPENAI_API_KEY",
                )
        return self._ef_cache[key]

    @property
    def client(self) -> chromadb.ClientAPI:
        return self._client

    # ── Collection access ──────────────────────────────────────────────────

    def get_collection(
        self,
        name: str,
        provider: str = DEFAULT_PROVIDER,
        model_name: str = DEFAULT_MODEL,
    ) -> chromadb.Collection:
        """Get or create a collection, persisting its embedding spec in metadata."""
        ef = self.get_embedding_function(provider, model_name)
        return self._client.get_or_create_collection(
            name=name,
            embedding_function=ef,
            metadata={
                "embedding_provider": provider,
                "embedding_model": model_name,
            },
        )

    def get_existing_collection(self, name: str) -> Optional[chromadb.Collection]:
        """Get an existing collection using the embedding function from its metadata."""
        try:
            # First call — no EF needed, just to read stored metadata
            raw = self._client.get_collection(name)
            meta = raw.metadata or {}
            provider = meta.get("embedding_provider")
            model_name = meta.get("embedding_model")
            if provider and model_name:
                ef = self.get_embedding_function(provider, model_name)
            else:
                from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
                ef = DefaultEmbeddingFunction()
            # Second call — with the right EF attached
            return self._client.get_collection(name, embedding_function=ef)
        except Exception:
            return None

    def list_collections(self) -> list:
        return self._client.list_collections()

    def delete_collection(self, name: str) -> bool:
        try:
            self._client.delete_collection(name)
            return True
        except Exception:
            return False

    def heartbeat(self) -> int:
        return self._client.heartbeat()
