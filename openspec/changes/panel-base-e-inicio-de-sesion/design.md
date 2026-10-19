# Design: panel-base-e-inicio-de-sesion

Fecha del design: **2026-10-19**. Gobernanza **CRÍTICO** (autenticación y tokens en el navegador): nada de esto se implementa hasta que el autor apruebe este documento, el spec y `tasks.md`.

**Respuesta del autor (2026-10-19): las doce preguntas abiertas (Q1 a Q12) se cierran con la recomendación del agente.** Quedan como decisiones del autor D217 a D228, una por pregunta y en orden, registradas en `knowledge-base/10_preguntas_abiertas.md` (sección «Decisiones del autor (2026-10-19, panel-base-e-inicio-de-sesion)»). Las demás decisiones marcadas «Propuesta» siguen así hasta que el autor apruebe el plan completo. Las correcciones de la KB, de `openspec/config.yaml` y de `CLAUDE.md`/`AGENTS.md` que estas decisiones piden quedan en «Notas para el archive».

Las decisiones se numeran **F1 a F18** («F» de frontend) para no confundirlas con las D1..D228 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores (D de C-01, I de C-02, H de C-03, P de C-04, S de C-05, J de C-06, R de C-07). Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design, a confirmar) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»). Las que salieron de una pregunta del propose dicen su número («Decisión del autor (D219)»).

## Context

Motivación y alcance: ver `proposal.md`. Requisitos: `specs/ingreso-al-panel/spec.md`.

**Lo que dejaron C-01 a C-07** (leído del código y de los specs, no supuesto):

- **No existe `frontend/`** ni ningún archivo de Node en el repositorio. `.gitignore` solo cubre Python y `.env`.
- **Contrato de sesión** (`openspec/specs/sesion-del-panel/spec.md`, `backend/app/api/routers/auth.py`, `api/esquemas.py`): `POST /auth/login` recibe `{"email", "contrasena"}` (`extra="forbid"`) y responde `200` con `access_token`, `refresh_token`, `token_type` `bearer` y `expires_in` (900); `POST /auth/refresh` recibe `{"refresh_token"}` y responde `200` con `access_token`, `token_type` y `expires_in`, **sin refresh nuevo** (D201). Las dos respuestas llevan `Cache-Control: no-store`. Todo rechazo sale como `application/problem+json` con `codigos`: el login, `401` `["RN-AU-04"]` con texto fijo («El email o la contraseña no son correctos.»), idéntico para email inexistente, contraseña incorrecta y usuario inactivo; el refresh, `401` `["RN-AU-03"]` («La sesión no es válida o venció. Iniciá sesión de nuevo.»); un cuerpo mal formado, `422` con `codigos` vacío.
- **Protección** (`openspec/specs/proteccion-del-panel/spec.md`, `api/seguridad.py`): toda ruta del panel exige `Authorization: Bearer <access>`; sin sesión válida responde el mismo `401` `["RN-AU-03"]` para toda causa (D206) y con rol insuficiente `403` `["RN-AU-05"]` (D207). Las rutas de la API **no tienen prefijo** (`/auth/...`, `/turnos`, `/prestaciones`, `/sillones`).
- **No hay ruta que diga quién es el usuario** ni sus roles (`GET /auth/yo` quedó para C-08 «si lo necesita», C-07 R-Non-Goals), **ni cierre de sesión en el servidor** (RN-AU-03: no hay revocación de a uno).
- **`backend/app/main.py`** no registra `CORSMiddleware`: un navegador en otro origen (`http://127.0.0.1:5173`) no puede leer las respuestas de la API en `127.0.0.1:8000`.
- **Demo sin Docker** (`crear_app_demo`): SQLite en memoria con `odontologa@consultorio-demo.test` (`odontologo` + `dueno`) y `recepcion@consultorio-demo.test` (`recepcionista`), los dos activos, con la contraseña de demostración del seed; **no hay usuario inactivo** en la demo.
- **Compose** (`docker-compose.yml`): servicios `postgres` (`127.0.0.1:5434`) y `api` (`127.0.0.1:8000`), imágenes fijadas por etiqueta y digest (D144). La imagen de la API (`backend/Dockerfile`) es de dos etapas, sin root y con `HEALTHCHECK`.
- **KB**: `02` («Arquitectura general») dibuja una SPA con `/panel/...` autenticado y `/reservar/{slug}` público; `08` («Estructura de directorios») prevé `frontend/src/{features,shared,pages}` y el servicio `frontend` en Compose; `08` («Versiones y dependencias») dice «las versiones exactas de React y Vite no están decididas» y fija **un único archivo de dependencias, `backend/pyproject.toml`** (D137). `PUBLIC_BASE_URL` tiene como ejemplo `http://localhost:5173` (`08`, «Variables de entorno»).
- **Máquina del autor** (comprobado hoy): Node **23.5.0** y npm 10.9.2. Node 23 ya no tiene soporte y **no** satisface los `engines` de Vitest 5 (`^22.12.0 || ^24.0.0 || >=26.0.0`) ni de jsdom 30 (`^22.22.2 || ^24.15.0 || >=26.0.0`).
- **`openspec/config.yaml`**: `openspec context` avisa que `rules.tasks[5]` se lee como un mapa (hay un «: » sin comillas en la regla de la prueba en el navegador) y que por eso **ignora todas las reglas de `tasks`**. Este design y `tasks.md` las aplican igual, leídas del archivo (ver «Contradicciones», punto 9).

## Goals / Non-Goals

**Goals:**

- Que el panel no muestre nada del panel sin una sesión, y que **cualquier** `401` de la API termine en una renovación o en el inicio de sesión, nunca en una pantalla rota.
- Que la lógica de sesión (guardar, renovar, olvidar) sea **TypeScript puro**, testeable sin navegador real ni backend, con la API reemplazada por un servidor falso inyectado y no por `vi.mock`.
- Que la interfaz **no revele** si un email existe ni si un usuario está inactivo (RN-AU-04), igual que la API.
- Que la suite del frontend corra solo con Node y el README, sin Docker ni Python.
- No tocar la API.

