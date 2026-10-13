# syntax=docker/dockerfile:1
# Imagen de la API (C-02, design I10). Contexto de construcción: backend/.
# Base fijada por etiqueta y digest (design I2): 3.13.15-slim-bookworm, último push 2026-09-19.
ARG PYTHON_IMAGE=python:3.13.15-slim-bookworm@sha256:2325bb286ec344af3e5898cc224b5844e2707ac6e26b1632516fd3edc84a5e26

FROM ${PYTHON_IMAGE} AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Solo el manifiesto, para aprovechar la caché de capas. Las dependencias de test no entran.
COPY pyproject.toml ./
RUN python -m pip install --group app

FROM ${PYTHON_IMAGE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
RUN useradd --system --no-create-home --uid 10001 --shell /usr/sbin/nologin api
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY alembic.ini ./
COPY app ./app
USER api
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/openapi.json', timeout=3)"]
# Migra, carga el seed si falta y arranca (design I10). Una sola réplica de la API.
CMD ["sh", "-c", "alembic upgrade head && python -m app.infrastructure.db.cargar_seed && exec uvicorn app.main:crear_app_desde_entorno --factory --host 0.0.0.0 --port 8000"]
