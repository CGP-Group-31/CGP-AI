import httpx 
from app.core.config import settings

async def get_elder_form(elder_id: int, report_date:str):
    async with httpx.AsyncClient(timeout=30)as client:
        r = await client.get(
            f"{settings.CRUD_API}/api/v1/elder/elder-form/{elder_id}/latest"
        )
        if r.status_code !=200:
            return None
        return r.json()


async def get_med_adherence(elder_id: int, report_date:str):
    async with httpx.AsyncClient(timeout=30)as client:
        r = await client.get(
            f"{settings.CRUD_API}/api/v1/daily-reports/elder/{elder_id}/medication",params={"report_date": report_date}
        )
        if r.status_code !=200:
            return []
        return r.json()
    

async def get_meal_adherence(elder_id: int, report_date:str):
    async with httpx.AsyncClient(timeout=30)as client:
        r = await client.get(
            f"{settings.CRUD_API}/api/v1/daily-reports/elder/{elder_id}/meals",params={"report_date": report_date}
        )
        if r.status_code !=200:
            return []
        return r.json()
    


