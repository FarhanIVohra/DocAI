from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.schemas import chat_schema as schemas
from backend.database import get_db
from backend.services.ai_client import ai_client

router = APIRouter()

@router.post("/message", response_model=schemas.ChatMessageResponse)
async def post_message(request: schemas.ChatMessageRequest, db: Session = Depends(get_db)):
    try:
        ai_response = await ai_client.chat(str(request.job_id), request.message)
        import uuid
        import datetime
        return {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": ai_response['answer'],
            "sources": ai_response.get('sources'),
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {e}")
