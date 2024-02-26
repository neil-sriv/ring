FROM python:3.12.1-bullseye

# RUN apk add libpq-dev python3-dev gcc
# RUN apk add build-base
# RUN apk add libffi-dev python3-dev
# RUN apt-get install

WORKDIR /src

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt ./
RUN pip install -r requirements.txt