FROM python:3.9-alpine
RUN apk add --no-cache git
COPY . .
ENTRYPOINT [ "/entrypoint.sh" ]