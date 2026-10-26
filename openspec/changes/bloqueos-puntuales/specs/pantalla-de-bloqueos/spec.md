## Purpose

Define cómo el panel muestra, crea y elimina desde el navegador los bloqueos puntuales del consultorio: la lista con su alcance y sus horas, el alta con los turnos activos afectados, cómo se ven los rechazos de la API con su código y qué pasa si la sesión termina en la pantalla (US-003, US-092 CA-1).

Convenciones de los escenarios: la API es la de `bloqueos-puntuales`, que decide todas las reglas; la pantalla no valida el orden de las fechas, solo que estén los campos obligatorios, y muestra cada rechazo con su código RN. Las fechas y horas se escriben y se muestran en **hora del consultorio** (`America/Argentina/Buenos_Aires`, UTC−3, la `zona_horaria` que devuelve `GET /bloqueos`), con el formato `dd/mm/aaaa hh:mm`; la API recibe y devuelve UTC (entre paréntesis, el valor en UTC). «Con sesión de X» significa que X inició sesión en el panel (capability `ingreso-al-panel`). Los datos de partida de la suite son ficticios: el profesional 1 «Dra. Demo Ficticia» y el «Sillón 1», activos, sin bloqueos salvo que el escenario diga otra cosa; «la odontóloga» (`odontologo`), «la recepcionista» (`recepcionista`) y «el dueño» (`dueno`). La pantalla no conoce el rol de quien inició sesión (D249): las acciones se ven para todos y la API decide. Las elecciones de la pantalla son decisiones del autor del 2026-10-26 (hora del consultorio, D285; detalles, D286). La disposición viene de la pantalla de Stitch (D234 y D288, **pendiente**: se consigue antes de aprobar el plan); lo puramente visual no tiene escenario. Los textos fijos son Propuesta del design (B17). Tipos de escenario en el título: los de `bloqueos-puntuales`. Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite del frontend (`npm test`) y se repiten en la prueba en el navegador, salvo los que dicen que solo se verifican contra el servidor falso.

## ADDED Requirements

### Requirement: La pantalla lista los bloqueos

La ruta `/panel/bloqueos`, a la que se llega desde el enlace «Bloqueos» de la barra del panel, SHALL mostrar los bloqueos de `GET /bloqueos` en su orden, cada uno con su alcance («Todo el consultorio», «Profesional: <nombre>» o «Sillón: <nombre>», con los nombres de `GET /profesionales` y `GET /sillones`), «Desde», «Hasta» en hora del consultorio y el motivo, o «No hay bloqueos cargados.». Mientras carga SHALL mostrar «Cargando bloqueos…» y sin conexión, el mensaje de conexión con «Reintentar».

#### Scenario: US-003 CA-1 Feliz - la odontóloga ve los bloqueos

- **GIVEN** con sesión de la odontóloga, y en el servidor falso un bloqueo del profesional 1 del `2026-11-09T03:00:00Z` al `2026-11-14T03:00:00Z` con motivo «Vacaciones» y uno de todo el consultorio del `2026-11-23T03:00:00Z` al `2026-11-24T03:00:00Z` con motivo «Feriado»
- **WHEN** pulsa «Bloqueos» en la barra del panel
- **THEN** ve dos filas en este orden: «Profesional: Dra. Demo Ficticia», desde «09/11/2026 00:00» hasta «14/11/2026 00:00», «Vacaciones»; y «Todo el consultorio», desde «23/11/2026 00:00» hasta «24/11/2026 00:00», «Feriado»
- **AND** se hizo una sola petición `GET /bloqueos`, una sola `GET /profesionales` y una sola `GET /sillones`

#### Scenario: US-003 CA-1 Borde - sin bloqueos, y la recepcionista y el dueño ven la lista

- **GIVEN** sin bloqueos, con sesión de la recepcionista y después del dueño
- **WHEN** abre `/panel/bloqueos`
- **THEN** ve «No hay bloqueos cargados.» y el formulario del alta

