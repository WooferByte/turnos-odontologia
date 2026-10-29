# cancelacion-de-turnos Specification

## Purpose

Define cómo la API cancela un turno desde el panel indicando quién lo pidió, libera su horario y registra el evento `cancelado` en su historial, con los mismos rechazos de acceso que el resto del panel (US-013 CA-1 y CA-2; CAN-1; RN-AG-10, RN-AG-11, RN-AG-12, RN-TD-03).

Convenciones de los escenarios: todos los instantes están en **UTC** y se escriben con `Z`; los turnos son del lunes 2026-11-02 salvo que se diga otra cosa («13:00» significa `2026-11-02T13:00:00Z`, las 10:00 del consultorio) y el reloj de la API marca `2026-10-29T12:00:00Z`. El consultorio es el único de la instalación (D173), con `zona_horaria` `America/Argentina/Buenos_Aires` (UTC−3). Datos de partida, todos ficticios (RN-PR-01): el profesional 1 y el sillón 1, activos y únicos, con horario de lunes a viernes de 08:00 a 20:00 del consultorio (`11:00Z` a `23:00Z`); los pacientes 1 «Ana Ejemplo» y 2 «Bruno Ficticio»; las prestaciones 1 «Consulta / control» (30 min) y 2 «Limpieza» (45 min); «la odontóloga» (`odontologo` + `dueno`, usuario 1), «la recepcionista» (`recepcionista`, usuario 2), «el dueño» (solo `dueno`) y «el usuario sin roles». «El turno de Ana» es un turno `reservado` de Ana Ejemplo con «Consulta / control», del profesional 1 y el sillón 1, de 13:00 a 13:30, creado con `POST /turnos` (con su evento `creado`). «Con el token de X» significa con la cabecera `Authorization: Bearer <access token>` vigente de X. «El `401` de sesión inválida» y «el `403` de permiso insuficiente» son las respuestas fijas de `proteccion-del-panel` (`RN-AU-03`, D206; `RN-AU-05`, D207). Un error sale como `application/problem+json` con `codigos`. «El turno no cambia» significa que `GET /turnos/{id}` devuelve el mismo `estado`, `inicio` y `fin` que antes de la petición y que su historial no suma eventos. Las elecciones de este spec que no fijaba la KB son **decisiones del autor** del 2026-10-29 (D344 a D349), ya escritas en la KB: entre ellas, el nombre del campo `estado` del cuerpo (`02`), el `409` de `RN-AG-12` (`05` y `08`), el orden de evaluación (`05` RN-GL-02) y el permiso `turnos.cancelar` (`03`). Los turnos que la API no puede crear (en estados distintos de `reservado`, en una fecha ya pasada o de otro consultorio) se cargan directo en la base con la fábrica de tests, con su evento `creado`. La cancelación usa el estado **almacenado** del turno (D317, D345). Cada escenario tiene un ID propio (`CAN-1a`…) que lleva el nombre de su test; `CAN-1` es el escenario mínimo que `CHANGES.md` fija para C-17 («cancelar un turno en estado terminal se rechaza con RN-AG-12 y no cambia») y aquí es `CAN-1c`. Salvo `CAN-1d`, que corre en el perfil opcional `postgres`, los escenarios se verifican en la suite por defecto.

## Requirements

### Requirement: Cancelar pasa un turno activo al estado de quien lo pidió y libera su horario

