# Revisión de spec y tasks: gestion-de-prestaciones (copia del fixture)

## Veredicto
**NO está lista para el apply.** Hay 3 defectos en la spec que contradicen la KB (RN-AG-15, RN-GL-02, RN-AG-01), uno de ellos con una regla inventada sin respaldo y sin tarea que la pruebe. Se corrigen en la spec; las tasks ya son coherentes con la KB, así que la spec quedaría alineada con ellas.

## Hallazgos (por gravedad)

### 1. Escenario inventado: «no se admiten más de 50 prestaciones activas»
- Spec, requirement «El nombre es único», escenario «Error de negocio - no se admiten más de 50 prestaciones activas».
- No existe en la KB: ni US-001 (CA-1 a CA-3), ni RN-AG-01, ni RN-AG-15, ni ninguna D del registro (D171 a D182). No hay un límite de 50 en la KB.
- Además usa mal `RN-AG-01` (que es solo duración > 0 y múltiplo de 5) para un tope de cantidad, y con `409`.
- Ninguna tarea lo prueba (ni el design lo define): rompe la regla 12 (un change, una capability, nada fuera de alcance) y dejaría un escenario sin test.
- Corrección: borrar el escenario. Si el autor quiere un tope, es una decisión nueva (D, regla RN propia), no de este change.

### 2. Escenario de nombre repetido con `codigos` vacío
- Spec, «Error de negocio - nombre repetido en el alta»: responde `409` con `codigos` `[]`.
- RN-AG-15 y RN-GL-02 exigen el código: `409` con `codigos` `["RN-AG-15"]`. Los demás escenarios y las tasks (4.1, 6.1) ya dicen `["RN-AG-15"]`, así que la spec contradice las tasks.
- Corrección: `codigos` `["RN-AG-15"]`.

### 3. Duración 47 con `400` en lugar de `422`
- Spec, «CA-2 Error de negocio - una duración que no es múltiplo de 5»: responde `400`.
- Es validación de entrada (RN-GL-02, D135; RN-AG-01 en `05`; D177): `422` con `codigos` `["RN-AG-01"]` y error del campo `duracion_minutos`. El propio requirement dice `422`, y las tasks 5.1 y 6.1 también; el escenario las contradice.
- Corrección: `422`.

### 4. Menores
- Los escenarios de CA-2 con 47, 0 y -5 se titulan «Error de negocio» pero son validación de entrada (RN-GL-02 distingue las dos clases); conviene titularlos «Error de entrada» o aclarar, sin cambiar el contenido.
- «Una edición mal formada» (escenario de `PATCH`) está en la spec y cubierto por 6.3; en cambio `PATCH {}` -> `200` sin cambios y `PATCH` con duración inválida (6.3) están en las tasks pero no en la spec: pedir un escenario o quitarlos de las tasks, para que cada tarea tenga su escenario.
- Estado de las tasks: todas figuran `[x]` aunque el plan todavía no se aprobó ni se aplicó. Para el apply deberían estar sin marcar; si no, el apply no tiene nada que hacer y el estado no refleja la realidad.

## Lo que está bien
- Los tres CA de US-001 tienen caso feliz, de error y de borde; CA-3 queda cubierto por escenarios y por las tareas 7.1 y 7.2.
- Códigos y estados correctos: `RN-GL-04` con `404` para el id de la URL y `422` para la prestación inactiva en `POST /turnos`; el orden «duración inválida antes que nombre repetido» coincide con D177; la clave de nombre sin mayúsculas, tildes ni espacios de más y el hecho de que las inactivas ocupan nombre (D171, D172).
- Las 22 tareas en 9 grupos: consistente con la cabecera; TDD con RED/GREEN/TRIANGULATE, sin mocks, sin dependencias nuevas.

## Cobertura escenario -> tarea (resumen)
Alta feliz/borde/formato: 6.1, 6.3. Nombre repetido (exacto, sin tildes, renombrar): 4.1, 4.3, 6.1. Tope de 50: **sin tarea**. Duración: 2.1, 5.1, 5.2, 6.1, 6.3. Listado: 4.1, 6.1. Editar/desactivar/404/mal formado: 4.3, 6.1, 6.3, 7.2. CA-3: 7.1, 7.2.

## Acción recomendada
Corregir los puntos 1 a 3 en `specs/gestion-de-prestaciones/spec.md`, resolver los menores y recién después aprobar el plan y correr el apply.
