## Purpose

Define cómo la API marca desde el panel si el paciente asistió a un turno (`atendido` o `ausente`), libera su horario, registra el evento `estado_cambiado` en su historial y deja de considerar nuevo al paciente con su primer `atendido`, con los mismos rechazos de acceso que el resto del panel (US-014 CA-1, CA-2, CA-3, CA-4, CA-6 y CA-11; RN-AG-10, RN-AG-11, RN-AG-12, RN-AG-13, RN-TD-05).

Convenciones de los escenarios: todos los instantes están en **UTC** y se escriben con `Z`; los turnos son del lunes 2026-11-02 salvo que se diga otra cosa («13:00» significa `2026-11-02T13:00:00Z`, las 10:00 del consultorio) y, salvo que el escenario diga otra cosa, el reloj de la API marca `2026-11-02T13:10:00Z`. El consultorio es el único de la instalación (D173), con `zona_horaria` `America/Argentina/Buenos_Aires` (UTC−3). Datos de partida, todos ficticios (RN-PR-01): el profesional 1 y el sillón 1, activos y únicos, con horario de lunes a viernes de 08:00 a 20:00 del consultorio (`11:00Z` a `23:00Z`); los pacientes 1 «Ana Ejemplo» y 2 «Bruno Ficticio», los dos con `es_nuevo` `true` y sin turnos `atendido`, y el paciente 3 «Carla Inventada», con `es_nuevo` `false` porque ya tiene un turno `atendido` (el del lunes 26 de octubre de 12:00 a 12:30, cargado con la fábrica de tests; así ningún dato de partida contradice D52); las prestaciones 1 «Consulta / control» (30 min) y 2 «Limpieza» (45 min); «la odontóloga» (`odontologo` + `dueno`, usuario 1), «la recepcionista» (`recepcionista`, usuario 2), «el dueño» (solo `dueno`) y «el usuario sin roles». «El turno de Ana» es un turno `reservado` de Ana Ejemplo con «Consulta / control», del profesional 1 y el sillón 1, de 13:00 a 13:30, con su evento `creado`. «Con el token de X» significa con la cabecera `Authorization: Bearer <access token>` vigente de X. «El `401` de sesión inválida» y «el `403` de permiso insuficiente» son las respuestas fijas de `proteccion-del-panel` (`RN-AU-03`, D206; `RN-AU-05`, D207). Un error sale como `application/problem+json` con `codigos`. «El turno no cambia» significa que `GET /turnos/{id}` devuelve el mismo `estado`, `inicio` y `fin` que antes de la petición y que su historial no suma eventos. Los turnos que la API no puede crear (en estados distintos de `reservado`, que ya empezaron según el reloj del escenario o de otro consultorio) se cargan directo en la base con la fábrica de tests, con su evento `creado`. `es_nuevo` no viaja por la API en este change: los escenarios que lo miran se verifican a nivel de caso de uso, leyendo el paciente con el repositorio. Las elecciones de este spec que no fijaba la KB son **decisiones del autor** del 2026-10-30 (Q2 a Q9 del design, D355 a D362): entre ellas, el cuerpo `{"estado"}`, el `409` de `RN-AG-13`, el orden de evaluación, el permiso `turnos.marcar`, el tipo `estado_cambiado` y el relleno de `es_nuevo`. El marcado usa el estado **almacenado** del turno (D317). Cada escenario tiene un ID propio (`ASI-1a`…) que lleva el nombre de su test. Salvo `ASI-1e`, que corre en el perfil opcional `postgres`, los escenarios se verifican en la suite por defecto.

## ADDED Requirements

### Requirement: Marcar pasa un turno reservado o confirmado a atendido o ausente desde su inicio y libera su horario

