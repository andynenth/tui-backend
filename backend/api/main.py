# backend/api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# ✅ Import routers
from backend.api.routes.routes import router as api_router
from backend.api.routes.ws import router as ws_router

app = FastAPI(
    title="Liap Tui API",
    description="Backend API for Liap Tui Board Game",
    version="1.0"
)

# ✅ Allow CORS (frontend and WebSocket)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include REST and WebSocket routers
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

# ✅ Serve static files (for index.html and bundle.js)
app.mount("/", StaticFiles(directory="backend/static", html=True), name="static")

# ✅ Optional fallback: serve index.html for root path
@app.get("/")
def read_index():
    return FileResponse(os.path.join("backend/static", "index.html"))
