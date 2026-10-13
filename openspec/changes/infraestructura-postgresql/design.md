# Design: infraestructura-postgresql

Fecha del design: **2026-10-13**. Gobernanza **ALTO**: nada de esto se implementa hasta que el autor lo revise.

**Revisión del autor (2026-10-13): aprobado tal cual.** Las decisiones marcadas «Propuesta» (I1 a I16) quedan confirmadas sin cambios, incluidas las 28 tareas como excepción de tamaño y el criterio de commits de I16. Su registro en `knowledge-base/10_preguntas_abiertas.md` y el cierre de los huecos de la sección «Contradicciones y huecos» se hacen al terminar el Apply, en un commit `docs(kb)` aparte.

**Ajuste del autor durante el Apply (2026-10-13): el contenedor se publica en el puerto 5434 del host.** Al empezar el grupo 2 se encontró el puerto 5432 ocupado por un PostgreSQL instalado en Windows como servicio (y el 5433 por el contenedor de otro proyecto). El autor eligió publicar en `127.0.0.1:5434:5432`: cambia el mapeo de I10 y la `TEST_DATABASE_URL` de I9 e I11 (`localhost:5434`). Dentro de la red de Compose la API sigue usando `postgres:5432`. Motivo adicional: el perfil de tests borra y recrea el esquema `public`, y no debe poder apuntar por accidente a una base local ajena.

Las decisiones de este documento se numeran **I1 a I16** («I» de infraestructura) para no confundirlas con las D1..D141 de `knowledge-base/10_preguntas_abiertas.md` ni con las D1..D20 del design de C-01. Cuando se cita «D» seguido de un número mayor que 20 es una decisión de la KB; «design C-01 D12» es del design archivado.

Cada decisión dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design, a confirmar por el autor) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»).

## Context

Motivación y alcance: ver `proposal.md`. Acá va solo el estado actual que condiciona el cómo.

**Lo que dejó C-01** (leído del código, no supuesto):

- `backend/app/infrastructure/db/motor.py` tiene una sola función, `crear_engine_en_memoria()`, con la URL de SQLite como constante. Nada lee variables de entorno.
- `modelos.py` define seis tablas con `DeclarativeBase`. Las restricciones `CHECK` y los índices tienen nombre explícito; las claves primarias, las foráneas y las dos `UNIQUE` **no tienen nombre**. Las fechas usan el tipo `FechaHoraUTC` (`DateTime(timezone=True)`), que ya normaliza a UTC lo que lee.
- `RepositorioAgendaSqlAlchemy.agregar` hace `flush()` y la unidad de trabajo confirma al salir. `turnos_que_intersecan` trae turnos de cualquier estado: la regla la decide el dominio.
- `crear_turno` valida la entrada, después RN-AG-10d, después el solapamiento, e inserta. Todo dentro de un `with uow:`.
- `app/main.py` tiene `crear_app(engine)` y `crear_app_demo()` (SQLite en memoria con el seed). No hay variable `app` de módulo.
- `seed_demo.cargar_demo` asigna los identificadores a mano y espera una base vacía.
- `tests/conftest.py` define los fixtures `engine`, `fabrica_sesiones`, `sesion` y `uow`; los tres últimos cuelgan de `engine`. La suite tiene 144 tests en verde.
- `.gitignore` ya ignora `.env` y `.env.*` y deja pasar `.env.example`.

**Por qué la validación de dominio sola no alcanza.** Con PostgreSQL en su nivel de aislamiento por defecto (lectura confirmada), dos transacciones que piden el mismo hueco leen la agenda antes de que la otra confirme: ninguna ve el turno de la otra, las dos pasan la validación de dominio y las dos insertan. La restricción de exclusión es lo que frena a la segunda (DD-04).

**Estado de Docker en esta máquina (comprobado el 2026-10-13).** `docker --version` responde `Docker version 28.5.1` y `docker compose version` responde `v2.40.2-desktop.1`: están instalados. Pero `docker info` falla con «open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified»: **Docker Desktop no está en ejecución**. Por eso este design no pudo probar nada contra PostgreSQL y todo lo que depende de la base va marcado «A verificar en el change». Para el Apply, el autor tiene que abrir Docker Desktop antes del grupo 2 de `tasks.md`.

## Goals / Non-Goals

**Goals:**

- Que el esquema de PostgreSQL salga solo de migraciones, y que haya una comprobación automática de que coincide con los modelos (INF-1).
- Que la base rechace por sí misma el solapamiento de turnos activos (INF-2) sin rechazar lo que el dominio acepta (INF-3).
- Que la carrera entre dos reservas termine con un ganador y un `409` con códigos RN para el otro (E11), sin tocar `backend/app/domain` ni `backend/app/api`.
- Que quien no usa Docker no note ningún cambio (INF-4).
- Dejar fijados los pins, los nombres de las variables de entorno y el comando del perfil opcional.

**Non-Goals:**

- Migraciones que corran en SQLite. Las migraciones son solo para PostgreSQL; la suite por defecto sigue con `create_all` (I6).
- Declarar la restricción de exclusión en el modelo declarativo (I5).
- Bloqueos explícitos (`SELECT ... FOR UPDATE`, bloqueos consultivos) o aislamiento serializable: la KB eligió la restricción (DD-04).
- Reintentos genéricos de transacciones o manejo de interbloqueos.
- Un endpoint de salud, lecturas, autenticación o cualquier cambio en el contrato de `POST /turnos`.
- Leer un archivo `.env` desde Python: no se agrega ninguna biblioteca para eso (I11).
- Redis, worker, frontend, tablas o columnas nuevas, historial (C-03).
- Configuración de producción: TLS, copias de respaldo, roles con privilegios mínimos, ajuste del pool.

## Decisions

### I1. Una capability nueva, `persistencia-postgresql`; E11 vive ahí — Propuesta

Los cinco escenarios (E11, INF-1 a INF-4) van en una capability nueva. `creacion-de-turnos` no recibe ningún delta.

**Por qué.** E1 a E7 y E12 describen qué responde `POST /turnos` y valen en cualquier base. E11 describe una garantía que **solo existe en PostgreSQL** y que la suite por defecto no puede comprobar (D75). Si E11 entrara en `creacion-de-turnos`, esa capability tendría un requisito que sus propios tests por defecto no ejercitan, y el change tocaría dos capabilities, contra «un change, una capability» (regla dura 12, regla de `proposal` en `openspec/config.yaml`).

**Alternativa.** Un delta `ADDED` en `creacion-de-turnos` con E11 y la capability nueva solo con INF-1 a INF-4. Es defendible porque E11 es un escenario de US-010. **Consecuencia de elegirla:** dos capabilities en un change y un requisito de `creacion-de-turnos` verificable solo con Docker.

### I2. Dependencias y versiones exactas — Decisión del autor (D116, D133, D137) + Propuesta (qué paquetes y en qué grupo)

