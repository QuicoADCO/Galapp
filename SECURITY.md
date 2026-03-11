# SECURITY.md

## Política de Seguridad

Este documento describe las medidas de seguridad implementadas en el proyecto **GalApp**, desarrollado como práctica de la asignatura de **Puesta en Producción Segura / SecDevOps**.

El objetivo es identificar y mitigar posibles vulnerabilidades siguiendo las recomendaciones del **OWASP Top 10** para aplicaciones web y APIs.

---

# 1. Control de acceso (OWASP A01 – Broken Access Control)

La aplicación implementa un sistema de autenticación con dos tipos de usuario:

* **Administrador**
* **Usuario normal**

Dependiendo del tipo de usuario autenticado, la aplicación puede mostrar comportamientos o elementos visuales diferentes (por ejemplo, cambios en la interfaz).

Medidas aplicadas:

* Autenticación obligatoria para acceder a ciertas funcionalidades.
* Separación de roles de usuario.
* Control del acceso a determinadas rutas de la aplicación.

Esto evita que usuarios no autorizados accedan a recursos restringidos.

---

# 2. Fallos criptográficos (OWASP A02 – Cryptographic Failures)

Las contraseñas de los usuarios deben almacenarse utilizando **funciones de hash seguras**.

Buenas prácticas aplicadas o recomendadas:

* Uso de algoritmos de hash seguros como **bcrypt**.
* Nunca almacenar contraseñas en texto plano.
* Uso de variables de entorno para almacenar información sensible.

Estas medidas protegen las credenciales de los usuarios en caso de acceso no autorizado a la base de datos.

---

# 3. Inyección (OWASP A03 – Injection)

Para prevenir ataques de inyección (como **SQL Injection**), la aplicación utiliza:

* **ORM SQLAlchemy** para interactuar con la base de datos.
* Evitar la concatenación directa de consultas SQL.

Esto permite que los parámetros enviados por el usuario sean tratados de forma segura.

---

# 4. Configuración de seguridad incorrecta (OWASP A05 – Security Misconfiguration)

La aplicación utiliza buenas prácticas para evitar errores de configuración:

* Uso de **variables de entorno** para información sensible.
* Separación entre configuración de desarrollo y producción.
* Uso de contenedores **Docker** para asegurar entornos consistentes.

Esto reduce el riesgo de exposición accidental de información sensible.

---

# 5. Fallos de identificación y autenticación (OWASP A07 – Identification and Authentication Failures)

La aplicación implementa un sistema de autenticación básico con:

* Registro de usuarios.
* Inicio de sesión mediante credenciales.
* Gestión de sesión del usuario.

Además, se diferencian roles de usuario para mejorar el control de acceso.

---

# 6. Seguridad en APIs

El backend de la aplicación expone una API que es utilizada por el frontend.

Medidas aplicadas:

* Validación de datos recibidos.
* Control de acceso mediante autenticación.
* Separación entre frontend y backend.

Estas medidas ayudan a evitar accesos no autorizados y manipulación de datos.

---

# 7. Gestión de dependencias

Las dependencias del proyecto se gestionan mediante el archivo:

requirements.txt

Esto permite controlar las versiones utilizadas y facilita la actualización de librerías vulnerables.

---

# 8. Automatización y pruebas de seguridad

El proyecto incluye automatización mediante herramientas de integración continua (CI).

Las pruebas automatizadas permiten:

* Detectar errores durante el desarrollo.
* Verificar el funcionamiento de la autenticación y la API.

---

# 9. Buenas prácticas DevSecOps

Durante el desarrollo del proyecto se han aplicado principios de **DevSecOps**:

* Uso de control de versiones con **Git**.
* Separación del desarrollo en ramas (`main`, `develop`, `feature`, `hotfix`).
* Automatización del pipeline mediante herramientas CI.
* Uso de contenedores Docker para reproducibilidad del entorno.

---

# 10. Reporte de vulnerabilidades

Si se detecta una vulnerabilidad de seguridad en el proyecto, se recomienda:

1. No divulgar la vulnerabilidad públicamente.
2. Notificar al responsable del proyecto.
3. Proporcionar una descripción detallada del problema y pasos para reproducirlo.

---

# Conclusión

El proyecto aplica diferentes medidas de seguridad alineadas con las recomendaciones del **OWASP Top 10**, integrando prácticas de desarrollo seguro dentro del ciclo **SecDevOps**.
