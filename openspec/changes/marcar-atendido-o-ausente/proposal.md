# Proposal: marcar-atendido-o-ausente

Change **C-18** de `CHANGES.md` (US-014, fase 4, orden 4). Gobernanza **MEDIO**: se implementa con checkpoints y las decisiones no obvias se le presentan al autor. Depende de C-03 (historial, archivado el 2026-10-14) y de C-14 (agenda, archivado el 2026-10-28); usa además lo que dejaron C-07 (protección), C-15 (panel del historial), C-16 (bloqueo de fila del turno) y C-17 (cancelar: `RN-AG-12` con `409`, `turno_para_cambiar`, `cambiar_estado`, el panel con opciones sin marcar y el delta del historial). Las preguntas **Q1 a Q12** del design están **cerradas**: el autor aceptó el 2026-10-30 las doce recomendaciones («Sí, todo») y los hallazgos H1 a H6 de `revisor-de-escenarios`; quedaron como **D354 a D365** en `knowledge-base/10_preguntas_abiertas.md`.

## Why

Hoy un turno que ya pasó queda `reservado` o `confirmado` para siempre: el consultorio no puede registrar si el paciente vino, así que no hay forma de medir el ausentismo (US-014) y el horario de un turno terminado sigue contando como ocupado. Además, `Paciente.es_nuevo` no existe todavía: es el dato que la aprobación manual de pacientes nuevos (C-27, RN-TD-05) necesita, y la KB lo hace nacer con el primer `atendido` (D52, D99). US-014 es la tercera acción sobre un turno de la agenda, después de reprogramar (C-16) y cancelar (C-17), sin pantalla nueva (D112).

## What Changes

- **Ruta nueva `POST /turnos/{id}/estado`** (la de `02`, fila Turnos): marca un turno como `atendido` o `ausente` (US-014 CA-1). Cuerpo obligatorio `{"estado": "atendido" | "ausente"}` (Q2, D355), el mismo idioma de `POST /turnos/{id}/cancelar` (D344). Responde `200` con el turno, con la misma forma que `201` de `POST /turnos`; nada más del turno cambia.
  - **Solo desde `reservado` o `confirmado`** (US-014 CA-2 y CA-3, RN-AG-13, DD-16): desde cualquier otro estado (`pendiente_aprobacion`, `pendiente_sena`, los cancelados, `vencido`, `atendido`, `ausente`) se rechaza con `409` y `RN-AG-12` y no cambia, también si se repite el mismo marcado. Pasar de `atendido` a `ausente` o al revés es la **corrección**, que llega con C-19: en este change también da `RN-AG-12` (Q3, D356).
  - **Solo si `ahora >= inicio`** (US-014 CA-6, D34): antes de que empiece, `RN-AG-13`. Con **`409`**, `type` `/errores/marcado-antes-del-inicio` (Q4, D357, ya escrito en `05` y `08`), evaluado después de `RN-AG-12`.
  - **Recursos desactivados después**: marcar no exige que el profesional, el sillón o la prestación sigan activos (`RN-AG-07` y `RN-GL-04` solo valen al crear o reprogramar; hallazgo H4).
  - **El horario queda libre** (US-014 CA-2, RN-AG-10): `atendido` y `ausente` no son activos, así que otro turno puede ocupar el hueco. La restricción de exclusión de la migración `0002` ya filtra solo los activos.
  - **Evento `estado_cambiado`** en el historial, en la misma transacción, con el estado de antes y de después, quién y cuándo (US-014 CA-4, RN-AG-11; Q7, D360). Un rechazo no registra nada.
  - **`Paciente.es_nuevo`** (US-014 CA-11, RN-TD-05, D52): columna nueva, `true` por defecto; el primer `atendido` del paciente la pasa a `false` en la misma transacción; `ausente` no la toca. Migración **`0010`** con relleno de los pacientes que ya tengan un turno `atendido` (Q8, D361). No se expone por la API hasta que un change la use (C-20, C-27).
  - **Permiso nuevo `turnos.marcar`** para el odontólogo y la recepcionista (fila «Marcar turno atendido / ausente» de `03`); el dueño y un usuario sin roles reciben `403` `RN-AU-05` (Q6, D359).
  - **Concurrencia**: el turno se lee con el bloqueo de fila de C-16/C-17 (`turno_para_cambiar`): dos marcados simultáneos dejan uno solo aceptado; un marcado y una cancelación se serializan (Q9, D362). Prueba solo en el perfil `postgres`.
