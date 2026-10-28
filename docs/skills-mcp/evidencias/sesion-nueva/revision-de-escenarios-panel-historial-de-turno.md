# Revisión de escenarios: `panel-historial-de-turno` (C-15)

Fecha: 2026-10-28. Revisión estática (sin correr suites). Las preguntas Q1 a Q6 del design están abiertas (D326 a D331, «Propuesta»); los hallazgos que dependen de una se marcan «condicional a Qn» y no son bloqueantes por sí solos.

**Veredicto**: listo con correcciones menores (condicionado a que el autor responda Q1 a Q6 y a que el `/opsx:update` registre D326 a D331). No hay bloqueantes.
**Base**: 5 escenarios (feliz 1, error de negocio 1, borde 3, otros 0); CA mínimos 3/3 (US-015 CA-1, E9 y HIS-2; el script solo ve US-015 CA-1 porque no lee E9 ni HIS-2 de la entrada C-15 de `CHANGES.md`); escenarios con tarea que los verifica 5/5 (el script marca «NO» porque las tareas citan `HIS-2x`, no un CA; cruzado a mano en «Cobertura»). Tamaño: 15 tareas en 6 grupos para 5 escenarios, dentro de `config.yaml` (3 a 6 escenarios, alrededor de 20 tareas).

## Hallazgos

| ID | Severidad | Control | Ubicación | Hallazgo | Fuente | Corrección propuesta |
|----|-----------|---------|-----------|----------|--------|----------------------|
| H1 | A corregir | C7/C6 | design G2, G4, G5, G9; tasks 2.3, 3.3; spec (requisito 1) | Comportamientos que el design y las tareas prueban o implementan y la spec no describe ni con requisito ni con escenario: un solo panel lateral a la vez (abrir «Historial» cierra «Nuevo turno» y al revés, test de 3.3), `actor_tipo` desconocido mostrado tal cual, `despues` incompleto sin detalle, respuesta de otra forma como `SinConexion` (2.3), la columna «Acciones» con el nombre accesible por fila, y el foco al título al abrir y de vuelta al botón al cerrar (G9, sin Q, sin escenario ni test). | `openspec/config.yaml` `rules.specs` (todo comportamiento con escenario); regla dura 9; design G9 | Sumar al requisito 1 «un solo panel a la vez» y un escenario borde (o ampliar `HIS-2c`) que lo cubra; para los tres casos defensivos de 2.3, decir en la tarea que son tests unitarios de `mensajes.ts` y `apiHistorial.ts` sin escenario propio, o agregarlos a `HIS-2b`; el foco: o se prueba (test más frase en la spec) o se saca de G9 y queda como estilo. |
| H2 | A corregir | C6 | design G2 («cambiar de día cierra el historial»); tasks 3.2 | La tarea 3.2 (GREEN) implementa el cierre del historial al cambiar de día, pero ninguna tarea RED lo prueba y la spec no lo dice. Código sin test que falle antes. | módulo Strict TDD (primera ley); `rules.tasks` | Agregar a 3.1 o 3.3 un test «cambiar de día cierra el historial» y su frase en la spec (ver H1), o sacar el comportamiento de 3.2. |
| H3 | A corregir | C5 | specs/pantalla-de-historial/spec.md, `HIS-2c` | El escenario encadena tres secuencias en un WHEN (turno 12 vacío, cambio al turno 11 con el 12 pendiente, «Cerrar») y el primer THEN («con el turno 12 a la vista, la lista vacía…») es incompatible con el orden del WHEN: si se pulsa el turno 11 mientras la respuesta del 12 está pendiente, la lista vacía del 12 nunca se muestra. La tarea 4.1 lo resuelve partiéndolo en tres tests, pero el escenario como está no se puede convertir en uno. | `rules.specs` (escenarios verificables con GIVEN/WHEN/THEN concretos); tasks 4.1 | Reescribir `HIS-2c` con tres bloques «en una corrida» (A: abrir 12 vacío; B: abrir 12 retenido, luego 11, soltar el 12; C: abrir y «Cerrar») o separar el cambio de turno en un `HIS-2f`. |
| H4 | Sugerencia | C10 | spec requisito 2 («Sin conexión o con un `5xx`»); tasks 4.3 | El requisito nombra el `5xx`, pero solo se prueba la caída de red (`caerse`). | spec requisito 2; design G6; D310 (criterio análogo de C-50) | Agregar el `500` como caso de `HIS-2e` y de 4.3 (o decir que `caerse` ya lo cubre). |
| H5 | Sugerencia | C10 | `HIS-2d` (segunda corrida) | «Un usuario sin roles» no puede llegar al botón «Historial»: `GET /turnos` exige el permiso de la agenda y da `403` (spec `pantalla-de-agenda`, escenario de rechazos). El `403` del historial solo es alcanzable en el falso quitando el permiso después de cargar la agenda. | spec `pantalla-de-agenda` (`403` `RN-AU-05` sin tabla); tasks 4.1 (`quitarPermiso`) | Redactar el GIVEN como «con la agenda ya cargada, al usuario se le quitó el permiso de historial» para que el escenario sea alcanzable y verificable. |
| H6 | Sugerencia | C10 | `HIS-2c` | Falta el borde simétrico de la respuesta tardía: la respuesta del historial que llega después de «Cerrar» (o de cambiar de día) no debe reabrir ni mostrar entradas. El escenario solo cubre la tardía tras cambiar de turno. | design G3 (bandera de vigencia); patrón de C-14 | Sumar un caso a 4.1: abrir con `retener`, «Cerrar», soltar y comprobar que el panel sigue cerrado. |
| H7 | Sugerencia | C7 | spec «Purpose», design «Contradicciones»; `CHANGES.md` C-15 | `HIS-2` está definido solo en `CHANGES.md` (la KB tiene HIS-1 de C-03); `CHANGES.md` es fuente válida del change y el design lo declara, así que es aceptable. Queda un detalle: US-015 dice «Como dueño» y la matriz de `03` da lectura a los tres roles. | `CHANGES.md` C-15; `06` §US-015; `03` fila «Historial de cambios de turno» (D68) | Al registrar D326 a D331, dejar anotado que HIS-2 vive en `CHANGES.md` y que manda la matriz de `03`. No hace falta tocar la KB. |

