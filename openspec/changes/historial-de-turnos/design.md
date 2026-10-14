# Design: historial-de-turnos

Fecha del design: **2026-10-14**. Gobernanza **CRÍTICO** (registro de auditoría): nada de esto se implementa hasta que el autor revise y apruebe este documento, los specs y `tasks.md`.

**Respuesta del autor (2026-10-14): las cuatro preguntas abiertas se cierran con la propuesta del agente.** Quedan como decisiones del autor D158 (H1, dos capabilities), D159 (H4, actor), D160 (H14, turnos previos sin historial) y D161 (tamaño de `tasks.md`), registradas en `knowledge-base/10_preguntas_abiertas.md`. Las demás decisiones marcadas «Propuesta» siguen así hasta que el autor apruebe el plan completo.

Las decisiones se numeran **H1 a H17** («H» de historial) para no confundirlas con las D1..D157 de `knowledge-base/10_preguntas_abiertas.md`, las D1..D20 del design de C-01 ni las I1..I16 del de C-02. Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design, a confirmar) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»).

## Context

Motivación y alcance: ver `proposal.md`. Requisitos: `specs/historial-de-turnos/spec.md` y el delta de `specs/persistencia-postgresql/spec.md`. Acá va solo el estado actual que condiciona el cómo.

**Lo que dejaron C-01 y C-02** (leído del código, no supuesto):

- `application/crear_turno.py`: `_intentar_crear_turno` hace todo dentro de un `with uow:` (validación de entrada, RN-AG-10d, `bloquear_recursos`, `ocupados_en_el_intervalo`, `detectar_conflictos`, `uow.agenda.agregar`). `crear_turno` lo reintenta hasta `INTENTOS_ANTE_CARRERA` (3) si la base levanta `SolapamientoEnLaBase`. El turno se crea con `creado_en=reloj()`.
- `infrastructure/unidad_de_trabajo.py`: abre una sesión por uso, crea `self.agenda`, confirma al salir sin error y deshace si hubo uno (tiene su propio test de `rollback`).
- `application/puertos.py`: protocolos `RepositorioAgenda` y `UnidadDeTrabajo`. No hay lectura de un turno por id.
- `infrastructure/db/modelos.py`: seis tablas, `CONVENCION_DE_NOMBRES` (`pk_`, `fk_`, `uq_`, `ix_`), claves foráneas con `ondelete="RESTRICT"`, fechas con `FechaHoraUTC`.
- Migraciones `0001_esquema_inicial` y `0002_exclusion_de_solapamientos` (esta con SQL literal que no está en el modelo, D145).
- `api/errores.py`: tabla `_CLASES_DE_ERROR` por clase exacta (409, 422); una clase que no está ahí sube como 500. `_manejar_cuerpo_mal_formado` atiende todo `RequestValidationError` con el texto «el cuerpo no tiene el formato esperado» y quita el prefijo `body` de la ubicación.
- `ReferenciaInvalida.recurso` admite `prestacion`, `paciente`, `profesional` y `sillon`.
- Tests que la tabla nueva afecta: `tests/postgres/test_migraciones.py` exige exactamente las seis tablas de C-01 (`TABLAS_DE_C01`) en INF-1; los guards de fechas y de nombres recorren `Base.metadata` y van a ver la tabla nueva (deben seguir pasando sin tocarlos).
- El seed de la demo no crea turnos.

## Goals / Non-Goals

**Goals:**

- Que el historial nazca **inmutable en dos capas**: la aplicación no tiene con qué modificarlo y PostgreSQL lo rechaza aunque alguien entre por fuera.
- Que el evento `creado` sea **atómico** con el turno, sin una segunda transacción ni un efecto posterior.
- Dejar el **punto de extensión** listo para los changes siguientes: un tipo de evento nuevo es un valor de enumeración, una función de dominio que arma el evento y una llamada a `registrar` en su caso de uso.

**Non-Goals:**

