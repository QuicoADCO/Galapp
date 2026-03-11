# GalApp – Proyecto Final SecDevOps

## Descripción del proyecto

**GalApp** es una aplicación web sencilla desarrollada en **Python con Flask** cuyo objetivo es simular un ciclo completo de **desarrollo seguro (SecDevOps)**.

El proyecto integra diferentes conceptos vistos en la asignatura de **Puesta en Producción Segura**, incluyendo contenedorización, autenticación, control de acceso, automatización de pruebas y revisión de vulnerabilidades basadas en **OWASP Top 10**.

El objetivo principal no es la complejidad funcional de la aplicación, sino demostrar la integración de **prácticas de desarrollo seguro durante todo el ciclo de vida del software**.

---

# Arquitectura de la aplicación

La aplicación sigue una arquitectura cliente-servidor separada en **frontend y backend**.

### Frontend

* Implementado con **Flask** y plantillas HTML.
* Interfaz simple para autenticación de usuarios y acceso a funcionalidades.

### Backend

* API desarrollada también con **Flask**.
* Gestiona autenticación, lógica de negocio y comunicación con la base de datos.

### Infraestructura

La aplicación se ejecuta utilizando contenedores:

* **Docker**
* **Docker Compose**
* **Nginx** como servidor proxy

Esto permite garantizar que el entorno sea reproducible en cualquier sistema.

---

# Autenticación y autorización

La aplicación implementa un sistema básico de autenticación con dos tipos de usuario:

* **Administrador**
* **Usuario normal**

Una vez autenticado el usuario, la aplicación puede modificar la interfaz o comportamiento dependiendo del rol.
Por ejemplo, el administrador puede visualizar diferencias en la interfaz de la aplicación.

Este mecanismo permite simular un sistema de **control de acceso basado en roles (RBAC)**.

---

# Entorno de desarrollo

Para aislar el desarrollo de otros proyectos se utiliza un **entorno virtual de Python**.

Ejemplo de activación del entorno virtual:

```
(.venv) user@equipo:~/galapp$
```

Esto garantiza que las dependencias del proyecto no interfieran con otras aplicaciones instaladas en el sistema.

---

# Contenedorización

La aplicación está preparada para ejecutarse en contenedores Docker.

Archivos principales:

* `Dockerfile`
* `docker-compose.yml`

Para iniciar la aplicación:

```
docker-compose up --build
```

Esto construye los contenedores necesarios y ejecuta la aplicación en un entorno aislado.

---

# Seguridad de la aplicación

Durante el desarrollo se han tenido en cuenta diferentes vulnerabilidades descritas en **OWASP Top 10**.

Las principales medidas consideradas incluyen:

* Control de acceso mediante autenticación.
* Separación de roles de usuario.
* Uso de ORM para evitar inyecciones SQL.
* Configuración mediante variables de entorno.
* Separación entre frontend y backend mediante API.

El análisis completo de seguridad se encuentra documentado en:

* `SECURITY.md`

---

# Seguridad en la API

La comunicación entre el frontend y el backend se realiza mediante una **API REST**.

Medidas aplicadas:

* Validación de datos recibidos.
* Separación entre capas de aplicación.
* Control de acceso en endpoints protegidos.

Esto ayuda a reducir riesgos relacionados con manipulación de datos o accesos no autorizados.

---

# Pruebas del proyecto

El proyecto incluye **tests automatizados** utilizando el framework **pytest**.

Tipos de pruebas implementadas:

* **Tests unitarios**
* **Tests de integración**

Para ejecutar las pruebas:

```
pytest
```

Las pruebas permiten verificar el funcionamiento correcto de:

* autenticación
* endpoints de la API
* lógica principal de la aplicación

---

# Integración continua (CI)

El proyecto utiliza **GitHub Actions** para automatizar el proceso de integración continua.

Cada vez que se realiza un **push** o **pull request** al repositorio:

1. Se clona el repositorio
2. Se instala Python
3. Se instalan las dependencias del proyecto
4. Se ejecutan los tests automáticos

Esto permite detectar errores de forma temprana y garantizar la estabilidad del proyecto.

El flujo de automatización se encuentra en:

```
.github/workflows/ci.yml
```

---

# Control de versiones

El proyecto utiliza **Git** como sistema de control de versiones.

Se sigue una estrategia de ramas inspirada en **GitFlow**:

* `main` → versión estable del proyecto
* `develop` → integración de nuevas funcionalidades
* `feature/*` → desarrollo de nuevas características
* `hotfix/*` → corrección de errores críticos
* `release/*` → preparación de nuevas versiones

Esta estrategia permite mantener un desarrollo organizado y seguro.

---

# Estructura del proyecto

```
galapp/
│
├── app/
│   ├── models/
│   ├── routes/
│   └── templates/
│
├── tests/
│
├── docker/
│
├── .github/workflows/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── SECURITY.md
```

---

# Tecnologías utilizadas

* Python
* Flask
* SQLAlchemy
* Docker
* Docker Compose
* Nginx
* Git
* GitHub Actions
* Pytest

---

# Conclusión

Este proyecto demuestra cómo integrar prácticas de **seguridad, automatización y control de versiones dentro de un flujo de desarrollo SecDevOps**.

Aunque la aplicación es sencilla, incorpora diferentes elementos clave para el desarrollo de aplicaciones seguras y preparadas para producción.
