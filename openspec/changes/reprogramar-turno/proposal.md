# Proposal: reprogramar-turno

Change **C-16** de `CHANGES.md` (US-012, fase 4, orden 4). Gobernanza **MEDIO**: se implementa con checkpoints y las decisiones no obvias se le presentan al autor. Las preguntas **Q1 a Q11** del design están **cerradas**: el autor aceptó el 2026-10-29 todas las recomendaciones (con la duración en «Antes:» y «Después:» del historial, Q9) y todos los hallazgos del informe de `revisor-de-escenarios` (H1 a H11), registrados como **D332 a D342** en `knowledge-base/10_preguntas_abiertas.md`. Depende de C-03 (historial, archivado el 2026-10-14) y de C-14 (agenda, archivado el 2026-10-28); usa además lo que dejaron C-07 (protección), C-12 (horario), C-13 (bloqueos) y C-15 (panel del historial).

## Why

Hoy un turno mal ubicado solo se arregla creando otro, porque no hay forma de moverlo ni de cambiarle la duración: el hueco viejo queda ocupado o hay que pedir a la base que lo borre, y el historial pierde el hilo. US-012 es la primera acción sobre un turno de la agenda (D112, «sin pantalla nueva») y la necesitan el consultorio en el día a día y los bloqueos de C-13, que listan los turnos afectados «para que el odontólogo los reprograme o cancele» (D83).

## What Changes

- **Ruta nueva `PATCH /turnos/{id}`** (la de `02`, fila Turnos): mueve el turno a otro `inicio`, le cambia la duración o las dos cosas, sobre **el mismo turno** (DD-05): mismo id, paciente, prestación, profesional, sillón y estado; `fin` se recalcula (RN-AG-02). Cuerpo con `inicio` y `duracion_minutos`, los dos opcionales (D333). Responde `200` con el turno; una petición que no cambia nada responde `200` sin evaluar reglas ni registrar evento (D333).
  - **Se valida como un turno nuevo, excluyéndose a sí mismo** (US-012 CA-1, RN-AG-10b): `inicio` en UTC (RN-GL-01), duración mayor que 0, múltiplo de la constante de 5 minutos y de hasta 1440 minutos (RN-AG-01, US-012 CA-4, D333), sin cruzar la medianoche del consultorio (RN-AG-10d), dentro del horario (RN-AG-04, con `exigir_dentro_del_horario` de C-12), sin bloqueos (RN-AG-04b, con `exigir_sin_bloqueos` de C-13) y sin solaparse con otro turno activo del profesional o del sillón (RN-AG-05, RN-AG-08): reprogramar sobre otro turno activo responde `409` con los dos códigos y el turno no cambia (**REP-1**).
  - **Solo un turno activo se reprograma** (D334): uno cancelado, vencido, atendido o ausente se rechaza con `409` y un código nuevo, **`RN-AG-18`**, específico de la reprogramación (`RN-AG-12` sigue siendo el código genérico de transición de estado); el orden de evaluación queda en `05` RN-GL-02 (D335).
  - **Evento `reprogramado`** en el historial, en la misma transacción, con el horario y la duración de antes y de después, quién y cuándo (US-012 CA-2, RN-AG-11, DD-05; D338). Se registra solo cuando algo cambia: un rechazo o una petición sin cambios no registran nada.
  - **Permiso nuevo `turnos.reprogramar`** para el odontólogo y la recepcionista (matriz de `03`, fila Turnos: «U» para los dos, «R» para el dueño); el dueño y un usuario sin roles reciben `403` `RN-AU-05` (D336).
  - **Concurrencia**: el turno se lee con bloqueo de fila y después se bloquean el profesional y el sillón como en `crear_turno` (D157); la restricción de exclusión de PostgreSQL sigue como última defensa, con el mismo reintento; prueba solo en el perfil `postgres` (D337).
