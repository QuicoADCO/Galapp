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
│   │   ├── user.py               # Modelo User: id, username, email, password (hash), role
│   │   └── survey.py             # Survey, Question, QuestionOption, Vote + UniqueConstraint
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
│   │   ├── dashboard.js          # Dashboard: carga surveys, votación, compartir
│   │   ├── create_survey.js      # Constructor dinámico de encuestas (WeakMap para imágenes)
│   │   ├── survey_vote.js        # Página de votación pública
│   │   ├── login.css             # Estilos del formulario de login
│   │   ├── register.css          # Estilos del formulario de registro
│   │   ├── dashboard.css         # Estilos completos del dashboard
│   │   ├── create_survey.css     # Estilos del constructor de encuestas
│   │   ├── survey_vote.css       # Estilos de la página de votación pública
│   │   └── uploads/              # Imágenes subidas (volumen Docker persistente)
│   ├── database.py               # Inicialización de SQLAlchemy (init_db)
│   ├── main.py                   # App factory + MAX_CONTENT_LENGTH + rate limits + error handlers
│   ├── utils.py                  # generate_token, token_required (inyecta g.current_user)
│   └── seed.py                   # Crea el usuario administrador inicial
├── tests/
│   ├── conftest.py               # Fixture pytest con SQLite en memoria
│   └── test_auth.py              # Tests de registro y login
├── nginx/
│   └── nginx.conf                # Proxy inverso + cabeceras de seguridad + Cache-Control /api/
├── .github/
│   └── workflows/ci.yml          # Pipeline CI: lint + tests + PostgreSQL service
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

| Método | Endpoint                              | Auth | Solo creador | Descripción                                      |
|--------|---------------------------------------|------|:------------:|--------------------------------------------------|
| GET    | `/api/health`                         | No   | —            | Estado del servicio                              |
| POST   | `/auth/register`                      | No   | —            | Registro — máx. 5 req/min por IP                 |
| POST   | `/auth/login`                         | No   | —            | Login — devuelve JWT, máx. 10 req/min            |
| GET    | `/api/surveys`                        | Sí   | —            | Listar todas las encuestas                       |
| POST   | `/api/surveys`                        | Sí   | —            | Crear encuesta — máx. 20 req/min                 |
| GET    | `/api/surveys/<id>`                   | Sí   | —            | Encuesta con preguntas y opciones                |
| POST   | `/api/surveys/<id>/questions`         | Sí   | ✓            | Añadir pregunta (solo el creador de la encuesta) |
| POST   | `/api/questions/<id>/options`         | Sí   | ✓            | Añadir opción (solo el creador de la encuesta)   |
| POST   | `/api/votes`                          | Sí   | —            | Votar — máx. 60 req/min, opción verificada       |
| GET    | `/api/surveys/<id>/my-votes`          | Sí   | —            | Votos del usuario autenticado en esta encuesta   |
| GET    | `/api/surveys/<id>/results`           | Sí   | —            | Resultados con porcentajes por opción            |

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

**Problema mitigado:** Acceso a recursos sin autorización, IDOR (Insecure Direct Object Reference), redirección abierta (Open Redirect).

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Todos los endpoints `/api/*` requieren JWT válido | `@token_required()` en cada ruta | `app/routes/api.py` |
| El `created_by` de una encuesta se toma del JWT, nunca del body | `created_by = g.current_user["id"]` | `app/routes/api.py` |
| El `user_id` del voto se toma del JWT, nunca del body | `user_id = g.current_user["id"]` | `app/routes/api.py` |
| Control de roles: el decorador acepta parámetro `role=` | `if role and data.get("role") != role` | `app/utils.py` |
| Un usuario solo puede votar una vez por opción/pregunta | `UniqueConstraint("question_id", "option_id", "user_id")` | `app/models/survey.py` |
| **IDOR en preguntas:** solo el creador de la encuesta puede añadir preguntas | `if survey.created_by != g.current_user["id"]: return 403` | `app/routes/api.py:add_question` |
| **IDOR en opciones:** solo el creador puede añadir opciones a sus preguntas | Verificación de propiedad a través de `question → survey` | `app/routes/api.py:add_option` |
| **Vote tampering:** la opción votada debe pertenecer a la pregunta indicada | `if option.question_id != question_id: return 400` | `app/routes/api.py:vote` |
| **Open Redirect en login:** el parámetro `?siguiente=` solo acepta rutas relativas | `siguiente.startsWith('/') && !siguiente.startsWith('//')` | `app/static/login.js` |

