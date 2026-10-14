# Design: gestion-de-prestaciones

Fecha del design: **2026-10-14**. Gobernanza **BAJO** (catálogo): autonomía completa en el Apply si los tests pasan. Antes del Apply, el autor responde las preguntas de «Open Questions» (Q1 a Q4): cambian el spec o las tareas.

**Respuesta del autor (2026-10-14): las cuatro preguntas abiertas se cierran con la recomendación del agente.** Quedan como decisiones del autor D171 (P6, código RN-AG-15), D172 (P7, comparación normalizada del nombre), D173 (P3, consultorio único) y D174 (P12 y P13, colores), registradas en `knowledge-base/10_preguntas_abiertas.md`. Las demás decisiones marcadas «Propuesta» siguen así hasta que el autor apruebe el plan completo.

Las decisiones se numeran **P1 a P17** («P» de prestaciones) para no confundirlas con las D1..D174 de `knowledge-base/10_preguntas_abiertas.md`, las D1..D20 del design de C-01, las I1..I16 de C-02 ni las H1..H17 de C-03. Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design, a confirmar) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»).

## Context

Motivación y alcance: ver `proposal.md`. Requisitos: `specs/gestion-de-prestaciones/spec.md`. Acá va solo el estado actual que condiciona el cómo.

**Lo que dejaron C-01, C-02 y C-03** (leído del código, no supuesto):

- `infrastructure/db/modelos.py`: `PrestacionModelo` con `id`, `consultorio_id`, `nombre`, `duracion_minutos` y `activa` (Python `default=True`); `UniqueConstraint("consultorio_id", "nombre")`, que por `CONVENCION_DE_NOMBRES` se llama `uq_prestacion_consultorio_id_nombre`, y `ck_prestacion_duracion_positiva` (`duracion_minutos > 0`). No hay `color` ni `reservable_online` (D130).
- `domain/agenda/recursos.py`: `Prestacion(id, consultorio_id, duracion_minutos, activa)`, el dato mínimo que usa `crear_turno`. `RepositorioAgendaSqlAlchemy.prestacion(id)` lo arma desde el modelo.
- `crear_turno` ya rechaza una prestación **inactiva** o de otro consultorio con `RN-GL-04` (`422`, E12) y copia la duración al turno (`Turno.duracion_minutos`, `fin`): RN-AG-02 ya se cumple; nada lee la prestación después de crear el turno.
- `domain/errors.py`: `EntradaInvalida` agrupa errores de entrada (hoy `FechaNoUTC` y `RecursoNoEncontrado`); `TurnoNoEncontrado` es el `404` con `RN-GL-04` (D166). `ReferenciaInvalida.recurso` ya admite `prestacion`.
- `api/errores.py`: `_CLASES_DE_ERROR` por clase exacta; una clase que no está ahí sube como `500`. `_problema_de_entrada` arma los `errores` de campo **solo** para `FechaNoUTC`, con un mensaje fijo de fecha. `_manejar_cuerpo_mal_formado` atiende todo `RequestValidationError` (cuerpo o ruta) con `codigos` vacío.
- `api/routers/turnos.py`: `_PROBLEMA_JSON` y `_respuesta_de_error` viven en el router de turnos.
- `application/puertos.py`: `RepositorioAgenda`, `RepositorioHistorial`, `UnidadDeTrabajo` (`agenda` e `historial` sobre la misma sesión) y `SolapamientoEnLaBase` (excepción de infraestructura que el caso de uso traduce).
- Migraciones `0001` a `0004`, solo PostgreSQL (D145). `env.py` compara con `compare_type=True` (no compara `server_default`). INF-1 (`tests/postgres/test_migraciones.py`) compara la base migrada con `Base.metadata` con `compare_metadata` y deshace hasta `0002` y hasta `base`.
- `seed_demo.py`: cinco prestaciones con ids 1 a 5 (D56), sin color; `cargar_demo_si_falta` no vuelve a cargar si el consultorio 1 ya existe; `ajustar_secuencias` ya avanza la secuencia de `prestacion` en PostgreSQL, así que un `POST /prestaciones` en Compose no choca con los ids fijos.
- `tests/factories.py`: `una_prestacion` sin color. `tests/api/test_demo.py` comprueba las cinco duraciones del seed.
- KB: «un solo consultorio por instalación en el MVP» (`02`); `color` hex `#RRGGBB` validado en la API (†, `04`); `reservable_online` default `false` (†); `UNIQUE(consultorio_id, nombre)` (`04`); la duración inválida se rechaza con el error de dominio `RN-AG-01` (`05`, D99, D131).

