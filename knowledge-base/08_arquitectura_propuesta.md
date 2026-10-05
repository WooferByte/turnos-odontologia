# Arquitectura Propuesta

## Patrones aplicados

| Patrón | Dónde se usa | Por qué |
|---|---|---|
| Monolito modular | Backend único con módulos por dominio (agenda, turnos, lista de espera, mensajería, pagos, ficha, privacidad) | Un consultorio, un desarrollador; evita complejidad distribuida (DD-01) |
| Arquitectura en capas / hexagonal liviana | `domain` (reglas puras) ← `application` (casos de uso) ← `api` / `infrastructure` | Las reglas de solapamiento se testean sin base ni framework (DD-02) |
| Repository | `infrastructure/repositories` con SQLAlchemy | Permite cambiar PostgreSQL por SQLite en memoria en tests (DD-03) |
| Value Object `Intervalo [inicio, fin)` | `domain/agenda` | Centraliza la regla de solapamiento semiabierto (RN-AG-09) |
| Errores de dominio con código RN | `domain/errors.py` | Los tests y la API verifican la regla exacta que falló (RN-GL-02) |
| Unit of Work / transacción por caso de uso | `application` | Atomicidad de la validación + inserción (RN-AG-10c) |
| Cola de tareas | Redis + worker (tarea periódica) | En la v1: preparar recordatorios `wa.me` a `inicio − 24 h`, persistir el vencimiento de señas impagas (30 min) y de ofertas de lista de espera (2 h) y disparar los efectos en cadena, sin bloquear la API. **No envía mensajes**: los envía a mano el odontólogo (DD-06). El vencimiento se evalúa al consultar; ver «Vencimientos y tarea periódica» (RN-GL-05) |
| Puerto/adaptador de mensajería | `MensajeriaPort` con `WaMeAdapter` en la v1; `CloudApiAdapter` queda para la Fase 2 | Sumar la Cloud API sin tocar el dominio (DD-06) |
| Idempotencia de webhooks | `webhooks/mercadopago` (v1); `webhooks/whatsapp` (Fase 2) | Notificaciones repetidas no duplican efectos (RN-SP-08) |
| Event log (historial) | `EventoTurno` solo inserción | Trazabilidad (RN-AG-11) |

## Estructura de directorios

```
proyecto/
├── backend/
│   ├── app/
│   │   ├── domain/
│   │   │   ├── agenda/          # Intervalo, solapamiento, horario, bloqueos
│   │   │   ├── turnos/          # Turno, estados, transiciones, EventoTurno
│   │   │   ├── lista_espera/
│   │   │   ├── pagos/           # Sena, RegistroPago
│   │   │   ├── ficha/           # Paciente, Anamnesis, Evolucion, Presupuesto
│   │   │   ├── tiempo.py        # utc_now() y tipo Reloj (DD-13)
│   │   │   └── errors.py        # ErrorDeDominio(codigo="RN-AG-05", ...)
│   │   ├── application/         # casos de uso: crear_turno, reprogramar, cancelar, reservar_publico...
│   │   ├── infrastructure/
│   │   │   ├── db/              # modelos SQLAlchemy, sesión, migraciones
│   │   │   ├── repositories/
│   │   │   ├── messaging/       # wa_me.py (v1); cloud_api.py (Fase 2)
│   │   │   ├── payments/        # mercadopago.py
│   │   │   └── queue/           # productor/consumidor Redis
│   │   ├── api/
│   │   │   ├── routers/         # auth, turnos, agenda, public, webhooks...
│   │   │   └── deps.py          # sesión de DB; auth JWT desde el change de usuarios (DD-14)
│   │   ├── worker.py
│   │   └── main.py
│   ├── tests/
│   │   ├── unit/                # dominio puro (solapamiento, ventanas)
│   │   ├── integration/         # casos de uso + repos con SQLite en memoria
│   │   └── api/                 # endpoints con TestClient
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── features/            # agenda, turnos, reserva-publica, ficha...
│       ├── shared/
│       └── pages/
├── docker-compose.yml           # api, worker, postgres, redis, frontend
├── .env.example                 # solo valores de prueba
└── README.md                    # cómo correr tests sin Postgres ni Redis, y el perfil opcional con PostgreSQL (E11)
```

