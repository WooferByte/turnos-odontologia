# horario-recurrente Specification

## Purpose
Define la API con la que el odontólogo configura el horario recurrente semanal de un profesional (sus días y franjas de atención, en hora del consultorio) y con la que el panel lo consulta y elige al profesional (US-002; RN-AG-04, RN-AG-16, RN-AU-05, RN-GL-04).

Convenciones de los escenarios: las horas de una franja (`hora_inicio`, `hora_fin`) son **horas del consultorio** (`America/Argentina/Buenos_Aires`, UTC−3), en formato `HH:MM` de 24 horas; `dia_semana` va de 0 (lunes) a 6 (domingo). Una franja es el intervalo semiabierto `[hora_inicio, hora_fin)`. «Con el token de X» significa con la cabecera `Authorization: Bearer <access token>` de un access token vigente emitido para X por `POST /auth/login` (capability `sesion-del-panel`); el `401` de sesión inválida y el `403` de permiso insuficiente son los de `proteccion-del-panel` (`RN-AU-03` y `RN-AU-05`). Un error sale como `application/problem+json` con `codigos`. «La odontóloga» tiene el rol `odontologo`, «la recepcionista» solo `recepcionista` y «el dueño» solo `dueno`; «el profesional 1» es un profesional activo del único consultorio de la instalación (D173). Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite por defecto, salvo que digan otra cosa. Tipos de escenario en el título: Feliz, Error de negocio, Borde, Error de formato (`422` sin código) y **Error de entrada** (`422` de validación de entrada del dominio con su código RN, RN-GL-02; acá, `RN-AG-16`).

## Requirements

### Requirement: Consultar el horario de un profesional

`GET /profesionales/{id}/horario` SHALL responder `200` con `profesional_id`, `zona_horaria` (la del consultorio) y `franjas`: todas las franjas del profesional, cada una con `dia_semana`, `hora_inicio` y `hora_fin`, ordenadas por día y por hora de inicio. Un profesional sin franjas SHALL responder `franjas` vacía. Pueden leer los tres roles (matriz de `03`, fila «Horario recurrente y bloqueos»). Un `id` de la URL que no es un entero SHALL responder `422` con `codigos` vacío (formato), sin buscar ningún profesional.

#### Scenario: US-002 CA-1 Feliz - se leen las franjas de mañana y de tarde

- **GIVEN** el profesional 1 con las franjas lunes 15:00-19:00 y lunes 09:00-13:00, cargadas en ese orden
- **WHEN** la recepcionista pide con su token `GET /profesionales/1/horario`
- **THEN** el sistema responde `200` con `zona_horaria` `America/Argentina/Buenos_Aires` y `franjas` exactamente `[{dia_semana: 0, hora_inicio: "09:00", hora_fin: "13:00"}, {dia_semana: 0, hora_inicio: "15:00", hora_fin: "19:00"}]`

#### Scenario: US-002 CA-1 Borde - un profesional sin horario responde la lista vacía

- **GIVEN** el profesional 1 sin franjas
- **WHEN** el dueño pide con su token `GET /profesionales/1/horario`
- **THEN** el sistema responde `200` con `franjas` vacía

#### Scenario: US-002 CA-1 Error de negocio - un profesional inexistente responde 404

- **WHEN** la odontóloga pide con su token `GET /profesionales/999/horario`
- **THEN** el sistema responde `404` con `codigos` `["RN-GL-04"]` y una referencia con `recurso` `profesional`, `recurso_id` 999 y `motivo` `inexistente`

#### Scenario: US-002 CA-1 Borde - un id que no es entero responde 422 de formato

- **WHEN** la odontóloga pide con su token `GET /profesionales/abc/horario`
- **THEN** el sistema responde `422` con `codigos` vacío y un error de campo del `id`, no `404`

### Requirement: Reemplazar el horario de un profesional

`PUT /profesionales/{id}/horario` SHALL reemplazar todas las franjas del profesional por las del cuerpo (`franjas`, una lista que puede estar vacía) y responder `200` con el horario resultante, con la misma forma que `GET`. Las franjas SHALL guardarse sin vigencia (siempre vigentes; la vigencia no viaja en la API, D259). Un rechazo MUST NOT cambiar ninguna franja. Reemplazar el horario MUST NOT modificar, cancelar ni informar turnos existentes (D261).