- Ningún tipo de evento distinto de `creado`, ni sus `antes` (no hay cambios todavía).
- Atribuir el cambio a un usuario real (no hay usuarios hasta C-06 y C-07).
- Completar el historial de turnos guardados antes de la migración.
- Leer un turno (`GET /turnos/{id}`), filtrar o paginar el historial.
- Roles de base con privilegios mínimos, y un disparador equivalente en SQLite.
- Cambiar el contrato HTTP de `POST /turnos`.

## Decisions

### H1. Una capability nueva, `historial-de-turnos`, y un delta en `persistencia-postgresql` — Decisión del autor (D158)

E9, US-015 CA-1 e HIS-1 van en la capability nueva. E9 describe lo que deja en el historial la creación, no cómo responde `POST /turnos`, que no cambia; se aloja donde vive el historial, igual que E11 se alojó en `persistencia-postgresql` (D142). Así `creacion-de-turnos` no se toca.

El delta de `persistencia-postgresql` **no es opcional**: su requisito de INF-1 dice que una base migrada tiene solo las seis tablas de C-01, y con `evento_turno` eso es falso. Se generaliza a «la base migrada coincide con el modelo de datos» (lo que el test ya comprueba con `compare_metadata`), así los changes siguientes con migraciones no vuelven a tocar el requisito, solo la lista de ejemplo del escenario. El título del escenario «INF-1 Feliz - … esquema del primer change» se conserva porque `openspec validate` exige no perder escenarios en un MODIFIED; su contenido es el nuevo.

**Alternativas descartadas:** (a) dejar INF-1 sin tocar y migrar el test solo hasta `0002`: el requisito dice «hasta la última versión» y quedaría probando algo que nadie usa; (b) meter E9 en `creacion-de-turnos`: serían tres capabilities. **Choca con la regla «una sola capability»** de `config.yaml`: el autor aceptó tocar las dos capabilities como excepción de este change (D158).

### H2. Dependencias: ninguna nueva — Decisión del autor (D116, D137) + Propuesta

El change no agrega ningún paquete ni cambia ningún pin de `backend/pyproject.toml`. La columna JSON usa el tipo `JSON` de SQLAlchemy 2.0.54 (ya fijado), que funciona en SQLite y en PostgreSQL; las migraciones usan Alembic 1.20.0 (ya fijado); el disparador es SQL de PostgreSQL 17.10 (imagen ya fijada, D143). No se actualiza la línea de cabecera de consulta de versiones del archivo, porque no se consultó ni se eligió ninguna versión. La política de D133 no aplica: no hay pins nuevos.

### H3. El evento como tipo de dominio — Propuesta

En `backend/app/domain/turnos/eventos.py` (el árbol de `08` ya ubica `EventoTurno` en `domain/turnos/`), solo biblioteca estándar:

- `TipoEvento(StrEnum)` con **un solo valor**, `CREADO = "creado"`. Cada change agrega el suyo (regla dura 12: no implementar fuera del alcance).
- `ActorTipo(StrEnum)` con **un solo valor**, `USUARIO = "usuario"`; `paciente`, `sistema` y `webhook_mp` los agrega el change que los produce.
- `Actor` (dataclass congelada): `tipo: ActorTipo`, `id: str | None`.
- `EventoTurno` (dataclass congelada): `turno_id`, `tipo`, `actor_tipo`, `actor_id`, `ocurrido_en`, `antes`, `despues`, `motivo` e `id: int | None = None`, con los nombres y la nulabilidad de `04_modelo_de_datos.md`.
- `evento_creado(turno: Turno, actor: Actor) -> EventoTurno`: función pura. Exige `turno.id` (el evento cuelga de un turno guardado); `ocurrido_en = turno.creado_en` (el mismo instante, sin volver a leer el reloj); `antes = None`, `motivo = None`; `despues` es la foto de H5.

**Alternativa descartada:** enumerar los nueve tipos y los cuatro actores de la KB desde ahora. Son valores que ningún código produce ni ningún test ejerce, y cada uno trae reglas propias que deciden otros changes.

### H4. Actor del evento `creado` mientras no hay autenticación — Decisión del autor (D159)