**Migraciones:** Alembic **no se usa en el primer change**; los tests crean el esquema con `create_all`. **Alembic se usa a partir del change de infraestructura con PostgreSQL** (decisión del autor 2026-10-03, DD-15), que va en el **orden 2, justo después del primer change** (decisión del autor 2026-10-05, D105). Las columnas que el primer change no crea se agregan con migraciones (`04_modelo_de_datos.md`).

**Interfaz (decisión del autor 2026-10-05, D106):** las historias de orden 1 y 2 y el change de infraestructura con PostgreSQL se implementan y se prueban como API (tests de dominio y de API; sin interfaz gráfica). El `frontend/` empieza en el **orden 3**, con el inicio de sesión (Épica 10); la interfaz de las historias de orden 1 y 2 se construye a partir de ahí.

## Regla de capas

Los imports son **unidireccionales** y no pueden invertirse (redacción confirmada por el autor 2026-10-05, D70; la separación en capas es la de DD-02):

```
api → application → domain          infrastructure → domain
(api y infrastructure conocen application/domain; domain no conoce a nadie)
```

| Capa | Responsabilidad | Puede importar |
|---|---|---|
| `domain` | Reglas puras: `Intervalo`, solapamiento, estados, errores de dominio, `utc_now()` | Solo biblioteca estándar |
| `application` | Casos de uso; orquesta repositorio y transacción; lanza errores de dominio | `domain` |
| `infrastructure` | Modelos SQLAlchemy, repositorios, sesión | `domain` (y `application` solo para implementar sus puertos) |
| `api` | HTTP: valida el cuerpo con Pydantic, llama al caso de uso, traduce errores a RFC 7807 | `application`, `domain` |

**Violaciones prohibidas** (decisión del autor 2026-10-03 de adoptar la regla; el texto es del agente):
- `domain` importando FastAPI, Pydantic, SQLAlchemy o cualquier capa superior.
- Lógica de negocio (solapamiento, estados activos, duración) en un router o en un repositorio.
- Un caso de uso o un repositorio que haga `commit()` por su cuenta: la transacción la abre y cierra el límite de la unidad de trabajo.
- Un repositorio o el dominio que lancen excepciones HTTP: el dominio lanza `ErrorDeDominio`; solo `api` conoce los códigos HTTP.
- Un caso de uso que arme consultas SQL directamente: cada consulta es un método del repositorio (por ejemplo, `turnos_que_intersecan(recurso, intervalo)`).
- Tests que sustituyan la sesión o el repositorio por mocks (ver «Estrategia de tests»).

Verificación mecánica (confirmada por el autor 2026-10-05, D70): un test que recorra los imports de `app/domain` y falle si aparece un módulo prohibido.

## Contrato del primer change

Contrato del change «crear turno sin solapamientos por profesional y por sillón». **Confirmados por el autor (2026-10-03):** el doble conflicto (E4), la forma del error y del cuerpo RFC 7807 con lista de códigos y conflictos, que el filtro de estados activos lo aplica el dominio, que el change **expone `POST /turnos` sin autenticación** y que E12 entra en el spec. Los **nombres exactos** de clases y funciones son una propuesta aceptada por el autor 2026-10-03; se revisa en el design del change. Los escenarios del primer change son E1..E7 y E12 de `06_funcionalidades.md` (US-010).

**Value object y función pura de dominio** (sin I/O, sin base de datos):

```python
@dataclass(frozen=True)
class Intervalo:                     # [inicio, fin) — RN-AG-09
    inicio: datetime                 # aware, UTC (RN-GL-01)
    fin: datetime                    # aware, UTC; inicio < fin (RN-AG-10d)
    # RN-AG-10d (D63): misma fecha local del consultorio (zona = dato, p. ej. zoneinfo); fin == 00:00 local es válido
    def se_solapa_con(self, otro: "Intervalo") -> bool:
        return self.inicio < otro.fin and otro.inicio < self.fin

@dataclass(frozen=True)
class TurnoOcupado:                  # lo mínimo que el dominio necesita de un turno existente
    turno_id: int
    intervalo: Intervalo
    estado: EstadoTurno

@dataclass(frozen=True)
class Conflicto:
    codigo: Literal["RN-AG-05", "RN-AG-08"]
    recurso: Literal["profesional", "sillon"]
    recurso_id: int
    turno_id: int                    # turno existente con el que choca

def detectar_conflictos(
    candidato: Intervalo,
    profesional_id: int, ocupados_profesional: Sequence[TurnoOcupado],
    sillon_id: int, ocupados_sillon: Sequence[TurnoOcupado],
) -> tuple[Conflicto, ...]: ...
```

