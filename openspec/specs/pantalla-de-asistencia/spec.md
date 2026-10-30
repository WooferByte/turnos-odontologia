# pantalla-de-asistencia Specification

## Purpose

Define cómo el panel registra desde la agenda del día en el navegador si el paciente asistió a un turno: la acción «Asistencia» de cada turno reservado o confirmado, el panel lateral que pregunta cómo terminó el turno, qué manda a la API, cómo se ven el resultado y cada rechazo con su código, y cómo convive con «Nuevo turno», «Historial», «Reprogramar» y «Cancelar» (US-014 CA-1, CA-2, CA-3 y CA-6).

Convenciones de los escenarios: la API es la de `marcado-de-asistencia` (`POST /turnos/{id}/estado`), que decide los permisos, la existencia del turno, su estado y el momento; la pantalla no evalúa reglas (tampoco compara la hora del turno con el reloj del navegador) y muestra cada rechazo con su código RN, sin el `detail` de la API (D323). Fechas y horas se muestran en **hora del consultorio** (`America/Argentina/Buenos_Aires`, UTC−3, la `zona_horaria` que trae la agenda); entre paréntesis, el valor en UTC que viaja por la API. La agenda de partida es la de `pantalla-de-agenda` en el servidor falso: el lunes 2 de noviembre de 2026, el turno 11 de Ana Ejemplo con «Consulta / control» de 09:00 a 09:30 (`12:00Z` a `12:30Z`), `reservado`; el turno 12 de Bruno Ficticio con «Limpieza» de 10:00 a 10:45 (`13:00Z` a `13:45Z`), `reservado`; y el turno 13 de Carla Inventada con «Obturación» de 11:00 a 12:00 (`14:00Z` a `15:00Z`), `confirmado`. El servidor falso responde `200` al marcado de un turno `reservado` o `confirmado` y `409` `RN-AG-12` a uno en otro estado; no evalúa el momento: el `409` `RN-AG-13` sale de su respuesta fijada. «Con sesión de X» significa que X inició sesión en el panel (`ingreso-al-panel`); «la odontóloga», «la recepcionista» y «el dueño» (solo `dueno`) son los usuarios ficticios de la demo. Los textos fijos y las elecciones de la pantalla son **decisiones del autor** del 2026-10-30 (Q10 del design, D363). La disposición viene de las pantallas de Stitch citadas en el design (D234); lo puramente visual no tiene escenario. Cada escenario tiene un ID propio (`ASI-5a`…) que lleva el nombre de su test; en los de varias corridas, cada corrida es un test propio. Los escenarios se verifican en la suite del frontend (`npm test`) y los que lo dicen se repiten en la prueba en el navegador.

## Requirements

### Requirement: La asistencia de un turno reservado o confirmado se registra desde su fila de la agenda

