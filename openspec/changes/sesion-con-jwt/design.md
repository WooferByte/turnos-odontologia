# Design: sesion-con-jwt

Fecha del design: **2026-10-14**. Gobernanza **CRÍTICO** (autenticación): nada de esto se implementa hasta que el autor apruebe este documento, los specs y `tasks.md`.

**Respuesta del autor (2026-10-14): las nueve preguntas abiertas (Q1 a Q9) se cierran con la recomendación del agente.** Quedan como decisiones del autor D195 a D203, una por pregunta y en orden, registradas en `knowledge-base/10_preguntas_abiertas.md` (sección «Decisiones del autor (2026-10-14, sesion-con-jwt)»). Las demás decisiones marcadas «Propuesta» siguen así hasta que el autor apruebe el plan completo.

Las decisiones se numeran **J1 a J22** («J» de JWT) para no confundirlas con las D1..D203 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores (D de C-01, I de C-02, H de C-03, P de C-04, S de C-05). Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design, a confirmar) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»). El spec y las tareas ya reflejan D195 a D203.

## Context

Motivación y alcance: ver `proposal.md`. Requisitos: `specs/sesion-del-panel/spec.md` y el delta de `specs/persistencia-postgresql/spec.md`.

**Lo que dejaron C-01 a C-05** (leído del código, no supuesto):

- `app/main.py` tiene tres fábricas: `crear_app(engine)` (la usan todos los tests de API), `crear_app_demo()` (SQLite en memoria con `cargar_demo`) y `crear_app_desde_entorno(entorno=os.environ)` (lee `DATABASE_URL` con `leer_database_url` y levanta `ConfiguracionInvalida` si falta, D148).
- `infrastructure/configuracion.py` solo conoce `DATABASE_URL`; Python no lee `.env` (D150).
- `api/deps.py` da `get_uow` y `get_reloj`; los tests de API sustituyen el reloj con `app.dependency_overrides[get_reloj]`.
- `api/errores.py`: tabla `_CLASES_DE_ERROR` (clase → estado, `type`, `title`) buscada por `__mro__`; `_responder` arma un `application/problem+json` **sin cabeceras extra**; el cuerpo mal formado sale `422` con `codigos` vacío.
- `infrastructure/unidad_de_trabajo.py` crea un repositorio por agregado sobre la misma sesión; confirma al salir sin error. `application/puertos.py` declara los protocolos y las excepciones de la base (`SolapamientoEnLaBase`, `NombreRepetidoEnLaBase`).
- `infrastructure/db/modelos.py`: `CONVENCION_DE_NOMBRES` (`uq_<tabla>_<columnas>`), claves foráneas con `ondelete="RESTRICT"`, fechas con `FechaHoraUTC`. Migraciones `0001` a `0005`.
- `seed_demo.py`: `cargar_demo` (catálogo con ids fijos), `cargar_demo_si_falta` (no hace nada si existe el consultorio 1) y `ajustar_secuencias` (`setval` de las tablas sembradas, solo PostgreSQL). `cargar_seed.py` llama a las dos últimas.
- `docker-compose.yml`: la API recibe solo `DATABASE_URL` armada con las `POSTGRES_*` del `.env`. `backend/Dockerfile` migra, siembra y arranca `uvicorn` en un solo comando (D151).
- `tests/unit/test_imports_dominio.py` recorre `backend/app/domain` y falla ante cualquier import fuera de la biblioteca estándar: **el dominio no puede importar `jwt` ni `bcrypt`**.
- `tests/postgres/test_migraciones.py` compara el esquema migrado con `Base.metadata` (INF-1) y deshace hasta `0002` y `0004`; `tests/postgres/test_seed_y_api.py` llama a `crear_app_desde_entorno({"DATABASE_URL": url})`, que dejará de alcanzar cuando la fábrica exija `JWT_SECRET` (J10).
- **El volumen de PostgreSQL del autor ya tiene el consultorio 1**: `cargar_demo_si_falta` devuelve `False` y, si el usuario se sembrara dentro de `cargar_demo`, nunca se crearía (J11).

## Goals / Non-Goals

**Goals:**

- Que el inicio de sesión **no revele** si un email existe ni si la cuenta está inactiva: misma respuesta y una comparación bcrypt en todos los caminos.
- Que la vigencia de los tokens dependa **solo del reloj inyectado**: los tests prueban el vencimiento exacto sin congelar el tiempo y el dominio decide qué es un token vigente.
- Que el **secreto nunca esté en el repositorio** con un valor que sirva fuera de la demo, y que la suite por defecto siga sin leer variables de entorno.
- Dejar a C-07 las piezas que necesita para validar el access token en cada petición (leer el token, verificar vigencia, `activo` y `token_version`) sin rehacerlas.

**Non-Goals:**

- Validar el access token en las rutas existentes, roles y `403` (C-07).
- Incrementar `token_version` (lo hacen C-09 y C-10 al desactivar y al cambiar o restablecer la contraseña).
- La regla de largo de contraseña como error de la API (RN-AU-07 se aplica al definir una contraseña: C-09 y C-10). Acá solo se usa para validar la contraseña del seed (J11).
- Rotación del refresh, lista de revocación y cierre de sesión en el servidor.
- Límite de peticiones y registro de eventos de seguridad (D195).
- Dónde guarda los tokens el panel de React (C-08; ver «Contradicciones y huecos», punto 9).
- Un segundo consultorio o un usuario de otro consultorio (D173).

