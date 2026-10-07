# Design: crear-turno-sin-solapamientos

## Context

Motivación y alcance: ver `proposal.md`. Requisitos y escenarios: ver `specs/creacion-de-turnos/spec.md`.

Estado de partida (verificado el 2026-10-07): el repositorio **no tiene código de aplicación**. No existen `backend/`, archivo de dependencias ni `README.md` en la raíz; `.gitignore` solo ignora `.claude/settings.local.json`; `openspec/specs/` está vacío. Este change crea todo eso.

Restricciones que mandan (no se reabren): Python 3.11+, FastAPI de la serie 0.115.x y SQLAlchemy de la serie 2.0.x (D133) **sincrónico** (DD-12, D119), pytest; tests sobre SQLite en memoria con `StaticPool` y engine por test, sin mocks de sesión ni de repositorio; dominio sin base de datos y sin imports fuera de la biblioteca estándar; intervalos `[inicio, fin)`; fechas aware en UTC con un único `utc_now()` inyectable; TDD estricto; datos ficticios; sin secretos.

**Cómo leer las etiquetas de este documento**

- **Decisión del autor (Dnnn / DD-nn)**: ya tomada y registrada en `knowledge-base/`. No se discute acá.
- **Propuesta**: elección de este design que el autor todavía no confirmó. Vale para el apply salvo que el autor la cambie antes.
- **A verificar en el change (verificar antes de …)**: comprobación técnica pendiente, con el momento antes del cual tiene que estar hecha.

Las 19 decisiones que el relevamiento (`docs/explore/crear-turno-sin-solapamientos.md`, sección 8) dejó para el design están resueltas en D1..D19 de «Decisions», con la misma numeración.

**Revisión del 2026-10-07 (segunda ronda del autor, D133 a D138).** Este documento reemplaza al primer borrador en cuatro puntos: los pins (D1: series y antigüedad mínima, D133), el archivo de dependencias (D1 y D17: `backend/pyproject.toml`, D137), el modelo de errores (D4, D6, D7 y D12: validación de entrada toda junta y reglas de negocio de a una, D135) y el paciente, que solo puede ser `inexistente` (D10, D136). La numeración «D1..D19» de este documento es la del design; «D122..D139» son decisiones del autor registradas en `knowledge-base/10_preguntas_abiertas.md`. **Confirmaciones del 2026-10-07 (D139):** el autor confirmó la lectura de E4 (D4, D6), RN-AG-10d como regla de negocio (D6), el `type` único de la validación de entrada (D4) y Python 3.11 a 3.13 con `pydantic 2.11.10` (D1); esos puntos dejaron de ser Propuesta.

## Goals / Non-Goals

**Goals:**

- Que el apply no necesite tomar ninguna decisión de diseño: nombres, formas, comandos y casos límite quedan fijados acá.
- Un test automatizado por cada escenario del spec (E1..E7 y E12), más los tests transversales que pide la Definition of Done (E8 de `Intervalo`, ida y vuelta de fechas, imports del dominio, guard de fechas).
- Que el repo se clone y los tests corran siguiendo solo el `README.md`, sin Docker, PostgreSQL ni Redis.
- Que `POST /turnos` se pueda probar a mano desde `/docs` con datos ficticios de identificadores conocidos.

**Non-goals:**

Además de lo listado en «Fuera de alcance» de `proposal.md`, este design **no resuelve**:

- **Concurrencia.** Dos peticiones simultáneas pueden crear dos turnos solapados (RN-AG-10c, E11). Se resuelve en C-02 con la restricción de exclusión de PostgreSQL.
- **Claves foráneas en SQLite.** No se activa `PRAGMA foreign_keys`: las referencias las valida el caso de uso (RN-GL-04). La base las hace cumplir desde C-02.
- **Conversión de hora local.** La API no convierte horas de Buenos Aires a UTC: el cliente envía UTC y lo demás se rechaza (RN-GL-01).
- **Turnos en el pasado.** Ninguna regla de las fuentes los prohíbe; se aceptan.
- **Traducción de los mensajes de validación de Pydantic.** Se adapta la forma del error, no el texto.
- **Fijar las dependencias transitivas** (archivo de bloqueo). Ver D1.
- **Empaquetar el backend**: `pyproject.toml` no declara un proyecto instalable ni un backend de construcción (D1, D137).
- **Variables de entorno, `.env.example`, `Dockerfile` y el marcador `postgres` de pytest**: los crea C-02.
- **Cabecera `Location`** en el `201`: no hay `GET /turnos/{id}` al que apuntar.
- **Tests de capas para `application`, `infrastructure` y `api`**: el test de imports cubre solo `backend/app/domain`, que es lo que pide D70.

## Decisions

### D1. Archivo único de dependencias y versiones exactas — Decisión del autor (D133, D137, D139: pin de Pydantic y rango de Python) + Propuesta (forma de declararlas)

**Archivo:** `backend/pyproject.toml` (decisión del autor, D137). Es el **único** lugar donde se declaran dependencias, de ejecución y de test, y donde vive la configuración de pytest (D17). No hay `requirements.txt` ni `pytest.ini`.

**Política de pins (decisión del autor, D133):** SQLAlchemy, la última de la serie **2.0.x** (no la 2.1); FastAPI, la última de la serie **0.115.x**; Pydantic, una compatible con ese FastAPI; y para todos los paquetes, **ninguna versión publicada el 2026-09-30 o después** (la última semana contada desde el 2026-10-07). Si la más nueva es tan reciente, se toma la más nueva anterior dentro de la serie permitida.

**Cómo se declaran las dependencias — Propuesta.** Con **grupos de dependencias** (tabla `[dependency-groups]`, el mecanismo estándar de `pyproject.toml` para un proyecto que no se empaqueta), sin tabla `[project]` y sin `[build-system]`:

- `app`: lo que necesita la API para correr (incluida la demo con `uvicorn`).
- `test`: incluye `app` y agrega lo que solo usan los tests.

Se instala desde `backend/` con **`python -m pip install --group test`**. `pip` lee los grupos del `pyproject.toml` del directorio actual e instala esas dependencias; **no construye ni instala el proyecto**.

**Por qué así y no de otra forma:**

- *Alternativa descartada: tabla `[project]` con `dependencies` y un extra `test`, instalando con `pip install -e ".[test]"`.* Obliga a construir el proyecto: `pip` descarga un backend de construcción que no estaría fijado, y con `app/` y `tests/` como carpetas hermanas dentro de `backend/` el descubrimiento automático de paquetes necesita configuración extra. Es justo la complejidad de empaquetado que D137 pide no introducir.
- *Alternativa descartada: `requirements.txt`* (la del primer borrador). El autor decidió `pyproject.toml` (D137).
- **Límite de la propuesta:** `--group` existe desde `pip` 25.1 (publicado el 2025-04-26, según el índice de PyPI). Un entorno virtual recién creado puede traer un `pip` más viejo (depende de la versión de Python), así que el README hace actualizar `pip` antes de instalar. `pip` es la herramienta de instalación, no una dependencia del proyecto: no se fija.
- **Consecuencia:** sin tabla `[project]` no hay `requires-python` que `pip` haga cumplir; el rango de Python admitido lo dice el README (más abajo).

**Contenido exacto del archivo** (incluye la configuración de pytest de D17):

```toml
# backend/pyproject.toml
# Archivo único de dependencias del backend (D116, D137). Versiones exactas.
# Consultadas en PyPI el 2026-10-07; ninguna publicada el 2026-09-30 o después (D133).
# No es un paquete instalable: no tiene [project] ni [build-system].
# Instalar, desde backend/:  python -m pip install --group test
# Cada change agrega sus dependencias acá, con versión exacta, en su design.

[dependency-groups]
app = [
    "fastapi==0.115.14",
    "starlette==0.46.2",
    "pydantic==2.11.10",
    "SQLAlchemy==2.0.54",
    "uvicorn==0.54.0",
    "tzdata==2026.4",
]
test = [
    {include-group = "app"},
    "pytest==9.1.1",
    "httpx==0.28.1",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-ra --strict-markers"
```

**Pins.** Fuente de todos los datos: la API JSON de PyPI, consultada el **2026-10-07**. `https://pypi.org/pypi/<paquete>/json` da todas las versiones con su fecha de publicación (`releases[versión][].upload_time`); `https://pypi.org/pypi/<paquete>/<versión>/json` da `requires_python` y `requires_dist` de esa versión.

| Paquete | Versión | Publicada | Python requerido | Fuente | Por qué esa versión |
|---|---|---|---|---|---|
| `fastapi` | 0.115.14 | 2025-06-26 | `>=3.8` | https://pypi.org/pypi/fastapi/0.115.14/json | La última de la serie 0.115.x (D133). La serie va de 0.115.0 (2024-09-17) a 0.115.14 |
| `starlette` | 0.46.2 | 2025-04-13 | `>=3.9` | https://pypi.org/pypi/starlette/0.46.2/json | La más nueva **dentro del rango que admite `fastapi 0.115.14`** (`starlette<0.47.0,>=0.40.0`). La siguiente, 0.47.0 (2025-05-29), queda fuera. Se fija aunque sea transitiva porque trae el `TestClient` |
| `pydantic` | 2.11.10 | 2025-10-04 | `>=3.9` | https://pypi.org/pypi/pydantic/2.11.10/json | **Confirmada por el autor (2026-10-07, D139).** La última de la serie 2.11, que era la vigente cuando se publicó `fastapi 0.115.14`. Ver «Por qué Pydantic 2.11 y no la última» |
| `pydantic-core` | 2.33.2 | 2025-04-23 | `>=3.9` | https://pypi.org/pypi/pydantic-core/2.33.2/json | No se declara en el archivo: `pydantic 2.11.10` la exige con versión exacta (`pydantic-core==2.33.2`) y `pip` la instala sola |
| `SQLAlchemy` | 2.0.54 | 2026-09-15 | `>=3.7` | https://pypi.org/pypi/sqlalchemy/2.0.54/json | La última de la serie 2.0.x (D133). La serie 2.1 (2.1.0 del 2026-09-24 a 2.1.4 del 2026-10-07) queda excluida por decisión del autor |
| `uvicorn` | 0.54.0 | 2026-09-25 | `>=3.10` | https://pypi.org/pypi/uvicorn/0.54.0/json | La última publicada, y es anterior al 2026-09-30. Servidor de la demo; sin el extra `standard` |
| `tzdata` | 2026.4 | 2026-09-12 | `>=2` | https://pypi.org/pypi/tzdata/2026.4/json | La última, 2026.5, es del 2026-10-03: cae dentro de la última semana, así que se toma la anterior. Es el único pin que decide solo la regla de la semana |
| `pytest` | 9.1.1 | 2026-06-19 | `>=3.10` | https://pypi.org/pypi/pytest/9.1.1/json | La última publicada |
| `httpx` | 0.28.1 | 2024-12-06 | `>=3.8` | https://pypi.org/pypi/httpx/0.28.1/json | La última publicada; entra en el rango que pide el `TestClient` de `starlette 0.46.2` |

**Compatibilidad verificada con los metadatos de PyPI (`requires_dist`, `requires_python` y la lista de archivos de cada versión):**