**Non-Goals:**

- Renovar el access **antes** de que venza (por temporizador con `expires_in`): la renovación es reactiva, ante el `401` (F8).
- Compartir la sesión entre pestañas o sobrevivir al cierre del navegador (F7, D219).
- Mostrar el nombre o los roles del usuario (no hay ruta que los dé; D225).
- Un sistema de diseño, componentes reutilizables o estilos más allá de lo mínimo legible.
- Pruebas automatizadas de extremo a extremo con un navegador real (Playwright, Cypress): la verificación contra la API real es la prueba del agente en el navegador (F16).

## Decisions

### F1. Una capability nueva, `ingreso-al-panel` — Decisión del autor (D218)

Los requisitos de la interfaz van en una capability nueva, `ingreso-al-panel`: la pantalla de inicio de sesión, la sesión en el navegador, la renovación, la vuelta al inicio de sesión, las rutas protegidas y el cierre de sesión. `sesion-del-panel` y `proteccion-del-panel` **no** reciben delta: describen la API, que no cambia, y siguen siendo la fuente del contrato que la interfaz consume.

**Alternativas descartadas:** (a) deltas a `sesion-del-panel` (la pantalla) y `proteccion-del-panel` (las rutas de la interfaz): mezclan el contrato de la API con el comportamiento del navegador y un mismo requisito quedaría repartido en dos capabilities (regla dura 12, «un change, una capability»); (b) una capability amplia `interfaz-del-panel`: crecería con cada pantalla de negocio de los changes siguientes, que tienen su propia capability.

### F2. Archivo de dependencias del frontend — Decisión del autor (D217; amplía D137)

D137 fija **un único archivo de dependencias, `backend/pyproject.toml`**, y `config.yaml` repite la regla («Fijar las versiones exactas … en backend/pyproject.toml»). Un proyecto de Node no puede declarar sus dependencias ahí: npm solo lee `package.json`. No se resolvió en silencio (regla dura 9 y CLAUDE.md, «Flujo de trabajo»): se planteó como pregunta y **el autor decidió (D217)**:

- **Decidido (D217):** `frontend/package.json` es el archivo único **del frontend**, con versiones exactas (sin `^` ni `~`; `save-exact=true` en `frontend/.npmrc`), y `frontend/package-lock.json` es el archivo de bloqueo que genera npm (no se edita a mano y fija también las dependencias transitivas). D137 pasa a leerse «un archivo de dependencias por subproyecto»: `backend/pyproject.toml` para Python y `frontend/package.json` para Node, sin duplicar ningún paquete entre los dos.
- **Alternativas descartadas:** (a) un `package.json` en la raíz del repositorio con *workspaces*: agrega una capa sin necesidad (hay un solo proyecto de Node); (b) declarar las dependencias de Node en `pyproject.toml` y generar el `package.json` con un script: inventa una herramienta y contradice la forma estándar de instalar.

### F3. Versiones fijadas — Decisión del autor (D223, D224) + Propuesta (aplica D116, D133, D144)

Consultadas el **2026-10-19** en el registro de npm (`npm view <paquete> time`, `dist-tags`, `peerDependencies`, `engines`), en `https://nodejs.org/dist/index.json` y en la API de Docker Hub (`/v2/repositories/<repo>/tags/<etiqueta>`). **Corte de D133:** nada publicado desde el **2026-10-12** (la semana anterior al día del design). La compatibilidad sale de los metadatos, no se supone.

| Paquete | Versión | Publicada | Por qué esa | Grupo |
|---|---|---|---|---|
| `react` | 19.3.0 | 2026-09-09 | La 19.3.1 (`latest`) y las 19.2.9 / 19.1.10 / 19.0.9 son del 2026-10-14: excluidas | `dependencies` |
| `react-dom` | 19.3.0 | 2026-09-09 | Ídem; `peerDependencies` `react ^19.3.0` | `dependencies` |
| `react-router` | 7.18.4 | 2026-09-15 | Línea 7 mantenida (`dist-tag` `version-7`); `peer` `react >=18`, `node >=20`. Alternativa 8.4.0 (`latest`, misma fecha; D224) | `dependencies` |
| `typescript` | 6.0.3 | 2026-04-16 | Última de la línea 6 (compilador en JavaScript). Alternativa 7.0.2 (`latest`, 2026-07-08; D224) | `devDependencies` |
| `vite` | 8.3.4 | 2026-10-08 | `latest`; `engines` `node ^20.19.0 \|\| >=22.12.0` | `devDependencies` |
| `@vitejs/plugin-react` | 6.1.2 | 2026-10-05 | `latest`; `peer` `vite ^8.0.0` | `devDependencies` |
| `vitest` | 5.0.3 | 2026-09-30 | La 5.0.4 (2026-10-12) y la 5.0.5 (2026-10-15) quedan excluidas; `peer` `vite ^6.4.0 \|\| ^7.0.0 \|\| ^8.0.0`, `jsdom *`; `engines` `node ^22.12.0 \|\| ^24.0.0 \|\| >=26.0.0` | `devDependencies` |
| `jsdom` | 30.1.2 | 2026-10-04 | La 30.1.3 (2026-10-15) queda excluida; `engines` `node ^22.22.2 \|\| ^24.15.0 \|\| >=26.0.0` | `devDependencies` |
| `@testing-library/react` | 16.3.3 | 2026-08-27 | `peer` `react ^18 \|\| ^19`, `react-dom ^18 \|\| ^19`, `@testing-library/dom ^10.0.0` | `devDependencies` |
| `@testing-library/dom` | 10.4.2 | 2026-09-13 | Exigida como `peer` por la anterior | `devDependencies` |
| `@testing-library/user-event` | 14.6.7 | 2026-09-02 | La 14.6.8 (2026-10-13) queda excluida; `peer` `@testing-library/dom >=7.21.4` | `devDependencies` |
| `@types/react` | 19.3.0 | 2026-09-09 | Tipos de la 19.3 | `devDependencies` |
| `@types/react-dom` | 19.3.0 | 2026-09-09 | `peer` `@types/react ^19.3.0` | `devDependencies` |
| `@types/node` | 24.19.2 | 2026-10-09 | **Solo si V2 lo exige** (tipos de `vite.config.ts`); misma línea que Node 24 | `devDependencies` |