- **Acción «Reprogramar» en la agenda** (C-14), junto a «Historial» (C-15), solo en los turnos activos: abre un panel lateral «Reprogramar turno» con el resumen del turno, fecha, hora y duración cargadas con los valores actuales, «Termina a las…», y muestra cada rechazo con su código y «El turno no cambió.» (D339). Un solo panel lateral a la vez entre «Nuevo turno», «Historial» y «Reprogramar».
- **El historial muestra el evento `reprogramado`** con su etiqueta, «Turno reprogramado», y el antes y el después con su día, sus horas y su duración (D340; lo había dejado previsto C-15, design G5 de `panel-historial-de-turno`).
- **Pantallas de Stitch** (D234), generadas en este propose con «Clinical Ops»: reprogramar con error de escritorio `projects/14200813501064679723/screens/291535f17cc64edc8c79e1ce09977c42` y angosta `projects/14200813501064679723/screens/6557792ea9754df08b59484784462c27`; qué se toma y qué se rechaza, en el design.
- **Demo y README**: sin datos nuevos de seed; recorrido de `PATCH /turnos/{id}` en «Probar desde Swagger» y de la acción en «Panel (interfaz)», tablas escenario → test y límites conocidos.

Sin migraciones (D337), sin dependencias nuevas y sin variables de entorno nuevas. No hay **BREAKING**: `POST /turnos`, `GET /turnos` y `GET /turnos/{id}/historial` no cambian su contrato; el historial suma un tipo de evento, que la pantalla de C-15 ya mostraba sin romperse.

### Escenarios

Cubre los mínimos de la entrada C-16 de `CHANGES.md`: **US-012 CA-1**, **US-012 CA-2**, **US-012 CA-4** y **REP-1**. El spec de la API los detalla en **15 escenarios** y el de la pantalla en **8**, y el delta de `pantalla-de-historial` modifica dos (`HIS-2b` y `HIS-2f`; repite sin cambios `HIS-2a` y `HIS-2c`, porque un MODIFIED copia el requisito completo): **25 escenarios nuevos o cambiados**, por encima del «3 a 6» por capability de `config.yaml`, como C-14 y C-50; excepción aceptada por el autor y limitada a C-16 (**D341**). Cada escenario tiene un ID propio (`REP-1a`…) que lleva el nombre de su test.

| ID | Qué verifica | Dónde corre |
|---|---|---|
| REP-1 | Mover un turno: el feliz, la exclusión de sí mismo (RN-AG-10b), **REP-1** (otro turno activo: `409` con `RN-AG-05` y `RN-AG-08` y el turno no cambia), las reglas de un turno nuevo (RN-AG-04, RN-AG-04b, RN-AG-10d) y dos reprogramaciones simultáneas (US-012 CA-1) | pytest (+ `postgres`) + navegador |
| REP-2 | El evento `reprogramado` con antes y después, actor y momento; un rechazo no registra nada (US-012 CA-2) | pytest |
| REP-3 | Cambiar la duración: `fin` recalculado; `RN-AG-01` para una duración inválida o mayor que 1440, junto con `RN-GL-01` (US-012 CA-4) | pytest |
| REP-4 | Acceso (`401`, `403` antes de validar), turno inexistente o de otro consultorio (`404`), formato (`422`) y la petición que no cambia nada | pytest |
| REP-5 | Solo los turnos activos se reprograman (`RN-AG-18`); un terminal sin cambios responde `200` sin evento | pytest |
| REP-6 | La acción en la agenda: reprogramar, también a otro día y solo la duración; el foco y la fila seleccionada; un panel a la vez; sin la acción en los turnos no activos; la recarga que falla después del `200` | Vitest + navegador |
| REP-7 | Los rechazos con su código y «El turno no cambió.», lo que la pantalla frena sin pedir nada, la conexión y la sesión | Vitest + navegador |
| HIS-2b y HIS-2f (modificados) | El historial muestra «Turno reprogramado» con su antes y después (día, horas y duración); un solo panel entre los tres | Vitest + navegador |

