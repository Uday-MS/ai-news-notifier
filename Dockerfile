# ── Stage 1: Build Frontend ──
FROM node:22-alpine AS frontend-builder

WORKDIR /frontend

# Install frontend dependencies
COPY frontend/package*.json ./
RUN npm ci || npm install

# Build static bundle
COPY frontend/ ./
ENV VITE_API_URL=/api/v1
RUN npm run build

# ── Stage 2: Runtime Backend + Frontend ──
FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

# Backend application code
COPY backend/ .

# Built React frontend assets
COPY --from=frontend-builder /frontend/dist /app/static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
