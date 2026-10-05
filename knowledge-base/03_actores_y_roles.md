# Actores y Roles

## Actores del sistema

| Actor | Descripción | Cómo interactúa | Rol técnico |
|---|---|---|---|
| Odontólogo | Profesional que atiende. En el segmento primario (independiente) es también recepcionista y dueño | Panel autenticado: agenda del día, ficha clínica, configuración | `odontologo` |
| Recepcionista | Agenda y confirma turnos. En el independiente suele ser el propio odontólogo | Panel autenticado: turnos, lista de espera, señas y pagos | `recepcionista` |
| Dueño del consultorio | Controla ocupación, ausentismo y cobros pendientes. En el independiente es el mismo odontólogo | Panel autenticado: reportes e historial (lectura) | `dueno` |
| Paciente | Reserva, paga la seña, confirma, cancela o reprograma | Link público de reserva y link de gestión del turno; WhatsApp | Sin cuenta, gestionado por token (DD-11, SU-03) |
| Sistema (worker) | Tarea periódica con Redis: **persiste** los vencimientos (turno a `vencido`, seña a `vencida`, oferta a `vencida`) y **es la única que dispara las notificaciones y los efectos en cadena** (ofrecer el hueco al siguiente de la lista de espera, preparar los recordatorios `wa.me`). Antes de cada mensaje verifica `Paciente.acepta_contacto`. **Consultar nunca dispara efectos**: el estado efectivo de un vencimiento se evalúa al consultar (RN-GL-05, RN-PR-07; D80, D81) | Tareas en Redis | Actor técnico, registrado como `sistema` en el historial |
| Mercado Pago | Servicio externo que notifica pagos | Webhook | Actor externo, registrado como `webhook_mp` |
| Meta (WhatsApp Cloud API) | **Fase 2**: respuestas del paciente por el chat | Webhook | Actor externo, registrado como `webhook_wa` (Fase 2) |

**Nota de modelado.** Un mismo usuario puede tener varios roles (el odontólogo independiente tiene `odontologo` + `dueno` y opera como recepcionista). Los permisos se calculan como unión de roles, y los roles se leen de la base en cada petición (RN-AU-02, D102). **En el segmento primario (odontólogo independiente), la misma persona tiene los roles `odontologo` y `dueno`** (y opera como recepcionista); se mantienen los tres roles separados porque la matriz de permisos los distingue y la Fase 2 (consultorio compartido) los separa (decisión del autor 2026-10-03). Los roles válidos son `odontologo`, `recepcionista` y `dueno` (RN-AU-05); las historias están en la Épica 10 de `06_funcionalidades.md` (US-090 a US-094).

## RBAC — Matriz de permisos

C = crear, R = leer, U = actualizar, D = eliminar/anular. "Propio" = solo sus turnos o su propio registro.

| Recurso | odontologo | recepcionista | dueno | paciente (por token) |
|---|---|---|---|---|
| Configuración de reglas (RN configurables) | CRUD | R | R | — |
| Prestaciones (nombre, duración, color) | CRUD | R | R | R (públicas) |
| Sillones / boxes | CRUD | R | R | — |
| Horario recurrente y bloqueos | CRUD | R | R | — |
| Disponibilidad | R | R | R | R |
| Turnos | CRUD | CRU + cancelar | R | C (reserva), R/U/cancelar propio, según el estado del turno (RN-TD-08, D77) |
| Marcar turno atendido / ausente (RN-AG-13) | U | U | — | — |
| Corregir el marcado atendido ↔ ausente (≤ 24 h, RN-AG-13) y devolver o retener la seña manualmente (RN-SP-10) | U | — | — | — |
| Confirmación de turno | U | U | — | U propio |
| Mensajes `wa.me` (ver los listos para enviar y marcarlos como enviados, US-030) | R/U | R/U | — | — |
| Historial de cambios de turno | R | R | R | — (el historial no se expone al paciente; confirmado por el autor 2026-10-05, D68) |
| Lista de espera (el alta desde el panel registra el consentimiento con origen `panel`, RN-LE-05; solo la tarea periódica ofrece huecos, RN-LE-01) | CRUD | CRUD | R | C propio (con consentimiento, RN-LE-05); retirarse desde su link (RN-LE-06) |
| Pacientes: datos administrativos (identificación, contacto; US-016) | CRU | CRU | R | R propio (solo lectura; sin edición por token, RN-TD-09; decisión del autor 2026-10-05, D69) |
| Pacientes: aceptar o no ser contactado (`acepta_contacto`, RN-PR-07; el paciente lo pide al consultorio) | U | U | R | — |
| Ficha clínica (anamnesis, evolución) | CRU (sin borrado físico, ver RN-FC-03) | — | — | — |
| Presupuestos (el estado lo cambia solo el odontólogo, RN-FC-05) | CRUD | R | R | — |
| Registro de pagos y señas (un registro de pago no se edita: se corrige o anula con un registro nuevo, RN-SP-09) | CR | CR | R | C (pago de seña vía MP) |
| Consentimiento de datos | R | R | R | C propio |
| Reportes (ocupación, ausentismo, cobros) | R | — | R | — |
| Usuarios del consultorio (alta con contraseña inicial, roles, desactivar, restablecer contraseña; RN-AU-06, RN-AU-07) | CRUD | — | R | — |
| Cambiar la propia contraseña (pidiendo la actual, RN-AU-07) | U propio | U propio | U propio | — |

