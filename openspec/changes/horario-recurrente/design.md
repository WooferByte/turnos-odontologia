# Design: horario-recurrente

Change **C-12** (US-002 y la parte de horario de E10). Gobernanza **MEDIO**. Motivación y alcance en `proposal.md`; el comportamiento, en los cuatro specs del change (`horario-recurrente`, `pantalla-de-horario` y los deltas de `creacion-de-turnos` y `persistencia-postgresql`). Cada elección no confirmada por el autor está marcada **Propuesta**; las que salieron de una pregunta abierta citan su D y su Q («Decisión del autor (D257; Q3)»).

**Respuesta del autor (2026-10-22): las once preguntas abiertas se cierran con la recomendación del agente** («Aceptá Q1 a Q11 como se recomiendan y corré el update con los hallazgos H1 a H14 y los bordes que te parezcan»). Quedan como decisiones del autor D255 (H1, dos capabilities y dos deltas), D256 (H13, sin franjas no se admiten turnos), D257 (H6, código nuevo `RN-AG-16`), D258 (H9, una sola franja), D259 (H3 y H9, vigencia nula, fuera de la API y respetada por el dominio), D260 (H4 y H7, `GET /profesionales`), D261 (H5, el `PUT` no toca los turnos), D262 (H5, el profesional inactivo se edita), D263 (H13, horario de prueba de la fábrica), D264 (tamaño del Apply) y D265 (H9, sin `24:00`), registradas en `knowledge-base/10_preguntas_abiertas.md`; `RN-AG-16` quedó registrado en `knowledge-base/05_reglas_de_negocio.md` y en US-002 de `06`. En la misma revisión (`/opsx:update`) se incorporó el informe de `revisor-de-escenarios` (`docs/skills-mcp/evidencias/sesion-nueva/revision-de-escenarios-horario-recurrente.md`, que queda como el «antes»). **Sus hallazgos se citan como «hallazgo H1» a «hallazgo H14»** para no confundirlos con las decisiones H1 a H19 de este design. Se corrigieron los catorce hallazgos y se sumaron seis de los ocho bordes sugeridos (el resto ya estaba en un hallazgo); los specs pasan de 47 a **58 escenarios** y las tareas siguen siendo **31 en 13 grupos**, con la migración (grupo 5) movida antes que la regla en `crear_turno` (grupo 6) por el hallazgo H10. **Segunda revisión (2026-10-22).** El informe `revision-de-escenarios-horario-recurrente-despues.md` (hallazgos N1 a N7, sin bloqueantes) se incorporó con un segundo `/opsx:update`, y el autor aprobó las cuatro elecciones que seguían «Propuesta» y que el informe revisó contra la KB: **D266** (mensajes fijos de `RN-AG-16` y «válida» = «no invertida», H6), **D267** (sin profesionales activos se elige el primero de la lista, H15), **D268** (tope de 70 franjas en total, H4) y **D269** (error de red al guardar, H15). Se sumó el escenario de la cadena de tres franjas (N1): **59 escenarios**, con las mismas 31 tareas. Las demás decisiones marcadas «Propuesta» siguen así (gobernanza MEDIO: se implementan con puntos de control).

## Context

- `crear_turno` (`backend/app/application/crear_turno.py`) hoy hace: validación de entrada toda junta → `Intervalo.para_turno` (RN-AG-10d, con `uow.agenda.zona_horaria(consultorio_id)`) → `bloquear_recursos` → ocupados → `detectar_conflictos` → `agregar` + evento `creado`. No mira ningún horario: el paso 5 del Flujo 1 de `07` quedó afuera del primer change (P-10).
- `04` define `FranjaHoraria` (`profesional_id`, `dia_semana` 0-6, `hora_inicio < hora_fin` como `hora`, `vigente_desde` y `vigente_hasta` nulas, índice `(profesional_id, dia_semana)`) y deja al dominio la no superposición (US-002 CA-1). El seed de ejemplo es lunes a viernes 09:00-13:00 y 15:00-19:00 (D56).
- Migraciones en `backend/app/infrastructure/db/migraciones/versions/`, la última es **`0007`** (roles y creador). La suite por defecto usa `create_all` sobre SQLite; las migraciones se prueban en el perfil `postgres` (`tests/postgres/test_migraciones.py`).
- Matriz de `03`, fila «Horario recurrente y bloqueos»: `odontologo` CRUD, `recepcionista` R, `dueno` R. No hay ninguna ruta de profesionales todavía (ni listado ni detalle).
- Estado de las suites al proponer (dato del orquestador): backend 611 tests por defecto + 49 del perfil `postgres`; frontend 140.
- La pantalla de Stitch ya está (id copiado del canvas por el autor; ver «Referencia visual (Stitch)»).

## Goals / Non-Goals

**Goals:**
- Una regla pura de dominio para RN-AG-04 (franja que contiene al turno, en la zona del consultorio) y otra para la validez de un conjunto de franjas (RN-AG-16, D257), testeadas sin base de datos.
- Agregar RN-AG-04 a `crear_turno` sin cambiar lo que prueban los tests de C-01 a C-09 (H13).
- API y pantalla siguiendo los patrones de C-04, C-05, C-09 y C-11 (routers por recurso, `requiere(Permiso…)`, errores problem+json, servidor falso inyectado).

**Non-Goals:**
- Disponibilidad (C-24), bloqueos (C-13), reprogramación (que reutilizará la misma regla).
- Vigencia editable (D259), granularidad de las horas (US-005), franjas que crucen la medianoche o terminen a las 24:00 (D265).
- Garantizar en PostgreSQL que no haya franjas superpuestas (no hay restricción de exclusión para franjas: el `PUT` reemplaza todo en una transacción y valida antes; ver Risks).
- Coordinar un `PUT` del horario con un `POST /turnos` simultáneo (límite conocido, H11).

## Decisions

### H1. Dos capabilities nuevas y dos deltas — Decisión del autor (D255; Q1; sigue D241)