## Goals / Non-Goals

**Goals:**

- Que RN-AG-01 viva en el **dominio** como funciones puras, con la granularidad como **una constante con nombre**, para que C-22 la reemplace por el valor de `ConfiguracionReglas` cambiando solo de dónde sale el número.
- Que la unicidad del nombre no dependa de cómo se escribió (mayúsculas, acentos, espacios) y que la base siga siendo la última red para el caso exacto.
- Que la prueba de CA-3 sea **observable por la API**, sin leer filas a mano: un turno nuevo choca o no choca según el fin congelado del turno viejo.

**Non-Goals:**

- Ningún cambio en `crear_turno` ni en `recursos.Prestacion`: ya cumplen RN-AG-02 y el rechazo de la prestación inactiva.
- Validar en la base la granularidad (sería un `CHECK` que C-22 tendría que deshacer) o el formato del color.
- Un catálogo de colores, normalizar el color a mayúsculas o validar contraste.
- Optimistic locking o control de concurrencia entre dos ediciones de la misma prestación (sin usuarios, gana la última escritura).
- Generalizar los errores «no encontrado en la URL» en una jerarquía (ver P5).

## Decisions

### P1. Una capability nueva, sin deltas — Propuesta

`gestion-de-prestaciones` aloja US-001 CA-1, CA-2 y CA-3. **No se modifica `persistencia-postgresql`**: INF-1 ya dice, desde C-03 (D158), que la base migrada coincide con el modelo de la aplicación y compara columnas, tipos y nulabilidad; `0005` no agrega tablas, así que la lista de tablas del escenario feliz y el escenario «deshacer solo las migraciones del historial» (que baja a `0002` y deja las seis tablas del primer change) siguen siendo ciertos tal como están. Tampoco `creacion-de-turnos` (E12 ya cubre la prestación inactiva) ni `historial-de-turnos`. Cumple «una sola capability» de `openspec/config.yaml` sin excepción.

**Alternativa descartada:** un delta en `persistencia-postgresql` con un escenario de `0005`: repetiría lo que INF-1 ya exige. La comprobación propia de `0005` (las filas existentes reciben color) va como test del perfil, bajo INF-1 (P15).

### P2. Dependencias: ninguna nueva — Decisión del autor (D116, D137) + Propuesta

No se agrega ningún paquete ni cambia ningún pin de `backend/pyproject.toml`. Lo que se usa ya está fijado: FastAPI 0.115.14 y Pydantic 2.11.10 (`Field(pattern=...)`, `AfterValidator`, `model_fields_set`), SQLAlchemy 2.0.54 (`IntegrityError`), Alembic 1.20.0 (`add_column`, `alter_column`) y la biblioteca estándar (`unicodedata`) en el dominio. La política de pins de D133 no aplica porque no se elige ninguna versión.

### P3. El consultorio de la petición: el único de la instalación — Decisión del autor (D173; Q3)

Sin autenticación no hay un usuario del que sacar el consultorio, y la KB dice que hay **un solo consultorio por instalación en el MVP** (`02`). El caso de uso pide a la unidad de trabajo `uow.prestaciones.consultorio_unico()`: el id del único consultorio. Si no hay exactamente uno, es un error de configuración de la instalación y sube como `500` (no es un error de la petición ni tiene código RN). `GET` lista las de ese consultorio, `POST` crea en él y `PATCH` busca la prestación por id (con un solo consultorio, toda prestación es suya; el filtro por consultorio llega con C-07, cuando la sesión lo defina). Cuando C-07 proteja las rutas, el consultorio sale de la sesión y se reemplaza esa sola llamada.

**Alternativas descartadas:** `consultorio_id` en el cuerpo y en la consulta (el cliente elegiría un dato que en la v1 no puede variar, y C-07 lo tendría que quitar del contrato) y el id `1` fijo (ata el código al seed de la demo).

