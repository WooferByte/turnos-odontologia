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
│   │   ├── api/                 # endpoints con TestClient
│   │   └── postgres/            # perfil opcional con PostgreSQL (marcador `postgres`; C-02, D149)
│   ├── pyproject.toml           # archivo único: dependencias y configuración de pytest (D137)
│   ├── alembic.ini              # configuración de Alembic, sin URL ni credenciales (D147)
│   └── Dockerfile               # dos etapas (D151)
├── frontend/                # desde C-08 (F4 del design de ese change)
│   ├── package.json             # archivo único del frontend, versiones exactas (D217)
│   ├── package-lock.json        # generado con npm install --before=2026-10-12
│   ├── .npmrc                   # save-exact=true, engine-strict=true
│   ├── tsconfig.json            # strict, noEmit
│   ├── vite.config.ts           # plugin de React, proxy /api, configuración de Vitest
│   ├── index.html
│   ├── Dockerfile, nginx.conf, .dockerignore
│   └── src/
│       ├── main.tsx, App.tsx    # rutas del panel (ingreso y panel base)
│       ├── shared/api/          # clienteHttp, sesion, errores
│       ├── features/ingreso/    # pantalla de inicio de sesión
│       ├── features/usuarios/    # pantalla de usuarios (C-09)
│       ├── pages/               # panel base y rutas protegidas
│       └── test/                # servidor falso de la API para las pruebas
├── docker-compose.yml           # api, worker, postgres, redis, frontend (C-02 crea api y postgres, D151)
├── docker/postgres-init/        # 01_base_de_tests.sql: crea `turnos_test` (D149)
├── .env.example                 # solo valores de prueba
└── README.md                    # cómo correr tests sin Postgres ni Redis, y el perfil opcional con PostgreSQL (E11)
```

**Ubicación del código (decisión del autor 2026-10-07, D122):** el código vive en `backend/app` y los tests en `backend/tests`; el archivo único de dependencias es `backend/pyproject.toml` (decisión del autor 2026-10-07, D137; antes su formato quedaba para el design), y el `README.md` va en la raíz del repositorio. **Por qué `backend/` y no el `src/` de la estructura mínima de la consigna:** la consigna aclara que los nombres pueden variar; el frontend de React llega en la fase 3 como carpeta hermana (`frontend/`), y una raíz `backend/` mantiene separados los dos desde el primer día; este archivo ya usaba esa estructura. **Consecuencias:** el README dice desde qué directorio se instala y se corre `pytest`; toda referencia a `app/domain` en `openspec/config.yaml` y en `CLAUDE.md` / `AGENTS.md` significa `backend/app/domain`.

**Migraciones:** Alembic **no se usa en el primer change**; los tests crean el esquema con `create_all`. **Alembic se usa a partir del change de infraestructura con PostgreSQL** (decisión del autor 2026-10-03, DD-15), que va en el **orden 2, justo después del primer change** (decisión del autor 2026-10-05, D105). Las columnas que el primer change no crea se agregan con migraciones (`04_modelo_de_datos.md`). **Aplicado en C-02 (2026-10-13):** las migraciones viven en `backend/app/infrastructure/db/migraciones/` (revisiones `0001_esquema_inicial` y `0002_exclusion_de_solapamientos`), son solo para PostgreSQL y la suite por defecto sigue con `create_all` (D145); la configuración está en `backend/alembic.ini` (D147); los nombres de claves y restricciones `UNIQUE` siguen una convención fija (D146).

**Interfaz (decisión del autor 2026-10-05, D106):** las historias de orden 1 y 2 y el change de infraestructura con PostgreSQL se implementan y se prueban como API (tests de dominio y de API; sin interfaz gráfica). El `frontend/` empieza en el **orden 3**, con el inicio de sesión (Épica 10); la interfaz de las historias de orden 1 y 2 se construye a partir de ahí. **Mismo origen (decisión del autor 2026-10-19, D220):** desde C-08 la interfaz llama a la API con el prefijo `/api` (proxy de Vite en desarrollo y de nginx en Compose), sin CORS ni cambios de API.

## Regla de capas

Los imports son **unidireccionales** y no pueden invertirse (redacción confirmada por el autor 2026-10-05, D70; la separación en capas es la de DD-02):

```
api → application → domain          infrastructure → domain
(api y infrastructure conocen application/domain; domain no conoce a nadie)
```

| Capa | Responsabilidad | Puede importar |
|---|---|---|
| `domain` | Reglas puras: `Intervalo`, solapamiento, estados, errores de dominio, `utc_now()` | Solo biblioteca estándar (incluida `zoneinfo`, D132) |
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

Verificación mecánica (confirmada por el autor 2026-10-05, D70): un test que recorra los imports de `backend/app/domain` y falle si aparece un módulo prohibido. El conjunto permitido es la biblioteca estándar, que incluye `zoneinfo`; el paquete de datos de zonas (`tzdata`) se declara como dependencia pero el dominio **no lo importa** (decisión del autor 2026-10-07, D132).

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
    turno_id: int                    # turno existente con el que choca; si son varios del mismo recurso, el que empieza primero (D129)

def detectar_conflictos(
    candidato: Intervalo,
    profesional_id: int, ocupados_profesional: Sequence[TurnoOcupado],
    sillon_id: int, ocupados_sillon: Sequence[TurnoOcupado],
) -> tuple[Conflicto, ...]: ...
```

