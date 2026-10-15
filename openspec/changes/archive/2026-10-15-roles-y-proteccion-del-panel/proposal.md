# Proposal: roles-y-proteccion-del-panel

Change **C-07** de `CHANGES.md`, historias **US-091** («Roles odontólogo, recepcionista y dueño») y **US-092** («Proteger los endpoints del panel con JWT»). Gobernanza **CRÍTICO** (autenticación y autorización): solo planificación; nada se implementa hasta que el autor apruebe el plan completo. Las trece preguntas del propose quedaron cerradas por el autor el 2026-10-15 con la recomendación del agente (D204 a D216; ver `design.md`).

## Why

Desde C-06 existe la sesión del panel, pero ninguna ruta la exige: `POST /turnos`, `GET /turnos/{id}/historial`, `/prestaciones` y `/sillones` responden a cualquiera que llegue a la API (DD-14, límite conocido desde C-01). Además, el historial registra cada creación con `actor_id` vacío (D159) y el turno no guarda quién lo creó, así que la trazabilidad que pide RN-AG-11 está incompleta.

Va ahora porque está en el camino crítico (`C-03 → C-07 → C-08`): la interfaz de C-08 necesita que un `401` signifique «volver al inicio de sesión», y los changes del panel que siguen (C-09, C-12, C-13, C-14…) distinguen roles. Sus dependencias (C-03, C-04, C-05 y C-06) están archivadas.

## What Changes

- **Roles del usuario** (tabla `usuario_rol`, PK compuesta `usuario_id` + `rol`; roles válidos `odontologo`, `recepcionista` y `dueno`, RN-AU-05). Los permisos son la **unión** de los roles (RN-AU-02) y los roles **se leen de la base en cada petición**: quitar o asignar un rol tiene efecto inmediato, sin tocar `token_version` (D102).
- **Autenticación en cada petición del panel**: una dependencia de FastAPI lee `Authorization: Bearer <access>`, valida firma, tipo `access` y vigencia con el reloj inyectado, y lee de la base que el usuario exista, siga `activo` y tenga la misma `token_version` (RN-AU-01, RN-AU-03, RN-AU-04; reusa lo que C-06 dejó listo: `FirmadorDeTokens.leer`, `exigir_token_valido`, `RepositorioUsuarios.obtener`). Sin token válido → `401`.
- **Autorización por la matriz de `03`**: rol insuficiente → `403` con el código `RN-AU-05`. Se protegen **todas** las rutas existentes del panel:
  - `POST /turnos`: `odontologo` o `recepcionista` (US-092 CA-2).
  - `GET /turnos/{id}/historial`: los tres roles.
  - `GET /prestaciones` y `GET /sillones`: los tres roles; `POST` y `PATCH` de prestaciones y sillones: solo `odontologo` (D205).
- **Rutas públicas sin cambios** (US-092 CA-3): `POST /auth/login` y `POST /auth/refresh` siguen sin token. Toda ruta nueva queda protegida por defecto: un test guard falla si una ruta fuera de la lista pública no exige token.
- **El usuario como actor**: `Turno.creado_por` (FK nula a `usuario`) y el evento `creado` del historial con `actor_id` = id del usuario autenticado (cierra D159). Los turnos y eventos anteriores quedan como estaban.
- **`Profesional.usuario_id`** (FK nula, `UNIQUE` si no es nula) y **`Profesional.matricula`** (texto nulo), como manda `CHANGES.md`; el profesional del seed queda vinculado al usuario del seed (US-091 CA-4, D46, D202).
- **Migración `0007`** (reversible): `usuario_rol` y las tres columnas nuevas, todas nulas o con tabla nueva, sin tocar datos existentes.
- **Seed**: el usuario `odontologa@consultorio-demo.test` recibe `odontologo` + `dueno` y el vínculo con el profesional, también en un volumen de PostgreSQL sembrado antes de este change; más un usuario ficticio con rol `recepcionista` para poder mostrar el `403` (D212).
- **`/docs`**: esquema de seguridad Bearer (botón «Authorize» donde se pega el access token) y `401`/`403` declarados en cada ruta protegida.
- **README**: cómo obtener el token y usarlo en `/docs`, matriz de permisos de las rutas existentes, migración `0007`, tabla escenario → test y límites conocidos.

