FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY pyproject.toml requirements.lock README.md ./
COPY app ./app

RUN python -m pip wheel --wheel-dir /wheels -c requirements.lock .


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --create-home --home-dir /home/app app

WORKDIR /srv/app

COPY --from=builder /wheels /wheels
RUN python -m pip install --no-index --find-links=/wheels matine-api \
    && rm -rf /wheels

COPY alembic.ini ./
COPY migrations ./migrations

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import os, urllib.request; host = os.environ.get('TRUSTED_HOSTS', 'localhost').split(',')[0].strip(); request = urllib.request.Request('http://127.0.0.1:8000/health', headers={'Host': host}); urllib.request.urlopen(request, timeout=2).read()"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--no-server-header"]
