## Purpose

Define la API con la que el odontólogo bloquea días u horas de un profesional, de un sillón o de todo el consultorio (vacaciones, feriados, ausencias, mantenimiento), conoce los turnos activos que quedan dentro del bloqueo sin que se cancelen, y con la que el panel lista y elimina esos bloqueos (US-003; RN-AG-04b, RN-AG-17, RN-GL-01, RN-GL-04, RN-AU-05).

Convenciones de los escenarios: todos los horarios están en **UTC** (el consultorio está en `America/Argentina/Buenos_Aires`, UTC−3); «10:00» significa `2026-11-02T10:00:00Z`, un lunes. Un bloqueo es el intervalo semiabierto `[inicio, fin)` (RN-AG-09) y su **alcance** es `profesional` (con `profesional_id`), `sillon` (con `sillon_id`) o `consultorio` (sin ninguno de los dos). Un turno «activo» está en `pendiente_aprobacion`, `pendiente_sena`, `reservado` o `confirmado` (RN-AG-10). «Con el token de X» significa con la cabecera `Authorization: Bearer <access token>` de un access token vigente emitido para X por `POST /auth/login` (capability `sesion-del-panel`); el `401` de sesión inválida y el `403` de permiso insuficiente son los de `proteccion-del-panel` (`RN-AU-03` y `RN-AU-05`). Un error sale como `application/problem+json` con `codigos`. «La odontóloga» tiene el rol `odontologo`, «la recepcionista» solo `recepcionista` y «el dueño» solo `dueno`; «el profesional 1» y «el sillón 1» son activos del único consultorio de la instalación (D173). Los turnos de los escenarios se guardan directo en la base. Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite por defecto, salvo que digan otra cosa. Tipos de escenario en el título: Feliz, Error de negocio, Borde, Error de formato (`422` sin código) y **Error de entrada** (`422` de validación de entrada del dominio con su código RN, RN-GL-02). Las elecciones de este spec que salieron de las preguntas abiertas del design son decisiones del autor del 2026-10-26 (D271 a D289) y citan su D.

## ADDED Requirements

### Requirement: Crear un bloqueo del profesional, del sillón o de todo el consultorio

`POST /bloqueos` con `inicio`, `fin`, `motivo` y, opcionales, `profesional_id` o `sillon_id` SHALL guardar el bloqueo en el consultorio del usuario del token, con `creado_por` igual a ese usuario, y responder `201` con `id`, `alcance`, `profesional_id`, `sillon_id`, `inicio`, `fin`, `motivo`, `creado_por` y `turnos_afectados` (US-003 CA-1; RN-AG-04b). SHALL aceptar un bloqueo que se superpone con otro (D276) o que está en el pasado (D277: el alta no mira el reloj), y cualquier minuto en `inicio` y `fin`, sin exigir múltiplos de 5 (D289: la granularidad de D99 es la de la duración de la prestación, RN-AG-01). No hay tope de duración del bloqueo ni de cantidad de bloqueos (límite conocido, D289).

#### Scenario: US-003 CA-1 Feliz - la odontóloga bloquea al profesional por vacaciones

- **GIVEN** el profesional 1 sin turnos
- **WHEN** la odontóloga pide con su token `POST /bloqueos` con `profesional_id` 1, `inicio` `2026-11-09T03:00:00Z`, `fin` `2026-11-14T03:00:00Z` y `motivo` «Vacaciones»
- **THEN** el sistema responde `201` con `alcance` `profesional`, `profesional_id` 1, `sillon_id` nulo, ese `inicio` y ese `fin`, `motivo` «Vacaciones», `creado_por` el id de la odontóloga y `turnos_afectados` vacía
- **AND** un `GET /bloqueos` posterior lo lista

#### Scenario: US-003 CA-1 Feliz - un bloqueo del sillón por mantenimiento

- **WHEN** la odontóloga pide `POST /bloqueos` con `sillon_id` 1, `inicio` `2026-11-02T13:07:00Z`, `fin` `2026-11-02T14:53:00Z` y `motivo` «Mantenimiento del sillón»
- **THEN** el sistema responde `201` con `alcance` `sillon`, `sillon_id` 1, `profesional_id` nulo y ese `inicio` y ese `fin` (minutos que no son múltiplo de 5, D289)

#### Scenario: US-003 CA-1 Feliz - un bloqueo de todo el consultorio por un feriado

- **WHEN** la odontóloga pide `POST /bloqueos` sin `profesional_id` ni `sillon_id`, con `inicio` `2026-11-23T03:00:00Z`, `fin` `2026-11-24T03:00:00Z` (el lunes 23 completo del consultorio) y `motivo` «Feriado»
- **THEN** el sistema responde `201` con `alcance` `consultorio` y `profesional_id` y `sillon_id` nulos

