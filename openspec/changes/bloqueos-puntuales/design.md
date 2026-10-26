# Design: bloqueos-puntuales

Change **C-13** (US-003 y la parte de bloqueos de E10). Gobernanza **MEDIO**. Motivación y alcance en `proposal.md`; el comportamiento, en los cuatro specs del change (`bloqueos-puntuales`, `pantalla-de-bloqueos` y los deltas de `creacion-de-turnos` y `persistencia-postgresql`). Las referencias «B1» a «B20» son las decisiones de este design (para no confundirlas con las H de C-12). Cada elección no confirmada por el autor está marcada **Propuesta**; las que salieron de una pregunta abierta citan su D y su Q («Decisión del autor (D273; Q3)»).

**Respuesta del autor (2026-10-26): las dieciocho preguntas abiertas se cierran con la recomendación del agente, junto con las correcciones del informe de `revisor-de-escenarios`** («Coincido con tus recomendaciones y sugerencias, en base a Q1-Q18 como lo devuelto en el informe de revision-de-escenarios-bloqueos-puntuales.md»). Quedan como decisiones del autor D271 (B1, dos capabilities y dos deltas), D272 (B3 y B4, profesional y sillón a la vez como formato y `CHECK`), D273 (B5, código nuevo `RN-AG-17`), D274 (B5, recurso inactivo con `RN-GL-04`), D275 (B4 y B9, turnos afectados en el `201`), D276 (bloqueos superpuestos aceptados), D277 (B9 y B12, bloqueos pasados aceptados), D278 (B12, borrado físico), D279 (B4, `GET /bloqueos` sin filtros), D280 (B8 y B10, orden y `bloqueo_id`), D281 (B11, carrera como límite), D282 (B3, `0009` y `creado_por` NN), D283 (B4, `motivo` de 1 a 200), D284 (B13, demo sin bloqueos), D285 (B15, hora del consultorio), D286 (B16, detalles de la pantalla), D287 (B20, tamaño) y D288 (Stitch antes de aprobar el plan), más **D289** (B4, cualquier minuto y sin tope de rango ni de cantidad), que sale del hallazgo H11 del informe; todas registradas en `knowledge-base/10_preguntas_abiertas.md`. `RN-AG-17` quedó registrado en `knowledge-base/05_reglas_de_negocio.md` (y en la clase «Validación de entrada» de RN-GL-02) y en US-003 de `06`. En la misma revisión (`/opsx:update`) se incorporó el informe `docs/skills-mcp/evidencias/sesion-nueva/revision-de-escenarios-bloqueos-puntuales.md` (queda como el «antes»); **sus hallazgos se citan como «hallazgo H1» a «hallazgo H12»**. Se corrigieron H1 a H9 (nueve escenarios nuevos y dos reescritos), H10 quedó resuelto por D273, H11 por D289 y por la nota de C-16 en `CHANGES.md`, y H12 no pide cambios. Los specs pasan de 52 a **61 escenarios** y las tareas siguen siendo **22 en 10 grupos**. **La pantalla de Stitch ya está** (D288; obtenida el 2026-10-26 con un `/opsx:update` posterior, id en «Referencia visual (Stitch)»).

## Context

- `crear_turno` (`backend/app/application/crear_turno.py`) hoy hace: validación de entrada toda junta → `Intervalo.para_turno` (RN-AG-10d) → `exigir_dentro_del_horario` (RN-AG-04, C-12) → `bloquear_recursos` → ocupados → `detectar_conflictos` → `agregar` + evento `creado`. No mira bloqueos.
- `04` §Bloqueo: `consultorio_id` NN, `profesional_id` y `sillon_id` nulos («con `sillon_id` nulo bloquea al profesional; ambos nulos = bloquea todo el consultorio»), `inicio < fin` con `CHECK`, `motivo` texto NN (ejemplos: vacaciones, feriado, ausencia, mantenimiento), `creado_por` FK → `usuario` «null (columna agregada cuando existe `Usuario`)», índices `(profesional_id, inicio, fin)` y `(sillon_id, inicio, fin)`.
- RN-AG-04b (`05`): los bloqueos prevalecen sobre el horario; un turno no puede intersecar un bloqueo del profesional, de su sillón o de todo el consultorio; crear un bloqueo sobre turnos activos **no los cancela**: el sistema los lista (D83). `07` Flujo 1: el paso 5 valida horario (RN-AG-04) y bloqueos (RN-AG-04b); caso de error «Sobre bloqueo → `422` con `RN-AG-04b` (desde C-13)».
- Matriz de `03`, fila «Horario recurrente y bloqueos»: `odontologo` CRUD, `recepcionista` R, `dueno` R. `02`: `GET/POST/DELETE /bloqueos` (no hay `PATCH`).
- Migraciones en `backend/app/infrastructure/db/migraciones/versions/`; la última es **`0008`** (franja horaria). La suite por defecto usa `create_all` sobre SQLite; las migraciones se prueban en el perfil `postgres`.
- `Intervalo` (`domain/agenda/intervalo.py`) exige `inicio < fin` y levanta `IntervaloInvalido` con **`RN-AG-10d`**; `para_turno` agrega la regla de la medianoche. Un bloqueo puede durar varios días, así que no usa `para_turno`.
- Las rutas de C-12 toman el consultorio del usuario del token (D270); las de prestaciones, sillones y usuarios usan todavía `consultorio_unico()`.
- La pantalla necesita los nombres de profesionales y sillones: `GET /profesionales` (C-12, tres roles) y `GET /sillones` (C-05, tres roles) ya existen. El frontend ya tiene `listarProfesionales` en `features/horario/apiHorario.ts`; no tiene cliente de sillones.
- **Stitch**: la pantalla ya está (id devuelto por el MCP el 2026-10-26; ver «Referencia visual (Stitch)»).

## Goals / Non-Goals

**Goals:**
- Reglas puras de dominio para el alcance de un bloqueo, la validez de sus fechas (RN-AG-17, D273), los turnos afectados (US-003 CA-2) y RN-AG-04b en la creación, testeadas sin base de datos.
- Agregar RN-AG-04b a `crear_turno` **sin cambiar lo que prueba ningún test existente**: hoy no hay bloqueos en la base, en las fábricas ni en el seed (B13), así que la regla nueva no puede cambiar ningún resultado anterior.
- API y pantalla siguiendo los patrones de C-05, C-09, C-11 y C-12 (routers por recurso, `requiere(Permiso…)`, errores problem+json, servidor falso inyectado).

**Non-Goals:**
- Cancelar, reprogramar o avisar los turnos afectados (D83; C-16, C-17, C-32).
- Editar un bloqueo, bloqueos recurrentes, feriados automáticos, filtros de `GET /bloqueos` (D279).
- Un tope de duración del bloqueo o de cantidad de bloqueos, o una granularidad de sus horas (D289: cualquier minuto; límite conocido).
- Disponibilidad (C-24) y ocupación (C-47), que restarán los bloqueos.
- Garantizar en PostgreSQL que no se cree un turno sobre un bloqueo creado en el mismo instante (límite aceptado, B11, D281).
- Una restricción de base que impida bloqueos superpuestos (D276: se aceptan).

## Decisions

### B1. Dos capabilities nuevas y dos deltas — Decisión del autor (D271; Q1; sigue D241 y D255)