- **Acción «Asistencia» en la agenda** (C-14), primera de la fila, solo en los turnos `reservado` y `confirmado`: abre un panel lateral «Registrar asistencia» con el resumen del turno y la pregunta «¿Cómo terminó el turno?» («Atendido» o «Ausente», sin opción marcada), y muestra cada rechazo con su código y «El turno no cambió.». Un solo panel lateral a la vez entre los cinco (Q10, D363).
- **El historial muestra el evento `estado_cambiado`** como «Cambio de estado» con «Estado: Reservado → Atendido» (Q11, D364).
- **Pantallas de Stitch** (D234), generadas en este propose con «Clinical Ops»: registrar asistencia con error de escritorio `projects/14200813501064679723/screens/b64bb7234a344397b127fc921f0fc733` y angosta `projects/14200813501064679723/screens/7c88173529aa4877952728a3abe6c05c`; qué se toma y qué se rechaza, en el design.
- **Demo y README**: sin datos nuevos de seed; recorrido de `POST /turnos/{id}/estado` en «Probar desde Swagger» y de la acción en «Panel (interfaz)», tablas escenario → test y límites conocidos.

Sin dependencias nuevas y sin variables de entorno nuevas. Una migración (`0010`). No hay **BREAKING**: `POST /turnos`, `GET /turnos`, `PATCH /turnos/{id}`, `POST /turnos/{id}/cancelar` y `GET /turnos/{id}/historial` no cambian su contrato; el historial suma un tipo de evento, que la pantalla de C-15 ya mostraba sin romperse como «Cambio registrado (estado_cambiado)».

### Escenarios

Cubre los mínimos de la entrada C-18 de `CHANGES.md`: **US-014 CA-1, CA-2, CA-3, CA-4, CA-6 y CA-11**. El spec de la API los detalla en **13 escenarios**, el de la pantalla en **6**, el delta de `pantalla-de-historial` modifica dos (`HIS-2b` y `HIS-2f`; repite sin cambios `HIS-2a` y `HIS-2c`), el de `pantalla-de-cancelacion` modifica uno (`CAN-4c`, los cuatro botones; repite sin cambios `CAN-4a` y `CAN-4b`) y el de `persistencia-postgresql` suma dos (la migración `0010` se deshace y rellena; repite sin cambios los diez de su requisito): **24 escenarios nuevos o cambiados** (38 con los repetidos), por encima del «3 a 6» por capability de `config.yaml`; excepción limitada a C-18 (Q12, D365), con el criterio de D353. Cada escenario tiene un ID propio (`ASI-1a`…) que lleva el nombre de su test.

| ID | Qué verifica | Dónde corre |
|---|---|---|
| ASI-1 | Marcar: el feliz con cada valor (CA-1), el horario que queda libre y el borde `ahora == inicio` (CA-2), los estados que no admiten marcado (CA-3, `RN-AG-12`), antes del inicio (CA-6, `RN-AG-13`), dos marcados simultáneos y un turno con recursos desactivados después | pytest (+ `postgres`) + navegador |
| ASI-2 | El evento `estado_cambiado` con estado de antes y de después, actor y momento (CA-4); un rechazo no registra nada; atomicidad | pytest |
| ASI-3 | `Paciente.es_nuevo` pasa a `false` con el primer `atendido` y no con `ausente` (CA-11) | pytest |
| ASI-4 | Acceso (`401`, `403` antes de validar; el token vencido lo cubre `proteccion-del-panel`), turno inexistente o de otro consultorio (`404`) y formato (`422`) | pytest |
| ASI-5 | La acción en la agenda: marcar atendido y ausente, la fila que queda sin acciones de cambio, la recarga que falla, un panel a la vez y el foco | Vitest + navegador |
| ASI-6 | Los rechazos con su código (`RN-AG-12`, `RN-AG-13`, `404`, `403`) y «El turno no cambió.», lo que la pantalla frena, la conexión y la sesión | Vitest + navegador |
| HIS-2b y HIS-2f (modificados) | El historial muestra «Cambio de estado» con el cambio; un solo panel entre los cinco | Vitest + navegador |
| CAN-4c (modificado) | Las filas `reservado` y `confirmado` tienen cuatro botones, en el orden «Asistencia», «Reprogramar», «Cancelar», «Historial» | Vitest |
| INF-1 (dos nuevos) | La migración `0010` agrega `es_nuevo` con su relleno y se deshace sola | pytest `postgres` |

