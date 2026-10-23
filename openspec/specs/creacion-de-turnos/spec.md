# creacion-de-turnos Specification

## Purpose
Permite agendar un turno para un paciente, una prestación, un profesional y un sillón sin superponerlo con otro turno activo del mismo profesional o del mismo sillón, e informa con el código de la regla de negocio por qué se rechazó una petición.

Convenciones de los escenarios: todos los horarios están en **UTC** y son del día 2026-11-02; «10:00» significa `2026-11-02T10:00:00Z`. Los intervalos son semiabiertos `[inicio, fin)`. La operación es `POST /turnos` con `paciente_id`, `prestacion_id`, `inicio` y, opcionales, `profesional_id` y `sillon_id`. Un turno «activo» está en `pendiente_aprobacion`, `pendiente_sena`, `reservado` o `confirmado`. Todos los datos son ficticios.

Clases de rechazo (RN-GL-02): la **validación de entrada** (referencias inválidas, `RN-GL-04`; fecha sin zona o fuera de UTC, `RN-GL-01`; cuerpo mal formado) se informa toda junta en un único `422`; las **reglas de negocio** se evalúan solo con la entrada válida y de a una. El control de solapamiento es una sola regla de negocio que mira dos recursos, el profesional y el sillón. Desde C-12, salvo que un escenario diga otra cosa, el profesional tiene una franja del horario que cubre el turno pedido (RN-AG-04): E2 a E7 y E12 usan las 10:00 UTC, que son las 07:00 del consultorio, y sus tests cargan el horario de prueba 00:00-23:59 (D263).
## Requirements

### Requirement: Crear un turno reservado con fin calculado

El sistema SHALL crear el turno en estado `reservado` cuando cae completo en una franja del horario del profesional (RN-AG-04) y no hay conflicto, y responder `201`, con `fin = inicio + duración de la prestación` (RN-AG-02), ocupando un profesional y un sillón (RN-AG-06). El consultorio del turno SHALL ser el del profesional. Si la petición no indica el profesional o el sillón, el sistema SHALL usar el único activo del consultorio (RN-AG-14). `inicio` MUST ser una fecha-hora con zona en UTC (RN-GL-01).

#### Scenario: E1 Feliz - hueco libre

- **GIVEN** un profesional con una franja del lunes que cubre de 10:00 a 11:00 (07:00 a 08:00 del consultorio) y un sillón activos, sin turnos entre las 10:00 y las 11:00, y una prestación activa de 30 minutos
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

### Requirement: Rechazar el turno fuera del horario del profesional

El sistema SHALL rechazar con `422` y `codigos` `["RN-AG-04"]`, sin crear nada, el turno cuyo `[inicio, fin)`, convertido a la zona del consultorio, no cae completo dentro de una sola franja vigente del profesional para el día de la semana local de `inicio` (RN-AG-04, RN-GL-01; E10). Dos franjas contiguas no se suman: el turno debe caber en una sola (D258). Una franja cuenta solo si está vigente en la fecha local de `inicio`: `vigente_desde` nula o anterior o igual, y `vigente_hasta` nula o posterior o igual (D259; la vigencia no viaja en la API, así que solo se arma guardando la franja directo en la base). Un profesional sin franjas ese día, o sin ninguna, no admite turnos (D256). Una franja termina como mucho a las 23:59, así que un turno que termina exactamente a las 00:00 del consultorio, que RN-AG-10d acepta, no cabe en ninguna franja (D265). Salvo que un escenario diga otra cosa, en esta capability el profesional tiene una franja que cubre el turno pedido: por eso los escenarios E2 a E7 y E12, que usan las 10:00 UTC (07:00 del consultorio), siguen valiendo sin cambios.

#### Scenario: E10 US-002 CA-2 Error de negocio - el turno excede el fin de la franja

- **GIVEN** un profesional con la franja lunes 09:00-13:00 del consultorio (12:00 a 16:00), sin turnos, y una prestación de 30 minutos
- **WHEN** se pide crear un turno con `inicio` 15:45 (termina 16:15, después del fin de la franja; US-002 CA-2)
- **THEN** el sistema responde `422` y `codigos` es exactamente `["RN-AG-04"]`
- **AND** no se crea ningún turno

#### Scenario: E10 Borde - un turno que empieza o termina justo en el límite de la franja se acepta

- **GIVEN** un profesional con la franja lunes 09:00-13:00 del consultorio (12:00 a 16:00) y una prestación de 30 minutos
- **WHEN** se pide crear un turno con `inicio` 15:30 (termina 16:00, justo cuando termina la franja)
- **THEN** el sistema responde `201`
- **AND** si en cambio se pide con `inicio` 12:00 (empieza justo cuando empieza la franja), el sistema también responde `201`

