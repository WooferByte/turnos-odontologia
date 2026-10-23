## MODIFIED Requirements

### Requirement: Crear un turno reservado con fin calculado

El sistema SHALL crear el turno en estado `reservado` cuando cae completo en una franja del horario del profesional (RN-AG-04) y no hay conflicto, y responder `201`, con `fin = inicio + duración de la prestación` (RN-AG-02), ocupando un profesional y un sillón (RN-AG-06). El consultorio del turno SHALL ser el del profesional. Si la petición no indica el profesional o el sillón, el sistema SHALL usar el único activo del consultorio (RN-AG-14). `inicio` MUST ser una fecha-hora con zona en UTC (RN-GL-01).

#### Scenario: E1 Feliz - hueco libre

- **GIVEN** un profesional con una franja del lunes que cubre de 10:00 a 11:00 (07:00 a 08:00 del consultorio) y un sillón activos, sin turnos entre las 10:00 y las 11:00, y una prestación activa de 30 minutos
- **WHEN** se pide crear un turno de esa prestación para un paciente existente con `inicio` 10:00, ese profesional y ese sillón
- **THEN** el sistema responde `201` con el turno en estado `reservado`, `inicio` 10:00, `fin` 10:30 y `duracion_minutos` 30
- **AND** el turno queda guardado con el consultorio del profesional

## ADDED Requirements

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