**Quedan fuera** de US-014: **CA-5** (retener la seña de un ausente) con C-41; **CA-7, CA-8 y CA-9** (corrección del marcado) con C-19; **CA-10** (la seña no acompaña la corrección) con C-41 y C-42.

## Fuera de alcance

- **Corregir el marcado** `atendido` ↔ `ausente` (US-014 CA-7 a CA-9, C-19): en este change esa transición da `RN-AG-12`; C-19 la habilita con su plazo de 24 horas y solo para el odontólogo.
- **La seña** (US-014 CA-5 y CA-10, RN-SP-04 (a), RN-SP-10): no existe hasta C-35 a C-41.
- **Usar `es_nuevo`** (la aprobación manual de RN-TD-05, C-27) y **mostrarlo** (pacientes desde el panel, C-20): este change solo crea la columna y la mantiene.
- **La ficha clínica** del Flujo 7 (evolución, C-43 en adelante): marcar no pide ni registra evolución.
- **Un `EventoPaciente`** por el cambio de `es_nuevo`: `04` dice que esa consecuencia se deriva del `EventoTurno` del marcado.
- **Un motivo** escrito: el evento lleva `motivo` vacío y el cuerpo no lo acepta.
- **Reportes de ausentismo** (C-47): este change solo deja el dato.
- **Ocultar acciones según el rol** (D312): «Asistencia» se ve para los tres roles y el dueño recibe el `403` de la API.
- **Ocultar «Asistencia» en los turnos que todavía no empezaron**: la pantalla no evalúa reglas con el reloj del navegador (D323); la API responde `RN-AG-13` (Q10).
- **El estado efectivo** de un `pendiente_sena` con la seña vencida: no aplica (un `pendiente_sena` no se marca) y llega con la seña.

## Capabilities

### New Capabilities

- `marcado-de-asistencia`: el contrato de la API para marcar un turno como atendido o ausente desde el panel: `POST /turnos/{id}/estado`, qué estados lo admiten, desde qué momento, el horario que queda libre, el evento `estado_cambiado`, `Paciente.es_nuevo`, quién puede y los rechazos `401`, `403`, `404`, `409` y `422` (US-014 CA-1 a CA-4, CA-6 y CA-11; RN-AG-10, RN-AG-11, RN-AG-12, RN-AG-13, RN-TD-05, RN-GL-02, RN-GL-04, RN-AU-05).
- `pantalla-de-asistencia`: la acción «Asistencia» de la agenda y su panel: qué muestra, qué manda, cómo se ven el resultado y cada rechazo con su código, y cómo convive con los otros cuatro paneles (US-014 CA-1 a CA-3 y CA-6).

**Dos capabilities nuevas** se apartan de «una sola capability» (`config.yaml`, regla dura 12): es el corte API / navegador que el autor aceptó en D241 a D343; excepción limitada a C-18 (Q1, D354).

### Modified Capabilities

- `pantalla-de-historial`: el requisito «El historial de un turno se abre desde la agenda y es de solo lectura» suma la etiqueta del evento `estado_cambiado` («Cambio de estado» con el cambio de estado) y su escenario `HIS-2b` suma uno (Q11); el requisito «Un solo panel lateral a la vez…» nombra los cinco paneles y su escenario `HIS-2f` suma la corrida con «Registrar asistencia» (Q10).
- `pantalla-de-cancelacion` (hallazgo H1, D354): el requisito «Un turno activo se cancela desde su fila de la agenda indicando quién lo pidió» nombra los cinco paneles laterales y su escenario `CAN-4c` pasa a pedir los cuatro botones de las filas `reservado` y `confirmado`, en el orden «Asistencia», «Reprogramar», «Cancelar», «Historial» (decía «los tres botones», una lista cerrada que deja de ser cierta).
- `persistencia-postgresql`: el requisito «Esquema de PostgreSQL creado por migraciones» suma dos escenarios de la migración `0010` (deshacerla sola y el relleno de `es_nuevo`), como C-13 sumó los de `0009` (Q8).

