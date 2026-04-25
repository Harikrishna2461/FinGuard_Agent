# Build context: project root (.)
# docker build -f agent-service/Dockerfile -t finguard-agent .
FROM python:3.11-slim

# hnswlib (ChromaDB) + scikit-learn need C++ at install time
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY agent-service/requirements.txt agent-service/requirements.txt
RUN pip install --no-cache-dir -r agent-service/requirements.txt

# Agent-service source
COPY agent-service/ agent-service/

# Backend source — agents/ml/models/vector_store are imported at runtime
# (agent-service/app.py adds /app/backend to sys.path automatically)
COPY backend/ backend/

# Persistent ChromaDB volume mount-point
RUN mkdir -p /data/chroma

# /app/backend for agents/ml imports; /app/agent-service for agent_stream etc.
ENV PYTHONPATH=/app/backend:/app/agent-service \
    CHROMA_PERSIST_DIR=/data/chroma \
    AGENT_SERVICE_PORT=5002

EXPOSE 5002

WORKDIR /app/agent-service

CMD ["gunicorn", \
     "--bind", "0.0.0.0:5002", \
     "--workers", "1", \
     "--threads", "8", \
     "--timeout", "600", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