## Cobertura

| CA | Escenarios | Tarea que lo verifica |
|----|------------|-----------------------|
| US-015 CA-1 (solo lectura: sin acciones que creen, modifiquen o borren) | `HIS-2a` (ningún botón ni campo salvo «Cerrar») | 3.1, 3.3; navegador 6.1 |
| E9 (el evento `creado` aparece en la vista) | `HIS-2a` | 2.1, 2.2, 3.1; navegador 6.1 (turno creado desde la agenda de la demo) |
| HIS-2 (orden cronológico con actor y fecha) | `HIS-2b` | 2.1, 2.3, 3.3 |
| Vacío y cambio de turno | `HIS-2c` | 4.1 |
| Rechazos `404` `RN-GL-04` y `403` `RN-AU-05` | `HIS-2d` | 2.1, 4.1 |
| Carga, sin conexión, refresh y sesión irrenovable | `HIS-2e` | 4.3 |

Escenario a tarea (los 5): `HIS-2a` 2.1/3.1/3.3/6.1; `HIS-2b` 2.1/2.3/3.3; `HIS-2c` 4.1; `HIS-2d` 2.1/4.1; `HIS-2e` 4.3. La tarea 6.2 comprueba al menos un test por ID.

Alcance (C8): sin hallazgos. Solo frontend, sin cambios de API; editar eventos, historial para el paciente y auditoría de pacientes quedan fuera. Datos (C9): ficticios (Ana Ejemplo, Bruno Ficticio); sin teléfonos ni emails. Fechas (C4/C5): las conversiones a UTC−3 son correctas (`13:15Z` a 10:15; `02:30Z` del 1 de noviembre a 23:30 del 31 de octubre, borde de medianoche cubierto en `HIS-2b`) y los días de la semana coinciden con el calendario de 2026. Códigos RN (C3): `RN-GL-04` y `RN-AU-05` existen en `05`; el `404` con `RN-GL-04` en la URL sigue D166 y el orden de acceso antes que existencia, D208. Q-dependientes: los textos fijos están declarados como Propuesta (Q3 a Q5); sin hallazgo de C7 por eso. La capability nueva sin delta en `pantalla-de-agenda` es coherente: esa spec no fija la cantidad de columnas.

## Bordes sugeridos

- **Un panel a la vez**: GIVEN «Nuevo turno» abierto en la agenda del 2 de noviembre; WHEN pulsa «Historial» en la fila de Ana Ejemplo; THEN se ve «Historial del turno», no «Nuevo turno», y al pulsar «Nuevo turno» ocurre al revés. (H1; design G2)
- **Cambio de día cierra el historial**: GIVEN el historial del turno 11 abierto; WHEN pulsa «Día siguiente»; THEN el panel desaparece y no hay petición nueva de historial. (H2; design G2)
- **Respuesta tardía tras «Cerrar»**: GIVEN `retener` en `GET /turnos/11/historial`; WHEN abre, pulsa «Cerrar» y después se suelta la respuesta; THEN el panel sigue cerrado. (H6; design G3)
- **Error `500`**: GIVEN la API que responde `500`; WHEN abre el historial; THEN se ve el aviso de conexión con «Reintentar». (H4; spec requisito 2)

## Lo que no pude verificar

- Si `caerse` del servidor falso ya cubre el `5xx` o solo la caída de red (H4): depende del código de `servidorFalso.ts`, que no leí.
- Q3 (actor por número) y Q6 (el historial no filtra por consultorio): decisiones del autor; la KB no las resuelve. Si Q3 se responde con `actor_email`, el change deja de ser solo frontend y habría que rehacer alcance y gobernanza.