`POST /turnos/{id}/estado` SHALL pasar el turno indicado al estado que trae el cuerpo, `atendido` o `ausente`, y responder `200` con el turno completo (los mismos campos que `201` de `POST /turnos`), con el estado nuevo (US-014 CA-1). Nada más del turno SHALL cambiar: mismo `id`, paciente, prestación, profesional, sillón, `inicio`, `fin`, `duracion_minutos` y `creado_en`. Solo un turno `reservado` o `confirmado` SHALL poder marcarse (tabla de transiciones de `04`, RN-AG-13, DD-16); uno en cualquier otro estado (`pendiente_aprobacion`, `pendiente_sena`, `cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido`, `ausente`) SHALL rechazarse con `409` y el código `RN-AG-12` («transición de estado inválida»), también cuando se pide el mismo marcado que ya tiene o el contrario (la corrección del marcado llega con C-19), sin modificar el turno ni el historial (US-014 CA-3). Con el estado admitido, un turno cuyo `inicio` es posterior al reloj de la API SHALL rechazarse con `409` y el código `RN-AG-13` («marcado antes del inicio del turno»), sin modificar el turno ni el historial; con el reloj igual a `inicio` se admite (US-014 CA-6, D34). `RN-AG-12` y `RN-AG-13` son reglas de negocio (RN-GL-02): se evalúan después del control de acceso, del formato y de la existencia del turno, `RN-AG-12` antes que `RN-AG-13`. Un turno marcado SHALL dejar de ocupar su horario (US-014 CA-2, RN-AG-10): otro turno puede crearse en el mismo hueco. La verificación del estado SHALL ser atómica frente a otras escrituras simultáneas sobre el mismo turno. El marcado MUST NOT exigir que el profesional, el sillón o la prestación del turno sigan activos: `RN-AG-07` y `RN-GL-04` solo rechazan lo inactivo al crear o reprogramar un turno, y marcar no cambia ni ocupa esos recursos.

#### Scenario: ASI-1a Feliz - la recepcionista marca atendido y la odontóloga marca ausente (US-014 CA-1)

- **GIVEN** el turno de Ana, `reservado`, de 13:00 a 13:30, y un turno `confirmado` de Bruno Ficticio de 12:00 a 12:30, y el reloj en `2026-11-02T13:10:00Z`
- **WHEN** la recepcionista pide `POST /turnos/{id}/estado` del turno de Ana con `{"estado": "atendido"}` y su token
- **THEN** el sistema responde `200` con el mismo `id`, `estado` `atendido`, `inicio` `2026-11-02T13:00:00Z`, `fin` `2026-11-02T13:30:00Z`, `duracion_minutos` 30, `paciente_id` 1, `prestacion_id` 1, `profesional_id` 1, `sillon_id` 1 y el mismo `creado_en`
- **AND** `GET /turnos?fecha=2026-11-02` lo sigue listando a las 13:00 con `estado` `atendido`
- **AND** la odontóloga marca el turno de Bruno con `{"estado": "ausente"}` y su token, y el sistema responde `200` con `estado` `ausente`

#### Scenario: ASI-1b Borde - el horario queda libre, los dos estados de origen y el instante exacto del inicio (US-014 CA-2, RN-AG-10, D34)

- **GIVEN** el turno de Ana, de 13:00 a 13:30, marcado `ausente` con el reloj en `2026-11-02T13:10:00Z`
- **WHEN** la recepcionista pide `POST /turnos` para Bruno Ficticio con «Consulta / control» a las 13:00
- **THEN** la creación responde `201`: el turno marcado no choca (RN-AG-10)
- **AND** cuatro turnos de 30 minutos de Bruno ya empezados (`reservado` a las 11:00 y a las 12:00, `confirmado` a las 11:30 y a las 12:30) se marcan con `200`: los dos `reservado` uno con `atendido` y otro con `ausente`, y lo mismo los dos `confirmado` (cuatro corridas), y quedan con ese estado
- **AND** con el reloj en `2026-11-02T13:00:00Z` exacto, el turno de Ana `reservado` de 13:00 a 13:30 se marca `atendido` con `200` (`ahora == inicio` se admite)
- **AND** con el reloj en `2026-11-04T15:00:00Z`, un turno `confirmado` de Ana del lunes 2 de noviembre (dos días antes) se marca `ausente` con `200`: no hay plazo máximo para marcar

#### Scenario: ASI-1c Error de negocio - un turno que no está reservado ni confirmado se rechaza con RN-AG-12 y no cambia (US-014 CA-3)

- **GIVEN** siete turnos de Carla Inventada, ya empezados, uno por cada estado que no admite el marcado, cargados con la fábrica y cada uno con su evento `creado`: los dos activos en horarios distintos, `pendiente_aprobacion` de 11:00 a 11:30 y `pendiente_sena` de 11:30 a 12:00 (no se superponen entre sí ni con otro turno activo del profesional 1 y el sillón 1), y los cinco terminales (`cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido`, `ausente`) de 12:00 a 12:30, que no ocupan el horario (RN-AG-10)
- **WHEN** la recepcionista pide marcar cada uno, en una corrida con `{"estado": "atendido"}` y en otra con `{"estado": "ausente"}`
- **THEN** las catorce peticiones responden `409` con `codigos` `["RN-AG-12"]`
- **AND** ningún turno cambia: cada uno conserva su estado y su historial sigue con solo el evento `creado`
- **AND** el turno de Ana, `reservado`, marcado una vez `atendido` (`200`), responde `409` `RN-AG-12` si se pide otra vez `atendido` y también si se pide `ausente` (la corrección es de C-19), y sigue `atendido` con un solo evento `estado_cambiado`

