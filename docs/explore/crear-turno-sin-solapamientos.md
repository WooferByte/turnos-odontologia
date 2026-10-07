# Relevamiento (Explore): `crear-turno-sin-solapamientos`

## 1. Qué es este documento

Resultado de la fase **Explore** del ciclo OPSX (explore, propose, apply, verify, archive) para el primer change del proyecto, `crear-turno-sin-solapamientos` (C-01, US-010, gobernanza MEDIO). Fecha: 2026-10-07. La consigna de la Etapa 6 pide relevar el problema y el estado del código antes de proponer; este archivo es ese relevamiento y la entrada de `/opsx:propose`. No crea el change, no escribe código y no resuelve las preguntas abiertas: las lista.

**Qué se leyó.** `CHANGES.md` (reglas globales, entrada C-01, tablas de mapeo), `openspec/config.yaml`, `CLAUDE.md`/`AGENTS.md` (idénticos), `knowledge-base/` 02, 04 (Turno, Paciente, Profesional, Sillón, Prestación, "Subconjunto del primer change", "Seed data inicial"), 05 (RN-AG, RN-GL, RN-PR-01, RN-AU-01), 06 (US-010 y notas de orden), 07 (Flujo 1), 08 (completo), 09 (DD-02, 03, 04, 12, 13, 14, 15, SU-08), 10 (P-10, P-17, P-18, D116), `docs/discovery/informe-discovery.md` (D.3) y el árbol del repositorio. No se pudo leer `Consigna.pdf` (no hay herramienta para extraer su texto en este entorno): lo que se afirma sobre la consigna proviene del encargo de esta fase y de la KB (`01_vision_y_objetivos.md`, README de la KB). `openspec list --json` y `openspec list --specs --json` devuelven listas vacías; el proyecto tiene raíz OpenSpec válida.

## 2. Problema y alcance del change

**Problema.** Hoy el consultorio agenda en papel, Excel o WhatsApp y los turnos se pisan. El change entrega el núcleo de la agenda: crear un turno `reservado` para un paciente, una prestación, un profesional y un sillón, rechazando el que se superponga con un turno **activo** del profesional (RN-AG-05) o del sillón (RN-AG-08), con los errores identificados por código RN (RN-GL-02). Fuente: `06_funcionalidades.md` US-010; `07_flujos_principales.md` Flujo 1; `CHANGES.md` C-01.

**Incluye** (`CHANGES.md` C-01 "Alcance — dentro"; `08` "Contrato del primer change"):
- Value object `Intervalo` semiabierto `[inicio, fin)` (RN-AG-09), con la validación de RN-AG-10d y la zona del consultorio como dato.
- Función pura `detectar_conflictos` y filtro de `ESTADOS_ACTIVOS` en el dominio (RN-AG-10).
- Errores de dominio con código RN: `ErrorDeSolapamiento` y `RecursoNoEncontrado` (RN-GL-02, RN-GL-04).
- Caso de uso `crear_turno` con reloj inyectable y defaults de profesional y sillón (RN-AG-06); `fin = inicio + duración de la prestación` (RN-AG-02).
- `POST /turnos` (FastAPI) **sin autenticación** (DD-14), respuesta `201`, errores `application/problem+json` (RFC 7807): `409` solapamiento, `422` recurso no encontrado o intervalo/cuerpo inválido.
- Tablas `Consultorio`, `Profesional`, `Sillon`, `Prestacion`, `Paciente`, `Turno` con `create_all` sobre SQLite en memoria (`04` "Subconjunto del primer change").
- Test unitario de `Intervalo` (E8), test de ida y vuelta de zonas horarias con SQLite (D85), test de imports de `app/domain` (D70) y test guard de fechas (DD-13).
- Archivo único de dependencias con versiones exactas (D116) y README con el límite conocido y la tabla escenario-test.

