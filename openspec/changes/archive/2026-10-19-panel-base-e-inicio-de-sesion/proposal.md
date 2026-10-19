# Proposal: panel-base-e-inicio-de-sesion

Change **C-08** de `CHANGES.md`, historia **US-090** («Iniciar sesión», parte de interfaz) y **US-092 CA-1** visto desde la interfaz. Gobernanza **CRÍTICO** (autenticación y manejo de tokens en el navegador): solo planificación; nada se implementa hasta que el autor apruebe el plan completo. Las doce preguntas del propose quedaron cerradas por el autor el 2026-10-19 con la recomendación del agente (D217 a D228; ver `design.md`).

## Why

Desde C-06 y C-07 la API emite y exige tokens, pero el sistema no tiene interfaz: el único cliente es Swagger (`/docs`), donde el token se pega a mano y caduca a los 15 minutos. Ningún change del panel que sigue (C-09, C-11 a C-16, C-20…) puede llevar su pantalla sin una base de interfaz que sepa iniciar sesión, mandar el token, renovarlo y volver al inicio de sesión cuando la API responde `401`.

Va ahora porque está en el camino crítico (`C-07 → C-08 → C-20`) y es la puerta GATE 4 de `CHANGES.md`: desde C-08 «cada change incluye su pantalla». Sus dependencias (C-06 y C-07) están archivadas.

## What Changes

- **Proyecto `frontend/`** (React + TypeScript + Vite, `tsconfig` estricto, sin `any`, componentes en PascalCase; regla dura 8) hermano de `backend/`, con la estructura de `08` (`src/features/`, `src/shared/`, `src/pages/`) y su propio archivo de dependencias con versiones exactas y archivo de bloqueo (ver D217: amplía D137).
- **Pantalla de inicio de sesión** (`/ingresar`, Propuesta): email y contraseña contra `POST /auth/login` (RN-AU-01). Ante el `401` genérico muestra **un único mensaje fijo**, el mismo para email inexistente, contraseña incorrecta y usuario inactivo (RN-AU-04; US-090 CA-2 y CA-3). Un error de red o del servidor muestra otro mensaje, que no habla de credenciales.
- **Sesión en el navegador**: el access token en memoria y el refresh token en `sessionStorage` (D219). Ningún token ni contraseña viaja en la URL ni se escribe en la consola.
- **Cliente HTTP del panel**: toda petición del panel lleva `Authorization: Bearer <access>`; ante un `401` intenta **una sola** renovación con `POST /auth/refresh` (RN-AU-03), repite la petición una vez y, si la renovación también da `401`, borra la sesión y vuelve al inicio de sesión con el aviso «tu sesión terminó». Varias peticiones que reciben `401` a la vez comparten una sola renovación.
- **Rutas del panel protegidas** (`/panel/...`): sin sesión se redirige a `/ingresar` y, tras iniciar sesión, se vuelve a la ruta pedida. Al recargar la página, si hay refresh token guardado se renueva la sesión antes de mostrar el panel (US-092 CA-1 desde la interfaz).
- **Panel base vacío** (D225): encabezado con el nombre del sistema y el botón «Cerrar sesión» (D226), sin pantallas de negocio.
- **Mismo origen, sin cambios de API** (D220): el navegador habla con la API a través de `/api` del propio servidor del frontend (proxy de Vite en desarrollo, nginx en Compose). No hace falta CORS y la API no se toca.
- **Servicio `frontend` en Docker Compose** (D221): imagen de dos etapas (construcción con Node, servida por nginx sin privilegios), publicada en `127.0.0.1:5173`, con *healthcheck* y proxy de `/api` al servicio `api`.
- **Tests del frontend** (D222): Vitest con jsdom y Testing Library; la API se reemplaza por un **servidor falso en memoria inyectado** (no `vi.mock`) que respeta el contrato de `sesion-del-panel` y `proteccion-del-panel`. La suite del frontend corre sin Docker ni backend: `npm test` desde `frontend/`. Un test guard falla si aparece `any` o `vi.mock` en `frontend/src` (D227).
- **README**: requisitos (Node 24 LTS, D223), instalación y tests del frontend, cómo levantar la demo (API de demostración + `npm run dev`) y Compose con el servicio nuevo, tabla escenario → test, límites conocidos.

No hay cambios en el backend (`backend/` no se toca, salvo que una tarea lo pruebe sin modificarlo). No hay **BREAKING**.

### Escenarios

Cubre los cuatro mínimos de la entrada C-08 de `CHANGES.md` (dentro del «3 a 6»):

