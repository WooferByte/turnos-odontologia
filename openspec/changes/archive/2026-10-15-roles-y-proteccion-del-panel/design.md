# Design: roles-y-proteccion-del-panel

Fecha del design: **2026-10-15**. Gobernanza **CRÍTICO** (autenticación y autorización): nada de esto se implementa hasta que el autor apruebe este documento, los specs y `tasks.md`.

**Respuesta del autor (2026-10-15): las trece preguntas abiertas (Q1 a Q13) se cierran con la recomendación del agente.** Quedan como decisiones del autor D204 a D216, una por pregunta y en orden, registradas en `knowledge-base/10_preguntas_abiertas.md` (sección «Decisiones del autor (2026-10-15, roles-y-proteccion-del-panel)»). Las demás decisiones marcadas «Propuesta» siguen así hasta que el autor apruebe el plan completo. Las correcciones de la KB y de los specs vigentes que estas decisiones piden quedan en «Notas para el archive».

Las decisiones se numeran **R1 a R22** («R» de roles) para no confundirlas con las D1..D216 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores (D de C-01, I de C-02, H de C-03, P de C-04, S de C-05, J de C-06). Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design, a confirmar) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»).

## Context

Motivación y alcance: ver `proposal.md`. Requisitos: `specs/proteccion-del-panel/spec.md` y los deltas de `specs/historial-de-turnos/spec.md` y `specs/persistencia-postgresql/spec.md`.

**Lo que dejaron C-01 a C-06** (leído del código, no supuesto):

- `app/main.py`: `crear_app(engine, sesion=None)` (sin `sesion` usa un secreto efímero, D196; la usan todos los tests de API con `crear_app(engine)`), `crear_app_demo()` y `crear_app_desde_entorno(entorno)`. En `app.state` quedan `firmador`, `hasher` y `vigencias`; `api/deps.py` los entrega con `get_firmador`, `get_hasher`, `get_vigencias`, más `get_uow` y `get_reloj`.
- `domain/acceso/sesion.py`: `exigir_token_valido(claims, tipo_esperado, usuario | None, ahora)` ya recibe el tipo esperado como parámetro para que C-07 lo use con `TipoDeToken.ACCESS` (J5, J20). `FirmadorDeTokens.leer` levanta `TokenIlegible`. `RepositorioUsuarios` tiene `por_email`, `obtener` y `agregar`.
- `api/errores.py`: tabla `_CLASES_DE_ERROR`; los `401` llevan `WWW-Authenticate: Bearer` y texto fijo (`_ERRORES_DE_TEXTO_FIJO`). `SesionInvalida` es `401`, `RN-AU-03`, `/errores/sesion-invalida`.
- Routers: `turnos.py` (`POST /turnos`, `GET /turnos/{turno_id}/historial`), `prestaciones.py` y `sillones.py` (`GET`, `POST`, `PATCH /{id}`), `auth.py`. Ninguno pide token. **No hay** esquema de seguridad en OpenAPI (J12).
- `application/crear_turno.py`: `crear_turno(comando, uow, reloj=utc_now, actor=ACTOR_PANEL_SIN_AUTENTICAR)`; el router no pasa actor. `domain/turnos/eventos.py` define `ActorTipo.USUARIO` y la constante `ACTOR_PANEL_SIN_AUTENTICAR` (D159).
- `infrastructure/db/modelos.py`: `ProfesionalModelo` sin `usuario_id` ni `matricula`; `TurnoModelo` sin `creado_por`; `UsuarioModelo` (tabla `usuario`). Migraciones `0001` a `0006`.
- `seed_demo.py`: `cargar_demo`, `cargar_demo_si_falta`, `cargar_usuario_demo(_si_falta)` (usuario id 1, sin roles, D202), `ajustar_secuencias` (incluye `usuario`). `cargar_seed.py` siembra el consultorio y, aparte, el usuario.
- **Tests de API existentes**: cinco archivos (`test_post_turnos.py`, `test_historial.py`, `test_prestaciones.py`, `test_sillones.py`, `test_sillones_y_turnos.py`) arman su cliente con un *fixture* `cliente(engine)` que hace `TestClient(crear_app(engine))`: unos **55 tests** llaman sin token a rutas que este change protege. `test_demo.py` (6 tests) llama a `POST /turnos` de la demo sin token. En `tests/integration/` hay **32 llamadas** a `crear_turno(...)` sin actor. `test_historial.py` (API e integración) y `test_eventos.py` afirman `actor_id` vacío.
- **FastAPI 0.115.14** (`fastapi/security/http.py`, leído del paquete instalado): `HTTPBearer(auto_error=True)` responde **`403` «Not authenticated»** cuando falta la cabecera, no `401`. Y en `fastapi/routing.py`, un cuerpo con JSON roto se rechaza con `422` **antes** de resolver las dependencias (línea del `json_invalid` antes de `solve_dependencies`); dentro de `solve_dependencies`, las sub-dependencias se resuelven **antes** que los parámetros de ruta y el cuerpo.

## Goals / Non-Goals

**Goals:**

- Que ninguna ruta del panel se ejecute sin un access token válido, y que la lista de rutas públicas sea **cerrada**: una ruta nueva que olvide la protección hace fallar un test.
- Que la decisión «este rol puede esto» sea **una función pura** sobre una matriz de datos, testeada sin HTTP ni base, y que la matriz se lea igual que la de `03`.
- Que los roles, `activo` y `token_version` salgan de la base **en cada petición** (RN-AU-02, RN-AU-04, D102).
- Que la protección no revele nada a quien no tiene sesión: ni si un recurso existe ni si su petición era válida.
- Cerrar la trazabilidad pendiente: quién creó cada turno (`creado_por` y `actor_id`).