- Solo cuentan los turnos con `estado in ESTADOS_ACTIVOS` (RN-AG-10); el filtro vive en el dominio (decisión del autor 2026-10-03).
- Evalúa RN-AG-05 y RN-AG-08 **por separado** y devuelve **todos** los conflictos: tupla vacía si no hay ninguno; una por recurso en conflicto; **dos** si choca con ambos (E4). Orden estable: profesional primero, luego sillón.
- El bloque muestra solo `inicio` y `fin`: **cómo recibe `Intervalo` la zona del consultorio** para RN-AG-10d (campo, parámetro del constructor o validación aparte) **se fija en el design del primer change**.

**Error de dominio:**

```python
class ErrorDeDominio(Exception):
    codigo: str                      # p. ej. "RN-AG-10d"
    mensaje: str

class ErrorDeSolapamiento(ErrorDeDominio):
    conflictos: tuple[Conflicto, ...]    # 1 o 2 elementos
    @property
    def codigos(self) -> list[str]: ...  # ["RN-AG-05"], ["RN-AG-08"] o ["RN-AG-05", "RN-AG-08"]

class RecursoNoEncontrado(ErrorDeDominio):   # codigo = "RN-GL-04" (E12)
    recurso: Literal["prestacion", "paciente", "profesional", "sillon"]
    recurso_id: int | None               # None si no vino (p. ej. no hay sillón por defecto)
    motivo: Literal["inexistente", "inactivo"]
```

**Caso de uso** (aplicación): `crear_turno(comando: CrearTurnoComando, uow: UnidadDeTrabajo, reloj: Reloj = utc_now) -> Turno`.
- `CrearTurnoComando`: `paciente_id`, `prestacion_id`, `inicio` (aware UTC), `profesional_id` y `sillon_id` opcionales (defaults RN-AG-06).
- **Primero** resuelve los defaults y verifica que prestación, paciente, profesional y sillón existan y estén activos; si no, lanza `RecursoNoEncontrado` (`RN-GL-04`, E12) **sin persistir nada**. Luego calcula `fin`, pide al repositorio los turnos de cada recurso que intersecan el intervalo, llama a `detectar_conflictos`, y si la tupla no está vacía lanza `ErrorDeSolapamiento` **sin persistir nada**. Si no hay conflicto persiste el `Turno` en `reservado` con `creado_en = reloj()` y la unidad de trabajo hace commit.
- No registra `EventoTurno` (change siguiente). La concurrencia (RN-AG-10c) no se resuelve en este change.

**Endpoint** (decisión del autor 2026-10-03): el primer change expone `POST /turnos` con FastAPI, para probarlo desde Swagger (`/docs`) en el video. **Sin autenticación** en el primer change: es un **límite conocido** (DD-14); se protege con JWT en el change de usuarios y acceso (US-092). Sigue sin interfaz gráfica.

**Mapeo a HTTP** (cuerpo `application/problem+json`, RFC 7807):

| Situación | Estado | Notas |
|---|---|---|
| `ErrorDeSolapamiento` (E2, E3, E4, E7) | `409` | Cuerpo abajo |
| Cuerpo inválido (formato, `inicio` naive) o intervalo inválido (por ejemplo, el turno cruza la medianoche del consultorio) | `422` | Validación de Pydantic / error de dominio `RN-AG-10d` |
| `RecursoNoEncontrado` (E12) | `422` | La referencia viaja en el cuerpo, no en la URL. Código `RN-GL-04`; `422` confirmado por el autor 2026-10-05 (D73); un único status para inexistente e inactivo |
| `RecursoNoEncontrado` con el recurso identificado en la URL (por ejemplo, `GET /turnos/{id}` con un id inexistente) | `404` | Distinción confirmada por el autor 2026-10-05 (D73): `404` es para un recurso inexistente **identificado en la URL**; `422` es para una referencia inválida **dentro del cuerpo** (por ejemplo, `prestacion_id` inexistente en `POST /turnos`). No aplica al primer change, que solo expone `POST /turnos`. Los nombres de los campos del cuerpo y del error se fijan en el design |

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

