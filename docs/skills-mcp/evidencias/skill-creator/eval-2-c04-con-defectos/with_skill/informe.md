# Revisión de escenarios: `gestion-de-prestaciones` (copia de fixture)

**Veredicto**: no listo
**Base**: 21 escenarios (feliz 6, error de negocio 5, borde 9, otros 1 [error de formato]); CA mínimos 3/3 nominalmente cubiertos (US-001 CA-1, CA-2, CA-3); tareas cruzadas 20/21 (el inventario marca 21/21 porque solo cruza por CA; al leer `tasks.md`, el escenario de las 50 prestaciones no tiene ninguna tarea).

Alcance: solo la copia indicada (`specs/gestion-de-prestaciones/spec.md` y `tasks.md`); `design.md` se leyó solo para comprobar respaldos. No se comparó con el original archivado. Nota: todas las tareas de la copia ya figuran `[x]`; si la pregunta es «¿puede arrancar el apply?», primero hay que corregir la spec y destildar/agregar las tareas afectadas.

## Hallazgos
| ID | Severidad | Control | Ubicación | Hallazgo | Fuente | Corrección propuesta |
|----|-----------|---------|-----------|----------|--------|----------------------|
| H1 | Bloqueante | C3 | spec.md:37-43 (escenario «nombre repetido en el alta») | El `409` por nombre repetido dice `codigos` `[]`. Es un error de negocio sin código RN, y contradice el requirement de spec.md:35 («`409` y el código `RN-AG-15`»), el escenario de spec.md:51-55 y la tarea 4.1/6.1 (`["RN-AG-15"]`). | Regla dura 4; 05 RN-AG-15; 06 US-001 CA-1; D171 | Cambiar el THEN a `409` con `codigos` `["RN-AG-15"]` y el detalle con el nombre existente. |
| H2 | Bloqueante | C3, C7, C8 | spec.md:44-50 (escenario «no se admiten más de 50 prestaciones activas») | Regla inventada: ni la KB, ni CHANGES.md, ni el `design.md` (sin D ni «Propuesta» que fije un tope de 50) ni US-001 la contemplan. Además le asigna `RN-AG-01`, que es la regla de duración (> 0 y múltiplo de 5), y un `409`. Está fuera del alcance de C-04 (nombre único, duración, color; ver «Alcance — dentro»). | Regla dura 9 y 12; 05 RN-AG-01; CHANGES.md C-04; `config.yaml` (la KB manda) | Eliminar el escenario. Si el autor quisiera un tope, hace falta una D, una RN propia y su tarea; no con `RN-AG-01`. |
| H3 | Bloqueante | C4, C3 | spec.md:74-78 (escenario «duración que no es múltiplo de 5 se rechaza») | Responde `400` con `RN-AG-01`. La duración inválida es validación de entrada: `422` (D177/P8, RN-AG-01 en 05). Contradice el requirement de spec.md:67, los escenarios de spec.md:80-84 y 86-91 (`422`) y la tarea 6.1/6.3. Además el título dice «Error de negocio», pero es validación de entrada. | 05 RN-GL-02 (D135); 05 RN-AG-01; D177 | Cambiar a `422`, `codigos` `["RN-AG-01"]`, y retitular como «Error de formato»/validación de entrada. Con eso el change vuelve a tener un solo error de negocio propio (RN-AG-15, ver H5). |
| H4 | A corregir | C6 | tasks.md (ningún grupo) | El escenario de las 50 prestaciones no tiene tarea que lo pruebe; solo lo cubre el cruce por CA del inventario. | `config.yaml` rules.tasks; skill C6 | Se resuelve con H2 (al borrar el escenario no hace falta tarea). Si se conserva, agregar un RED. |
| H5 | A corregir | C2 | spec.md (conjunto) | Tras corregir H1-H3 los errores de negocio válidos son: nombre repetido en el alta (RN-AG-15, spec:37), borde de mayúsculas/acentos (spec:51), renombrar (spec:57) y el `404` (spec:134, que para la URL es validación de entrada con `RN-GL-04`, no regla de negocio). Los tres tipos siguen presentes, pero el escenario de spec:134 está rotulado «Error de negocio» siendo `404` de URL. | 05 RN-GL-02, RN-GL-04; D166 | Retitular spec:134 como «Error de referencia» (o aclarar que es de la URL). Menor, no bloquea. |
| H6 | A corregir | C8 / C7 | spec.md:125-132 | El escenario «Feliz» de desactivación incluye comportamiento de `POST /turnos` (`422` `RN-GL-04` inactivo y reactivación `201`), que pertenece a `creacion-de-turnos` (D175: E12 ya lo cubre). Mezcla dos capabilities en un escenario; si cambia E12, este se rompe. | D175; regla dura 12 | Dejar en este escenario solo `PATCH activa false/true` y que el turno existente no cambia; referirse a E12 para el rechazo del turno nuevo. |
| H7 | Sugerencia | C5 | spec.md:41 | «un detalle que dice qué nombre ya existe» no es un valor concreto verificable. | skill C5 | Dar el texto o la forma exacta del `detail`, como hace spec:48. |
| H8 | Sugerencia | C6 | tasks.md 6.3 | Hay tests para `PATCH {}` → `200` sin cambios (D178), `campo de más` y `abc` en la URL, pero la spec solo cubre parte (el `{}` no tiene escenario). | D178; skill C6 inverso | Agregar el escenario `{}` o aceptar que es detalle de diseño. |

