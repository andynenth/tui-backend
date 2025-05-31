# 📄 Dockerfile (Backend-only)

FROM python:3.11-slim

WORKDIR /app

# 🐍 Copy backend source code and dependencies
COPY backend/ ./backend
COPY requirements.txt ./

# 📦 Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 🧭 Set PYTHONPATH for FastAPI
ENV PYTHONPATH=/app/backend

# 🌐 Expose API port (actual value controlled by .env and docker-compose)
EXPOSE 5050

# 🏁 Let docker-compose set the command via `command:` and `.env`
# Leave CMD minimal
CMD ["uvicorn", "backend.api.main:app"]
