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