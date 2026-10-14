# Turnos Odontológicos AR

Sistema de gestión de turnos y agenda para odontólogos independientes y consultorios chicos de Argentina. Reemplaza el papel, el Excel y el WhatsApp suelto.

**Qué entrega hasta ahora**:

- `crear-turno-sin-solapamientos` (C-01): una API con un solo endpoint, `POST /turnos`, que crea un turno en estado `reservado` (con `fin = inicio + duración de la prestación`) y rechaza con `409` el que se superpone con un turno activo del mismo profesional (`RN-AG-05`) o del mismo sillón (`RN-AG-08`), informando el código de la regla que falló.
- `infraestructura-postgresql` (C-02): la misma API sobre **PostgreSQL**, con esquema creado por migraciones (Alembic), una restricción de exclusión que hace que la base rechace por sí misma el solapamiento de turnos activos, el caso de uso que serializa las reservas simultáneas (el que llega segundo recibe el mismo `409`) y `docker compose up` para levantar todo.

- `historial-de-turnos` (C-03): `GET /turnos/{id}/historial` devuelve los eventos del turno en orden cronológico. `POST /turnos` registra el evento `creado` en la misma transacción que el turno (si el evento no se guarda, el turno tampoco), y en PostgreSQL la base rechaza modificar o borrar un evento (el historial es de solo inserción).

No hay interfaz gráfica. La API se puede probar sin instalar nada más que Python (base SQLite en memoria) o sobre PostgreSQL con Docker.

> Todos los datos del proyecto, de los tests y de la demo son **ficticios**. No hay datos reales de pacientes ni secretos.

## Requisitos

- **Python 3.11, 3.12 o 3.13.** No funciona con Python 3.14: una de las dependencias fijadas (`pydantic-core`) no publica binario para esa versión.
- Para instalar, correr los tests y probar la demo: nada más. **No hacen falta Docker, PostgreSQL ni Redis.**
- **Docker Desktop** (Docker Compose v2) solo para levantar la API sobre PostgreSQL y para el perfil opcional de tests con PostgreSQL.

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
| `psycopg[binary]` | 3.3.6 |
| `alembic` | 1.20.0 |
| `pytest` | 9.1.1 |
| `httpx` | 0.28.1 |

Imágenes de Docker (fijadas por etiqueta y digest en `docker-compose.yml` y `backend/Dockerfile`):

| Imagen | Etiqueta |
|---|---|
| `postgres` | `17.10-bookworm` |
| `python` | `3.13.15-slim-bookworm` |

Las dependencias transitivas las resuelve `pip` el día de la instalación.

`tzdata` hace falta en Windows: ahí `zoneinfo` no trae base de zonas horarias y el sistema usa `America/Argentina/Buenos_Aires`.

## Tests

Desde `backend/`, con el entorno activado:

```
python -m pytest
```

Los tests corren con **SQLite en memoria**: no necesitan Docker, PostgreSQL ni Redis, ni ningún archivo de base de datos.

La corrida termina con **«193 passed, 37 deselected, 1 warning»**. Los 37 «deselected» son los del perfil opcional con PostgreSQL (más abajo), que la corrida por defecto excluye a propósito. El warning es un aviso de deprecación interno de Starlette (`starlette/testclient.py`, sobre `anyio.abc.BlockingPortal`): viene de una dependencia con versión fijada, no del código del proyecto, y no indica ningún problema.

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

Los escenarios del historial (`historial-de-turnos`, C-03) están en `openspec/changes/historial-de-turnos/specs/` y se prueban en la suite por defecto, en `backend/tests/integration/test_historial.py` (caso de uso) y `backend/tests/api/test_historial.py` (HTTP):

