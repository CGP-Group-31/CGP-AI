import httpx
from app.core.config import settings


async def get_elder_profile(elder_id: int):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{settings.CRUD_API}/api/v1/elder/elder-profile/{elder_id}")
        if r.status_code != 200:
            return None
        return r.json()


async def get_medical_profile(elder_id: int):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{settings.CRUD_API}/api/v1/caregiver/elder/medical-profile/{elder_id}")
        if r.status_code != 200:
            return None
        return r.json()


async def get_upcoming_appointments(elder_id: int):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            f"{settings.CRUD_API}/api/v1/caregiver/appointments/elder/{elder_id}/upcoming-7-days"
        )
        if r.status_code != 200:
            return []
        return r.json()


async def get_latest_additional_info(elder_id: int):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            f"{settings.CRUD_API}/api/v1/caregiver/additional-info/elder/{elder_id}/latest-2"
        )
        if r.status_code != 200:
            return []
        return r.json()


async def get_today_meals(elder_id: int):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{settings.CRUD_API}/api/v1/elder/meals/today/{elder_id}")
        if r.status_code != 200:
            return []
        data = r.json()
        return data.get("items", [])