**No incluye** (`CHANGES.md` C-01 "Alcance — fuera"; `05` RN-AG-04, RN-AG-10c, RN-AG-11; `06` E9 a E11): historial `EventoTurno` (E9, C-03); horario recurrente y bloqueos (E10, RN-AG-04/04b, P-10); concurrencia y restricción de exclusión (E11, RN-AG-10c, C-02); estados `pendiente_sena` y `pendiente_aprobacion` y seña; lista de espera; WhatsApp; consentimiento (RN-PR-02 no aplica al alta desde el panel); autenticación y roles; interfaz gráfica; Alembic, PostgreSQL, Redis, Docker; reprogramar (RN-AG-10b); sobreturnos y excepción de horario (fuera de la v1, P-11); duración modificable en el comando (RN-AG-02, D98: la implementa US-012); gestión de prestaciones y sillones (US-001, US-004), `GET`/`PATCH`/`cancelar` de turnos.

## 3. Reglas de negocio y escenarios

IDs tal como figuran en `06_funcionalidades.md` (tabla de US-010) y en `07` (Flujo 1). Todos los horarios del spec van en UTC (`openspec/config.yaml`, regla de specs).

| Escenario | Tipo | Regla(s) | Qué verifica |
|---|---|---|---|
| E1 Feliz | Feliz | RN-AG-02, RN-AG-06, RN-AG-09 | Hueco libre: el turno se crea `reservado` con `fin = inicio + duración` (30 min a las 10:00, fin 10:30). |
| E2 Error (profesional) | Error de negocio | RN-AG-05, RN-GL-02 | Mismo profesional en otro sillón, 10:15 contra 10:00-10:30: rechazo solo con `RN-AG-05`. |
| E3 Error (sillón) | Error de negocio | RN-AG-08, RN-GL-02 | Mismo sillón con otro profesional: rechazo solo con `RN-AG-08`. |
| E4 Doble conflicto | Error de negocio | RN-AG-05 + RN-AG-08, RN-GL-02 | Mismo profesional y sillón: se informan los dos códigos (lista `[RN-AG-05, RN-AG-08]`, profesional primero). |
| E5 Borde contiguo | Borde | RN-AG-09 | Empieza justo cuando termina otro (10:30 contra 10:00-10:30) y termina justo cuando empieza otro: se acepta. |
| E6 Estado no activo | Borde / regla de estado | RN-AG-10 | Turno cancelado, vencido, atendido o ausente no bloquea el horario. |
| E7 Borde de un minuto | Borde | RN-AG-09, RN-AG-05 | Inicio a las 10:29 contra 10:00-10:30: solapamiento de un minuto, se rechaza. |
| E12 Recurso no encontrado | Error de negocio | RN-GL-04, RN-AG-07 | Prestación, paciente, profesional o sillón inexistente o inactivo en el cuerpo: `422` con `RN-GL-04`, recurso y motivo; no persiste nada. |

Fuera del spec pero dentro del change como test: **E8** (intervalo inválido: `inicio >= fin`, naive, fuera de UTC, cruce de la medianoche del consultorio; RN-AG-10d, RN-GL-01), test unitario de `Intervalo` (decisión del autor 2026-10-03, SU-08 punto 6).

Cobertura de lo que pide la consigna para el spec: feliz = E1; error de negocio = E2, E3, E4, E12; borde = E5, E7 (el ejemplo "empieza exactamente cuando termina otro" es E5). Hay holgura sobre el mínimo de 3.

**Criterios de aceptación.** US-010 no tiene lista `CA-n`: sus criterios son los IDs E# (nota de `06`: "Cada escenario del primer change tiene un test"). La Definition of Done (`08`) completa el criterio de terminado.

## 4. Datos y arquitectura que el change necesita

**Datos** (`04` "Subconjunto del primer change"; tablas de campos de cada entidad).
- `Consultorio`: `id`, `nombre`, `slug` (UNIQUE), `zona_horaria` (default `America/Argentina/Buenos_Aires`). Fuente de la zona para RN-AG-10d.
- `Profesional`: `id`, `consultorio_id`, `nombre`, `activo` (sin `usuario_id` ni `matricula`).
- `Sillon`: `id`, `consultorio_id`, `nombre`, `activo`.
- `Prestacion`: `id`, `consultorio_id`, `nombre` (UNIQUE con consultorio), `duracion_minutos` (CHECK > 0), `activa` (sin `color` ni `reservable_online`).
- `Paciente`: `id`, `consultorio_id`, `nombre`, `apellido`, `telefono_whatsapp` (sin `dni`, `email`, `fecha_nacimiento`, `es_nuevo`, `acepta_contacto`, `creado_en`).
- `Turno`: `id`, `consultorio_id`, `paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id`, `inicio`, `fin` (CHECK `inicio < fin`), `duracion_minutos` (CHECK > 0), `estado` (texto), `creado_en` (sin `origen`, `token_gestion`, `creado_por`, `actualizado_en`, `version`). Índices `(profesional_id, inicio, fin)` y `(sillon_id, inicio, fin)`.
- Convenciones (`04` "Convenciones comunes"): PK entera autoincremental; fecha-hora `DateTime(timezone=True)`, aware UTC; enums como texto; FK `ON DELETE RESTRICT`. Sin restricción de exclusión (SQLite no la soporta, DD-04).
- Seed de demo ficticio (RN-PR-01): consultorio, un profesional, un sillón, prestaciones de ejemplo (30 a 60 min) y 2-3 pacientes (`04` "Seed data inicial", D56).

