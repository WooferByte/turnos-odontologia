# Design: gestion-de-sillones

Fecha del design: **2026-10-14**. Gobernanza **BAJO** (catálogo): autonomía completa en el Apply si los tests pasan.

**Respuesta del autor (2026-10-14): las tres preguntas abiertas se cierran con la recomendación del agente.** Quedan como decisiones del autor D183 (Q1, el nombre del sillón no es único), D184 (Q2, se puede desactivar el último sillón activo) y D185 (Q3, `PATCH` con `nombre` y `activo`, reactivación incluida), registradas en `knowledge-base/10_preguntas_abiertas.md`. Las demás decisiones marcadas «Propuesta» siguen así hasta que el autor apruebe el plan completo.

Las decisiones se numeran **S1 a S16** («S» de sillones) para no confundirlas con las D1..D185 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs de C-01 a C-04 (D, I, H y P). Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design, a confirmar) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»).

## Context

Motivación y alcance: ver `proposal.md`. Requisitos: `specs/gestion-de-sillones/spec.md`. Acá va solo el estado actual que condiciona el cómo.

**Lo que dejaron C-01 a C-04** (leído del código, no supuesto):

- `infrastructure/db/modelos.py`: `SillonModelo` con `id`, `consultorio_id`, `nombre` y `activo` (default de Python `True`). **No tiene `UNIQUE` sobre el nombre** (a diferencia de `prestacion`) ni `CHECK`. `04` §Sillon tampoco lo pide. La tabla ya tiene todo lo que pide US-004: no hace falta migración.
- `domain/agenda/recursos.py`: `Sillon(id, consultorio_id, activo)`, el dato mínimo de `crear_turno`; no tiene `nombre`.
- `application/crear_turno.py` **ya implementa RN-AG-14 y RN-AG-07 para el sillón**: con `sillon_id` omitido pide `uow.agenda.sillones_activos(consultorio_id)` y usa el único, o informa `ReferenciaInvalida("sillon", None, "ninguno_activo" | "varios_activos")`; un sillón explícito inactivo da `"inactivo"`, y uno de otro consultorio, `"inexistente"`. `tests/api/test_post_turnos.py` (`test_sillon_omitido_con_varios_activos_responde_422_sin_id_en_el_detalle`) y `tests/integration/test_crear_turno.py` ya lo prueban con sillones cargados por factory. El detalle del `422` dice «sillon (varios_activos)».
- `RepositorioAgenda` (`puertos.py`) tiene `sillon(id)` y `sillones_activos(consultorio_id)`, que son lo que necesita `crear_turno`; `bloquear_recursos` toma el bloqueo de fila del sillón (D157).
- C-04 dejó el patrón del catálogo: `domain/agenda/prestaciones.py` (`DatosPrestacion`, `normalizar_espacios`, `clave_de_nombre`), `application/prestaciones.py`, `RepositorioPrestaciones` con `consultorio_unico()` (D173), `infrastructure/repositories/prestaciones.py`, `api/routers/prestaciones.py`, `api/respuestas.py` (`_respuesta_de_error`), y en `api/esquemas.py` el tipo `NombreDePrestacion` (`AfterValidator` que normaliza y rechaza el vacío) y el `field_validator("*", mode="before")` que rechaza el `null` explícito de la edición (D178).
- `domain/errors.py`: `TurnoNoEncontrado` y `PrestacionNoEncontrada`, los dos «no encontrado en la URL» (`404`, `RN-GL-04`, D166), idénticos salvo el recurso y el texto; `api/errores.py` los atiende con un `isinstance` sobre la tupla de los dos y una fila cada uno en `_CLASES_DE_ERROR` (búsqueda por clase exacta).
- `seed_demo.py`: un solo sillón, «Sillón 1» con id 1, «a propósito: así omitirlos funciona (RN-AG-14)». `ajustar_secuencias` ya incluye `sillon`, así que un `POST /sillones` en PostgreSQL no choca con el id 1. El recorrido del README omite `sillon_id`.
- KB: la matriz de `03` da a los sillones «CRUD» para el odontólogo; `02` resume la API como `GET/POST /sillones`, `PATCH /sillones/{id}` (desactivar); US-004 CA-3 pide alta y desactivación.

## Goals / Non-Goals

