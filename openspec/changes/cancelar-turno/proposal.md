# Proposal: cancelar-turno

Change **C-17** de `CHANGES.md` (US-013, fase 4, orden 4). Gobernanza **MEDIO**: se implementa con checkpoints y las decisiones no obvias se le presentan al autor. Las preguntas **Q1 a Q11** del design están **cerradas**: el autor aceptó todas las recomendaciones el 2026-10-29 y quedaron como **D343 a D353** en `knowledge-base/10_preguntas_abiertas.md`, junto con los hallazgos H1 a H9 de `revisor-de-escenarios`. Depende de C-03 (historial, archivado el 2026-10-14) y de C-14 (agenda, archivado el 2026-10-28); usa además lo que dejaron C-07 (protección), C-15 (panel del historial) y C-16 (reprogramar: bloqueo de fila del turno, un panel lateral a la vez y la corrección pendiente de `cancelado_consultorio`, D342).

## Why

Hoy un turno que no se va a atender queda ocupando su horario para siempre: no hay forma de cancelarlo, así que el hueco no se puede volver a dar y la agenda muestra como activos turnos que ya no existen. US-013 es la segunda acción sobre un turno de la agenda (D112, «sin pantalla nueva») y abre el camino de la lista de espera (C-36), la gestión por link (C-29) y la seña (C-41), que dependen de C-17.

## What Changes

- **Ruta nueva `POST /turnos/{id}/cancelar`** (la de `02`, fila Turnos): pasa un turno activo a `cancelado_paciente` o a `cancelado_profesional` según quién lo pidió (US-013 CA-1). Cuerpo `{"estado": "cancelado_paciente" | "cancelado_profesional"}`, obligatorio (D344). Responde `200` con el turno, con la misma forma que `201` de `POST /turnos`; el horario, el paciente, la prestación, el profesional y el sillón no cambian.
  - **El horario queda libre** (US-013 CA-2, parte de liberar): un turno cancelado deja de contar para el solapamiento (RN-AG-10), así que el mismo hueco se puede volver a dar con `POST /turnos` o con `PATCH /turnos/{id}`. La restricción de exclusión de PostgreSQL ya cubre solo los estados activos (migración `0002`), así que no hay migración.
  - **Solo un turno activo se cancela** (tabla de transiciones de `04`, RN-AG-12): uno en estado terminal (cancelado, vencido, atendido o ausente) se rechaza con `409` y `RN-AG-12` y no cambia (**CAN-1**), también si se pide la misma cancelación otra vez (D345); se mira el estado almacenado del turno. El panel cancela **en cualquier momento** (RN-TD-03, D65), también un turno ya pasado.
  - **Evento `cancelado`** en el historial, en la misma transacción, con el estado de antes y el de después, quién y cuándo (RN-AG-11; D349). Un rechazo no registra nada.
  - **Permiso nuevo `turnos.cancelar`** para el odontólogo y la recepcionista (matriz de `03`, fila Turnos: «CRUD» y «CRU + cancelar», el dueño «R»); el dueño y un usuario sin roles reciben `403` `RN-AU-05` (D347).
  - **Concurrencia**: el turno se lee con bloqueo de fila, como al reprogramar (D337): dos cancelaciones simultáneas del mismo turno dejan una sola aceptada y un solo evento; una cancelación y una reprogramación simultáneas se serializan (D348). Prueba solo en el perfil `postgres`.
- **Acción «Cancelar» en la agenda** (C-14), entre «Reprogramar» (C-16) e «Historial» (C-15), solo en los turnos activos: abre un panel lateral «Cancelar turno» con el resumen del turno y la pregunta «¿Quién pidió la cancelación?» («El paciente» o «El consultorio», sin opción marcada), y muestra cada rechazo con su código y «El turno no cambió.» (D350). Un solo panel lateral a la vez entre los cuatro.
- **Corrección de `cancelado_consultorio`** (D342): el frontend usa el nombre de estado de la API, `cancelado_profesional`, en `apiAgenda.ts`, `mensajes.ts` y el test `AGE-4c` de `PaginaAgenda`; la etiqueta sigue siendo «Cancelado por el consultorio» (D351), así que el spec de `pantalla-de-agenda` no cambia.
- **El historial muestra el evento `cancelado`** con su etiqueta, «Turno cancelado», y el cambio de estado con las etiquetas de la agenda («Estado: Reservado → Cancelado por el paciente»; D352).
- **Pantallas de Stitch** (D234), generadas en este propose con «Clinical Ops»: cancelar con error de escritorio `projects/14200813501064679723/screens/e382a7e3a92f4cb18df0f6e7e9d677ca` y angosta `projects/14200813501064679723/screens/fcd2a428cdc44c5689b398cc8bf1936f`; qué se toma y qué se rechaza, en el design.
- **Demo y README**: sin datos nuevos de seed; recorrido de `POST /turnos/{id}/cancelar` en «Probar desde Swagger» y de la acción en «Panel (interfaz)», tablas escenario → test y límites conocidos.