`POST /turnos` lo usa el panel (recepcionista u odontólogo), así que el actor es un **usuario**, aunque todavía no se sepa cuál: `actor_tipo = "usuario"` y `actor_id = None`. `crear_turno` recibe un parámetro nuevo `actor: Actor` con valor por defecto `ACTOR_PANEL_SIN_AUTENTICAR = Actor(ActorTipo.USUARIO, None)`; el router no lo pasa. Cuando C-07 proteja la ruta, el router pasará el usuario del token y desde ahí los eventos nuevos llevan `actor_id`.

**Límite conocido (al README):** los eventos `creado` anteriores a C-07 quedan con `actor_id` vacío para siempre; no se completan después (sería editar el historial). **Alternativa:** `actor_tipo = "sistema"`. Se descarta porque «sistema» en la KB es la tarea periódica (`03`), y mezclaría dos orígenes que los reportes y la auditoría van a querer distinguir.

### H5. Contenido de `despues` en el evento `creado` — Propuesta

Un objeto JSON con la foto del turno al nacer: `estado`, `inicio`, `fin`, `duracion_minutos`, `paciente_id`, `prestacion_id`, `profesional_id` y `sillon_id`. Las fechas van como texto ISO 8601 en UTC con `Z` (`"2026-11-02T10:00:00Z"`), el mismo formato con que la API devuelve las fechas, con una función `a_texto_utc(valor)` en `domain/tiempo.py` que exige UTC (reusa `exigir_utc`). No van `id` (es `turno_id`), `consultorio_id` (sale del profesional) ni `creado_en` (es `ocurrido_en`).

**Por qué foto completa y no vacío:** cuando un change posterior cambie el turno, el historial ya tiene con qué comparar el primer estado sin depender de la fila actual (DD-05: reprogramar cambia el mismo turno). La aceptación de RN-TD-10 se sumará a este objeto en C-24 (D87).

### H6. Tabla `evento_turno` — Decisión del autor (`04` §EventoTurno) + Propuesta (tipos y nombres)

`EventoTurnoModelo` en `modelos.py`, tabla `evento_turno`:

| Columna | Tipo SQLAlchemy | Nulo | Nota |
|---|---|---|---|
| `id` | `int`, PK | no | `pk_evento_turno` |
| `turno_id` | `int`, `_fk("turno")` | no | `fk_evento_turno_turno_id`, `ON DELETE RESTRICT`: un turno con historial no se puede borrar |
| `tipo` | `String` | no | sin `CHECK` (ver abajo) |
| `actor_tipo` | `String` | no | sin `CHECK` |
| `actor_id` | `String` | sí | texto: puede ser id de usuario o de token (`04`) |
| `ocurrido_en` | `FechaHoraUTC` | no | fecha con zona |
| `antes` | `JSON` | sí | |
| `despues` | `JSON` | sí | |
| `motivo` | `String` | sí | |

Índice `ix_evento_turno_turno_id_ocurrido_en` sobre `(turno_id, ocurrido_en)`, el de la KB; sirve también de índice de la clave foránea (columna inicial).

**Sin `CHECK` sobre `tipo` ni `actor_tipo` (Propuesta):** cada change que agregue un tipo tendría que reemplazar la restricción con una migración más, y los valores ya los fija la enumeración de dominio, que es la única que escribe. **Alternativa:** un `CHECK` con la lista de valores, reemplazado en cada change; da una defensa más en la base a cambio de una migración por tipo nuevo.

**`JSON` y no `JSONB` (Propuesta):** la KB dice `json`, nadie consulta dentro del contenido y `JSON` es el mismo tipo en SQLite y en el modelo. `JSONB` en PostgreSQL necesitaría una variante por dialecto. **A verificar en el change** (antes de cerrar el grupo 3): que `compare_metadata` con `compare_type=True` no informe diferencias para las columnas `JSON` en PostgreSQL.

### H7. Puertos, repositorio y unidad de trabajo — Propuesta

