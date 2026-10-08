# Turnos Odontológicos AR

Sistema de gestión de turnos y agenda para odontólogos independientes y consultorios chicos de Argentina. Reemplaza el papel, el Excel y el WhatsApp suelto.

**Qué entrega este change (`crear-turno-sin-solapamientos`)**: una API con un solo endpoint, `POST /turnos`, que crea un turno en estado `reservado` (con `fin = inicio + duración de la prestación`) y rechaza con `409` el que se superpone con un turno activo del mismo profesional (`RN-AG-05`) o del mismo sillón (`RN-AG-08`), informando el código de la regla que falló. No hay interfaz gráfica.

> Todos los datos del proyecto, de los tests y de la demo son **ficticios**. No hay datos reales de pacientes ni secretos.

## Requisitos

- **Python 3.11, 3.12 o 3.13.** No funciona con Python 3.14: una de las dependencias fijadas (`pydantic-core`) no publica binario para esa versión.
- Nada más. **No hacen falta Docker, PostgreSQL ni Redis.**

En Windows, el lanzador `py` sin versión puede usar Python 3.14; por eso los comandos piden una versión explícita.

## Instalación

Desde la raíz del repositorio, en Windows (PowerShell o cmd):

```
cd backend
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install --group test
```

`py -3.13` puede ser `py -3.11` o `py -3.12`. Se actualiza `pip` primero porque `--group` necesita `pip` 25.1 o superior.

En Linux y macOS cambian solo la creación y la activación del entorno:

```
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --group test
```

Todas las dependencias están en un único archivo, `backend/pyproject.toml`. No hay `requirements.txt`.

### Versiones fijadas

Las versiones exactas viven en `backend/pyproject.toml`:

| Paquete | Versión |
|---|---|
| `fastapi` | 0.115.14 |
| `starlette` | 0.46.2 |
| `pydantic` | 2.11.10 |
| `SQLAlchemy` | 2.0.54 |
| `uvicorn` | 0.54.0 |
| `tzdata` | 2026.4 |
| `pytest` | 9.1.1 |
| `httpx` | 0.28.1 |

Las dependencias transitivas las resuelve `pip` el día de la instalación.

`tzdata` hace falta en Windows: ahí `zoneinfo` no trae base de zonas horarias y el sistema usa `America/Argentina/Buenos_Aires`.

## Tests

Desde `backend/`, con el entorno activado:

```
python -m pytest
```

Los tests corren con **SQLite en memoria**: no necesitan Docker, PostgreSQL ni Redis, ni ningún archivo de base de datos.

La corrida termina con **«144 passed, 1 warning»**. El warning es un aviso de deprecación interno de Starlette (`starlette/testclient.py`, sobre `anyio.abc.BlockingPortal`): viene de una dependencia con versión fijada, no del código del proyecto, y no indica ningún problema.

### Escenario → test

Cada escenario del change tiene un test titular de integración (caso de uso real, repositorio real y SQLite en memoria), en `backend/tests/integration/test_crear_turno.py`:

| Escenario | Qué verifica | Test titular |
|---|---|---|
| E1 | Se crea un turno `reservado` con el fin calculado | `test_e1_feliz_crea_turno_reservado_con_fin_calculado` |
| E2 | Se rechaza el solapamiento con un turno activo del profesional (`RN-AG-05`) | `test_e2_profesional_ocupado_rechaza_con_rn_ag_05` |
| E3 | Se rechaza el solapamiento con un turno activo del sillón (`RN-AG-08`) | `test_e3_sillon_ocupado_rechaza_con_rn_ag_08` |
| E4 | Si chocan los dos, se informan los dos códigos | `test_e4_doble_conflicto_informa_los_dos_codigos` |
| E5 | Un turno que empieza justo cuando termina otro se acepta | `test_e5_borde_contiguo_se_acepta` |
| E6 | Solo los turnos activos bloquean | `test_e6_estado_no_activo_no_bloquea` |
| E7 | Un minuto de solapamiento se rechaza | `test_e7_borde_de_un_minuto_se_rechaza` |
| E12 | Una referencia inválida se rechaza con `RN-GL-04` | `test_e12_recurso_no_encontrado_rechaza_con_rn_gl_04` |

