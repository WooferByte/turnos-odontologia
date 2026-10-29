# pantalla-de-reprogramacion Specification

## Purpose

Define cómo el panel reprograma un turno desde la agenda del día en el navegador: la acción «Reprogramar» de cada turno activo, el panel lateral que la hace, qué manda a la API, cómo se ven el resultado y cada rechazo con su código, y cómo convive con «Nuevo turno» e «Historial» (US-012 CA-1 y CA-4; REP-1).

Convenciones de los escenarios: la API es la de `reprogramacion-de-turnos` (`PATCH /turnos/{id}`), que decide los permisos, la existencia del turno y todas las reglas; la pantalla no evalúa reglas de agenda ni valida la duración (como D232) y muestra cada rechazo con su código RN, sin el `detail` de la API (D323). Fechas y horas se escriben y se muestran en **hora del consultorio** (`America/Argentina/Buenos_Aires`, UTC−3, la `zona_horaria` que trae la agenda); entre paréntesis, el valor en UTC que viaja por la API. La agenda de partida es la de `pantalla-de-agenda` en el servidor falso: el lunes 2 de noviembre de 2026, el turno 11 de Ana Ejemplo con «Consulta / control» de 09:00 a 09:30 (`12:00Z` a `12:30Z`), `reservado`; el turno 12 de Bruno Ficticio con «Limpieza» de 10:00 a 10:45 (`13:00Z` a `13:45Z`), `reservado`; y el turno 13 de Carla Inventada con «Obturación» de 11:00 a 12:00 (`14:00Z` a `15:00Z`), `confirmado`. «Con sesión de X» significa que X inició sesión en el panel (`ingreso-al-panel`); «la odontóloga», «la recepcionista» y «el dueño» (solo `dueno`) son los usuarios ficticios de la demo. Los textos fijos y las elecciones de la pantalla son decisiones del autor (D339, 2026-10-29). El frontend todavía nombra `cancelado_consultorio` al estado que la API llama `cancelado_profesional`; lo corrige C-17 (D342), así que los escenarios de esta pantalla no usan ese estado. La disposición viene de las pantallas de Stitch citadas en el design (D234); lo puramente visual no tiene escenario. Cada escenario tiene un ID propio (`REP-6a`…) que lleva el nombre de su test; en los de varias corridas, cada corrida es un test propio. Los escenarios se verifican en la suite del frontend (`npm test`) y los que lo dicen se repiten en la prueba en el navegador; los demás (por ejemplo, la corrida de `REP-6b` que cruza la medianoche UTC a las 22:00, fuera del horario de 08:00 a 20:00 de la demo) solo se verifican contra el servidor falso.

## Requirements

### Requirement: Un turno activo se reprograma desde su fila de la agenda

Cada fila de la agenda (`/panel/agenda`) de un turno **activo** (`pendiente_aprobacion`, `pendiente_sena`, `reservado`, `confirmado`) SHALL tener, en la columna «Acciones» y antes de «Historial», un botón «Reprogramar» con un nombre accesible propio de la fila («Reprogramar el turno de Ana Ejemplo, 09:00»); la fila de un turno en estado terminal MUST NOT tenerlo. El botón SHALL abrir, al costado de la agenda, el panel «Reprogramar turno» con el resumen del turno tomado de la fila («Ana Ejemplo · Consulta / control» y «Ahora: lunes 2 de noviembre de 2026, 09:00 – 09:30»), la nota «Fecha y hora del consultorio.» y los campos «Fecha», «Hora» y «Duración (minutos)» cargados con los valores actuales del turno, con la ayuda «Múltiplo de 5 minutos.» y, cuando los tres campos están completos, «Termina a las {hh:mm}.». La fila del turno abierto SHALL marcarse como seleccionada (la misma marca que usa el historial), y ninguna otra. Al abrir el panel el foco SHALL ir al campo «Fecha»; al cerrarlo con «Cancelar» o «Cerrar», SHALL volver al botón «Reprogramar» de la fila. «Reprogramar» del panel SHALL mandar un solo `PATCH /turnos/{id}` con `inicio` (la fecha y la hora del consultorio convertidas a UTC) y `duracion_minutos`; si responde `200`, el panel SHALL cerrarse, mostrarse «Turno reprogramado.» y pedirse la agenda del día del consultorio del nuevo inicio, que puede ser otro día. Si esa recarga falla, el turno ya quedó reprogramado: se ve «Turno reprogramado.» junto al aviso de conexión de la agenda con «Reintentar», que vuelve a pedir ese mismo día, y no se repite el `PATCH`. Al abrir el panel no se pide nada a la API.

