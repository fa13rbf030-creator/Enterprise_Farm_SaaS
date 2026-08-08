FROM python:3.14-slim

WORKDIR /app

COPY services/procurement/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY services/procurement/src ./src
COPY shared /app/shared

ENV PYTHONPATH=/app/src:/app/shared

CMD ["uvicorn", "procurement_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
