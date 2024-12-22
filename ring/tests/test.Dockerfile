FROM python:3.12.1-bullseye AS ring

WORKDIR /src

RUN pwd

RUN pip install --upgrade pip
RUN pip install uv
COPY ./tests/dev_requirements.txt ./
RUN uv pip install -r dev_requirements.txt --system --no-cache