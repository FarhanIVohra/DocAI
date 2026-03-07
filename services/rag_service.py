"""
rag_service.py
──────────────
LangChain RAG pipeline that retrieves relevant code chunks from ChromaDB
and feeds them to the Gradient AI LLM to answer questions about a repo.

Usage:
    from services.rag_service import RAGService
    rag = RAGService()
    result = rag.query("How does the auth module work?", job_id="abc123")
    print(result["answer"])
    print(result["sources"])
"""

from pathlib import Path

from services.embedder import get_embedder
from services.llm_service import get_llm

CHAT_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "chat_prompt.txt"
MAX_CONTEXT_CHUNKS = 10
MAX_CONTEXT_CHARS = 3000   # Cap total context to avoid exceeding model context window


class RAGService:
    """
    Retrieval-Augmented Generation over an indexed GitHub repository.
    Uses ChromaDB for retrieval and Gradient AI LLM for generation.
    """

    def __init__(self):
        self.embedder = get_embedder()
        self.llm = get_llm()
        self._system_prompt = CHAT_PROMPT_PATH.read_text(encoding="utf-8")

    def _build_context(self, chunks: list[dict]) -> str:
        """Format retrieved chunks into a context block for the LLM."""
        parts = []
        total_chars = 0

        for chunk in chunks:
            meta = chunk.get("metadata", {})
            file_path = meta.get("file_path", "unknown")
            start_line = meta.get("start_line", "?")
            # Embedder stores content in 'content', but original code used 'text'
            text = chunk.get("content", chunk.get("text", ""))

            entry = f"### {file_path} (line {start_line})\n```\n{text}\n```\n"

            if total_chars + len(entry) > MAX_CONTEXT_CHARS:
                break

            parts.append(entry)
            total_chars += len(entry)

        return "\n".join(parts)

    def _extract_sources(self, chunks: list[dict]) -> list[str]:
        """Extract source references from retrieved chunks."""
        sources = []
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            file_path = meta.get("file_path", "unknown")
            start_line = meta.get("start_line", "?")
            end_line = meta.get("end_line", "?")
            sources.append(f"{file_path}:L{start_line}-{end_line}")
        return sources

    def query(self, question: str, job_id: str) -> dict:
        """
        Answer a question about a repository using RAG.

        Args:
            question: Natural language question about the codebase
            job_id: Job ID of the indexed repo (used to find ChromaDB collection)

        Returns:
            Dict with:
                - answer: LLM-generated answer string
                - sources: List of source file references
                - chunks_used: Number of context chunks retrieved
        """
        collection_name = f"repo_{job_id}"

        # Step 1: Retrieve relevant code chunks
        chunks = self.embedder.search(
            query=question,
            collection_name=collection_name,
            top_k=MAX_CONTEXT_CHUNKS,
        )

        if not chunks:
            return {
                "answer": (
                    "I couldn't find relevant code for this question. "
                    "The repository may not be indexed yet, or this topic "
                    "may not be covered in the codebase."
                ),
                "sources": [],
                "chunks_used": 0,
            }

        # Step 2: Build context from chunks
        context = self._build_context(chunks)
        sources = self._extract_sources(chunks)

        # Step 3: Build the user message with context
        user_message = (
            f"Here is relevant code from the repository:\n\n"
            f"{context}\n\n"
            f"Question: {question}"
        )

        # Step 4: Generate answer using Gradient AI LLM
        answer = self.llm.generate(
            user_message=user_message,
            system_prompt=self._system_prompt,
            max_tokens=600,
        )

        return {
            "answer": answer,
            "sources": sources,
            "chunks_used": len(chunks),
        }

    def query_with_history(
        self,
        question: str,
        job_id: str,
        history: list[dict] | None = None,
    ) -> dict:
        """
        Answer a question with conversational context (last N turns).

        Args:
            question: Current user question
            job_id: Indexed repo job ID
            history: List of previous turns [{"role": "user"|"assistant", "content": str}]

        Returns:
            Same as query() but answer considers conversation history
        """
        if history is None:
            history = []

        # Incorporate history into the question for better context retrieval
        # CRITICAL: Strip "Sources" from history to avoid biasing search towards same files
        history_text = ""
        if history:
            recent = history[-4:]  # Last 2 exchanges
            cleaned_history = []
            for h in recent:
                content = h['content']
                if h['role'] == 'assistant':
                    # Strip everything from "**Sources:**" onwards
                    if "**Sources:**" in content:
                        content = content.split("**Sources:**")[0].strip()
                cleaned_history.append(f"{'User' if h['role'] == 'user' else 'Assistant'}: {content}")
            
            history_text = "\n".join(cleaned_history)
            
            # Use LLM to generate a standalone search query if history exists
            # This is "Query Rewriting" to ensure the search is focused
            standalone_prompt = (
                f"Given the following conversation history and a follow-up question, "
                f"rephrase the follow-up question to be a standalone search query for a codebase.\n\n"
                f"History:\n{history_text}\n\n"
                f"Follow-up: {question}\n\n"
                f"Standalone Query:"
            )
            try:
                # Use a small max_tokens for the query rewrite
                search_query = self.llm.generate(standalone_prompt, "You are a helpful assistant that rephrases questions for search.", max_tokens=100)
                question = search_query.strip()
                print(f"DEBUG: Rewritten search query: {question}")
            except Exception:
                # Fallback to simple concatenation if rewrite fails
                question = f"{history_text}\n\n{question}"

        return self.query(question, job_id)