**Arquitectura** (`08`).
- Capas `api → application → domain`, `infrastructure → domain`; `domain` solo con biblioteca estándar. Directorios `domain/agenda`, `domain/tiempo.py` (`utc_now()` y `Reloj`), `domain/errors.py`, `application/`, `infrastructure/{db,repositories}`, `api/{routers,deps.py}`, `main.py`; tests en `tests/{unit,integration,api}`.
- Reglas de capas prohibidas: lógica de negocio en router o repositorio; `commit()` dentro del caso de uso o repositorio (la transacción es de la unidad de trabajo); SQL en el caso de uso (consultas como método del repositorio, p. ej. `turnos_que_intersecan(recurso, intervalo)`); excepciones HTTP fuera de `api`; mocks de sesión o repositorio.
- Reloj: un único `utc_now()` inyectable, dominio solo con aware UTC, adaptador normaliza lo leído (DD-13).
- Tests: unit sin base; integration con SQLite en memoria (`StaticPool`, engine por test, `create_all`); API con `TestClient` (mínimo E1, E4, E12); reloj fijo; factories ficticias; un test por escenario con el ID en el nombre; comando único `pytest`.
- Definition of Done del primer change: 13 ítems de verificación en `08` (clon limpio con solo el README, SQLite en memoria declarado, un test por escenario y tabla escenario-test, API levantada y probada desde `/docs` con `201`/`409`/`422`, spec con feliz-error-borde, historial TDD, test guard de fechas, ida y vuelta, test de imports, `openspec validate` sin lock, sin secretos, límite conocido en el README).

## 5. Estado del código y del repositorio

Verificado en el árbol: **no hay código de aplicación**. No existen `app/`, `backend/`, `src/` ni `tests/`; no hay archivo de dependencias (`pyproject.toml`, `requirements*.txt`) ni `README.md` en la raíz; tampoco `.env.example`. Lo que existe (versionado):
- Documentación y proceso: `CLAUDE.md`, `AGENTS.md`, `CHANGES.md`, `Consigna.pdf`, `knowledge-base/` (01 a 12 y README), `discovery/` (`discovery.md` y 30 fuentes), `docs/discovery/` (informe en `.md` y `.pdf`, `generar-pdf.mjs`), `.active-orchestrator-state.json`.
- OpenSpec y agentes: `openspec/config.yaml`, `openspec/specs/.gitkeep`, `openspec/changes/archive/.gitkeep` (sin changes ni specs); `.atl/skill-registry.md`; `.claude/commands/opsx/*` y `.claude/skills/openspec-*`.
- `.gitignore` solo ignora `.claude/settings.local.json`: **no ignora** `.venv`, `__pycache__`, `.pytest_cache`, `.env`. Hay que agregarlos en el change (riesgo de versionar entorno o secretos, regla dura 1).
- El árbol de trabajo estaba limpio al empezar (rama `master`; los documentos mencionan `main` como principal).
- `docs/guia-entregable-borrador.md` se ignoró por indicación.

## 6. Encaje con el MVP del Discovery

Sí encaja. `docs/discovery/informe-discovery.md`, sección **D.3 "MVP sugerido"**, lista como "Imprescindible (v1)" el punto 4: "**Prevención de solapamientos** por profesional y por sillón". El mismo D.3 fija el segmento primario ("1 profesional, 1 sillón... La regla de solapamiento se aplica por profesional y por sillón, de modo que el crecimiento a varios sillones no requiera rediseñar la lógica"). `CHANGES.md` marca solo los changes C-47 y C-48 como "extensión fuera del MVP de la sección D"; C-01 queda dentro. La KB lo refleja en `01_vision_y_objetivos.md` (punto 4 del alcance) y en el README de la KB ("Change de la consigna").

