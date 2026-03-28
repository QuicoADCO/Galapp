# GalApp – Proyecto Final SecDevOps

GalApp es una aplicación web de votaciones en vivo desarrollada en Python con Flask, que implementa un ciclo completo de desarrollo seguro (SecDevOps). Integra autenticación JWT, API REST protegida, base de datos PostgreSQL, contenedorización con Docker y CI/CD con GitHub Actions.

---

## Índice

1. [Arquitectura del proyecto](#arquitectura-del-proyecto)
2. [Tecnologías](#tecnologías)
3. [Entorno virtual y aislamiento Docker](#entorno-virtual-y-aislamiento-docker)
4. [Puesta en marcha y despliegue en red](#puesta-en-marcha-y-despliegue-en-red)
5. [Tipos de usuario y diferenciación visual](#tipos-de-usuario-y-diferenciación-visual)
6. [Votación anónima desde enlace compartido](#votación-anónima-desde-enlace-compartido)
7. [API REST](#api-rest)
8. [Autenticación JWT](#autenticación-jwt)
9. [Seguridad – OWASP Top 10 Web 2025](#seguridad--owasp-top-10-web-2025)
10. [Seguridad – OWASP API Security Top 10](#seguridad--owasp-api-security-top-10)
11. [Cabeceras de seguridad HTTP](#cabeceras-de-seguridad-http)
12. [CCN-CERT – Estándares aplicados](#ccn-cert--estándares-aplicados)
13. [Base de datos](#base-de-datos)
14. [Contenedorización Docker](#contenedorización-docker)
15. [Testing](#testing)
16. [CI/CD – GitHub Actions](#cicd--github-actions)
17. [GitFlow](#gitflow)
18. [Pruebas con Postman](#pruebas-con-postman)

---

## Arquitectura del proyecto

```
Galapp/
├── app/
│   ├── models/
│   │   ├── user.py               # Modelo User: id, username, email, password (hash), role
│   │   └── survey.py             # Survey, Question, QuestionOption, Vote, AnonVote
│   ├── routes/
│   │   ├── api.py                # API REST: encuestas, preguntas, opciones, votos (IDOR protegido)
│   │   ├── auth.py               # Registro y login — validación + JWT + rollback DB
│   │   └── frontend.py           # Rutas HTML: /login, /register, /dashboard, /encuesta/<id>
│   ├── templates/
│   │   ├── login.html            # Formulario de acceso
│   │   ├── register.html         # Formulario de registro
│   │   ├── dashboard.html        # Panel principal de votación
│   │   ├── create_survey.html    # Constructor de encuestas multi-pregunta
│   │   └── survey_vote.html      # Página pública de votación compartible
│   ├── static/
│   │   ├── login.js              # Login + validación open redirect en ?siguiente=
│   │   ├── register.js           # Registro con validación cliente
│   │   ├── dashboard.js          # Dashboard: carga surveys, votación, tema admin
│   │   ├── create_survey.js      # Constructor dinámico de encuestas (WeakMap para imágenes)
│   │   ├── survey_vote.js        # Votación pública: anónima o con JWT, voter_token UUID
│   │   ├── login.css             # Estilos del formulario de login
│   │   ├── register.css          # Estilos del formulario de registro
│   │   ├── dashboard.css         # Estilos completos del dashboard + admin-theme
│   │   ├── create_survey.css     # Estilos del constructor de encuestas
│   │   ├── survey_vote.css       # Estilos de la página de votación pública
│   │   └── uploads/              # Imágenes subidas (volumen Docker persistente)
│   ├── database.py               # Inicialización de SQLAlchemy (init_db)
│   ├── main.py                   # App factory + MAX_CONTENT_LENGTH + rate limits + error handlers
│   ├── utils.py                  # generate_token, token_required (inyecta g.current_user)
│   └── seed.py                   # Crea el usuario administrador inicial
├── tests/
│   ├── conftest.py               # Fixture pytest con SQLite en memoria
│   ├── test_auth.py              # 24 tests: registro, login, protección JWT
│   ├── test_surveys.py           # 24 tests: CRUD encuestas/preguntas/opciones + IDOR
│   ├── test_votes.py             # 10 tests: votación, unicidad, vote tampering
│   └── test_health.py            # 4 tests: health check, error handlers
├── nginx/
│   └── nginx.conf                # Proxy inverso + cabeceras de seguridad + Cache-Control /api/
├── .github/
│   └── workflows/ci.yml          # Pipeline CI: lint (flake8) + tests + PostgreSQL service
├── postman/
│   └── Galapp.postman_collection.json
├── wsgi.py                       # Entry point para Gunicorn
├── Dockerfile                    # Imagen única python:3.12-slim + gosu + entrypoint inline
├── docker-compose.yml            # Orquestación: db + web + nginx + volumen uploads
└── .env                          # Variables de entorno (excluido del repositorio)
```

**Flujo de una petición HTTP:**

```
Navegador / curl
    │
    ▼
Nginx :80  ─── cabeceras de seguridad, CSP, server_tokens off
    │
    ▼
Gunicorn :8000  ─── WSGI workers
    │
    ▼
Flask (create_app)
    ├── /auth/*      →  auth.py   (registro, login)
    ├── /api/*       →  api.py    (protegido con JWT)
    └── /*           →  frontend.py (HTML estático)
    │
    ▼
PostgreSQL :5432  ─── SQLAlchemy ORM
```

---

## Tecnologías

| Categoría       | Tecnología                        |
|-----------------|-----------------------------------|
| Backend         | Python 3.12, Flask 3.0            |
| ORM             | Flask-SQLAlchemy 3.1, Flask-Migrate |
| Base de datos   | PostgreSQL 15                     |
| Autenticación   | PyJWT 2.8, Werkzeug PBKDF2-SHA256 |
| Rate limiting   | Flask-Limiter 3.7                 |
| Servidor WSGI   | Gunicorn 21                       |
| Proxy inverso   | Nginx stable-alpine               |
| Contenedores    | Docker, Docker Compose            |
| Testing         | pytest, SQLite en memoria         |
| CI/CD           | GitHub Actions (lint + tests)     |
| Seguridad       | OWASP Top 10 2025, OWASP API Top 10, CCN-CERT |

---

## Entorno virtual y aislamiento Docker

### ¿Por qué Docker como entorno virtual?

En este proyecto el **aislamiento de dependencias** se realiza a través de Docker en lugar de un entorno virtual clásico (`venv`). Esto proporciona un nivel de aislamiento mayor: no solo aísla los paquetes Python, sino también el sistema operativo, las librerías del sistema (`libpq5`), el usuario de ejecución y el sistema de archivos.

| Aspecto | venv tradicional | Docker (este proyecto) |
|---------|-----------------|------------------------|
| Aislamiento de paquetes Python | ✓ | ✓ |
| Aislamiento del sistema operativo | ✗ | ✓ (`python:3.12-slim`) |
| Reproducibilidad en CI/CD | Parcial | ✓ (misma imagen) |
| Usuario no-root | Depende del sistema | ✓ (`appuser`) |
| Gestión de secrets | Manual | ✓ (variables de entorno Docker) |

### Cómo está implementado

El aislamiento está definido en [`Dockerfile`](Dockerfile):

```dockerfile
FROM python:3.12-slim
# Instalar solo dependencias runtime (sin compiladores)
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl gosu \
    && rm -rf /var/lib/apt/lists/*
# Usuario no-root
RUN useradd -m appuser
WORKDIR /project
# Instalar dependencias Python aisladas dentro del contenedor
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app /project/app
COPY wsgi.py /project/wsgi.py
```

El fichero [`requirements.txt`](requirements.txt) fija todas las versiones exactas, garantizando reproducibilidad total entre entornos de desarrollo, CI y producción.

### Levantar el entorno

```bash
# Construir el entorno aislado y levantar todos los servicios
docker compose up -d --build

# Verificar que el entorno está activo
docker compose ps
```

> **Screenshot recomendado:** captura la salida de `docker compose ps` mostrando los tres servicios (`db`, `web`, `nginx`) en estado `healthy`.

---

## Puesta en marcha y despliegue en red

### Requisitos

- Docker Desktop instalado y en ejecución

### Variables de entorno

Crear el archivo `.env` en la raíz del proyecto (ya incluido, **nunca subir a git**):

```env
POSTGRES_USER=galapp
POSTGRES_PASSWORD=superpassword123
POSTGRES_DB=galapp
POSTGRES_HOST=db
SECRET_KEY=super-long-random-secret-key-123456
JWT_SECRET_KEY=another-super-long-random-key-987654
```

### Levantar la aplicación por primera vez

```bash
# 1. Construir imágenes y levantar todos los servicios
docker compose up -d --build

# 2. Crear el usuario administrador inicial
docker compose exec web python -m app.seed

# 3. Verificar que todos los servicios están healthy
docker compose ps
```

La aplicación queda disponible en: **http://localhost**

### Acceso desde otros dispositivos de la misma red (LAN/WiFi)

Nginx escucha en `0.0.0.0:80`, lo que significa que cualquier dispositivo conectado a la **misma red WiFi o LAN** puede acceder a la aplicación mientras el servidor esté encendido.

**Paso 1 — Encontrar la IP local del servidor:**

```bash
# Windows (PowerShell o CMD)
ipconfig
# Busca "Dirección IPv4" bajo tu adaptador WiFi o Ethernet
# Ejemplo: 192.168.1.46

# Linux / Mac
ip a | grep "inet "
# o
ifconfig | grep "inet "
```

**Paso 2 — Acceder desde cualquier dispositivo de la red:**

```
http://192.168.1.46          → Página principal
http://192.168.1.46/login    → Login
http://192.168.1.46/register → Registro
http://192.168.1.46/dashboard → Panel de control
http://192.168.1.46/encuesta/1 → Encuesta compartida (voto anónimo)
```

> Sustituye `192.168.1.46` por la IP que muestre `ipconfig` en tu máquina. Puede cambiar si tu router asigna IPs dinámicas — considera asignar una IP estática en la configuración de tu router para estabilidad.

**Paso 3 — Compartir una encuesta concreta:**

Desde el dashboard, haz clic en **🔗 Compartir** en cualquier tarjeta. El enlace copiado usará `window.location.origin`, que será la IP o el hostname desde el que estés accediendo. Envía ese enlace (WhatsApp, email, etc.) a quien quieras que vote.

### Requisitos para acceso externo (fuera de tu red)

Para que usuarios fuera de tu WiFi puedan acceder necesitarías:

| Opción | Descripción |
|--------|-------------|
| **Ngrok** (rápido) | `ngrok http 80` → genera URL pública temporal |
| **Port forwarding** | Abrir puerto 80 en tu router y usar tu IP pública |
| **VPS / Cloud** | Desplegar en un servidor con IP pública fija (recomendado para producción) |

### Reiniciar desde cero (borra todos los datos)

```bash
docker compose down -v
docker compose up -d --build
docker compose exec web python -m app.seed
```

### Comandos útiles

```bash
# Ver logs del servidor web
docker compose logs -f web

# Ver logs de nginx
docker compose logs -f nginx

# Parar sin borrar datos
docker compose down

# Parar y borrar todos los volúmenes (PostgreSQL + uploads)
docker compose down -v

# Ver estado de los contenedores
docker compose ps
```

---

## Tipos de usuario y diferenciación visual

### Roles del sistema

El modelo [`app/models/user.py`](app/models/user.py) define dos roles:

| Rol | Descripción | Se crea mediante |
|-----|-------------|-----------------|
| `user` | Usuario estándar. Puede crear encuestas, añadir preguntas/opciones y votar. | Registro público en `/register` |
| `admin` | Administrador. Mismo acceso que `user` más identificación visual diferenciada. | Script `app/seed.py` |

Credenciales del administrador por defecto (creadas con [`app/seed.py`](app/seed.py)):

| Campo    | Valor        |
|----------|--------------|
| Username | `admin`      |
| Password | `Admin1234!` |
| Role     | `admin`      |

```bash
docker compose exec web python -m app.seed
```

### Diferenciación visual del administrador

Cuando el token JWT contiene `role: "admin"`, el dashboard aplica automáticamente el **tema dorado** en [`app/static/dashboard.js`](app/static/dashboard.js):

```javascript
// app/static/dashboard.js — línea 17
if (role === 'admin') {
    document.body.classList.add('admin-theme');
    document.querySelector('.sidebar-logo').innerHTML = 'Gal<span>app</span> · Admin';
    document.getElementById('topbar-title').textContent = 'Panel de Administración';
}
```

Los cambios visuales están definidos en [`app/static/dashboard.css`](app/static/dashboard.css) bajo el selector `body.admin-theme`:

| Elemento | Usuario normal | Administrador |
|----------|---------------|---------------|
| Color acento (`--accent`) | Violeta `#6366f1` | Dorado `#f59e0b` |
| Título del topbar | `Encuestas` | `Panel de Administración` |
| Logo en sidebar | `Galapp` | `Galapp · Admin` |
| Avatar | Gradiente violeta | Gradiente dorado |
| Botón primario | Violeta | Dorado |
| Borde topbar | Sin borde de color | Borde dorado `2px` |
| Borde sidebar | Gris neutro | Dorado semitransparente |
| Badge de rol | Fondo violeta | Fondo dorado |

> El rol se extrae del **JWT almacenado en `localStorage`** — no hay ninguna petición adicional al servidor para determinar el rol. La modificación del token en el cliente solo afecta a la UI, nunca a los permisos del servidor (que siempre verifica el JWT en cada request).

---

## Votación anónima desde enlace compartido

Cualquier persona que reciba el enlace de una encuesta puede votar **sin necesidad de registrarse**, siempre que el servidor esté en línea y accesible desde su red.

### Cómo funciona

```
1. El creador comparte el enlace de su encuesta:
   http://192.168.1.46/encuesta/3

2. El visitante abre el enlace en su navegador.
   → Si tiene sesión JWT: vota como usuario registrado.
   → Si no tiene sesión: vota de forma anónima.

3. Para votar anónimamente, el navegador genera un UUID v4
   la primera vez y lo guarda en localStorage como "voter_token".

4. El UUID se envía en la cabecera HTTP X-Voter-Token en cada voto.

5. El servidor valida el formato del token y lo usa para
   deduplicar: una persona solo puede votar una vez por pregunta.
```

### Identificación del votante anónimo

| Mecanismo | Detalle |
|-----------|---------|
| **Generación del token** | UUID v4 generado en el navegador: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx` |
| **Almacenamiento** | `localStorage.setItem('voter_token', t)` — persiste entre recargas |
| **Transmisión** | Cabecera HTTP personalizada `X-Voter-Token` (no cookie, no URL) |
| **Reenvío por nginx** | `proxy_set_header X-Voter-Token $http_x_voter_token;` en `nginx.conf` |
| **Validación en servidor** | Regex `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$` |
| **Persistencia** | Tabla separada `anon_votes` — sin FK a `users` |

### Seguridad implementada

| Amenaza | Contramedida |
|---------|-------------|
| **Flood de votos / vote stuffing** | Rate limit de **30 req/min** en `/api/public/*/vote` (`Flask-Limiter`) |
| **Doble voto anónimo** | `UniqueConstraint("voter_token", "question_id")` en la tabla `anon_votes` — la BD rechaza el segundo intento aunque se eluda el rate limit |
| **Inyección de token malformado** | El servidor valida el formato UUID con regex antes de usar el token; `_voter_token()` devuelve `None` si no coincide → `400 Bad Request` |
| **Suplantación de otro votante** | El servidor no confía en el token del cliente para otorgar privilegios, solo para deduplicar. Cualquier UUID falso solo impide votar dos veces al atacante |
| **Vote tampering (opción ajena)** | El servidor verifica que `option.question_id == question_id` y que la pregunta pertenece a la encuesta (`question.survey_id == survey_id`) |
| **Acceso a encuestas privadas** | Los endpoints públicos solo exponen datos de encuestas (sin datos de usuario); la propiedad de la encuesta no se revela |
| **Exposición de votos de otros** | `GET /api/public/surveys/<id>/my-votes` filtra estrictamente por el `voter_token` de la petición |

### Endpoints públicos añadidos

```
GET  /api/public/surveys/<id>              → Datos de la encuesta (sin JWT)
GET  /api/public/surveys/<id>/my-votes     → Votos previos del voter_token actual
POST /api/public/surveys/<id>/vote         → Registrar voto anónimo (máx. 30/min)
```

### Flujo técnico detallado

```
Navegador (sin JWT)
    │
    │  GET /encuesta/3  → HTML de survey_vote.html
    │
    ▼
survey_vote.js detecta: jwtToken === null
    │
    │  Genera voter_token UUID v4 (si no existe en localStorage)
    │  BASE = '/api/public'
    │
    ▼
GET /api/public/surveys/3           (cabecera X-Voter-Token: uuid)
GET /api/public/surveys/3/my-votes  (para marcar preguntas ya votadas)
    │
    ▼
Usuario hace clic en "Votar esta pregunta"
    │
    ▼
POST /api/public/surveys/3/vote
    Body: { question_id: 2, option_id: 7 }
    Header: X-Voter-Token: a1b2c3d4-...
    │
    ▼  Nginx reenvía X-Voter-Token → Flask
    │
    ▼  Flask valida:
    │  1. UUID bien formado
    │  2. question_id pertenece a survey_id
    │  3. option_id pertenece a question_id
    │  4. ¿Ya existe AnonVote(voter_token, question_id)?  → 400 si sí
    │
    ▼
INSERT INTO anon_votes (voter_token, question_id, option_id)
    Si UniqueConstraint viola → IntegrityError → rollback → 400
```

---

## API REST

Todos los endpoints salvo `/api/health` requieren autenticación JWT en la cabecera:

```
Authorization: Bearer <token>
```

### Tabla de endpoints

| Método | Endpoint                                     | Auth        | Solo creador | Descripción                                      |
|--------|----------------------------------------------|-------------|:------------:|--------------------------------------------------|
| GET    | `/api/health`                                | No          | —            | Estado del servicio                              |
| POST   | `/auth/register`                             | No          | —            | Registro — máx. 5 req/min por IP                 |
| POST   | `/auth/login`                                | No          | —            | Login — devuelve JWT, máx. 10 req/min            |
| GET    | `/api/surveys`                               | JWT         | —            | Listar todas las encuestas                       |
| POST   | `/api/surveys`                               | JWT         | —            | Crear encuesta — máx. 20 req/min                 |
| GET    | `/api/surveys/<id>`                          | JWT         | —            | Encuesta con preguntas y opciones                |
| POST   | `/api/surveys/<id>/questions`                | JWT         | ✓            | Añadir pregunta (solo el creador de la encuesta) |
| POST   | `/api/questions/<id>/options`                | JWT         | ✓            | Añadir opción (solo el creador de la encuesta)   |
| POST   | `/api/votes`                                 | JWT         | —            | Votar — máx. 60 req/min, opción verificada       |
| GET    | `/api/surveys/<id>/my-votes`                 | JWT         | —            | Votos del usuario autenticado en esta encuesta   |
| GET    | `/api/surveys/<id>/results`                  | JWT         | —            | Resultados con porcentajes por opción            |
| GET    | `/api/public/surveys/<id>`                   | No (anónimo)| —            | Datos de encuesta sin JWT (votación compartida)  |
| GET    | `/api/public/surveys/<id>/my-votes`          | No (anónimo)| —            | Votos previos del voter_token actual             |
| POST   | `/api/public/surveys/<id>/vote`              | No (anónimo)| —            | Voto anónimo — máx. 30 req/min, UUID requerido   |

### Validaciones de entrada

| Campo        | Regla                                    | Archivo              |
|--------------|------------------------------------------|----------------------|
| `username`   | 3–32 chars, solo `[a-zA-Z0-9_]`         | [`app/routes/auth.py`](app/routes/auth.py) |
| `email`      | Formato `x@x.x` validado con regex       | [`app/routes/auth.py`](app/routes/auth.py) |
| `password`   | Mín. 8 chars, mayúscula + minúscula + dígito | [`app/routes/auth.py`](app/routes/auth.py) |
| `title`      | Requerido, máx. 200 chars               | [`app/routes/api.py`](app/routes/api.py) |
| `text` (opción) | Requerido, máx. 300 chars            | [`app/routes/api.py`](app/routes/api.py) |

### Respuestas de error estándar

| Código | Causa                                   |
|--------|-----------------------------------------|
| 400    | Campos faltantes o inválidos            |
| 401    | Token ausente, expirado o inválido      |
| 403    | Operación no permitida (IDOR)           |
| 404    | Recurso no encontrado                   |
| 429    | Rate limit superado                     |
| 500    | Error interno (mensaje genérico, sin stack trace) |

### Ejemplos curl

**Registro:**

```bash
curl -X POST http://localhost/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "ana", "email": "ana@example.com", "password": "Segura123"}'
```

**Login y obtención del token:**

```bash
curl -X POST http://localhost/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin1234!"}'
```

Respuesta:
```json
{ "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." }
```

**Crear encuesta** (el campo `created_by` lo toma el servidor del JWT):

```bash
curl -X POST http://localhost/api/surveys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "¿Mejor lenguaje?", "description": "Vota tu favorito"}'
```

**Añadir pregunta a una encuesta:**

```bash
curl -X POST http://localhost/api/surveys/1/questions \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"text": "¿Cuál prefieres?", "type": "single"}'
```

**Añadir opción a una pregunta:**

```bash
curl -X POST http://localhost/api/questions/1/options \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"text": "Python"}'
```

**Votar** (el campo `user_id` lo toma el servidor del JWT):

```bash
curl -X POST http://localhost/api/votes \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question_id": 1, "option_id": 2}'
```

---

## Autenticación JWT

### Flujo completo

```
1. POST /auth/login
       │
       ▼  valida credenciales + check_password_hash
   Servidor genera token firmado con HMAC-SHA256
       │   payload: { id, username, role, exp (+1h) }
       ▼
   Respuesta: { "token": "eyJ..." }
       │
       ▼  cliente almacena en localStorage
   Cada petición a /api/*:
       │   cabecera: Authorization: Bearer <token>
       ▼
   Decorador @token_required() valida:
       ├── Presencia de cabecera "Bearer ..."
       ├── Firma correcta (JWT_SECRET_KEY)
       ├── Token no expirado (exp)
       └── Inyecta g.current_user = { id, username, role }
```

### Implementación por archivo

| Función / decorador        | Archivo          | Descripción                                         |
|----------------------------|------------------|-----------------------------------------------------|
| `generate_token(user)`     | [`app/utils.py:15`](app/utils.py#L15) | Genera JWT con id, username, role y exp (+1 hora) |
| `@token_required(role=None)` | [`app/utils.py:25`](app/utils.py#L25) | Decorador de protección; inyecta `g.current_user` |
| `_get_secret()`            | [`app/utils.py:8`](app/utils.py#L8)  | Obtiene `JWT_SECRET_KEY` o lanza RuntimeError     |
| `login()`                  | [`app/routes/auth.py:40`](app/routes/auth.py#L40) | Valida credenciales, llama a `generate_token` |

---

## Seguridad – OWASP Top 10 Web 2025

### A01 – Broken Access Control (Control de Acceso Roto)

**Problema mitigado:** Acceso a recursos sin autorización, IDOR (Insecure Direct Object Reference), redirección abierta (Open Redirect).

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Todos los endpoints `/api/*` requieren JWT válido | `@token_required()` en cada ruta | [`app/routes/api.py`](app/routes/api.py) |
| El `created_by` de una encuesta se toma del JWT, nunca del body | `created_by = g.current_user["id"]` | [`app/routes/api.py`](app/routes/api.py) |
| El `user_id` del voto se toma del JWT, nunca del body | `user_id = g.current_user["id"]` | [`app/routes/api.py`](app/routes/api.py) |
| Control de roles: el decorador acepta parámetro `role=` | `if role and data.get("role") != role` | [`app/utils.py`](app/utils.py) |
| Un usuario solo puede votar una vez por pregunta | `UniqueConstraint("question_id", "user_id", "option_id")` | [`app/models/survey.py`](app/models/survey.py) |
| **IDOR en preguntas:** solo el creador puede añadir preguntas | `if survey.created_by != g.current_user["id"]: return 403` | [`app/routes/api.py`](app/routes/api.py) |
| **IDOR en opciones:** solo el creador puede añadir opciones | Verificación de propiedad a través de `question → survey` | [`app/routes/api.py`](app/routes/api.py) |
| **Vote tampering:** la opción debe pertenecer a la pregunta | `if option.question_id != question_id: return 400` | [`app/routes/api.py`](app/routes/api.py) |
| **Open Redirect en login:** `?siguiente=` solo acepta rutas relativas | `siguiente.startsWith('/') && !siguiente.startsWith('//')` | [`app/static/login.js`](app/static/login.js) |

> **IDOR (Insecure Direct Object Reference):** sin los controles de propiedad, cualquier usuario autenticado podía añadir preguntas y opciones a encuestas ajenas mediante `POST /api/surveys/<id>/questions`. Ahora el servidor verifica `survey.created_by == token.id`. Cubierto en norma CCN-CERT IC-03 (Gestión de acceso a objetos).

> **Vote Tampering:** sin la verificación de pertenencia, un atacante podía enviar `{"question_id": 1, "option_id": 99}` donde la opción 99 pertenece a otra pregunta, adulterando resultados. Ahora se verifica la coherencia pregunta↔opción.

> **Open Redirect:** `?siguiente=https://evil.com` causaba redirección a un dominio externo tras login, vector de phishing. Ahora solo se aceptan paths que empiecen por `/` y no por `//`.

---

### A02 – Cryptographic Failures (Fallos Criptográficos)

**Problema mitigado:** Contraseñas en texto plano, claves hardcodeadas, tokens expuestos.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Contraseñas hasheadas con PBKDF2-SHA256 al registrar | `generate_password_hash(password)` | [`app/routes/auth.py:49`](app/routes/auth.py#L49) |
| Verificación segura sin comparación directa | `check_password_hash(user.password, password)` | [`app/routes/auth.py:62`](app/routes/auth.py#L62) |
| Claves secretas en variables de entorno | `os.getenv("JWT_SECRET_KEY")` | [`app/utils.py:9`](app/utils.py#L9) |
| Error explícito si la clave no está definida | `raise RuntimeError(...)` | [`app/utils.py:11`](app/utils.py#L11) |
| JWT firmado con HMAC-SHA256 | `jwt.encode(..., algorithm="HS256")` | [`app/utils.py:22`](app/utils.py#L22) |
| JWT nunca se muestra en la interfaz | Token eliminado del dashboard | [`app/templates/dashboard.html`](app/templates/dashboard.html) |
| `.env` excluido del repositorio | Entrada en `.gitignore` | [`.gitignore`](.gitignore) |

---

### A03 – Injection (Inyección SQL y XSS)

**Problema mitigado:** Consultas SQL concatenadas, inyección de HTML en la interfaz.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Todas las consultas usan SQLAlchemy ORM con parámetros enlazados | `User.query.filter_by(username=username)` | [`app/routes/auth.py`](app/routes/auth.py), [`app/routes/api.py`](app/routes/api.py) |
| Sin ninguna consulta SQL manual con f-strings | Ningún `db.execute(f"...")` en el código | — |
| Todo el HTML dinámico pasa por la función `esc()` | `.replace(/</g,'&lt;')`, etc. | [`app/static/dashboard.js`](app/static/dashboard.js), [`app/static/survey_vote.js`](app/static/survey_vote.js) |
| `esc()` escapa los 5 caracteres peligrosos: `&`, `<`, `>`, `"`, `'` | `.replace(/'/g,'&#x27;')` (comilla simple) | [`app/static/dashboard.js`](app/static/dashboard.js) |
| Longitud máxima en todos los campos de texto | `len(title) > 200`, `len(text) > 500`, `len(text) > 300` | [`app/routes/api.py`](app/routes/api.py) |
| CSP `script-src 'self'` bloquea scripts inline y externos | Cabecera `Content-Security-Policy` en nginx | [`nginx/nginx.conf`](nginx/nginx.conf) |
| CSP `object-src 'none'` bloquea plugins (Flash, Java applets) | Añadido a la directiva CSP | [`nginx/nginx.conf`](nginx/nginx.conf) |

> **XSS via comilla simple:** la versión anterior de `esc()` no escapaba `'`. Un atacante con texto como `'; fetch('//evil')//` en un atributo HTML podía inyectar eventos. Ahora se escapa a `&#x27;`.

---

### A04 – Insecure Design (Diseño Inseguro)

**Problema mitigado:** Arquitectura sin separación de responsabilidades, sin principio de mínimo privilegio.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Patrón App Factory para configuración por entorno | `def create_app(test_config=None)` | [`app/main.py:29`](app/main.py#L29) |
| Modelos separados de rutas separados de templates | Estructura `models/`, `routes/`, `templates/` | Toda la carpeta `app/` |
| Usuario no-root en el contenedor Docker | `RUN useradd -m appuser` + `exec gosu appuser gunicorn` | [`Dockerfile`](Dockerfile) |
| Red interna Docker: web y db no expuestos al exterior | `networks: internal`, solo nginx expone puerto 80 | [`docker-compose.yml`](docker-compose.yml) |
| Verificación de variables de entorno al arrancar | `REQUIRED_ENV_VARS` loop en módulo raíz | [`app/main.py:16`](app/main.py#L16) |

---

### A05 – Security Misconfiguration (Mala Configuración de Seguridad)

**Problema mitigado:** Versiones de servidor visibles, errores con stack traces, configuraciones por defecto inseguras, caché de datos sensibles.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Nginx oculta versión del servidor | `server_tokens off;` | [`nginx/nginx.conf`](nginx/nginx.conf) |
| Timeouts de conexión configurados | `client_body_timeout 10s`, etc. | [`nginx/nginx.conf`](nginx/nginx.conf) |
| Límite de tamaño en nginx y Flask | `client_max_body_size 5M` + `MAX_CONTENT_LENGTH = 5 MB` | [`nginx/nginx.conf`](nginx/nginx.conf), [`app/main.py`](app/main.py) |
| Error 500 devuelve mensaje genérico, sin stack trace | `@app.errorhandler(500)` con log interno | [`app/main.py`](app/main.py) |
| Error 404 devuelve JSON, no página Flask por defecto | `@app.errorhandler(404)` | [`app/main.py`](app/main.py) |
| Dockerfile sin compiladores en producción | Imagen `python:3.12-slim` + solo dependencias runtime | [`Dockerfile`](Dockerfile) |
| Recursos limitados por contenedor | `cpus: "0.50"`, `memory: 512M` | [`docker-compose.yml`](docker-compose.yml) |
| Healthchecks en todos los servicios | `healthcheck:` en db, web, nginx | [`docker-compose.yml`](docker-compose.yml) |
| **Cache-Control en respuestas autenticadas** | `no-store, no-cache, must-revalidate, private` en `/api/` y `/auth/` | [`nginx/nginx.conf`](nginx/nginx.conf) |
| **Path Traversal en subida de imágenes** | `os.path.basename()` antes de extraer extensión y al construir URLs | [`app/routes/api.py`](app/routes/api.py) |
| `X-Permitted-Cross-Domain-Policies: none` | Impide carga de políticas desde dominios externos | [`nginx/nginx.conf`](nginx/nginx.conf) |
| `X-XSS-Protection: 0` (reemplaza el `1; mode=block` deprecated) | El valor `1` puede crear vulnerabilidades en navegadores modernos | [`nginx/nginx.conf`](nginx/nginx.conf) |
| `Referrer-Policy: strict-origin` | Solo envía el origen (sin path) en cabecera Referer | [`nginx/nginx.conf`](nginx/nginx.conf) |

> **Path Traversal:** un atacante podía enviar un filename como `../../etc/passwd.jpg`. Aunque el UUID rename ya lo neutralizaba en el almacenamiento, el procesador de extensiones y la función `_img_url()` operaban sobre el nombre sin sanear. Ahora se aplica `os.path.basename()` antes de cualquier operación.

> **Cache-Control:** sin esta cabecera, respuestas con votos, encuestas o datos del usuario podían quedar cacheadas en el navegador o proxies intermedios, exponiendo datos de otras sesiones en equipos compartidos.

---

### A07 – Identification and Authentication Failures (Fallos de Autenticación)

**Problema mitigado:** Credenciales en URL, tokens sin expiración, ataques de fuerza bruta, contraseñas débiles, vote stuffing.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Tokens JWT con expiración de 1 hora | `timedelta(hours=1)` en el payload `exp` | [`app/utils.py`](app/utils.py) |
| Error de login genérico (no indica si falla usuario o contraseña) | `"Invalid credentials"` en ambos casos | [`app/routes/auth.py`](app/routes/auth.py) |
| Rate limiting en login: máx. 10 peticiones/min por IP | `limiter.limit("10 per minute")` | [`app/main.py`](app/main.py) |
| Rate limiting en registro: máx. 5 peticiones/min por IP | `limiter.limit("5 per minute")` | [`app/main.py`](app/main.py) |
| **Rate limiting en creación de encuestas: máx. 20/min** | `limiter.limit("20 per minute")` en `create_survey` | [`app/main.py`](app/main.py) |
| **Rate limiting en votos: máx. 60/min** (anti vote-stuffing) | `limiter.limit("60 per minute")` en `vote` | [`app/main.py`](app/main.py) |
| Respuesta 429 con mensaje claro al superar el límite | `@app.errorhandler(429)` | [`app/main.py`](app/main.py) |
| Validación de complejidad de contraseña | Mín. 8 chars + mayúscula + minúscula + dígito | [`app/routes/auth.py`](app/routes/auth.py) |
| Validación de formato de email con regex | `_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")` | [`app/routes/auth.py:14`](app/routes/auth.py#L14) |
| Validación de username con caracteres seguros | `_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")` | [`app/routes/auth.py:15`](app/routes/auth.py#L15) |
| Login usa fetch JSON, nunca GET con credenciales en URL | `fetch('/auth/login', {method:'POST',...})` | [`app/static/login.js`](app/static/login.js) |
| Rollback de sesión DB en caso de error durante el registro | `try/except SQLAlchemyError` con `db.session.rollback()` | [`app/routes/auth.py`](app/routes/auth.py) |

---

### A09 – Security Logging and Monitoring

**Problema mitigado:** Falta de trazabilidad de eventos de seguridad.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Gunicorn registra cada petición: IP, método, ruta, código, tiempo | Configuración por defecto de Gunicorn | [`wsgi.py`](wsgi.py) |
| Nginx registra todas las peticiones entrantes | Log de acceso Nginx | [`nginx/nginx.conf`](nginx/nginx.conf) |
| Códigos HTTP semánticos en todas las respuestas | 200, 201, 400, 401, 403, 404, 429, 500 | [`app/routes/api.py`](app/routes/api.py), [`app/routes/auth.py`](app/routes/auth.py) |
| El ID del usuario nunca se expone en la UI | Stat card de User ID eliminada | [`app/templates/dashboard.html`](app/templates/dashboard.html) |

---

## Seguridad – OWASP API Security Top 10

La API de GalApp implementa medidas específicas contra las vulnerabilidades del [OWASP API Security Top 10](https://owasp.org/API-Security/editions/2023/en/0x11-t10/).

### API1:2023 – Broken Object Level Authorization

**Riesgo:** Un usuario autenticado puede acceder o modificar objetos que no le pertenecen usando su ID en la URL.

| Medida | Dónde |
|--------|-------|
| Solo el creador de una encuesta puede añadirle preguntas (`created_by == token.id`) | [`app/routes/api.py`](app/routes/api.py) — `add_question()` |
| Solo el creador puede añadir opciones a sus preguntas (verificación a través de FK) | [`app/routes/api.py`](app/routes/api.py) — `add_option()` |
| Los resultados y votos solo se devuelven al usuario autenticado que los solicita | [`app/routes/api.py`](app/routes/api.py) — `my_votes()`, `results()` |

### API2:2023 – Broken Authentication

**Riesgo:** Tokens débiles, sin expiración, o sin validación completa.

| Medida | Dónde |
|--------|-------|
| JWT firmado con HMAC-SHA256, expiración 1 hora | [`app/utils.py`](app/utils.py) |
| Validación de firma, expiración y formato en cada request | [`app/utils.py`](app/utils.py) — `@token_required()` |
| Rate limiting 10 req/min en login (anti brute-force) | [`app/main.py`](app/main.py) |

### API3:2023 – Broken Object Property Level Authorization

**Riesgo:** El cliente puede sobrescribir campos del servidor (mass assignment).

| Medida | Dónde |
|--------|-------|
| `created_by` de encuesta → siempre del JWT, no del body | [`app/routes/api.py`](app/routes/api.py) |
| `user_id` del voto → siempre del JWT, no del body | [`app/routes/api.py`](app/routes/api.py) |
| Solo se leen campos explícitos del JSON (`title`, `description`, `text`, `type`) | [`app/routes/api.py`](app/routes/api.py) |

### API4:2023 – Unrestricted Resource Consumption

**Riesgo:** Un cliente puede hacer flood de requests o subir archivos enormes.

| Medida | Dónde |
|--------|-------|
| Rate limits por IP en todos los endpoints sensibles | [`app/main.py`](app/main.py) |
| `MAX_CONTENT_LENGTH = 5 MB` en Flask | [`app/main.py`](app/main.py) |
| `client_max_body_size 5M` en nginx | [`nginx/nginx.conf`](nginx/nginx.conf) |
| Límite de longitud en todos los campos de texto | [`app/routes/api.py`](app/routes/api.py) |
| Límites de recursos Docker (`cpus`, `memory`) | [`docker-compose.yml`](docker-compose.yml) |

### API5:2023 – Broken Function Level Authorization

**Riesgo:** Acceso a funciones administrativas por usuarios no autorizados.

| Medida | Dónde |
|--------|-------|
| Decorador `@token_required(role="admin")` para operaciones administrativas | [`app/utils.py`](app/utils.py) |
| Respuesta 403 cuando el rol no coincide | [`app/utils.py`](app/utils.py) |

### API6:2023 – Unrestricted Access to Sensitive Business Flows

**Riesgo:** Automatización masiva de votos o registros, incluyendo votantes anónimos sin autenticación.

| Medida | Dónde |
|--------|-------|
| Rate limit 60 req/min en `/api/votes` (usuarios autenticados) | [`app/main.py`](app/main.py) |
| Rate limit **30 req/min** en `/api/public/*/vote` (votantes anónimos — más restrictivo) | [`app/main.py`](app/main.py) |
| Rate limit 5 req/min en `/auth/register` | [`app/main.py`](app/main.py) |
| `UniqueConstraint("question_id", "user_id")` impide doble voto de usuario registrado | [`app/models/survey.py`](app/models/survey.py) |
| `UniqueConstraint("voter_token", "question_id")` impide doble voto anónimo aunque se eluda el rate limit | [`app/models/survey.py`](app/models/survey.py) |
| Validación de formato UUID del `voter_token` — tokens malformados → 400 inmediato | [`app/routes/api.py`](app/routes/api.py) — `_voter_token()` |

### API8:2023 – Security Misconfiguration

**Riesgo:** Headers de seguridad ausentes, versiones de servidor visibles, CORS permisivo.

| Medida | Dónde |
|--------|-------|
| CSP, X-Frame-Options, X-Content-Type-Options, Permissions-Policy | [`nginx/nginx.conf`](nginx/nginx.conf) |
| `server_tokens off` (oculta versión Nginx) | [`nginx/nginx.conf`](nginx/nginx.conf) |
| `Cache-Control: no-store` en endpoints autenticados | [`nginx/nginx.conf`](nginx/nginx.conf) |
| Sin CORS `*` — fetch solo al mismo origen | [`nginx/nginx.conf`](nginx/nginx.conf) CSP `connect-src 'self'` |

### API9:2023 – Improper Inventory Management

**Riesgo:** Endpoints de debug o versiones antiguas de la API expuestos.

| Medida | Dónde |
|--------|-------|
| No hay endpoints de debug (`/debug`, `/test`, `/v0/*`) en producción | [`app/routes/api.py`](app/routes/api.py) |
| `GET /api/health` es el único endpoint público de estado, sin información sensible | [`app/routes/api.py`](app/routes/api.py) |

---

## Cabeceras de seguridad HTTP

Configuradas en [`nginx/nginx.conf`](nginx/nginx.conf) para todas las respuestas:

| Cabecera | Valor | Protección |
|----------|-------|------------|
| `X-Frame-Options` | `DENY` | Evita clickjacking / iframes maliciosos |
| `X-Content-Type-Options` | `nosniff` | Evita MIME-sniffing del navegador |
| `X-XSS-Protection` | `0` | Desactiva el filtro XSS legacy (deprecated, puede crear vulnerabilidades) |
| `Referrer-Policy` | `strict-origin` | Solo envía el origen (sin path ni query string) en Referer |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=(), payment=()` | Deshabilita APIs sensibles del navegador |
| `X-Permitted-Cross-Domain-Policies` | `none` | Impide que Flash/PDF carguen políticas de dominio |
| `Content-Security-Policy` | Ver tabla siguiente | Bloquea scripts/estilos inline y recursos externos no autorizados |
| `Cache-Control` *(solo /api/ y /auth/)* | `no-store, no-cache, must-revalidate, private` | Impide que proxies y navegadores cacheen datos autenticados |

### Content-Security-Policy detallada

| Directiva | Valor | Motivo |
|-----------|-------|--------|
| `default-src` | `'self'` | Todo recurso debe ser del mismo origen por defecto |
| `script-src` | `'self'` | Sin scripts inline ni externos no autorizados |
| `style-src` | `'self' https://fonts.googleapis.com` | Google Fonts CSS |
| `font-src` | `'self' https://fonts.gstatic.com` | Google Fonts archivos |
| `img-src` | `'self' data: blob:` | Imágenes propias + previsualizaciones FileReader |
| `connect-src` | `'self'` | `fetch()` solo al mismo origen |
| `form-action` | `'self'` | Los formularios solo envían al mismo origen |
| `base-uri` | `'self'` | Bloquea inyección de `<base href>` |
| `frame-ancestors` | `'none'` | Nadie puede incrustar la app en un iframe |
| `object-src` | `'none'` | Bloquea plugins (Flash, Java Applets, PDF inline) |

> La CSP `default-src 'self'` es la razón por la que todo el JavaScript y CSS está en archivos externos (`/static/`). Los scripts inline quedarían bloqueados por el navegador.

> **HSTS preparado:** cuando se configure HTTPS, añadir `Strict-Transport-Security: max-age=31536000; includeSubDomains` en `nginx.conf` (la línea está comentada lista para activar).

---

## CCN-CERT – Estándares aplicados

El proyecto toma como referencia las **Guías CCN-STIC** del Centro Criptológico Nacional (CCN-CERT), organismo del CNI responsable de la ciberseguridad en España.

| Guía CCN-STIC | Título | Medidas aplicadas en GalApp |
|--------------|--------|------------------------------|
| **CCN-STIC-812** | Seguridad en entornos y aplicaciones web | CSP, cabeceras HTTP, XSS, CSRF, rate limiting, validación de entrada |
| **CCN-STIC-817** | Gestión de ciberincidentes | Logging en Gunicorn y Nginx, códigos HTTP semánticos, trazabilidad |
| **CCN-STIC-821** | Ciclo de vida del desarrollo seguro (SSDLC) | GitFlow, tests en CI/CD, revisión de código, dependencias fijadas |
| **CCN-STIC-870** | Seguridad en contenedores | Usuario no-root (`appuser`), imagen mínima (`python:3.12-slim`), red interna Docker, límites de recursos |

### Aplicación concreta por área

**Gestión de identidades y accesos (CCN-STIC-812 §4):**
- Autenticación basada en JWT con expiración — [`app/utils.py`](app/utils.py)
- Hash PBKDF2-SHA256 para contraseñas — [`app/routes/auth.py`](app/routes/auth.py)
- Control de acceso por objeto (IDOR prevention) — [`app/routes/api.py`](app/routes/api.py)
- Dos roles diferenciados (`user`, `admin`) con tema visual distinto — [`app/models/user.py`](app/models/user.py), [`app/static/dashboard.css`](app/static/dashboard.css)

**Comunicaciones seguras (CCN-STIC-812 §5):**
- TLS listo para activar (HSTS preparado en nginx)
- `Cache-Control: no-store` en endpoints autenticados
- Cabecera `Referrer-Policy: strict-origin`

**Seguridad en el desarrollo (CCN-STIC-821):**
- Pipeline CI con lint (flake8) y tests automáticos — [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
- GitFlow estricto con ramas `feature/`, `develop`, `release/`, `hotfix/`
- Tests de regresión de seguridad (IDOR, vote tampering, open redirect) — [`tests/`](tests/)

**Contenedores (CCN-STIC-870):**
- Sin compiladores en imagen de producción (superficie de ataque reducida)
- `gosu` para transición segura al usuario no-root en el entrypoint
- Volumen persistente para uploads separado del código fuente
- Healthchecks y dependencias entre servicios bien definidas

---

## Base de datos

Motor: **PostgreSQL 15** gestionado con **Flask-SQLAlchemy**.
Las tablas se crean automáticamente en el primer arranque con `db.create_all()` ([`app/main.py`](app/main.py)).

### Modelo `users` — [`app/models/user.py`](app/models/user.py)

| Campo    | Tipo        | Restricciones            |
|----------|-------------|--------------------------|
| id       | Integer     | PK, autoincrement        |
| username | String(80)  | UNIQUE, NOT NULL         |
| email    | String(120) | UNIQUE, NOT NULL         |
| password | String(255) | NOT NULL — hash PBKDF2   |
| role     | String(20)  | NOT NULL, default `user` |

### Modelo `surveys` — [`app/models/survey.py`](app/models/survey.py)

| Campo       | Tipo        | Restricciones             |
|-------------|-------------|---------------------------|
| id          | Integer     | PK                        |
| title       | String(200) | NOT NULL                  |
| description | Text        | Opcional                  |
| image_url   | String(255) | Opcional (ruta interna)   |
| created_by  | Integer     | FK → users.id (del JWT)   |
| created_at  | DateTime    | UTC, automático           |

### Modelo `questions` — [`app/models/survey.py`](app/models/survey.py)

| Campo         | Tipo       | Restricciones             |
|---------------|------------|---------------------------|
| id            | Integer    | PK                        |
| survey_id     | Integer    | FK → surveys.id           |
| text          | String(500)| NOT NULL                  |
| question_type | String(20) | `single` o `multiple`     |
| order         | Integer    | Para ordenación           |

### Modelo `question_options` — [`app/models/survey.py`](app/models/survey.py)

| Campo       | Tipo        | Restricciones            |
|-------------|-------------|--------------------------|
| id          | Integer     | PK                       |
| question_id | Integer     | FK → questions.id        |
| text        | String(300) | NOT NULL                 |
| image_url   | String(255) | Opcional                 |

### Modelo `votes` — [`app/models/survey.py`](app/models/survey.py)

| Campo       | Tipo     | Restricciones                                          |
|-------------|----------|--------------------------------------------------------|
| id          | Integer  | PK                                                     |
| question_id | Integer  | FK → questions.id                                      |
| user_id     | Integer  | FK → users.id (tomado del JWT)                         |
| option_id   | Integer  | FK → question_options.id                               |
| created_at  | DateTime | UTC, automático                                        |
| —           | —        | `UNIQUE(question_id, user_id)` — un voto por usuario por pregunta |

### Modelo `anon_votes` — [`app/models/survey.py`](app/models/survey.py)

Tabla separada para votos anónimos (sin FK a `users`). Convive con `votes` sin alterar su esquema.

| Campo        | Tipo        | Restricciones                                               |
|--------------|-------------|-------------------------------------------------------------|
| id           | Integer     | PK                                                          |
| voter_token  | String(36)  | NOT NULL, indexado — UUID v4 del navegador                  |
| question_id  | Integer     | FK → questions.id                                           |
| option_id    | Integer     | FK → question_options.id                                    |
| created_at   | DateTime    | UTC, automático                                             |
| —            | —           | `UNIQUE(voter_token, question_id)` — un voto anónimo por pregunta |

> El servidor **nunca almacena** el `voter_token` vinculado a ninguna identidad real. Se usa exclusivamente para deduplicación y puede rotar si el usuario borra su `localStorage`.

### Relación entre tablas

```
users ──────────────────────── votes
  (id)                       (user_id FK)
                              (question_id FK) ──┐
                              (option_id FK)  ──┐│
                                               ││
surveys ── questions ─────────────────────────┘│
             (id)  └── question_options ────────┘
                             (id)

anon_votes (sin FK a users)
  voter_token  (UUID de localStorage)
  question_id  FK → questions.id
  option_id    FK → question_options.id
  UNIQUE(voter_token, question_id)
```

---

## Contenedorización Docker

### Servicios — [`docker-compose.yml`](docker-compose.yml)

| Servicio | Imagen              | Puerto | Red      | Descripción                              |
|----------|---------------------|--------|----------|------------------------------------------|
| `db`     | postgres:15-alpine  | 5432   | internal | Base de datos PostgreSQL                 |
| `web`    | galapp-web (build)  | 8000   | internal | Flask + Gunicorn (no expuesto al host)   |
| `nginx`  | nginx:stable-alpine | 80→80  | internal | Proxy inverso, único punto de entrada    |

**Solo el puerto 80 de nginx está expuesto al host.** Los servicios `db` y `web` son accesibles únicamente dentro de la red interna Docker `galapp_internal`.

### Dockerfile — [`Dockerfile`](Dockerfile)

Imagen única `python:3.12-slim` sin compiladores (todos los paquetes usan wheels pre-compilados):

```
FROM python:3.12-slim
│
├── apt: libpq5, curl, gosu  (solo runtime, sin build-essential)
├── useradd -m appuser        (usuario no-root)
├── pip install requirements.txt
├── COPY app/ + wsgi.py
├── mkdir uploads/ + chown appuser
└── ENTRYPOINT /entrypoint.sh
        └── mkdir uploads/  →  chown appuser  →  exec gosu appuser gunicorn
```

Ventajas de seguridad:
- La imagen final no contiene compiladores (superficie de ataque reducida)
- Si hay una vulnerabilidad en el contenedor, el atacante no puede compilar herramientas
- `gosu` garantiza que Gunicorn se ejecuta como `appuser`, no como root

### Healthchecks

Cada servicio tiene un healthcheck configurado. Docker Compose los respeta en el orden de arranque:

```
db (pg_isready) → HEALTHY
    │
    ▼
web (curl /api/health) → HEALTHY
    │
    ▼
nginx (wget /) → HEALTHY
```

Si `web` no pasa su healthcheck, nginx no arranca.

### Límites de recursos

```yaml
# Cada servicio tiene límites para evitar consumo descontrolado
cpus: "0.50"       # Máx. 50% de un núcleo
memory: 512M       # db y web
memory: 256M       # nginx
```

### Volumen persistente

```yaml
volumes:
  postgres_data:   # Los datos de PostgreSQL sobreviven a docker compose down
  uploads_data:    # Las imágenes subidas por usuarios sobreviven a reinicios
                   # Para borrarlos: docker compose down -v
```

---

## Testing

**62 tests — 0 fallos.** Usan **SQLite en memoria**: no requieren Docker ni PostgreSQL para ejecutarse.

### Ejecución

```bash
# Dentro del contenedor (recomendado — mismas dependencias que producción)
docker compose exec web python -m pytest tests/ -v

# Local (requiere pip install -r requirements.txt)
python -m pytest tests/ -v
```

### Infraestructura — [`tests/conftest.py`](tests/conftest.py)

El fixture `client` crea una instancia de la app con `test_config`:
- `SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"`
- `db.create_all()` antes de cada test → `db.drop_all()` al terminar
- Sin estado compartido entre tests

Helpers reutilizables expuestos desde `conftest.py`:

| Helper | Descripción |
|--------|-------------|
| `register(client, ...)` | POST /auth/register con datos por defecto sobreescribibles |
| `login(client, ...)` | POST /auth/login |
| `auth_headers(client, ...)` | Registra + hace login y devuelve `{"Authorization": "Bearer ..."}` listo para usar |

---

### Tests unitarios

Validan lógica interna **sin levantar servidor HTTP**.

#### [`tests/test_auth.py`](tests/test_auth.py) — `TestGenerateToken` / `TestGetSecret`

| Test | Qué verifica |
|------|-------------|
| `test_returns_string` | `generate_token` devuelve string con formato `header.payload.signature` |
| `test_payload_contains_required_claims` | El JWT contiene `id`, `username`, `role` y `exp` con los valores correctos |
| `test_token_expires_in_about_one_hour` | El campo `exp` está entre 59 y 61 minutos en el futuro |
| `test_raises_if_missing` | `_get_secret()` lanza `RuntimeError` si `JWT_SECRET_KEY` no está definida |

#### [`tests/test_surveys.py`](tests/test_surveys.py) — `TestSurveyModel`

| Test | Qué verifica |
|------|-------------|
| `test_survey_created_correctly` | El modelo `Survey` se persiste con `id` y `created_at` automáticos |
| `test_question_option_linked_to_survey` | `Question` y `QuestionOption` quedan enlazadas vía FK |
| `test_vote_unique_constraint` | La `UniqueConstraint(question_id, user_id)` lanza `IntegrityError` en doble voto |

#### [`tests/test_votes.py`](tests/test_votes.py) — `TestVoteModel`

| Test | Qué verifica |
|------|-------------|
| `test_same_user_cannot_vote_twice_in_db` | La BD rechaza dos votos del mismo usuario en la misma pregunta |
| `test_different_users_can_vote_same_option` | Dos usuarios distintos pueden votar la misma opción sin conflicto |

---

### Tests de integración

Cubren el **flujo HTTP completo** a través del cliente de test Flask.

#### [`tests/test_auth.py`](tests/test_auth.py) — Registro (11 casos)

| Test | Código esperado |
|------|----------------|
| `test_success_returns_201` | 201 |
| `test_missing_username/email/password_returns_400` | 400 |
| `test_duplicate_username_returns_400` | 400 |
| `test_duplicate_email_returns_400` | 400 |
| `test_weak_password_*_returns_400` (3 variantes) | 400 |
| `test_invalid_email_returns_400` | 400 |
| `test_invalid_username_*_returns_400` (2 variantes) | 400 |
| `test_empty_body_returns_400` | 400 |

#### [`tests/test_auth.py`](tests/test_auth.py) — Login (6 casos)

| Test | Código esperado |
|------|----------------|
| `test_success_returns_token` | 200 + `token` con formato JWT |
| `test_wrong_password_returns_401` | 401 |
| `test_nonexistent_user_returns_401` | 401 |
| `test_missing_username/password_returns_400` | 400 |
| `test_empty_body_returns_400` | 400 |
| `test_error_message_is_generic` | Mismo mensaje para usuario y contraseña incorrectos (OWASP A07) |

#### [`tests/test_auth.py`](tests/test_auth.py) — Protección JWT (4 casos)

| Test | Qué verifica |
|------|-------------|
| `test_no_token_returns_401` | Sin cabecera Authorization → 401 |
| `test_invalid_token_returns_401` | Token con firma inválida → 401 |
| `test_malformed_header_returns_401` | Header sin prefijo `Bearer` → 401 |
| `test_valid_token_grants_access` | Token válido → acceso concedido (200) |

#### [`tests/test_surveys.py`](tests/test_surveys.py) — CRUD de encuestas (18 casos)

| Test | Código esperado |
|------|----------------|
| `test_returns_empty_list_initially` | 200 + `[]` |
| `test_returns_created_survey` | 200 + array con la encuesta creada |
| `test_success_returns_201_with_id` | 201 + `id` numérico |
| `test_missing_title_returns_400` | 400 |
| `test_title_too_long_returns_400` (201 chars) | 400 |
| `test_created_by_is_taken_from_jwt_not_body` | 201 y `created_by ≠ 9999` (IDOR) |
| `test_survey_without_description_is_ok` | 201 |
| `test_returns_survey_with_questions_and_options` | 200 + `questions[0].options[0]` |
| `test_nonexistent_survey_returns_404` | 404 |
| `test_add_question_success` | 201 + `id` |
| `test_missing_text_returns_400` | 400 |
| `test_invalid_type_returns_400` | 400 |
| `test_non_owner_cannot_add_question` | **403** (IDOR protection) |
| `test_add_option_success` | 201 |
| `test_missing_option_text_returns_400` | 400 |
| `test_option_text_too_long_returns_400` (301 chars) | 400 |
| `test_non_owner_cannot_add_option` | **403** (IDOR protection) |
| Todos los endpoints sin token | 401 |

#### [`tests/test_votes.py`](tests/test_votes.py) — Votación (8 casos + 1 end-to-end)

| Test | Qué verifica |
|------|-------------|
| `test_success_returns_201` | Voto registrado correctamente |
| `test_double_vote_returns_400` | El mismo usuario no puede votar dos veces (single) |
| `test_user_id_is_taken_from_jwt_not_body` | Enviar `user_id: 9999` no suplanta a otro usuario (IDOR) |
| `test_two_different_users_can_vote` | Dos usuarios distintos votan con éxito |
| `test_invalid_option_for_question_returns_400` | **Vote tampering:** opción de otra pregunta → 400 |
| `test_missing_question_id/option_id_returns_400` | 400 por campos faltantes |
| `test_unauthenticated_returns_401` | 401 sin token |
| `test_register_login_create_vote` | Flujo completo: registro → login → encuesta → preguntas → opciones → voto → doble voto bloqueado |

#### [`tests/test_health.py`](tests/test_health.py) — Health y error handlers (4 casos)

| Test | Qué verifica |
|------|-------------|
| `test_health_returns_200` | GET /api/health devuelve `{"status": "ok"}` |
| `test_health_no_auth_required` | El endpoint es público (sin JWT) |
| `test_404_returns_json` | Las rutas inexistentes devuelven JSON, no HTML de Flask |
| `test_404_no_stack_trace` | La respuesta no contiene `Traceback` ni rutas internas |

---

## CI/CD – GitHub Actions

Archivo: [`.github/workflows/ci.yml`](.github/workflows/ci.yml)

El pipeline se ejecuta automáticamente en cada `push` y `pull_request` sobre cualquier rama.

### Pasos del pipeline

```
1. Checkout del repositorio
2. Setup Python 3.11
3. Instalar dependencias (pip install -r requirements.txt)
4. Lint: flake8 app/ --max-line-length=120
5. Levantar servicio PostgreSQL 15 como service container de GitHub Actions
6. Ejecutar pytest -v
```

### Variables de entorno en CI

```yaml
PYTHONPATH: .
POSTGRES_HOST: localhost
POSTGRES_USER: postgres
POSTGRES_PASSWORD: postgres
POSTGRES_DB: galapp
SECRET_KEY: test
JWT_SECRET_KEY: test
```

### Estrategia de calidad

| Nivel | Herramienta | Qué detecta |
|-------|-------------|-------------|
| Lint estático | flake8 | Errores de estilo, imports no usados, líneas demasiado largas |
| Tests unitarios | pytest | Lógica de modelos, utils, JWT |
| Tests de integración | pytest + SQLite | Flujos HTTP completos, IDOR, vote tampering |
| Tests con BD real | pytest + PostgreSQL 15 | Constraints, transacciones, integridad referencial |

El CI **no despliega** la aplicación. Solo valida que los tests pasan en cada commit.

---

## GitFlow

El proyecto sigue la estrategia **GitFlow** de forma estricta.

### Diagrama de ramas

```
main ────────────────────────────────────────── (producción, protegida)
  │                              ▲
  │                              │ merge + tag
  │                         release/1.0.0
  │                              ▲
  │                              │ merge cuando develop está estable
develop ──────────────────────────────────────── (integración continua)
  │         ▲         ▲         ▲
  │         │         │         │ merge tras revisión + CI verde
  │     feature/  feature/  feature/
  │     docker-   jwt-auth   owasp-
  │     hardening            hardening
  │
  └── hotfix/critical-security-fix → merge a main + develop
```

### Tipos de ramas

| Rama | Origen | Destino | Propósito |
|------|--------|---------|-----------|
| `main` | — | — | Código en producción. Solo recibe merges de `release/*` y `hotfix/*` |
| `develop` | `main` | `main` vía release | Integración de todas las features. Base para nuevas ramas |
| `feature/*` | `develop` | `develop` | Nueva funcionalidad o mejora |
| `release/*` | `develop` | `main` + `develop` | Preparación de versión: tests, bumps de versión, documentación |
| `hotfix/*` | `main` | `main` + `develop` | Corrección urgente de un bug en producción |

### Flujo de trabajo paso a paso

```bash
# ── NUEVA FEATURE ──
git checkout develop
git pull origin develop
git checkout -b feature/nombre-funcionalidad

# ... desarrollar ...

git add app/routes/api.py app/models/survey.py
git commit -m "feat: añadir endpoint de votación con protección IDOR"
git push origin feature/nombre-funcionalidad
# → Abrir Pull Request a develop en GitHub
# → Esperar CI verde (lint + tests) + code review
# → Merge a develop

# ── RELEASE ──
git checkout develop
git checkout -b release/1.1.0
# bumps de versión, tests finales
git commit -m "chore: bump version to 1.1.0"
git checkout main
git merge release/1.1.0 --no-ff
git tag v1.1.0
git checkout develop
git merge release/1.1.0 --no-ff
git branch -d release/1.1.0

# ── HOTFIX ──
git checkout main
git checkout -b hotfix/fix-rate-limit-bypass
# corregir el bug
git commit -m "fix: aplicar rate limit correctamente tras refactor de blueprints"
git checkout main
git merge hotfix/fix-rate-limit-bypass --no-ff
git tag v1.0.1
git checkout develop
git merge hotfix/fix-rate-limit-bypass --no-ff
git branch -d hotfix/fix-rate-limit-bypass
```

### Convención de mensajes de commit

```
feat:     nueva funcionalidad
fix:      corrección de bug
security: cambio relacionado con seguridad
docs:     documentación
chore:    mantenimiento, dependencias, CI
test:     tests
refactor: refactorización sin cambio de comportamiento
```

---

## Pruebas con Postman

### Archivos

| Archivo | Descripción |
|---------|-------------|
| [`postman/Galapp.postman_collection.json`](postman/Galapp.postman_collection.json) | Colección con todos los endpoints, ejemplos y tests automáticos |

### Importar

1. Postman → **File → Import** → selecciona `Galapp.postman_collection.json`
2. Arriba a la derecha selecciona el environment **"Galapp – Local"** (incluido en la colección)

### Variables de entorno

| Variable | Valor por defecto | Se actualiza automáticamente al... |
|----------|-------------------|------------------------------------|
| `base_url` | `http://localhost` | — (fija) |
| `token` | *(vacío)* | Ejecutar **Auth / Login** |
| `survey_id` | `1` | Ejecutar **Crear encuesta** |
| `question_id` | `1` | Ejecutar **Añadir pregunta** |
| `option_id` | `1` | Ejecutar **Añadir opción** |

### Flujo de uso recomendado

```
1. Auth / Login                   →  {{token}} se guarda automáticamente
2. Surveys / Crear encuesta        →  {{survey_id}} se guarda automáticamente
3. Surveys / Añadir pregunta       →  {{question_id}} se guarda automáticamente
4. Surveys / Añadir opción (×2)    →  {{option_id}} se guarda automáticamente
5. Votes / Votar                   →  usa {{question_id}} y {{option_id}}
6. Votes / Votar (otra vez)        →  devuelve 400 "User already voted"
```

### Tests automáticos por request

Cada request tiene scripts en la pestaña **Tests** que se ejecutan automáticamente:

| Request | Qué comprueba |
|---------|--------------|
| Health Check | Status 200, `status = "ok"` |
| Registro | Status 201, mensaje `"User created"` |
| Login | Status 200, campo `token` presente, formato `x.x.x` de JWT |
| Listar encuestas | Status 200, respuesta es array |
| Crear encuesta | Status 201, campo `id` numérico |
| Ver encuesta | Status 200, contiene `survey` y `questions` |
| Añadir pregunta | Status 201, campo `id` presente |
| Añadir opción | Status 201, campo `id` presente |
| Votar | Status 201 (primer voto) o 400 con `"already voted"` (doble voto) |

### Endpoints de referencia rápida

```
GET  http://localhost/api/health                              — Sin auth
POST http://localhost/auth/register                           — Sin auth
POST http://localhost/auth/login                              — Sin auth
GET  http://localhost/api/surveys                             — Bearer {{token}}
POST http://localhost/api/surveys                             — Bearer {{token}}
GET  http://localhost/api/surveys/{{survey_id}}               — Bearer {{token}}
POST http://localhost/api/surveys/{{survey_id}}/questions     — Bearer {{token}}
POST http://localhost/api/questions/{{question_id}}/options   — Bearer {{token}}
POST http://localhost/api/votes                               — Bearer {{token}}
GET  http://localhost/api/surveys/{{survey_id}}/my-votes      — Bearer {{token}}
GET  http://localhost/api/surveys/{{survey_id}}/results       — Bearer {{token}}
```
