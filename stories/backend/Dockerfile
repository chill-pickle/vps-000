FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

RUN chown -R app:app /app

USER app

RUN mkdir -p data

EXPOSE 8093

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8093"]
