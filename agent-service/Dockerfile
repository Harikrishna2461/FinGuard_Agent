FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY agent-service/requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.org/simple --timeout 1000 -r requirements.txt
# Service entrypoint
COPY agent-service/app.py agent-service/agent_stream.py ./

# Shared backend code baked in for CI/CD image builds.
# In local docker-compose, these paths are overridden by volume mounts,
# so changes to agents/ are picked up without rebuilding.
COPY backend/agents/       ./agents/
COPY backend/ml/           ./ml/
COPY backend/vector_store.py ./vector_store.py

RUN mkdir -p /data/chroma /app/data/knowledge_base

ENV PYTHONUNBUFFERED=1 \
    CHROMA_PERSIST_DIR=/data/chroma \
    AGENT_SERVICE_PORT=5002

EXPOSE 5002

CMD ["python", "app.py"]