> **IDOR (Insecure Direct Object Reference):** sin los controles de propiedad, cualquier usuario autenticado podía añadir preguntas y opciones a encuestas ajenas mediante `POST /api/surveys/<id>/questions`. Ahora el servidor verifica que `survey.created_by == token.id`.

> **Vote Tampering:** sin la verificación de pertenencia, un atacante podía enviar `{"question_id": 1, "option_id": 99}` donde la opción 99 pertenece a otra pregunta, adulterando resultados. Ahora se verifica la coherencia pregunta↔opción.

> **Open Redirect:** `?siguiente=https://evil.com` causaba redirección a un dominio externo tras login, vector de phishing. Ahora solo se aceptan paths que empiecen por `/` y no por `//`.

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
| Todo el HTML dinámico pasa por la función `esc()` | `.replace(/</g,'&lt;')`, etc. | `app/static/dashboard.js`, `app/static/survey_vote.js` |
| `esc()` escapa los 5 caracteres peligrosos: `&`, `<`, `>`, `"`, `'` | Añadido `.replace(/'/g,'&#x27;')` (comilla simple) | `app/static/dashboard.js`, `app/static/survey_vote.js` |
| Longitud máxima en todos los campos de texto | `len(title) > 200`, `len(text) > 500`, `len(text) > 300` | `app/routes/api.py` |
| CSP `script-src 'self'` bloquea scripts inline y externos | Cabecera `Content-Security-Policy` en nginx | `nginx/nginx.conf` |
| CSP `object-src 'none'` bloquea plugins (Flash, Java applets) | Añadido a la directiva CSP | `nginx/nginx.conf` |

> **XSS via comilla simple:** la versión anterior de `esc()` no escapaba `'`. Un atacante con texto como `'; fetch('//evil')//` en un atributo HTML podía inyectar eventos. Ahora se escapa a `&#x27;`.

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

**Problema mitigado:** Versiones de servidor visibles, errores con stack traces, configuraciones por defecto inseguras, caché de datos sensibles.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Nginx oculta versión del servidor | `server_tokens off;` | `nginx/nginx.conf` |
| Timeouts de conexión configurados | `client_body_timeout 10s`, etc. | `nginx/nginx.conf` |
| Límite de tamaño en nginx y Flask | `client_max_body_size 5M` + `MAX_CONTENT_LENGTH = 5 MB` | `nginx/nginx.conf`, `app/main.py` |
| Error 500 devuelve mensaje genérico, sin stack trace | `@app.errorhandler(500)` con log interno | `app/main.py` |
| Error 404 devuelve JSON, no página Flask por defecto | `@app.errorhandler(404)` | `app/main.py` |
| Dockerfile sin compiladores en producción | Imagen única basada en `python:3.12-slim` + solo dependencias runtime | `Dockerfile` |
| Recursos limitados por contenedor | `cpus: "0.50"`, `memory: 512M` | `docker-compose.yml` |
| Healthchecks en todos los servicios | `healthcheck:` en db, web, nginx | `docker-compose.yml` |
| **Cache-Control en respuestas autenticadas** | `no-store, no-cache, must-revalidate, private` en `/api/` y `/auth/` | `nginx/nginx.conf` |
| **Path Traversal en subida de imágenes** | `os.path.basename()` antes de extraer extensión y al construir URLs | `app/routes/api.py` |
| `X-Permitted-Cross-Domain-Policies: none` | Impide carga de políticas desde dominios externos (Flash, PDF) | `nginx/nginx.conf` |
| `X-XSS-Protection: 0` (reemplaza el `1; mode=block` deprecated) | El valor `1` puede crear nuevas vulnerabilidades en navegadores modernos | `nginx/nginx.conf` |
| `Referrer-Policy: strict-origin` | Solo envía el origen (sin path) en cabecera Referer | `nginx/nginx.conf` |

