# Proposal: gestion-de-sillones

Change **C-05** de `CHANGES.md`, historia **US-004** («Sillón como recurso»). Gobernanza **BAJO** (catálogo): autonomía completa en el Apply si los tests pasan. Las tres preguntas del propose quedaron cerradas por el autor el 2026-10-14 (D183 a D185; ver `design.md`).

## Why

Hoy el único sillón existe porque lo carga el seed («Sillón 1») o las factories de los tests: el consultorio no puede sumar un segundo sillón, renombrarlo ni dejar de usar uno que se rompió. La regla del sillón por defecto (RN-AG-14: el único activo, no un id fijo) y el rechazo del sillón inactivo (RN-AG-07) ya están construidos en `POST /turnos` desde C-01, pero ninguna petición puede llegar a ellos: no hay forma de tener dos sillones activos ni uno inactivo sin tocar la base a mano.

Va ahora, en el orden 2, porque C-07 (roles y protección del panel) depende de las tres rutas de catálogo (C-03, C-04, C-05), y porque la tabla `sillon` ya existe desde C-01: el change es solo API, sin migración.

## What Changes

- **`GET /sillones`**: lista los sillones del consultorio, activos e inactivos, por `id`, con `id`, `nombre` y `activo`.
- **`POST /sillones`**: da de alta un sillón (`201`) con su `nombre`; nace activo. El nombre se guarda sin espacios de más y no puede quedar vacío.
- **`PATCH /sillones/{id}`**: cambia el `nombre` y/o `activo` (desactivar con `activo: false`, reactivar con `true`; D185). **No hay borrado** (`02`). Un id inexistente en la URL responde `404` con `RN-GL-04` (D166).
- **Un sillón desactivado no admite turnos nuevos**: `POST /turnos` ya lo rechaza con `422`, `RN-GL-04` y motivo `inactivo` (RN-AG-07); los turnos que ya lo usan no cambian.
- **El sillón por defecto sigue la cuenta de activos** (RN-AG-14, D138): con un único sillón activo, un turno sin `sillon_id` va a ese; con dos o más activos, omitirlo se rechaza con `422`, `RN-GL-04` y motivo `varios_activos`; sin ninguno activo, con motivo `ninguno_activo`. Ya es el comportamiento de `POST /turnos`; este change lo vuelve alcanzable por la API y lo prueba de punta a punta.
- **Sin autenticación** hasta C-07 (DD-14; la matriz de `03` reserva el CRUD de sillones al odontólogo).
- **Sin cambios de esquema ni dependencias nuevas**: la tabla `sillon` (`id`, `consultorio_id`, `nombre`, `activo`) ya tiene todo lo que pide US-004, y alcanza con lo que fija `backend/pyproject.toml`.
- **Seed de la demo sin cambios**: sigue «Sillón 1» como único sillón, para que el recorrido del README que omite el sillón siga funcionando.
- **README**: los endpoints nuevos con peticiones de ejemplo sobre la demo, la tabla escenario → test y el límite de la demo (un segundo sillón activo hace que el recorrido que omite `sillon_id` responda `422` con `varios_activos` hasta desactivarlo).

No hay cambios **BREAKING**: `POST /turnos`, `GET /turnos/{id}/historial` y las rutas de `/prestaciones` responden igual.

### Escenarios

Cubre los tres mínimos de la entrada C-05 de `CHANGES.md` (dentro del «3 a 6»):

| ID | Qué verifica | Dónde corre |
|---|---|---|
| US-004 CA-1 | El turno sin sillón explícito va al único sillón activo; con más de uno activo hay que indicarlo (`422`, `RN-GL-04`, `varios_activos`); sin ninguno activo, `ninguno_activo` | Suite por defecto |
| US-004 CA-2 | El modelo admite más sillones: con un segundo sillón, dos profesionales atienden a la misma hora en sillones distintos, y el solapamiento se controla por sillón | Suite por defecto |
| US-004 CA-3 | Alta, listado, renombre, desactivación y reactivación; un sillón inactivo no admite turnos nuevos (RN-AG-07) y los existentes no cambian; `404` para un id inexistente en la URL | Suite por defecto (más un test del perfil `postgres`: el alta tras el seed no choca con el id fijo) |