**Node:** **24.21.0** (LTS «Krypton», 2026-09-07; la 24.22.0 es del 2026-10-14). Es la que usa la imagen de construcción; el README pide «Node 24 LTS, 24.15 o superior» (el piso de jsdom) y `package.json` lo declara en `engines` (`"node": ">=24.15.0 <25"`), con `engine-strict=true` en `.npmrc` para que `npm ci` frene con un Node que no sirve. npm: el que trae ese Node (no se fija aparte).

**Imágenes de Docker** (D144: etiqueta y digest; la regla de la semana se aplica al último push de la etiqueta):

| Imagen | Etiqueta | Último push | Digest |
|---|---|---|---|
| `node` (etapa de construcción) | `24.21.0-bookworm-slim` | 2026-10-06 | `sha256:d6aa754f16b3197301076f047b5def2f02ea1dbbc2ca920407d46d7ec7f87b20` |
| `nginxinc/nginx-unprivileged` (etapa final) | `1.30.4-alpine` | 2026-09-14 | `sha256:adf5042a17f4ecdd200c595fa9ffd1be37efb18f89a830bd1a00e4ab4d59d42c` |

`nginx` 1.30 es la línea estable; `1.30.5-alpine` (push 2026-10-12) y `1.30.6-alpine` (2026-10-19) quedan excluidas. Se eligió `bookworm` para la etapa de Node por coherencia con la imagen de la API (`python:3.13.15-slim-bookworm`).

**Dependencias transitivas:** la regla D133 vale «para ningún paquete», pero un `npm install` común resuelve cada transitiva a la más nueva que admita su rango. El archivo de bloqueo se genera **una sola vez** con `npm install --before=2026-10-12` (npm toma, para cada paquete, la versión más nueva publicada antes de esa fecha) y después se instala siempre con `npm ci`. **A verificar en el change (V1, antes de cerrar la tarea 1.3).**

**No entran** (Propuesta): `@testing-library/jest-dom` (las consultas de Testing Library ya fallan si el elemento falta; se compara texto y atributos con `expect`), `msw` (F13), ESLint y `typescript-eslint` (F13, D227), bibliotecas de estado o de datos (SWR, TanStack Query: con dos peticiones no se justifican), CSS en JS o bibliotecas de componentes.

### F4. Estructura de `frontend/` — Propuesta (aplica `08`, «Estructura de directorios»)

```
frontend/
├── package.json            # archivo único del frontend (F2)
├── package-lock.json       # generado con --before (F3)
├── .npmrc                  # save-exact=true, engine-strict=true
├── tsconfig.json           # strict, noEmit (F13)
├── vite.config.ts          # plugin de React, proxy /api (F5), configuración de Vitest (F13)
├── index.html
├── Dockerfile, nginx.conf, .dockerignore   (F14)
└── src/
    ├── main.tsx            # monta <App/> con BrowserRouter
    ├── App.tsx             # rutas (F6)
    ├── shared/api/         # clienteHttp.ts, sesion.ts, errores.ts (F7, F8, F12)
    ├── features/ingreso/   # PaginaIngreso.tsx y su lógica de formulario (F9)
    ├── pages/              # PanelBase.tsx, RutaProtegida.tsx (F10, F11)
    └── test/               # servidorFalso.ts, guards (F13)
```

Los componentes van en PascalCase, uno por archivo, nunca definidos dentro de otro componente (regla dura 8; `vercel-react-best-practices`). Sin archivos *barrel* (`index.ts` que reexporta): cada import apunta al archivo.

### F5. Mismo origen: la interfaz habla con la API por `/api` — Decisión del autor (D220)

El navegador nunca llama a `127.0.0.1:8000` directamente: llama a **`/api/...` del mismo origen** que sirvió la página, y el servidor del frontend reenvía a la API quitando el prefijo (`/api/auth/login` → `/auth/login`).

- **Desarrollo** (`npm run dev`, `127.0.0.1:5173`): `server.proxy` de Vite, `'/api' → http://127.0.0.1:8000` con `rewrite` que quita `/api`.
- **Compose**: `nginx.conf` con `location /api/ { proxy_pass http://api:8000/; }` (la barra final quita el prefijo) y el resto con `try_files $uri /index.html` para que `/panel/...` funcione al recargar.

**Por qué:** la API no tiene CORS y agregarlo es un cambio de API, fuera del alcance de C-08 (`CHANGES.md`); el mismo origen además evita *preflight* y deja la puerta abierta a una cookie `HttpOnly` en el futuro sin CORS con credenciales. El prefijo `/api` evita que una ruta de la interfaz (`/panel`, `/reservar`) choque con una de la API. **Sin variable de entorno nueva**: la base `/api` es fija en el código.

**Alternativa descartada:** `CORSMiddleware` en FastAPI con el origen del frontend (cambio de API; habría que versionar y probar el origen permitido).

### F6. Rutas de la interfaz — Propuesta

| Ruta | Qué muestra |
|---|---|
| `/ingresar` | Pantalla de inicio de sesión. Con una sesión activa, redirige a `/panel`. |
| `/panel` (y todo `/panel/*`) | Panel base, protegido (F10). Los changes siguientes agregan sus pantallas debajo. |
| `/` y cualquier otra | Redirige a `/panel` (que, sin sesión, lleva a `/ingresar`). |

