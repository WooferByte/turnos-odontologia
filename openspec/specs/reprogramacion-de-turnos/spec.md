# reprogramacion-de-turnos Specification

## Purpose

Define cómo la API mueve un turno a otro horario o le cambia la duración desde el panel, sobre el mismo turno y validándolo como uno nuevo que se excluye a sí mismo, con el evento `reprogramado` en su historial y los mismos rechazos de acceso que el resto del panel (US-012 CA-1, CA-2 y CA-4; REP-1; DD-05; RN-AG-10b, RN-AG-11).

Convenciones de los escenarios: todos los instantes están en **UTC** y se escriben con `Z`; los turnos son del lunes 2026-11-02 salvo que se diga otra cosa («13:00» significa `2026-11-02T13:00:00Z`, las 10:00 del consultorio) y el reloj de la API marca `2026-10-29T12:00:00Z`. El consultorio es el único de la instalación (D173), con `zona_horaria` `America/Argentina/Buenos_Aires` (UTC−3), así que su medianoche es a las `03:00Z`. Datos de partida, todos ficticios (RN-PR-01): el profesional 1 y el sillón 1, activos y únicos, con horario de lunes a viernes de 08:00 a 20:00 del consultorio (`11:00Z` a `23:00Z`) salvo que se diga otra cosa; los pacientes 1 «Ana Ejemplo» y 2 «Bruno Ficticio»; las prestaciones 1 «Consulta / control» (30 min) y 2 «Limpieza» (45 min); «la odontóloga» (`odontologo` + `dueno`, usuario 1), «la recepcionista» (`recepcionista`, usuario 2), «el dueño» (solo `dueno`) y «el usuario sin roles». «El turno de Ana» es un turno `reservado` de Ana Ejemplo con «Consulta / control», del profesional 1 y el sillón 1, de 13:00 a 13:30 (30 min), creado con `POST /turnos` (con su evento `creado`). «Con el token de X» significa con la cabecera `Authorization: Bearer <access token>` vigente de X. «El `401` de sesión inválida» y «el `403` de permiso insuficiente» son las respuestas fijas de `proteccion-del-panel` (`RN-AU-03`, D206; `RN-AU-05`, D207). Un error sale como `application/problem+json` con `codigos`. «El turno no cambia» significa que `GET /turnos/{id}` devuelve el mismo `inicio`, `fin`, `duracion_minutos` y `estado` que antes de la petición y que su historial no suma eventos. Las elecciones de este spec que no fijaba la KB son decisiones del autor (D333 a D338, 2026-10-29), incluidos el código nuevo `RN-AG-18` (D334) y el tope de 1440 minutos de la duración (D333), ya registrados en `05`. Cada escenario tiene un ID propio (`REP-1a`…) que lleva el nombre de su test; `REP-1` es el escenario mínimo que `CHANGES.md` fija para C-16 y aquí es `REP-1c`. Salvo `REP-1e`, que corre en el perfil opcional `postgres`, los escenarios se verifican en la suite por defecto.

## Requirements

### Requirement: Reprogramar mueve el mismo turno y lo valida como uno nuevo excluyéndose a sí mismo

`PATCH /turnos/{id}` SHALL cambiar el `inicio`, la duración o las dos cosas del turno indicado y responder `200` con el turno completo (los mismos campos que `201` de `POST /turnos`). El turno SHALL seguir siendo el mismo (DD-05): mismo `id`, paciente, prestación, profesional, sillón, `estado` y `creado_en`. Un campo omitido conserva su valor: sin `duracion_minutos` se conserva la duración actual del turno (no la de su prestación, RN-AG-02) y sin `inicio` se conserva el inicio. `fin` SHALL recalcularse como `inicio + duracion_minutos` (RN-AG-02). El horario resultante SHALL validarse con las reglas de un turno nuevo, en este orden y de a una (RN-GL-02, D135): no cruzar la medianoche del consultorio (RN-AG-10d, `422`), caer completo en una franja vigente del horario del profesional (RN-AG-04, `422`), no intersecar un bloqueo del profesional, del sillón o del consultorio (RN-AG-04b, `422`) y no solaparse con otro turno activo del profesional ni del sillón (RN-AG-05, RN-AG-08, `409`, con los dos códigos si chocan los dos recursos, D139). Para el solapamiento el turno MUST excluirse a sí mismo (RN-AG-10b) y SHALL contar solo los turnos activos (RN-AG-10). Un rechazo MUST NOT cambiar el turno ni registrar eventos. La verificación SHALL ser atómica frente a otras escrituras simultáneas (RN-AG-10c).

