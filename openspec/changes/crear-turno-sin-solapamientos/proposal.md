# Proposal: crear-turno-sin-solapamientos

Change C-01 de `CHANGES.md` (fase 1, orden 1, gobernanza MEDIO). Historia: **US-010**. Es el change de la consigna y el hito de entrega.

## Why

Hoy el consultorio agenda en papel, Excel o WhatsApp y los turnos se pisan: nada impide dar dos turnos al mismo profesional o al mismo sillón en el mismo horario. Este change entrega el núcleo de la agenda: crear un turno `reservado` y rechazar el que se superponga con un turno **activo** del profesional (RN-AG-05) o del sillón (RN-AG-08), informando el código de la regla que falló (RN-GL-02). Va primero porque todos los demás changes de la agenda se apoyan en él (C-02, C-03 y de C-16 en adelante).

## Por qué se eligió este change

- **Pertenece al MVP recomendado en el Discovery**: la sección D.3 de `docs/discovery/informe-discovery.md` («MVP sugerido») lista como *Imprescindible (v1)*, punto 4, la «Prevención de solapamientos por profesional y por sillón».
- **Tiene reglas de negocio verificables**: RN-AG-05, RN-AG-08, RN-AG-09, RN-AG-10 y RN-GL-04 tienen código, definición exacta (`[inicio, fin)`; se solapan si `A.inicio < B.fin` y `B.inicio < A.fin`) y ejemplos numéricos de borde en la base de conocimiento.
- **Es una sola funcionalidad**: una historia (US-010), una capability y un endpoint (`POST /turnos`), sin interfaz gráfica.

## What Changes

- Se agrega el endpoint **`POST /turnos`** (API, sin interfaz gráfica), que crea un turno en estado `reservado` con `fin = inicio + duración de la prestación` (RN-AG-02).
- Se rechaza con `409` el turno que se solapa con un turno activo del profesional (`RN-AG-05`) o del sillón (`RN-AG-08`); si chocan los dos, el error lleva **los dos códigos**, con un conflicto por recurso (D129).
- Los intervalos son semiabiertos `[inicio, fin)` (RN-AG-09): un turno que empieza justo cuando termina otro es válido; un solapamiento de un minuto se rechaza.
- Solo ocupan horario los turnos en estado activo (`pendiente_aprobacion`, `pendiente_sena`, `reservado`, `confirmado`; RN-AG-10).
- Una referencia a prestación, profesional o sillón inexistente, inactivo o de otro consultorio, o a un paciente inexistente o de otro consultorio, se rechaza con `422` y `RN-GL-04`, listando **todas** las referencias inválidas (D127), sin crear nada. Un paciente solo puede ser `inexistente`: el «paciente inactivo» no existe en la v1 (D136). Si no se indica el sillón o el profesional se usa el único activo del consultorio (RN-AG-14, D125).
- Las fechas son aware en UTC: una fecha sin zona o con desfase distinto de UTC se rechaza con `RN-GL-01` (`422`, D128).
- Los rechazos son de **dos clases** (RN-GL-02, D135). La **validación de entrada** (referencias inválidas, fecha sin zona o fuera de UTC, cuerpo mal formado) se informa **toda junta** en un único `422`: una petición con una prestación inexistente y una fecha sin zona responde un solo error con `RN-GL-01` y `RN-GL-04`. Las **reglas de negocio** se evalúan solo con la entrada válida y **de a una**: primero que el turno no cruce la medianoche del consultorio (`RN-AG-10d`), después el solapamiento. El solapamiento es una sola regla que mira dos recursos, por eso el doble conflicto conserva sus dos códigos (lectura confirmada por el autor, D139; ver `design.md`, D4).
- Los errores salen como `application/problem+json` (RFC 7807) con la lista `codigos`.
- Se crea el esqueleto del backend (`backend/app`, `backend/tests`; D122), el **archivo único de dependencias**, `backend/pyproject.toml` (D137), con versiones exactas (D116, D133) y la configuración de pytest, y el `README.md` de la raíz, con el que el repo se clona y se corren los tests.

**Historias y escenarios**

| | IDs |
|---|---|
| Historia cubierta | US-010 |
| Escenarios cubiertos en el spec (8) | E1, E2, E3, E4, E5, E6, E7, E12 |
| Cubierto solo como test unitario, fuera del spec | E8 (intervalo inválido; RN-AG-10d, RN-GL-01) |
| Escenarios de US-010 que quedan fuera | E9 (historial, C-03), E10 (horario y bloqueos, C-12 y C-13), E11 (concurrencia, C-02) |

