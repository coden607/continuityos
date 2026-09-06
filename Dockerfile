FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY packages ./packages
COPY services ./services
RUN python -m pip install --no-cache-dir .

COPY packs ./packs
COPY continuity.toml.example ./continuity.toml.example

RUN useradd --create-home --uid 10001 continuity \
    && mkdir -p /app/.continuity \
    && chown -R continuity:continuity /app
USER continuity

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/status/health', timeout=3).read()" || exit 1

CMD ["uvicorn", "services.api.main:api", "--host", "0.0.0.0", "--port", "8000"]