**Non-Goals:**

- Permisos sobre «lo propio» (`U propio`, paciente por token) y comparación de consultorio entre usuario y recurso (un solo consultorio, D173).
- Un endpoint para que el panel conozca sus roles (`GET /auth/yo`): lo decide C-08 si lo necesita.
- Escribir roles fuera del seed (C-09) o incrementar `token_version` (C-09, C-10).
- Límite de peticiones y registro de eventos de seguridad (D195).
- Cachear roles o usuarios entre peticiones (contradiría D102).

## Decisions

### R1. Una capability nueva, `proteccion-del-panel`, más dos deltas — Decisión del autor (D204; aplica D158 a INF-1)

Los requisitos de US-091 y US-092 van en `proteccion-del-panel`, el nombre que C-06 dejó previsto (J1, J20). Es transversal: dice quién puede llamar a cada ruta, y por eso las capabilities de cada ruta (`creacion-de-turnos`, `gestion-de-prestaciones`, `gestion-de-sillones`) **no** reciben delta: siguen describiendo qué hace la ruta para quien tiene permiso, y la convención de la capability nueva lo dice. Deltas obligados: `historial-de-turnos` (E9 cambia `actor_id` vacío por el id del usuario; no hay forma de cumplir D159 sin tocar ese escenario) y `persistencia-postgresql` (lista de INF-1 y borde de `0007`, como fijó D158). `sesion-del-panel` no cambia: el login y el refresh siguen iguales.

**Alternativas descartadas:** (a) sumar la validación del access token a `sesion-del-panel` y los roles a una capability aparte (dos capabilities nuevas o modificadas para lo mismo); (b) agregar escenarios `401`/`403` a cada capability de ruta (cuatro deltas y la matriz repartida). Elegida la capability única (D204).

### R2. Sin dependencias nuevas — Propuesta (aplica D116, D133, D137)

`fastapi.security.HTTPBearer` y `HTTPAuthorizationCredentials` vienen con FastAPI 0.115.14; los JWT y bcrypt ya están (`PyJWT==2.15.1`, `bcrypt==5.0.0`, J2). `backend/pyproject.toml` no cambia y la política D133 no aplica porque no se elige ninguna versión. Se comprueba al cerrar con `git diff` sobre `pyproject.toml`.

### R3. Roles y permisos en el dominio — Propuesta

`backend/app/domain/acceso/roles.py` (solo biblioteca estándar):

- `Rol` (`StrEnum`: `odontologo`, `recepcionista`, `dueno`; RN-AU-05).
- `Permiso` (`StrEnum`), uno por acción que hoy existe: `turnos.crear`, `historial.leer`, `prestaciones.leer`, `prestaciones.editar`, `sillones.leer`, `sillones.editar`.
- `MATRIZ: Mapping[Permiso, frozenset[Rol]]` (R4) y `puede(roles: frozenset[Rol], permiso) -> bool` = intersección no vacía (unión de roles, RN-AU-02).
- `exigir_permiso(roles, permiso)`: levanta `PermisoInsuficiente` (R11) si `puede` es falso.

**Por qué permisos y no roles por ruta:** la matriz de `03` es por recurso y acción; con `Permiso` hay **una sola tabla** que se compara renglón a renglón con `03` y se testea completa sin HTTP (tabla parametrizada). Los changes siguientes agregan un `Permiso` y su renglón. **Alternativa descartada:** listar roles en cada ruta (`requiere_roles(ODONTOLOGO, RECEPCIONISTA)`): la matriz queda repartida en los routers y no hay un lugar donde revisarla.

### R4. La matriz de las rutas existentes — Decisión del autor (`03`, US-092 CA-2) + Decisión del autor (D205)

| Permiso | Ruta | `odontologo` | `recepcionista` | `dueno` | Fuente |
|---|---|---|---|---|---|
| `turnos.crear` | `POST /turnos` | sí | sí | no | `03` fila Turnos (CRUD / CRU / R); US-092 CA-2 lo dice literal |
| `historial.leer` | `GET /turnos/{id}/historial` | sí | sí | sí | `03` fila «Historial de cambios de turno» (R / R / R) |
| `prestaciones.leer` | `GET /prestaciones` | sí | sí | sí | `03` fila Prestaciones (CRUD / R / R) |
| `prestaciones.editar` | `POST /prestaciones`, `PATCH /prestaciones/{id}` | sí | no | no | `03` (solo el odontólogo escribe) |
| `sillones.leer` | `GET /sillones` | sí | sí | sí | `03` fila Sillones (CRUD / R / R) |
| `sillones.editar` | `POST /sillones`, `PATCH /sillones/{id}` | sí | no | no | `03` |

**D205:** `02` («API REST (resumen)») pone «Odontólogo» como acceso de Prestaciones y Sillones, sin distinguir lectura. Se sigue `03`, que es la matriz que RN-AU-05 nombra como fuente; `02` se corrige al archivar (ver «Notas para el archive»).

### R5. Tabla `usuario_rol` y columnas nuevas — Decisión del autor (`04`, `CHANGES.md`) + Decisión del autor (D213, D215)

| Tabla / columna | Tipo | Nota |
|---|---|---|
| `usuario_rol.usuario_id` | entero, NN, FK → `usuario` (`RESTRICT`) | Parte de `pk_usuario_rol` |
| `usuario_rol.rol` | texto, NN | Parte de `pk_usuario_rol`. **D213:** `CHECK` `ck_usuario_rol_rol_valido` con `rol IN ('odontologo', 'recepcionista', 'dueno')` |
| `profesional.usuario_id` | entero, nulo, FK → `usuario` (`RESTRICT`), `UNIQUE` (`uq_profesional_usuario_id`) | `04`: «`UNIQUE` si no es nulo»: un `UNIQUE` simple admite varios nulos en PostgreSQL y en SQLite |
| `profesional.matricula` | texto, nulo | **D215:** se crea porque `CHANGES.md` la pone en C-07; nadie la escribe ni la lee todavía (ni API ni seed) |
| `turno.creado_por` | entero, nulo, FK → `usuario` (`RESTRICT`) | Nula para los turnos anteriores (`04` †, propuesta 8) |

