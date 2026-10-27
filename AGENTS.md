# Turnos Odontológicos AR — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.

**Qué es el proyecto**: sistema de gestión de turnos y agenda para odontólogos independientes y consultorios chicos de Argentina. Reemplaza el papel, el Excel y el WhatsApp suelto: agenda con duraciones por prestación, prevención de solapamientos por profesional y por sillón, reserva pública por link, recordatorios por WhatsApp (`wa.me` en la v1), seña con Mercado Pago, trazabilidad de cambios de turno y ficha clínica mínima. El paciente no tiene cuenta: gestiona su turno con un token. Todos los datos son ficticios.

---

## Stack Tecnológico

Las versiones exactas **no están decididas a propósito**: el criterio es versiones exactas en un único archivo de dependencias (`backend/pyproject.toml`, D137), que se fija en el `design.md` del primer change y se amplía en el de cada change siguiente (D72, D116), sin tomar ninguna versión publicada en la última semana (D133). **No inventes números de versión.**

| Capa | Tecnologías | Versión mínima |
|------|-------------|----------------|
| Lenguaje backend | Python | 3.11+ (confirmada por el autor) |
| Framework API | FastAPI (validación con Pydantic, incluido en FastAPI) | Serie 0.115.x (D133); pin exacto en el `design.md` del primer change |
| Autenticación | JWT (access y refresh token, HS256) y hash bcrypt | No fijada |
| ORM / acceso a datos | SQLAlchemy, **modo síncrono** en todos los changes (DD-12, D119) | Serie 2.0.x (no la 2.1; D133), API declarativa tipada |
| Base de datos | PostgreSQL (producción / docker-compose), con driver `psycopg` 3 y migraciones Alembic desde C-02 (DD-15) | 17.10, imagen `postgres:17.10-bookworm` fijada con etiqueta y digest (D143, D144) |
| Base de datos de tests | SQLite en memoria, `sqlite+pysqlite:///:memory:` con `StaticPool` (DD-03, DD-12); sin `aiosqlite` | — |
| Asincronía | Redis: tarea periódica que persiste vencimientos y dispara efectos (RN-GL-05); no interviene en el primer change | No fijada (pin en el `design.md` del change que la use) |
| Contenedores | Docker y Docker Compose; PostgreSQL se publica en `127.0.0.1:5434` y la API en `127.0.0.1:8000` (D153) | Imágenes fijadas con etiqueta y digest (D144) |
| Frontend | React 19.3.0, React Router 7.18.4, TypeScript 6.0.3, Vite 8.3.4, Node 24 LTS (desde C-08; D223, D224); pruebas con Vitest 5.0.3 y jsdom 30.1.2 | Pins exactos en `frontend/package.json` con su `package-lock.json` (D217) |
| Tests backend | pytest + cliente de pruebas de FastAPI (D84) | — |

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---------|---------------|
| [README.md](knowledge-base/README.md) | Índice de la KB y orden de lectura sugerido |
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Entender propósito, segmento, casos de uso, alcance de la v1 y qué queda fuera |
| [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) | Stack, arquitectura general, integraciones y resumen de la API REST |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Auth, RBAC, permisos y rutas públicas |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades, ERD, convenciones, migraciones y subconjunto del primer change |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | Reglas codificadas (RN-XX): solapamientos, estados del turno, seña, lista de espera, globales |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Historias de usuario, criterios de aceptación, escenarios E1..E12 y orden de implementación |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos E2E (crear turno, reserva, WhatsApp, seña, cancelar, lista de espera, ficha, auth) |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrones, directorios, regla de capas, reloj/UTC, estrategia de tests, versiones, Definition of Done |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | Decisiones DD, supuestos SU y riesgos R: por qué se eligió cada cosa |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | Inconsistencias, preguntas priorizadas y registro de decisiones del autor (D1..D314) |
| [11_integraciones_whatsapp_y_mercadopago.md](knowledge-base/11_integraciones_whatsapp_y_mercadopago.md) | Implementar o diseñar recordatorios (`wa.me` / Cloud API) o la seña con Checkout Pro |
| [12_contexto_de_mercado.md](knowledge-base/12_contexto_de_mercado.md) | Entender competidores y vacíos del mercado; justificar una decisión de producto |