**Goals:**

- Que el estado de los sillones sea gestionable por la API y que RN-AG-14 y RN-AG-07, ya construidas en `crear_turno`, queden probadas de punta a punta con sillones creados por esa API (no solo por factory).
- Reusar el patrón de C-04 sin copiarlo a ciegas: compartir lo que ya se repite tres veces (los `404` de la URL) y lo que es idéntico (el nombre normalizado y el rechazo del `null`), sin una abstracción genérica de «catálogo».

**Non-Goals:**

- Ningún cambio en `crear_turno`, `recursos.Sillon` ni `RepositorioAgenda`: ya cumplen RN-AG-07 y RN-AG-14.
- Ninguna migración ni restricción nueva en la base (alcance de `CHANGES.md`; D183).
- Nombre único del sillón (D183).
- Impedir desactivar el último sillón activo (D184).
- Avisar, mover o cancelar los turnos futuros de un sillón que se desactiva.
- Control de concurrencia entre la desactivación de un sillón y el alta simultánea de un turno en él (ver Risks).
- Un repositorio o caso de uso genérico para todos los catálogos.

## Decisions

### S1. Una capability nueva, sin deltas — Propuesta

`gestion-de-sillones` aloja US-004 CA-1, CA-2 y CA-3. **No se modifica `creacion-de-turnos`**: su requisito «Crear un turno reservado con fin calculado» ya dice «si la petición no indica el profesional o el sillón, el sistema SHALL usar el único activo del consultorio (RN-AG-14)», y «Rechazar las referencias inválidas» ya cubre el sillón inactivo (RN-AG-07) y el omitido «sin que haya uno solo activo». Lo que `CHANGES.md` pone «dentro» de C-05 sobre los turnos (inactivo con motivo `inactivo`; único activo; con más de uno, indicarlo o `RN-GL-04`, D138) es exactamente lo que ya dicen esos requisitos y hace el código. Este change solo lo vuelve alcanzable por la API; los escenarios que lo recorren con `POST /sillones` viven en `gestion-de-sillones`, como C-04 dejó la prestación inactiva en su propio spec sin tocar E12. Tampoco cambian `persistencia-postgresql` (sin migración), `historial-de-turnos` ni `gestion-de-prestaciones`.

**Alternativa descartada:** un delta MODIFIED en `creacion-de-turnos` que nombre los motivos `ninguno_activo` y `varios_activos`: es precisión de texto, no cambio de comportamiento, y repetiría escenarios que ya están acá.

### S2. Dependencias y esquema: nada nuevo — Decisión del autor (D116, D137; `CHANGES.md` «sin cambios de esquema») + Propuesta

Ningún paquete ni pin nuevo en `backend/pyproject.toml`: se usa lo ya fijado (FastAPI 0.115.14, Pydantic 2.11.10, SQLAlchemy 2.0.54). La política de pins de D133 no aplica porque no se elige ninguna versión. Ninguna migración: la última sigue siendo `0005`.

### S3. El consultorio de la petición: el único de la instalación — Decisión del autor (D173, por extensión) + Propuesta

D173 lo fijó para las rutas de prestaciones; se aplica igual a `/sillones`: sin `consultorio_id` en el cuerpo ni en la salida, el caso de uso pide `uow.sillones.consultorio_unico()`, y si la base no tiene exactamente un consultorio es un `500` de configuración. `PATCH` busca el sillón por id (con un solo consultorio, todo sillón es suyo). C-07 reemplaza esa llamada por el consultorio de la sesión.

### S4. Dato del sillón en el dominio — Decisión del autor (D183, sin nombre único) + Propuesta (forma)

Módulo nuevo `backend/app/domain/agenda/sillones.py`, solo biblioteca estándar, con `DatosSillon` (dataclass congelada: `id: int | None`, `consultorio_id`, `nombre`, `activo`), el catálogo completo. `recursos.Sillon` sigue siendo el dato mínimo de `crear_turno` (no se toca, como `recursos.Prestacion` en C-04). No hay reglas puras nuevas: sin nombre único (D183) ni límite al último activo (D184), la única regla del alta es de formato (nombre no vacío) y la de RN-AG-14 ya vive en `crear_turno`.