**Quedan fuera** de US-012: **CA-3** (conservar la seña) se completa con C-40 (US-050), cuando exista la seña; hasta entonces el turno no tiene seña que perder, y como reprogramar modifica el mismo turno (DD-05), la seña que cuelgue de él lo va a seguir.

## Fuera de alcance

- **La seña** (US-012 CA-3, RN-TD-04): no existe hasta C-35 a C-40. Tampoco se persiste ningún vencimiento de seña antes de reprogramar (RN-AG-10, RN-GL-05 (a)): en la v1 no hay `pendiente_sena` con plazo; el vencimiento efectivo llega con el change de la seña (C-37).
- **El tope de 1440 minutos en las prestaciones**: la duración de una prestación (C-04, archivado) sigue sin tope; queda como límite conocido en `05` y `10` para un change futuro (D333).
- **La reprogramación por el paciente** con el link de gestión (C-30): sus reglas propias (RN-TD-01, RN-TD-02, RN-TD-03, RN-TD-08, RN-TD-11) no se aplican al panel (D65).
- **La granularidad configurable** (C-22): se usa la constante de 5 minutos (D99).
- **Cambiar paciente, prestación, profesional o sillón** de un turno: US-012 solo mueve el horario y la duración; con un solo profesional y un solo sillón activos no hay a dónde moverlo (Fase 2).
- **Un motivo** escrito por quien reprograma: el evento lleva `motivo` vacío (D338).
- **Avisar al paciente** (mensaje `wa.me`, C-31) y **ofrecer el hueco liberado** a la lista de espera (C-37, Flujo 6): llegan con sus changes.
- **Ocultar acciones según el rol** (D312): «Reprogramar» se ve para los tres roles y el dueño recibe el `403` `RN-AU-05` de la API.
- **Arrastrar y soltar** en la agenda, ni una vista de huecos libres: la reprogramación es un formulario.
- **Corregir el estado `cancelado_consultorio` del frontend** (la API y la KB dicen `cancelado_profesional`): hallazgo de este propose; lo corrige C-17, el change que crea esos turnos, y su entrada de `CHANGES.md` lo dice (D342).

## Capabilities

### New Capabilities

- `reprogramacion-de-turnos`: el contrato de la API para reprogramar un turno: `PATCH /turnos/{id}`, qué se puede cambiar, cómo se valida (como un turno nuevo excluyéndose a sí mismo), qué estados lo admiten, el evento `reprogramado`, quién puede y los rechazos `401`, `403`, `404`, `409` y `422` (US-012 CA-1, CA-2 y CA-4; REP-1; RN-AG-01, RN-AG-02, RN-AG-04, RN-AG-04b, RN-AG-05, RN-AG-08, RN-AG-10b, RN-AG-10c, RN-AG-10d, RN-AG-11, RN-AG-18, RN-GL-01, RN-GL-02, RN-GL-04, RN-AU-05).
- `pantalla-de-reprogramacion`: la acción «Reprogramar» de la agenda y su panel: qué muestra, qué manda, cómo se ven los rechazos con su código y cómo convive con «Nuevo turno» e «Historial» (US-012 CA-1 y CA-4; REP-1).

**Dos capabilities nuevas** se apartan de «una sola capability» (`config.yaml`, regla dura 12): es el mismo corte API / navegador que el autor aceptó como excepción en D241, D255, D271, D290, D304 y D315; aceptada por el autor como excepción limitada a C-16 (**D332**).

### Modified Capabilities

- `pantalla-de-historial`: el requisito «El historial de un turno se abre desde la agenda y es de solo lectura» suma la etiqueta del evento `reprogramado` («Turno reprogramado» con el antes y el después, con su duración) y su escenario `HIS-2b` cambia el ejemplo del tipo desconocido (D332, D340); el requisito «Un solo panel lateral a la vez…» nombra los tres paneles y su escenario `HIS-2f` suma la corrida con «Reprogramar» (D339). C-15 lo había dejado previsto: «el change que agregue el tipo le pone su etiqueta y su escenario» (design G5).