Reglas verificables: RN-AG-05, RN-AG-08, RN-AG-09, RN-AG-10, RN-GL-04, con códigos y ejemplos numéricos en la KB. Tamaño: una sola capability (agenda: crear turno sin solapamientos), una sola historia (US-010) y un solo endpoint. Justificación sugerida para el `proposal.md` (2-3 líneas): está en el MVP de D.3 (punto 4), sus reglas son exactas y verificables con ejemplos de borde, y es el núcleo del que dependen los demás changes (C-02, C-03, C-16 en adelante).

## 7. Decisiones ya tomadas

| Tema | Decisión | Referencia |
|---|---|---|
| Stack | Python 3.11+, SQLAlchemy 2.x **sincrónico** en todos los changes, pytest; sin `aiosqlite` ni `pytest-asyncio` | CLAUDE.md regla 5; DD-12, D119 |
| Tests | SQLite en memoria con `StaticPool`, engine por test; sin mocks de sesión ni repositorio; dominio sin base; sin Docker, PostgreSQL ni Redis | DD-03, DD-12; `08` "Estrategia de tests" |
| Intervalos y tiempo | `[inicio, fin)`; solapan si `A.inicio < B.fin` y `B.inicio < A.fin`; aware UTC; `utc_now()` único inyectable; RN-AG-10d usa la medianoche del consultorio, con `fin == 00:00` local válido | RN-AG-09, RN-AG-10d (D63), RN-GL-01, DD-13 |
| Estado inicial y activos | El turno nace `reservado`; `ESTADOS_ACTIVOS` en el dominio | SU-08 puntos 3-4; RN-AG-10 |
| Doble conflicto | Se informan ambos códigos, profesional primero | RN-AG-08; `08` contrato |
| Errores HTTP | `409` solapamiento; `422` recurso no encontrado (RN-GL-04, un único status para inexistente e inactivo) y intervalo inválido; `404` solo para recurso en la URL (no aplica); cuerpo `application/problem+json` con `codigos` y `conflictos` | D73, SU-08 punto 10; `08` mapeo HTTP |
| Orden de evaluación | RN-GL-04 se resuelve antes que los solapamientos y no persiste nada | RN-GL-04; `08` caso de uso |
| Endpoint | `POST /turnos` sin autenticación (límite conocido que el README debe declarar), sin interfaz, probado desde `/docs` | DD-14 |
| Esquema | `create_all` en tests; sin Alembic; sin restricción de exclusión | DD-15; `04` subconjunto |
| Persistencia | Sin `EventoTurno`; `creado_en = reloj()` | RN-AG-11 (fuera); `08` caso de uso |
| E8, E11 | E8 solo test unitario; E11 fuera de la suite por defecto | SU-08 punto 6; RN-AG-10c (D75) |
| Dependencias | Un único archivo con pins exactos, fijado en el design de este change; los changes siguientes agregan al mismo; el archivo lo elige el design; toda dependencia de test declarada | D72, D116, P-17 |
| Datos | Siempre ficticios; sin secretos ni `.env` versionados | RN-PR-01; CLAUDE.md regla 1 |
| Firmas del contrato | Nombres de clases y funciones: propuesta aceptada, a revisar en el design | `08` "Contrato del primer change" |
| Gobernanza | MEDIO: implementar con puntos de control | `CHANGES.md` C-01 |

## 8. Decisiones que quedan para el design

Cada ítem indica qué lo deja abierto. Los marcados "Propuesta" o "A verificar" deben rotularse así en el `design.md` (reglas de `openspec/config.yaml`).

