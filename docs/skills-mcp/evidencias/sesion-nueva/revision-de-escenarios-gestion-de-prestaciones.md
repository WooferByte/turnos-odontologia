# Revisión de escenarios: `gestion-de-prestaciones`

> Generado con la skill propia `revisor-de-escenarios` (`.claude/skills/revisor-de-escenarios/`) en una sesión nueva, el 2026-10-19, sobre el change archivado `openspec/changes/archive/2026-10-14-gestion-de-prestaciones/` (C-04). Revisión estática: no se corrió la suite ni se editó ningún artefacto.
>
> Fuentes leídas: salida de `scripts/inventario.py`; `CHANGES.md` §[C-04]; `knowledge-base/06_funcionalidades.md` §US-001; `knowledge-base/05_reglas_de_negocio.md` RN-AG-01, RN-AG-02, RN-AG-05, RN-AG-08, RN-AG-15, RN-GL-02, RN-GL-03, RN-GL-04; `knowledge-base/10_preguntas_abiertas.md` D171 a D182; `openspec/config.yaml` (`rules.specs`, `rules.tasks`); `spec.md`, `tasks.md` y `design.md` del change.

**Veredicto**: listo para implementar (con sugerencias de redacción y bordes menores; ningún bloqueante ni nada a corregir).
**Base**: 20 escenarios según el título (feliz 6, error de negocio 4, borde 9, error de formato 1); por la clase real del rechazo (RN-GL-02, D177), los errores de regla de negocio son 3 (RN-AG-15) y el resto de los rechazos son validación de entrada. CA mínimos 3/3 (US-001 CA-1, CA-2, CA-3). Tareas cruzadas 20/20.

## Hallazgos

No encontré **bloqueantes** ni hallazgos **a corregir**: los tres CA mínimos tienen escenarios que prueban lo que dicen; hay feliz, error de negocio (RN-AG-15, `409`) y borde; cada código RN citado existe en `05` y dice lo que el escenario le atribuye; los estados HTTP siguen RN-GL-02 y RN-GL-04 (`422` de formato sin código, `422` con `RN-AG-01` como validación de entrada, `409` con `RN-AG-15` como regla de negocio después de `RN-AG-01`, `404` con `RN-GL-04` para la prestación de la URL); y los valores no presentes en la KB están respaldados por D171 a D182 o marcados como «Propuesta» en `design.md` (P1 a P17, aprobados con el plan y registrados en `10`).

| ID | Severidad | Control | Ubicación | Hallazgo | Fuente | Corrección propuesta |
|----|-----------|---------|-----------|----------|--------|----------------------|
| H1 | Sugerencia | C3 / C4 | specs/gestion-de-prestaciones/spec.md:67 | El escenario de la duración 47 se titula «Error de negocio», pero `RN-AG-01` es **validación de entrada** (`422`, se informa junto con los demás errores de entrada). El cuerpo del escenario y el Requirement (spec.md:60) son correctos; solo el tipo del título confunde y hace que el inventario cuente 4 errores de negocio en vez de 3. | 05 RN-AG-01 («es validación de entrada»); D177; RN-GL-02 | Retitular como «Error de validación» (o «Error de entrada») y dejar «Error de negocio» para los de `RN-AG-15`. |
| H2 | Sugerencia | C4 | specs/gestion-de-prestaciones/spec.md:127 | «Prestación inexistente en la URL» se titula «Error de negocio», pero el recurso inexistente de la URL (`404`, `RN-GL-04`) va antes que la duración y que el nombre en el orden de D177; no es una regla de negocio de RN-GL-02. | 05 RN-GL-04 (distinción `404`/`422`); D166; D177 | Retitular como «Error - recurso de la URL inexistente» o similar. |
| H3 | Sugerencia | C5 | specs/gestion-de-prestaciones/spec.md:62 | El feliz de CA-2 («duración 45 se acepta») no da `nombre` ni `color`, que son obligatorios (spec.md:13): leído al pie de la letra, la petición sería un `422` de formato. | spec.md:13 (Requirement «Dar de alta») | Completar los valores, por ejemplo `nombre` «Limpieza», `duracion_minutos` 45, `color` `#43A047`. |
| H4 | Sugerencia | C6 | tasks.md:25 y tasks.md:49 | El feliz de CA-2 (`201` con 45) se verifica solo a nivel de la función pura `duracion_valida` (2.1); ningún test de API pide `POST` con 45 y comprueba el `201` (el feliz de 6.1 usa 60). El riesgo es bajo porque el camino de API está cubierto por otros felices. | config.yaml `rules.tasks[1]` (cada test cita el escenario que verifica) | Citar el escenario en 6.1 o agregar el caso 45 al test de API del feliz. |
| H5 | Sugerencia | C6 (traza inversa) | tasks.md:51 | `test_ca1_patch_vacio_responde_200_sin_cambios` prueba un comportamiento (`PATCH {}` → `200`) que no tiene escenario en la spec. Está respaldado por D178, así que no es una regla inventada, pero queda fuera del contrato. | D178 | Agregar el escenario de borde (ver «Bordes sugeridos»). |

## Cobertura