| Escenario | Qué verifica | Test titular |
|---|---|---|
| E9 | Crear un turno registra el evento `creado` | `test_e9_crear_turno_registra_el_evento_creado` |
| E9 | Un rechazo no registra ningún evento | `test_e9_un_rechazo_no_registra_ningun_evento` |
| E9 | Si el evento no se puede guardar, el turno tampoco queda | `test_e9_si_el_evento_no_se_guarda_no_queda_el_turno` |
| E9 | Por HTTP, `POST /turnos` deja el evento en el historial | `test_e9_post_turnos_deja_el_evento_creado_en_el_historial` |
| US-015 CA-1 | El historial devuelve los eventos del turno pedido, en orden cronológico | `test_ca1_consultar_historial_devuelve_los_eventos_del_turno`, `test_ca1_consultar_historial_respeta_el_orden_cronologico` |
| US-015 CA-1 | Un turno sin eventos devuelve la lista vacía | `test_ca1_turno_sin_eventos_devuelve_lista_vacia` (por HTTP: `test_ca1_get_historial_de_turno_sin_eventos_responde_lista_vacia`) |
| US-015 CA-1 | La ruta del historial no admite modificaciones (`405`) | `test_ca1_la_ruta_del_historial_no_admite_modificaciones` (parametrizado) |
| HIS-1 | Un turno inexistente rechaza con `RN-GL-04` (`404` por HTTP) | `test_his1_turno_inexistente_rechaza_con_rn_gl_04`, `test_his1_get_historial_de_turno_inexistente_responde_404` |
| HIS-1 | Un id que no es número responde `422` sin código | `test_his1_id_que_no_es_numero_responde_422_sin_codigo` |

Además, E1, E4 y E12 se prueban por HTTP en `backend/tests/api/test_post_turnos.py` (`test_e1_post_turnos_responde_201`, `test_e4_post_turnos_responde_409_con_los_dos_codigos`, `test_e12_post_turnos_responde_422_con_rn_gl_04`), y las reglas puras tienen tests unitarios sin base de datos en `backend/tests/unit/`.

## Perfil opcional con PostgreSQL

Una parte de los tests (la que prueba lo que solo PostgreSQL garantiza) está fuera de la corrida por defecto y lleva el marcador `postgres`. **Docker Desktop hace falta solo para esto**: la instalación y los tests de las secciones anteriores no lo usan.

1. Desde la raíz del repositorio, copiá `.env.example` a `.env` (si no existe) y levantá la base. Queda publicada en `127.0.0.1:5434` (el puerto 5434 del host tiene que estar libre) y crea las bases `turnos` y `turnos_test`:

   ```
   docker compose up -d postgres
   docker compose ps
   ```

   Esperá a que `postgres` figure como `healthy`.

2. Desde `backend/`, con el entorno activado, definí `TEST_DATABASE_URL` en esa terminal y corré el perfil. La base tiene que terminar en `_test`: el perfil **borra y recrea** su esquema `public`.

   PowerShell:

   ```
   $env:TEST_DATABASE_URL = "postgresql+psycopg://app:app@127.0.0.1:5434/turnos_test"
   python -m pytest -m postgres
   ```

   bash:

   ```
   TEST_DATABASE_URL=postgresql+psycopg://app:app@127.0.0.1:5434/turnos_test python -m pytest -m postgres
   ```

   Se usa `127.0.0.1` y no `localhost`: en Windows `localhost` resuelve primero a IPv6 y la conexión espera varios segundos antes de caer a IPv4.

Con la base levantada, la corrida termina con **«37 passed, 193 deselected, 1 warning»**. **Si PostgreSQL no está disponible** (Docker apagado, `TEST_DATABASE_URL` sin definir o base que no responde), los 37 tests del perfil **se omiten con el motivo en el resumen** (**«37 skipped, 193 deselected»**) y la corrida termina con código de salida 0. Si la base de `TEST_DATABASE_URL` no termina en `_test`, el perfil falla a propósito para no borrar otra base.

El esquema de estos tests sale siempre de las migraciones, nunca de `create_all`. Por eso el perfil también comprueba que las migraciones y los modelos coinciden (INF-1): si alguien cambia un modelo sin escribir su migración, ese test se pone en rojo. **La suite por defecto no avisa de esto**: hay que correr el perfil cada vez que se toque el esquema.

Para detener la base: `docker compose down` (conserva los datos); `docker compose down -v` los borra.

### Escenario → test (perfil con PostgreSQL)