- Solo cuentan los turnos con `estado in ESTADOS_ACTIVOS` (RN-AG-10); el filtro vive en el dominio (decisión del autor 2026-10-03).
- Evalúa RN-AG-05 y RN-AG-08 **por separado** y devuelve **todos** los conflictos: tupla vacía si no hay ninguno; una por recurso en conflicto; **dos** si choca con ambos (E4). Orden estable: profesional primero, luego sillón. **Un `Conflicto` por recurso, con el turno existente que empieza primero** (menor `inicio`) si el candidato choca con más de uno del mismo recurso (decisión del autor 2026-10-07, D129); no hay empate posible, porque los turnos activos de un mismo recurso no se solapan entre sí (RN-AG-05, RN-AG-08).
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

@dataclass(frozen=True)
class ReferenciaInvalida:
    recurso: Literal["prestacion", "paciente", "profesional", "sillon"]
    recurso_id: int | None               # None si no vino y no hay un único activo por defecto (RN-AG-14)
    motivo: Literal["inexistente", "inactivo"]   # RN-AG-14 suma valores para «ninguno activo» y «varios activos»: nombres en el design
                                                 # un paciente solo puede ser "inexistente" (D136)

class RecursoNoEncontrado(ErrorDeDominio):   # codigo = "RN-GL-04" (E12)
    referencias: tuple[ReferenciaInvalida, ...]   # TODAS las inválidas de la petición, 1 o más (D127)

class FechaNoUTC(ErrorDeDominio): ...        # codigo = "RN-GL-01" (D128)

class EntradaInvalida(ErrorDeDominio):       # validación de entrada: se informa todo junto (RN-GL-02, D135)
    errores: tuple[ErrorDeDominio, ...]      # FechaNoUTC y/o RecursoNoEncontrado; 1 o 2
    @property
    def codigos(self) -> list[str]: ...      # ["RN-GL-01"], ["RN-GL-04"] o ["RN-GL-01", "RN-GL-04"]