#### Scenario: E10 Error de negocio - antes de la franja, entre franjas, en un día sin franjas o sin horario

- **GIVEN** un profesional con las franjas lunes 09:00-13:00 y lunes 15:00-19:00 del consultorio, y una prestación de 30 minutos
- **WHEN** se pide crear un turno con `inicio` 11:45 (08:45 del consultorio), otro con `inicio` 16:30 (13:30, entre las dos franjas) y otro con `inicio` `2026-11-07T13:00:00Z` (sábado)
- **THEN** cada pedido recibe `422` con `codigos` exactamente `["RN-AG-04"]`
- **AND** con un profesional sin ninguna franja, un turno con `inicio` 13:00 también recibe `422` con `["RN-AG-04"]`
- **AND** no se crea ningún turno

#### Scenario: E10 Borde - el día y la hora son los del consultorio, no los de UTC

- **GIVEN** un profesional con la franja lunes 21:00-23:00 del consultorio y una prestación de 30 minutos
- **WHEN** se pide crear un turno con `inicio` `2026-11-03T00:30:00Z` (martes en UTC, lunes 21:30 del consultorio)
- **THEN** el sistema responde `201`
- **AND** si la única franja del profesional es martes 21:00-23:00, el mismo pedido recibe `422` con `["RN-AG-04"]`

#### Scenario: E10 Borde - un turno que pasa de una franja a otra contigua se rechaza

- **GIVEN** un profesional con las franjas lunes 09:00-13:00 y lunes 13:00-17:00 del consultorio, y una prestación de 30 minutos
- **WHEN** se pide crear un turno con `inicio` 15:45 (12:45 a 13:15 del consultorio)
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-AG-04"]`, porque el turno no cae completo dentro de una sola franja

#### Scenario: E10 Borde - una franja fuera de vigencia no cuenta

- **GIVEN** un profesional cuya única franja es lunes 09:00-13:00 del consultorio con `vigente_hasta` 2026-10-31, guardada directo en la base, y una prestación de 30 minutos
- **WHEN** se pide crear un turno con `inicio` 13:00 (lunes 10:00 del consultorio, 2026-11-02)
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-AG-04"]` y no se crea ningún turno
- **AND** si la franja tiene en cambio `vigente_desde` 2026-11-02 y `vigente_hasta` nula, el mismo pedido responde `201`
- **AND** este escenario se verifica con el caso de uso sobre la base en memoria (la vigencia no se puede cargar por la API, D259)

#### Scenario: E10 Borde - un turno que termina justo a las 00:00 del consultorio no cabe en ninguna franja

- **GIVEN** un profesional cuya única franja es lunes 21:00-23:59 del consultorio, y una prestación de 30 minutos
- **WHEN** se pide crear un turno con `inicio` `2026-11-03T02:30:00Z` (lunes 23:30 a martes 00:00 del consultorio)
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-AG-04"]` y no `RN-AG-10d`, porque el turno no cruza la medianoche (intervalo semiabierto, D63) pero ninguna franja llega a las 00:00 (D265)
- **AND** si en cambio se pide con `inicio` `2026-11-03T02:00:00Z` (23:00 a 23:30 del consultorio), el sistema responde `201`

### Requirement: Orden de las reglas de negocio al crear un turno

El sistema SHALL evaluar las reglas de negocio de a una y solo con la entrada válida, en este orden: RN-AG-10d (el turno no cruza la medianoche del consultorio), RN-AG-04 (horario) y el solapamiento (RN-AG-05, RN-AG-08). La primera que falla SHALL ser la única que se informa (RN-GL-02). Es el orden de los pasos 4, 5 y 6 del Flujo 1 de `07` (RN-AG-10d y RN-AG-08 de `05`).

#### Scenario: E10 Borde - cruzar la medianoche se informa antes que el horario

- **GIVEN** un profesional cuya única franja es lunes 09:00-13:00 del consultorio, y una prestación de 30 minutos
- **WHEN** se pide crear un turno con `inicio` `2026-11-03T02:45:00Z` (23:45 a 00:15 del consultorio)
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-AG-10d"]`

#### Scenario: E10 Borde - el horario se informa antes que el solapamiento

- **GIVEN** un profesional cuya única franja es lunes 09:00-13:00 del consultorio, y un turno activo de ese profesional de 10:00 a 10:30 guardado antes de configurar el horario
- **WHEN** se pide crear un turno de 30 minutos con ese profesional con `inicio` 10:00
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-AG-04"]`, sin `conflictos`

#### Scenario: E10 Borde - con la entrada inválida no se evalúa el horario

- **GIVEN** un profesional cuya única franja es lunes 09:00-13:00 del consultorio
- **WHEN** se pide crear un turno con `prestacion_id` 999 y `inicio` 10:00 (fuera de la franja)
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-GL-04"]`
