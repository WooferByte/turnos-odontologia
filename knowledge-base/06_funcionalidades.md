# Funcionalidades

Organizadas por **épica** y **historia de usuario** (US-NNN). Versión: **v1** salvo indicación. Cada historia referencia el caso de uso (CU) de `01_vision_y_objetivos.md` y las reglas de `05_reglas_de_negocio.md`.

## Épica 1: Configuración de agenda

### US-001 — Tabla de prestaciones
**Como** odontólogo **quiero** definir prestaciones con nombre, duración por defecto y color **para** que cada turno ocupe el tiempo real que necesita.
- [ ] CA-1: puedo crear, editar y desactivar prestaciones; el nombre es único en el consultorio.
- [ ] CA-2: la duración debe ser > 0 y múltiplo de la granularidad; si no, se rechaza.
- [ ] CA-3: cambiar la duración no modifica turnos existentes.
**Reglas**: RN-AG-01, RN-AG-02, RN-GL-03

### US-002 — Horario recurrente
**Como** odontólogo **quiero** configurar mis días y franjas de atención **para** que solo se ofrezcan turnos dentro de ese horario.
- [ ] CA-1: puedo cargar varias franjas por día (p. ej. mañana y tarde) sin que se superpongan entre sí.
- [ ] CA-2: un turno que excede el fin de la franja se rechaza.
**Reglas**: RN-AG-04

### US-003 — Bloqueos puntuales
**Como** odontólogo **quiero** bloquear días u horas (vacaciones, feriados, ausencias) **para** que no se reserven turnos en esos momentos.
- [ ] CA-1: el bloqueo puede ser del profesional, del sillón o de todo el consultorio.
- [ ] CA-2: al crear un bloqueo sobre turnos activos, el sistema lista los afectados.
**Reglas**: RN-AG-04b

### US-004 — Sillón como recurso
**Como** odontólogo **quiero** que el consultorio tenga un sillón por defecto **para** que la agenda controle su ocupación sin configuración extra.
- [ ] CA-1: el seed crea "Sillón 1"; todo turno sin sillón explícito se asigna a él.
- [ ] CA-2: el modelo admite agregar más sillones (la UI multi-sillón es Fase 2).
**Reglas**: RN-AG-06, RN-AG-07

### US-005 — Reglas configurables
**Como** odontólogo **quiero** ajustar antelaciones, horizonte, aprobación de nuevos y seña **para** adaptar el sistema a mi forma de trabajo.
- [ ] CA-1: la antelación de cancelación solo acepta valores entre 24 y 48 h.
- [ ] CA-2: todos los valores arrancan con los defaults propuestos.
**Reglas**: RN-TD-01, RN-TD-02, RN-TD-03, RN-TD-05, RN-SP-01

## Épica 2: Gestión de turnos (núcleo)

### US-010 — Crear turno sin solapamientos por profesional y por sillón ⭐ (change candidato de la consigna)
**Como** recepcionista (o el propio odontólogo) **quiero** crear un turno para un paciente, prestación, profesional y sillón **para** agendarlo sin superponerlo con otro.
- [ ] CA-1 (feliz): dado un hueco libre dentro del horario, al crear el turno queda `reservado` (o `pendiente_sena` si se exige seña) con `fin = inicio + duración de la prestación`.
- [ ] CA-2 (error de negocio): si el profesional ya tiene un turno activo que se superpone, se rechaza con `RN-AG-05`.
- [ ] CA-3 (error de negocio): si el sillón ya tiene un turno activo que se superpone (aunque sea otro profesional), se rechaza con `RN-AG-08`.
- [ ] CA-4 (borde): un turno que empieza exactamente cuando termina otro se acepta.
- [ ] CA-5 (borde): un solapamiento de un minuto se rechaza.
- [ ] CA-6: un turno cancelado no bloquea el horario.
- [ ] CA-7: la creación queda registrada en el historial.
- [ ] CA-8 (opcional en el change): un turno fuera del horario o sobre un bloqueo se rechaza (RN-AG-04/04b); **puede quedar fuera del primer change para mantenerlo chico**.
**Reglas**: RN-AG-02, RN-AG-05, RN-AG-06, RN-AG-08, RN-AG-09, RN-AG-10, RN-AG-10c, RN-AG-10d, RN-AG-11, RN-GL-02

### US-011 — Agenda del día
**Como** odontólogo **quiero** ver los turnos del día con color por prestación y estado **para** organizar la atención.
- [ ] CA-1: se listan los turnos del profesional ordenados por inicio, con paciente, prestación y estado.
**Reglas**: RN-AG-01

### US-012 — Reprogramar turno (panel)
**Como** recepcionista **quiero** mover un turno a otro horario **para** acomodar cambios sin perder el historial.
- [ ] CA-1: se valida como un turno nuevo, excluyéndose a sí mismo.
- [ ] CA-2: el historial guarda el horario anterior y el nuevo.
**Reglas**: RN-AG-10b, RN-AG-11

### US-013 — Cancelar turno (panel) y liberar horario
**Como** recepcionista **quiero** cancelar un turno **para** liberar el horario y ofrecerlo a la lista de espera.
- [ ] CA-1: el turno pasa a `cancelado_profesional` o `cancelado_paciente` según quién lo pidió.
- [ ] CA-2: el horario queda libre y se dispara la búsqueda en la lista de espera.
- [ ] CA-3: si había seña y cancela el odontólogo, la seña se marca para devolución.
**Reglas**: RN-AG-10, RN-LE-01, RN-SP-05

### US-014 — Marcar atendido / ausente
**Como** odontólogo **quiero** marcar si el paciente asistió **para** medir el ausentismo.
**Reglas**: RN-AG-11

