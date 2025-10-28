ARG PYTHON_VERSION=3.12
ARG BASE_OS=bookworm

FROM docker.io/library/python:$PYTHON_VERSION-slim-$BASE_OS
ARG PSIK_API_VERSION=2.0.1
ARG BASE_OS

ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install -y git rc \
    && rm -rf /var/lib/apt/lists/*
RUN pip install git+https://github.com/frobnitzem/psik_api@v$PSIK_API_VERSION

# Add a self-signed certificate in case the user didn't configure it.
RUN certified init 'Psik-API Microservice' \
            --host 127.0.0.1 \
            --host ::1 \
            --host localhost
WORKDIR /app

LABEL org.opencontainers.image.source="https://github.com/frobnitzem/psik_api" \
      org.opencontainers.image.title="psik_api" \
      org.opencontainers.image.description="Psik-API Microservice v$PSIK_API_VERSION on Python $PYTHON_VERSION-slim-$BASE_OS" \
      maintainer="David M. Rogers"

CMD ["certified", "serve", "psik_api.main:app", "https://0.0.0.0:4433"]
