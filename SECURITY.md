# Seguridad de la aplicación

Este documento describe las medidas de seguridad implementadas en el proyecto **GalApp**, alineadas con el **OWASP Top 10**, y especifica en qué archivos se aplica cada una.

---

## OWASP A01: Control de acceso roto (Broken Access Control)

### Medidas aplicadas

* Separación de rutas según responsabilidad:

  * Autenticación
  * API
  * Frontend
* Control del flujo de acceso a funcionalidades según autenticación

### Implementación

* `app/routes/auth.py`
  Gestiona registro e inicio de sesión de usuarios.

* `app/routes/api.py`
  Define endpoints de la API que pueden ser restringidos según lógica de acceso.

* `app/routes/frontend.py`
  Controla la navegación del usuario en la interfaz.

---

## OWASP A02: Fallos criptográficos (Cryptographic Failures)

### Medidas aplicadas

* Almacenamiento seguro de contraseñas mediante hash
* Uso de claves secretas para la configuración de la aplicación
* Uso de variables de entorno para evitar exponer información sensible

### Implementación

* `app/routes/auth.py`
  Generación y verificación de contraseñas mediante hashing.

* `.env`
  Almacena:

  * `SECRET_KEY`

* `.gitignore`
  Evita que el archivo `.env` se suba al repositorio.

---

## OWASP A03: Inyección (Injection)

### Medidas aplicadas

* Uso de consultas parametrizadas en SQLite
* Evita concatenación directa de strings en consultas SQL

### Implementación

* `app/database.py`
  Gestión de conexión a base de datos.

* Uso de `sqlite3` con parámetros (`?`) en las consultas

---

## OWASP A04: Diseño inseguro (Insecure Design)

### Medidas aplicadas

* Arquitectura modular separando responsabilidades
* Separación entre lógica de negocio, autenticación y presentación

### Implementación

* `app/routes/auth.py`
* `app/routes/api.py`
* `app/routes/frontend.py`

Esto reduce el acoplamiento y mejora la seguridad del diseño.

---

## OWASP A05: Configuración de seguridad incorrecta (Security Misconfiguration)

### Medidas aplicadas

* Uso de variables de entorno para configuración sensible
* Contenedorización con Docker para entornos controlados
* Separación entre entorno de desarrollo y ejecución

### Implementación

* `Dockerfile`
  Define el entorno de ejecución.

* `docker-compose.yml`
  Orquesta los servicios.

* `app/main.py`
  Carga configuración desde variables de entorno.

---

## OWASP A07: Fallos de identificación y autenticación (Identification and Authentication Failures)

### Medidas aplicadas

* Sistema de autenticación basado en:

  * Registro de usuarios
  * Login con validación de credenciales
* Almacenamiento de contraseñas hasheadas

### Implementación

* `app/routes/auth.py`
  Manejo completo del flujo de autenticación.

* Base de datos (`users`)
  Almacena credenciales de forma segura (`password_hash`).

---

## OWASP A09: Fallos en el registro y monitoreo de seguridad (Security Logging and Monitoring Failures)

### Medidas aplicadas

* Manejo controlado de errores
* Respuestas HTTP estructuradas
* Validación de entrada de datos

### Implementación

* `app/routes/api.py`
  Devuelve respuestas JSON con códigos HTTP adecuados.

* `app/main.py`
  Control de errores al iniciar la aplicación.

---

## Protección de credenciales

Las credenciales sensibles no se almacenan en el código fuente.

### Archivos implicados

* `.env`
* `.env.example`
* `.gitignore`

El archivo `.env` está excluido del repositorio para evitar la exposición de secretos.

---

## Seguridad en base de datos

### Medidas aplicadas

* Uso de claves primarias y foráneas
* Integridad referencial entre tablas
* Separación de entidades (users, surveys, votes)

### Implementación

* `init_db.py`
  Definición de estructura de base de datos SQLite.

---

## Seguridad en despliegue

La aplicación se ejecuta mediante Docker, lo que proporciona:

* Aislamiento del entorno
* Control de dependencias
* Reproducibilidad

### Archivos

* `Dockerfile`
* `docker-compose.yml`

---

## Conclusión

GalApp implementa medidas de seguridad alineadas con OWASP Top 10, incluyendo protección de credenciales, validación de datos, separación de responsabilidades y configuración segura del entorno.

Estas prácticas permiten reducir riesgos comunes en aplicaciones web y asegurar un desarrollo más robusto dentro del enfoque SecDevOps.