**BREAKING**: todas las rutas del panel pasan a exigir `Authorization: Bearer <access token>`; una petición sin token que antes daba `201`/`200` ahora da `401`. Es el cambio que DD-14 anunció desde C-01. Los tests de API de C-01 a C-05, la demo del README y el recorrido de `/docs` cambian en consecuencia (D211).

No hay dependencias nuevas: `fastapi.security.HTTPBearer` viene con FastAPI 0.115.14 y lo demás ya está fijado (`PyJWT` 2.15.1, `bcrypt` 5.0.0). No hay variables de entorno nuevas.

### Escenarios

Cubre los seis mínimos de la entrada C-07 de `CHANGES.md` (dentro del «3 a 6»), más dos deltas obligados por el esquema y el historial:

| ID | Qué verifica | Dónde corre |
|---|---|---|
| US-091 CA-1 | Un usuario con varios roles tiene la unión de sus permisos (`odontologo` + `dueno`; `recepcionista` + `dueno`) | Suite por defecto |
| US-091 CA-3 | Un rol insuficiente recibe `403` con `RN-AU-05` y no se modifica nada | Suite por defecto |
| US-091 CA-5 | Los roles se leen de la base en cada petición: quitar o asignar un rol vale con el mismo token | Suite por defecto |
| US-092 CA-1 + CA-3 | Sin token, con token vencido, mal firmado o de tipo refresh → `401`; las rutas públicas siguen sin token | Suite por defecto |
| US-092 CA-2 | Las rutas de C-01 a C-05 exigen JWT con el rol de la matriz | Suite por defecto |
| US-092 CA-4 | Token de un usuario inactivo o con `token_version` vieja → `401` aunque no haya vencido | Suite por defecto |
| E9 (delta) | El evento `creado` lleva el id del usuario autenticado; el turno guarda `creado_por` | Suite por defecto |
| INF-1 (delta) | La base migrada incluye `usuario_rol` y las columnas nuevas; deshacer solo `0007` deja el esquema de C-06 | Perfil `postgres` |

Quedan fuera US-091 CA-2 (la recepcionista no ve la ficha clínica: se completa en C-43, D115) y US-091 CA-4 como comportamiento de gestión (asignar `odontologo` a otro usuario no crea un `Profesional`: no hay alta de usuarios hasta C-09); acá solo se vincula el profesional del seed. No se toca ningún escenario de US-010 salvo el delta de E9.

## Fuera de alcance

- **Gestión de usuarios** (alta, roles, desactivación, restablecer contraseña; C-09) y **cambio de la propia contraseña** (C-10). Este change no incrementa `token_version` ni escribe roles fuera del seed.
- **Acceso a la ficha clínica** (US-091 CA-2, RN-FC-02; C-43).
- **Interfaz**: pantalla de inicio de sesión, guardado de tokens y menú por rol (C-08 en adelante). Tampoco un `GET /auth/yo` para que el panel conozca sus roles: lo decide C-08 si lo necesita.
- **Permisos sobre «lo propio»** (paciente por token, «U propio» de la contraseña): no hay rutas de ese tipo todavía.
- **Multi-consultorio**: un solo consultorio por instalación (D173); no se compara el consultorio del usuario con el del recurso.
- **Límite de peticiones** y **registro de eventos de seguridad** (D195; siguen fuera).
- Endpoints de profesionales (ni alta ni edición de `matricula`), un segundo profesional (Fase 2, D46).
- OAuth2, scopes, cookies, CSRF, MFA (fuera de la v1).
- Completar el `actor_id` de los eventos anteriores a C-07 (D159: sería modificar el historial).
- Sobreturnos y excepción de horario: fuera de la v1.

## Capabilities

### New Capabilities

- `proteccion-del-panel`: quién puede usar cada ruta del panel. Los roles del usuario y su unión, la validación del access token en cada petición (firma, tipo, vigencia, `activo`, `token_version`), el `401` y el `403`, la matriz de permisos aplicada a las rutas, la lista cerrada de rutas públicas y el registro del usuario que crea un turno (RN-AU-01, RN-AU-02, RN-AU-03, RN-AU-04, RN-AU-05; US-091, US-092). Es el nombre que dejó previsto C-06 (J1, J20); `sesion-del-panel` sigue siendo cómo se obtiene y renueva la sesión (D204).