#### Scenario: ASI-1d Error de negocio - marcar antes del inicio se rechaza con RN-AG-13 y no cambia (US-014 CA-6)

- **GIVEN** el turno de Ana, `reservado`, de 13:00 a 13:30, y un turno `confirmado` de Bruno del martes 3 de noviembre de 13:00 a 13:30
- **WHEN** con el reloj en `2026-11-02T12:59:59Z` la recepcionista pide marcar el turno de Ana con `{"estado": "atendido"}` y, en otra corrida, con `{"estado": "ausente"}`; y con el mismo reloj pide marcar `atendido` el turno de Bruno
- **THEN** las tres peticiones responden `409` con `codigos` `["RN-AG-13"]`
- **AND** ningún turno cambia
- **AND** un turno `cancelado_paciente` de Ana del martes 3 de noviembre (todavía no empezó) responde `409` con `codigos` `["RN-AG-12"]` y no `RN-AG-13`: el estado se evalúa antes que el momento

#### Scenario: ASI-1e Borde - dos marcados simultáneos del mismo turno: uno solo gana (perfil postgres)

- **GIVEN** en PostgreSQL el turno de Ana, `reservado`, de 13:00 a 13:30, con el reloj en `2026-11-02T13:10:00Z`
- **WHEN** dos peticiones simultáneas lo marcan, una con `atendido` y otra con `ausente`; y, en otra corrida, una lo marca `atendido` mientras otra lo cancela con `POST /turnos/{id}/cancelar` y `cancelado_paciente`
- **THEN** en la primera corrida una responde `200` y la otra `409` con `codigos` `["RN-AG-12"]`, y el turno queda con el estado de la que respondió `200` y un solo evento `estado_cambiado`
- **AND** en la segunda corrida una responde `200` y la otra `409` con `codigos` `["RN-AG-12"]`, y el turno queda con un solo evento además del `creado` (un `estado_cambiado` o un `cancelado`), el de la que respondió `200`

#### Scenario: ASI-1f Borde - un turno cuyo profesional, sillón o prestación se desactivó después se marca igual (RN-AG-07, RN-GL-04)

- **GIVEN** el turno de Ana, `reservado`, de 13:00 a 13:30, con su evento `creado`, y después de crearlo el sillón 1, el profesional 1 y la prestación 1 pasan a inactivos (cargados así en la base con la fábrica de tests)
- **WHEN** con el reloj en `2026-11-02T13:10:00Z` la recepcionista pide `POST /turnos/{id}/estado` del turno de Ana con `{"estado": "atendido"}`
- **THEN** el sistema responde `200` con `estado` `atendido` y los mismos `profesional_id`, `sillon_id` y `prestacion_id`, nunca `422` ni `404` con `RN-GL-04`
- **AND** el historial suma un solo evento `estado_cambiado` y Ana Ejemplo queda con `es_nuevo` `false`: `RN-AG-07` y `RN-GL-04` rechazan lo inactivo solo al crear o reprogramar un turno, y el marcado mira solo el estado del turno y el momento

### Requirement: Marcar registra el evento `estado_cambiado` con el estado de antes y el de después

Un marcado aceptado SHALL registrar en el historial del turno exactamente un evento de tipo `estado_cambiado`, en la misma operación que guarda el estado nuevo: o quedan los dos o no queda ninguno (US-014 CA-4, RN-AG-11). El evento SHALL llevar `ocurrido_en` igual al reloj de la API, `actor_tipo` `usuario` y `actor_id` igual al id del usuario del token como texto decimal (D209), `antes` `{"estado": <estado anterior>}`, `despues` `{"estado": <estado nuevo>}` y `motivo` vacío. Un rechazo MUST NOT registrar ningún evento. La atomicidad del estado, el evento y `es_nuevo` se verifica a nivel de caso de uso, con un disparador de SQLite que hace fallar el registro del evento (`ASI-2c`).

