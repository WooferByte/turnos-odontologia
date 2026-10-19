# Revisión de escenarios: `gestion-de-prestaciones` (archivado, 2026-10-14)

**Veredicto**: listo para implementar (sin bloqueantes; una observación documental menor)
**Base**: 20 escenarios (feliz 6, error de negocio 4, borde 9, otros 1 [error de formato]); CA mínimos 3/3 (US-001 CA-1, CA-2, CA-3); tareas cruzadas 20/20.

Revisión estática: no se corrió la suite ni se editó ningún archivo del repo.

## Hallazgos
| ID | Severidad | Control | Ubicación | Hallazgo | Fuente | Corrección propuesta |
|----|-----------|---------|-----------|----------|--------|----------------------|
| H1 | A corregir (documental, no traba el diseño) | Regla de proposal | proposal.md §Escenarios; spec.md (20 escenarios) | CHANGES.md pide «3 a 6 escenarios». El proposal dice que cubre «los tres mínimos (dentro del "3 a 6")», pero la spec tiene 20 escenarios, y ni el proposal ni el design asientan la excepción con una D (como se hizo con D123/D134 en C-01 y D152 en C-03). Las tareas sí están justificadas en el propio tasks.md (22 tareas, «alrededor de 20»). | `openspec/config.yaml` rules.proposal[3]; CHANGES.md cabecera y C-01 (D123) | Registrar la excepción en el proposal (20 escenarios en 5 requisitos, agrupados por CA) con su decisión, o aclarar que «3 a 6» cuenta los CA mínimos. |
| H2 | Sugerencia | C2/C5 (rótulo) | spec.md:67 | El escenario «Error de negocio» de RN-AG-01 es validación de entrada (`422`, `codigos` `["RN-AG-01"]`), no una regla de negocio de RN-GL-02. El comportamiento es el correcto (05 RN-AG-01, D176/D177); solo el rótulo engaña a quien cuente tipos. | 05 RN-AG-01; RN-GL-02 | Rotular «Error de entrada con código RN». El escenario 15 (spec.md:118) está rotulado «Feliz» pero incluye un rechazo `422`; es mixto, conviene aclararlo. |

No hay hallazgos bloqueantes.

## Controles
- C1: los tres CA tienen escenarios que prueban lo que dicen (CA-1 alta, edición, desactivación y nombre único con `409`; CA-2 `>0` y múltiplo de 5 en alta y edición; CA-3 turnos existentes intactos).
- C2: hay feliz, error de negocio y borde en abundancia.
- C3: RN-AG-15 (`409`), RN-AG-01 (`422`), RN-GL-04 (`404` URL / `422` cuerpo) y RN-AG-05/08 existen en 05 y dicen lo que el escenario afirma. Los códigos y el orden RN-AG-01 antes de RN-AG-15 coinciden con 05.
- C4: formato malformado `422` con `codigos` vacío; id inexistente en URL `404` con RN-GL-04 (D166); duración inválida antes del nombre repetido (RN-GL-02). Sin autenticación hasta C-07, coherente con DD-14.
- C5: todos tienen GIVEN/WHEN/THEN con valores concretos y UTC del 2026-11-02. El escenario de «Error de formato» (spec.md:27) agrupa tres entradas y pide «un error que nombra el campo», aceptable pero algo laxo.
- C6: cada CA/escenario tiene su tarea RED en tasks.md (2.1, 3.1, 4.1, 4.3, 5.1, 6.1, 6.3, 7.1, 7.2) y la prueba en `/docs` (8.2).
- C7: las reglas añadidas (color `#RRGGBB`, `reservable_online` por defecto `false`, relleno `#9E9E9E`, orden por `id`, normalización de nombre) están respaldadas por D171 a D182, 04 §Prestacion y marcadas «Propuesta» en design.md.
- C8: nada fuera de alcance (sin pantalla, sin granularidad configurable, sin efecto de `reservable_online`).
- C9: datos ficticios (prestaciones genéricas), sin personas ni emails.

## Cobertura
| CA | Escenarios (spec.md líneas) | Tarea que lo verifica |
|----|------------|-----------------------|
| US-001 CA-1 | 15, 22, 27, 37, 44, 50, 96, 102, 112, 118, 127, 133 | 2.1, 2.3, 3.1, 4.1, 4.3, 6.1, 6.3, 7.2 |
| US-001 CA-2 | 62, 67, 73, 79, 86 | 2.1, 2.3, 5.1, 5.2, 6.1, 6.3 |
| US-001 CA-3 | 143, 150, 157 | 7.1, 7.2 |

## Bordes sugeridos
- GIVEN nada; WHEN `POST` con `color` `#3a7bd5` (minúsculas) — THEN `201` y se guarda tal cual. El patrón lo permite (design P9) pero ningún escenario lo fija (C10; design.md:119).
- GIVEN nada; WHEN `POST` con `nombre` de longitud muy grande — THEN el comportamiento definido. Ni KB ni spec fijan un máximo (C10); decidir si es un hueco o un límite aceptado.
- GIVEN una prestación inactiva; WHEN `PATCH` cambia su duración a 50 — THEN `200` (editar inactivas). Hoy implícito.
- Concurrencia de dos altas idénticas ya está tratada como red de seguridad `UNIQUE` en 05 RN-AG-15 y tarea 3.1 (V3); no hace falta escenario.

## Lo que no pude verificar
- No corrí tests ni comprobé que el código implementado cumpla la spec (revisión estática).
- Si «3 a 6 escenarios» de CHANGES.md cuenta escenarios o CA mínimos es ambiguo; el proyecto parece haberlo tratado como CA mínimos (ver H1).