### P4. Reglas de la prestación en el dominio — Propuesta

Módulo nuevo `backend/app/domain/agenda/prestaciones.py`, solo biblioteca estándar:

- `GRANULARIDAD_MINUTOS = 5` (D99; C-22 la reemplaza por `ConfiguracionReglas`).
- `duracion_valida(minutos: int, granularidad: int = GRANULARIDAD_MINUTOS) -> bool`: `minutos > 0 and minutos % granularidad == 0` (RN-AG-01).
- `normalizar_espacios(nombre: str) -> str`: quita los espacios de los extremos y colapsa los internos (` "  Control   de ortodoncia " → "Control de ortodoncia"`). Es lo que se guarda.
- `clave_de_nombre(nombre: str) -> str`: `normalizar_espacios`, `casefold()` y sin marcas diacríticas (`unicodedata.normalize("NFKD", ...)` sin los caracteres de categoría `Mn`). Solo se usa para comparar; nunca se guarda (P7).
- `nombre_repetido(nombre, existentes, excepto_id=None) -> DatosPrestacion | None`: la primera prestación de `existentes` con la misma clave, salvo la que se edita.
- `DatosPrestacion` (dataclass congelada): `id: int | None`, `consultorio_id`, `nombre`, `duracion_minutos`, `color`, `reservable_online`, `activa`. Es el catálogo completo; `recursos.Prestacion` sigue siendo el dato mínimo que usa `crear_turno` (no se toca, Non-Goals).

**Alternativa descartada:** sumar `nombre`, `color` y `reservable_online` a `recursos.Prestacion`: obligaría a tocar `crear_turno`, su repositorio y sus tests sin que los necesiten.

### P5. Errores nuevos — Propuesta

En `domain/errors.py`:

- `DuracionInvalida(campo="duracion_minutos")`, código `RN-AG-01`, **validación de entrada**: viaja dentro de `EntradaInvalida`, como `FechaNoUTC`. Mensaje: «El campo 'duracion_minutos' debe ser mayor que 0 y múltiplo de 5 minutos.» (el 5 sale de la constante).
- `NombreDePrestacionRepetido(nombre)`, código `RN-AG-15` (D171), **regla de negocio**: `409`, `type` `/errores/nombre-repetido`, `title` «Nombre repetido», `detail` «Ya existe una prestación llamada «Limpieza».» con el nombre **guardado** de la existente.
- `PrestacionNoEncontrada(prestacion_id)`, código `RN-GL-04`, `404`, con una `ReferenciaInvalida("prestacion", id, "inexistente")`, igual que `TurnoNoEncontrado` (D166).

En `api/errores.py`: las dos clases nuevas van a `_CLASES_DE_ERROR` (`PrestacionNoEncontrada` comparte `type` y `title` con `TurnoNoEncontrado`); `_problema_de` atiende `PrestacionNoEncontrada` como `TurnoNoEncontrado` y `NombreDePrestacionRepetido` con su `detail`; `_problema_de_entrada` deja de suponer que todo error de campo es de fecha: cada error de campo lleva **su propio** mensaje (`MENSAJE_FECHA_NO_UTC` para `FechaNoUTC`, el de `DuracionInvalida` para la duración). El `422` de `POST /turnos` no cambia (test de C-01 sin tocar).

**Por qué no una jerarquía «no encontrado en la URL»:** con `TurnoNoEncontrado` y `PrestacionNoEncontrada` son dos casos; C-05 (`gestion-de-sillones`, en paralelo) suma el tercero. Regla de tres: se generaliza ahí, no acá.

### P6. Código del nombre repetido: `RN-AG-15` — Decisión del autor (D171; Q1)

US-001 CA-1 exige el nombre único, pero **la KB no le da código RN**, y la regla dura 4 prohíbe un error de regla de negocio sin su código. El autor creó una regla nueva: **RN-AG-15** (fija): «el nombre de una prestación es único en el consultorio, activas e inactivas, sin distinguir mayúsculas, acentos ni espacios de más; un alta o una edición que lo repita se rechaza con `409`». Es el siguiente número libre de la serie `RN-AG` (la última es RN-AG-14, D125). Al archivar se agrega a `05_reglas_de_negocio.md` y a US-001 (`Reglas`).

