FROM python:3.12.1-bullseye AS ring

WORKDIR /src

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
RUN pip install uv
COPY ./ ./ring
RUN uv pip install -r ring/requirements.txt --system --no-cache