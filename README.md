# GalApp – Proyecto Final SecDevOps

GalApp es una aplicación web de votaciones en vivo desarrollada en Python con Flask, que implementa un ciclo completo de desarrollo seguro (SecDevOps). Integra autenticación JWT, API REST protegida, base de datos PostgreSQL, contenedorización con Docker y CI/CD con GitHub Actions.

---

## Índice

1. [Arquitectura del proyecto](#arquitectura-del-proyecto)
2. [Tecnologías](#tecnologías)
3. [Puesta en marcha](#puesta-en-marcha)
4. [Usuario administrador](#usuario-administrador)
5. [API REST](#api-rest)
6. [Autenticación JWT](#autenticación-jwt)
7. [Seguridad – OWASP Top 10 2025](#seguridad--owasp-top-10-2025)
8. [Cabeceras de seguridad HTTP](#cabeceras-de-seguridad-http)
9. [Base de datos](#base-de-datos)
10. [Contenedorización Docker](#contenedorización-docker)
11. [Testing](#testing)
12. [CI/CD – GitHub Actions](#cicd--github-actions)
13. [GitFlow](#gitflow)
14. [Pruebas con Postman](#pruebas-con-postman)

---

## Arquitectura del proyecto

```
Galapp/
├── app/
│   ├── models/
│   │   ├── user.py          # Modelo User: id, username, email, password (hash), role
│   │   └── survey.py        # Modelos Survey, SurveyOption, Vote + UniqueConstraint
│   ├── routes/
│   │   ├── api.py           # API REST protegida: encuestas, opciones, votos
│   │   ├── auth.py          # Registro y login — validación + JWT
│   │   └── frontend.py      # Rutas HTML: /login, /register, /dashboard
│   ├── templates/
│   │   ├── login.html       # Formulario de acceso
│   │   ├── register.html    # Formulario de registro
│   │   └── dashboard.html   # Panel principal de votación
│   ├── static/
│   │   ├── login.js         # Lógica de login con fetch JSON
│   │   ├── register.js      # Lógica de registro con validación cliente
│   │   ├── dashboard.js     # Lógica del dashboard: carga surveys, votación, creación
│   │   ├── login.css        # Estilos del formulario de login
│   │   ├── register.css     # Estilos del formulario de registro
│   │   └── dashboard.css    # Estilos completos del dashboard
│   ├── database.py          # Inicialización de SQLAlchemy (init_db)
│   ├── main.py              # App factory create_app + rate limiting + error handlers
│   ├── utils.py             # generate_token, token_required (inyecta g.current_user)
│   └── seed.py              # Crea el usuario administrador inicial
├── tests/
│   ├── conftest.py          # Fixture pytest con SQLite en memoria
│   └── test_auth.py         # Tests de registro y login
├── nginx/
│   └── nginx.conf           # Proxy inverso + cabeceras de seguridad HTTP
├── .github/
│   └── workflows/ci.yml     # Pipeline CI: lint + tests + PostgreSQL service
├── postman/
│   └── Galapp.postman_collection.json
├── wsgi.py                  # Entry point para Gunicorn
├── Dockerfile               # Build multietapa: builder → runtime sin compiladores
├── docker-compose.yml       # Orquestación: db + web + nginx con healthchecks
└── .env                     # Variables de entorno (excluido del repositorio)
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
| CI/CD           | GitHub Actions                    |
| Seguridad       | OWASP Top 10 2025, CCN-CERT       |

---

## Puesta en marcha

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
# Construir imágenes y levantar todos los servicios
docker compose up -d --build

# Crear el usuario administrador
docker compose exec web python -m app.seed
```

La aplicación queda disponible en: **http://localhost**

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

# Parar y borrar volumen de base de datos
docker compose down -v
```

---

## Usuario administrador

El script `app/seed.py` crea el usuario admin automáticamente.

> Usar `python -m app.seed` (no `python app/seed.py`) para que Python resuelva correctamente los imports desde `/project/`.

```bash
docker compose exec web python -m app.seed
```

Credenciales por defecto:

| Campo    | Valor        |
|----------|--------------|
| Username | `admin`      |
| Password | `Admin1234!` |
| Role     | `admin`      |

---

## API REST

Todos los endpoints salvo `/api/health` requieren autenticación JWT en la cabecera:

```
Authorization: Bearer <token>
```

### Tabla de endpoints

| Método | Endpoint                    | Auth | Descripción                          |
|--------|-----------------------------|------|--------------------------------------|
| GET    | `/api/health`               | No   | Estado del servicio                  |
| POST   | `/auth/register`            | No   | Registro — máx. 5 req/min por IP     |
| POST   | `/auth/login`               | No   | Login — devuelve JWT, máx. 10 req/min|
| GET    | `/api/surveys`              | Sí   | Listar todas las encuestas           |
| POST   | `/api/surveys`              | Sí   | Crear encuesta (autor tomado del JWT)|
| GET    | `/api/surveys/<id>`         | Sí   | Encuesta con sus opciones            |
| POST   | `/api/surveys/<id>/options` | Sí   | Añadir opción (máx. 300 chars)       |
| POST   | `/api/votes`                | Sí   | Votar — usuario tomado del JWT       |

### Validaciones de entrada

| Campo        | Regla                                    | Archivo              |
|--------------|------------------------------------------|----------------------|
| `username`   | 3–32 chars, solo `[a-zA-Z0-9_]`         | `app/routes/auth.py` |
| `email`      | Formato `x@x.x` validado con regex       | `app/routes/auth.py` |
| `password`   | Mín. 8 chars, mayúscula + minúscula + dígito | `app/routes/auth.py` |
| `title`      | Requerido, máx. 200 chars               | `app/routes/api.py`  |
| `option_text`| Requerido, máx. 300 chars               | `app/routes/api.py`  |

### Respuestas de error estándar

| Código | Causa                                   |
|--------|-----------------------------------------|
| 400    | Campos faltantes o inválidos            |
| 401    | Token ausente, expirado o inválido      |
| 403    | Rol insuficiente                        |
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

**Crear encuesta** (el campo `created_by` lo toma el servidor del JWT, no hace falta enviarlo):

```bash
curl -X POST http://localhost/api/surveys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "¿Mejor lenguaje?", "description": "Vota tu favorito"}'
```

**Añadir opción:**

```bash
curl -X POST http://localhost/api/surveys/1/options \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"option_text": "Python"}'
```

**Votar** (el campo `user_id` lo toma el servidor del JWT, no hace falta enviarlo):

```bash
curl -X POST http://localhost/api/votes \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"survey_id": 1, "option_id": 2}'
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
| `generate_token(user)`     | `app/utils.py:15`| Genera JWT con id, username, role y exp (+1 hora)   |
| `@token_required(role=None)` | `app/utils.py:25`| Decorador de protección; inyecta `g.current_user`   |
| `_get_secret()`            | `app/utils.py:8` | Obtiene `JWT_SECRET_KEY` o lanza RuntimeError       |
| `login()`                  | `app/routes/auth.py:40` | Valida credenciales, llama a `generate_token` |

---

## Seguridad – OWASP Top 10 2025

### A01 – Broken Access Control (Control de Acceso Roto)

**Problema mitigado:** Acceso a recursos sin autorización, IDOR (Insecure Direct Object Reference).

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Todos los endpoints `/api/*` requieren JWT válido | `@token_required()` en cada ruta | `app/routes/api.py` |
| El `created_by` de una encuesta se toma del JWT, nunca del body | `created_by = g.current_user["id"]` | `app/routes/api.py:47` |
| El `user_id` del voto se toma del JWT, nunca del body | `user_id = g.current_user["id"]` | `app/routes/api.py:117` |
| Control de roles: el decorador acepta parámetro `role=` | `if role and data.get("role") != role` | `app/utils.py:42` |
| Un usuario solo puede votar una vez por encuesta | `UniqueConstraint("survey_id", "user_id")` | `app/models/survey.py:35` |

> Sin esta protección, cualquier usuario podría enviar `{"user_id": 1}` en el body y votar como el administrador. Ahora ese campo se ignora completamente del request.

---

### A02 – Cryptographic Failures (Fallos Criptográficos)

**Problema mitigado:** Contraseñas en texto plano, claves hardcodeadas, tokens expuestos.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Contraseñas hasheadas con PBKDF2-SHA256 al registrar | `generate_password_hash(password)` | `app/routes/auth.py:49` |
| Verificación segura sin comparación directa | `check_password_hash(user.password, password)` | `app/routes/auth.py:62` |
| Claves secretas en variables de entorno | `os.getenv("JWT_SECRET_KEY")` | `app/utils.py:9` |
| Error explícito si la clave no está definida | `raise RuntimeError(...)` | `app/utils.py:11` |
| JWT firmado con HMAC-SHA256 | `jwt.encode(..., algorithm="HS256")` | `app/utils.py:22` |
| JWT nunca se muestra en la interfaz | Token eliminado del dashboard | `app/templates/dashboard.html` |
| `.env` excluido del repositorio | Entrada en `.gitignore` | `.gitignore` |

---

### A03 – Injection (Inyección SQL y XSS)

**Problema mitigado:** Consultas SQL concatenadas, inyección de HTML en la interfaz.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Todas las consultas usan SQLAlchemy ORM con parámetros enlazados | `User.query.filter_by(username=username)` | `app/routes/auth.py`, `app/routes/api.py` |
| Sin ninguna consulta SQL manual con f-strings | Ningún `db.execute(f"...")` en el código | — |
| Todo el HTML dinámico pasa por la función `esc()` | `.replace(/</g,'&lt;')`, etc. | `app/static/dashboard.js:152` |
| Longitud máxima en todos los campos de texto | `len(title) > 200`, `len(option_text) > 300` | `app/routes/api.py` |

---

### A04 – Insecure Design (Diseño Inseguro)

**Problema mitigado:** Arquitectura sin separación de responsabilidades, sin principio de mínimo privilegio.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Patrón App Factory para configuración por entorno | `def create_app(test_config=None)` | `app/main.py:29` |
| Modelos separados de rutas separados de templates | Estructura `models/`, `routes/`, `templates/` | Toda la carpeta `app/` |
| Usuario no-root en el contenedor Docker | `RUN useradd -m appuser` + `USER appuser` | `Dockerfile:32,54` |
| Red interna Docker: web y db no expuestos al exterior | `networks: internal`, solo nginx expone puerto 80 | `docker-compose.yml:11,34` |
| Verificación de variables de entorno al arrancar | `REQUIRED_ENV_VARS` loop en módulo raíz | `app/main.py:16` |

---

### A05 – Security Misconfiguration (Mala Configuración de Seguridad)

**Problema mitigado:** Versiones de servidor visibles, errores con stack traces, configuraciones por defecto inseguras.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Nginx oculta versión del servidor | `server_tokens off;` | `nginx/nginx.conf:5` |
| Timeouts de conexión configurados | `client_body_timeout 10s`, etc. | `nginx/nginx.conf:9` |
| Límite de tamaño de cuerpo de petición | `client_max_body_size 1M;` | `nginx/nginx.conf:7` |
| Error 500 devuelve mensaje genérico, sin stack trace | `@app.errorhandler(500)` | `app/main.py:72` |
| Error 404 devuelve JSON, no página Flask por defecto | `@app.errorhandler(404)` | `app/main.py:64` |
| Dockerfile multietapa: sin compiladores en producción | Stage builder separado de stage runtime | `Dockerfile` |
| Recursos limitados por contenedor | `cpus: "0.50"`, `memory: 512M` | `docker-compose.yml:17,40,63` |
| Healthchecks en todos los servicios | `healthcheck:` en db, web, nginx | `docker-compose.yml` |

---

### A07 – Identification and Authentication Failures (Fallos de Autenticación)

**Problema mitigado:** Credenciales en URL, tokens sin expiración, ataques de fuerza bruta, contraseñas débiles.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Tokens JWT con expiración de 1 hora | `timedelta(hours=1)` en el payload `exp` | `app/utils.py:20` |
| Error de login genérico (no indica si falla usuario o contraseña) | `"Invalid credentials"` en ambos casos | `app/routes/auth.py:63` |
| Rate limiting en login: máx. 10 peticiones/min por IP | `limiter.limit("10 per minute")` | `app/main.py:61` |
| Rate limiting en registro: máx. 5 peticiones/min por IP | `limiter.limit("5 per minute")` | `app/main.py:62` |
| Respuesta 429 con mensaje claro al superar el límite | `@app.errorhandler(429)` | `app/main.py:68` |
| Validación de complejidad de contraseña | Mín. 8 chars + mayúscula + minúscula + dígito | `app/routes/auth.py:17` |
| Validación de formato de email con regex | `_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")` | `app/routes/auth.py:13` |
| Validación de username con caracteres seguros | `_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")` | `app/routes/auth.py:14` |
| Login usa fetch JSON, nunca GET con credenciales en URL | `fetch('/auth/login', {method:'POST',...})` | `app/static/login.js` |

---

### A09 – Security Logging and Monitoring

**Problema mitigado:** Falta de trazabilidad de eventos de seguridad.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Gunicorn registra cada petición: IP, método, ruta, código, tiempo | Configuración por defecto de Gunicorn | `wsgi.py` |
| Nginx registra todas las peticiones entrantes | Log de acceso Nginx | `nginx/nginx.conf` |
| Códigos HTTP semánticos en todas las respuestas | 200, 201, 400, 401, 403, 404, 429, 500 | `app/routes/api.py`, `app/routes/auth.py` |
| El ID del usuario nunca se expone en la UI | Stat card de User ID eliminada | `app/templates/dashboard.html` |

---

## Cabeceras de seguridad HTTP

Configuradas en `nginx/nginx.conf` para todas las respuestas:

| Cabecera | Valor | Protección |
|----------|-------|------------|
| `X-Frame-Options` | `DENY` | Evita clickjacking / iframes maliciosos |
| `X-Content-Type-Options` | `nosniff` | Evita MIME-sniffing del navegador |
| `X-XSS-Protection` | `1; mode=block` | Activa filtro XSS en navegadores legacy |
| `Referrer-Policy` | `no-referrer` | Evita filtración de URL en cabecera Referer |
| `Content-Security-Policy` | `default-src 'self'; style-src 'self' fonts.googleapis.com; font-src 'self' fonts.gstatic.com` | Bloquea scripts/estilos inline y externos no autorizados |

> La CSP `default-src 'self'` es la razón por la que todo el JavaScript y CSS está en archivos externos (`/static/`). Los scripts inline quedarían bloqueados por el navegador.

---

## Base de datos

Motor: **PostgreSQL 15** gestionado con **Flask-SQLAlchemy**.
Las tablas se crean automáticamente en el primer arranque con `db.create_all()` (`app/main.py:77`).

### Modelo `users` — `app/models/user.py`

| Campo    | Tipo        | Restricciones            |
|----------|-------------|--------------------------|
| id       | Integer     | PK, autoincrement        |
| username | String(80)  | UNIQUE, NOT NULL         |
| email    | String(120) | UNIQUE, NOT NULL         |
| password | String(255) | NOT NULL — hash PBKDF2   |
| role     | String(20)  | NOT NULL, default `user` |

### Modelo `surveys` — `app/models/survey.py`

| Campo       | Tipo        | Restricciones             |
|-------------|-------------|---------------------------|
| id          | Integer     | PK                        |
| title       | String(200) | NOT NULL                  |
| description | Text        | Opcional                  |
| created_by  | Integer     | FK → users.id (del JWT)   |
| created_at  | DateTime    | UTC, automático           |

### Modelo `survey_options` — `app/models/survey.py`

| Campo       | Tipo        | Restricciones          |
|-------------|-------------|------------------------|
| id          | Integer     | PK                     |
| survey_id   | Integer     | FK → surveys.id        |
| option_text | String(500) | NOT NULL               |

### Modelo `votes` — `app/models/survey.py`

| Campo      | Tipo     | Restricciones                           |
|------------|----------|-----------------------------------------|
| id         | Integer  | PK                                      |
| survey_id  | Integer  | FK → surveys.id                         |
| user_id    | Integer  | FK → users.id (tomado del JWT)          |
| option_id  | Integer  | FK → survey_options.id                  |
| created_at | DateTime | UTC, automático                         |
| —          | —        | `UNIQUE(survey_id, user_id)` — un voto por usuario por encuesta |

---

## Contenedorización Docker

### Servicios — `docker-compose.yml`

| Servicio | Imagen              | Puerto | Red      | Descripción                              |
|----------|---------------------|--------|----------|------------------------------------------|
| `db`     | postgres:15-alpine  | 5432   | internal | Base de datos PostgreSQL                 |
| `web`    | galapp-web (build)  | 8000   | internal | Flask + Gunicorn (no expuesto al host)   |
| `nginx`  | nginx:stable-alpine | 80→80  | internal | Proxy inverso, único punto de entrada    |

**Solo el puerto 80 de nginx está expuesto al host.** Los servicios `db` y `web` son accesibles únicamente dentro de la red interna Docker `galapp_internal`.

### Dockerfile multietapa — `Dockerfile`

```
┌─────────────────────────────────────┐
│  STAGE 1: builder (python:3.12-slim) │
│  - apt: build-essential, libpq-dev  │
│  - pip install -r requirements.txt  │
│  - resultado: /venv compilado        │
└────────────────┬────────────────────┘
                 │  COPY --from=builder /venv /venv
┌────────────────▼────────────────────┐
│  STAGE 2: runtime (python:3.12-slim) │
│  - sin gcc, sin build-essential      │
│  - solo libpq5 (runtime PostgreSQL) │
│  - usuario no-root: appuser          │
│  - WORKDIR /project                  │
│  - CMD gunicorn wsgi:app             │
└─────────────────────────────────────┘
```

Ventajas de seguridad del multietapa:
- La imagen final no contiene compiladores (superficie de ataque reducida)
- Si hay una vulnerabilidad en el contenedor, el atacante no puede compilar herramientas

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
                   # Para borrarlos: docker compose down -v
```

---

## Testing

Los tests usan **SQLite en memoria** para ejecutarse sin necesidad de PostgreSQL local.

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar todos los tests
pytest -v
```

### Configuración de tests — `tests/conftest.py`

El fixture `client` crea una instancia de la app con `test_config`:
- `SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"`
- Hace `db.create_all()` antes de cada test
- Hace `db.drop_all()` después de cada test

No hay estado compartido entre tests.

### Tests incluidos — `tests/test_auth.py`

| Test             | Descripción                                            |
|------------------|--------------------------------------------------------|
| `test_register`  | POST /auth/register devuelve 201 con datos válidos     |
| `test_login`     | POST /auth/login devuelve 200 con campo `token` en JSON|

---

## CI/CD – GitHub Actions

Archivo: `.github/workflows/ci.yml`

El pipeline se ejecuta automáticamente en cada `push` y `pull_request` sobre cualquier rama.

### Pasos del pipeline

```
1. Checkout del repositorio
2. Setup Python 3.11
3. Instalar dependencias (pip install -r requirements.txt)
4. Levantar servicio PostgreSQL 15 como service container de GitHub Actions
5. Ejecutar pytest -v
```

### Variables de entorno en CI

```yaml
POSTGRES_HOST: localhost
POSTGRES_USER: postgres
POSTGRES_PASSWORD: postgres
POSTGRES_DB: galapp
SECRET_KEY: test
JWT_SECRET_KEY: test
```

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
# → Esperar CI verde + code review
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

Colección disponible en: `postman/Galapp.postman_collection.json`

La aplicación corre en **http://localhost** (puerto 80 vía Nginx).

### 1. Registro

```json
POST http://localhost/auth/register
Content-Type: application/json

{
  "username": "usuario_test",
  "email": "test@email.com",
  "password": "MiPassword1"
}
```

Respuesta `201`:
```json
{ "message": "User created" }
```

### 2. Login

```json
POST http://localhost/auth/login
Content-Type: application/json

{
  "username": "usuario_test",
  "password": "MiPassword1"
}
```

Respuesta `200`:
```json
{ "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." }
```

### 3. Usar el token en Postman

Pestaña **Authorization** → tipo **Bearer Token** → pegar el valor del campo `token`.

### 4. Crear encuesta

```json
POST http://localhost/api/surveys
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "¿Cuál es tu framework favorito?",
  "description": "Vota tu favorito"
}
```

Respuesta `201`:
```json
{ "message": "Survey created", "id": 1 }
```

### 5. Añadir opciones

```json
POST http://localhost/api/surveys/1/options
Authorization: Bearer <token>
Content-Type: application/json

{ "option_text": "Flask" }
```

### 6. Votar

```json
POST http://localhost/api/votes
Authorization: Bearer <token>
Content-Type: application/json

{
  "survey_id": 1,
  "option_id": 1
}
```

### 7. Health check

```
GET http://localhost/api/health
```

Respuesta:
```json
{ "status": "ok" }
```
