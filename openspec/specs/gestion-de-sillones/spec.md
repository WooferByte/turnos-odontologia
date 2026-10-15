# gestion-de-sillones Specification

## Purpose

Permite que el consultorio mantenga sus sillones como recurso de la agenda (alta, listado, renombre, desactivación y reactivación), y fija cómo el estado de los sillones decide el sillón de un turno nuevo: el sillón inactivo no admite turnos (RN-AG-07) y el sillón por defecto es el único activo, no un id fijo (RN-AG-06, RN-AG-14; US-004).

Convenciones de los escenarios: todos los horarios están en **UTC** y son del día 2026-11-02; «10:00» significa `2026-11-02T10:00:00Z`. Hay un solo consultorio por instalación (MVP, D173) y los sillones son siempre los de ese consultorio. Las operaciones son `GET /sillones`, `POST /sillones` y `PATCH /sillones/{id}`, que desde el change de roles y protección del panel exigen un access token y el permiso de cada operación (D204; capability `proteccion-del-panel`); los turnos se piden con `POST /turnos` (capability `creacion-de-turnos`). Un error sale como `application/problem+json` con la lista `codigos`. Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite por defecto, salvo que digan otra cosa.

## Requirements

### Requirement: Dar de alta un sillón

El sistema SHALL crear el sillón con `POST /sillones` y responder `201` con `id`, `nombre` y `activo`. El sillón nace activo (RN-AG-06). `nombre` es obligatorio y SHALL guardarse sin espacios en los extremos ni espacios internos repetidos; un nombre vacío o solo de espacios, un campo de más (incluido `activo`) o un tipo erróneo son de formato y se rechazan con `422` sin código RN. El rechazo MUST NOT crear nada.

#### Scenario: US-004 CA-3 Feliz - alta de un segundo sillón

- **GIVEN** un consultorio con el sillón «Sillón 1» activo
- **WHEN** se pide crear un sillón con `nombre` «Sillón 2»
- **THEN** el sistema responde `201` con un `id` nuevo, `nombre` «Sillón 2» y `activo` `true`
- **AND** `GET /sillones` devuelve los dos

#### Scenario: US-004 CA-3 Borde - el nombre se guarda sin espacios de más

- **WHEN** se pide crear un sillón con `nombre` «  Box   de cirugía »
- **THEN** el sistema responde `201` con `nombre` «Box de cirugía»

#### Scenario: US-004 CA-3 Error de formato - nombre vacío, faltante o campo de más

- **WHEN** se pide crear un sillón sin `nombre`, o con `nombre` «   », o con `activo` `false` en el cuerpo
- **THEN** el sistema responde `422` con `codigos` vacío y un error que nombra el campo
- **AND** no se crea ningún sillón

### Requirement: Listar los sillones del consultorio

El sistema SHALL devolver con `GET /sillones` y estado `200` todos los sillones del consultorio, activos e inactivos, ordenados por `id`, cada uno con `id`, `nombre` y `activo`.

#### Scenario: US-004 CA-3 Feliz - el listado incluye los inactivos

- **GIVEN** un sillón activo «Sillón 1» y un sillón inactivo «Sillón 2»
- **WHEN** se pide `GET /sillones`
- **THEN** el sistema responde `200` con los dos, en orden de `id`, con `activo` `true` y `false` respectivamente

#### Scenario: US-004 CA-3 Borde - un consultorio sin sillones devuelve una lista vacía

- **GIVEN** un consultorio sin sillones
- **WHEN** se pide `GET /sillones`
- **THEN** el sistema responde `200` con una lista vacía

### Requirement: Editar, desactivar y reactivar un sillón

El sistema SHALL modificar con `PATCH /sillones/{id}` solo los campos que trae la petición (`nombre`, `activo`) y responder `200` con el sillón completo. Desactivar es `activo: false`; reactivar, `activo: true`. No hay borrado. El nombre editado SHALL normalizarse igual que en el alta. Un id inexistente en la URL SHALL responder `404` con `RN-GL-04` (D166). Una edición mal formada (campo de más, `null` explícito, nombre vacío, id de la ruta que no es entero) SHALL responder `422` sin código RN y MUST NOT cambiar nada. Editar un sillón MUST NOT modificar los turnos que ya lo usan.