### US-015 — Historial de cambios
**Como** dueño **quiero** ver quién cambió qué y cuándo en cada turno **para** tener trazabilidad.
- [ ] CA-1: el historial es de solo lectura y no puede editarse.
**Reglas**: RN-AG-11

## Épica 3: Reserva y autogestión del paciente

### US-020 — Reserva online 24/7 por link (CU-01)
**Como** paciente **quiero** elegir prestación y horario desde el celular **para** sacar turno en menos de 30 segundos sin depender del horario de atención.
- [ ] CA-1: solo se muestran huecos que respetan horario, bloqueos, solapamientos, horizonte (60 días) y antelación mínima (2 h).
- [ ] CA-2: debo aceptar el consentimiento de datos para confirmar.
- [ ] CA-3: si soy paciente nuevo y la aprobación manual está activa, el turno queda `pendiente_aprobacion`.
- [ ] CA-4: si dos personas reservan el mismo hueco a la vez, solo una lo obtiene.
**Reglas**: RN-TD-01, RN-TD-02, RN-TD-05, RN-TD-06, RN-AG-10c, RN-PR-02

### US-021 — Sin horarios: lista de espera (CU-06)
**Como** paciente **quiero** anotarme en lista de espera cuando no hay horarios **para** que me avisen si se libera uno.
**Reglas**: RN-TD-07, RN-LE-01

### US-022 — Cancelar o reprogramar por el paciente (CU-05)
**Como** paciente **quiero** cancelar o reprogramar desde el link del turno **para** liberar el horario con anticipación.
- [ ] CA-1: permitido hasta 24 h antes (configurable 24-48); después, el link indica contactar al consultorio.
- [ ] CA-2: la reprogramación aplica las mismas reglas que una reserva.
**Reglas**: RN-TD-03, RN-TD-04, RN-TD-08, RN-SP-04, RN-SP-06

## Épica 4: Recordatorio y confirmación por WhatsApp (CU-02)

### US-030 — Recordatorio 24 h antes
**Como** odontólogo **quiero** que el sistema recuerde el turno 24 h antes **para** reducir ausencias.
- [ ] CA-1 (Cloud API): el worker envía el mensaje con plantilla y link de gestión.
- [ ] CA-2 (`wa.me`): el panel muestra la lista de recordatorios del día con el enlace listo para enviar.
**Reglas**: RN-WA-01, RN-WA-03

### US-031 — Confirmación por respuesta
**Como** odontólogo **quiero** registrar quién confirmó **para** saber qué huecos podrían liberarse.
- [ ] CA-1: la confirmación cambia el estado a `confirmado` y queda en el historial.
**Reglas**: RN-WA-02, RN-AG-11

## Épica 5: Lista de espera (CU-06) — diferenciador

### US-040 — Ofrecer hueco liberado
**Como** odontólogo **quiero** que un hueco liberado se ofrezca automáticamente a quien espera **para** convertir cancelaciones en turnos.
- [ ] CA-1: se ofrece por orden de alta a la primera entrada compatible.
- [ ] CA-2: la oferta vence; si vence o se rechaza, pasa al siguiente.
- [ ] CA-3: al aceptar, se revalida el solapamiento.
**Reglas**: RN-LE-01 a RN-LE-04

## Épica 6: Seña con Mercado Pago (CU-04)

### US-050 — Pagar seña al reservar
**Como** paciente **quiero** pagar la seña al reservar **para** asegurar mi turno.
- [ ] CA-1: se genera una preferencia de Checkout Pro en la cuenta del odontólogo (credenciales de prueba).
- [ ] CA-2: el webhook acreditado pasa el turno a `reservado`; notificaciones duplicadas no acreditan dos veces.
- [ ] CA-3: si no se paga a tiempo, el turno vence y libera el horario.
**Reglas**: RN-SP-01, RN-SP-02, RN-SP-03, RN-SP-08

### US-051 — Retención / devolución de seña (**sujeta a revisión legal**)
**Reglas**: RN-SP-04, RN-SP-05, RN-SP-06

## Épica 7: Ficha clínica mínima, presupuestos y pagos (CU-03)

### US-060 — Ficha del paciente
**Como** odontólogo **quiero** abrir la ficha en la consulta y registrar anamnesis y evolución **para** no depender de la carpeta de papel.
**Reglas**: RN-FC-01, RN-FC-02, RN-FC-03

### US-061 — Presupuesto simple
**Reglas**: RN-FC-04

### US-062 — Registro de pago simple
**Reglas**: RN-SP-07

## Épica 8: Privacidad y consentimiento (CU-07)

### US-070 — Consentimiento informado de datos
**Como** paciente **quiero** saber qué datos de salud se guardan y aceptar su tratamiento.
**Reglas**: RN-PR-02, RN-PR-03

### US-071 — Datos ficticios en el repositorio
**Como** autor del proyecto **quiero** que seeds, tests y ejemplos usen solo datos inventados **para** no exponer datos reales.
**Reglas**: RN-PR-01

## Épica 9: Control del dueño

### US-080 — Reportes de ocupación, ausentismo y cobros pendientes
**Como** dueño **quiero** ver ocupación, ausentismo y señas/pagos pendientes **para** controlar el consultorio.

## Épicas posteriores (no implementar en v1)

| Épica | Versión |
|---|---|
| Odontograma completo | v1.1 |
| Obras sociales (códigos y valores manuales) | v1.1 |
| Imágenes y radiografías | v2 |
| ARCA / facturación electrónica | v2 |
| Caja completa con arqueo | v2 |
| Agenda multi-profesional y multi-sillón en UI (CU-08) | Fase 2 |
| Split de pagos 1:N en Mercado Pago | Fase 2 |
| WhatsApp API oficial en producción | Posterior |
| Google Calendar, API pública | Posterior |
