# pantalla-de-agenda Specification

## Purpose

Define cómo el panel muestra en el navegador la agenda de un día del consultorio y cómo crea un turno desde ella: qué se ve de cada turno, cómo se cambia de día, cómo se ven los rechazos de `POST /turnos` con su código y qué pasa si la sesión termina en la pantalla (US-011 CA-1 y CA-2; E4, E12; US-092 CA-1).

Convenciones de los escenarios: la API es la de `consulta-de-turnos` (leer) y la de `creacion-de-turnos` (crear), que deciden todas las reglas; la pantalla solo exige que estén los campos obligatorios y muestra cada rechazo con su código RN, sin el `detail` de la API. Fechas y horas se escriben y se muestran en **hora del consultorio** (`America/Argentina/Buenos_Aires`, UTC−3, la `zona_horaria` que devuelve `GET /turnos`); entre paréntesis, el valor en UTC que viaja por la API. El servidor falso considera «hoy» el `2026-11-02` (lunes) salvo que el escenario diga otra cosa. «Con sesión de X» significa que X inició sesión en el panel (`ingreso-al-panel`). Datos de partida, todos ficticios (RN-PR-01): los pacientes 1 «Ana Ejemplo», 2 «Bruno Ficticio» y 3 «Carla Inventada»; las prestaciones activas 1 «Consulta / control» (30 min, `#1E88E5`), 2 «Limpieza» (45 min, `#43A047`) y 3 «Obturación» (60 min, `#FB8C00`), y la inactiva 5 «Urgencia»; «la odontóloga», «la recepcionista» y «el dueño» (solo `dueno`). La pantalla no conoce el rol de quien inició sesión (D249, D312): «Nuevo turno» se ve para todos y la API decide. La disposición viene de las pantallas de Stitch citadas en el design (D234); lo puramente visual no tiene escenario. Los textos fijos y las elecciones de la pantalla son decisiones del autor (D319, D320, D323 y D324; 2026-10-28). Cada escenario tiene un ID propio (`AGE-4a`…) que lleva el nombre de su test. Los escenarios se verifican en la suite del frontend (`npm test`) y se repiten en la prueba en el navegador, salvo los que dicen que solo se verifican contra el servidor falso.

## Requirements

### Requirement: La agenda muestra los turnos del día

La ruta `/panel/agenda`, a la que se llega desde el enlace «Agenda» de la barra del panel, SHALL pedir `GET /turnos` sin `fecha` al abrirse y mostrar el día que devuelve la API, con su nombre («lunes 2 de noviembre de 2026»), y una fila por turno en el orden de la respuesta, con la hora de inicio y de fin en hora del consultorio («09:00 – 09:30»), el paciente («Ana Ejemplo»), la prestación con una marca de su color y el estado con su etiqueta (US-011 CA-1). Sin turnos SHALL mostrar «No hay turnos para este día.». Mientras llega el día SHALL mostrar «Cargando agenda…»; sin conexión o con un `5xx`, el mensaje de conexión con «Reintentar»; y con un `403` `RN-AU-05`, «Tu usuario no tiene permiso para ver la agenda (RN-AU-05).», sin tabla y sin «Reintentar» (D323).

#### Scenario: AGE-4a Feliz - la odontóloga ve la agenda de hoy

- **GIVEN** con sesión de la odontóloga, y en el servidor falso, el 2 de noviembre, el turno de Ana Ejemplo con «Consulta / control» de 09:00 a 09:30 (`12:00Z` a `12:30Z`), `reservado`; el de Bruno Ficticio con «Limpieza» de 10:00 a 10:45 (`13:00Z` a `13:45Z`), `reservado`; y el de Carla Inventada con «Obturación» de 11:00 a 12:00 (`14:00Z` a `15:00Z`), `confirmado`
- **WHEN** pulsa «Agenda» en la barra del panel
- **THEN** ve «lunes 2 de noviembre de 2026» y tres filas en este orden: «09:00 – 09:30», «Ana Ejemplo», «Consulta / control», «Reservado»; «10:00 – 10:45», «Bruno Ficticio», «Limpieza», «Reservado»; «11:00 – 12:00», «Carla Inventada», «Obturación», «Confirmado»
- **AND** la marca de color de cada fila es la de su prestación (`#1E88E5`, `#43A047` y `#FB8C00`)
- **AND** se hizo una sola petición `GET /turnos`, sin `fecha`