## Decisions

### J1. Una capability nueva, `sesion-del-panel`, y la lista de INF-1 — Decisión del autor (D158) + Propuesta (nombre)

US-090 y US-094 van en una capability nueva, `sesion-del-panel`. **Propuesta:** el nombre describe el comportamiento duradero (la sesión del panel) y no la tecnología; C-07 puede agregarle la validación del access token o abrir la suya (`proteccion-del-panel`), lo decide su propose. El delta de `persistencia-postgresql` cambia **solo la lista del escenario INF-1** y suma un borde para deshacer `0006`: es lo que D158 fijó para todo change que agregue tablas («toca solo la lista del escenario, no el requisito»). El texto del requisito queda igual.

### J2. Dependencias: `PyJWT==2.15.1` y `bcrypt==5.0.0` en el grupo `app` — Propuesta (aplica D116, D133, D137)

Consultadas el **2026-10-14** en la API JSON de PyPI (`https://pypi.org/pypi/<paquete>/json` y `/<versión>/json`). Límite de D133: ninguna publicada el **2026-10-07 o después**.

| Paquete | Pin | Publicada | Requiere Python | Ruedas | Dependencias |
|---|---|---|---|---|---|
| `PyJWT` | `PyJWT==2.15.1` (la más nueva) | 2026-09-28 | `>=3.9`; clasificadores 3.11 a 3.15 | `py3-none-any` | Ninguna en 3.11+ (`typing_extensions` solo para `<3.11`); el extra `crypto` no hace falta para HS256 |
| `bcrypt` | `bcrypt==5.0.0` (la más nueva) | 2025-09-25 | `>=3.8`; clasificadores 3.11 a 3.14 | `cp39-abi3` para `win_amd64` y `manylinux` `x86_64` (la imagen `python:3.13.15-slim-bookworm`): no compila | Ninguna |

Van al grupo `app` (la API los usa en Compose); el grupo `test` los incluye. Compatibilidad comprobada con los metadatos, no supuesta: ninguno pide nada que choque con los pins actuales y los dos cubren 3.11 a 3.13 (el rango del proyecto; `pydantic-core` sigue sin 3.14, D139). **Cambios de las versiones que este design usa** (de los changelogs oficiales): `bcrypt` 5.0.0 hace que `hashpw` levante `ValueError` con más de 72 bytes (antes truncaba en silencio); `PyJWT` 2.13.0 a 2.15.1 son de seguridad y correcciones (claves HMAC vacías rechazadas, validación del `alg`, errores de claims mal formados como `PyJWTError`), y desde antes valida que `sub` sea texto y que `iat` no esté en el futuro.

**Alternativas descartadas:** `passlib` (última versión 1.7.4 del 2020-10-08, sin mantenimiento e incompatible con `bcrypt` 4.1 en adelante); `python-jose` (3.5.0 del 2025-05-28; historial de vulnerabilidades y trae `ecdsa`, `rsa` y `pyasn1`, que HS256 no necesita); `authlib` (1.9.1 publicada hoy, 2026-10-14: la excluye D133, y es mucho más de lo que hace falta); `pwdlib` (0.3.1 del 2026-08-12; una capa más sobre `bcrypt`, pensada para argon2, que la KB no eligió). Transitivas: ninguna.

### J3. Tabla `usuario` — Decisión del autor (`04` §«Usuario y UsuarioRol»; normalización del email, D199) + Propuesta (tipos)

| Columna | Tipo | Nota |
|---|---|---|
| `id` | entero, PK | |
| `consultorio_id` | entero, NN, FK → `consultorio` (`RESTRICT`) | Un solo consultorio hasta C-07 (D173) |
| `email` | texto, NN, `UNIQUE` (`uq_usuario_email`) | Guardado **normalizado**: sin espacios en los extremos y en minúsculas (D199) |
| `hash_password` | texto, NN | Hash bcrypt con su sal y su costo; nunca la contraseña |
| `activo` | booleano, NN, default `true` | |
| `token_version` | entero, NN, default 0 | |
| `creado_en` | `FechaHoraUTC`, NN | Del reloj inyectado |

**Por qué normalizar al guardar y no un índice funcional** (`lower(email)`): el mismo `UNIQUE` simple vale igual en SQLite y en PostgreSQL, la suite por defecto lo ejerce sin depender de una función de PostgreSQL, y la comparación del inicio de sesión es una igualdad exacta sobre el valor normalizado. `str.lower()` y no `casefold()`: la parte local de un email es ASCII en la práctica y `casefold` cambia caracteres como «ß». Sin `nombre` ni `UsuarioRol` (C-07). Un `UNIQUE` violado en el repositorio sale como `EmailRepetidoEnLaBase` (excepción de puerto, como `NombreRepetidoEnLaBase`); en este change solo lo usan el seed y los tests (no hay alta de usuarios hasta C-09).