**Alternativa:** reusar `RN-AG-01`, que define la tabla de prestaciones. Descartada como recomendación: un mismo código para la duración (`422`, entrada) y el nombre (`409`, negocio) obliga a leer el detalle para distinguirlos.

### P7. Unicidad del nombre: normalizada en el dominio, exacta en la base — Decisión del autor (D172; Q2)

El caso de uso lee las prestaciones del consultorio y pregunta a `nombre_repetido` (P4). La comparación ignora mayúsculas, acentos y espacios de más (la misma normalización que RN-TD-09 usa para nombres de pacientes), porque «Limpieza» y «limpieza» en la misma agenda son la misma prestación para quien la usa. Las inactivas cuentan: el nombre sigue ocupado para poder reactivarla.

La restricción `uq_prestacion_consultorio_id_nombre` **se mantiene igual** (exacta, sobre el nombre ya normalizado de espacios): cubre la carrera de dos altas idénticas simultáneas. El repositorio traduce el `IntegrityError` de esa restricción, al hacer `flush`, a `NombreRepetidoEnLaBase` (excepción de infraestructura en `puertos.py`, como `SolapamientoEnLaBase`), y el caso de uso la convierte en `NombreDePrestacionRepetido`.

**Límite aceptado:** dos altas **simultáneas** que difieran solo en mayúsculas o acentos pasan las dos; sin usuarios ni concurrencia real en el panel, no se justifica una columna normalizada con su propio `UNIQUE` (se registra en Risks).

**Alternativas descartadas:** un índice único sobre `lower(nombre)` (en SQLite `lower` solo baja ASCII y no quita acentos: la suite por defecto y PostgreSQL se comportarían distinto) y una columna `nombre_clave` (columna que la KB no tiene; descartada por el autor en D172).

### P8. Clasificación de los rechazos y orden de evaluación (RN-GL-02) — Propuesta

| Rechazo | Clase | Estado | Código |
|---|---|---|---|
| Cuerpo mal formado: campo ausente en el alta, campo de más, tipo erróneo, `null` explícito en la edición, `color` que no es `#RRGGBB`, `nombre` vacío tras normalizar espacios, id de la ruta que no es entero | Validación de entrada (formato, Pydantic) | `422` | sin código |
| Prestación de la URL inexistente o de otro consultorio | Validación de entrada (URL) | `404` | `RN-GL-04` |
| `duracion_minutos` no mayor que 0 o no múltiplo de 5 | Validación de entrada | `422` | `RN-AG-01` |
| Nombre repetido en el consultorio | Regla de negocio | `409` | `RN-AG-15` |

Orden: **formato → prestación de la URL → RN-AG-01 → RN-AG-15**. Si el formato falla no se evalúa nada más (D135 d). La prestación de la URL va antes que la duración porque sin prestación no hay nada que editar. RN-AG-01 se informa dentro de un `EntradaInvalida` (hoy es el único error de entrada de dominio de estas rutas, pero queda listo para sumarse a otros). El nombre repetido se evalúa solo con la entrada válida y de a una (es la única regla de negocio de estas rutas).

**Por qué RN-AG-01 es entrada y no negocio:** la duración se juzga por sí sola contra la granularidad; no depende de lo que haya guardado. **Por qué no lo valida Pydantic:** la KB lo define como error de dominio con código (`05`), y C-22 va a leer la granularidad de la base; con Pydantic saldría `422` sin código.

### P9. Esquemas HTTP — Propuesta

En `api/esquemas.py`, con `extra="forbid"` y ejemplos de la demo para `/docs`:

- `CrearPrestacionEntrada`: `nombre: str` (con `AfterValidator(normalizar_espacios)` y longitud mínima 1 después de normalizar), `duracion_minutos: int`, `color: str` con `pattern=r"^#[0-9A-Fa-f]{6}$"`, `reservable_online: bool = False`. El color se guarda tal como llega.
- `EditarPrestacionEntrada`: los mismos cinco campos más `activa`, todos opcionales; un `null` explícito se rechaza como formato (un `model_validator(mode="before")` que no admite valores nulos; V2). El router arma el comando solo con `model_fields_set`. Un cuerpo vacío (`{}`) es válido y responde `200` sin cambios.
- `PrestacionSalida`: `id`, `nombre`, `duracion_minutos`, `color`, `reservable_online`, `activa`. Sin `consultorio_id`: en la v1 hay uno solo (P3).