**Decisión del autor (2026-10-02, P-09 / SU-04):** la recepcionista ve los datos **administrativos** del paciente (identificación, contacto, turnos, pagos) pero **no** los datos **clínicos** (anamnesis, evolución, odontograma), por minimización de datos de salud (Ley 25.326). Ver RN-FC-02.

## Rutas públicas

Accesibles sin autenticación (protegidas por slug del consultorio, token de gestión firmado o firma del webhook):

- `GET /public/{slug}/prestaciones` — prestaciones reservables online.
- `GET /public/{slug}/disponibilidad` — huecos libres.
- `POST /public/{slug}/reservas` — reserva 24/7 (CU-01), con aceptación de consentimiento (CU-07) y, si el turno cae dentro de la ventana de cancelación, con la aceptación explícita de RN-TD-10 (D87). Reutiliza un paciente existente solo si coinciden teléfono, nombre y apellido normalizados, y la respuesta es idéntica en ambos casos (RN-TD-09, RN-PR-06). La respuesta **devuelve el link de gestión** del turno (RN-TD-08, D93).
- `POST /public/{slug}/lista-espera` — anotarse cuando no hay horarios.
- `GET /public/turnos/{token}` y `POST /public/turnos/{token}/{confirmar|cancelar|reprogramar}` — gestión del turno por el paciente (CU-05). **Todo turno tiene token, también el cargado desde el panel** (D94). El token no vence por sí mismo; las acciones permitidas dependen del estado del turno y, en un estado terminal, solo se ve el estado (RN-TD-08, D77); una acción no permitida se rechaza con `RN-TD-11` (D89).
- `POST /public/turnos/{token}/pagar-sena` — **Propuesta** (las rutas se fijan en el design de cada change; decisión del autor 2026-10-05, D89): el paciente paga la seña desde su link de gestión; devuelve la URL de Checkout Pro de la preferencia. Solo con el turno en `pendiente_sena` (RN-TD-08); en otro estado se rechaza con `RN-TD-11`.
- `POST /public/ofertas/{token}/{aceptar|rechazar}` — respuesta a una oferta de lista de espera. Si el hueco cae dentro de la ventana de cancelación, aceptar exige la aceptación explícita de RN-TD-10.
- `POST /public/lista-espera/{token}/retirar` — el paciente se retira de la lista de espera desde su link (RN-LE-06). El token es propio de la entrada de lista de espera porque el token de gestión identifica un único turno (RN-TD-08); confirmado por el autor el 2026-10-05, D29.
- `POST /webhooks/mercadopago` — notificación de pago. `GET/POST /webhooks/whatsapp` — **Fase 2** (Cloud API).
- `POST /auth/login`. `POST /auth/refresh` (se autentica con el refresh token, no con el JWT de acceso; RN-AU-03).

Todas las demás rutas requieren JWT. **Excepción conocida:** en el primer change, `POST /turnos` va **sin autenticación** (decisión del autor 2026-10-03, DD-14); desde el change de usuarios y acceso exige JWT con rol `odontologo` o `recepcionista` (US-092).
