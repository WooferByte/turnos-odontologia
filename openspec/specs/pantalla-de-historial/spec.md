# pantalla-de-historial Specification

## Purpose

Define cómo el panel muestra en el navegador el historial de un turno, abierto desde la agenda del día: qué se ve de cada evento, en qué orden, que es de solo lectura, que hay un solo panel lateral a la vez y qué pasa con la carga, el vacío, los rechazos y la sesión que termina (US-015 CA-1; E9; HIS-2; RN-AG-11).

Convenciones de los escenarios: la API es la de `historial-de-turnos` (`GET /turnos/{id}/historial`), que decide los permisos y la existencia del turno y devuelve los eventos ya ordenados; la pantalla no reordena, no evalúa reglas y muestra cada rechazo con su código RN, sin el `detail` de la API. Fechas y horas se escriben y se muestran en **hora del consultorio** (`America/Argentina/Buenos_Aires`, UTC−3, la `zona_horaria` que trae la agenda); entre paréntesis, el valor en UTC que viaja por la API. La agenda de partida es la de `pantalla-de-agenda` en el servidor falso: el lunes 2 de noviembre de 2026, el turno 11 de Ana Ejemplo con «Consulta / control» de 09:00 a 09:30 (`12:00Z` a `12:30Z`) y el turno 12 de Bruno Ficticio con «Limpieza» de 10:00 a 10:45 (`13:00Z` a `13:45Z`), ambos `reservado`. «Con sesión de X» significa que X inició sesión en el panel (`ingreso-al-panel`); «la odontóloga», «la recepcionista» y «el dueño» (solo `dueno`) son los usuarios ficticios de la demo. `HIS-2` es el escenario mínimo que `CHANGES.md` fija para C-15 («los eventos se muestran en orden cronológico con actor y fecha»); la KB solo define `HIS-1` (C-03), y este spec lo detalla en `HIS-2a` a `HIS-2f`. US-015 dice «Como dueño», pero la matriz de `03` da lectura del historial a los tres roles (D68), y manda la matriz. Los textos fijos y las elecciones de la pantalla son decisiones del autor (D327 a D330; 2026-10-28). La disposición viene de las pantallas de Stitch citadas en el design (D234); lo puramente visual no tiene escenario. Los casos defensivos del design que la API de hoy no produce (un `actor_tipo` que la pantalla no conoce, un `despues` sin `estado`, `inicio` o `fin`, y un `2xx` con otra forma) se prueban con tests unitarios de `mensajes.ts` y `apiHistorial.ts`, sin escenario propio. Cada escenario tiene un ID propio (`HIS-2a`…) que lleva el nombre de su test. Los escenarios se verifican en la suite del frontend (`npm test`) y los que lo dicen se repiten en la prueba en el navegador.

## Requirements

### Requirement: El historial de un turno se abre desde la agenda y es de solo lectura