**Política aplicada.** Fecha del design: 2026-10-13. No se toma ninguna versión publicada el **2026-10-06 o después** (D133). Todo va al archivo único `backend/pyproject.toml` (D137); no hay `requirements.txt`.

**Paquetes de Python.** Fuente: la API JSON de PyPI, consultada el **2026-10-13** con `curl` (`https://pypi.org/pypi/<paquete>/json` para las fechas de todas las versiones; `https://pypi.org/pypi/<paquete>/<versión>/json` para `requires_python` y `requires_dist`).

| Paquete | Versión | Publicada | Python requerido | Fuente | Por qué esa versión |
|---|---|---|---|---|---|
| `psycopg` | 3.3.6 | 2026-09-18 | `>=3.10` | `pypi.org/pypi/psycopg/3.3.6/json` | Es la más nueva y tiene 25 días. Driver sincrónico de PostgreSQL |
| `psycopg-binary` | 3.3.6 | 2026-09-18 | `>=3.10` | `pypi.org/pypi/psycopg-binary/3.3.6/json` | La fija el extra `binary` de `psycopg` 3.3.6 (`psycopg-binary==3.3.6`) |
| `alembic` | 1.20.0 | 2026-09-11 | `>=3.10` | `pypi.org/pypi/alembic/1.20.0/json` | Es la más nueva y tiene 32 días |

Compatibilidad comprobada con los metadatos, no supuesta:

- `psycopg` 3.3.6 pide `typing-extensions>=4.6` (solo Python menor que 3.13) y `tzdata` en Windows: `tzdata==2026.4` ya está fijado.
- `psycopg-binary` 3.3.6 publica ruedas `win_amd64` para CPython 3.11, 3.12 y 3.13 y `manylinux2014_x86_64` para las mismas: se instala sin compilar en Windows y en la imagen de Docker. No publica nada que este proyecto use para 3.14, igual que `pydantic-core` (límite ya declarado en el README).
- `alembic` 1.20.0 pide `SQLAlchemy>=2.0`, `Mako` y `typing-extensions>=4.12`: compatible con `SQLAlchemy==2.0.54`.
- `SQLAlchemy` 2.0.54 declara el extra `postgresql-psycopgbinary` como `psycopg[binary]>=3.0.7`: el dialecto `postgresql+psycopg` acepta 3.3.6.

**Dependencias transitivas.** Se mantiene el criterio de C-01: las resuelve `pip` el día de la instalación. `alembic` trae `Mako` sin rango (la más nueva al consultar es 1.4.3, del 2026-09-22) y `typing-extensions`. **Propuesta:** no fijarlas, como en C-01. Alternativa: fijar `Mako==1.4.3`; consecuencia, una línea más en el archivo y un pin que nadie eligió por una razón.

**Driver: `psycopg` (versión 3), no `psycopg2` — Propuesta.** La KB ya escribe la URL con `postgresql+psycopg://` (`08`, «Variables de entorno»). `psycopg` 3 es sincrónico por defecto y es el driver vigente; `psycopg2` está en mantenimiento. No se usa su modo asíncrono (DD-12, D119).

**Grupo: `app`, no un grupo aparte — Propuesta.** La API en Compose y las migraciones los necesitan para correr. Quien instala con `python -m pip install --group test` recibe dos paquetes más, con rueda binaria: no hace falta PostgreSQL ni un compilador para instalarlos (INF-4). Alternativa: un grupo `postgres` separado; consecuencia, la instalación por defecto no cambia, pero aparecen dos comandos de instalación y un `import alembic` que puede faltar.

**Cambios en `backend/pyproject.toml`:**

```toml
# Se agrega al comentario de cabecera:
# C-02: psycopg y alembic consultadas en PyPI el 2026-10-13; ninguna publicada el 2026-10-06 o después.

[dependency-groups]
app = [
    "fastapi==0.115.14",
    "starlette==0.46.2",
    "pydantic==2.11.10",
    "SQLAlchemy==2.0.54",
    "uvicorn==0.54.0",
    "tzdata==2026.4",
    "psycopg[binary]==3.3.6",
    "alembic==1.20.0",
]
# el grupo test no cambia

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = ["-ra", "--strict-markers", "-m", "not postgres"]
markers = [
    "postgres: necesita PostgreSQL (perfil opcional, D75); fuera de la corrida por defecto",
]
```

**Imágenes de Docker.** Fuente: la API de Docker Hub (`https://hub.docker.com/v2/repositories/library/<imagen>/tags?name=<etiqueta>`), consultada el **2026-10-13**.

| Imagen | Etiqueta | Último push de la etiqueta | Digest (índice multi-arquitectura) | Por qué |
|---|---|---|---|---|
| `postgres` | `17.10-bookworm` | 2026-08-05 | `sha256:9b18b78397054fce88a9552e9d5a3ad5bb7fd258c5b3cc1c5028e46373d6ea8f` | `17.11-bookworm` se volvió a subir el 2026-10-06: queda dentro de la semana |
| `python` | `3.13.15-slim-bookworm` | 2026-09-19 | `sha256:2325bb286ec344af3e5898cc224b5844e2707ac6e26b1632516fd3edc84a5e26` | `3.13.16-slim-bookworm` es del 2026-10-06. Python 3.13 es el del entorno local |

Dos aclaraciones que el autor tiene que conocer:

- **Docker Hub no da la fecha de publicación original de una etiqueta, solo la del último push**, y las etiquetas se pueden volver a subir (una reconstrucción con parches del sistema base). Lo verificado es «último push anterior al 2026-10-06». D133 habla de paquetes y no dice nada de imágenes: es un hueco de la KB (ver «Contradicciones y huecos»).
- **Propuesta: fijar etiqueta y digest** (`postgres:17.10-bookworm@sha256:…`) en `docker-compose.yml` y en el `Dockerfile`. Con solo la etiqueta, una reconstrucción posterior cambia lo que se descarga sin que cambie el archivo. Alternativa: solo la etiqueta; consecuencia, archivos más legibles pero no reproducibles byte a byte.

**Versión mayor de PostgreSQL: 17 — Propuesta.** La KB dice «no fijada». Se propone la serie 17 por conservadora. Alternativa verificada: `postgres:18.4-bookworm` (último push 2026-08-05, digest `sha256:882236b897e39051d2368c5ccc6cda944904723506b2dfc97f2a8f5bc9afa382`); la restricción de exclusión, `btree_gist` y `tstzrange` existen igual en las dos. Consecuencia de elegir la 18: la imagen oficial cambió la ubicación del directorio de datos, así que el volumen del `docker-compose.yml` se monta distinto (queda como «a verificar» si se elige).

**No se pudo verificar** (queda como «A verificar en el change», ver la lista V): que `pip` dentro de la imagen `python:3.13.15-slim-bookworm` sea 25.1 o superior (lo necesita `--group`), y la fecha de publicación de PostgreSQL 17.10 en `postgresql.org` (solo se consultó Docker Hub).

### I3. Estructura de archivos — Propuesta, sobre el árbol de `08_arquitectura_propuesta.md`