- `puertos.py`: protocolo nuevo `RepositorioHistorial` con **solo dos métodos**: `registrar(evento) -> EventoTurno` (lo guarda y lo devuelve con su id) y `del_turno(turno_id) -> Sequence[EventoTurno]` (ordenado por `ocurrido_en` y, a igual momento, por `id`). `RepositorioAgenda` suma `existe_turno(turno_id) -> bool`. `UnidadDeTrabajo` suma el atributo `historial`.
- `infrastructure/repositories/historial.py`: `RepositorioHistorialSqlAlchemy(sesion)`; `registrar` hace `add` y `flush` (el commit es de la unidad de trabajo, como en `agregar`).
- `UnidadDeTrabajoSqlAlchemy.__enter__` crea también `self.historial` sobre **la misma sesión** que `self.agenda`: por eso turno y evento quedan en la misma transacción.

**Por qué un repositorio aparte y no métodos en `RepositorioAgenda`:** el historial es una capability propia que van a usar casos de uso que no son de agenda (seña, marcado). **Inmutabilidad en la aplicación:** el repositorio no tiene método de actualizar ni de borrar, y un test guard lo fija (H10).

### H8. `crear_turno` registra el evento en el mismo intento — Propuesta

En `_intentar_crear_turno`, dentro del mismo `with uow:` y justo después de `turno = uow.agenda.agregar(...)`: `uow.historial.registrar(evento_creado(turno, actor))`, y se devuelve el turno. Consecuencias:

- Un rechazo (validación de entrada, RN-AG-10d, solapamiento) se levanta **antes** de `agregar`: no se llega a registrar nada (E9, error de negocio).
- Si la base rechaza el turno por una carrera (`SolapamientoEnLaBase` en el `flush` de `agregar`), tampoco se llega a `registrar`, y el reintento de `crear_turno` arma un evento nuevo con el turno nuevo. No cambia nada de C-02.
- Si `registrar` falla, la excepción sale del `with` y la unidad de trabajo deshace también el turno (E9, borde).
- La respuesta de `POST /turnos` no cambia: sigue devolviendo el turno.

**Alternativa descartada:** registrar el evento en la unidad de trabajo o con un evento de SQLAlchemy (`after_insert`). Esconde la regla de negocio en la infraestructura y no sirve para los eventos de otros changes, que necesitan `antes`, `motivo` y un actor que solo conoce el caso de uso.

### H9. Leer el historial y el `404` — Decisión del autor (RN-GL-04: URL → `404`) + Propuesta (forma)

- `application/historial.py`: `consultar_historial(turno_id, uow) -> Sequence[EventoTurno]`. Dentro de `with uow:`: si `not uow.agenda.existe_turno(turno_id)`, levanta `TurnoNoEncontrado(turno_id)`; si no, devuelve `uow.historial.del_turno(turno_id)`. Un turno sin eventos devuelve una lista vacía (spec, borde).
- `domain/errors.py`: `TurnoNoEncontrado(ErrorDeDominio)` con `codigo = "RN-GL-04"` y `referencias = (ReferenciaInvalida("turno", turno_id, "inexistente"),)`; `ReferenciaInvalida.recurso` suma `"turno"`. Es una clase aparte de `RecursoNoEncontrado` porque esta va dentro de `EntradaInvalida` y sale como `422`.
- `api/errores.py`: `TurnoNoEncontrado: (404, "/errores/recurso-no-encontrado", "Recurso no encontrado")`, con `detail` «No existe el turno 999.» y la lista `referencias`, en `application/problem+json` como el resto de los errores.
- `api/routers/turnos.py` (mismo router, prefijo `/turnos`): `GET /{turno_id}/historial`, `def` síncrono, `turno_id: int`, `response_model=list[EventoTurnoSalida]`, con `404` y `422` declarados con el esquema `Problema` en OpenAPI. `EventoTurnoSalida` en `esquemas.py`, con los nueve campos del spec; `antes` y `despues` como `dict[str, object] | None`. La respuesta es una **lista**, no un objeto que la envuelva (KISS; si un change necesita paginar, cambia la forma con su propio spec).
- **Id que no es entero** (`/turnos/abc/historial`): lo rechaza FastAPI con `RequestValidationError` y lo atiende el manejador existente. Se ajusta para que (a) quite también el prefijo `path` de la ubicación (`campo = "turno_id"`) y (b) diga «la ruta no tiene el formato esperado» cuando ningún error está en el cuerpo. **A verificar en el change** (antes del GREEN del grupo 6): que ningún test de C-01 compare ese `detail` de forma que el ajuste lo rompa.

