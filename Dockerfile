# Dockerfile
FROM node:18 AS builder
WORKDIR /app
COPY frontend/ ./frontend
COPY esbuild.config.cjs ./
COPY package.json ./
RUN npm install && node esbuild.config.cjs

FROM python:3.11-slim
WORKDIR /app
COPY backend/ ./backend
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=builder /app/build /app/backend/static
COPY frontend/index.html /app/backend/static/index.html

ENV PYTHONPATH=/app/backend

EXPOSE 80
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "80"]
