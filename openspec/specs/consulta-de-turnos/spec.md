# consulta-de-turnos Specification

## Purpose

Define cómo la API devuelve los turnos de un día del consultorio y un turno por su id, con el paciente, la prestación y el estado que necesita la agenda del panel, para los tres roles y con los mismos rechazos de acceso que el resto del panel (US-011 CA-1; RN-GL-01, RN-GL-02, RN-GL-04, RN-AU-05).

Convenciones de los escenarios: todos los instantes están en **UTC**; el consultorio es el único de la instalación (D173), con `zona_horaria` `America/Argentina/Buenos_Aires` (UTC−3, sin horario de verano en 2026), así que el día `2026-11-02` del consultorio va de `2026-11-02T03:00:00Z` (incluido) a `2026-11-03T03:00:00Z` (excluido). «Con el token de X» significa con la cabecera `Authorization: Bearer <access token>` de un access token vigente emitido para X por `POST /auth/login`. «El `401` de sesión inválida» y «el `403` de permiso insuficiente» son las respuestas fijas de `proteccion-del-panel` (`RN-AU-03`, D206; `RN-AU-05`, D207). Un error sale como `application/problem+json` con `codigos`. Datos de partida, todos ficticios (RN-PR-01): el profesional 1 y el sillón 1, activos; los pacientes 1 «Ana Ejemplo», 2 «Bruno Ficticio» y 3 «Carla Inventada»; las prestaciones 1 «Consulta / control» (30 min, `#1E88E5`), 2 «Limpieza» (45 min, `#43A047`) y 3 «Obturación» (60 min, `#FB8C00`); «la odontóloga» (`odontologo` + `dueno`), «la recepcionista» (`recepcionista`), «el dueño» (solo `dueno`) y «el usuario sin roles». Los turnos de partida se cargan directamente en la base del test, con el estado que dice el escenario. El contrato de la respuesta, el día por defecto, los estados que se listan, los datos del paciente, el permiso y el rechazo de `fecha` son decisiones del autor (D316 a D318, D321 y D322; 2026-10-28). En la v1 el consultorio tiene un solo profesional, así que «los turnos del profesional» de US-011 CA-1 son los del consultorio (D316). El `estado` que se devuelve es el almacenado (D317). Cada escenario tiene un ID propio (`AGE-1a`…) que lleva el nombre de su test. Los escenarios se verifican en la suite por defecto.

## Requirements

### Requirement: La agenda de un día lista sus turnos ordenados por inicio

`GET /turnos?fecha=aaaa-mm-dd` SHALL responder `200` con `fecha`, `zona_horaria` y `turnos`: los turnos del consultorio del usuario del token cuyo `inicio` cae en ese día del consultorio, en cualquier estado, ordenados por `inicio` y, a igual inicio, por `id` (US-011 CA-1). Cada turno SHALL traer `id`, `inicio`, `fin`, `duracion_minutos`, `estado`, `profesional_id`, `sillon_id`, `paciente` (`id`, `nombre`, `apellido`) y `prestacion` (`id`, `nombre`, `color`), y MUST NOT traer otros datos del paciente (RN-PR-01). La ruta MUST NOT cambiar nada.

#### Scenario: AGE-1a Feliz - la odontóloga ve el día ordenado con paciente, prestación y estado

- **GIVEN** en la base tres turnos del profesional 1 y el sillón 1, cargados en este orden: el de Carla Inventada con «Obturación» de `2026-11-02T14:00:00Z` a `15:00:00Z`, `confirmado`; el de Ana Ejemplo con «Consulta / control» de `2026-11-02T12:00:00Z` a `12:30:00Z`, `reservado`; y el de Bruno Ficticio con «Limpieza» de `2026-11-02T13:00:00Z` a `13:45:00Z`, `reservado`
- **WHEN** la odontóloga pide `GET /turnos?fecha=2026-11-02` con su token
- **THEN** el sistema responde `200` con `fecha` `2026-11-02`, `zona_horaria` `America/Argentina/Buenos_Aires` y tres turnos en este orden: Ana Ejemplo, Bruno Ficticio, Carla Inventada
- **AND** el primero es exactamente `{"id": <id>, "inicio": "2026-11-02T12:00:00Z", "fin": "2026-11-02T12:30:00Z", "duracion_minutos": 30, "estado": "reservado", "profesional_id": 1, "sillon_id": 1, "paciente": {"id": 1, "nombre": "Ana", "apellido": "Ejemplo"}, "prestacion": {"id": 1, "nombre": "Consulta / control", "color": "#1E88E5"}}`
- **AND** ningún turno trae el teléfono ni otro dato del paciente, y la base queda como estaba