1. **Archivo único de dependencias y pins exactos**: formato (`pyproject.toml` o `requirements`), ubicación y versiones, consultadas el día del design. No se proponen números aquí. Incluye la dependencia de test del cliente HTTP (`TestClient` la requiere) y cualquier plugin de pytest. (`08` "Versiones y dependencias"; D116.)
2. **Nombre y ubicación de los directorios**: la KB usa `backend/app/...` y `backend/tests/`; `openspec/config.yaml` y la DoD hablan de `app/domain`; la consigna nombra `src/` y `tests/` como estructura mínima con nombres variables. Decidir una estructura y su relación con `README.md` en la raíz. (`08` "Estructura de directorios"; ver sección 9.)
3. **Cómo se levanta la API para Swagger**: comando `uvicorn`, módulo de entrada, qué base usa la demo sin PostgreSQL (memoria con seed al arrancar o archivo SQLite) y cómo se cargan los datos ficticios de la demo. Sin endpoints de lectura, los ids de la demo deben ser conocidos. (`08` DoD ítem 4: "se fija en el design".)
4. **Contrato HTTP**: nombres de los campos del cuerpo y de la respuesta `201` (qué campos devuelve el turno), forma del `type`/`title` de cada error (los `type` son propuesta aceptada), y cómo se adapta el `422` de validación de Pydantic de FastAPI al formato `problem+json` (por defecto devuelve otra forma). (`08` mapeo HTTP y cuerpo E12; RN-GL-04 "nombres... se fijan en el design".)
5. **Zona horaria en `Intervalo`**: campo, parámetro del constructor o validación aparte para RN-AG-10d; de dónde sale la zona al ejecutar el caso de uso (`Consultorio.zona_horaria` vía el profesional). (`08` "Contrato", "Reloj y zonas".)
6. **Código de error de los intervalos inválidos**: RN-AG-10d tiene código; `inicio >= fin` también; para datetime naive o con otro offset (RN-GL-01) no hay código RN asignado. Qué excepción lanza `Intervalo` y cuál llega a la API frente a la validación de Pydantic. (RN-GL-02; `08` "Reloj y zonas".)
7. **Varias referencias inválidas a la vez** (por ejemplo prestación y sillón inexistentes): `RecursoNoEncontrado` modela un único recurso; RN-GL-02 pide lista de códigos cuando se infringen varias reglas. Decidir si se informa solo el primero o todos. (`08` contrato; RN-GL-02.)
8. **Qué `turno_id` lleva cada `Conflicto`** si el candidato choca con dos turnos existentes del mismo recurso: el contrato dice "una por recurso" con un único `turno_id`. (`08` contrato.)
9. **Cómo se identifica el sillón y el profesional por defecto** (RN-AG-06, Flujo 1 "profesional único"): ni `Sillon` ni `Profesional` tienen columna de "por defecto"; criterios posibles a decidir (único activo, menor id, etc.) y qué ocurre si hay cero o varios. El contrato prevé `recurso_id = None` cuando no hay sillón por defecto. (`04` Sillon; `08` `RecursoNoEncontrado`.)
10. **Pertenencia al consultorio**: si paciente, prestación, profesional y sillón deben ser del mismo consultorio y de dónde sale `Turno.consultorio_id`; `CrearTurnoComando` no lo incluye. La KB no lo dice. (`04` Turno; `08` comando.)
11. **Granularidad de RN-AG-01** (5 minutos por constante, D99): si el change valida la duración de la prestación o solo la usa; las prestaciones se crean por seed o factories y no hay endpoint de alta. (RN-AG-01.)
12. **Unidad de trabajo y sesión en la API**: forma de `UnidadDeTrabajo`, dependencia de sesión, y cómo `TestClient` y el servidor comparten la base en memoria con endpoints sincrónicos. **A verificar en el change, antes de las pruebas de API**: SQLite y hilos con `StaticPool` (FastAPI ejecuta los endpoints sincrónicos en un pool de hilos; la conexión de `pysqlite` por defecto rechaza el uso desde otro hilo). (`08` "Fixtures de test": "ajustes exactos de conexión se fijan en el design".)
13. **Test de ida y vuelta de zonas horarias y su normalización en el adaptador**: tipo de columna y mecanismo (por ejemplo un `TypeDecorator`) para que SQLite devuelva aware UTC. **A verificar en el change, antes de cerrar el primer change** (D85).
14. **Test de imports de `app/domain`**: lista de módulos prohibidos y método (recorrido de `ast` o similar); la regla dice "solo biblioteca estándar", pero la zona horaria requiere `zoneinfo` (ver riesgo R4). (`08` "Regla de capas"; D70.)
15. **Test guard de fechas**: cómo recorre los metadatos (`DateTime(timezone=True)`) y cómo busca `utcnow()`/`now()` sin zona en el código. (`08` DoD.)
16. **Tabla escenario-test**: README o design. (`08` DoD.)
17. **Perfil de ejecución de pytest**: dónde vive la configuración (en el archivo único), desde qué directorio se corre `pytest`, y el marcador `postgres` que no se crea aquí (lo crea C-02). (`08` "Estrategia de tests".)
18. **Gestión de `.gitignore`** y de variables de entorno: `DATABASE_URL` figura en la KB pero C-02 fija "los nombres definitivos de las variables de entorno y `.env.example`"; decidir si este change lee alguna variable o usa constantes. (`CHANGES.md` C-02; `08` "Variables de entorno".)
19. **Estructura de los factories y del seed de demo** y sus datos ficticios concretos (nombres, teléfonos con prefijo de prueba). (`04` seed; RN-PR-01.)

