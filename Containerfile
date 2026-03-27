# hadolint ignore=DL3007
FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder
WORKDIR /build
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
RUN uv build --wheel

FROM python:3.14-alpine
RUN apk add --no-cache ffmpeg
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

LABEL org.opencontainers.image.title="chapter-mp3s"
LABEL org.opencontainers.image.authors="gregswift@gmail.com"
LABEL org.opencontainers.image.description="Split m4b audiobooks into per-chapter audio files"
LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"
LABEL org.opencontainers.image.source="https://github.com/gregswift/chapter-mp3s"
LABEL org.opencontainers.image.url="https://github.com/gregswift/chapter-mp3s"

ENTRYPOINT ["chapter-mp3s"]
CMD ["--help"]