- `fastapi 0.115.14` exige `starlette<0.47.0,>=0.40.0`, `pydantic!=1.8,!=1.8.1,!=2.0.0,!=2.0.1,!=2.1.0,<3.0.0,>=1.7.4` y `typing-extensions>=4.8.0`. `starlette 0.46.2` y `pydantic 2.11.10` cumplen. No exige nada más: **no trae `opentelemetry`** (la nota del primer borrador era de `fastapi 0.142.4` y se elimina).
- `starlette 0.46.2` exige `anyio<5,>=3.6.2`; su extra `full` pide `httpx<0.29.0,>=0.27.0`, que es el rango del `TestClient`: `httpx 0.28.1` cumple. No aparece `httpx2` (también era de la versión nueva; la nota se elimina).
- `pydantic 2.11.10` exige `pydantic-core==2.33.2`, `annotated-types>=0.6.0`, `typing-extensions>=4.12.2` y `typing-inspection>=0.4.0`. `pydantic-core 2.33.2` publica binarios para Windows de 64 bits en CPython 3.9 a 3.13, **no para 3.14**.
- `SQLAlchemy 2.0.54` exige `typing-extensions>=4.6.0` y, en las arquitecturas habituales (entre ellas `x86_64` y `AMD64`), `greenlet>=1`. Publica binarios para Windows de 64 bits en CPython 3.8 a 3.14. `greenlet` se instala sola; el proyecto no usa nada asíncrono.
- `uvicorn 0.54.0` exige `click>=7.0` y `h11>=0.8`. `pytest 9.1.1` exige `pluggy<2,>=1.5`, `iniconfig>=1.0.1`, `packaging>=22`, `pygments>=2.7.2` y, en Windows, `colorama>=0.4`. `httpx 0.28.1` exige `anyio`, `certifi`, `httpcore==1.*` e `idna`.
- No hay rangos en conflicto entre los ocho paquetes declarados: los únicos compartidos son `typing-extensions` (mínimos 4.6.0, 4.8.0 y 4.12.2, sin tope) y `anyio` (`<5,>=3.6.2` y sin rango).
- No entra nada del lado asíncrono de la base (`aiosqlite`, `pytest-asyncio`) ni Alembic.

**Python admitido — Confirmado por el autor (2026-10-07, D139; consecuencia de D133).** La más restrictiva hacia abajo es `uvicorn` y `pytest` (`>=3.10`), por debajo del mínimo del proyecto (3.11). Hacia arriba, el límite lo pone `pydantic-core 2.33.2`, que no tiene binario para Python 3.14: ahí `pip` intentaría compilarlo y haría falta un compilador de Rust. Por eso **este change se instala con Python 3.11, 3.12 o 3.13**, y el README lo dice. Sigue cumpliendo «Python 3.11+» de la KB como mínimo, pero **no admite 3.14**; en la máquina del autor hay 3.12, 3.13 y 3.14, y el lanzador `py` usa 3.14 por defecto, así que el README indica crear el entorno con `py -3.13 -m venv .venv`. `fastapi 0.115.14`, `starlette 0.46.2` y `pydantic 2.11.10` declaran soporte hasta 3.13 en sus clasificadores.

