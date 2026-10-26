# Proposal: bloqueos-puntuales

Change **C-13** de `CHANGES.md`, historia **US-003** («Bloqueos puntuales») y la parte de bloqueos de **E10** (US-010). Gobernanza **MEDIO**: se implementa por grupos con puntos de control y las decisiones no obvias se le muestran al autor. Depende de C-07 y C-08, los dos archivados (y usa lo que dejaron C-05, C-11, C-49, C-09 y C-12 en la API y en el panel). **Las preguntas abiertas Q1 a Q18 del design quedaron cerradas por el autor el 2026-10-26 con la recomendación del agente** (D271 a D288), junto con las correcciones del informe de `revisor-de-escenarios` (D289 sale de su hallazgo H11), registradas en `knowledge-base/10_preguntas_abiertas.md` con un `/opsx:update`. **La pantalla de Stitch ya está** (D288; la tarea 1.2 se hizo el 2026-10-26 con otro `/opsx:update`: el MCP devolvió el id `projects/14200813501064679723/screens/05d78d7e7d144f92bb9f77d0e4a220db`).

## Why

Hoy el horario recurrente (C-12) dice cuándo atiende el profesional, pero no hay forma de cerrar la agenda un día puntual: vacaciones, un feriado, una ausencia o el mantenimiento de un sillón. US-003 pide bloquear días u horas del profesional, del sillón o de todo el consultorio (CA-1) para que no se den turnos en ese momento (RN-AG-04b: los bloqueos prevalecen sobre el horario), y que al crear un bloqueo sobre turnos activos el sistema los liste sin cancelarlos (CA-2, D83), para que el odontólogo los reprograme o cancele.

Va ahora porque sus dos dependencias están archivadas, el horario recurrente ya valida RN-AG-04 en `POST /turnos` y lo necesitan el cálculo de disponibilidad (C-24) y el reporte de ocupación (C-47).

## What Changes

- **Tabla `bloqueo`** (modelo de `04`, «Bloqueo»): `consultorio_id`, `profesional_id` y `sillon_id` nulos (los dos nulos = todo el consultorio), `inicio` y `fin` con zona (`CHECK inicio < fin`), `motivo` y `creado_por` (FK → `usuario`). Migración Alembic nueva **`0009`**, reversible, con `creado_por` NN y un `CHECK` que impide profesional y sillón a la vez (D282, D272).
- **API de bloqueos** (contrato en el design, B4 a B9; decisiones del autor D272 a D283):
  - `GET /bloqueos`: los bloqueos del consultorio del usuario del token (D270), ordenados por `inicio`, con la zona del consultorio. Leen los tres roles (matriz de `03`, fila «Horario recurrente y bloqueos»).
  - `POST /bloqueos`: crea un bloqueo del profesional, del sillón o de todo el consultorio (US-003 CA-1) y responde `201` con el bloqueo y la lista de **turnos activos afectados**, que **no se cancelan ni cambian** (US-003 CA-2, D83). Solo `odontologo`; `403` `RN-AU-05` para los demás, evaluado antes que la entrada (D208).
  - `DELETE /bloqueos/{id}`: elimina el bloqueo (`204`); no toca ningún turno. Solo `odontologo`. Un bloqueo inexistente o de otro consultorio: `404` `RN-GL-04`.
  - Validación de entrada toda junta en un `422` (RN-GL-02): fechas sin zona o fuera de UTC (`RN-GL-01`), profesional o sillón inexistente, inactivo o de otro consultorio (`RN-GL-04`) y un bloqueo que no termina después de empezar (código nuevo **`RN-AG-17`**, D273, registrado en `05`). `inicio` y `fin` admiten cualquier minuto (D289); el `motivo`, de 1 a 200 caracteres (D283).