> **Estado de `10_preguntas_abiertas.md`**: las tres preguntas de prioridad **Alta** (P-01, P-02, P-03: legales) están **cerradas** (2026-10-03) como fuera del alcance académico; requieren revisión legal antes de uso real, y la seña solo se usa con credenciales de prueba. No queda ninguna pregunta Alta abierta antes del primer change. Quedan diferidas (Fase 2 o fuera de la v1) P-04, P-05, P-06, P-07 y P-15. Antes de implementar un change, repasá igual el registro de decisiones del archivo: las decisiones D29 a D118 (cerradas el 2026-10-05) precisan reglas que aparecen en `05` y `06`. Las decisiones D142 a D157 (2026-10-13) fijan la infraestructura con PostgreSQL de C-02 y el control de concurrencia al crear turnos: bloqueo de fila por recurso más restricción de exclusión (DD-04). Las decisiones D158 a D170 (2026-10-14) fijan el historial de turnos de C-03: tabla `evento_turno` de solo inserción (disparador en PostgreSQL), actor `usuario` sin id hasta C-07 y `404` con `RN-GL-04` para un recurso de la URL. Las decisiones D171 a D182 (2026-10-14) fijan la gestión de prestaciones de C-04: nombre único sin distinguir mayúsculas, tildes ni espacios (`RN-AG-15`, `409`), duración validada como entrada (`RN-AG-01`, `422`), consultorio único hasta C-07 y migración `0005` con color de relleno. Las decisiones D183 a D194 (2026-10-14) fijan la gestión de sillones de C-05: nombre del sillón no único, se puede desactivar el último activo, `PATCH` con `nombre` y `activo` (reactivación incluida) y sin cambios de esquema. Las decisiones D195 a D203 (2026-10-14) fijan la sesión del panel de C-06: sin límite de peticiones en `/auth/login`, secreto efímero en la demo y en los tests, contraseña del usuario del seed por `SEED_USUARIO_PASSWORD`, `JWT_SECRET` de 32 bytes como mínimo, email normalizado con `UNIQUE` simple, un `401` idéntico por endpoint, refresh sin rotación y el usuario del seed sin roles hasta C-07. Las decisiones D204 a D216 (2026-10-15) fijan la protección del panel de C-07: capability nueva `proteccion-del-panel`, matriz de `03` para las rutas existentes (lectura del catálogo para los tres roles), el mismo `401` de sesión inválida para toda causa y `403` con `RN-AU-05`, el control de acceso evaluado antes que la validación de entrada (precisa RN-GL-02), el usuario del token como actor del historial y creador del turno, una recepcionista ficticia en el seed y la migración `0007` con `usuario_rol` y `CHECK` del rol. Las decisiones D217 a D228 (2026-10-19) fijan el panel base y el inicio de sesión de C-08, el primer change con interfaz: capability nueva `ingreso-al-panel`, un archivo de dependencias por subproyecto (`frontend/package.json` con versiones exactas y su `package-lock.json`, amplía D137), el access token en memoria y el refresh en `sessionStorage`, el mismo origen por `/api` sin cambios de API, el servicio `frontend` de Compose con nginx sin privilegios en `127.0.0.1:5173`, Vitest con un servidor falso de la API inyectado (sin `vi.mock`), Node 24 LTS, TypeScript 6.0.3 y React Router 7.18.4, el panel base sin datos del usuario, el cierre de sesión solo en el cliente y un test guard contra `any`. Las decisiones D229 a D233 (2026-10-19) fijan la pantalla de prestaciones de C-11: capability nueva `pantalla-de-prestaciones`, las acciones visibles para todos los roles con el `403` `RN-AU-05` de la API, el cableado de `SesionTerminada` en C-11, sin validación local de la duración y el selector de color nativo. La decisión D234 (2026-10-19) fija que toda pantalla del frontend se implementa a partir de una pantalla generada en Stitch, no solo de sus tokens (ver «Integraciones MCP»). Las decisiones D235 a D240 (2026-10-20) fijan el inicio de sesión con diseño de Stitch de C-49: «Cargando…» incluido en la verificación de sesión e `InicioDelPanel` fuera, sin subtítulo en la pantalla de ingreso, ícono de espera en SVG en línea, estilos en `panel.css` y tokens nuevos en `tokens.css`, y gobernanza MEDIO (código C-49 al final del índice). Las decisiones D241 a D254 (2026-10-22) fijan la gestión de usuarios de C-09: capabilities nuevas `gestion-de-usuarios` (API) y `pantalla-de-usuarios` (interfaz), contraseña inicial de 10 caracteres a 72 bytes con `RN-AU-07`, código nuevo `RN-AU-08` con `409` para el email repetido, al menos un rol en el alta y en el `PATCH`, formato mínimo propio del email, el profesional vinculado sin cambios hasta Fase 2, quitarse el propio rol `odontologo` si queda otro activo, bloqueo `FOR UPDATE` de `consultorio` antes de contar, sin `GET /auth/yo` ni confirmación al desactivar, tareas agrupadas por tema como excepción al «alrededor de 20» (D251), y el botón «Cerrar» y la nota de roles tomados de Stitch; D252 y D253 fijan el orden de las reglas de un `PATCH` con roles y `activo`, y la edición de roles de un usuario inactivo. Las decisiones D255 a D270 (2026-10-22) fijan el horario recurrente de C-12: capabilities nuevas `horario-recurrente` y `pantalla-de-horario` como excepción limitada a C-12 (D255); un profesional sin franjas no admite turnos y el turno fuera de una sola franja vigente da `422` `RN-AG-04` (D256, D258, D259 y D265); el código nuevo `RN-AG-16` rechaza las franjas superpuestas o invertidas como validación de entrada, con todas juntas y mensajes fijos (D257, D266); `GET /profesionales` es de solo lectura para los tres roles (D260); el `PUT` no toca los turnos existentes (D261) y el horario de un profesional inactivo se lee y se edita (D262); la fábrica de tests carga 00:00-23:59 (D263); la excepción de tamaño de las tareas queda limitada a C-12 (D264); la pantalla fija el primer profesional de la lista cuando no hay activos, con tope de 70 franjas y mensaje de error de red al guardar (D267 a D269); y las rutas del horario usan el consultorio del usuario del token (D270). Las decisiones D271 a D289 (2026-10-26) fijan el bloqueo puntual de C-13: dos capabilities nuevas, `bloqueos-puntuales` y `pantalla-de-bloqueos`, como excepción limitada a C-13 (D271); profesional y sillón a la vez se rechazan con `422` de formato y el `CHECK` de la base (D272); el código nuevo `RN-AG-17` rechaza un bloqueo que no termina después de empezar como validación de entrada (D273); los turnos afectados solo se listan en el `201` del alta, sin cancelarlos (D275); RN-AG-04b se evalúa después del horario y antes del solapamiento, con el `bloqueo_id` del que empieza primero (D280); y los bloqueos admiten cualquier minuto y no tienen tope (D289). Las decisiones D290 a D303 (2026-10-26/27) fijan las contraseñas de usuarios de C-10: dos capabilities nuevas, `contrasenas-de-usuarios` y `pantalla-de-contrasenas`, como excepción limitada a C-10 (D290); el cambio de la propia responde `200` con un access y un refresh nuevos, de modo que la sesión actual sigue y las demás caen (D291); el código nuevo `RN-AU-09` con `422` rechaza la contraseña actual incorrecta, como regla de negocio después de `RN-AU-07` y nunca como `401` (D292); el código nuevo `RN-AU-10` con `409` rechaza restablecer la propia, y «cualquier usuario» de `RN-AU-07` se lee como cualquier otro (D293); un usuario inactivo se restablece y sigue inactivo, y la nueva igual a la actual se acepta (D294, D295); la repetición de la nueva va solo en «Mi contraseña», y «Restablecer contraseña» es una acción de fila con «Mi contraseña» en `/panel/contrasena` (D296, D297); el permiso nuevo `contrasena.propia` va para los tres roles y un usuario sin roles recibe `403` `RN-AU-05` (D298); restablecer y cambiar la propia leen al usuario con bloqueo de fila `FOR UPDATE` para que cada cambio corte los tokens del otro (D299); 29 tareas en 13 grupos para 38 escenarios son excepción limitada a C-10 (D300); las pantallas de Stitch se consiguen antes de aprobar el plan (D301); la guía de prueba manual va en `docs/guias/` (D302); y la fila del usuario no se resalta mientras se restablece su contraseña (D303). Las decisiones D304 a D314 (2026-10-27) fijan el usuario de la sesión de C-50: dos capabilities nuevas, `usuario-de-la-sesion` y `encabezado-del-panel`, como excepción limitada a C-50 (D304); la ruta `GET /auth/yo` devuelve solo `email` y `roles`, con los roles en el orden fijo del enum y sin caché (D305, D306); el permiso nuevo `sesion.leer` va para los tres roles y un usuario sin roles recibe `403` `RN-AU-05` (D307); el encabezado muestra el email y los roles con las etiquetas de la pantalla de usuarios, separadas por « · » (D308); el panel lo pide una vez por entrada y no muestra una respuesta que llega después de «Cerrar sesión» (D309); ante una falla que no es `401` (red, `5xx`, `403` o una respuesta de otra forma) el indicador no se muestra y la sesión sigue (D310); debajo de 720 px la barra pasa a filas y el email se corta con puntos suspensivos (D311); ocultar acciones según el rol queda para un change posterior y D230 y D249 siguen (D312); la ruta quedó en `02` y en la matriz de `03` antes del Apply (D313); y 24 tareas en 10 grupos para 24 escenarios son excepción limitada a C-50 (D314).