**Por qué Pydantic 2.11 y no la última — Confirmado por el autor (2026-10-07, D139).** El rango de `fastapi 0.115.14` (`<3.0.0`) admite también `pydantic 2.13.5` (2026-08-28, anterior a la última semana), que además sí tiene binarios para Python 3.14. No se elige porque el rango de los metadatos es solo un tope formal: las notas de la versión 0.118.1 de FastAPI (2025-10-08, https://github.com/fastapi/fastapi/releases/tag/0.118.1) dicen «Ensure compatibility with Pydantic 2.12.0», es decir, hizo falta un cambio en FastAPI **posterior a la serie 0.115** para funcionar con Pydantic 2.12 en adelante. La serie 2.11 es la que existía cuando se publicó `fastapi 0.115.14`. El autor confirmó la 2.11.10 (D139). La alternativa era la 2.13.5 (para poder usar Python 3.14): un cambio de una línea, con `pydantic-core==2.46.5`, que haría más importante la verificación V1.

**Lo que no se pudo verificar desde los metadatos** (todo queda como «A verificar en el change», más abajo):

- No se instaló nada (este paso es solo de planificación): la instalación real en un entorno nuevo está sin probar, y también el comando `python -m pip install --group test`.
- `uvicorn 0.54.0`, `pytest 9.1.1` y `SQLAlchemy 2.0.54` son de 2026 y conviven con un `fastapi` y un `starlette` de 2025. Los metadatos no declaran ningún conflicto, pero no prueban que funcionen juntos.
- Que `pytest 9.1.1` lee la tabla `[tool.pytest.ini_options]` no surge de los metadatos; es el mecanismo documentado de pytest desde hace varias versiones mayores.
- `httpx 0.28.1` declara clasificadores hasta Python 3.12 (su `requires_python` es `>=3.8`, sin tope).

**Dependencias transitivas — Propuesta (límite de D133).** No se fijan: `pip` las resuelve dentro de los rangos que declaran los paquetes (`anyio`, `typing-extensions`, `annotated-types`, `typing-inspection`, `greenlet`, `click`, `h11`, `httpcore`, `certifi`, `idna`, `pluggy`, `iniconfig`, `packaging`, `pygments`, `colorama`). Dos consecuencias que el autor debe conocer: (1) dos clones en fechas distintas pueden recibir versiones transitivas distintas; (2) **la regla de «ninguna versión de la última semana» se garantiza para los ocho paquetes declarados y para `pydantic-core`, no para las transitivas**, que `pip` elige el día de la instalación. Fijarlas también es posible en el mismo archivo (un tercer grupo), sin crear un archivo de bloqueo, pero son unos quince pins más que habría que consultar y mantener: no se hace sin que el autor lo pida. El README lista los ocho pins.

### D2. Directorios — Decisión del autor (D122)

Código en `backend/app`, tests en `backend/tests`, `backend/pyproject.toml` (D137) y `README.md` en la raíz.

**Por qué `backend/` y no `src/`:** la estructura mínima de la consigna muestra `src/` y `tests/` y aclara que los nombres pueden variar. El frontend de React llega en la fase 3 como carpeta hermana (`frontend/`); con una raíz `backend/` los dos quedan separados desde el primer día y no hay que mover nada después. `08_arquitectura_propuesta.md` ya usaba esa estructura. La correspondencia con la consigna es directa: `src/` → `backend/app/`, `tests/` → `backend/tests/`. El README lo dice.

Árbol que crea este change (todas las carpetas de `app` y de `tests` llevan `__init__.py`):

```
README.md
.gitignore                         (se amplía, D18)
backend/
├── pyproject.toml                 dependencias y configuración de pytest (D1, D17)
├── app/
│   ├── main.py                    crear_app, crear_app_demo (D3)
│   ├── domain/
│   │   ├── tiempo.py              UTC, Reloj, utc_now, exigir_utc
│   │   ├── errors.py              errores con código RN, Conflicto, ReferenciaInvalida, EntradaInvalida
│   │   ├── agenda/
│   │   │   ├── intervalo.py       Intervalo
│   │   │   ├── solapamiento.py    TurnoOcupado, detectar_conflictos
│   │   │   └── recursos.py        Paciente, Prestacion, Profesional, Sillon (datos mínimos)
│   │   └── turnos/
│   │       ├── estados.py         EstadoTurno, ESTADOS_ACTIVOS
│   │       └── turno.py           Turno
│   ├── application/
│   │   ├── puertos.py             RepositorioAgenda, UnidadDeTrabajo (protocolos)
│   │   └── crear_turno.py         CrearTurnoComando, crear_turno
│   ├── infrastructure/
│   │   ├── db/
│   │   │   ├── tipos.py           FechaHoraUTC (D13)
│   │   │   ├── modelos.py         Base y los seis modelos
│   │   │   ├── motor.py           crear_engine_en_memoria (D12)
│   │   │   └── seed_demo.py       cargar_demo (D19)
│   │   ├── repositories/
│   │   │   └── agenda.py          RepositorioAgendaSqlAlchemy
│   │   └── unidad_de_trabajo.py   UnidadDeTrabajoSqlAlchemy
│   └── api/
│       ├── deps.py                get_uow, get_reloj
│       ├── esquemas.py            CrearTurnoEntrada, TurnoSalida, Problema
│       ├── errores.py             registrar_manejadores (D4)
│       └── routers/
│           └── turnos.py          POST /turnos
└── tests/
    ├── conftest.py                engine, fabrica_sesiones, sesion, uow, RELOJ_FIJO (D12)
    ├── factories.py               (D19)
    ├── unit/                      sin base de datos
    ├── integration/               caso de uso y repositorio sobre SQLite en memoria
    └── api/                       TestClient
```

### D3. Cómo se levanta la API para Swagger — Decisión del autor (D124) + Propuesta (comando y módulos)

- `app/main.py` expone dos funciones y **ninguna variable `app` a nivel de módulo** (importar el módulo no crea ninguna base):
  - `crear_app(engine: Engine) -> FastAPI`: crea la aplicación, guarda `app.state.fabrica_sesiones = sessionmaker(bind=engine, expire_on_commit=False)`, incluye el router de turnos y llama a `registrar_manejadores(app)`. La usan los tests de API con el engine del test.
  - `crear_app_demo() -> FastAPI`: `crear_engine_en_memoria()`, `Base.metadata.create_all(engine)`, `cargar_demo(...)` y devuelve `crear_app(engine)`.
- **Comando**, desde `backend/`: `python -m uvicorn app.main:crear_app_demo --factory`. Swagger queda en `http://127.0.0.1:8000/docs`. Sin `--reload`.
- La demo usa SQLite en memoria: cada arranque parte de los mismos datos y un reinicio borra los turnos creados. No hay endpoints de lectura; los identificadores son fijos (D19) y están en el README con un ejemplo de petición.
- **Alternativa descartada:** un archivo SQLite en disco (dejaría datos entre corridas y un archivo que ignorar) y una variable `app` global (crearía la base de demo cada vez que un test importa `app.main`).
- **Límite:** una sola conexión compartida; la demo es para un usuario probando a mano, no para peticiones simultáneas.

**A verificar en el change** (verificar antes de escribir el README): que `uvicorn 0.54.0` sirve la aplicación de `fastapi 0.115.14`, acepta `--factory` con ese comando y que `/docs` carga.

### D4. Contrato HTTP — Decisión del autor (D73, D127, D128, D129, D135, D136) + Propuesta (nombres de campos, textos y los demás valores de `type`; el `type` único de la validación de entrada está confirmado, D139)

Esta sección se puede leer sola. Todos los datos de los ejemplos son ficticios y todos los horarios están en UTC.

#### Petición

`POST /turnos`, sin autenticación (DD-14), `Content-Type: application/json`. Esquema `CrearTurnoEntrada`.

| Campo | Tipo | Obligatorio | Qué es |
|---|---|---|---|
| `paciente_id` | entero | sí | Paciente al que se le da el turno |
| `prestacion_id` | entero | sí | Prestación; de ella sale la duración del turno (RN-AG-02) |
| `inicio` | fecha-hora ISO 8601 | sí | Comienzo del turno, **con zona y en UTC**: `2026-11-02T13:00:00Z` o `2026-11-02T13:00:00+00:00`. Sin zona o con otro desfase se rechaza (`RN-GL-01`) |
| `profesional_id` | entero o `null` | no | Profesional que atiende. Si falta, el único activo del consultorio (RN-AG-14) |
| `sillon_id` | entero o `null` | no | Sillón que se ocupa. Si falta, el único activo del consultorio (RN-AG-14) |

No se aceptan otros campos (`extra="forbid"`): mandar `duracion_minutos`, `fin` o `consultorio_id` es un cuerpo mal formado. La duración sale de la prestación y el consultorio, del profesional (D126).

Ejemplo:

```json
{"paciente_id": 1, "prestacion_id": 1, "inicio": "2026-11-02T13:00:00Z"}
```

#### Respuesta `201 Created`

`Content-Type: application/json`. Esquema `TurnoSalida`. Sin cabecera `Location` (no hay `GET /turnos/{id}`).

| Campo | Tipo | Qué es |
|---|---|---|
| `id` | entero | Identificador del turno creado |
| `consultorio_id` | entero | Consultorio del turno: el del profesional (D126) |
| `paciente_id` | entero | El de la petición |
| `profesional_id` | entero | El de la petición, o el único activo si no se indicó |
| `sillon_id` | entero | El de la petición, o el único activo si no se indicó |
| `prestacion_id` | entero | El de la petición |
| `inicio` | fecha-hora UTC | El de la petición |
| `fin` | fecha-hora UTC | `inicio` + duración de la prestación (RN-AG-02) |
| `duracion_minutos` | entero | Duración de la prestación al crear el turno |
| `estado` | texto | Siempre `reservado` en este change |
| `creado_en` | fecha-hora UTC | Momento de la creación, tomado del reloj inyectable |

```json
{
  "id": 1,
  "consultorio_id": 1,
  "paciente_id": 1,
  "profesional_id": 1,
  "sillon_id": 1,
  "prestacion_id": 1,
  "inicio": "2026-11-02T13:00:00Z",
  "fin": "2026-11-02T13:30:00Z",
  "duracion_minutos": 30,
  "estado": "reservado",
  "creado_en": "2026-10-07T12:00:00Z"
}
```

Las fechas salen aware en UTC. Los tests las comparan **como fechas** (parseando el texto), no como cadenas, para no depender de si el serializador escribe `Z` o `+00:00`.

#### Errores: forma común

Todo error responde `Content-Type: application/problem+json` (RFC 7807) con estos campos, **siempre presentes**:

| Campo | Tipo | Qué es |
|---|---|---|
| `type` | texto | Clase del problema, como URI relativa. Tres valores en este change: `/errores/solapamiento-turno`, `/errores/intervalo-invalido`, `/errores/entrada-invalida` |
| `title` | texto | Nombre corto de la clase, fijo para cada `type` |
| `status` | entero | El mismo estado HTTP de la respuesta |
| `detail` | texto | Explicación en español de este caso concreto |
| `instance` | texto | La ruta de la petición: `/turnos` |
| `codigos` | lista de textos | Códigos de las reglas que fallaron (RN-GL-02). Vacía solo si el cuerpo está mal formado |

Según el `type` se agregan listas de detalle:

| `type` | Listas de detalle (siempre presentes en ese `type`, pueden estar vacías) |
|---|---|
| `/errores/solapamiento-turno` | `conflictos`: `{codigo, recurso, recurso_id, turno_id}` |
| `/errores/intervalo-invalido` | ninguna |
| `/errores/entrada-invalida` | `referencias`: `{recurso, recurso_id, motivo}` · `errores`: `{campo, codigo, mensaje}` |

#### Errores: los siete casos

Hay **dos clases de rechazo** (RN-GL-02, D135; el detalle está en D6):

- **Validación de entrada**: se informa **todo junto** en un único `422` de `type` `/errores/entrada-invalida`.
- **Regla de negocio**: solo se evalúa si la entrada es válida, y **de a una**: primero RN-AG-10d, después el solapamiento.

| # | Situación | Clase | Estado | `type` | `codigos` |
|---|---|---|---|---|---|
| 1 | Solapamiento con un recurso (E2, E3, E7) | Regla de negocio | `409` | `/errores/solapamiento-turno` | `["RN-AG-05"]` o `["RN-AG-08"]` |
| 2 | Solapamiento con los dos recursos (E4) | Regla de negocio | `409` | `/errores/solapamiento-turno` | `["RN-AG-05", "RN-AG-08"]` |
| 3 | Referencias inválidas (E12) | Validación de entrada | `422` | `/errores/entrada-invalida` | `["RN-GL-04"]` |
| 4 | `inicio` sin zona o con desfase distinto de UTC | Validación de entrada | `422` | `/errores/entrada-invalida` | `["RN-GL-01"]` |
| 5 | Las dos anteriores en la misma petición | Validación de entrada | `422` | `/errores/entrada-invalida` | `["RN-GL-01", "RN-GL-04"]` |
| 6 | Cuerpo mal formado (campo ausente, tipo erróneo, campo de más, JSON roto) | Validación de entrada | `422` | `/errores/entrada-invalida` | `[]` |
| 7 | El turno cruza la medianoche del consultorio | Regla de negocio (confirmada por el autor, D139) | `422` | `/errores/intervalo-invalido` | `["RN-AG-10d"]` |

> **Lectura confirmada por el autor (2026-10-07, D139; E4 no cambia).** «De a una» (D135) significa que las reglas de negocio no se acumulan entre sí ni con los errores de validación de entrada. El control de solapamiento se toma como **una sola regla de negocio que mira dos recursos**: por eso el caso 2 sigue informando los dos códigos, `RN-AG-05` y `RN-AG-08`, con un `Conflicto` por recurso en un único `409`, exactamente como dicen RN-AG-08, D129 y el escenario E4. Un solo código también ahí habría obligado a cambiar RN-AG-08, E4, D129 y los tests de E4; el autor no lo pidió.

**Caso 1 — `409`, solapamiento con un recurso** (E2: el profesional 1 ya tiene el turno 7 en ese horario; el sillón pedido está libre):

```json
{
  "type": "/errores/solapamiento-turno",
  "title": "Turno solapado",
  "status": 409,
  "detail": "El profesional ya tiene un turno activo en ese horario.",
  "instance": "/turnos",
  "codigos": ["RN-AG-05"],
  "conflictos": [
    {"codigo": "RN-AG-05", "recurso": "profesional", "recurso_id": 1, "turno_id": 7}
  ]
}
```

**Caso 2 — `409`, solapamiento con los dos recursos** (E4; es el ejemplo de `08_arquitectura_propuesta.md`). Un `Conflicto` por recurso, primero el profesional; si un recurso choca con varios turnos, lleva el que empieza primero (D129):

```json
{
  "type": "/errores/solapamiento-turno",
  "title": "Turno solapado",
  "status": 409,
  "detail": "El profesional y el sillón ya tienen un turno activo en ese horario.",
  "instance": "/turnos",
  "codigos": ["RN-AG-05", "RN-AG-08"],
  "conflictos": [
    {"codigo": "RN-AG-05", "recurso": "profesional", "recurso_id": 1, "turno_id": 7},
    {"codigo": "RN-AG-08", "recurso": "sillon", "recurso_id": 1, "turno_id": 7}
  ]
}
```

**Caso 3 — `422`, referencias inválidas** (E12: no existe la prestación 999 y el sillón 2 está inactivo). Un solo código aunque haya varias referencias (D127):

```json
{
  "type": "/errores/entrada-invalida",
  "title": "Entrada inválida",
  "status": 422,
  "detail": "La petición tiene 2 problemas de entrada: prestacion 999 (inexistente); sillon 2 (inactivo).",
  "instance": "/turnos",
  "codigos": ["RN-GL-04"],
  "referencias": [
    {"recurso": "prestacion", "recurso_id": 999, "motivo": "inexistente"},
    {"recurso": "sillon", "recurso_id": 2, "motivo": "inactivo"}
  ],
  "errores": []
}
```

Valores de `motivo`: `inexistente` (no existe o es de otro consultorio, D126), `inactivo` (solo prestación, profesional y sillón: **un paciente solo puede ser `inexistente`**, D136), `ninguno_activo` y `varios_activos` (el recurso se omitió y no hay uno solo activo, RN-AG-14; en ese caso `recurso_id` es `null`).

**Caso 4 — `422`, fecha sin zona o fuera de UTC** (se envió `"inicio": "2026-11-02T10:00:00-03:00"`):

```json
{
  "type": "/errores/entrada-invalida",
  "title": "Entrada inválida",
  "status": 422,
  "detail": "La petición tiene 1 problema de entrada: inicio debe tener zona y estar en UTC.",
  "instance": "/turnos",
  "codigos": ["RN-GL-01"],
  "referencias": [],
  "errores": [
    {"campo": "inicio", "codigo": "RN-GL-01", "mensaje": "La fecha y hora debe tener zona y estar en UTC, por ejemplo 2026-11-02T13:00:00Z."}
  ]
}
```

**Caso 5 — `422` combinado** (la misma petición trae `"inicio": "2026-11-02T10:00:00"`, sin zona, y `"prestacion_id": 999`). **Un** `422` con los dos códigos, en orden estable (`RN-GL-01`, después `RN-GL-04`):

```json
{
  "type": "/errores/entrada-invalida",
  "title": "Entrada inválida",
  "status": 422,
  "detail": "La petición tiene 2 problemas de entrada: inicio debe tener zona y estar en UTC; prestacion 999 (inexistente).",
  "instance": "/turnos",
  "codigos": ["RN-GL-01", "RN-GL-04"],
  "referencias": [
    {"recurso": "prestacion", "recurso_id": 999, "motivo": "inexistente"}
  ],
  "errores": [
    {"campo": "inicio", "codigo": "RN-GL-01", "mensaje": "La fecha y hora debe tener zona y estar en UTC, por ejemplo 2026-11-02T13:00:00Z."}
  ]
}
```

**Caso 6 — `422`, cuerpo mal formado** (falta `inicio` y sobra `duracion_minutos`). Sin código RN: no es una regla, es que no se pudo leer la petición. `mensaje` es el texto de Pydantic, sin traducir:

```json
{
  "type": "/errores/entrada-invalida",
  "title": "Entrada inválida",
  "status": 422,
  "detail": "La petición tiene 2 problemas de entrada: el cuerpo no tiene el formato esperado.",
  "instance": "/turnos",
  "codigos": [],
  "referencias": [],
  "errores": [
    {"campo": "inicio", "codigo": null, "mensaje": "Field required"},
    {"campo": "duracion_minutos", "codigo": null, "mensaje": "Extra inputs are not permitted"}
  ]
}
```

**Límite del caso 6 (Propuesta, D135):** si el cuerpo no se puede leer como petición, no hay comando sobre el que evaluar referencias ni fecha, así que el `422` lleva **todos los errores de formato juntos** y nada más. Es la misma regla general: lo que no se puede evaluar porque otro dato es inválido no se informa. Corregido el formato, la petición siguiente informa el resto.

**Caso 7 — `422`, el turno cruza la medianoche del consultorio** (`"inicio": "2026-11-03T02:45:00Z"` con una prestación de 30 minutos: de 23:45 a 00:15 en Buenos Aires). Es una regla de negocio: se informa sola, y no se evalúa el solapamiento:

```json
{
  "type": "/errores/intervalo-invalido",
  "title": "Intervalo inválido",
  "status": 422,
  "detail": "El turno no puede cruzar la medianoche del consultorio.",
  "instance": "/turnos",
  "codigos": ["RN-AG-10d"]
}
```

El estado `422` de este caso es el del mapeo de `08_arquitectura_propuesta.md` y no se cambia: el estado HTTP no define la clase del rechazo.

#### Cómo se arma en el código

Solo `app/api` conoce los códigos HTTP. `registrar_manejadores(app)` (en `app/api/errores.py`) registra dos manejadores:

1. Uno para `ErrorDeDominio`: busca la clase del error en una tabla `{clase: (estado, type, title)}` con tres entradas (`ErrorDeSolapamiento` → `409`; `IntervaloInvalido` → `422`; `EntradaInvalida` → `422`) y arma el cuerpo con `error.codigos`, `error.mensaje` como `detail` y las listas de detalle de ese `type`. Para `EntradaInvalida`, cada `RecursoNoEncontrado` que agrupa aporta sus `referencias` y cada `FechaNoUTC` aporta un elemento de `errores` con su `campo` y su código. Un `ErrorDeDominio` que no esté en la tabla es un error de programación: se deja subir (500), no se inventa un estado.
2. Uno para `RequestValidationError` (el `422` automático de FastAPI/Pydantic, que por defecto responde `{"detail": [...]}` en `application/json` y no cumple el contrato): arma el cuerpo del caso 6. Cada elemento de `errores` lleva `campo` (la ubicación de Pydantic sin el prefijo `body`, unida con puntos; `null` si el error es del cuerpo entero, como un JSON roto), `codigo` `null` y `mensaje`.

El router declara en OpenAPI las respuestas `409` y `422` con el esquema `Problema` (campos comunes más `conflictos`, `referencias` y `errores` opcionales) para que `/docs` muestre el contrato real, y un ejemplo de petición con los identificadores de la demo.

**Cambio respecto de la KB — Confirmado por el autor (2026-10-07, D139).** `08_arquitectura_propuesta.md` proponía para E12 el `type` `/errores/recurso-no-encontrado` con título «Recurso no encontrado», y el primer borrador de este design tenía un `type` por situación. Con D135 un mismo `422` puede reunir una fecha inválida y referencias inválidas, así que se usa **un único `type` para toda la validación de entrada**. `codigos` sigue diciendo qué regla falló (`RN-GL-04` para E12), que es lo que verifican los tests. `08` quedó actualizado.

**A verificar en el change** (verificar antes de dar por cerradas las pruebas de API): que declarar la respuesta `422` en el router reemplaza en `/docs` al esquema `HTTPValidationError` que FastAPI pone por defecto. Si no lo reemplaza, se avisa al autor; el contrato en ejecución no cambia.

### D5. `Intervalo` y la zona del consultorio — Propuesta (forma), sobre D63

```python
# backend/app/domain/agenda/intervalo.py
@dataclass(frozen=True)
class Intervalo:                                   # [inicio, fin) — RN-AG-09
    inicio: datetime
    fin: datetime

    def __post_init__(self) -> None: ...           # RN-GL-01 y luego inicio < fin (RN-AG-10d)

    @classmethod
    def para_turno(cls, inicio: datetime, duracion_minutos: int, zona_horaria: str) -> "Intervalo": ...

    def se_solapa_con(self, otro: "Intervalo") -> bool:
        return self.inicio < otro.fin and otro.inicio < self.fin
```

- **El constructor** valida lo que vale para cualquier intervalo, en este orden: `inicio` y `fin` aware con desfase cero (con `exigir_utc`; si no, `FechaNoUTC`, `RN-GL-01`); después `inicio < fin` (si no, `IntervaloInvalido`, `RN-AG-10d`). Lo usa también el repositorio para armar los `TurnoOcupado` de turnos ya guardados. Son invariantes del value object: valen aunque quien lo construya no haya validado antes (E8).
- **`para_turno`** es la única puerta para un turno **nuevo**: valida `inicio` (RN-GL-01), calcula `fin = inicio + timedelta(minutes=duracion_minutos)` (RN-AG-02), construye el intervalo y aplica la regla de la medianoche (RN-AG-10d). En `crear_turno` la fecha ya llega validada (D6): ahí `para_turno` solo puede fallar por la medianoche, que es una regla de negocio. La zona entra como **dato**: el nombre IANA de `Consultorio.zona_horaria` (`str`); el dominio hace `ZoneInfo(zona_horaria)` y no lee configuración.
- **Regla de la medianoche**, exacta: con `inicio_local` y `fin_local` convertidos a la zona, el intervalo es válido si `fin_local.date() == inicio_local.date()`, **o** si `fin_local` es exactamente las 00:00:00 del día siguiente al de `inicio_local`. En cualquier otro caso, `IntervaloInvalido` (`RN-AG-10d`).
- **De dónde sale la zona en ejecución:** el caso de uso resuelve el profesional, toma su `consultorio_id` y pide `repositorio.zona_horaria(consultorio_id)`.
- **Alternativas descartadas:** la zona como campo de `Intervalo` (la arrastrarían todos los intervalos, también los leídos de la base, y la comparación de dos intervalos no la necesita) y una función de validación suelta fuera del value object (la KB pide que lo haga cumplir `Intervalo`).
- Una zona con nombre desconocido levanta el error de la biblioteca estándar y se deja subir: la zona sale del seed o de las factories, no de la petición.

### D6. Errores de dominio, clases de rechazo y orden de evaluación — Decisión del autor (D128, D135, D139: clasificación de RN-AG-10d y lectura de E4) + Propuesta (clases, orden de `codigos`)

Todo en `backend/app/domain/errors.py`, solo con biblioteca estándar:

```python
class ErrorDeDominio(Exception):
    codigo: str                                   # código RN principal
    mensaje: str
    @property
    def codigos(self) -> list[str]: ...           # [codigo]; lo redefinen ErrorDeSolapamiento y EntradaInvalida

# --- Validación de entrada (se informa toda junta) ---
class FechaNoUTC(ErrorDeDominio):                 # codigo = "RN-GL-01"
    campo: str                                    # "inicio" o "fin"

@dataclass(frozen=True)
class ReferenciaInvalida:
    recurso: Literal["prestacion", "paciente", "profesional", "sillon"]
    recurso_id: int | None
    motivo: Literal["inexistente", "inactivo", "ninguno_activo", "varios_activos"]

class RecursoNoEncontrado(ErrorDeDominio):        # codigo = "RN-GL-04"
    referencias: tuple[ReferenciaInvalida, ...]   # 1 o más

class EntradaInvalida(ErrorDeDominio):            # codigo = errores[0].codigo
    errores: tuple[ErrorDeDominio, ...]           # FechaNoUTC y/o RecursoNoEncontrado, en ese orden; 1 o 2
    # codigos     -> [e.codigo for e in errores]
    # referencias -> las de su RecursoNoEncontrado, o () si no tiene

# --- Reglas de negocio (de a una) ---
class IntervaloInvalido(ErrorDeDominio): ...      # codigo = "RN-AG-10d"

@dataclass(frozen=True)
class Conflicto:
    codigo: Literal["RN-AG-05", "RN-AG-08"]
    recurso: Literal["profesional", "sillon"]
    recurso_id: int
    turno_id: int

class ErrorDeSolapamiento(ErrorDeDominio):        # codigo = conflictos[0].codigo
    conflictos: tuple[Conflicto, ...]             # 1 o 2
    # codigos -> [c.codigo for c in conflictos]
```

`Conflicto` y `ReferenciaInvalida` viven en `errors.py` (y no en `agenda/`) para que `errors.py` no importe nada de `agenda/` y no haya imports circulares. `exigir_utc(valor: datetime, campo: str) -> None` vive en `domain/tiempo.py` y levanta `FechaNoUTC` si el valor es naive o tiene un desfase distinto de cero; la usan `Intervalo` y el caso de uso, así la regla está escrita una sola vez.

**Las dos clases de rechazo (RN-GL-02, decisión del autor D135):**

| Rechazo | Código | Clase | Por qué |
|---|---|---|---|
| Referencia inexistente, inactiva o de otro consultorio; recurso omitido sin un único activo | `RN-GL-04` | Validación de entrada | Decisión del autor (D135) |
| `inicio` sin zona o con desfase distinto de UTC | `RN-GL-01` | Validación de entrada | Decisión del autor (D135). `2026-11-02T10:00:00-03:00` se rechaza aunque sea un instante válido: el contrato es «UTC o nada» |
| Cuerpo mal formado | sin código | Validación de entrada | Decisión del autor (D135) |
| El turno cruza la medianoche del consultorio | `RN-AG-10d` | Regla de negocio | **Confirmada por el autor (2026-10-07, D139).** La KB no lo clasificaba. La petición está bien formada (fecha en UTC, prestación válida): lo que la invalida es la duración de la prestación combinada con la zona del consultorio, dos datos que no vienen en la petición. Además es una regla del dominio Agenda (`RN-AG`), no una global de entrada (`RN-GL`) |
| `inicio >= fin` | `RN-AG-10d` | Regla de negocio | **Propuesta.** Es la primera cláusula del texto literal de RN-AG-10d («`inicio < fin`»). En `POST /turnos` **no puede ocurrir**: `fin` lo calcula el sistema con una duración positiva (`CHECK duracion_minutos > 0`). Queda como invariante del constructor de `Intervalo` y se prueba solo como test unitario (E8). Cuando US-012 permita modificar la duración, una duración no positiva se rechazará antes, como entrada, con `RN-AG-01` (RN-AG-02) |
| Solapamiento con el profesional y/o con el sillón | `RN-AG-05`, `RN-AG-08` | Regla de negocio (**una** regla, dos recursos) | Lectura confirmada por el autor (2026-10-07, D139, sobre D135); ver la nota de D4 |

**Orden de evaluación en `crear_turno`:**

1. **Validación de entrada, todo junto.** Se evalúan las dos cosas, siempre, sin cortar en la primera: (a) `exigir_utc(comando.inicio, "inicio")`; (b) las referencias, con el algoritmo de D10. Las dos son independientes (ninguna necesita a la otra para evaluarse), así que la lista es completa. Si alguna falló, se levanta **un** `EntradaInvalida` con lo que haya fallado y **no se evalúa ninguna regla de negocio**.
2. **Reglas de negocio, de a una**, solo si el paso 1 no encontró nada:
   1. `Intervalo.para_turno(...)`: si el turno cruza la medianoche del consultorio, `IntervaloInvalido` (`RN-AG-10d`) y se termina. Va primero porque sin un intervalo válido no hay con qué comparar.
   2. `detectar_conflictos(...)`: si hay conflictos, `ErrorDeSolapamiento` con uno o dos códigos.

**Orden de `codigos` en el `422` combinado — Propuesta:** `RN-GL-01`, después `RN-GL-04` (el orden en que se evalúan; es estable y los tests lo verifican).

**Qué no se informa** (porque no se puede evaluar; RN-GL-02):

- Con una prestación inválida no hay duración, y sin duración no hay `fin`: no se evalúan RN-AG-10d ni el solapamiento. Tampoco se evalúan si la fecha es inválida. En general, **con cualquier error de entrada no se evalúa ninguna regla de negocio**.
- Con el paciente inexistente y el profesional omitido, el profesional por defecto no se puede buscar (D10): se informa solo el paciente.
- Con el cuerpo mal formado no hay comando: se informan solo los errores de formato (D4, caso 6).

**Consecuencias respecto del primer borrador** (que evaluaba «por etapas sin combinar códigos»):

| Petición | Antes | Ahora |
|---|---|---|
| Prestación inexistente **y** fecha sin zona | solo `RN-GL-04` | un `422` con `["RN-GL-01", "RN-GL-04"]` |
| Fecha sin zona **y** horario ocupado | solo `RN-GL-01` | igual: solo `RN-GL-01` (no se evalúa el negocio) |
| Referencia inválida **y** horario ocupado | solo `RN-GL-04` | igual: solo `RN-GL-04` |
| Cruza la medianoche **y** horario ocupado | solo `RN-AG-10d` | igual: solo `RN-AG-10d` (de a una) |
| Choca con el profesional **y** con el sillón (E4) | `["RN-AG-05", "RN-AG-08"]` | igual (una regla, dos recursos) |

**Cómo llega la API al mismo código que el dominio:** el esquema de Pydantic declara `inicio: datetime` y **no** valida la zona. El router pasa el valor tal cual al comando y es el caso de uso quien llama a `exigir_utc`; el manejador de D4 convierte el `EntradaInvalida` en `422` con `RN-GL-01`. Así la regla vive en un solo lugar y la API y el dominio no pueden divergir.

### D7. Varias referencias inválidas a la vez — Decisión del autor (D127, D135)

`RecursoNoEncontrado` lleva **todas** las referencias inválidas bajo un único código `RN-GL-04`. El caso de uso no lo levanta suelto: lo mete dentro de `EntradaInvalida` (D6), junto con el `FechaNoUTC` si lo hay. En el cuerpo HTTP la lista se llama **`referencias`** (Propuesta: mismo nombre que el atributo del error). El orden es fijo: `prestacion`, `paciente`, `profesional`, `sillon`. El algoritmo completo está en D10.

### D8. Qué turno lleva cada `Conflicto` — Decisión del autor (D129)

Un `Conflicto` por recurso. Si el candidato choca con varios turnos activos del mismo recurso, lleva el de menor `inicio`. Orden de la tupla: profesional, después sillón.

```python
# backend/app/domain/agenda/solapamiento.py
@dataclass(frozen=True)
class TurnoOcupado:
    turno_id: int
    intervalo: Intervalo
    estado: EstadoTurno

def detectar_conflictos(
    candidato: Intervalo,
    profesional_id: int, ocupados_profesional: Sequence[TurnoOcupado],
    sillon_id: int, ocupados_sillon: Sequence[TurnoOcupado],
) -> tuple[Conflicto, ...]: ...
```

Para cada recurso: se queda con los ocupados cuyo `estado` está en `ESTADOS_ACTIVOS` (RN-AG-10) y cuyo intervalo `se_solapa_con` el candidato (RN-AG-09); si queda alguno, agrega un `Conflicto` con el de menor `inicio`. No depende del orden en que lleguen las secuencias. `EstadoTurno` (enum de texto con los nueve estados de `04_modelo_de_datos.md`) y `ESTADOS_ACTIVOS` (`frozenset` de los cuatro activos) están en `domain/turnos/estados.py`.

### D9. Profesional y sillón por defecto — Decisión del autor (D125, RN-AG-14) + Propuesta (consultorio de referencia y motivos)

Si la petición no indica el recurso, se usa el **único activo** del consultorio. No hay columna ni `id` de «por defecto».

- **Profesional omitido:** el consultorio de referencia es el del **paciente**. Se cuentan sus profesionales activos: uno → se usa; ninguno → referencia inválida `("profesional", None, "ninguno_activo")`; más de uno → `("profesional", None, "varios_activos")`.
- **Sillón omitido:** el consultorio de referencia es el del **profesional ya resuelto**. Uno activo → se usa; ninguno → `("sillon", None, "ninguno_activo")`; más de uno → `("sillon", None, "varios_activos")`.
- Los motivos `ninguno_activo` y `varios_activos` se suman a `inexistente` e `inactivo`. Se resuelve junto con las demás referencias, como validación de entrada (D6), antes de cualquier regla de negocio y sin persistir nada.

### D10. Pertenencia al consultorio y algoritmo de referencias — Decisión del autor (D126) + Propuesta (casos que D126 dejó abiertos)

`Turno.consultorio_id` sale del profesional. Una referencia de otro consultorio cuenta como `inexistente`. El comando no lleva `consultorio_id`.

Algoritmo de `crear_turno` para las referencias (la parte (b) de la validación de entrada, D6). `C` es el consultorio del turno; vale «desconocido» hasta que se resuelve el profesional.

1. **Paciente.** `repositorio.paciente(id)`. Si no existe → inválida (`inexistente`).
2. **Profesional.**
   - Indicado: si no existe → `inexistente`; si no está activo → `inactivo`; si no, queda resuelto y `C` = su consultorio.
   - Omitido: si el paciente existe, se aplica D9 sobre el consultorio del paciente; si queda resuelto, `C` = ese consultorio. Si el paciente no existe, el profesional **no se puede evaluar** y no se informa (ya se informa el paciente).
3. **Paciente, segunda comprobación.** Si existe, `C` es conocido y su consultorio no es `C` → `inexistente`.
4. **Prestación.** Si no existe → `inexistente`. Si existe, `C` es conocido y es de otro consultorio → `inexistente`. Si no, y no está activa → `inactivo`.
5. **Sillón.**
   - Indicado: si no existe → `inexistente`. Si existe, `C` es conocido y es de otro consultorio → `inexistente`. Si no, y no está activo → `inactivo`.
   - Omitido: si `C` es conocido, se aplica D9 sobre `C`. Si `C` es desconocido, **no se puede evaluar** y no se informa.
6. Si hay al menos una inválida → un `RecursoNoEncontrado` con todas, en el orden de D7, que el caso de uso agrupa en `EntradaInvalida` junto con el resultado de la fecha (D6). No se persiste nada.

Reglas de desempate: «de otro consultorio» gana sobre «inactivo» (no se revela el estado de un recurso ajeno). Cuando `C` es desconocido siempre hay al menos una referencia informada, así que la petición nunca pasa a las reglas de negocio con algo sin evaluar.

**Paciente (decisión del autor, D136):** un paciente solo puede ser `inexistente` (no existe o es de otro consultorio). `Paciente` no tiene columna de actividad y el «paciente inactivo» queda para la Fase 2; por eso el tipo `Paciente` del dominio no lleva `activo` (D12) y el paso 1 no tiene rama `inactivo`.

### D11. Granularidad de la duración — Decisión del autor (D131)

Este change **no valida** que la duración de la prestación sea múltiplo de 5 (RN-AG-01): la usa tal como está. Las prestaciones salen del seed de demo y de las factories, siempre con duraciones válidas. La base conserva el `CHECK duracion_minutos > 0`.

### D12. Unidad de trabajo, sesión y SQLite con hilos — Propuesta + A verificar

**Puertos** (`backend/app/application/puertos.py`, protocolos; los implementa `infrastructure`):

```python
class RepositorioAgenda(Protocol):
    def paciente(self, paciente_id: int) -> Paciente | None: ...
    def prestacion(self, prestacion_id: int) -> Prestacion | None: ...
    def profesional(self, profesional_id: int) -> Profesional | None: ...
    def sillon(self, sillon_id: int) -> Sillon | None: ...
    def profesionales_activos(self, consultorio_id: int) -> Sequence[Profesional]: ...
    def sillones_activos(self, consultorio_id: int) -> Sequence[Sillon]: ...
    def zona_horaria(self, consultorio_id: int) -> str: ...
    def turnos_que_intersecan(
        self, recurso: Literal["profesional", "sillon"], recurso_id: int, intervalo: Intervalo
    ) -> Sequence[TurnoOcupado]: ...
    def agregar(self, turno: Turno) -> Turno: ...          # devuelve el turno con su id

class UnidadDeTrabajo(Protocol):
    agenda: RepositorioAgenda
    def __enter__(self) -> "UnidadDeTrabajo": ...
    def __exit__(self, tipo, valor, traza) -> None: ...
```

Los tipos de `recursos.py` son dataclasses congeladas con lo mínimo: `Paciente(id, consultorio_id)`, `Prestacion(id, consultorio_id, duracion_minutos, activa)`, `Profesional(id, consultorio_id, activo)`, `Sillon(id, consultorio_id, activo)`. `Turno` (en `domain/turnos/turno.py`) es una dataclass congelada con los once campos de `TurnoSalida`; `id` es `int | None` hasta que el repositorio lo guarda. El repositorio traduce entre modelos ORM y estos tipos: **ningún modelo ORM sale de `infrastructure`**.

`turnos_que_intersecan` devuelve los turnos del recurso **en cualquier estado** cuyo intervalo interseca al pedido (`turno.inicio < :fin AND turno.fin > :inicio`). Es un recorte para no traer toda la agenda; la regla (estados activos y solapamiento) la decide `detectar_conflictos` en el dominio.

**Caso de uso** (`backend/app/application/crear_turno.py`):

```python
@dataclass(frozen=True)
class CrearTurnoComando:
    paciente_id: int
    prestacion_id: int
    inicio: datetime
    profesional_id: int | None = None
    sillon_id: int | None = None

def crear_turno(comando: CrearTurnoComando, uow: UnidadDeTrabajo, reloj: Reloj = utc_now) -> Turno: ...
```

Dentro de `with uow:`, en el orden de D6: (1) **validación de entrada**: `exigir_utc(comando.inicio, "inicio")` y las referencias (D10), las dos siempre; si algo falló, `EntradaInvalida` con todo; (2) **primera regla de negocio**: `Intervalo.para_turno(comando.inicio, prestacion.duracion_minutos, uow.agenda.zona_horaria(C))`, que puede levantar `IntervaloInvalido` (`RN-AG-10d`); (3) **segunda regla de negocio**: `turnos_que_intersecan` para el profesional y para el sillón, y `detectar_conflictos`; si hay conflictos, `ErrorDeSolapamiento`; (4) `uow.agenda.agregar(Turno(..., estado=EstadoTurno.RESERVADO, creado_en=reloj()))`. El caso de uso no hace `commit()` ni arma SQL.

**Unidad de trabajo** (`UnidadDeTrabajoSqlAlchemy(fabrica_sesiones)`): `__enter__` abre una sesión y crea `self.agenda = RepositorioAgendaSqlAlchemy(sesion)`; `__exit__` hace `commit()` si no hubo excepción y `rollback()` si la hubo, y siempre cierra la sesión. Una unidad de trabajo por petición; no se reutiliza.

**Dependencias de la API** (`backend/app/api/deps.py`): `get_uow(request)` devuelve `UnidadDeTrabajoSqlAlchemy(request.app.state.fabrica_sesiones)`; `get_reloj()` devuelve `utc_now`. El endpoint es una función `def` (sincrónica). Los tests de API construyen la aplicación con `crear_app(engine)` usando el engine del test y sustituyen el reloj con `app.dependency_overrides[get_reloj]`. No se sustituye la sesión por un doble: es una sesión real sobre el engine del test.

**Engine** (`backend/app/infrastructure/db/motor.py`), el mismo para la demo y para los tests:

```python
def crear_engine_en_memoria() -> Engine:
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
```

- `StaticPool` hace que todas las sesiones usen **la misma conexión**, que es lo que mantiene viva y compartida la base en memoria.
- `check_same_thread=False` hace falta porque FastAPI ejecuta los endpoints `def` en un grupo de hilos, distinto del hilo que creó la conexión.

**Fixtures** (`backend/tests/conftest.py`): `engine` (crea con `crear_engine_en_memoria()`, `create_all`, entrega, `dispose()`; **uno por test**), `fabrica_sesiones`, `sesion` (para que las factories carguen datos y para las aserciones), `uow` y la constante `RELOJ_FIJO = datetime(2026, 10, 7, 12, 0, tzinfo=UTC)` con `reloj_fijo = lambda: RELOJ_FIJO`. Las factories hacen `commit()` antes de devolver, para que la sesión del caso de uso no dependa de una transacción abierta del test.

**A verificar en el change** (verificar antes de escribir las pruebas de API, grupo 12 de tareas): que con esa configuración un test que carga datos en el hilo del test y llama a `POST /turnos` con `TestClient` ve los datos y no recibe el error de hilo de `pysqlite`. Lo prueba el primer test de API (E1). Si falla, no se cambia la configuración en silencio: se vuelve a este design.

### D13. Ida y vuelta de fechas con SQLite — Propuesta + A verificar (D85)

`backend/app/infrastructure/db/tipos.py` define un `TypeDecorator`:

```python
class FechaHoraUTC(TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True
    def process_bind_param(self, valor, dialect): ...     # None -> None; naive o no UTC -> ValueError; aware UTC -> tal cual
    def process_result_value(self, valor, dialect): ...   # None -> None; naive -> replace(tzinfo=UTC); aware -> astimezone(UTC)
```

- **Al escribir** rechaza con `ValueError` un datetime naive o con desfase distinto de cero: es un error de programación (el dominio ya lo filtró), no un error de negocio, por eso no lleva código RN.
- **Al leer** normaliza: SQLite devuelve naive, y como solo se escribió UTC, se le pone la zona UTC; PostgreSQL devolverá aware y se pasa a UTC.
- **Toda** columna de fecha-hora usa `FechaHoraUTC`: `turno.inicio`, `turno.fin`, `turno.creado_en`. Como las comparaciones de `turnos_que_intersecan` son contra esas columnas, los parámetros pasan por el mismo tipo.

**A verificar en el change** (verificar antes de cerrar el primer change, y en la práctica antes del grupo 4 de tareas, que es el primero que persiste turnos): `backend/tests/integration/test_fechas_ida_y_vuelta.py` comprueba que (a) un turno escrito con `inicio` aware UTC se lee con `tzinfo` UTC y el mismo instante; (b) escribir un naive levanta `ValueError`; (c) la consulta por rango devuelve el turno correcto comparando contra un parámetro aware UTC (que SQLite compare bien el texto que guarda).

### D14. Test de imports del dominio — Propuesta (método), sobre D70 y D132

`backend/tests/unit/test_imports_dominio.py`. Una función auxiliar del test, `imports_prohibidos(codigo_fuente: str) -> list[str]`, recorre el árbol sintáctico (`ast`) y junta el primer segmento del nombre de cada `import` e `import from`. Un import está **permitido** si es relativo, si su primer segmento está en `sys.stdlib_module_names` (incluye `zoneinfo`), o si el módulo es `app.domain` o un submódulo. Todo lo demás está prohibido: `fastapi`, `pydantic`, `starlette`, `sqlalchemy`, `tzdata` y también `app.application`, `app.infrastructure` y `app.api`.

El test tiene dos partes: (1) recorre todos los `.py` de `backend/app/domain` y exige lista vacía, y exige además que encontró al menos un archivo (para que no pase por recorrer una carpeta vacía); (2) llama a la función con textos de ejemplo (`import sqlalchemy`, `from fastapi import FastAPI`, `from app.infrastructure.db import modelos`, `import tzdata`) y exige que los detecte, y con `from zoneinfo import ZoneInfo` y `from app.domain.tiempo import utc_now` exige que no. La parte 2 es la que demuestra que el test puede fallar.

### D15. Test guard de fechas — Propuesta (método), sobre DD-13

`backend/tests/integration/test_guard_fechas.py` (no usa base, pero importa los modelos de SQLAlchemy, por eso no va en `unit`):

1. **Esquema:** recorre `Base.metadata.tables` y, para cada columna cuyo tipo es `DateTime` o un `TypeDecorator` con `impl` `DateTime`, exige que sea `FechaHoraUTC` con `timezone=True`. Exige también que encontró al menos tres columnas de fecha-hora (las de `turno`).
2. **Código:** recorre con `ast` todos los `.py` de `backend/app` y falla si encuentra una llamada a `.utcnow()`, `.utcfromtimestamp()` o `.today()`, o una llamada a `.now(...)` fuera de `backend/app/domain/tiempo.py`. El único `now` permitido es el de `utc_now()`: `datetime.now(UTC)`.

Como en D14, la detección está en una función auxiliar que se prueba con textos de ejemplo que deben dar positivo.

`backend/app/domain/tiempo.py`: `UTC = timezone.utc`, `Reloj = Callable[[], datetime]` y `def utc_now() -> datetime: return datetime.now(UTC)`.

### D16. Tabla escenario ↔ test — Propuesta

Va en los dos lugares: acá (trazabilidad completa, abajo) y en el `README.md` (tabla corta escenario → test). El test «titular» de cada escenario es el de integración (caso de uso real + repositorio real + SQLite en memoria), con el ID en el nombre. Las reglas puras se prueban además en `unit`, y el mapeo HTTP en `api` para E1, E4 y E12, que es el mínimo que fija `08_arquitectura_propuesta.md`. Esto resuelve la inconsistencia 6 del relevamiento (en qué capa se prueba cada escenario).

| Escenario | Requirement del spec | RN | Test titular (`backend/tests/integration/test_crear_turno.py`) | Tests de apoyo |
|---|---|---|---|---|
| E1 | Crear un turno reservado con fin calculado | RN-AG-02, RN-AG-06, RN-AG-14, RN-GL-01 | `test_e1_feliz_crea_turno_reservado_con_fin_calculado` | `api/test_post_turnos.py::test_e1_post_turnos_responde_201` |
| E2 | Rechazar el solapamiento con un turno activo del profesional | RN-AG-05, RN-GL-02 | `test_e2_profesional_ocupado_rechaza_con_rn_ag_05` | `unit/test_detectar_conflictos.py::test_e2_conflicto_solo_de_profesional` |
| E3 | Rechazar el solapamiento con un turno activo del sillón | RN-AG-08, RN-GL-02 | `test_e3_sillon_ocupado_rechaza_con_rn_ag_08` | `unit/test_detectar_conflictos.py::test_e3_conflicto_solo_de_sillon` |
| E4 | Informar todos los conflictos de solapamiento | RN-AG-05, RN-AG-08, RN-GL-02 | `test_e4_doble_conflicto_informa_los_dos_codigos` | `unit/test_detectar_conflictos.py::test_e4_dos_conflictos_profesional_primero`; `api/test_post_turnos.py::test_e4_post_turnos_responde_409_con_los_dos_codigos` |
| E5 | Tratar los turnos como intervalos semiabiertos | RN-AG-09 | `test_e5_borde_contiguo_se_acepta` | `unit/test_intervalo.py::test_se_solapa_con` (tabla) |
| E6 | Contar solo los turnos en estado activo | RN-AG-10 | `test_e6_estado_no_activo_no_bloquea` | `unit/test_detectar_conflictos.py::test_e6_estados_no_activos_no_generan_conflicto` |
| E7 | Tratar los turnos como intervalos semiabiertos | RN-AG-09, RN-AG-05 | `test_e7_borde_de_un_minuto_se_rechaza` | `unit/test_intervalo.py::test_se_solapa_con` (tabla) |
| E12 | Rechazar las referencias inválidas | RN-GL-04, RN-GL-02, RN-AG-07, RN-AG-14 | `test_e12_recurso_no_encontrado_rechaza_con_rn_gl_04` | `api/test_post_turnos.py::test_e12_post_turnos_responde_422_con_rn_gl_04` |

Tests que cubren el modelo de errores de D135 (RN-GL-02). No son escenarios nuevos: el conjunto E1..E7 y E12 lo fija la KB, y lo que D135 agrega se verifica con el texto ampliado del Requirement de E12 y con estos tests:

| Qué | RN / decisión | Test |
|---|---|---|
| Entrada: fecha sin zona **y** referencia inválida en la misma petición → un error con `["RN-GL-01", "RN-GL-04"]` | RN-GL-01, RN-GL-04, RN-GL-02, D135 | `integration/test_crear_turno.py::test_entrada_invalida_informa_fecha_y_referencias_juntas`; `api/test_post_turnos.py::test_fecha_sin_zona_y_referencia_invalida_responde_un_422_con_los_dos_codigos` |
| Entrada antes que negocio: referencia inválida y horario ocupado → solo `RN-GL-04` | RN-GL-04, RN-GL-02, D135 | `integration/test_crear_turno.py::test_referencia_invalida_y_horario_ocupado_informa_solo_rn_gl_04` |
| Entrada antes que negocio: fecha sin zona y horario ocupado → solo `RN-GL-01` | RN-GL-01, RN-GL-02, D135 | `integration/test_crear_turno.py::test_fecha_sin_zona_y_horario_ocupado_informa_solo_rn_gl_01` |
| Negocio de a una: cruza la medianoche y además se solapa → solo `RN-AG-10d` | RN-AG-10d, RN-GL-02, D135 | `integration/test_crear_turno.py::test_cruce_de_medianoche_y_horario_ocupado_informa_solo_rn_ag_10d` |
| Paciente: solo `inexistente` (también el de otro consultorio) | RN-GL-04, D126, D136 | casos de `integration/test_crear_turno.py::test_e12_*` (tarea 11.3) |

Tests fuera del spec que también entran en el change:

| Qué | RN / decisión | Test |
|---|---|---|
| E8, intervalo inválido | RN-GL-01, RN-AG-10d | `unit/test_intervalo.py::test_e8_*` |
| `exigir_utc` | RN-GL-01, D128 | `unit/test_tiempo.py::test_exigir_utc_*` |
| Fecha no UTC e intervalo inválido por HTTP | RN-GL-01, RN-AG-10d, D128 | `api/test_post_turnos.py::test_fecha_sin_zona_responde_422_con_rn_gl_01`, `::test_cruce_de_medianoche_responde_422_con_rn_ag_10d` |
| `422` de formato con el mismo cuerpo | D4, D135 | `api/test_post_turnos.py::test_cuerpo_invalido_responde_problem_json` |
| Reloj | DD-13 | `unit/test_tiempo.py::test_utc_now_devuelve_aware_utc` |
| Ida y vuelta de fechas | D85 | `integration/test_fechas_ida_y_vuelta.py` |
| Imports del dominio | D70, D132 | `unit/test_imports_dominio.py` |
| Guard de fechas | DD-13 | `integration/test_guard_fechas.py` |
| Demo | D124 | `api/test_demo.py::test_la_peticion_de_ejemplo_del_readme_responde_201` |

### D17. Configuración de pytest — Decisión del autor (D137: dentro de `pyproject.toml`) + Propuesta (opciones)

Va en `backend/pyproject.toml`, en la tabla `[tool.pytest.ini_options]` (contenido completo en D1). **No se crea `backend/pytest.ini`**: el primer borrador lo tenía porque el archivo de dependencias era `requirements.txt`; con D137 la configuración se muda al archivo único.

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-ra --strict-markers"
```

- Se corre **desde `backend/`** con `python -m pytest`. `pythonpath = ["."]` hace importable `app` y `tests` sin instalar el proyecto, que es lo que permite no empaquetarlo (D1).
- No se registra ningún marcador: el marcador `postgres` (E11) lo crea C-02. Con `--strict-markers`, un marcador mal escrito falla en vez de pasar inadvertido.
- Sin plugins de pytest: no hay ninguno que declarar.

**A verificar en el change** (verificar antes de escribir el primer test, tarea 1.2): que `python -m pytest` desde `backend/` toma esa tabla (la cabecera de la corrida muestra `configfile: pyproject.toml` y `testpaths: tests`).

### D18. `.gitignore` y variables de entorno — Propuesta

Se agregan a `.gitignore` (hoy solo ignora `.claude/settings.local.json`):

```
# Python
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/

# Entorno y secretos (nunca se versionan)
.env
.env.*
!.env.example

# Bases locales
*.db
*.sqlite3
```

**Variables de entorno: ninguna.** Este change no lee `DATABASE_URL` ni ninguna otra: la URL de SQLite en memoria es una constante de `motor.py` y la zona del consultorio sale de la columna. No se crea `.env.example`; los nombres definitivos de las variables y ese archivo son de C-02.

### D19. Factories de test y seed de demo — Propuesta (datos concretos), sobre D124 y RN-PR-01

**Factories** (`backend/tests/factories.py`): funciones que reciben la `sesion`, guardan, hacen `commit()` y devuelven el modelo con su `id`. Todo parámetro tiene un valor por defecto válido y se puede sobreescribir.

| Función | Valores por defecto |
|---|---|
| `un_consultorio(sesion, **kw)` | `nombre="Consultorio de Prueba"`, `slug` único por llamada (`consultorio-prueba-N`), `zona_horaria="America/Argentina/Buenos_Aires"` |
| `un_profesional(sesion, consultorio, **kw)` | `nombre="Profesional de Prueba"`, `activo=True` |
| `un_sillon(sesion, consultorio, **kw)` | `nombre="Sillón de Prueba"`, `activo=True` |
| `una_prestacion(sesion, consultorio, **kw)` | `nombre` único por llamada (`Prestación de Prueba N`), `duracion_minutos=30`, `activa=True` |
| `un_paciente(sesion, consultorio, **kw)` | `nombre="Paciente"`, `apellido="De Prueba"`, `telefono_whatsapp="+5491155550100"` |
| `un_turno(sesion, *, paciente, profesional, sillon, prestacion, inicio, estado="reservado", **kw)` | `fin = inicio + duración de la prestación`, `duracion_minutos` de la prestación, `consultorio_id` del profesional, `creado_en = RELOJ_FIJO` |

Cada test arma sus datos; no hay seed compartido entre tests (`08_arquitectura_propuesta.md`, «Fixtures de test»). Los tests de dominio no usan estas factories: construyen `Intervalo` y `TurnoOcupado` en memoria.

**Seed de demo** (`backend/app/infrastructure/db/seed_demo.py`, `cargar_demo(sesion) -> None`), con identificadores asignados a mano para que sean fijos:

| Tabla | id | Datos |
|---|---|---|
| `consultorio` | 1 | «Consultorio Demo», slug `consultorio-demo`, zona `America/Argentina/Buenos_Aires` |
| `profesional` | 1 | «Dra. Demo Ficticia», activo |
| `sillon` | 1 | «Sillón 1», activo |
| `prestacion` | 1 | «Consulta / control», 30 min |
| `prestacion` | 2 | «Limpieza», 45 min |
| `prestacion` | 3 | «Obturación», 60 min |
| `prestacion` | 4 | «Extracción», 45 min |
| `prestacion` | 5 | «Urgencia», 30 min |
| `paciente` | 1 | «Ana Ejemplo», `+5491155550101` |
| `paciente` | 2 | «Bruno Ficticio», `+5491155550102` |
| `paciente` | 3 | «Carla Inventada», `+5491155550103` |

Las prestaciones y sus duraciones son las de `04_modelo_de_datos.md` («Seed data inicial», D56). Los nombres y teléfonos de pacientes son inventados para este design; el bloque `5555-01xx` se usa como «prefijo de prueba», que la KB pide sin definir. La demo tiene **un** profesional y **un** sillón a propósito: así omitirlos funciona (RN-AG-14) y un segundo turno a la misma hora muestra el `409` con los dos códigos (E4).

**Petición de ejemplo del README** (la misma que prueba `test_demo.py`):

```json
{"paciente_id": 1, "prestacion_id": 1, "inicio": "2026-11-02T13:00:00Z"}
```

Recorrido de la prueba manual en `/docs`: (1) esa petición → `201`; (2) la misma petición otra vez → `409` con `codigos` `["RN-AG-05", "RN-AG-08"]`; (3) la misma con `"prestacion_id": 999` → `422` con `RN-GL-04`.

### Esquema de base de datos — Decisión del autor (subconjunto del primer change, D130) + Propuesta (nombres de tabla)

Modelos en `backend/app/infrastructure/db/modelos.py`, con `DeclarativeBase`, `Mapped` y `mapped_column`. Clases con sufijo `Modelo` (`TurnoModelo`…) para no chocar con los tipos del dominio. Nombres de tabla en singular y minúscula. Claves primarias enteras autoincrementales; claves foráneas con `ondelete="RESTRICT"`; `estado` como texto.

| Tabla | Columnas | Restricciones e índices |
|---|---|---|
| `consultorio` | `id`, `nombre`, `slug`, `zona_horaria` (default `America/Argentina/Buenos_Aires`) | `UNIQUE(slug)` |
| `profesional` | `id`, `consultorio_id`, `nombre`, `activo` (default `true`) | FK a `consultorio` |
| `sillon` | `id`, `consultorio_id`, `nombre`, `activo` (default `true`) | FK a `consultorio` |
| `prestacion` | `id`, `consultorio_id`, `nombre`, `duracion_minutos`, `activa` (default `true`) | FK; `UNIQUE(consultorio_id, nombre)`; `CHECK duracion_minutos > 0` |
| `paciente` | `id`, `consultorio_id`, `nombre`, `apellido`, `telefono_whatsapp` | FK; índice `(consultorio_id, telefono_whatsapp)` sin `UNIQUE` |
| `turno` | `id`, `consultorio_id`, `paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id`, `inicio`, `fin`, `duracion_minutos`, `estado`, `creado_en` | FK a las cinco; `CHECK inicio < fin`; `CHECK duracion_minutos > 0`; índices `(profesional_id, inicio, fin)` y `(sillon_id, inicio, fin)` |

Todas las columnas son no nulas. **No se crean** las columnas que el subconjunto excluye: `consultorio.creado_en`, `profesional.usuario_id` y `matricula`, `prestacion.color` y `reservable_online`, `paciente.dni`, `email`, `fecha_nacimiento`, `es_nuevo`, `acepta_contacto` y `creado_en`, `turno.origen`, `token_gestion`, `creado_por`, `actualizado_en` y `version` (D130). Sin restricción de exclusión (DD-04). El esquema se crea con `Base.metadata.create_all(engine)`; sin Alembic (DD-15).

### Contenido del `README.md` — Propuesta

En español, en este orden: (1) qué es el proyecto y qué entrega este change; (2) requisitos: **Python 3.11, 3.12 o 3.13** (no 3.14, D1) y nada más (sin Docker, PostgreSQL ni Redis); (3) instalación desde `backend/`, con los comandos de abajo; (4) tests: `python -m pytest` desde `backend/`, con la frase explícita de que corren con **SQLite en memoria**; (5) las ocho versiones fijadas, que viven en `backend/pyproject.toml`, y la nota sobre `tzdata` (D132: hace falta en Windows, donde `zoneinfo` no trae base de zonas); (6) cómo levantar la API y abrir `/docs`; (7) identificadores de la demo, petición de ejemplo y el recorrido `201` / `409` / `422`; (8) tabla escenario → test; (9) **límites conocidos**: `POST /turnos` sin autenticación (DD-14), datos de demo que se pierden al reiniciar, sin concurrencia (E11) y sin validación de horario; (10) correspondencia con la estructura mínima de la consigna (`src/` → `backend/app/`); (11) aviso de que todos los datos son ficticios.

Comandos de instalación y de tests que el README copia tal cual (Windows; para Linux y macOS cambia la creación y la activación del entorno: `python3 -m venv .venv` y `source .venv/bin/activate`):

```
cd backend
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install --group test
python -m pytest
```

`py -3.13` puede ser `py -3.11` o `py -3.12`. El paso `--upgrade pip` está porque `--group` necesita `pip` 25.1 o superior (D1).

**A verificar en el change** (verificar antes de crear el archivo de dependencias, tarea 1.1, y otra vez en el clon limpio, tarea 14.2): que esa secuencia, sin ningún otro paso, deja el entorno instalado y los tests corriendo.

### Skills del rol Backend / API

Se aplican las reglas compactas de `.atl/skill-registry.md` para `fastapi-templates`, `python-design-patterns`, `python-error-handling` y `python-testing-patterns`, con la precedencia de la KB y de `openspec/config.yaml`. Lo que se **adapta o no se usa**: nada asíncrono (sesión, cliente de pruebas ni tests); nada de mocks de sesión o de repositorio ni de `freezegun` (se inyecta el reloj); las capas son las de la KB (`domain`, `application`, `infrastructure`, `api`), no las de la plantilla (`services`, `repositories`, `core`); las reglas de negocio levantan errores de dominio con código RN, no `ValueError`.

## Contradicciones y vacíos encontrados en las fuentes

No se resolvió ninguno en silencio. Lo que este design eligió queda como **Propuesta** en la decisión indicada.

**Resueltos por la segunda ronda del autor (2026-10-07) y ya reflejados en la KB:** el formato del archivo de dependencias (D137: `pyproject.toml`, como dibujaba `08`); el paciente «inactivo» (D136: solo `inexistente`); RN-GL-02 frente a la evaluación por etapas (D135: RN-GL-02 se reescribió); la cantidad de tareas (D134: segunda excepción registrada); la entrada C-05 de `CHANGES.md` (D138). También quedó resuelto, antes de esta revisión, el aviso del CLI sobre `operations.apply.guidance` de `openspec/config.yaml`: las líneas ya van entre comillas y el CLI las lee como textos.

**Nuevos, que salen de aplicar esas decisiones:**

1. **«De a una» frente a E4.** D135 dice que las reglas de negocio se informan de a una; RN-AG-08, D129 y E4 dicen que el doble conflicto informa dos códigos. Leídos literalmente se contradicen. Este design aplica la lectura del orquestador (el solapamiento es **una** regla que mira dos recursos, D4 y D6) y RN-GL-02 lo dice de forma explícita. **Confirmada por el autor (2026-10-07, D139).**
2. **RN-AG-10d: regla de negocio con estado `422`.** La KB no dice de qué clase es. Este design la clasifica como regla de negocio (D6) y conserva el `422` del mapeo de `08`, aunque el otro rechazo de negocio (el solapamiento) responde `409`. No se cambió el estado porque ninguna decisión lo pide. **Confirmado por el autor (2026-10-07, D139):** es regla de negocio, se informa sola y responde `422`.
3. **«Todos juntos» frente a un cuerpo que no se puede leer.** D135 pone el cuerpo mal formado en la misma clase que las referencias y la fecha, pero si Pydantic rechaza el cuerpo no hay petición sobre la que evaluar lo demás. Este design informa todos los errores de formato juntos, con el mismo cuerpo de `422`, y nada más (D4, caso 6). Juntar además referencias y fecha exigiría leer el cuerpo «a medias», que este design no hace.
4. **`type` y título del error de E12.** RN-GL-04 llama al error «recurso no encontrado» y `08` proponía el `type` `/errores/recurso-no-encontrado`. Con un `422` que puede reunir varias clases de problema, este design usa un único `type` `/errores/entrada-invalida` (D4). El código `RN-GL-04` y la clase `RecursoNoEncontrado` no cambian. `08` quedó actualizado; el texto de RN-GL-04 conserva el nombre del error de dominio. **Confirmado por el autor (2026-10-07, D139).**
5. **«Python 3.11+» frente a los pins de D133.** La KB dice 3.11 o superior. Con FastAPI 0.115.x y el Pydantic que ese FastAPI soporta, el change **no se instala en Python 3.14** sin compilar (D1). El README dirá «3.11, 3.12 o 3.13». Era una consecuencia de D133 que el autor no había decidido de forma explícita; **la confirmó el 2026-10-07 (D139):** Python 3.11 a 3.13 para este proyecto.
6. **«Ninguna versión de la última semana, para ningún paquete» frente a las transitivas.** D133 habla de todos los paquetes; este design fija ocho y deja las transitivas a `pip` (D1), que puede traer una versión publicada ayer. Cumplirlo al pie de la letra pide fijar unas quince más.
7. **«Pydantic compatible con ese FastAPI».** El rango de los metadatos de `fastapi 0.115.14` admite hasta la última serie 2.13, pero las notas de FastAPI 0.118.1 indican que la compatibilidad con Pydantic 2.12 llegó después de la serie 0.115. Este design elige la serie 2.11 (D1), con un dato externo a PyPI. **Confirmado por el autor (2026-10-07, D139):** `pydantic 2.11.10`.
8. **Reglas generales de `CHANGES.md`.** Las líneas «SQLAlchemy 2.x sincrónico» y «El archivo único de dependencias y sus versiones exactas se fijan en el `design.md` de C-01 … (D116)» siguen sin nombrar la serie 2.0.x (D133) ni `pyproject.toml` (D137). No son falsas, pero quedaron menos precisas que la KB. No se tocaron: la segunda ronda pidió tocar solo las entradas C-05 y C-01.
9. **`CLAUDE.md` y `AGENTS.md`.** La regla dura 4 decía «se informan todos los códigos que fallen», que contradice D135. Se alineó (junto con las filas de FastAPI y SQLAlchemy de la tabla del stack y el rango de decisiones). Las reglas duras las confirmó el autor el 2026-10-06, y **la nueva redacción de la regla 4, el 2026-10-07 (D139).**

**Siguen abiertos del primer borrador:**

10. **RN-GL-01 y «la conversión ocurre en el borde».** `08` («Reloj y zonas») dice que la conversión desde la hora de Buenos Aires ocurre «en el borde (API o adaptador)»; D128 dice que una fecha con desfase distinto de UTC se **rechaza** con `422`. Este design sigue a D128, que es posterior: la API no convierte, rechaza (D6). El «borde» que convierte será el cliente (la interfaz de la fase 3).
11. **`.env.example` en la Definition of Done.** `08` pide «`.env.example` solo con valores de prueba»; este change no lee variables y no crea ese archivo, que `CHANGES.md` asigna a C-02 (D18). El ítem se cumple por ausencia.
12. **Seed del sillón.** `06_funcionalidades.md` (US-004 CA-1) asigna «el seed crea Sillón 1» a un change posterior, y este change ya lo necesita en la demo (D19). Queda como estaba: lo señala el registro de decisiones como abierto.
13. **Rama.** El repositorio está en `master` y la documentación nombra `main` como rama principal. No afecta al change; importa al etiquetar el hito.

## Risks / Trade-offs

- **[`fastapi 0.115.14`, `starlette 0.46.2` y `pydantic 2.11.10` son de 2025: tienen recorrido, pero ya no reciben correcciones]** → Es la decisión del autor (D133): se prefiere una serie probada a una nueva. Aceptable para un trabajo académico sin despliegue público; cada change posterior puede proponer subir de serie en su design.
- **[Paquetes de 2026 (`uvicorn 0.54.0`, `pytest 9.1.1`, `SQLAlchemy 2.0.54`) junto a un `fastapi` de 2025]** → Los metadatos no declaran conflictos, pero nada se instaló. La primera tarea instala en un entorno nuevo y comprueba los imports. Si algo falla **no se cambia la versión en silencio**: se vuelve al design y lo decide el autor.
- **[El change no se instala en Python 3.14, que es el Python por defecto del lanzador `py` en la máquina del autor]** → El README pide 3.11, 3.12 o 3.13 y da el comando con `py -3.13`; la tarea 1.1 lo comprueba. La alternativa (Pydantic 2.13.5) está descrita en D1.
- **[`pip install --group` necesita `pip` 25.1 o superior]** → El README hace actualizar `pip` antes de instalar; se verifica en la tarea 1.1 y en el clon limpio.
- **[Dependencias transitivas sin fijar]** → Límite declarado (D1), que además deja fuera de la regla de la semana (D133) a las transitivas; la verificación en clon limpio se hace al final y el README lista los ocho pins.
- **[El contrato de errores depende de dos lecturas: E4 con dos códigos y RN-AG-10d como regla de negocio]** → El autor las confirmó antes del apply (2026-10-07, D139). Están aisladas en D4 y D6 y en los tests de la tabla de D16.
- **[SQLite no se comporta como PostgreSQL: zonas, hilos, sin claves foráneas activas, sin `EXCLUDE`]** → La regla vive en el dominio; `FechaHoraUTC` normaliza; el test de ida y vuelta y el primer test de API prueban los dos puntos frágiles. La concurrencia queda fuera, declarada.
- **[Endpoint de escritura sin autenticación]** → Solo datos ficticios, base en memoria y sin despliegue público; el README lo declara como límite conocido (DD-14).
- **[Change grande para «una sola funcionalidad»: 8 escenarios, 6 tablas, 4 capas]** → Orden estricto por escenario; cada grupo de tareas deja la suite en verde; nada fuera del alcance (sin lecturas, sin migraciones).
- **[Los mensajes de validación de formato salen en inglés]** → Se adapta la forma (`problem+json`); traducirlos queda fuera.
- **[El recorte por rango de `turnos_que_intersecan` repite en SQL la condición de solapamiento]** → Es solo un filtro de rendimiento; el dominio vuelve a aplicar la regla, y los tests de borde (E5, E7) corren contra el repositorio real.
- **[La demo comparte una sola conexión]** → Uso manual de un solo usuario; declarado en D3.

## A verificar en el change

| # | Qué | Verificar antes de | Cómo |
|---|---|---|---|
| V1 | Los ocho pins se instalan juntos en un entorno nuevo con Python 3.11, 3.12 o 3.13, con `python -m pip install --upgrade pip` y `python -m pip install --group test` desde `backend/`, sin compilar nada | crear el archivo de dependencias definitivo (tarea 1.1) | La instalación termina sin errores y `python -m pip list` muestra las ocho versiones de D1 y `pydantic-core 2.33.2` |
| V2 | `fastapi 0.115.14` funciona con `pydantic 2.11.10`, y el `TestClient` de `starlette 0.46.2` con `httpx 0.28.1` | escribir el primer test de API (grupo 12) | `python -c "from fastapi import FastAPI; from fastapi.testclient import TestClient"` en la tarea 1.1; después, el test de API de E1 |
| V3 | `SQLAlchemy 2.0.54` acepta el estilo usado (`DeclarativeBase`, `Mapped`, `mapped_column`, `TypeDecorator`, `StaticPool`) | persistir el primer turno (grupo 4) | Los tests del grupo 3 |
| V4 | SQLite devuelve aware UTC con `FechaHoraUTC` y compara bien los rangos | cerrar el primer change (en la práctica, antes del grupo 4) | `test_fechas_ida_y_vuelta.py` |
| V5 | SQLite en memoria con `StaticPool` y `check_same_thread=False` funciona entre el hilo del test y el del endpoint | escribir el resto de las pruebas de API (grupo 12) | El test de API de E1 |
| V6 | Declarar `422` en el router reemplaza el esquema por defecto en `/docs` | cerrar las pruebas de API | Mirar `/openapi.json` en la tarea 13.3 |
| V7 | `uvicorn 0.54.0` sirve la aplicación de `fastapi 0.115.14`, acepta `--factory` y `/docs` carga | escribir el README | Tarea 13.3 |
| V8 | `zoneinfo` encuentra `America/Argentina/Buenos_Aires` en Windows con `tzdata 2026.4` instalado | escribir los tests de E8 | Los tests de `test_intervalo.py` |
| V9 | `pytest 9.1.1` toma la configuración de `[tool.pytest.ini_options]` de `backend/pyproject.toml` | escribir el primer test (tarea 1.2) | La cabecera de `python -m pytest` muestra `configfile: pyproject.toml` |
| V10 | Un `pyproject.toml` sin tabla `[project]` es aceptado por `pip install --group` y por pytest | crear el archivo de dependencias definitivo (tarea 1.1) | Lo cubren V1 y V9; si `pip` lo rechaza, se vuelve a este design (D1), no se agrega la tabla por cuenta propia |
| V11 | En Python 3.14 la instalación intenta compilar `pydantic-core` (no hay binario) | escribir los requisitos del README | Opcional: probar `py -3.14 -m venv` en una carpeta aparte; si instala sin compilar, se corrige el requisito del README |

## Migration Plan

No hay nada que migrar: es el primer código del repositorio y la base es en memoria. Para deshacer el change alcanza con revertir sus commits. C-02 reemplazará `create_all` por una migración inicial equivalente a este esquema.

## Open Questions

Ninguna que bloquee el apply. El autor confirmó el 2026-10-07 (D139) tres de los cuatro puntos que esta sección listaba: E4 conserva sus dos códigos, RN-AG-10d es regla de negocio con `422`, y Pydantic 2.11.10 con Python 3.11 a 3.13. Queda **un punto que el autor debería confirmar antes de empezar**, porque condiciona el archivo de dependencias:

1. **Dependencias en grupos de `pyproject.toml`, sin tabla de proyecto**, instaladas con `python -m pip install --group test` (D1).

Las demás elecciones marcadas como **Propuesta** valen tal como están; si el autor quiere cambiar alguna, conviene hacerlo antes de empezar, porque el contrato HTTP (D4) y el algoritmo de referencias (D10) condicionan tests ya planificados.