**Nombre normalizado — REFACTOR:** `normalizar_espacios` pasa de `domain/agenda/prestaciones.py` a un módulo compartido `domain/agenda/nombres.py` (junto con `clave_de_nombre`, que la sigue usando prestaciones), y `prestaciones.py` la importa de ahí. Los tests unitarios de C-04 se mueven solo en su `import`. Es el único lugar del dominio donde se repite algo entre los dos catálogos.

### S5. Error del sillón de la URL y base común de los `404` (regla de tres) — Propuesta

`SillonNoEncontrado(sillon_id)` en `domain/errors.py`: código `RN-GL-04`, `404`, `ReferenciaInvalida("sillon", id, "inexistente")`, mensaje «No existe el sillón 999.». Con él son **tres** clases idénticas salvo el recurso y el texto: P5 de C-04 (D176) dejó dicho que en C-05 se generaliza. **REFACTOR**, después del GREEN del `404`:

- Clase base `RecursoDeLaUrlNoEncontrado(ErrorDeDominio)` con `codigo = "RN-GL-04"`, `referencias` y el armado de la referencia a partir de `recurso` y `recurso_id`; `TurnoNoEncontrado`, `PrestacionNoEncontrada` y `SillonNoEncontrado` quedan como subclases de una línea cada una (conservan su nombre: los tests de C-03 y C-04 no se tocan).
- `api/errores.py`: una sola fila para la base en `_CLASES_DE_ERROR`, y `_manejar_error_de_dominio` busca la clase recorriendo `type(error).__mro__` (la primera que esté en el mapa), así que las demás clases siguen resolviendo igual; `_problema_de` usa `isinstance(error, RecursoDeLaUrlNoEncontrado)` en lugar de la tupla.

`RecursoNoEncontrado` (el `422` de referencias del cuerpo) **no** entra en la base: va dentro de `EntradaInvalida` y es otra clase de rechazo (RN-GL-02).

### S6. Clasificación de los rechazos y orden de evaluación (RN-GL-02) — Decisión del autor (D183, D184: sin reglas de negocio) + Propuesta (tabla y orden)

| Rechazo | Clase | Estado | Código |
|---|---|---|---|
| Cuerpo mal formado: `nombre` ausente en el alta, campo de más (incluido `activo` en el alta), tipo erróneo, `null` explícito en la edición, `nombre` vacío tras normalizar, id de la ruta que no es entero | Validación de entrada (formato, Pydantic) | `422` | sin código |
| Sillón de la URL inexistente | Validación de entrada (URL) | `404` | `RN-GL-04` |
| (En `POST /turnos`, sin cambios) sillón del cuerpo inexistente, inactivo, de otro consultorio, u omitido sin un único activo | Validación de entrada | `422` | `RN-GL-04` |

Orden en `/sillones`: **formato → sillón de la URL**. Las rutas de sillones **no tienen reglas de negocio** (sin nombre único, D183; sin límite al último activo, D184): no hay `409`. En `POST /turnos` el orden de C-01 no cambia (entrada junta, RN-AG-10d, solapamiento).

### S7. Esquemas HTTP — Decisión del autor (D185, campos) + Propuesta (forma)

En `api/esquemas.py`, con `extra="forbid"` y ejemplos para `/docs`:

- `CrearSillonEntrada`: `nombre` (el tipo de nombre normalizado). Sin `activo`: el sillón nace activo (un `activo` en el cuerpo es campo de más, `422`).
- `EditarSillonEntrada`: `nombre` y `activo`, opcionales; `{}` es válido y responde `200` sin cambios; el router arma el comando solo con `model_fields_set`.
- `SillonSalida`: `id`, `nombre`, `activo` (sin `consultorio_id`, S3).

**REFACTOR:** `NombreDePrestacion` pasa a llamarse `NombreNormalizado` (mismo `AfterValidator`, ahora con la función de `domain/agenda/nombres.py`) y lo usan los dos catálogos; el `field_validator("*", mode="before")` que rechaza el `null` (D178) sube a una base `EntradaDeEdicion(BaseModel)` de la que heredan `EditarPrestacionEntrada` y `EditarSillonEntrada`. El contrato de `/prestaciones` y su OpenAPI no cambian (sus tests no se tocan).

### S8. Casos de uso — Decisión del autor (D184, D185) + Propuesta

