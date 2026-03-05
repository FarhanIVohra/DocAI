"""
doc_generator.py
─────────────────
Orchestrates all 5 documentation output types using the LLM + RAG services.
Called by the FastAPI backend whenever a user requests a doc type.

Usage:
    from services.doc_generator import DocGenerator
    gen = DocGenerator()
    readme = gen.generate("readme", job_id="abc123", repo_meta={...})
    api_docs = gen.generate("api-docs", job_id="abc123", repo_meta={...})
"""

import json
import re
from pathlib import Path

from services.embedder import get_embedder
from services.llm_service import get_llm

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

DOC_TYPE_CONFIG = {
    "readme": {
        "prompt_name": "readme",
        "max_tokens": 1024,
        "description": "Full README.md",
    },
    "api-docs": {
        "prompt_name": "api_doc",
        "max_tokens": 2048,
        "description": "API reference documentation",
    },
    "diagram": {
        "prompt_name": "diagram",
        "max_tokens": 512,
        "description": "Mermaid.js architecture diagram",
    },
    "changelog": {
        "prompt_name": "changelog",
        "max_tokens": 1024,
        "description": "CHANGELOG.md from git history",
    },
    "onboarding": {
        "prompt_name": "onboarding",
        "max_tokens": 1024,
        "description": "New contributor onboarding guide",
    },
    "audit": {
        "prompt_name": "audit",
        "max_tokens": 2048,
        "description": "Security & Code Health Audit",
    },
    "code-review": {
        "prompt_name": "code_review",
        "max_tokens": 2048,
        "description": "Technical Debt & Security Audit",
    },
}