#### Scenario: REP-1a Feliz - la recepcionista mueve un turno a otro horario libre (US-012 CA-1)

- **GIVEN** el turno de Ana, de 13:00 a 13:30
- **WHEN** la recepcionista pide `PATCH /turnos/{id}` con `{"inicio": "2026-11-02T17:00:00Z"}` y su token
- **THEN** el sistema responde `200` con el mismo `id`, `inicio` `2026-11-02T17:00:00Z`, `fin` `2026-11-02T17:30:00Z`, `duracion_minutos` 30, `estado` `reservado`, `paciente_id` 1, `prestacion_id` 1, `profesional_id` 1, `sillon_id` 1 y el mismo `creado_en`
- **AND** `GET /turnos?fecha=2026-11-02` lo lista a las 17:00 y en la base sigue habiendo un solo turno
- **AND** la odontóloga puede hacer lo mismo con su token (`200`)

#### Scenario: REP-1b Borde - el turno no choca consigo mismo y los bordes semiabiertos se respetan (RN-AG-10b, RN-AG-09)

- **GIVEN** el turno de Ana, de 13:00 a 13:30, y un turno `reservado` de Bruno Ficticio de 14:00 a 14:45, los dos del profesional 1 y el sillón 1
- **WHEN** se pide reprogramar el turno de Ana con `inicio` 13:15 (se superpone con su propio horario anterior) y, en otra corrida, con `inicio` 13:30 (termina justo cuando empieza el de Bruno)
- **THEN** las dos peticiones responden `200`: la primera de 13:15 a 13:45 y la segunda de 13:30 a 14:00
- **AND** el turno de Bruno no cambia

#### Scenario: REP-1c Error de negocio - reprogramar sobre otro turno activo se rechaza con los dos códigos y el turno no cambia (REP-1)

- **GIVEN** el turno de Ana, de 13:00 a 13:30, y un turno `confirmado` de Bruno Ficticio de 14:00 a 14:45, del mismo profesional y el mismo sillón
- **WHEN** se pide reprogramar el turno de Ana con `inicio` 14:15
- **THEN** el sistema responde `409` con `codigos` `["RN-AG-05", "RN-AG-08"]` y `conflictos` con dos elementos, en este orden, con la forma de E4: `{"codigo": "RN-AG-05", "recurso": "profesional", "recurso_id": 1, "turno_id": <id del turno de Bruno>}` y `{"codigo": "RN-AG-08", "recurso": "sillon", "recurso_id": 1, "turno_id": <id del turno de Bruno>}`
- **AND** el turno de Ana no cambia
- **AND** si el turno de Bruno está `cancelado_paciente`, la misma petición responde `200` de 14:15 a 14:45 (un turno no activo libera el horario, RN-AG-10)

#### Scenario: REP-1d Error de negocio - las reglas de un turno nuevo, de a una y sin cambiar el turno (RN-AG-10d, RN-AG-04, RN-AG-04b)

- **GIVEN** el turno de Ana, de 13:00 a 13:30, y un bloqueo del consultorio de `2026-11-03T12:00:00Z` a `2026-11-03T15:00:00Z`
- **WHEN** se pide reprogramarlo, en una corrida por caso, con `inicio` `2026-11-03T02:45:00Z` (23:45 del consultorio, cruzaría la medianoche), con `inicio` `2026-11-02T10:30:00Z` (07:30, antes del horario), con `inicio` `2026-11-07T13:00:00Z` (sábado, sin horario) y con `inicio` `2026-11-03T13:00:00Z` (sobre el bloqueo)
- **THEN** responden `422` con `codigos` `["RN-AG-10d"]`, `["RN-AG-04"]`, `["RN-AG-04"]` y `["RN-AG-04b"]` respectivamente, el último con el `bloqueo_id` del bloqueo
- **AND** en las cuatro el turno de Ana no cambia
- **AND** con un turno `reservado` de Bruno Ficticio de 07:30 a 08:00 del consultorio (`2026-11-02T10:30:00Z` a `11:00:00Z`) guardado antes de cargar el horario de 08:00 a 20:00 (el horario no toca los turnos existentes, D261), reprogramar el turno de Ana con `inicio` `2026-11-02T10:30:00Z` choca a la vez con el horario y con ese turno, y responde `422` con `codigos` `["RN-AG-04"]` solamente, sin `conflictos` (la primera regla que falla)