#### Scenario: AGE-4b Borde - cambiar de día y volver a hoy

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, y en el servidor falso ningún turno el 3 de noviembre
- **WHEN** pulsa «Día siguiente»; después «Día anterior» dos veces; después elige el 10 de noviembre en el selector de fecha; y por último pulsa «Hoy»
- **THEN** primero se pide `GET /turnos?fecha=2026-11-03` y se ve «martes 3 de noviembre de 2026» con «No hay turnos para este día.»
- **AND** después se piden `fecha=2026-11-02` y `fecha=2026-11-01`, luego `fecha=2026-11-10`, y con «Hoy» un `GET /turnos` sin `fecha`, que vuelve a mostrar el 2 de noviembre con sus turnos

#### Scenario: AGE-4c Borde - cada estado se ve con su etiqueta

- **GIVEN** con sesión del dueño, y en el servidor falso un turno del 2 de noviembre en cada uno de los nueve estados del turno
- **WHEN** abre `/panel/agenda`
- **THEN** ve las etiquetas «Pendiente de aprobación», «Pendiente de seña», «Reservado», «Confirmado», «Cancelado por el paciente», «Cancelado por el consultorio», «Vencido», «Atendido» y «Ausente», una por fila
- **AND** este escenario solo se verifica contra el servidor falso (la API real solo crea turnos `reservado` hasta C-16 a C-19)

#### Scenario: AGE-4d Borde - mientras carga, sin conexión y sin permiso

- **GIVEN** con sesión de la odontóloga
- **WHEN** abre `/panel/agenda` con la respuesta todavía pendiente, y después la API no responde; y, en otra corrida, abre `/panel/agenda` con un usuario sin roles
- **THEN** primero se ve «Cargando agenda…» sin filas
- **AND** después se ve «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» con «Reintentar», que al responder la API muestra el día
- **AND** con el usuario sin roles, la API responde `403` con `codigos` `["RN-AU-05"]` y se ve «Tu usuario no tiene permiso para ver la agenda (RN-AU-05).», sin tabla, sin «Reintentar» y sin pedir `POST /auth/refresh`
- **AND** el caso sin roles solo se verifica contra el servidor falso

### Requirement: Crear un turno desde la agenda

«Nuevo turno» SHALL abrir un panel con «N.º de paciente», «Prestación» (solo las activas de `GET /prestaciones`, con su duración), «Fecha» (el día mostrado, editable) y «Hora», y con «Crear turno» mandar un único `POST /turnos` con `paciente_id`, `prestacion_id` e `inicio` en UTC, sin profesional ni sillón (RN-AG-14). Con el `201` SHALL mostrar «Turno creado.», cerrar el panel y mostrar la agenda del día del turno (US-011 CA-2, D110). Con un campo vacío SHALL mostrar «Completá paciente, prestación, fecha y hora.» sin mandar nada; mientras espera, «Crear turno» SHALL estar deshabilitado.

#### Scenario: AGE-5a Feliz - la recepcionista da un turno y lo ve en la agenda

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre con el turno de Ana Ejemplo de 09:00 a 09:30
- **WHEN** pulsa «Nuevo turno», escribe el paciente «2», elige «Limpieza · 45 min», deja la fecha «02/11/2026», escribe la hora «10:00» y pulsa «Crear turno»
- **THEN** antes de enviar, el panel muestra «Termina a las 10:45.»
- **AND** se manda un solo `POST /turnos` con exactamente `{"paciente_id": 2, "prestacion_id": 2, "inicio": "2026-11-02T13:00:00Z"}`
- **AND** se ve «Turno creado.», el panel se cierra, se pide `GET /turnos?fecha=2026-11-02` y la agenda muestra «10:00 – 10:45», «Bruno Ficticio», «Limpieza», «Reservado» después del turno de Ana Ejemplo
- **AND** el selector «Prestación» no ofrece «Urgencia», que está inactiva

