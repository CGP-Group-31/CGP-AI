from fastapi import FastAPI
from app.api.chat import router as chat_router

app = FastAPI(title="Elder AI System")

app.include_router(chat_router, prefix="/ai")

from app.api.debug import router as debug_router
from app.daily_reports.api import router as daily_report_router

app.include_router(debug_router)
app.include_router(daily_report_router)