#!/bin/sh
set -e

# Garantiza que el directorio de uploads existe y pertenece a appuser
# (necesario cuando el volumen Docker se monta como root en el primer arranque)
mkdir -p /project/app/static/uploads
chown -R appuser:appuser /project/app/static/uploads

# Cede privilegios y ejecuta gunicorn como appuser
exec gosu appuser gunicorn --bind 0.0.0.0:8000 wsgi:app