#### Scenario: US-003 CA-1 Borde - un bloqueo que se superpone con otro se acepta

- **GIVEN** un bloqueo del profesional 1 de 13:00 a 15:00
- **WHEN** la odontóloga pide `POST /bloqueos` con `profesional_id` 1, `inicio` 14:00, `fin` 16:00 y `motivo` «Ausencia»
- **THEN** el sistema responde `201` y `GET /bloqueos` lista los dos

#### Scenario: US-003 CA-1 Borde - un bloqueo en el pasado se acepta, lista sus turnos activos y se elimina

- **GIVEN** el reloj de la aplicación fijado en `2026-11-10T12:00:00Z`, y el profesional 1 con un turno `atendido` de 13:00 a 13:30 y uno `reservado` de 14:00 a 14:30 (los dos del lunes 2, ya pasados)
- **WHEN** la odontóloga pide `POST /bloqueos` con `profesional_id` 1, `inicio` 12:00, `fin` 16:00 y `motivo` «Ausencia»
- **THEN** el sistema responde `201` con `turnos_afectados` con solo el turno `reservado` de 14:00 (el `atendido` no es activo)
- **AND** un `DELETE /bloqueos/<id>` posterior de la odontóloga responde `204` (D277)

### Requirement: Listar los turnos activos afectados sin cancelarlos

La respuesta de `POST /bloqueos` SHALL incluir en `turnos_afectados` los turnos activos del alcance (los del profesional, los del sillón o todos los del consultorio) cuyo `[inicio, fin)` interseca el del bloqueo, ordenados por `inicio` y por `id`, cada uno con `id`, `inicio`, `fin`, `estado`, `profesional_id`, `sillon_id` y `paciente_id`, sin otros datos del paciente (US-003 CA-2; RN-AG-04b, RN-AG-09, RN-AG-10; D275). Crear el bloqueo MUST NOT cancelar, modificar ni registrar en el historial ningún turno (D83).

#### Scenario: US-003 CA-2 Feliz - el bloqueo del profesional lista sus dos turnos activos

- **GIVEN** el profesional 1 con un turno `confirmado` de 14:00 a 14:30 y uno `reservado` de 13:00 a 13:30
- **WHEN** la odontóloga pide `POST /bloqueos` con `profesional_id` 1, `inicio` 12:00, `fin` 16:00 y `motivo` «Ausencia»
- **THEN** el sistema responde `201` con `turnos_afectados` con los dos turnos, primero el de 13:00 y después el de 14:00, cada uno con su `estado`
- **AND** los dos turnos siguen en la base con el mismo estado y sin eventos nuevos en su historial

#### Scenario: US-003 CA-2 Borde - los turnos no activos y los contiguos no se listan

- **GIVEN** el profesional 1 con un turno `cancelado` de 13:00 a 13:30, uno `atendido` de 13:30 a 14:00, uno `reservado` de 11:30 a 12:00 (termina justo cuando empieza el bloqueo), uno `reservado` de 16:00 a 16:30 (empieza justo cuando termina) y uno `reservado` de 15:59 a 16:29
- **WHEN** la odontóloga pide `POST /bloqueos` con `profesional_id` 1, `inicio` 12:00, `fin` 16:00 y `motivo` «Ausencia»
- **THEN** `turnos_afectados` tiene solo el turno de 15:59 a 16:29 (un minuto de intersección)

#### Scenario: US-003 CA-2 Borde - cada alcance lista sus propios turnos

- **GIVEN** un segundo profesional activo y un segundo sillón activo del consultorio, un turno `reservado` del profesional 1 en el sillón 1 de 13:00 a 13:30 y uno `reservado` del segundo profesional en el segundo sillón de 13:00 a 13:30
- **WHEN** la odontóloga crea un bloqueo del sillón 1 de 12:00 a 16:00, después uno del segundo profesional de 12:00 a 16:00 y después uno de todo el consultorio de 12:00 a 16:00
- **THEN** el del sillón 1 lista solo el turno del sillón 1, el del segundo profesional lista solo el suyo y el del consultorio lista los dos

#### Scenario: US-003 CA-2 Borde - un turno de otro consultorio no se lista

- **GIVEN** un segundo consultorio con un turno `reservado` de 13:00 a 13:30, guardados directo en la base (la instalación tiene un solo consultorio, D173)
- **WHEN** la odontóloga pide `POST /bloqueos` de todo el consultorio de 12:00 a 16:00
- **THEN** `turnos_afectados` está vacía

