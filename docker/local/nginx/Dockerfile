FROM docker.io/nginx:1.27.0-alpine3.19-slim

RUN rm /etc/nginx/conf.d/default.conf

COPY ./nginx.conf /etc/nginx/conf.d/default.conf