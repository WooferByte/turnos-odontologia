# Descripción General

## Tipo de sistema

Aplicación web con **API REST** (backend) y **SPA** (frontend), más rutas públicas para la reserva del paciente por link. Un solo consultorio por instalación en el MVP (segmento: odontólogo independiente).

## Stack tecnológico

Stack definido por el autor en el Discovery (restricción, punto 9). Las versiones mínimas no figuran en las fuentes.

| Capa | Tecnologías | Versión mínima |
|---|---|---|
| Lenguaje backend | Python | **Suposición:** 3.11+ (a confirmar) |
| Framework API | FastAPI (validación con Pydantic, incluido en FastAPI) | No fijada |
| Autenticación | JWT (access token firmado) | No fijada |
| ORM / acceso a datos | SQLAlchemy | **Suposición:** 2.x (API declarativa tipada) |
| Base de datos | PostgreSQL (producción / docker-compose) | No fijada |
| Base de datos de tests | SQLite en memoria (ver DD-03) | — |
| Asincronía | Redis: colas de mensajes y tareas diferidas (recordatorios, ofertas de lista de espera, vencimiento de señas) | No fijada |
| Contenedores | Docker y Docker Compose | No fijada |
| Frontend | React + TypeScript + Vite | No fijada |
| Tests backend | **Suposición:** pytest + cliente de pruebas de FastAPI | — |

> **Alcance del change de la consigna.** El change que se implementa en la Etapa 6 solo necesita el **backend** (API o módulo de dominio). Sus tests deben correr **sin PostgreSQL ni Redis** (p. ej. SQLite en memoria y dobles de prueba para la cola), para que el repositorio se pueda clonar y testear siguiendo solo el README (restricción del Discovery). Ver DD-03 y R-08 en `09_decisiones_y_supuestos.md`.

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
         │                      │ encola tareas
         ▼                      ▼
   PostgreSQL               Redis ──► Worker (recordatorios,
   (fuente de verdad)                  ofertas de lista de espera,
                                       vencimiento de señas)
                                         │
                     ┌───────────────────┴─────────────────┐
                     ▼                                     ▼
          WhatsApp Cloud API (modo prueba)        Mercado Pago Checkout Pro
          o enlace wa.me (semiautomático)         + webhook de notificación
```

Decisiones de alto nivel:
- **Monolito modular** (un backend, un worker): suficiente para un consultorio y un trabajo individual. Ver DD-01.
- **Reglas de dominio puras** (sin dependencia de framework ni base) para que el change de solapamientos se testee como función pura. Ver DD-02.
- **La base de datos es la fuente de verdad**; Redis solo transporta trabajo diferido y puede perderse sin perder turnos.

## Integraciones externas

| Servicio | Propósito | Tipo | Versión |
|---|---|---|---|
| WhatsApp Cloud API (Meta), **modo prueba** | Recordatorio 24 h antes; confirmación o cancelación por respuesta; oferta de huecos a la lista de espera | REST saliente + webhook entrante | v1 (preferida, si la configuración resulta viable) |
| Enlace `wa.me` | Alternativa semiautomática: el sistema arma el mensaje y el odontólogo lo envía desde su WhatsApp | Enlace generado (sin API) | v1 (alternativa; a la par del mercado según el informe C.3) |
| Mercado Pago Checkout Pro | Cobro de la seña al reservar, cuenta única del odontólogo | REST (crear preferencia) + webhook (notificación de pago) | v1 (solo credenciales de prueba) |
| Mercado Pago split 1:N | Cobro a varios profesionales | — | Fase 2 |
| Google Calendar, ARCA, obras sociales, radiología, firma digital | — | — | Fuera de la v1 |

Detalle, restricciones y preguntas en `11_integraciones_whatsapp_y_mercadopago.md`.

## API REST (resumen)

**Suposición:** rutas propuestas para orientar el diseño; el contrato definitivo de cada endpoint se fija en el `design.md`/`specs` de cada change.

| Recurso | Endpoints principales | Acceso |
|---|---|---|
| Auth | `POST /auth/login`, `POST /auth/refresh` | Público (login) |
| Prestaciones | `GET/POST /prestaciones`, `PATCH/DELETE /prestaciones/{id}` | Odontólogo |
| Sillones | `GET/POST /sillones` (MVP: 1 sillón por defecto) | Odontólogo |
| Horario | `GET/PUT /profesionales/{id}/horario`, `GET/POST/DELETE /bloqueos` | Odontólogo |
| Disponibilidad | `GET /disponibilidad?prestacion_id&desde&hasta` | Interno + público |
| Turnos | `POST /turnos`, `GET /turnos?fecha`, `PATCH /turnos/{id}` (reprogramar), `POST /turnos/{id}/cancelar`, `POST /turnos/{id}/confirmar`, `POST /turnos/{id}/estado` | Odontólogo / Recepcionista |
| Historial | `GET /turnos/{id}/historial` | Odontólogo / Recepcionista / Dueño |
| Lista de espera | `GET/POST /lista-espera`, `POST /lista-espera/{id}/ofertar` | Odontólogo / Recepcionista |
| Pacientes y ficha | `GET/POST /pacientes`, `GET/PATCH /pacientes/{id}`, `POST /pacientes/{id}/anamnesis`, `POST /pacientes/{id}/evoluciones` | Odontólogo (ficha clínica); Recepcionista (datos de contacto) |
| Presupuestos y pagos | `POST /presupuestos`, `POST /pagos` | Odontólogo / Recepcionista |
| Configuración | `GET/PUT /configuracion/reglas` | Odontólogo |
| Reportes | `GET /reportes/ocupacion`, `GET /reportes/ausentismo`, `GET /reportes/cobros-pendientes` | Dueño / Odontólogo |
| Público | `GET /public/{slug}/prestaciones`, `GET /public/{slug}/disponibilidad`, `POST /public/{slug}/reservas`, `POST /public/{slug}/lista-espera`, `GET/POST /public/turnos/{token}` (ver, cancelar, reprogramar, confirmar) | Público (token de gestión firmado) |
| Webhooks | `POST /webhooks/mercadopago`, `GET/POST /webhooks/whatsapp` | Público con verificación de firma/token |

Para el change de la consigna alcanza con `POST /turnos` (o el caso de uso equivalente en un módulo) y su validación de solapamientos.