**Excepción de tamaño (D123).** `CHANGES.md` define cada change con «3 a 6 escenarios»; este tiene **8** (E1..E7 y E12). El autor lo aceptó como excepción registrada, solo para C-01: son variantes cortas de una misma regla que la base de conocimiento ya definió, y recortarlas dejaría casos definidos sin probar. La consigna pide al menos tres (feliz, error de negocio y borde): feliz = E1; error de negocio = E2, E3, E4, E12; borde = E5 (empieza exactamente cuando termina otro), E6, E7.

**Segunda excepción de tamaño (D134).** `CHANGES.md` habla de «alrededor de 20 tareas» por change; `tasks.md` tiene **53**, en 14 grupos. El autor lo aceptó como segunda excepción registrada, solo para C-01, con una condición: que las tareas vayan **agrupadas por tema** (preparación, dominio, persistencia, un grupo por escenario, API, demo y README, verificación final). Es la consecuencia directa de la primera: ocho escenarios, cada uno con su ciclo RED → GREEN → TRIANGULATE → REFACTOR. El change no entra en una sola sesión de trabajo: se implementa por grupos.

## Fuera de alcance

Este change **no** hace nada de lo siguiente:

- **Historial de cambios** (`EventoTurno`, RN-AG-11; E9): es del change siguiente, C-03.
- **Horario recurrente y bloqueos** (RN-AG-04, RN-AG-04b; E10): un turno fuera del horario de atención se acepta.
- **Concurrencia** (RN-AG-10c; E11) y la restricción de exclusión de PostgreSQL: llegan con C-02.
- **Autenticación y roles**: `POST /turnos` va **sin autenticación**. Es un **límite conocido** (DD-14) que el README declara; se protege con JWT en el change de usuarios y acceso (US-092).
- **Interfaz gráfica**: se prueba desde Swagger (`/docs`) y con tests; la pantalla es de US-011.
- **PostgreSQL, Alembic, Redis y Docker**: el esquema se crea con `create_all` sobre SQLite en memoria (DD-15).
- Estados `pendiente_sena` y `pendiente_aprobacion` como estado inicial, **seña**, **lista de espera**, **WhatsApp** y **consentimiento**.
- **Reprogramar, cancelar, confirmar y consultar** turnos: no hay `GET`, `PATCH` ni `DELETE`.
- **Gestión de prestaciones, sillones, profesionales y pacientes**: salen del seed de demo o de las factories de test. No se valida que la duración sea múltiplo de 5 (RN-AG-01, D131).
- **Paciente inactivo**: no existe en el modelo de la v1; queda para la Fase 2 (D136).
- **Duración modificable** en la petición (RN-AG-02, D98: la implementa US-012).
- **Sobreturnos y excepción de horario**: fuera de la v1.

## Capabilities

### New Capabilities

- `creacion-de-turnos`: alta de un turno para un paciente, una prestación, un profesional y un sillón, con prevención de solapamientos por profesional y por sillón sobre intervalos semiabiertos, contando solo los turnos activos, y con errores identificados por código de regla.

### Modified Capabilities

Ninguna: `openspec/specs/` está vacío, es el primer change.

## Impact

- **Código nuevo** (el repo no tiene código de aplicación): `backend/app` (capas `domain`, `application`, `infrastructure`, `api`) y `backend/tests` (`unit`, `integration`, `api`).
- **API**: un endpoint nuevo, `POST /turnos`, con respuestas `201`, `409` y `422`. El contrato completo, con un ejemplo de cada respuesta, está en `design.md` (D4).
- **Datos**: tablas `consultorio`, `profesional`, `sillon`, `prestacion`, `paciente` y `turno` (subconjunto del primer change de `04_modelo_de_datos.md`), solo en SQLite en memoria. Datos siempre ficticios (RN-PR-01).
- **Dependencias**: se crea `backend/pyproject.toml` con versiones exactas, sin empaquetar el proyecto. Política de pins del autor (D133): FastAPI de la serie 0.115.x, SQLAlchemy de la serie 2.0.x, Pydantic compatible con ese FastAPI y ninguna versión publicada en la última semana. Los pins, con su fecha y su fuente, están en `design.md` (D1). Con esos pins el change se instala en Python 3.11, 3.12 o 3.13.
- **Repositorio**: `README.md` nuevo en la raíz y entradas de Python en `.gitignore`.
- **Changes posteriores**: C-02 reemplaza `create_all` por migraciones y agrega la restricción de exclusión; C-03 suma el historial al mismo caso de uso; C-07 protege el endpoint.