Fuentes sin objeción: nombres y valores ficticios (C9, sin emails/DNI), horarios UTC en las convenciones (C5), códigos citados existen en 05 (`RN-AG-01`, `RN-AG-02`, `RN-AG-05`, `RN-AG-08`, `RN-AG-15`, `RN-GL-03`, `RN-GL-04`), el `404` con `RN-GL-04` (D166) y el orden duración antes que nombre repetido (D177) están bien.

## Cobertura
| CA | Escenarios (spec:línea) | Tarea que lo verifica |
|----|-------------------------|-----------------------|
| US-001 CA-1 (alta, único, editar, desactivar, listar) | 15, 22, 27, 37 (H1), 51, 57, 103, 109, 119, 125, 134, 140; **44 sin tarea (H2)** | 2.1-2.3, 3.1, 4.1-4.3, 6.1-6.3, 7.2 |
| US-001 CA-2 (duración > 0 y múltiplo de 5) | 69, 74 (H3), 80, 86, 93 | 2.1, 2.3, 5.1-5.2, 6.1, 6.3 |
| US-001 CA-3 (cambiar duración no toca turnos) | 150, 157, 164 | 7.1, 7.2 |

## Bordes sugeridos
- GIVEN una prestación 999 inexistente — WHEN `PATCH /prestaciones/999` con `duracion_minutos` 47 — THEN `404` con `RN-GL-04` y no `RN-AG-01` (orden «prestación de la URL antes que la duración», D177).
- WHEN `POST` con `color` «azul» y `duracion_minutos` 47 a la vez — THEN `422` sin código RN: si el formato falla, no se evalúa RN-AG-01 (RN-GL-02, D135 d). Es la única forma de fijar la frontera entre ambas clases.
- WHEN `PATCH` con `{}` — THEN `200` con la prestación sin cambios (D178).
- Reactivar una prestación inactiva cuyo nombre no choca con otra — `200`; una inactiva sigue ocupando su nombre (RN-AG-15, D171).
- `color` en minúsculas (`#3a7bd5`): D178 dice que se guarda tal cual; vale un escenario si se quiere dejarlo explícito.
- Sin `401`/`403` ni concurrencia: no corresponden a C-04 (sin auth hasta C-07; la carrera de dos altas es un límite aceptado, D172, y queda en el perfil `postgres`).

## Lo que no pude verificar
- No hay en la KB un tope de prestaciones; asumo que el escenario de 50 es una invención y no una decisión del autor que no encontré (busqué en 05, 06, 10, CHANGES.md y el `design.md` de la copia).
- Que `design.md` y `proposal.md` de la copia coincidan con la spec corregida: no los auditó esta revisión (solo se consultaron para respaldos).
- No se corrió la suite ni se levantó nada (revisión estática). No se editó ningún archivo.