Además, E1, E4 y E12 se prueban por HTTP en `backend/tests/api/test_post_turnos.py` (`test_e1_post_turnos_responde_201`, `test_e4_post_turnos_responde_409_con_los_dos_codigos`, `test_e12_post_turnos_responde_422_con_rn_gl_04`), y las reglas puras tienen tests unitarios sin base de datos en `backend/tests/unit/`.

## Levantar la API y probarla a mano

Desde `backend/`, con el entorno activado:

```
python -m uvicorn app.main:crear_app_demo --factory
```

Swagger queda en <http://127.0.0.1:8000/docs>. Para detener el servidor, `Ctrl+C`.

La demo usa una base SQLite en memoria con datos ficticios. Cada arranque parte de los mismos datos y al reiniciar se pierden los turnos creados. No hay endpoints de lectura, así que los identificadores son fijos:

| Qué | Identificadores |
|---|---|
| Consultorio | 1 — «Consultorio Demo» |
| Profesional | 1 — «Dra. Demo Ficticia» |
| Sillón | 1 — «Sillón 1» |
| Prestaciones | 1 «Consulta / control» (30 min), 2 «Limpieza» (45 min), 3 «Obturación» (60 min), 4 «Extracción» (45 min), 5 «Urgencia» (30 min) |
| Pacientes | 1 «Ana Ejemplo», 2 «Bruno Ficticio», 3 «Carla Inventada» |

El profesional y el sillón se pueden omitir en la petición: como la demo tiene uno solo de cada uno, se usan esos.

### Petición de ejemplo

`POST /turnos` con el cuerpo:

```json
{"paciente_id": 1, "prestacion_id": 1, "inicio": "2026-11-02T13:00:00Z"}
```

El `inicio` va en UTC (termina en `Z`).

### Recorrido

1. Esa petición → `201`, con el turno `reservado` en el profesional 1 y el sillón 1.
2. La misma petición otra vez → `409`, con `codigos` igual a `["RN-AG-05", "RN-AG-08"]`.
3. La misma con `"prestacion_id": 999` → `422`, con el código `RN-GL-04`.

Con `curl`:

```
curl -i -X POST http://127.0.0.1:8000/turnos -H "Content-Type: application/json" -d "{\"paciente_id\": 1, \"prestacion_id\": 1, \"inicio\": \"2026-11-02T13:00:00Z\"}"
```

## Límites conocidos

- **`POST /turnos` no tiene autenticación** en este change (DD-14). Es aceptable porque solo hay datos ficticios, base en memoria y ningún despliegue público.
- Los datos de la demo viven en memoria y se pierden al reiniciar.
- No hay control de concurrencia: dos peticiones simultáneas al mismo horario no están cubiertas (E11 queda fuera del change). La demo comparte una sola conexión y es para una persona probando a mano.
- No se valida el horario de atención del profesional ni del consultorio.
- No hay interfaz gráfica, PostgreSQL, Docker, Redis ni migraciones: llegan en changes posteriores.
- En `/docs`, las respuestas `409` y `422` figuran bajo `application/problem+json` y también bajo `application/json`. La respuesta real sale siempre como `application/problem+json`.
- Los mensajes de validación de formato que genera Pydantic salen en inglés.

## Estructura

La consigna muestra `src/` y `tests/` y aclara que los nombres pueden variar. Acá la correspondencia es:

| Consigna | Este repositorio |
|---|---|
| `src/` | `backend/app/` |
| `tests/` | `backend/tests/` |

`backend/app/` tiene las capas `domain` (reglas puras, sin FastAPI ni SQLAlchemy), `application` (casos de uso), `infrastructure` (SQLAlchemy, SQLite, seed de la demo) y `api` (FastAPI). La documentación del dominio está en `knowledge-base/` y el plan de changes en `CHANGES.md`.