```
docker-compose.yml                       # nuevo (raíz)
.env.example                             # nuevo (raíz)
docker/postgres-init/01_base_de_tests.sql   # nuevo: CREATE DATABASE turnos_test;
backend/
  Dockerfile                             # nuevo
  .dockerignore                          # nuevo
  alembic.ini                            # nuevo
  pyproject.toml                         # se modifica (I2)
  app/
    main.py                              # + crear_app_desde_entorno
    application/puertos.py               # + SolapamientoEnLaBase
    application/crear_turno.py           # reevaluación ante la carrera (I8)
    infrastructure/
      configuracion.py                   # nuevo: leer_database_url
      repositories/agenda.py             # traduce la violación (I7)
      db/
        motor.py                         # + crear_engine(url)
        modelos.py                       # + convención de nombres (I4)
        seed_demo.py                     # + cargar_demo_si_falta, ajustar_secuencias
        cargar_seed.py                   # nuevo: python -m app.infrastructure.db.cargar_seed
        migraciones/
          env.py
          script.py.mako
          versions/
            0001_esquema_inicial.py
            0002_exclusion_de_solapamientos.py
  tests/
    unit/test_configuracion.py           # nuevo, suite por defecto
    integration/test_guard_nombres.py    # nuevo, suite por defecto
    integration/test_seed_demo.py        # nuevo, suite por defecto
    api/test_app_desde_entorno.py        # nuevo, suite por defecto
    postgres/                            # nuevo, todo con el marcador postgres
      __init__.py
      conftest.py
      carrera.py                         # ayuda para forzar la carrera (I9)
      test_migraciones.py                # INF-1
      test_restriccion_de_exclusion.py   # INF-2, INF-3
      test_reservas_simultaneas.py       # E11
      test_seed_y_api.py                 # seed y fábrica de la app sobre PostgreSQL
```

Las migraciones van dentro de `infrastructure/db/`, como dice el árbol de `08` («modelos SQLAlchemy, sesión, migraciones»). `backend/app/domain` y `backend/app/api` no cambian.

**`alembic.ini` aparte — Propuesta.** D137 puso en `pyproject.toml` las dependencias y la configuración de pytest. Alembic se configura con su `alembic.ini` clásico (ubicación de los scripts y registro de eventos), sin la URL de la base ni credenciales. Alternativa: la sección `[tool.alembic]` de `pyproject.toml` que admiten las versiones recientes de Alembic; no se propone porque este design no pudo probarla y `alembic.ini` es la forma documentada de siempre.

### I4. Nombres estables para las restricciones — Propuesta

Se agrega una convención de nombres a los metadatos de `Base` para las claves primarias, las foráneas y las `UNIQUE`, que hoy no tienen nombre:

```python
CONVENCION_DE_NOMBRES = {
    "ix": "ix_%(column_0_label)s",
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
}
```

No se pone clave `ck`: las tres `CHECK` ya tienen nombre explícito con prefijo `ck_` y una convención las duplicaría. Los índices conservan su nombre explícito.

**Por qué.** Una migración posterior que quiera quitar o cambiar una clave necesita su nombre. Sin convención, PostgreSQL inventa uno (`turno_paciente_id_fkey`) que no figura en ningún archivo del repositorio. Fijarlo ahora, con seis tablas y antes de la primera migración, no cuesta nada; hacerlo después obliga a migrar los nombres.

**Efecto en SQLite.** Solo cambian los nombres de las restricciones en el `create_all` de los tests. Ningún test los mira. Se comprueba corriendo la suite (V8).

**Alternativa.** No tocar `modelos.py` y aceptar los nombres por defecto de PostgreSQL. Consecuencia: la migración inicial queda igual de válida, pero las migraciones de C-03 en adelante dependen de nombres implícitos.

### I5. La restricción de exclusión: SQL exacto y dónde vive — Decisión del autor (DD-04, D75: el qué) + Propuesta (el cómo)

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE turno ADD CONSTRAINT ex_turno_profesional_sin_solapamiento
    EXCLUDE USING gist (
        profesional_id WITH =,
        tstzrange(inicio, fin, '[)') WITH &&
    )
    WHERE (estado IN ('pendiente_aprobacion', 'pendiente_sena', 'reservado', 'confirmado'));

ALTER TABLE turno ADD CONSTRAINT ex_turno_sillon_sin_solapamiento
    EXCLUDE USING gist (
        sillon_id WITH =,
        tstzrange(inicio, fin, '[)') WITH &&
    )
    WHERE (estado IN ('pendiente_aprobacion', 'pendiente_sena', 'reservado', 'confirmado'));