`POST /turnos/{id}/cancelar` SHALL pasar el turno indicado al estado que trae el cuerpo, `cancelado_paciente` (lo pidió el paciente) o `cancelado_profesional` (lo pidió el consultorio), y responder `200` con el turno completo (los mismos campos que `201` de `POST /turnos`), con el estado nuevo (US-013 CA-1). Nada más del turno SHALL cambiar: mismo `id`, paciente, prestación, profesional, sillón, `inicio`, `fin`, `duracion_minutos` y `creado_en`. Solo un turno en estado activo (`pendiente_aprobacion`, `pendiente_sena`, `reservado`, `confirmado`) SHALL poder cancelarse (tabla de transiciones de `04`: «cualquier estado activo → `cancelado_paciente` | `cancelado_profesional`»); uno en estado terminal (`cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido`, `ausente`) SHALL rechazarse con `409` y el código `RN-AG-12` («transición de estado inválida»), también cuando se pide la misma cancelación que ya tiene, sin modificar el turno ni el historial (RN-AG-12). `RN-AG-12` es una regla de negocio (RN-GL-02): se evalúa después del control de acceso, del formato y de la existencia del turno. El panel SHALL poder cancelar **en cualquier momento** (RN-TD-03, D65): un turno ya pasado o que empieza en minutos no se rechaza por eso. Un turno cancelado SHALL dejar de ocupar su horario (RN-AG-10): otro turno puede crearse o reprogramarse en el mismo hueco. La verificación del estado SHALL ser atómica frente a otras escrituras simultáneas sobre el mismo turno.

#### Scenario: CAN-1a Feliz - la recepcionista cancela un turno a pedido del paciente (US-013 CA-1)

- **GIVEN** el turno de Ana, `reservado`, de 13:00 a 13:30
- **WHEN** la recepcionista pide `POST /turnos/{id}/cancelar` con `{"estado": "cancelado_paciente"}` y su token
- **THEN** el sistema responde `200` con el mismo `id`, `estado` `cancelado_paciente`, `inicio` `2026-11-02T13:00:00Z`, `fin` `2026-11-02T13:30:00Z`, `duracion_minutos` 30, `paciente_id` 1, `prestacion_id` 1, `profesional_id` 1, `sillon_id` 1 y el mismo `creado_en`
- **AND** `GET /turnos?fecha=2026-11-02` lo sigue listando a las 13:00 con `estado` `cancelado_paciente`
- **AND** con otro turno `reservado` de Bruno Ficticio a las 15:00, la odontóloga lo cancela con `{"estado": "cancelado_profesional"}` y su token, y el sistema responde `200` con `estado` `cancelado_profesional`

#### Scenario: CAN-1b Borde - el horario queda libre y se cancela desde cualquier estado activo y en cualquier momento (US-013 CA-2, RN-AG-10, D65)

- **GIVEN** el turno de Ana, de 13:00 a 13:30, cancelado con `cancelado_profesional`
- **WHEN** la recepcionista pide `POST /turnos` para Bruno Ficticio con «Consulta / control» a las 13:00; y, en otra corrida, reprograma con `PATCH /turnos/{id}` un turno `reservado` de Bruno de 18:00 a 18:30 con `{"inicio": "2026-11-02T13:00:00Z"}`
- **THEN** la creación responde `201` y la reprogramación `200`: el turno cancelado no choca (RN-AG-10)
- **AND** cuatro turnos de 30 minutos de Bruno, uno por cada estado activo (`pendiente_aprobacion` a las 14:00, `pendiente_sena` a las 15:00, `reservado` a las 16:00 y `confirmado` a las 17:00), se cancelan con `200`, cada uno en una corrida con `cancelado_paciente` y en otra con `cancelado_profesional` (ocho corridas), y quedan con ese estado
- **AND** un turno `reservado` de Ana de `2026-10-26T13:00:00Z` a `2026-10-26T13:30:00Z` (ya pasado según el reloj) y, en otra corrida, un turno `confirmado` de Ana de `2026-10-29T12:05:00Z` a `2026-10-29T12:35:00Z` (empieza en cinco minutos), los dos creados con la fábrica, se cancelan con `200` y `cancelado_paciente` (D65)
- **AND** el escenario suma doce corridas: dos del hueco liberado (creación y reprogramación), ocho de los estados activos y dos de los momentos

#### Scenario: CAN-1c Error de negocio - cancelar un turno en estado terminal se rechaza con RN-AG-12 y no cambia (CAN-1)