Cada fila de la agenda (`/panel/agenda`) SHALL tener, en una columna «Acciones», un botón «Historial» con un nombre accesible propio de la fila («Historial del turno de Ana Ejemplo, 09:00») que abre, al costado de la agenda, el panel «Historial del turno» con el resumen del turno tomado de la fila (paciente y prestación; día, hora de inicio y de fin en hora del consultorio) y la nota «Solo lectura: el historial no se puede editar.». Al abrirse SHALL pedir una sola vez `GET /turnos/{id}/historial` del turno de esa fila, llevar el foco al título del panel y mostrar una entrada por evento, en el orden de la respuesta (del más antiguo al más reciente, RN-AG-11). Cada entrada SHALL mostrar qué pasó (para el tipo `creado`, «Turno creado»; para el tipo `reprogramado`, «Turno reprogramado»; para el tipo `cancelado`, «Turno cancelado»; para un tipo que la pantalla todavía no conoce, «Cambio registrado ({tipo})»), cuándo (fecha y hora de `ocurrido_en` en hora del consultorio, «lunes 26 de octubre de 2026, 10:15») y quién («Por: Usuario n.º 2»; con `actor_tipo` `usuario` y `actor_id` vacío, «Por: Usuario del panel (sin identificar)», D159), y «Motivo: {motivo}» si el evento lo trae. El evento `creado` SHALL mostrar además el estado y el horario con que nació el turno, tomados de su `despues` («Estado inicial: Reservado · 09:00 – 09:30»). El evento `reprogramado` SHALL mostrar además el horario de antes y el de después, tomados de su `antes` y su `despues`, cada uno con su día, sus horas de inicio y de fin en hora del consultorio y su duración en minutos («Antes: lunes 2 de noviembre de 2026, 09:00 – 09:30 (30 min)» y «Después: martes 3 de noviembre de 2026, 15:00 – 15:45 (45 min)»; D340); si `antes` o `despues` no traen un `inicio` y un `fin` de texto y un `duracion_minutos` entero, esas líneas no se muestran y la entrada sí (US-012 CA-2, DD-05). El evento `cancelado` SHALL mostrar además el cambio de estado con las etiquetas de la agenda, tomado del `estado` de su `antes` y de su `despues` («Estado: Reservado → Cancelado por el paciente»; D352); si `antes` o `despues` no traen un `estado` que la pantalla conoce, esa línea no se muestra y la entrada sí (RN-AG-11). El panel MUST NOT ofrecer ninguna acción que cree, modifique o borre eventos (US-015 CA-1): solo «Cerrar», que lo cierra sin ninguna petición nueva y devuelve el foco al botón «Historial» de la fila. Una respuesta que llega después de cerrar el panel MUST NOT volver a abrirlo. El botón y el panel SHALL estar disponibles para el odontólogo, la recepcionista y el dueño (matriz de `03`, fila «Historial de cambios de turno»).

#### Scenario: HIS-2a Feliz - la recepcionista ve el evento `creado` de un turno (US-015 CA-1, E9)

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, y en el servidor falso el historial del turno 11 con un evento `creado`, `ocurrido_en` `2026-10-26T13:15:00Z`, `actor_tipo` `usuario`, `actor_id` `"2"`, `antes` vacío y `despues` con `estado` `reservado`, `inicio` `2026-11-02T12:00:00Z` y `fin` `2026-11-02T12:30:00Z`
- **WHEN** pulsa «Historial del turno de Ana Ejemplo, 09:00»
- **THEN** se hace una sola petición `GET /turnos/11/historial` y se ve el panel «Historial del turno» con «Ana Ejemplo · Consulta / control», «lunes 2 de noviembre de 2026, 09:00 – 09:30» y «Solo lectura: el historial no se puede editar.», con el foco en el título del panel
- **AND** se ve una entrada con «Turno creado», «lunes 26 de octubre de 2026, 10:15», «Por: Usuario n.º 2» y «Estado inicial: Reservado · 09:00 – 09:30»
- **AND** el panel no tiene ningún botón ni campo para editar, borrar o agregar eventos: solo «Cerrar»
- **AND** lo mismo se ve con sesión de la odontóloga y con sesión del dueño (cada rol es un caso propio)
- **AND** este escenario se repite en la prueba en el navegador con un turno creado desde la agenda de la demo

#### Scenario: HIS-2b Borde - varios eventos en orden cronológico, con actor y fecha (HIS-2)