### J4. Migración `0006_usuarios` — Decisión del autor (DD-15) + Propuesta

Autogenerada y revisada a mano contra `modelos.py`, como `0005`: `create_table('usuario', ...)` con `pk_usuario`, `fk_usuario_consultorio_id` y `uq_usuario_email`; `downgrade` hace `drop_table('usuario')` y nada más (no toca las demás tablas). Sin `server_default` (los valores por defecto los pone la aplicación, como en el resto del modelo). `ajustar_secuencias` agrega `usuario` a `_TABLAS_SEMBRADAS`.

### J5. Dominio de acceso, puro — Propuesta

`backend/app/domain/acceso/` (solo biblioteca estándar; el guard de imports lo exige):

- `usuarios.py`: `DatosUsuario` (dataclass congelada: `id`, `consultorio_id`, `email`, `hash_password`, `activo`, `token_version`, `creado_en`) y `normalizar_email(texto) -> str` (`strip().lower()`).
- `sesion.py`: `TipoDeToken` (enum `access`, `refresh`); `ClaimsDeSesion` (dataclass congelada: `usuario_id`, `token_version`, `tipo`, `emitido_en`, `vence_en`, aware UTC); `claims_para(usuario, tipo, ahora, vigencia)`; `esta_vigente(claims, ahora)` = `emitido_en <= ahora < vence_en` (semiabierto, como los intervalos de la agenda); y `exigir_token_valido(claims, tipo_esperado, usuario | None, ahora)`, que levanta `SesionInvalida` si el tipo no es el esperado, si no está vigente, si el usuario no existe, si no está activo o si su `token_version` difiere. **C-07 reusa la misma función con `TipoDeToken.ACCESS`** (por eso recibe el tipo esperado como parámetro, Propuesta); C-06 la llama solo con `TipoDeToken.REFRESH`.
- `domain/errors.py`: `CredencialesInvalidas` (`RN-AU-04`) y `SesionInvalida` (`RN-AU-03`), sin datos del usuario en el mensaje.

**Por qué en el dominio:** las reglas de vigencia, tipo, `activo` y `token_version` son reglas de negocio (RN-AU-03, RN-AU-04) y se testean sin JWT ni base. Firmar y hashear son I/O criptográfico y van en infraestructura.

### J6. Puertos y adaptadores — Propuesta

En `application/puertos.py`:

- `RepositorioUsuarios`: `por_email(email_normalizado) -> DatosUsuario | None`, `obtener(usuario_id) -> DatosUsuario | None`, `agregar(datos) -> DatosUsuario`. La unidad de trabajo expone `usuarios`.
- `HasherDeContrasenas`: `hashear(contrasena) -> str`, `verificar(contrasena, hash) -> bool` y `verificar_sin_usuario(contrasena) -> bool` (siempre `False`, con el mismo costo; J8).
- `FirmadorDeTokens`: `firmar(claims) -> str` y `leer(token) -> ClaimsDeSesion`, que levanta `TokenIlegible` (excepción de puerto) ante cualquier problema de forma o firma.

Adaptadores en `infrastructure/seguridad/`: `contrasenas.py` (`HasherBcrypt(rondas)`: `bcrypt.hashpw(..., bcrypt.gensalt(rondas))` y `bcrypt.checkpw`; una contraseña de más de 72 bytes en UTF-8 devuelve `False` **sin llamar a bcrypt**, porque 5.0.0 levanta `ValueError` y nunca puede coincidir con un hash guardado, que viene de una contraseña de 72 bytes como mucho) y `tokens.py` (`FirmadorJwtHs256(secreto)`).

### J7. Forma de los JWT y lectura con `PyJWT` — Propuesta + A verificar (V2)

- Claims: `sub` (id del usuario como texto: `PyJWT` exige texto), `token_version` (entero; el nombre que fija `CHANGES.md`), `typ` (`access` o `refresh`), `iat` y `exp` (segundos enteros desde la época, calculados con el reloj inyectado). Sin `iss`, `aud`, `nbf` ni `jti`: una sola instalación, sin revocación de a uno.
- `firmar`: `jwt.encode(payload, secreto, algorithm="HS256")`.
- `leer`: `jwt.decode(token, secreto, algorithms=["HS256"], options={"verify_exp": False, "verify_iat": False, "verify_nbf": False, "require": ["sub", "typ", "token_version", "iat", "exp"], "enforce_minimum_key_length": True})`. **Por qué se apaga la verificación de tiempos de `PyJWT`:** usa `time.time()` y no el reloj inyectado (regla dura 2); con un reloj de prueba del 2026-11-02, `iat` quedaría «en el futuro» y `PyJWT` levantaría `ImmatureSignatureError`. La firma, el algoritmo (lista cerrada `["HS256"]`, que rechaza `none` y HS512) y los claims obligatorios sí los verifica `PyJWT`; el tiempo lo decide `esta_vigente` en el dominio. Cualquier `jwt.PyJWTError`, un `sub` que no es un entero o un `typ` desconocido → `TokenIlegible`.

### J8. Iniciar sesión — Propuesta (aplica RN-AU-04)

`application/sesion.py`, `iniciar_sesion(comando, uow, hasher, firmador, vigencias, reloj) -> TokensDeSesion`:

1. `email = normalizar_email(comando.email)`; `usuario = uow.usuarios.por_email(email)`.
2. Si no hay usuario: `hasher.verificar_sin_usuario(contrasena)` (compara contra un hash de relleno calculado al construir el hasher, con las mismas rondas) y `CredencialesInvalidas`.
3. Si hay: `coincide = hasher.verificar(contrasena, usuario.hash_password)`. **Se verifica la contraseña antes de mirar `activo`**, para que el inactivo cueste lo mismo que el activo.
4. Si `not coincide or not usuario.activo`: `CredencialesInvalidas`.
5. Si no, emite access (`vigencias.access`, 15 minutos) y refresh (`vigencias.refresh`, 7 días) con `ahora = reloj()` único para los dos.

La lectura del usuario se hace dentro de `with uow:` y no escribe nada (no hay «último ingreso» en el modelo). Contraseña de más de 72 bytes: cae en el paso 4 por `verificar` (`False`, J6); responde el mismo `401`.

### J9. Renovar la sesión — Decisión del autor (sin rotación del refresh, D201) + Propuesta (aplica RN-AU-03, RN-AU-04, D43)

`renovar_sesion(token, uow, firmador, vigencias, reloj) -> AccessToken`:

1. `claims = firmador.leer(token)`; `TokenIlegible` → `SesionInvalida`.
2. `usuario = uow.usuarios.obtener(claims.usuario_id)` (de la base en cada renovación).
3. `exigir_token_valido(claims, TipoDeToken.REFRESH, usuario, reloj())`.
4. Emite un access nuevo con la `token_version` **actual** del usuario y `ahora = reloj()`. **No** emite refresh nuevo: el refresh sigue venciendo a los 7 días del inicio de sesión (US-094 CA-1 pide «un nuevo access token»; D201).

### J10. Configuración y fábricas de la aplicación — Decisión del autor (secreto efímero y constante de tests, D196; mínimo de 32 bytes, D198) + Propuesta

En `infrastructure/configuracion.py`:

- `ConfiguracionDeSesion(secreto: str, minutos_access: int = 15, dias_refresh: int = 7, rondas_bcrypt: int = 12)` (dataclass congelada; `__repr__` **no muestra el secreto**).
- `leer_configuracion_de_sesion(entorno)`: `JWT_SECRET` obligatoria y de **32 bytes como mínimo** en UTF-8 (D198); `JWT_ACCESS_MINUTES` y `JWT_REFRESH_DAYS` opcionales, enteros mayores que 0, con 15 y 7 por defecto (SU-09: «configurables por variable de entorno»). Cualquier problema → `ConfiguracionInvalida` con el **nombre** de la variable, nunca su valor. Las rondas de bcrypt no son variable de entorno: 12 (el valor por defecto de `bcrypt`).
- `secreto_efimero()`: `secrets.token_urlsafe(48)` (64 caracteres).

En `app/main.py`:

- `crear_app(engine, sesion: ConfiguracionDeSesion | None = None)`: si no se pasa, usa un **secreto efímero** generado al crear la app (D196). Así los tests de C-01 a C-05, que llaman a `crear_app(engine)`, no cambian. Guarda en `app.state` el firmador, el hasher y las vigencias; `api/deps.py` los entrega con `get_firmador`, `get_hasher` y `get_vigencias`.
- `crear_app_demo()`: secreto efímero y usuario del seed (J11). Los tokens de la demo mueren con el proceso, igual que sus datos en memoria.
- `crear_app_desde_entorno(entorno)`: lee `DATABASE_URL` **y después** `JWT_*`; sin `JWT_SECRET` (o con uno corto) levanta `ConfiguracionInvalida` y no arranca con un secreto efímero. Los dos tests existentes de `tests/api/test_app_desde_entorno.py` siguen pasando porque fallan antes, por `DATABASE_URL`.
- Los tests de la sesión pasan una `ConfiguracionDeSesion` con un secreto ficticio de prueba definido en `tests/conftest.py` (`SECRETO_DE_PRUEBA`, 32 bytes o más) y `rondas_bcrypt=4` (el mínimo de bcrypt), para que la suite no tarde un cuarto de segundo por hash.

### J11. Usuario del seed — Decisión del autor (`04` «Seed data inicial»: un usuario ficticio; contraseña, D197; sin roles, D202) + Propuesta

- Id 1, consultorio 1, email `odontologa@consultorio-demo.test` (el dominio `.test` está reservado y no existe), activo, `token_version` 0, **sin roles** hasta C-07 (D202).
- **Contraseña** (D197): la demo sin Docker usa la constante `CONTRASENA_DEMO = "demo-consultorio-2026"` (21 caracteres, solo para la base en memoria) y la carga en PostgreSQL lee **`SEED_USUARIO_PASSWORD`**, que `.env.example` trae con el mismo valor de prueba (el README documenta una sola contraseña). Si falta, está vacía o no tiene entre 10 caracteres y 72 bytes (RN-AU-07), `cargar_seed` termina con `ConfiguracionInvalida` antes de tocar la base.
- `cargar_demo` **no cambia**. Se agregan `cargar_usuario_demo(sesion, hash_password)` y `cargar_usuario_demo_si_falta(sesion, hash_password) -> bool` (no hace nada si ya hay un usuario con ese email). `crear_app_demo` llama a `cargar_demo` y a `cargar_usuario_demo`; `cargar_seed` llama a `cargar_demo_si_falta`, a `cargar_usuario_demo_si_falta` y, si sembró algo, a `ajustar_secuencias`. Así **un volumen sembrado antes de C-06 recibe el usuario** (spec, tercer escenario del primer requisito).
- Límite: cambiar `SEED_USUARIO_PASSWORD` después no cambia la contraseña de un usuario ya sembrado (no hay restablecimiento hasta C-09); se documenta con `docker compose down -v`.

