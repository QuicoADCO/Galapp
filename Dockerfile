FROM python:3.12-slim

# gosu: cede privilegios root→appuser de forma segura en el entrypoint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser

WORKDIR /project

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app    /project/app
COPY wsgi.py  /project/wsgi.py

# Crear directorio de uploads antes del chown
RUN mkdir -p /project/app/static/uploads \
    && chown -R appuser:appuser /project

# Escribir el entrypoint DIRECTAMENTE en el Dockerfile para evitar
# problemas de CRLF cuando se edita desde Windows
RUN printf '#!/bin/sh\nset -e\nmkdir -p /project/app/static/uploads\nchown -R appuser:appuser /project/app/static/uploads\nchmod -R 775 /project/app/static/uploads\ncd /project && gosu appuser python -m app.seed\nexec gosu appuser gunicorn --bind 0.0.0.0:8000 wsgi:app\n' \
    > /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
