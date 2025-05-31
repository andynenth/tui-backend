# backend/api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.api.routes.routes import router as api_router
from backend.api.routes.ws import router as ws_router
import os
from dotenv import load_dotenv

# ✅ Load .env file
load_dotenv()

# ✅ Read config from environment
STATIC_DIR = os.getenv("STATIC_DIR", "backend/static")
INDEX_FILE = os.getenv("INDEX_FILE", "index.html")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# ✅ Create FastAPI app
app = FastAPI(
    title="Liap Tui API",
    description="Backend API for Liap Tui Board Game",
    version="1.0"
)

# ✅ Allow CORS (frontend and WebSocket)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include REST and WebSocket routers
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

# ✅ Serve static files (for index.html and bundle.js)
app.mount("/", StaticFiles(directory=os.getenv("STATIC_DIR", "backend/static"), html=True), name="static")

# ✅ Optional fallback: serve index.html for root path
@app.get("/")
def read_index():
    return FileResponse(os.path.join(os.getenv("STATIC_DIR", "backend/static"), os.getenv("INDEX_FILE", "index.html")))

