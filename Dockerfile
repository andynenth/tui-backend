# 📄 Dockerfile (Backend-only)

FROM python:3.11-slim

WORKDIR /app

# 🐍 Copy backend source code and dependencies
COPY backend/ ./backend
COPY shared/ ./shared
COPY requirements.txt ./

# 📦 Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 📁 Create data directory for SQLite database
RUN mkdir -p /app/data && chmod 755 /app/data

# 🧭 Set PYTHONPATH for FastAPI
ENV PYTHONPATH=/app/backend

# 🌐 Expose API port (actual value controlled by .env and docker-compose)
EXPOSE 5050

# 🏁 Default command for standalone Docker
# docker-compose can override this with its own command
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "5050"]