### J12. API: `POST /auth/login` y `POST /auth/refresh` — Propuesta

`api/routers/auth.py` (`prefix="/auth"`, endpoints síncronos), esquemas en `api/esquemas.py` con `extra="forbid"` y ejemplos para `/docs`:

- `LoginEntrada`: `email` (texto de 1 a 254 caracteres, sin validar formato: un email mal escrito es simplemente inexistente, y `EmailStr` agregaría la dependencia `email-validator`) y `contrasena` (texto de 1 carácter como mínimo; el tope de 72 bytes no es de formato, J8).
- `TokensSalida`: `access_token`, `refresh_token`, `token_type` (`"bearer"`) y `expires_in` (segundos de vida del access). Los nombres de los tokens siguen la convención de OAuth 2.0 (RFC 6749 §5.1) para que los clientes y `/docs` los reconozcan; el resto de la API sigue en español.
- `RefreshEntrada`: `refresh_token` (texto de 1 carácter como mínimo). `AccessSalida`: `access_token`, `token_type`, `expires_in`.
- `200` con `Cache-Control: no-store` (RFC 6749 §5.1). Los dos declaran `401` y `422` con el esquema `Problema` en OpenAPI.
- **Sin** `OAuth2PasswordBearer` ni botón «Authorize» en `/docs`: ninguna ruta exige token hasta C-07, que elige el esquema de seguridad.

### J13. Respuestas `401` — Decisión del autor (un `401` idéntico por endpoint, D200) + Propuesta (textos y `type`)

Dos filas nuevas en `_CLASES_DE_ERROR`:

| Clase | Estado | `type` | `title` | `detail` | `codigos` |
|---|---|---|---|---|---|
| `CredencialesInvalidas` | 401 | `/errores/credenciales-invalidas` | «Credenciales inválidas» | «El email o la contraseña no son correctos.» | `["RN-AU-04"]` |
| `SesionInvalida` | 401 | `/errores/sesion-invalida` | «Sesión inválida» | «La sesión no es válida o venció. Iniciá sesión de nuevo.» | `["RN-AU-03"]` |

Las dos llevan `WWW-Authenticate: Bearer` (RFC 6750 §3): `_responder` pasa a aceptar cabeceras. El texto es fijo: no depende de la causa. El usuario inactivo recibe exactamente el `401` de credenciales (RN-AU-04 no distingue). En el refresh, el usuario inactivo usa `RN-AU-03` como todo lo demás, para no revelar la causa (D200).

### J14. Clasificación de los rechazos y orden de evaluación (RN-GL-02) — Propuesta

- **Validación de entrada** (`422`, sin código RN, todo junto, D135): cuerpo ausente o JSON roto, campo faltante, campo de más, tipo erróneo, `email` vacío o de más de 254 caracteres, `contrasena` o `refresh_token` vacíos. No se evalúa nada más.
- **Regla de negocio** (de a una; la primera que falla es la única):
  - Login: usuario por email → contraseña (siempre con bcrypt, J8) → `activo`. Las tres salen como el mismo `401` `RN-AU-04`, así que el orden no se ve desde afuera; está fijado para que el tiempo no lo revele.
  - Refresh: forma y firma → tipo `refresh` → vigencia con el reloj → usuario existe → `activo` → `token_version`. Todas salen como el mismo `401` `RN-AU-03`.

### J15. Reloj — Decisión del autor (regla dura 2, DD-13) + Propuesta

Los dos casos de uso reciben `reloj` (`get_reloj` en la API). `emitido_en`, `vence_en` y la comparación de vigencia son aware UTC; `iat` y `exp` del JWT se derivan de esos valores con `int(timestamp())`. Los tests de API sustituyen `get_reloj` como ya lo hacen los de C-01 a C-05. No se usa `time.time()` en ningún lado; el único `datetime.now` sigue en `domain/tiempo.py`.

### J16. Compose y `.env.example` — Propuesta + tarea del autor (D197) + A verificar (V3)

`docker-compose.yml`, servicio `api`, agrega:

```yaml
      JWT_SECRET: ${JWT_SECRET}
      JWT_ACCESS_MINUTES: ${JWT_ACCESS_MINUTES:-15}
      JWT_REFRESH_DAYS: ${JWT_REFRESH_DAYS:-7}
      SEED_USUARIO_PASSWORD: ${SEED_USUARIO_PASSWORD}
```