Cada fila de la agenda (`/panel/agenda`) de un turno **`reservado` o `confirmado`** SHALL tener, en la columna «Acciones», como primer botón (antes de «Reprogramar», «Cancelar» e «Historial»), un botón «Asistencia» con un nombre accesible propio de la fila («Registrar la asistencia del turno de Ana Ejemplo, 09:00»); la fila de un turno en cualquier otro estado (`pendiente_aprobacion`, `pendiente_sena`, `cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido`, `ausente`) MUST NOT tenerlo. El botón se muestra también en un turno que todavía no empezó: la API decide el momento (RN-AG-13). El botón SHALL abrir, al costado de la agenda, el panel «Registrar asistencia» con el resumen del turno tomado de la fila («Ana Ejemplo · Consulta / control» y «lunes 2 de noviembre de 2026, 09:00 – 09:30 · Reservado»), la pregunta «¿Cómo terminó el turno?» con dos opciones, «Atendido» y «Ausente», **ninguna marcada**, la ayuda «El horario queda libre para otro turno.», y los botones «Volver» y «Registrar asistencia». La fila del turno abierto SHALL marcarse como seleccionada (la misma marca que usan los otros paneles), y ninguna otra. Al abrir el panel el foco SHALL ir a la primera opción; al cerrarlo con «Volver» o «Cerrar», SHALL volver al botón «Asistencia» de la fila. «Registrar asistencia» SHALL mandar un solo `POST /turnos/{id}/estado` con `{"estado": "atendido"}` o `{"estado": "ausente"}` según la opción elegida; si responde `200`, el panel SHALL cerrarse, mostrarse «Asistencia registrada.» y pedirse de nuevo la agenda del mismo día, donde la fila se ve con la etiqueta del estado nuevo («Atendido» o «Ausente»), con «Historial» y sin «Asistencia», «Reprogramar» ni «Cancelar». Si esa recarga falla, el turno ya quedó marcado: se ve «Asistencia registrada.» junto al aviso de conexión de la agenda con «Reintentar», que vuelve a pedir ese mismo día, y no se repite el `POST`. Al abrir el panel no se pide nada a la API. La agenda SHALL mostrar un solo panel lateral a la vez entre «Nuevo turno», «Historial del turno», «Reprogramar turno», «Cancelar turno» y «Registrar asistencia», y cambiar de día SHALL cerrar «Registrar asistencia» sin mandar nada.

#### Scenario: ASI-5a Feliz - la recepcionista registra que el paciente fue atendido (US-014 CA-1, CA-2)

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre
- **WHEN** pulsa «Registrar la asistencia del turno de Ana Ejemplo, 09:00», elige «Atendido» y pulsa «Registrar asistencia»
- **THEN** al abrir ve «Registrar asistencia», «Ana Ejemplo · Consulta / control», «lunes 2 de noviembre de 2026, 09:00 – 09:30 · Reservado», «¿Cómo terminó el turno?» con «Atendido» y «Ausente» sin marcar y «El horario queda libre para otro turno.», y no se hizo ninguna petición nueva
- **AND** al abrir, el foco está en la opción «Atendido» y la fila de Ana Ejemplo está marcada como seleccionada, y ninguna otra
- **AND** al pulsar «Registrar asistencia» se manda un solo `POST /turnos/11/estado` con el cuerpo exacto `{"estado": "atendido"}`
- **AND** el panel se cierra, se ve «Asistencia registrada.», se pide `GET /turnos?fecha=2026-11-02` y la fila de Ana Ejemplo se ve de 09:00 a 09:30 con «Atendido», con «Historial» y sin «Asistencia», «Reprogramar» ni «Cancelar»
- **AND** este escenario se repite en la prueba en el navegador con un turno de hoy ya empezado, creado desde el formulario «Nuevo turno» de la agenda de la demo (o, si a esa hora no hay una franja ya empezada del horario de la demo, con el plan B del design, V4), y después se crea otro turno en el mismo horario desde «Nuevo turno» (el horario quedó libre)

#### Scenario: ASI-5b Borde - ausente, un turno confirmado y la recarga que falla

- **GIVEN** con sesión de la odontóloga, en la agenda del 2 de noviembre
- **WHEN** en una corrida registra el turno de Carla Inventada (`confirmado`) eligiendo «Ausente»; en otra registra el turno de Bruno Ficticio eligiendo «Atendido», el servidor falso responde `200` al `POST /turnos/12/estado` y la recarga `GET /turnos?fecha=2026-11-02` no responde (sin conexión)
- **THEN** en la primera se manda `{"estado": "ausente"}` y la fila de Carla se ve con «Ausente», sin «Asistencia», «Reprogramar» ni «Cancelar»
- **AND** en la segunda el panel se cierra, se ven «Asistencia registrada.» y el aviso de conexión de la agenda con «Reintentar», se mandó un solo `POST` y no se repite, y al pulsar «Reintentar» con la conexión de vuelta se pide de nuevo `GET /turnos?fecha=2026-11-02` y la fila de Bruno se ve con «Atendido»
- **AND** la primera corrida se repite en la prueba en el navegador contra la API de la demo

