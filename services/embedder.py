"""
embedder.py
───────────
Fast embedding pipeline using sentence-transformers (all-MiniLM-L6-v2).
Optimized for speed and low memory usage.
"""

import os
from typing import Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

# ─── Config ──────────────────────────────────────────────────────────────────
# Using a much lighter and faster model: 80MB vs 440MB for CodeBERT
FAST_MODEL = "all-MiniLM-L6-v2"
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
TOP_K_RESULTS = 5


class CodeEmbedder:
    """
    Embeds code chunks using a fast sentence-transformer model.
    """

    def __init__(self):
        print(f"[Embedder] Using fast model: {FAST_MODEL}")
        
        # ChromaDB persistent client
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
        
        # Use ChromaDB's built-in SentenceTransformer embedding function
        # This is much faster and handles batching/tokenization automatically
        self._embedding_fn = None

    @property
    def embedding_fn(self):
        if self._embedding_fn is None:
            print(f"[Embedder] Loading ONNX embedding model: {FAST_MODEL}")
            try:
                # ONNX version is more robust and faster in restricted environments
                self._embedding_fn = embedding_functions.ONNXMiniLM_L6_V2()
            except Exception as e:
                print(f"[Embedder] Error loading ONNX model: {e}. Falling back to DefaultEmbeddingFunction.")
                self._embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            print("[Embedder] Embedding model loaded.")
        return self._embedding_fn

    def index_chunks(self, chunks: list[dict], collection_name: str):
        """
        Stores chunks in a collection. Chunks should have 'content' and 'metadata'.
        """
        collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

        ids = [chunk['id'] for chunk in chunks]
        documents = [chunk['content'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"[Embedder] Indexed {len(chunks)} chunks into collection '{collection_name}'")

    def search(self, query: str, collection_name: str, top_k: int = TOP_K_RESULTS) -> list[dict]:
        """
        Search for relevant chunks in a collection.
        """
        try:
            collection = self.chroma_client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_fn
            )
        except Exception:
            print(f"[Embedder] Collection '{collection_name}' not found.")
            return []

        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )

        # Reformat results for easy use
        formatted_results = []
        if results['documents']:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted_results

def get_embedder():
    return CodeEmbedder()