Sin `${VAR:?…}`: con esa forma Compose rechaza **todo** el archivo si falta la variable, también `docker compose up -d postgres` del perfil de tests; sin ella, la API arranca, `cargar_seed` o `crear_app_desde_entorno` fallan con `ConfiguracionInvalida` y el nombre de la variable en el log (V3).

**Tarea del autor** (una regla de permisos impide que el agente lea o escriba `.env` y `.env.example`): agregar al final de `.env.example` **y** de su `.env` del repositorio principal, a mano, estas líneas exactas:

```
# Sesión del panel (C-06). Valores de prueba: cambiarlos fuera de la demo.
# JWT_SECRET: 32 bytes como mínimo; firma los access y refresh token (HS256).
JWT_SECRET=cambiar-en-local-secreto-de-prueba-0000
JWT_ACCESS_MINUTES=15
JWT_REFRESH_DAYS=7
# Contraseña ficticia del usuario del seed odontologa@consultorio-demo.test (de 10 caracteres a 72 bytes).
SEED_USUARIO_PASSWORD=demo-consultorio-2026
```

(`cambiar-en-local-secreto-de-prueba-0000` tiene 39 bytes; D198.)

### J17. Tests: dónde va cada uno — Propuesta

- `tests/unit/test_sesion.py`: `claims_para`, `esta_vigente` (tabla parametrizada: emitido, un segundo antes de vencer, el instante del vencimiento, después), `exigir_token_valido` (tipo, vigencia, usuario ausente, inactivo, `token_version`), `normalizar_email`, y los códigos de `CredencialesInvalidas` y `SesionInvalida`.
- `tests/unit/test_seguridad.py`: `HasherBcrypt(4)` (hash distinto de la contraseña y con prefijo `$2b$04$`, verifica la correcta, rechaza la incorrecta, más de 72 bytes da `False` sin excepción, `verificar_sin_usuario` da `False`) y `FirmadorJwtHs256` (ida y vuelta, otro secreto, firma alterada, `alg` `none`, HS512, claim faltante, `sub` no entero, `typ` desconocido, secreto corto rechazado).
- `tests/unit/test_configuracion.py` (se agregan casos): `JWT_SECRET` ausente, vacía o corta; minutos y días inválidos; valores por defecto; el `repr` no muestra el secreto.
- `tests/integration/test_repositorio_usuarios.py` y `tests/integration/test_sesion.py` (casos de uso con SQLite en memoria, el hasher y el firmador reales): CA-1 a CA-4 de US-090 y CA-1 a CA-3 de US-094.
- `tests/api/test_auth.py`: estados, cuerpos, cabeceras (`WWW-Authenticate`, `Cache-Control`), igualdad de los cuerpos del `401`, `422` de formato y OpenAPI.
- `tests/integration/test_seed_demo.py` y `tests/api/test_demo.py` (se agregan casos): el usuario de la demo inicia sesión; `cargar_usuario_demo_si_falta` no duplica.
- `tests/api/test_app_desde_entorno.py` (se agregan casos): sin `JWT_SECRET` o con uno corto, `ConfiguracionInvalida` que nombra la variable.
- Perfil `postgres`: `test_migraciones.py` (INF-1 con `usuario` y el borde de `0006`), `test_seed_y_api.py` (el volumen con consultorio sin usuario recibe el usuario, la secuencia avanza, inicio de sesión sobre PostgreSQL; los dos tests que llaman a `crear_app_desde_entorno` reciben un `JWT_SECRET` de prueba).
- **Comparación de contraseña en todos los caminos** (spec, CA-2 borde): `HasherQueCuenta`, un envoltorio escrito en el test sobre el `HasherBcrypt` real que cuenta las llamadas. No es un mock de sesión ni de repositorio (regla dura 6) y no reemplaza ningún comportamiento: Propuesta.
- Nombres con el ID: `test_us090_ca2_...`, `test_us094_ca3_...`. Sin `Mock`, `patch` ni nada asíncrono. Usuarios ficticios de `tests/factories.py` (`un_usuario(sesion, consultorio, contrasena=..., activo=..., token_version=...)`, que hashea con 4 rondas).

### J18. README — Propuesta

Sección «Sesión del panel» con `POST /auth/login` y `POST /auth/refresh` sobre la demo (usuario y contraseña de prueba, cómo leer `exp`), variables nuevas en la tabla de «Variables de entorno», migración `0006` en «Migraciones», tabla escenario → test (y la del perfil) y límites conocidos: las rutas siguen sin exigir token hasta C-07; sin límite de peticiones en `/auth/login` (D195); sin cierre de sesión en el servidor; los tokens de la demo dejan de valer al reiniciarla (secreto efímero); la contraseña del seed es de prueba y un volumen ya sembrado no la cambia; el secreto de `.env.example` es de prueba.

### J19. Fuera del change: límite de peticiones y registro de eventos — Decisión del autor (D195)