### H10. Solo lectura en la aplicación y por HTTP (US-015 CA-1) — Propuesta

- La ruta del historial solo declara `GET`. Un `POST`, `PUT`, `PATCH` o `DELETE` a ella lo responde el enrutador con `405`. **A verificar en el change** (antes del GREEN del grupo 6): que FastAPI 0.115.14 responda `405` y no `404` para un método no declarado en una ruta existente. La respuesta `405` no sale como `application/problem+json` (la arma Starlette); el spec solo exige el estado y que el historial no cambie.
- Test guard: los métodos públicos de `RepositorioHistorialSqlAlchemy` son exactamente `registrar` y `del_turno`. Si un change agrega un método de modificación, el test falla y obliga a discutirlo.
- Los tests de API comprueban, después de cada método rechazado, que el historial sigue con el mismo evento.

### H11. Inmutabilidad en la base: disparador solo en PostgreSQL — Decisión del autor («ni la aplicación ni la base exponen `UPDATE` ni `DELETE`», `04`) + Propuesta (el cómo)

Migración aparte, **`0004_historial_solo_insercion`**, con SQL literal que no está en el modelo (como la restricción de exclusión, D145):

- Función `evento_turno_solo_insercion()` (`RETURNS trigger`, `LANGUAGE plpgsql`) que hace `RAISE EXCEPTION 'evento_turno es de solo inserción (RN-AG-11)'`.
- Disparador `tg_evento_turno_sin_modificar`: `BEFORE UPDATE OR DELETE ON evento_turno FOR EACH ROW`.
- Disparador `tg_evento_turno_sin_vaciar`: `BEFORE TRUNCATE ON evento_turno FOR EACH STATEMENT`.
- `downgrade`: borra los dos disparadores y la función.

**Por qué un disparador y no quitar permisos:** la aplicación se conecta con el dueño de la tabla (usuario `app` de Compose), y el dueño puede devolverse cualquier permiso que se le quite; un rol aparte sin `UPDATE` es configuración de producción, fuera de alcance. El disparador frena también al dueño. **Límite:** un superusuario puede deshabilitarlo o borrarlo; un `DROP TABLE` (incluido el `downgrade` de `0003`) no lo frena, y no tiene que frenarlo.

**Por qué dos migraciones (`0003` tabla, `0004` disparador):** el orden de TDD (la tabla se prueba con INF-1 antes de que exista el disparador) y la misma separación que `0001` y `0002`. **Sin disparador en SQLite:** la suite por defecto no depende de garantías propias de PostgreSQL; la inmutabilidad en la base se prueba en el perfil `postgres`. **A verificar en el change** (antes de cerrar el grupo 7): que el `TRUNCATE` sobre la tabla se rechace y que `DROP SCHEMA public CASCADE` del fixture del perfil siga funcionando con la función y los disparadores.

### H12. Migración `0003_historial_de_turnos` — Decisión del autor (DD-15) + Propuesta

Se genera con `alembic revision --autogenerate` contra `turnos_test` migrada a `0002` y se **revisa a mano** contra `modelos.py`: solo `create_table("evento_turno", ...)` con los nombres de H6 y el índice, y su `downgrade` con `drop_index` y `drop_table`. Ningún cambio en las tablas existentes. **No completa eventos** para los turnos ya guardados (ver H14).

### H13. Clasificación de los rechazos y orden de evaluación (RN-GL-02) — Propuesta

| Operación | Rechazo | Clase | HTTP | Código |
|---|---|---|---|---|
| `GET /turnos/{id}/historial` | id que no es entero | Validación de entrada (petición mal formada) | `422` | ninguno |
| `GET /turnos/{id}/historial` | turno inexistente en la URL | Recurso identificado en la URL (RN-GL-04) | `404` | `RN-GL-04` |
| `POST/PUT/PATCH/DELETE` a la ruta del historial | método no admitido | Protocolo (no es regla de negocio) | `405` | ninguno |
| `POST /turnos` | sin rechazos nuevos | — | igual que C-01 y C-02 | — |
| Base (perfil `postgres`) | `UPDATE`, `DELETE`, `TRUNCATE` de un evento | Garantía de la base, sin ruta HTTP que la dispare | — | — |