Los escenarios están en `openspec/changes/infraestructura-postgresql/specs/persistencia-postgresql/spec.md` (y los de E9 y US-015 CA-1 en `openspec/changes/historial-de-turnos/specs/`); los tests, en `backend/tests/postgres/`.

| Escenario | Qué verifica | Test titular |
|---|---|---|
| INF-1 | Una base vacía migrada queda con el esquema de los modelos (siete tablas desde C-03), sin diferencias | `test_inf1_base_vacia_migrada_queda_con_el_esquema_del_modelo` (`test_migraciones.py`) |
| INF-1 | Deshacer las migraciones deja la base vacía | `test_inf1_deshacer_las_migraciones_deja_la_base_vacia` (`test_migraciones.py`) |
| INF-1 | Deshacer solo las migraciones del historial deja el esquema de C-01 | `test_inf1_deshacer_las_migraciones_del_historial_deja_el_esquema_de_c01` (`test_migraciones.py`) |
| INF-2 | La base rechaza el solapamiento por profesional (E2) y por sillón (E3) | `test_inf2_la_base_rechaza_el_solapamiento_de_e2`, `test_inf2_la_base_rechaza_el_solapamiento_de_e3` (`test_restriccion_de_exclusion.py`) |
| INF-2 | Cualquier estado activo bloquea | `test_inf2_cualquier_estado_activo_bloquea` (parametrizado) |
| INF-3 | La base acepta el turno contiguo (E5) y un turno no activo no bloquea (E6) | `test_inf3_la_base_acepta_el_turno_contiguo_de_e5`, `test_inf3_un_turno_no_activo_no_bloquea` (parametrizado) |
| E11 | La reserva que pierde la carrera recibe el rechazo con los códigos completos | `test_e11_la_reserva_que_pierde_la_carrera_recibe_el_rechazo_por_solapamiento` (`test_reservas_simultaneas.py`) |
| E11 | Ocho peticiones a la vez crean un solo turno | `test_e11_de_ocho_peticiones_a_la_vez_se_crea_un_solo_turno` |
| E11 | Por HTTP, el que pierde recibe `409` | `test_e11_post_turnos_responde_409_al_que_pierde_la_carrera` |
| E9 | Ocho reservas simultáneas dejan un solo turno y un solo evento `creado` | `test_e9_de_ocho_reservas_simultaneas_queda_un_solo_evento` (`test_reservas_simultaneas.py`) |
| US-015 CA-1 | La base rechaza `UPDATE`, `DELETE` y `TRUNCATE` sobre un evento | `test_ca1_la_base_rechaza_modificar_o_borrar_un_evento` (parametrizado: `update_del_tipo`, `delete`, `truncate`; `test_historial_inmutable.py`) |
| US-015 CA-1 | La base acepta un evento nuevo del mismo turno | `test_ca1_la_base_acepta_un_evento_nuevo_del_mismo_turno` (`test_historial_inmutable.py`) |
| INF-4 | La suite por defecto corre sin PostgreSQL y el perfil se omite | Ningún test: se comprueba con los dos comandos de esta sección y de «Tests» (arriba) en una máquina sin Docker ni variables de entorno |

`crear_turno` toma un bloqueo de fila sobre el profesional y el sillón antes de leer los turnos ocupados (`SELECT ... FOR NO KEY UPDATE`): la segunda reserva del mismo recurso espera, ve el turno ya confirmado y responde su `409` sin reintentar. La restricción de exclusión de la base sigue siendo la última defensa.

## Levantar la API y probarla a mano (demo sin Docker)

Desde `backend/`, con el entorno activado:

```
python -m uvicorn app.main:crear_app_demo --factory
```

Swagger queda en <http://127.0.0.1:8000/docs>. Para detener el servidor, `Ctrl+C`.

