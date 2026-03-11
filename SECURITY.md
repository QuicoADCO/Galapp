# Seguridad de la aplicación

Este documento describe las medidas de seguridad implementadas en el proyecto siguiendo las recomendaciones del **OWASP Top 10**.

---

# OWASP A01: Control de acceso roto (Broken Access Control)

**Medida aplicada**

Uso de **JWT (JSON Web Tokens)** para autenticar usuarios y proteger endpoints privados.

**Implementación**

* `app/routes/auth.py`
  Implementa el login y generación de tokens JWT.

* `app/routes/api.py`
  Contiene endpoints protegidos que requieren autenticación.

---

# OWASP A02: Fallos criptográficos (Cryptographic Failures)

**Medidas aplicadas**

* Uso de **SECRET_KEY** y **JWT_SECRET_KEY** para proteger sesiones y tokens.
* Las claves sensibles se almacenan en **variables de entorno**.

**Implementación**

* `app/main.py`
  Carga y valida las variables de entorno necesarias para el funcionamiento seguro de la aplicación.

* `.env`
  Almacena claves secretas y credenciales fuera del código fuente.

---

# OWASP A03: Inyección (Injection)

**Medida aplicada**

Uso de **SQLAlchemy ORM** para evitar consultas SQL directas y prevenir ataques de inyección SQL.

**Implementación**

* `app/database.py`
  Configuración de la base de datos utilizando SQLAlchemy.

* `app/models/user.py`
  Definición del modelo de usuario utilizando ORM.

---

# OWASP A04: Diseño inseguro (Insecure Design)

**Medidas aplicadas**

* Separación clara entre:

  * rutas de autenticación
  * rutas de API
  * rutas de frontend

**Implementación**

* `app/routes/auth.py`
* `app/routes/api.py`
* `app/routes/frontend.py`

Esto mejora la organización del código y reduce riesgos de diseño inseguro.

---

# OWASP A05: Configuración de seguridad incorrecta (Security Misconfiguration)

**Medidas aplicadas**

* Validación de variables de entorno obligatorias.
* Uso de Docker para entornos controlados.

**Implementación**

* `app/main.py`
  Verificación de variables críticas como:

  * POSTGRES_USER
  * POSTGRES_PASSWORD
  * POSTGRES_DB
  * SECRET_KEY
  * JWT_SECRET_KEY

* `Dockerfile`
  Define el entorno de ejecución de la aplicación.

* `docker-compose.yml`
  Configura los servicios de aplicación y base de datos.

---

# OWASP A07: Fallos de identificación y autenticación (Identification and Authentication Failures)

**Medidas aplicadas**

Sistema de autenticación basado en:

* Registro de usuarios
* Login con credenciales
* Generación de token JWT

**Implementación**

* `app/routes/auth.py`
  Manejo de registro y login de usuarios.

* `app/models/user.py`
  Modelo de usuario almacenado en base de datos.

---

# OWASP A09: Fallos en el registro y monitoreo de seguridad (Security Logging and Monitoring Failures)

**Medidas aplicadas**

* Manejo controlado de errores.
* Validación de variables críticas al inicio de la aplicación.

**Implementación**

* `app/main.py`
  Genera errores si faltan variables críticas de configuración.

---

# Protección de credenciales

Las credenciales sensibles **no se almacenan en el código fuente**.

**Archivos implicados**

* `.env`
* `.env.example`
* `.gitignore`

`.env` está excluido del repositorio para evitar exposición de secretos.

---

# Seguridad en despliegue

La aplicación se ejecuta mediante **Docker**, lo que proporciona:

* aislamiento del entorno
* control de dependencias
* configuración reproducible

**Archivos**

* `Dockerfile`
* `docker-compose.yml`
