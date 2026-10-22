## Purpose

Define cómo el panel muestra y edita desde el navegador el horario recurrente semanal de un profesional: la semana por días, elegir el profesional, agregar y quitar franjas, guardar, cómo se ven los rechazos de la API con su código y qué pasa si la sesión termina en la pantalla (US-002, US-092 CA-1).

Convenciones de los escenarios: la API es la de `horario-recurrente`, que decide todas las reglas; la pantalla no valida superposiciones ni el orden de las horas, solo que cada franja tenga sus dos horas, y muestra cada rechazo con su código RN. Las horas son del consultorio, en `HH:MM`. «Con sesión de X» significa que X inició sesión en el panel (capability `ingreso-al-panel`). Los datos de partida de la suite son ficticios: el profesional 1 «Dra. Demo Ficticia», activo, con lunes a viernes 09:00-13:00 y 15:00-19:00; «la odontóloga» (`odontologo`), «la recepcionista» (`recepcionista`) y «el dueño» (`dueno`). La pantalla no conoce el rol de quien inició sesión (D249): las acciones se ven para todos y la API decide. La disposición viene de la pantalla de Stitch (D234); lo puramente visual no tiene escenario. Tipos de escenario en el título: los de `horario-recurrente` (Feliz, Error de negocio, Borde, Error de formato y **Error de entrada**, el `422` de validación de entrada con código RN, acá `RN-AG-16`). Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite del frontend (`npm test`) y se repiten en la prueba en el navegador, salvo los que dicen que solo se verifican contra el servidor falso.

## ADDED Requirements

### Requirement: La pantalla muestra la semana del profesional

La ruta `/panel/horario`, a la que se llega desde el enlace «Horario» de la barra del panel, SHALL mostrar la zona del consultorio, la nota de RN-AG-04, el selector «Profesional» con los profesionales de `GET /profesionales` (D260; elegido el primero activo o, si ninguno está activo, el primero de la lista, con «(inactivo)» en el nombre; D267) y siete filas, de «Lunes» a «Domingo», con las franjas en orden («Desde» y «Hasta») o «Sin atención». Mientras carga SHALL mostrar «Cargando horario…» y sin conexión, el mensaje de conexión con «Reintentar».

#### Scenario: US-002 CA-1 Feliz - la odontóloga ve la semana de la demo

- **GIVEN** con sesión de la odontóloga
- **WHEN** pulsa «Horario» en la barra del panel
- **THEN** el selector muestra «Dra. Demo Ficticia», las filas de lunes a viernes muestran 09:00 a 13:00 y 15:00 a 19:00, y sábado y domingo dicen «Sin atención»
- **AND** el subtítulo dice «Franjas semanales en hora del consultorio (America/Argentina/Buenos_Aires).» con la `zona_horaria` de la API, y la nota dice «Los turnos solo se pueden crear dentro de una franja (RN-AG-04). Cambiar el horario no modifica los turnos ya dados.»
- **AND** se hizo una sola petición `GET /profesionales` y una sola `GET /profesionales/1/horario`

#### Scenario: US-002 CA-1 Borde - mientras carga y sin conexión

- **GIVEN** con sesión de la odontóloga
- **WHEN** abre `/panel/horario` con la respuesta todavía pendiente, y después la API no responde
- **THEN** primero se ve «Cargando horario…» sin filas
- **AND** después se ve «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» con «Reintentar», que al responder la API muestra la semana

#### Scenario: US-002 CA-1 Borde - la recepcionista y el dueño ven la semana

- **GIVEN** con sesión de la recepcionista, y después del dueño
- **WHEN** abre `/panel/horario`
- **THEN** ve la misma semana que la odontóloga

#### Scenario: US-002 CA-1 Borde - elegir otro profesional muestra su horario

- **GIVEN** con sesión de la odontóloga, y en el servidor falso un profesional 2 inactivo «Dr. Ejemplo Ficticio» sin franjas
- **WHEN** elige «Dr. Ejemplo Ficticio (inactivo)» en el selector
- **THEN** se pide `GET /profesionales/2/horario` y los siete días dicen «Sin atención»
- **AND** lo que se había editado sin guardar del profesional 1 se descarta
- **AND** este escenario solo se verifica contra el servidor falso (la demo tiene un solo profesional)

#### Scenario: US-002 CA-1 Borde - sin profesionales activos se elige el primero de la lista

