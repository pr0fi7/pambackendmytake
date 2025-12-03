# syntax=docker/dockerfile:1
FROM python:3.13-slim

# COPY requirements.txt /
# RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml uv.lock* ./

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN uv venv --python 3.11 ./.venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN uv sync 

RUN mkdir -p logs

COPY src/ src/
COPY app/ app/
COPY log_config.yml log_config.yml

CMD uv run uvicorn --host 0.0.0.0 --log-config log_config.yml --port 8080 app.main:app
