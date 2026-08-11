FROM --platform=linux/amd64 python:3.12.1-bullseye as ring

WORKDIR /src

RUN pwd

RUN pip install --upgrade pip
RUN pip install uv
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
COPY ./ ./ring
RUN uv pip install -r ./ring/tests/dev_requirements.txt --system --no-cache

LABEL org.opencontainers.image.source=https://github.com/neil-sriv/ring