#### Scenario: AGE-5b Borde - campos vacíos, cancelar y doble clic

- **GIVEN** con sesión de la odontóloga, con el panel «Nuevo turno» abierto
- **WHEN** pulsa «Crear turno» sin paciente; después completa todo y pulsa «Cancelar»; después lo abre, completa todo con el servidor falso reteniendo la respuesta del `POST /turnos` y pulsa «Crear turno» dos veces
- **THEN** la primera vez se ve «Completá paciente, prestación, fecha y hora.» y no se manda ningún `POST`
- **AND** «Cancelar» cierra el panel sin mandar nada
- **AND** mientras la respuesta está retenida «Crear turno» está deshabilitado y el servidor falso recibió un solo `POST`; al liberarla se ve «Turno creado.»
- **AND** el doble clic solo se verifica contra el servidor falso

#### Scenario: AGE-5h Borde - un turno en otro día que cruza la medianoche UTC

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, y en el servidor falso ningún turno el 3 de noviembre
- **WHEN** pulsa «Nuevo turno», escribe el paciente «2», elige «Limpieza · 45 min», cambia la fecha a «03/11/2026», escribe la hora «22:00» y pulsa «Crear turno»
- **THEN** antes de enviar, el panel muestra «Termina a las 22:45.»
- **AND** se manda un solo `POST /turnos` con exactamente `{"paciente_id": 2, "prestacion_id": 2, "inicio": "2026-11-04T01:00:00Z"}`
- **AND** se ve «Turno creado.», el panel se cierra, se pide `GET /turnos?fecha=2026-11-03` (la fecha del consultorio, no la de UTC) y se ve «martes 3 de noviembre de 2026» con «22:00 – 22:45», «Bruno Ficticio», «Limpieza», «Reservado»
- **AND** este escenario solo se verifica contra el servidor falso (en la demo, las 22:00 están fuera del horario del profesional y la API responde `RN-AG-04`)

### Requirement: Los rechazos al crear un turno se ven con su código

Cada rechazo de `POST /turnos` SHALL verse en el panel con un texto fijo y su código RN, conservando lo cargado y sin «Turno creado.»: el doble conflicto (E4) con los dos códigos juntos, `RN-GL-04` (E12) con cada referencia que falló, y `RN-AG-05`, `RN-AG-08`, `RN-AG-04`, `RN-AG-04b`, `RN-AG-10d` y `RN-AU-05` con el suyo (US-011 CA-2: «los errores de dominio son los de US-010»). La pantalla MUST NOT evaluar ninguna de esas reglas por su cuenta.

#### Scenario: AGE-5c Error de negocio - E4 muestra los dos códigos

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre con el turno activo de Ana Ejemplo de 09:00 a 09:30 del profesional 1 y el sillón 1 (los únicos activos)
- **WHEN** da un turno al paciente «2» con «Consulta / control» el «02/11/2026» a las «09:00» (`2026-11-02T12:00:00Z`)
- **THEN** la API responde `409` con `codigos` `["RN-AG-05", "RN-AG-08"]` y el panel muestra «El profesional y el sillón ya tienen un turno activo en ese horario (RN-AG-05, RN-AG-08).»
- **AND** el panel sigue abierto con lo cargado, no se ve «Turno creado.» y la agenda sigue con un solo turno

#### Scenario: AGE-5d Error de entrada - E12 muestra RN-GL-04 con las referencias

- **GIVEN** con sesión de la odontóloga, con el panel «Nuevo turno» abierto, y el servidor falso, que desactiva «Limpieza» después de mandar la lista de prestaciones
- **WHEN** da un turno al paciente «99» con «Limpieza» el «02/11/2026» a las «10:00»
- **THEN** la API responde `422` con `codigos` `["RN-GL-04"]` y las referencias del paciente 99 (`inexistente`) y de la prestación 2 (`inactivo`)
- **AND** el panel muestra «Hay datos que no existen o no están activos: paciente 99 (no existe), prestación 2 (inactiva) (RN-GL-04).», conserva lo cargado y vuelve a pedir `GET /prestaciones`, que ya no ofrece «Limpieza»
- **AND** el paso que desactiva «Limpieza» solo se verifica contra el servidor falso; en el navegador se prueba con el paciente 99