`horario-recurrente` (API) y `pantalla-de-horario` (interfaz), separadas por la suite que verifica cada una, como C-09 (D241, D218, D229). La regla RN-AG-04 en la creación es un **delta de `creacion-de-turnos`** (MODIFIED del requisito de E1 + dos ADDED), no un requisito de `horario-recurrente`, porque describe qué hace `POST /turnos`. `persistencia-postgresql` suma la tabla y el escenario de deshacer `0008`. Es una excepción a «una sola capability» limitada a C-12 (D255). **Alternativa descartada:** todo en `horario-recurrente`, incluido RN-AG-04 (dejaría el comportamiento de `POST /turnos` repartido en dos specs sin que `creacion-de-turnos` lo diga).

### H2. Estructura del backend — Propuesta (aplica `08`, «Estructura de directorios», y la regla dura 3)

```
backend/app/domain/agenda/horario.py        Franja, HorarioSemanal; validar_franjas (RN-AG-16); exigir_dentro_del_horario (RN-AG-04). Solo stdlib (datetime, zoneinfo).
backend/app/domain/errors.py                FranjaInvalida (RN-AG-16, error de campo), FueraDeHorario (RN-AG-04), ProfesionalNoEncontrado (404)
backend/app/domain/acceso/roles.py          Permiso.HORARIO_LEER (_TODOS), Permiso.HORARIO_EDITAR (_SOLO_EL_ODONTOLOGO), Permiso.PROFESIONALES_LEER (_TODOS)
backend/app/application/horario.py          listar_profesionales, obtener_horario, reemplazar_horario
backend/app/application/puertos.py          RepositorioHorario (franjas_de, reemplazar, profesionales_del_consultorio, profesional) + UnidadDeTrabajo.horario
backend/app/application/crear_turno.py      lee las franjas del día local y llama a exigir_dentro_del_horario (H10)
backend/app/infrastructure/db/modelos.py    FranjaHorariaModelo
backend/app/infrastructure/repositories/horario.py
backend/app/infrastructure/db/migraciones/versions/0008_franja_horaria.py
backend/app/api/routers/profesionales.py    GET /profesionales, GET y PUT /profesionales/{id}/horario
backend/app/api/esquemas.py                 FranjaEntrada/Salida, ReemplazarHorarioEntrada, HorarioSalida, ProfesionalSalida
```

### H3. Modelo y migración `0008` — Propuesta (aplica `04` y `database-migration`; columnas de vigencia por D259)

`franja_horaria`: `id` PK; `profesional_id` FK → `profesional` `ON DELETE RESTRICT`; `dia_semana` `SmallInteger` con `CHECK dia_semana BETWEEN 0 AND 6`; `hora_inicio` y `hora_fin` `Time` sin zona con `CHECK hora_inicio < hora_fin`; `vigente_desde` y `vigente_hasta` `Date` nulas con `CHECK vigente_hasta >= vigente_desde` si ambas existen (†7 de `04`); índice `ix_franja_horaria_profesional_dia (profesional_id, dia_semana)`. Generada con autogenerate y revisada a mano; `downgrade` borra solo la tabla. Sin datos en la migración: el horario de la demo lo carga el seed (H12). Las horas no son fechas-hora: no entran en el guard de «columnas de fecha-hora con zona» (A verificar V2).

### H4. Contrato de la API — Decisión del autor (`GET /profesionales`: D260; vigencia: D259; tope de 70 franjas: D268) + Propuesta (forma)

- `GET /profesionales` → `200` `[{id, nombre, activo}]` del consultorio, por `id` (D260).
- `GET /profesionales/{id}/horario` → `200` `{profesional_id, zona_horaria, franjas: [{dia_semana, hora_inicio, hora_fin}]}`, franjas por `(dia_semana, hora_inicio)`. Un `id` no entero → `422` de formato (escenario propio).
- `PUT /profesionales/{id}/horario` con `{franjas: [...]}` (`extra="forbid"`, lista obligatoria, puede ser vacía) → `200` con la misma forma que `GET`. Horas como texto `HH:MM` (patrón `^([01]\d|2[0-3]):[0-5]\d$`) para que la salida sea siempre `09:00` y no `09:00:00`; `dia_semana` entero 0 a 6. **Tope de 70 franjas en total por pedido** (un tope de tamaño del cuerpo, no por día; hallazgo N2): `422` de formato con `codigos` vacío y el error en el campo `franjas`. Decisión del autor (D268; la KB no fija ningún tope); tiene escenario y test de RED propios (71 se rechaza, 70 se acepta; hallazgo H3).
- La vigencia no viaja en la API (D259): se guarda nula.

### H5. Reemplazo — Decisión del autor (D261; Q7. D262; Q8) + Propuesta (forma)

`reemplazar_horario` abre la unidad de trabajo, valida las franjas (H6), busca el profesional (404 si no existe o es de otro consultorio; este último con escenario propio, armado con las fábricas porque la instalación tiene un solo consultorio, D173), borra sus franjas e inserta las nuevas en la misma transacción. Si algo falla, nada cambia. No toca ni informa turnos (D261). Un profesional inactivo se edita igual (D262).

### H6. Validez de las franjas: `RN-AG-16` — Decisión del autor (D257; Q3. Mensajes y franjas informadas: D266)

Función pura `validar_franjas(franjas) -> tuple[FranjaInvalida, ...]`: recorre la lista **en el orden del cuerpo**; una franja con `hora_inicio >= hora_fin` se informa como invertida y no se compara con las demás; una válida que se superpone (`a.inicio < b.fin and b.inicio < a.fin`, semiabierto) con **alguna anterior válida del mismo día** se informa (dos franjas idénticas se superponen: se informa la segunda). **«Válida» es «no invertida»**: una anterior ya informada por superponerse sigue contando, así que con miércoles 09:00-13:00, 12:00-16:00 y 15:00-19:00 se informan `franjas.1` y `franjas.2` (D266; escenario propio de la API, hallazgo N1, que es el contrato que copia el servidor falso). Cada error lleva `campo` `franjas.<i>`, `codigo` `RN-AG-16` y un **mensaje fijo según la causa** (D266, hallazgo H12; sigue el estilo de los errores de campo existentes, «`<campo>` debe …»): `franjas.<i> se superpone con otra franja del mismo día` o `franjas.<i> debe terminar después de empezar`. Si hay alguno, `EntradaInvalida` con todos (un `422`, RN-GL-02). Contiguas no se superponen. El número `RN-AG-16` solo había aparecido en D183 como alternativa descartada para el nombre de un sillón (hallazgo H1): estaba libre.