`bloqueos-puntuales` (API) y `pantalla-de-bloqueos` (interfaz), separadas por la suite que verifica cada una (pytest o Vitest), como C-09 y C-12. RN-AG-04b en la creación es un **delta de `creacion-de-turnos`** (ADDED + el requisito del orden, MODIFIED), porque describe qué hace `POST /turnos`; `persistencia-postgresql` suma la tabla y el escenario de deshacer `0009`. D241 y D255 quedaron limitadas a su change, así que C-13 tiene su propia excepción a «un change, una capability», limitada a C-13 (D271). **Alternativa descartada:** una sola capability `bloqueos-puntuales` con los requisitos de la pantalla adentro (cumple la regla, pero mezcla en un spec dos suites).

### B2. Estructura del backend — Propuesta (aplica `08`, «Estructura de directorios», y la regla dura 3)

```
backend/app/domain/agenda/bloqueos.py       Alcance, DatosBloqueo; validar_fechas_del_bloqueo (RN-AG-17); afecta_al_turno;
                                             turnos_afectados (US-003 CA-2); exigir_sin_bloqueos (RN-AG-04b). Solo stdlib.
backend/app/domain/errors.py                BloqueoInvertido (RN-AG-17, error de campo), SobreBloqueo (RN-AG-04b, con bloqueo_id)
backend/app/domain/acceso/roles.py          Permiso.BLOQUEOS_LEER (_TODOS), Permiso.BLOQUEOS_EDITAR (_SOLO_EL_ODONTOLOGO)
backend/app/application/bloqueos.py         listar_bloqueos, crear_bloqueo (devuelve bloqueo + afectados), eliminar_bloqueo
backend/app/application/puertos.py          RepositorioBloqueos (agregar, del_consultorio, obtener, eliminar, que_intersecan)
                                             + RepositorioAgenda.turnos_activos_que_intersecan(alcance, intervalo) + UnidadDeTrabajo.bloqueos
backend/app/application/crear_turno.py      lee los bloqueos que intersecan y llama a exigir_sin_bloqueos (B10)
backend/app/infrastructure/db/modelos.py    BloqueoModelo
backend/app/infrastructure/repositories/bloqueos.py
backend/app/infrastructure/db/migraciones/versions/0009_bloqueo.py
backend/app/api/routers/bloqueos.py         GET /bloqueos, POST /bloqueos, DELETE /bloqueos/{id}
backend/app/api/esquemas.py                 CrearBloqueoEntrada, BloqueoSalida, BloqueoCreadoSalida, TurnoAfectadoSalida, BloqueosSalida
```

### B3. Modelo y migración `0009` — Decisión del autor (D282 y D272; Q12 y Q2; aplica `04` y `database-migration`)

`bloqueo`: `id` PK; `consultorio_id` FK → `consultorio`, NN; `profesional_id` FK → `profesional` nula; `sillon_id` FK → `sillon` nula; `inicio` y `fin` `DateTime(timezone=True)` NN con `CHECK inicio < fin`; `motivo` `String(200)` NN; `creado_por` FK → `usuario`, **NN** (D282: `04` la marca nula porque la pensó agregada después de `Usuario`; hoy `Usuario` existe y todo bloqueo se crea con un token, así que no hay filas sin creador). Todas las FK `ON DELETE RESTRICT`. **`CHECK NOT (profesional_id IS NOT NULL AND sillon_id IS NOT NULL)`** (D272), con su escenario INF-1 en el perfil `postgres` (hallazgo H7). Índices de `04` `ix_bloqueo_profesional (profesional_id, inicio, fin)` y `ix_bloqueo_sillon (sillon_id, inicio, fin)`, más `ix_bloqueo_consultorio (consultorio_id, inicio)` (la lista y el bloqueo de consultorio filtran por él; `supabase-postgres-best-practices`: índice en la FK). Sin índice en `creado_por` (no se consulta por él). Generada con autogenerate y revisada a mano; `downgrade` borra solo la tabla. Sin datos (B13). Las fechas entran en el guard de «columnas de fecha-hora con zona» (A verificar V2).

### B4. Contrato de la API — Decisión del autor (D275, D278, D279, D283 y D289; Q5, Q8, Q9, Q13 y hallazgo H11) + Propuesta (nombres de los esquemas)

- `POST /bloqueos` con `{inicio, fin, motivo, profesional_id?, sillon_id?}` (`extra="forbid"`) → `201` `{id, alcance, profesional_id, sillon_id, inicio, fin, motivo, creado_por, turnos_afectados: [{id, inicio, fin, estado, profesional_id, sillon_id, paciente_id}]}`. `alcance` es `profesional`, `sillon` o `consultorio` y se deriva de las dos columnas (no se guarda). `motivo` se normaliza como los nombres (sin espacios de más, `NombreNormalizado` del proyecto) y debe quedar con 1 a 200 caracteres (D283: la KB no fija largo; 200 es un tope de tamaño del cuerpo, como D268; escenario de límite propio, hallazgo H3). `profesional_id` y `sillon_id` a la vez: `422` de formato con `model_validator` (D272). `turnos_afectados` no lleva datos del paciente más que su id (D275; minimización, RN-PR-01 y P-09). `inicio` y `fin` admiten cualquier minuto: no se exige múltiplo de 5 (D289; la granularidad de D99 es la de la duración de la prestación, RN-AG-01). **Límite conocido** (D289, hallazgo H11): no hay tope de duración del bloqueo (uno de años es válido) ni de cantidad de bloqueos; se anota en el README.
- `GET /bloqueos` → `200` `{zona_horaria, bloqueos: [...]}` con los mismos campos salvo `turnos_afectados`, todos los del consultorio, por `(inicio, id)` (D279). `zona_horaria` va en el sobre porque la pantalla escribe y muestra en hora del consultorio (B15), como `GET /profesionales/{id}/horario`.
- `DELETE /bloqueos/{id}` → `204` sin cuerpo; borrado físico (D278: la tabla de `04` no tiene estado ni `activo`). Un `id` no entero → `422` de formato.
- Las tres rutas toman el consultorio del usuario del token (sigue D270, B7).

### B5. Validación de entrada del alta: `RN-GL-01`, `RN-GL-04` y `RN-AG-17` — Decisión del autor (D273 y D274; Q3 y Q4; aplica RN-GL-02, D135 y la regla dura 4)

Función de aplicación `_validar_entrada` (como la de `crear_turno`), que junta en un único `EntradaInvalida`: `exigir_utc` de `inicio` y de `fin` (`RN-GL-01`, cada uno su error de campo); las referencias del cuerpo (`profesional_id` o `sillon_id` inexistente, inactivo o de otro consultorio → `RN-GL-04`, D126 y D274, con `recurso`, `recurso_id` y `motivo`); y, **solo si las dos fechas son válidas**, `validar_fechas_del_bloqueo(inicio, fin)` del dominio: `fin <= inicio` → `BloqueoInvertido`, código nuevo **`RN-AG-17`** (D273, registrado en `05`), error de campo `fin` con el mensaje fijo «fin debe ser posterior a inicio». Es validación de entrada porque depende solo del cuerpo (como `RN-AG-16`, D257). No se construye `Intervalo` antes de validar: `Intervalo` levanta `RN-AG-10d` (E8), que habla de turnos. **Alternativas descartadas:** reutilizar `RN-AG-10d` (su texto es la medianoche del turno) o `RN-AG-04b` (su texto es el turno sobre un bloqueo).