- **`crear_turno` valida RN-AG-04b** (E10): un turno cuyo `[inicio, fin)` interseca un bloqueo de su profesional, de su sillón o de todo su consultorio se rechaza con **`422` `RN-AG-04b`** (`07` Flujo 1, casos de error) y no se crea nada. Orden de las reglas de negocio: validación de entrada → RN-AG-10d → RN-AG-04 → **RN-AG-04b** → solapamiento (el paso 5 de `07` Flujo 1 nombra el horario y después los bloqueos; D280). El error lleva `bloqueo_id` del bloqueo que empieza primero. Contiguo no interseca (intervalos semiabiertos, RN-AG-09).
- **Seed de la demo**: sin bloqueos (D284), así los ejemplos del README siguen dando `201` y la regla nueva no rompe ningún test de la demo.
- **Pantalla «Bloqueos»** en `/panel/bloqueos`, a partir de una pantalla de **Stitch** con el design system «Clinical Ops» (D234; `projects/14200813501064679723/screens/05d78d7e7d144f92bb9f77d0e4a220db`, D288): la lista de bloqueos (alcance, desde, hasta en hora del consultorio y motivo), el alta (alcance, recurso, desde, hasta y motivo), la lista de turnos afectados después de crear, «Eliminar», los rechazos de la API con su código (`RN-AG-17`, `RN-GL-04`, `RN-AU-05`) y la sesión que termina vuelve al inicio de sesión. Enlace «Bloqueos» en la barra del panel.

**BREAKING** (comportamiento, no contrato): `POST /turnos` empieza a rechazar con `422` `RN-AG-04b` los turnos que intersecan un bloqueo. Sin bloqueos cargados no cambia nada. La forma de las respuestas no cambia.

### Escenarios

Cubre los tres mínimos de la entrada C-13 de `CHANGES.md` (dentro del «3 a 6»):

| ID | Qué verifica | Dónde corre |
|---|---|---|
| US-003 CA-1 | Se crea un bloqueo del profesional, del sillón o de todo el consultorio, se lista y se elimina | pytest (dominio, integración y API) + Vitest (pantalla) + navegador |
| US-003 CA-2 | Al crear un bloqueo sobre turnos activos, la respuesta y la pantalla los listan sin cancelarlos (D83) | pytest (dominio, integración y API) + Vitest + navegador |
| E10 (parte de bloqueos) | Un turno que interseca un bloqueo de su profesional, de su sillón o de su consultorio se rechaza con `RN-AG-04b`; el contiguo se acepta | pytest (dominio, integración y API) + navegador (Swagger) |

Los specs los detallan en escenarios felices, de error de negocio, de error de entrada y de borde: **61 escenarios** (51 nuevos y 10 copiados en los requisitos MODIFIED, después del `/opsx:update` con el informe de `revisor-de-escenarios`; conteo en el design, B20). La cantidad de escenarios y de tareas es una excepción registrada, limitada a C-13 (D287). Con E10 ya completo (horario en C-12 y bloqueos acá), la nota de E10 de `06` se cierra al archivar.

## Fuera de alcance

- **Cancelar o reprogramar automáticamente los turnos afectados** (D83): el sistema solo los lista; cancelar es C-17 y reprogramar, C-16.
- **Horario recurrente** (C-12, archivado) y **excepción de horario puntual** (Fase 2, D86).
- **Cálculo de disponibilidad** (C-24) y **reporte de ocupación** (C-47), que restarán los bloqueos.
- **Editar un bloqueo** (no hay `PATCH` en `02`: para cambiarlo se elimina y se crea de nuevo).
- **Bloqueos recurrentes** (todos los lunes, todos los años) y feriados cargados automáticamente.
- **Avisar a los pacientes** de los turnos afectados (mensajes, C-32).
- **Filtros o paginación** de `GET /bloqueos` (D279).
- **Un tope de duración o de cantidad de bloqueos** y una granularidad de sus horas (D289: cualquier minuto; límite conocido).
- **La reprogramación sobre un bloqueo**: C-16 aplica RN-AG-04b al reprogramar (RN-TD-04; anotado en su entrada de `CHANGES.md`).
- Varios consultorios por instalación (D173).

## Capabilities

### New Capabilities

- `bloqueos-puntuales`: el contrato de la API de los bloqueos puntuales: crear un bloqueo del profesional, del sillón o de todo el consultorio con la lista de turnos activos afectados, listarlos, eliminarlos, la validación de la entrada, quién puede usar cada ruta y el orden de evaluación (US-003; RN-AG-04b, RN-AG-17, RN-GL-01, RN-GL-04, RN-AU-05).
- `pantalla-de-bloqueos`: cómo el panel muestra, crea y elimina los bloqueos desde el navegador: la lista, el alta con los turnos afectados, los rechazos de la API con su código y qué pasa si la sesión termina en la pantalla (US-003, US-092 CA-1).