### H7. Permisos — Decisión del autor (matriz de `03`; `GET /profesionales` para los tres roles: D260) + Propuesta (nombres)

`horario.leer` y `profesionales.leer`: los tres roles; `horario.editar`: solo `odontologo`. Se usa `requiere(...)` como en `/sillones`, así el guard de rutas protegidas las cubre.

### H8. Clases de rechazo y orden de evaluación — Decisión del autor por la KB (orden de `POST /turnos`: `07` Flujo 1 pasos 4 a 6, `05` RN-AG-10d y RN-AG-08, RN-GL-02 y D135; clase de `RN-AG-16`: D257) + Propuesta (orden del `PUT`, aplica D208 y el orden de U13 de C-09)

**Orden de las reglas de negocio de `POST /turnos`** (hallazgo H7): validación de entrada → RN-AG-10d → RN-AG-04 → solapamiento (RN-AG-05, RN-AG-08). No es una elección de este design sino lo que ya fija la KB: el Flujo 1 de `07` pone la medianoche en el paso 4, el horario en el paso 5 y el solapamiento en el paso 6; `05` dice en RN-AG-10d que la medianoche se evalúa antes del solapamiento y en RN-AG-08 / RN-GL-02 que el solapamiento se evalúa solo con la entrada válida y de a una regla. RN-GL-02 escribe hoy el «orden en el primer change» sin RN-AG-04: se completa al archivar (ver «Notas para el archive»). Ninguna D nueva lo cambia; la respuesta a Q1 a Q11 no lo tocó.

| # | Clase | `GET /profesionales/{id}/horario` | `PUT /profesionales/{id}/horario` | `POST /turnos` |
|---|---|---|---|---|
| 0 | Límite de FastAPI | — | JSON roto: `422` sin código | igual |
| 1 | Control de acceso | `401` `RN-AU-03` | `401`; `403` `RN-AU-05` | `401`; `403` |
| 2 | Formato (Pydantic) | `id` no entero: `422` | `422` `codigos` vacío: `id`, día, hora, campo de más, tope de 70 | igual que antes |
| 3 | Validación de entrada del dominio | — | `422` `RN-AG-16` (todas juntas) | `422` `RN-GL-01` y/o `RN-GL-04` (todas juntas) |
| 4 | Recurso de la URL | `404` `RN-GL-04` | `404` `RN-GL-04` | — |
| 5 | Reglas de negocio, de a una | — | — | `422` `RN-AG-10d` → `422` `RN-AG-04` → `409` `RN-AG-05`/`RN-AG-08` |

Los órdenes 1 → 3 → 4 del `PUT` y 10d → 04 → solapamiento de `POST /turnos` tienen escenario propio. `FueraDeHorario` → `422`, `/errores/fuera-de-horario`, «Fuera de horario», `detail` fijo «El turno no cae completo dentro de una franja del horario del profesional.» (sin repetir horas). `FranjaInvalida` viaja dentro de `EntradaInvalida` como error de campo (como `DuracionInvalida`).

### H9. La regla RN-AG-04 — Decisión del autor (D256; Q2. D258; Q4. D259; Q5. D265; Q11) + Propuesta (forma; aplica RN-AG-04, RN-GL-01 y RN-AG-09)

`exigir_dentro_del_horario(intervalo, franjas_del_dia, zona)`: convierte `inicio` y `fin` a `ZoneInfo(zona)`; el día de la semana es el de `inicio` local (`weekday()`, 0 = lunes, igual que `dia_semana`); acepta si existe **una** franja vigente ese día con `hora_inicio <= inicio_local.time()` y `fin_local.time() <= hora_fin`, con `fin_local` en la misma fecha local (si `fin` cae a las 00:00 del día siguiente, ninguna franja lo contiene, porque `hora_fin` llega a 23:59; D265, con escenario propio: el turno de 23:30 a 00:00 pasa RN-AG-10d y recibe `RN-AG-04`). Vigente: `vigente_desde` nula o `<= fecha local` y `vigente_hasta` nula o `>= fecha local` (D259; con escenario de integración, la franja guardada con vigencia por la fábrica, porque la API no la expone; hallazgo H5). Sin franjas ese día, o sin ninguna, `FueraDeHorario` (D256). Si no, `FueraDeHorario`. Una sola franja, no la unión de contiguas (D258).

### H10. Lugar de RN-AG-04 en `crear_turno` — Propuesta (el orden respecto de las otras reglas lo fija la KB, H8)

Después de `Intervalo.para_turno` (RN-AG-10d) y **antes** de `bloquear_recursos`: `franjas = uow.horario.franjas_de(profesional.id)` (todas; son pocas) y `exigir_dentro_del_horario(...)`. Así un turno fuera de horario no toma bloqueos de fila, y el solapamiento solo se evalúa con la regla de horario cumplida (escenario «el horario se informa antes que el solapamiento»). El reintento ante carrera (E11) repite todo, incluida esta lectura.

### H11. `PUT` y `POST /turnos` simultáneos — Propuesta (límite conocido)

El `PUT` no toma el bloqueo del profesional; un turno creado mientras se reemplaza el horario se evalúa con el horario anterior o el nuevo según qué transacción lea primero. Es el mismo efecto que crear el turno un instante antes de cambiar el horario, que la KB acepta (el cambio no toca turnos existentes, D261). Se documenta en el README. **Alternativa descartada:** que el `PUT` tome `bloquear_recursos` del profesional (más acoplamiento sin una regla que lo pida).

### H12. Seed de la demo — Decisión del autor (D56) + Propuesta (forma)