`backend/app/application/sillones.py`, sin `commit()` ni SQL:

- `listar_sillones(uow) -> list[DatosSillon]`.
- `crear_sillon(comando: CrearSillonComando, uow) -> DatosSillon`: arma el `DatosSillon` activo en el consultorio único y lo agrega.
- `editar_sillon(sillon_id, comando: EditarSillonComando, uow) -> DatosSillon`: obtiene el sillón (o `SillonNoEncontrado`) y guarda la versión con los campos que llegaron (`dataclasses.replace`; un campo `None` del comando es «no cambia»).

Ninguno toca turnos ni registra eventos de turno. Sin RN-AG-15 ni nada parecido (D183). `editar_sillon` admite desactivar el último activo (D184) y reactivar (D185).

### S9. Puerto, repositorio y unidad de trabajo — Propuesta

`RepositorioSillones` en `puertos.py`: `consultorio_unico() -> int`, `del_consultorio(consultorio_id) -> Sequence[DatosSillon]` (por `id`), `obtener(sillon_id) -> DatosSillon | None`, `agregar(datos) -> DatosSillon` (con id, tras `flush`) y `guardar(datos) -> DatosSillon`. Sin traducción de `IntegrityError` (no hay `UNIQUE`). Implementación `RepositorioSillonesSqlAlchemy` en `infrastructure/repositories/sillones.py`; `UnidadDeTrabajoSqlAlchemy` suma `self.sillones` sobre la misma sesión que `agenda`, `historial` y `prestaciones`.

**REFACTOR:** la consulta de `consultorio_unico` (una línea, hoy en el repositorio de prestaciones) pasa a una función `consultorio_unico(sesion)` en `infrastructure/repositories/consultorio.py` que usan los dos repositorios. El método queda en cada puerto (cada caso de uso depende solo de su repositorio).

**Alternativas descartadas:** sumar estos métodos a `RepositorioAgenda` (es el puerto de `crear_turno`; ya tiene `sillon` y `sillones_activos` para eso) y un repositorio genérico de catálogo (dos catálogos con campos y reglas distintas no lo justifican).

### S10. Router — Propuesta

`api/routers/sillones.py` (`prefix="/sillones"`, `tags=["sillones"]`, endpoints síncronos `def`): `GET ""` (`200`, `list[SillonSalida]`), `POST ""` (`201`, con `422` declarado con `Problema`) y `PATCH "/{sillon_id}"` (`200`, con `404` y `422`). Las respuestas de error usan `_respuesta_de_error` de `api/respuestas.py`. `main.py` incluye el router. No hay `DELETE`.

### S11. Seed de la demo y factories: sin cambios — Propuesta

El seed sigue con un único «Sillón 1» (id 1): es lo que hace que el recorrido del README, que omite `sillon_id`, funcione (RN-AG-14). La factory `un_sillon` ya alcanza. **Límite de la demo** (README): después de dar de alta un segundo sillón en `/docs`, el `POST /turnos` sin `sillon_id` responde `422` con `varios_activos` hasta que se desactive uno; en la API sobre PostgreSQL ese estado queda en el volumen (se vuelve con `PATCH` o con `docker compose down -v`).

### S12. Tests: dónde va cada uno — Propuesta

| Escenario del spec | Test | Capa |
|---|---|---|
| `SillonNoEncontrado` y la base común de los `404` | `tests/unit/test_errores_de_url.py` | Dominio, sin base |
| Repositorio (alta, listado por `id` con inactivos, lectura, guardado), unidad de trabajo | `tests/integration/test_repositorio_sillones.py` | SQLite en memoria |
| CA-3 en los casos de uso (alta, renombre, desactivar, reactivar, `{}`, inexistente) | `tests/integration/test_sillones.py` | SQLite en memoria |
| CA-3 por HTTP (`201`, `200`, `404`, formato, OpenAPI) | `tests/api/test_sillones.py` | `TestClient` sobre `crear_app(engine)` |
| CA-3 inactivo y CA-1 / CA-2 con `POST /turnos` sobre sillones creados por `POST /sillones` | `tests/api/test_sillones_y_turnos.py` | `TestClient` |
| CA-2 borde: alta tras el seed en PostgreSQL | `tests/postgres/test_seed_y_api.py` (un test nuevo) | Perfil `postgres` |