### P10. Casos de uso — Propuesta

`backend/app/application/prestaciones.py`, sin `commit()` ni SQL (lo hace la unidad de trabajo):

- `listar_prestaciones(uow) -> list[DatosPrestacion]`.
- `crear_prestacion(comando: CrearPrestacionComando, uow) -> DatosPrestacion`: valida RN-AG-01, busca el nombre repetido y agrega.
- `editar_prestacion(prestacion_id, comando: EditarPrestacionComando, uow) -> DatosPrestacion`: obtiene la prestación (o `PrestacionNoEncontrada`), valida RN-AG-01 si viene la duración, busca el nombre repetido si viene el nombre (excluyendo la propia) y guarda la versión nueva (`dataclasses.replace`). En `EditarPrestacionComando` un campo `None` significa «no cambia»: el `null` explícito ya lo rechazó la API (P9).

Ninguno registra eventos de turno ni toca turnos (CA-3).

### P11. Puerto, repositorio y unidad de trabajo — Propuesta

`RepositorioPrestaciones` en `puertos.py`, con cinco métodos: `consultorio_unico() -> int`, `del_consultorio(consultorio_id) -> Sequence[DatosPrestacion]` (por `id`), `obtener(prestacion_id) -> DatosPrestacion | None`, `agregar(datos) -> DatosPrestacion` (con id, tras `flush`) y `guardar(datos) -> DatosPrestacion` (actualiza la fila y hace `flush`). `agregar` y `guardar` traducen el `IntegrityError` del `UNIQUE` a `NombreRepetidoEnLaBase` (P7). Implementación `RepositorioPrestacionesSqlAlchemy` en `infrastructure/repositories/prestaciones.py`; `UnidadDeTrabajoSqlAlchemy` suma `self.prestaciones` sobre la misma sesión que `agenda` e `historial`.

**Alternativa descartada:** sumar estos métodos a `RepositorioAgenda`: ese puerto es de lo que necesita `crear_turno`, y crecería con un catálogo que no usa.

### P12. Modelo y migración `0005_color_y_reserva_online_de_prestaciones` — Decisión del autor (DD-15, `04` §Prestacion, D130; relleno, D174) + Propuesta (forma)

Modelo: `color: Mapped[str]` (no nula, **sin** default: la API la exige) y `reservable_online: Mapped[bool] = mapped_column(default=False)` (no nula, default de Python como `activa`). Ninguna `CHECK` nueva (Non-Goals).

Migración (solo PostgreSQL, como `0001` a `0004`), revisada a mano contra `modelos.py`: `upgrade` agrega las dos columnas `NOT NULL` con `server_default` (`'#9E9E9E'` y `false`) para completar las filas existentes, y después quita los dos `server_default` con `alter_column`, para que la base quede igual que el modelo; `downgrade` quita las dos columnas. Nada destructivo: los datos de C-01 a C-03 siguen. **Color de relleno `#9E9E9E` (gris): Decisión del autor (D174).**

### P13. Seed de la demo y factories — Decisión del autor (D174; colores del seed) + Propuesta (factory)

`_PRESTACIONES` de `seed_demo.py` suma un color por prestación (D56 dice «cada una con un color», sin fijarlo): Consulta / control `#1E88E5`, Limpieza `#43A047`, Obturación `#FB8C00`, Extracción `#E53935`, Urgencia `#8E24AA`; `reservable_online` queda en `false`. **Límite:** el volumen de PostgreSQL que ya tiene la demo de C-02 no se vuelve a sembrar (`cargar_demo_si_falta`): ahí las cinco prestaciones quedan con el gris de `0005` hasta que se borre el volumen (README).

`una_prestacion` (`tests/factories.py`) suma `"color": "#9E9E9E"` a sus datos por defecto. Es la única forma de que los tests de C-01 a C-03 sigan pasando **sin tocarlos** con la columna no nula.

