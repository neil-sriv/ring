FROM python:3.12.1-alpine3.18

# RUN apk add libpq-dev python3-dev postgresql-server-dev-all

WORKDIR /src

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt ./
RUN pip install -r requirements.txt