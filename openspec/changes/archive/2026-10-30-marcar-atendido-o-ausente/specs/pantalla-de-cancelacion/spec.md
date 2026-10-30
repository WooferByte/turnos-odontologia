## Purpose

Delta de C-18 (`marcar-atendido-o-ausente`) sobre `pantalla-de-cancelacion` (hallazgo H1 de `revisor-de-escenarios`, D354): con la acción «Asistencia» de `pantalla-de-asistencia`, las filas `reservado` y `confirmado` de la agenda pasan a tener cuatro botones y la agenda, cinco paneles laterales. Un MODIFIED repite el requisito completo: `CAN-4a` y `CAN-4b` son copia literal del spec vigente; cambia `CAN-4c` (los turnos 11 a 13 tienen los cuatro botones, en el orden «Asistencia», «Reprogramar», «Cancelar», «Historial», y los no activos tampoco tienen «Asistencia»), y en el requisito cambia solo la frase de los paneles, que nombra los cinco. «Cancelar» sigue entre «Reprogramar» e «Historial». El requisito «Los rechazos y lo que la pantalla frena…» no cambia. Las convenciones de los escenarios son las del spec vigente.

## MODIFIED Requirements

### Requirement: Un turno activo se cancela desde su fila de la agenda indicando quién lo pidió

Cada fila de la agenda (`/panel/agenda`) de un turno **activo** (`pendiente_aprobacion`, `pendiente_sena`, `reservado`, `confirmado`) SHALL tener, en la columna «Acciones», entre «Reprogramar» e «Historial», un botón «Cancelar» con un nombre accesible propio de la fila («Cancelar el turno de Ana Ejemplo, 09:00»); la fila de un turno en estado terminal (`cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido`, `ausente`) MUST NOT tenerlo. El botón SHALL abrir, al costado de la agenda, el panel «Cancelar turno» con el resumen del turno tomado de la fila («Ana Ejemplo · Consulta / control» y «lunes 2 de noviembre de 2026, 09:00 – 09:30 · Reservado»), la pregunta «¿Quién pidió la cancelación?» con dos opciones, «El paciente» y «El consultorio», **ninguna marcada**, la ayuda «El horario queda libre para otro turno.», y los botones «Volver» y «Cancelar turno». La fila del turno abierto SHALL marcarse como seleccionada (la misma marca que usan el historial y «Reprogramar»), y ninguna otra. Al abrir el panel el foco SHALL ir a la primera opción; al cerrarlo con «Volver» o «Cerrar», SHALL volver al botón «Cancelar» de la fila. «Cancelar turno» SHALL mandar un solo `POST /turnos/{id}/cancelar` con `{"estado": "cancelado_paciente"}` si se eligió «El paciente» o `{"estado": "cancelado_profesional"}` si se eligió «El consultorio»; si responde `200`, el panel SHALL cerrarse, mostrarse «Turno cancelado.» y pedirse de nuevo la agenda del mismo día, donde la fila se ve con la etiqueta del estado nuevo, con «Historial» y sin «Reprogramar» ni «Cancelar». Si esa recarga falla, el turno ya quedó cancelado: se ve «Turno cancelado.» junto al aviso de conexión de la agenda con «Reintentar», que vuelve a pedir ese mismo día, y no se repite el `POST`. Al abrir el panel no se pide nada a la API. La agenda SHALL mostrar un solo panel lateral a la vez entre «Nuevo turno», «Historial del turno», «Reprogramar turno», «Cancelar turno» y «Registrar asistencia» (C-18, D363), y cambiar de día SHALL cerrar «Cancelar turno» sin mandar nada.

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
- **AND** en la cuarta las filas de los turnos 14 a 17 y 20 (no activos) tienen «Historial» y no tienen «Asistencia», «Reprogramar» ni «Cancelar»; la del turno 20 se ve con «Cancelado por el consultorio»; y las de los turnos 11, 12 y 13 (activos, `reservado` o `confirmado`) tienen los cuatro botones, en el orden «Asistencia», «Reprogramar», «Cancelar», «Historial» (desde C-18, D354)
- **AND** la cuarta corrida solo se verifica contra el servidor falso (la demo no tiene turnos en esos estados salvo los cancelados)