### P14. Router — Propuesta

`api/routers/prestaciones.py` (`prefix="/prestaciones"`, `tags=["prestaciones"]`, endpoints síncronos `def`): `GET ""` (`200`, `list[PrestacionSalida]`), `POST ""` (`201`, con `409` y `422` declarados con `Problema`) y `PATCH "/{prestacion_id}"` (`200`, con `404`, `409` y `422`). `main.py` incluye el router. **REFACTOR:** `_PROBLEMA_JSON` y `_respuesta_de_error` pasan de `routers/turnos.py` a un módulo compartido (`api/respuestas.py`): con este router son tres rutas que los usan.

### P15. Tests: dónde va cada uno — Propuesta

| Escenario del spec | Test | Capa |
|---|---|---|
| CA-2 (reglas puras), nombre normalizado y clave | `tests/unit/test_prestaciones.py` | Dominio, sin base |
| Repositorio (alta, lectura, guardado, traducción del `UNIQUE`), unidad de trabajo | `tests/integration/test_repositorio_prestaciones.py` | SQLite en memoria |
| CA-1, CA-2 y RN-AG-15 en los casos de uso | `tests/integration/test_prestaciones.py` | SQLite en memoria |
| CA-1, CA-2 y CA-3 por HTTP, `404`, formato y OpenAPI | `tests/api/test_prestaciones.py` | `TestClient` sobre `crear_app(engine)` |
| Demo con colores | `tests/api/test_demo.py` (un test nuevo; los existentes no cambian) | API |
| INF-1 con `0005` y relleno de filas existentes | `tests/postgres/test_migraciones.py` (un test nuevo) | Perfil `postgres` |

Los nombres siguen `test_<id>_<situación>_<resultado>` con el ID del escenario (`ca1`, `ca2`, `ca3`). Sin mocks; datos de `tests/factories.py`; reloj `RELOJ_FIJO`. Los tests de C-01 a C-03 no se tocan (solo cambia la factory, P13).

### P16. README — Propuesta

Suma: los tres endpoints con una petición de ejemplo cada uno sobre la demo (alta de «Blanqueamiento», edición del color de la prestación 2, desactivación de la 5 y el `422` de `POST /turnos` que sigue), la tabla escenario → test de CA-1 a CA-3, `0005` en «Migraciones» y dos límites: las rutas no tienen autenticación (DD-14) y el volumen de PostgreSQL anterior a `0005` deja las prestaciones de la demo en gris (P13).

### P17. Commits y forma de trabajo del Apply — Propuesta (continúa H17 de C-03)

Un commit por tarea cerrada, en español, con prefijo (`test:` para RED, `feat:` para GREEN, `refactor:`, `docs:`), con el ok del autor (regla dura 10). Los grupos del Apply se encadenan sin pedir ok entre ellos; se frena ante un desvío del design, una falla de verificación (V1 a V4) o una tarea del autor.

### Skills aplicadas

- `fastapi-templates`: router → caso de uso → repositorio; esquemas de entrada y salida, nunca modelos ORM; sesión por dependencia; `def` síncronos.
- `python-design-patterns`: puerto propio para el catálogo (SRP), sin tocar `crear_turno`; regla de tres para no generalizar los `404` todavía (P5).
- `python-error-handling`: errores de dominio con código; entrada junta, negocio de a uno; la excepción de infraestructura se traduce en el caso de uso (P7).
- `python-testing-patterns`: AAA, parametrize para triangular, sin mocks, dominio sin base.
- `database-migration`: una migración reversible; columnas no nulas con relleno por `server_default` que después se quita; revisión a mano del autogenerate.
- `supabase-postgres-best-practices`: unicidad con restricción con nombre; la suite por defecto no depende de funciones propias de PostgreSQL (P7 descarta `lower()`).

## Contradicciones y huecos encontrados en las fuentes

