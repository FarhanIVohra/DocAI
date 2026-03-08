import asyncio
from services.chat_agent import get_session_manager

async def test_memory():
    job_id = "test-id"
    session_id = "test_user_1"
    manager = get_session_manager()
    
    questions = [
        "Hi, I'm looking at process_item.",
        "What type of argument does it take?",
        "What does it do with the item?",
        "Is there a return value?",
        "Okay, what was the name of the function I asked about initially?"
    ]
    
    print("Starting conversation...")
    for i, q in enumerate(questions):
        print(f"\n--- Turn {i+1} ---")
        print(f"User: {q}")
        
        # chat() is synchronous in ChatSessionManager but it schedules async tasks
        # We need to run it in an event loop environment
        result = await asyncio.to_thread(manager.chat, session_id, job_id, q)
        
        print(f"AI: {result['answer'][:150]}...")
        
        # Give the background summarizer a moment to run after turn 4
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_memory())
