FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY ai_system/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ai_system ./ai_system
COPY backend/ml ./ml

EXPOSE 8000

CMD ["uvicorn", "ai_system.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