Se revisaron y **no cambian**:
- `creacion-de-turnos`, `reprogramacion-de-turnos` y `cancelacion-de-turnos`: ya cuentan solo los turnos activos y ya rechazan los terminales (`RN-AG-18`, `RN-AG-12`); un turno atendido o ausente se comporta como cualquier terminal.
- `historial-de-turnos`: el evento `estado_cambiado` se especifica donde nace, en `marcado-de-asistencia`, como `reprogramado` (D332) y `cancelado` (D343).
- `consulta-de-turnos` y `pantalla-de-agenda`: ya listan y etiquetan `atendido` («Atendido», verde) y `ausente` («Ausente», rojo).
- `pantalla-de-reprogramacion`: `REP-6c` pide que las filas activas «tengan los dos» botones («Reprogramar» e «Historial»), que sigue siendo cierto con botones de más; el botón nuevo va antes, como C-17 sumó «Cancelar» sin delta de `REP-6c`. La convivencia de los cinco paneles queda en los deltas de `pantalla-de-historial` y `pantalla-de-cancelacion`.
- `proteccion-del-panel`: su guard exige el token a la ruta nueva; el permiso `turnos.marcar` queda en `marcado-de-asistencia`.

## Impact

- **Backend**: `domain/turnos/asistencia.py` (nuevo, puro: qué estados se marcan, hacia cuáles, desde qué momento y si el paciente deja de ser nuevo); `domain/turnos/eventos.py` (`TipoEvento.ESTADO_CAMBIADO`, `evento_estado_cambiado`); `domain/errors.py` (`MarcadoAntesDelInicio`, `RN-AG-13`; reusa `TransicionInvalida`); `domain/acceso/roles.py` (`Permiso.TURNOS_MARCAR`); `domain/agenda/recursos.py` (`Paciente.es_nuevo`); `application/marcar_asistencia.py` (nuevo); puerto y repositorio de la agenda (`marcar_paciente_no_nuevo` y la lectura de `es_nuevo`); `infrastructure/db/modelos.py` (`PacienteModelo.es_nuevo`); migración `0010_paciente_es_nuevo.py`; `api/esquemas.py` (`MarcarAsistenciaEntrada`); `api/errores.py` (`RN-AG-13` → `409`); `api/routers/turnos.py` (`POST /turnos/{id}/estado`). Tests de unidad, integración, API y del perfil `postgres`; los contadores de la matriz de permisos (18 → 19) y de rutas protegidas suben.
- **Frontend**: `features/agenda/` (`PanelAsistencia.tsx`, `marcarAsistencia` en `apiAgenda.ts`, textos en `mensajes.ts`, el botón en `TablaDeTurnos.tsx`, el estado `panel` de `PaginaAgenda.tsx`); `features/historial/mensajes.ts` (la etiqueta y el detalle de `estado_cambiado`); `test/servidorFalso.ts` (`POST /api/turnos/{id}/estado`); `shared/iconos/` (un ícono de tilde en SVG en línea); `panel.css` y, si hace falta, `tokens.css`.
- **Esquema y migraciones**: `paciente.es_nuevo` (`boolean NOT NULL DEFAULT true`) en `0010`, con relleno; `turno.estado` y `evento_turno.tipo` siguen sin `CHECK`; la exclusión de `0002` ya filtra los activos.
- **Dependencias y variables de entorno**: ninguna nueva.
- **Documentación**: `README.md`; evidencia de Stitch en `docs/skills-mcp/evidencias/sesion-nueva/stitch-asistencia.md` y `stitch-asistencia-pantalla/`. El `/opsx:update` del 2026-10-30 registró D354 a D365 en `10` y escribió en la KB: el `409` de `RN-AG-13` en `05` y en el mapeo de `08`, el orden de `POST /turnos/{id}/estado` en RN-GL-02 de `05`, `turnos.marcar` en `03`, el cuerpo en la fila Turnos de `02`, la nota de US-014 en `06`, `es_nuevo` (migración `0010` con relleno) y el evento `estado_cambiado` en `04`, el rango D1..D365 en `openspec/config.yaml`, y el resumen de D354 a D365 en `CLAUDE.md` y `AGENTS.md`.
- **`CHANGES.md`**: C-18 pasa a `[~]` en curso con este propose; el `/opsx:update` sumó D354 a D365 y RN-GL-02 a su «Leer antes».
- **Tamaño**: 34 tareas en 13 grupos para 24 escenarios nuevos o cambiados, por encima de las «alrededor de 20» tareas de `config.yaml`: excepción limitada a C-18 (Q12, D365).