#### Scenario: US-002 CA-1 Feliz - la odontóloga carga mañana y tarde

- **GIVEN** el profesional 1 sin franjas
- **WHEN** la odontóloga pide con su token `PUT /profesionales/1/horario` con las franjas miércoles 15:00-19:00 y miércoles 09:00-13:00
- **THEN** el sistema responde `200` con `franjas` `[{dia_semana: 2, hora_inicio: "09:00", hora_fin: "13:00"}, {dia_semana: 2, hora_inicio: "15:00", hora_fin: "19:00"}]`
- **AND** un `GET /profesionales/1/horario` posterior devuelve exactamente esas dos franjas

#### Scenario: US-002 CA-1 Borde - franjas contiguas del mismo día no se superponen

- **WHEN** la odontóloga pide `PUT /profesionales/1/horario` con las franjas lunes 09:00-13:00 y lunes 13:00-17:00
- **THEN** el sistema responde `200` con las dos franjas

#### Scenario: US-002 CA-1 Borde - el mismo horario en días distintos se acepta

- **WHEN** la odontóloga pide `PUT /profesionales/1/horario` con lunes 09:00-13:00 y martes 09:00-13:00
- **THEN** el sistema responde `200` con las dos franjas

#### Scenario: US-002 CA-1 Borde - reemplazar quita las franjas anteriores

- **GIVEN** el profesional 1 con lunes 09:00-13:00 y lunes 15:00-19:00
- **WHEN** la odontóloga pide `PUT /profesionales/1/horario` con solo martes 10:00-14:00, y después con `franjas` vacía
- **THEN** la primera respuesta tiene solo la franja del martes y la segunda tiene `franjas` vacía
- **AND** un turno ya creado del profesional 1 sigue en la base con su estado

### Requirement: Rechazar franjas superpuestas o invertidas

El sistema SHALL rechazar el `PUT` cuyo cuerpo tiene dos franjas del mismo día que se superponen (US-002 CA-1, HOR-1) o una franja con `hora_inicio` igual o posterior a `hora_fin`, con `422` y el código `RN-AG-16` (D257). Es validación de entrada (RN-GL-02), no una regla de negocio: SHALL informar juntas, cada una como un error de campo `franjas.<i>` (su posición en la lista) con `codigo` `RN-AG-16`, las franjas invertidas y las que se superponen con alguna anterior válida del mismo día, y no cambiar nada. Una franja invertida no se compara con las demás. «Válida» es «no invertida»: una franja anterior que ya se informó por superponerse sigue contando para las posteriores (D266). El `mensaje` de cada error SHALL ser fijo según la causa (D266): `franjas.<i> se superpone con otra franja del mismo día` o `franjas.<i> debe terminar después de empezar`.

#### Scenario: HOR-1 Error de entrada - dos franjas superpuestas del mismo día se rechazan

- **GIVEN** el profesional 1 con lunes 09:00-13:00
- **WHEN** la odontóloga pide `PUT /profesionales/1/horario` con miércoles 09:00-13:00 y miércoles 12:00-16:00
- **THEN** el sistema responde `422` con `codigos` exactamente `["RN-AG-16"]` y un único error de campo: `campo` `franjas.1`, `codigo` `RN-AG-16` y `mensaje` `franjas.1 se superpone con otra franja del mismo día`
- **AND** el horario sigue siendo solo lunes 09:00-13:00

#### Scenario: HOR-1 Borde - en una cadena de tres franjas se informan las dos posteriores

- **GIVEN** el profesional 1 con lunes 09:00-13:00
- **WHEN** la odontóloga pide `PUT /profesionales/1/horario` con miércoles 09:00-13:00, miércoles 12:00-16:00 y miércoles 15:00-19:00
- **THEN** el sistema responde `422` con `codigos` `["RN-AG-16"]` y dos errores, en este orden: `franjas.1` con `franjas.1 se superpone con otra franja del mismo día` y `franjas.2` con `franjas.2 se superpone con otra franja del mismo día`; ninguno en `franjas.0` (la 15:00-19:00 se superpone con la 12:00-16:00, que no está invertida aunque ya se informó, D266)
- **AND** el horario sigue siendo solo lunes 09:00-13:00