`codigos` es la lista de códigos RN (uno o dos); `conflictos` detalla recurso y turno en conflicto. El valor de `type` (URI relativa) es una propuesta aceptada por el autor 2026-10-03; se revisa en el design del change. Los tests de dominio verifican la tupla de `Conflicto`; los de API, el estado y `codigos`.

Cuerpo para E12 (`422`): igual forma, con `"type": "/errores/recurso-no-encontrado"`, `"title": "Recurso no encontrado"`, `"codigos": ["RN-GL-04"]` y los campos `recurso`, `recurso_id` y `motivo`.

## Vencimientos y tarea periódica (Redis en la v1)

Decisión del autor 2026-10-05 (D80; RN-GL-05):

- **Los vencimientos se evalúan al consultar**: la seña (RN-SP-03) y la oferta de lista de espera (RN-LE-03) se comparan por `vence_en` contra `utc_now()`. El **estado efectivo** (por ejemplo, un turno `pendiente_sena` con la seña vencida no ocupa el horario) **no depende de que haya corrido ninguna tarea**. Por eso **los tests no necesitan Redis**.
- **Una tarea periódica con Redis persiste el estado** (turno a `vencido`, seña a `vencida`, oferta a `vencida`) y **es la única que dispara las notificaciones y los efectos en cadena**: ofrecer el hueco al siguiente de la lista de espera y preparar los recordatorios `wa.me`.
- **Las lecturas nunca persisten ni disparan nada.** Una **escritura cuyo resultado depende del estado efectivo** persiste el vencimiento en su misma transacción, **sin disparar efectos** (decisión del autor 2026-10-05, D92): (a) crear o reprogramar un turno, o aceptar una oferta, sobre un horario ocupado por un turno `pendiente_sena` con la seña vencida (persiste el turno a `vencido` y la seña a `vencida` antes de insertar, para que la restricción de exclusión de PostgreSQL no rechace lo que el dominio aceptó); (b) el webhook de pago que llega con la seña efectivamente vencida (`pendiente` → `vencida` → `devuelta` y el turno a `vencido`, RN-SP-11); (c) aceptar una oferta efectivamente vencida (la persiste como `vencida` y rechaza).
- La tarea detecta los vencimientos ya persistidos por (a), (b) o (c) cuyos efectos todavía no se dispararon. **El mecanismo se fija en el design del change que crea la tarea**; hoy el modelo no tiene ningún campo para eso.
- La tarea verifica `Paciente.acepta_contacto` justo antes de preparar cada mensaje o cada oferta, incluidos los ya programados (RN-PR-07).
- Los estados de `Mensaje` de la v1 son los del modelo (`programado`, `generado_link`, `enviado`) más `descartado` (`04_modelo_de_datos.md`).

## Seguridad

