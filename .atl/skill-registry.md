# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

See `_shared/skill-resolver.md` for the full resolution protocol.

> **PRECEDENCE (read first): `knowledge-base/` and `openspec/config.yaml` OVERRIDE any skill rule.**
> Project stack: Python 3.11+, FastAPI, SQLAlchemy 2.x **SYNCHRONOUS**, JWT (HS256, bcrypt), PostgreSQL + Redis + Docker Compose; React + TypeScript + Vite (NOT Next.js). Tests: pytest on in-memory SQLite (StaticPool, engine per test), strict TDD, **NO mocks of session or repository**, domain tested without DB. Intervals `[inicio, fin)`, aware UTC datetimes, single injectable `utc_now()`. All data fictitious (RN-PR-01). Alembic only from the infrastructure change (DD-15), not in the first change.
> Rules tagged **[N/A]** below must NOT be applied. Rules tagged **[ADAPT]** apply only in the adapted form shown.

## User Skills

| Trigger | Skill | Path |
|---------|-------|------|
| Building new FastAPI apps / backend API projects | fastapi-templates | ~/.claude/skills/fastapi-templates/SKILL.md |
| Writing Python tests, pytest suites, fixtures, TDD | python-testing-patterns | ~/.claude/skills/python-testing-patterns/SKILL.md |
| Validation logic, exception hierarchies, robust APIs | python-error-handling | ~/.claude/skills/python-error-handling/SKILL.md |
| Layering services, refactoring God classes, SRP/KISS/composition | python-design-patterns | ~/.claude/skills/python-design-patterns/SKILL.md |
| Implementing auth, JWT, RBAC, securing APIs | auth-implementation-patterns | ~/.claude/skills/auth-implementation-patterns/SKILL.md |
| Schema changes, migrations, rollback, zero-downtime | database-migration | ~/.claude/skills/database-migration/SKILL.md |
| Before writing/changing anything in Postgres (schema, indexes, queries, locking) | supabase-postgres-best-practices | ~/.claude/skills/supabase-postgres-best-practices/SKILL.md |
| Writing/reviewing React components, data fetching, bundle size | vercel-react-best-practices | ~/.claude/skills/vercel-react-best-practices/SKILL.md |
| Creating Dockerfiles (API and frontend images) | multi-stage-dockerfile | ~/.claude/skills/multi-stage-dockerfile/SKILL.md |
| Foundation flow (/active-orchestrator:*) | active-orchestrator | ~/.claude/skills/active-orchestrator/SKILL.md |
| Generate AGENTS.md / CLAUDE.md | agent-instruction | ~/.claude/skills/agent-instruction/SKILL.md |
| Create/generate knowledge base | kb-creator | ~/.claude/skills/kb-creator/SKILL.md |
| Generate CHANGES.md roadmap | roadmap-generator | ~/.claude/skills/roadmap-generator/SKILL.md |
| Discovery/research phase before the KB | discovery-research | ~/.claude/skills/discovery-research/SKILL.md |
| Research a competitor from a URL | web-scraper | ~/.claude/skills/web-scraper/SKILL.md |
| Find/install skills | find-skill | ~/.claude/skills/find-skill/SKILL.md |
| Create/modify/evaluate skills | skill-creator | ~/.claude/skills/skill-creator/SKILL.md |
| OpenSpec: implement tasks of a change | openspec-apply-change | .claude/skills/openspec-apply-change/SKILL.md |
| OpenSpec: archive a completed change | openspec-archive-change | .claude/skills/openspec-archive-change/SKILL.md |
| OpenSpec: explore mode (thinking partner) | openspec-explore | .claude/skills/openspec-explore/SKILL.md |
| OpenSpec: propose a change with all artifacts | openspec-propose | .claude/skills/openspec-propose/SKILL.md |
| OpenSpec: sync delta specs to main specs | openspec-sync-specs | .claude/skills/openspec-sync-specs/SKILL.md |
| OpenSpec: revise artifacts of an existing change | openspec-update-change | .claude/skills/openspec-update-change/SKILL.md |
| Revisar spec y tasks de un change contra la KB antes del apply (propia del proyecto, versionada) | revisor-de-escenarios | .claude/skills/revisor-de-escenarios/SKILL.md |

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`. Always include the PRECEDENCE note above when injecting any block.

### fastapi-templates
- Layering (keep): `api/` (routers + `dependencies.py`) -> `services/` (business logic) -> `repositories/` (data access); `models/` ORM, `schemas/` Pydantic, `core/` config+security+database, `main.py` entry. Routers never touch the ORM directly; never return ORM models (use response schemas).
- Use FastAPI `Depends` for DB session, auth and config injection; override dependencies in tests (`app.dependency_overrides[get_db]`).
- **[N/A] Async DB**: skill's `create_async_engine`, `AsyncSession`, `async def` repositories/services, `aiosqlite`, `pytest-asyncio`, `AsyncClient`, `event_loop` fixture. Project = sync `Session`, `create_engine`, plain `def` repos/services, `fastapi.testclient.TestClient`. Do NOT add aiosqlite or pytest-asyncio.
- **[ADAPT]** `get_db`: sync generator yielding a `Session` (`with SessionLocal() as session: yield session`); route handlers that do sync DB work are plain `def` (FastAPI runs them in a threadpool).
- **[ADAPT]** Test client: sync `TestClient(app)`; SQLite URL `sqlite+pysqlite:///:memory:` with `StaticPool`, engine created per test.
- Error handling: map domain exceptions to HTTP via exception handlers (409 conflict with RN codes, 422 for missing/inactive resource in body per RN-GL-04, 404 for resource in URL).
- First change exposes `POST /turnos` WITHOUT auth (known limit, DD-14); do not add JWT there.

