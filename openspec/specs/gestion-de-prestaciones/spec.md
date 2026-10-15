# gestion-de-prestaciones Specification

## Purpose

Permite que el consultorio mantenga su catálogo de prestaciones (nombre, duración por defecto, color y si se ofrecen en la reserva online), con nombres únicos y duraciones que respetan la granularidad de la agenda, sin que editar una prestación cambie los turnos ya creados (US-001; RN-AG-01, RN-AG-02, RN-GL-03).

Convenciones de los escenarios: todos los horarios están en **UTC** y son del día 2026-11-02; «10:00» significa `2026-11-02T10:00:00Z`. Hay un solo consultorio por instalación (MVP) y las prestaciones son siempre las de ese consultorio. Las operaciones son `GET /prestaciones`, `POST /prestaciones` y `PATCH /prestaciones/{id}`, que desde el change de roles y protección del panel exigen un access token y el permiso de cada operación (D204; capability `proteccion-del-panel`). La granularidad de la agenda es la constante de **5 minutos** (D99). Un error sale como `application/problem+json` con la lista `codigos`. Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite por defecto.

## Requirements

### Requirement: Dar de alta una prestación

El sistema SHALL crear la prestación con `POST /prestaciones` y responder `201` con `id`, `nombre`, `duracion_minutos`, `color`, `reservable_online` y `activa`. La prestación nace activa y, si la petición no indica `reservable_online`, con `false`. `nombre`, `duracion_minutos` y `color` son obligatorios; `color` MUST ser un hex `#RRGGBB` (RN-AG-01).

#### Scenario: US-001 CA-1 Feliz - alta de una prestación

- **GIVEN** un consultorio sin ninguna prestación llamada «Blanqueamiento»
- **WHEN** se pide crear la prestación con `nombre` «Blanqueamiento», `duracion_minutos` 60 y `color` `#3A7BD5`
- **THEN** el sistema responde `201` con un `id` nuevo, esos tres valores, `reservable_online` `false` y `activa` `true`
- **AND** la prestación aparece en `GET /prestaciones`

#### Scenario: US-001 CA-1 Borde - el nombre se guarda sin espacios de más y se puede marcar como reservable

- **WHEN** se pide crear la prestación con `nombre` «  Control   de ortodoncia », `duracion_minutos` 30, `color` `#2E7D32` y `reservable_online` `true`
- **THEN** el sistema responde `201` con `nombre` «Control de ortodoncia» y `reservable_online` `true`

#### Scenario: US-001 CA-1 Error de formato - color inválido o campo faltante

- **WHEN** se pide crear una prestación con `color` «azul», o sin `nombre`, o con `nombre` vacío o solo de espacios
- **THEN** el sistema responde `422` con `codigos` vacío y un error que nombra el campo
- **AND** no se crea ninguna prestación

### Requirement: El nombre de la prestación es único en el consultorio

El sistema SHALL rechazar con `409` y el código `RN-AG-15` el alta o la edición que deje dos prestaciones del consultorio con el mismo nombre, activas o inactivas. Dos nombres SHALL considerarse iguales si coinciden sin distinguir mayúsculas, acentos ni espacios de más. El rechazo MUST NOT modificar nada.

#### Scenario: US-001 CA-1 Error de negocio - nombre repetido en el alta

- **GIVEN** una prestación activa llamada «Limpieza»
- **WHEN** se pide crear otra prestación con `nombre` «Limpieza»
- **THEN** el sistema responde `409` con `codigos` `["RN-AG-15"]` y un detalle que dice qué nombre ya existe
- **AND** sigue habiendo una sola prestación «Limpieza»

#### Scenario: US-001 CA-1 Borde - el nombre repetido se reconoce sin mayúsculas ni acentos, también entre inactivas

- **GIVEN** una prestación inactiva llamada «Obturación»
- **WHEN** se pide crear una prestación con `nombre` «obturacion»
- **THEN** el sistema responde `409` con `codigos` `["RN-AG-15"]`