- **Autenticación** (change de usuarios y acceso, Épica 10; **el primer change no la tiene**, DD-14): JWT firmado (HS256 con secreto de entorno) para el panel. Decisión del autor 2026-10-05 (D74; SU-09): access token de 15 minutos y refresh token de 7 días, ambos JWT; el refresh no se revoca de a uno (no hay tabla de tokens) pero se **invalida en bloque por usuario** con el claim `token_version` (se compara en cada petición y en el refresh y se incrementa al desactivar al usuario o al cambiar o restablecer su contraseña; D43); además `activo` se verifica en cada petición y en el refresh (RN-AU-04); contraseñas con hash **bcrypt**, de **10 caracteres como mínimo y 72 bytes como máximo** (el tope de bcrypt; RN-AU-07). Credenciales inválidas → `401` genérico (RN-AU-04).
- **Autorización**: RBAC por rol (`odontologo`, `recepcionista`, `dueno`) vía dependencies de FastAPI; unión de roles. Los roles se leen de la base en cada petición: quitar un rol tiene efecto inmediato (RN-AU-02, D102). Ficha clínica solo `odontologo`.
- **Paciente**: sin cuenta; **token de gestión firmado** por turno (**sin vencimiento propio**: su validez sale del estado del turno, RN-TD-08) y por oferta de lista de espera (válido hasta el `vence_en` de la oferta); la entrada de lista de espera tiene además su propio token para retirarse (`EntradaListaEspera.token`, D29). **Todo turno tiene token, también el cargado desde el panel** (D94); el link se entrega en la respuesta de la reserva y, desde US-030, en los mensajes `wa.me` (D93). Nunca datos personales en la URL (RN-PR-06).
- **Webhooks**: verificación de firma del webhook de Mercado Pago y consulta del pago a su API antes de acreditar. El webhook de WhatsApp (verificación de firma de Meta) es **Fase 2**.
- **Validación de input**: modelos Pydantic en todos los endpoints; reglas de negocio en el dominio, no en el router.
- **Datos sensibles (Ley 25.326)**: HTTPS obligatorio fuera de desarrollo; minimización por rol; logs sin datos clínicos ni teléfonos completos (**requisito**, confirmado por el autor 2026-10-05, D70); **datos siempre ficticios** en el repositorio (RN-PR-01).
- **Secrets management**: variables de entorno; `.env` fuera del repositorio; `.env.example` solo con valores de prueba. Nunca tokens reales o de producción de Mercado Pago ni de Meta en el repo.
- **Rate limiting** (límite de peticiones) en las rutas públicas de reserva, para evitar abuso del link: **requisito** confirmado por el autor 2026-10-05 (D70); los valores se fijan en el change de reserva pública.

## Variables de entorno

| Variable | Descripción | Ejemplo | Sensible |
|---|---|---|---|
| `DATABASE_URL` | Conexión SQLAlchemy | `postgresql+psycopg://app:app@db:5432/turnos` (tests: `sqlite+pysqlite:///:memory:`) | Y |
| `REDIS_URL` | Cola de tareas | `redis://redis:6379/0` | N |
| `JWT_SECRET` | Firma de JWT y tokens de gestión | `cambiar-en-local` | Y |
| `JWT_ACCESS_MINUTES` | Vida del access token | `15` | N |
| `JWT_REFRESH_DAYS` | Vida del refresh token | `7` | N |
| `APP_TIMEZONE` | Zona por defecto con la que el seed carga `Consultorio.zona_horaria`; **la fuente de verdad es la columna** (RN-AG-10d) | `America/Argentina/Buenos_Aires` | N |
| `PUBLIC_BASE_URL` | Base de los links públicos | `http://localhost:5173` | N |
| `WHATSAPP_MODE` | Canal de mensajería (v1: solo `wa_me`; `cloud_api` en Fase 2) | `wa_me` | N |
| `MP_ACCESS_TOKEN` | Credencial **de prueba** de Mercado Pago | `TEST-...` | Y |
| `MP_WEBHOOK_SECRET` | Validación de notificaciones | `<secret>` | Y |
| `QUEUE_ENABLED` | Permite levantar la API sin la tarea periódica (los tests no usan Redis, RN-GL-05) | `false` en tests | N |

Los nombres son **propuestos** y se toman como requisito (confirmado por el autor 2026-10-05, D70); los nombres definitivos se fijan en el change de infraestructura. Las variables de la Cloud API de Meta (token, id de número, verificación y secreto del webhook) se definen en la Fase 2. `JWT_*` aplican desde el change de usuarios y acceso.

## Estrategia de tests

