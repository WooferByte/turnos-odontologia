## ADDED Requirements

### Requirement: Rechazar el turno que interseca un bloqueo

El sistema SHALL rechazar con `422` y `codigos` `["RN-AG-04b"]`, sin crear nada, el turno cuyo `[inicio, fin)` interseca un bloqueo de su profesional, de su sillón o de todo su consultorio (RN-AG-04b, RN-AG-09; E10). Un bloqueo de otro profesional o de otro sillón no lo afecta, y uno contiguo no interseca. El error SHALL llevar `type` `/errores/sobre-bloqueo` y `bloqueo_id`, el id del bloqueo intersecado que empieza primero y, con el mismo `inicio`, el de menor `id` (D280, como D129). Salvo que un escenario diga otra cosa, en esta capability no hay bloqueos.

#### Scenario: E10 Error de negocio - un turno sobre un bloqueo del profesional se rechaza

- **GIVEN** un profesional con una franja que cubre el turno pedido y un bloqueo de ese profesional de 10:00 a 12:00, y una prestación de 30 minutos
- **WHEN** se pide crear un turno con ese profesional y `inicio` 10:30
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-AG-04b"]`, `type` `/errores/sobre-bloqueo` y `bloqueo_id` igual al id del bloqueo del profesional
- **AND** no se crea ningún turno ni evento

#### Scenario: E10 Error de negocio - un bloqueo del sillón rechaza el turno de cualquier profesional

- **GIVEN** dos profesionales activos con franjas que cubren el turno pedido, el sillón 1 con un bloqueo de 10:00 a 12:00 y el sillón 2 sin bloqueos
- **WHEN** se pide crear un turno del segundo profesional en el sillón 1 con `inicio` 11:00
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-AG-04b"]`
- **AND** el mismo pedido en el sillón 2 responde `201`

#### Scenario: E10 Error de negocio - un bloqueo de todo el consultorio rechaza cualquier turno

- **GIVEN** un profesional con una franja que cubre el turno pedido, un bloqueo de todo el consultorio de 10:00 a 12:00 y una prestación de 30 minutos
- **WHEN** se pide crear un turno con ese profesional e `inicio` 11:30 (termina 12:00)
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-AG-04b"]`

#### Scenario: E10 Borde - un turno contiguo al bloqueo se acepta y un minuto de intersección se rechaza

- **GIVEN** un profesional con una franja que cubre los turnos pedidos, un bloqueo de ese profesional de 10:00 a 12:00 y una prestación de 30 minutos
- **WHEN** se pide crear un turno con `inicio` 09:30 (termina justo cuando empieza el bloqueo) y otro con `inicio` 12:00 (empieza justo cuando termina)
- **THEN** los dos pedidos responden `201`
- **AND** un turno con `inicio` 09:31 (un minuto dentro del bloqueo) responde `422` con `["RN-AG-04b"]`

#### Scenario: E10 Borde - un bloqueo de otro profesional no afecta y eliminado el bloqueo el turno se crea

- **GIVEN** dos profesionales activos con franjas que cubren el turno pedido, en sillones distintos, y un bloqueo del segundo profesional de 10:00 a 12:00
- **WHEN** se pide crear un turno del primer profesional con `inicio` 10:30
- **THEN** el sistema responde `201`
- **AND** después de que la odontóloga elimina el bloqueo con `DELETE /bloqueos/<id>`, un turno del segundo profesional con `inicio` 10:30 también responde `201`

#### Scenario: E10 Borde - con dos bloqueos que intersecan se informa el que empieza primero

- **GIVEN** un profesional con una franja que cubre el turno pedido, una prestación de 30 minutos, un bloqueo de todo el consultorio de 11:00 a 12:00 guardado primero (id menor) y un bloqueo de ese profesional de 10:00 a 12:00 guardado después
- **WHEN** se pide crear un turno con ese profesional e `inicio` 11:00
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-AG-04b"]` y `bloqueo_id` igual al id del bloqueo del profesional (empieza primero)
- **AND** con dos bloqueos del profesional que empiezan los dos a las 10:00, el `bloqueo_id` es el del de menor `id` (D280)

## MODIFIED Requirements

### Requirement: Orden de las reglas de negocio al crear un turno

El sistema SHALL evaluar las reglas de negocio de a una y solo con la entrada válida, en este orden: RN-AG-10d (el turno no cruza la medianoche del consultorio), RN-AG-04 (horario), RN-AG-04b (bloqueos) y el solapamiento (RN-AG-05, RN-AG-08). La primera que falla SHALL ser la única que se informa (RN-GL-02). Es el orden de los pasos 4, 5 y 6 del Flujo 1 de `07` (RN-AG-10d y RN-AG-08 de `05`); dentro del paso 5, el horario va antes que los bloqueos (D280).

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

#### Scenario: E10 Borde - el horario se informa antes que el bloqueo

- **GIVEN** un profesional cuya única franja es lunes 09:00-13:00 del consultorio y un bloqueo de ese profesional de 10:00 a 12:00
- **WHEN** se pide crear un turno de 30 minutos con ese profesional con `inicio` 10:30 (07:30 del consultorio, fuera de la franja y dentro del bloqueo)
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-AG-04"]`

#### Scenario: E10 Borde - el bloqueo se informa antes que el solapamiento

- **GIVEN** un profesional con una franja que cubre el turno pedido, un turno activo de ese profesional de 10:00 a 10:30 y un bloqueo de ese profesional de 10:00 a 12:00 creado después del turno
- **WHEN** se pide crear un turno de 30 minutos con ese profesional con `inicio` 10:00
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-AG-04b"]`, sin `conflictos`

#### Scenario: E10 Borde - con la entrada inválida no se evalúa el bloqueo

- **GIVEN** un bloqueo de todo el consultorio de 10:00 a 12:00
- **WHEN** se pide crear un turno con `sillon_id` 999 e `inicio` 10:30
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-GL-04"]`
