# Proposal: historial-de-turnos

Change **C-03** de `CHANGES.md`, historia **US-015** («Historial de cambios»). Gobernanza **CRÍTICO** (registro de auditoría): solo análisis y planificación; no se escribe código hasta que el autor apruebe `proposal.md`, `design.md`, los specs y `tasks.md`.

## Why

Hoy un turno se crea y no queda ningún rastro de quién lo creó, cuándo ni con qué datos: si después alguien lo cambia, no hay forma de reconstruir qué pasó. RN-AG-11 exige que **todo cambio de turno quede registrado en un historial inmutable** (solo inserción), y el dueño del consultorio necesita consultarlo para tener trazabilidad (US-015).

Va ahora, en el orden 2, porque cada change siguiente que toca un turno (reprogramar, cancelar, confirmar, marcar, seña: US-012, US-013, US-014, US-031, US-051) escribe en este historial y depende de US-015 (D11, D14, D18 y D99). Si la tabla no existe antes, cada uno tendría que inventarla. Además cierra el escenario **E9** de US-010, que quedó fuera de C-01 (decisión del autor 2026-10-03).

## What Changes

- **Tabla `evento_turno`, solo inserción** (`04_modelo_de_datos.md` §EventoTurno), con su migración Alembic `0003`, reversible. La aplicación no ofrece ninguna forma de modificar ni borrar un evento, y en PostgreSQL la propia base rechaza `UPDATE`, `DELETE` y `TRUNCATE` sobre la tabla (la KB pide que «ni la aplicación ni la base» los expongan).
- **`crear_turno` registra el evento `creado`** en la **misma transacción** que el turno (E9 de US-010): si una de las dos escrituras falla, no queda ninguna. Un rechazo (`409` o `422`) no registra ningún evento.
- **`GET /turnos/{id}/historial`** devuelve los eventos del turno en orden cronológico, en solo lectura, **sin autenticación** hasta C-07 (límite conocido, DD-14; la matriz de `03` reserva la lectura a odontólogo, recepcionista y dueño, y el paciente nunca la ve, D68).
- **`404` con `RN-GL-04`** para un id de turno inexistente en la URL (RN-GL-04: un recurso identificado en la URL devuelve `404`, uno referido en el cuerpo devuelve `422`).
- **Solo lectura por HTTP**: la ruta del historial no acepta `PUT`, `PATCH` ni `DELETE` (US-015 CA-1).
- **Sin dependencias nuevas**: alcanza con SQLAlchemy y Alembic, ya fijados en `backend/pyproject.toml`.
- **README**: el endpoint nuevo, la tabla escenario → test y los límites (sin autenticación, quién figura como actor mientras no hay usuarios, turnos anteriores a la migración sin evento).

No hay cambios **BREAKING**: `POST /turnos` responde igual (mismos estados y mismo cuerpo); solo agrega una fila más en la base.

### Escenarios

Cubre los tres mínimos de la entrada C-03 de `CHANGES.md` (dentro del «3 a 6»):

| ID | Qué verifica | Dónde corre |
|---|---|---|
| E9 (US-010) | Crear un turno registra el evento `creado`, en la misma transacción; un rechazo no registra nada | Suite por defecto |
| CA-1 (US-015) | El historial es de solo lectura: la API no lo modifica y, en PostgreSQL, la base rechaza modificarlo o borrarlo | Suite por defecto (API) y perfil `postgres` (base) |
| HIS-1 | Un id de turno inexistente en la URL responde `404` con `RN-GL-04` | Suite por defecto |

Quedan fuera de US-010: E8 (ya cubierto por el test unitario de `Intervalo`), E10 (horario y bloqueos) y E11 (ya probado en C-02). No se tocan E1 a E7 ni E12.

## Fuera de alcance

- **Pantalla del historial** (C-15; la interfaz empieza en la fase 3).
- **Los demás tipos de evento**: `reprogramado`, `confirmado`, `cancelado`, `estado_cambiado`, `sena_acreditada`, `sena_retenida`, `sena_devuelta` y `nota`. Los agrega cada change que produce ese hecho, con su propio test. Este change solo produce `creado`.
- **`EventoPaciente`** (C-21) y la regla de reparto en la práctica: no hay ningún hecho de paciente sin turno todavía.
- **Autenticación y actor real**: sin usuarios no hay a quién atribuir el cambio; el `actor_id` queda vacío hasta C-07 (ver `design.md`).
- **La aceptación explícita de RN-TD-10** dentro del evento `creado`: es de la reserva pública (C-24).
- **Completar el historial de turnos creados antes de la migración** (no se inventan eventos; ver `design.md`).
- **Filtros, paginación** y cualquier otra lectura de turnos (`GET /turnos/{id}`, agenda del día).
- **Roles de base con privilegios mínimos** (un rol sin permiso de `UPDATE`): no hay configuración de producción.
- **Sobreturnos y excepción de horario**: fuera de la v1.

## Capabilities

### New Capabilities

- `historial-de-turnos`: el registro inmutable de lo que le pasa a cada turno y su lectura. Qué evento deja cada hecho, en qué transacción se registra, qué garantías de inmutabilidad hay y cómo se consulta. Aloja E9, US-015 CA-1 e HIS-1, y es donde los changes siguientes agregan sus tipos de evento.

### Modified Capabilities

- `persistencia-postgresql`: el requisito «Esquema de PostgreSQL creado por migraciones» (INF-1) dice hoy que una base migrada queda **solo** con las seis tablas del primer change. Con la migración `0003` eso deja de ser cierto. Se generaliza para que diga que la base migrada coincide con el modelo de datos de la aplicación, sin atarla a una lista de tablas de un change. Es una consecuencia obligada de agregar la primera tabla nueva, no una regla nueva, y evita que cada change siguiente con migraciones tenga que volver a tocarlo.

`creacion-de-turnos` **no recibe delta**: E9 se aloja en `historial-de-turnos`, igual que E11 se alojó en `persistencia-postgresql` (D142). **Conflicto con la regla «una sola capability»** de `openspec/config.yaml`: el delta de `persistencia-postgresql` es la segunda capability tocada. El autor lo aceptó como excepción de este change (D158; `design.md`, H1).

## Impact

- **Código nuevo**: el tipo de dominio del evento y su construcción para `creado` (`backend/app/domain/turnos/`), el caso de uso de lectura del historial, el repositorio del historial, el modelo `EventoTurnoModelo`, la migración `0003`, el router del historial y sus tests (unitarios, de integración, de API y del perfil `postgres`).
- **Código que se modifica**: `application/crear_turno.py` (registra el evento), `application/puertos.py` (puerto del historial y unidad de trabajo), `infrastructure/unidad_de_trabajo.py`, `infrastructure/db/modelos.py`, `domain/errors.py` (error del turno inexistente en la URL), `api/errores.py` y `api/esquemas.py` (`404` y esquema de salida), `main.py` (incluye el router) y `tests/postgres/test_migraciones.py` (INF-1 con la tabla nueva).
- **API**: un endpoint nuevo, `GET /turnos/{id}/historial`. `POST /turnos` no cambia su contrato.
- **Base**: una tabla nueva y, solo en PostgreSQL, una función y sus disparadores que impiden modificarla.
- **Dependencias**: ninguna nueva.
- **Documentación**: `README.md`. Al archivar, `CHANGES.md` marca C-03 y la KB registra las decisiones que el autor confirme (commit `docs(kb)` aparte, como en C-02).