La ruta pedida viaja en el **estado de navegación** del router (no en la URL como `?siguiente=`): así no hay redirección abierta a otro sitio, y solo se vuelve a una ruta que empiece con `/panel`. `/reservar/...` no existe todavía (C-28).

### F7. Dónde vive la sesión — Decisión del autor (D219)

El **access token** vive **solo en memoria** (una variable del módulo de sesión, nunca en `localStorage` ni en el estado de React que se serializa). El **refresh token** vive en **`sessionStorage`** con una clave versionada (`turnos.sesion.v1`, solo `{ "refresh": "<token>" }`).

- Recargar la pestaña conserva la sesión: al arrancar se renueva el access con el refresh guardado (F10).
- Cerrar la pestaña o el navegador la termina; otra pestaña pide iniciar sesión otra vez.
- Si `sessionStorage` no está disponible o lanza (modo privado, almacenamiento bloqueado), la sesión vive solo en memoria y recargar pide iniciar sesión: se envuelve cada acceso en `try`/`catch` y nunca se rompe la pantalla.
- **Riesgo aceptado:** un script inyectado (XSS) podría leer el refresh de `sessionStorage`. Lo mitigan React (escapa el texto por defecto), la ausencia de HTML crudo (`dangerouslySetInnerHTML` prohibido por el guard de F13) y la política de contenido de nginx (F14). La opción que lo evita, una cookie `HttpOnly`, cambia el contrato de `/auth/refresh` y suma CSRF: es un cambio de API fuera de C-08 (C-06 J20).

**Alternativas descartadas:** (a) los dos tokens solo en memoria: lo más seguro, pero cada recarga (F5) pide la contraseña; (b) `localStorage`: la sesión sobrevive al cierre del navegador durante los 7 días del refresh, también en una computadora compartida de recepción, y queda expuesta a XSS por más tiempo; (c) cookie `HttpOnly` (descartada: cambio de API).

### F8. Cliente HTTP y renovación — Propuesta (aplica RN-AU-03, US-094)

`src/shared/api/clienteHttp.ts` expone dos funciones y recibe **`fetch` inyectado** (por defecto `globalThis.fetch`; en los tests, el servidor falso de F13):

- `iniciarSesion(email, contrasena)`: `POST /api/auth/login` con `{"email", "contrasena"}`; con `200` guarda los dos tokens (F7) y devuelve; el resto se traduce con F12. **Nunca** intenta renovar ante su propio `401`.
- `pedidoDelPanel(ruta, opciones)`: agrega `Authorization: Bearer <access>`; si responde `401`:
  1. Si no hay refresh guardado → `SesionTerminada`.
  2. Si no, **una** renovación con `POST /api/auth/refresh`. Varias peticiones que reciben `401` a la vez esperan **la misma** promesa de renovación (se guarda la promesa en curso; *single flight*).
  3. Con `200`, guarda el access nuevo y **repite la petición original una sola vez**; si la repetición vuelve a dar `401`, no se renueva de nuevo: `SesionTerminada` (sin bucles) y se borra la sesión (memoria y `sessionStorage`) para que la pantalla vuelva al inicio de sesión (aceptado por el orquestador en el Apply, grupo 4).
  4. Con `401` en la renovación → borra la sesión (memoria y `sessionStorage`) y `SesionTerminada`.

`SesionTerminada` la recibe el proveedor de sesión de React (F10), que navega a `/ingresar` con el aviso de F9. Un `403` **no** termina la sesión: se devuelve al llamador (cada pantalla futura decide cómo mostrarlo). La renovación es **reactiva**: no se usa `expires_in` para programar una renovación anticipada (Non-Goals); el costo es un `401` extra cada 15 minutos de uso.

En C-08 **ninguna pantalla llama a `pedidoDelPanel`** (el panel base está vacío, D225): queda probado por la suite y listo para C-09 en adelante. La renovación al arrancar (F10) sí ocurre en el navegador.

### F9. Pantalla de inicio de sesión y sus mensajes — Propuesta (aplica RN-AU-04)

Formulario con «Email» (`type="email"`, `autocomplete="username"`) y «Contraseña» (`type="password"`, `autocomplete="current-password"`), etiquetas asociadas y botón «Ingresar». Mensajes **fijos de la interfaz** (no se muestra el `detail` de la API, para que un cambio de texto en el servidor no cambie la pantalla):

| Situación | Mensaje | Campos |
|---|---|---|
| `401` del login (email inexistente, contraseña incorrecta o usuario inactivo) | «El email o la contraseña no son correctos.» | Se conserva el email y se vacía la contraseña |
| `422` del login | «Revisá el email y la contraseña.» | Igual |
| Sin respuesta, error de red o `5xx` | «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» | Se conservan los dos |
| Llegada desde `SesionTerminada` (F8, F10) | «Tu sesión terminó. Iniciá sesión de nuevo.» (aviso, no error) | Vacíos |

Mientras la petición está en curso el botón queda deshabilitado y dice «Ingresando…», para no mandar dos logins. El email no se normaliza en la interfaz (la API ya lo hace, `sesion-del-panel`). La contraseña no se guarda en ningún lado ni se escribe en la consola; el formulario usa `method="post"` y `preventDefault`, de modo que, aun si fallara el JavaScript, los datos nunca quedan en la URL.

### F10. Arranque y rutas protegidas — Propuesta

Un `ProveedorDeSesion` (contexto de React) tiene tres estados: `verificando`, `con-sesion`, `sin-sesion`.