```

**Propuesta** (la forma exacta se **fija en el design** del primer change): hasta el 2026-10-06 este contrato modelaba un único recurso (`recurso`, `recurso_id`, `motivo` en el propio error). Desde la decisión del autor 2026-10-07 (D127) el error lista **todas** las referencias inválidas de la petición, así que la lista `referencias` reemplaza a esos tres campos. Un id de otro consultorio cuenta como `inexistente` (D126). Desde D135 el caso de uso no lanza `RecursoNoEncontrado` ni `FechaNoUTC` sueltos: los reúne en `EntradaInvalida`, que es el único error de validación de entrada que sale del caso de uso (**Propuesta**: nombre y forma se fijan en el design). `Intervalo` sigue lanzando `FechaNoUTC` por su cuenta cuando se lo construye con una fecha inválida (E8).

**Caso de uso** (aplicación): `crear_turno(comando: CrearTurnoComando, uow: UnidadDeTrabajo, reloj: Reloj = utc_now) -> Turno`.
- `CrearTurnoComando`: `paciente_id`, `prestacion_id`, `inicio` (aware UTC), `profesional_id` y `sillon_id` opcionales (si faltan, el único activo del consultorio: RN-AG-14, D125; si no hay uno solo, `RN-GL-04`). El comando no lleva `consultorio_id`: sale del profesional (D126).
- **Orden de evaluación (RN-GL-02, decisión del autor 2026-10-07, D135).** El caso de uso tiene dos fases y la segunda solo corre si la primera no encontró nada:
  1. **Validación de entrada, todo junto.** Verifica que `inicio` sea aware en UTC (`RN-GL-01`), resuelve los defaults (RN-AG-14) y verifica que prestación, profesional y sillón existan, estén activos y pertenezcan al consultorio del profesional, y que el paciente exista y sea de ese consultorio (D126, D136). Reúne **todos** los problemas; si hay alguno, lanza `EntradaInvalida` con los códigos que correspondan (`RN-GL-01` y/o `RN-GL-04`, este con la lista completa de referencias, D127) **sin persistir nada**. Lo que no se puede evaluar porque otro dato es inválido no se informa.
  2. **Reglas de negocio, de a una.** Calcula `fin` y construye el `Intervalo`: si cruza la medianoche del consultorio lanza el error de `RN-AG-10d` y termina. Si no, pide al repositorio los turnos de cada recurso que intersecan el intervalo y llama a `detectar_conflictos`; si la tupla no está vacía lanza `ErrorDeSolapamiento` (una regla, uno o dos códigos; E4) **sin persistir nada**.
- Si nada falla, persiste el `Turno` en `reservado` con `creado_en = reloj()` y la unidad de trabajo hace commit.
- No registra `EventoTurno` en C-01 (**desde C-03 sí:** registra el evento `creado` dentro del mismo intento y de la misma transacción, con `actor: Actor` opcional que por defecto es `usuario` sin id hasta C-07; D159, D165). La concurrencia (RN-AG-10c) no se resuelve en este change.

**Endpoint** (decisión del autor 2026-10-03): el primer change expone `POST /turnos` con FastAPI, para probarlo desde Swagger (`/docs`) en el video. **Sin autenticación** en el primer change: es un **límite conocido** (DD-14); se protege con JWT en el change de usuarios y acceso (US-092). Sigue sin interfaz gráfica. **Desde C-07 (`roles-y-proteccion-del-panel`) la excepción ya no vale**: todas las rutas del panel exigen JWT y rol (D214).

**Demo con Swagger** (decisión del autor 2026-10-07, D124): la API que se levanta para la prueba manual usa SQLite en memoria con datos ficticios cargados al arrancar; los identificadores son **fijos** y el README los documenta con un ejemplo de petición. **Límite:** son datos de demo, un reinicio los restablece y no se agregan endpoints de lectura para esto. El comando de arranque y el módulo de entrada se fijan en el design.

**Mapeo a HTTP** (cuerpo `application/problem+json`, RFC 7807). La columna «Clase» es la de RN-GL-02 (D135):

| Situación | Clase | Estado | Notas |
|---|---|---|---|
| `ErrorDeSolapamiento` (E2, E3, E4, E7) | Regla de negocio | `409` | Cuerpo abajo. Una regla que mira dos recursos: uno o dos códigos |
| El turno cruza la medianoche del consultorio | Regla de negocio (**Propuesta**, D135) | `422` | Error de dominio `RN-AG-10d`. Se evalúa antes del solapamiento y, si falla, es el único código |
| `EntradaInvalida`: referencias inválidas (E12), `inicio` sin zona o con un desfase distinto de UTC, o las dos cosas | Validación de entrada | `422` | **Un único `422` con todos los problemas** (D135): `codigos` lleva `RN-GL-04` (D73, D127; un único status para inexistente e inactivo), `RN-GL-01` (D128) o los dos. La referencia viaja en el cuerpo, no en la URL |
| Cuerpo inválido de formato (campo ausente, tipo erróneo, campo de más) | Validación de entrada | `422` | Validación de Pydantic, adaptada al **mismo cuerpo** del `422` de entrada, sin código RN. Si el cuerpo no se puede leer como petición no se evalúan referencias ni fecha (D135). La forma exacta se fija en el design |
| Recurso identificado en la URL que no existe (por ejemplo, `GET /turnos/{id}` con un id inexistente) | Validación de entrada | `404` | Distinción confirmada por el autor 2026-10-05 (D73): `404` es para un recurso inexistente **identificado en la URL**; `422` es para una referencia inválida **dentro del cuerpo** (por ejemplo, `prestacion_id` inexistente en `POST /turnos`). No aplica al primer change, que solo expone `POST /turnos`; lo usan después `GET /turnos/{id}/historial` (C-03), `PATCH /prestaciones/{id}` (C-04) y `PATCH /sillones/{id}` (C-05), con la clase base `RecursoDeLaUrlNoEncontrado` (D188). Los nombres de los campos del cuerpo y del error se fijan en el design |
| Duración de una prestación que no es mayor que 0 ni múltiplo de la granularidad (`POST /prestaciones`, `PATCH /prestaciones/{id}`) | Validación de entrada | `422` | Error de dominio `RN-AG-01` dentro de `EntradaInvalida`, con el error del campo `duracion_minutos` (C-04, D177). Se evalúa después del `404` de la URL y antes del nombre repetido |
| Nombre de prestación repetido en el consultorio | Regla de negocio | `409` | Error de dominio `RN-AG-15`, `type` `/errores/nombre-repetido` (C-04, D171, D177). Se evalúa solo con la entrada válida |

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

Cuerpo del `422` de validación de entrada (E12, fecha inválida, formato): igual forma, con `codigos` (para E12, `["RN-GL-04"]`: un solo código aunque haya varias referencias inválidas; `["RN-GL-01", "RN-GL-04"]` si además la fecha es inválida) y, para `RN-GL-04`, una lista con un elemento por referencia inválida, cada uno con `recurso`, `recurso_id` y `motivo` (D127). **Confirmado por el autor (2026-10-07, D139):** un único valor de `type` (`/errores/entrada-invalida`) para toda la validación de entrada, en lugar del `/errores/recurso-no-encontrado` que figuraba acá, porque un mismo `422` puede reunir problemas de varias clases; los nombres de las listas de detalle y los ejemplos completos están en el design.

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
| `DATABASE_URL` | Conexión SQLAlchemy; la leen la API (`crear_app_desde_entorno`), Alembic y la carga del seed; **obligatoria**: si falta, `ConfiguracionInvalida` y no cae a SQLite (D148) | Dentro de Compose, `postgresql+psycopg://app:app@postgres:5432/turnos` (el servicio se llama `postgres`, no `db`; la arma `docker-compose.yml` desde las `POSTGRES_*`); desde el host, `postgresql+psycopg://app:app@127.0.0.1:5434/turnos` (D153, D154). **La suite por defecto no lee ninguna variable**: usa `sqlite+pysqlite:///:memory:` por código (D148) | Y |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Credenciales y base que crea la imagen oficial de PostgreSQL y que lee `docker-compose.yml` (los nombres los exige la imagen; C-02, D150) | `app`, `app`, `turnos` | Y |
| `TEST_DATABASE_URL` | Base del perfil opcional `postgres` de pytest; el nombre de la base tiene que terminar en `_test` porque el perfil borra y recrea su esquema `public` (C-02, D149, D150) | `postgresql+psycopg://app:app@127.0.0.1:5434/turnos_test` | Y |
| `REDIS_URL` | Cola de tareas | `redis://redis:6379/0` | N |
| `JWT_SECRET` | Firma de JWT y tokens de gestión | `cambiar-en-local` | Y |
| `JWT_ACCESS_MINUTES` | Vida del access token | `15` | N |
| `JWT_REFRESH_DAYS` | Vida del refresh token | `7` | N |
| `APP_TIMEZONE` | Zona por defecto con la que el seed carga `Consultorio.zona_horaria`; **la fuente de verdad es la columna** (RN-AG-10d). **No se lee todavía**: el seed tiene escrita `America/Argentina/Buenos_Aires` (D150) | `America/Argentina/Buenos_Aires` | N |
| `PUBLIC_BASE_URL` | Base de los links públicos | `http://127.0.0.1:5173` | N |
| `WHATSAPP_MODE` | Canal de mensajería (v1: solo `wa_me`; `cloud_api` en Fase 2) | `wa_me` | N |
| `MP_ACCESS_TOKEN` | Credencial **de prueba** de Mercado Pago | `TEST-...` | Y |
| `MP_WEBHOOK_SECRET` | Validación de notificaciones | `<secret>` | Y |
| `QUEUE_ENABLED` | Permite levantar la API sin la tarea periódica (los tests no usan Redis, RN-GL-05) | `false` en tests | N |

