from pydantic import BaseModel


class StartCheckInRequest(BaseModel):
    run_id: int
    elder_id: int
    schedule_name: str


class RespondCheckInRequest(BaseModel):
    run_id: int
    elder_id: int
    message: str