| CA | Escenarios | Tarea que lo verifica |
|----|------------|-----------------------|
| US-001 CA-1 (alta) | spec.md:15 feliz, :22 borde espacios + reservable, :27 formato | 4.1, 6.1 (feliz y borde); 6.3 (`test_ca1_post_mal_formado_responde_422_sin_codigo`) |
| US-001 CA-1 (nombre único, RN-AG-15) | :37 alta repetida, :44 mayúsculas/acentos e inactiva, :50 renombrar | 2.1, 2.3 (dominio); 3.1 (red de seguridad `UNIQUE`); 4.1, 4.3 (casos de uso); 6.1 (`409` por HTTP) |
| US-001 CA-1 (listado) | :96 incluye inactivas, :102 lista vacía | 4.1 (`test_ca1_listar_prestaciones_incluye_las_inactivas`); 6.1 (`GET` con activas e inactivas y `GET` vacío) |
| US-001 CA-1 (editar y desactivar) | :112 editar color, :118 desactivar y reactivar con efecto en `POST /turnos`, :127 `404`, :133 edición mal formada | 4.3; 6.1 (`PATCH` color y `/999`); 6.3 (`test_ca1_patch_mal_formado_no_cambia_nada`); 7.2 (`test_ca1_una_prestacion_desactivada_no_admite_turnos_nuevos`) |
| US-001 CA-2 (duración, RN-AG-01) | :62 feliz 45, :67 47, :73 5 / 0 / -5, :79 edición 50 / 52, :86 antes que el nombre | 2.1, 2.3 (dominio); 5.1, 5.2 (casos de uso, incluido el mínimo 5); 6.1 (`422` por HTTP); 6.3 (`test_ca2_patch_con_duracion_invalida_responde_422`) |
| US-001 CA-3 (no toca turnos) | :143 alargar, :150 acortar no libera (`409` RN-AG-05 + RN-AG-08), :157 sin eventos nuevos | 7.1 (los dos HTTP y la lectura de la fila desde otra sesión); 7.2 (`test_ca3_editar_la_prestacion_no_agrega_eventos_al_historial`) |

El escenario :118 comprueba el efecto en `POST /turnos` (capability `creacion-de-turnos`, E12) sin cambiar su comportamiento: no se sale del alcance (C8; D175). Los datos son nombres de prestaciones y colores, sin personas (C9, RN-PR-01). La prueba en `/docs` (8.2) y la verificación en clon limpio (9.2) cumplen `rules.tasks[4]` y `rules.tasks[5]`.

## Bordes sugeridos

- **GIVEN** una prestación «Limpieza» de 45 minutos, `color` `#43A047`, activa **WHEN** se pide `PATCH /prestaciones/{id}` con cuerpo `{}` **THEN** el sistema responde `200` con la prestación sin cambios — ya lo prueba 6.3 y lo fija D178; falta en la spec (H5).
- **GIVEN** que no existe la prestación 999 **WHEN** se pide editarla con `duracion_minutos` 47 **THEN** el sistema responde `404` con `codigos` `["RN-GL-04"]`, sin `RN-AG-01` — prueba el orden «prestación de la URL → RN-AG-01» de D177, que hoy solo está en el design (D177; RN-GL-02).
- **WHEN** se pide crear una prestación con `duracion_minutos` «45» (texto) o 45.5 **THEN** el sistema responde `422` con `codigos` vacío y un error del campo `duracion_minutos` — separa el error de tipo (formato, sin código) del de `RN-AG-01`, una frontera que la spec no muestra (D177: «tipo erróneo» es formato; RN-GL-02).
- **WHEN** se pide crear una prestación con `color` `#3a7bd5` (minúsculas) **THEN** el sistema responde `201` con `color` `#3a7bd5` tal como llegó — fija que el patrón acepta minúsculas y que el color no se transforma (D178: «el color se guarda tal como llega»; P9).
- **GIVEN** una prestación inactiva «Urgencia» **WHEN** se la reactiva con `activa` `true` **THEN** responde `200` sin `409`, aunque su nombre ya esté «ocupado» por ella misma — es el motivo explícito de que una inactiva siga ocupando su nombre (05 RN-AG-15; D171). Hoy está cubierto de forma indirecta en :118 y por `excepto_id` (2.3).

No sugiero bordes de `401`/`403` (las rutas no tienen autenticación hasta C-07, DD-14), de intervalo semiabierto (el `409` de :150 ya lo implica con 10:30 dentro de `[10:00, 11:00)`), de medianoche del consultorio (no aplica a un catálogo) ni de interfaz (la pantalla es C-11).

## Lo que no pude verificar

- **ID de escenario en el título.** `openspec/config.yaml` `rules.specs[1]` pide «el ID de escenario (E#) en el título», pero los E1..E12 de `06` son los del primer change; desde C-04 todos los changes archivados titulan con `US-NNN CA-N` (C-04, C-05, C-06, C-07, C-08) y ninguno usa E#. No encontré en `10` una decisión que actualice la regla; la trato como una ambigüedad de `config.yaml`, no como un hallazgo del change. Convendría que el autor aclare la regla (por ejemplo, «E# o `US-NNN CA-N`»).
- **Concurrencia de dos altas.** Dos altas simultáneas con el mismo nombre exacto terminan en `409` por la `UNIQUE` (3.1, V3), y dos que difieren solo en mayúsculas o tildes pasan las dos: es un límite aceptado (05 RN-AG-15; D172). No lo sugiero como escenario porque no es verificable de forma determinista por HTTP con SQLite en memoria.
- No contrasté el código implementado ni corrí los tests: la revisión es estática sobre los artefactos del change, como pide la skill. Que las tareas estén marcadas `[x]` no lo verifiqué contra la suite.
