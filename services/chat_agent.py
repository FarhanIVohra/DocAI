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
from services.llm_service import get_llm
import asyncio

MAX_HISTORY_TURNS = 6   # Keep last 3 exchanges (user + assistant each)


@dataclass
class ChatSession:
    """Represents a single conversation session with a repo."""
    job_id: str
    history: list[dict] = field(default_factory=list)
    running_summary: str = ""

    def add_turn(self, role: str, content: str) -> None:
        """Add a message to history, scheduling a background summary if too long."""
        self.history.append({"role": role, "content": content})
        
        # When history exceeds our max turns, we need to compress the oldest exchange
        if len(self.history) > MAX_HISTORY_TURNS + 2:  # Allow it to go +2 before trimming
            # Extract the oldest exchange (user + assistant) that we're about to drop
            oldest_turns = self.history[:2]
            self.history = self.history[2:]
            
            # Fire and forget background task to update the running summary
            # We use a thread because ChatAgent runs in a synchronous FastAPI endpoint
            import threading
            threading.Thread(target=self._run_summary_sync, args=(oldest_turns,), daemon=True).start()

    def _run_summary_sync(self, dropped_turns: list[dict]) -> None:
        """Synchronous wrapper to run the async update."""
        asyncio.run(self._update_summary(dropped_turns))

    async def _update_summary(self, dropped_turns: list[dict]) -> None:
        """Background task to compress dropped turns into the running summary."""
        try:
            llm = get_llm()
            dropped_text = "\n".join([f"{t['role'].capitalize()}: {t['content']}" for t in dropped_turns])
            
            prompt = (
                f"You are an AI assistant tasked with maintaining a concise running summary of a conversation.\n"
                f"Previous Summary:\n{self.running_summary or 'None'}\n\n"
                f"New conversation turns to incorporate:\n{dropped_text}\n\n"
                f"Write a brief, updated summary that captures the core context, intent, and any important code references. Keep it very concise."
            )
            
            new_summary = await asyncio.to_thread(llm.generate, prompt, "Summarizer", max_tokens=200)
            self.running_summary = new_summary.strip()
            print(f"DEBUG: Updated Running Summary: {self.running_summary[:100]}...")
            
        except Exception as e:
            print(f"Error generating chat summary: {e}")

    def clear(self) -> None:
        self.history.clear()
        self.running_summary = ""


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

        # Build context string with history and the running summary
        history_for_rag = list(self.session.history[:-1])
        if self.session.running_summary:
            # Inject the running summary as a seamless 'system' context block to guide RAG
            summary_msg = f"[Prior Conversation Summary: {self.session.running_summary}]"
            history_for_rag.insert(0, {"role": "system", "content": summary_msg})

        # Get grounded answer from RAG with conversation history
        result = self.rag.query_with_history(
            question=user_message,
            job_id=self.session.job_id,
            history=history_for_rag,  # Exclude current message but include summary
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