#### Scenario: US-001 CA-1 Error de negocio - renombrar con el nombre de otra prestación

- **GIVEN** dos prestaciones, «Limpieza» y «Extracción»
- **WHEN** se pide editar «Extracción» con `nombre` «LIMPIEZA»
- **THEN** el sistema responde `409` con `codigos` `["RN-AG-15"]`
- **AND** «Extracción» conserva su nombre
- **AND** editar «Extracción» con su propio nombre, o cambiándole solo las mayúsculas a «extracción», responde `200`

### Requirement: La duración es mayor que 0 y múltiplo de la granularidad

El sistema SHALL rechazar con `422` y el código `RN-AG-01` el alta o la edición cuya `duracion_minutos` no sea mayor que 0 o no sea múltiplo de la granularidad de la agenda (5 minutos, D99). Es validación de entrada: se informa junto con los demás problemas de entrada de la petición y no se evalúa el nombre repetido. El rechazo MUST NOT modificar nada.

#### Scenario: US-001 CA-2 Feliz - una duración múltiplo de 5 se acepta

- **WHEN** se pide crear una prestación con `duracion_minutos` 45
- **THEN** el sistema responde `201` con `duracion_minutos` 45

#### Scenario: US-001 CA-2 Error de negocio - una duración que no es múltiplo de 5 se rechaza

- **WHEN** se pide crear una prestación con `duracion_minutos` 47
- **THEN** el sistema responde `422` con `codigos` `["RN-AG-01"]` y un error del campo `duracion_minutos` que dice que debe ser mayor que 0 y múltiplo de 5
- **AND** no se crea ninguna prestación

#### Scenario: US-001 CA-2 Borde - el mínimo, el cero y los negativos

- **WHEN** se pide crear una prestación con `duracion_minutos` 5
- **THEN** el sistema responde `201`
- **AND** con `duracion_minutos` 0 o -5 responde `422` con `codigos` `["RN-AG-01"]`

#### Scenario: US-001 CA-2 Borde - la edición valida la duración igual que el alta

- **GIVEN** una prestación «Limpieza» de 45 minutos
- **WHEN** se pide editarla con `duracion_minutos` 50
- **THEN** el sistema responde `200` con `duracion_minutos` 50
- **AND** editarla con `duracion_minutos` 52 responde `422` con `codigos` `["RN-AG-01"]` y la prestación sigue en 50

#### Scenario: US-001 CA-2 Borde - la duración inválida se informa antes que el nombre repetido

- **GIVEN** una prestación activa llamada «Limpieza»
- **WHEN** se pide crear otra prestación con `nombre` «Limpieza» y `duracion_minutos` 47
- **THEN** el sistema responde `422` con `codigos` `["RN-AG-01"]`, sin `RN-AG-15`

### Requirement: Listar las prestaciones del consultorio

El sistema SHALL devolver con `GET /prestaciones` y estado `200` todas las prestaciones del consultorio, activas e inactivas, ordenadas por `id`, cada una con `id`, `nombre`, `duracion_minutos`, `color`, `reservable_online` y `activa`.

#### Scenario: US-001 CA-1 Feliz - el listado incluye las inactivas

- **GIVEN** una prestación activa «Consulta / control» y una inactiva «Urgencia»
- **WHEN** se pide `GET /prestaciones`
- **THEN** el sistema responde `200` con las dos, en orden de `id`, con `activa` `true` y `false` respectivamente

#### Scenario: US-001 CA-1 Borde - un consultorio sin prestaciones devuelve una lista vacía

- **GIVEN** un consultorio sin prestaciones
- **WHEN** se pide `GET /prestaciones`
- **THEN** el sistema responde `200` con una lista vacía

### Requirement: Editar y desactivar una prestación

