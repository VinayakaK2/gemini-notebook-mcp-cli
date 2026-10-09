FROM golang:1.27-alpine AS tunnel-builder
RUN apk add --no-cache git ca-certificates
RUN git clone --depth 1 https://github.com/openai/tunnel-client.git /src
WORKDIR /src
RUN go build -trimpath -ldflags="-s -w" -o /out/tunnel-client ./cmd/client

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:/usr/local/bin:/usr/bin:/bin"
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=tunnel-builder /out/tunnel-client /usr/local/bin/tunnel-client
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev
COPY deploy/entrypoint.py ./deploy/entrypoint.py
EXPOSE 10000
CMD ["python", "/app/deploy/entrypoint.py"]
