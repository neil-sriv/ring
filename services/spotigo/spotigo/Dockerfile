FROM golang:1.23-alpine

# RUN apk update && apk upgrade && \
#     apk add --no-cache bash git openssh

WORKDIR /app

RUN go install github.com/air-verse/air@latest

COPY go.mod go.sum ./

RUN go mod download