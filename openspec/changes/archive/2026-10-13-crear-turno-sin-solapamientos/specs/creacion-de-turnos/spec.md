# Spec Delta: creacion-de-turnos

## Purpose

Permite agendar un turno para un paciente, una prestación, un profesional y un sillón sin superponerlo con otro turno activo del mismo profesional o del mismo sillón, e informa con el código de la regla de negocio por qué se rechazó una petición.

Convenciones de los escenarios: todos los horarios están en **UTC** y son del día 2026-11-02; «10:00» significa `2026-11-02T10:00:00Z`. Los intervalos son semiabiertos `[inicio, fin)`. La operación es `POST /turnos` con `paciente_id`, `prestacion_id`, `inicio` y, opcionales, `profesional_id` y `sillon_id`. Un turno «activo» está en `pendiente_aprobacion`, `pendiente_sena`, `reservado` o `confirmado`. Todos los datos son ficticios.

Clases de rechazo (RN-GL-02): la **validación de entrada** (referencias inválidas, `RN-GL-04`; fecha sin zona o fuera de UTC, `RN-GL-01`; cuerpo mal formado) se informa toda junta en un único `422`; las **reglas de negocio** se evalúan solo con la entrada válida y de a una. El control de solapamiento es una sola regla de negocio que mira dos recursos, el profesional y el sillón.

## ADDED Requirements

### Requirement: Crear un turno reservado con fin calculado

El sistema SHALL crear el turno en estado `reservado` cuando no hay conflicto y responder `201`, con `fin = inicio + duración de la prestación` (RN-AG-02), ocupando un profesional y un sillón (RN-AG-06). El consultorio del turno SHALL ser el del profesional. Si la petición no indica el profesional o el sillón, el sistema SHALL usar el único activo del consultorio (RN-AG-14). `inicio` MUST ser una fecha-hora con zona en UTC (RN-GL-01).

#### Scenario: E1 Feliz - hueco libre

- **GIVEN** un profesional y un sillón activos, sin turnos entre las 10:00 y las 11:00, y una prestación activa de 30 minutos
- **WHEN** se pide crear un turno de esa prestación para un paciente existente con `inicio` 10:00, ese profesional y ese sillón
- **THEN** el sistema responde `201` con el turno en estado `reservado`, `inicio` 10:00, `fin` 10:30 y `duracion_minutos` 30
- **AND** el turno queda guardado con el consultorio del profesional

### Requirement: Rechazar el solapamiento con un turno activo del profesional

El sistema SHALL rechazar la creación de un turno cuyo intervalo se solapa con el de un turno activo del mismo profesional (RN-AG-05), aunque el sillón pedido esté libre. El rechazo SHALL responder `409` con un error que lleva el código `RN-AG-05` y el conflicto: recurso `profesional`, su identificador y el turno existente con el que choca (RN-GL-02). El sistema MUST NOT crear ningún turno.

#### Scenario: E2 Error de negocio - profesional ocupado

- **GIVEN** un turno activo de 10:00 a 10:30 del profesional A en el sillón 1, y el sillón 2 libre
- **WHEN** se pide crear un turno de 30 minutos con el profesional A en el sillón 2 con `inicio` 10:15
- **THEN** el sistema responde `409` y `codigos` es exactamente `["RN-AG-05"]`
- **AND** `conflictos` tiene un solo elemento, con `recurso` `profesional`, el identificador del profesional A y el identificador del turno existente
- **AND** no se crea ningún turno

### Requirement: Rechazar el solapamiento con un turno activo del sillón

El sistema SHALL rechazar la creación de un turno cuyo intervalo se solapa con el de un turno activo del mismo sillón (RN-AG-08), aunque ese turno sea de otro profesional y el profesional pedido esté libre. El rechazo SHALL responder `409` con un error que lleva el código `RN-AG-08` y el conflicto: recurso `sillon`, su identificador y el turno existente con el que choca (RN-GL-02). El sistema MUST NOT crear ningún turno.

#### Scenario: E3 Error de negocio - sillón ocupado

- **GIVEN** un turno activo de 10:00 a 10:30 del profesional A en el sillón 1, y el profesional B sin turnos
- **WHEN** se pide crear un turno de 30 minutos con el profesional B en el sillón 1 con `inicio` 10:00
- **THEN** el sistema responde `409` y `codigos` es exactamente `["RN-AG-08"]`
- **AND** `conflictos` tiene un solo elemento, con `recurso` `sillon`, el identificador del sillón 1 y el identificador del turno existente
- **AND** no se crea ningún turno

### Requirement: Informar todos los conflictos de solapamiento

El sistema SHALL tratar el control de solapamiento como **una sola regla de negocio que mira dos recursos** (RN-GL-02): SHALL evaluar RN-AG-05 y RN-AG-08 por separado y, si fallan las dos, informar **los dos** códigos en un mismo error `409`, en orden estable: primero `RN-AG-05`, después `RN-AG-08`. El sistema SHALL evaluar el solapamiento solo cuando la entrada es válida, y MUST NOT acumular sus códigos con los de otra regla de negocio ni con los de la validación de entrada. El error SHALL llevar un conflicto por recurso; si el turno pedido choca con más de un turno activo del mismo recurso, el conflicto SHALL indicar el que empieza primero.

