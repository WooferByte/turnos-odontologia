# Proposal: gestion-de-prestaciones

Change **C-04** de `CHANGES.md`, historia **US-001** («Tabla de prestaciones»). Gobernanza **BAJO** (catálogo): autonomía completa si los tests pasan. Las cuatro preguntas del propose quedaron cerradas por el autor el 2026-10-14 (D171 a D174; ver `design.md`).

## Why

Hoy las prestaciones solo existen porque las carga el seed de la demo o las factories de los tests: el consultorio no puede dar de alta una prestación nueva, corregir la duración de una existente ni dejar de ofrecer una que ya no hace. Tampoco tienen color, que la agenda del día (US-011) necesita para distinguirlas, ni la marca `reservable_online` que la reserva pública (RN-TD-06) va a leer. Y la regla RN-AG-01 (duración mayor que 0 y múltiplo de la granularidad) no se valida en ningún lado: el primer change la dejó explícitamente para este (D131).

Va ahora, en el orden 2, porque la pantalla de prestaciones (C-11), la disponibilidad (C-24) y los presupuestos (C-44) dependen de esta API, y porque C-02 ya dejó Alembic listo para agregar las dos columnas que faltan con una migración.

## What Changes

- **`GET /prestaciones`**: lista las prestaciones del consultorio, activas e inactivas, con `nombre`, `duracion_minutos`, `color`, `reservable_online` y `activa`.
- **`POST /prestaciones`**: da de alta una prestación (`201`). El nombre es único en el consultorio; la duración debe ser mayor que 0 y múltiplo de **5 minutos**, la constante de granularidad hasta que exista `ConfiguracionReglas` (RN-AG-01, D99); el color es un hex `#RRGGBB`; `reservable_online` es opcional y vale `false` por defecto.
- **`PATCH /prestaciones/{id}`**: edita uno o varios campos, incluida la desactivación (`activa: false`) y la reactivación. **No hay borrado** (`02_descripcion_general.md`, D104). Un id inexistente en la URL responde `404` con `RN-GL-04` (D166).
- **Cambiar la duración no toca los turnos existentes** (RN-AG-02, RN-GL-03): el turno ya guarda su propia duración y su fin; lo que este change agrega es la prueba de que sigue siendo así cuando la prestación se edita.
- **Una prestación desactivada no admite turnos nuevos**: `POST /turnos` ya la rechaza con `422` y `RN-GL-04` (motivo `inactivo`, E12); los turnos que ya la usan no cambian.
- **Migración `0005`**: agrega `Prestacion.color` y `Prestacion.reservable_online`, no nulas, completando las filas que ya existen (las cinco prestaciones de la demo en el volumen de C-02).
- **Seed de la demo**: las cinco prestaciones de D56 con un color cada una.
- **Sin autenticación** hasta C-07 (límite conocido, DD-14; la matriz de `03` reserva el alta y la edición al odontólogo).
- **Sin dependencias nuevas**: alcanza con lo que ya fija `backend/pyproject.toml`.
- **README**: los endpoints nuevos con peticiones de ejemplo, la tabla escenario → test y los límites.

No hay cambios **BREAKING**: `POST /turnos` y `GET /turnos/{id}/historial` responden igual.

### Escenarios

Cubre los tres mínimos de la entrada C-04 de `CHANGES.md` (dentro del «3 a 6»):

| ID | Qué verifica | Dónde corre |
|---|---|---|
| US-001 CA-1 | Alta, listado, edición y desactivación; nombre único en el consultorio; `404` para un id inexistente en la URL | Suite por defecto |
| US-001 CA-2 | Una duración que no es mayor que 0 o no es múltiplo de 5 se rechaza con `RN-AG-01`, en el alta y en la edición | Suite por defecto |
| US-001 CA-3 | Cambiar la duración de la prestación no modifica los turnos ya creados; los nuevos usan la duración nueva | Suite por defecto |

La migración `0005` se prueba en el perfil `postgres` dentro del requisito INF-1 que ya existe (la base migrada coincide con el modelo; ver «Capabilities»). No se toca ningún escenario de US-010 ni de US-015.

## Fuera de alcance

- **Pantalla de prestaciones** (C-11; la interfaz empieza en la fase 3).
- **Granularidad configurable** (C-22, `ConfiguracionReglas`): acá es la constante de 5 minutos.
- **Efecto de `reservable_online`** (C-24, disponibilidad y reserva pública): se guarda y se lee, pero nadie la usa todavía.
- **Rutas públicas de prestaciones** (`GET /public/{slug}/prestaciones`, C-24 / C-28).
- **Borrado** de prestaciones, ni físico ni lógico distinto de `activa`.
- **Autenticación y roles** (C-06, C-07).
- **Historial o auditoría de los cambios de una prestación**: el historial inmutable es de turnos (RN-AG-11).
- **Lectura de una sola prestación** (`GET /prestaciones/{id}`), filtros y paginación.
- **Modificar la duración de un turno** desde el panel (US-012, C-16).
- **Sobreturnos y excepción de horario**: fuera de la v1.

## Capabilities

### New Capabilities

- `gestion-de-prestaciones`: el catálogo de prestaciones del consultorio y sus reglas: alta, listado, edición y desactivación, nombre único, duración válida según la granularidad (RN-AG-01), color, y la garantía de que editar una prestación no cambia los turnos ya creados (RN-AG-02, RN-GL-03). Aloja US-001 CA-1, CA-2 y CA-3; C-11 (pantalla), C-22 (granularidad configurable) y C-24 (`reservable_online`) le agregan sus requisitos.

### Modified Capabilities

Ninguna. Se revisaron las tres capabilities existentes:

- `persistencia-postgresql`: INF-1 ya fue generalizado en C-03 (D158) a «la base migrada coincide con el modelo de datos de la aplicación» y compara columnas, tipos y nulabilidad; la lista de tablas de su escenario feliz no cambia (`0005` no agrega tablas) y el escenario «deshacer solo las migraciones del historial» sigue dejando las seis tablas del primer change. La migración `0005` queda cubierta por el requisito tal como está; no hace falta delta.
- `creacion-de-turnos`: E12 ya rechaza una prestación inactiva con `RN-GL-04`; este change la vuelve alcanzable por la API, pero no cambia el requisito.
- `historial-de-turnos`: no cambia; editar una prestación no registra eventos de turno.

## Impact

- **Código nuevo**: reglas puras de la prestación (granularidad, duración válida, nombre normalizado) en `backend/app/domain/`, el caso de uso de prestaciones en `backend/app/application/`, el repositorio de prestaciones, la migración `0005`, el router `prestaciones` y sus tests (unitarios, de integración, de API y del perfil `postgres`).
- **Código que se modifica**: `infrastructure/db/modelos.py` (dos columnas), `application/puertos.py` y `infrastructure/unidad_de_trabajo.py` (puerto y repositorio nuevos), `domain/errors.py` (errores de duración, de nombre repetido y de prestación inexistente en la URL), `api/errores.py` y `api/esquemas.py`, `main.py` (incluye el router), `infrastructure/db/seed_demo.py` (colores) y `tests/factories.py` (color por defecto).
- **API**: tres operaciones nuevas en `/prestaciones`. Los contratos existentes no cambian.
- **Base**: dos columnas nuevas en `prestacion`; ninguna tabla nueva.
- **Dependencias**: ninguna nueva.
- **Documentación**: `README.md`. Al archivar, `CHANGES.md` marca C-04 y la KB registra las decisiones que el autor confirme (commit `docs(kb)` aparte, como en C-02 y C-03).