#### Scenario: US-003 CA-1 Borde - mientras carga y sin conexión

- **GIVEN** con sesión de la odontóloga
- **WHEN** abre `/panel/bloqueos` con la respuesta todavía pendiente, y después la API no responde
- **THEN** primero se ve «Cargando bloqueos…» sin filas
- **AND** después se ve «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» con «Reintentar», que al responder la API muestra la lista

### Requirement: Crear un bloqueo y ver los turnos afectados

El alta SHALL pedir «Alcance» («Todo el consultorio», «Un profesional» o «Un sillón», con un segundo selector que ofrece solo los profesionales o sillones activos, D286), «Desde», «Hasta» y «Motivo», y con «Bloquear» mandar un único `POST /bloqueos` con las fechas convertidas a UTC. Con el `201` SHALL mostrar «Bloqueo creado.», sumar el bloqueo a la lista y mostrar los turnos afectados de la respuesta, avisando que no se cancelaron (US-003 CA-2, D83). Con un campo obligatorio vacío SHALL mostrar «Completá alcance, desde, hasta y motivo.» sin mandar nada; mientras espera, «Bloquear» SHALL estar deshabilitado y un segundo clic MUST NOT mandar otro `POST` (D286).

#### Scenario: US-003 CA-1 Feliz - bloquear todo el consultorio por un feriado

- **GIVEN** con sesión de la odontóloga, sin bloqueos
- **WHEN** elige «Todo el consultorio», escribe desde «23/11/2026 00:00», hasta «24/11/2026 00:00» y motivo «Feriado», y pulsa «Bloquear»
- **THEN** se manda un solo `POST /bloqueos` con `inicio` `2026-11-23T03:00:00Z`, `fin` `2026-11-24T03:00:00Z`, `motivo` «Feriado» y sin `profesional_id` ni `sillon_id`
- **AND** se ve «Bloqueo creado. No hay turnos activos en ese horario.» y la lista muestra el bloqueo

#### Scenario: US-003 CA-2 Feliz - bloquear al profesional sobre dos turnos activos los muestra sin cancelarlos

- **GIVEN** con sesión de la odontóloga, y en el servidor falso dos turnos activos del profesional 1: el 7 `reservado` del `2026-11-02T13:00:00Z` al `13:30:00Z` y el 8 `confirmado` del `2026-11-02T14:00:00Z` al `14:30:00Z`
- **WHEN** elige «Un profesional» y «Dra. Demo Ficticia», escribe desde «02/11/2026 09:00», hasta «02/11/2026 13:00» y motivo «Ausencia», y pulsa «Bloquear»
- **THEN** se ve «Bloqueo creado. Hay 2 turnos activos en ese horario: no se cancelaron, hay que reprogramarlos o cancelarlos.»
- **AND** debajo, dos filas: «Turno 7 · 02/11/2026 10:00 a 10:30 · reservado» y «Turno 8 · 02/11/2026 11:00 a 11:30 · confirmado»

#### Scenario: US-003 CA-1 Borde - con un campo obligatorio vacío no se manda nada

- **GIVEN** con sesión de la odontóloga
- **WHEN** elige «Un sillón» sin elegir el sillón, completa desde, hasta y motivo y pulsa «Bloquear»; y después elige «Sillón 1», borra el motivo y pulsa «Bloquear»
- **THEN** no se manda ningún `POST` y cada vez se ve «Completá alcance, desde, hasta y motivo.»

#### Scenario: US-003 CA-1 Borde - sin conexión al crear se conserva lo cargado

- **GIVEN** con sesión de la odontóloga, con el formulario completo para todo el consultorio
- **WHEN** pulsa «Bloquear» y la API no responde
- **THEN** se ve el mensaje de conexión sin «Reintentar» y no se ve «Bloqueo creado.»
- **AND** el formulario conserva lo cargado y «Bloquear» vuelve a estar habilitado
- **AND** este escenario solo se verifica contra el servidor falso

