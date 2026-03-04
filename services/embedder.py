"""
embedder.py
───────────
Code-aware embedding pipeline using microsoft/codebert-base.
Embeds code chunks and stores/retrieves them in ChromaDB.

Usage:
    from services.embedder import CodeEmbedder
    embedder = CodeEmbedder()
    embedder.index_chunks(chunks, collection_name="my_repo_jobid")
    results = embedder.search("how does auth work?", collection_name="my_repo_jobid")
"""

import os
from typing import Optional

import chromadb
import torch
from chromadb.config import Settings
from transformers import AutoModel, AutoTokenizer

# ─── Config ──────────────────────────────────────────────────────────────────
CODEBERT_MODEL = "microsoft/codebert-base"
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
EMBEDDING_DIM = 768         # CodeBERT output dimension
MAX_CHUNK_TOKENS = 512       # Max tokens per chunk for CodeBERT
TOP_K_RESULTS = 5            # Default number of search results


class CodeEmbedder:
    """
    Embeds code chunks using CodeBERT and stores them in ChromaDB.
    Supports per-repo collections so different repos stay isolated.
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"📡 CodeEmbedder using device: {self.device}")

        self._model: Optional[AutoModel] = None
        self._tokenizer: Optional[AutoTokenizer] = None

        # ChromaDB persistent client
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )

    def _load_model(self):
        """Lazy-load CodeBERT (only when first embedding is needed)."""
        if self._model is None:
            print(f"📦 Loading CodeBERT: {CODEBERT_MODEL}")
            self._tokenizer = AutoTokenizer.from_pretrained(CODEBERT_MODEL)
            self._model = AutoModel.from_pretrained(CODEBERT_MODEL).to(self.device)
            self._model.eval()
            print("✅ CodeBERT loaded.")

    def _embed_text(self, text: str) -> list[float]:
        """
        Embed a single text string using CodeBERT.
        Returns a 768-dimensional vector.
        """
        self._load_model()

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_CHUNK_TOKENS,
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            outputs = self._model(**inputs)
            # Use [CLS] token embedding as the representation
            embedding = outputs.last_hidden_state[:, 0, :].squeeze()

        return embedding.cpu().tolist()

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts in one batch for efficiency."""
        self._load_model()

        inputs = self._tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_CHUNK_TOKENS,
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            outputs = self._model(**inputs)
            embeddings = outputs.last_hidden_state[:, 0, :].squeeze()

        if len(texts) == 1:
            embeddings = embeddings.unsqueeze(0)

        return embeddings.cpu().tolist()

    def get_or_create_collection(self, collection_name: str):
        """Get or create a ChromaDB collection for a repo job."""
        return self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def index_chunks(
        self,
        chunks: list[dict],
        collection_name: str,
        batch_size: int = 32,
    ) -> None:
        """
        Index code chunks into ChromaDB.

        Args:
            chunks: List of dicts with keys:
                    - id: unique string ID
                    - text: code text to embed
                    - metadata: dict with file_path, start_line, end_line, chunk_type
            collection_name: ChromaDB collection name (use job_id for isolation)
            batch_size: Number of chunks to embed at once
        """
        collection = self.get_or_create_collection(collection_name)
        total = len(chunks)
        print(f"🔢 Indexing {total} chunks into collection '{collection_name}'...")

        for i in range(0, total, batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c["text"] for c in batch]
            ids = [c["id"] for c in batch]
            metadatas = [c.get("metadata", {}) for c in batch]
            documents = texts

            embeddings = self._embed_batch(texts)

            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

            done = min(i + batch_size, total)
            print(f"  ✅ Indexed {done}/{total} chunks", end="\r")

        print(f"\n✅ Indexing complete — {total} chunks in '{collection_name}'")

    def search(
        self,
        query: str,
        collection_name: str,
        top_k: int = TOP_K_RESULTS,
    ) -> list[dict]:
        """
        Search the vector store for code chunks relevant to a query.

        Args:
            query: Natural language question or code snippet
            collection_name: ChromaDB collection to search
            top_k: Number of results to return

        Returns:
            List of dicts with: text, metadata, distance
        """
        collection = self.get_or_create_collection(collection_name)
        query_embedding = self._embed_text(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            output.append({"text": doc, "metadata": meta, "distance": dist})

        return output

    def delete_collection(self, collection_name: str) -> None:
        """Remove a repo's collection from ChromaDB (cleanup)."""
        try:
            self.chroma_client.delete_collection(collection_name)
            print(f"🗑️  Deleted collection: {collection_name}")
        except Exception:
            pass  # Collection may not exist


# ─── Singleton ───────────────────────────────────────────────────────────────
_embedder_instance: Optional[CodeEmbedder] = None


def get_embedder() -> CodeEmbedder:
    """Get or create the singleton CodeEmbedder instance."""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = CodeEmbedder()
    return _embedder_instance