**Dos capabilities nuevas en un change** se aparta de la regla «una sola capability» (`openspec/config.yaml`, regla dura 12). Las excepciones anteriores (D241 para C-09, D255 para C-12) quedaron **limitadas a su change**, así que C-13 tiene su propia decisión: **D271** (Q1), la misma separación API / pantalla, por la suite que verifica cada una, registrada como excepción limitada a C-13.

### Modified Capabilities

- `creacion-de-turnos`: se agrega el requisito de RN-AG-04b (el turno no interseca un bloqueo de su profesional, de su sillón ni de todo su consultorio; E10) y su lugar en el orden de las reglas de negocio (requisito «Orden de las reglas de negocio al crear un turno», MODIFIED).
- `persistencia-postgresql`: el requisito «Esquema de PostgreSQL creado por migraciones» suma la tabla `bloqueo`, el escenario de deshacer solo la migración `0009` y el `CHECK` de `inicio < fin`.

Se revisaron sin cambios: `horario-recurrente` (RN-AG-04 no cambia; RN-AG-04b se evalúa en `POST /turnos`), `proteccion-del-panel` (el guard de rutas protegidas ya alcanza a las nuevas; los permisos de `/bloqueos` quedan en `bloqueos-puntuales`, como hicieron C-09 y C-12), `historial-de-turnos` (un rechazo por RN-AG-04b no registra nada y un bloqueo no cambia ningún turno), `gestion-de-sillones` (la pantalla solo lee `GET /sillones`), `ingreso-al-panel`, `pantalla-de-prestaciones`, `pantalla-de-usuarios` y `pantalla-de-horario` (el enlace nuevo de la barra no cambia sus requisitos).

## Impact

- **Backend, código nuevo**: `backend/app/domain/agenda/bloqueos.py` (alcance, validación de `inicio < fin`, turnos afectados y RN-AG-04b, puros), `backend/app/application/bloqueos.py`, `backend/app/api/routers/bloqueos.py`, `backend/app/infrastructure/repositories/bloqueos.py`, errores nuevos en `domain/errors.py` y su traducción en `api/errores.py`, permisos `bloqueos.leer` y `bloqueos.editar` en `domain/acceso/roles.py`, modelo `BloqueoModelo` en `infrastructure/db/modelos.py`, migración `0009_bloqueo.py`. **Se modifica**: `application/crear_turno.py` (RN-AG-04b), `application/puertos.py`, `infrastructure/unidad_de_trabajo.py`, `infrastructure/repositories/agenda.py` (turnos activos que intersecan un intervalo por alcance), `tests/factories.py` (fábrica `un_bloqueo`).
- **Frontend, código nuevo**: `frontend/src/features/bloqueos/` (cliente, página, formulario, lista, mensajes, conversión de hora del consultorio y tests). **Se modifica**: `App.tsx`, `pages/PanelBase.tsx` (enlace «Bloqueos»), `test/servidorFalso.ts`, `shared/estilos/panel.css` y `tokens.css`, un ícono SVG nuevo en `shared/iconos/`.
- **Esquema**: tabla nueva `bloqueo` (migración `0009`); sin cambios en las tablas existentes.
- **Dependencias y variables de entorno**: ninguna nueva.
- **Documentación**: `README.md`; evidencia de Stitch en `docs/skills-mcp/evidencias/sesion-nueva/stitch-bloqueos.md` (el pedido, la pantalla obtenida con su id y la revisión de datos, D288). Con el `/opsx:update` del 2026-10-26: las decisiones D271 a D289 en `10`, `RN-AG-17` en `05` (y en RN-GL-02) y en US-003 de `06`, y la nota de RN-AG-04b en C-16 de `CHANGES.md`. Al archivar: la nota de E10 y US-003 en `06`, `07` Flujo 1 (paso 5 y casos de error), `08` (estructura y «Mapeo a HTTP»), `02`, `03`, `04` §Bloqueo, RN-AG-04b y RN-GL-02 en `05`, `CHANGES.md` y el párrafo de estado de `CLAUDE.md` y `AGENTS.md` (lista en las «Notas para el archive» del design).
- **Tamaño**: **22 tareas en 10 grupos** para 61 escenarios, frente a «alrededor de 20» tareas y «3 a 6 escenarios» de `CHANGES.md`: excepción aceptada por el autor y limitada a C-13 (D287, como D228 para las 22 tareas de C-08; las excepciones D251 y D264 quedaron limitadas a C-09 y C-12).