#### Scenario: REP-1e Borde - dos reprogramaciones simultáneas al mismo hueco: una sola gana (RN-AG-10c, perfil postgres)

- **GIVEN** en PostgreSQL dos turnos `reservado` del profesional 1 y el sillón 1, de 13:00 a 13:30 y de 14:00 a 14:30, y el hueco de 16:00 a 16:30 libre
- **WHEN** dos peticiones simultáneas reprograman cada turno a `inicio` 16:00 y, en otra corrida, una reprograma el primer turno a 16:00 mientras otra crea con `POST /turnos` un turno a las 16:00
- **THEN** en cada corrida una petición responde `200` o `201` y la otra `409` con `codigos` `["RN-AG-05", "RN-AG-08"]`
- **AND** a las 16:00 queda un solo turno activo, y el turno perdedor (o el que no se creó) no cambia ni suma eventos
- **AND** en otra corrida, dos reprogramaciones simultáneas del **mismo** turno a 16:00 y a 17:00 responden `200` las dos, una después de la otra: el turno queda en el horario de la que terminó última y su historial tiene dos eventos `reprogramado` cuyos `antes` encadenan (el `antes` del segundo es el `despues` del primero)

### Requirement: Reprogramar registra el evento `reprogramado` con el antes y el después

Una reprogramación aceptada SHALL registrar en el historial del turno exactamente un evento de tipo `reprogramado`, en la misma operación que guarda el horario nuevo: o quedan los dos o no queda ninguno (RN-AG-11, DD-05; US-012 CA-2). El evento SHALL llevar `ocurrido_en` igual al reloj de la API, `actor_tipo` `usuario` y `actor_id` igual al id del usuario del token como texto decimal (D209), `antes` y `despues` con `inicio`, `fin` (ISO UTC con `Z`) y `duracion_minutos` del turno antes y después del cambio, y `motivo` vacío. El evento SHALL registrarse **solo cuando algo cambia** (el inicio, la duración o los dos, D338): un rechazo o una petición sin cambios (D333) MUST NOT registrar ningún evento.

#### Scenario: REP-2a Feliz - el historial guarda el horario anterior y el nuevo (US-012 CA-2)

- **GIVEN** el turno de Ana, de 13:00 a 13:30, con su evento `creado`
- **WHEN** la recepcionista (usuario 2) lo reprograma con `inicio` 17:00 y `duracion_minutos` 45, y el sistema responde `200`
- **THEN** `GET /turnos/{id}/historial` devuelve dos eventos en este orden: el `creado` sin cambios y uno de `tipo` `reprogramado`
- **AND** el `reprogramado` tiene `ocurrido_en` `2026-10-29T12:00:00Z`, `actor_tipo` `usuario`, `actor_id` `"2"`, `antes` `{"inicio": "2026-11-02T13:00:00Z", "fin": "2026-11-02T13:30:00Z", "duracion_minutos": 30}`, `despues` `{"inicio": "2026-11-02T17:00:00Z", "fin": "2026-11-02T17:45:00Z", "duracion_minutos": 45}` y `motivo` vacío

#### Scenario: REP-2b Error de negocio - un rechazo no registra eventos y un evento que falla no deja el turno movido

- **GIVEN** el turno de Ana, de 13:00 a 13:30, con su evento `creado`
- **WHEN** se pide reprogramarlo y la petición se rechaza (en una corrida por causa) con `409` por solapamiento, con `422` por `RN-AG-04`, con `422` por `RN-AG-01`, con `403` por rol insuficiente o con `401` sin sesión; y, en otra corrida, una reprogramación válida a 17:00 cuyo registro del evento falla después de que el horario nuevo ya se envió a la base
- **THEN** en las primeras el historial sigue teniendo solo el evento `creado` y el turno no cambia
- **AND** en la última la operación termina con error, el turno sigue de 13:00 a 13:30 y no queda ningún evento `reprogramado`

### Requirement: Cambiar la duración recalcula el fin y exige un múltiplo de la granularidad

`duracion_minutos` SHALL ser un entero mayor que 0, múltiplo de la constante de 5 minutos y **no mayor que 1440** (24 horas) (RN-AG-01, D99, D333; US-012 CA-4). Una duración que no lo cumple es **validación de entrada**: se rechaza con `422`, el código `RN-AG-01` y un error del campo `duracion_minutos`, y se informa **junto** con `RN-GL-01` si `inicio` tampoco tiene zona UTC (RN-GL-02, D135, D176). Una duración desmedida MUST NOT terminar en un `500`. Con una duración válida, `fin` SHALL recalcularse y el turno SHALL validarse como en el requisito anterior.