#### Scenario: E4 Doble conflicto - profesional y sillón ocupados

- **GIVEN** un turno activo de 10:00 a 10:30 del profesional A en el sillón 1
- **WHEN** se pide crear un turno de 30 minutos con el profesional A en el sillón 1 con `inicio` 10:00
- **THEN** el sistema responde `409` y `codigos` es exactamente `["RN-AG-05", "RN-AG-08"]`
- **AND** `conflictos` tiene dos elementos: el primero con `codigo` `RN-AG-05` y `recurso` `profesional`, el segundo con `codigo` `RN-AG-08` y `recurso` `sillon`, ambos con el identificador del turno existente
- **AND** no se crea ningún turno

### Requirement: Tratar los turnos como intervalos semiabiertos

El sistema SHALL tratar cada turno como el intervalo semiabierto `[inicio, fin)`: dos turnos se solapan si y solo si `A.inicio < B.fin` y `B.inicio < A.fin` (RN-AG-09). Un turno que empieza en el instante exacto en que termina otro, o que termina en el instante exacto en que empieza otro, MUST aceptarse. Un solapamiento de un minuto MUST rechazarse.

#### Scenario: E5 Borde - turnos contiguos

- **GIVEN** un turno activo de 10:00 a 10:30 del profesional A en el sillón 1
- **WHEN** se pide crear un turno de 30 minutos con el profesional A en el sillón 1 con `inicio` 10:30
- **THEN** el sistema responde `201` con un turno `reservado` de 10:30 a 11:00
- **AND** si en cambio se pide con `inicio` 09:30 (termina a las 10:00, justo cuando empieza el existente), el sistema también responde `201`

#### Scenario: E7 Borde - solapamiento de un minuto

- **GIVEN** un turno activo de 10:00 a 10:30 del profesional A en el sillón 1, y el sillón 2 libre
- **WHEN** se pide crear un turno de 30 minutos con el profesional A en el sillón 2 con `inicio` 10:29
- **THEN** el sistema responde `409` y `codigos` es exactamente `["RN-AG-05"]`
- **AND** no se crea ningún turno

### Requirement: Contar solo los turnos en estado activo

El sistema SHALL considerar para el solapamiento únicamente los turnos en estado activo: `pendiente_aprobacion`, `pendiente_sena`, `reservado` y `confirmado` (RN-AG-10). Un turno en `cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido` o `ausente` MUST NOT bloquear el horario.

#### Scenario: E6 Estado no activo - un turno cancelado no bloquea

- **GIVEN** un turno en estado `cancelado_paciente` de 10:00 a 10:30 del profesional A en el sillón 1
- **WHEN** se pide crear un turno de 30 minutos con el profesional A en el sillón 1 con `inicio` 10:00
- **THEN** el sistema responde `201` con un turno `reservado` de 10:00 a 10:30
- **AND** lo mismo ocurre si el turno existente está en `cancelado_profesional`, `vencido`, `atendido` o `ausente`

### Requirement: Rechazar las referencias inválidas

El sistema SHALL rechazar con `422` y el código `RN-GL-04` la petición cuyo cuerpo refiere una prestación, un profesional o un sillón inexistente, inactivo (RN-AG-07) o de otro consultorio, o un paciente inexistente o de otro consultorio, o que omite el profesional o el sillón sin que haya uno solo activo (RN-AG-14). Un paciente MUST NOT informarse como inactivo: solo puede ser `inexistente`. El error SHALL listar **todas** las referencias inválidas, cada una con recurso, identificador y motivo.

Las referencias inválidas son **validación de entrada** (RN-GL-02): el sistema SHALL informar juntos, en un único `422`, todos los problemas de entrada de la petición. Si además `inicio` no tiene zona o no está en UTC, ese mismo error SHALL llevar los dos códigos, en orden estable: primero `RN-GL-01`, después `RN-GL-04`. Con cualquier problema de entrada el sistema MUST NOT evaluar ninguna regla de negocio (ni el cruce de la medianoche, RN-AG-10d, ni el solapamiento) y MUST NOT crear ningún turno.

#### Scenario: E12 Error de negocio - recurso no encontrado

- **GIVEN** que no existe la prestación 999, que el paciente de la petición existe, y que el profesional y el sillón de la petición existen y están activos
- **WHEN** se pide crear un turno con `prestacion_id` 999 con `inicio` 10:00
- **THEN** el sistema responde `422` y `codigos` es exactamente `["RN-GL-04"]`
- **AND** `referencias` tiene un solo elemento, con `recurso` `prestacion`, `recurso_id` 999 y `motivo` `inexistente`
- **AND** no se crea ningún turno
- **AND** si además el sillón pedido está inactivo, `codigos` sigue siendo `["RN-GL-04"]` y `referencias` lista las dos: la prestación (`inexistente`) y el sillón (`inactivo`)
- **AND** si además `inicio` se envía sin zona, el sistema responde un único `422` con `codigos` exactamente `["RN-GL-01", "RN-GL-04"]`