Los nombres siguen `test_<id>_<situación>_<resultado>` con el ID del escenario (`ca1`, `ca2`, `ca3`). Sin mocks; datos de `tests/factories.py`; reloj `RELOJ_FIJO`. Los tests de C-01 a C-04 no se tocan, salvo el `import` de `normalizar_espacios` y `clave_de_nombre` en `tests/unit/test_prestaciones.py` si se mueven (S4).

**Tests que nacen verdes:** los de `test_sillones_y_turnos.py` ejercitan lógica de C-01 que ya existe; su RED es la falta de `POST /sillones` y `PATCH /sillones/{id}` (fallan con `404`/`405` de ruta) hasta el GREEN del router. Para comprobar que protegen RN-AG-14 y RN-AG-07, en su tarea se cambia a propósito y temporalmente `crear_turno` (por ejemplo, tomar `activos_sillon[0]` aunque haya varios, o ignorar `activo`) y deben fallar; después se revierte (como D182 en C-04).

### S13. README — Propuesta

Suma una sección «Sillones» con los tres endpoints y una petición de ejemplo cada uno sobre la demo (listar; alta de «Sillón 2»; el `POST /turnos` del recorrido sin `sillon_id`, ahora `422` con `varios_activos`; el mismo con `"sillon_id": 2`, `201`; desactivar el 2 con `PATCH`, y el recorrido vuelve a funcionar), la tabla escenario → test de CA-1 a CA-3 y dos límites: las rutas no tienen autenticación (DD-14) y el estado de sillones de la demo cambia el resultado del recorrido (S11).

### S14. Commits y forma de trabajo del Apply — Propuesta (continúa D182 de C-04)

Un commit por tarea cerrada, en español, con prefijo (`test:` para RED, `feat:` para GREEN, `refactor:`, `docs:`) y la línea `Co-Authored-By`, con el ok del autor (regla dura 10). Los grupos del Apply se encadenan sin pedir ok entre ellos; se frena ante un desvío del design, una falla de verificación (V1 a V3) o una tarea del autor (prueba en `/docs` y clon limpio).

### S15. Concurrencia — Propuesta

No se agrega bloqueo para la edición de un sillón. `crear_turno` valida el sillón (activo) **antes** de tomar el bloqueo de fila del sillón (D157), así que una desactivación simultánea con el alta de un turno en ese sillón puede dejar un turno nuevo en un sillón recién desactivado. Sin usuarios ni panel todavía, se acepta (Risks).

### S16. Verificación en clon limpio — Propuesta (como C-04, D182)

Clon en una ruta corta (`C:\c05-clon`), proyecto Compose `-p c05`; al terminar, `docker compose -p c05 down -v`, se quita la imagen del proyecto y se borra **solo** la carpeta del clon. Una regla de permisos bloquea los comandos que mencionan el archivo de entorno: **el autor copia `.env.example` a `.env` en el clon a mano** (Copy-Item con rutas absolutas), como en C-04.

### Skills aplicadas

- `fastapi-templates`: router → caso de uso → repositorio; esquemas de entrada y salida, nunca modelos ORM; sesión por dependencia; `def` síncronos; los errores de dominio los traduce un manejador.
- `python-design-patterns`: puerto propio por catálogo (SRP), sin tocar `crear_turno`; regla de tres aplicada a los `404` (S5) y no a un «catálogo genérico» (S9); KISS en el dominio (sin reglas que la KB no pide).
- `python-error-handling`: error de dominio con su código para el `404`; jerarquía solo donde ya hay tres casos; cada camino de error con su test.
- `python-testing-patterns`: AAA, parametrize para triangular el formato, sin mocks, dominio sin base, comprobación de que los tests que nacen verdes protegen algo.
- `database-migration` y `supabase-postgres-best-practices`: **no aplican** (sin cambios de esquema); solo se comprueba que la secuencia de `sillon` ya está ajustada (V3).

## Contradicciones y huecos encontrados en las fuentes