`cargar_demo` agrega las diez franjas del profesional 1. Para PostgreSQL, `cargar_horario_demo_si_falta(sesion)` (como `cargar_roles_demo_si_faltan`): inserta solo si el profesional 1 no tiene ninguna franja. Las franjas no llevan id fijo (no hace falta citarlas en el README), así que `ajustar_secuencias` no cambia. **Límite:** si el autor deja al profesional 1 sin franjas con un `PUT` vacío, el próximo arranque del contenedor vuelve a cargar el horario de ejemplo (README).

### H13. Riesgo: tests que se rompen — Decisión del autor (D256; Q2. D263; Q9) + Propuesta (orden de las tareas)

**Qué rompe RN-AG-04 si no se hace nada.** Con «sin franjas = no admite turnos» (D256), todo test que hoy crea un turno por el caso de uso o por `POST /turnos` con un profesional de la fábrica `un_profesional` pasaría a recibir `422` `RN-AG-04`: `tests/integration/test_crear_turno.py` (12 usos de la fábrica), `test_post_turnos.py`, `test_sillones_y_turnos.py`, `test_historial.py` (API e integración), `test_proteccion*.py`, `test_unidad_de_trabajo.py`, `test_prestaciones.py` (API), `test_usuarios.py` y, en el perfil `postgres`, `carrera.py` (E11) y `test_historial_inmutable.py`. Además, aunque se cargara un horario «realista» (09-13 y 15-19 del consultorio), los escenarios de C-01 usan las 10:00 UTC del 2026-11-02, que son las **07:00** de Buenos Aires: quedarían todos fuera. Los tests que guardan turnos directo con `un_turno` (sin el caso de uso) no se ven afectados. El frontend (140) no crea turnos: solo puede cambiar algún test que cuente los enlaces de la barra (A verificar V3).

**Lo que no rompe.** La demo y su README: `2026-11-02T13:00:00Z` y `2026-11-03T13:00:00Z` son lunes y martes 10:00 del consultorio, dentro de 09-13; `13:30` también (`test_demo.py`, `test_seed_y_api.py`). El cruce de medianoche (`2026-11-03T02:45Z`) sigue dando solo `RN-AG-10d`, porque se evalúa antes (H10). Los tests unitarios de `Intervalo` no pasan por el horario.

**Decisión del autor (D263).** `un_profesional(sesion, consultorio, horario=HORARIO_DE_PRUEBA, **kw)` en `tests/factories.py`: por defecto guarda siete franjas **00:00-23:59, de lunes a domingo**, así todos los tests existentes siguen probando lo mismo sin cambiar sus horas ni sus aserciones; `horario=()` deja al profesional sin franjas y `horario=(franja(0, "09:00", "13:00"), …)` arma el de un escenario de E10. El único hueco del horario de prueba es el minuto 23:59-00:00 local (02:59-03:00 UTC): ningún test existente crea un turno ahí (búsqueda hecha en el propose: los únicos turnos cerca de la medianoche local son el de `RN-AG-10d`, que se rechaza antes, y uno de `test_eventos.py`, que es unitario). El orden de los cambios en las tareas es: primero la fábrica con el horario por defecto y la tabla (grupo 3, la suite por defecto sigue en verde), después la migración `0008` (grupo 5, el perfil `postgres` en verde con el horario de prueba y todavía sin la regla) y recién después la regla en `crear_turno` (grupo 6), que se compara contra las dos suites: la por defecto y, si hay Docker, enseguida el perfil `postgres` (hallazgo H10; el perfil arma el esquema con las migraciones, así que entre 3.2 y 5.2 no se corre). Si después de la regla algún test existente cambia de resultado, se frena y se analiza: no se «arregla» moviendo horas sin entender por qué.

**Los escenarios E2 a E7 y E12 de `creacion-de-turnos`** (hallazgo H9) usan las 10:00 UTC del 2026-11-02, que son las **07:00** del consultorio: con un horario «realista» quedarían fuera de RN-AG-04. Siguen valiendo sin cambios porque el delta lo dice en el requisito de RN-AG-04 («salvo que un escenario diga otra cosa, en esta capability el profesional tiene una franja que cubre el turno pedido») y sus tests usan la fábrica con el horario de prueba 00:00-23:59 (D263). Un delta no puede cambiar el `Purpose` de la spec principal, que es donde vive esa convención para todos los escenarios: se actualiza a mano al archivar (ver «Notas para el archive»).

**Alternativas descartadas:** (a) agregar el horario a mano en cada test (unos 40 lugares, mucho ruido y riesgo de cambiar lo que prueban); (b) un fixture `autouse` de pytest que cargue franjas a todo profesional (escondido, y no sirve para los tests que crean profesionales con la sesión directa); (c) Q2 opción «sin franjas = sin validación», que evitaría tocar las fábricas pero contradice RN-AG-04.

### H14. Estructura del frontend — Propuesta (aplica U17 de C-09 y T3 de C-11)

```
frontend/src/features/horario/apiHorario.ts (+ .test.ts)   listarProfesionales, obtenerHorario, reemplazarHorario; respuestas validadas sin any; traducirRechazo
frontend/src/features/horario/PaginaHorario.tsx (+ .test.tsx)  estados: cargando / sin-conexion / lista; selector; aviso de guardado o de error
frontend/src/features/horario/SemanaDeHorario.tsx             siete filas; FranjaEditable con <input type="time" step="60">
frontend/src/features/horario/mensajes.ts (+ .test.ts)        textos fijos de H17
frontend/src/shared/iconos/IconoReloj.tsx                     SVG en línea, aria-hidden
frontend/src/App.tsx, pages/PanelBase.tsx                     ruta hija "horario" y enlace «Horario»
frontend/src/test/servidorFalso.ts                            GET /api/profesionales, GET/PUT /api/profesionales/{id}/horario con el orden de H8, el tope de 70 y RN-AG-16 como H6; quitarProfesional(id); marcar inactivo; respuesta retenida; falla de red en el PUT
```

### H15. Pantalla — Decisión del autor (profesional sin activos: D267; error de red al guardar: D269) + Propuesta (resto; aplica `vercel-react-best-practices`)

