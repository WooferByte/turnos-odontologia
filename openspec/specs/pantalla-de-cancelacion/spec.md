# pantalla-de-cancelacion Specification

## Purpose

Define cómo el panel cancela un turno desde la agenda del día en el navegador: la acción «Cancelar» de cada turno activo, el panel lateral que pregunta quién pidió la cancelación, qué manda a la API, cómo se ven el resultado y cada rechazo con su código, y cómo convive con «Nuevo turno», «Reprogramar» e «Historial» (US-013 CA-1 y CA-2; CAN-1).

Convenciones de los escenarios: la API es la de `cancelacion-de-turnos` (`POST /turnos/{id}/cancelar`), que decide los permisos, la existencia del turno y su estado; la pantalla no evalúa reglas y muestra cada rechazo con su código RN, sin el `detail` de la API (D323). Fechas y horas se muestran en **hora del consultorio** (`America/Argentina/Buenos_Aires`, UTC−3, la `zona_horaria` que trae la agenda); entre paréntesis, el valor en UTC que viaja por la API. La agenda de partida es la de `pantalla-de-agenda` en el servidor falso: el lunes 2 de noviembre de 2026, el turno 11 de Ana Ejemplo con «Consulta / control» de 09:00 a 09:30 (`12:00Z` a `12:30Z`), `reservado`; el turno 12 de Bruno Ficticio con «Limpieza» de 10:00 a 10:45 (`13:00Z` a `13:45Z`), `reservado`; y el turno 13 de Carla Inventada con «Obturación» de 11:00 a 12:00 (`14:00Z` a `15:00Z`), `confirmado`. «Con sesión de X» significa que X inició sesión en el panel (`ingreso-al-panel`); «la odontóloga», «la recepcionista» y «el dueño» (solo `dueno`) son los usuarios ficticios de la demo. Desde este change el frontend nombra `cancelado_profesional` al estado que antes llamaba `cancelado_consultorio` (D342), con la etiqueta «Cancelado por el consultorio». Los textos fijos y las elecciones de la pantalla son **decisiones del autor** del 2026-10-29 (D350 y D351). La disposición viene de las pantallas de Stitch citadas en el design (D234); lo puramente visual no tiene escenario. Cada escenario tiene un ID propio (`CAN-4a`…) que lleva el nombre de su test; en los de varias corridas, cada corrida es un test propio. Los escenarios se verifican en la suite del frontend (`npm test`) y los que lo dicen se repiten en la prueba en el navegador.

## Requirements

### Requirement: Un turno activo se cancela desde su fila de la agenda indicando quién lo pidió

Cada fila de la agenda (`/panel/agenda`) de un turno **activo** (`pendiente_aprobacion`, `pendiente_sena`, `reservado`, `confirmado`) SHALL tener, en la columna «Acciones», entre «Reprogramar» e «Historial», un botón «Cancelar» con un nombre accesible propio de la fila («Cancelar el turno de Ana Ejemplo, 09:00»); la fila de un turno en estado terminal (`cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido`, `ausente`) MUST NOT tenerlo. El botón SHALL abrir, al costado de la agenda, el panel «Cancelar turno» con el resumen del turno tomado de la fila («Ana Ejemplo · Consulta / control» y «lunes 2 de noviembre de 2026, 09:00 – 09:30 · Reservado»), la pregunta «¿Quién pidió la cancelación?» con dos opciones, «El paciente» y «El consultorio», **ninguna marcada**, la ayuda «El horario queda libre para otro turno.», y los botones «Volver» y «Cancelar turno». La fila del turno abierto SHALL marcarse como seleccionada (la misma marca que usan el historial y «Reprogramar»), y ninguna otra. Al abrir el panel el foco SHALL ir a la primera opción; al cerrarlo con «Volver» o «Cerrar», SHALL volver al botón «Cancelar» de la fila. «Cancelar turno» SHALL mandar un solo `POST /turnos/{id}/cancelar` con `{"estado": "cancelado_paciente"}` si se eligió «El paciente» o `{"estado": "cancelado_profesional"}` si se eligió «El consultorio»; si responde `200`, el panel SHALL cerrarse, mostrarse «Turno cancelado.» y pedirse de nuevo la agenda del mismo día, donde la fila se ve con la etiqueta del estado nuevo, con «Historial» y sin «Reprogramar» ni «Cancelar». Si esa recarga falla, el turno ya quedó cancelado: se ve «Turno cancelado.» junto al aviso de conexión de la agenda con «Reintentar», que vuelve a pedir ese mismo día, y no se repite el `POST`. Al abrir el panel no se pide nada a la API. La agenda SHALL mostrar un solo panel lateral a la vez entre «Nuevo turno», «Historial del turno», «Reprogramar turno» y «Cancelar turno», y cambiar de día SHALL cerrar «Cancelar turno» sin mandar nada.

