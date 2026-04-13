FROM nginx:stable-alpine

RUN apk add --no-cache openssl && \
    mkdir -p /etc/nginx/certs && \
    openssl req -x509 -nodes -days 3650 \
        -newkey rsa:2048 \
        -keyout /etc/nginx/certs/galapp.key \
        -out    /etc/nginx/certs/galapp.crt \
        -subj "/C=ES/ST=Madrid/L=Madrid/O=Galapp/CN=galapp.local" \
        -addext "subjectAltName=IP:127.0.0.1,DNS:localhost,DNS:galapp.local"

COPY nginx.conf /etc/nginx/nginx.conf