#### Scenario: US-003 CA-1 Borde - pulsar «Bloquear» dos veces manda un solo pedido

- **GIVEN** con sesión de la odontóloga, con el formulario completo para todo el consultorio y el servidor falso reteniendo la respuesta del `POST /bloqueos`
- **WHEN** pulsa «Bloquear» dos veces
- **THEN** mientras la respuesta está retenida «Bloquear» está deshabilitado y el servidor falso recibió un solo `POST`
- **AND** al liberar la respuesta se ve «Bloqueo creado. No hay turnos activos en ese horario.»
- **AND** este escenario solo se verifica contra el servidor falso

#### Scenario: US-003 CA-1 Borde - el selector de recurso ofrece solo los activos

- **GIVEN** con sesión de la odontóloga, y en el servidor falso, además de los datos de partida, un profesional inactivo «Dr. Inactivo Ficticio» y un sillón inactivo «Sillón 2»
- **WHEN** elige «Un profesional» y después «Un sillón»
- **THEN** el segundo selector ofrece solo «Dra. Demo Ficticia» y, después, solo «Sillón 1»
- **AND** este escenario solo se verifica contra el servidor falso (la demo no tiene recursos inactivos)

### Requirement: Eliminar un bloqueo

Cada bloqueo de la lista SHALL tener «Eliminar» (nombre accesible «Eliminar bloqueo»), que manda un único `DELETE /bloqueos/{id}` sin pedir confirmación (D286) y, con el `204`, quita el bloqueo de la lista y muestra «Bloqueo eliminado.». Mientras espera, ese «Eliminar» SHALL estar deshabilitado y un segundo clic MUST NOT mandar otro `DELETE`. Si la API no responde, SHALL mostrar el mensaje de conexión sin «Reintentar», sin «Bloqueo eliminado.», con el bloqueo todavía en la lista y «Eliminar» habilitado de nuevo.

#### Scenario: US-003 CA-1 Feliz - la odontóloga elimina un bloqueo

- **GIVEN** con sesión de la odontóloga, y en el servidor falso el bloqueo «Feriado» de todo el consultorio
- **WHEN** pulsa «Eliminar» en ese bloqueo
- **THEN** se manda un solo `DELETE /bloqueos/<id>`, se ve «Bloqueo eliminado.» y la lista dice «No hay bloqueos cargados.»

#### Scenario: US-003 CA-1 Borde - pulsar «Eliminar» dos veces manda un solo pedido

- **GIVEN** con sesión de la odontóloga, en el servidor falso el bloqueo «Feriado» y la respuesta del `DELETE` retenida
- **WHEN** pulsa «Eliminar» en ese bloqueo dos veces
- **THEN** mientras la respuesta está retenida ese «Eliminar» está deshabilitado y el servidor falso recibió un solo `DELETE`
- **AND** al liberar la respuesta se ve «Bloqueo eliminado.», no «El bloqueo ya no existe (RN-GL-04).»
- **AND** este escenario solo se verifica contra el servidor falso

#### Scenario: US-003 CA-1 Borde - sin conexión al eliminar el bloqueo sigue en la lista

- **GIVEN** con sesión de la odontóloga, y en el servidor falso el bloqueo «Feriado»
- **WHEN** pulsa «Eliminar» en ese bloqueo y la API no responde
- **THEN** se ve el mensaje de conexión sin «Reintentar» y no se ve «Bloqueo eliminado.»
- **AND** el bloqueo «Feriado» sigue en la lista y su «Eliminar» vuelve a estar habilitado
- **AND** este escenario solo se verifica contra el servidor falso

### Requirement: Los rechazos de los bloqueos se ven con su código

