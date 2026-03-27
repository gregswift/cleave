# This source image doesnt really seem to put out good versioning
# hadolint ignore=DL3007
FROM python:3.14-slim AS builder

ENV PYTHONUNBUFFERED=1

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

ENV UV_COMPILE_BYTE=1

ENV UV_LINK_MODE=copy

WORKDIR /usr/src/app

# Copy in project files
COPY --chown=1001:1001 pyproject.toml uv.lock ./

# Install dependencies and devDependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy in source code and other assets
COPY --chown=1001:1001 . ./

# This is mostly for documentation, can be overridden with CALAS_PORT at runtime
EXPOSE 8000

LABEL org.opencontainers.image.title="chapter-mp3s"
LABEL org.opencontainers.image.authors="gregswift@gmail.com"
LABEL org.opencontainers.image.description="Script to convert m4b to chapter mp3s"
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.source="https://github.com/gregswift/chapter-mp3s"
LABEL org.opencontainers.image.url="http://github.com/gregswift/chapter-mp3s"

ENTRYPOINT ["uv", "run", "python", "chapter-mp3s"]

# Primary command entrypoint
CMD ["--help"]