#### Scenario: AGE-1b Borde - el día es el del consultorio, no el de UTC

- **GIVEN** en la base tres turnos `reservado`: uno de `2026-11-02T02:30:00Z` a `03:00:00Z` (23:30 del 1 de noviembre en el consultorio), uno de `2026-11-02T03:00:00Z` a `03:30:00Z` (00:00 del 2) y uno de `2026-11-03T02:30:00Z` a `03:00:00Z` (23:30 del 2)
- **WHEN** la odontóloga pide `GET /turnos?fecha=2026-11-02`
- **THEN** el sistema responde `200` con los dos últimos, en ese orden, y sin el primero
- **AND** `GET /turnos?fecha=2026-11-01` responde solo el primero

#### Scenario: AGE-1c Borde - sin fecha se lista el día de hoy del consultorio

- **GIVEN** el reloj de la API en `2026-11-03T01:00:00Z` (22:00 del 2 de noviembre en el consultorio) y en la base el turno de Ana Ejemplo de `2026-11-02T12:00:00Z` a `12:30:00Z`
- **WHEN** la recepcionista pide `GET /turnos` sin parámetros
- **THEN** el sistema responde `200` con `fecha` `2026-11-02` y el turno de Ana Ejemplo
- **AND** con el reloj en `2026-11-03T03:00:00Z` la misma petición responde `fecha` `2026-11-03` y `turnos` vacío

#### Scenario: AGE-1d Borde - un día sin turnos, un turno cancelado y una prestación inactiva

- **GIVEN** en la base un turno `cancelado_paciente` de Bruno Ficticio con «Limpieza» de `2026-11-04T13:00:00Z` a `13:45:00Z` y un turno `reservado` de Ana Ejemplo con «Obturación» de `2026-11-04T15:00:00Z` a `16:00:00Z`, y la prestación «Obturación» desactivada después de dar el turno
- **WHEN** la odontóloga pide `GET /turnos?fecha=2026-11-04` y después `GET /turnos?fecha=2026-11-05`
- **THEN** la primera respuesta es `200` con los dos turnos: el cancelado con `estado` `cancelado_paciente` y el otro con `prestacion` `{"id": 3, "nombre": "Obturación", "color": "#FB8C00"}`
- **AND** la segunda es `200` con `fecha` `2026-11-05` y `turnos` vacío

#### Scenario: AGE-1e Feliz - la recepcionista y el dueño leen la agenda

- **GIVEN** en la base el turno de Ana Ejemplo de `2026-11-02T12:00:00Z` a `12:30:00Z`
- **WHEN** la recepcionista y después el dueño piden `GET /turnos?fecha=2026-11-02` con su token
- **THEN** las dos respuestas son `200` con el mismo cuerpo, con el turno de Ana Ejemplo (matriz de `03`, fila Turnos: «R» para el dueño)

#### Scenario: AGE-1f Borde - a igual inicio, los turnos salen por id

- **GIVEN** en la base dos turnos con el mismo horario, de `2026-11-04T13:00:00Z` a `13:45:00Z`, cargados con id explícito y en este orden: primero el `reservado` de Ana Ejemplo con «Limpieza» e id 20, después el `cancelado_paciente` de Bruno Ficticio con «Limpieza» e id 10
- **WHEN** la odontóloga pide `GET /turnos?fecha=2026-11-04`
- **THEN** el sistema responde `200` con los dos turnos en este orden: el de id 10 (Bruno Ficticio) y el de id 20 (Ana Ejemplo)

### Requirement: Un turno se lee por su id

`GET /turnos/{id}` SHALL responder `200` con el turno en la misma forma que un elemento de `turnos` de la agenda del día. Un id que no existe o que es de un turno de otro consultorio SHALL responder `404` con `codigos` `["RN-GL-04"]` y la referencia `turno` / id / `inexistente` (D73, D166); un id que no es un número entero, `422` con `codigos` vacío. La ruta MUST NOT cambiar nada.

#### Scenario: AGE-2a Feliz - la recepcionista lee un turno