Orden en `GET`: (1) formato del id (lo hace FastAPI antes del caso de uso); (2) existencia del turno; (3) lectura. Hay una sola referencia, así que no hay nada que acumular. En `POST /turnos` el orden de C-01 no cambia; el registro del evento va después de todas las reglas y no puede fallar por una regla de negocio: una falla ahí es un error técnico (`500`) con todo deshecho.

### H14. Turnos anteriores a la migración — Decisión del autor (D160)

Un turno guardado en PostgreSQL antes de `0003` (por ejemplo, el de la prueba manual de C-02) no tiene evento `creado`. **No se inventa**: su historial es una lista vacía (spec, borde). **Alternativa:** que `0003` inserte un `creado` por cada turno existente, con `actor_tipo = "sistema"`, `ocurrido_en = creado_en` y `motivo = "migración C-03"`. Se descarta porque escribiría como hecho algo que nadie registró en su momento. En la demo con SQLite no hay turnos previos.

### H15. Tests: dónde va cada uno — Propuesta

| Escenario | Test | Capa |
|---|---|---|
| E9 (armado del evento) | `tests/unit/test_eventos.py` | Unit, sin base |
| E9 feliz, error de negocio y borde | `tests/integration/test_historial.py` | Caso de uso + SQLite |
| E9 por HTTP | `tests/api/test_historial.py` | `TestClient` |
| US-015 CA-1 (lectura, orden, vacía, otros turnos) | `tests/integration/test_historial.py` y `tests/api/test_historial.py` | Integración y API |
| US-015 CA-1 (solo lectura por HTTP y guard del repositorio) | `tests/api/test_historial.py`, `tests/integration/test_repositorio_historial.py` | API e integración |
| HIS-1 (`404` y `422`) | `tests/integration/test_historial.py` y `tests/api/test_historial.py` | Integración y API |
| US-015 CA-1 (la base rechaza) | `tests/postgres/test_historial_inmutable.py` | Perfil `postgres` |
| INF-1 (modificado) | `tests/postgres/test_migraciones.py` | Perfil `postgres` |

**E9 borde sin dobles (Propuesta):** para que falle el registro del evento sin un mock ni un repositorio falso, el test crea en la base SQLite del test un disparador `BEFORE INSERT ON evento_turno` que hace `SELECT RAISE(ABORT, ...)`. La falla es real, del `flush` de `registrar`, después del `flush` del turno; el test comprueba con otra sesión que no quedó ni turno ni evento. **A verificar en el change** (antes de escribir ese test, tarea 4.3): que SQLAlchemy propague el `RAISE(ABORT)` de SQLite como `IntegrityError` u `OperationalError` y que la unidad de trabajo haga `rollback`.

Factory nueva en `tests/factories.py`: `un_evento(sesion, turno, **kw)`, para guardar eventos directamente (orden cronológico y turno sin eventos se arman con `un_turno`, que no registra evento). Datos ficticios (RN-PR-01), reloj fijo (`RELOJ_FIJO`).

### H16. README — Propuesta

Suma: `GET /turnos/{id}/historial` en la sección de la demo (con la petición de ejemplo: crear el turno de ejemplo y consultar `GET /turnos/1/historial`), la tabla escenario → test de E9, US-015 CA-1 e HIS-1, la mención de `0003` y `0004` en «Migraciones», y tres límites conocidos: la ruta del historial no tiene autenticación (DD-14), los eventos anteriores a C-07 no tienen `actor_id` (H4), y los turnos guardados antes de `0003` no tienen historial (H14). La garantía de la base (H11) se menciona junto a INF-1 y E11, como algo que solo prueba el perfil `postgres`.

### H17. Commits y forma de trabajo del Apply — Propuesta (continúa I16 de C-02)