## 9. Inconsistencias encontradas

Se reportan, no se resuelven.

1. **`Consultorio.creado_en`**: la tabla de `Consultorio` en `04` lo declara NN, y la lista "Columnas que NO crea" del subconjunto del primer change lo excluye (marcado †). Misma situación en `Paciente.creado_en` (NN en la tabla, excluido del primer change) y `Turno.actualizado_en`/`version` (NN en la tabla, excluidos). Para `Consultorio` y `Paciente` la KB no dice si el seed puede prescindir de la columna; para `Turno`, `CHANGES.md` aclara que se agregan "cuando su design los necesite (previsto en C-16)".
2. **Tamaño del change**: `CHANGES.md` define cada change como "de 3 a 6 escenarios y alrededor de 20 tareas", y C-01 tiene 8 escenarios (E1 a E7 y E12) más E8 como test unitario, cuatro tests transversales, API, seis tablas y deps. La consigna también pide un change chico. La KB (SU-08) confirma los 8, pero no reconcilia con la regla de 3 a 6.
3. **Estructura de directorios**: `08` ubica el código en `backend/app/` y los tests en `backend/tests/` (con `pyproject.toml` en `backend/` y `README.md` en la raíz); `openspec/config.yaml`, `CLAUDE.md` y la DoD hablan de `app/domain`; el encargo menciona `src/` y `tests/`. No hay contradicción de fondo pero los tres nombres circulan.
4. **Seed**: `04` "Seed data inicial" dice que el seed del primer change incluye cinco tablas, pero la lista que sigue incluye `Usuario`, `ConfiguracionReglas` y un horario recurrente (de changes posteriores) sin marcarlos como futuros en la lista (solo lo aclara la frase previa). Además `06` US-004 CA-1 asigna "el seed crea Sillón 1" a un change posterior, mientras C-01 necesita ese sillón. Y `08` DoD dice que cómo se cargan los datos de la demo "se fija en el design", mientras `08` "Fixtures" dice que no hay seed compartido entre tests.
5. **Prestación**: `04` declara `color` NN, pero C-01 no lo crea y el seed dice "cada una con un color"; sin consecuencia si el seed lo omite, pero queda sin aclarar.
6. **Cobertura de API**: `08` pide como mínimo E1, E4 y E12 en los tests de API; la DoD y `06` piden un test por escenario (E1..E7, E12) sin precisar en qué capa. Compatible, pero no unívoco.
7. **Errores de intervalo en la API**: `08` mapea "cuerpo inválido (`inicio` naive) o intervalo inválido" a `422`, y RN-GL-01 dice que el dominio rechaza naive/otro offset, pero ningún código RN se asigna a ese rechazo, mientras RN-GL-02 exige código RN en todo rechazo por regla.
8. **Rama principal**: el encargo y el entorno indican rama principal `main` y el repositorio está en `master`; el Git tag del hito se pone al archivar (`CHANGES.md`). Sin efecto en el change; se anota por la etiqueta.
9. **Lectura de la consigna**: el relevamiento no leyó `Consigna.pdf` directamente; las exigencias citadas se verificaron después contra el PDF (2026-10-07). La consigna pide «al menos 3 escenarios» (uno feliz, uno de error de negocio y uno de borde) y muestra `src/` y `tests/` en la «estructura mínima», aclarando que «los nombres exactos de algunos archivos pueden variar»; exige además un `README.md` en la raíz con el que se pueda clonar y correr los tests.

