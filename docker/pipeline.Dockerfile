FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY config/ config/
COPY src/shared/ src/shared/
COPY src/data_pipeline/ src/data_pipeline/
COPY data/raw/ data/raw/

ENV PYTHONPATH=/app/src

CMD ["uv", "run", "python", "-m", "data_pipeline.main"]