- **GIVEN** con sesión de la odontóloga, y en el servidor falso el historial del turno 12 con cuatro eventos en este orden de respuesta: un `creado` con `ocurrido_en` `2026-10-27T11:40:00Z` y `actor_id` vacío; un `reprogramado` con `ocurrido_en` `2026-10-30T19:05:00Z`, `actor_id` `"1"`, `antes` con `inicio` `2026-11-02T12:00:00Z`, `fin` `2026-11-02T12:45:00Z` y `duracion_minutos` 45 y `despues` con `inicio` `2026-11-02T13:00:00Z`, `fin` `2026-11-02T13:45:00Z` y `duracion_minutos` 45; un evento de un tipo que la pantalla todavía no conoce, `confirmado`, con `ocurrido_en` `2026-11-01T02:30:00Z`, `actor_id` `"2"` y `motivo` «Pedido del paciente»; y un `cancelado` con `ocurrido_en` `2026-11-01T14:20:00Z`, `actor_id` `"2"`, `antes` `{"estado": "confirmado"}` y `despues` `{"estado": "cancelado_paciente"}`
- **WHEN** pulsa «Historial» en la fila de Bruno Ficticio
- **THEN** ve cuatro entradas en ese mismo orden: «Turno creado», «martes 27 de octubre de 2026, 08:40», «Por: Usuario del panel (sin identificar)»; «Turno reprogramado», «viernes 30 de octubre de 2026, 16:05», «Por: Usuario n.º 1», «Antes: lunes 2 de noviembre de 2026, 09:00 – 09:45 (45 min)» y «Después: lunes 2 de noviembre de 2026, 10:00 – 10:45 (45 min)»; «Cambio registrado (confirmado)», «sábado 31 de octubre de 2026, 23:30», «Por: Usuario n.º 2», «Motivo: Pedido del paciente»; y «Turno cancelado», «domingo 1 de noviembre de 2026, 11:20», «Por: Usuario n.º 2» y «Estado: Confirmado → Cancelado por el paciente»
- **AND** la fecha del tercer evento es la del consultorio (31 de octubre) y no la de UTC (1 de noviembre)
- **AND** un `reprogramado` cuyo `despues` no trae `inicio` (y, en otra corrida, no trae `duracion_minutos`) se ve con «Turno reprogramado», su fecha y su actor, sin las líneas «Antes:» y «Después:»
- **AND** un `cancelado` con `despues` `{"estado": "cancelado_profesional"}` muestra «Estado: Confirmado → Cancelado por el consultorio», y uno cuyo `despues` no trae `estado` (y, en otra corrida, trae un estado que la pantalla no conoce) se ve con «Turno cancelado», su fecha y su actor, sin la línea «Estado:»
- **AND** las entradas «Turno reprogramado» y «Turno cancelado» se repiten en la prueba en el navegador después de reprogramar y de cancelar un turno de la demo (la API real registra `reprogramado` desde C-16 y `cancelado` desde C-17; `confirmado` solo se verifica contra el servidor falso)

#### Scenario: HIS-2c Borde - un turno sin eventos y «Cerrar»

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, y en el servidor falso el turno 12 sin eventos (`200` con una lista vacía, como un turno guardado antes del historial, D160)
- **WHEN** en una corrida pulsa «Historial» en la fila de Bruno Ficticio; en otra, lo abre y pulsa «Cerrar»; y en otra, lo abre con la respuesta retenida, pulsa «Cerrar» y después la respuesta llega
- **THEN** en la primera se ve «Este turno no tiene eventos registrados.»
- **AND** en la segunda el panel desaparece, la agenda sigue a la vista, no se hace ninguna petición nueva y el foco vuelve al botón «Historial» de la fila de Bruno Ficticio
- **AND** en la tercera el panel sigue cerrado aunque la respuesta llegue después de «Cerrar»
- **AND** este escenario se repite en la prueba en el navegador con «Cerrar» (cada corrida es un caso propio)

### Requirement: Un solo panel lateral a la vez, y el historial sigue al turno y al día a la vista

La agenda SHALL mostrar un solo panel lateral a la vez entre «Nuevo turno», «Historial del turno», «Reprogramar turno» y «Cancelar turno» (D339, D350): abrir cualquiera de los cuatro SHALL cerrar el que estuviera abierto. Con el historial de un turno abierto, pulsar «Historial» en otra fila SHALL mostrar el historial de ese otro turno y solo la última respuesta pedida, aunque la del turno anterior llegue después. Cambiar el día de la agenda SHALL cerrar el historial y los paneles «Reprogramar turno» y «Cancelar turno» (el turno ya no está a la vista) sin pedir nada de nuevo, y una respuesta del historial que llega después del cambio de día MUST NOT volver a abrirlo.