Los nombres son **propuestos** y se toman como requisito (confirmado por el autor 2026-10-05, D70); los nombres definitivos se fijaron en el change de infraestructura (C-02, 2026-10-13, D150): se confirman los once de esta tabla y se agregan `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` y `TEST_DATABASE_URL`. `.env.example` trae solo las variables que algún código lee hoy; Python no lee `.env` (lo lee Compose). Las URLs que se usan desde el host llevan `127.0.0.1` y no `localhost` (D154). Las variables de la Cloud API de Meta (token, id de número, verificación y secreto del webhook) se definen en la Fase 2. `JWT_*` aplican desde el change de usuarios y acceso.

## Estrategia de tests

- **Unit**: funciones puras de dominio (solapamiento, ventanas de cancelación, transiciones de estado). Sin I/O y **sin base de datos**.
- **Integration**: caso de uso con repositorio SQLAlchemy **síncrono** sobre **SQLite en memoria** (`sqlite+pysqlite:///:memory:` con `StaticPool`); no hay cola en los tests: la lógica de la tarea periódica se prueba llamándola directamente (RN-GL-05). **Sin mocks de sesión ni de repositorio** (decisión del autor 2026-10-03, DD-12).
- **API**: `TestClient` de FastAPI con la misma base en memoria (se sustituye la dependencia de sesión por la del test). **El primer change expone `POST /turnos`**, por lo que estos tests son parte del change: verifican el estado HTTP y `codigos` de E1, E4 y E12 como mínimo (propuesta aceptada por el autor 2026-10-03; se revisa en el design del change). La dependencia de test del cliente HTTP se declara en el archivo de dependencias.
- **Sin `aiosqlite` ni `pytest-asyncio`**: el backend es síncrono en todos los changes (DD-12, ampliada por D119).
- Comando único documentado en el README (p. ej. `pytest`), sin Docker ni servicios externos. El README debe decir explícitamente que los tests corren con SQLite en memoria (DD-03, confirmada por el autor el 2026-10-02) y fijar las versiones (ver «Versiones y dependencias»).
- **Perfil opcional con PostgreSQL** (decisión del autor 2026-10-05, D75): la restricción de exclusión (que se agrega en PostgreSQL **además** de la validación de dominio) y la prueba de reservas simultáneas (**E11**) se corren **solo** en este perfil, **fuera de la suite por defecto** (que usa SQLite en memoria, DD-03). Los tests de E11 llevan un marcador de pytest (por ejemplo, `postgres`) que la suite por defecto excluye; se corren levantando PostgreSQL con Docker Compose y ejecutando pytest con ese marcador. El comando exacto se fija en el change de infraestructura y **debe figurar en el README**. **No es requisito** para la suite del primer change. El SQL de la restricción (por ejemplo, la extensión `btree_gist`) queda para el design del change de infraestructura con PostgreSQL. **Fijado en C-02 (2026-10-13, D145 y D149):** marcador `postgres` excluido por `-m "not postgres"` en `addopts`; se corre con `python -m pytest -m postgres` y `TEST_DATABASE_URL` definida; si PostgreSQL no está disponible el perfil se omite sin fallar; el esquema sale siempre de las migraciones; E11 se prueba forzando la carrera (D149) y la serialización por recurso de `crear_turno` (D157) se prueba también acá.
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
- El **dominio recibe solo datetimes aware en UTC**: `Intervalo` rechaza datetimes naive o con otro offset (E8) con el código `RN-GL-01` (decisión del autor 2026-10-07, D128). La conversión desde `America/Argentina/Buenos_Aires` ocurre en el borde (API o adaptador). **Única excepción** (RN-AG-10d, decisión del autor 2026-10-05, D63): para verificar que un turno no cruce la medianoche, `Intervalo` recibe la **zona del consultorio** (`Consultorio.zona_horaria`) como dato y convierte `inicio` y `fin` a esa zona solo para esa comprobación; el instante guardado sigue siendo UTC. La zona entra como parámetro, no se lee de la configuración dentro del dominio.
- El **adaptador de persistencia normaliza** lo que lee de la base antes de entregarlo al dominio.
- **A verificar en el change** (verificar antes de cerrar el primer change; decisión del autor 2026-10-05, D85): SQLite no conserva la zona horaria y SQLAlchemy puede devolver datetimes naive aunque la columna tenga `timezone=True`; por eso la normalización del adaptador y un test de ida y vuelta (escribir aware UTC, leer aware UTC) son parte del change. PostgreSQL sí conserva el instante.