La PK compuesta ya impide el rol repetido. **El `CHECK` (D213):** D164 descartó un `CHECK` sobre `evento_turno.tipo` porque esa lista crece con cada change; la de roles está **cerrada por RN-AU-05** y es de seguridad: una fila con un rol mal escrito no daría permisos, pero ensuciaría la gestión de C-09 sin que nada lo avise. Se crea el `CHECK` (la aplicación igual valida con el enum `Rol`). **Alternativa descartada:** sin `CHECK`, como `evento_turno`.

Sin índice sobre `turno.creado_por` (nadie busca turnos por creador todavía y un usuario no se borra: el `RESTRICT` no se dispara; lo agrega el change que lo consulte, p. ej. reportes) ni sobre `usuario_rol.usuario_id` (es la primera columna de la PK). Sin `server_default` (como en el resto del modelo). **No hay tabla `Rol`** (`04` †, propuesta 3).

### R6. Migración `0007_roles_y_creador` — Decisión del autor (DD-15) + Propuesta

Autogenerada y revisada a mano contra `modelos.py`, como `0005` y `0006`: `create_table('usuario_rol', ...)` con `pk_usuario_rol`, `fk_usuario_rol_usuario_id` y el `CHECK` (D213); `add_column` de las tres columnas nulas con sus FK y el `UNIQUE` con nombres por convención. **Sin datos**: los roles y el vínculo del seed los pone `cargar_seed` (R16), no la migración (una migración no sabe cuál es el usuario «del seed» en una base real). `downgrade`: quita el `UNIQUE`, las FK y las columnas, y la tabla; no toca nada más. **Límite (al README):** deshacer `0007` pierde los roles guardados y el creador de los turnos (son datos de las columnas que se quitan); volver a aplicarla y sembrar restaura los del seed, no los demás. Sobre una tabla `turno` con datos, `ADD COLUMN` nula no reescribe la tabla en PostgreSQL 17.

### R7. Puertos y repositorio — Propuesta

- `RepositorioUsuarios` suma `roles_de(usuario_id) -> frozenset[Rol]` y `asignar_rol(usuario_id, rol)` / `quitar_rol(usuario_id, rol)` (estos dos solo para el seed y los tests; C-09 los usa por la API). Un rol desconocido leído de la base levanta un error de programación (no se ignora en silencio). Un `asignar_rol` repetido o inválido sale como `RolInvalidoEnLaBase` (excepción de puerto, como `EmailRepetidoEnLaBase`).
- `DatosUsuario` **no** suma los roles: se leen aparte para que nadie los tome de un objeto viejo (D102).
- `Turno` (dominio) suma `creado_por: int | None = None`; `RepositorioAgenda.agregar` lo guarda.

### R8. Identificar al usuario de la petición — Propuesta (aplica RN-AU-01, RN-AU-03, RN-AU-04)

`application/acceso.py`, `identificar_usuario(token: str | None, uow, firmador, reloj) -> UsuarioDelPanel`, con `UsuarioDelPanel(id: int, roles: frozenset[Rol])` (dataclass congelada en `domain/acceso/roles.py`):

1. Sin token → `SesionInvalida`.
2. `claims = firmador.leer(token)`; `TokenIlegible` → `SesionInvalida`.
3. En un `with uow:`: `usuario = uow.usuarios.obtener(claims.usuario_id)` y, si existe, `roles = uow.usuarios.roles_de(usuario.id)`.
4. `exigir_token_valido(claims, TipoDeToken.ACCESS, usuario, reloj())` (la misma función del refresh, con el tipo `access`: tipo, vigencia semiabierta, existe, `activo`, `token_version`).
5. Devuelve `UsuarioDelPanel(usuario.id, roles)`.

`autorizar(usuario: UsuarioDelPanel, permiso) -> UsuarioDelPanel` llama a `exigir_permiso` y lo devuelve. La lectura es una transacción propia, separada de la de la operación (R21).

### R9. Dependencias de FastAPI y esquema Bearer en `/docs` — Propuesta + A verificar (V1, V2)

En `api/seguridad.py` (nuevo; `api/deps.py` queda con lo de C-01 a C-06):

- `esquema_bearer = HTTPBearer(auto_error=False, scheme_name="AccessToken", description=...)`. **`auto_error=False` es obligatorio:** con `True`, FastAPI 0.115.14 responde `403 Not authenticated` sin token (Context), que contradice RN-AU-05 («sin token válido, `401`») y no lleva el cuerpo `problem+json`. Con `False` devuelve `None` y el caso de uso levanta `SesionInvalida`. Un esquema distinto de `Bearer` (por ejemplo `Basic`) también da `None` con `auto_error=False` (V1).
- `usuario_actual(credenciales = Depends(esquema_bearer), uow, firmador, reloj) -> UsuarioDelPanel` = `identificar_usuario(credenciales.credentials if credenciales else None, ...)`.
- `requiere(permiso) -> Callable` devuelve una dependencia que recibe `usuario_actual` y llama a `autorizar`. Cada ruta declara la suya como parámetro: `usuario: Annotated[UsuarioDelPanel, Depends(requiere(Permiso.TURNOS_CREAR))]`; las que no necesitan el usuario lo reciben igual (o con `dependencies=[...]`), pero **todas** pasan por `requiere`.
- **Por qué `HTTPBearer` y no `OAuth2PasswordBearer`:** el flujo «password» de `/docs` manda un formulario a `tokenUrl`, y `POST /auth/login` recibe JSON (J12): el botón no funcionaría. Con `HTTPBearer` el autor pega el access token en «Authorize» y Swagger lo agrega a cada petición.