- **Arranque:** si hay refresh en `sessionStorage`, el estado empieza en `verificando` (inicialización perezosa de `useState`) y se pide `POST /api/auth/refresh`; con `200` pasa a `con-sesion`; con `401` borra la sesión y pasa a `sin-sesion` con el aviso «Tu sesión terminó»; con un error de red pasa a `sin-sesion` con el mensaje de conexión, **sin borrar** el refresh (la API puede estar reiniciando). Sin refresh guardado, empieza en `sin-sesion` sin pedir nada.
- **`RutaProtegida`:** en `verificando` muestra «Cargando…» (nunca el panel); en `sin-sesion` redirige a `/ingresar` guardando la ruta pedida (F6); en `con-sesion` muestra la ruta.
- **`/ingresar` con sesión:** redirige a `/panel`.

Reglas de React aplicadas (`vercel-react-best-practices`): estado derivado durante el render (si hay sesión se calcula, no se copia), `setState` funcional, dependencias primitivas en el único efecto (el del arranque, con limpieza para no actualizar un componente desmontado) y ternarios en lugar de `&&` en el JSX.

### F11. Panel base y cierre de sesión — Decisión del autor (D225, D226)

`/panel` muestra un encabezado con «Turnos Odontológicos AR» y el botón **«Cerrar sesión»**, y un cuerpo con «Panel del consultorio» y ningún dato. No se muestra quién inició sesión (no hay ruta que lo informe, y decodificar el JWT en el navegador daría solo el id; D225).

«Cerrar sesión» borra el access de la memoria y el refresh de `sessionStorage` y navega a `/ingresar` **reemplazando** la entrada del historial (el botón «Atrás» no vuelve a mostrar el panel). **No llama a la API** (no hay ruta de cierre): el refresh sigue siendo válido en el servidor hasta su vencimiento o hasta que cambie la `token_version` del usuario. Va como límite conocido del README.

### F12. Clases de rechazo y orden de evaluación en la interfaz — Propuesta (aplica RN-GL-02 y D208 desde el lado del cliente)

La interfaz no evalúa reglas de negocio; solo clasifica lo que recibe:

1. **Validación local** (antes de enviar): email o contraseña vacíos (`required`) → no se envía nada; el navegador marca el campo. No hay más validación local (el formato del email y el largo de la contraseña los decide la API).
2. **Control de acceso** (respuesta de la API): `401` del login → mensaje genérico (F9); `401` de una ruta del panel → renovación (F8); `401` de la renovación → `SesionTerminada`; `403` → se devuelve al llamador.
3. **Validación de entrada de la API**: `422` del login → «Revisá el email y la contraseña».
4. **Falla de transporte**: sin respuesta, cuerpo que no se puede leer o `5xx` → `SinConexion` (mensaje de conexión).

Los errores son clases de TypeScript en `src/shared/api/errores.ts` (`CredencialesRechazadas`, `EntradaRechazada`, `SesionTerminada`, `SinConexion`), cada una con el código RN cuando la API lo dio (`RN-AU-04`, `RN-AU-03`), para que los tests verifiquen el código y no el texto.

### F13. Tests del frontend — Decisión del autor (D222, D227) + Propuesta (detalle)

- **Runner:** Vitest 5.0.3 con `environment: 'jsdom'` y `globals: false` (cada test importa `describe`, `it`, `expect`), configurado en `vite.config.ts`. Comandos de `package.json`: `npm test` (`vitest run`) y `npm run typecheck` (`tsc --noEmit`). `npm test` no levanta servidores ni necesita el backend, Docker ni red.
- **Capas:** (a) **unidad** de `sesion.ts` y `clienteHttp.ts` con el servidor falso (sin React); (b) **componentes** con Testing Library + `user-event` sobre `<App/>` dentro de un `MemoryRouter` (V5), con el `fetch` falso inyectado por el proveedor de sesión.
- **Servidor falso de la API** (`src/test/servidorFalso.ts`): una función con la firma de `fetch`, **escrita a mano**, que implementa en memoria el contrato de `sesion-del-panel` y `proteccion-del-panel`: usuarios ficticios (`odontologa@consultorio-demo.test` activa, `recepcion@consultorio-demo.test` inactiva en el falso), tokens opacos generados por el falso, `401` con los cuerpos `problem+json` reales (`codigos`, `type`, `title`, `detail` copiados de los specs), y perillas para los tests (`vencerAccess()`, `invalidarRefresh()`, `caerse()`, contador de peticiones por ruta). **No** es `vi.mock` ni `vi.fn` sobre módulos: es una implementación alternativa inyectada, el mismo criterio que el backend aplica con SQLite real en lugar de mocks (regla dura 6).
- **Riesgo de que el falso se aparte de la API real** → sus respuestas citan el spec de la capability de donde salen, y la prueba del agente en el navegador (F16) recorre los mismos escenarios contra la API real.
- **Guards** (`src/test/guards.test.ts`, como los del backend): recorren `frontend/src` y fallan si encuentran el tipo `any` (`: any`, `as any`, `<any>`, `any[]`), `vi.mock(` o los *stubs* de `fetch`, `dangerouslySetInnerHTML`, `localStorage` o un archivo *barrel* (`index.ts`). Que ningún token llegue a la consola se revisa en la prueba en el navegador (F16), no con un guard. **Alternativa descartada** (D227): ESLint con `typescript-eslint` y `no-explicit-any` (más preciso, pero suma cinco paquetes y su compatibilidad con TypeScript 6 o 7 habría que verificarla).
- **TypeScript estricto:** `strict: true`, `noUncheckedIndexedAccess`, `noImplicitOverride`, `noFallthroughCasesInSwitch`, `exactOptionalPropertyTypes`, `verbatimModuleSyntax`, `moduleResolution: "bundler"`, `jsx: "react-jsx"`, `noEmit` (V6). `npm run typecheck` es parte de la verificación de cada grupo.
- Nombres de test con el escenario (`it('US-090 CA-2: email inexistente muestra el mensaje genérico')`). TDD estricto: el RED se demuestra corriendo `npm test`.