- **Unit**: funciones puras de dominio (solapamiento, ventanas de cancelación, transiciones de estado). Sin I/O y **sin base de datos**.
- **Integration**: caso de uso con repositorio SQLAlchemy **síncrono** sobre **SQLite en memoria** (`sqlite+pysqlite:///:memory:` con `StaticPool`); no hay cola en los tests: la lógica de la tarea periódica se prueba llamándola directamente (RN-GL-05). **Sin mocks de sesión ni de repositorio** (decisión del autor 2026-10-03, DD-12).
- **API**: `TestClient` de FastAPI con la misma base en memoria (se sustituye la dependencia de sesión por la del test). **El primer change expone `POST /turnos`**, por lo que estos tests son parte del change: verifican el estado HTTP y `codigos` de E1, E4 y E12 como mínimo (propuesta aceptada por el autor 2026-10-03; se revisa en el design del change). La dependencia de test del cliente HTTP se declara en el archivo de dependencias.
- **Sin `aiosqlite` ni `pytest-asyncio`**: el backend del primer change es síncrono (DD-12).
- Comando único documentado en el README (p. ej. `pytest`), sin Docker ni servicios externos. El README debe decir explícitamente que los tests corren con SQLite en memoria (DD-03, confirmada por el autor el 2026-10-02) y fijar las versiones (ver «Versiones y dependencias»).
- **Perfil opcional con PostgreSQL** (decisión del autor 2026-10-05, D75): la restricción de exclusión (que se agrega en PostgreSQL **además** de la validación de dominio) y la prueba de reservas simultáneas (**E11**) se corren **solo** en este perfil, **fuera de la suite por defecto** (que usa SQLite en memoria, DD-03). Los tests de E11 llevan un marcador de pytest (por ejemplo, `postgres`) que la suite por defecto excluye; se corren levantando PostgreSQL con Docker Compose y ejecutando pytest con ese marcador. El comando exacto se fija en el change de infraestructura y **debe figurar en el README**. **No es requisito** para la suite del primer change. El SQL de la restricción (por ejemplo, la extensión `btree_gist`) queda para el design del change de infraestructura con PostgreSQL.
- **Sin Redis en los tests**: los vencimientos se evalúan al consultar (RN-GL-05), así que ningún test necesita Redis; la lógica de la tarea periódica (persistir vencimientos, ofrecer huecos, preparar mensajes) se prueba llamando a su función directamente.
- **Un test por escenario del spec**, con el ID en el nombre o el docstring (`test_e4_doble_conflicto`). TDD estricto: primero el test que falla, luego el mínimo código.

### Fixtures de test (decisión del autor 2026-10-03 de adoptar la estrategia; detalles propuestos por el agente)

- **Engine por test**: cada test crea su engine SQLite en memoria con `StaticPool` (para que todas las conexiones vean la misma base), ejecuta `create_all`, y lo descarta (`dispose`) al terminar. **Aislamiento total**: no hay base ni seed compartidos entre tests.
- **Sesión por test**, abierta sobre ese engine y cerrada al final. Los ajustes exactos de conexión se fijan en el `design.md`.
- **Factories de datos**: funciones pequeñas (`un_profesional()`, `un_sillon()`, `una_prestacion(duracion_minutos=30)`, `un_turno(estado=..., inicio=..., fin=...)`) que construyen datos **ficticios** (RN-PR-01) con valores por defecto válidos y permiten sobreescribir solo lo que el escenario necesita.
- **Tests de dominio sin fixtures de base**: construyen `Intervalo` y `TurnoOcupado` en memoria. Casos de intervalos en una tabla parametrizada (contiguo antes y después, un minuto de solape, contenido, idéntico).
- **Reloj fijo** inyectado en el caso de uso (`reloj=lambda: FECHA_FIJA`) para que los tests sean deterministas.
- **Test guard de fechas**: recorre los metadatos del esquema y exige que toda columna de fecha-hora tenga zona (DD-13).

## Reloj y zonas horarias (DD-13)

