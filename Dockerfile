# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user --no-warn-script-location -r requirements.txt


FROM python:3.12-slim AS runtime

RUN groupadd -r miransas && useradd -r -g miransas -u 1000 miransas

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY --from=builder /root/.local /home/miransas/.local

COPY --chown=miransas:miransas src/ ./src/
COPY --chown=miransas:miransas migrations/ ./migrations/
COPY --chown=miransas:miransas alembic.ini ./

ENV PATH=/home/miransas/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER miransas

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fs http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
