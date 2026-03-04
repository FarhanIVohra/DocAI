"""
chat_agent.py
─────────────
Conversational RAG agent that answers questions about a repo with
memory of the last few turns. Wraps rag_service.py with session
management and clean response formatting.

Usage:
    from services.chat_agent import ChatAgent
    agent = ChatAgent(job_id="abc123")
    result = agent.chat("How does authentication work?")
    result = agent.chat("What about token refresh?")  # Remembers context
"""

from dataclasses import dataclass, field
from services.rag_service import RAGService

MAX_HISTORY_TURNS = 6   # Keep last 3 exchanges (user + assistant each)


@dataclass
class ChatSession:
    """Represents a single conversation session with a repo."""
    job_id: str
    history: list[dict] = field(default_factory=list)

    def add_turn(self, role: str, content: str) -> None:
        """Add a message to history, pruning if too long."""
        self.history.append({"role": role, "content": content})
        # Keep only the last MAX_HISTORY_TURNS messages
        if len(self.history) > MAX_HISTORY_TURNS:
            self.history = self.history[-MAX_HISTORY_TURNS:]

    def clear(self) -> None:
        self.history.clear()


class ChatAgent:
    """
    Stateful conversational agent for "Chat with your Repo."
    Each instance manages one chat session for one indexed repo.
    """

    def __init__(self, job_id: str):
        """
        Args:
            job_id: Job ID of the indexed repo to chat about
        """
        self.session = ChatSession(job_id=job_id)
        self.rag = RAGService()

    def chat(self, user_message: str) -> dict:
        """
        Process a user message and return a grounded answer.

        Args:
            user_message: The user's question about the repo

        Returns:
            Dict with:
                - answer: str — the AI's response
                - sources: List[str] — source file references
                - turn: int — conversation turn number
        """
        # Add user message to history
        self.session.add_turn("user", user_message)

        # Get grounded answer from RAG with conversation history
        result = self.rag.query_with_history(
            question=user_message,
            job_id=self.session.job_id,
            history=self.session.history[:-1],  # Exclude current message
        )

        answer = result["answer"]
        sources = result["sources"]

        # Add assistant response to history
        self.session.add_turn("assistant", answer)

        return {
            "answer": answer,
            "sources": sources,
            "turn": len(self.session.history) // 2,
            "chunks_used": result.get("chunks_used", 0),
        }

    def reset(self) -> None:
        """Clear conversation history."""
        self.session.clear()

    @property
    def history(self) -> list[dict]:
        return self.session.history


# ─── Session Manager (for API server with multiple concurrent users) ──────────

class ChatSessionManager:
    """
    Manages multiple ChatAgent instances keyed by session_id.
    Used by the FastAPI server to maintain per-user sessions.
    """

    def __init__(self):
        self._sessions: dict[str, ChatAgent] = {}

    def get_or_create(self, session_id: str, job_id: str) -> ChatAgent:
        """Get existing session or create a new one."""
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatAgent(job_id=job_id)
        return self._sessions[session_id]

    def delete(self, session_id: str) -> None:
        """Remove a session (cleanup on disconnect)."""
        self._sessions.pop(session_id, None)

    def chat(self, session_id: str, job_id: str, message: str) -> dict:
        """Convenience method — get/create session and send a message."""
        agent = self.get_or_create(session_id, job_id)
        return agent.chat(message)


# ─── Singleton ────────────────────────────────────────────────────────────────
_session_manager: ChatSessionManager | None = None


def get_session_manager() -> ChatSessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = ChatSessionManager()
    return _session_manager