### Requirement: Rechazar la entrada inválida de un bloqueo

El sistema SHALL rechazar en un único `422`, con todos los códigos juntos y sin guardar nada (RN-GL-02): `inicio` o `fin` sin zona o con un desfase distinto de UTC (`RN-GL-01`); un `profesional_id` o `sillon_id` inexistente, inactivo o de otro consultorio (`RN-GL-04`, todas las referencias; D274); y un `fin` que no es posterior a `inicio` (`RN-AG-17`, D273), que no se evalúa si alguna de las dos fechas es inválida.

#### Scenario: US-003 CA-1 Error de entrada - un bloqueo que no termina después de empezar se rechaza

- **WHEN** la odontóloga pide `POST /bloqueos` con `profesional_id` 1, `inicio` 15:00, `fin` 13:00 y `motivo` «Ausencia»; y después con `inicio` y `fin` 13:00
- **THEN** cada pedido recibe `422` con `codigos` exactamente `["RN-AG-17"]` y un error de campo en `fin`
- **AND** no se guarda ningún bloqueo

#### Scenario: US-003 CA-1 Error de entrada - fecha sin zona y referencias inválidas se informan juntas

- **GIVEN** un sillón inactivo con id 2
- **WHEN** la odontóloga pide `POST /bloqueos` con `profesional_id` 999, `inicio` `2026-11-02T13:00:00` (sin zona), `fin` 15:00 y `motivo` «Ausencia»; y después con `sillon_id` 2, `inicio` 13:00 y `fin` 15:00
- **THEN** el primer pedido recibe un único `422` con `codigos` `RN-GL-01` y `RN-GL-04` (referencia al `profesional` 999 `inexistente`), sin `RN-AG-17`
- **AND** el segundo recibe `422` con `codigos` `["RN-GL-04"]` y una referencia al `sillon` 2 con `motivo` `inactivo`
- **AND** no se guarda ningún bloqueo

#### Scenario: US-003 CA-1 Borde - un profesional de otro consultorio cuenta como inexistente

- **GIVEN** un segundo consultorio con el profesional 3, guardados directo en la base
- **WHEN** la odontóloga pide `POST /bloqueos` con `profesional_id` 3, `inicio` 13:00, `fin` 15:00 y `motivo` «Ausencia»
- **THEN** el sistema responde `422` con `codigos` `["RN-GL-04"]` y una referencia al `profesional` 3 con `motivo` `inexistente`

### Requirement: Rechazar un cuerpo mal formado del bloqueo

El sistema SHALL rechazar con `422` y `codigos` vacío, informando todos los campos juntos y sin guardar nada, un cuerpo sin `inicio`, `fin` o `motivo`, con un campo de más, con un `motivo` vacío o de más de 200 caracteres después de quitar los espacios de más (D283), o con `profesional_id` y `sillon_id` a la vez (D272). El `motivo` SHALL guardarse y devolverse sin espacios de más. El formato SHALL evaluarse antes que la validación de entrada del dominio.

#### Scenario: US-003 CA-1 Borde - el profesional y el sillón a la vez son un error de formato

- **WHEN** la odontóloga pide `POST /bloqueos` con `profesional_id` 1, `sillon_id` 1, `inicio` 13:00, `fin` 15:00 y `motivo` «Ausencia»
- **THEN** el sistema responde `422` con `codigos` vacío y no se guarda ningún bloqueo

#### Scenario: US-003 CA-1 Borde - motivo vacío y campo de más se informan juntos antes que la fecha invertida

- **WHEN** la odontóloga pide `POST /bloqueos` con `inicio` 15:00, `fin` 13:00, `motivo` «   » y un campo `color` de más
- **THEN** el sistema responde un único `422` con `codigos` vacío y dos errores de campo (`motivo` y el campo de más), sin `RN-AG-17`

#### Scenario: US-003 CA-1 Borde - el motivo admite hasta 200 caracteres y se guarda sin espacios de más

- **WHEN** la odontóloga pide tres `POST /bloqueos` con `profesional_id` 1, `inicio` 13:00 y `fin` 15:00: el primero con un `motivo` de 200 caracteres, el segundo con uno de 201 y el tercero con `motivo` «  Vacaciones  »
- **THEN** el primero responde `201` y el tercero `201` con `motivo` «Vacaciones»
- **AND** el segundo responde `422` con `codigos` vacío y un error de campo en `motivo`
- **AND** `GET /bloqueos` lista solo dos bloqueos (D283)

### Requirement: Listar los bloqueos del consultorio

