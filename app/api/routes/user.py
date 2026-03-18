# app/api/routes/user.py
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


def get_user_basic_internal(user_id: int) -> dict | None:
    query = text("""SELECT FullName, DateOfBirth, Gender FROM Users
        WHERE UserID = :user_id AND RoleID = 5""")

    with engine.connect() as conn:
        row = conn.execute(query, {"user_id": user_id}).mappings().first()

    if not row:
        return None

    age = calculate_age(row["DateOfBirth"])

    return {
        "name": row["FullName"],
        "age": age,
        "gender": row["Gender"]
    }

@router.get("/{user_id}/basic", response_model=UserBasicResponse)
def get_user_basic(user_id: int):
    data = get_user_basic_internal(user_id)

    if not data:
        raise HTTPException(status_code=404, detail="User not found")

    return UserBasicResponse(
        name=data["name"],
        age=data["age"],
        gender=data["gender"]
    )