| ID | Qué verifica | Dónde corre |
|---|---|---|
| US-090 CA-1 | Con credenciales válidas se entra al panel; se guardan los dos tokens y la ruta pedida se respeta | Suite del frontend + prueba en el navegador |
| US-090 CA-2 | Email inexistente y contraseña incorrecta muestran el mismo mensaje genérico; no queda sesión | Suite del frontend + prueba en el navegador |
| US-090 CA-3 | Un usuario inactivo ve el mismo mensaje y no entra | Suite del frontend + prueba en el navegador (Compose) |
| US-092 CA-1 | Sin sesión, o con la sesión vencida e irrenovable, el panel vuelve al inicio de sesión; con el access vencido y el refresh vigente renueva sin interrumpir (usa US-094 CA-1 y CA-2, ya implementados en la API por C-06) | Suite del frontend + prueba en el navegador |

Quedan fuera US-090 CA-4 (vida y firma de los tokens: es de la API, C-06), US-092 CA-2 a CA-4 (protección por rol y por `token_version` en la API, C-07; la interfaz solo ve el `401` resultante) y US-094 como criterios propios (la API ya los cumple; acá solo se consumen).

## Fuera de alcance

- **Pantallas de negocio** (agenda, turnos, prestaciones, sillones, pacientes, usuarios): cada una va en su change (C-09, C-11 en adelante).
- **Páginas públicas** (`/reservar/{slug}`, gestión por token; C-28 y siguientes).
- **Cualquier cambio de API**: sin `GET /auth/yo`, sin cierre de sesión en el servidor, sin cookies `HttpOnly`, sin CORS (D219, D220, D225, D226).
- **Menú o pantallas según el rol**: la interfaz no conoce los roles (no hay ruta que los informe); el `403` de cada pantalla lo maneja el change que la agrega.
- **Cambio y restablecimiento de contraseña** (C-10), gestión de usuarios (C-09), «recordarme», varias pestañas con una misma sesión.
- **Límite de peticiones** del login y registro de eventos de seguridad (D195; siguen fuera).
- Diseño visual elaborado, biblioteca de componentes, internacionalización, PWA, pruebas de extremo a extremo automatizadas con navegador real.
- Configuración de producción: TLS, dominio, cabeceras de seguridad más allá de las mínimas de `nginx.conf` (design F14).
- Sobreturnos y excepción de horario: fuera de la v1.

## Capabilities

### New Capabilities

- `ingreso-al-panel`: cómo una persona del consultorio entra al panel desde el navegador y se mantiene adentro: la pantalla de inicio de sesión y su mensaje genérico, dónde vive la sesión en el navegador, la renovación ante un `401`, la vuelta al inicio de sesión, las rutas del panel protegidas y el cierre de sesión (RN-AU-01, RN-AU-03, RN-AU-04; US-090, US-092 CA-1). Es una capability de interfaz: `sesion-del-panel` sigue siendo el contrato de la API para obtener y renovar la sesión y `proteccion-del-panel` el de quién puede llamar a cada ruta (D218).

### Modified Capabilities

Ninguna. Se revisaron `sesion-del-panel` y `proteccion-del-panel`: sus requisitos describen la API y no cambian (este change no modifica la API). `creacion-de-turnos`, `historial-de-turnos`, `gestion-de-prestaciones`, `gestion-de-sillones` y `persistencia-postgresql` no se tocan.

## Impact

- **Código nuevo**: todo `frontend/` (configuración de TypeScript, Vite y Vitest; `src/shared/api/` con el cliente HTTP y la sesión; `src/features/ingreso/` con la pantalla; `src/pages/` con el panel base y las rutas; tests junto al código y el servidor falso de la API con los guards en `frontend/src/test/`), `frontend/Dockerfile`, `frontend/nginx.conf`, `frontend/.dockerignore`.
- **Código que se modifica**: `docker-compose.yml` (servicio `frontend`), `.gitignore` (`node_modules/`, `dist/`), `README.md`. **El backend no cambia.**
- **API**: ninguna ruta nueva ni modificada.
- **Dependencias y entorno**: dependencias de npm con versión exacta en `frontend/package.json` y `frontend/package-lock.json` (D217, D224); Node 24 LTS como requisito nuevo para el frontend (D223). La máquina del autor tiene hoy Node 23.5.0, que las versiones propuestas no admiten: **tarea del autor** (instalar Node 24 LTS). Sin variables de entorno nuevas: `.env.example` no cambia.
- **Documentación**: `README.md`. Al archivar, `CHANGES.md` marca C-08 y la KB registra las decisiones que el autor apruebe (commit `docs(kb)` aparte), con las correcciones diferidas de `design.md`, «Notas para el archive» (`02`, `08`, `config.yaml`, `CLAUDE.md`/`AGENTS.md`).
- **Tamaño**: 22 tareas en 10 grupos, apenas por encima del «alrededor de 20» de `CHANGES.md` (el autor lo aceptó como séptima excepción, D228, tras D216).
