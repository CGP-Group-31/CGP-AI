from fastapi import APIRouter
from .routes import chat, health

api_router = APIRouter()

api_router.include_router(chat.router, prefix="/ai")
api_router.include_router(health.router)