Sin migraciones, sin dependencias nuevas y sin variables de entorno nuevas. No hay **BREAKING**: `POST /turnos`, `GET /turnos`, `PATCH /turnos/{id}` y `GET /turnos/{id}/historial` no cambian su contrato; el historial suma un tipo de evento, que la pantalla de C-15 ya mostraba sin romperse como «Cambio registrado (cancelado)».

### Escenarios

Cubre los mínimos de la entrada C-17 de `CHANGES.md`: **US-013 CA-1**, **US-013 CA-2** (la parte de liberar el horario) y **CAN-1**. El spec de la API los detalla en **9 escenarios** y el de la pantalla en **5**, y el delta de `pantalla-de-historial` modifica dos (`HIS-2b` y `HIS-2f`; repite sin cambios `HIS-2a` y `HIS-2c`, porque un MODIFIED copia el requisito completo): **16 escenarios nuevos o cambiados**, por encima del «3 a 6» por capability de `config.yaml` en la API; excepción limitada a C-17 (D353). Cada escenario tiene un ID propio (`CAN-1a`…) que lleva el nombre de su test.

| ID | Qué verifica | Dónde corre |
|---|---|---|
| CAN-1 | Cancelar: el feliz con cada valor (US-013 CA-1), el horario que queda libre y los cuatro estados activos (US-013 CA-2), **CAN-1** (un turno terminal: `409` `RN-AG-12` y no cambia) y dos cancelaciones simultáneas | pytest (+ `postgres`) + navegador |
| CAN-2 | El evento `cancelado` con el estado de antes y de después, actor y momento; un rechazo no registra nada y, si el evento falla, el turno no queda cancelado (RN-AG-11) | pytest |
| CAN-3 | Acceso (`401`, `403` antes de validar), turno inexistente o de otro consultorio (`404`) y formato (`422`) | pytest |
| CAN-4 | La acción en la agenda: cancelar por el paciente y por el consultorio, la fila que queda cancelada y sin acciones de cambio, la recarga que falla después del `200`, un panel a la vez y el foco | Vitest + navegador |
| CAN-5 | Los rechazos con su código y «El turno no cambió.», lo que la pantalla frena sin pedir nada, la conexión y la sesión | Vitest + navegador |
| HIS-2b y HIS-2f (modificados) | El historial muestra «Turno cancelado» con el cambio de estado; un solo panel entre los cuatro | Vitest + navegador |

**Quedan fuera** de US-013: la segunda mitad de **CA-2** (disparar la búsqueda en la lista de espera) se completa con C-36 (US-040, RN-LE-01), y **CA-3** (marcar la seña para devolución si cancela el odontólogo, RN-SP-05) con C-41 (US-051), cuando exista la seña.

## Fuera de alcance

- **Ofrecer el hueco a la lista de espera** (US-013 CA-2, RN-LE-01, Flujo 6): llega con C-36; la cancelación no deja ninguna marca para eso (lo detecta el change que dispare la oferta).
- **La seña** (US-013 CA-3, RN-SP-04, RN-SP-05): no existe hasta C-35 a C-41; tampoco se distingue una cancelación del paciente «fuera de plazo» (RN-TD-03), porque la ventana configurable llega con C-22 y su efecto es sobre la seña.
- **La cancelación por el paciente** con el link de gestión (C-29), con su plazo y `RN-TD-11`.
- **Rechazar un turno `pendiente_aprobacion`** (`POST /turnos/{id}/rechazar`, RN-TD-05, C-27): es otra acción, aunque también termine en `cancelado_profesional`.
- **Un motivo** escrito por quien cancela: el evento lleva `motivo` vacío y el cuerpo no lo acepta (D344).
- **Avisar al paciente** (mensaje `wa.me`, C-31).
- **Deshacer una cancelación**: un estado terminal no tiene salida (`04`); el turno se vuelve a dar con «Nuevo turno».
- **Ocultar acciones según el rol** (D312): «Cancelar» se ve para los tres roles y el dueño recibe el `403` `RN-AU-05` de la API.
- **Cambiar la etiqueta** «Cancelado por el consultorio» (D351).
- **El estado efectivo** de un `pendiente_sena` con la seña vencida: llega con la seña (C-38 a C-40); hasta entonces se cancela por el estado almacenado (D317, D345).

## Capabilities

### New Capabilities

- `cancelacion-de-turnos`: el contrato de la API para cancelar un turno desde el panel: `POST /turnos/{id}/cancelar`, quién lo pidió, qué estados lo admiten, el horario que queda libre, el evento `cancelado`, quién puede y los rechazos `401`, `403`, `404`, `409` y `422` (US-013 CA-1 y CA-2; CAN-1; RN-AG-10, RN-AG-11, RN-AG-12, RN-TD-03, RN-GL-02, RN-GL-04, RN-AU-05).
- `pantalla-de-cancelacion`: la acción «Cancelar» de la agenda y su panel: qué muestra, qué manda, cómo se ven el resultado y cada rechazo con su código, y cómo convive con «Nuevo turno», «Reprogramar» e «Historial» (US-013 CA-1 y CA-2; CAN-1).