#### Scenario: US-004 CA-3 Feliz - renombrar sin tocar lo demás

- **GIVEN** un sillón activo «Sillón 2»
- **WHEN** se pide editarlo con `nombre` «Box 2»
- **THEN** el sistema responde `200` con `nombre` «Box 2» y `activo` `true`

#### Scenario: US-004 CA-3 Error de negocio - sillón inexistente en la URL

- **GIVEN** que no existe el sillón 999
- **WHEN** se pide editar el sillón 999 con `activo` `false`
- **THEN** el sistema responde `404` con `codigos` `["RN-GL-04"]` y una referencia con `recurso` `sillon`, `recurso_id` 999 y `motivo` `inexistente`

#### Scenario: US-004 CA-3 Borde - una edición mal formada no cambia nada

- **WHEN** se pide editar un sillón existente con un campo que no existe, con `activo` nulo, con `nombre` «  », o con `/sillones/abc`
- **THEN** el sistema responde `422` con `codigos` vacío y un error que nombra el campo
- **AND** el sillón no cambia

#### Scenario: US-004 CA-3 Borde - una edición vacía responde el sillón sin cambios

- **WHEN** se pide editar un sillón existente con el cuerpo `{}`
- **THEN** el sistema responde `200` con el sillón tal como estaba

### Requirement: Un sillón inactivo no admite turnos nuevos

Un turno nuevo que indica un sillón inactivo SHALL rechazarse con `422`, el código `RN-GL-04` y la referencia `sillon` con motivo `inactivo` (RN-AG-07, RN-GL-04); es validación de entrada y se informa junto con las demás referencias inválidas de la petición. Desactivar un sillón MUST NOT modificar ni cancelar los turnos que ya lo usan, y reactivarlo SHALL volver a admitir turnos nuevos en él.

#### Scenario: US-004 CA-3 Feliz - desactivar rechaza los turnos nuevos y conserva los existentes

- **GIVEN** dos sillones activos, «Sillón 1» y «Sillón 2», y un turno `reservado` de 10:00 a 10:30 en el «Sillón 2»
- **WHEN** se pide editar el «Sillón 2» con `activo` `false`
- **THEN** el sistema responde `200` con `activo` `false` y el sillón sigue en `GET /sillones`
- **AND** pedir un turno con `sillon_id` del «Sillón 2» e `inicio` 11:00 responde `422` con `codigos` `["RN-GL-04"]` y la referencia `sillon` con su id y motivo `inactivo`
- **AND** el turno de las 10:00 sigue `reservado`, de 10:00 a 10:30, en el «Sillón 2»

#### Scenario: US-004 CA-3 Borde - reactivar vuelve a admitir turnos

- **GIVEN** el «Sillón 2» inactivo
- **WHEN** se pide editarlo con `activo` `true`
- **THEN** pedir un turno con `sillon_id` del «Sillón 2» e `inicio` 11:00 responde `201` en ese sillón

#### Scenario: US-004 CA-3 Borde - el sillón inactivo se informa junto con otra referencia inválida

- **GIVEN** el «Sillón 2» inactivo
- **WHEN** se pide un turno con `sillon_id` del «Sillón 2» y `prestacion_id` 999
- **THEN** el sistema responde un único `422` con `codigos` `["RN-GL-04"]` y `referencias` lista las dos: la prestación (`inexistente`) y el sillón (`inactivo`)

### Requirement: El sillón por defecto es el único activo

Si la petición de un turno no indica `sillon_id`, el sistema SHALL usar el único sillón activo del consultorio (RN-AG-06, RN-AG-14); el sillón por defecto MUST NOT ser un id fijo ni una marca guardada: sale de contar los activos en el momento de la petición. Con más de un sillón activo, omitir el sillón SHALL rechazarse con `422`, `RN-GL-04` y la referencia `sillon` sin id y con motivo `varios_activos` (D138); sin ningún sillón activo, con motivo `ninguno_activo`. Son validación de entrada (RN-GL-02) y no persisten nada.