### B6. Alcance, turnos afectados y RN-AG-04b en el dominio — Propuesta (aplica RN-AG-04b, RN-AG-09, RN-AG-10 y D83)

`Alcance` (`profesional`, `sillon`, `consultorio`) sale de qué id está presente. `afecta_al_turno(bloqueo, turno)`: el bloqueo es del profesional del turno, del sillón del turno o del consultorio del turno, **y** `bloqueo.inicio < turno.fin and turno.inicio < bloqueo.fin` (semiabierto, la misma comparación que `Intervalo.se_solapa_con`). `turnos_afectados(bloqueo, turnos)` filtra los activos (`ESTADOS_ACTIVOS`) que cumplen eso y los ordena por `(inicio, id)`. `exigir_sin_bloqueos(intervalo, profesional_id, sillon_id, consultorio_id, bloqueos)` levanta `SobreBloqueo(bloqueo_id)` con el que **empieza primero** (desempate por `id`; sigue D129, D280) si alguno lo afecta. El estado efectivo de la seña (RN-GL-05) no aplica todavía: no hay seña.

### B7. Permisos y consultorio — Propuesta (matriz de `03`; sigue D270)

`bloqueos.leer`: los tres roles; `bloqueos.editar` (`POST` y `DELETE`): solo `odontologo`. `requiere(...)` como en `/profesionales`, así el guard de rutas protegidas las cubre (sus contadores suben: permisos 11 → 13, rutas protegidas 14 → 17; solo cambia el número esperado, como en C-12). El consultorio es el del usuario del token (`usuario.consultorio_id`), por el escenario de «otro consultorio» y por D270.

### B8. Clases de rechazo y orden de evaluación — Decisión del autor por la KB (RN-GL-02, D135, D208; `07` Flujo 1) y Decisión del autor (D280; Q10)

| # | Clase | `GET /bloqueos` | `POST /bloqueos` | `DELETE /bloqueos/{id}` | `POST /turnos` |
|---|---|---|---|---|---|
| 0 | Límite de FastAPI | — | JSON roto: `422` sin código | — | igual |
| 1 | Control de acceso | `401` `RN-AU-03` | `401`; `403` `RN-AU-05` | `401`; `403` | `401`; `403` |
| 2 | Formato (Pydantic) | — | `422` `codigos` vacío: campo ausente o de más, `motivo` vacío o largo, profesional y sillón a la vez | `id` no entero: `422` | igual que antes |
| 3 | Validación de entrada del dominio | — | `422` `RN-GL-01`, `RN-GL-04`, `RN-AG-17` (todas juntas) | — | `422` `RN-GL-01` y/o `RN-GL-04` |
| 4 | Recurso de la URL | — | — | `404` `RN-GL-04` | — |
| 5 | Reglas de negocio, de a una | — | — | — | `422` `RN-AG-10d` → `422` `RN-AG-04` → **`422` `RN-AG-04b`** → `409` `RN-AG-05`/`RN-AG-08` |

`SobreBloqueo` → `422`, `type` `/errores/sobre-bloqueo`, `title` «Sobre un bloqueo», `detail` fijo «El turno cae dentro de un bloqueo del profesional, del sillón o del consultorio.» y `bloqueo_id` (D280; los escenarios lo comparan, hallazgos H5 y H6). El `422` sale de `07` (casos de error de Flujo 1). Que el horario vaya **antes** que los bloqueos es la lectura del paso 5 de `07` («horario recurrente … y bloqueos»); RN-AG-04b dice que los bloqueos «prevalecen» sobre el horario, lo que se lee como que un bloqueo cierra horas que el horario abría, no como un orden de evaluación (D280).

### B9. Alta del bloqueo — Decisión del autor (D275, D277 y D281; Q5, Q7 y Q11)

`crear_bloqueo` abre la unidad de trabajo, valida (B5), guarda el bloqueo con `creado_por` = usuario del token, lee los turnos activos que intersecan con `uow.agenda.turnos_activos_que_intersecan(alcance, intervalo)` (consulta por `profesional_id`, `sillon_id` o `consultorio_id`, estados activos e intersección semiabierta, filtrada otra vez por el dominio con `turnos_afectados`) y confirma. No toca turnos ni registra eventos (D83). Los turnos pasados que intersecan también se listan (un bloqueo puede empezar en el pasado, D277; escenario propio, hallazgo H4).

### B10. Lugar de RN-AG-04b en `crear_turno` — Decisión del autor (D280; el orden lo fija B8) + Propuesta (el lugar en el código)

Después de `exigir_dentro_del_horario` (RN-AG-04) y **antes** de `bloquear_recursos`: `bloqueos = uow.bloqueos.que_intersecan(consultorio_id, profesional.id, sillon.id, intervalo)` y `exigir_sin_bloqueos(...)`. Así un turno sobre un bloqueo no toma bloqueos de fila, y el solapamiento solo se evalúa sin bloqueo. El reintento ante carrera (E11) repite todo, incluida esta lectura.

### B11. Bloqueo y turno creados a la vez — Decisión del autor (D281; Q11; límite conocido, como D261 en C-12)

`POST /bloqueos` no toma el bloqueo de fila del profesional ni del sillón: un turno creado en el mismo instante puede quedar dentro del bloqueo, y tampoco aparecería en `turnos_afectados` si su transacción confirma después de la lectura. Es el mismo efecto que crear el turno un instante antes que el bloqueo, que la KB acepta (el bloqueo no cancela turnos, D83). Se documenta en el README. **Alternativa descartada:** que `crear_bloqueo` tome `bloquear_recursos` (profesional, sillón o, para el consultorio, una fila de `consultorio`) y que `crear_turno` lea los bloqueos después de su bloqueo de fila: cierra la carrera pero agrega acoplamiento sin una regla que lo pida.

### B12. Eliminación — Decisión del autor (D278 y D277; Q8 y Q7)

`eliminar_bloqueo` busca el bloqueo en el consultorio del usuario (`404` `RN-GL-04` con `recurso` `bloqueo` si no está o es de otro, D166) y lo borra. No toca turnos. Se puede eliminar un bloqueo pasado. No queda rastro del borrado (la tabla no tiene historial; `creado_por` solo dice quién lo creó).

### B13. Seed de la demo y fábricas — Decisión del autor (D284; Q14; evita el hueco de orden de C-12)

La demo arranca **sin bloqueos**: los ejemplos del README (`2026-11-02T13:00:00Z` y `2026-11-03T13:00:00Z`) siguen dando `201` y la regla nueva no cambia ningún test de la demo ni del perfil `postgres`. Por eso, a diferencia de C-12 (que tuvo que adelantar el seed antes de cerrar la regla, nota de 6.2 de su tasks), **no hay tarea de seed** y la regla de `crear_turno` (grupo 5) no depende de ningún dato de la demo. La fábrica nueva `un_bloqueo(sesion, consultorio, *, inicio, fin, profesional=None, sillon=None, motivo="Ausencia", creado_por=None)` guarda directo en la base (crea un usuario de la fábrica si `creado_por` no se da, porque la columna es NN, D282); ninguna fábrica existente cambia. **Alternativa descartada** (Q14): un bloqueo de ejemplo en la demo, fuera de las horas del README y cargado antes de la regla.