### R10. Respuesta `401` en las rutas protegidas — Decisión del autor (formato de D200) + Decisión del autor (D206)

**Decidido (D206):** el mismo `401` de sesión inválida que ya usa `POST /auth/refresh` (`SesionInvalida`: `RN-AU-03`, `/errores/sesion-invalida`, «Sesión inválida», texto fijo, `WWW-Authenticate: Bearer`) para **todas** las causas: sin cabecera, otro esquema, token ilegible, refresh usado como access, vencido, usuario inexistente o inactivo, `token_version` vieja. **Motivo:** D200 eligió un `401` idéntico por endpoint; para el panel (C-08) toda causa significa lo mismo (volver al inicio de sesión) y distinguirlas le da información a quien tiene un token robado. **Alternativa descartada:** distinguir la falta de token (`RN-AU-01`) o el usuario inactivo (`RN-AU-04`) con su propio código.

### R11. Respuesta `403` — Decisión del autor (D207)

Error nuevo `PermisoInsuficiente` en `domain/errors.py`, código `RN-AU-05`, fila en `_CLASES_DE_ERROR`: `403`, `type` `/errores/permiso-insuficiente`, `title` «Permiso insuficiente», `detail` fijo «Tu usuario no tiene permiso para esta operación.», sumado a `_ERRORES_DE_TEXTO_FIJO`. **Sin** `WWW-Authenticate` (RFC 6750 §3.1 lo sugiere con `error="insufficient_scope"`, pero el proyecto no usa scopes) y **sin** listar los roles que harían falta. **Motivo:** el usuario autenticado ya conoce sus roles; listar los necesarios describe la matriz a quien no la tiene. **Alternativa descartada:** un campo con los roles requeridos (útil para el panel al mostrar el error).

### R12. Clase y orden de evaluación (RN-GL-02) — Decisión del autor (D208) + A verificar (V2)

Orden para toda ruta protegida:

0. **Cuerpo con JSON roto** → `422` sin código. FastAPI 0.115.14 lo rechaza antes de llamar a cualquier dependencia (Context); no se puede evitar sin reescribir el manejo del cuerpo. Es el único caso en que una petición sin token recibe algo distinto de `401`, y no revela nada del sistema (V2).
1. **Autenticación** → `401` (R10).
2. **Autorización** → `403` (R11).
3. **Validación de entrada** → `422`, toda junta (ruta y cuerpo; D135).
4. **Recurso de la URL inexistente** → `404` `RN-GL-04` (D166).
5. **Reglas de negocio**, de a una (la primera que falla).

**D208:** RN-GL-02 define dos clases, validación de entrada y regla de negocio, y dice que las reglas de negocio se evalúan **solo con la entrada válida**. Autenticación y autorización no encajan: si fueran «regla de negocio» irían después de la validación, y un usuario sin sesión vería un `422` con la lista de sus referencias inválidas, o un `404` que revela qué turnos existen. **Decidido:** tratarlas como una **tercera clase, el control de acceso**, que se evalúa **antes** que las otras dos, de a una (`401` antes que `403`), y precisar así RN-GL-02 en `05` al archivar (ver «Notas para el archive»). **Alternativa descartada:** dejarlas como regla de negocio después de la validación (contra el spec de C-07: «sin sesión no se revela si el recurso existe»).

### R13. Actor del historial y `creado_por` — Decisión del autor (D159) + Decisión del autor (D209, D210)

- `POST /turnos` pasa a `crear_turno(comando, uow, reloj, actor=Actor(ActorTipo.USUARIO, str(usuario.id)), creado_por=usuario.id)`; el turno guarda `creado_por` y el evento `creado`, `actor_id` = `"1"`, `"2"`… (D159: «el evento lleva el id del usuario del token»). `actor_id` es texto desde C-03 (`04`: «id del usuario o del token»): **D209:** se escribe el id **como texto decimal**, sin prefijo (`"1"`, no `"usuario:1"`), porque `actor_tipo` ya dice de qué es el id.
- **D209:** `TurnoSalida` **no** suma `creado_por`: ningún criterio lo pide en la respuesta, el historial ya muestra el actor y agregarlo cambiaría el contrato de `POST /turnos` sin necesidad. **Alternativa descartada:** exponerlo (cambio aditivo del contrato).
- **D210: el actor pasa a ser obligatorio** en `crear_turno` (se quitan el valor por defecto y la constante `ACTOR_PANEL_SIN_AUTENTICAR`) y `creado_por` también. **Motivo:** en un dominio CRÍTICO, un parámetro con valor por defecto «anónimo» es un camino para crear turnos sin autor que ningún test detecta. **Costo:** las 32 llamadas a `crear_turno` de `tests/integration/` pasan un actor de prueba (`ACTOR_DE_PRUEBA` en `tests/factories.py`, con un usuario de la factory). **Alternativa descartada:** conservar el valor por defecto y confiar en que la API siempre lo pase (no toca esos tests).
- `evento_creado(turno, actor)` no cambia. Los eventos anteriores a C-07 quedan con `actor_id` vacío (D159, límite del README).

### R14. Rutas públicas y guard de protección — Decisión del autor (`03`, RN-AU-01) + Decisión del autor (D214)

