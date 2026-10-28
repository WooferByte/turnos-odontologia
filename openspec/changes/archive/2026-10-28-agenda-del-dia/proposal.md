# Proposal: agenda-del-dia

Change **C-14** de `CHANGES.md` (US-011, fase 4, orden 4). Gobernanza **BAJO**: autonomía completa si los tests pasan. Las preguntas **Q1 a Q11** del design quedaron respondidas por el autor el 2026-10-28 con la recomendación del agente, junto con los hallazgos H1 a H11 de `revisor-de-escenarios`, y están registradas como **D315 a D325** en `knowledge-base/10_preguntas_abiertas.md`. Depende de C-07 (archivado el 2026-10-15) y de C-08 (archivado el 2026-10-19); usa además lo que dejaron C-03 (historial), C-11 (pantalla de prestaciones), C-12 (horario), C-13 (bloqueos) y C-50 (encabezado).

## Why

El panel ya configura prestaciones, sillones, usuarios, horario y bloqueos, pero **no muestra ningún turno**: el único modo de dar un turno es `POST /turnos` desde Swagger, y no hay forma de ver qué tiene el consultorio en un día. US-011 es la pantalla con la que el odontólogo y la recepcionista trabajan todos los días, y C-15 a C-19, C-27 y C-33 le suman sus acciones «sin pantalla nueva» (D112, D113): es la base de toda la fase 4 y va ahora porque el resto de la fase depende de ella (`CHANGES.md`, «GATE 6: C-14 archivado»).

## What Changes

- **Dos rutas nuevas de solo lectura** (las de `02`, fila Turnos):
  - `GET /turnos?fecha=aaaa-mm-dd`: los turnos del consultorio del usuario del token cuyo inicio cae en ese **día del consultorio** (`Consultorio.zona_horaria`, RN-GL-01), ordenados por inicio y, a igual inicio, por id, cada uno con paciente (solo id, nombre y apellido), prestación (id, nombre y color) y estado (el almacenado; D317, D318). Sin `fecha`, el día de hoy del consultorio según el reloj inyectable (D316). La respuesta lleva la `fecha` consultada y la `zona_horaria`. Una `fecha` mal formada o fuera de `0001-01-02` a `9999-12-30` da `422` de formato (D322). En la v1 hay un solo profesional, así que «los turnos del profesional» de US-011 CA-1 son los del consultorio (D316).
  - `GET /turnos/{id}`: un turno con la misma forma; `404` `RN-GL-04` si no existe o es de otro consultorio (D73, D166).
  - Permiso nuevo `turnos.leer` para los tres roles (matriz de `03`: «R» para el dueño); un usuario sin roles recibe `403` `RN-AU-05` (D321).
- **Pantalla «Agenda»** en `/panel/agenda`, primer enlace de la barra del panel: un día por vez, con «Día anterior», «Día siguiente», «Hoy» y un selector de fecha; una fila por turno ordenada por inicio, con la hora en la zona del consultorio, el paciente, la prestación con su color y el estado (US-011 CA-1).
- **Formulario «Nuevo turno»** en un panel lateral de la agenda (US-011 CA-2, D110): número de paciente, prestación activa, fecha y hora del consultorio; manda el `POST /turnos` existente sin profesional ni sillón (el único activo, RN-AG-14) y muestra cada rechazo de US-010 con su código: **E4** con `RN-AG-05` y `RN-AG-08` juntos y **E12** con `RN-GL-04` y las referencias que fallaron; también `RN-AG-04`, `RN-AG-04b`, `RN-AG-10d` y `RN-AU-05`.
- **Pantallas de Stitch** (D234), generadas en este propose con «Clinical Ops»: agenda de escritorio `projects/14200813501064679723/screens/cd19642b8b1b4bcda5162e35d6291e10`, «Nuevo turno» con error `projects/14200813501064679723/screens/5371dfaf7cc441c08af62712e311c326` y agenda angosta `projects/14200813501064679723/screens/20bcd71b007a43f7874a05ae70a45753`; qué se toma y qué se rechaza, en el design.
- **Demo y README**: sin datos nuevos de seed; recorrido de las dos rutas en «Probar desde Swagger» y de la pantalla en «Panel (interfaz)», tabla escenario → test y límites conocidos (el paciente se elige por número hasta C-20).

