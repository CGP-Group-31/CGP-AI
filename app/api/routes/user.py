from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from datetime import datetime
from app.core.db import engine

router = APIRouter(prefix="/users", tags=["Users"])


class UserBasicResponse(BaseModel):
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None


def calculate_age(dob):
    if dob is None:
        return None

    today = datetime.now().date()
    age = today.year - dob.year

    if (today.month, today.day) < (dob.month, dob.day):
        age -= 1

    return age


@router.get("/{user_id}/basic", response_model=UserBasicResponse)
def get_user_basic(user_id: int):

    query = text("""SELECT FullName, DateOfBirth, Gender FROM Users
        WHERE UserID = :user_id AND RoleID = 5""")

    with engine.connect() as conn:
        row = conn.execute(query, {"user_id": user_id}).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    age = calculate_age(row["DateOfBirth"])

    return UserBasicResponse(
        name=row["FullName"],
        age=age,
        gender=row["Gender"]
    )