- Públicas: `POST /auth/login` y `POST /auth/refresh` (no declaran `requiere`).
- **D214:** `/docs`, `/docs/oauth2-redirect`, `/redoc` y `/openapi.json` (rutas que agrega FastAPI) **no** están en la lista de `03`, y RN-AU-01 dice que las rutas públicas «se limitan» a esa lista. **Decidido:** dejarlas públicas: no exponen datos, son el medio de prueba de las fases 1 a 3 (`openspec/config.yaml`) y protegerlas impediría usar «Authorize» (Swagger necesita leer `/openapi.json` antes de tener token). Se documenta como límite conocido: fuera de desarrollo se deberían apagar (`docs_url=None`), lo que queda para cuando haya configuración de producción. **Alternativas descartadas:** protegerlas, o apagarlas en `crear_app_desde_entorno` (Compose) y dejarlas solo en la demo.
- **Guard** (`tests/api/test_proteccion_de_rutas.py`): recorre `app.routes` de `crear_app(engine)` y exige que toda `APIRoute` que no esté en la lista pública tenga `usuario_actual` en su árbol de dependencias (`route.dependant`), y que su operación de OpenAPI declare `security` con `AccessToken` y las respuestas `401` y `403`. Si un change agrega una ruta sin protección, el guard falla.

### R15. OpenAPI — Propuesta

Cada ruta protegida declara `401` («Sin sesión válida (RN-AU-03)») y `403` («Rol insuficiente (RN-AU-05)») con el esquema `Problema`, sumados a sus `responses` actuales, mediante una constante compartida en `api/respuestas.py`. El esquema `AccessToken` (tipo `http`, `bearer`, formato `JWT`) aparece en `components.securitySchemes` porque `HTTPBearer` lo registra solo.

### R16. Seed: roles, vínculo y una recepcionista — Decisión del autor (D46, D202) + Decisión del autor (D212)

- `cargar_roles_demo_si_faltan(sesion) -> bool`: asigna `odontologo` y `dueno` al usuario 1 si le faltan, y vincula el profesional 1 al usuario 1 si `usuario_id` es nulo. Va **aparte** de `cargar_usuario_demo_si_falta`, por el mismo motivo que J11: el volumen del autor ya tiene el usuario (sembrado en C-06) y `cargar_usuario_demo_si_falta` devuelve `False` (spec, tercer escenario del primer requisito). `cargar_demo` sigue sin tocar; `crear_app_demo` y `cargar_seed` llaman a la función nueva. Es idempotente: una segunda corrida no cambia nada.
- **D212:** con un único usuario `odontologo` + `dueno`, todo está permitido y el `403` (US-091 CA-3) **no se puede mostrar en `/docs`** de la demo sin Docker (sin base que editar). **Decidido:** sembrar además **`recepcion@consultorio-demo.test`** (id 2, activo, rol `recepcionista`, misma contraseña de prueba: `CONTRASENA_DEMO` en la demo, `SEED_USUARIO_PASSWORD` en PostgreSQL), con `cargar_recepcionista_demo_si_falta`. Muestra el `403` en `POST /prestaciones` y el `201` en `POST /turnos`. El `403` del dueño en `POST /turnos` y US-091 CA-5 se muestran en Compose quitando el rol `odontologo` con SQL (R20). **Contradice** `04` («Seed data inicial»: «1 `Usuario`»), que se ajusta al archivar. **Alternativa descartada:** un solo usuario y el `403` solo en Compose con SQL.
- `ajustar_secuencias` ya incluye `usuario`; `usuario_rol` no tiene secuencia (PK compuesta).

### R17. Tests existentes de C-01 a C-05 — Decisión del autor (D211)

La protección rompe todos los tests de API de las rutas existentes (unos 55, Context): **no se puede cumplir** la regla de C-03 a C-06 «no se toca ningún test de los changes anteriores». **D211:** cambiar **solo el *fixture* `cliente`** de cada archivo para que cree un usuario con la factory, con los roles que su archivo necesita (`odontologo` + `recepcionista` cubre todas las rutas existentes), firme un access token **real** con `FirmadorJwtHs256(SECRETO_DE_PRUEBA)` y lo pase como cabecera por defecto (`TestClient(app, headers={"Authorization": f"Bearer {token}"})`), con la app armada con `crear_app(engine, ConfiguracionDeSesion(SECRETO_DE_PRUEBA, rondas_bcrypt=4))`. El token lo emite un helper `cabecera_de(engine, roles=...)` en `tests/conftest.py` (sobre `claims_para` y el reloj de prueba). Los cuerpos de los tests no cambian. `test_demo.py` inicia sesión con el usuario del seed por `POST /auth/login` (como el README). **Por qué no `app.dependency_overrides[usuario_actual]`:** no es un mock de sesión ni de repositorio, pero saltea justo lo que este change agrega; con el token real, cada test de C-01 a C-05 ejerce también la autenticación. **Alternativa descartada:** el *override* (menos código, menos cobertura).

Además se ajustan las aserciones de `actor_id` vacío (E9 cambia), las 32 llamadas a `crear_turno` (D210) y, en el perfil, `test_migraciones.py` y `test_seed_y_api.py`. Todo lo demás de C-01 a C-06 queda sin tocar.

### R18. Tests nuevos: dónde va cada uno — Propuesta