#### Scenario: HIS-2f Borde - otro turno, otro día y un solo panel a la vez

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, y en el servidor falso el historial del turno 11 del escenario HIS-2a y el turno 12 sin eventos
- **WHEN** en una corrida pulsa «Historial» en la fila de Bruno Ficticio con la respuesta retenida, después «Historial» en la fila de Ana Ejemplo, y por último la respuesta del turno 12 llega; en otra, con «Nuevo turno» abierto pulsa «Historial» en la fila de Ana Ejemplo y después «Nuevo turno»; en otra, con «Reprogramar turno» del turno 11 abierto pulsa «Historial» en la fila de Ana Ejemplo y después «Reprogramar el turno de Bruno Ficticio, 10:00»; en otra, con «Cancelar turno» del turno 11 abierto pulsa «Historial» en la fila de Ana Ejemplo y después «Cancelar el turno de Bruno Ficticio, 10:00»; en otra, con el historial del turno 11 abierto pulsa «Día siguiente»; y en otra, abre el historial del turno 11 con la respuesta retenida, pulsa «Día siguiente» y después la respuesta llega
- **THEN** en la primera se ve solo el historial del turno 11 («Turno creado»), nunca «Este turno no tiene eventos registrados.»
- **AND** en la segunda, al abrir «Historial» se ve «Historial del turno» y no «Nuevo turno», y al pulsar «Nuevo turno» se ve el formulario y no el historial
- **AND** en la tercera, al abrir «Historial» se ve «Historial del turno» y no «Reprogramar turno», y al pulsar «Reprogramar» de Bruno se ve «Reprogramar turno» con «Bruno Ficticio · Limpieza» y no el historial
- **AND** en la cuarta, al abrir «Historial» se ve «Historial del turno» y no «Cancelar turno», y al pulsar «Cancelar» de Bruno se ve «Cancelar turno» con «Bruno Ficticio · Limpieza» y no el historial
- **AND** en la quinta el panel del historial desaparece, se ve la agenda del 3 de noviembre y no se hace ninguna petición nueva de historial
- **AND** en la sexta el panel sigue cerrado aunque la respuesta llegue después del cambio de día
- **AND** este escenario solo se verifica contra el servidor falso (cada corrida es un caso propio)
### Requirement: Los rechazos, la carga y la sesión del historial se ven con su texto

Mientras llega el historial el panel SHALL mostrar «Cargando historial…». Con un `404` `RN-GL-04` (el turno ya no existe) SHALL mostrar «El turno ya no existe (RN-GL-04).» y con un `403` `RN-AU-05`, «Tu usuario no tiene permiso para ver el historial (RN-AU-05).», en ambos casos sin entradas y sin «Reintentar». Sin conexión o con un `5xx` SHALL mostrar «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» con «Reintentar», que vuelve a pedir el historial. Si el access token venció y el refresh sigue vigente, la sesión SHALL renovarse sin aviso y el historial mostrarse; si la sesión no se puede renovar, el panel SHALL volver al inicio de sesión como el resto del panel (`ingreso-al-panel`).

#### Scenario: HIS-2d Error de negocio - el turno ya no existe o el usuario perdió el permiso

- **GIVEN** con sesión de la odontóloga, con la agenda del 2 de noviembre ya cargada
- **WHEN** pulsa «Historial» en la fila de Ana Ejemplo y la API responde `404` con `codigos` `["RN-GL-04"]`; y, en otra corrida, con la agenda ya cargada al usuario se le quita el permiso en el servidor falso, pulsa «Historial» en la misma fila y la API responde `403` con `codigos` `["RN-AU-05"]`
- **THEN** con el `404` se ve «El turno ya no existe (RN-GL-04).», sin entradas y sin «Reintentar»
- **AND** con el `403` se ve «Tu usuario no tiene permiso para ver el historial (RN-AU-05).», sin entradas, sin «Reintentar» y sin pedir `POST /auth/refresh`
- **AND** en los dos casos la agenda sigue a la vista
- **AND** este escenario solo se verifica contra el servidor falso (cada causa es un caso propio)

#### Scenario: HIS-2e Borde - mientras carga, sin conexión, con un `500` y la sesión que termina

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, y en el servidor falso el historial del turno 11 del escenario HIS-2a
- **WHEN** pulsa «Historial» en la fila de Ana Ejemplo con la respuesta todavía pendiente, y después la API no responde; y, en otras corridas, con la API que responde `500` al historial, con el access token vencido y el refresh vigente, o con la sesión que no se puede renovar
- **THEN** primero se ve «Cargando historial…» sin entradas
- **AND** después se ve «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» con «Reintentar», que al responder la API muestra «Turno creado»
- **AND** con el `500` se ve el mismo texto con «Reintentar», sin entradas
- **AND** con el refresh vigente se hace un solo `POST /auth/refresh` y se ve el historial sin ningún aviso
- **AND** con la sesión que no se puede renovar se vuelve al inicio de sesión
- **AND** este escenario solo se verifica contra el servidor falso (cada causa es un caso propio)