class DocGenerator:
    """
    Generates the 5 AutoDoc AI documentation outputs for an indexed repo.
    Each method fetches relevant context from ChromaDB and calls the LLM.
    """

    def __init__(self):
        self.llm = get_llm()
        self.embedder = get_embedder()

    def _load_prompt(self, prompt_name: str) -> str:
        path = PROMPTS_DIR / f"{prompt_name}_prompt.txt"
        return path.read_text(encoding="utf-8")

    def _get_top_chunks(self, job_id: str, query: str, top_k: int = 8) -> str:
        """Retrieve top-k relevant code chunks as a text block."""
        collection_name = f"repo_{job_id}"
        chunks = self.embedder.search(query, collection_name, top_k=top_k)
        if not chunks:
            return "(No code context available)"

        parts = []
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            file_path = meta.get("file_path", "?")
            # Embedder stores content in 'content', but original code used 'text'
            text = chunk.get("content", chunk.get("text", ""))
            parts.append(f"### {file_path}\n```\n{text[:800]}\n```")

        return "\n\n".join(parts)

    # ─── README ───────────────────────────────────────────────────────────────

    def generate_readme(self, job_id: str, repo_meta: dict) -> str:
        """
        Generate a full README.md for the repository.

        Args:
            job_id: Indexed repo job ID
            repo_meta: Dict with repo_url, repo_name, file_count, dep_graph keys

        Returns:
            README.md content as a Markdown string
        """
        context = self._get_top_chunks(
            job_id,
            "main entry point features overview setup installation",
            top_k=10,
        )

        repo_name = repo_meta.get("repo_name", "this project")
        repo_url = repo_meta.get("repo_url", "")

        user_message = (
            f"Repository: {repo_name}\n"
            f"GitHub URL: {repo_url}\n"
            f"Files: {repo_meta.get('file_count', '?')} code files\n\n"
            f"Here is a sample of the codebase:\n\n{context}"
        )

        system = self._load_prompt("readme")
        return self.llm.generate(user_message, system, max_tokens=1200)

    # ─── API DOCS ─────────────────────────────────────────────────────────────

    def generate_api_docs(self, job_id: str, repo_meta: dict) -> str:
        """
        Generate API reference documentation for all public functions/classes.

        Returns:
            Markdown API reference string
        """
        context = self._get_top_chunks(
            job_id,
            "public functions classes methods parameters return types API",
            top_k=12,
        )

        user_message = (
            f"Repository: {repo_meta.get('repo_name', 'Unknown')}\n\n"
            f"Code to document:\n\n{context}"
        )

        system = self._load_prompt("api_doc")
        return self.llm.generate(user_message, system, max_tokens=2000)

    # ─── ARCHITECTURE DIAGRAM ─────────────────────────────────────────────────

    def generate_diagram(self, job_id: str, repo_meta: dict) -> str:
        """
        Generate a Mermaid.js architecture diagram.

        Returns:
            Mermaid diagram string (ready to render)
        """
        # Use the dependency graph from the indexing step
        dep_graph = repo_meta.get("dependency_graph", {})

        if dep_graph:
            # Format the dependency graph as text for the LLM
            dep_text = "\n".join(
                f"{src} → {', '.join(deps[:5])}"  # Cap deps to avoid huge prompts
                for src, deps in list(dep_graph.items())[:30]
                if deps
            )
            context = f"Module dependency graph:\n{dep_text}"
        else:
            # Fall back to RAG
            context = self._get_top_chunks(
                job_id, "import from module architecture structure", top_k=8
            )

        user_message = (
            f"Repository: {repo_meta.get('repo_name', 'Unknown')}\n\n"
            f"{context}"
        )

        system = self._load_prompt("diagram")
        raw = self.llm.generate(user_message, system, max_tokens=600)

        # Ensure output is a valid mermaid block
        if "```mermaid" not in raw:
            raw = f"```mermaid\n{raw}\n```"

        return raw

    # ─── CHANGELOG ────────────────────────────────────────────────────────────

    def generate_changelog(self, job_id: str, repo_meta: dict) -> str:
        """
        Generate CHANGELOG.md from git commit history.

        Args:
            job_id: Job ID
            repo_meta: Must include 'commits' key with list of commit message strings

        Returns:
            CHANGELOG.md content as Markdown
        """
        commits = repo_meta.get("commits", [])

        if not commits:
            return "# Changelog\n\n*No git history available for this repository.*"

        # Format commits as a numbered list for the LLM
        commits_text = "\n".join(
            f"{i+1}. {msg}" for i, msg in enumerate(commits[:60])
        )

        user_message = (
            f"Repository: {repo_meta.get('repo_name', 'Unknown')}\n\n"
            f"Git commit messages (most recent first):\n{commits_text}"
        )

        system = self._load_prompt("changelog")
        return self.llm.generate(user_message, system, max_tokens=1200)

    # ─── ONBOARDING GUIDE ─────────────────────────────────────────────────────

    def generate_onboarding(self, job_id: str, repo_meta: dict) -> str:
        """
        Generate a "New Contributor Guide" for new developers.

        Returns:
            Onboarding guide as Markdown
        """
        context = self._get_top_chunks(
            job_id,
            "main setup configuration environment tests structure architecture",
            top_k=10,
        )

        file_tree = repo_meta.get("file_tree", "(not available)")

        user_message = (
            f"Repository: {repo_meta.get('repo_name', 'Unknown')}\n"
            f"GitHub URL: {repo_meta.get('repo_url', '')}\n\n"
            f"File structure (top-level):\n{file_tree}\n\n"
            f"Key code samples:\n\n{context}"
        )

        system = self._load_prompt("onboarding")
        return self.llm.generate(user_message, system, max_tokens=1200)

    # ─── SECURITY AUDIT ───────────────────────────────────────────────────────

    def generate_audit(self, job_id: str, repo_meta: dict) -> str:
        """
        Generate a security and code health audit report.

        Returns:
            Audit report as Markdown
        """
        context = self._get_top_chunks(
            job_id,
            "vulnerability security secret hardcoded thread-safety complexity",
            top_k=15,
        )

        user_message = (
            f"Repository: {repo_meta.get('repo_name', 'Unknown')}\n\n"
            f"Please audit the following code context:\n\n{context}"
        )

        system = self._load_prompt("audit")
        return self.llm.generate(user_message, system, max_tokens=2000)

    # ─── CODE REVIEW & AUDIT ───────────────────────────────────────────────

    def generate_code_review(self, job_id: str, repo_meta: dict) -> str:
        """
        Generate a technical debt and security audit report.

        Returns:
            Markdown audit report
        """
        context = self._get_top_chunks(
            job_id,
            "vulnerability security performance bottleneck debt complexity logic",
            top_k=15,
        )

        user_message = (
            f"Repository: {repo_meta.get('repo_name', 'Unknown')}\n\n"
            f"Analyzing these code segments for health and security:\n\n{context}"
        )

        system = self._load_prompt("code_review")
        return self.llm.generate(user_message, system, max_tokens=2000)

    # ─── Unified Entry Point ──────────────────────────────────────────────────

    def generate(self, doc_type: str, job_id: str, repo_meta: dict) -> str:
        """
        Generate any of the 5 doc types.

        Args:
            doc_type: One of: readme, api-docs, diagram, changelog, onboarding
            job_id: Indexed repo job ID
            repo_meta: Metadata dict from indexing step

        Returns:
            Generated documentation as a Markdown string

        Raises:
            ValueError: If doc_type is not recognized
        """
        dispatch = {
            "readme": self.generate_readme,
            "api-docs": self.generate_api_docs,
            "diagram": self.generate_diagram,
            "changelog": self.generate_changelog,
            "onboarding": self.generate_onboarding,
            "audit": self.generate_audit,
            "code-review": self.generate_code_review,
        }

        if doc_type not in dispatch:
            raise ValueError(
                f"Unknown doc_type: '{doc_type}'. "
                f"Must be one of: {list(dispatch.keys())}"
            )

        print(f"📝 Generating {DOC_TYPE_CONFIG[doc_type]['description']}...")
        result = dispatch[doc_type](job_id, repo_meta)
        print(f"✅ Done generating {doc_type}")
        return result