### B14. Estructura del frontend — Propuesta (aplica H14 de C-12 y U17 de C-09)

```
frontend/src/features/bloqueos/apiBloqueos.ts (+ .test.ts)        listarBloqueos, crearBloqueo, eliminarBloqueo, listarSillones; respuestas validadas sin any; traducirRechazo
frontend/src/features/bloqueos/horaDelConsultorio.ts (+ .test.ts)  aUtc(fechaHoraLocal, zona) y aLocal(utc, zona) con Intl.DateTimeFormat, sin dependencias
frontend/src/features/bloqueos/PaginaBloqueos.tsx (+ .test.tsx)    estados: cargando / sin-conexion / lista; aviso de creado, eliminado o de error
frontend/src/features/bloqueos/FormularioDeBloqueo.tsx             alcance, recurso, desde, hasta (datetime-local), motivo, «Bloquear»
frontend/src/features/bloqueos/ListaDeBloqueos.tsx                 filas con alcance, desde, hasta, motivo y «Eliminar»
frontend/src/features/bloqueos/TurnosAfectados.tsx                 aviso y filas de los turnos afectados (US-003 CA-2)
frontend/src/features/bloqueos/mensajes.ts (+ .test.ts)            textos fijos de B17
frontend/src/shared/iconos/IconoCalendario.tsx                     SVG en línea, aria-hidden
frontend/src/App.tsx, pages/PanelBase.tsx                          ruta hija "bloqueos" y enlace «Bloqueos»
frontend/src/test/servidorFalso.ts                                 GET/POST /api/bloqueos y DELETE /api/bloqueos/{id} con el orden de B8, formato del motivo, RN-AG-17 y RN-GL-04;
                                                                   GET /api/sillones; recursos inactivos y turnos de partida; respuesta retenida y falla de red en POST y DELETE; quitarBloqueo(id); quitarProfesional (ya existe)
```

`listarProfesionales` se reutiliza de `features/horario/apiHorario.ts` (sin copiarla).

### B15. Hora del consultorio en la pantalla — Decisión del autor (D285; Q15; aplica RN-GL-01)

La pantalla escribe y muestra fechas en la **zona del consultorio** que devuelve `GET /bloqueos` (no en la del navegador): un odontólogo que bloquea «el 23 de noviembre» piensa en su día local. Entrada con `<input type="datetime-local">` (valor `aaaa-mm-ddThh:mm`, sin zona); `aUtc` calcula el desfase de la zona en ese instante con `Intl.DateTimeFormat(..., {timeZone})` (iterando una vez para los cambios de hora) y manda ISO en UTC con `Z`; `aLocal` formatea `dd/mm/aaaa hh:mm`. Sin bibliotecas nuevas. A verificar V4. Sin opción «Todo el día» (un día completo es de 00:00 a 00:00 del día siguiente; D285).

### B16. Pantalla — Decisión del autor (D286; Q16; aplica `vercel-react-best-practices`)

Una sola carga al montar (bloqueos, profesionales y sillones en paralelo). El selector de recurso ofrece solo los **activos** (un inactivo daría `RN-GL-04`; escenario propio, hallazgo H9). Sin validación local del orden de las fechas ni del largo del motivo (como D232: la API decide; escenarios propios de `RN-AG-17` y del `422` sin código, hallazgo H2). «Bloquear» se deshabilita mientras espera: un segundo clic no manda otro `POST` (escenario propio con la respuesta retenida, hallazgo H1, como el de «Guardar horario» de C-12); con el `201` se limpia el formulario y se suma el bloqueo a la lista en el orden de la API (se vuelve a pedir `GET /bloqueos`, que ya ordena). Los turnos afectados se muestran debajo del aviso hasta el próximo alta o eliminación; muestran id, fechas locales y estado, sin el paciente (D275). «Eliminar» sin confirmación (D286: el bloqueo se puede volver a crear igual y no toca turnos). **El doble clic en «Eliminar» queda cubierto** (hallazgo H9 (c)), con el mismo patrón de C-12: el «Eliminar» de esa fila se deshabilita mientras espera el `DELETE` y un escenario con la respuesta retenida comprueba que se manda uno solo (sin eso, el segundo `DELETE` daría `404` y la pantalla mostraría «El bloqueo ya no existe»). Si el `DELETE` no responde, se ve el mensaje de conexión de C-11 sin «Reintentar», el bloqueo sigue en la lista y «Eliminar» vuelve a habilitarse (escenario propio, hallazgo H9 (b); como D269). Las acciones se ven para todos los roles y la API responde `403` (sigue D230 y D249).

### B17. Mensajes fijos de la pantalla — Propuesta (como H17 de C-12)

«Cargando bloqueos…»; el de conexión de C-11; «No hay bloqueos cargados.»; «Todo el consultorio», «Profesional: <nombre>», «Sillón: <nombre>»; «Completá alcance, desde, hasta y motivo.»; «Bloqueo creado. No hay turnos activos en ese horario.»; «Bloqueo creado. Hay N turnos activos en ese horario: no se cancelaron, hay que reprogramarlos o cancelarlos.» (con N = 1, «Hay 1 turno activo»); fila de afectado «Turno <id> · <dd/mm/aaaa hh:mm> a <hh:mm> · <estado>»; «Bloqueo eliminado.»; `RN-AG-17`: «El bloqueo tiene que terminar después de empezar (RN-AG-17).»; `RN-GL-04` al crear: «El profesional o el sillón elegido ya no está disponible (RN-GL-04).»; `404` al eliminar: «El bloqueo ya no existe (RN-GL-04).»; `RN-AU-05`: «Tu usuario no tiene permiso para modificar los bloqueos (RN-AU-05).»; `422` sin código: «Revisá los datos del bloqueo.»; nota: «Un bloqueo impide dar turnos en ese horario (RN-AG-04b). Los turnos que ya estaban no se cancelan.»; subtítulo: «Fechas y horas del consultorio (<zona_horaria>).». No se muestra el `detail` de la API.

### B18. Tests y servidor falso — Decisión del autor (D222, D227, reglas duras 5 y 6) + Propuesta (detalle)

Backend: unitarios de `domain/agenda/bloqueos.py` (sin base), integración del repositorio y de los casos de uso con SQLite en memoria, API con tokens reales (D211), perfil `postgres` para `0009` (INF-1). Frontend: Vitest con el servidor falso inyectado, sin `vi.mock`/`vi.fn`; la conversión de hora como función pura con su test. Los nombres de los tests citan el escenario (`US-003 CA-1`, `US-003 CA-2`, `E10`, `INF-1`, `US-092 CA-1`).

### B19. Versiones y dependencias — Propuesta

**Sin dependencias nuevas** ni cambios de versión: `DateTime(timezone=True)` y `String` son de SQLAlchemy 2.0 ya instalado; `Intl` es del navegador y de Node 24. `backend/pyproject.toml`, `frontend/package.json` y `package-lock.json` no cambian. Por eso no hay pins nuevos que fijar (regla de `config.yaml`).

