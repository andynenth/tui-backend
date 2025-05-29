# backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes.routes import router as api_router 
from backend.api.routes.ws import router as ws_router

app = FastAPI(
    title="Liap Tui API",
    description="Backend API for Liap Tui Board Game",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")  # ✅ REST API
app.include_router(ws_router)                  # ✅ WebSocket ที่ /ws/{room_id}