- `tests/unit/test_roles.py`: la matriz completa contra la tabla de R4 (parametrizada por permiso y rol: 6 × 3 casos), `puede` con varios roles (unión), con ninguno, `exigir_permiso` y el código de `PermisoInsuficiente`.
- `tests/integration/test_repositorio_usuarios.py` (se agregan casos): `roles_de`, `asignar_rol`, rol repetido o inválido, `quitar_rol`.
- `tests/integration/test_acceso.py`: `identificar_usuario` (sin token, ilegible, refresh, vencido en el instante exacto y un segundo antes, inexistente, inactivo, `token_version`, reactivado) y `autorizar`, con SQLite real, el firmador real y el reloj fijo.
- `tests/api/test_proteccion.py`: US-092 CA-1 y CA-4 por HTTP (cuerpos iguales, `WWW-Authenticate`), US-091 CA-1, CA-3 y CA-5, el orden `401` → `403` → `422`/`404` y la matriz de R4 sobre las siete rutas (parametrizada).
- `tests/api/test_proteccion_de_rutas.py`: el guard de R14 y US-092 CA-3 (login y refresh sin cabecera).
- `tests/api/test_historial.py` y `tests/integration/test_historial.py`: E9 con el actor (incluido el borde de dos usuarios).
- `tests/integration/test_seed_demo.py` y `tests/api/test_demo.py`: roles, vínculo y recepcionista.
- Perfil `postgres`: `test_migraciones.py` (INF-1 con `usuario_rol` y borde de `0007`; el `CHECK` de D213 rechaza un rol inválido) y `test_seed_y_api.py` (volumen sembrado en C-06 recibe roles y vínculo; recorrido con token sobre PostgreSQL).
- Nombres con el ID (`test_us092_ca4_...`, `test_us091_ca5_...`, `test_e9_...`). Sin `Mock`, `patch`, `freezegun` ni nada asíncrono; usuarios ficticios de `tests/factories.py` (`un_usuario(..., roles=...)`).

### R19. README — Propuesta

Sección «Protección del panel»: cómo obtener el access token con `POST /auth/login` y pegarlo en «Authorize» de `/docs`; la matriz de R4; los usuarios de prueba y sus roles; el recorrido de la demo con token (el de C-01 a C-06 cambia: sin token, `401`); `0007` en «Migraciones»; tabla escenario → test; y límites conocidos: `/docs` y `/openapi.json` públicos (D214); un cuerpo con JSON roto da `422` antes que `401` (R12); los eventos anteriores a C-07 sin `actor_id` y los turnos sin `creado_por`; deshacer `0007` pierde los roles; sin límite de peticiones (D195); el access token sigue valiendo hasta 15 minutos después de quitarle **un** rol solo para lo que sus otros roles permiten (el rol se lee en cada petición), pero desactivar al usuario lo corta en la siguiente.

### R20. Prueba en el navegador — Propuesta

Demo y Compose. En la demo: sin token, `POST /turnos` da `401`; con el token de la odontóloga (Authorize), el recorrido de siempre (`201`, `409` con los dos códigos, `422` `RN-GL-04`) y `GET /turnos/1/historial` con `actor_id` `"1"`; con el de la recepcionista, `POST /prestaciones` da `403` y `POST /turnos` `201`. En Compose (volumen existente, sembrado en C-06): el usuario recibe sus roles; `DELETE FROM usuario_rol WHERE usuario_id = 1 AND rol = 'odontologo'` y, **con el mismo token**, `POST /turnos` da `403` y el historial `200` (CA-5 y unión); se restaura el rol y vuelve el `201`; `UPDATE usuario SET token_version = token_version + 1` da `401`.

### R21. Riesgos de concurrencia y transacciones — Propuesta

La identificación lee usuario y roles en una transacción y la operación corre en otra. Un rol quitado entre las dos no se ve hasta la petición siguiente: es la misma ventana que tiene cualquier lectura previa, de milisegundos, y RN-AU-02 pide «en cada petición», no «en la misma transacción». No se toma bloqueo sobre `usuario` (frenaría toda la API por un dato que casi no cambia).

### R22. Tamaño y forma de trabajo del Apply — Decisión del autor (D216; continúa J21)

**26 tareas en 12 grupos**, por encima del «alrededor de 20» de `CHANGES.md`: es la **sexta excepción registrada** (D216; tras D123, D134, D152, D161 y D203). Motivos: seis escenarios con su RED, GREEN y TRIANGULATE; la adaptación de los tests de C-01 a C-05; una migración con su perfil; el seed en dos caminos; y las cuatro tareas fijas de navegador y verificación. No hay tarea del autor de entorno (no hay variables nuevas). Commits por tarea con el ok del autor dado por adelantado para el Apply, en español, con prefijo y `Co-Authored-By`; sin `--amend`. Los artefactos de este propose y la KB se commitean con el ok del autor antes del Apply. `CHANGES.md` y `.env*` no se tocan.

### Skills aplicadas

- `auth-implementation-patterns`: validación en el servidor en cada petición, RBAC en dependencias (`Depends`), roles de la base, `401` sin token y `403` con rol insuficiente, `401` genérico. **No aplicadas** (registro): revocación de a uno, cookies/CSRF, OAuth2/scopes, MFA, ejemplos de Node. **Contradicción con la KB:** la skill pide limitar peticiones y registrar eventos de seguridad en la autenticación; siguen fuera por D195 (manda la KB, regla dura 9).
- `fastapi-templates`: routers finos, `Depends` para seguridad y unidad de trabajo, errores de dominio traducidos en un manejador, endpoints síncronos. **Adaptada:** el *override* de dependencias en los tests no se usa para la autenticación (R17).
- `python-design-patterns`: la regla de permisos es pura y está separada del I/O (token, base); composición de dependencias (`requiere(permiso)` sobre `usuario_actual`); KISS: una matriz de datos y no una jerarquía de políticas.
- `python-error-handling`: un error de dominio por causa con su código RN (`PermisoInsuficiente`), excepciones de puerto traducidas en el caso de uso, mensajes sin datos del usuario.
- `python-testing-patterns`: AAA, nombres con el escenario, parametrización de la matriz, SQLite real, reloj inyectado, sin mocks ni `freezegun`.
- `database-migration` y `supabase-postgres-best-practices`: una migración reversible, columnas nuevas nulas (sin reescribir `turno`), nombres por convención, FK con `RESTRICT`, PK compuesta que ya indexa `usuario_id`, `CHECK` solo donde la lista es cerrada (D213), nada exclusivo de PostgreSQL en el modelo que usa SQLite.

