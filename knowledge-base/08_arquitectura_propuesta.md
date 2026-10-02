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
| Cola de tareas | Redis + worker | Recordatorios, ofertas y vencimientos sin bloquear la API |
| Puerto/adaptador de mensajería | `MensajeriaPort` con adaptadores `CloudApiAdapter` y `WaMeAdapter` | Cambiar de canal sin tocar el dominio (DD-06) |
| Idempotencia de webhooks | `webhooks/mercadopago`, `webhooks/whatsapp` | Notificaciones repetidas no duplican efectos (RN-SP-08) |
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
│   │   │   └── errors.py        # ErrorDeDominio(codigo="RN-AG-05", ...)
│   │   ├── application/         # casos de uso: crear_turno, reprogramar, cancelar, reservar_publico...
│   │   ├── infrastructure/
│   │   │   ├── db/              # modelos SQLAlchemy, sesión, migraciones
│   │   │   ├── repositories/
│   │   │   ├── messaging/       # cloud_api.py, wa_me.py
│   │   │   ├── payments/        # mercadopago.py
│   │   │   └── queue/           # productor/consumidor Redis
│   │   ├── api/
│   │   │   ├── routers/         # auth, turnos, agenda, public, webhooks...
│   │   │   └── deps.py          # auth JWT, sesión de DB
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

**Suposición:** migraciones con Alembic (no figura en las fuentes; es la herramienta habitual con SQLAlchemy). Confirmar en el change de infraestructura.

## Seguridad

- **Autenticación**: JWT firmado (HS256 con secreto de entorno) para el panel; access token de vida corta + refresh (**Suposición** sobre tiempos). Contraseñas con hash adaptativo (**Suposición:** bcrypt/argon2).
- **Autorización**: RBAC por rol (`odontologo`, `recepcionista`, `dueno`) vía dependencies de FastAPI; unión de roles. Ficha clínica solo `odontologo`.
- **Paciente**: sin cuenta; **token de gestión firmado** por turno y por oferta de lista de espera, con vencimiento. Nunca datos personales en la URL (RN-PR-06).
- **Webhooks**: verificación de firma/token de Meta y de Mercado Pago; consulta del pago a la API de Mercado Pago antes de acreditar.
- **Validación de input**: modelos Pydantic en todos los endpoints; reglas de negocio en el dominio, no en el router.
- **Datos sensibles (Ley 25.326)**: HTTPS obligatorio fuera de desarrollo; minimización por rol; logs sin datos clínicos ni teléfonos completos (**Suposición**); **datos siempre ficticios** en el repositorio (RN-PR-01).
- **Secrets management**: variables de entorno; `.env` fuera del repositorio; `.env.example` solo con valores de prueba. Nunca tokens reales o de producción de Meta o Mercado Pago en el repo.
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
| `WHATSAPP_MODE` | Canal de mensajería | `cloud_api` \| `wa_me` | N |
| `WHATSAPP_TOKEN` | Token de la Cloud API (modo prueba) | `<token-de-prueba>` | Y |
| `WHATSAPP_PHONE_NUMBER_ID` | ID del número de prueba de Meta | `<id>` | N |
| `WHATSAPP_VERIFY_TOKEN` | Verificación del webhook | `<random>` | Y |
| `WHATSAPP_APP_SECRET` | Validación de firma del webhook | `<secret>` | Y |
| `MP_ACCESS_TOKEN` | Credencial **de prueba** de Mercado Pago | `TEST-...` | Y |
| `MP_WEBHOOK_SECRET` | Validación de notificaciones | `<secret>` | Y |
| `QUEUE_ENABLED` | Permite desactivar Redis en tests | `false` en tests | N |

Los nombres son **propuestos** (**Suposición**); se fijan en el change de infraestructura.

## Estrategia de tests

- **Unit**: funciones puras de dominio (solapamiento, ventanas de cancelación, transiciones de estado). Sin I/O.
- **Integration**: casos de uso con repositorios SQLAlchemy sobre **SQLite en memoria**; la cola se reemplaza por un doble en memoria.
- **API**: `TestClient` de FastAPI con la misma base en memoria.
- Comando único documentado en el README (p. ej. `pytest`), sin Docker ni servicios externos. El README debe decir explícitamente que los tests corren con SQLite en memoria (DD-03, confirmada por el autor el 2026-10-02) y fijar las versiones de FastAPI, PostgreSQL, Redis, React y Vite al implementar el change (P-17).
- La restricción de exclusión de PostgreSQL (si se usa) se testea aparte en un perfil opcional con docker-compose; **no es requisito** para la suite del change.
