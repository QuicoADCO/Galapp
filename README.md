# GalApp – Proyecto Final SecDevOps

## Descripción del proyecto

GalApp es una aplicación web desarrollada en Python con Flask cuyo objetivo es implementar y demostrar un ciclo completo de desarrollo seguro (SecDevOps).

El proyecto integra conceptos clave de Puesta en Producción Segura, incluyendo autenticación, control de acceso, diseño de APIs, contenedorización, automatización de pruebas e integración continua, alineándose con buenas prácticas basadas en OWASP Top 10.

---

## Arquitectura de la aplicación

La aplicación sigue una arquitectura modular cliente-servidor estructurada en diferentes capas:

```
app/
├── models/
├── routes/
│   ├── api.py
│   ├── auth.py
│   └── frontend.py
├── templates/
├── database.py
└── main.py
```

---

## Backend (API REST)

Archivo principal: `app/routes/api.py`

### Funcionalidades

* Endpoint de verificación: `/api/health`
* Gestión de encuestas:

  * Crear encuestas
  * Obtener encuestas
  * Obtener encuesta con sus opciones
* Gestión de opciones
* Registro de votos

### Implementación

* Uso de Flask Blueprints (`api_bp`)
* Rutas REST bajo `/api`
* Respuestas en JSON con códigos HTTP
* Conexión a SQLite mediante funciones auxiliares

---

## Autenticación

Archivo: `app/routes/auth.py`

### Funcionalidades

* Registro de usuarios
* Inicio de sesión

### Implementación

* Contraseñas almacenadas como `password_hash`
* Validación de credenciales
* Separación de lógica de autenticación

---

## Frontend

Archivos:

* `app/routes/frontend.py`
* `app/templates/`

### Funcionalidades

* Registro
* Login
* Navegación básica

### Implementación

* Plantillas HTML con Flask
* Separación entre frontend y backend

---

## Base de datos

Archivo: `init_db.py`

### Tablas

* `users`
* `surveys`
* `survey_options`
* `votes`

### Implementación

* SQLite (`sqlite3`)
* Claves primarias y foráneas
* Timestamps automáticos
* Relaciones entre entidades

---

## Seguridad

Archivo: `SECURITY.md`

### Medidas implementadas

* Autenticación de usuarios
* Hash de contraseñas
* Validación de datos
* Consultas parametrizadas
* Uso de variables de entorno
* Separación frontend/backend

---

## Contenedorización

Archivos:

* `Dockerfile`
* `docker-compose.yml`
* `nginx/nginx.conf`

### Implementación

* Contenedor Flask
* Proxy inverso con Nginx
* Orquestación con Docker Compose

### Ejecución

```
docker-compose up --build
```

---

## Testing

Carpeta: `tests/`

### Implementación

* Uso de `pytest`
* Tests de autenticación y API

### Ejecución

```
pytest -v
```

---

## Integración continua

Archivo: `.github/workflows/ci.yml`

### Funcionamiento

* Ejecución en cada push o pull request
* Instalación de dependencias
* Ejecución automática de tests

---

## API REST

Archivo: `app/routes/api.py`

| Método | Endpoint                  | Descripción                   |
| ------ | ------------------------- | ----------------------------- |
| GET    | /api/health               | Verificación del estado       |
| GET    | /api/surveys              | Obtener encuestas             |
| POST   | /api/surveys              | Crear encuesta                |
| GET    | /api/surveys/<id>         | Obtener encuesta con opciones |
| POST   | /api/surveys/<id>/options | Añadir opción                 |
| POST   | /api/votes                | Registrar voto                |

---

## Control de versiones

Estrategia basada en GitFlow:

* `main` → versión estable
* `develop` → integración
* `feature/*` → nuevas funcionalidades
* `hotfix/*` → correcciones
* `release/*` → versiones

---

## Tecnologías utilizadas

* Python
* Flask
* SQLite
* Docker
* Docker Compose
* Nginx
* Pytest
* Git
* GitHub Actions

---

## Pruebas con Postman

Carpeta: `postman/`

### Endpoints probados

#### Registro

```
POST http://localhost:5000/register
```

```json
{
  "username": "usuario_test",
  "email": "test@email.com",
  "password": "123456"
}
```

#### Login

```
POST http://localhost:5000/login
```

```json
{
  "email": "test@email.com",
  "password": "123456"
}
```

### Objetivo

* Validar registro de usuarios
* Comprobar autenticación
* Verificar respuestas HTTP

---

## Uso

1. Ejecutar la aplicación
2. Abrir Postman
3. Realizar peticiones a:

```
http://localhost:5000
```

---

## Conclusión

GalApp representa una implementación práctica de un flujo SecDevOps, integrando desarrollo backend, frontend, seguridad, automatización y despliegue en contenedores.

El proyecto presenta una estructura modular clara, uso de buenas prácticas y automatización del ciclo de desarrollo.