**Dos capabilities nuevas** se apartan de «una sola capability» (`config.yaml`, regla dura 12): es el mismo corte API / navegador que el autor aceptó en D241, D255, D271, D290, D304, D315 y D332; excepción limitada a C-17 decidida por el autor (D343).

### Modified Capabilities

- `pantalla-de-historial`: el requisito «El historial de un turno se abre desde la agenda y es de solo lectura» suma la etiqueta del evento `cancelado` («Turno cancelado» con el cambio de estado) y su escenario `HIS-2b` suma un `cancelado` (D352); el requisito «Un solo panel lateral a la vez…» nombra los cuatro paneles y su escenario `HIS-2f` suma la corrida con «Cancelar» (D350).

Se revisaron y **no cambian**:
- `creacion-de-turnos` y `reprogramacion-de-turnos`: ya cuentan solo los turnos activos (RN-AG-10) y ya rechazan los terminales (`RN-AG-18`); un turno cancelado se comporta como cualquier terminal.
- `historial-de-turnos`: sus requisitos siguen valiendo; el evento `cancelado` se especifica donde nace, en `cancelacion-de-turnos`, como `reprogramado` (D332).
- `consulta-de-turnos`: lista todos los estados con el almacenado (D317).
- `pantalla-de-agenda`: `AGE-4c` pide la etiqueta «Cancelado por el consultorio», que no cambia (D351); la corrección de `cancelado_consultorio` es de implementación (D342).
- `pantalla-de-reprogramacion`: `REP-6c` sigue igual; la fila `cancelado_profesional` sin «Reprogramar» se prueba en `CAN-4c`.
- `proteccion-del-panel`: su guard exige el token a la ruta nueva; el permiso `turnos.cancelar` queda en `cancelacion-de-turnos`.

## Impact

- **Backend**: `domain/turnos/cancelacion.py` (nuevo, puro: qué estados se cancelan y hacia cuáles); `domain/turnos/eventos.py` (`TipoEvento.CANCELADO`, `evento_cancelado`); `domain/errors.py` (`TransicionInvalida`, `RN-AG-12`); `domain/acceso/roles.py` (`Permiso.TURNOS_CANCELAR`); `application/cancelar_turno.py` (nuevo); puerto y repositorio de la agenda (el bloqueo de fila del turno, que hoy se llama `turno_para_reprogramar`, y `cambiar_estado`); `api/esquemas.py` (`CancelarTurnoEntrada`); `api/errores.py` (`RN-AG-12` → `409`); `api/routers/turnos.py` (`POST /turnos/{id}/cancelar`). Tests de unidad, integración, API y del perfil `postgres`; los contadores de la matriz de permisos (17 → 18) y de rutas protegidas suben (solo su número).
- **Frontend**: `features/agenda/` (`PanelCancelar.tsx`, `cancelarTurno` en `apiAgenda.ts`, textos en `mensajes.ts`, el botón en `TablaDeTurnos.tsx`, el estado `panel` de `PaginaAgenda.tsx`, y `cancelado_consultorio` → `cancelado_profesional`); `features/historial/mensajes.ts` (la etiqueta y el detalle de `cancelado`); `test/servidorFalso.ts` (`POST /api/turnos/{id}/cancelar`); `panel.css` y, si hace falta, `tokens.css`.
- **Esquema y migraciones**: sin cambios (`turno.estado` no tiene `CHECK`; la exclusión de `0002` ya filtra los activos; `evento_turno.tipo` no tiene `CHECK`).
- **Dependencias y variables de entorno**: ninguna nueva.
- **Documentación**: `README.md`; evidencia de Stitch en `docs/skills-mcp/evidencias/sesion-nueva/stitch-cancelar.md` y `stitch-cancelar-pantalla/`. El `/opsx:update` del 2026-10-29 registró D343 a D353 en `10` y escribió el `409` de `RN-AG-12` en `05` y en el mapeo de `08`, el orden de `POST /turnos/{id}/cancelar` en RN-GL-02 de `05`, `turnos.cancelar` en `03`, el cuerpo en la fila Turnos de `02` y la nota de US-013 en `06`; `CLAUDE.md` y `AGENTS.md` resumen D343 a D353.
- **`CHANGES.md`**: C-17 pasa a `[~]` en curso con este propose.
- **Tamaño**: 32 tareas en 12 grupos para 16 escenarios nuevos o cambiados (9 + 5 + 2 modificados), con RED, GREEN, TRIANGULATE y REFACTOR separados; por encima de las «alrededor de 20» tareas de `config.yaml`: excepción limitada a C-17 (D353).
