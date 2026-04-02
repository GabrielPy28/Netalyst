# syntax=docker/dockerfile:1
# Multistage + Python slim (instructions.md). Contexto de build: raíz del repo.
#
# Variables de entorno: la imagen no incluye .env (ignorado en el build).
#   docker run --rm -p 8000:8000 --env-file .env netalyst-api
# O: docker compose up (usa env_file en compose.yaml).

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY backend/requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /service
COPY backend/app ./app

USER app
EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