---

## Skills Disponibles

Fuente de verdad: [.atl/skill-registry.md](.atl/skill-registry.md). Cargá la skill correspondiente al contexto ANTES de escribir código.

| Agente | Rol | Skills que carga | Desde qué fase |
|--------|-----|------------------|----------------|
| **Backend / API** | FastAPI, dominio puro, errores de dominio, capas | `fastapi-templates`, `python-design-patterns`, `python-error-handling`, `python-testing-patterns` | Fase 1 (API-only en fases 1 y 2) |
| **Base de datos e infraestructura** | PostgreSQL, migraciones Alembic, Docker | `supabase-postgres-best-practices`, `database-migration`, `multi-stage-dockerfile` | Fase 2 (infraestructura con PostgreSQL; Alembic recién ahí, DD-15) |
| **Acceso / autenticación** | JWT, bcrypt, roles y protección del panel | `auth-implementation-patterns` | Fase 3 (el primer change no lleva auth, DD-14) |
| **Frontend** | React + TypeScript + Vite | `vercel-react-best-practices` | Fase 3 (la interfaz empieza con el inicio de sesión) |
| **Orquestación** | OPSX / fundación del proyecto | `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, `openspec-explore`, `openspec-sync-specs`, `openspec-update-change`, `active-orchestrator`, `kb-creator`, `roadmap-generator`, `agent-instruction`, `skill-registry`, `find-skill`, `skill-creator` | Siempre |
| **Revisión de changes** | Revisar la spec y las tasks de un change contra la KB (solo informa, no edita) | `revisor-de-escenarios` | Desde la fase 3 (C-11 en adelante); aplica a todo change con `spec.md` y `tasks.md` |

Las seis skills `openspec-*` y `revisor-de-escenarios` viven en `.claude/skills/` del proyecto (es la única copia, versionada en el repo); las `openspec-*` son las que usan los comandos `/opsx:*`. El resto está en `~/.claude/skills/`.

### `revisor-de-escenarios` (skill propia)

- **Qué es**: skill propia del proyecto, creada con `skill-creator` (ver [docs/skills-mcp/investigacion.md](docs/skills-mcp/investigacion.md)). Revisa los escenarios (`specs/*/spec.md`) y las tasks de un change contra la KB, `CHANGES.md` y `openspec/config.yaml`.
- **Quién la usa**: el rol de orquestación y revisión de changes.
- **Cuándo**: después de `/opsx:propose` o `/opsx:update` y **antes** de aprobar el plan o de arrancar `/opsx:apply`; también cuando se pregunte si un change «está listo para implementar».
- **Qué necesita**: el nombre del change (`openspec/changes/<nombre>/`), más la KB (`knowledge-base/`, sobre todo `05` y `06`), `CHANGES.md` y `openspec/config.yaml`.
- **Cómo revisar el resultado**: el resultado es un **informe**, no una edición: la skill no toca spec, tasks ni design. Cada hallazgo cita su fuente (archivo y sección, código RN, decisión D o regla de `config.yaml`) y se clasifica como bloqueante, a corregir o sugerencia. Las correcciones las decide el autor (o las hace `/opsx:update` con el informe a la vista); un hallazgo sin fuente es una opinión y no manda sobre la KB.
- **Evidencia**: [docs/skills-mcp/evidencias/](docs/skills-mcp/evidencias/) (evaluación con y sin la skill).

---

## Integraciones MCP

Un servidor MCP **no es una skill**: es una integración externa y no se registra en `.atl/skill-registry.md`. Configuración y pasos en [docs/skills-mcp/mcp-stitch.md](docs/skills-mcp/mcp-stitch.md).

- **Stitch (Google)**, versionado en `.mcp.json` (servidor HTTP remoto).
  - **Propósito**: dar un diseño visual previo a las pantallas del panel, que el proyecto no tiene.
  - **Capacidades que se usan**: generar el diseño de una pantalla a partir de un texto y consultar los diseños ya generados. La lista exacta de herramientas se confirma al conectar (ver el documento).
  - **Cuándo**: **obligatorio en todo change con interfaz** (D234). El `/opsx:explore` o el `/opsx:propose` genera la pantalla con el design system del proyecto («Clinical Ops»); el `design.md` cita el id de la pantalla (`projects/…/screens/…`) y su evidencia (captura y HTML); el `/opsx:apply` la implementa traduciendo su HTML a los tokens CSS del proyecto, sin dependencias nuevas (ni Tailwind ni fuentes o íconos por CDN); la prueba en el navegador compara la implementación con la captura. Si Stitch no entrega la pantalla, el change de interfaz no se cierra.
  - **Límites**: solo textos y datos ficticios del dominio; nunca datos de pacientes (RN-PR-01) ni secretos. El diseño es una referencia visual: la KB y la spec mandan, y ante un conflicto se sigue la KB. No se usa para modificar código. La API key vive fuera del repo, en la variable de entorno `STITCH_API_KEY`.
- `context7` (documentación de librerías) y `engram` (memoria) están conectados a nivel global del autor, no versionados en el repo.

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry` y versionado en este repo, con las reglas de cada skill que no aplican al proyecto marcadas como tales). Esta tabla solo mapea skill→rol.

---

## Roadmap de Changes

El plan de implementación completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 50 changes en 9 fases (la fase 9, reportes C-47 y C-48, es extensión fuera del MVP).
- **Fases**: 1 change de la consigna · 2 base persistente y catálogos (solo API) · 3 usuarios y acceso, primera interfaz y horario · 4 operación diaria del panel · 5 reglas, consentimiento, reserva pública y link de gestión · 6 tarea periódica, mensajes y lista de espera · 7 seña con Mercado Pago · 8 ficha clínica, presupuestos y pagos · 9 reportes.
- **Camino crítico** (15 changes): `C-01 → C-02 → C-03 → C-07 → C-08 → C-20 → C-23 → C-25 → C-26 → C-28 → C-34 → C-35 → C-36 → C-37 → C-40`.
- **Primer change**: `C-01` = `crear-turno-sin-solapamientos` (US-010, gobernanza MEDIO; es el change de la consigna y el hito de entrega, se etiqueta en Git al archivarlo). El comando es `/opsx:propose crear-turno-sin-solapamientos`: el nombre kebab-case es inmutable y el código `C-NN` es solo el índice de `CHANGES.md`.
- Las fases 1 y 2 se implementan y prueban como **API**; la interfaz empieza en la fase 3.

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras

> Reglas **globales** ya definidas en `~/.claude/CLAUDE.md` (orquestador, governance, TDD, engram): el proyecto las **hereda**, no se repiten acá. Acá viven solo las reglas **específicas de este proyecto** y las universales que el global no cubre (reglas de commit). Son contrato; romperlas es un defecto. Las 12 fueron confirmadas por el autor el 2026-10-06.

### Dominio y datos

1. **NUNCA** datos reales de pacientes en seeds, tests, ejemplos o demos (RN-PR-01), ni secretos o `.env` en el repo → datos ficticios siempre.
2. **NUNCA** fechas naive ni `datetime.now()` directo → fechas aware en UTC con un único `utc_now()` inyectable; intervalos semiabiertos `[inicio, fin)`. Excepciones: RN-AG-10d (medianoche del consultorio) y RN-AG-04 (horario del profesional), ambas en la zona del consultorio (`Consultorio.zona_horaria`; RN-GL-01).
3. **NUNCA** importar FastAPI ni SQLAlchemy desde `backend/app/domain` → las reglas de agenda son funciones puras de dominio, testeadas sin base de datos.
4. **NUNCA** un error de regla de negocio sin su código RN → la validación de entrada se informa toda junta en un único 422 y las reglas de negocio de a una, solo con la entrada válida (RN-GL-02, D135; el solapamiento es una regla y puede llevar dos códigos, E4); referencia inválida en el cuerpo = 422 (RN-GL-04), recurso inexistente en la URL = 404.

### Stack y tests

5. **NUNCA** sesiones asíncronas, `aiosqlite` ni `pytest-asyncio` → SQLAlchemy 2.x sincrónico, estilo 2.x, en todos los changes (DD-12, D119).
6. **NUNCA** mocks de sesión ni de repositorio → SQLite en memoria (`StaticPool`, engine por test); la suite por defecto corre sin Docker, PostgreSQL ni Redis, solo con el README.
7. **NUNCA** inventar versiones ni repartir dependencias → un archivo único por subproyecto con versiones exactas: `backend/pyproject.toml` para la API y `frontend/package.json` con su `package-lock.json` para la interfaz (D217, amplía D137); se fijan en el design de cada change que las agregue (D116).
8. **NUNCA** usar `any` en TypeScript → `tsconfig` estricto y componentes en PascalCase. Aplica desde la fase 3 (cuando empieza la interfaz). Propuesta del agente aceptada por el autor (D120).

### Proceso

9. **NUNCA** aplicar una regla de skill que contradiga `knowledge-base/` u `openspec/config.yaml` → la KB manda; las reglas marcadas como no aplicables en `.atl/skill-registry.md` no se usan.
10. **NUNCA** commitear sin el ok explícito del autor, ni fusionar (squash) o reescribir el historial → la trazabilidad de commits puntúa en la consigna; cada etapa cierra con un commit de nombre claro.
11. Artefactos, documentación y mensajes de commit **en español**, con prefijo convencional (`docs:`, `feat:`, `test:`, `chore:`…) y la línea `Co-Authored-By` del agente, como en el historial existente.
12. **NUNCA** implementar algo fuera del alcance del change en curso ni fuera de la v1 (sobreturnos, excepción de horario) → un change, una capability.

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/)        → entender el dominio
2. Identificar el change en CHANGES.md           → respetar dependencias
3. /opsx:propose <nombre-del-change>             → proposal + design + specs + tasks
   (ej.: /opsx:propose crear-turno-sin-solapamientos; si el change tiene interfaz, la pantalla se genera
   en Stitch y el design cita su id: ver «Integraciones MCP», D234)
4. Revisar con `revisor-de-escenarios`           → informe de la spec y las tasks contra la KB;
   el autor decide las correcciones               (bloqueantes resueltos antes de aprobar el plan)
5. Implementar las tasks (cargando skills)       → respetando las reglas duras, TDD estricto
6. /opsx:archive <nombre-del-change> + marcar [x] en CHANGES.md → cerrar el change
```

Aplicar TODAS las reglas duras en cada paso. Las reglas duras provienen de la KB: ante un conflicto entre este archivo y `knowledge-base/` (o `openspec/config.yaml`), no elijas en silencio: avisale al autor.
