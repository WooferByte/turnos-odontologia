# Descripción General

## Tipo de sistema

Aplicación web con **API REST** (backend) y **SPA** (frontend), más rutas públicas para la reserva del paciente por link. Un solo consultorio por instalación en el MVP (segmento: odontólogo independiente).

## Stack tecnológico

Stack definido por el autor en el Discovery (restricción, punto 9). Las versiones no figuran en las fuentes. El autor confirmó (2026-10-02, P-17) Python 3.11+ y SQLAlchemy 2.x. **Las demás versiones no se inventan**: el criterio es **versiones exactas, en un único archivo de dependencias** (decisión del autor 2026-10-05, D72); los pins se consultan y fijan en el `design.md` del primer change y se verifican en un clon limpio (política de 2026-10-03; ver «Versiones y dependencias» en `08_arquitectura_propuesta.md`).

| Capa | Tecnologías | Versión mínima |
|---|---|---|
| Lenguaje backend | Python | 3.11+ (confirmada por el autor, 2026-10-02) |
| Framework API | FastAPI (validación con Pydantic, incluido en FastAPI) | No fijada (pin en el `design.md` del primer change) |
| Autenticación | JWT (access y refresh token, HS256) y hash bcrypt (decisión del autor 2026-10-05, D74) | No fijada |
| ORM / acceso a datos | SQLAlchemy, **modo síncrono** en el primer change (DD-12) | 2.x, API declarativa tipada (confirmada por el autor, 2026-10-02) |
| Base de datos | PostgreSQL (producción / docker-compose) | No fijada (pin en el `design.md` del change que la use) |
| Base de datos de tests | SQLite en memoria, `sqlite+pysqlite:///:memory:` con `StaticPool` (DD-03, DD-12); sin `aiosqlite` | — |
| Asincronía | Redis: tarea periódica que persiste los vencimientos (señas y ofertas) y dispara los efectos (recordatorios, ofertas de lista de espera); el vencimiento se evalúa al consultar, por lo que los tests no la necesitan (RN-GL-05, D80). No interviene en el primer change | No fijada (pin en el `design.md` del change que la use) |
| Contenedores | Docker y Docker Compose | No fijada |
| Frontend | React + TypeScript + Vite (no interviene en el primer change) | No fijada |
| Tests backend | pytest + cliente de pruebas de FastAPI (**confirmado por el autor 2026-10-05, D84**; el primer change expone `POST /turnos`, por lo que también se prueba la API); todas las dependencias de test declaradas en el archivo único de dependencias | — |

> **Alcance del change de la consigna.** El change que se implementa en la Etapa 6 solo necesita el **backend**: dominio, caso de uso y el endpoint `POST /turnos` (FastAPI), **sin interfaz gráfica y sin autenticación** (límite conocido, DD-14), para demostrarlo desde Swagger. El autor implementará el proyecto completo antes de fin de año, change por change. Sus tests deben correr **sin PostgreSQL ni Redis** (SQLite en memoria; los vencimientos se evalúan al consultar y la lógica de la tarea periódica se prueba llamándola directamente, sin Redis), para que el repositorio se pueda clonar y testear siguiendo solo el README (restricción del Discovery). Ver DD-03 (confirmada por el autor el 2026-10-02: el README debe decir explícitamente que los tests corren con SQLite en memoria) y R-08 en `09_decisiones_y_supuestos.md`.

## Arquitectura general

