# Build context: project root (.)
# docker build -f backend/Dockerfile -t finguard-backend .
FROM python:3.11-slim

# hnswlib (ChromaDB) needs a C++ compiler at install time
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps as a separate cached layer
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Backend source
COPY backend/ backend/

# Frontend — backend serves index.html at /  (see app/__init__.py _FRONTEND_DIR)
COPY frontend/ frontend/

# Persistent volume mount-points (override with -v or Azure file shares)
RUN mkdir -p /data/chroma /data/db

ENV PYTHONPATH=/app/backend \
    FLASK_ENV=production \
    PORT=5001 \
    CHROMA_PERSIST_DIR=/data/chroma

EXPOSE 5001

WORKDIR /app/backend

CMD ["gunicorn", \
     "--bind", "0.0.0.0:5001", \
     "--workers", "2", \
     "--threads", "4", \
     "--timeout", "300", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "wsgi:app"]
