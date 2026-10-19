> Informe producido por la skill `revisor-de-escenarios` el 2026-10-19, segunda revisión ("después") del change activo `panel-de-prestaciones` (C-11) tras `/opsx:update` (decisiones D229 a D233 y arreglos del primer informe), revisión estática: no se editó ningún artefacto ni se corrió la suite.

# Revisión de escenarios: `panel-de-prestaciones`

**Veredicto**: listo para implementar
**Base**: 33 escenarios (feliz 8, error de negocio 6, borde 19, otros 0); CA mínimos 3/3 (US-001 CA-1, CA-2, CA-3; más 3 escenarios de US-092 CA-1 como requisito propio); tareas cruzadas 33/33.

## Comparación con la revisión anterior

Primer informe: `openspec/changes/panel-de-prestaciones/revision-de-escenarios.md` (24 escenarios, 4 a corregir, 3 sugerencias). Cada fila se verificó leyendo `spec.md` y `tasks.md` actuales, no el resumen del updater.

| Hallazgo anterior | Estado | Evidencia |
|---|---|---|
| H1 (A corregir): «Guardar» sin cambios, T9/6.2 sin escenario ni test | Resuelto | `spec.md` l.153 «US-001 CA-1 Borde - guardar sin cambios no pide nada» (sin `PATCH`, panel cerrado); test RED en tarea 6.1 («guardar sin cambios cierra el panel sin ningún PATCH») y GREEN en 6.2 |
| H2 (A corregir): estado de carga sin escenario | Resuelto | `spec.md` l.23 «Borde - mientras carga se ve «Cargando prestaciones…»» (respuesta retenida, sin filas, luego cinco); tarea 3.3 (test con `retener`); mensaje en design T11 |
| H3 (A corregir): cableado de `SesionTerminada` sin Requirement en esta spec, Q3 abierta | Resuelto | Requirement propio `spec.md` l.239-262 con tres escenarios US-092 CA-1 (l.243 renovación, l.250 irrenovable con RN-AU-03, l.257 sesión termina al guardar); tareas 3.1, 3.3, 4.3; D231 en `10`; la entrada C-09 de `CHANGES.md` se ajusta al archivar (design T4 y «Open Questions») |
| H4 (A corregir): GIVEN de «la prestación ya no existe» sin id ni modo | Resuelto | `spec.md` l.159-164: «Urgencia» id 5, `quitarPrestacion(5)` después de listar, `PATCH /prestaciones/5` con `404` y `RN-GL-04`, recarga con cuatro filas; tareas 2.1 (`quitarPrestacion`) y 6.3 |
| H5 (Sugerencia): 403 antes que 422 | Resuelto | `spec.md` l.232 «Borde - sin permiso se ve RN-AU-05 antes que RN-AG-01»; tareas 2.3 y 6.4 (D208) |
| H6 (Sugerencia): 403 solo en alta y desactivar; dónde se muestra el mensaje | Resuelto | Texto del Requirement l.209 (aviso del panel con lo escrito conservado, o aviso de la tabla en acciones de fila); escenarios de edición l.218 y de desactivar y reactivar l.225; tarea 6.4 (RED y TRIANGULATE) |
| H7 (Sugerencia): error de red al guardar y al desactivar | Resuelto | `spec.md` l.72 (alta) y l.184 (desactivar); tareas 4.3 y 6.3. Queda sin escenario propio la red caída al guardar una edición (Sugerencia 2) |
| Borde sugerido 1: 403 antes que 422 | Resuelto | Igual que H5 (l.232) |
| Borde sugerido 2: error de red al guardar | Resuelto | Igual que H7 (l.72) |
| Borde sugerido 3: guardar sin cambios | Resuelto | Igual que H1 (l.153) |
| Borde sugerido 4: cargando | Resuelto | Igual que H2 (l.23) |
| «No pude verificar»: Q1 a Q5 abiertas | Resuelto | Cerradas por D229 a D233 (`10_preguntas_abiertas.md` l.421-425); `design.md` «Open Questions: Ninguna». Los escenarios reflejan D230 (l.209), D232 (l.104, sin `min`/`step`) y D233 (`#3A7BD5` en mayúsculas) |

Resumen: 11 de 11 resueltos, 0 parciales, 0 no resueltos. El spec pasó de 24 a 33 escenarios y las tareas siguen siendo 20 (1+3+3+3+2+4+1+1+2).

## Hallazgos
No encontré bloqueantes ni puntos a corregir. Controles:

- C1: US-001 CA-1, CA-2 y CA-3 tienen escenario feliz, de error y de borde, y prueban lo que dice el CA (CA-3: l.195 y l.202).
- C2: hay feliz, error de negocio y borde.
- C3: RN-AG-15, RN-AG-01, RN-GL-04, RN-AU-05 y RN-AU-03 existen en `05` y dicen lo que cada escenario afirma.
- C4: `422` con `codigos` vacío para el nombre en blanco (l.96); `409` solo con entrada válida (l.130, RN-GL-02); `404` `RN-GL-04` para el id de la URL (l.159); `403` antes que la validación (l.232, D208); `401` `RN-AU-03` (l.250, l.257).
- C5 y C6: todos los escenarios tienen valores concretos y tarea que los verifica (el script marca 33/33 y lo confirmé leyendo tasks.md).
- C7: los valores propios de la interfaz están marcados «Propuesta» en `design.md` T9 a T11; lo decidido tiene D (D229 a D233).
- C8: el cableado de la sesión es alcance decidido por D231; no hay cambios de API.
- C9: datos ficticios (`.test`, prestaciones de la demo).

| ID | Severidad | Control | Ubicación | Hallazgo | Fuente | Corrección propuesta |
|----|-----------|---------|-----------|----------|--------|----------------------|
| — | — | — | — | Sin hallazgos nuevos | — | — |

## Cobertura
| CA | Escenarios (spec, línea) | Tarea que lo verifica |
|----|--------------------------|-----------------------|
| US-001 CA-1 (ver, crear, editar, desactivar, nombre único, solo odontólogo) | 15, 23, 30, 36, 43, 53, 60, 66, 72, 83, 90, 96, 140, 147, 153, 159, 170, 177, 184, 211, 218, 225, 232 | 2.1, 2.3, 3.1, 3.3, 4.1, 4.3, 6.1, 6.3, 6.4 |
| US-001 CA-2 (duración, RN-AG-01) | 106, 113, 118, 123, 130 | 2.1, 2.3, 5.1, 5.2 |
| US-001 CA-3 (la duración no toca turnos) | 195, 202 | 6.1, 6.3 |
| US-092 CA-1 (sesión que termina en la pantalla; RN-AU-03) | 243, 250, 257 | 3.1, 3.3, 4.3 |
| Prueba en el navegador de todo lo anterior | — | 8.1 (agente), 9.2 (clon limpio) |

## Bordes sugeridos
(Dos sugerencias nuevas, ninguna bloquea el apply.)

1. **Acciones de fila deshabilitadas mientras esperan.** GIVEN la odontóloga con la respuesta de `PATCH /prestaciones/4` retenida tras pulsar «Desactivar» en «Extracción»; WHEN vuelve a pulsar «Desactivar»; THEN el botón está deshabilitado y la API recibió un solo `PATCH`. Aplica porque la tarea 6.2 exige los botones deshabilitados mientras esperan y solo el alta tiene escenario de doble clic (l.66); el l.189 comprueba únicamente que se rehabilitan. (C10 doble envío; `config.yaml` operations.apply: código con test previo; tarea 6.2)
2. **Red caída al guardar una edición.** GIVEN la odontóloga editando «Limpieza» con la duración en 50 y la API caída o con `5xx`; WHEN pulsa «Guardar»; THEN el aviso del panel muestra «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.», el panel sigue abierto con 50 y la fila sigue en «45 min». Hoy lo cubre la tabla de T11 («Al guardar, aviso del panel»), pero el único escenario con ese modo es el del alta (l.72). (C10 error de red; design T11)

## Lo que no pude verificar
- **`config.yaml` rules.specs[1]** dice literalmente «E#» en el título, y los títulos usan `US-NNN CA-N <Tipo> - ...` (convención desde C-04). Es una ambigüedad de la configuración, no un hallazgo.
- **Ajuste de la entrada C-09 en `CHANGES.md`**: por D231 se quita al archivar C-11 («no se edita antes»); hoy C-09 todavía lista el cableado de `SesionTerminada` en su alcance, y no puedo confirmar el ajuste hasta el archivado.
- **Ciclo de vida de los avisos** (cuándo se limpia el aviso de la tabla o del panel tras un reintento exitoso): la spec solo lo dice para los errores de campo (l.128); no hay D ni regla en la KB, así que no lo traté como hallazgo.
- **Textos y valores propios de la interfaz** (T9 a T12: mensajes, «5 minutos»): están marcados «Propuesta»; el color inicial y el hex en mayúsculas ya son D233. Los textos exactos no pueden contrastarse contra la KB.
- **Contrato del servidor falso frente a la API real**: lo cubren V4 y la tarea 8.1, posteriores a esta revisión. No leí el código del backend ni `seed_demo.py`.