Una sola carga al montar (profesionales y después el horario del elegido: el primero activo o, **si ninguno está activo, el primero de la lista** con «(inactivo)»; D267, borde sugerido 6 de la primera revisión: el requisito decía «el primero activo» sin cubrir ese caso; la lista vacía no se cubre porque la demo siempre trae al profesional 1 y ninguna ruta borra profesionales, D46); el estado editable es una copia del horario recibido; «Guardar horario» compara con lo recibido (sin cambios no pide nada), arma el cuerpo ordenado por día y hora y lo manda; con el `200` reemplaza la copia por lo que devolvió la API. Los errores `RN-AG-16` se ubican por la posición del cuerpo enviado (`franjas.<i>`): esas franjas llevan `aria-invalid="true"` y la fila de su día muestra el mensaje una vez. Cambiar de profesional descarta lo editado sin preguntar (como «Cancelar» en C-09). Sin validación local más allá de las dos horas presentes (como D232: la API decide; una franja invertida se manda y vuelve con `RN-AG-16`, escenario propio). «Guardar horario» se deshabilita mientras espera: un segundo clic no manda otro `PUT` (escenario propio con la respuesta retenida, hallazgo H4). Si el `PUT` no responde, se ve el mensaje de conexión de C-11, se conserva lo editado y el botón vuelve a habilitarse (D269; escenario propio; sin «Reintentar», que es de la carga).

### H16. Acciones visibles para todos los roles — Propuesta (sigue D230 y D249)

La pantalla no conoce el rol: «Agregar franja», «Quitar» y «Guardar horario» se ven para la recepcionista y el dueño, y la API responde `403` `RN-AU-05` al guardar. Límite del README.

### H17. Mensajes fijos de la pantalla — Propuesta (como T11 de C-11 y U19 de C-09)

«Cargando horario…»; el de conexión de C-11; «Sin atención»; «Horario guardado.»; «Completá las dos horas de la franja.»; `RN-AG-16`: «Hay franjas que se superponen o no terminan después de empezar (RN-AG-16).»; nota: «Los turnos solo se pueden crear dentro de una franja (RN-AG-04). Cambiar el horario no modifica los turnos ya dados.»; `RN-AU-05`: «Tu usuario no tiene permiso para modificar el horario (RN-AU-05).»; `RN-GL-04`: «El profesional ya no existe (RN-GL-04).»; `422` sin código: «Revisá las franjas del horario.» (con escenario propio: 71 franjas, el tope de H4; hallazgo H11); subtítulo: «Franjas semanales en hora del consultorio (<zona_horaria>).». No se muestra el `detail` de la API.

### H18. Tests y servidor falso — Decisión del autor (D222, D227, reglas duras 5 y 6) + Propuesta (detalle)

Backend: unitarios de `domain/agenda/horario.py` (sin base), integración del repositorio y del caso de uso con SQLite en memoria, API con tokens reales (D211), perfil `postgres` para `0008` (INF-1) y la carga repetible de la demo. Frontend: Vitest con el servidor falso inyectado, sin `vi.mock`/`vi.fn`. Los nombres de los tests citan el escenario (`US-002 CA-1`, `US-002 CA-2`, `E10`, `HOR-1`, `INF-1`, `US-092 CA-1`).

### H19. Versiones y dependencias — Propuesta

**Sin dependencias nuevas** ni cambios de versión: `zoneinfo` es de la biblioteca estándar y `tzdata` ya está declarado en `backend/pyproject.toml` (contexto de `config.yaml`); `Time` y `Date` son tipos de SQLAlchemy 2.0 ya instalado. `frontend/package.json` y `package-lock.json` no cambian. Por eso no hay pins nuevos que fijar (regla de `config.yaml`).

### Skills aplicadas

- `python-design-patterns`: reglas puras en el dominio y el caso de uso como orquestador; una función por regla (RN-AG-04, RN-AG-16).
- `python-error-handling`: errores de dominio con código; validación de entrada junta (RN-AG-16) y reglas de a una (RN-AG-10d → RN-AG-04 → solapamiento).
- `python-testing-patterns`: TDD estricto; bordes de los límites (franja exacta, un minuto de más, contiguas, día local distinto del UTC); fábrica con horario por defecto explícito y desactivable; sin mocks.
- `fastapi-templates`: router por recurso, esquemas de entrada y salida separados, dependencias. **No aplica** su parte asíncrona (DD-12, regla dura 5).
- `database-migration`: una migración reversible por cambio de esquema, tabla nueva sin tocar las existentes, autogenerate revisado a mano. **No aplican** sus ejemplos JavaScript ni la tabla de respaldo destructiva.
- `supabase-postgres-best-practices`: índice en la FK (`profesional_id`, primero en el compuesto), `CHECK` en la base como red, tipos propios (`time`, `date`). **No aplican** RLS ni lo específico de Supabase.
- `vercel-react-best-practices` (SPA de Vite): una carga al montar, estado derivado en el render, `setState` funcional, sin componentes definidos dentro de otros, ternario en vez de `&&`.

## Referencia visual (Stitch)

- **Pantalla**: `projects/14200813501064679723/screens/c3cccdb362364deba0d4eaac0d678b4d` («Horario de atención - Turnos Odontológicos AR», `DESKTOP`), generada con el design system «Clinical Ops» (`assets/b683d44391ab410db2dd48aa71ed0b47`). El MCP no devolvió el id (un intento terminó por tiempo de espera y el otro sin id); la generación quedó en el canvas y el autor copió el `node-id` el 2026-10-22.
- **Evidencia**: `docs/skills-mcp/evidencias/sesion-nueva/stitch-horario.md` (pedido, intentos y revisión de datos) y `stitch-horario-pantalla/pantalla.png` (1280 × 1101) y `pantalla.html`.

