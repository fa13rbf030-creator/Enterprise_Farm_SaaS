FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/services/finance/src:/app/shared

WORKDIR /app

COPY services/finance/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir \
    -r /tmp/requirements.txt

COPY shared /app/shared
COPY services/finance /app/services/finance

WORKDIR /app/services/finance

EXPOSE 8000

CMD [
    "uvicorn",
    "finance_service.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000"
]
