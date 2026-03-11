import httpx
from app.core.config import settings


async def get_vitals(elder_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.CRUD_API}/vitals/{elder_id}")
        if r.status_code != 200:
            return []
        return r.json()


async def get_medications(elder_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.CRUD_API}/medications/{elder_id}")
        if r.status_code != 200:
            return []
        return r.json()
    s

async def get_chat_messages(elder_id: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{settings.CRUD_API}/api/v1/ai_system/chat-messages/elder/{elder_id}?limit=10")
        if r.status_code != 200:
            return []
        return r.json()




