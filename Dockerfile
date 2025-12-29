# Multi-stage Dockerfile for BeamNG Telemetry Platform
# Stage 1: Build Vue frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /build

# Copy frontend package files
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend with built frontend
FROM python:3.12-slim

WORKDIR /app

# No system dependencies needed:
# - psycopg2-binary is pre-compiled (no gcc needed)
# - We use SQLAlchemy, not psql commands (no postgresql-client needed)
# - All Python packages have pre-built wheels for python:3.12-slim

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY app/ ./app/

# Copy built frontend from builder stage
COPY --from=frontend-builder /build/dist ./static

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