No se toca ningún escenario de US-010 (E1 a E12), US-015 (historial) ni US-001 (prestaciones): sus tests siguen sin cambios.

## Fuera de alcance

- **Interfaz** de sillones (US-004 no tiene pantalla; la agenda multi-sillón es Fase 2).
- **Cambios de esquema**: ninguna migración (la tabla `Sillon` ya existe). En particular, **ningún `UNIQUE` sobre el nombre** (D183).
- **Nombre único del sillón** (D183): la KB no lo pide.
- **Borrado** de sillones, ni físico ni lógico distinto de `activo`.
- **Bloqueos por sillón** (US-003, C-13) y **horario** (US-002, C-12).
- **Avisar o mover los turnos futuros** de un sillón que se desactiva: quedan como están (tema de la agenda, C-14).
- **Autenticación y roles** (C-06, C-07); el consultorio de la petición es el único de la instalación (D173).
- **Lectura de un solo sillón** (`GET /sillones/{id}`), filtros y paginación.
- **Gestión de profesionales** (RN-AG-14 también cubre el profesional por defecto; su alta llega con los usuarios, C-09).
- **Sobreturnos y excepción de horario**: fuera de la v1.

## Capabilities

### New Capabilities

- `gestion-de-sillones`: el catálogo de sillones del consultorio: alta, listado, renombre, desactivación y reactivación, y cómo el estado de los sillones decide qué sillón usa un turno (RN-AG-06, RN-AG-07, RN-AG-14). Aloja US-004 CA-1, CA-2 y CA-3; la Fase 2 (agenda multi-sillón) y C-13 (bloqueos de sillón) le agregan sus requisitos.

### Modified Capabilities

Ninguna. Se revisaron las cuatro existentes:

- `creacion-de-turnos`: su requisito «Crear un turno reservado con fin calculado» ya dice que, si la petición no indica el sillón, se usa **el único activo** del consultorio (RN-AG-14), y «Rechazar las referencias inválidas» ya rechaza el sillón inactivo (RN-AG-07) y el sillón omitido «sin que haya uno solo activo». El código de C-01 (`application/crear_turno.py`) ya cuenta los activos y devuelve `ninguno_activo` o `varios_activos`, y `tests/api/test_post_turnos.py` ya prueba los dos casos con un sillón cargado por factory. Nada de eso cambia: este change solo lo vuelve alcanzable por la API, como C-04 hizo con la prestación inactiva (E12) sin delta.
- `persistencia-postgresql`: sin migración nueva; INF-1 sigue igual. La lista de tablas no cambia.
- `historial-de-turnos`: no cambia; editar un sillón no registra eventos de turno.
- `gestion-de-prestaciones`: no cambia; solo se reusan piezas de su código (ver `design.md`).

## Impact

- **Código nuevo**: el dato completo del sillón en `backend/app/domain/agenda/sillones.py`, el error `SillonNoEncontrado` en `domain/errors.py`, los casos de uso en `backend/app/application/sillones.py`, el repositorio `infrastructure/repositories/sillones.py`, el router `api/routers/sillones.py` y sus tests (unitarios, de integración, de API y uno del perfil `postgres`).
- **Código que se modifica**: `application/puertos.py` y `infrastructure/unidad_de_trabajo.py` (puerto y repositorio nuevos), `api/errores.py` (el `404` del sillón; los tres «no encontrado en la URL» pasan a compartir una base, regla de tres), `api/esquemas.py` (esquemas de sillón; el nombre normalizado y el rechazo del `null` se comparten con prestaciones), `main.py` (incluye el router) y `README.md`.
- **API**: tres operaciones nuevas en `/sillones`. Los contratos existentes no cambian.
- **Base**: ninguna tabla ni columna nueva; ninguna migración.
- **Dependencias**: ninguna nueva.
- **Documentación**: `README.md`. Al archivar, `CHANGES.md` marca C-05 y la KB registra las decisiones que el autor confirme (commit `docs(kb)` aparte, como en C-02 a C-04).