### F14. Servicio `frontend` en Docker Compose — Decisión del autor (D221) + Propuesta (`nginx.conf`; aplica D144, `multi-stage-dockerfile`)

`frontend/Dockerfile` de dos etapas con nombre:

1. `construccion` (`node:24.21.0-bookworm-slim@sha256:…`): copia **primero** `package.json`, `package-lock.json` y `.npmrc`, corre `npm ci`, después copia el resto y corre `npm run build` (`tsc --noEmit && vite build`). Los tests no corren en la imagen (corren en la suite).
2. `servidor` (`nginxinc/nginx-unprivileged:1.30.4-alpine@sha256:…`): copia `dist/` y `nginx.conf`; corre como el usuario sin privilegios de la imagen y escucha en `8080` (V4). `HEALTHCHECK` con `wget -q -O /dev/null http://127.0.0.1:8080/`.

`nginx.conf` (Propuesta): el proxy de `/api/` de F5; `try_files $uri /index.html`; `index.html` con `Cache-Control: no-store` y los archivos con hash de `assets/` con caché larga; cabeceras `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`, `X-Content-Type-Options: nosniff` y `Referrer-Policy: no-referrer`. `.dockerignore` excluye `node_modules`, `dist` y todo `.env*`.

`docker-compose.yml` agrega `frontend` con `build: ./frontend`, `depends_on: api: condition: service_healthy` y `ports: "127.0.0.1:5173:8080"`. Mismo puerto que `npm run dev`: igual que la API (demo y Compose en el `8000`), son dos formas alternativas de levantar lo mismo y el README avisa que se detiene una antes de la otra. No hay variables nuevas ni secretos en la imagen.

**Alternativa descartada:** correr `vite` (servidor de desarrollo) dentro del contenedor: monta el código, no es lo que se despliega y no sirve el resultado de `vite build`.

### F15. README — Propuesta

Sección nueva «Panel (interfaz)»: requisitos (Node 24 LTS, 24.15 o superior; cómo comprobarlo con `node --version`), instalación (`cd frontend`, `npm ci`), tests (`npm test`, `npm run typecheck`), la demo sin Docker en **dos terminales** (la API de demostración con `crear_app_demo` y `npm run dev`; abrir `http://127.0.0.1:5173`), los usuarios de prueba, el recorrido (iniciar sesión, mensaje genérico, recargar, cerrar sesión), Compose con el servicio `frontend` (`http://127.0.0.1:5173`), la tabla escenario → test del frontend, las versiones fijadas del frontend y los límites conocidos: cerrar sesión no revoca el refresh (F11); la sesión no se comparte entre pestañas ni sobrevive al cierre (F7); el refresh en `sessionStorage` es legible por un script inyectado (F7); un `401` extra cada 15 minutos (F8); los puertos `5173` y `8000` tienen que estar libres. Se actualizan «Qué entrega hasta ahora» y se quitan «No hay interfaz gráfica» y el límite «Dónde guarda el panel los tokens … se decide en C-08».

### F16. Prueba en el navegador — Propuesta

**Demo** (`crear_app_demo` + `npm run dev`): `/panel` sin sesión lleva a `/ingresar`; la odontóloga con su contraseña entra y vuelve a `/panel`; una contraseña incorrecta y `nadie@consultorio-demo.test` muestran **el mismo** mensaje y en la pestaña de red se ve el `401` `RN-AU-04` por `/api/auth/login`; recargar `/panel` mantiene la sesión (se ve un `POST /api/auth/refresh` `200`); «Cerrar sesión» vuelve a `/ingresar` y «Atrás» no muestra el panel; ningún token aparece en la URL ni en la consola. **Compose** (`docker compose up --build -d`): `http://127.0.0.1:5173` sirve la interfaz, `/api/openapi.json` llega a la API, recargar `/panel` directo no da `404`; con `UPDATE usuario SET activo = false WHERE email = 'recepcion@consultorio-demo.test'`, la recepcionista ve el mismo mensaje genérico (US-090 CA-3) y se restaura; con `UPDATE usuario SET token_version = token_version + 1 WHERE id = 1`, recargar `/panel` lleva a `/ingresar` con «Tu sesión terminó» (US-092 CA-1). El contenedor corre sin root (`docker compose exec frontend id`).

### F17. Lo que el backend no cambia — Propuesta

Ningún archivo de `backend/` se modifica. La tarea 1.1 toma la línea base de `python -m pytest` y la verificación final la repite: mismo número de tests en verde. `git diff --stat backend/` vacío al cerrar.

### F18. Tamaño y forma de trabajo del Apply — Decisión del autor (D228; continúa D216)

**22 tareas en 10 grupos**, dos más que el «alrededor de 20» de `CHANGES.md`: es la **séptima excepción registrada** (D228; tras D123, D134, D152, D161, D203 y D216). Motivos: el primer proyecto de Node (preparación con su tarea del autor y el archivo de bloqueo), cuatro escenarios con RED, GREEN y TRIANGULATE repartidos en tres capas (sesión, pantalla, rutas), el servicio de Compose y las cuatro tareas fijas de navegador y verificación. Hay una **tarea del autor** antes de empezar (instalar Node 24 LTS, tarea 1.2). Commits por tarea con el ok del autor dado por adelantado para el Apply, en español, con prefijo y `Co-Authored-By`; sin `--amend`. Los artefactos de este propose y la KB se commitean con el ok del autor antes del Apply. `CHANGES.md` y `.env*` no se tocan.

### Skills aplicadas