- **GIVEN** con sesión de la odontóloga, y en el servidor falso el profesional 1 marcado inactivo y el profesional 2 inactivo «Dr. Ejemplo Ficticio»
- **WHEN** abre `/panel/horario`
- **THEN** el selector muestra «Dra. Demo Ficticia (inactivo)» y se pide `GET /profesionales/1/horario`, con su semana
- **AND** este escenario solo se verifica contra el servidor falso (la API no tiene cómo desactivar al único profesional de la demo, D46)

### Requirement: Editar y guardar el horario

Cada día SHALL tener «Agregar franja», que suma una franja con «Desde» y «Hasta» vacíos, y cada franja, «Quitar». «Guardar horario» SHALL mandar un único `PUT /profesionales/{id}/horario` con todas las franjas de la semana ordenadas por día y hora, mostrar «Horario guardado.» y la semana que devuelve la API. Mientras espera la respuesta, «Guardar horario» SHALL estar deshabilitado, así que un segundo clic MUST NOT mandar otro `PUT`. Sin cambios, «Guardar horario» MUST NOT mandar nada; con una franja sin sus dos horas SHALL mostrar «Completá las dos horas de la franja.» sin mandar nada. Si la API no responde al guardar, SHALL mostrar el mensaje de conexión sin «Reintentar» (D269), conservar lo editado, no mostrar «Horario guardado.» y volver a habilitar «Guardar horario».

#### Scenario: US-002 CA-1 Feliz - agregar la mañana del sábado y guardar

- **GIVEN** con sesión de la odontóloga, en la semana de la demo
- **WHEN** pulsa «Agregar franja» en el sábado, escribe 09:00 y 12:00 y pulsa «Guardar horario»
- **THEN** se manda un solo `PUT /profesionales/1/horario` con las once franjas: las diez de lunes a viernes y sábado 09:00-12:00, en orden
- **AND** se ve «Horario guardado.» y el sábado muestra 09:00 a 12:00

#### Scenario: US-002 CA-1 Borde - quitar la tarde del viernes y guardar

- **GIVEN** con sesión de la odontóloga, en la semana de la demo
- **WHEN** pulsa «Quitar» en la franja 15:00 a 19:00 del viernes y pulsa «Guardar horario»
- **THEN** el `PUT` lleva nueve franjas, sin viernes 15:00-19:00, y el viernes muestra solo 09:00 a 13:00

#### Scenario: US-002 CA-1 Borde - guardar sin cambios o con una franja incompleta no manda nada

- **GIVEN** con sesión de la odontóloga, en la semana de la demo
- **WHEN** pulsa «Guardar horario» sin cambiar nada; y después agrega una franja al domingo, escribe solo «Desde» 10:00 y pulsa «Guardar horario»
- **THEN** no se manda ningún `PUT`
- **AND** la franja del domingo muestra «Completá las dos horas de la franja.»

#### Scenario: US-002 CA-1 Borde - guardar dos veces seguidas manda un solo pedido

- **GIVEN** con sesión de la odontóloga, en la semana de la demo, con una franja agregada al sábado 09:00 a 12:00 y el servidor falso reteniendo la respuesta del `PUT`
- **WHEN** pulsa «Guardar horario» dos veces
- **THEN** mientras la respuesta está retenida «Guardar horario» está deshabilitado y el servidor falso recibió un solo `PUT`
- **AND** al liberar la respuesta se ve «Horario guardado.»
- **AND** este escenario solo se verifica contra el servidor falso

#### Scenario: US-002 CA-1 Borde - sin conexión al guardar se conserva lo editado

- **GIVEN** con sesión de la odontóloga, en la semana de la demo, con una franja agregada al sábado 09:00 a 12:00
- **WHEN** pulsa «Guardar horario» y la API no responde
- **THEN** se ve «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» sin «Reintentar» y no se ve «Horario guardado.»
- **AND** el sábado sigue mostrando 09:00 a 12:00 y «Guardar horario» vuelve a estar habilitado
- **AND** este escenario solo se verifica contra el servidor falso

### Requirement: Los rechazos del horario se ven con su código

