# Guía de uso — Galapp

## Índice

1. [Arrancar la aplicación](#1-arrancar-la-aplicación)
2. [Abrir la app en el navegador](#2-abrir-la-app-en-el-navegador)
3. [Aceptar el certificado de seguridad](#3-aceptar-el-certificado-de-seguridad)
4. [Registrarse e iniciar sesión](#4-registrarse-e-iniciar-sesión)
5. [Crear una encuesta](#5-crear-una-encuesta)
6. [Compartir una encuesta](#6-compartir-una-encuesta)
7. [Votar en una encuesta](#7-votar-en-una-encuesta)
8. [Ver resultados en vivo](#8-ver-resultados-en-vivo)
9. [Usuario administrador](#9-usuario-administrador)

---

## 1. Arrancar la aplicación

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
docker compose up -d
```

Espera unos segundos hasta que los tres contenedores estén en estado **healthy**. Puedes comprobarlo con:

```bash
docker compose ps
```

Para detener la aplicación:

```bash
docker compose down
```

> Si quieres borrar también la base de datos (todos los datos se perderán):
> ```bash
> docker compose down -v
> ```

---

## 2. Abrir la app en el navegador

Una vez arrancada, abre tu navegador y ve a:

```
https://localhost
```

> La app usa HTTPS con un certificado autofirmado. El navegador mostrará un aviso de seguridad la primera vez — esto es completamente normal. Sigue las instrucciones del apartado siguiente según tu navegador.

---

## 3. Aceptar el certificado de seguridad

### Google Chrome

1. Verás la pantalla **"Tu conexión no es privada"**.
2. Haz clic en **Avanzado** (parte inferior de la pantalla).
3. Haz clic en **Acceder a localhost (sitio no seguro)**.
4. Ya estás dentro de la app.

### Opera

1. Verás la pantalla **"Tu conexión no es privada"**.
2. Opera no muestra el botón "Avanzado" directamente.
3. Haz clic en cualquier zona en blanco de la página.
4. Escribe exactamente (sin comillas, no aparecerá nada en pantalla):
   ```
   thisisunsafe
   ```
5. Al terminar la última letra, la página cargará automáticamente.

### Microsoft Edge

1. Verás la pantalla **"Tu conexión no es privada"**.
2. Haz clic en **Avanzado**.
3. Haz clic en **Continuar en localhost (no es seguro)**.

### Mozilla Firefox

1. Verás la pantalla **"Aviso: riesgo potencial de seguridad"**.
2. Haz clic en **Avanzado**.
3. Haz clic en **Aceptar el riesgo y continuar**.

---

## 4. Registrarse e iniciar sesión

### Crear una cuenta nueva

1. En la pantalla de inicio de sesión, haz clic en **Crear cuenta** (o ve a `https://localhost/register`).
2. Introduce un nombre de usuario, correo electrónico y contraseña.
3. Haz clic en **Registrarse**.
4. Serás redirigido automáticamente al dashboard.

### Iniciar sesión

1. Ve a `https://localhost/login`.
2. Introduce tu usuario/correo y contraseña.
3. Haz clic en **Iniciar sesión**.

### Cerrar sesión

Haz clic en el botón **Cerrar sesión** en la parte inferior de la barra lateral izquierda.

---

## 5. Crear una encuesta

1. En el dashboard, haz clic en el botón **+ Nueva encuesta** (esquina superior derecha de la sección "Mis encuestas").
2. Rellena los campos:
   - **Título**: nombre de la encuesta (obligatorio).
   - **Descripción**: texto opcional que verán los votantes.
   - **Imagen de portada**: opcional, puedes subir una imagen (JPG, PNG, GIF o WebP, máximo 4 MB).
3. Añade las preguntas:
   - Haz clic en **+ Añadir pregunta**.
   - Escribe el texto de la pregunta.
   - Elige el tipo: **Única** (solo una opción) o **Múltiple** (varias opciones).
   - Añade las opciones de respuesta con **+ Añadir opción**.
   - Puedes añadir una imagen a cada opción.
4. Haz clic en **Crear encuesta**.

La encuesta aparecerá en tu dashboard en la sección **Mis encuestas**.

---

## 6. Compartir una encuesta

1. En tu encuesta, haz clic en el botón **🔗 Compartir**.
2. Se abrirá un modal con:
   - Un **código QR** que lleva directamente a la encuesta.
   - El **enlace directo** a la encuesta.
   - Un botón **Copiar** que copia al portapapeles un mensaje de invitación con el enlace.
   - Un botón **📤 Enviar vía...** (solo en navegadores y dispositivos compatibles con la API de compartir nativa).

### Compartir con otros dispositivos de tu red local

Para que otras personas en tu red (móvil, tablet, otro ordenador) puedan acceder, el enlace usa la IP de red de tu ordenador (ej: `https://192.168.1.46/encuesta/1`).

La primera vez que otro dispositivo abra ese enlace, también verá el aviso de certificado. Debe aceptarlo igual que se describe en el [apartado 3](#3-aceptar-el-certificado-de-seguridad).

---

## 7. Votar en una encuesta

### Desde el dashboard (usuario registrado)

Las encuestas en las que puedes votar aparecen directamente en tu dashboard. Selecciona una opción y haz clic en **Votar**.

### Desde el enlace compartido

1. Abre el enlace recibido (o escanea el QR).
2. Si es la primera vez desde ese dispositivo, acepta el certificado (ver [apartado 3](#3-aceptar-el-certificado-de-seguridad)).
3. Puedes votar como **invitado** (sin cuenta) o iniciando sesión.
4. Selecciona tu opción y haz clic en **Votar**.

Una vez votado, no podrás cambiar tu voto en esa pregunta.

---

## 8. Ver resultados en vivo

1. En tu encuesta del dashboard, haz clic en **📊 Resultados**.
2. Se abrirá un panel con los resultados actuales de cada pregunta.
3. Los resultados se **actualizan automáticamente cada 5 segundos** sin necesidad de recargar la página.
4. La opción más votada se resalta visualmente.
5. Haz clic en **×** o fuera del panel para cerrarlo.

---

## 9. Usuario administrador

La aplicación crea automáticamente un usuario administrador al arrancar:

| Campo | Valor |
|---|---|
| Usuario | `admin` |
| Contraseña | `Admin1234!` |

> **Recomendado**: cambia la contraseña por defecto añadiendo esta línea a tu archivo `.env` antes de arrancar:
> ```
> ADMIN_PASSWORD=TuContraseñaSegura123!
> ```
> Luego reinicia con `docker compose up -d`.