Se revisaron y **no cambian**:
- `creacion-de-turnos`: `POST /turnos` no cambia; las reglas se reusan sin modificar sus requisitos.
- `historial-de-turnos`: sus requisitos (registrar `creado`, consultar, `404`, solo lectura, la base impide modificar) siguen valiendo; el evento `reprogramado` se especifica donde nace, en `reprogramacion-de-turnos`, como `creado` se especificó con el alta (D332).
- `consulta-de-turnos` y `pantalla-de-agenda`: la agenda muestra el turno movido sin cambiar su contrato; el botón se suma en la columna «Acciones» que ya agregó C-15.
- `proteccion-del-panel`: su guard exige el token a la ruta nueva; el permiso `turnos.reprogramar` queda en `reprogramacion-de-turnos`, como hicieron C-09 a C-14.
- `horario-recurrente` y `bloqueos-puntuales`: las reglas se reusan tal cual.

## Impact

- **Backend**: `domain/turnos/reprogramacion.py` (nuevo, puro: qué estados se reprograman y el evento `reprogramado`); `domain/turnos/eventos.py` (`TipoEvento.REPROGRAMADO`); `domain/agenda/solapamiento.py` (excluir al propio turno, RN-AG-10b, sin cambiar lo que hace hoy); `domain/errors.py` (`TurnoNoReprogramable`, `RN-AG-18`); `domain/acceso/roles.py` (`Permiso.TURNOS_REPROGRAMAR`); `application/reprogramar_turno.py` (nuevo); puerto y repositorio de la agenda (leer el turno con bloqueo de fila y guardar el horario nuevo, con la traducción de la violación de exclusión); `api/esquemas.py` (`ReprogramarTurnoEntrada`); `api/errores.py` (`RN-AG-18` → `409`); `api/routers/turnos.py` (`PATCH`). Tests de unidad, integración, API y del perfil `postgres`; los contadores de la matriz de permisos y de rutas protegidas suben (solo su número).
- **Frontend**: `features/agenda/` (`PanelReprogramar.tsx`, `reprogramarTurno` en `apiAgenda.ts`, textos en `mensajes.ts`, el botón en `TablaDeTurnos.tsx`, el estado `panel` de `PaginaAgenda.tsx`); `features/historial/mensajes.ts` (la etiqueta y el detalle de `reprogramado`); `test/servidorFalso.ts` (`PATCH /api/turnos/{id}`); `panel.css` y, si hace falta, `tokens.css`.
- **Esquema y migraciones**: sin cambios (`turno` y `evento_turno` ya existen; `evento_turno.tipo` no tiene `CHECK`).
- **Dependencias y variables de entorno**: ninguna nueva.
- **Documentación**: `README.md`; evidencia de Stitch en `docs/skills-mcp/evidencias/sesion-nueva/stitch-reprogramar.md` y `stitch-reprogramar-pantalla/`. Las respuestas a Q1 a Q11 quedaron en `knowledge-base/10_preguntas_abiertas.md` (D332 a D342) con el `/opsx:update` del 2026-10-29, que además sumó `RN-AG-18`, el tope de 1440 de RN-AG-01 y el orden de `PATCH /turnos/{id}` en RN-GL-02 a `05`, `turnos.reprogramar` a `03`, la precisión del `PATCH` a la fila Turnos de `02`, el `409` de `RN-AG-18` al mapeo de `08` y la nota de US-012 en `06`.
- **`CHANGES.md`**: C-16 pasa a `[~]` en curso con este propose; el `/opsx:update` suma D332 a D342 a su «Leer antes» y la corrección de `cancelado_consultorio` al «Alcance — dentro» de C-17 (D342).
- **Tamaño**: 32 tareas en 12 grupos para 25 escenarios nuevos o cambiados (15 + 8 + 2 modificados), con RED, GREEN, TRIANGULATE y REFACTOR separados; por encima de las «alrededor de 20» tareas de `config.yaml`: excepción aceptada por el autor, limitada a C-16 (D341).