```

Cómo responde cada parte a la KB:

- `btree_gist` permite combinar la igualdad de un entero con el solapamiento de un rango en un mismo índice GiST.
- `tstzrange(inicio, fin, '[)')` es el intervalo semiabierto de RN-AG-09: `[10:00, 10:30)` y `[10:30, 11:00)` no se solapan (E5).
- El `WHERE` limita la restricción a los cuatro estados activos de RN-AG-10: un turno cancelado, vencido, atendido o ausente no participa (E6).
- Son dos restricciones separadas porque son dos recursos (RN-AG-05 y RN-AG-08) y porque el nombre de la que falla dice cuál chocó (I7).
- `inicio` y `fin` son `timestamp with time zone`, así que el rango no depende de la zona de la sesión.

**Dónde vive: solo en la migración `0002`, en SQL literal — Propuesta.** El modelo declarativo no la declara. Así SQLite no se entera (su `create_all` no cambia) y el SQL que corre es exactamente el que está escrito arriba, revisado a mano.

- La lista de estados va **escrita como literal** en la migración, no importada de `ESTADOS_ACTIVOS`: una migración es una foto y no puede cambiar si mañana cambia el dominio. Lo que avisa si se desalinean son los tests de INF-2 (parametrizado sobre los estados activos del dominio) e INF-3 (sobre los no activos).
- `downgrade` quita las dos restricciones. **No** quita la extensión: puede haberla creado otro. (La base de tests se limpia borrando el esquema entero, I9.)

**Alternativa descartada: declararla en el modelo** con `ExcludeConstraint` de `sqlalchemy.dialects.postgresql` y `.ddl_if(dialect="postgresql")`. Tendría una sola fuente de verdad, pero mete un tipo exclusivo de PostgreSQL en los modelos que usa la suite de SQLite, obliga a que `create_all` sobre PostgreSQL cree antes la extensión, y Alembic no compara restricciones de exclusión al autogenerar, así que igual habría que escribirla a mano en la migración.

**Estado efectivo y estado persistido (D92).** La restricción mira el estado persistido. Hoy coincide con el efectivo porque no hay seña. El change que cree la seña tiene que persistir el vencimiento antes de insertar (RN-GL-05 (a)); está fuera de este change, ver «Risks».

### I6. Alembic y la migración inicial (INF-1) — Decisión del autor (DD-15) + Propuesta (forma)

- **`0001_esquema_inicial`**: las seis tablas de C-01 con sus columnas, `CHECK`, `UNIQUE`, claves foráneas con `ON DELETE RESTRICT` e índices, con los nombres de I4. Se genera con `alembic revision --autogenerate` contra una base PostgreSQL vacía y **se revisa a mano** antes de darla por buena (regla del registro de skills). `downgrade` borra las seis tablas.
- **`0002_exclusion_de_solapamientos`**: el SQL de I5. Es una migración aparte porque es otro cambio de esquema y porque permite ver INF-1 en verde antes de que exista la restricción.
- Identificadores de revisión cortos y legibles (`0001`, `0002`), en lugar del hash por defecto.
- **`env.py`**: usa `Base.metadata` como destino; toma la URL de la opción `sqlalchemy.url` si alguien la puso por programa (los tests) y si no de `leer_database_url()` (I11). Solo modo en línea. `alembic.ini` no contiene la URL.
- **Las migraciones son solo para PostgreSQL.** La suite por defecto sigue creando el esquema con `create_all` (DD-03, DD-15).

**Cómo se garantiza la equivalencia (INF-1).** Un test del perfil `postgres` toma una base vacía, aplica todas las migraciones y le pide a Alembic que compare el resultado con `Base.metadata` (`alembic.autogenerate.compare_metadata`, con comparación de tipos). La lista de diferencias tiene que ser vacía. Además comprueba por inspección que las tablas son exactamente las seis más `alembic_version`. Es la misma comparación que usa el autogenerado, así que cualquier change futuro que toque un modelo sin escribir su migración pone ese test en rojo.

**Alternativa descartada: correr las migraciones también en SQLite** para tener esa comparación en la suite por defecto. Obligaría a que todas las migraciones futuras funcionen en SQLite, que no soporta bien `ALTER TABLE`, y a esquivar el SQL de I5. Es justo la dependencia que DD-03 quiso evitar.

**Límite conocido.** La equivalencia solo se comprueba en el perfil opcional. Si alguien cambia un modelo y no corre ese perfil, la suite por defecto no avisa. Mitigación: el README lo dice y la verificación final de cada change que toque el esquema lo corre.

### I7. De la violación de la restricción a un error con código RN — Propuesta

**Dónde aparece el error.** En el `flush()` de `RepositorioAgendaSqlAlchemy.agregar`. La transacción que llega segunda queda esperando a la primera; cuando la primera confirma, PostgreSQL le devuelve el error `23P01` (violación de exclusión). SQLAlchemy lo entrega como `IntegrityError` con el error del driver en `.orig`.

**Qué hace el repositorio.** Atrapa `IntegrityError`, lee el nombre de la restricción violada (`error.orig.diag.constraint_name`, leído con `getattr` para que el camino de SQLite no dependa del driver) y:

| Restricción violada | Qué levanta |
|---|---|
| `ex_turno_profesional_sin_solapamiento` | `SolapamientoEnLaBase(recurso="profesional")` |
| `ex_turno_sillon_sin_solapamiento` | `SolapamientoEnLaBase(recurso="sillon")` |
| cualquier otra, o ninguna | deja subir el `IntegrityError` original: es un error de programación |

`SolapamientoEnLaBase` es una excepción nueva de `app/application/puertos.py`. No es un error de dominio ni lleva código RN: es la señal, entre el repositorio y el caso de uso, de que otra transacción ocupó el hueco. La regla de capas lo permite: `infrastructure` importa `application` «solo para implementar sus puertos» (`08`, D70). El repositorio no decide nada de negocio ni conoce HTTP.

**Por qué el repositorio no arma él mismo el `ErrorDeSolapamiento`.** PostgreSQL informa **una sola** restricción violada (la primera que encuentra) y no dice contra qué turno. `Conflicto` necesita el `turno_id`, y un choque doble (E4) necesita los dos códigos. Esa información la tiene la validación de dominio, no el mensaje de la base. Por eso se reevalúa (I8).

### I8. El que pierde la carrera se reevalúa con el dominio (E11) — Propuesta

`crear_turno` pasa a ser:

```python
INTENTOS_ANTE_CARRERA = 3

def crear_turno(comando, uow, reloj=utc_now) -> Turno:
    for _ in range(INTENTOS_ANTE_CARRERA - 1):
        try:
            return _intentar_crear_turno(comando, uow, reloj)
        except SolapamientoEnLaBase:
            continue  # otra transacción ganó el hueco: ahora el dominio ya la ve
    return _intentar_crear_turno(comando, uow, reloj)