#### Scenario: AGE-5e Error de negocio - las demás reglas de US-010 con su texto

- **GIVEN** con sesión de la odontóloga, con el panel «Nuevo turno» completo, y el servidor falso respondiendo cada vez uno de estos rechazos de `POST /turnos`
- **WHEN** pulsa «Crear turno» una vez por rechazo
- **THEN** `409` `["RN-AG-05"]` muestra «El profesional ya tiene un turno activo en ese horario (RN-AG-05).»; `409` `["RN-AG-08"]`, «El sillón ya tiene un turno activo en ese horario (RN-AG-08).»; `422` `["RN-AG-04"]`, «El turno no cae dentro del horario de atención del profesional (RN-AG-04).»; `422` `["RN-AG-04b"]`, «Ese horario está bloqueado (RN-AG-04b).»; `422` `["RN-AG-10d"]`, «El turno no puede pasar de la medianoche del consultorio (RN-AG-10d).»; y un `422` sin código, «Revisá los datos del turno.»
- **AND** cada vez el panel conserva lo cargado y no se ve «Turno creado.»
- **AND** este escenario se verifica contra el servidor falso; en el navegador se repiten `RN-AG-04` (un sábado) y `RN-AG-04b` (sobre un bloqueo de la demo)

#### Scenario: AGE-5f Error de negocio - el dueño no puede crear turnos

- **GIVEN** con sesión del dueño, con el panel «Nuevo turno» completo
- **WHEN** pulsa «Crear turno»
- **THEN** la API responde `403` con `codigos` `["RN-AU-05"]` y el panel muestra «Tu usuario no tiene permiso para crear turnos (RN-AU-05).»
- **AND** no se pidió `POST /auth/refresh`, el dueño sigue en la agenda y no se creó ningún turno

#### Scenario: AGE-5g Borde - sin conexión al crear se conserva lo cargado

- **GIVEN** con sesión de la odontóloga, con el panel «Nuevo turno» completo
- **WHEN** pulsa «Crear turno» y la API no responde
- **THEN** se ve el mensaje de conexión sin «Reintentar» y no se ve «Turno creado.»
- **AND** el panel conserva lo cargado y «Crear turno» vuelve a estar habilitado
- **AND** este escenario solo se verifica contra el servidor falso

### Requirement: La sesión que termina en la agenda vuelve al inicio de sesión

Si el access token venció y el refresh sigue vigente, la interfaz SHALL renovarlo una vez y repetir la petición sin aviso (`ingreso-al-panel`). Si la sesión no se puede renovar mientras se usa la agenda (al cargar o cambiar de día, o al crear un turno), la interfaz SHALL volver a `/ingresar` con «Tu sesión terminó. Iniciá sesión de nuevo.» y MUST NOT mostrar el mensaje de conexión ni dejar un turno a medio crear (US-092 CA-1; cableado de C-11, D231; D323).

#### Scenario: AGE-6a Borde - la sesión al cargar el día y al crear un turno

- **GIVEN** con sesión de la odontóloga
- **WHEN** abre `/panel/agenda` con el access token vencido y el refresh vigente; en otra corrida, abre `/panel/agenda` con la sesión que ya no se puede renovar; y en otra, con el panel «Nuevo turno» completo y la sesión que ya no se puede renovar, pulsa «Crear turno»
- **THEN** en la primera se pide `POST /auth/refresh` una sola vez, se repite `GET /turnos` y se ve el día, sin aviso
- **AND** en la segunda y en la tercera la interfaz vuelve a `/ingresar` con el aviso de sesión terminada, sin el mensaje de conexión
- **AND** en la tercera no se creó ningún turno