`GET /bloqueos` SHALL responder `200` con `zona_horaria` (la del consultorio del usuario del token) y `bloqueos`: todos los bloqueos de ese consultorio, pasados y futuros, ordenados por `inicio` y por `id`, cada uno con los campos de la respuesta del alta salvo `turnos_afectados`, sin filtros ni paginación (D279). Pueden leer los tres roles (matriz de `03`, fila «Horario recurrente y bloqueos»).

#### Scenario: US-003 CA-1 Feliz - la recepcionista lista los bloqueos

- **GIVEN** un bloqueo de todo el consultorio del `2026-11-23T03:00:00Z` al `2026-11-24T03:00:00Z` y uno del profesional 1 de 13:00 a 15:00
- **WHEN** la recepcionista pide con su token `GET /bloqueos`
- **THEN** el sistema responde `200` con `zona_horaria` `America/Argentina/Buenos_Aires` y los dos bloqueos, primero el del profesional y después el del consultorio, sin `turnos_afectados`

#### Scenario: US-003 CA-1 Borde - un bloqueo de otro consultorio no se lista

- **GIVEN** un segundo consultorio con un bloqueo, guardados directo en la base, y ningún bloqueo en el consultorio de la instalación
- **WHEN** el dueño pide con su token `GET /bloqueos`
- **THEN** el sistema responde `200` con `bloqueos` vacía

### Requirement: Eliminar un bloqueo

`DELETE /bloqueos/{id}` SHALL eliminar el bloqueo del consultorio del usuario del token y responder `204` sin cuerpo; es un borrado físico y vale también para un bloqueo pasado (D278, D277). Eliminar un bloqueo MUST NOT cambiar ningún turno. Un bloqueo inexistente o de otro consultorio SHALL responder `404` con `RN-GL-04`; un `id` que no es un entero, `422` con `codigos` vacío.

#### Scenario: US-003 CA-1 Feliz - la odontóloga elimina un bloqueo

- **GIVEN** un bloqueo del profesional 1 de 13:00 a 15:00 y un turno `reservado` del profesional 1 de 13:00 a 13:30
- **WHEN** la odontóloga pide con su token `DELETE /bloqueos/<id>`
- **THEN** el sistema responde `204`, `GET /bloqueos` ya no lo lista y el turno sigue `reservado`

#### Scenario: US-003 CA-1 Error de negocio - un bloqueo inexistente o de otro consultorio responde 404

- **GIVEN** un segundo consultorio con un bloqueo de id 7, guardados directo en la base
- **WHEN** la odontóloga pide `DELETE /bloqueos/999`, después `DELETE /bloqueos/7` y después `DELETE /bloqueos/abc`
- **THEN** las dos primeras respuestas son `404` con `codigos` `["RN-GL-04"]` y una referencia con `recurso` `bloqueo` y `motivo` `inexistente`; la tercera es `422` con `codigos` vacío
- **AND** el bloqueo 7 sigue en la base

### Requirement: Permisos y orden de evaluación de los bloqueos

`GET /bloqueos` SHALL aceptar `odontologo`, `recepcionista` y `dueno`; `POST` y `DELETE`, solo `odontologo` (`403` `RN-AU-05`). El orden SHALL ser: sesión (`401`), permiso (`403`), formato (`422` sin código), validación de entrada del dominio (`422` con código, solo en `POST`) y bloqueo de la URL (`404`, solo en `DELETE`) (RN-GL-02, D208).

#### Scenario: US-003 CA-1 Error de negocio - la recepcionista y el dueño no pueden crear ni eliminar bloqueos

- **GIVEN** un bloqueo del profesional 1 de 13:00 a 15:00
- **WHEN** la recepcionista y después el dueño piden con su token `POST /bloqueos` con un cuerpo válido y `DELETE /bloqueos/<id>`
- **THEN** cada pedido recibe `403` con `codigos` `["RN-AU-05"]`
- **AND** sigue habiendo un solo bloqueo

#### Scenario: US-003 CA-1 Borde - sin sesión se responde 401 antes que la entrada

- **WHEN** se pide `POST /bloqueos` sin la cabecera `Authorization` y con `fin` anterior a `inicio`, y `GET /bloqueos` sin la cabecera
- **THEN** las dos respuestas son el `401` de sesión inválida, no `422`

#### Scenario: US-003 CA-1 Borde - el permiso se evalúa antes que la entrada y que el bloqueo de la URL

- **WHEN** la recepcionista pide `POST /bloqueos` con `fin` anterior a `inicio` y `DELETE /bloqueos/999`
- **THEN** las dos respuestas son `403` `RN-AU-05`, no `422` ni `404`