## Contradicciones y huecos encontrados en las fuentes

1. **`02` contra `03` sobre la lectura del catálogo**: `02` («API REST (resumen)») da acceso «Odontólogo» a `/prestaciones` y `/sillones`; la matriz de `03` da `R` a la recepcionista y al dueño. → D205 (manda `03`; `02` se corrige al archivar).
2. **RN-GL-02 no prevé el control de acceso**: sus dos clases (entrada y negocio) pondrían el `401`/`403` después de la validación de entrada, revelando referencias y recursos a quien no tiene sesión. → D208 (tercera clase evaluada primero; RN-GL-02 se precisa al archivar).
3. **FastAPI rechaza el JSON roto antes que la autenticación**: una petición sin token y con JSON inválido recibe `422` y no `401` (código de `fastapi/routing.py` 0.115.14). RN-AU-05 dice «sin token válido, `401`». → Límite conocido (R12, V2); no se reescribe el manejo del cuerpo.
4. **`HTTPBearer` de FastAPI 0.115.14 responde `403` sin token** cuando `auto_error=True`; RN-AU-05 pide `401`. → `auto_error=False` (R9, V1).
5. **RN-AU-01 «las rutas públicas se limitan a las listadas en `03`»** no incluye `/docs`, `/redoc` ni `/openapi.json`, que FastAPI publica. → D214 (públicas como límite conocido; `03` y RN-AU-01 se ajustan al archivar).
6. **Specs vigentes desactualizados que un delta no puede corregir**: los «Propósito» de `gestion-de-prestaciones` y `gestion-de-sillones` dicen «sin autenticación hasta el change de roles (DD-14)», y `openspec/config.yaml` dice «ninguna ruta exige el token hasta C-07». → Se corrigen a mano al archivar (no son requisitos).
7. **Actor del historial (D159)**: el spec vigente de E9 afirma `actor_id` vacío «porque la creación no está autenticada todavía», y `04` §EventoTurno dice que los eventos anteriores a C-07 quedan así para siempre. → Delta de `historial-de-turnos` (R1, R13); los eventos viejos no se tocan.
8. **Regla de trabajo de C-03 a C-06 «no se toca ningún test de los changes anteriores»**: imposible de cumplir al proteger las rutas (unos 55 tests de API llaman sin token) y las 32 llamadas a `crear_turno`. → D211 (solo los *fixtures*) y D210.
9. **Demo sin Docker y seed de C-06 (D202)**: el usuario del seed no tiene roles; sin roles, desde C-07 recibiría `403` en todo. Y el volumen de PostgreSQL del autor ya tiene el usuario, así que `cargar_usuario_demo_si_falta` no lo vuelve a tocar. → R16 (asignación aparte e idempotente); la demo y el recorrido del README pasan a pedir token.
10. **`04` «Seed data inicial» dice «1 `Usuario`»**; mostrar el `403` en la demo pide un segundo usuario. → D212 (`04` se ajusta al archivar).
11. **`Profesional.matricula`** está en el alcance de `CHANGES.md` (y en la tabla «Tablas del modelo»), pero ningún criterio de US-091/US-092 la usa ni hay ruta que la escriba. → D215 (se crea en `0007`, sin uso).
12. **`CHECK` de enums**: `04` dice «enums de texto, sin tipo enum nativo» y D164 descartó `CHECK` sobre `evento_turno`; los roles son una lista cerrada (RN-AU-05). → D213 (`CHECK` solo para el rol).
13. **US-091 CA-4** («asignar `odontologo` a otro usuario no crea un `Profesional`») es de gestión de usuarios: no hay alta de usuarios ni asignación de roles por la API hasta C-09. → En C-07 solo se vincula el profesional del seed; el criterio se prueba en C-09 (CA-8 de US-093 es el mismo).
14. **`CHANGES.md`, árbol de dependencias**: la línea de C-07 lista «(C-03, C-04, C-05)» y C-06 aparece como su padre en el árbol; la entrada dice «C-03, C-04, C-05, C-06». No es una contradicción de fondo (las cuatro están archivadas), solo de lectura.
15. **`08` §Seguridad** dice «Ficha clínica solo `odontologo`»: no hay ficha hasta C-43; el `Permiso` correspondiente lo agrega ese change.

## Risks / Trade-offs

- [Dos lecturas de la base por petición (usuario y roles)] → Son por clave primaria y PK compuesta; consultorio chico y un solo proceso. Cachearlas contradiría D102.
- [Un access token robado sirve 15 minutos aunque se le quite un rol, para lo que sus otros roles permiten] → Es RN-AU-02 tal cual: el rol se lee en cada petición, así que el rol quitado deja de valer en la siguiente; para cortar todo, desactivar (C-09) incrementa `token_version`.
- [El JSON roto da `422` antes que `401`] → No revela datos (el cuerpo no se interpretó); límite del README (R12).
- [`/docs` y `/openapi.json` públicos describen todas las rutas] → La API se publica solo en `127.0.0.1`; sin configuración de producción todavía (D214).
- [Cambiar los *fixtures* de 55 tests podría esconder un cambio de comportamiento] → Solo cambia la cabecera; los cuerpos y aserciones quedan iguales y la suite debe dar el mismo número de tests en verde más los nuevos (verificación en 7.2).
- [Deshacer `0007` pierde roles y creadores] → Límite del README; los datos son ficticios y el seed restaura los suyos.
- [Un olvido de `requiere` en una ruta futura la dejaría abierta] → Guard de R14.
- [El actor obligatorio (D210) obliga a tocar 32 llamadas de tests de integración] → Cambio mecánico con un actor de prueba; a cambio no queda un camino anónimo.

