FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install uv \
    && uv sync --frozen

ENV PATH="/app/.venv/bin:$PATH"

COPY . .