- `vercel-react-best-practices`: SPA de Vite, así que **no aplican** las reglas de Next.js, RSC y servidor. **Aplicadas:** sin cascadas de peticiones (solo hay una al arrancar), sin imports *barrel*, estado derivado en el render, `setState` funcional, `useState` perezoso para leer `sessionStorage` una vez, dependencias primitivas en los efectos, componentes fuera de otros componentes, ternario en vez de `&&`, datos de `sessionStorage` mínimos y versionados (`turnos.sesion.v1`). **No aplicadas** (registro): SWR o TanStack Query para deduplicar (con dos peticiones no se justifica; la renovación compartida de F8 cubre la única duplicación posible) y `React.lazy` (no hay partes pesadas todavía).
- `auth-implementation-patterns`: el servidor valida siempre (la interfaz no decide nada sobre la sesión, solo reacciona), mensaje genérico ante credenciales inválidas (RN-AU-04), renovación con el refresh, ningún token en la URL ni en los registros. **[ADAPT]** dónde guardar los tokens: la KB no lo decide; lo decidió el autor (D219), y la cookie `HttpOnly` se descarta por ser un cambio de API. **Contradicción con la KB:** la skill pide límite de intentos y bloqueo de cuenta en el login; siguen fuera por D195 (manda la KB, regla dura 9).
- `multi-stage-dockerfile`: etapas con nombre, base fijada por etiqueta y digest (D144), manifiesto de dependencias copiado antes que el código, `.dockerignore`, sin secretos, sin root, `HEALTHCHECK`. La suite del frontend no necesita Docker.
- Las skills de Python (`fastapi-templates`, `python-*`) y de base de datos no aplican: el backend no cambia (F17).

## Contradicciones y huecos encontrados en las fuentes

1. **D137 y `config.yaml` (regla de `design`) fijan un único archivo de dependencias, `backend/pyproject.toml`**; un frontend de Node necesita `package.json` y su archivo de bloqueo. → D217 (F2): un archivo por subproyecto.
2. **«Cambios de API» está fuera de alcance, pero la API no tiene CORS**: un frontend en otro origen no puede leer sus respuestas. → D220 (F5: mismo origen por proxy, sin tocar la API).
3. **Dónde guarda el panel los tokens** no está en la KB (C-06 J20 y el README lo dejaron para C-08). → D219 (F7).
4. **No hay ruta para saber quién es el usuario ni para cerrar sesión**, y agregarlas es un cambio de API. → D225 y D226 (F11): panel sin datos del usuario y cierre de sesión solo en el cliente.
5. **Node 23.5.0 de la máquina del autor** no cumple los `engines` de Vitest 5 ni de jsdom 30 (y Node 23 ya no tiene soporte). → D223 (F3) y tarea del autor 1.2.
6. **Las majors más nuevas de TypeScript (7.0.2) y React Router (8.4.0)** son de julio y septiembre de 2026; la documentación disponible para este design (Context7) llega hasta React Router 7.9, así que la API de la 8 no se pudo verificar. → D224 (F3).
7. **US-092 CA-1 es un criterio de la API** («un endpoint del panel sin token o con token vencido responde `401`») y C-07 ya lo cumple; `CHANGES.md` lo pone entre los escenarios mínimos de C-08. → Se lee desde la interfaz: lo que el panel hace con ese `401` (renovar o volver al inicio de sesión). US-094 CA-1 y CA-2 se usan dentro de ese escenario, sin contarse aparte.
8. **US-090 CA-3 (usuario inactivo) no se puede mostrar en la demo sin Docker**: la demo no trae un usuario inactivo y agregarlo sería tocar el seed (backend). → Se prueba con el servidor falso en la suite y en Compose desactivando a la recepcionista con SQL (F16).
9. **`openspec/config.yaml`, `rules.tasks[5]`**: el texto «La repetición a mano del autor es opcional: va como tarea…» tiene un «: » sin comillas y YAML lo lee como un mapa; `openspec` avisa y **descarta todas las reglas de `tasks`**. → Este change las aplica igual; la corrección (poner la regla entre comillas) va en «Notas para el archive».
10. **`config.yaml`, contexto «Sesión (desde C-06)»**: la frase quedó cortada («ninguna ruta exige el token desde C-07 las rutas del panel exigen…»). → Nota para el archive (corrección de redacción).
11. **`08` dice que el directorio del frontend es `frontend/src/{features,shared,pages}`** y no dice dónde van los tests. → F4 los pone junto al código (`*.test.ts(x)`) y el servidor falso en `src/test/`.
12. **El `Dockerfile` de la API** usa `python:…-bookworm`; para nginx sin root la imagen oficial `nginx` necesita configuración extra y `nginxinc/nginx-unprivileged` es de NGINX Inc. (editor verificado, no «imagen oficial» de Docker). → F14 la elige y lo deja dicho; D221.
13. **Mismo puerto `5173`** para `npm run dev` y para el servicio de Compose. → Igual que la API (`8000` en demo y Compose); el README avisa (F14).

## Risks / Trade-offs

- [El servidor falso puede apartarse de la API real] → Respuestas copiadas de los specs vigentes; la prueba del agente en el navegador repite los escenarios contra la API real (F16); un cambio futuro del contrato de la API obliga a tocar el falso en el mismo change.
- [Refresh en `sessionStorage` legible por XSS] → React escapa por defecto, guard contra `dangerouslySetInnerHTML`, CSP de nginx; la sesión muere al cerrar la pestaña. La solución completa (cookie `HttpOnly`) es un cambio de API.
- [Cerrar sesión no revoca el refresh] → Límite del README; el refresh solo estaba en `sessionStorage` y se borra; para cortar todo, subir `token_version` (C-09, C-10).
- [Dependencias transitivas más nuevas que el corte de D133] → `npm install --before=2026-10-12` y `npm ci` (V1).
- [Una dependencia de npm comprometida] → Versiones exactas, archivo de bloqueo con `integrity`, `npm ci`, ninguna dependencia con *postinstall* propia salvo las de las herramientas (se revisa en V1).
- [Node 24 obligatorio para el frontend] → Tarea del autor 1.2; el backend sigue funcionando sin Node.
- [Un `401` extra cada 15 minutos] → Aceptado (renovación reactiva, F8).
- [Si la API se cae mientras se recarga el panel, la persona ve el inicio de sesión] → Se conserva el refresh y el mensaje dice que no hay conexión (F10); al volver la API, recargar recupera la sesión.