#### Scenario: REP-6a Feliz - la recepcionista mueve un turno y lo ve en su nuevo horario (US-012 CA-1)

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre
- **WHEN** pulsa «Reprogramar el turno de Ana Ejemplo, 09:00», cambia «Hora» a 12:30 y pulsa «Reprogramar»
- **THEN** al abrir ve «Reprogramar turno», «Ana Ejemplo · Consulta / control», «Ahora: lunes 2 de noviembre de 2026, 09:00 – 09:30», «Fecha» 2026-11-02, «Hora» 09:00, «Duración (minutos)» 30 y «Termina a las 09:30.», y no se hizo ninguna petición nueva
- **AND** al abrir, el foco está en el campo «Fecha» y la fila de Ana Ejemplo está marcada como seleccionada, y ninguna otra
- **AND** al cambiar la hora ve «Termina a las 13:00.»
- **AND** al pulsar «Reprogramar» se manda un solo `PATCH /turnos/11` con el cuerpo exacto `{"inicio": "2026-11-02T15:30:00Z", "duracion_minutos": 30}`
- **AND** el panel se cierra, se ve «Turno reprogramado.», se pide `GET /turnos?fecha=2026-11-02` y la fila de Ana Ejemplo se ve de 12:30 a 13:00, después de la de Carla Inventada
- **AND** este escenario se repite en la prueba en el navegador con un turno creado desde la agenda de la demo

#### Scenario: REP-6b Borde - mover a otro día y cambiar solo la duración (US-012 CA-1, CA-4)

- **GIVEN** con sesión de la odontóloga, en la agenda del 2 de noviembre
- **WHEN** en una corrida reprograma el turno de Bruno Ficticio con «Fecha» 2026-11-03 y «Hora» 22:00 (cuerpo con `inicio` `2026-11-04T01:00:00Z`, `duracion_minutos` 45); y en otra reprograma el turno de Carla Inventada solo con «Duración (minutos)» 90
- **THEN** en la primera se ve «Termina a las 22:45.», la agenda pasa al «martes 3 de noviembre de 2026» (`GET /turnos?fecha=2026-11-03`, no la fecha UTC del inicio) y muestra el turno de Bruno de 22:00 a 22:45
- **AND** en la segunda se manda `{"inicio": "2026-11-02T14:00:00Z", "duracion_minutos": 90}`, se ve «Termina a las 12:30.» antes de enviar y después la fila de Carla de 11:00 a 12:30
- **AND** la corrida de las 22:00 solo se verifica contra el servidor falso; en la prueba en el navegador este escenario se repite moviendo un turno a otro día dentro del horario de la demo (de 08:00 a 20:00) y cambiando solo la duración

