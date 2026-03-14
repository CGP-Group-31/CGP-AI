from pydantic import BaseModel


class StartCheckInRequest(BaseModel):
    elder_id: int


class RespondCheckInRequest(BaseModel):
    run_id: int
    elder_id: int
    message: str