## 10. Riesgos

- **R1. Tamaño.** Muchas piezas para "una sola funcionalidad" (inconsistencia 2). Mitigación: orden estricto por escenario en RED, GREEN, TRIANGULATE, REFACTOR y diferir cualquier adorno (sin endpoints de lectura, sin migraciones).
- **R2. Reproducibilidad en clon limpio.** El comando de instalación debe usar solo el archivo único y declarar toda dependencia de test; olvidar el cliente HTTP de `TestClient` o un plugin rompe el clon. Verificar en un entorno nuevo (DoD).
- **R3. SQLite, zonas y hilos.** SQLite devuelve datetimes naive (R-10, D85) y la conexión en memoria con hilos de FastAPI exige configuración específica. Ambos están marcados "A verificar en el change".
- **R4. `zoneinfo` en Windows.** `RN-AG-10d` convierte a `America/Argentina/Buenos_Aires`; en Windows `zoneinfo` no trae base de zonas propia y requiere el paquete de datos de zonas instalado, mientras `domain` solo admite biblioteca estándar. Hay que decidir cómo se declara esa dependencia en el archivo único (sin número aquí) y si el test de imports la permite. Es un riesgo derivado del entorno (Windows) del autor, no reportado en la KB.
- **R5. Forma del error de validación.** El `422` automático de FastAPI/Pydantic no es `problem+json` con `codigos`; si no se adapta, el comportamiento observado en `/docs` contradice el contrato.
- **R6. Demo sin PostgreSQL.** Con base en memoria el seed debe correr al arrancar y los ids deben ser predecibles; si no, el video de `/docs` no puede armar un cuerpo válido.
- **R7. Ambigüedades de contrato** (ítems 6 a 10 de la sección 8) pueden generar retrabajo si se descubren en el apply.
- **R8. Endpoint abierto.** `POST /turnos` sin autenticación es aceptable solo con datos ficticios y sin despliegue público (DD-14); el README debe declararlo.
- **R9. Higiene del repo.** Sin `.gitignore` de Python, existe riesgo de versionar entorno, cachés o un `.env` (regla dura 1).
- **R10. Procedimiento.** Reglas 10 y 11 de CLAUDE.md: commits solo con ok del autor, en español, con prefijo y `Co-Authored-By`; TDD estricto exige que el historial muestre el test antes del código.

## 11. Preguntas para el autor

No se inventó ninguna respuesta. Ordenadas por bloqueo del propose/design.

1. **Directorios.** ¿Se adopta `backend/app` y `backend/tests` como en `08`, o `app/` y `tests/` en la raíz, o `src/` y `tests/`? ¿Dónde vive el archivo único de dependencias y desde qué directorio se corre `pytest` según el README?
2. **Tamaño.** ¿Se acepta que C-01 tenga 8 escenarios y supere el "3 a 6" de `CHANGES.md`, o se prefiere recortar (por ejemplo, mover alguna prueba transversal)?
3. **Demo con Swagger.** Sin PostgreSQL, ¿la demo usa SQLite en memoria con seed al arrancar, o un archivo SQLite? ¿Se acepta que los ids de la demo sean fijos y estén documentados en el README, sin endpoints de lectura?
4. **Defaults de RN-AG-06.** ¿Cómo se identifica el sillón (y el profesional) por defecto: único activo, primero por id, u otro criterio? ¿Qué se hace si no hay ninguno o hay varios?
5. **Consultorio.** ¿Debe verificarse que las cuatro referencias pertenezcan al mismo consultorio y de dónde sale `Turno.consultorio_id`?
6. **Varias referencias inválidas.** ¿`RN-GL-04` informa solo la primera referencia inválida o todas?
7. **Intervalos inválidos.** ¿Qué código RN o mensaje se asigna a naive/offset distinto de UTC y a `inicio >= fin`? ¿Y se reflejan igual en la API que en el dominio?
8. **Conflictos.** Si el candidato choca con dos turnos del mismo recurso, ¿`conflictos` lista un `Conflicto` por recurso con el primer `turno_id`, o uno por turno en conflicto?
9. **Columnas con †.** Para `Consultorio.creado_en` y `Paciente.creado_en`: ¿se omiten en el primer change como indica el subconjunto, o se incluyen?
10. **Granularidad.** ¿El change valida que la duración de la prestación sea múltiplo de 5 (RN-AG-01) o eso queda para US-001?
11. **zoneinfo y datos de zona.** ¿Se acepta declarar el paquete de datos de zonas en el archivo único para que funcione en Windows, aunque `domain` solo importe biblioteca estándar?
12. **Consigna.** Resuelta: el texto se verificó contra el PDF el 2026-10-07 (ver la inconsistencia 9 de la sección 9).

