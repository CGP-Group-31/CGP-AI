from fastapi import APIRouter
from app.services.rag_service import generate_answer

router = APIRouter()

@router.get("/chat/{elder_id}")
async def chat(elder_id: int, question: str):
    return await generate_answer(elder_id, question)