```
 Paciente (celular)            Odontólogo / Recepcionista
        │ link público                    │ login (JWT)
        ▼                                 ▼
 ┌───────────────────────────────────────────────────┐
 │  Frontend SPA (React + TS + Vite)                 │
 │  - /reservar/{slug}  (público)                    │
 │  - /panel/...        (autenticado)                │
 └───────────────────────┬───────────────────────────┘
                         │ HTTPS / JSON
                         ▼
 ┌───────────────────────────────────────────────────┐
 │  API FastAPI                                      │
 │  api/ (routers) → application/ (casos de uso)     │
 │       → domain/ (reglas: solapamiento, ventanas)  │
 │       → infrastructure/ (repos SQLAlchemy,        │
 │          clientes WhatsApp y Mercado Pago)        │
 └───────┬──────────────────────┬────────────────────┘
         │                      │ tarea periódica
         ▼                      ▼
   PostgreSQL               Redis ──► Worker (prepara recordatorios
   (fuente de verdad)                  wa.me, vence señas impagas
                                       y ofertas de lista de espera)
                                         │
                     ┌───────────────────┴─────────────────┐
                     ▼                                     ▼
          Enlace wa.me (semiautomático)           Mercado Pago Checkout Pro
          (Cloud API oficial: Fase 2)             + webhook de notificación
```

Decisiones de alto nivel:
- **Monolito modular** (un backend, un worker): suficiente para un consultorio y un trabajo individual. Ver DD-01.
- **Reglas de dominio puras** (sin dependencia de framework ni base) para que el change de solapamientos se testee como función pura. Ver DD-02.
- **La base de datos es la fuente de verdad**; Redis solo transporta trabajo diferido y puede perderse sin perder turnos. **Qué queda para Redis en la v1** (confirmado por el autor 2026-10-05, D80; con `wa.me` no hay envío automático): una tarea periódica prepara el recordatorio a `inicio − 24 h` y persiste el vencimiento de las señas impagas (30 min) y de las ofertas de lista de espera (2 h) (DD-06). Los vencimientos se evalúan al consultar y consultar nunca dispara efectos (RN-GL-05).

## Integraciones externas

| Servicio | Propósito | Tipo | Versión |
|---|---|---|---|
| Enlace `wa.me` | Canal de la v1: el sistema arma el mensaje (recordatorio, oferta de hueco) y el odontólogo lo envía desde su WhatsApp; la confirmación llega por el link de gestión | Enlace generado (sin API) | **v1** (decisión del autor 2026-10-03; a la par del mercado según el informe C.3) |
| WhatsApp Cloud API (Meta) | Envío automático y respuesta del paciente por el chat | REST saliente + webhook entrante | **Fase 2** (adaptador sobre el puerto de mensajería) |
| Mercado Pago Checkout Pro | Cobro de la seña al reservar, cuenta única del odontólogo | REST (crear preferencia) + webhook (notificación de pago) | v1 (solo credenciales de prueba) |
| Mercado Pago split 1:N | Cobro a varios profesionales | — | Fase 2 |
| Google Calendar, ARCA, obras sociales, radiología, firma digital | — | — | Fuera de la v1 |

Detalle, restricciones y preguntas en `11_integraciones_whatsapp_y_mercadopago.md`.

## API REST (resumen)

**Propuesta:** rutas propuestas para orientar el diseño; el contrato definitivo de cada endpoint se fija en el `design.md`/`specs` de cada change.