#### Scenario: ASI-5c Borde - un solo panel a la vez, el cambio de día lo cierra, el foco vuelve a la fila y los demás estados no tienen la acción

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, y en el servidor falso también un turno 14 de Bruno Ficticio `cancelado_paciente` de 12:00 a 12:30, un turno 15 `atendido` de 13:00 a 13:30, un turno 16 `ausente` de 14:00 a 14:30, un turno 17 `vencido` de 15:00 a 15:30, un turno 18 `pendiente_aprobacion` de 16:00 a 16:30, un turno 19 `pendiente_sena` de 17:00 a 17:30 y un turno 20 `cancelado_profesional` de 18:00 a 18:30
- **WHEN** en una corrida abre «Asistencia» del turno de Ana, después «Cancelar» del mismo turno y después otra vez «Asistencia»; en otra, con «Registrar asistencia» abierto pulsa «Día siguiente»; en otra, abre «Asistencia» del turno de Ana, elige «Ausente» y pulsa «Volver» (y, en otra, «Cerrar»); y en otra mira las filas de los turnos 11 a 20
- **THEN** en la primera se ve un solo panel lateral por vez: «Cancelar turno» cierra «Registrar asistencia» y viceversa
- **AND** en la segunda el panel «Registrar asistencia» desaparece, se ve la agenda del 3 de noviembre y no se manda ningún `POST`
- **AND** en la tercera el panel desaparece sin ninguna petición, el foco vuelve al botón «Registrar la asistencia del turno de Ana Ejemplo, 09:00», ninguna fila queda marcada como seleccionada y, al volver a abrirlo, ninguna opción está marcada
- **AND** en la cuarta las filas de los turnos 14 a 20 no tienen «Asistencia»; las de los turnos 18 y 19 (activos pero pendientes) tienen «Reprogramar», «Cancelar» e «Historial»; y las de los turnos 11, 12 y 13 tienen los cuatro botones, en el orden «Asistencia», «Reprogramar», «Cancelar», «Historial»
- **AND** la cuarta corrida solo se verifica contra el servidor falso (la demo no tiene turnos en esos estados salvo los que se marcan o cancelan en la prueba)

### Requirement: Los rechazos y lo que la pantalla frena se ven con su texto y la elección se conserva

Un rechazo de `POST /turnos/{id}/estado` SHALL mostrarse en el panel con un texto fijo según su tipo y su código, seguido de «El turno no cambió.», conservando la opción elegida y sin «Asistencia registrada.»:

| Respuesta | Texto |
|---|---|
| `409` con `RN-AG-12` | «Este turno ya no admite registrar la asistencia por su estado (RN-AG-12).» |
| `409` con `RN-AG-13` | «El turno todavía no empezó: la asistencia se registra desde su hora de inicio (RN-AG-13).» |
| `404` con `RN-GL-04` | «El turno ya no existe (RN-GL-04).» |
| `403` con `RN-AU-05` | «Tu usuario no tiene permiso para registrar la asistencia (RN-AU-05).» |
| sin conexión, `5xx`, un `422` o una respuesta de otra forma | el aviso de conexión de la agenda |

La pantalla SHALL frenar, sin pedir nada a la API, «Registrar asistencia» sin ninguna opción elegida («Elegí si el paciente fue atendido o estuvo ausente.»). Mientras espera la respuesta, «Registrar asistencia» SHALL estar deshabilitado, así que un doble clic manda un solo `POST`. «Volver» y «Cerrar» SHALL cerrar el panel sin pedir nada. Si la sesión se puede renovar, la petición se repite sin aviso; si no, se vuelve al inicio de sesión (como en la agenda).