## Versiones y dependencias

Política (decisión del autor 2026-10-03; **no se inventan números de versión**; precisada el 2026-10-07, D133 y D137):
- **Confirmadas por el autor:** Python 3.11+; SQLAlchemy de la **serie 2.0.x** (no la 2.1: «2.x» en esta KB significa la línea 2.0, con su API declarativa tipada); FastAPI de la **serie 0.115.x**; Pydantic, una versión compatible con ese FastAPI. Las versiones exactas de pytest, Redis, React y Vite **no están decididas**. PostgreSQL quedó fijado en C-02: **17.10** (D143).
- **Antigüedad mínima de un pin** (D133): **ninguna versión publicada en la semana anterior al día del design**. Si la más nueva de un paquete es tan reciente, se toma la más nueva publicada antes, dentro de la serie permitida. Motivo: una versión de pocos días no tiene recorrido, y el design no instala nada para probarla. Vale para el design del primer change y para el de cada change que agregue dependencias.
- **Un archivo de dependencias por subproyecto** (decisión del autor 2026-10-19, D217; amplía D137): la API sigue en `backend/pyproject.toml`; el frontend tiene `frontend/package.json` con versiones exactas y su `package-lock.json`, generado con `npm install --before=2026-10-12` e instalado con `npm ci`. Versiones del frontend fijadas en C-08: Node 24 LTS (24.21.0 en la imagen de construcción; D223), React 19.3.0, React Router 7.18.4 y TypeScript 6.0.3 (D224), Vite 8.3.4, Vitest 5.0.3 y jsdom 30.1.2 (Propuesta, F3 del design). Imágenes: `node:24.21.0-bookworm-slim` y `nginxinc/nginx-unprivileged:1.30.4-alpine` (D144, D221).
- **Un único archivo de dependencias: `backend/pyproject.toml`** (decisión del autor 2026-10-07, D137; D116 dejaba la elección al design), con **versiones exactas** (pins), sin duplicar la lista en otro archivo (criterio fijado por el autor el 2026-10-05, D72). Ahí van las dependencias de ejecución, las de test y la **configuración de pytest**: no hay `requirements.txt` ni `pytest.ini`. **Sin empaquetado**: no se agrega un backend de construcción ni más de lo necesario para instalar y correr los tests. **Propuesta** (se fija en el design del primer change): cómo se declaran las dependencias dentro del archivo y el comando exacto de instalación.
- Los pins se **fijan en el `design.md` del primer change**, con la versión exacta, su fecha de publicación, la fuente y la fecha de consulta, y la compatibilidad entre ellos se comprueba con los metadatos de los paquetes, no se supone; lo que no se pueda obtener queda como **A verificar en el change** (verificar antes de crear el archivo de dependencias). Se **verifican en un clon limpio** (crear entorno, instalar solo desde ese archivo, correr los tests). **Los changes siguientes (incluido el de infraestructura con PostgreSQL) agregan sus dependencias a ese mismo archivo, con versión exacta**, cada uno en su design (D116), con el mismo criterio de antigüedad.
- **Toda dependencia de test está declarada** en ese archivo (pytest y cualquier plugin que use la configuración). Ninguna dependencia queda implícita ni instalada solo en la máquina del autor.
- **Zonas horarias en Windows** (decisión del autor 2026-10-07, D132): el paquete de datos de zonas (`tzdata`) se declara en el archivo único de dependencias, con versión exacta fijada en el design, y se menciona en el README; en Windows `zoneinfo` no trae base de zonas propia. `backend/app/domain` sigue importando solo la biblioteca estándar (`zoneinfo` lo es); `tzdata` no se importa, `zoneinfo` lo encuentra por su cuenta.
- Sin dependencias del lado async (ver DD-12). Alembic no entra en el primer change.
- **Imágenes de Docker** (decisión del autor 2026-10-13, D144; precisa D133): la regla de la semana se aplica al **último push de la etiqueta** (Docker Hub no da la fecha de publicación original) y se fija **etiqueta y digest** en `docker-compose.yml` y en el `Dockerfile`.
- **Agregadas por C-02** (2026-10-13, D143): `psycopg[binary]==3.3.6` y `alembic==1.20.0` en el grupo `app` de `backend/pyproject.toml`; PostgreSQL `17.10-bookworm` y Python `3.13.15-slim-bookworm` como imágenes. La configuración de Alembic va en `backend/alembic.ini`, no en `pyproject.toml` (D147).