### B20. Tamaño — Decisión del autor (D287; Q17; excepción limitada a C-13)

**22 tareas en 10 grupos** para **61 escenarios** (51 nuevos: 22 de `bloqueos-puntuales`, 17 de `pantalla-de-bloqueos`, 9 de `creacion-de-turnos` y 3 de `persistencia-postgresql`; más 10 copiados sin cambios de fondo en los requisitos MODIFIED). Los 9 escenarios que sumó la revisión (hallazgos H1, H2, H3, H4, H6, H7 y H9) entran en las tareas existentes. Frente a C-12 (31 tareas) se ahorra: la migración y la persistencia van en un mismo par RED/GREEN, no hay seed (B13) y los dos README van en una sola tarea. La tarea 1.2 (pantalla de Stitch) es del autor. Igual pasa de «alrededor de 20» y de «3 a 6 escenarios»: como C-08 con 22 (D228), queda registrado como excepción limitada a C-13 (D287).

### Skills aplicadas

- `python-design-patterns`: reglas puras en el dominio y los casos de uso como orquestadores; una función por regla (RN-AG-17, afectados, RN-AG-04b).
- `python-error-handling`: errores de dominio con código; validación de entrada junta (RN-GL-01, RN-GL-04, RN-AG-17) y reglas de a una (RN-AG-10d → RN-AG-04 → RN-AG-04b → solapamiento).
- `python-testing-patterns`: TDD estricto; bordes del intervalo semiabierto (contiguo, un minuto), estados no activos, alcance; fábrica `un_bloqueo` explícita; sin mocks.
- `fastapi-templates`: router por recurso, esquemas de entrada y salida separados, dependencias, `204` sin cuerpo. **No aplica** su parte asíncrona (DD-12, regla dura 5).
- `database-migration`: una migración reversible, tabla nueva sin tocar las existentes, autogenerate revisado a mano. **No aplican** sus ejemplos JavaScript.
- `supabase-postgres-best-practices`: índices en las FK (`profesional_id`, `sillon_id`, `consultorio_id`, primeras en el compuesto), `CHECK` en la base como red, `timestamptz`. **No aplican** RLS ni lo específico de Supabase.
- `auth-implementation-patterns`: permisos por dependencia del token; consultorio del usuario del token (D270).
- `vercel-react-best-practices` (SPA de Vite): una carga al montar (en paralelo), estado derivado en el render, `setState` funcional, sin componentes definidos dentro de otros, ternario en vez de `&&`.

## Referencia visual (Stitch)

- **Pantalla**: `projects/14200813501064679723/screens/05d78d7e7d144f92bb9f77d0e4a220db` («Bloqueos - Turnos Odontológicos AR», `DESKTOP`), generada con el design system «Clinical Ops» (`assets/b683d44391ab410db2dd48aa71ed0b47`) al primer intento, con el pedido de la sección 2 de la evidencia. A diferencia de C-09 y C-12, el MCP devolvió el id directamente (2026-10-26, tarea 1.2, D288); `get_screen` la devuelve por él.
- **Evidencia**: `docs/skills-mcp/evidencias/sesion-nueva/stitch-bloqueos.md` (pedido, intento, revisión de datos y sugerencias no aceptadas) y `stitch-bloqueos-pantalla/pantalla.png` (1280 × 1065) y `pantalla.html`.

**Qué se toma:**
- La barra del panel con la pastilla «Bloqueos» activa y «Cerrar sesión» con borde (la barra es la compartida de C-08, C-11, C-09 y C-12: solo se suma el enlace).
- El encabezado: título «Bloqueos» y el subtítulo «Fechas y horas del consultorio (<zona>).» con la `zona_horaria` de la API; el aviso informativo azul con ícono, con el texto de B17 («Un bloqueo impide dar turnos en ese horario (RN-AG-04b). Los turnos que ya estaban no se cancelan.»).
- La disposición de escritorio en dos columnas (el alta a la izquierda, ~5/12; la lista a la derecha, ~7/12) que en pantallas angostas se apilan; tarjetas con título, e ícono de calendario en el de «Nuevo bloqueo».
- Etiquetas chicas en mayúsculas sobre los campos («Alcance», el recurso, «Desde», «Hasta», «Motivo»; el selector del recurso se llama «Profesional» o «Sillón» según el alcance) y el botón primario «Bloquear» a todo el ancho de la tarjeta con ícono de candado (SVG en línea).
- El estilo del error de `RN-AG-17`: borde rojo y texto rojo bajo «Hasta» (con `aria-invalid="true"`) y el mensaje en una caja roja suave con ícono; el texto es el de B17, no el de Stitch.
- El aviso de éxito verde suave con ícono debajo del formulario, con una fila compacta por turno afectado («Turno <id> · <fecha> <hh:mm> a <hh:mm>») y una etiqueta chica con su estado («reservado», «confirmado»); los textos son los de B17.
- La tabla de «Bloqueos cargados» con las columnas Alcance, Desde, Hasta y Motivo más una de acción, y el «Eliminar» destructivo sin relleno (borde y texto rojos) con ícono de papelera por fila (nombre accesible «Eliminar bloqueo»).

**Qué se rechaza (motivo):**
- Los prefijos «Aviso operativo:» y «Error de validación:»: los textos los fijan B17 y el spec.
- La insignia «Alta de indisponibilidad», «3 registros activos» y «Orden cronológico»: sin respaldo en la KB; un bloqueo no tiene estado (D278) y el orden ya es el de la API (D280).
- La etiqueta «Profesional asignado» y los asteriscos de obligatorio: las etiquetas son las del spec; el faltante se informa con «Completá alcance, desde, hasta y motivo.».
- Las ayudas «24 h (dd/mm/aaaa hh:mm)» y «Formato o valor incorrecto» y los campos de texto monoespaciados: se usan `<input type="datetime-local">` (B15), sin validación local (D286); las cifras de la lista quedan tabulares.
- El encabezado «Último resultado operativo»: el aviso de éxito va solo, debajo del formulario (B16).
- Las etiquetas de color por motivo («Ausencia», «Vacaciones», «Feriado») y el punto de color del alcance: el motivo es texto libre (D283), no una categoría; se muestra como texto.
- El pie de la tabla («sincronizado con la agenda en tiempo real», falso: la pantalla no se actualiza sola) y «Zona horaria: UTC-3 (Buenos Aires)» (la zona se muestra por su nombre, leída de la API, RN-GL-01, D285).
- El pie de página institucional («Módulo de Bloqueos e Indisponibilidad Clínica · Sede Central»): no hay sedes (D173) ni existe en las otras pantallas.
- La barra superior fija (sticky): las otras pantallas no la tienen.
- La opción «Dr. Roberto Pérez» del selector, que Stitch inventó: las opciones salen de `GET /profesionales` y `GET /sillones`, solo las activas.
- Las sugerencias de Stitch: el modal de confirmación al eliminar (contradice D286), «Ver el estado del formulario sin errores» (es el estado base) y la vista de reprogramación asistida de los turnos afectados (fuera del alcance: C-16, D83).
- Tailwind, Google Fonts y la fuente monoespaciada por CDN (CSP `default-src 'self'`): se traduce a `tokens.css` y `panel.css` (sección «Pantalla de bloqueos») sin dependencias nuevas; íconos en SVG en línea con `aria-hidden="true"`.