#### Scenario: REP-6c Borde - un solo panel a la vez, el cambio de día lo cierra, el foco vuelve a la fila y los turnos no activos no tienen la acción

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, y en el servidor falso también un turno 14 de Bruno Ficticio `cancelado_paciente` de 12:00 a 12:30, un turno 15 `atendido` de 13:00 a 13:30, un turno 16 `ausente` de 14:00 a 14:30, un turno 17 `vencido` de 15:00 a 15:30, un turno 18 `pendiente_aprobacion` de 16:00 a 16:30 y un turno 19 `pendiente_sena` de 17:00 a 17:30
- **WHEN** en una corrida abre «Reprogramar» del turno de Ana y después «Historial» del mismo turno, y después «Nuevo turno»; en otra, con «Reprogramar» abierto, pulsa «Día siguiente»; en otra, abre «Reprogramar» del turno de Ana y pulsa «Cancelar» (y, en otra, «Cerrar»); y en otra mira las filas de los turnos 11 a 19
- **THEN** en la primera se ve un solo panel lateral por vez: «Historial» cierra «Reprogramar turno» y «Nuevo turno» cierra el historial
- **AND** en la segunda el panel «Reprogramar turno» desaparece, se ve la agenda del 3 de noviembre y no se manda ningún `PATCH`
- **AND** en la tercera el panel desaparece sin ninguna petición, el foco vuelve al botón «Reprogramar el turno de Ana Ejemplo, 09:00» y ninguna fila queda marcada como seleccionada
- **AND** en la cuarta las filas de los turnos 14 a 17 (no activos) tienen «Historial» y no tienen «Reprogramar», y las de los turnos 11, 12, 13, 18 y 19 (activos) tienen los dos

#### Scenario: REP-6d Borde - el PATCH responde 200 pero la recarga del día falla

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, con «Reprogramar» del turno de Ana abierto y «Hora» 12:30
- **WHEN** pulsa «Reprogramar», el servidor falso responde `200` al `PATCH /turnos/11` y la recarga `GET /turnos?fecha=2026-11-02` no responde (sin conexión)
- **THEN** el panel se cierra y se ven «Turno reprogramado.» y el aviso de conexión de la agenda con «Reintentar»
- **AND** se mandó un solo `PATCH` y no se repite
- **AND** al pulsar «Reintentar» con la conexión de vuelta se pide de nuevo `GET /turnos?fecha=2026-11-02` y la fila de Ana Ejemplo se ve de 12:30 a 13:00

### Requirement: Los rechazos y lo que la pantalla frena se ven con su texto y lo cargado se conserva

Un rechazo de `PATCH /turnos/{id}` SHALL mostrarse en el panel con un texto fijo según su tipo y su código, seguido de «El turno no cambió.», conservando lo cargado y sin «Turno reprogramado.»:

| Respuesta | Texto |
|---|---|
| `409` con `RN-AG-05` y `RN-AG-08` | «El profesional y el sillón ya tienen un turno activo en ese horario (RN-AG-05, RN-AG-08).» |
| `409` con un solo código de solapamiento | el texto de `RN-AG-05` o de `RN-AG-08` de la agenda |
| `422` con `RN-AG-01` | «La duración debe ser mayor que 0 y múltiplo de 5 minutos (RN-AG-01).» |
| `422` con `RN-AG-04`, `RN-AG-04b`, `RN-AG-10d` o `RN-GL-01` | los textos de la agenda para ese código |
| `409` con `RN-AG-18` | «Este turno ya no se puede reprogramar por su estado (RN-AG-18).» |
| `404` con `RN-GL-04` | «El turno ya no existe (RN-GL-04).» |
| `403` con `RN-AU-05` | «Tu usuario no tiene permiso para reprogramar turnos (RN-AU-05).» |
| sin conexión, `5xx` o respuesta de otra forma | el aviso de conexión de la agenda |

La pantalla SHALL frenar, sin pedir nada a la API, una petición con «Fecha», «Hora» o «Duración (minutos)» vacíos o con una duración que no es un número entero sin signo («Completá fecha, hora y duración.») y una petición que no cambia ni el inicio ni la duración («No cambiaste la fecha, la hora ni la duración.»). Mientras espera la respuesta, «Reprogramar» SHALL estar deshabilitado, así que un doble clic manda un solo `PATCH`. «Cancelar» y «Cerrar» SHALL cerrar el panel sin pedir nada. Si la sesión se puede renovar, la petición se repite sin aviso; si no, se vuelve al inicio de sesión (como en la agenda).