Si la API rechaza el `PUT` con `422` `RN-AG-16`, la pantalla SHALL marcar cada franja informada como inválida, mostrar una vez debajo de las franjas de cada día afectado «Hay franjas que se superponen o no terminan después de empezar (RN-AG-16).», conservar lo editado y no mostrar «Horario guardado.». Un `403` `RN-AU-05` SHALL mostrar «Tu usuario no tiene permiso para modificar el horario (RN-AU-05).» sin cerrar la sesión. Un `404` `RN-GL-04` SHALL mostrar «El profesional ya no existe (RN-GL-04).» y volver a pedir la lista de profesionales. Un `422` sin código (formato) SHALL mostrar «Revisá las franjas del horario.» y conservar lo editado. La pantalla no muestra el `detail` ni el `mensaje` de la API.

#### Scenario: HOR-1 Error de entrada - dos franjas superpuestas del miércoles

- **GIVEN** con sesión de la odontóloga, en la semana de la demo
- **WHEN** agrega al miércoles la franja 12:00 a 16:00 y pulsa «Guardar horario»
- **THEN** la API responde `422` `RN-AG-16`; las franjas 12:00 a 16:00 y 15:00 a 19:00 del miércoles (las que la API informa, como en la cadena de tres franjas de `horario-recurrente`: cada una se superpone con una anterior no invertida del mismo día, D266) quedan marcadas como inválidas, 09:00 a 13:00 no, y debajo de las franjas del miércoles se ve una sola vez el mensaje de `RN-AG-16`
- **AND** el miércoles sigue mostrando las tres franjas editadas y no se ve «Horario guardado.»

#### Scenario: HOR-1 Borde - una franja invertida se marca con el mensaje de RN-AG-16

- **GIVEN** con sesión de la odontóloga, en la semana de la demo
- **WHEN** agrega al sábado la franja 12:00 a 09:00 y pulsa «Guardar horario»
- **THEN** la pantalla manda el `PUT` sin validar el orden de las horas, la API responde `422` `RN-AG-16`, la franja del sábado queda marcada como inválida y debajo de ella se ve una vez «Hay franjas que se superponen o no terminan después de empezar (RN-AG-16).»
- **AND** ninguna franja de lunes a viernes queda marcada y no se ve «Horario guardado.»

#### Scenario: US-002 CA-1 Borde - un rechazo de formato sin código

- **GIVEN** con sesión de la odontóloga, en la semana de la demo (diez franjas)
- **WHEN** agrega 61 franjas válidas sin superposiciones (71 en total, más que el tope de 70) y pulsa «Guardar horario»
- **THEN** la API responde `422` con `codigos` vacío y se ve «Revisá las franjas del horario.»
- **AND** lo editado se conserva y no se ve «Horario guardado.»
- **AND** este escenario solo se verifica contra el servidor falso

#### Scenario: US-002 CA-1 Error de negocio - la recepcionista intenta guardar

- **GIVEN** con sesión de la recepcionista, en la semana de la demo
- **WHEN** agrega al sábado 09:00 a 12:00 y pulsa «Guardar horario»
- **THEN** se ve «Tu usuario no tiene permiso para modificar el horario (RN-AU-05).»
- **AND** no se pidió `POST /auth/refresh`, la recepcionista sigue en el panel y un `GET` posterior del horario no tiene la franja del sábado

#### Scenario: US-002 CA-1 Borde - un profesional que ya no existe

- **GIVEN** con sesión de la odontóloga, en la semana del profesional 1, que el servidor falso quita antes de guardar
- **WHEN** cambia una franja y pulsa «Guardar horario»
- **THEN** se ve «El profesional ya no existe (RN-GL-04).» y se vuelve a pedir `GET /profesionales`
- **AND** este escenario solo se verifica contra el servidor falso (la API real no borra profesionales)

### Requirement: La sesión que termina en la pantalla vuelve al inicio de sesión

Si la sesión no se puede renovar mientras se usa la pantalla, la interfaz SHALL volver a `/ingresar` con «Tu sesión terminó. Iniciá sesión de nuevo.» y MUST NOT mostrar el mensaje de conexión ni dejar nada a medio guardar (US-092 CA-1; cableado de C-11, D231).

#### Scenario: US-092 CA-1 Borde - una sesión irrenovable al guardar el horario

- **GIVEN** con sesión de la odontóloga, una franja agregada al sábado y la sesión que ya no se puede renovar
- **WHEN** pulsa «Guardar horario»
- **THEN** la interfaz vuelve a `/ingresar` con el aviso de sesión terminada
- **AND** el horario del profesional 1 no cambió
