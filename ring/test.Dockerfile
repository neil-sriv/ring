FROM --platform=linux/amd64 python:3.12.1-bullseye as ring

WORKDIR /src

RUN pwd

RUN pip install --upgrade pip
RUN pip install uv
# Prefer Debian main (bullseye) over bullseye-security for git. The security
# Packages index can advertise a version whose .deb has already been dropped
# from the pool (HTTP 404), which fails `apt-get install git` even after a
# fresh `apt-get update`. Suite-targeting keeps local/CI image builds working.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git/bullseye \
    && rm -rf /var/lib/apt/lists/*
COPY ./ ./ring
RUN uv pip install -r ./ring/tests/dev_requirements.txt --system --no-cache

LABEL org.opencontainers.image.source=https://github.com/neil-sriv/ring