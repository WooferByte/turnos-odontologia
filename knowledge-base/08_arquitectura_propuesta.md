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
| Cola de tareas | Redis + worker | En la v1: preparar recordatorios `wa.me` a `inicio − 24 h`, vencer señas impagas (30 min) y vencer ofertas de lista de espera (2 h) sin bloquear la API. **No envía mensajes**: los envía a mano el odontólogo (DD-06) |
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
└── README.md                    # cómo correr tests sin Postgres ni Redis
```

**Migraciones:** Alembic **no se usa en el primer change**; los tests crean el esquema con `create_all`. **Alembic se usa a partir del change de infraestructura con PostgreSQL** (decisión del autor 2026-10-03, DD-15). Las columnas que el primer change no crea se agregan con migraciones (`04_modelo_de_datos.md`).

## Regla de capas

Los imports son **unidireccionales** y no pueden invertirse (**Suposición** de redacción; la separación en capas es la de DD-02):

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

Verificación mecánica (**Suposición**): un test que recorra los imports de `app/domain` y falle si aparece un módulo prohibido.

## Contrato del primer change

Contrato del change «crear turno sin solapamientos por profesional y por sillón». **Confirmados por el autor (2026-10-03):** el doble conflicto (E4), la forma del error y del cuerpo RFC 7807 con lista de códigos y conflictos, que el filtro de estados activos lo aplica el dominio, que el change **expone `POST /turnos` sin autenticación** y que E12 entra en el spec. Los **nombres exactos** de clases y funciones son una propuesta aceptada por el autor 2026-10-03; se revisa en el design del change. Los escenarios del primer change son E1..E7 y E12 de `06_funcionalidades.md` (US-010).

**Value object y función pura de dominio** (sin I/O, sin base de datos):

```python
@dataclass(frozen=True)
class Intervalo:                     # [inicio, fin) — RN-AG-09
    inicio: datetime                 # aware, UTC (RN-GL-01)
    fin: datetime                    # aware, UTC; inicio < fin (RN-AG-10d)
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
| Cuerpo inválido (formato, `inicio` naive) | `422` | Validación de Pydantic / RN-AG-10d |
| `RecursoNoEncontrado` (E12) | `422` | La referencia viaja en el cuerpo, no en la URL. Código `RN-GL-04` y status: propuesta aceptada por el autor 2026-10-03; se revisa en el design del change (SU-08); un único status para inexistente e inactivo |

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

## Seguridad

- **Autenticación** (change de usuarios y acceso, Épica 10; **el primer change no la tiene**, DD-14): JWT firmado (HS256 con secreto de entorno) para el panel. Propuesta aceptada por el autor 2026-10-03 (SU-09; se revisa en el design del change): access token de 15 minutos y refresh token de 7 días, ambos JWT, sin revocación del refresh en la v1; contraseñas con hash **bcrypt**. Credenciales inválidas → `401` genérico (RN-AU-04).
- **Autorización**: RBAC por rol (`odontologo`, `recepcionista`, `dueno`) vía dependencies de FastAPI; unión de roles. Ficha clínica solo `odontologo`.
- **Paciente**: sin cuenta; **token de gestión firmado** por turno y por oferta de lista de espera, con vencimiento. Nunca datos personales en la URL (RN-PR-06).
- **Webhooks**: verificación de firma del webhook de Mercado Pago y consulta del pago a su API antes de acreditar. El webhook de WhatsApp (verificación de firma de Meta) es **Fase 2**.
- **Validación de input**: modelos Pydantic en todos los endpoints; reglas de negocio en el dominio, no en el router.
- **Datos sensibles (Ley 25.326)**: HTTPS obligatorio fuera de desarrollo; minimización por rol; logs sin datos clínicos ni teléfonos completos (**Suposición**); **datos siempre ficticios** en el repositorio (RN-PR-01).
- **Secrets management**: variables de entorno; `.env` fuera del repositorio; `.env.example` solo con valores de prueba. Nunca tokens reales o de producción de Mercado Pago ni de Meta en el repo.
- **Rate limiting** en rutas públicas de reserva (**Suposición**, para evitar abuso del link).

## Variables de entorno

| Variable | Descripción | Ejemplo | Sensible |
|---|---|---|---|
| `DATABASE_URL` | Conexión SQLAlchemy | `postgresql+psycopg://app:app@db:5432/turnos` (tests: `sqlite+pysqlite:///:memory:`) | Y |
| `REDIS_URL` | Cola de tareas | `redis://redis:6379/0` | N |
| `JWT_SECRET` | Firma de JWT y tokens de gestión | `cambiar-en-local` | Y |
| `JWT_ACCESS_MINUTES` | Vida del access token | `15` | N |
| `JWT_REFRESH_DAYS` | Vida del refresh token | `7` | N |
| `APP_TIMEZONE` | Zona del consultorio | `America/Argentina/Buenos_Aires` | N |
| `PUBLIC_BASE_URL` | Base de los links públicos | `http://localhost:5173` | N |
| `WHATSAPP_MODE` | Canal de mensajería (v1: solo `wa_me`; `cloud_api` en Fase 2) | `wa_me` | N |
| `MP_ACCESS_TOKEN` | Credencial **de prueba** de Mercado Pago | `TEST-...` | Y |
| `MP_WEBHOOK_SECRET` | Validación de notificaciones | `<secret>` | Y |
| `QUEUE_ENABLED` | Permite desactivar Redis en tests | `false` en tests | N |

