FROM python:3.11-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

RUN mkdir -p /install/lib/python3.11/site-packages/efinance/data && \
    chmod 777 /install/lib/python3.11/site-packages/efinance/data

FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

RUN mkdir -p /usr/local/lib/python3.11/site-packages/efinance/data && \
    chmod 777 /usr/local/lib/python3.11/site-packages/efinance/data

WORKDIR /app
COPY app ./app
COPY alembic.ini .

RUN mkdir -p /app/data/ml_models /app/data/nlp_cache && \
    chmod -R 777 /app/data

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