## Definition of Done del primer change

Checklist verificable (el requisito de fondo es de la consigna y de DD-03; la redacción de los ítems y el uso de `/docs` en el video son decisión del autor 2026-10-03):
- [ ] En un **clon limpio**, siguiendo solo el README (que indica desde qué directorio, `backend/`, se instala y se corre `pytest`, D122), se crea el entorno, se instala desde el único archivo de dependencias y se corre `pytest` sin Docker, PostgreSQL ni Redis.
- [ ] El README dice explícitamente que los tests corren con **SQLite en memoria**, lista las versiones fijadas y dice con qué versiones de Python se instala (D133).
- [ ] `pytest` termina en verde y ejecuta al menos **un test por escenario del primer change (E1..E7 y E12)**; una tabla escenario ↔ test está en el README o en el design. Son 8 escenarios: excepción registrada al «3 a 6» de `CHANGES.md` (D123); sus tareas, agrupadas por tema, son la segunda excepción, al «alrededor de 20» (D134).
- [ ] **Se levanta la API** (`uvicorn`, con el comando del README) y `POST /turnos` se prueba desde Swagger en `/docs`: un turno válido devuelve `201`, un solapamiento devuelve `409` con `codigos`, y una referencia inexistente devuelve `422` con `RN-GL-04`. La demo usa SQLite en memoria con datos ficticios cargados al arrancar, con identificadores fijos documentados en el README junto con un ejemplo de petición (D124); el comando de arranque se fija en el design. Los tests usan una base en memoria por test, sin seed compartido.
- [ ] El spec del change tiene al menos 3 escenarios (feliz, error de negocio, borde), con Requirement y Scenario en WHEN/THEN citando RN y E#.
- [ ] El historial TDD muestra primero el test que falla y luego el código (RED → GREEN → TRIANGULATE → REFACTOR por escenario).
- [ ] Ningún test usa mocks de sesión ni de repositorio; ninguna dependencia de test falta en el archivo de dependencias.
- [ ] El test guard de fechas pasa y no hay `datetime.utcnow()` en el código.
- [ ] El **test de ida y vuelta de fechas** pasa: se escribe un datetime aware en UTC y se lee aware en UTC con SQLite (DD-13, D85).
- [ ] El **test de imports de `backend/app/domain`** pasa (regla de capas, D70; permite `zoneinfo`, D132).
- [ ] `openspec validate` del change sin errores y sin archivos de bloqueo residuales (`.openspec-archive.lock`) antes de archivar.
- [ ] No hay datos reales, secretos ni `.env` versionados; `.env.example` solo con valores de prueba (RN-PR-01).
- [ ] El README declara el **límite conocido**: `POST /turnos` va sin autenticación en este change (DD-14).