1. **`CHANGES.md` pone «dentro» comportamiento que C-01 ya construyó** (sillón inactivo, único activo, `varios_activos`), y US-004 CA-3 dice «CA-1 ya lo cumple el primer change». No es contradicción: el change lo prueba de punta a punta con sillones creados por la API, sin delta (S1).
2. **Nombre único del sillón**: la KB no lo pide (`04` no tiene `UNIQUE` en `Sillon`; US-004 no lo menciona), a diferencia de las prestaciones (D171). Resuelto en D183.
3. **Qué edita el `PATCH`**: `02` y `CHANGES.md` dicen «(desactivar)»; `03` da «CRUD»; US-004 CA-3, «dar de alta y desactivar». Resuelto en D185.
4. **Desactivar el último sillón activo**: la KB no lo dice; RN-AG-14 ya define qué pasa sin activos (`RN-GL-04`). Resuelto en D184.
5. **DD-08 «valor 1 por defecto»** (`09`): el título conserva la redacción anterior a D125 (el por defecto no es un id fijo). El cuerpo ya está bien; al archivar se propone ajustar el título en el commit `docs(kb)` (sin pregunta: es redacción).

## Risks / Trade-offs

- [Dos sillones con el mismo nombre] → Aceptado (D183): el id los distingue y en la v1 no hay pantalla multi-sillón; si hiciera falta, una regla nueva con su código.
- [Desactivar el único sillón deja la agenda sin sillones] → Admitido por D184: `POST /turnos` responde `422` con `ninguno_activo`, que dice qué hacer; se reactiva con `PATCH`.
- [Un segundo sillón activo cambia el resultado del recorrido de la demo] → Es lo que pide RN-AG-14 (D138); documentado en el README (S11, S13).
- [Desactivación simultánea con el alta de un turno en ese sillón] → Sin concurrencia real hoy; si hiciera falta, validar el sillón después de `bloquear_recursos` (S15).
- [Mover `normalizar_espacios` y la base de los `404` podría romper C-03/C-04] → REFACTOR con los tests de C-03 y C-04 sin tocar (salvo un `import`) y la suite completa en verde después de cada paso.
- [Sin autenticación cualquiera puede desactivar un sillón] → Límite conocido (DD-14), igual que el resto de las rutas; C-07 las protege.

## A verificar en el change

- **V1** (antes de cerrar el REFACTOR de S5): que con la búsqueda por `__mro__` en `_manejar_error_de_dominio` los cuerpos del `404` de `GET /turnos/{id}/historial` y de `PATCH /prestaciones/{id}` no cambian (sus tests de API siguen pasando sin tocarlos) y que una clase de error que no esté en el mapa sigue subiendo como `500`.
- **V2** (antes de escribir `EditarSillonEntrada`): que el `field_validator("*", mode="before")` en una clase base se hereda con Pydantic 2.11.10 y sigue nombrando el campo en el `422` de los dos esquemas de edición.
- **V3** (antes de dar por GREEN el test del perfil `postgres`): que `ajustar_secuencias` deja la secuencia de `sillon` en 1 sobre el volumen de la demo, así que el primer `POST /sillones` recibe el id 2.

## Migration Plan

No hay migración. Desplegar es reemplazar la imagen: `alembic upgrade head` no hace nada nuevo (`0005` sigue siendo la última) y los datos de C-01 a C-04 no cambian. **Rollback:** volver a la imagen anterior; los sillones dados de alta quedan en la tabla y la versión anterior los sigue usando en `POST /turnos` (si hay más de uno activo, omitir el sillón da `varios_activos`, igual que ahora).

## Open Questions

Ninguna. Las tres preguntas del propose quedaron cerradas por el autor el 2026-10-14, todas con la recomendación del agente:

- **Q1 → D183.** El nombre del sillón **no es único** en el consultorio: sin código RN nuevo, sin `409` y sin restricción en la base (S4, S6).
- **Q2 → D184.** **Se puede desactivar el último sillón activo**; después, un turno sin sillón se rechaza con `RN-GL-04` y `ninguno_activo` (RN-AG-14) (S6, S8).
- **Q3 → D185.** `PATCH /sillones/{id}` acepta **`nombre` y `activo`**, incluida la reactivación; `POST /sillones` recibe solo `nombre` (S7, S8).

Los ajustes de la KB (US-004 en `06`, §Sillon en `04` si hace falta y el título de DD-08 en `09`, hueco 5) y las decisiones «Propuesta» que el autor apruebe van en el commit `docs(kb)` del archive.