> **Path Traversal:** un atacante podía enviar un filename como `../../etc/passwd.jpg`. Aunque el UUID rename ya lo neutralizaba en el almacenamiento, el procesador de extensiones y la función `_img_url()` operaban sobre el nombre sin sanear. Ahora se aplica `os.path.basename()` antes de cualquier operación.

> **Cache-Control:** sin esta cabecera, respuestas con votos, encuestas o datos del usuario podían quedar cacheadas en el navegador o proxies intermedios, exponiendo datos de otras sesiones en equipos compartidos.

---

### A07 – Identification and Authentication Failures (Fallos de Autenticación)

**Problema mitigado:** Credenciales en URL, tokens sin expiración, ataques de fuerza bruta, contraseñas débiles, vote stuffing.

| Medida | Implementación | Archivo |
|--------|---------------|---------|
| Tokens JWT con expiración de 1 hora | `timedelta(hours=1)` en el payload `exp` | `app/utils.py` |
| Error de login genérico (no indica si falla usuario o contraseña) | `"Invalid credentials"` en ambos casos | `app/routes/auth.py` |
| Rate limiting en login: máx. 10 peticiones/min por IP | `limiter.limit("10 per minute")` | `app/main.py` |
| Rate limiting en registro: máx. 5 peticiones/min por IP | `limiter.limit("5 per minute")` | `app/main.py` |
| **Rate limiting en creación de encuestas: máx. 20/min por IP** | `limiter.limit("20 per minute")` en `create_survey` | `app/main.py` |
| **Rate limiting en votos: máx. 60/min por IP** (anti vote-stuffing) | `limiter.limit("60 per minute")` en `vote` | `app/main.py` |
| Respuesta 429 con mensaje claro al superar el límite | `@app.errorhandler(429)` | `app/main.py` |
| Validación de complejidad de contraseña | Mín. 8 chars + mayúscula + minúscula + dígito | `app/routes/auth.py` |
| Validación de formato de email con regex | `_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")` | `app/routes/auth.py` |
| Validación de username con caracteres seguros | `_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")` | `app/routes/auth.py` |
| Login usa fetch JSON, nunca GET con credenciales en URL | `fetch('/auth/login', {method:'POST',...})` | `app/static/login.js` |
| Rollback de sesión DB en caso de error durante el registro | `try/except SQLAlchemyError` con `db.session.rollback()` | `app/routes/auth.py` |

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

**62 tests — 0 fallos.** Usan **SQLite en memoria**: no requieren Docker ni PostgreSQL para ejecutarse.

### Ejecución

```bash
# Dentro del contenedor (recomendado — mismas dependencias que producción)
docker compose exec web python -m pytest tests/ -v

# Local (requiere pip install -r requirements.txt)
python -m pytest tests/ -v
```

### Infraestructura — `tests/conftest.py`

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

#### `tests/test_auth.py` — `TestGenerateToken` / `TestGetSecret`

| Test | Qué verifica |
|------|-------------|
| `test_returns_string` | `generate_token` devuelve string con formato `header.payload.signature` |
| `test_payload_contains_required_claims` | El JWT contiene `id`, `username`, `role` y `exp` con los valores correctos |
| `test_token_expires_in_about_one_hour` | El campo `exp` está entre 59 y 61 minutos en el futuro |
| `test_raises_if_missing` | `_get_secret()` lanza `RuntimeError` si `JWT_SECRET_KEY` no está definida |

#### `tests/test_surveys.py` — `TestSurveyModel`

