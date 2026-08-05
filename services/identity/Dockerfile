FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/services/identity/src:/app/shared

WORKDIR /app

COPY services/identity/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY shared /app/shared
COPY services/identity /app/services/identity

WORKDIR /app/services/identity

EXPOSE 8000

CMD ["uvicorn", "identity_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