La KB y los specs mandan sobre el contenido; la prueba en el navegador (grupo 9) compara la implementación con `pantalla.png` y anota las diferencias en la evidencia.

## Contradicciones y huecos encontrados en las fuentes

- **Profesional y sillón a la vez**: `04` define «sillón nulo = profesional» y «ambos nulos = consultorio», pero no dice qué es un bloqueo con los dos. → Q2, D272.
- **Código del bloqueo invertido**: `04` pone `CHECK inicio < fin`, pero la regla dura 4 exige un código para todo rechazo y `Intervalo` hoy informa `RN-AG-10d` (E8), que habla de la medianoche del turno. → Q3, D273 (`RN-AG-17` estaba libre; ya registrado en `05`).
- **`creado_por` nulo en `04`**: la nota «columna agregada cuando existe `Usuario`» supone una tabla anterior a los usuarios; C-13 la crea con los usuarios ya existentes. → Q12, D282.
- **«RN-AG-04b (configurable)»**: `05` la etiqueta «configurable», pero ningún parámetro de `ConfiguracionReglas` (US-005) la toca. Se lee como que el odontólogo configura los bloqueos (datos), no como un parámetro; no se propone ninguna configuración. Si el autor la lee distinto, cambia el alcance (C-22).
- **«Prevalecen sobre el horario» y el orden**: RN-AG-04b dice que prevalecen; `07` pone horario y bloqueos en el mismo paso, horario primero. → Q10, D280.
- **Qué devuelve «la lista de afectados»**: D83 y US-003 CA-2 dicen «lista», sin campos ni dónde (respuesta del alta, `GET`, pantalla). → Q5, D275.
- **Granularidad y rango del bloqueo** (hallazgo H11): D99 fija 5 minutos para la duración de la prestación (RN-AG-01), no para los bloqueos, y ninguna fuente fija un tope de duración ni de cantidad. → D289 (cualquier minuto; sin tope, límite conocido).
- **Reprogramación** (hallazgo H11): RN-TD-04 dice que la reprogramación aplica RN-AG-04 a RN-AG-10 «también desde el panel», así que C-16 tiene que llamar a `exigir_sin_bloqueos` (RN-AG-04b). Fuera del alcance de C-13 (D83); queda anotado en el «Alcance — dentro» y el «Leer antes» de C-16 en `CHANGES.md`.
- **`07` Flujo 1** y **`06` E10**: dicen «bloqueos desde C-13»; se ajustan al archivar.

## Risks / Trade-offs

- [La regla nueva cambia un test existente] → hoy no hay bloqueos en ninguna fábrica, test ni seed (B13), así que no puede; igual 5.2 compara la cantidad y el resultado de los tests con 3.2 en las dos suites y, si alguno cambia, se frena y se analiza.
- [Conversión de hora del consultorio en el navegador] → función pura con tests en los bordes (medianoche local, cambio de día UTC) y V4; Argentina no tiene horario de verano hoy, pero la función no lo supone.
- [Turno y bloqueo creados a la vez] → límite aceptado (B11, D281), documentado en el README.
- [Un bloqueo eliminado sin rastro] → límite aceptado (B12, D278); la auditoría de bloqueos no está en la KB.
- [Bloqueos sin tope de duración ni de cantidad] → límite conocido (B4, D289): un bloqueo de años es válido y la lista no se pagina; un consultorio chico tiene pocos bloqueos y se documenta en el README.
- [El perfil `postgres` queda roto entre 3.1 y 3.2] → la fábrica y el modelo nuevos no se usan en ningún test del perfil hasta que existe `0009`; el RED y el GREEN de la migración van en el mismo grupo (3) y, sin Docker, se completan en 10.1 (como 5.1 y 5.2 de C-12).
- [La pantalla de Stitch se desvía de la KB] → ya está (D288); se toma solo lo visual y el design lista lo rechazado; la KB y los specs mandan (D234).

## A verificar en el change

- **V1** (antes de 2.1): que `ESTADOS_ACTIVOS` de `domain/turnos/estados.py` tenga los cuatro estados activos y se pueda reutilizar desde `domain/agenda/bloqueos.py` sin romper el guard de imports del dominio.
- **V2** (antes de 3.1): que el guard de columnas de fecha-hora con zona (`tests/integration/test_guard_fechas.py`) incluya `bloqueo.inicio` y `bloqueo.fin` sin cambios en el guard.
- **V3** (antes de 4.1): cómo arma hoy la API un `204` sin cuerpo con los routers del proyecto (ningún endpoint existente lo devuelve) y que el guard de rutas protegidas acepte un `DELETE`.
- **V4** (antes de 6.1): que `Intl.DateTimeFormat` con `timeZone: "America/Argentina/Buenos_Aires"` dé el desfase esperado en Node 24 (Vitest con jsdom) y en el navegador, para `aUtc` y `aLocal`.
- **V5** (antes de 3.2, con Docker): que `alembic upgrade head` y `downgrade 0008` sobre PostgreSQL 17.10 dejen el esquema del modelo (INF-1) con los `CHECK` de la tabla.

## Migration Plan

0. **Hecho el 2026-10-26:** el autor respondió Q1 a Q18 y el informe de `revisor-de-escenarios`; el `/opsx:update` registró D271 a D289 en `10`, `RN-AG-17` en `05` (y en RN-GL-02) y en US-003 de `06`, la nota de RN-AG-04b en C-16 de `CHANGES.md`, y ajustó los artefactos. La pantalla de Stitch (tarea 1.2, D288) se obtuvo el 2026-10-26 y se incorporó con otro `/opsx:update`. **Falta**: con el ok del autor, commitear los artefactos (con el `[~]` de C-13 y la nota de C-16 en `CHANGES.md`) y, en un commit `docs(kb)` aparte, las decisiones.
1. `0009_bloqueo` (solo crea la tabla; `downgrade` la borra). Sin datos.
2. **Efecto visible**: desde este change, `POST /turnos` sobre un bloqueo responde `422` `RN-AG-04b`. Sin bloqueos cargados, nada cambia.
3. Rollback: `alembic downgrade 0008` y volver al commit anterior; la regla y la tabla se van juntas (los bloqueos guardados se pierden con la tabla).

## Notas para el archive