Mismo criterio que C-02: el sub-agente de cada grupo commitea dentro del grupo (`test:` al cerrar cada RED con la salida en rojo en el cuerpo, `feat:` o `chore:` al cerrar cada GREEN, triangulación y refactor en commits propios), en español, con prefijo y la línea `Co-Authored-By`, sin `--amend` ni reescritura. Por ser CRÍTICO, el Apply no empieza hasta la aprobación de este plan; una vez aprobado, el autor confirma si se encadenan los grupos frenando solo ante un desvío, como en C-02 (regla dura 10). La prueba en el navegador la hace primero el agente y después el autor repite el paso a paso, antes de archivar.

### Skills aplicadas

- **fastapi-templates**: ruta `def` síncrona en el router; el router no toca el ORM y responde con un esquema (`EventoTurnoSalida`), no con el modelo; errores de dominio traducidos en `api/errores.py` (`404` con código RN). Sin JWT (llega en C-06 y C-07).
- **python-design-patterns**: un repositorio por responsabilidad (agenda e historial), inyectados por la unidad de trabajo; la foto del evento es una función pura de dominio; la regla «registrar el evento» vive en el caso de uso y no en un evento del ORM (H8).
- **python-error-handling**: `TurnoNoEncontrado` con código RN, mapeado a HTTP solo en la capa de API; cada camino de error con su test (`404`, `422`, `405`, falla del registro).
- **python-testing-patterns**: AAA, nombres `test_<escenario>_…`, parametrización para triangular, base SQLite real por test, reloj fijo; sin mocks de sesión ni de repositorio (la falla de E9 borde es un disparador real de SQLite, H15).
- **database-migration**: dos migraciones reversibles, autogenerado revisado a mano, sin patrones destructivos sobre datos existentes; `downgrade` probado.
- **supabase-postgres-best-practices** (solo lo genérico de PostgreSQL): índice que cubre la clave foránea, `timestamptz`, `snake_case`, función de disparador con nombre estable; las garantías propias de PostgreSQL quedan en el perfil `postgres`, no en la suite por defecto.

## Contradicciones y huecos encontrados en las fuentes

1. **«Una sola capability» frente a INF-1.** `config.yaml` pide una sola capability por change, y el requisito INF-1 de `persistencia-postgresql` queda falso con la tabla nueva. No hay forma de agregar una tabla sin tocarlo (H1). Resuelto: se aceptan las dos capabilities (D158).
2. **Actor sin autenticación.** `04` lista `usuario`, `paciente`, `sistema` y `webhook_mp`, pero no dice qué actor lleva un cambio hecho por el panel antes de C-07. Resuelto: `usuario` con `actor_id` vacío hasta C-07 (D159).
3. **`HIS-1` con `RN-GL-04`.** `CHANGES.md` pide `404` con `RN-GL-04`; RN-GL-04 está redactada para referencias en el cuerpo (`422`) y solo dice que un recurso de la URL devuelve `404`, sin decir con qué código. Este design usa `RN-GL-04` también en el `404` (lo que dice `CHANGES.md`) y lo marca para confirmar en la KB al cerrar.
4. **`despues` del evento `creado`.** `04` dice «estado nuevo» sin fijar qué campos. H5 propone la foto completa.
5. **«La base no expone `UPDATE` ni `DELETE`» sin mecanismo.** `04` no dice cómo; H11 propone un disparador solo en PostgreSQL y nada en SQLite.
6. **`RN-AG-11` en `05` sigue diciendo «fuera del primer change: se implementa en el change siguiente»**, y `07` (Flujo 1, paso 8) y `08` («Contrato del primer change») dicen que el `EventoTurno(creado)` queda fuera. Son correctas para C-01; al archivar C-03 se actualizan a «implementado en C-03» en el commit `docs(kb)`.
7. **Tamaño.** `tasks.md` tiene 24 tareas en 9 grupos, frente a «alrededor de 20» de `CHANGES.md`. Resuelto: cuarta excepción registrada (D161).

## Risks / Trade-offs