#### Scenario: REP-3a Feliz - alargar un turno sin moverlo (US-012 CA-4)

- **GIVEN** el turno de Ana, de 13:00 a 13:30
- **WHEN** la odontóloga pide reprogramarlo con `{"duracion_minutos": 60}`
- **THEN** el sistema responde `200` con `inicio` `2026-11-02T13:00:00Z`, `fin` `2026-11-02T14:00:00Z` y `duracion_minutos` 60
- **AND** la duración de la prestación «Consulta / control» sigue siendo 30 (RN-AG-02)
- **AND** si un turno activo de Bruno empieza a las 13:45, la misma petición responde `409` con `codigos` `["RN-AG-05", "RN-AG-08"]` y el turno no cambia

#### Scenario: REP-3b Error de negocio - una duración que no es múltiplo de 5 se rechaza con RN-AG-01 junto con RN-GL-01

- **GIVEN** el turno de Ana, de 13:00 a 13:30
- **WHEN** se pide reprogramarlo, en una corrida por caso, con `duracion_minutos` 42, 0 y −5; y con `{"inicio": "2026-11-02T14:00:00", "duracion_minutos": 42}` (sin zona)
- **THEN** las tres primeras responden `422` con `codigos` `["RN-AG-01"]` y un error del campo `duracion_minutos`
- **AND** la última responde un único `422` con `codigos` `["RN-GL-01", "RN-AG-01"]` y los errores de los campos `inicio` y `duracion_minutos`
- **AND** en todas el turno no cambia
- **AND** `duracion_minutos` 5 es válida (`200`, de 13:00 a 13:05)

#### Scenario: REP-3c Borde - una duración por encima de 1440 minutos se rechaza con RN-AG-01, nunca con un 500 (D333)

- **GIVEN** el turno de Ana, de 13:00 a 13:30
- **WHEN** se pide reprogramarlo, en una corrida por caso, con `duracion_minutos` 1445 y con `duracion_minutos` 1000000000
- **THEN** las dos responden `422` con `codigos` `["RN-AG-01"]` y un error del campo `duracion_minutos`, nunca `500`
- **AND** en las dos el turno no cambia y su historial no suma eventos
- **AND** `duracion_minutos` 1440 pasa la validación de entrada y, desde las 13:00 (10:00 del consultorio), responde `422` con `codigos` `["RN-AG-10d"]` (cruzaría la medianoche), no `RN-AG-01`

### Requirement: Quién puede reprogramar, qué turno y qué cuerpo se aceptan

`PATCH /turnos/{id}` SHALL exigir el permiso `turnos.reprogramar`, que tienen el odontólogo y la recepcionista (matriz de `03`, fila Turnos); el control de acceso SHALL evaluarse antes que cualquier validación (D208): sin sesión válida, el `401` de sesión inválida; con un rol sin el permiso (el dueño) o sin roles, el `403` de permiso insuficiente con `RN-AU-05`. Después, un cuerpo mal formado (un campo de más, un `null` explícito, un tipo erróneo, un `inicio` que no es fecha y hora) o un id de la URL que no es entero SHALL responder `422` sin código RN. Un turno inexistente **o de otro consultorio** SHALL responder `404` con `RN-GL-04` y la referencia `turno` (D166, D321), antes de validar `inicio` y `duracion_minutos`. Una petición que no cambia ni el inicio ni la duración (cuerpo `{}` o los mismos valores) SHALL responder `200` con el turno tal como está, sin evaluar reglas de negocio (tampoco el estado, `RN-AG-18`) y sin registrar eventos (D333, D335).

#### Scenario: REP-4a Error de negocio - sin sesión 401; el dueño y el usuario sin roles 403 antes de validar

- **GIVEN** el turno de Ana
- **WHEN** se pide reprogramarlo con `inicio` 17:00 sin cabecera `Authorization`; con el token del dueño; y con el token del usuario sin roles, este último también con `{"inicio": "mal"}` y con el id 999
- **THEN** la primera responde el `401` de sesión inválida
- **AND** las demás responden el `403` de permiso insuficiente con `codigos` `["RN-AU-05"]`, nunca `422` ni `404`
- **AND** en todas el turno no cambia

