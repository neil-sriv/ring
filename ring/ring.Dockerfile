FROM python:3.12.1-bullseye AS ring

WORKDIR /src

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
RUN pip install uv
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
# Install deps before copying the rest of the tree so code-only rebuilds
# reuse this layer (requirements.txt + the path-dep llm_service client).
COPY requirements.txt ./ring/requirements.txt
COPY packages/service_clients/llm_service ./ring/packages/service_clients/llm_service
RUN uv pip install -r ring/requirements.txt --system --no-cache
COPY ./ ./ring

ARG RING_GIT_SHA
ARG RING_GIT_SHORT_SHA
ARG RING_GIT_BRANCH
ARG RING_GIT_SUBJECT
ARG RING_GIT_AUTHOR_NAME
ARG RING_GIT_AUTHOR_EMAIL
ARG RING_GIT_COMMITTED_AT
ARG RING_GIT_DIRTY
ENV RING_BUILD_GIT_SHA=${RING_GIT_SHA}
ENV RING_BUILD_GIT_SHORT_SHA=${RING_GIT_SHORT_SHA}
ENV RING_BUILD_GIT_BRANCH=${RING_GIT_BRANCH}
ENV RING_BUILD_GIT_SUBJECT=${RING_GIT_SUBJECT}
ENV RING_BUILD_GIT_AUTHOR_NAME=${RING_GIT_AUTHOR_NAME}
ENV RING_BUILD_GIT_AUTHOR_EMAIL=${RING_GIT_AUTHOR_EMAIL}
ENV RING_BUILD_GIT_COMMITTED_AT=${RING_GIT_COMMITTED_AT}
ENV RING_BUILD_GIT_DIRTY=${RING_GIT_DIRTY}
LABEL org.opencontainers.image.source="https://github.com/neil-sriv/ring"
LABEL org.opencontainers.image.revision="${RING_GIT_SHA}"
LABEL org.opencontainers.image.title="ring-api"