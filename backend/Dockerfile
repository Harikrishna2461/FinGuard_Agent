FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.org/simple --timeout 1000 -r requirements.txt

# Copy backend source
COPY app/       ./app/
COPY models/    ./models/
COPY ml/        ./ml/
COPY agents/    ./agents/
COPY vector_store.py load_knowledge_base.py run.py ./

# Ensure data dirs exist
RUN mkdir -p /app/data/chroma

ENV PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5001

EXPOSE 5001

CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5001", \
     "--workers", "2", "--threads", "4", \
     "--timeout", "300", "--worker-class", "gthread", \
     "app:create_app()"]