#### Scenario: US-004 CA-1 Feliz - con un único sillón activo, el turno sin sillón va a ese

- **GIVEN** el «Sillón 1» activo como único sillón, y un profesional activo
- **WHEN** se pide un turno sin `sillon_id` con `inicio` 10:00
- **THEN** el sistema responde `201` con el turno en el «Sillón 1»

#### Scenario: US-004 CA-1 Error de negocio - con dos sillones activos hay que indicarlo

- **GIVEN** los sillones activos «Sillón 1» y «Sillón 2», este último dado de alta con `POST /sillones`
- **WHEN** se pide un turno sin `sillon_id` con `inicio` 10:00
- **THEN** el sistema responde `422` con `codigos` `["RN-GL-04"]` y la referencia `sillon` con `recurso_id` nulo y `motivo` `varios_activos`
- **AND** no se crea ningún turno
- **AND** la misma petición con `sillon_id` del «Sillón 2» responde `201` en ese sillón

#### Scenario: US-004 CA-1 Borde - el por defecto no es un id fijo

- **GIVEN** los sillones «Sillón 1» y «Sillón 2», ambos activos
- **WHEN** se desactiva el «Sillón 1» y se pide un turno sin `sillon_id` con `inicio` 10:00
- **THEN** el sistema responde `201` con el turno en el «Sillón 2», el único activo

#### Scenario: US-004 CA-1 Borde - sin sillones activos no hay por defecto

- **GIVEN** que el único sillón del consultorio se desactivó
- **WHEN** se pide un turno sin `sillon_id` con `inicio` 10:00
- **THEN** el sistema responde `422` con `codigos` `["RN-GL-04"]` y la referencia `sillon` con `recurso_id` nulo y `motivo` `ninguno_activo`

### Requirement: Varios sillones se ocupan por separado

Con más de un sillón activo, el sistema SHALL controlar el solapamiento de cada sillón por separado (RN-AG-06, RN-AG-08): dos turnos a la misma hora en sillones distintos y con profesionales distintos SHALL admitirse, y un turno que choca con otro del mismo sillón SHALL rechazarse con `409` y `RN-AG-08`. Un sillón dado de alta con `POST /sillones` SHALL comportarse igual que el del seed.

#### Scenario: US-004 CA-2 Feliz - dos profesionales a la misma hora en sillones distintos

- **GIVEN** los sillones activos «Sillón 1» y «Sillón 2» (este, dado de alta con `POST /sillones`), los profesionales A y B, y un turno `reservado` de 10:00 a 10:30 del profesional A en el «Sillón 1»
- **WHEN** se pide un turno de 30 minutos del profesional B en el «Sillón 2» con `inicio` 10:00
- **THEN** el sistema responde `201` con el turno en el «Sillón 2»

#### Scenario: US-004 CA-2 Error de negocio - el sillón nuevo también se ocupa

- **GIVEN** un turno `reservado` de 10:00 a 10:30 del profesional B en el «Sillón 2», dado de alta con `POST /sillones`
- **WHEN** se pide un turno de 30 minutos del profesional A en el «Sillón 2» con `inicio` 10:15
- **THEN** el sistema responde `409` con `codigos` `["RN-AG-08"]` y el conflicto con `recurso` `sillon`, el id del «Sillón 2» y el id del turno existente

#### Scenario: US-004 CA-2 Borde - el alta tras el seed no choca con el id fijo en PostgreSQL

- **GIVEN** la API sobre PostgreSQL con el seed de la demo («Sillón 1» con id 1)
- **WHEN** se pide crear un sillón con `POST /sillones`
- **THEN** el sistema responde `201` con un `id` distinto de 1
- **AND** este escenario se verifica en el perfil opcional `postgres`