Un `422` `RN-AG-17` SHALL mostrar «El bloqueo tiene que terminar después de empezar (RN-AG-17).» y conservar lo cargado. Un `422` `RN-GL-04` al crear SHALL mostrar «El profesional o el sillón elegido ya no está disponible (RN-GL-04).» y volver a pedir los profesionales y los sillones. Un `403` `RN-AU-05` SHALL mostrar «Tu usuario no tiene permiso para modificar los bloqueos (RN-AU-05).» sin cerrar la sesión. Un `404` al eliminar SHALL mostrar «El bloqueo ya no existe (RN-GL-04).» y volver a pedir la lista. Un `422` sin código, «Revisá los datos del bloqueo.». La pantalla no muestra el `detail` ni el `mensaje` de la API.

#### Scenario: US-003 CA-1 Error de entrada - hasta antes que desde se manda y vuelve con RN-AG-17

- **GIVEN** con sesión de la odontóloga
- **WHEN** elige «Todo el consultorio», escribe desde «02/11/2026 15:00», hasta «02/11/2026 13:00» y motivo «Ausencia», y pulsa «Bloquear»
- **THEN** la pantalla manda el `POST` sin validar el orden de las fechas y se ve «El bloqueo tiene que terminar después de empezar (RN-AG-17).»
- **AND** el formulario conserva lo cargado y no se ve «Bloqueo creado.»

#### Scenario: US-003 CA-1 Error de formato - un motivo demasiado largo vuelve con «Revisá los datos del bloqueo.»

- **GIVEN** con sesión de la odontóloga
- **WHEN** elige «Todo el consultorio», escribe desde «23/11/2026 00:00», hasta «24/11/2026 00:00» y un motivo de 201 caracteres, y pulsa «Bloquear»
- **THEN** la pantalla manda el `POST` sin limitar el largo del motivo y la API responde `422` con `codigos` vacío (D283)
- **AND** se ve «Revisá los datos del bloqueo.», el formulario conserva lo cargado y no se ve «Bloqueo creado.»

#### Scenario: US-003 CA-1 Error de negocio - la recepcionista intenta crear y eliminar

- **GIVEN** con sesión de la recepcionista, y en el servidor falso el bloqueo «Feriado»
- **WHEN** completa el formulario y pulsa «Bloquear», y después pulsa «Eliminar» en el bloqueo «Feriado»
- **THEN** cada vez se ve «Tu usuario no tiene permiso para modificar los bloqueos (RN-AU-05).»
- **AND** no se pidió `POST /auth/refresh`, la recepcionista sigue en el panel y el bloqueo «Feriado» sigue en la lista

#### Scenario: US-003 CA-1 Borde - un bloqueo que ya no existe y un profesional que ya no está

- **GIVEN** con sesión de la odontóloga, el bloqueo «Feriado» en la lista, que el servidor falso quita antes de eliminarlo, y el profesional 1, que el servidor falso quita antes de crear
- **WHEN** pulsa «Eliminar» en «Feriado»; y después completa un bloqueo de «Un profesional» «Dra. Demo Ficticia» y pulsa «Bloquear»
- **THEN** primero se ve «El bloqueo ya no existe (RN-GL-04).» y se vuelve a pedir `GET /bloqueos`
- **AND** después se ve «El profesional o el sillón elegido ya no está disponible (RN-GL-04).» y se vuelven a pedir `GET /profesionales` y `GET /sillones`
- **AND** este escenario solo se verifica contra el servidor falso (la API real no borra profesionales)

### Requirement: La sesión que termina en la pantalla de bloqueos vuelve al inicio de sesión

Si la sesión no se puede renovar mientras se usa la pantalla, la interfaz SHALL volver a `/ingresar` con «Tu sesión terminó. Iniciá sesión de nuevo.» y MUST NOT mostrar el mensaje de conexión ni dejar un bloqueo a medio crear (US-092 CA-1; cableado de C-11, D231).

#### Scenario: US-092 CA-1 Borde - una sesión irrenovable al crear un bloqueo

- **GIVEN** con sesión de la odontóloga, el formulario completo y la sesión que ya no se puede renovar
- **WHEN** pulsa «Bloquear»
- **THEN** la interfaz vuelve a `/ingresar` con el aviso de sesión terminada
- **AND** no se guardó ningún bloqueo
