# Dockerfile (Backend-only)

FROM python:3.11-slim

WORKDIR /app

# Copy backend source
COPY backend/ ./backend
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set PYTHONPATH for FastAPI
ENV PYTHONPATH=/app/backend

# Expose port for FastAPI
EXPOSE 5050

# Run backend with hot reload
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "5050", "--reload"]