Sin migraciones, sin dependencias nuevas y sin variables de entorno nuevas. No hay **BREAKING**: `POST /turnos` y las demás rutas no cambian.

### Escenarios

Cubre los mínimos de la entrada C-14 de `CHANGES.md`: **US-011 CA-1**, **US-011 CA-2**, **E4** (el formulario muestra los dos códigos) y **E12** (el formulario muestra `RN-GL-04`). El spec de la API los detalla en **11 escenarios** y el de la pantalla en **13** (24 en total, después del `/opsx:update` con el informe de `revisor-de-escenarios`), por encima del «3 a 6» de `config.yaml`: excepción aceptada por el autor y limitada a C-14 (**D325**, Q11), con el criterio de D300 y D314. Cada escenario tiene un ID propio (`AGE-1a`…) que lleva el nombre de su test.

| ID | Qué verifica | Dónde corre |
|---|---|---|
| AGE-1 | `GET /turnos` lista el día del consultorio ordenado por inicio y, a igual inicio, por id, con paciente, prestación con color y estado; los bordes del día en la zona del consultorio; «hoy» sin `fecha`; un día vacío; los tres roles (US-011 CA-1) | pytest + navegador |
| AGE-2 | `GET /turnos/{id}` devuelve el turno; un id inexistente o de otro consultorio da `404` `RN-GL-04` | pytest |
| AGE-3 | `fecha` mal formada o en los extremos del calendario da `422`; sin sesión, `401`; sin roles, `403` `RN-AU-05` | pytest |
| AGE-4 | La pantalla muestra el día con sus turnos, cambia de día, avisa del día vacío, de la carga, de la falta de conexión y del `403` (US-011 CA-1) | Vitest + navegador |
| AGE-5 | El formulario crea el turno, también en otro día que cruza la medianoche UTC, y muestra cada rechazo de US-010 con su código: E4 con los dos, E12 con `RN-GL-04` (US-011 CA-2) | Vitest + navegador |
| AGE-6 | La sesión se renueva sola si se puede, y si no, vuelve al inicio de sesión, al cargar el día y al crear | Vitest |

**Quedan fuera** (de US-011 y US-010): el resto de los E1..E12 ya está cubierto por la API en `creacion-de-turnos` (C-01, C-12, C-13); E11 (concurrencia) sigue en el perfil `postgres`. Las acciones sobre un turno de la agenda llegan con sus changes (abajo).

## Fuera de alcance

- **Acciones sobre un turno** desde la agenda: reprogramar (C-16), cancelar (C-17), marcar atendido o ausente (C-18, C-19), ver el historial (C-15), aprobar o rechazar (C-27, D112) y confirmar (C-33, D113). La pantalla no tiene columna de acciones (Stitch propone «Ver ficha»: se rechaza).
- **Alta, búsqueda o listado de pacientes** (`GET/POST /pacientes`, C-20): el formulario pide el **número** de paciente y la agenda muestra nombre y apellido que trae `GET /turnos` (D318, D319). C-20 cambiará ese campo por una búsqueda.
- **Agenda multi-profesional y multi-sillón** (Fase 2): no hay filtro por profesional ni por sillón, ni selector en el formulario; se usa el único activo (RN-AG-14, D320).
- **Vista semanal o mensual**, huecos libres, disponibilidad o sobreturnos (fuera de la v1).
- **Ocultar acciones según el rol** (D312): «Nuevo turno» se ve para los tres roles y el dueño recibe el `403` `RN-AU-05` de la API, como en C-11 a C-13 (D230, D249).
- **Datos de contacto del paciente** en la agenda (teléfono, email): no se devuelven (D318, RN-PR-01).
- **Refrescar la agenda sola** cuando otro usuario da un turno: se ve al cambiar de día, al volver a la pantalla o al recargar.

## Capabilities

### New Capabilities