La KB pide límite de peticiones solo en las rutas públicas de **reserva** (D70); para `/auth/login` no dice nada, y la skill `auth-implementation-patterns` lo recomienda. Decisión: **fuera de C-06**, como límite conocido del README, y anotarlo para el change de reserva pública (C-25/C-28), que ya tiene que elegir cómo limitar. Motivos: agregarlo exige una dependencia o un contador en memoria que no sirve con varias réplicas; la API se publica solo en `127.0.0.1`; y bcrypt con 12 rondas ya limita el ritmo de prueba de contraseñas por proceso. Tampoco se agrega registro de eventos de seguridad: los logs del proyecto no tienen formato definido todavía (D70 solo pide que no lleven datos clínicos ni teléfonos).

### J20. Lo que queda para C-07 y C-08 — Propuesta

- **C-07** reusa `FirmadorDeTokens.leer`, `exigir_token_valido` con `TipoDeToken.ACCESS` y `RepositorioUsuarios.obtener` en una dependencia de FastAPI; agrega `UsuarioRol`, los roles del seed y el esquema de seguridad de `/docs`.
- **C-08** decide dónde guarda el panel los tokens (memoria, `sessionStorage`, cookie `HttpOnly`); si elige una cookie, el refresh pasaría a leerse de una cookie y habría que sumar CSRF: es un cambio de contrato de `/auth/refresh` que se decide en su propose, no acá.

### J21. Commits y forma de trabajo del Apply — Propuesta (continúa I16 de C-02)

Gobernanza CRÍTICO: el Apply empieza recién con la aprobación explícita del plan. Commit por tarea con el ok del autor dado por adelantado para el Apply (como en C-03 a C-05), en español, con prefijo y la línea `Co-Authored-By`; sin `--amend` ni reescritura. Los artefactos de este propose y la KB se commitean con el ok del autor antes del Apply. `CHANGES.md` y `.env*` no se tocan.

### J22. Tamaño: 27 tareas en 11 grupos — Decisión del autor (D203)

Por encima del «alrededor de 20» de `CHANGES.md`: el autor lo aceptó como quinta excepción registrada (tras D123, D134, D152 y D161). Motivos: dos dependencias nuevas y su configuración, seis escenarios con su RED, GREEN y TRIANGULATE, una migración con su perfil, el seed en dos caminos (demo y PostgreSQL), una tarea del autor para el entorno y las cuatro tareas fijas de navegador y verificación. Bajarlo a ~22 obligaría a juntar RED y GREEN en la misma tarea, contra el TDD estricto.

### Skills aplicadas

- `auth-implementation-patterns`: bcrypt, access corto y refresh largo, HS256 con secreto del entorno, `401` genérico, validación en el servidor. **No aplicadas** (registro): revocación de a uno y tabla de tokens (RN-AU-03 lo descarta), sesiones con cookie y CSRF, OAuth2, MFA, ejemplos de Node. **Adaptadas**: el límite de peticiones queda fuera (D195) porque la KB lo pide solo para la reserva pública.
- `fastapi-templates`: router fino, esquemas de respuesta, `Depends` para unidad de trabajo, reloj, firmador y hasher; endpoints síncronos (DD-12).
- `python-testing-patterns`: AAA, nombres con el escenario, parametrización, `pytest.raises`, SQLite real, reloj inyectado; sin `freezegun`.
- `python-error-handling` y `python-design-patterns`: errores de dominio con código RN, puertos con inyección por constructor, I/O criptográfico fuera de las reglas, KISS (sin rotación ni lista de revocación).
- `database-migration` y `supabase-postgres-best-practices`: una migración reversible, `UNIQUE` con nombre por convención, `timestamptz`, nada exclusivo de PostgreSQL en el modelo que usa SQLite.

## Contradicciones y huecos encontrados en las fuentes

1. **`04` «Seed data inicial»** dice que el usuario del seed tiene los roles `odontologo` + `dueno`, pero `CHANGES.md` pone `UsuarioRol` en C-07. → El seed de C-06 crea el usuario sin roles y C-07 se los asigna (D202).
2. **`04` «Seed data inicial»** dice que las credenciales de prueba se definen «en un archivo de ejemplo de entorno», pero la demo sin Docker y la suite no leen variables (D148, regla dura 6). → D197: variable para PostgreSQL y constante con el mismo valor para la demo.
3. **`08` «Variables de entorno»** da `cambiar-en-local` (16 bytes) como ejemplo de `JWT_SECRET`; para HS256 la RFC 7518 §3.2 pide una clave de 256 bits como mínimo y `PyJWT` 2.15.1 emite `InsecureKeyLengthWarning` con menos de 32 bytes. → D198 (y corregir el ejemplo de `08` al archivar).
4. **`08`** describe `JWT_SECRET` como «Firma de JWT y tokens de gestión». C-06 solo firma JWT del panel; si los tokens de gestión del paciente (C-25) usan el mismo secreto o uno propio se decide en ese change. Sin cambio acá.
5. **Skill vs KB sobre el límite de peticiones**: la skill lo pide en los endpoints de autenticación; la KB (D70), solo en las rutas públicas de reserva. → D195 (fuera de C-06; manda la KB).
6. **Email único** (`04`, US-093 CA-2) sin regla de mayúsculas. → D199 (normalizar al guardar).
7. **US-090 CA-3** dice que un usuario inactivo «no puede iniciar sesión» sin fijar la respuesta; RN-AU-04 dice «`401` genérico» para credenciales inválidas y que el inactivo no inicia sesión. → El mismo `401` (D200).
8. **RN-AU-07** (largo de la contraseña) dice que «el error y su forma se definen en el design del change»: es de C-09/C-10, que son los que definen contraseñas. C-06 solo lo usa para validar la contraseña del seed (J11) y para no llamar a bcrypt con más de 72 bytes (J6).
9. **Dónde guarda los tokens el panel** no está en la KB (marca [ADAPT] del registro de skills). → Queda para C-08 (J20).
10. **`02`** lista `POST /auth/cambiar-contrasena` en la fila «Auth»: es de C-10, fuera de este change.

