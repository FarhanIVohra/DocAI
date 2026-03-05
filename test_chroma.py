import chromadb
from chromadb.config import Settings
import os

CHROMA_PERSIST_DIR = "./data/chroma_db"
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

print(f"Initializing ChromaDB client at {CHROMA_PERSIST_DIR}...")
try:
    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),
    )
    print("ChromaDB client initialized.")
except Exception as e:
    import traceback
    traceback.print_exc()
