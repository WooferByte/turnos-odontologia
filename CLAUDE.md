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
| Base de datos | PostgreSQL (producción / docker-compose) | No fijada (pin en el `design.md` del change que la use) |
| Base de datos de tests | SQLite en memoria, `sqlite+pysqlite:///:memory:` con `StaticPool` (DD-03, DD-12); sin `aiosqlite` | — |
| Asincronía | Redis: tarea periódica que persiste vencimientos y dispara efectos (RN-GL-05); no interviene en el primer change | No fijada (pin en el `design.md` del change que la use) |
| Contenedores | Docker y Docker Compose | No fijada |
| Frontend | React + TypeScript + Vite (no interviene en el primer change; empieza en la fase 3) | No fijada |
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
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | Inconsistencias, preguntas priorizadas y registro de decisiones del autor (D1..D138) |
| [11_integraciones_whatsapp_y_mercadopago.md](knowledge-base/11_integraciones_whatsapp_y_mercadopago.md) | Implementar o diseñar recordatorios (`wa.me` / Cloud API) o la seña con Checkout Pro |
| [12_contexto_de_mercado.md](knowledge-base/12_contexto_de_mercado.md) | Entender competidores y vacíos del mercado; justificar una decisión de producto |

> **Estado de `10_preguntas_abiertas.md`**: las tres preguntas de prioridad **Alta** (P-01, P-02, P-03: legales) están **cerradas** (2026-10-03) como fuera del alcance académico; requieren revisión legal antes de uso real, y la seña solo se usa con credenciales de prueba. No queda ninguna pregunta Alta abierta antes del primer change. Quedan diferidas (Fase 2 o fuera de la v1) P-04, P-05, P-06, P-07 y P-15. Antes de implementar un change, repasá igual el registro de decisiones del archivo: las decisiones D29 a D118 (cerradas el 2026-10-05) precisan reglas que aparecen en `05` y `06`.

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

Las seis skills `openspec-*` viven en `.claude/skills/` del proyecto (es la única copia); son las que usan los comandos `/opsx:*`. El resto está en `~/.claude/skills/`.

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry` y versionado en este repo, con las reglas de cada skill que no aplican al proyecto marcadas como tales). Esta tabla solo mapea skill→rol.

---

## Roadmap de Changes

El plan de implementación completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 48 changes en 9 fases (la fase 9, reportes C-47 y C-48, es extensión fuera del MVP).
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
2. **NUNCA** fechas naive ni `datetime.now()` directo → fechas aware en UTC con un único `utc_now()` inyectable; intervalos semiabiertos `[inicio, fin)`. Única excepción: RN-AG-10d (medianoche del consultorio, usa `Consultorio.zona_horaria`).
3. **NUNCA** importar FastAPI ni SQLAlchemy desde `backend/app/domain` → las reglas de agenda son funciones puras de dominio, testeadas sin base de datos.
4. **NUNCA** un error de regla de negocio sin su código RN → la validación de entrada se informa toda junta en un único 422 y las reglas de negocio de a una, solo con la entrada válida (RN-GL-02, D135; el solapamiento es una regla y puede llevar dos códigos, E4); referencia inválida en el cuerpo = 422 (RN-GL-04), recurso inexistente en la URL = 404.

### Stack y tests

5. **NUNCA** sesiones asíncronas, `aiosqlite` ni `pytest-asyncio` → SQLAlchemy 2.x sincrónico, estilo 2.x, en todos los changes (DD-12, D119).
6. **NUNCA** mocks de sesión ni de repositorio → SQLite en memoria (`StaticPool`, engine por test); la suite por defecto corre sin Docker, PostgreSQL ni Redis, solo con el README.
7. **NUNCA** inventar versiones ni repartir dependencias → un archivo único con versiones exactas, fijado en el design de C-01 y ampliado en el design de cada change (D116).
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
   (ej.: /opsx:propose crear-turno-sin-solapamientos)
4. Implementar las tasks (cargando skills)       → respetando las reglas duras, TDD estricto
5. /opsx:archive <nombre-del-change> + marcar [x] en CHANGES.md → cerrar el change
```

Aplicar TODAS las reglas duras en cada paso. Las reglas duras provienen de la KB: ante un conflicto entre este archivo y `knowledge-base/` (o `openspec/config.yaml`), no elijas en silencio: avisale al autor.