## Risks / Trade-offs

- [El refresh no se revoca de a uno: un refresh robado sirve hasta 7 días] → Decisión del autor (RN-AU-03). Lo corta `token_version` (C-09 y C-10) o desactivar al usuario; la API se publica solo en `127.0.0.1`.
- [Sin límite de peticiones, `/auth/login` admite pruebas de contraseña sin tope] → bcrypt con 12 rondas limita el ritmo por proceso; límite conocido del README (D195).
- [Igualar tiempos con un hash de relleno no es una garantía estricta: hay diferencias de microsegundos en la lectura de la base] → Se iguala lo que domina el tiempo (bcrypt, cientos de milisegundos); la respuesta y las cabeceras son idénticas.
- [El secreto de prueba de `.env.example` es público] → Es de prueba (como `POSTGRES_PASSWORD`); el README dice que hay que cambiarlo fuera de la demo; la validación de 32 bytes evita secretos triviales.
- [Un secreto efímero en `crear_app` sin configuración podría esconder un error de configuración] → Solo lo usan los tests y la demo en memoria; `crear_app_desde_entorno`, la que arranca Compose, exige `JWT_SECRET` y no cae al efímero.
- [Normalizar con `lower()` no cubre emails con mayúsculas no ASCII] → Datos ficticios con ASCII; un email internacionalizado quedaría con su forma exacta, igual de único.
- [La verificación de tiempos la hace el dominio y no `PyJWT`: un error ahí aceptaría tokens vencidos] → Tabla parametrizada de vigencia en el dominio y escenarios de vencimiento exacto por la API (US-094 CA-2).

## A verificar en el change

- **V1** (antes de la tarea 3.2): que `bcrypt.hashpw` de 5.0.0 levanta `ValueError` con más de 72 bytes (changelog) y qué hace `bcrypt.checkpw` en ese caso; el hasher no lo llama, pero el test lo deja documentado.
- **V2** (antes de la tarea 3.2): que `jwt.decode` de 2.15.1 acepta `options` con `verify_exp`, `verify_iat` y `verify_nbf` en `False`, `require` y `enforce_minimum_key_length`, y que con esta última un secreto de menos de 32 bytes levanta `InvalidKeyError` al firmar y al leer (visto en el código fuente de `api_jws.py` 2.15.1; falta comprobarlo instalado).
- **V3** (antes de la tarea 8.3): que `docker compose up -d postgres` funciona sin `JWT_SECRET` en `.env` (solo un aviso) y que la API sin la variable termina con `ConfiguracionInvalida` y el nombre en el log.
- **V4** (antes de la tarea 10.1): que `docker compose up --build` instala `bcrypt` 5.0.0 desde la rueda `abi3` en `python:3.13.15-slim-bookworm`, sin compilar.

## Migration Plan

1. Con el ok del autor, se commitean los artefactos y la KB; el autor hace la tarea 8.2 (líneas de `.env.example` y de su `.env`) cuando el Apply llegue ahí.
2. `0006_usuarios` crea la tabla; Compose la aplica al arrancar (`alembic upgrade head`) y `cargar_seed` agrega el usuario aunque el volumen ya tenga el consultorio.
3. **Vuelta atrás:** `python -m alembic downgrade 0005` quita la tabla `usuario` sin tocar los turnos ni el historial (escenario nuevo de INF-1). Las rutas existentes no dependen de la tabla.

## Open Questions

Ninguna. Las nueve preguntas abiertas de este design las cerró el autor el 2026-10-14 eligiendo la recomendación del agente: límite de peticiones y registro de eventos fuera de C-06 (D195, J19); secreto efímero en la demo y constante ficticia en los tests (D196, J10); `SEED_USUARIO_PASSWORD` desde el entorno en PostgreSQL y una constante con el mismo valor en la demo (D197, J11, J16); `JWT_SECRET` de 32 bytes como mínimo (D198, J10); email sin espacios, en minúsculas y con `UNIQUE` simple (D199, J3); un `401` idéntico por endpoint (D200, J13); el refresh no rota (D201, J9); los roles del seed se asignan en C-07 (D202, J11); y 27 tareas como quinta excepción (D203, J22).

Quedan marcadas «Propuesta», y el autor puede cambiarlas sin tocar el plan: el nombre `sesion-del-panel` (J1), los textos de `detail` y los `type` (J13), los nombres de campo `contrasena` y `refresh_token` (J12), `expires_in` y `Cache-Control` (J12), el email del seed (J11) y las 12 rondas de bcrypt (J10).