```

`_intentar_crear_turno` es el cuerpo actual, sin cambios, con su `with uow:`. Cuando el repositorio levanta `SolapamientoEnLaBase`, la unidad de trabajo deshace y cierra la sesión (ya lo hace hoy ante cualquier excepción). El intento siguiente abre una sesión nueva; como el ganador **ya confirmó** (PostgreSQL solo devuelve `23P01` después de eso), la validación de dominio lo encuentra y levanta el `ErrorDeSolapamiento` de siempre: con `RN-AG-05`, `RN-AG-08` o los dos, y el `turno_id` del ganador. La capa `api` lo traduce al `409` `application/problem+json` que ya existe. **No se toca `app/api` ni `app/domain`.**

**Clasificación del rechazo (RN-GL-02, D135) y orden de evaluación.** No aparece ninguna clase de rechazo nueva:

| Rechazo | Clase | Estado | Cambia en este change |
|---|---|---|---|
| Fecha sin zona o fuera de UTC (`RN-GL-01`), referencia inválida (`RN-GL-04`), cuerpo mal formado | Validación de entrada, toda junta | `422` | No |
| El turno cruza la medianoche del consultorio (`RN-AG-10d`) | Regla de negocio | `422` | No |
| Solapamiento (`RN-AG-05`, `RN-AG-08`), detectado por el dominio **o por la base y reevaluado** | Regla de negocio, una regla que mira dos recursos | `409` | Solo el segundo camino |

El orden sigue siendo: validación de entrada, RN-AG-10d, solapamiento. La violación de la base es la misma regla de solapamiento detectada más tarde; al reevaluar se recorre el orden completo otra vez, así que si entre un intento y otro cambió otra cosa (por ejemplo, se desactivó el sillón) se informa lo que corresponda.

**Por qué tres intentos.** Uno alcanza para el caso normal. Un segundo choque exige que, entre la reevaluación y el nuevo `INSERT`, otra transacción distinta ocupe otra parte del mismo intervalo: posible, muy raro. Si los tres intentos chocan, `SolapamientoEnLaBase` sube sin traducir y la API responde `500`: no se inventa un código. Es deliberado, porque a esa altura lo más probable es que el dominio y la base no estén de acuerdo (ver «Risks»), y eso es un defecto que conviene ver.

**Alternativas descartadas.**

- *Bloquear el profesional y el sillón con `SELECT ... FOR UPDATE` antes de validar.* Evita la carrera sin reintento, pero DD-04 la consideró y eligió la restricción; además no protege ante un `INSERT` que no pase por el caso de uso.
- *Traducir directo en la capa `api`* un `IntegrityError` a `409`. La API pasaría a conocer SQLAlchemy y el nombre de una restricción, y el `409` saldría sin `turno_id` y con un solo código en el caso doble.
- *Un error de dominio nuevo con código `RN-AG-10c`.* Cambia el contrato (`codigos` nuevos, `conflictos` vacío) para un caso que el cliente no distingue de «llegué tarde».

### I9. Perfil opcional de tests con PostgreSQL — Decisión del autor (D75: que exista, con marcador y en el README) + Propuesta (forma)

- **Marcador `postgres`**, registrado en `pyproject.toml`. La corrida por defecto lo excluye con `-m "not postgres"` en `addopts` (I2). `python -m pytest -m postgres` lo incluye: la opción de la línea de comandos pisa la de `addopts` (V2).
- **Carpeta `tests/postgres/`.** Cada módulo declara `pytestmark = pytest.mark.postgres`.
- **Variable `TEST_DATABASE_URL`.** El `conftest.py` de esa carpeta **redefine el fixture `engine`**. Los fixtures `fabrica_sesiones`, `sesion` y `uow` de `tests/conftest.py`, y las fábricas de `tests/factories.py`, se reutilizan sin tocar porque cuelgan de `engine`.
- **Si PostgreSQL no está disponible, se omite, no falla:** sin `TEST_DATABASE_URL`, o si no se puede conectar, el fixture hace `pytest.skip` con un mensaje que dice qué falta y cómo levantarlo. Con `-ra` el motivo aparece en el resumen.
- **Protección de datos:** si el nombre de la base de `TEST_DATABASE_URL` no termina en `_test`, el fixture **falla** con un mensaje claro. No es «PostgreSQL no disponible», es una configuración que borraría otra base.
- **Aislamiento: esquema nuevo por test.** Antes de cada test el fixture borra y recrea el esquema `public` y aplica las migraciones hasta la última. Es el equivalente al «engine por test» de la suite por defecto, y hace que **el esquema de los tests del perfil salga siempre de las migraciones**, nunca de `create_all`. Son pocos tests; el costo es aceptable.
- **Sin mocks.** Sesiones, repositorio, unidad de trabajo y caso de uso reales.

**Cómo se prueba E11 de forma determinista.** Lanzar dos hilos y esperar que choquen no prueba nada: si uno termina antes de que el otro lea, el segundo es rechazado por el dominio y la restricción nunca se ejercita. La carrera se **fuerza**:

1. El test abre una sesión A, inserta el turno ganador y hace `flush()` **sin confirmar**.
2. En otro hilo, B llama a `crear_turno` con su propia unidad de trabajo. Su validación de dominio no ve el turno de A (no está confirmado) y su `INSERT` queda esperando.
3. El test consulta `pg_stat_activity` desde una tercera conexión hasta ver una sesión esperando un bloqueo (con un tope de 10 segundos; si no aparece, el test falla: significa que la restricción no existe).
4. A confirma. B recibe `23P01`, el repositorio lo traduce, el caso de uso reevalúa y levanta `ErrorDeSolapamiento`.
5. El test verifica los códigos, el `turno_id` del ganador y que en la base hay un solo turno.

Esa secuencia vive en `tests/postgres/carrera.py` y la usan el escenario principal, el de un solo recurso y el de la API (`TestClient` sobre `crear_app(engine)`, que comprueba el `409` `application/problem+json`). Un cuarto test lanza ocho hilos a la vez con una barrera y comprueba el invariante: un ganador, siete `ErrorDeSolapamiento`, un turno en la base. Todas las esperas tienen tope, para que un fallo no cuelgue la corrida.

**Comando exacto del perfil** (va al README). Desde la raíz, `docker compose up -d postgres`. Después, desde `backend/` con el entorno activado:

```
# PowerShell
$env:TEST_DATABASE_URL = "postgresql+psycopg://app:app@localhost:5434/turnos_test"
python -m pytest -m postgres

# bash
TEST_DATABASE_URL=postgresql+psycopg://app:app@localhost:5434/turnos_test python -m pytest -m postgres
```

Los tests corren en el entorno virtual de la máquina, contra el PostgreSQL del contenedor. No hace falta construir la imagen de la API para correrlos.

**Alternativa descartada: Testcontainers.** DD-03 ya la consideró; agrega una dependencia y hace que los tests manejen Docker.

### I10. Docker Compose y Dockerfile — Propuesta

**`docker-compose.yml`** (raíz), con los dos servicios que pide `CHANGES.md`:

```yaml
name: turnos-odontologia

services:
  postgres:
    image: postgres:17.10-bookworm@sha256:9b18b78397054fce88a9552e9d5a3ad5bb7fd258c5b3cc1c5028e46373d6ea8f
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "127.0.0.1:5434:5432"
    volumes:
      - datos_postgres:/var/lib/postgresql/data
      - ./docker/postgres-init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10

  api:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "127.0.0.1:8000:8000"

volumes:
  datos_postgres:
```

- Los puertos se publican solo en `127.0.0.1`: la API no tiene autenticación (DD-14) y la base tiene una clave de prueba.
- `docker/postgres-init/01_base_de_tests.sql` contiene `CREATE DATABASE turnos_test;`. La imagen oficial lo corre **solo la primera vez**, con el volumen vacío. Es un `.sql` y no un `.sh` para que los fines de línea de Windows no lo rompan.
- La `DATABASE_URL` de la API se arma en el propio archivo a partir de las `POSTGRES_*`: las credenciales se escriben una sola vez (I11).
- El servicio se llama `postgres` (`CHANGES.md` y el árbol de `08`), así que ese es el nombre de host en la URL. El ejemplo de `08` dice `@db:`: ver «Contradicciones y huecos».

**`backend/Dockerfile`**, en dos etapas con nombre (regla de `multi-stage-dockerfile`):

- **`builder`**: parte de la imagen de Python fijada en I2, crea un entorno virtual en `/opt/venv`, copia **solo** `pyproject.toml` (para aprovechar la caché de capas) y corre `python -m pip install --group app`. Las dependencias de test no entran en la imagen.
- **`runtime`**: la misma imagen base; copia `/opt/venv`, `alembic.ini` y `app/`; define `PYTHONDONTWRITEBYTECODE=1` y `PYTHONUNBUFFERED=1`; crea un usuario sin privilegios y corre como él (`USER`); declara un `HEALTHCHECK` que pide `http://127.0.0.1:8000/openapi.json` con `urllib` de la biblioteca estándar (la imagen `slim` no trae `curl` y no se agrega un endpoint de salud).
- **Comando de arranque**: `alembic upgrade head`, después `python -m app.infrastructure.db.cargar_seed`, después `uvicorn app.main:crear_app_desde_entorno --factory --host 0.0.0.0 --port 8000`. Va escrito en línea en el `Dockerfile`, sin un script aparte, por los fines de línea.
- **`backend/.dockerignore`**: `.venv/`, `__pycache__/`, `.pytest_cache/`, `tests/`, `.env*`. Ningún secreto ni `.env` entra en la imagen.