- **GIVEN** en la base el turno de Bruno Ficticio con «Limpieza» de `2026-11-02T13:00:00Z` a `13:45:00Z`, `reservado`
- **WHEN** la recepcionista pide `GET /turnos/<id de ese turno>` con su token
- **THEN** el sistema responde `200` con `inicio` `2026-11-02T13:00:00Z`, `fin` `2026-11-02T13:45:00Z`, `duracion_minutos` 45, `estado` `reservado`, `paciente` `{"id": 2, "nombre": "Bruno", "apellido": "Ficticio"}` y `prestacion` `{"id": 2, "nombre": "Limpieza", "color": "#43A047"}`

#### Scenario: AGE-2b Error de negocio - un turno que no existe o una ruta mal formada

- **GIVEN** en la base ningún turno con id 999
- **WHEN** la odontóloga pide `GET /turnos/999` y después `GET /turnos/abc`
- **THEN** la primera respuesta es `404` con `codigos` `["RN-GL-04"]` y `referencias` `[{"recurso": "turno", "recurso_id": 999, "motivo": "inexistente"}]`
- **AND** la segunda es `422` con `codigos` vacío

### Requirement: Solo se listan los turnos del consultorio del usuario

El consultorio de las dos rutas SHALL ser el del usuario del token (D270): un turno de otro consultorio MUST NOT aparecer en la agenda del día y su id SHALL responder como inexistente (`404` `RN-GL-04`), sin revelar que existe.

#### Scenario: AGE-3c Borde - un turno de otro consultorio no se ve

- **GIVEN** en la base un segundo consultorio con su profesional, su sillón, su paciente y un turno de `2026-11-02T12:00:00Z` a `12:30:00Z`, además del turno de Ana Ejemplo a la misma hora en el consultorio de la odontóloga
- **WHEN** la odontóloga pide `GET /turnos?fecha=2026-11-02` y `GET /turnos/<id del turno del otro consultorio>`
- **THEN** la agenda trae solo el turno de Ana Ejemplo
- **AND** la segunda respuesta es `404` con `codigos` `["RN-GL-04"]`, igual que para un id que no existe

### Requirement: Una fecha mal formada se rechaza como validación de entrada

`fecha` SHALL ser una fecha de calendario `aaaa-mm-dd`, sin hora ni zona, entre `0001-01-02` y `9999-12-30`: es un día del consultorio (RN-GL-01, D316) y, pasado a UTC, tiene que caber en una fecha-hora para cualquier zona (D322). Cualquier otro valor, incluidos `0001-01-01` y `9999-12-31`, SHALL responder `422` con `codigos` vacío y el campo `fecha` en `errores` (validación de entrada, RN-GL-02), sin listar turnos y nunca un `500`.

#### Scenario: AGE-3a Error de entrada - fechas que no son un día o están en los extremos del calendario

- **WHEN** la odontóloga pide `GET /turnos?fecha=2026-13-01`, `GET /turnos?fecha=02/11/2026`, `GET /turnos?fecha=2026-11-02T03:00:00Z`, `GET /turnos?fecha=0001-01-01` y `GET /turnos?fecha=9999-12-31`
- **THEN** las cinco respuestas son `422` con `codigos` vacío, un error con `campo` `fecha` y sin `turnos`
- **AND** `GET /turnos?fecha=0001-01-02` y `GET /turnos?fecha=9999-12-30` responden `200` con `turnos` vacío

### Requirement: Leer turnos exige sesión y un rol del panel

Las dos rutas SHALL exigir el access token (`proteccion-del-panel`) y el permiso nuevo de leer turnos, que tienen los tres roles (`03`, fila Turnos). Sin sesión válida SHALL responder el `401` de sesión inválida; un usuario sin roles, el `403` de permiso insuficiente (`RN-AU-05`). El control de acceso SHALL evaluarse antes que la validación de `fecha` y del id (D208).

#### Scenario: AGE-3b Error de negocio - sin sesión o sin roles no se lee la agenda

- **WHEN** se pide `GET /turnos?fecha=2026-11-02` sin cabecera `Authorization`, y el usuario sin roles pide `GET /turnos?fecha=2026-11-02`, `GET /turnos?fecha=mal` y `GET /turnos/1` con su token
- **THEN** la primera respuesta es el `401` de sesión inválida con `codigos` `["RN-AU-03"]`
- **AND** las otras tres son el `403` de permiso insuficiente con `codigos` `["RN-AU-05"]`, sin turnos ni datos de pacientes