La demo usa una base SQLite en memoria con datos ficticios. Cada arranque parte de los mismos datos y al reiniciar se pierden los turnos creados. El único endpoint de lectura es el del historial de un turno, así que los identificadores de los demás recursos son fijos:

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
3. La misma con `"prestacion_id": 999` → `422`, con el código `RN-GL-04` (no se registra ningún evento).
4. `GET /turnos/1/historial` → `200`, con una lista de un solo evento: `tipo` `creado`, `actor_tipo` `usuario` y `actor_id` vacío (`null`). El `409` y el `422` de los pasos 2 y 3 no agregan eventos: repetir la consulta sigue mostrando uno.
5. `GET /turnos/999/historial` → `404`, con el código `RN-GL-04`.

Con `curl`:

```
curl -i -X POST http://127.0.0.1:8000/turnos -H "Content-Type: application/json" -d "{\"paciente_id\": 1, \"prestacion_id\": 1, \"inicio\": \"2026-11-02T13:00:00Z\"}"
curl -i http://127.0.0.1:8000/turnos/1/historial
```

La demo parte siempre sin turnos, así que el primero que se crea es el `1`. En la API sobre PostgreSQL el id lo asigna la base y puede ser otro: usá el `id` que devolvió el `201`.

## Levantar la API con PostgreSQL

Necesita Docker Desktop. Los datos son los mismos de la demo y todos son ficticios.

1. Desde la raíz del repositorio, copiá `.env.example` a `.env` (Compose lo lee solo; Python no lee `.env`).
2. Construí y levantá todo:

   ```
   docker compose up --build -d
   docker compose ps
   ```

   Esperá a que `postgres` y `api` figuren como `healthy`. Al arrancar, el contenedor de la API aplica las migraciones (`alembic upgrade head`), carga el seed ficticio si falta y recién entonces levanta el servidor: `docker compose logs api` lo muestra. Una segunda vez el log dice «El seed ya estaba cargado: no hizo falta.». Esto vale para una sola réplica de la API.
3. Swagger queda en <http://127.0.0.1:8000/docs>, con los mismos identificadores, la misma petición de ejemplo y el mismo recorrido de la sección anterior. A diferencia de la demo, los turnos **persisten**: tras `docker compose restart api`, repetir la primera petición devuelve `409`.

Los puertos se publican solo en `127.0.0.1`: `8000` para la API y `5434` para PostgreSQL (el 5434 y no el 5432, para no chocar con un PostgreSQL local). Los dos tienen que estar libres en el host; si no, `docker compose up` falla y hay que cambiar el mapeo en `docker-compose.yml` (y la URL de `TEST_DATABASE_URL`). Se usa `127.0.0.1` y no `localhost` por la razón explicada arriba.

Para detener: `docker compose down` (conserva los datos); `docker compose down -v` los borra y la próxima vez la base arranca vacía.

### Variables de entorno

| Variable | Quién la lee | Valor de prueba |
|---|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | La imagen de PostgreSQL y `docker-compose.yml` | `app`, `app`, `turnos` |
| `DATABASE_URL` | La API (`crear_app_desde_entorno`), Alembic y la carga del seed | Dentro de Compose la arma `docker-compose.yml`: `postgresql+psycopg://app:app@postgres:5432/turnos`. Desde tu máquina: `postgresql+psycopg://app:app@127.0.0.1:5434/turnos` |
| `TEST_DATABASE_URL` | Solo el perfil `postgres` de pytest | `postgresql+psycopg://app:app@127.0.0.1:5434/turnos_test` |

Si falta `DATABASE_URL`, la API sin Docker (`crear_app_desde_entorno`) **no cae a SQLite**: falla con un mensaje que nombra la variable. Las credenciales son de prueba.

Para levantar la API sobre PostgreSQL sin construir la imagen (con la base ya levantada, desde `backend/`):

```
# PowerShell
$env:DATABASE_URL = "postgresql+psycopg://app:app@127.0.0.1:5434/turnos"
python -m alembic upgrade head
python -m app.infrastructure.db.cargar_seed
python -m uvicorn app.main:crear_app_desde_entorno --factory
```

### Migraciones

El esquema de PostgreSQL sale solo de migraciones (`backend/app/infrastructure/db/migraciones/versions/`: `0001` crea las seis tablas, `0002` agrega las restricciones de exclusión, `0003` crea la tabla `evento_turno` del historial y `0004` agrega los disparadores que hacen que la base rechace `UPDATE`, `DELETE` y `TRUNCATE` sobre esa tabla). Son solo para PostgreSQL; la suite por defecto crea el esquema con `create_all` sobre SQLite. Desde `backend/`, con `DATABASE_URL` definida como arriba:

```
python -m alembic current
python -m alembic upgrade head
python -m alembic downgrade base
python -m alembic revision --autogenerate --rev-id 0005 -m "descripcion"
```

La migración autogenerada **se revisa a mano** antes de usarla, y cada change que toque un modelo agrega la suya y corre el perfil opcional (INF-1).

## Límites conocidos

- **`POST /turnos` no tiene autenticación** en este change (DD-14). Es aceptable porque solo hay datos ficticios y ningún despliegue público; por eso los puertos se publican solo en `127.0.0.1`.
- Los datos de la demo sin Docker viven en memoria y se pierden al reiniciar; los de la API sobre PostgreSQL persisten en el volumen de Docker.
- La coincidencia entre migraciones y modelos (INF-1), la protección ante reservas simultáneas (E11, y el evento único de E9 con ocho reservas) y la garantía de que la base rechaza modificar o borrar un evento (US-015 CA-1, migración `0004`) **solo se prueban en el perfil opcional con PostgreSQL**: la suite por defecto no las ejerce. En SQLite (demo y suite por defecto) la inmutabilidad del historial se garantiza solo desde la aplicación: no hay métodos para modificarlo y la ruta responde `405`.
- **`GET /turnos/{id}/historial` no tiene autenticación** (DD-14): cualquiera que llegue a la API ve el historial de cualquier turno. Es aceptable por el mismo motivo que `POST /turnos`: datos ficticios y puertos solo en `127.0.0.1`.
- Los eventos `creado` anteriores a C-07 tienen `actor_tipo` `usuario` y **`actor_id` vacío para siempre** (D159): todavía no hay usuarios autenticados y completarlo después sería modificar el historial.
- Los turnos guardados antes de la migración `0003` (por ejemplo, los de la prueba manual de C-02 en el volumen de PostgreSQL) **no tienen historial**: la consulta devuelve `200` con `[]` (D160). La migración no inventa eventos del pasado.
- El puerto 5434 (PostgreSQL) y el 8000 (API) del host tienen que estar libres.
- El proyecto de Compose tiene nombre fijo (`turnos-odontologia`): **dos copias del repositorio en la misma máquina comparten contenedores y volumen**, y un `docker compose down -v` en una borra los datos de la otra. Para levantar una segunda copia aparte, usá otro nombre de proyecto en todos los comandos: `docker compose -p otro-nombre up -d`.
- En Windows, si el repositorio está en una ruta muy larga (más de unos 200 caracteres), el perfil opcional falla al importar `psycopg` con «El nombre del archivo o la extensión es demasiado largo». Cloná en una ruta corta.
- Las credenciales de los ejemplos y de `.env.example` son de prueba. No hay configuración de producción: TLS, copias de respaldo, roles con privilegios mínimos ni ajuste del pool.
- La API migra al arrancar el contenedor: sirve para una sola réplica.
- No se valida el horario de atención del profesional ni del consultorio.
- No hay interfaz gráfica ni Redis: llegan en changes posteriores.
- En `/docs`, las respuestas `409` y `422` figuran bajo `application/problem+json` y también bajo `application/json`. La respuesta real sale siempre como `application/problem+json`.
- Los mensajes de validación de formato que genera Pydantic salen en inglés.

## Estructura

La consigna muestra `src/` y `tests/` y aclara que los nombres pueden variar. Acá la correspondencia es:

| Consigna | Este repositorio |
|---|---|
| `src/` | `backend/app/` |
| `tests/` | `backend/tests/` |

`backend/app/` tiene las capas `domain` (reglas puras, sin FastAPI ni SQLAlchemy), `application` (casos de uso), `infrastructure` (SQLAlchemy, SQLite y PostgreSQL, migraciones de Alembic, seed de la demo) y `api` (FastAPI). La documentación del dominio está en `knowledge-base/` y el plan de changes en `CHANGES.md`.