**Migrar y cargar el seed al arrancar la API — Propuesta.** Con un solo contenedor de API y datos ficticios, `docker compose up` deja Swagger listo sin pasos manuales. Alternativa: un servicio aparte de un solo uso para migrar; `CHANGES.md` pide solo `api` y `postgres`. Consecuencia de la propuesta: no sirve tal cual para varias réplicas de la API, que no están en el alcance.

### I11. Variables de entorno y `.env.example` — Decisión del autor (D70: nombres de `08` como requisito, definitivos en este change) + Propuesta (cuáles se usan ya)

**Nombres definitivos.** Se confirman sin cambios los once de la tabla de `08` («Variables de entorno»): `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS`, `APP_TIMEZONE`, `PUBLIC_BASE_URL`, `WHATSAPP_MODE`, `MP_ACCESS_TOKEN`, `MP_WEBHOOK_SECRET` y `QUEUE_ENABLED`. Se agregan cuatro que este change necesita:

| Variable | Quién la lee | Valor de prueba |
|---|---|---|
| `DATABASE_URL` | La API (`crear_app_desde_entorno`), Alembic y la carga del seed | `postgresql+psycopg://app:app@postgres:5432/turnos` (dentro de Compose) |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | La imagen oficial de PostgreSQL y `docker-compose.yml` | `app`, `app`, `turnos` |
| `TEST_DATABASE_URL` | Solo el perfil `postgres` de pytest | `postgresql+psycopg://app:app@localhost:5434/turnos_test` |

Las `POSTGRES_*` son los nombres que exige la imagen oficial: no se pueden elegir.

**`.env.example` trae solo lo que algún código lee hoy — Propuesta.** Las tres `POSTGRES_*` como valores, y `DATABASE_URL` y `TEST_DATABASE_URL` como líneas comentadas de referencia para quien corra algo desde su máquina. Las demás variables las agrega el change que empieza a leerlas, igual que las dependencias (D116). Alternativa: listar ya las once; consecuencia, un archivo que promete configuración que ningún código usa. El archivo aclara en su cabecera que todos los valores son de prueba (RN-PR-01).

**Cómo se usa.** Se copia `.env.example` a `.env` en la raíz; Compose lo lee solo. Python **no** lee `.env`: no se agrega una biblioteca para eso. Quien corre el perfil de tests define `TEST_DATABASE_URL` en su terminal (I9).

**`leer_database_url(entorno=os.environ) -> str`** en `app/infrastructure/configuracion.py`. Si `DATABASE_URL` falta o está vacía levanta `ConfiguracionInvalida`, con un mensaje que nombra la variable. **No cae en silencio a SQLite.** Recibe el entorno como parámetro para poder testearla con un diccionario.

**La suite por defecto no lee ninguna variable.** `08` dice «tests: `sqlite+pysqlite:///:memory:`» en la fila de `DATABASE_URL`; se mantiene el criterio del design de C-01 (D18): los tests usan `crear_engine_en_memoria()` y no miran el entorno.

**`APP_TIMEZONE` no se lee en este change — Propuesta.** `08` la describe como «la zona con la que el seed carga `Consultorio.zona_horaria`». El seed de C-01 la tiene escrita (`America/Argentina/Buenos_Aires`) y sus identificadores y datos están documentados en el README. Se deja igual. Alternativa: que la carga del seed la lea; consecuencia, una variable más y un test más para un valor que hoy no cambia.

### I12. Qué base usa la aplicación al arrancar, y la demo de Swagger — Propuesta

Quedan **dos formas de levantar la API**, cada una con su fábrica:

| Fábrica | Base | Para qué | Necesita |
|---|---|---|---|
| `crear_app_demo()` (sin cambios) | SQLite en memoria, con el seed | La demo del README sin instalar nada más; los tests de `tests/api/test_demo.py` | Solo Python |
| `crear_app_desde_entorno()` (nueva) | La de `DATABASE_URL` | La API «de verdad» sobre PostgreSQL; es la que arranca Compose | `DATABASE_URL` |

`crear_app_desde_entorno(entorno=os.environ)` lee la URL (I11), crea el engine con `crear_engine(url)` y devuelve `crear_app(engine)`. **No migra ni carga datos**: eso lo hace el comando de arranque del contenedor (I10), de forma explícita.

`crear_engine(url)` se agrega a `motor.py` con `pool_pre_ping=True`, para que una conexión caída tras reiniciar PostgreSQL no rompa la primera petición.

**Por qué se conserva `crear_app_demo`.** D124 decidió que la demo del primer change usa SQLite en memoria, y la regla dura 6 exige que el repositorio se pueda clonar y probar solo con el README, sin Docker. Sacarla rompería eso y los tests de la demo. El README pasa a mostrar las dos opciones, primero la que no necesita Docker.

**Alternativa.** Una sola fábrica que use PostgreSQL si hay `DATABASE_URL` y SQLite si no. Consecuencia: un error de configuración (variable mal escrita) arranca en silencio con una base en memoria que pierde los datos.

### I13. Carga del seed ficticio en PostgreSQL — Propuesta

- `cargar_demo(sesion)` no cambia: la siguen usando `crear_app_demo` y sus tests.
- **`cargar_demo_si_falta(sesion) -> bool`**: si ya existe el consultorio 1 no hace nada y devuelve `False`; si no, llama a `cargar_demo` y devuelve `True`. Hace que el arranque del contenedor se pueda repetir sin duplicar datos ni fallar.
- **`ajustar_secuencias(sesion)`**: el seed asigna los identificadores a mano (1 a 5) para que el README pueda documentarlos. En PostgreSQL eso **no avanza la secuencia** de la columna `id`, y el primer alta posterior sin identificador explícito chocaría con el 1. Después de cargar, para cada tabla sembrada se ejecuta `SELECT setval(pg_get_serial_sequence('<tabla>', 'id'), (SELECT max(id) FROM <tabla>))`. Solo corre si el dialecto es PostgreSQL; en SQLite no hace falta.
- **`python -m app.infrastructure.db.cargar_seed`**: lee `DATABASE_URL`, abre una sesión, carga si falta, ajusta las secuencias e informa por pantalla qué hizo. Espera una base ya migrada.

Los datos son los mismos de C-01, todos ficticios (RN-PR-01): un consultorio, un profesional, un sillón, cinco prestaciones y tres pacientes. La petición de ejemplo y el recorrido del README valen igual sobre PostgreSQL.

### I14. Contenido nuevo del `README.md` — Propuesta

Se conserva todo lo que hay. Cambia o se agrega:

- **Qué entrega**: suma este change.
- **Requisitos**: Python solo para instalar, testear y probar la demo; Docker Desktop **solo** para la API sobre PostgreSQL y para el perfil opcional.
- **Versiones fijadas**: dos filas (`psycopg[binary]` 3.3.6 y `alembic` 1.20.0) y las dos imágenes.
- **Tests**: el resultado real de la corrida por defecto (cantidad de tests que pasan y cantidad «deselected»), que sale del Apply; sigue diciendo que corre con SQLite en memoria, sin Docker.
- **Sección nueva «Perfil opcional con PostgreSQL»**: qué prueba (INF-1, INF-2, INF-3, E11), cómo levantar la base, el comando de I9 para PowerShell y para bash, el resultado esperado, qué se ve si PostgreSQL no está (tests omitidos) y la tabla escenario → test.
- **Sección nueva «Levantar la API con PostgreSQL»**: copiar `.env.example` a `.env`, `docker compose up --build`, Swagger en el mismo puerto, los mismos identificadores y recorrido, cómo detener (`docker compose down`) y cómo borrar los datos (`docker compose down -v`).
- **Variables de entorno**: la tabla de I11.
- **Migraciones**: cómo aplicarlas y cómo crear una nueva.
- **Límites conocidos**: se quita «no hay control de concurrencia» y «no hay PostgreSQL, Docker ni migraciones»; se agregan los de este design (la equivalencia de INF-1 y la concurrencia solo se prueban en el perfil opcional; el puerto 5434 del host tiene que estar libre; las credenciales del ejemplo son de prueba; sigue sin autenticación).

### I15. Cómo se verifica cada tarea, con Docker apagado o encendido — Propuesta

- Los grupos 1 y 3 de `tasks.md`, y parte del 4 y del 7, se verifican **sin Docker** (suite por defecto).
- Del grupo 2 en adelante hace falta **Docker Desktop en ejecución**. Si no lo está, el Apply **frena y avisa**; no simula resultados ni marca tareas como hechas.
- El RED de un test del perfil `postgres` se demuestra con PostgreSQL levantado: un test omitido no cuenta como RED.
- Las tareas de pura infraestructura (Compose, Dockerfile) llevan su comando de verificación y el resultado esperado escritos en la tarea.

### I16. Commits durante el Apply — Propuesta (continúa el design de C-01, D20)

Se mantiene el último criterio que fijó el autor para C-01: el sub-agente commitea dentro de cada grupo (`test:` al cerrar cada RED, con la salida en rojo en el cuerpo; `feat:` o `chore:` al cerrar cada GREEN; triangulación y refactor en commits propios), **con el ok del autor dado por grupo y por adelantado**, y frena al cerrar el grupo. Mensajes en español, con prefijo y la línea `Co-Authored-By`. Sin `--amend` ni reescritura. La prueba manual en `/docs` (tarea 7.6) la hace el autor, como en C-01. A confirmar por el autor antes del Apply (regla dura 10).

### Skills aplicadas

Reglas compactas tomadas de `.atl/skill-registry.md`, con la KB por encima (regla dura 9):

- `database-migration`: una migración reversible por cambio de esquema; autogenerar y revisar a mano. **No aplican** sus ejemplos en JavaScript ni el patrón de tabla de respaldo.
- `supabase-postgres-best-practices`: `timestamptz`, nombres en minúsculas con guion bajo, índices sobre las claves foráneas que se consultan, restricción parcial solo para los estados activos, transacciones cortas, garantías exclusivas de PostgreSQL verificadas en el perfil opcional. **No aplican** RLS ni lo específico de Supabase. «Agregar restricciones con `NOT VALID` y después validar» no hace falta: la tabla nace vacía. Los roles con privilegios mínimos, opcionales según el registro, quedan fuera.
- `multi-stage-dockerfile`: etapas con nombre, imagen base con versión exacta, manifiesto de dependencias antes que el código, `.dockerignore`, usuario sin privilegios, `HEALTHCHECK`, sin secretos en la imagen.
- `python-testing-patterns`: marcador para la suite opcional, fixtures en `conftest.py`, parametrización para triangular. **No aplican** los mocks de sesión o repositorio, `freezegun` ni los tests asíncronos.
- `fastapi-templates`: inyección por dependencias y traducción de errores en la capa de API, que no cambian. **No aplica** nada asíncrono.

## Contradicciones y huecos encontrados en las fuentes

No se resolvió ninguno en silencio: cada uno tiene una propuesta marcada arriba y queda para que el autor decida. La KB no se tocó.

1. **Nombre de host en `DATABASE_URL`.** `08` da como ejemplo `postgresql+psycopg://app:app@db:5432/turnos`, pero `CHANGES.md` (C-02) y el árbol de `08` llaman `postgres` al servicio. Propuesta: servicio `postgres` y URL con `@postgres:` (I10).
2. **`DATABASE_URL` en los tests.** La misma fila dice «tests: `sqlite+pysqlite:///:memory:`», como si los tests leyeran la variable. El design de C-01 (D18) fijó que no leen ninguna. Propuesta: mantener eso (I11).
3. **Demo de Swagger.** D124 y la Definition of Done de `08` dicen que la demo usa SQLite en memoria; el objetivo de C-02 dice «PostgreSQL como base de ejecución». La KB no dice qué pasa con `crear_app_demo`. Propuesta: conviven (I12).
4. **Versión de PostgreSQL.** «No fijada» en `CLAUDE.md` y en `08`. Propuesta: 17.10 (I2).
5. **D133 e imágenes de Docker.** La política habla de versiones «publicadas» de paquetes. Para una imagen solo se puede saber el último push de la etiqueta, y las etiquetas se vuelven a subir. Propuesta: aplicar la semana al último push y fijar el digest (I2).
6. **`TEST_DATABASE_URL` y las `POSTGRES_*`** no están en la tabla de variables de `08`. Propuesta: agregarlas (I11).
7. **`APP_TIMEZONE`.** `08` dice que el seed la usa; el seed de C-01 no lee ninguna variable. Propuesta: no leerla todavía (I11).
8. **`alembic.ini`.** D137 dice que la configuración de herramientas (pytest) vive en `pyproject.toml`; no dice nada de Alembic. Propuesta: `alembic.ini` (I3).
9. **«A verificar en el change» que este change cierra.** DD-04, RN-AG-10c, la nota de `04` §Turno y D85 dejan pendiente comprobar que la restricción funciona con los estados activos y con `[inicio, fin)`, y que junto con el dominio hace ganar a una sola reserva. Los tests de INF-2, INF-3 y E11 lo comprueban. Después del Apply, el autor debería registrarlo en `10_preguntas_abiertas.md` y quitar esas marcas.
10. **`CHANGES.md`, «Leer antes» de C-02**, no lista D116, D119, D133 ni D137, que condicionan los pins y el modo sincrónico. Se leyeron igual.
11. **README de C-01, «Límites conocidos»**: dice que no hay control de concurrencia, PostgreSQL, Docker ni migraciones. Deja de ser cierto; lo corrige la tarea del README.
12. **Cantidad de tareas.** `CHANGES.md` pide «alrededor de 20»; `tasks.md` tiene 28. No hay una excepción registrada para C-02 (las de C-01 son D123 y D134). Ver «Open Questions».

