FROM --platform=linux/amd64 python:3.12.1-bullseye as ring

WORKDIR /src

RUN pwd

RUN pip install --upgrade pip
RUN pip install uv
COPY ./tests/dev_requirements.txt ./
RUN uv pip install -r dev_requirements.txt --system --no-cache

LABEL org.opencontainers.image.source=https://github.com/neil-sriv/ring