| Recurso | Endpoints principales | Acceso |
|---|---|---|
| Auth | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/cambiar-contrasena` (el usuario cambia la propia, pidiendo la actual) | Público (login); `POST /auth/refresh` tampoco usa el JWT de acceso: se autentica con el refresh token (RN-AU-03); `cambiar-contrasena` con sesión; change de usuarios y acceso (Épica 10) |
| Usuarios | `GET/POST /usuarios`, `PATCH /usuarios/{id}` (roles, activar o desactivar), `POST /usuarios/{id}/restablecer-contrasena` | Odontólogo (el dueño solo lee) |
| Prestaciones | `GET/POST /prestaciones`, `PATCH /prestaciones/{id}` (editar o desactivar; no hay borrado) | Odontólogo |
| Sillones | `GET/POST /sillones`, `PATCH /sillones/{id}` (desactivar) (MVP: 1 sillón por defecto) | Odontólogo |
| Horario | `GET/PUT /profesionales/{id}/horario`, `GET/POST/DELETE /bloqueos` | Odontólogo |
| Disponibilidad | `GET /disponibilidad?prestacion_id&desde&hasta` | Interno + público |
| Turnos | `POST /turnos`, `GET /turnos?fecha`, `GET /turnos/{id}`, `PATCH /turnos/{id}` (reprogramar o cambiar la duración, US-012), `POST /turnos/{id}/cancelar`, `POST /turnos/{id}/confirmar`, `POST /turnos/{id}/estado` (marcar atendido o ausente; corregir el marcado, solo odontólogo), `POST /turnos/{id}/aprobar` y `POST /turnos/{id}/rechazar` (aprobación manual, solo odontólogo, RN-TD-05), `POST /turnos/{id}/sena/devolver` y `POST /turnos/{id}/sena/retener` (acción manual, solo odontólogo, RN-SP-10) | Odontólogo / Recepcionista |
| Mensajes | `GET /mensajes?fecha` (recordatorios y mensajes listos para enviar), `POST /mensajes/{id}/enviado` (marcarlo como enviado) (US-030) | Odontólogo / Recepcionista |
| Historial | `GET /turnos/{id}/historial` | Odontólogo / Recepcionista / Dueño |
| Lista de espera | `GET/POST /lista-espera` (el alta desde el panel registra el consentimiento con origen `panel` cuando el paciente lo da en persona, y su falta no bloquea el alta, RN-LE-05), `POST /lista-espera/{id}/retirar` (el consultorio retira una entrada, RN-LE-06). No hay ruta para ofertar a mano: en la v1 solo la tarea periódica ofrece huecos (RN-LE-01, D96) | Odontólogo / Recepcionista |
| Pacientes y ficha | `GET/POST /pacientes`, `GET/PATCH /pacientes/{id}` (datos administrativos, US-016; el alta avisa si hay un posible duplicado y solo crea igual con confirmación explícita, RN-TD-12; el odontólogo o la recepcionista cambian `acepta_contacto` con `PATCH /pacientes/{id}`, RN-PR-07), `POST /pacientes/{id}/consentimientos` (consentimiento dado en persona, origen `panel`; US-016 CA-7), `POST /pacientes/{id}/anamnesis`, `POST /pacientes/{id}/evoluciones` (US-060) | Odontólogo y Recepcionista (datos administrativos; el dueño solo lee); Odontólogo (ficha clínica) |
| Presupuestos | `GET/POST /presupuestos`, `PATCH /presupuestos/{id}` (ítems mientras está en `borrador` y cambio de estado, RN-FC-04, RN-FC-05) | Odontólogo (la recepcionista y el dueño solo leen) |
| Pagos | `GET/POST /pagos` (un registro no se edita: la corrección o la anulación es un registro nuevo, RN-SP-09) | Odontólogo / Recepcionista (el dueño solo lee) |
| Configuración | `GET/PUT /configuracion/reglas` | Odontólogo |
| Reportes | `GET /reportes/ocupacion`, `GET /reportes/ausentismo` (ambos con rango de fechas y profesional opcional, RN-RP-03), `GET /reportes/cobros-pendientes` | Dueño / Odontólogo |
| Público | `GET /public/{slug}/prestaciones`, `GET /public/{slug}/disponibilidad`, `POST /public/{slug}/reservas`, `POST /public/{slug}/lista-espera`, `POST /public/lista-espera/{token}/retirar`, `GET /public/turnos/{token}` (ver) y `POST /public/turnos/{token}/{confirmar|cancelar|reprogramar}`, `POST /public/ofertas/{token}/{aceptar|rechazar}`, `POST /public/turnos/{token}/pagar-sena` (paga la seña desde el link; devuelve la URL de Checkout Pro) | Público (token de gestión firmado) |
| Webhooks | `POST /webhooks/mercadopago`; `GET/POST /webhooks/whatsapp` (**Fase 2**) | Público con verificación de firma/token |

Para el change de la consigna alcanza con `POST /turnos` y su validación de solapamientos; en ese change va **sin autenticación** (límite conocido, DD-14) y se protege con JWT en el change de usuarios y acceso (US-092).