#### Scenario: HOR-1 Borde - se informan juntas las superposiciones de varios días y una franja invertida

- **WHEN** la odontóloga pide `PUT /profesionales/1/horario` con lunes 09:00-13:00, lunes 12:59-14:00, martes 10:00-11:00, martes 10:30-10:45 y jueves 18:00-09:00
- **THEN** el sistema responde un único `422` con `codigos` `["RN-AG-16"]` y tres errores, en este orden: `franjas.1` con `franjas.1 se superpone con otra franja del mismo día`, `franjas.3` con `franjas.3 se superpone con otra franja del mismo día` y `franjas.4` con `franjas.4 debe terminar después de empezar`
- **AND** no cambia ninguna franja

#### Scenario: HOR-1 Borde - una franja de duración cero se rechaza

- **WHEN** la odontóloga pide `PUT /profesionales/1/horario` con lunes 09:00-09:00
- **THEN** el sistema responde `422` con `codigos` `["RN-AG-16"]` y un único error: `franjas.0` con `franjas.0 debe terminar después de empezar`

#### Scenario: HOR-1 Borde - dos franjas idénticas del mismo día se superponen

- **WHEN** la odontóloga pide `PUT /profesionales/1/horario` con lunes 09:00-13:00 dos veces
- **THEN** el sistema responde `422` con `codigos` `["RN-AG-16"]` y un único error: `franjas.1` con `franjas.1 se superpone con otra franja del mismo día`
- **AND** no cambia ninguna franja

### Requirement: Rechazar un cuerpo mal formado del horario

El sistema SHALL rechazar con `422` y `codigos` vacío, informando todos los campos juntos, un cuerpo sin `franjas`, con un campo de más, con `dia_semana` fuera de 0 a 6, con una hora que no sea `HH:MM` de 00:00 a 23:59 o con **más de 70 franjas en total** (un tope de tamaño del pedido, no por día; D268). El formato SHALL evaluarse antes que `RN-AG-16`. Un rechazo de formato MUST NOT cambiar ninguna franja.

#### Scenario: US-002 CA-1 Borde - día y hora mal formados se informan juntos

- **WHEN** la odontóloga pide `PUT /profesionales/1/horario` con una franja `dia_semana` 7 y otra con `hora_fin` `"24:00"`
- **THEN** el sistema responde un único `422` con `codigos` vacío y dos errores de campo
- **AND** no cambia ninguna franja

#### Scenario: US-002 CA-1 Borde - con formato inválido no se evalúa la superposición

- **WHEN** la odontóloga pide `PUT /profesionales/1/horario` con lunes 09:00-13:00, lunes 12:00-16:00 y un campo `color` de más
- **THEN** el sistema responde `422` con `codigos` vacío, solo con el error del campo de más

#### Scenario: US-002 CA-1 Borde - más de 70 franjas se rechazan como formato

- **GIVEN** el profesional 1 con lunes 09:00-13:00
- **WHEN** la odontóloga pide `PUT /profesionales/1/horario` con 71 franjas válidas y sin superposiciones (diez franjas de una hora por día, de 08:00 a 18:00, de lunes a domingo, más domingo 18:00-19:00)
- **THEN** el sistema responde `422` con `codigos` vacío y un error del campo `franjas`
- **AND** el horario sigue siendo solo lunes 09:00-13:00
- **AND** el mismo pedido sin la franja del domingo 18:00-19:00 (70 franjas) responde `200` con las 70

### Requirement: Permisos y orden de evaluación del horario

`GET /profesionales/{id}/horario` SHALL aceptar `odontologo`, `recepcionista` y `dueno`; `PUT`, solo `odontologo` (`403` `RN-AU-05`). El orden SHALL ser: sesión (`401`), permiso (`403`), formato del cuerpo (`422`), `RN-AG-16` (`422`) y profesional de la URL (`404` `RN-GL-04`, también para uno de otro consultorio). Un profesional inactivo SHALL poder consultarse y editarse (D262).

#### Scenario: US-002 CA-1 Error de negocio - la recepcionista y el dueño no pueden reemplazar el horario

