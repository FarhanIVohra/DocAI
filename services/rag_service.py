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
MAX_RETRIEVED_CHUNKS = 30
MAX_CONTEXT_CHUNKS = 8
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

    def _rank_chunks(self, query: str, chunks: list[dict]) -> list[dict]:
        """
        Re-rank retrieved chunks using simple Term Frequency / Keyword Density 
        combined with original vector distance (if semantic search).
        """
        query_terms = set(word.lower() for word in query.replace('"', '').split() if len(word) > 2)
        if not query_terms:
            return chunks

        scored_chunks = []
        for chunk in chunks:
            text = chunk.get("content", "").lower()
            
            # 1. Keyword overlap score (number of unique query terms present)
            overlap = sum(1 for term in query_terms if term in text)
            
            # 2. Keyword frequency score (how many times they appear)
            frequency = sum(text.count(term) for term in query_terms)
            
            # Combine scores (simple heuristic)
            # Original distance is lower-is-better (for cosine/L2). 
            # We invert it roughly, assuming standard ranges, or simply sort by our new score if it's high enough.
            base_distance_penalty = chunk.get("distance", 1.0) or 1.0
            
            # Final score: Higher is better
            score = (overlap * 5.0) + (frequency * 1.0) - (base_distance_penalty * 10.0)
            
            scored_chunks.append((score, chunk))
            
        # Sort descending by score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for c in scored_chunks]

    def query(self, question: str, job_id: str, search_type: str = "SEMANTIC") -> dict:
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
        if search_type == "KEYWORD":
            # Keyword search ignores vector embeddings and looks for exact strings
            print(f"DEBUG: Executing KEYWORD search for: {question}")
            chunks = self.embedder.keyword_search(
                query=question,
                collection_name=collection_name,
                top_k=MAX_CONTEXT_CHUNKS
            )
        else:
            # Semantic search fetches many candidates then re-ranks
            print(f"DEBUG: Executing SEMANTIC search for: {question}")
            chunks = self.embedder.search(
                query=question,
                collection_name=collection_name,
                top_k=MAX_RETRIEVED_CHUNKS,
            )
            # Re-rank based on keyword overlap
            if chunks:
                chunks = self._rank_chunks(question, chunks)[:MAX_CONTEXT_CHUNKS]

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
                f"Given the following conversation history and a follow-up user message, "
                f"rephrase the follow-up message to be a standalone search query for a codebase.\n"
                f"Crucially, determine the SEARCH_TYPE. If the user is asking for a specific function, variable, "
                f"or exact string (e.g., 'Where is auth_token defined?'), output KEYWORD.\n"
                f"If the user is asking a conceptual question (e.g., 'How does the auth system work?'), output SEMANTIC.\n\n"
                f"IMPORTANT: If the type is KEYWORD, the 'query' field MUST contain ONLY the exact substring, class name, or variable name to search for (e.g., just 'auth_token' or 'HTTPException'), with NO conversational words.\n"
                f"If the type is SEMANTIC, the 'query' should be a natural language question.\n\n"
                f"History:\n{history_text}\n\n"
                f"Follow-up: {question}\n\n"
                f"Format your response EXACTLY as a JSON object with 'query' and 'type' keys. Example:\n"
                f'{{"query": "HTTPException", "type": "KEYWORD"}}'
            )
            try:
                # Use a small max_tokens for the query rewrite
                raw_response = self.llm.generate(standalone_prompt, "You are a helpful assistant that rephrases questions for search. Output ONLY valid JSON.", max_tokens=150)
                print(f"DEBUG: Raw LLM Router Response: {raw_response}")
                import json
                import re
                
                # Extract JSON if markdown wrapped
                json_str = raw_response.strip()
                match = re.search(r'\{.*\}', json_str, re.DOTALL)
                if match:
                    json_str = match.group(0)
                
                data = json.loads(json_str)
                search_query = data.get("query", question)
                search_type = data.get("type", "SEMANTIC").upper()
                
                if search_type not in ["KEYWORD", "SEMANTIC"]:
                    search_type = "SEMANTIC"
                    
                print(f"DEBUG: Query Router - Type: {search_type}, Query: {search_query}")
                return self.query(search_query, job_id, search_type=search_type)
                
            except Exception as e:
                print(f"DEBUG: Query Router failed ({e}), falling back to simple concatenation")
                # Fallback to simple concatenation if rewrite/JSON fails
                question = f"{history_text}\n\n{question}"
                return self.query(question, job_id, search_type="SEMANTIC")

        return self.query(question, job_id, search_type="SEMANTIC")