1. **Nombre único sin código RN** (US-001 CA-1 contra la regla dura 4). Ver P6; resuelto en D171.
2. **Unicidad sin criterio de comparación**: `04` dice `UNIQUE(consultorio_id, nombre)` y US-001 «único en el consultorio», sin decir si «Limpieza» y «limpieza» son el mismo. Ver P7; resuelto en D172.
3. **De dónde sale el consultorio** sin autenticación: la KB no lo dice para las rutas de catálogo (sí para el turno, D126). Ver P3; resuelto en D173.
4. **Relleno de `color` para las filas existentes**: D130 deja la Propuesta «valor por defecto en la migración» sin fijar el valor. Ver P12; resuelto en D174.
5. **`02` (API) contra `CHANGES.md`**: coinciden (`GET/POST /prestaciones`, `PATCH /prestaciones/{id}`, sin borrado). Sin conflicto.

## Risks / Trade-offs

- [Dos altas simultáneas con el mismo nombre escrito distinto pasan las dos] → Sin usuarios ni panel todavía no hay concurrencia real; si hiciera falta, una columna con la clave normalizada y su `UNIQUE` (P7, D172).
- [Desactivar una prestación con turnos futuros no avisa nada] → Es lo que pide la KB (los turnos existentes no cambian); un aviso es tema de la pantalla (C-11).
- [Las prestaciones de la demo en un volumen viejo quedan en gris] → Límite documentado en el README; `docker compose down -v` vuelve a sembrar con los colores.
- [Quitar el `server_default` después de rellenar deja la columna sin default en la base] → Es lo buscado: la base coincide con el modelo y la API siempre manda el color; INF-1 lo comprueba.
- [Generalizar `_problema_de_entrada` podría cambiar el `422` de `POST /turnos`] → Los tests de API de C-01 fijan ese cuerpo y no se tocan; deben seguir pasando.
- [Sin autenticación cualquiera puede editar el catálogo] → Límite conocido (DD-14), igual que `POST /turnos`; C-07 protege las rutas.

## A verificar en el change

- **V1** (antes de dar por GREEN la migración `0005`): que `compare_metadata` no informe diferencias después de quitar los `server_default` y que el `downgrade` hasta `0004` y hasta `base` funcione con filas en `prestacion`.
- **V2** (antes de escribir `EditarPrestacionEntrada`): que con Pydantic 2.11.10 un `null` explícito se rechace como `422` de formato con el campo nombrado, y que un campo omitido no aparezca en `model_fields_set`.
- **V3** (antes de traducir el `IntegrityError`): cómo se reconoce la violación del `UNIQUE` en SQLite (mensaje «UNIQUE constraint failed») y en PostgreSQL (SQLSTATE `23505` con el nombre `uq_prestacion_consultorio_id_nombre`), para traducir solo esa y dejar subir cualquier otra.
- **V4** (antes de cerrar el grupo de dominio): que `clave_de_nombre` iguale «Obturación», «obturacion» y « OBTURACIÓN » y distinga «Limpieza» de «Limpiezas».

## Migration Plan

1. `alembic upgrade head` aplica `0005` sobre la base de C-03: las prestaciones existentes quedan con `color` `#9E9E9E` y `reservable_online` `false`; los turnos y el historial no cambian.
2. El arranque del contenedor ya corre `alembic upgrade head` antes de sembrar (Dockerfile): no hay pasos manuales.
3. **Rollback:** `alembic downgrade 0004` quita las dos columnas; la aplicación de C-03 vuelve a funcionar sobre esa base. Se pierden los colores y las marcas `reservable_online` cargados, nada más.

## Open Questions

Ninguna. Las cuatro preguntas del propose quedaron cerradas por el autor el 2026-10-14, todas con la recomendación del agente:

- **Q1 → D171.** Código nuevo **RN-AG-15** para el nombre repetido (`409`); una prestación inactiva sigue ocupando su nombre (P6).
- **Q2 → D172.** La comparación ignora mayúsculas, tildes y espacios de más, se hace en el dominio, y la restricción exacta queda como red de seguridad (P7).
- **Q3 → D173.** El consultorio es el único de la instalación hasta C-07, sin `consultorio_id` en el cuerpo (P3).
- **Q4 → D174.** Gris `#9E9E9E` para completar las filas existentes en `0005` y los cinco colores de P13 en el seed de la demo (P12, P13).

El texto de RN-AG-15 en `05_reglas_de_negocio.md` y los demás ajustes de la KB van en el commit `docs(kb)` del archive.