### python-testing-patterns
- AAA structure; names `test_<unit>_<scenario>_<expected>`; tests independent, no shared state; `conftest.py` for shared fixtures; markers for optional suites (e.g. `postgres` marker excluded from default run; E11 concurrency test lives there).
- Use `parametrize` for triangulation (>=2 cases per behavior); test error paths with `pytest.raises`.
- DB tests: real SQLAlchemy `Session` on in-memory SQLite, fresh engine per test (the skill's `db_session` fixture shape is fine, but use SQLAlchemy 2.x style: `DeclarativeBase`/`Mapped`, `select()`, not `declarative_base`/`session.query`; add `StaticPool`).
- **[N/A] Mocking the session or repository** (`Mock`/`MagicMock`/`patch` of DB, `side_effect` doubles for repos). Use real session + real repository. Mocks only acceptable for true external HTTP services (WhatsApp, Mercado Pago), never for DB layers.
- **[N/A]** `freezegun`/`freeze_time`: project injects a single `utc_now()` clock; pass a fixed clock in tests instead.
- **[N/A]** async tests (`pytest.mark.asyncio`, async fixtures): project is synchronous.
- Domain (`app/domain`) is tested with plain pytest and NO database; a test must fail if `app/domain` imports a forbidden module.
- Include a timezone round-trip test with SQLite (write aware UTC, read aware UTC).
- `pytest-cov` / `--cov-fail-under` are optional; the project mandates no coverage threshold.

### python-error-handling
- Fail fast: validate at the boundary; convert external data to domain types early (enums, value objects); Pydantic for request schemas.
- Chain exceptions (`raise ... from e`); never raise bare `Exception`; include context (ids, values) in messages.
- **[ADAPT]** Instead of plain `ValueError` for business rules, use a domain exception hierarchy carrying the RN code (e.g. RN-AG-05, RN-AG-08, RN-GL-04); if several rules fail at once, report ALL codes together. Map to HTTP in the API layer only (domain stays free of HTTP/FastAPI).
- Report all validation errors at once when possible (matches the multi-code rule above).
- Partial-failure/batch patterns apply only to future batch jobs (e.g. reminders), not the first change.
- Test every error path (exception type + RN code).

### python-design-patterns
- KISS; SRP ("reason to change" test); composition over inheritance; rule of three before abstracting; small focused functions; explicit over clever.
- Dependency direction API -> Service -> Repository -> Models; services must not import from API layer; never leak ORM models through the API (response schemas).
- Constructor injection for dependencies; keep I/O out of business rules (agenda rules are pure functions over intervals).
- **[ADAPT]** Skill examples are `async def`; write them sync. Skill's "test with fakes" advice: for the DB layer use a real in-memory SQLite session, not fake repositories or session doubles.
- Constructor with 7+ params = too many responsibilities: split the class first.

### auth-implementation-patterns
- Hash passwords with bcrypt (project: min 10 chars, max 72 bytes, RN-AU-07); short-lived access token (project: 15 min) + refresh (7 days), HS256 with `JWT_SECRET` from env; never commit secrets/.env.
- Validate server-side always; ownership/RBAC checks in dependencies (`Depends`); generic 401 on bad credentials (RN-AU-04); rate-limit auth endpoints; log security events.
- Project specifics override skill: refresh tokens are NOT stored/revoked one by one; invalidate in bulk via `token_version` claim; verify `activo` on each request and refresh. Patients have no account (token-based access to their appointment).
- **[N/A]** Skill code examples are Node/Express/TypeScript (`jsonwebtoken`, `passport`, `express-session`, zod): translate ideas to Python only after the design fixes library versions. Session-cookie/CSRF, OAuth2/social login/SSO and MFA patterns are out of scope for v1.
- **[ADAPT]** "JWT in localStorage is vulnerable to XSS; use httpOnly cookies": token storage in the React panel is not decided in the KB; surface it as a design decision, do not assume.
- First change (`POST /turnos`) has NO auth; JWT arrives in the users-and-access change (US-092).

### database-migration
- Keep: one reversible migration per schema change (up + down); add columns nullable or with default; multi-step expand -> migrate data -> contract for renames/type changes; verify before dropping; wrap data transforms in transactions where the DB allows.
- **[N/A]** All skill examples are Sequelize/TypeORM/Prisma (JavaScript) and cross-DB (PostgreSQL->MySQL); no Alembic content. Translate concepts to Alembic only (`alembic revision --autogenerate`, `upgrade head`/`downgrade -1`), reviewing autogenerated output by hand.
- **[ADAPT]** Alembic is NOT used in the first change (tests use `create_all`); it starts in the infrastructure-with-PostgreSQL change (orden 2, DD-15). Columns the first change omits are added later via migrations (see 04_modelo_de_datos.md).
- The skill's "checkpoint backup table" pattern (DROP TABLE + CREATE TABLE AS SELECT) is destructive; do not use it. Never run migrations against real data; data is fictitious.

### supabase-postgres-best-practices
- Keep (generic PostgreSQL): index FK columns; composite indexes (equality columns first, then range); partial indexes for filtered subsets (e.g. only active states); proper types (`timestamptz`, not `timestamp`); lowercase snake_case identifiers; add constraints safely in migrations (NOT VALID then VALIDATE).
- Keep: short transactions; consistent lock ordering to avoid deadlocks; `FOR UPDATE SKIP LOCKED`/advisory locks only where justified (E11 concurrency, optional PostgreSQL profile); keyset pagination over OFFSET; batch inserts; EXPLAIN ANALYZE to diagnose; connection pooling and idle timeouts.
- The default test suite runs on SQLite: do not make the default path depend on PostgreSQL-only features; PostgreSQL-specific guarantees are verified in the optional `postgres` profile (E11).
- **[N/A] Supabase-specific**: RLS policies and `auth.uid()`-style rules (`security-rls-basics`, `security-rls-performance`), Supabase CLI/dashboard/Supavisor pooler specifics, pg_cron/pgmq/pgvector unless the KB adds them. Project authorization is application-level (JWT + roles), not RLS.
- Least-privilege DB roles (`security-privileges`) is generic and optional for the infra change.

### vercel-react-best-practices
- Applies to the React + TypeScript + Vite frontend (frontend phase, not the first change). Keep client-side rules: eliminate waterfalls (`Promise.all` for independent fetches), avoid barrel-file imports, dynamic `import()`/`React.lazy` for heavy components, defer third-party scripts.
- Re-render rules: derive state during render (not in effects), functional `setState`, lazy `useState` init, primitive effect deps, no components defined inside components, `startTransition` for non-urgent updates, hoist static JSX/default props, ternary over `&&` for conditionals.
- Client data fetching: dedupe requests (SWR or TanStack Query), passive scroll listeners, version/minimize localStorage data.
- JS perf: `Map`/`Set` lookups, early returns, combine iterations, hoist RegExp, `toSorted()`.
- **[N/A] Next.js/RSC-only**: all `server-*` rules (React.cache, `after()`, RSC serialization, server actions auth), `next/dynamic`, Suspense streaming for server components, `rendering-hydration-*`, App Router assumptions. A Vite SPA has no SSR.

### multi-stage-dockerfile
- Named stages (`AS builder`/`AS runtime`), order deps -> build -> test -> runtime; copy only artifacts into runtime.
- Pin exact base tags (e.g. `python:3.11-slim`, never bare/`latest`); minimal official images; versions come from the design pins.
- Copy dependency manifests first, then source (layer cache); use `.dockerignore`; never bake secrets or `.env` into images.
- Run as non-root (`USER`); add `HEALTHCHECK`; set `PYTHONDONTWRITEBYTECODE`/`NODE_ENV=production` as appropriate.
- Docker/Compose belongs to the infra change and optional PostgreSQL profile; the default test suite must run without Docker.

### active-orchestrator
- Foundation flow owner: openspec init -> [discovery-research] -> kb-creator -> roadmap-generator -> find-skill -> skill-registry -> agent-instruction. Owns `.active-orchestrator-state.json` and the `step` field only; idempotent.

### agent-instruction
- Generates the project AGENTS.md/CLAUDE.md from KB + roadmap; confirms hard rules interactively; emits only project-specific content.

### kb-creator
- Produces the canonical `knowledge-base/*.md` files; the KB is the source of truth for project decisions.

### roadmap-generator
- Produces `CHANGES.md` (change index, dependency tree, critical path, governance level, "Leer antes" pointers).

### discovery-research
- Runs discovery Q&A and competitor research before the KB; writes the `discovery` state section and `docs/discovery/`.

### web-scraper
- Competitor notes from a URL via WebFetch/WebSearch into fixed-schema markdown; no mass crawling, no JS-heavy/anti-bot sites.

### find-skill
- Discovers and installs agent skills; installing requires user consent; records `skills` in the state file.

### skill-creator
- Create/improve/eval skills; not used for project coding.

### openspec-apply-change / openspec-archive-change / openspec-explore / openspec-propose / openspec-sync-specs / openspec-update-change
- OpenSpec workflow skills (project-level). The `openspec` CLI owns artifact state; artifacts in Spanish; follow `openspec/config.yaml` rules (strict TDD, no session/repo mocks, tasks ordered RED/GREEN/TRIANGULATE/REFACTOR per scenario, final clean-clone verification task).

### revisor-de-escenarios
- Skill PROPIA del proyecto (creada con skill-creator), versionada en `.claude/skills/revisor-de-escenarios/` junto a las `openspec-*`. Usarla despues de `/opsx:propose` o `/opsx:update` y antes de aprobar el plan o de arrancar `/opsx:apply`, o cuando pregunten si un change "esta listo para implementar". Entrada: nombre del change (lee su spec.md y tasks.md, la KB, CHANGES.md y `openspec/config.yaml`).
- Controla: cada CA de CHANGES.md con escenario; al menos un escenario feliz, uno de error de negocio y uno de borde; todo error de negocio con un RN-XX-NN que exista en `05`; estados HTTP segun RN-GL-02 y RN-GL-04 (422 de entrada juntos, 404 para el recurso de la URL, reglas de negocio de a una, 401/403 antes de la validacion); cada escenario verificable y con una tarea que lo pruebe.
- Detecta reglas inventadas sin una D o una RN que las respalde y cambios fuera del alcance del change (regla dura 12); la KB manda.
- **Solo informa, NO edita** spec, tasks ni design: cada hallazgo cita su fuente (archivo y seccion, RN, D o regla de config.yaml) y se clasifica como bloqueante, a corregir o sugerencia. Las correcciones las decide el autor.
- Incluye `scripts/inventario.py` (inventario de escenarios, codigos RN y tareas); no instalar nada ni usar mocks.

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| openspec config | openspec/config.yaml | Project context + per-artifact rules (OVERRIDES skills) |
| Knowledge base index | knowledge-base/README.md | Index of the KB |
| Vision y objetivos | knowledge-base/01_vision_y_objetivos.md | Referenced by KB README |
| Descripcion general | knowledge-base/02_descripcion_general.md | |
| Actores y roles | knowledge-base/03_actores_y_roles.md | |
| Modelo de datos | knowledge-base/04_modelo_de_datos.md | |
| Reglas de negocio | knowledge-base/05_reglas_de_negocio.md | RN-XX-NN codes |
| Funcionalidades | knowledge-base/06_funcionalidades.md | US-NNN and E# scenarios |
| Flujos principales | knowledge-base/07_flujos_principales.md | |
| Arquitectura propuesta | knowledge-base/08_arquitectura_propuesta.md | Sync SQLAlchemy, JWT, env vars, Alembic timing |
| Decisiones y supuestos | knowledge-base/09_decisiones_y_supuestos.md | DD-NN decisions |
| Preguntas abiertas | knowledge-base/10_preguntas_abiertas.md | |
| Integraciones WhatsApp y MP | knowledge-base/11_integraciones_whatsapp_y_mercadopago.md | |
| Contexto de mercado | knowledge-base/12_contexto_de_mercado.md | |
| Roadmap | CHANGES.md | 48 changes (C-01..C-48) |
| Shared state | .active-orchestrator-state.json | Foundation flow state |

El proyecto ya tiene `CLAUDE.md` y `AGENTS.md` (idénticos), generados por agent-instruction; las skills propias del proyecto viven en `.claude/skills/` (las `openspec-*` y `revisor-de-escenarios`).

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted — no need to read index files to discover more.
