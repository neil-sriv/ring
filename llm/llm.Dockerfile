FROM python:3.12.1-bullseye AS llm

WORKDIR /src

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
RUN pip install uv
COPY ./llm_requirements.txt ./
RUN uv pip install -r llm_requirements.txt --system --no-cache 