- `consulta-de-turnos`: el contrato de la API para leer turnos: `GET /turnos` por día del consultorio y `GET /turnos/{id}`, la forma de la respuesta (con paciente y prestación), el orden, el día por defecto, quién puede leer y los rechazos `401`, `403`, `404` y `422` (US-011 CA-1; RN-GL-01, RN-GL-02, RN-GL-04, RN-AU-05).
- `pantalla-de-agenda`: la agenda del día en el navegador y su formulario de alta: cómo se muestran los turnos, cómo se cambia de día y cómo se ven los rechazos de `POST /turnos` con su código (US-011 CA-1 y CA-2; E4, E12; RN-AG-01, RN-AG-04, RN-AG-04b, RN-AG-05, RN-AG-08, RN-AG-10d, RN-GL-04, RN-AU-05).

**Dos capabilities en un change** se apartan de «una sola capability» (`config.yaml`, regla dura 12): el autor la aceptó como excepción limitada a C-14 (**D315**, Q1), con el mismo corte API / navegador que el autor aceptó en D241, D255, D271, D290 y D304.

### Modified Capabilities

Ninguna (D315). Se revisaron:
- `creacion-de-turnos`: `POST /turnos` no cambia; leer turnos es otro contrato.
- `proteccion-del-panel`: su guard ya exige el token a toda ruta nueva fuera de la lista pública; el permiso `turnos.leer` queda en `consulta-de-turnos`, como hicieron C-09, C-10, C-12, C-13 y C-50.
- `historial-de-turnos`: `GET /turnos/{id}/historial` no cambia (su vista en la agenda es de C-15).
- `ingreso-al-panel` y `encabezado-del-panel`: la barra suma el enlace «Agenda», sin cambiar sus requisitos (la lista de enlaces no está especificada como cerrada).

## Impact

- **Backend**: `domain/agenda/dia.py` (nuevo, puro: el rango UTC de un día del consultorio y el «hoy» del consultorio); `domain/acceso/roles.py` (`Permiso.TURNOS_LEER`); `domain/errors.py` (reusa `TurnoNoEncontrado`); `application/consultar_turnos.py` (nuevo); puerto y repositorio de la agenda (`turnos_del_dia`, `turno_de_la_agenda`); `api/esquemas.py` (salida de la agenda); `api/routers/turnos.py` (las dos rutas). Tests de unidad, integración y API; los contadores de los guards de permisos y de rutas protegidas suben (solo su número).
- **Frontend**: `src/features/agenda/` (cliente, página, tabla, formulario, mensajes y tests); `shared/api/rechazos.ts` y `errores.ts` (los `codigos` en el `409` y las `referencias` del `422`, sin cambiar lo que verifican los tests existentes); la conversión de hora del consultorio de `features/bloqueos/horaDelConsultorio.ts` pasa a `shared/` (REFACTOR); `App.tsx` y `PanelBase.tsx` (ruta y enlace «Agenda»); `test/servidorFalso.ts` (`GET /api/turnos`, `POST /api/turnos` con los rechazos de US-010); `panel.css` y, si hace falta, `tokens.css`.
- **Esquema y migraciones**: sin cambios (`turno` y `paciente` ya existen; hay índices por profesional e inicio).
- **Dependencias y variables de entorno**: ninguna nueva.
- **Documentación**: `README.md`; evidencia de Stitch en `docs/skills-mcp/evidencias/sesion-nueva/stitch-agenda.md` y `stitch-agenda-pantalla/`. Las respuestas a Q1 a Q11 quedaron en `knowledge-base/10_preguntas_abiertas.md` (D315 a D325) con el `/opsx:update` del 2026-10-28, que además sumó la agenda del día a las excepciones de RN-GL-01 en `05`, precisó `fecha` en la fila Turnos de `02`, anotó `turnos.leer` en `03` y la lectura de US-011 CA-1 en `06`. `02` y `03` ya listaban `GET /turnos?fecha` y `GET /turnos/{id}`, así que el verificador no cambia.
- **`CHANGES.md`**: C-14 pasa a `[~]` en curso con este propose.
- **Tamaño**: 30 tareas en 11 grupos para 24 escenarios, con RED, GREEN, TRIANGULATE y REFACTOR separados; excepción aceptada por el autor y limitada a C-14 (D325).