**Qué se toma:**
- La barra del panel con la pastilla «Horario» activa (la barra es la compartida de C-08, C-11 y C-09: solo se suma el enlace).
- El encabezado: «Horario de atención», el subtítulo «Franjas semanales en hora del consultorio (<zona>).» con la `zona_horaria` que devuelve la API, el selector con la etiqueta «Profesional» y el botón primario «Guardar horario» con un ícono de guardar (SVG en línea).
- La nota informativa azul con ícono «Los turnos solo se pueden crear dentro de una franja (RN-AG-04). Cambiar el horario no modifica los turnos ya dados.» (respaldo: RN-AG-04 y D261), sin la etiqueta «Aviso regulatorio:».
- La tarjeta «Semana» con una fila por día: el nombre a la izquierda; cada franja como una caja con «Desde» y «Hasta» y un botón «Quitar» con ícono de papelera (nombre accesible «Quitar franja»); «Agregar franja» con ícono de más; «Sin atención» en gris en un día vacío.
- El estilo del error de `RN-AG-16`: borde rojo en las franjas informadas (con `aria-invalid="true"` en sus campos), borde izquierdo rojo en la fila del día y un solo mensaje con ícono debajo de sus franjas (el texto es el de H17, no el de Stitch).

**Qué se rechaza (motivo):**
- La insignia «7 días», el texto «Doble turno estándar y atención programada», el contador «2 franjas» y «Cerrado» bajo cada día, y «Conflicto detectado» con su ícono junto al nombre del día: sin respaldo en la KB ni escenario; «Sin atención» y el mensaje de `RN-AG-16` ya lo dicen.
- El pie de la tarjeta («Configuración activa para la agenda online y recepción», «Zona horaria clínica: UTC-3 (Buenos Aires)»): la reserva online no existe todavía (C-26) y la zona ya está en el subtítulo, leída de la API y no fija.
- El pie de página («Módulo de Control de Horarios y Disponibilidad Clínica · Sede Central»): no hay sedes (D173) ni existe en las otras pantallas.
- Los profesionales que Stitch inventó en el selector: las opciones salen de `GET /profesionales`.
- El borde rojo en **las dos** franjas de un par superpuesto: la API informa solo la posterior de cada par (H6, D266); se marcan las informadas (en la cadena de tres del miércoles, la segunda y la tercera, no la primera).
- Campos de texto para las horas: se usan `<input type="time">` (teclado y formato del navegador); la fuente monoespaciada pasa a cifras tabulares.
- Tailwind, Google Fonts y Material Symbols por CDN (CSP `default-src 'self'`): se traduce a `tokens.css` y `panel.css` (sección «Pantalla de horario») sin dependencias nuevas; íconos en SVG en línea con `aria-hidden="true"`.

La KB y los specs mandan sobre el contenido; la prueba en el navegador (grupo 12) compara la implementación con `pantalla.png` y anota las diferencias en la evidencia.

## Contradicciones y huecos encontrados en las fuentes

- **Profesional sin horario**: la KB no lo dice. RN-AG-04 («solo puede crearse si cae completo dentro de una franja vigente») lleva a rechazar; US-080 CA-7 menciona «sin horario configurado» solo para el reporte. → Q2, resuelto por D256 (se rechaza con `RN-AG-04`).
- **Código de las franjas inválidas**: `04` deja la no superposición «al dominio» sin código, pero la regla dura 4 exige uno para todo rechazo de regla. → Q3, resuelto por D257 (`RN-AG-16` en `05`).
- **Franjas contiguas**: RN-AG-04 dice «dentro de una franja»; un turno que pasa de 09-13 a 13-17 queda afuera aunque el profesional atienda sin corte. → Q4, resuelto por D258 (se rechaza).
- **Vigencia**: `04` tiene `vigente_desde`/`vigente_hasta`, RN-AG-04 dice «franja vigente» y US-080 CA-9 las usa, pero ninguna historia pide editarlas. → Q5, resuelto por D259 (nulas, fuera de la API, respetadas por el dominio).
- **Selección del profesional en la pantalla**: no hay ninguna ruta de profesionales y la pantalla necesita un id. → Q6, resuelto por D260 (`GET /profesionales`; amplía el alcance escrito de C-12 en `CHANGES.md`, que se ajusta al archivar).
- **Escenarios de C-01 en UTC**: las 10:00 UTC de los escenarios son las 07:00 del consultorio; con el horario de la demo quedarían fuera. Se resuelve con el horario de prueba (D263, H13), no cambiando los escenarios.
- **Regla dura 2 de `CLAUDE.md` y `AGENTS.md`** (hallazgo H8): dice que la conversión a la zona del consultorio es excepción **solo** de RN-AG-10d, y C-12 convierte también para RN-AG-04. No hay conflicto con la KB (`05` RN-GL-01: «las reglas de horario se evalúan en la zona del consultorio»); el texto de la regla dura queda desactualizado y se amplía al archivar.
- **`07` Flujo 1** (hallazgo H9): el paso 5 («Fuera del primer change… Dominio valida horario recurrente») y el caso de error «Fuera de horario o sobre bloqueo… (fuera del primer change)» quedan falsos al archivar C-12 para la parte de horario. Se ajustan al archivar.

## Risks / Trade-offs

- [Tests que pasan a dar `RN-AG-04`] → horario de prueba por defecto en la fábrica antes de agregar la regla (D263, H13); red de seguridad en 1.1, comparación en 6.2 con las dos suites y de la cantidad de tests en 13.1.
- [El perfil `postgres` queda roto entre 3.2 y 5.2] → la fábrica ya inserta franjas y la tabla todavía no existe en las migraciones; el perfil no se corre en ese tramo y la migración va antes que la regla (H13, hallazgo H10).
- [El horario de prueba esconde un bug de zona] → los escenarios de E10 usan horarios acotados (`horario=` explícito) y el borde «día local distinto del UTC».
- [Franjas superpuestas guardadas por otro camino] → solo el `PUT` escribe franjas y valida antes; no hay restricción de exclusión en la base (H3). El seed carga franjas válidas.
- [`PUT` y `POST /turnos` a la vez] → límite aceptado (H11).
- [Reiniciar el contenedor repone el horario de ejemplo] → límite del README (H12).

## A verificar en el change