## 12. Recomendación para el Propose

- Proponer `crear-turno-sin-solapamientos` tal cual está en `CHANGES.md`: una capability (agenda: creación de turno sin solapamientos), US-010, E1 a E7 y E12 en el spec; E8 como test unitario fuera del spec; E9, E10 y E11 como "Fuera de alcance" citados.
- En el `proposal.md`: justificar el encaje en D.3 punto 4 en 2-3 líneas (sección 6), incluir "Fuera de alcance" con la lista de la sección 2 y citar US-010 y los escenarios que cubre y deja fuera (regla de `openspec/config.yaml`).
- En el `spec.md`: un Requirement por regla (RN-AG-05/08, RN-AG-09, RN-AG-10, RN-GL-04, RN-AG-02) con SHALL y WHEN/THEN, el ID del escenario en el título, horarios en UTC y los ejemplos numéricos de `07`.
- En el `design.md`: resolver los ítems 1 a 5 y 12 a 14 de la sección 8 antes que el resto, marcar "Propuesta" lo no confirmado, "A verificar en el change" lo técnico pendiente (hilos de SQLite, ida y vuelta de zonas, `zoneinfo`) con el hito antes del cual se verifica, y fijar los pins consultando las versiones el día del design (no inventarlas). Incluir "Non-goals".
- En las `tasks.md`: orden por escenario, test primero; cada tarea de test cita E# y RN; los tests transversales (ida y vuelta, imports, guard de fechas) en tareas propias; tarea final en clon limpio solo con el README y tarea de prueba de `POST /turnos` en `/docs` (`201`, `409` con códigos, `422` con `RN-GL-04`).
- Antes de proponer, conviene que el autor responda al menos las preguntas 1 a 4, 6 y 7 de la sección 11; el resto puede resolverse en el design como "Propuesta".

## 13. Decisiones del autor tras el relevamiento (2026-10-07)

El autor respondió las preguntas de la sección 11. Las decisiones se registran en `knowledge-base/10_preguntas_abiertas.md` y son la entrada del Propose.

| # | Pregunta | Decisión del autor |
|---|---|---|
| 1 | Directorios | `backend/app` y `backend/tests`, archivo de dependencias en `backend/` y `README.md` en la raíz. El design documenta por qué `backend/` y no `src/` |
| 2 | Tamaño | Se aceptan los 8 escenarios como excepción al «3 a 6» de `CHANGES.md`, registrada en el change |
| 3 | Demo con Swagger | SQLite en memoria con datos ficticios cargados al arrancar; identificadores fijos documentados en el README, con un ejemplo de petición |
| 4 | Sillón y profesional por defecto | Si no se indica, se usa el único activo del consultorio; si no hay ninguno o hay más de uno, se rechaza. Se documenta como regla nueva `RN-AG-14` |
| 5 | Consultorio | En la v1 un profesional pertenece a un consultorio; el consultorio del turno sale del profesional y una referencia de otro consultorio se trata como inexistente |
| 6 | Varias referencias inválidas | El error lista todas las referencias inválidas, no solo la primera |
| 7 | Fechas sin zona o con otro desfase | Se rechazan con el código `RN-GL-01` |
| 8 | Choque con dos turnos del mismo recurso | Un conflicto por recurso, con el turno que empieza primero; el error indica ambos recursos (profesional y sillón) cuando chocan los dos |
| 9 | Columnas `creado_en` de consultorio y paciente | Se omiten, como indica el subconjunto del primer change |
| 10 | Granularidad de la duración | No se valida en este change; queda para `gestion-de-prestaciones` |
| 11 | Zonas horarias en Windows | Se declara el paquete de datos de zonas en el archivo único de dependencias y se documenta en el README |
| 12 | Consigna | Verificada contra el PDF (sección 9, punto 9) |