El sistema SHALL modificar con `PATCH /prestaciones/{id}` solo los campos que trae la petición (`nombre`, `duracion_minutos`, `color`, `reservable_online`, `activa`) y responder `200` con la prestación completa. Desactivar es `activa: false`; reactivar, `activa: true`. No hay borrado. Un id inexistente en la URL SHALL responder `404` con `RN-GL-04` (D166).

#### Scenario: US-001 CA-1 Feliz - editar el color sin tocar lo demás

- **GIVEN** una prestación «Limpieza» de 45 minutos, `color` `#3A7BD5`, activa
- **WHEN** se pide editarla con `color` `#F9A825`
- **THEN** el sistema responde `200` con `color` `#F9A825`, y `nombre`, `duracion_minutos`, `reservable_online` y `activa` sin cambios

#### Scenario: US-001 CA-1 Feliz - una prestación desactivada no admite turnos nuevos

- **GIVEN** una prestación activa «Extracción» y un turno de esa prestación de 10:00 a 10:45 en estado `reservado`
- **WHEN** se pide editarla con `activa` `false`
- **THEN** el sistema responde `200` con `activa` `false` y la prestación sigue en `GET /prestaciones`
- **AND** pedir un turno nuevo de esa prestación con `inicio` 11:00 responde `422` con `codigos` `["RN-GL-04"]` y la referencia `prestacion` con motivo `inactivo`
- **AND** el turno de las 10:00 sigue `reservado`, de 10:00 a 10:45
- **AND** editarla después con `activa` `true` vuelve a admitir el turno de las 11:00 (`201`)

#### Scenario: US-001 CA-1 Error de negocio - prestación inexistente en la URL

- **GIVEN** que no existe la prestación 999
- **WHEN** se pide editar la prestación 999 con `color` `#F9A825`
- **THEN** el sistema responde `404` con `codigos` `["RN-GL-04"]` y una referencia con `recurso` `prestacion`, `recurso_id` 999 y `motivo` `inexistente`

#### Scenario: US-001 CA-1 Borde - una edición mal formada no cambia nada

- **WHEN** se pide editar una prestación existente con un campo que no existe, con `nombre` nulo, o con `/prestaciones/abc`
- **THEN** el sistema responde `422` con `codigos` vacío y un error que nombra el campo
- **AND** la prestación no cambia

### Requirement: Cambiar la duración no modifica los turnos existentes

Cambiar la `duracion_minutos` de una prestación MUST NOT modificar el inicio, el fin ni la duración de los turnos ya creados con ella: quedan congelados al crearse (RN-AG-02, RN-GL-03). Los turnos que se creen después SHALL usar la duración nueva.

#### Scenario: US-001 CA-3 Feliz - el turno existente conserva su fin y el nuevo usa la duración nueva

- **GIVEN** una prestación «Consulta / control» de 30 minutos y un turno de esa prestación de 10:00 a 10:30
- **WHEN** se edita la prestación con `duracion_minutos` 60
- **THEN** el turno de las 10:00 sigue de 10:00 a 10:30, con `duracion_minutos` 30
- **AND** un turno nuevo de esa prestación, con el mismo profesional y el mismo sillón, con `inicio` 10:30 responde `201` con `fin` 11:30 y `duracion_minutos` 60

#### Scenario: US-001 CA-3 Borde - el horario que liberaría el turno viejo no se libera

- **GIVEN** una prestación de 60 minutos y un turno de esa prestación de 10:00 a 11:00
- **WHEN** se edita la prestación con `duracion_minutos` 30
- **AND** se pide un turno nuevo de esa prestación con el mismo profesional y el mismo sillón con `inicio` 10:30
- **THEN** el sistema responde `409` con `codigos` `["RN-AG-05", "RN-AG-08"]`, porque el turno de las 10:00 sigue terminando a las 11:00

#### Scenario: US-001 CA-3 Borde - editar la prestación no agrega eventos al historial del turno

- **GIVEN** un turno creado con `POST /turnos`, con su evento `creado`
- **WHEN** se edita la duración de su prestación
- **THEN** el historial del turno sigue teniendo un solo evento, el `creado`