- **V1** (antes de 2.1): que `datetime.weekday()` del `inicio` convertido con `ZoneInfo("America/Argentina/Buenos_Aires")` dé el día local esperado en los bordes de E10 (lunes 21:30 local = martes 00:30 UTC).
- **V2** (antes de 3.1): que el guard de columnas de fecha-hora con zona (`tests/integration/test_guard_fechas.py`) no exija zona a columnas `Time`/`Date`; si lo hace, se ajusta el guard para que mire solo `DateTime`, sin aflojarlo.
- **V3** (antes de 8.1): si algún test de C-08, C-11, C-49 o C-09 cuenta los enlaces de la barra del panel; si lo hace, se actualiza sumando «Horario» y se anota.
- **V4** (antes de 4.1): cómo informa hoy la API la ubicación de un error de Pydantic dentro de una lista (`campo`), para que `franjas.<i>` de `RN-AG-16` use la misma forma.
- **V5** (antes de 5.2): que `alembic upgrade head` y `downgrade 0007` sobre PostgreSQL 17.10 dejen el esquema del modelo (INF-1) con los `CHECK` de la tabla.

## Migration Plan

0. Q1 a Q11 ya están respondidas (D255 a D265, 2026-10-22) y los artefactos ajustados con `/opsx:update` junto con el informe de `revisor-de-escenarios`. Con el ok del autor (dado el 2026-10-22, con D266 a D269 y la segunda revisión), se commitean los artefactos y, en un commit `docs(kb)` aparte, D255 a D269 y `RN-AG-16` ya registrados en la KB.
1. `0008_franja_horaria` (solo crea la tabla; `downgrade` la borra). Sin datos.
2. Al arrancar el contenedor de la API, `cargar_horario_demo_si_falta` carga el horario de ejemplo del profesional 1 si no tiene franjas (después de `cargar_demo_si_falta` y antes de `ajustar_secuencias`).
3. **Efecto visible**: desde este change, `POST /turnos` fuera del horario responde `422` `RN-AG-04`. Una base de la demo sin franjas para un profesional (si se lo deja vacío) rechaza todos sus turnos.
4. Rollback: `alembic downgrade 0007` y volver al commit anterior; la regla y la tabla se van juntas.

## Notas para el archive

- `knowledge-base/10_preguntas_abiertas.md`: D255 a D269 ya están registradas (2026-10-22; D266 a D269 son las cuatro «Propuesta» aprobadas tras la segunda revisión: mensajes de `RN-AG-16`, primer profesional de la lista, tope de 70 y error de red al guardar); al cerrar se registran las demás decisiones «Propuesta» que el autor apruebe y los hallazgos del Apply (V1 a V5).
- `05`: `RN-AG-16` ya está registrado (D257, 2026-10-22); al archivar, «a implementar en C-12» pasa a «implementada en C-12». En RN-AG-04, anotar que se implementó en C-12 (con D256, D258, D259 y D265). En RN-GL-02, el «Orden en el primer change» pasa a incluir RN-AG-04: entrada → RN-AG-10d → RN-AG-04 → solapamiento (H8, hallazgo H7); y en la clase **«Validación de entrada»** de RN-GL-02 se agrega `RN-AG-16` (franjas superpuestas o invertidas, todas juntas; D257), para que la clase quede dicha en la regla madre y no solo en RN-AG-16 y D257 (hallazgo N5).
- `06`: US-002 ya cita `RN-AG-16` (D257); al archivar, E10 pasa a «parte de horario en C-12; bloqueos en C-13» y US-002 CA-1 y CA-2 quedan implementadas.
- `07` Flujo 1 (hallazgo H9): el paso 5 («Fuera del primer change… Dominio valida horario recurrente») pasa a «desde C-12» (con `422` `RN-AG-04`, después de RN-AG-10d y antes del solapamiento), y el caso de error «Fuera de horario o sobre bloqueo… (fuera del primer change)» dice que el horario se valida desde C-12 y el bloqueo en C-13.
- `02`: fila «Horario» con `GET /profesionales` (D260). `03`: anotar `GET /profesionales` (tres roles) en la fila «Horario recurrente y bloqueos».
- `04` §FranjaHoraria: la no superposición y el inicio antes del fin los valida el dominio con `RN-AG-16` (D257); la vigencia no viaja en la API (D259).
- `08`: `features/horario/` y `domain/agenda/horario.py` en la «Estructura de directorios»; en el «Mapeo a HTTP», una fila para `RN-AG-04` (regla de negocio, `422`, `/errores/fuera-de-horario`, entre RN-AG-10d y el solapamiento) y otra para `RN-AG-16` (validación de entrada, `422`, error de campo `franjas.<i>`).
- `openspec/specs/creacion-de-turnos/spec.md`: actualizar a mano la convención del `Purpose` («el profesional tiene una franja que cubre el turno salvo que el escenario diga otra cosa»; E2 a E7 y E12 usan las 07:00 del consultorio, hallazgo H9), que un delta no puede cambiar; opcional: que el requisito «Rechazar las referencias inválidas» nombre también el horario entre las reglas que no se evalúan con entrada inválida.
- `CHANGES.md`: `[x]` en C-12; por D260, sumar `GET /profesionales` (solo lectura) al «Alcance — dentro» de C-12 (hallazgo H6); repetir `scripts/verificar_changes.py`.
- `CLAUDE.md` y `AGENTS.md`: regla dura 2, la excepción de la zona del consultorio pasa a cubrir RN-AG-10d **y RN-AG-04** (RN-GL-01; hallazgo H8); párrafo «Estado de `10_preguntas_abiertas.md`» con D255 a D269.

## Open Questions

Ninguna. Las once preguntas del propose quedaron cerradas por el autor el 2026-10-22, todas con la recomendación del agente:

- **Q1 → D255.** Dos capabilities nuevas (`horario-recurrente` y `pantalla-de-horario`) y dos deltas, como excepción a «una sola capability» limitada a C-12 (H1).
- **Q2 → D256.** Un profesional sin franjas, o sin franjas ese día, no admite turnos: `422` `RN-AG-04` (H9, H13).
- **Q3 → D257.** Código nuevo `RN-AG-16`, validación de entrada, `422` con todas juntas; ya registrado en `05` y en US-002 de `06` (H6).
- **Q4 → D258.** El turno debe caber en una sola franja; las contiguas no se suman (H9).
- **Q5 → D259.** Vigencia nula, fuera de la API y respetada por el dominio, con escenario de integración (H3, H9).
- **Q6 → D260.** `GET /profesionales` de solo lectura para los tres roles; el alcance de C-12 en `CHANGES.md` se ajusta al archivar (H4, H7).
- **Q7 → D261.** El `PUT` no toca ni informa los turnos existentes (H5).
- **Q8 → D262.** El horario de un profesional inactivo se lee y se edita (H5).
- **Q9 → D263.** La fábrica `un_profesional` carga por defecto 00:00-23:59 de lunes a domingo; `horario=()` lo deja sin franjas (H13).
- **Q10 → D264.** 31 tareas en 13 grupos para 59 escenarios (después de los dos `/opsx:update`) como excepción limitada a C-12.
- **Q11 → D265.** Sin `24:00`: un turno que termina a las 00:00 del consultorio pasa RN-AG-10d y recibe `RN-AG-04`, con escenario propio (H9).

Las cuatro elecciones que seguían «Propuesta» y que revisó la segunda revisión quedaron aprobadas por el autor el 2026-10-22: **D266** (mensajes fijos de `RN-AG-16`; «válida» = «no invertida»; H6), **D267** (sin profesionales activos, el primero de la lista con «(inactivo)»; H15), **D268** (tope de 70 franjas en total, formato; H4) y **D269** (error de red al guardar: mensaje de conexión sin «Reintentar», lo editado se conserva y el botón vuelve a habilitarse; H15).

Texto de las preguntas tal como se propusieron (para la trazabilidad):

- **Q1. Dos capabilities nuevas en un change.** (a) `horario-recurrente` y `pantalla-de-horario`, como excepción a «una sola capability» igual que D241; (b) una sola, `horario-recurrente`, con la pantalla adentro; (c) partir el change en API y pantalla. **Recomendación: (a)**, cada spec se verifica con su suite y C-09 ya probó el esquema.
- **Q2. Profesional sin franjas (o día sin franjas).** (a) No admite turnos: `422` `RN-AG-04` (lectura literal de RN-AG-04); (b) sin ninguna franja no se valida el horario (compatibilidad), con franjas sí. **Recomendación: (a)**, con el horario de prueba de la fábrica (Q9) para no romper los tests; (b) inventa una excepción que la KB no tiene y haría que «borrar el horario» abra la agenda entera.
- **Q3. Código y clase del rechazo de franjas inválidas** (superpuestas o con inicio no anterior al fin). (a) Código nuevo `RN-AG-16`, validación de entrada, `422` con todas juntas; (b) reutilizar `RN-AG-04`; (c) regla de negocio `409`, de a una. **Recomendación: (a)**: el rechazo depende solo del cuerpo (no del estado guardado), así que es entrada y se informa junto (RN-GL-02); un código propio evita confundirlo con el turno fuera de horario.
- **Q4. Turno que pasa de una franja a otra contigua** (09-13 y 13-17, turno 12:45-13:15). (a) Se rechaza: debe caber en una sola franja (literal); (b) se aceptan como una franja continua. **Recomendación: (a)** por ser la letra de RN-AG-04; el odontólogo que atiende corrido carga una sola franja 09-17. Si el autor prefiere (b), cambia el escenario de borde de E10 y H9.
- **Q5. Vigencia (`vigente_desde`, `vigente_hasta`).** (a) Las columnas se crean nulas, la API no las expone y el dominio ya las respeta al evaluar RN-AG-04 (test unitario); (b) exponerlas en el `PUT` y en la pantalla; (c) no crear las columnas hasta que una historia las pida. **Recomendación: (a)**: respeta el modelo de `04` (que US-080 CA-9 usa) sin sumar pantalla ni escenarios de API.
- **Q6. Cómo elige la pantalla al profesional.** (a) `GET /profesionales` nuevo, de solo lectura (`id`, `nombre`, `activo`), para los tres roles, y un selector; (b) la pantalla usa siempre el profesional 1 (`/panel/horario` fijo); (c) incluir el nombre en `GET /profesionales/{id}/horario` y pedir el id en la URL de la pantalla. **Recomendación: (a)**: es una ruta mínima y la necesitarán la agenda (C-20) y la disponibilidad (C-24); (b) ata la interfaz a un id del seed.
- **Q7. Turnos existentes que quedan fuera del horario nuevo.** (a) El `PUT` no los toca ni los informa (como D83 para bloqueos, sin la lista); (b) la respuesta lista los turnos activos que quedan fuera; (c) el `PUT` se rechaza si deja turnos afuera. **Recomendación: (a)**: (b) es la parte de «turnos afectados» que D83 pone en bloqueos (C-13) y (c) impediría corregir un horario mal cargado.
- **Q8. Profesional inactivo en la URL.** (a) Se lee y se edita su horario (existe); (b) `404` como inexistente. **Recomendación: (a)**: RN-GL-04 habla de «inactivo» para referencias del cuerpo; en la URL, D166 usa `404` solo para el inexistente, y reactivarlo sin perder su horario es útil.
- **Q9. Horario de los tests existentes.** (a) La fábrica `un_profesional` carga por defecto 00:00-23:59 de lunes a domingo, desactivable con `horario=()`; (b) cada test carga su horario a mano; (c) un fixture `autouse`. **Recomendación: (a)**, análisis en H13.
- **Q10. Tamaño.** 31 tareas en 13 grupos para 47 escenarios (41 nuevos y 6 copiados en los MODIFIED), frente a «alrededor de 20» de `CHANGES.md`: API, pantalla, migración con perfil `postgres` y la regla nueva en `crear_turno` con su análisis de tests. (a) Aceptar como excepción limitada a C-12, como D251; (b) partir el change. **Recomendación: (a)**, con RED, GREEN y TRIANGULATE separados (TDD estricto).
- **Q11. Franjas hasta la medianoche.** (a) No se pueden expresar: `hora_fin` llega a 23:59 (`hora` con `CHECK hora_inicio < hora_fin` de `04`), así que un turno que termina a las 00:00 locales nunca cabe; (b) aceptar `24:00` como fin del día. **Recomendación: (a)**: ningún consultorio de la v1 atiende hasta la medianoche y (b) obliga a un tipo y un `CHECK` distintos de `04`.