- [El disparador solo existe en PostgreSQL; en SQLite un `UPDATE` directo pasa] → La suite por defecto prueba la inmutabilidad de la aplicación (sin métodos de modificación, `405`); la de la base se prueba en el perfil `postgres` y el README lo dice.
- [Un superusuario puede deshabilitar el disparador] → Aceptado: es un entorno local con datos ficticios; un rol de aplicación sin privilegios es configuración de producción (fuera de alcance).
- [`actor_id` vacío en los eventos anteriores a C-07] → Límite documentado en el README; no se completa después, porque eso sería modificar el historial.
- [Sin `CHECK` sobre `tipo` y `actor_tipo`, una escritura directa en la base puede guardar un valor inventado] → Solo el dominio escribe, con enumeraciones; el `CHECK` queda como alternativa si el autor la prefiere (H6).
- [Cada evento suma una escritura a `POST /turnos`] → Es un `INSERT` en la misma transacción y sobre una tabla con un índice; no cambia el bloqueo por recurso de C-02, que se toma antes.
- [`ON DELETE RESTRICT` impide borrar un turno con historial] → Es lo buscado: un turno no se borra, se cancela (RN-AG-12). Ningún código ni test borra turnos.
- [La foto de `despues` queda atada a los nombres de campo de hoy] → Es un registro histórico: si un change renombra un campo, los eventos viejos conservan el nombre viejo. Se documenta en el design de ese change si llegara a pasar.

## A verificar en el change

| # | Qué | Antes de qué |
|---|---|---|
| V1 | `compare_metadata` (con `compare_type=True`) no informa diferencias para `evento_turno` ni para sus columnas `JSON` en PostgreSQL (H6, H12) | Cerrar el grupo 3 |
| V2 | El `RAISE(ABORT)` de un disparador de SQLite sube por SQLAlchemy y la unidad de trabajo deshace el turno ya enviado (H15) | Escribir el test de borde de la tarea 4.3 |
| V3 | FastAPI 0.115.14 responde `405` a un método no declarado en una ruta existente (H10) | El GREEN del grupo 6 |
| V4 | Ningún test de C-01 compara el `detail` del `422` de cuerpo mal formado de forma que el ajuste de H9 lo rompa | El GREEN del grupo 6 |
| V5 | El disparador rechaza `UPDATE`, `DELETE` y `TRUNCATE`, acepta `INSERT`, y `DROP SCHEMA public CASCADE` del fixture del perfil sigue funcionando (H11) | Cerrar el grupo 7 |
| V6 | `downgrade` a `0002` deja exactamente las seis tablas de C-01 y ninguna función de la aplicación; `downgrade base` sigue dejando la base vacía (INF-1) | Cerrar el grupo 7 |
| V7 | Con Compose, el contenedor `api` aplica `0003` y `0004` al arrancar sobre la base de C-02 que ya tiene turnos, y el historial de esos turnos responde `[]` (H14) | La prueba en el navegador (grupo 8) |

## Migration Plan

1. `alembic upgrade head` aplica `0003` (tabla e índice) y `0004` (función y disparadores). En Compose lo hace el arranque del contenedor `api` (D151); no hay pasos manuales.
2. Los turnos existentes no se tocan y quedan sin evento (H14).
3. **Vuelta atrás:** `alembic downgrade 0002` borra disparadores, función, índice y tabla (se pierden los eventos registrados, que en este entorno son ficticios); el código de C-02 vuelve a funcionar sin cambios sobre esa base.
4. La demo con SQLite (`crear_app_demo`) no necesita nada: `create_all` crea la tabla.

## Open Questions

Ninguna. Las cuatro preguntas abiertas de este design las cerró el autor el 2026-10-14 eligiendo la propuesta del agente: dos capabilities (D158, H1), actor `usuario` con `actor_id` vacío hasta C-07 (D159, H4), turnos previos a la migración sin historial (D160, H14) y 24 tareas como cuarta excepción de tamaño (D161).

Quedan marcadas «Propuesta», y el autor puede cambiarlas sin tocar el plan: sin `CHECK` en `tipo` y `actor_tipo` (H6), `JSON` y no `JSONB` (H6), la respuesta como lista (H9), el texto de `detail` del `422` de ruta (H9) y el tipo `/errores/recurso-no-encontrado` (H9).
