# Spec Delta: historial-de-turnos

## MODIFIED Requirements

### Requirement: Crear un turno registra el evento `creado`

Al crear un turno, el sistema SHALL registrar en su historial exactamente un evento de tipo `creado`, en la misma operación que guarda el turno: o quedan los dos o no queda ninguno (RN-AG-11). El evento SHALL llevar el momento de la creación, el actor y los datos con los que nació el turno. Un rechazo MUST NOT registrar ningún evento.

#### Scenario: E9 Feliz - la creación queda registrada en el historial

- **GIVEN** un profesional y un sillón activos y libres a las 10:00, y una prestación activa de 30 minutos
- **WHEN** un usuario del panel con permiso para crear turnos pide, con su access token, crear un turno de esa prestación para un paciente existente con `inicio` 10:00, y el sistema responde `201`
- **THEN** el historial de ese turno tiene exactamente un evento, de `tipo` `creado`
- **AND** el evento tiene `ocurrido_en` `2026-10-07T12:00:00Z`, igual al `creado_en` del turno
- **AND** el evento tiene `actor_tipo` `usuario` y `actor_id` igual al identificador del usuario del token, escrito como texto decimal (desde C-07; D159, D209)
- **AND** `antes` y `motivo` están vacíos
- **AND** `despues` lleva el estado `reservado`, `inicio` `2026-11-02T10:00:00Z`, `fin` `2026-11-02T10:30:00Z`, `duracion_minutos` 30 y los identificadores del paciente, la prestación, el profesional y el sillón del turno

#### Scenario: E9 Borde - cada evento lleva al usuario que creó su turno

- **GIVEN** dos usuarios del panel con permiso para crear turnos, la odontóloga y la recepcionista
- **WHEN** la odontóloga crea un turno a las 10:00 y la recepcionista otro a las 11:00, cada una con su token
- **THEN** el evento `creado` del turno de las 10:00 lleva el identificador de la odontóloga y el del turno de las 11:00, el de la recepcionista
- **AND** los eventos `creado` guardados antes de C-07 siguen con `actor_id` vacío (D159)

#### Scenario: E9 Error de negocio - un rechazo no registra ningún evento

- **GIVEN** un turno activo de 10:00 a 10:30 del profesional A en el sillón 1, con su evento `creado`
- **WHEN** se pide crear otro turno de 30 minutos con el profesional A en el sillón 1 con `inicio` 10:00, y el sistema responde `409` (RN-AG-05, RN-AG-08)
- **THEN** en el sistema sigue habiendo un solo evento, el del turno existente
- **AND** lo mismo ocurre si la petición se rechaza con `422` por una referencia inválida (RN-GL-04), con `401` por falta de sesión o con `403` por un rol insuficiente (RN-AU-05)

#### Scenario: E9 Borde - si el evento no se puede guardar, el turno tampoco queda

- **GIVEN** un profesional y un sillón activos y libres a las 10:00, y una prestación activa de 30 minutos
- **WHEN** se pide crear un turno con `inicio` 10:00 y el registro del evento `creado` falla después de que el turno ya se envió a la base
- **THEN** la creación termina con error
- **AND** no queda ningún turno ni ningún evento