#### Scenario: REP-7a Error de negocio - reprogramar sobre otro turno activo muestra los dos códigos y el turno no cambia (REP-1)

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre
- **WHEN** abre «Reprogramar» del turno de Ana Ejemplo, pone «Hora» 10:15 (sobre el turno de Bruno) y pulsa «Reprogramar»
- **THEN** se manda un solo `PATCH /turnos/11`, el servidor falso responde `409` con `codigos` `["RN-AG-05", "RN-AG-08"]` y en el panel se ve «El profesional y el sillón ya tienen un turno activo en ese horario (RN-AG-05, RN-AG-08).» y «El turno no cambió.»
- **AND** el panel sigue abierto con «Hora» 10:15 y «Duración (minutos)» 30, no se ve «Turno reprogramado.» y la fila de Ana sigue de 09:00 a 09:30
- **AND** este escenario se repite en la prueba en el navegador contra la API de la demo

#### Scenario: REP-7b Error de negocio - los demás rechazos de la API con su texto

- **GIVEN** con sesión de la recepcionista (o del dueño, en la corrida del `403`), en la agenda del 2 de noviembre, con «Reprogramar» del turno de Ana abierto y un cambio cargado
- **WHEN** en una corrida por respuesta el servidor falso contesta `422` `RN-AG-01` (con «Duración (minutos)» 42), `422` `RN-AG-04`, `422` `RN-AG-04b`, `422` `RN-AG-10d`, `409` `RN-AG-18`, `404` `RN-GL-04` y `403` `RN-AU-05`
- **THEN** cada corrida muestra el texto de la tabla para esa respuesta, seguido de «El turno no cambió.», con lo cargado conservado
- **AND** el `403` no hace ningún `POST /auth/refresh`
- **AND** el `RN-AG-01` y el `RN-AG-04` se repiten en la prueba en el navegador contra la API de la demo

#### Scenario: REP-7c Borde - lo que la pantalla frena sin pedir nada, Cancelar, el doble clic y la conexión

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, con «Reprogramar» del turno de Ana abierto
- **WHEN** en una corrida por caso: borra «Hora» y pulsa «Reprogramar»; pone «Duración (minutos)» «media» y pulsa «Reprogramar»; pulsa «Reprogramar» sin cambiar nada; cambia la hora y pulsa «Cancelar»; cambia la hora y pulsa «Reprogramar» dos veces con la respuesta retenida; cambia la hora y la API no responde (sin conexión); y cambia la hora con el access token vencido y, en otra, con la sesión irrenovable
- **THEN** las dos primeras muestran «Completá fecha, hora y duración.», la tercera «No cambiaste la fecha, la hora ni la duración.», y la cuarta cierra el panel: en ninguna se manda un `PATCH`
- **AND** en la del doble clic se manda un solo `PATCH` y «Reprogramar» está deshabilitado mientras espera
- **AND** sin conexión se ve el aviso de conexión de la agenda seguido de «El turno no cambió.» y lo cargado se conserva
- **AND** con el access token vencido se hace un solo `POST /auth/refresh`, se repite el `PATCH` y se ve «Turno reprogramado.»; con la sesión irrenovable se vuelve al inicio de sesión

#### Scenario: REP-7d Borde - el dueño ve la acción y recibe el 403 de la API (D312)

- **GIVEN** con sesión del dueño, en la agenda del 2 de noviembre
- **WHEN** abre «Reprogramar» del turno de Ana, cambia la hora y pulsa «Reprogramar»
- **THEN** el botón «Reprogramar» está en las filas activas (ocultar acciones según el rol queda para un change posterior, D312)
- **AND** el servidor falso responde `403` `RN-AU-05` y se ve «Tu usuario no tiene permiso para reprogramar turnos (RN-AU-05).» y «El turno no cambió.»
- **AND** este escenario se repite en la prueba en el navegador con el dueño de la demo