| Test | Qué verifica |
|------|-------------|
| `test_survey_created_correctly` | El modelo `Survey` se persiste con `id` y `created_at` automáticos |
| `test_survey_option_linked_to_survey` | `SurveyOption` queda enlazada vía FK y accesible en `survey.options` |
| `test_vote_unique_constraint` | La `UniqueConstraint(survey_id, user_id)` lanza `IntegrityError` en doble voto |

#### `tests/test_votes.py` — `TestVoteModel`

| Test | Qué verifica |
|------|-------------|
| `test_same_user_cannot_vote_twice_in_db` | La BD rechaza dos votos del mismo usuario en la misma encuesta |
| `test_different_users_can_vote_same_survey` | Dos usuarios distintos pueden votar en la misma encuesta sin conflicto |

---

### Tests de integración

Cubren el **flujo HTTP completo** a través del cliente de test Flask.

#### `tests/test_auth.py` — Registro (13 casos)

| Test | Código esperado |
|------|----------------|
| `test_success_returns_201` | 201 |
| `test_missing_username/email/password_returns_400` | 400 |
| `test_duplicate_username_returns_400` | 400 |
| `test_duplicate_email_returns_400` | 400 |
| `test_weak_password_no_uppercase_returns_400` | 400 |
| `test_weak_password_too_short_returns_400` | 400 |
| `test_weak_password_no_digit_returns_400` | 400 |
| `test_invalid_email_returns_400` | 400 |
| `test_invalid_username_too_short_returns_400` | 400 |
| `test_invalid_username_special_chars_returns_400` | 400 |
| `test_empty_body_returns_400` | 400 |

#### `tests/test_auth.py` — Login (7 casos)

| Test | Código esperado |
|------|----------------|
| `test_success_returns_token` | 200 + `token` con formato JWT |
| `test_wrong_password_returns_401` | 401 |
| `test_nonexistent_user_returns_401` | 401 |
| `test_missing_username/password_returns_400` | 400 |
| `test_empty_body_returns_400` | 400 |
| `test_error_message_is_generic` | Mismo mensaje para usuario y contraseña incorrectos (OWASP A07) |

#### `tests/test_auth.py` — Protección JWT (4 casos)

| Test | Qué verifica |
|------|-------------|
| `test_no_token_returns_401` | Sin cabecera Authorization → 401 |
| `test_invalid_token_returns_401` | Token con firma inválida → 401 |
| `test_malformed_header_returns_401` | Header sin prefijo `Bearer` → 401 |
| `test_valid_token_grants_access` | Token válido → acceso concedido (200) |

#### `tests/test_surveys.py` — CRUD de encuestas (15 casos)

| Test | Código esperado |
|------|----------------|
| `test_returns_empty_list_initially` | 200 + `[]` |
| `test_returns_created_survey` | 200 + array con la encuesta creada |
| `test_success_returns_201_with_id` | 201 + `id` numérico |
| `test_missing_title_returns_400` | 400 |
| `test_title_too_long_returns_400` (201 chars) | 400 |
| `test_created_by_is_taken_from_jwt_not_body` | 201 y `created_by ≠ 9999` (IDOR) |
| `test_survey_without_description_is_ok` | 201 |
| `test_returns_survey_with_options` | 200 + `survey` + `options[]` |
| `test_nonexistent_survey_returns_404` | 404 |
| `test_add_option_success` | 201 |
| `test_option_text_too_long_returns_400` (301 chars) | 400 |
| `test_missing_option_text_returns_400` | 400 |
| `test_survey_not_found_returns_404` | 404 |
| Todos los endpoints sin token | 401 |

#### `tests/test_votes.py` — Votación (7 casos + 1 end-to-end)