#### Scenario: ASI-6a Error de negocio - un turno que ya no está reservado ni confirmado muestra RN-AG-12 y no cambia (US-014 CA-3)

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, con «Asistencia» del turno de Ana Ejemplo abierto, y en el servidor falso el turno 11 ya pasado a `atendido` por otra sesión después de cargar la agenda
- **WHEN** elige «Ausente» y pulsa «Registrar asistencia»
- **THEN** se manda un solo `POST /turnos/11/estado`, el servidor falso responde `409` con `codigos` `["RN-AG-12"]` y en el panel se ve «Este turno ya no admite registrar la asistencia por su estado (RN-AG-12).» y «El turno no cambió.»
- **AND** el panel sigue abierto con «Ausente» marcado y no se ve «Asistencia registrada.»
- **AND** en la prueba en el navegador se repite registrando el mismo turno de la demo desde dos pestañas: la segunda ve este texto

#### Scenario: ASI-6b Error de negocio - un turno que todavía no empezó muestra RN-AG-13 y no cambia (US-014 CA-6)

- **GIVEN** con sesión de la recepcionista, en la agenda del 2 de noviembre, con «Asistencia» del turno de Carla Inventada abierto, y el servidor falso fijado para responder `409` con `codigos` `["RN-AG-13"]`
- **WHEN** elige «Atendido» y pulsa «Registrar asistencia»
- **THEN** se manda un solo `POST /turnos/13/estado` y en el panel se ve «El turno todavía no empezó: la asistencia se registra desde su hora de inicio (RN-AG-13).» y «El turno no cambió.»
- **AND** el panel sigue abierto con «Atendido» marcado y no se ve «Asistencia registrada.»
- **AND** en la prueba en el navegador se repite con un turno de la demo de un día futuro, contra la API real

#### Scenario: ASI-6c Borde - lo que la pantalla frena sin pedir nada, los demás rechazos, el doble clic, la conexión y la sesión

- **GIVEN** con sesión de la recepcionista (o del dueño, en la corrida del `403`), en la agenda del 2 de noviembre, con «Asistencia» del turno de Ana abierto
- **WHEN** en una corrida por caso: pulsa «Registrar asistencia» sin elegir ninguna opción; elige «Atendido» y el servidor falso contesta `404` `RN-GL-04`; el dueño elige «Atendido» y el servidor falso contesta `403` `RN-AU-05`; elige una opción y pulsa «Registrar asistencia» dos veces con la respuesta retenida; elige una opción y la API no responde (sin conexión); elige una opción y el servidor falso contesta `500`; elige una opción y el servidor falso contesta `422` (un cuerpo de otra forma); y elige una opción con el access token vencido y, en otra, con la sesión irrenovable
- **THEN** la primera muestra «Elegí si el paciente fue atendido o estuvo ausente.» y no manda ningún `POST`
- **AND** el `404` muestra «El turno ya no existe (RN-GL-04).» y el `403` «Tu usuario no tiene permiso para registrar la asistencia (RN-AU-05).», cada uno seguido de «El turno no cambió.» y con la opción elegida conservada, y el `403` no hace ningún `POST /auth/refresh`
- **AND** el dueño ve «Asistencia» en las filas `reservado` y `confirmado` (ocultar acciones según el rol queda para un change posterior, D312)
- **AND** en la del doble clic se manda un solo `POST` y «Registrar asistencia» está deshabilitado mientras espera
- **AND** sin conexión, con el `500` y con el `422` se ve, en cada corrida, el aviso de conexión de la agenda seguido de «El turno no cambió.», la opción elegida se conserva y no se ve «Asistencia registrada.»
- **AND** con el access token vencido se hace un solo `POST /auth/refresh`, se repite el `POST` y se ve «Asistencia registrada.»; con la sesión irrenovable se vuelve al inicio de sesión
- **AND** la corrida sin opción y la del dueño se repiten en la prueba en el navegador contra la API de la demo
