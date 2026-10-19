# Revisión de escenarios: gestion-de-prestaciones (C-04)

Alcance: `specs/gestion-de-prestaciones/spec.md` y `tasks.md` del change archivado, contra US-001 (06), RN-AG-01/02/15, RN-GL-02/03/04 (05) y D171 a D182 (10). No se editó nada.

## Veredicto

Sí, estaba listo para implementar. No encontré bloqueantes ni hallazgos mayores. Solo observaciones menores, ninguna impide arrancar el Apply.

## Lo que está bien

- **Cobertura de criterios.** CA-1 (alta, listado, editar, desactivar y reactivar, nombre único), CA-2 (duración) y CA-3 (turnos existentes congelados) tienen cada uno escenario feliz, de error y de borde. Cada escenario lleva el prefijo `US-001 CA-n`.
- **Códigos RN reales y bien usados.** RN-AG-15 (409), RN-AG-01 (422), RN-GL-04 (404 en la URL, 422 en el cuerpo), RN-AG-05 y RN-AG-08 juntos (E4). Todos existen en `05` y las D171 a D177 los respaldan. No hay reglas inventadas.
- **Clasificación según RN-GL-02.** RN-AG-01 es validación de entrada (422 y se informa junto con el resto de la entrada). RN-AG-15 es regla de negocio (409, solo con entrada válida). El escenario "duración inválida antes que nombre repetido" fija el orden. El formato mal formado va con 422 y `codigos` vacío.
- **Verificabilidad.** Los escenarios traen valores concretos (horas UTC, ids, colores, códigos HTTP), sin lenguaje vago.
- **Trazabilidad a tareas.** Cada escenario tiene tarea con test nombrado: unitarios en 2.x, repositorio en 3.x, casos de uso en 4.x y 5.x, API en 6.x y CA-3 en 7.x. La migración `0005` (INF-1) se prueba aparte, sin escenario propio, y está bien porque ya la cubre `persistencia-postgresql`.
- **TDD honesto.** Las tareas explican qué hacer con los tests que nacen verdes (romper la línea de producción a propósito), que es el caso de CA-3.

## Observaciones menores (no bloquean)

1. **Entrada con varios problemas a la vez.** RN-GL-02 manda informar juntos todos los problemas de entrada. Ningún escenario prueba, por ejemplo, `color` «azul» más `duracion_minutos` 47 en la misma petición (¿`codigos` `["RN-AG-01"]` y un error de campo para `color`?). Es un borde de RN-GL-02 sin escenario.
2. **Duración de tipo inválido.** `duracion_minutos` 45.5, «abc» o `null` cae en formato (422 sin código, `int` de Pydantic), no en RN-AG-01. El design lo implica pero ningún escenario lo dice. Conviene un caso en el escenario de formato.
3. **Sin tope máximo de duración.** Ni KB ni spec lo piden. Una duración enorme se frena recién al crear el turno (RN-AG-10d), no en la prestación. Es coherente con la KB, pero ningún escenario lo documenta como decisión.
4. **Renombrar a un nombre de una prestación inactiva.** El borde de inactivas solo se prueba en el alta. La edición usa la misma función, así que el riesgo es bajo.
5. **`reservable_online` en la edición.** Solo se prueba en el alta. El PATCH lo acepta y no hay escenario que cambie solo ese campo.
6. **Escenarios agrupados.** "Error de formato" del alta y "edición mal formada" juntan varios casos en un escenario. Se verifican bien con tests parametrizados (6.3), pero un fallo no apunta a un caso concreto.

## Conclusión

El spec cubre los tres criterios con sus tres tipos de escenario, usa solo códigos y decisiones existentes, respeta RN-GL-02 y RN-GL-04, y todas las tareas tienen su test. Las seis observaciones son mejoras opcionales.