- `knowledge-base/10_preguntas_abiertas.md`: D271 a D289 ya están registradas (2026-10-26); al archivar, las «Propuesta» que el autor apruebe y los hallazgos del Apply (V1 a V5).
- `05`: RN-AG-04b «implementada en C-13» (con el orden y el código de error, D280); en `RN-AG-17` (ya registrado, D273, con su lugar en la clase «Validación de entrada» de RN-GL-02), «se implementa en C-13» pasa a «implementada en C-13»; en RN-GL-02, el orden pasa a entrada → RN-AG-10d → RN-AG-04 → RN-AG-04b → solapamiento. En RN-AG-04, quitar «RN-AG-04b sigue pendiente de C-13».
- `06`: US-003 CA-1 y CA-2 implementadas (CA-1 ya cita `RN-AG-17`, D273); E10 completo (horario en C-12, bloqueos en C-13).
- `07` Flujo 1: el paso 5 y el caso de error «Sobre bloqueo» pasan a «desde C-13» con el orden de B8.
- `04` §Bloqueo: `creado_por` NN (D282), el `CHECK` de profesional y sillón a la vez (D272), el índice de `consultorio_id` (D282), `motivo` de hasta 200 caracteres (D283) y que `inicio` y `fin` admiten cualquier minuto (D289).
- `08`: `features/bloqueos/` y `domain/agenda/bloqueos.py` en la «Estructura de directorios»; en el «Mapeo a HTTP», una fila para `RN-AG-04b` (regla de negocio, `422`, `/errores/sobre-bloqueo`, entre RN-AG-04 y el solapamiento) y otra para `RN-AG-17` (validación de entrada, `422`, error de campo `fin`).
- `02` y `03`: sin cambios de rutas (ya dicen `GET/POST/DELETE /bloqueos` y la fila de la matriz).
- `openspec/specs/creacion-de-turnos/spec.md`: en el `Purpose`, agregar a la convención «salvo que un escenario diga otra cosa, no hay bloqueos» (un delta no puede cambiar el `Purpose`).
- `CHANGES.md`: `[x]` en C-13; repetir `scripts/verificar_changes.py`. La nota de que la reprogramación (C-16) aplica RN-AG-04b con `exigir_sin_bloqueos` (RN-TD-04, hallazgo H11) ya quedó en el «Alcance — dentro» y el «Leer antes» de C-16 con el `/opsx:update`; al archivar, comprobar que sigue y que el design de C-16 la recoja.
- `CLAUDE.md` y `AGENTS.md`: párrafo «Estado de `10_preguntas_abiertas.md`» con las decisiones de C-13 (D271 a D289, `RN-AG-17`).

## Open Questions

Ninguna. Las dieciocho preguntas del propose quedaron cerradas por el autor el 2026-10-26, todas con la recomendación del agente:

- **Q1 → D271.** Dos capabilities nuevas (`bloqueos-puntuales` y `pantalla-de-bloqueos`) y dos deltas, como excepción a «una sola capability» limitada a C-13 (B1).
- **Q2 → D272.** Profesional y sillón a la vez: `422` de formato y `CHECK` en la base, con escenario INF-1 (B3, B4; hallazgo H7).
- **Q3 → D273.** Código nuevo `RN-AG-17`, validación de entrada, `422`, error de campo `fin`, junto con `RN-GL-01` y `RN-GL-04`; ya registrado en `05` (y en RN-GL-02) y en US-003 de `06` (B5; hallazgo H10).
- **Q4 → D274.** Profesional o sillón inactivo en el cuerpo: `422` `RN-GL-04` con `motivo` `inactivo` (B5).
- **Q5 → D275.** Turnos afectados solo en el `201`, activos que intersecan, también pasados, por `(inicio, id)`, sin datos del paciente más que su id (B4, B9).
- **Q6 → D276.** Bloqueos superpuestos o repetidos se aceptan.
- **Q7 → D277.** Bloqueos en el pasado se aceptan y se eliminan; el alta no mira el reloj (B9, B12; hallazgo H4).
- **Q8 → D278.** Borrado físico, `204`, `404` `RN-GL-04` para inexistente o de otro consultorio (B12).
- **Q9 → D279.** `GET /bloqueos` con todos los del consultorio, por `(inicio, id)`, en `{zona_horaria, bloqueos}`, sin filtros (B4).
- **Q10 → D280.** Orden entrada → RN-AG-10d → RN-AG-04 → RN-AG-04b → solapamiento; `422` `/errores/sobre-bloqueo` con `bloqueo_id` del que empieza primero (desempate por `id`) (B8, B10; hallazgos H5 y H6).
- **Q11 → D281.** La carrera entre bloqueo y turno es un límite aceptado y documentado (B11).
- **Q12 → D282.** `0009_bloqueo`, `creado_por` NN, índices de `04` más `(consultorio_id, inicio)` (B3).
- **Q13 → D283.** `motivo` libre, sin espacios de más, de 1 a 200 caracteres; si no, `422` de formato (B4; hallazgos H2 y H3).
- **Q14 → D284.** La demo arranca sin bloqueos; no hay tarea de seed (B13).
- **Q15 → D285.** Fechas en la zona del consultorio con `Intl`, sin «Todo el día» (B15).
- **Q16 → D286.** Lista y alta en `/panel/bloqueos`, solo recursos activos, sin confirmación al eliminar, botones deshabilitados mientras esperan (B16; hallazgos H1 y H9).
- **Q17 → D287.** 22 tareas en 10 grupos para 61 escenarios (después del `/opsx:update`) como excepción limitada a C-13 (B20).
- **Q18 → D288.** La pantalla de Stitch se consigue antes de aprobar el plan (tarea 1.2); hecha el 2026-10-26: el MCP devolvió el id (`projects/14200813501064679723/screens/05d78d7e7d144f92bb9f77d0e4a220db`).

Del informe de `revisor-de-escenarios` sale además **D289** (hallazgo H11): `inicio` y `fin` de un bloqueo admiten cualquier minuto (la granularidad de 5 minutos de D99 es la de la duración de la prestación, RN-AG-01), y no hay tope de duración ni de cantidad de bloqueos (límite conocido, B4).

Texto de las preguntas tal como se propusieron (para la trazabilidad):

