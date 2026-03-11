from fastapi import APIRouter
from datetime import datetime, timezone
from app.vector_store.indexer import index_message
from app.vector_store.embedder import embed_query

router = APIRouter(prefix="/debug", tags=["debug"])

@router.post("/index-test")
async def index_test():
    content = "today is my bithday march 10. now im 40 years old" #this dummy data inser for azure ai search 
    vector = await embed_query(content)

    doc = {
        "id": "debug-chat-224-1",
        "elder_id": 224,
        "thread_id": 1,
        "source_type": "chat_message",
        "role": "elder",
        "mood": "Happy",
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "content_vector": vector
    }

    result = await index_message(doc)

    return {
        "status": "ok",
        "indexed_elder_id": 224,
        "content": content,
        "result": str(result)
    }