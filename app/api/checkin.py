from fastapi import APIRouter, HTTPException
from app.schemas.checkin import StartCheckInRequest, RespondCheckInRequest
from app.services.checkin_service import start_checkin, get_current_checkin, respond_checkin

router = APIRouter(prefix="/ai/checkin", tags=["AI CheckIn"])


@router.post("/start")
async def api_start_checkin(payload: StartCheckInRequest):
    try:
        return await start_checkin(
            run_id=payload.run_id,
            elder_id=payload.elder_id,
            schedule_name=payload.schedule_name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/current/{elder_id}")
async def api_get_current_checkin(elder_id: int):
    return await get_current_checkin(elder_id)


@router.post("/respond")
async def api_respond_checkin(payload: RespondCheckInRequest):
    try:
        return await respond_checkin(
            run_id=payload.run_id,
            elder_id=payload.elder_id,
            message=payload.message
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))