GalApp – Proyecto Final SecDevOps
Descripción del proyecto

GalApp es una aplicación web desarrollada en Python con Flask cuyo objetivo es implementar y demostrar un ciclo completo de desarrollo seguro (SecDevOps).

El proyecto integra conceptos clave de la asignatura de Puesta en Producción Segura, incluyendo autenticación, control de acceso, diseño de APIs, contenedorización, automatización de pruebas e integración continua, alineándose con buenas prácticas basadas en OWASP Top 10.

Arquitectura de la aplicación

La aplicación sigue una arquitectura modular cliente-servidor estructurada en diferentes capas:

app/
├── models/
├── routes/
│   ├── api.py
│   ├── auth.py
│   └── frontend.py
├── templates/
├── database.py
└── main.py
Backend (API REST)

Archivo principal: app/routes/api.py

Funcionalidades implementadas

Endpoint de verificación (/api/health)

Gestión de encuestas:

Crear encuestas

Obtener encuestas

Obtener encuesta con sus opciones

Gestión de opciones de encuesta

Registro de votos

Implementación

Uso de Flask Blueprints (api_bp)

Definición de rutas REST bajo el prefijo /api

Conexión a base de datos SQLite mediante funciones auxiliares

Respuestas en formato JSON con códigos HTTP adecuados

Autenticación

Archivo: app/routes/auth.py

Funcionalidades

Registro de usuarios

Inicio de sesión

Implementación

Almacenamiento de contraseñas mediante password_hash

Validación de credenciales en el login

Separación de lógica de autenticación respecto a la API

Frontend

Archivos:

app/routes/frontend.py

app/templates/

Funcionalidades

Interfaz de usuario para:

Registro

Login

Navegación básica

Implementación

Uso de plantillas HTML renderizadas con Flask

Separación clara entre lógica de presentación y backend

Base de datos

Archivo: init_db.py

Estructura

Se implementa una base de datos SQLite con las siguientes tablas:

users

surveys

survey_options

votes

Implementación

Uso de sqlite3

Definición de claves primarias y foráneas

Generación automática de timestamps

Relación entre entidades para garantizar integridad de datos

Seguridad de la aplicación

Archivo: SECURITY.md

La aplicación incorpora medidas alineadas con OWASP Top 10.

Medidas implementadas

Autenticación de usuarios

Hash de contraseñas

Separación de roles y lógica de acceso

Validación de datos en endpoints

Uso de consultas parametrizadas en base de datos

Configuración mediante variables de entorno

Separación entre frontend y backend

Contenedorización

Archivos:

Dockerfile

docker-compose.yml

nginx/nginx.conf

Implementación

Contenedor para la aplicación Flask

Servidor proxy inverso con Nginx

Orquestación mediante Docker Compose

Ejecución
docker-compose up --build
Testing

Carpeta: tests/

Implementación

Uso de pytest

Tests automatizados para:

Autenticación

Funcionalidad de la API

Ejecución
pytest -v
Integración continua (CI)

Archivo: .github/workflows/ci.yml

Funcionamiento

Cada vez que se realiza un push o pull request:

Se clona el repositorio

Se configura el entorno de Python

Se instalan las dependencias

Se ejecutan los tests automatizados

Esto permite validar automáticamente el estado del proyecto.

API REST

Archivo: app/routes/api.py

Endpoints principales
Método	Endpoint	Descripción
GET	/api/health	Verificación del estado
GET	/api/surveys	Obtener encuestas
POST	/api/surveys	Crear encuesta
GET	/api/surveys/<id>	Obtener encuesta con opciones
POST	/api/surveys/<id>/options	Añadir opción
POST	/api/votes	Registrar voto
Control de versiones

Se utiliza Git con una estrategia basada en GitFlow:

main → versión estable

develop → integración de cambios

feature/* → nuevas funcionalidades

hotfix/* → correcciones

release/* → preparación de versiones

Tecnologías utilizadas

Python

Flask

SQLite

Docker

Docker Compose

Nginx

Pytest

Git

GitHub Actions

Pruebas de API con Postman

Carpeta: postman/

Descripción

Se ha utilizado Postman para realizar pruebas manuales sobre los endpoints principales de autenticación de la aplicación.

Estas pruebas permiten validar el correcto funcionamiento del sistema y simular el comportamiento de un cliente real interactuando con la API.

Endpoints probados

Registro de usuario:

POST http://localhost:5000/register
{
  "username": "usuario_test",
  "email": "test@email.com",
  "password": "123456"
}

Inicio de sesión:

POST http://localhost:5000/login
{
  "email": "test@email.com",
  "password": "123456"
}
Objetivo de las pruebas

Verificar el registro correcto de usuarios en la base de datos

Validar el proceso de autenticación

Comprobar respuestas HTTP del servidor

Detectar errores durante el desarrollo

Uso

Ejecutar la aplicación

Abrir Postman

Realizar peticiones a:

http://localhost:5000
Resultado

Las pruebas realizadas han permitido comprobar el correcto funcionamiento de los endpoints de autenticación, asegurando la comunicación entre cliente y servidor y la persistencia de datos en la base de datos.

Conclusión

GalApp representa una implementación práctica de un flujo SecDevOps, integrando desarrollo backend, frontend, seguridad, automatización y despliegue en contenedores.

El proyecto refleja una estructura modular clara, el uso de buenas prácticas y la automatización del ciclo de desarrollo, permitiendo validar el funcionamiento y la seguridad de la aplicación de forma continua.