#### Scenario: REP-4b Error de negocio - turno inexistente, de otro consultorio o petición mal formada

- **GIVEN** el turno de Ana y un turno de otro consultorio
- **WHEN** la recepcionista pide reprogramar el turno 999; el turno del otro consultorio; el turno de Ana con `{"inicio": "2026-11-02T17:00:00Z", "sillon_id": 2}`, con `{"inicio": null}`, con `{"duracion_minutos": "media hora"}`; y `PATCH /turnos/abc`
- **THEN** las dos primeras responden `404` con `codigos` `["RN-GL-04"]` y la referencia `turno` con su id y motivo `inexistente`, sin distinguir entre ellas
- **AND** las demás responden `422` con `codigos` vacío y un error que nombra el campo
- **AND** el turno 999 con `duracion_minutos` 42 responde `404`, no `422` (la existencia del turno va antes que la validación de `inicio` y `duracion_minutos`)
- **AND** ningún turno cambia

#### Scenario: REP-4c Borde - una petición que no cambia nada responde el turno sin evento

- **GIVEN** el turno de Ana, de 13:00 a 13:30, con su evento `creado`, y un bloqueo del consultorio que hoy cubre ese horario (creado después del turno, D83)
- **WHEN** la recepcionista pide reprogramarlo con `{}` y, en otra corrida, con `{"inicio": "2026-11-02T13:00:00Z", "duracion_minutos": 30}`
- **THEN** las dos responden `200` con el turno de 13:00 a 13:30, sin `RN-AG-04b`
- **AND** el historial sigue teniendo solo el evento `creado`

### Requirement: Solo un turno activo se reprograma

Solo un turno en estado activo (`pendiente_aprobacion`, `pendiente_sena`, `reservado`, `confirmado`) SHALL poder reprogramarse. Uno en estado terminal (`cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido`, `ausente`) SHALL rechazarse con `409` y el código `RN-AG-18` («el turno no se puede reprogramar en su estado»), que es una regla de negocio: se evalúa con la entrada válida, después de la existencia del turno y antes de RN-AG-10d, y el turno no cambia. La excepción es una petición sin cambios, que responde `200` antes de evaluar el estado (D335): un turno terminal con `{}` o con sus mismos valores no se rechaza ni registra eventos. Reprogramar MUST NOT cambiar el estado. El panel puede reprogramar en cualquier momento (D65): un turno ya pasado o un `inicio` nuevo en el pasado no se rechazan por eso.

#### Scenario: REP-5a Error de negocio - un turno terminal no se reprograma y uno activo sí, sin cambiar su estado

- **GIVEN** cinco turnos de Ana de 13:00 a 13:30, uno por cada estado terminal (`cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido`, `ausente`; no ocupan el horario, RN-AG-10), y cuatro turnos de Bruno Ficticio de 30 minutos, uno por cada estado activo: `pendiente_aprobacion` a las 14:00, `pendiente_sena` a las 15:00, `reservado` a las 16:00 y `confirmado` a las 17:00
- **WHEN** la recepcionista pide reprogramar cada terminal con `inicio` 19:00 y cada activo media hora después de su inicio (14:30, 15:30, 16:30 y 17:30)
- **THEN** los cinco terminales responden `409` con `codigos` `["RN-AG-18"]` y no cambian
- **AND** los cuatro activos responden `200` con su nuevo horario y su mismo `estado`
- **AND** un turno `reservado` del 2026-10-26 (ya pasado según el reloj) reprogramado a `2026-10-27T13:00:00Z` responde `200`
- **AND** un turno `cancelado_paciente` con `duracion_minutos` 42 responde `422` `RN-AG-01`, no `409` (la entrada se valida antes que el estado)

#### Scenario: REP-5b Borde - un turno terminal con una petición sin cambios responde 200 sin evento (D333, D335)

- **GIVEN** un turno `atendido` de Ana Ejemplo de 13:00 a 13:30, con su evento `creado`
- **WHEN** la recepcionista pide reprogramarlo con `{}` y, en otra corrida, con `{"inicio": "2026-11-02T13:00:00Z", "duracion_minutos": 30}`
- **THEN** las dos responden `200` con el turno tal como está (`estado` `atendido`, de 13:00 a 13:30), sin `RN-AG-18`
- **AND** su historial sigue teniendo solo el evento `creado`
- **AND** la misma petición con `inicio` 17:00 responde `409` con `codigos` `["RN-AG-18"]` y el turno no cambia
