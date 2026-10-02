# Actores y Roles

## Actores del sistema

| Actor | Descripción | Cómo interactúa | Rol técnico |
|---|---|---|---|
| Odontólogo | Profesional que atiende. En el segmento primario (independiente) es también recepcionista y dueño | Panel autenticado: agenda del día, ficha clínica, configuración | `odontologo` |
| Recepcionista | Agenda y confirma turnos. En el independiente suele ser el propio odontólogo | Panel autenticado: turnos, lista de espera, señas y pagos | `recepcionista` |
| Dueño del consultorio | Controla ocupación, ausentismo y cobros pendientes. En el independiente es el mismo odontólogo | Panel autenticado: reportes e historial (lectura) | `dueno` |
| Paciente | Reserva, paga la seña, confirma, cancela o reprograma | Link público de reserva y link de gestión del turno; WhatsApp | Sin cuenta, gestionado por token (DD-11, SU-03) |
| Sistema (worker) | Envía recordatorios, ofertas de lista de espera y vence señas impagas | Tareas en Redis | Actor técnico, registrado como `sistema` en el historial |
| Mercado Pago / Meta | Servicios externos que notifican pagos y respuestas | Webhooks | Actor externo, registrado como `webhook_mp` / `webhook_wa` |

**Nota de modelado.** Un mismo usuario puede tener varios roles (el odontólogo independiente tiene `odontologo` + `dueno` y opera como recepcionista). Los permisos se calculan como unión de roles.

## RBAC — Matriz de permisos

C = crear, R = leer, U = actualizar, D = eliminar/anular. "Propio" = solo sus turnos o su propio registro.

| Recurso | odontologo | recepcionista | dueno | paciente (por token) |
|---|---|---|---|---|
| Configuración de reglas (RN configurables) | CRUD | R | R | — |
| Prestaciones (nombre, duración, color) | CRUD | R | R | R (públicas) |
| Sillones / boxes | CRUD | R | R | — |
| Horario recurrente y bloqueos | CRUD | R | R | — |
| Disponibilidad | R | R | R | R |
| Turnos | CRUD | CRU + cancelar | R | C (reserva), R/U/cancelar propio |
| Confirmación de turno | U | U | — | U propio |
| Historial de cambios de turno | R | R | R | — (**Suposición:** no se expone al paciente) |
| Lista de espera | CRUD | CRUD | R | C propio |
| Pacientes: datos administrativos (identificación, contacto) | CRUD | CRU | R | R/U propio (**Suposición**) |
| Ficha clínica (anamnesis, evolución) | CRU (sin borrado físico, ver RN-FC-03) | — | — | — |
| Presupuestos | CRUD | R | R | — |
| Registro de pagos y señas | CRU | CRU | R | C (pago de seña vía MP) |
| Consentimiento de datos | R | R | R | C propio |
| Reportes (ocupación, ausentismo, cobros) | R | — | R | — |
| Usuarios del consultorio | CRUD | — | R | — |

**Decisión del autor (2026-10-02, P-09 / SU-04):** la recepcionista ve los datos **administrativos** del paciente (identificación, contacto, turnos, pagos) pero **no** los datos **clínicos** (anamnesis, evolución, odontograma), por minimización de datos de salud (Ley 25.326). Ver RN-FC-02.

## Rutas públicas

Accesibles sin autenticación (protegidas por slug del consultorio, token de gestión firmado o firma del webhook):

- `GET /public/{slug}/prestaciones` — prestaciones reservables online.
- `GET /public/{slug}/disponibilidad` — huecos libres.
- `POST /public/{slug}/reservas` — reserva 24/7 (CU-01), con aceptación de consentimiento (CU-07).
- `POST /public/{slug}/lista-espera` — anotarse cuando no hay horarios.
- `GET /public/turnos/{token}` y `POST /public/turnos/{token}/{confirmar|cancelar|reprogramar}` — gestión del turno por el paciente (CU-05).
- `POST /public/ofertas/{token}/{aceptar|rechazar}` — respuesta a una oferta de lista de espera.
- `POST /webhooks/mercadopago`, `GET/POST /webhooks/whatsapp` — notificaciones externas.
- `POST /auth/login`.

Todas las demás rutas requieren JWT.
