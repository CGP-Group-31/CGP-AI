from fastapi import FastAPI
from app.api.chat import router as chat_router

app = FastAPI(title="Elder AI System")



from app.api.checkin import router as checkin_router
from app.api.debug import router as debug_router
from app.api.routes.user import router as users_router

app.include_router(users_router)

app.include_router(debug_router)




app.include_router(chat_router)
app.include_router(checkin_router)
from app.daily_reports.api import router as daily_report_router
from app.weekly_report.api import router as weekly_report_router

app.include_router(debug_router)
app.include_router(daily_report_router)
app.include_router(weekly_report_router)