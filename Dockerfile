# -------------------------
# STAGE 1 — Builder
# -------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalamos solo lo necesario para compilar dependencias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Creamos entorno virtual
RUN python -m venv /venv

ENV PATH="/venv/bin:$PATH"

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# -------------------------
# STAGE 2 — Runtime (LIMPIO)
# -------------------------
FROM python:3.12-slim

# Creamos usuario no root
RUN useradd -m appuser

WORKDIR /app

# Solo librerías runtime necesarias (NO build-essential)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiamos entorno virtual ya compilado
COPY --from=builder /venv /venv

ENV PATH="/venv/bin:$PATH"

# Copiamos aplicación
COPY ./app /app

# Cambiamos permisos
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "main:app"]