## A verificar en el change

- **V1** (antes de la tarea 7.1): con FastAPI 0.115.14 instalado, `HTTPBearer(auto_error=False)` devuelve `None` sin cabecera y con `Authorization: Basic ...`, y registra `AccessToken` en `components.securitySchemes`; con `auto_error=True` respondería `403` (visto en el código fuente; falta comprobarlo con un test).
- **V2** (antes de la tarea 7.3): que una petición sin token con JSON roto da `422` y una con JSON válido pero mal formado (campo de más, id de ruta no entero) da `401`, porque las sub-dependencias se resuelven antes que la ruta y el cuerpo.
- **V3** (antes de la tarea 3.3): que `compare_metadata` no informa diferencias para la PK compuesta, el `UNIQUE` nulo de `profesional.usuario_id` y el `CHECK` (D213) tras `0007`, y que el `downgrade` a `0006` quita columnas con FK sin errores en PostgreSQL 17.10.
- **V4** (antes de la tarea 7.1): que `TestClient(app, headers=...)` de la versión instalada (`httpx` 0.28.1) envía la cabecera por defecto en cada petición y que una cabecera explícita en la petición la reemplaza (para los tests que prueban otro token).

## Migration Plan

1. Con el ok del autor, se commitean los artefactos y la KB (decisiones D204 a D216).
2. `0007_roles_y_creador` crea `usuario_rol` y las columnas nulas; Compose la aplica al arrancar y `cargar_seed` asigna los roles, el vínculo y la recepcionista (D212) aunque el volumen ya tenga el usuario.
3. **Corte de compatibilidad:** desde el despliegue, todo cliente del panel necesita un access token (no hay clientes todavía: la interfaz llega en C-08).
4. **Vuelta atrás:** `python -m alembic downgrade 0006` quita `usuario_rol` y las tres columnas sin tocar usuarios, turnos ni historial (escenario nuevo de INF-1); volver al código de C-06 deja las rutas abiertas otra vez.

## Notas para el archive

Correcciones que estas decisiones piden fuera del change. **No se editan ahora ni durante el Apply**: van en el commit `docs(kb)` del archive (y, las de `openspec/`, en el commit del archive), como en C-03 a C-06.

- `knowledge-base/02_descripcion_general.md`, «API REST (resumen)»: fila de Prestaciones y de Sillones con lectura para los tres roles (D205).
- `knowledge-base/05_reglas_de_negocio.md`, RN-GL-02: la tercera clase, «control de acceso» (`401` → `403`), evaluada antes que la validación de entrada, y el límite del JSON roto (D208). Misma precisión en el contexto de `openspec/config.yaml`.
- `knowledge-base/03_actores_y_roles.md` («Rutas públicas») y RN-AU-01 en `05`: la documentación interactiva sin token como límite conocido (D214); y quitar la «excepción conocida» de `POST /turnos` sin autenticación (DD-14), que deja de valer (también en `06` §US-010 y nota del orden, `07` Flujo 8 y `08` §Seguridad).
- `knowledge-base/04_modelo_de_datos.md`: «Seed data inicial» con los roles del usuario del seed y la recepcionista (D212); §Profesional y §Turno con `usuario_id`, `matricula` y `creado_por` construidos en `0007` (D213, D215); §«Usuario y UsuarioRol» con el `CHECK` del rol (D213); §EventoTurno con el `actor_id` desde C-07 (D209).
- `openspec/specs/gestion-de-prestaciones/spec.md` y `openspec/specs/gestion-de-sillones/spec.md`: quitar «sin autenticación hasta el change de roles (DD-14)» de su «Propósito» (un delta no puede editarlo; D204).
- `openspec/config.yaml`: la frase «ninguna ruta exige el token hasta el change de roles y protección del panel (C-07)» (D204).
- `CHANGES.md`: marcar C-07 con `[x]` y repetir `scripts/verificar_changes.py`.

## Open Questions

Ninguna. **Las trece preguntas abiertas de este design las cerró el autor el 2026-10-15 aceptando la recomendación del agente**: capability nueva `proteccion-del-panel` con dos deltas (Q1 → D204, R1); lectura del catálogo para los tres roles según `03` (Q2 → D205, R4); el mismo `401` de sesión inválida para toda causa (Q3 → D206, R10); `403` con `PermisoInsuficiente` y `RN-AU-05`, sin roles requeridos (Q4 → D207, R11); control de acceso como tercera clase evaluada primero (Q5 → D208, R12); `actor_id` como texto decimal y `creado_por` no expuesto (Q6 → D209, R13); actor obligatorio en `crear_turno` (Q7 → D210, R13); *fixtures* de C-01 a C-05 con token real, sin *override* (Q8 → D211, R17); recepcionista en el seed (Q9 → D212, R16); `CHECK` del rol (Q10 → D213, R5); documentación interactiva pública (Q11 → D214, R14); `matricula` en `0007` (Q12 → D215, R5); y 26 tareas como sexta excepción (Q13 → D216, R22).

Quedan marcadas «Propuesta», y el autor puede cambiarlas sin tocar el plan: los nombres de los permisos (R3), el nombre de la migración (R6), el nombre `AccessToken` del esquema (R9), los textos de `title` y `detail` (R11), el email de la recepcionista (R16) y la ubicación `api/seguridad.py` (R9).