- Un único `utc_now()` en `domain/tiempo.py` devuelve un datetime aware en UTC. Está prohibido `datetime.utcnow()` y `datetime.now()` sin zona.
- Los casos de uso reciben el reloj como parámetro (`reloj: Reloj = utc_now`), por lo que los tests lo reemplazan.
- El **dominio recibe solo datetimes aware en UTC**: `Intervalo` rechaza datetimes naive o con otro offset (E8). La conversión desde `America/Argentina/Buenos_Aires` ocurre en el borde (API o adaptador). **Única excepción** (RN-AG-10d, decisión del autor 2026-10-05, D63): para verificar que un turno no cruce la medianoche, `Intervalo` recibe la **zona del consultorio** (`Consultorio.zona_horaria`) como dato y convierte `inicio` y `fin` a esa zona solo para esa comprobación; el instante guardado sigue siendo UTC. La zona entra como parámetro, no se lee de la configuración dentro del dominio.
- El **adaptador de persistencia normaliza** lo que lee de la base antes de entregarlo al dominio.
- **A verificar en el change** (verificar antes de cerrar el primer change; decisión del autor 2026-10-05, D85): SQLite no conserva la zona horaria y SQLAlchemy puede devolver datetimes naive aunque la columna tenga `timezone=True`; por eso la normalización del adaptador y un test de ida y vuelta (escribir aware UTC, leer aware UTC) son parte del change. PostgreSQL sí conserva el instante.

## Versiones y dependencias

Política (decisión del autor 2026-10-03; **no se inventan números de versión**): 
- **Confirmadas por el autor:** Python 3.11+ y SQLAlchemy 2.x. Las versiones exactas de FastAPI, Pydantic, pytest, PostgreSQL, Redis, React y Vite **no están decididas**.
- **Un único archivo de dependencias** (el que elija el change de infraestructura: `pyproject.toml` o `requirements`), con **versiones exactas** (pins), sin duplicar la lista en otro archivo (criterio fijado por el autor el 2026-10-05, D72).
- Los pins se **fijan en el `design.md` del primer change** (las versiones se consultan ese día; hoy solo se fija el criterio) y se **verifican en un clon limpio** (crear entorno, instalar solo desde ese archivo, correr los tests).
- **Toda dependencia de test está declarada** en ese archivo (pytest y cualquier plugin que use la configuración). Ninguna dependencia queda implícita ni instalada solo en la máquina del autor.
- Sin dependencias del lado async (ver DD-12). Alembic no entra en el primer change.

## Definition of Done del primer change

Checklist verificable (el requisito de fondo es de la consigna y de DD-03; la redacción de los ítems y el uso de `/docs` en el video son decisión del autor 2026-10-03):
- [ ] En un **clon limpio**, siguiendo solo el README, se crea el entorno, se instala desde el único archivo de dependencias y se corre `pytest` sin Docker, PostgreSQL ni Redis.
- [ ] El README dice explícitamente que los tests corren con **SQLite en memoria** y lista las versiones fijadas.
- [ ] `pytest` termina en verde y ejecuta al menos **un test por escenario del primer change (E1..E7 y E12)**; una tabla escenario ↔ test está en el README o en el design.
- [ ] **Se levanta la API** (`uvicorn`, con el comando del README) y `POST /turnos` se prueba desde Swagger en `/docs`: un turno válido devuelve `201`, un solapamiento devuelve `409` con `codigos`, y una referencia inexistente devuelve `422` con `RN-GL-04`. Qué base usa la demo sin PostgreSQL y cómo se cargan sus datos ficticios **se fija en el design del change** (los tests usan una base en memoria por test, sin seed compartido).
- [ ] El spec del change tiene al menos 3 escenarios (feliz, error de negocio, borde), con Requirement y Scenario en WHEN/THEN citando RN y E#.
- [ ] El historial TDD muestra primero el test que falla y luego el código (RED → GREEN → TRIANGULATE → REFACTOR por escenario).
- [ ] Ningún test usa mocks de sesión ni de repositorio; ninguna dependencia de test falta en el archivo de dependencias.
- [ ] El test guard de fechas pasa y no hay `datetime.utcnow()` en el código.
- [ ] El **test de ida y vuelta de fechas** pasa: se escribe un datetime aware en UTC y se lee aware en UTC con SQLite (DD-13, D85).
- [ ] El **test de imports de `app/domain`** pasa (regla de capas, D70).
- [ ] `openspec validate` del change sin errores y sin archivos de bloqueo residuales (`.openspec-archive.lock`) antes de archivar.
- [ ] No hay datos reales, secretos ni `.env` versionados; `.env.example` solo con valores de prueba (RN-PR-01).
- [ ] El README declara el **límite conocido**: `POST /turnos` va sin autenticación en este change (DD-14).