Los nombres son **propuestos** (**Suposición**); se fijan en el change de infraestructura. Las variables de la Cloud API de Meta (token, id de número, verificación y secreto del webhook) se definen en la Fase 2. `JWT_*` aplican desde el change de usuarios y acceso.

## Estrategia de tests

- **Unit**: funciones puras de dominio (solapamiento, ventanas de cancelación, transiciones de estado). Sin I/O y **sin base de datos**.
- **Integration**: caso de uso con repositorio SQLAlchemy **síncrono** sobre **SQLite en memoria** (`sqlite+pysqlite:///:memory:` con `StaticPool`); la cola se reemplaza por un doble en memoria. **Sin mocks de sesión ni de repositorio** (decisión del autor 2026-10-03, DD-12).
- **API**: `TestClient` de FastAPI con la misma base en memoria (se sustituye la dependencia de sesión por la del test). **El primer change expone `POST /turnos`**, por lo que estos tests son parte del change: verifican el estado HTTP y `codigos` de E1, E4 y E12 como mínimo (propuesta aceptada por el autor 2026-10-03; se revisa en el design del change). La dependencia de test del cliente HTTP se declara en el archivo de dependencias.
- **Sin `aiosqlite` ni `pytest-asyncio`**: el backend del primer change es síncrono (DD-12).
- Comando único documentado en el README (p. ej. `pytest`), sin Docker ni servicios externos. El README debe decir explícitamente que los tests corren con SQLite en memoria (DD-03, confirmada por el autor el 2026-10-02) y fijar las versiones (ver «Versiones y dependencias»).
- La restricción de exclusión de PostgreSQL (si se usa) se testea aparte en un perfil opcional con docker-compose; **no es requisito** para la suite del change.
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
- El **dominio recibe solo datetimes aware en UTC**: `Intervalo` rechaza datetimes naive o con otro offset (E8). La conversión desde `America/Argentina/Buenos_Aires` ocurre en el borde (API o adaptador).
- El **adaptador de persistencia normaliza** lo que lee de la base antes de entregarlo al dominio.
- **Suposición a verificar en el change:** SQLite no conserva la zona horaria y SQLAlchemy puede devolver datetimes naive aunque la columna tenga `timezone=True`; por eso la normalización del adaptador y un test de ida y vuelta (escribir aware UTC, leer aware UTC) son parte del change. PostgreSQL sí conserva el instante.

## Versiones y dependencias

Política (decisión del autor 2026-10-03; **no se inventan números de versión**): 
- **Confirmadas por el autor:** Python 3.11+ y SQLAlchemy 2.x. Las versiones exactas de FastAPI, Pydantic, pytest, PostgreSQL, Redis, React y Vite **no están decididas**.
- **Un único archivo de dependencias** (el que elija el change de infraestructura: `pyproject.toml` o `requirements`), con **versiones exactas** (pins), sin duplicar la lista en otro archivo.
- Los pins se **fijan en el `design.md` del primer change** y se **verifican en un clon limpio** (crear entorno, instalar solo desde ese archivo, correr los tests).
- **Toda dependencia de test está declarada** en ese archivo (pytest y cualquier plugin que use la configuración). Ninguna dependencia queda implícita ni instalada solo en la máquina del autor.
- Sin dependencias del lado async (ver DD-12). Alembic no entra en el primer change.

## Definition of Done del primer change

Checklist verificable (el requisito de fondo es de la consigna y de DD-03; la redacción de los ítems y el uso de `/docs` en el video son decisión del autor 2026-10-03):
- [ ] En un **clon limpio**, siguiendo solo el README, se crea el entorno, se instala desde el único archivo de dependencias y se corre `pytest` sin Docker, PostgreSQL ni Redis.
- [ ] El README dice explícitamente que los tests corren con **SQLite en memoria** y lista las versiones fijadas.
- [ ] `pytest` termina en verde y ejecuta al menos **un test por escenario del primer change (E1..E7 y E12)**; una tabla escenario ↔ test está en el README o en el design.
- [ ] **Se levanta la API** (`uvicorn`, con el comando del README) y `POST /turnos` se prueba desde Swagger en `/docs`: un turno válido devuelve `201`, un solapamiento devuelve `409` con `codigos`, y una referencia inexistente devuelve `422` con `RN-GL-04`.
- [ ] El spec del change tiene al menos 3 escenarios (feliz, error de negocio, borde), con Requirement y Scenario en WHEN/THEN citando RN y E#.
- [ ] El historial TDD muestra primero el test que falla y luego el código (RED → GREEN → TRIANGULATE → REFACTOR por escenario).
- [ ] Ningún test usa mocks de sesión ni de repositorio; ninguna dependencia de test falta en el archivo de dependencias.
- [ ] El test guard de fechas pasa y no hay `datetime.utcnow()` en el código.
- [ ] `openspec validate` del change sin errores y sin archivos de bloqueo residuales (`.openspec-archive.lock`) antes de archivar.
- [ ] No hay datos reales, secretos ni `.env` versionados; `.env.example` solo con valores de prueba (RN-PR-01).
- [ ] El README declara el **límite conocido**: `POST /turnos` va sin autenticación en este change (DD-14).