#### Scenario: CAN-4a Feliz - la recepcionista cancela un turno a pedido del paciente (US-013 CA-1, CA-2)

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre
- **WHEN** pulsa «Cancelar el turno de Ana Ejemplo, 09:00», elige «El paciente» y pulsa «Cancelar turno»
- **THEN** al abrir ve «Cancelar turno», «Ana Ejemplo · Consulta / control», «lunes 2 de noviembre de 2026, 09:00 – 09:30 · Reservado», «¿Quién pidió la cancelación?» con «El paciente» y «El consultorio» sin marcar y «El horario queda libre para otro turno.», y no se hizo ninguna petición nueva
- **AND** al abrir, el foco está en la opción «El paciente» y la fila de Ana Ejemplo está marcada como seleccionada, y ninguna otra
- **AND** al pulsar «Cancelar turno» se manda un solo `POST /turnos/11/cancelar` con el cuerpo exacto `{"estado": "cancelado_paciente"}`
- **AND** el panel se cierra, se ve «Turno cancelado.», se pide `GET /turnos?fecha=2026-11-02` y la fila de Ana Ejemplo se ve de 09:00 a 09:30 con «Cancelado por el paciente», con «Historial» y sin «Reprogramar» ni «Cancelar»
- **AND** este escenario se repite en la prueba en el navegador con un turno creado desde la agenda de la demo, y después se crea otro turno a las 09:00 del mismo día desde «Nuevo turno» (el horario quedó libre)

#### Scenario: CAN-4b Borde - cancelar por el consultorio, otros estados activos y la recarga que falla

- **GIVEN** con sesión de la odontóloga, en la agenda del 2 de noviembre, y en el servidor falso también un turno 18 `pendiente_aprobacion` de 16:00 a 16:30 y un turno 19 `pendiente_sena` de 17:00 a 17:30
- **WHEN** en una corrida cancela el turno de Carla Inventada (`confirmado`) eligiendo «El consultorio»; en otra cancela el turno 18 y en otra el 19 eligiendo «El paciente»; y en otra cancela el turno de Bruno Ficticio, el servidor falso responde `200` al `POST /turnos/12/cancelar` y la recarga `GET /turnos?fecha=2026-11-02` no responde (sin conexión)
- **THEN** en la primera se manda `{"estado": "cancelado_profesional"}` y la fila de Carla se ve con «Cancelado por el consultorio», sin «Reprogramar» ni «Cancelar»
- **AND** en la segunda y la tercera cada fila se ve con «Cancelado por el paciente»
- **AND** en la última el panel se cierra, se ven «Turno cancelado.» y el aviso de conexión de la agenda con «Reintentar», se mandó un solo `POST` y no se repite, y al pulsar «Reintentar» con la conexión de vuelta se pide de nuevo `GET /turnos?fecha=2026-11-02` y la fila de Bruno se ve con «Cancelado por el paciente»
- **AND** la primera corrida se repite en la prueba en el navegador contra la API de la demo

#### Scenario: CAN-4c Borde - un solo panel a la vez, el cambio de día lo cierra, el foco vuelve a la fila y los turnos no activos no tienen la acción

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, y en el servidor falso también un turno 14 de Bruno Ficticio `cancelado_paciente` de 12:00 a 12:30, un turno 15 `atendido` de 13:00 a 13:30, un turno 16 `ausente` de 14:00 a 14:30, un turno 17 `vencido` de 15:00 a 15:30 y un turno 20 `cancelado_profesional` de 18:00 a 18:30
- **WHEN** en una corrida abre «Cancelar» del turno de Ana, después «Reprogramar» del mismo turno y después otra vez «Cancelar»; en otra, con «Cancelar turno» abierto pulsa «Día siguiente»; en otra, abre «Cancelar» del turno de Ana, elige «El paciente» y pulsa «Volver» (y, en otra, «Cerrar»); y en otra mira las filas de los turnos 11 a 17 y 20
- **THEN** en la primera se ve un solo panel lateral por vez: «Reprogramar turno» cierra «Cancelar turno» y viceversa
- **AND** en la segunda el panel «Cancelar turno» desaparece, se ve la agenda del 3 de noviembre y no se manda ningún `POST`
- **AND** en la tercera el panel desaparece sin ninguna petición, el foco vuelve al botón «Cancelar el turno de Ana Ejemplo, 09:00», ninguna fila queda marcada como seleccionada y, al volver a abrirlo, ninguna opción está marcada
- **AND** en la cuarta las filas de los turnos 14 a 17 y 20 (no activos) tienen «Historial» y no tienen «Reprogramar» ni «Cancelar»; la del turno 20 se ve con «Cancelado por el consultorio»; y las de los turnos 11, 12 y 13 (activos) tienen los tres botones, en el orden «Reprogramar», «Cancelar», «Historial»
- **AND** la cuarta corrida solo se verifica contra el servidor falso (la demo no tiene turnos en esos estados salvo los cancelados)