| Test | Qué verifica |
|------|-------------|
| `test_success_returns_201` | Voto registrado correctamente |
| `test_double_vote_returns_400` | El mismo usuario no puede votar dos veces |
| `test_user_id_is_taken_from_jwt_not_body` | Enviar `user_id: 9999` no suplanta a otro usuario (IDOR) |
| `test_two_different_users_can_vote` | Dos usuarios distintos votan con éxito |
| `test_missing_survey_id/option_id_returns_400` | 400 por campos faltantes |
| `test_unauthenticated_returns_401` | 401 sin token |
| `test_register_login_create_vote` | Flujo completo: registro → login → encuesta → opciones → voto → doble voto bloqueado |

#### `tests/test_health.py` — Health y error handlers (4 casos)

| Test | Qué verifica |
|------|-------------|
| `test_health_returns_200` | GET /api/health devuelve `{"status": "ok"}` |
| `test_health_no_auth_required` | El endpoint es público (sin JWT) |
| `test_404_returns_json` | Las rutas inexistentes devuelven JSON, no HTML de Flask |
| `test_404_no_stack_trace` | La respuesta no contiene `Traceback` ni rutas internas |

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

### Archivos

| Archivo | Descripción |
|---------|-------------|
| `postman/Galapp.postman_collection.json` | Colección con todos los endpoints, ejemplos y tests automáticos |
| `postman/Galapp.postman_environment.json` | Environment con variables `base_url`, `token`, `survey_id`, `option_id` |

### Importar

1. Postman → **File → Import** → selecciona `Galapp.postman_collection.json`
2. Postman → **File → Import** → selecciona `Galapp.postman_environment.json`
3. Arriba a la derecha selecciona el environment **"Galapp – Local"**

### Variables de entorno

| Variable | Valor por defecto | Se actualiza automáticamente al... |
|----------|-------------------|------------------------------------|
| `base_url` | `http://localhost` | — (fija) |
| `token` | *(vacío)* | Ejecutar **Auth / Login** |
| `survey_id` | `1` | Ejecutar **Crear encuesta** o **Listar encuestas** |
| `option_id` | `1` | Ejecutar **Añadir opción** o **Ver encuesta con opciones** |

### Flujo de uso recomendado

```
1. Auth / Login           →  {{token}} se guarda automáticamente
2. Surveys / Crear        →  {{survey_id}} se guarda automáticamente
3. Surveys / Añadir opción (×2 mínimo)  →  {{option_id}} se guarda
4. Votes / Votar          →  usa {{survey_id}} y {{option_id}} ya guardados
5. Votes / Votar (otra vez)  →  devuelve 400 "User already voted"
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
| Ver encuesta | Status 200, contiene `survey` y `options` |
| Añadir opción | Status 201, campo `id` presente |
| Votar | Status 201 (primer voto) o 400 con `"already voted"` (doble voto) |

### Respuestas de ejemplo guardadas

Cada request incluye respuestas de ejemplo (pestaña **Examples**) con los cuerpos reales de éxito y error:

| Request | Ejemplos guardados |
|---------|--------------------|
| Registro | 201 Created, 400 Contraseña débil, 400 Usuario ya existe |
| Login | 200 Token JWT, 401 Credenciales inválidas, 429 Rate limit |
| Listar encuestas | 200 con array, 401 sin token |
| Crear encuesta | 201 Created, 400 Título faltante |
| Ver encuesta | 200 con opciones, 404 no encontrada |
| Añadir opción | 201 Created, 400 texto vacío |
| Votar | 201 registrado, 400 ya votó, 401 sin token |

### Endpoints de referencia rápida

```
GET  http://localhost/api/health                     — Sin auth
POST http://localhost/auth/register                  — Sin auth
POST http://localhost/auth/login                     — Sin auth
GET  http://localhost/api/surveys                    — Bearer {{token}}
POST http://localhost/api/surveys                    — Bearer {{token}}
GET  http://localhost/api/surveys/{{survey_id}}      — Bearer {{token}}
POST http://localhost/api/surveys/{{survey_id}}/options  — Bearer {{token}}
POST http://localhost/api/votes                      — Bearer {{token}}
```
