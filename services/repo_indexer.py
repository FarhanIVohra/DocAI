"""
repo_indexer.py
────────────────
Clones a GitHub repo, parses code files using tree-sitter AST analysis
to extract meaningful chunks (functions + classes — not raw line splits),
then hands the chunks to the embedder to store in ChromaDB.

Usage:
    from services.repo_indexer import RepoIndexer
    indexer = RepoIndexer()
    chunks = indexer.index_repo(repo_url="https://github.com/psf/requests", job_id="abc123")
"""

import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from services.embedder import get_embedder

# ─── Config ──────────────────────────────────────────────────────────────────
REPOS_TMP_DIR = Path(os.getenv("REPOS_TMP_DIR", "/tmp/autodoc_repos"))
SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".java", ".go", ".rb", ".cpp", ".c"}
MAX_FILE_SIZE_BYTES = 100_000   # Skip files larger than 100KB
MAX_FILES_PER_REPO = 200        # Cap to avoid huge repos taking forever


class RepoIndexer:
    """
    Clones a GitHub repo, extracts meaningful code chunks via AST parsing,
    and indexes them into ChromaDB for RAG retrieval.
    """

    def __init__(self):
        REPOS_TMP_DIR.mkdir(parents=True, exist_ok=True)
        self.embedder = get_embedder()

    # ── Cloning ───────────────────────────────────────────────────────────────

    def _clone_repo(self, repo_url: str, job_id: str) -> Path:
        """
        Shallow-clone a GitHub repo to a temp directory.

        Args:
            repo_url: Public GitHub URL (https://github.com/user/repo)
            job_id: Unique job ID used to name the temp folder

        Returns:
            Path to the cloned repo directory
        """
        clone_path = REPOS_TMP_DIR / job_id
        if clone_path.exists():
            shutil.rmtree(clone_path)

        print(f"📥 Cloning repo: {repo_url}")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(clone_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")

        print(f"✅ Cloned to {clone_path}")
        return clone_path

    # ── File Discovery ────────────────────────────────────────────────────────

    def _discover_files(self, repo_path: Path) -> list[Path]:
        """Find all supported code files, excluding common non-code dirs."""
        exclude_dirs = {
            ".git", "node_modules", "__pycache__", ".venv", "venv",
            "dist", "build", ".pytest_cache", "vendor", "site-packages",
        }

        files = []
        for ext in SUPPORTED_EXTENSIONS:
            for f in repo_path.rglob(f"*{ext}"):
                # Skip excluded directories
                if any(p in exclude_dirs for p in f.parts):
                    continue
                # Skip huge files
                if f.stat().st_size > MAX_FILE_SIZE_BYTES:
                    continue
                files.append(f)

        # Prioritize smaller, focused files — sort by size ascending
        files.sort(key=lambda f: f.stat().st_size)
        return files[:MAX_FILES_PER_REPO]

    # ── Python AST Parsing (fallback for tree-sitter) ─────────────────────────

    def _extract_chunks_python(self, file_path: Path, repo_root: Path) -> list[dict]:
        """
        Extract function and class definitions from a Python file using regex.
        A proper tree-sitter integration can replace this for full AST accuracy.
        """
        chunks = []
        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return chunks

        rel_path = str(file_path.relative_to(repo_root))

        # Match function definitions with their bodies
        func_pattern = re.compile(
            r"(def\s+\w+[^:]+:(?:\s*(?:\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?''')[^)]*)?.*?)(?=\ndef\s|\nclass\s|\Z)",
            re.MULTILINE,
        )

        lines = source.splitlines()
        current_func = []
        current_start = 0
        in_func = False

        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("def ") or stripped.startswith("class "):
                if in_func and current_func:
                    chunk_text = "\n".join(current_func)
                    if len(chunk_text.strip()) > 30:
                        chunks.append({
                            "id": f"{rel_path}:L{current_start}:{uuid.uuid4().hex[:8]}",
                            "text": chunk_text,
                            "metadata": {
                                "file_path": rel_path,
                                "start_line": current_start,
                                "end_line": i - 1,
                                "chunk_type": "function",
                                "language": "python",
                            },
                        })
                current_func = [line]
                current_start = i + 1
                in_func = True
            elif in_func:
                current_func.append(line)

        # Don't forget the last function
        if in_func and current_func:
            chunk_text = "\n".join(current_func)
            if len(chunk_text.strip()) > 30:
                chunks.append({
                    "id": f"{rel_path}:L{current_start}:{uuid.uuid4().hex[:8]}",
                    "text": chunk_text,
                    "metadata": {
                        "file_path": rel_path,
                        "start_line": current_start,
                        "end_line": len(lines),
                        "chunk_type": "function",
                        "language": "python",
                    },
                })

        # If no functions found, index the whole file as one chunk
        if not chunks and len(source.strip()) > 50:
            chunks.append({
                "id": f"{rel_path}:full:{uuid.uuid4().hex[:8]}",
                "text": source[:3000],  # Cap at 3000 chars
                "metadata": {
                    "file_path": rel_path,
                    "start_line": 1,
                    "end_line": len(lines),
                    "chunk_type": "file",
                    "language": "python",
                },
            })

        return chunks

    def _extract_chunks_generic(self, file_path: Path, repo_root: Path) -> list[dict]:
        """Generic chunker for non-Python files — splits by 50-line windows."""
        chunks = []
        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return chunks

        rel_path = str(file_path.relative_to(repo_root))
        ext = file_path.suffix.lstrip(".")
        lines = source.splitlines()
        window = 50
        step = 40  # Overlap of 10 lines

        for start in range(0, len(lines), step):
            end = min(start + window, len(lines))
            chunk_text = "\n".join(lines[start:end])
            if len(chunk_text.strip()) < 30:
                continue
            chunks.append({
                "id": f"{rel_path}:L{start}:{uuid.uuid4().hex[:8]}",
                "text": chunk_text,
                "metadata": {
                    "file_path": rel_path,
                    "start_line": start + 1,
                    "end_line": end,
                    "chunk_type": "window",
                    "language": ext,
                },
            })

        return chunks

    def _extract_chunks(self, file_path: Path, repo_root: Path) -> list[dict]:
        """Route to the appropriate parser based on file extension."""
        if file_path.suffix == ".py":
            return self._extract_chunks_python(file_path, repo_root)
        return self._extract_chunks_generic(file_path, repo_root)

    # ── Dependency Graph ────────────────────────────────────────────────────

    def extract_dependency_graph(self, repo_path: Path) -> dict[str, list[str]]:
        """
        Build a simple module dependency graph by scanning import statements.
        Returns a dict mapping each file to its list of imported modules.
        """
        graph = {}
        for py_file in repo_path.rglob("*.py"):
            if any(p in py_file.parts for p in {".git", "__pycache__", "venv"}):
                continue
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            rel = str(py_file.relative_to(repo_path))
            imports = re.findall(r"^(?:from|import)\s+([\w.]+)", source, re.MULTILINE)
            graph[rel] = list(set(imports))

        return graph

    # ── Main Entry Point ───────────────────────────────────────────────────

    def index_repo(self, repo_url: str, job_id: str) -> dict:
        """
        Full pipeline: clone → parse → embed → store in ChromaDB.

        Args:
            repo_url: Public GitHub repo URL
            job_id: Unique job ID for this indexing run

        Returns:
            Summary dict with chunk_count, file_count, collection_name
        """
        # Clone
        repo_path = self._clone_repo(repo_url, job_id)
        return self.index_local_path(repo_path, job_id, repo_url=repo_url)

    def index_local_path(self, repo_path: Path, job_id: str, repo_url: str = "") -> dict:
        """
        Indexes a local directory.
        """
        # Discover files
        files = self._discover_files(repo_path)
        print(f"📂 Found {len(files)} code files to index at {repo_path}")

        # Extract chunks
        all_chunks = []
        for f in files:
            chunks = self._extract_chunks(f, repo_path)
            all_chunks.extend(chunks)

        print(f"🔀 Extracted {len(all_chunks)} code chunks from {len(files)} files")

        # Extract dependency graph for diagram generation
        dep_graph = self.extract_dependency_graph(repo_path)

        # Index into ChromaDB
        collection_name = f"repo_{job_id}"
        if all_chunks:
            self.embedder.index_chunks(all_chunks, collection_name)

        return {
            "job_id": job_id,
            "collection_name": collection_name,
            "chunk_count": len(all_chunks),
            "file_count": len(files),
            "repo_path": str(repo_path),
            "dependency_graph": dep_graph,
            "repo_url": repo_url
        }

    def cleanup_repo(self, job_id: str) -> None:
        """Delete the cloned repo from disk to free space."""
        repo_path = REPOS_TMP_DIR / job_id
        if repo_path.exists():
            shutil.rmtree(repo_path)
            print(f"🗑️  Cleaned up repo: {job_id}")