- **GIVEN** cinco turnos de Ana de 13:00 a 13:30, uno por cada estado terminal (`cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido`, `ausente`), cada uno con su evento `creado`
- **WHEN** la recepcionista pide cancelar cada uno, en una corrida con `{"estado": "cancelado_paciente"}` y en otra con `{"estado": "cancelado_profesional"}`
- **THEN** las diez peticiones responden `409` con `codigos` `["RN-AG-12"]`
- **AND** ningún turno cambia: cada uno conserva su estado y su historial sigue con solo el evento `creado`
- **AND** el turno de Ana, `reservado`, cancelado una vez con `cancelado_paciente` (`200`), responde `409` `RN-AG-12` si se pide otra vez la misma cancelación y también si se pide `cancelado_profesional`, y sigue `cancelado_paciente` con un solo evento `cancelado`

#### Scenario: CAN-1d Borde - dos cancelaciones simultáneas del mismo turno: una sola gana (perfil postgres)

- **GIVEN** en PostgreSQL el turno de Ana, `reservado`, de 13:00 a 13:30
- **WHEN** dos peticiones simultáneas lo cancelan, una con `cancelado_paciente` y otra con `cancelado_profesional`; y, en otra corrida, una lo cancela mientras otra lo reprograma con `PATCH /turnos/{id}` a las 16:00
- **THEN** en la primera corrida una responde `200` y la otra `409` con `codigos` `["RN-AG-12"]`, y el turno queda con el estado de la que respondió `200` y un solo evento `cancelado`
- **AND** en la segunda corrida las dos se serializan: o la reprogramación responde `200` y después la cancelación `200` (el turno queda cancelado a las 16:00, con un `reprogramado` y después un `cancelado`), o la cancelación responde `200` y la reprogramación `409` con `codigos` `["RN-AG-18"]` (el turno queda cancelado a las 13:00, con solo el `cancelado`)

### Requirement: Cancelar registra el evento `cancelado` con el estado de antes y el de después

Una cancelación aceptada SHALL registrar en el historial del turno exactamente un evento de tipo `cancelado`, en la misma operación que guarda el estado nuevo: o quedan los dos o no queda ninguno (RN-AG-11). El evento SHALL llevar `ocurrido_en` igual al reloj de la API, `actor_tipo` `usuario` y `actor_id` igual al id del usuario del token como texto decimal (D209), `antes` `{"estado": <estado anterior>}`, `despues` `{"estado": <estado nuevo>}` y `motivo` vacío. Un rechazo MUST NOT registrar ningún evento. La atomicidad del estado y el evento se verifica a nivel de caso de uso, con un disparador de SQLite que hace fallar el registro del evento (`CAN-2c`).

#### Scenario: CAN-2a Feliz - el historial guarda quién canceló y el cambio de estado

- **GIVEN** el turno de Ana, `confirmado`, con su evento `creado`
- **WHEN** la recepcionista (usuario 2) lo cancela con `{"estado": "cancelado_paciente"}` y el sistema responde `200`
- **THEN** `GET /turnos/{id}/historial` devuelve dos eventos en este orden: el `creado` sin cambios y uno de `tipo` `cancelado`
- **AND** el `cancelado` tiene `ocurrido_en` `2026-10-29T12:00:00Z`, `actor_tipo` `usuario`, `actor_id` `"2"`, `antes` `{"estado": "confirmado"}`, `despues` `{"estado": "cancelado_paciente"}` y `motivo` vacío

#### Scenario: CAN-2b Borde - un rechazo no registra eventos

- **GIVEN** el turno de Ana, `reservado`, con su evento `creado`, y un turno `atendido` de Ana de 15:00 a 15:30, creado con la fábrica, con su evento `creado`
- **WHEN** se pide cancelar el turno de Ana y la petición se rechaza, en una corrida por causa, con `422` por un cuerpo inválido (`{"estado": "vencido"}`), con `403` por rol insuficiente (el token del dueño) o con `401` sin sesión; y la recepcionista pide cancelar el turno `atendido` con `{"estado": "cancelado_paciente"}` y el sistema responde `409` `RN-AG-12`
- **THEN** en las cuatro corridas el historial de cada turno sigue teniendo solo su evento `creado`
- **AND** cada turno conserva su estado, `reservado` o `atendido`