#### Scenario: ASI-2a Feliz - el historial guarda quién marcó y el cambio de estado (US-014 CA-4)

- **GIVEN** el turno de Ana, `confirmado`, con su evento `creado`
- **WHEN** la recepcionista (usuario 2) lo marca con `{"estado": "atendido"}` y el sistema responde `200`
- **THEN** `GET /turnos/{id}/historial` devuelve dos eventos en este orden: el `creado` sin cambios y uno de `tipo` `estado_cambiado`
- **AND** el `estado_cambiado` tiene `ocurrido_en` `2026-11-02T13:10:00Z`, `actor_tipo` `usuario`, `actor_id` `"2"`, `antes` `{"estado": "confirmado"}`, `despues` `{"estado": "atendido"}` y `motivo` vacío
- **AND** con un turno `reservado` de Bruno de 12:00 a 12:30 marcado `ausente` por la odontóloga (usuario 1), su `estado_cambiado` tiene `actor_id` `"1"`, `antes` `{"estado": "reservado"}` y `despues` `{"estado": "ausente"}`

#### Scenario: ASI-2b Borde - un rechazo no registra eventos

- **GIVEN** el turno de Ana, `reservado`, con su evento `creado`, y el turno `atendido` de Carla Inventada del lunes 26 de octubre de 12:00 a 12:30, creado con la fábrica, con su evento `creado`
- **WHEN** se pide marcar el turno de Ana y la petición se rechaza, en una corrida por causa, con `422` por un cuerpo inválido (`{"estado": "cancelado_paciente"}`), con `403` por rol insuficiente (el token del dueño), con `401` sin sesión o con `409` `RN-AG-13` (el reloj en `2026-11-02T12:00:00Z`); y la recepcionista pide marcar `ausente` el turno `atendido` de Carla y el sistema responde `409` `RN-AG-12`
- **THEN** en las cinco corridas el historial de cada turno sigue teniendo solo su evento `creado`
- **AND** cada turno conserva su estado, `reservado` o `atendido`, Ana Ejemplo sigue con `es_nuevo` `true` y Carla Inventada sigue con `es_nuevo` `false`

#### Scenario: ASI-2c Borde - si el evento no se puede registrar, el turno no queda marcado y el paciente sigue nuevo (atomicidad)

- **GIVEN** en la base en memoria el turno de Ana, `reservado`, con su evento `creado`, Ana Ejemplo con `es_nuevo` `true`, y un disparador de SQLite que aborta todo `INSERT` en `evento_turno` (sin dobles del repositorio, como `REP-2b` y `CAN-2c`)
- **WHEN** el caso de uso de marcar recibe un marcado válido del turno de Ana con `atendido`, de modo que el `UPDATE` del estado y el de `es_nuevo` ya se enviaron a la base cuando falla el registro del evento
- **THEN** el caso de uso termina con un error de base de datos (`DBAPIError`)
- **AND** después de quitar el disparador, el turno de Ana sigue `reservado`, su historial tiene solo el evento `creado` y Ana Ejemplo sigue con `es_nuevo` `true`
- **AND** este escenario se verifica a nivel de caso de uso (pytest de integración), no por la API

### Requirement: El primer turno atendido deja de considerar nuevo al paciente

Todo paciente SHALL tener `es_nuevo`, `true` por defecto (RN-TD-05, D52, D99). Un marcado aceptado con `atendido` SHALL dejar `es_nuevo` en `false` para el paciente del turno, en la misma operación que el estado y el evento (US-014 CA-11); si ya era `false`, sigue `false`. Un marcado con `ausente` MUST NOT cambiar `es_nuevo`, y un marcado rechazado tampoco. Solo cambia el paciente del turno marcado. El cambio de `es_nuevo` no registra un evento propio: queda explicado por el `estado_cambiado` del turno (`04`, reparto con `EventoPaciente`).

#### Scenario: ASI-3a Feliz - el primer atendido deja de considerar nuevo al paciente (US-014 CA-11)

- **GIVEN** Ana Ejemplo con `es_nuevo` `true` y sin turnos atendidos, Bruno Ficticio con `es_nuevo` `true`, y el turno de Ana, `reservado`, de 13:00 a 13:30
- **WHEN** la recepcionista marca el turno de Ana con `{"estado": "atendido"}` y el sistema responde `200`
- **THEN** leído con el repositorio, Ana Ejemplo tiene `es_nuevo` `false`
- **AND** Bruno Ficticio sigue con `es_nuevo` `true`