- **Q1. Una o dos capabilities** (regla dura 12, «un change, una capability»; D241 y D255 limitadas a C-09 y C-12). (a) Dos nuevas, `bloqueos-puntuales` (API) y `pantalla-de-bloqueos`, más los deltas de `creacion-de-turnos` y `persistencia-postgresql`, registradas como excepción de C-13; (b) una sola, `bloqueos-puntuales`, con los requisitos de la pantalla adentro; (c) generalizar la regla en `config.yaml`: «una capability de API y, si el change tiene interfaz, su capability de pantalla». **Recomendación: (a)**, o (c) si el autor prefiere dejar de registrar la misma excepción en cada change con interfaz: C-09 y C-12 ya hicieron este corte por suite. Con (b) se juntan los dos specs en uno (B1).
- **Q2. Bloqueo con profesional y sillón a la vez.** Fuente: `04` §Bloqueo define solo «sillón nulo = profesional» y «ambos nulos = consultorio». (a) No se admite: `422` de formato y `CHECK` en la base; (b) bloquea a los dos recursos; (c) bloquea al profesional solo en ese sillón. **Recomendación: (a)**, porque US-003 CA-1 dice «del profesional, del sillón **o** de todo el consultorio» y (b) se arma con dos bloqueos; (c) no tiene respaldo.
- **Q3. Código del bloqueo que no termina después de empezar** (regla dura 4; `04` `CHECK inicio < fin`; precedente D257). (a) Código nuevo **`RN-AG-17`**, validación de entrada, `422`, error de campo `fin`, junto con `RN-GL-01` y `RN-GL-04`; (b) reutilizar `RN-AG-10d` como hace `Intervalo` (E8); (c) reutilizar `RN-AG-04b`. **Recomendación: (a)**: depende solo del cuerpo (entrada, RN-GL-02) y un código propio no confunde con la medianoche del turno ni con el turno sobre un bloqueo. Se registra en `05` con el update.
- **Q4. Profesional o sillón inactivo en el cuerpo.** Fuente: RN-GL-04 («inexistente o inactivo … en el cuerpo → `422`»). (a) `422` `RN-GL-04` con `motivo` `inactivo` (literal); (b) se acepta, porque bloquear un recurso inactivo no daña nada. **Recomendación: (a)**, por la letra de RN-GL-04 y porque un recurso inactivo no admite turnos (RN-AG-07), así que no hay nada que bloquear.
- **Q5. Qué es «la lista de turnos afectados».** Fuente: D83, US-003 CA-2 y RN-AG-04b dicen «lista» sin forma. (a) Solo en la respuesta `201` del `POST`, con los turnos **activos** del alcance que **intersecan** el bloqueo (semiabierto; también los pasados), por `(inicio, id)`, con `id`, `inicio`, `fin`, `estado`, `profesional_id`, `sillon_id` y `paciente_id`, sin nombre del paciente; (b) además una ruta `GET /bloqueos/{id}/turnos-afectados`; (c) con nombre y teléfono del paciente para avisarle. **Recomendación: (a)**: es lo mínimo que pide CA-2; (b) no está en `02`; (c) suma datos personales que la pantalla no necesita para reprogramar (C-16 y C-17 ya tendrán al paciente) y la agenda del día (C-14) mostrará los turnos.
- **Q6. Bloqueos superpuestos o repetidos.** La KB no tiene ninguna regla. (a) Se aceptan; (b) se rechazan con un código nuevo. **Recomendación: (a)**: no dañan (un turno se rechaza igual) y (b) sería una regla inventada.
- **Q7. Bloqueos en el pasado.** La KB no dice nada. (a) Se aceptan (no se usa `utc_now()` en el alta); (b) se rechaza un bloqueo con `fin <= ahora` con un código nuevo. **Recomendación: (a)**: (b) inventa una regla, y un bloqueo que empieza hoy temprano y sigue hasta mañana es válido.
- **Q8. Eliminar.** Fuente: `03` («D = eliminar/anular»), `02` (`DELETE`), `04` (sin estado en la tabla). (a) Borrado físico, `204`, solo `odontologo`, sin tocar turnos, también un bloqueo pasado; `404` `RN-GL-04` para uno inexistente o de otro consultorio; (b) borrado lógico con una columna nueva. **Recomendación: (a)**, porque la tabla de `04` no tiene estado; (b) agrega una columna y un filtro que nadie pide.
- **Q9. `GET /bloqueos`.** (a) Todos los del consultorio, pasados y futuros, por `(inicio, id)`, dentro de `{zona_horaria, bloqueos}`, sin filtros; (b) solo los que no terminaron (`fin > ahora`); (c) con filtros `desde`/`hasta`. **Recomendación: (a)**: un consultorio chico tiene pocos bloqueos; (b) esconde datos y suma el reloj; (c) lo puede agregar C-24 si lo necesita.
- **Q10. RN-AG-04b en `POST /turnos`: orden y detalle.** Fuente: `07` Flujo 1 (paso 5, horario y bloqueos; casos de error `422` `RN-AG-04b`), RN-AG-04b («prevalecen»), D129. (a) Orden entrada → RN-AG-10d → RN-AG-04 → **RN-AG-04b** → solapamiento; `422` con `type` `/errores/sobre-bloqueo` y `bloqueo_id` del que empieza primero; (b) RN-AG-04b antes que RN-AG-04; (c) sin `bloqueo_id`. **Recomendación: (a)**: sigue el orden del texto de `07`, y `bloqueo_id` es «el detalle necesario para que los tests lo verifiquen» (RN-GL-02), como `turno_id` en el solapamiento.
- **Q11. Bloqueo y turno simultáneos.** (a) Límite aceptado y documentado (B11), como D261/H11 en C-12; (b) serializar con bloqueos de fila (profesional, sillón o consultorio) y que `crear_turno` lea los bloqueos después del suyo. **Recomendación: (a)**: el bloqueo no cancela turnos (D83), así que un turno que entra en el mismo instante queda como cualquier turno anterior al bloqueo; (b) suma acoplamiento y un test del perfil `postgres`.
- **Q12. Migración `0009` y `creado_por`.** Fuente: `04` §Bloqueo (`creado_por` nulo «cuando existe `Usuario`») y el último número, `0008`. (a) `0009_bloqueo`, `creado_por` **NN**, índices de `04` más `(consultorio_id, inicio)`; (b) `creado_por` nulo, como dice `04`. **Recomendación: (a)**: todas las filas nacen de un token; `04` se ajusta al archivar. Con (b) solo cambia la columna y la fábrica.
- **Q13. `motivo`.** Fuente: `04` («texto NN; vacaciones, feriado, ausencia, mantenimiento»). (a) Texto libre, sin espacios de más, de 1 a 200 caracteres (vacío o más largo: `422` de formato); (b) una lista cerrada de cuatro valores; (c) texto libre sin tope. **Recomendación: (a)**: los cuatro de `04` son ejemplos; 200 es un tope de tamaño del cuerpo, como D268, sin código RN.
- **Q14. Demo.** (a) Sin bloqueos en el seed (los ejemplos del README no cambian y la regla nueva no toca la demo); (b) un bloqueo ficticio de ejemplo (por ejemplo, un feriado) fuera de las horas del README. **Recomendación: (a)**: evita el hueco de orden que tuvo C-12 (seed adelantado antes de cerrar la regla) y el README muestra cómo crear uno desde `/docs` y desde la pantalla.
- **Q15. Hora en la pantalla.** (a) Se escribe y se muestra en la zona del consultorio (`zona_horaria` de la API), convertida con `Intl` sin dependencias, sin opción «Todo el día»; (b) en la zona del navegador; (c) con una casilla «Todo el día» que solo pide fechas. **Recomendación: (a)**: las reglas de horario se evalúan en la zona del consultorio (RN-GL-01) y (c) suma un control y escenarios que US-003 no pide («días u horas» se cubre con 00:00 a 00:00).
- **Q16. Detalles de la pantalla.** (a) Lista y alta en la misma página `/panel/bloqueos`; selector de recurso solo con los activos; turnos afectados con id, fechas y estado, sin el paciente; «Eliminar» sin confirmación; acciones visibles para todos los roles (D230, D249); (b) con confirmación antes de eliminar. **Recomendación: (a)**: el bloqueo eliminado se vuelve a crear igual y no toca turnos; la confirmación suma un paso y un escenario.
- **Q17. Tamaño.** 22 tareas en 10 grupos para 52 escenarios (42 nuevos y 10 copiados), frente a «alrededor de 20» y «3 a 6 escenarios» de `CHANGES.md`. (a) Aceptarlo como excepción registrada de C-13 (como D228 para C-08); (b) recortar (por ejemplo, sacar los escenarios de borde de la pantalla que solo corren contra el servidor falso). **Recomendación: (a)**: RED, GREEN y TRIANGULATE separados por TDD estricto; ya se juntaron persistencia y migración y no hay seed.
- **Q18. Pantalla de Stitch (resuelta, D288).** Se envió el pedido de `stitch-bloqueos.md` (un intento) y el MCP devolvió el id; la sección «Referencia visual (Stitch)» lo cita y lista qué se toma y qué se rechaza, y la tarea 1.2 quedó hecha. Sigue valiendo D234 para el archive: la implementación se compara con la captura.