#### Scenario: CAN-2c Borde - si el evento no se puede registrar, el turno no queda cancelado (atomicidad)

- **GIVEN** en la base en memoria el turno de Ana, `reservado`, con su evento `creado`, y un disparador de SQLite que aborta todo `INSERT` en `evento_turno` (sin dobles del repositorio, como `REP-2b`)
- **WHEN** el caso de uso de cancelar recibe una cancelación válida del turno de Ana con `cancelado_paciente`, de modo que el `UPDATE` del estado ya se envió a la base cuando falla el registro del evento
- **THEN** el caso de uso termina con un error de base de datos (`DBAPIError`)
- **AND** después de quitar el disparador, el turno de Ana sigue `reservado` y su historial tiene solo el evento `creado`, sin ningún `cancelado`
- **AND** este escenario se verifica a nivel de caso de uso (pytest de integración), no por la API

### Requirement: Quién puede cancelar, qué turno y qué cuerpo se aceptan

`POST /turnos/{id}/cancelar` SHALL exigir el permiso `turnos.cancelar`, que tienen el odontólogo y la recepcionista (matriz de `03`, fila Turnos: «CRUD» y «CRU + cancelar»); el control de acceso SHALL evaluarse antes que cualquier validación (D208): sin sesión válida, el `401` de sesión inválida; con un rol sin el permiso (el dueño) o sin roles, el `403` de permiso insuficiente con `RN-AU-05`. Después, un cuerpo mal formado (sin `estado`, un `estado` que no es `cancelado_paciente` ni `cancelado_profesional`, un `null` explícito, un campo de más, un tipo erróneo) la falta de cuerpo o un id de la URL que no es entero SHALL responder `422` sin código RN, sin mirar el turno. Con el cuerpo bien formado, un turno inexistente **o de otro consultorio** SHALL responder `404` con `RN-GL-04` y la referencia `turno` (D166, D321), antes de evaluar su estado.

#### Scenario: CAN-3a Error de negocio - sin sesión 401; el dueño y el usuario sin roles 403 antes de validar

- **GIVEN** el turno de Ana
- **WHEN** se pide cancelarlo con `{"estado": "cancelado_paciente"}` sin cabecera `Authorization`; con el token del dueño; y con el token del usuario sin roles, este último también con `{"estado": "vencido"}` y con el id 999
- **THEN** la primera responde el `401` de sesión inválida
- **AND** las demás responden el `403` de permiso insuficiente con `codigos` `["RN-AU-05"]`, nunca `422` ni `404`
- **AND** en todas el turno no cambia

#### Scenario: CAN-3b Error de negocio - turno inexistente, de otro consultorio o petición mal formada

- **GIVEN** el turno de Ana y un turno `reservado` de otro consultorio, creado directo en la base con la fábrica de tests (junto con su consultorio, su profesional y su sillón), porque la API no crea un segundo consultorio (D173; como `REP-4b`)
- **WHEN** la recepcionista pide cancelar con `{"estado": "cancelado_paciente"}` el turno 999 y el turno del otro consultorio; y el turno de Ana con `{}`, con `{"estado": "cancelado_consultorio"}`, con `{"estado": "atendido"}`, con `{"estado": null}`, con `{"estado": "cancelado_paciente", "motivo": "Viaje"}`, con `{"estado": 1}` y sin cuerpo; y `POST /turnos/abc/cancelar`
- **THEN** las dos primeras responden `404` con `codigos` `["RN-GL-04"]` y la referencia `turno` con su id y motivo `inexistente`, sin distinguir entre ellas, y el turno del otro consultorio sigue `reservado`
- **AND** las demás responden `422` con `codigos` vacío y un error que nombra el campo (o el parámetro `turno_id`)
- **AND** el turno 999 con `{"estado": "atendido"}` responde `422`, no `404` (el formato del cuerpo va antes que la existencia del turno)
- **AND** el turno de Ana no cambia