## A verificar en el change

- **V1** (antes de cerrar la tarea 1.3): que `npm install --before=2026-10-12` con el npm de Node 24.21.0 genera un `package-lock.json` donde **ningún** paquete tiene una versión publicada desde el 2026-10-12 (se comprueba con un script que recorre el archivo de bloqueo y consulta `npm view <paquete>@<versión> time`), que las versiones directas son las de F3 y que `npm ci` instala sin avisos de `peer` ni de `engines`.
- **V2** (antes de cerrar la tarea 1.3): si `tsc --noEmit` sobre `vite.config.ts` necesita `@types/node`; solo entonces se agrega `@types/node` 24.19.2.
- **V3** (antes de la tarea 3.1): que Vitest 5.0.3 acepta `test.environment: 'jsdom'` en `vite.config.ts` (con `/// <reference types="vitest/config" />` o `defineConfig` de `vitest/config`) y que jsdom 30.1.2 trae `sessionStorage`.
- **V4** (antes de la tarea 7.1): que `nginxinc/nginx-unprivileged:1.30.4-alpine` corre sin root, escucha en `8080` y trae `wget`; que el digest de F3 corresponde a esa etiqueta (`docker buildx imagetools inspect`); y que `proxy_pass http://api:8000/;` dentro de `location /api/` quita el prefijo.
- **V5** (antes de la tarea 5.1): que `react-router` 7.18.4 exporta `BrowserRouter`, `MemoryRouter`, `Routes`, `Route`, `Navigate`, `useNavigate` y `useLocation` desde el paquete `react-router` (sin `react-router-dom`). La 8.4.0 quedó descartada (D224).
- **V6** (antes de cerrar la tarea 1.3): que TypeScript 6.0.3 acepta las opciones de F13 sin avisos de opciones obsoletas. La 7.0.2 quedó descartada (D224).

## Migration Plan

1. Con el ok del autor, se commitean los artefactos y la KB (decisiones D217 a D228).
2. El autor instala Node 24 LTS (tarea 1.2).
3. El Apply crea `frontend/` y el servicio de Compose. `docker compose up --build -d` sobre el volumen existente agrega el contenedor `frontend`; `postgres` y `api` no cambian.
4. **Vuelta atrás:** borrar `frontend/` y el servicio de `docker-compose.yml`; la API y la base no se tocaron (F17).

## Notas para el archive

Correcciones que estas decisiones piden fuera del change. **No se editan ahora ni durante el Apply**: van en el commit `docs(kb)` del archive (y, las de `openspec/`, en el commit del archive), como en C-03 a C-07.

- `knowledge-base/08_arquitectura_propuesta.md`, «Versiones y dependencias»: el archivo único por subproyecto (D217), las versiones del frontend y de Node, el método `--before` y las imágenes nuevas; «Estructura de directorios»: `frontend/` con sus archivos (F4); «Interfaz»: el proxy `/api` (F5). «Variables de entorno»: `PUBLIC_BASE_URL` de ejemplo con `127.0.0.1:5173` (D154, D221).
- `knowledge-base/02_descripcion_general.md`, «Stack tecnológico»: fila Frontend con las versiones fijadas y fila de tests del frontend (Vitest, Testing Library); «Arquitectura general»: el `/api` del mismo origen.
- `knowledge-base/04_modelo_de_datos.md` no cambia. `03` no cambia (las rutas de la interfaz no son rutas de la API).
- `openspec/config.yaml`: (a) contexto con el frontend (`frontend/package.json`, Node 24, `npm test` como segunda suite por defecto, sin Docker); (b) la regla de `design` sobre los pins (archivo por subproyecto); (c) **entrecomillar `rules.tasks[5]`** para que `openspec` deje de ignorar las reglas de `tasks`; (d) la frase cortada de «Sesión (desde C-06)».
- `CLAUDE.md` y `AGENTS.md` (copias sincronizadas): fila Frontend del stack con las versiones y la regla dura 7 con el archivo por subproyecto.
- `CHANGES.md`: marcar C-08 con `[x]` y repetir `scripts/verificar_changes.py`.

## Open Questions

Ninguna. **Las doce preguntas abiertas de este design las cerró el autor el 2026-10-19 aceptando la recomendación del agente**: un archivo de dependencias por subproyecto, `frontend/package.json` con su `package-lock.json` (Q1 → D217, F2); capability nueva `ingreso-al-panel` (Q2 → D218, F1); access en memoria y refresh en `sessionStorage` (Q3 → D219, F7); mismo origen por `/api`, sin CORS ni cambios de API (Q4 → D220, F5); servicio `frontend` de dos etapas con `nginxinc/nginx-unprivileged` en `127.0.0.1:5173` (Q5 → D221, F14); Vitest + jsdom + Testing Library con un servidor falso inyectado, sin `vi.mock` (Q6 → D222, F13); Node 24 LTS (Q7 → D223, F3); TypeScript 6.0.3 y React Router 7.18.4 (Q8 → D224, F3); panel base sin datos del usuario (Q9 → D225, F11); cierre de sesión solo en el cliente (Q10 → D226, F11); test guard contra `any`, sin ESLint (Q11 → D227, F13); y 22 tareas como séptima excepción (Q12 → D228, F18).

Quedan marcadas «Propuesta», y el autor puede cambiarlas sin tocar el plan: los nombres de las rutas (`/ingresar`, `/panel`, F6), los textos de los mensajes (F9), la clave `turnos.sesion.v1` (F7), los nombres de los archivos y de las clases de error (F4, F12) y las cabeceras de `nginx.conf` (F14).