### Modified Capabilities

- `historial-de-turnos`: el requisito «Crear un turno registra el evento `creado`» cambia el actor de E9: de `actor_id` vacío («la creación no está autenticada todavía») a `actor_id` con el id del usuario autenticado (D159 anunciaba este cambio para C-07).
- `persistencia-postgresql`: solo la lista de ejemplo del escenario INF-1 (agrega `usuario_rol`) y un escenario de borde para deshacer la migración `0007`; el texto del requisito no cambia (D158).

Se revisaron las demás: `creacion-de-turnos`, `gestion-de-prestaciones` y `gestion-de-sillones` **no cambian sus requisitos**: siguen describiendo qué hace cada ruta para quien tiene permiso; quién puede llamarla lo define `proteccion-del-panel` (D204). Sus textos de «Propósito» dicen «sin autenticación hasta el change de roles (DD-14)» y quedan desactualizados: un delta no puede editarlos, así que se corrigen a mano al archivar (ver `design.md`, «Contradicciones», punto 6). `sesion-del-panel` tampoco cambia: el login y el refresh siguen igual.

## Impact

- **Código nuevo**: `domain/acceso/roles.py` (`Rol`, `Permiso`, la matriz y la regla pura de autorización); error `PermisoInsuficiente` (`RN-AU-05`) en `domain/errors.py`; caso de uso `application/acceso.py` (identificar al usuario de la petición y autorizarlo); dependencias `usuario_actual` y `requiere_permiso` en `api/deps.py` (o `api/seguridad.py`); migración `0007`; y sus tests (unitarios, de integración, de API y del perfil `postgres`).
- **Código que se modifica**: `domain/turnos/eventos.py` y `application/crear_turno.py` (actor obligatorio, D210), `domain/turnos/turno.py` y el repositorio de agenda (`creado_por`), `application/puertos.py` y `infrastructure/repositories/usuarios.py` (roles), `infrastructure/db/modelos.py`, los cuatro routers (`turnos`, `prestaciones`, `sillones`; `auth` no), `api/errores.py` (`403`), `main.py` (esquema de seguridad), `seed_demo.py` y `cargar_seed.py`, `README.md`.
- **Tests existentes que se tocan** (inevitable: las rutas pasan a exigir token): los *fixtures* `cliente` de `tests/api/test_post_turnos.py`, `test_historial.py`, `test_prestaciones.py`, `test_sillones.py` y `test_sillones_y_turnos.py`; `tests/api/test_demo.py`; las llamadas a `crear_turno` de `tests/integration/` porque el actor pasa a ser obligatorio (D210); `tests/unit/test_eventos.py`; las aserciones de `actor_id` vacío de `tests/api/test_historial.py` e `tests/integration/test_historial.py`; y en el perfil, `tests/postgres/test_migraciones.py` y `test_seed_y_api.py`. D211 fija la forma.
- **API**: todas las rutas del panel exigen Bearer (**BREAKING**, anunciado por DD-14); nuevas respuestas `401` y `403` en el contrato; ninguna ruta nueva.
- **Base**: tabla `usuario_rol` y columnas `profesional.usuario_id`, `profesional.matricula` y `turno.creado_por` (migración `0007`).
- **Dependencias y entorno**: ninguna dependencia nueva; ninguna variable nueva; `.env.example` no cambia.
- **Documentación**: `README.md`. Al archivar, `CHANGES.md` marca C-07, la KB registra las decisiones «Propuesta» que el autor apruebe con el plan (commit `docs(kb)` aparte) y se hacen las correcciones diferidas que piden D204 a D216: `02` (D205), RN-GL-02 en `05` (D208), `03` y RN-AU-01 (D214), `04` (D212, D213, D215, D209), los «Propósito» de `gestion-de-prestaciones` y `gestion-de-sillones` y el contexto de `openspec/config.yaml` (D204). La lista completa está en `design.md`, «Notas para el archive»; ninguna se edita antes.