- **GIVEN** el profesional 1 con lunes 09:00-13:00
- **WHEN** la recepcionista y después el dueño piden con su token `PUT /profesionales/1/horario` con martes 09:00-13:00
- **THEN** cada uno recibe `403` con `codigos` `["RN-AU-05"]` y el horario sigue siendo lunes 09:00-13:00

#### Scenario: US-002 CA-1 Borde - el permiso y la entrada se evalúan antes que el profesional

- **WHEN** la recepcionista pide `PUT /profesionales/999/horario` con dos franjas superpuestas, y la odontóloga pide `PUT /profesionales/999/horario` con esas franjas y después con un cuerpo válido
- **THEN** la recepcionista recibe `403` `RN-AU-05`; la odontóloga recibe `422` `RN-AG-16` y después `404` `RN-GL-04`

#### Scenario: US-002 CA-1 Borde - sin sesión se responde 401 antes que la entrada

- **WHEN** se pide `PUT /profesionales/1/horario` sin la cabecera `Authorization` y con `dia_semana` 9
- **THEN** el sistema responde el `401` de sesión inválida, no `422`

#### Scenario: US-002 CA-1 Borde - el horario de un profesional inactivo se puede editar

- **GIVEN** el profesional 2, inactivo
- **WHEN** la odontóloga pide `PUT /profesionales/2/horario` con lunes 09:00-13:00 y después `GET`
- **THEN** las dos respuestas son `200` con esa franja

#### Scenario: US-002 CA-1 Error de negocio - un profesional de otro consultorio responde 404

- **GIVEN** un segundo consultorio con el profesional 3, guardados directo en la base (la instalación tiene un solo consultorio, D173: este caso no se arma por la API)
- **WHEN** la odontóloga pide `GET /profesionales/3/horario` y después `PUT /profesionales/3/horario` con lunes 09:00-13:00
- **THEN** las dos respuestas son `404` con `codigos` `["RN-GL-04"]` y una referencia al `profesional` 3
- **AND** el profesional 3 sigue sin franjas y `GET /profesionales` no lo lista

### Requirement: Listar los profesionales para elegir su horario

`GET /profesionales` SHALL responder `200` con los profesionales del consultorio, activos e inactivos, ordenados por `id`, cada uno con `id`, `nombre` y `activo`. Es de solo lectura y la pueden usar los tres roles (D260).

#### Scenario: US-002 CA-1 Feliz - la recepcionista lista los profesionales

- **GIVEN** el profesional 1 activo «Dra. Demo Ficticia» y el profesional 2 inactivo
- **WHEN** la recepcionista pide con su token `GET /profesionales`
- **THEN** el sistema responde `200` con `[{id: 1, nombre: "Dra. Demo Ficticia", activo: true}, {id: 2, …, activo: false}]`

#### Scenario: US-002 CA-1 Borde - sin sesión no se listan

- **WHEN** se pide `GET /profesionales` sin la cabecera `Authorization`
- **THEN** el sistema responde el `401` de sesión inválida

### Requirement: La demo trae el horario de ejemplo

Los datos de la demo (SQLite en memoria y PostgreSQL, D148) SHALL incluir para el profesional 1 el horario de ejemplo de `04` (D56): lunes a viernes 09:00-13:00 y 15:00-19:00, sin franjas el sábado y el domingo. En PostgreSQL SHALL cargarse solo si el profesional 1 no tiene franjas.

#### Scenario: US-002 CA-1 Feliz - la demo arranca con el horario de ejemplo

- **GIVEN** la demo recién arrancada
- **WHEN** la odontóloga pide `GET /profesionales/1/horario`
- **THEN** la respuesta tiene diez franjas: 09:00-13:00 y 15:00-19:00 de cada día de 0 a 4
- **AND** el ejemplo del README, `POST /turnos` con `inicio` `2026-11-02T13:00:00Z` (lunes 10:00 del consultorio), responde `201`

#### Scenario: US-002 CA-1 Borde - volver a cargar la demo en PostgreSQL no duplica el horario

- **GIVEN** una base PostgreSQL con la demo ya cargada
- **WHEN** se vuelve a ejecutar la carga de la demo
- **THEN** el profesional 1 sigue con las mismas diez franjas
- **AND** este escenario se verifica en el perfil opcional `postgres`