## Risks / Trade-offs

- **[La equivalencia y la concurrencia solo se prueban con Docker]** → Es el trade-off que DD-03 y DD-04 ya aceptaron. El README lo declara y la verificación final corre el perfil.
- **[El dominio acepta y la base rechaza]** → Si alguna vez el dominio considera libre un horario que la base considera ocupado, los tres intentos chocan y la API responde `500`. Hoy no puede pasar: los dos miran el mismo estado persistido y la misma definición de intervalo. Pasará con la seña si el change que la cree no persiste el vencimiento antes de insertar (D92, RN-GL-05 (a)). Queda anotado para ese change; el `500` es deliberado para que el defecto se vea.
- **[La lista de estados activos está escrita dos veces]**, en el dominio y en la migración `0002` → Los tests de INF-2 e INF-3 recorren los estados del dominio contra la base: si se desalinean, fallan. Agregar un estado activo exige una migración nueva.
- **[Identificadores fijos del seed y secuencias]** → `ajustar_secuencias`, con su test en el perfil (I13).
- **[Migrar al arrancar el contenedor]** → Válido con una sola instancia de la API. Con más de una habría que separar la migración.
- **[El puerto 5434 del host puede estar ocupado]** por otro servicio (se eligió el 5434 y no el 5432 para no chocar con un PostgreSQL local) → `docker compose up` falla con un mensaje claro; el README dice cómo cambiar el mapeo y la URL de tests.
- **[Etiquetas de Docker mutables]** → Se fija el digest (I2). Si Docker Hub retira ese digest, hay que actualizar el pin con un nuevo design.
- **[`alembic` 1.20.0 es una versión menor de un mes]** → Cumple D133. Alternativa verificada: 1.19.2 (2026-09-04).
- **[Reiniciar el esquema por test es lento]** → Pocos tests y solo en el perfil opcional. Si crece, se migra una vez por sesión y se vacían las tablas entre tests.
- **[Carrera entre el test y el hilo en E11]** → El test espera a ver el bloqueo en `pg_stat_activity` antes de confirmar; no usa pausas fijas. Todas las esperas tienen tope.
- **[Convención de nombres sobre modelos de C-01]** → Cambia nombres de restricciones también en SQLite; ningún test los usa. Se comprueba con la suite completa (V8).

## A verificar en el change

Nada de esto se pudo probar en el design (Docker Desktop apagado y el design no instala nada). Cada punto dice antes de qué se verifica.

| N.º | Qué | Antes de |
|---|---|---|
| V1 | `python -m pip install --group test` instala `psycopg`, `psycopg-binary` y `alembic` en Windows con Python 3.13 sin compilar, y los 144 tests siguen en verde | Cerrar el grupo 1 |
| V2 | `python -m pytest -m postgres` pisa el `-m "not postgres"` de `addopts`, y la forma de lista de `addopts` funciona con pytest 9.1.1 | Cerrar el grupo 1 |
| V3 | `docker pull` de las dos referencias `etiqueta@digest` de I2 funciona en esta máquina | Crear `docker-compose.yml` |
| V4 | El script de `/docker-entrypoint-initdb.d` crea `turnos_test` con el montaje de Docker Desktop en Windows | Cerrar el grupo 2 |
| V5 | El usuario de la base puede borrar y recrear el esquema `public`, y eso se lleva la extensión `btree_gist` | Escribir el fixture `engine` de PostgreSQL |
| V6 | La convención de nombres no altera los nombres explícitos ni rompe el `create_all` de SQLite | Generar la migración `0001` |
| V7 | `compare_metadata` devuelve una lista vacía en la última versión: ni los índices GiST de las restricciones ni `alembic_version` aparecen como diferencias. Si aparecen, se filtran por nombre en `env.py` y se anota | Cerrar el grupo 4 y, de nuevo, el 5 |
| V8 | PostgreSQL 17.10 acepta el SQL de I5 tal como está escrito | Cerrar la migración `0002` |
| V9 | Con SQLAlchemy 2.0.54 y psycopg 3.3.6, el `IntegrityError` trae `orig.diag.constraint_name` con el nombre de la restricción y `orig.sqlstate == "23P01"` | Implementar la traducción (I7) |
| V10 | La sesión que espera por la restricción se ve en `pg_stat_activity` con `wait_event_type = 'Lock'` | Escribir `tests/postgres/carrera.py` |
| V11 | Las claves primarias que crea la migración son de tipo serial y `pg_get_serial_sequence` las encuentra | Implementar `ajustar_secuencias` |
| V12 | El `pip` de la imagen `python:3.13.15-slim-bookworm` es 25.1 o superior. Si no, el `Dockerfile` lo actualiza con el mismo comando del README | Cerrar el `Dockerfile` |
| V13 | La restricción funciona con los estados activos y con `[inicio, fin)` (DD-04, `04` §Turno, D85) | Cerrar el grupo 5; en todo caso antes del change de reserva online |
| V14 | La restricción y la validación de dominio, juntas, hacen ganar a una sola de dos reservas simultáneas (RN-AG-10c, D85) | Cerrar el grupo 6; en todo caso antes del change de reserva online |

Si alguna falla, no se improvisa: se vuelve a este design y se le avisa al autor.

## Migration Plan

No hay datos que migrar: la base de PostgreSQL nace vacía y todos los datos son ficticios.

- **Puesta en marcha:** copiar `.env.example` a `.env` y `docker compose up --build`. El contenedor de la API migra, carga el seed si falta y arranca.
- **Vuelta atrás del esquema:** `alembic downgrade base` deja la base sin tablas de la aplicación (INF-1). `docker compose down -v` borra el volumen.
- **Vuelta atrás del change:** quien no usa Docker no depende de nada de esto. Revertir los commits deja el repositorio como en C-01; la reevaluación de I8 no hace nada en SQLite porque el repositorio nunca levanta `SolapamientoEnLaBase` ahí.
- **Changes siguientes:** cada uno que toque un modelo agrega su migración reversible y corre el test de INF-1.

## Open Questions

Ninguna cambia los specs. Las que cambian el enfoque están resueltas arriba como **Propuesta** y listadas para el autor; se repiten acá las dos que conviene cerrar antes del Apply.

1. **Tamaño del change.** `tasks.md` tiene **28 tareas en 8 grupos**, frente a «alrededor de 20». El motivo es que el ciclo RED y GREEN va en tareas separadas, que hay cinco escenarios y que la infraestructura (Compose, Dockerfile, README) suma tareas sin test. Opciones: aceptarlo como excepción registrada, como D134, o sacar del change la convención de nombres (I4, dos tareas) y dejar la fábrica `crear_app_desde_entorno` sin test propio sobre PostgreSQL, cubierta solo por la prueba manual (una tarea menos, peor cobertura). No se recomienda bajar más: lo que queda son los ciclos de los cinco escenarios.
2. **Commits** (I16): si el autor mantiene el criterio de C-01 o prefiere otro para un change de gobernanza ALTO.