### Requirement: Los rechazos y lo que la pantalla frena se ven con su texto y la elección se conserva

Un rechazo de `POST /turnos/{id}/cancelar` SHALL mostrarse en el panel con un texto fijo según su tipo y su código, seguido de «El turno no cambió.», conservando la opción elegida y sin «Turno cancelado.»:

| Respuesta | Texto |
|---|---|
| `409` con `RN-AG-12` | «Este turno ya no se puede cancelar por su estado (RN-AG-12).» |
| `404` con `RN-GL-04` | «El turno ya no existe (RN-GL-04).» |
| `403` con `RN-AU-05` | «Tu usuario no tiene permiso para cancelar turnos (RN-AU-05).» |
| sin conexión, `5xx`, un `422` o una respuesta de otra forma | el aviso de conexión de la agenda |

La pantalla SHALL frenar, sin pedir nada a la API, «Cancelar turno» sin ninguna opción elegida («Elegí quién pidió la cancelación.»). Mientras espera la respuesta, «Cancelar turno» SHALL estar deshabilitado, así que un doble clic manda un solo `POST`. «Volver» y «Cerrar» SHALL cerrar el panel sin pedir nada. Si la sesión se puede renovar, la petición se repite sin aviso; si no, se vuelve al inicio de sesión (como en la agenda).

#### Scenario: CAN-5a Error de negocio - un turno que ya no está activo muestra RN-AG-12 y no cambia (CAN-1)

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, con «Cancelar» del turno de Ana Ejemplo abierto, y en el servidor falso el turno 11 ya pasado a `cancelado_profesional` por otra sesión después de cargar la agenda
- **WHEN** elige «El paciente» y pulsa «Cancelar turno»
- **THEN** se manda un solo `POST /turnos/11/cancelar`, el servidor falso responde `409` con `codigos` `["RN-AG-12"]` y en el panel se ve «Este turno ya no se puede cancelar por su estado (RN-AG-12).» y «El turno no cambió.»
- **AND** el panel sigue abierto con «El paciente» marcado y no se ve «Turno cancelado.»
- **AND** en la prueba en el navegador se repite cancelando el mismo turno de la demo desde dos pestañas: la segunda ve este texto

#### Scenario: CAN-5b Borde - lo que la pantalla frena sin pedir nada, los demás rechazos, el doble clic, la conexión y la sesión

- **GIVEN** con sesión de la recepcionista (o del dueño, en la corrida del `403`), en la agenda del 2 de noviembre, con «Cancelar» del turno de Ana abierto
- **WHEN** en una corrida por caso: pulsa «Cancelar turno» sin elegir ninguna opción; elige «El consultorio» y el servidor falso contesta `404` `RN-GL-04`; el dueño elige «El paciente» y el servidor falso contesta `403` `RN-AU-05`; elige una opción y pulsa «Cancelar turno» dos veces con la respuesta retenida; elige una opción y la API no responde (sin conexión); elige una opción y el servidor falso contesta `500`; elige una opción y el servidor falso contesta `422` (un cuerpo de otra forma); y elige una opción con el access token vencido y, en otra, con la sesión irrenovable
- **THEN** la primera muestra «Elegí quién pidió la cancelación.» y no manda ningún `POST`
- **AND** el `404` muestra «El turno ya no existe (RN-GL-04).» y el `403` «Tu usuario no tiene permiso para cancelar turnos (RN-AU-05).», cada uno seguido de «El turno no cambió.» y con la opción elegida conservada, y el `403` no hace ningún `POST /auth/refresh`
- **AND** el dueño ve «Cancelar» en las filas activas (ocultar acciones según el rol queda para un change posterior, D312)
- **AND** en la del doble clic se manda un solo `POST` y «Cancelar turno» está deshabilitado mientras espera
- **AND** sin conexión, con el `500` y con el `422` se ve, en cada corrida, el aviso de conexión de la agenda seguido de «El turno no cambió.», la opción elegida se conserva y no se ve «Turno cancelado.»
- **AND** con el access token vencido se hace un solo `POST /auth/refresh`, se repite el `POST` y se ve «Turno cancelado.»; con la sesión irrenovable se vuelve al inicio de sesión
- **AND** la corrida sin opción y la del dueño se repiten en la prueba en el navegador contra la API de la demo