#### Scenario: ASI-3b Borde - ausente no lo cambia y un segundo atendido lo deja en false

- **GIVEN** Ana Ejemplo con `es_nuevo` `true`, con un turno `reservado` de 11:00 a 11:30 y otro `confirmado` de 12:00 a 12:30, y Bruno Ficticio con `es_nuevo` `false` porque ya tiene un turno `atendido` (del lunes 26 de octubre de 11:00 a 11:30, cargado con la fábrica) y un turno `reservado` de 12:30 a 13:00
- **WHEN** la recepcionista marca `ausente` el turno de las 11:00 de Ana; después marca `atendido` el de las 12:00; y marca `atendido` el turno de Bruno
- **THEN** después del `ausente`, Ana sigue con `es_nuevo` `true`
- **AND** después del `atendido`, Ana tiene `es_nuevo` `false`
- **AND** Bruno sigue con `es_nuevo` `false` y su turno queda `atendido` con `200`

### Requirement: Quién puede marcar, qué turno y qué cuerpo se aceptan

`POST /turnos/{id}/estado` SHALL exigir el permiso `turnos.marcar`, que tienen el odontólogo y la recepcionista (matriz de `03`, fila «Marcar turno atendido / ausente (RN-AG-13)»: «U» y «U»); el control de acceso SHALL evaluarse antes que cualquier validación (D208): sin sesión válida, el `401` de sesión inválida; con un rol sin el permiso (el dueño) o sin roles, el `403` de permiso insuficiente con `RN-AU-05`. Después, un cuerpo mal formado (sin `estado`, un `estado` que no es `atendido` ni `ausente`, un `null` explícito, un campo de más, un tipo erróneo), la falta de cuerpo o un id de la URL que no es entero SHALL responder `422` sin código RN, sin mirar el turno. Con el cuerpo bien formado, un turno inexistente **o de otro consultorio** SHALL responder `404` con `RN-GL-04` y la referencia `turno` (D166, D321), antes de evaluar su estado y su momento.

#### Scenario: ASI-4a Error de negocio - sin sesión 401; el dueño y el usuario sin roles 403 antes de validar

- **GIVEN** el turno de Ana
- **WHEN** se pide marcarlo con `{"estado": "atendido"}` sin cabecera `Authorization`; con el token del dueño; y con el token del usuario sin roles, este último también con `{"estado": "cancelado_paciente"}` y con el id 999
- **THEN** la primera responde el `401` de sesión inválida
- **AND** las demás responden el `403` de permiso insuficiente con `codigos` `["RN-AU-05"]`, nunca `422` ni `404`
- **AND** en todas el turno no cambia
- **AND** un access token vencido o con firma inválida recibe el mismo `401` de sesión inválida: lo cubren el guard y los escenarios de `proteccion-del-panel` para toda ruta protegida (RN-AU-03, D206), así que esta ruta no repite esas corridas, como `POST /turnos/{id}/cancelar` en C-17

#### Scenario: ASI-4b Error de negocio - turno inexistente, de otro consultorio o petición mal formada

- **GIVEN** el turno de Ana y un turno `reservado` de otro consultorio, ya empezado, creado directo en la base con la fábrica de tests (junto con su consultorio, su profesional y su sillón), porque la API no crea un segundo consultorio (D173; como `REP-4b` y `CAN-3b`)
- **WHEN** la recepcionista pide marcar con `{"estado": "atendido"}` el turno 999 y el turno del otro consultorio; y el turno de Ana con `{}`, con `{"estado": "reservado"}`, con `{"estado": "cancelado_paciente"}`, con `{"estado": "Atendido"}`, con `{"estado": null}`, con `{"estado": "atendido", "motivo": "Llegó tarde"}`, con `{"estado": 1}` y sin cuerpo; y `POST /turnos/abc/estado`
- **THEN** las dos primeras responden `404` con `codigos` `["RN-GL-04"]` y la referencia `turno` con su id y motivo `inexistente`, sin distinguir entre ellas, y el turno del otro consultorio sigue `reservado`
- **AND** las demás responden `422` con `codigos` vacío y un error que nombra el campo (o el parámetro `turno_id`)
- **AND** el turno 999 con `{"estado": "reservado"}` responde `422`, no `404` (el formato del cuerpo va antes que la existencia del turno)
- **AND** el turno de Ana no cambia
