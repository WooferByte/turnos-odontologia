# Funcionalidades

Organizadas por **épica** y **historia de usuario** (US-NNN). Versión: **v1** salvo indicación. Cada historia referencia el caso de uso (CU) de `01_vision_y_objetivos.md` y las reglas de `05_reglas_de_negocio.md`.

Cada historia lleva dos líneas de planificación:

- `**Orden**: N` (1 a 9): **orden de implementación, no importancia** (decisión del autor 2026-10-03). Todas las historias de la v1 pertenecen al MVP de la sección D del informe, **salvo US-080 (reportes), que es una extensión fuera de ese MVP**. Dentro de un mismo orden, las dependencias fijan la secuencia.
- `**Depende de**`: historias que deben existir antes. Las historias de panel que distinguen roles dependen de US-092 (Épica 10).

Resumen del orden: **1** US-010 · **2** US-015, US-001, US-004 · **3** Épica 10 (US-090 a US-094), US-002, US-003 · **4** US-011, US-012, US-013, US-014, US-016 · **5** US-070, US-020, US-022, US-005 · **6** US-030, US-031, US-021, US-040 · **7** US-050, US-051 · **8** US-060, US-061, US-062 · **9** US-080. **Changes técnicos** (no son historias; ver «Changes técnicos y frontend»): **infraestructura con PostgreSQL** en el orden 2, justo después de US-010 y antes de US-015, US-001 y US-004 (decisión del autor 2026-10-05, D105) · **tarea periódica con Redis** en el orden 6, antes de US-030. **Interfaz del panel:** empieza en el orden 3; las historias de orden 1 y 2 se implementan y se prueban como API (D106).

**Notas del orden (decisión del autor 2026-10-03):**
- US-010 depende conceptualmente de US-001 y US-004, pero va **primero** porque el primer change crea el subconjunto mínimo (prestación y sillón por seed); US-001 y US-004 agregan después la gestión (alta, edición, desactivación).
- Las historias de orden 1 y 2 (US-010, US-015, US-001, US-004) crean endpoints antes de la Épica 10 (orden 3): van **sin autenticación** hasta que US-092 los proteja (ver US-092 CA-2) (decisión del autor 2026-10-03, DD-14; US-092 confirmada el 2026-10-05, D42). **Desde C-07 (`roles-y-proteccion-del-panel`) la excepción ya no vale**: todas las rutas del panel exigen JWT y rol (D214).
- **API primero (decisión del autor 2026-10-05, D106):** las historias de orden 1 y 2 se implementan y se prueban **como API** (tests de dominio y de API; sin interfaz gráfica). La interfaz del panel empieza en el orden 3, con el inicio de sesión (Épica 10); ver «Changes técnicos y frontend».
- Las historias que leen reglas configurables (RN-GL-03) dependen de US-005, que crea `ConfiguracionReglas` (`04_modelo_de_datos.md`): US-020, US-022, US-030, US-040 y US-050 (propuesta aceptada por el autor 2026-10-03; se revisa en el design del change).
- US-013 CA-2 se completa con US-040 (orden 6) y CA-3 con US-051 (orden 7); los criterios de US-014 que hablan de la seña (CA-5 y CA-10) se completan con US-051 (orden 7): son referencias hacia adelante, no dependencias.
- **Más referencias hacia adelante (decisión del autor 2026-10-05, D99):** US-001 CA-2 y US-012 CA-4 validan contra la granularidad, que vive en `ConfiguracionReglas` (US-005, orden 5): hasta entonces usan la **constante por defecto de 5 minutos**. US-012 CA-3, US-020 CA-3 (aprobación con seña) y US-022 CA-2 hablan de la seña y se completan con US-050 y US-051 (orden 7); `requiere_sena` y `monto_sena` existen desde US-005 pero **no tienen efecto hasta US-050**. US-020 CA-3 (el rechazo dispara la lista de espera) se completa con US-040 (orden 6). US-020 CA-11 entrega el link en la respuesta; el mensaje `wa.me` con el link llega con US-030 (orden 6). US-070 CA-5 se completa con US-021 (orden 6). US-016 CA-7 (consentimiento con origen `panel`) se completa con US-070 (orden 5), y los efectos de US-016 CA-4 (`acepta_contacto`) llegan con US-030 y US-040 (orden 6).
- **Referencias hacia adelante que faltaba declarar (decisión del autor 2026-10-05, D115):** US-091 CA-2 (la recepcionista no ve la ficha clínica) se completa con US-060 (orden 8); US-021 CA-4 y CA-5, en lo que toca a una entrada `ofertada`, se completan con US-040 (orden 6); US-020 CA-10 (aceptación de RN-TD-10 al aceptar una oferta) se completa con US-040 (orden 6). Además, dos acciones que viven en la agenda del día de US-011 (orden 4) llegan con su propia historia: aprobar o rechazar (US-020 CA-12, orden 5; D112) y confirmar desde el panel (US-031 CA-4, orden 6; D113).

**Changes técnicos y frontend (decisión del autor 2026-10-05, D100; orden de la infraestructura y primer frontend precisados en D105 y D106).** No son historias ni tienen criterios de aceptación propios; el roadmap los ubica así:
- **Infraestructura con PostgreSQL:** Docker Compose con PostgreSQL, **Alembic** desde este change (DD-15), la **restricción de exclusión** por profesional y por sillón (DD-04, RN-AG-10c) y el **perfil opcional de tests** con el marcador de pytest para E11, documentado en el README (D75). Va en el **orden 2, justo después del primer change (US-010)** y antes del resto de las historias de orden 2 (**decisión del autor 2026-10-05, D105**), para que las tablas y columnas de los changes siguientes se agreguen con migraciones: **empezar con migraciones temprano evita rehacerlas sobre muchas tablas**. US-020 (orden 5) sigue teniendo este change como dependencia técnica (concurrencia, RN-AG-10c / E11). No cambia la suite por defecto (SQLite en memoria, DD-03).
- **Tarea periódica con Redis:** el worker y el servicio Redis. Va en el **orden 6, antes de US-030**, la primera historia que la usa (recordatorios y mensaje con el link de gestión). Después la usan US-040 (ofrecer huecos, vencimiento de ofertas) y US-050 (vencimiento de señas). **Ninguna historia de orden 1 a 5 depende de vencimientos:** los únicos son el de la oferta (US-040) y el de la seña (US-050). El mecanismo con el que la tarea detecta los vencimientos que persistió una escritura (RN-GL-05) se fija en el design de este change. Los tests no usan Redis.
- **Frontend (React + TypeScript + Vite):** la interfaz de cada historia va con su change, sin inventar pantallas que ningún criterio pide. **Panel autenticado:** US-090, US-093, US-001, US-002, US-003, US-005, US-011 a US-016, US-020 (aprobar o rechazar un turno `pendiente_aprobacion`: acción en la agenda del día de US-011, sin pantalla nueva; D112), US-021 (alta y retiro desde el panel), US-030, US-031 (confirmar un turno desde el panel: acción en la agenda del día de US-011, sin pantalla nueva; D113), US-040, US-051 (acción manual sobre la seña), US-060 a US-062 y US-080. **Páginas públicas:** US-020 (con US-070), US-021, US-022, US-031 y US-050. **Sin interfaz:** US-010 (solo API; la pantalla de crear turno desde el panel va con US-011, D110), US-004, US-091, US-092 y US-094. El panel exige sesión (US-090 y US-092, orden 3): **API primero (decisión del autor 2026-10-05, D106):** las historias de **orden 1 y 2** (US-010, US-015, US-001, US-004) y el change de infraestructura con PostgreSQL se implementan y se prueban **como API** (tests de dominio y de API; sin interfaz gráfica). **La interfaz del panel empieza en el orden 3**, con el inicio de sesión (Épica 10); la interfaz de las historias de orden 2 que figuran en el panel (US-001 y US-015) se construye **a partir de ahí**.

Los criterios de US-010 usan IDs estables `E1..E12` (compartidos con `07_flujos_principales.md` y con el spec y los tests del change). El autor implementará el proyecto completo antes de fin de año, change por change (decisión 2026-10-03); US-010 es el primero y el hito de entrega de la consigna.

## Épica 1: Configuración de agenda

### US-001 — Tabla de prestaciones
**Como** odontólogo **quiero** definir prestaciones con nombre, duración por defecto y color **para** que cada turno ocupe el tiempo real que necesita.
- [ ] CA-1: puedo crear, editar y desactivar prestaciones; el nombre es único en el consultorio, sin distinguir mayúsculas, tildes ni espacios de más (una prestación inactiva sigue ocupando su nombre); si se repite, se rechaza con `409` y el error de dominio `RN-AG-15` (D171, D172). **Implementada en C-04** como API: `GET/POST /prestaciones` y `PATCH /prestaciones/{id}` (desactivar es `activa: false`), sin autenticación hasta C-07 y sobre el único consultorio de la instalación (D173); la pantalla llega con el panel.
- [ ] CA-2: la duración debe ser > 0 y múltiplo de la granularidad; si no, se rechaza con el error de dominio `RN-AG-01`. Hasta US-005 la granularidad es la constante por defecto de 5 minutos (referencia hacia adelante, D99).
- [ ] CA-3: cambiar la duración no modifica turnos existentes.
**Orden**: 2
**Depende de**: Ninguna
**Reglas**: RN-AG-01, RN-AG-02, RN-AG-15, RN-GL-03

### US-002 — Horario recurrente
**Como** odontólogo **quiero** configurar mis días y franjas de atención **para** que solo se ofrezcan turnos dentro de ese horario.
- [ ] CA-1: puedo cargar varias franjas por día (p. ej. mañana y tarde) sin que se superpongan entre sí; si dos franjas del mismo día se superponen o una no termina después de empezar, se rechaza con `422` y el error de dominio `RN-AG-16`, informando todas juntas (decisión del autor 2026-10-22, D257).
- [ ] CA-2: un turno que excede el fin de la franja se rechaza.
**Orden**: 3
**Depende de**: US-092
**Reglas**: RN-AG-04, RN-AG-16

### US-003 — Bloqueos puntuales
**Como** odontólogo **quiero** bloquear días u horas (vacaciones, feriados, ausencias) **para** que no se reserven turnos en esos momentos.
- [ ] CA-1: el bloqueo puede ser del profesional, del sillón o de todo el consultorio.
- [ ] CA-2: al crear un bloqueo sobre turnos activos, el sistema lista los afectados.
**Orden**: 3
**Depende de**: US-092
**Reglas**: RN-AG-04b

### US-004 — Sillón como recurso
**Como** odontólogo **quiero** que el consultorio tenga un sillón por defecto **para** que la agenda controle su ocupación sin configuración extra.
- [ ] CA-1: el seed crea "Sillón 1"; todo turno sin sillón explícito se asigna a él mientras sea el único sillón activo (RN-AG-14, D125; con más de uno activo hay que indicarlo).
- [ ] CA-2: el modelo admite agregar más sillones (la UI multi-sillón es Fase 2).
- [ ] CA-3: puedo dar de alta un sillón y desactivarlo (`POST /sillones`, `PATCH /sillones/{id}`); un sillón inactivo no admite turnos nuevos (RN-AG-07). CA-1 ya lo cumple el primer change; este change agrega la gestión. **Implementada en C-05** como API: `GET/POST /sillones` y `PATCH /sillones/{id}` con `nombre` y `activo` (desactivar es `activo: false`; también se reactiva, D185); el nombre no es único (D183) y se puede desactivar el último sillón activo (D184, después un turno sin sillón se rechaza con `ninguno_activo`); sin autenticación hasta C-07 y sobre el único consultorio de la instalación (D187); la pantalla multi-sillón es Fase 2.
**Orden**: 2
**Depende de**: Ninguna
**Reglas**: RN-AG-06, RN-AG-07

### US-005 — Reglas configurables
**Como** odontólogo **quiero** ajustar antelaciones, horizonte, aprobación de nuevos y seña **para** adaptar el sistema a mi forma de trabajo.
- [ ] CA-1: la antelación de cancelación solo acepta valores entre 24 y 48 h.
- [ ] CA-2: todos los valores arrancan con los defaults propuestos.
**Orden**: 5
**Depende de**: US-092
**Reglas**: RN-TD-01, RN-TD-02, RN-TD-03, RN-TD-05, RN-SP-01

## Épica 2: Gestión de turnos (núcleo)

### US-010 — Crear turno sin solapamientos por profesional y por sillón ⭐ (change candidato de la consigna)
**Como** recepcionista (o el propio odontólogo) **quiero** crear un turno para un paciente, prestación, profesional y sillón **para** agendarlo sin superponerlo con otro.

**Escenarios con ID estable** (decisión del autor 2026-10-03; reemplazan a los antiguos CA-1..CA-8). Cada escenario del primer change (E1..E7 y E12) tiene **un test**:

| ID | Escenario | ¿Entra en el primer change? |
|---|---|---|
| E1 | **Feliz**: hueco libre; el turno se crea `reservado` con `fin = inicio + duración de la prestación` (RN-AG-02) | **Sí** |
| E2 | **Error de negocio (profesional)**: el profesional tiene un turno activo que se superpone; se rechaza con `RN-AG-05` | **Sí** |
| E3 | **Error de negocio (sillón)**: el sillón tiene un turno activo que se superpone (aunque sea de otro profesional); se rechaza con `RN-AG-08` | **Sí** |
| E4 | **Doble conflicto**: el turno choca con el profesional y con el sillón a la vez; se informan **los dos** errores (`RN-AG-05` y `RN-AG-08`) | **Sí** |
| E5 | **Borde contiguo**: un turno que empieza exactamente cuando termina otro se acepta (RN-AG-09) | **Sí** |
| E6 | **Estado no activo**: un turno cancelado, vencido, atendido o ausente no bloquea el horario (RN-AG-10) | **Sí** |
| E7 | **Borde de un minuto**: un solapamiento de un minuto se rechaza | **Sí** |
| E8 | Intervalo inválido (`inicio >= fin`, naive, fuera de UTC o que cruza la medianoche del consultorio) se rechaza (RN-AG-10d, RN-GL-01). Naive o fuera de UTC es **validación de entrada**; `inicio >= fin` y el cruce de la medianoche son **regla de negocio** (RN-GL-02, D135) | **No como escenario del spec**: lo cubre un test unitario del value object `Intervalo` (decisión del autor 2026-10-03) |
| E9 | La creación queda registrada en el historial (antes CA-7; RN-AG-11) | **No: fuera del primer change** (decisión del autor 2026-10-03). **Se especifica y se prueba en C-03**, en la capability `historial-de-turnos` (D158) |
| E10 | Un turno fuera del horario o sobre un bloqueo se rechaza (RN-AG-04/04b; antes CA-8) | **No** (decisión del autor 2026-10-02, P-10) |
| E11 | Dos reservas concurrentes del mismo hueco: solo una gana (RN-AG-10c) | **No** (no verificable con SQLite; corre solo en un perfil opcional con PostgreSQL, con un marcador de pytest, fuera de la suite por defecto; decisión del autor 2026-10-03 y 2026-10-05, D75). **Se especifica y se prueba en C-02**, en la capability `persistencia-postgresql` (D142), con el bloqueo de fila por recurso y la restricción de exclusión (D157) |
| E12 | **Recurso no encontrado**: prestación, profesional o sillón inexistente o inactivo, o paciente inexistente (el paciente no tiene estado de actividad en la v1, D136), referenciado en el cuerpo, se rechaza con `RN-GL-04` (RN-AG-07, RN-AG-14), listando **todas** las referencias inválidas (D127); en HTTP, `422` (`404` queda para un recurso inexistente identificado en la URL). Es validación de entrada: si además la fecha no tiene zona o no está en UTC, el mismo `422` lleva también `RN-GL-01` (RN-GL-02, D135) | **Sí** (decisión del autor 2026-10-03; `422` confirmado el 2026-10-05, D73) |

- **Nota del orden**: US-010 es el change de la consigna y el hito de entrega. Depende conceptualmente de US-001 y US-004, pero va primero porque este change crea el subconjunto mínimo (prestación y sillón por seed); US-001 y US-004 agregan después la gestión (decisión del autor 2026-10-03).
- **Estado inicial** del turno en el primer change: `reservado` (decisión del autor 2026-10-03; `pendiente_sena` depende de la seña, fuera del primer change).
- **Endpoint:** el primer change expone `POST /turnos` (FastAPI) para probarlo desde Swagger (`/docs`), **sin autenticación** (límite conocido, decisión del autor 2026-10-03, DD-14); se protege con JWT en el change de usuarios y acceso (US-092). Sin interfaz gráfica. **Desde C-07 (`roles-y-proteccion-del-panel`) la excepción ya no vale**: todas las rutas del panel exigen JWT y rol (D214).
- **Tamaño (decisión del autor 2026-10-07, D123):** el primer change conserva sus 8 escenarios (E1..E7 y E12) como **excepción registrada** a la regla de «3 a 6 escenarios» de `CHANGES.md`: son variantes cortas de una sola regla, la KB ya las definió y recortarlas dejaría casos definidos sin probar. La excepción vale solo para este change y debe constar también en su `proposal.md`. **Segunda excepción (decisión del autor 2026-10-07, D134):** sus tareas (53) superan el «alrededor de 20» de `CHANGES.md`; se aceptan con la condición de que vayan agrupadas por tema, y consta en `proposal.md` y en el encabezado de `tasks.md`.
- **Recursos por defecto, consultorio y errores (decisiones del autor 2026-10-07, D125 a D129):** si no se indica el sillón o el profesional se usa el único activo, y si no hay uno solo se rechaza con `RN-GL-04` (RN-AG-14); el consultorio del turno sale del profesional; `RN-GL-04` lista todas las referencias inválidas; un `Conflicto` por recurso con el turno que empieza primero.
- **Cómo se informan los errores (decisión del autor 2026-10-07, D135 y D136; RN-GL-02):** los problemas de **validación de entrada** (referencias inválidas, `RN-GL-04`; fecha sin zona o fuera de UTC, `RN-GL-01`; cuerpo mal formado) se informan **todos juntos** en un único `422`; las **reglas de negocio** se evalúan solo con la entrada válida y **de a una** (primero RN-AG-10d, después el solapamiento). El solapamiento es una sola regla que mira dos recursos: E4 sigue informando los dos códigos (**lectura confirmada por el autor**, 2026-10-07, D139). Un paciente solo puede ser `inexistente`.
**Orden**: 1
**Depende de**: Ninguna (conceptualmente usa US-001 y US-004; ver nota del orden). E10 dependería además de US-002 y US-003
**Reglas**: RN-AG-02, RN-AG-05, RN-AG-06, RN-AG-08, RN-AG-09, RN-AG-10, RN-AG-10b (reprogramar: fuera del primer change), RN-AG-10c, RN-AG-10d, RN-AG-14, RN-AG-11 (historial: **fuera del primer change**, implementado en C-03), RN-GL-01, RN-GL-02, RN-GL-04

### US-011 — Agenda del día
**Como** odontólogo **quiero** ver los turnos del día con color por prestación y estado **para** organizar la atención.
- [ ] CA-1: se listan los turnos del profesional ordenados por inicio, con paciente, prestación y estado.
- [ ] CA-2 (crear turno desde la agenda; decisión del autor 2026-10-05, D110): desde la agenda del día se crea un turno con un formulario que usa `POST /turnos` (US-010). Esta pantalla pertenece a US-011; US-010 sigue siendo solo API, sin interfaz. Las reglas y los errores de dominio son los de US-010 (el formulario los muestra).
**Orden**: 4
**Depende de**: US-010, US-092
**Reglas**: RN-AG-01

### US-012 — Reprogramar turno (panel)
**Como** recepcionista **quiero** mover un turno a otro horario **para** acomodar cambios sin perder el historial.
- [ ] CA-1: se valida como un turno nuevo, excluyéndose a sí mismo.
- [ ] CA-2: el historial guarda el horario anterior y el nuevo.
- [ ] CA-3: la reprogramación conserva la seña ya acreditada: modifica el mismo turno y la seña cuelga del turno (RN-TD-04, decisión del autor 2026-10-05, D66). Este criterio se completa con US-050.
- [ ] CA-4: desde el panel se puede **modificar la duración** del turno (RN-AG-02): `fin` se recalcula y el turno se valida como en CA-1. La duración nueva debe ser > 0 y **múltiplo de la granularidad** (5 minutos como constante hasta US-005); si no, se rechaza con el error de dominio `RN-AG-01` y el turno no cambia. Fuera del primer change: `CrearTurnoComando` no lleva duración (decisión del autor 2026-10-05, D98).
**Orden**: 4
**Depende de**: US-010, US-015, US-092
**Reglas**: RN-AG-01, RN-AG-02, RN-AG-10b, RN-AG-11, RN-TD-04

### US-013 — Cancelar turno (panel) y liberar horario
**Como** recepcionista **quiero** cancelar un turno **para** liberar el horario y ofrecerlo a la lista de espera.
- [ ] CA-1: el turno pasa a `cancelado_profesional` o `cancelado_paciente` según quién lo pidió.
- [ ] CA-2: el horario queda libre y se dispara la búsqueda en la lista de espera.
- [ ] CA-3: si había seña y cancela el odontólogo, la seña se marca para devolución.
**Orden**: 4
**Depende de**: US-010, US-015, US-092 (CA-2 se completa con US-040; CA-3 con US-051)
**Reglas**: RN-AG-10, RN-LE-01, RN-SP-05

### US-014 — Marcar atendido / ausente
**Como** odontólogo o recepcionista **quiero** marcar si el paciente asistió **para** medir el ausentismo.
- [ ] CA-1: el odontólogo y la recepcionista pueden marcar un turno como `atendido` o `ausente` (RN-AG-13, decisión del autor 2026-10-03).
- [ ] CA-2: solo desde `reservado` o `confirmado`; al marcarlo, el turno deja de ser activo y libera el horario (RN-AG-12, RN-AG-10).
- [ ] CA-3 (error): si el turno está en otro estado (por ejemplo `cancelado_paciente`, `vencido`, `pendiente_sena` o `pendiente_aprobacion`), se rechaza con el error de dominio `RN-AG-12` y el turno no cambia.
- [ ] CA-4: el cambio queda en el historial con quién lo hizo y cuándo (RN-AG-11).
- [ ] CA-5: si el turno queda `ausente` y tiene seña acreditada, la seña pasa a `retenida` (RN-SP-04 (a)); este criterio se completa con US-051.
- [ ] CA-6 (error): solo se puede marcar `atendido` o `ausente` si `ahora >= inicio` del turno; antes se rechaza con el error de dominio `RN-AG-13` y el turno no cambia (decisión del autor 2026-10-05, D34).
- [ ] CA-7: **corrección del marcado**: se permite pasar de `atendido` a `ausente` y de `ausente` a `atendido`; el cambio queda en el historial con quién, cuándo, valor anterior y valor nuevo (RN-AG-13, RN-AG-11).
- [ ] CA-8 (error): la corrección solo se admite dentro de las 24 horas posteriores al marcado original (el momento sale del historial `EventoTurno`); pasado ese plazo se rechaza con `RN-AG-12`. Una corrección posterior requiere una acción administrativa explícita (**Fase 2**).
- [ ] CA-9 (error): solo el rol `odontologo` puede corregir el marcado; la recepcionista y el dueño reciben `403` (RN-AG-13, RN-AU-05).
- [ ] CA-10: **la seña no acompaña automáticamente la corrección**, en ninguno de los dos sentidos: si se corrige `ausente` → `atendido`, la seña queda `retenida` y el odontólogo debe devolverla manualmente con registro; si se corrige `atendido` → `ausente`, la seña sigue `acreditada` y el odontólogo puede retenerla manualmente con registro (RN-SP-10). Motivo: evitar que la corrección sea un mecanismo para retener o devolver dinero sin control. Este criterio se completa con US-051.
- [ ] CA-11: al marcar `atendido` el **primer** turno de un paciente, `Paciente.es_nuevo` pasa a `false`; una corrección posterior `atendido` → `ausente` no lo revierte. Este change agrega la columna (default `true`), que US-020 usa para la aprobación manual (RN-TD-05, D52; decisión del autor 2026-10-05, D99).
**Orden**: 4
**Depende de**: US-010, US-015, US-092
**Reglas**: RN-AG-10, RN-AG-11, RN-AG-12, RN-AG-13, RN-SP-04, RN-SP-10, RN-TD-05

### US-015 — Historial de cambios
**Como** dueño **quiero** ver quién cambió qué y cuándo en cada turno **para** tener trazabilidad.
- [ ] CA-1: el historial es de solo lectura y no puede editarse.
**Orden**: 2
**Depende de**: US-010
**Reglas**: RN-AG-11

### US-016 — Pacientes: datos administrativos desde el panel
**Como** recepcionista (o el propio odontólogo) **quiero** dar de alta, buscar y editar los datos administrativos de un paciente **para** agendarle turnos sin depender del link público.
Historia agregada por decisión del autor (2026-10-05, D95; alta con aviso de posible duplicado, D108). Cubre solo los datos **administrativos** (identificación y contacto); los datos clínicos son de US-060 (RN-FC-02).
- [ ] CA-1 (alta): `POST /pacientes` crea un paciente con nombre, apellido y teléfono de WhatsApp (obligatorios; el teléfono en E.164) y, opcionalmente, DNI, email y fecha de nacimiento. Este change agrega a `Paciente` las columnas `dni`, `email`, `fecha_nacimiento`, `creado_en` y `acepta_contacto` (`04_modelo_de_datos.md`).
- [ ] CA-2 (edición): `PATCH /pacientes/{id}` modifica esos datos. Crean y editan el odontólogo y la recepcionista; el dueño solo lee (matriz de `03_actores_y_roles.md`).
- [ ] CA-3 (búsqueda y listado): `GET /pacientes` lista los pacientes del consultorio y permite buscar por nombre, apellido o teléfono; `GET /pacientes/{id}` devuelve los datos administrativos de uno.
- [ ] CA-4 (no contactar): el odontólogo o la recepcionista cambian `acepta_contacto` (default `true`) con `PATCH /pacientes/{id}`; el paciente lo pide comunicándose con el consultorio (RN-PR-07, D81). Sus efectos sobre los mensajes y las ofertas llegan con US-030 y US-040.
- [ ] CA-5 (error): un alta sin nombre, apellido o teléfono, o con un teléfono que no está en E.164, se rechaza con `422` y no se crea ni modifica el paciente.
- [ ] CA-6 (error): un rol insuficiente recibe `403` (por ejemplo, el dueño que intenta crear o editar; RN-AU-05); un id inexistente en la URL, `404` (RN-GL-04).
- [ ] CA-7 (consentimiento en persona): el panel registra el consentimiento del paciente con origen `panel` y la versión vigente del texto (**ruta propuesta** `POST /pacientes/{id}/consentimientos`; se fija en el design del change). No bloquea la carga de turnos (RN-PR-02, D37). **Se completa con US-070** (orden 5), que crea `Consentimiento`: referencia hacia adelante.
- [ ] CA-8: las respuestas no incluyen datos clínicos (RN-FC-02), y los pacientes de seeds, tests y ejemplos son siempre ficticios (RN-PR-01).
- [ ] CA-9 (alta sin coincidencias; RN-TD-12, decisión del autor 2026-10-05, D108): si el paciente que se da de alta no coincide con ninguno existente, `POST /pacientes` lo crea sin más y no registra ningún evento `posible_duplicado`.
- [ ] CA-10 (posible duplicado sin confirmar; RN-TD-12, D108): si existe otro paciente del consultorio que coincide por **teléfono y nombre** (motivo `telefono_y_nombre`: teléfono, nombre y apellido normalizados, RN-TD-09) o **solo por teléfono** (motivo `solo_telefono`: coincide el teléfono pero no el nombre o el apellido; por ejemplo, un error de tipeo o un familiar que usa el mismo número), `POST /pacientes` **no crea nada** y responde con las coincidencias, **cada una con su motivo** (id, nombre, apellido, teléfono y motivo; los nombres de los motivos son propuestos; el estado HTTP y la forma de la respuesta se fijan en el design del change). El panel **avisa y muestra las coincidencias, diciendo por qué coincide cada paciente**, y quien carga elige **usar el existente** (no se crea nada y sigue con ese paciente) o **crear uno nuevo** (CA-11). **No bloquea, no fusiona y no oculta** a ningún paciente; la fusión manual es Fase 2 (RN-TD-09). El aviso por solo teléfono fue aceptado por el autor (2026-10-05, D109).
- [ ] CA-11 (crear igual, con evento; RN-TD-12, D108): si la petición trae la **confirmación explícita de crear igual** (indicador booleano; el nombre del campo se fija en el design del change), `POST /pacientes` crea el paciente y registra un `EventoPaciente` de tipo `posible_duplicado`, con `actor_id` (quien lo cargó), `ocurrido_en` y `detalle` con los ids de los pacientes coincidentes y el motivo de cada uno (`telefono_y_nombre` o `solo_telefono`). Este change crea `EventoPaciente` (entidad **Propuesta**, solo inserción, a revisar en su design; `04_modelo_de_datos.md`). Sin coincidencias, el indicador no tiene efecto (CA-9).
- [ ] CA-12 (eventos del paciente; D111): el alta desde el panel registra un `EventoPaciente` `creado`; la edición de datos administrativos, uno `editado`; el cambio de `acepta_contacto`, uno `contacto_cambiado` (y no `editado` por el mismo cambio); y el alta confirmada con *crear igual* registra además el `posible_duplicado` de CA-11. Cada hecho va en una sola tabla: no se duplica en `EventoTurno` (regla de reparto en `04_modelo_de_datos.md`).
**Orden**: 4
**Depende de**: US-010, US-092 (CA-7 se completa con US-070)
**Reglas**: RN-PR-01, RN-PR-02, RN-PR-07, RN-TD-09, RN-TD-12, RN-FC-02, RN-AU-05, RN-GL-04

## Épica 3: Reserva y autogestión del paciente

### US-020 — Reserva online 24/7 por link (CU-01)
**Como** paciente **quiero** elegir prestación y horario desde el celular **para** sacar turno en menos de 30 segundos sin depender del horario de atención.
- [ ] CA-1: solo se muestran huecos que respetan horario, bloqueos, solapamientos, horizonte (60 días) y antelación mínima (2 h).
- [ ] CA-2: debo aceptar el consentimiento de datos para confirmar.
- [ ] CA-2b: no necesito cuenta; ingreso mi teléfono de WhatsApp (obligatorio) y, opcionalmente, DNI y email; gestiono el turno por token (DD-11, SU-03).
- [ ] CA-3: si soy paciente nuevo y la aprobación manual está activa, el turno queda `pendiente_aprobacion` (ocupa el horario). Si el odontólogo lo rechaza, pasa a `cancelado_profesional`, libera el horario y dispara la lista de espera; si lo aprueba, pasa a `reservado` o, si se exige seña, a `pendiente_sena` (la seña se crea al aprobar y su plazo empieza ahí) (RN-TD-05, RN-SP-02; decisión del autor 2026-10-05, D76). La parte de la seña se completa con US-050 y el disparo de la lista de espera con US-040 (referencias hacia adelante).
- [ ] CA-4: si dos personas reservan el mismo hueco a la vez, solo una lo obtiene.
- [ ] CA-5: la reserva **reutiliza un paciente existente solo si coinciden los tres: teléfono, nombre y apellido normalizados** (teléfono en E.164; nombre y apellido sin distinguir mayúsculas, sin acentos y sin espacios de más); si difiere cualquiera, crea un paciente nuevo (RN-TD-09, decisión del autor 2026-10-05, D48).
- [ ] CA-6 (privacidad): la respuesta de la reserva es **idéntica** se reutilice o no el paciente, y el formulario público **no pisa datos ya cargados**: DNI y email solo se completan si estaban vacíos (RN-PR-06, RN-TD-09).
- [ ] CA-7 (limitación conocida): un error de tipeo («Gonzalez» / «Gonzales») crea un paciente duplicado, que vuelve a dar el consentimiento; la fusión manual de duplicados es **Fase 2** (RN-TD-09).
- [ ] CA-8 (aviso, RN-TD-10, decisión del autor 2026-10-05, D87): si `inicio − ahora < antelacion_cancelacion_horas` (valor vigente, RN-TD-03), antes de confirmar la reserva avisa que ese turno **no va a poder cancelarse ni reprogramarse online**, y el botón de confirmación dice **«Confirmar sin derecho a cancelación»**. Si la reserva no está en esa condición, no hay aviso y el botón es el habitual.
- [ ] CA-9 (error): una reserva en esa condición exige en la petición la **aceptación explícita** (un indicador booleano; el nombre del campo se fija en el design del change); sin ella se rechaza con el error de dominio `RN-TD-10` y **no se crea el turno**. Con la aceptación, el turno se crea y la aceptación queda registrada en el historial (evento de creación, RN-AG-11). Si la reserva no está en esa condición, el indicador no hace falta.
- [ ] CA-10: lo mismo vale al aceptar una oferta de lista de espera cuyo hueco cae dentro de la ventana (RN-TD-10, RN-LE-04). No aplica a los turnos cargados desde el panel.
- [ ] CA-11 (link de gestión; decisión del autor 2026-10-05, D93 y D94): la respuesta de la reserva **devuelve el link de gestión** del turno y la pantalla de confirmación lo muestra; hasta US-030 no se prepara ningún mensaje `wa.me`. Este change crea `Turno.token_gestion` y **genera el token de todo turno, también de los cargados desde el panel y de los ya existentes**; ese token sirve para el mismo flujo de gestión (RN-TD-08).
- [ ] CA-12 (dónde se aprueba; decisión del autor 2026-10-05, D112): los turnos `pendiente_aprobacion` se ven en la **agenda del día** del panel (interfaz de US-011) con las acciones **aprobar** y **rechazar** (`POST /turnos/{id}/aprobar` y `POST /turnos/{id}/rechazar`); no hay una pantalla nueva. Solo el rol `odontologo` aprueba o rechaza: la recepcionista y el dueño reciben `403` (RN-TD-05, RN-AU-05). El resultado de cada acción es el de CA-3.
**Orden**: 5
**Depende de**: US-001, US-002, US-003, US-005, US-010, US-011 (agenda del día, CA-12), US-014 (`es_nuevo`), US-015 (historial), US-070; dependencia técnica: change de infraestructura con PostgreSQL (concurrencia, RN-AG-10c / E11)
**Reglas**: RN-TD-01, RN-TD-02, RN-TD-03, RN-TD-05, RN-TD-06, RN-TD-08, RN-TD-09, RN-TD-10, RN-AG-03, RN-AG-10c, RN-PR-02, RN-PR-06, RN-AU-05

### US-021 — Sin horarios: lista de espera (CU-06)
**Como** paciente **quiero** anotarme en lista de espera cuando no hay horarios **para** que me avisen si se libera uno.
- [ ] CA-1: cuando la disponibilidad no devuelve huecos en el rango pedido, la reserva pública ofrece anotarse en la lista de espera (RN-TD-07, Flujo 2).
- [ ] CA-2 (error): para anotarse **desde el link público** el paciente debe aceptar el consentimiento de datos; sin aceptarlo no se crea la entrada (RN-LE-05, RN-PR-02). Desde el panel no bloquea (CA-8).
- [ ] CA-3: la entrada se crea en estado `activa` con el paciente (teléfono de WhatsApp obligatorio, DNI opcional, SU-03; se reutiliza un paciente existente solo si coinciden teléfono, nombre y apellido normalizados, RN-TD-09), la prestación (**obligatoria**: el turno exige una, D78) y las preferencias, una lista de franjas `{dia_semana, desde, hasta}` en hora del consultorio (lista vacía = cualquier horario, RN-LE-01); su `creada_en` define el orden FIFO (RN-LE-02). No requiere cuenta ni autenticación (`POST /public/{slug}/lista-espera`).
- [ ] CA-4: el paciente puede retirarse desde su link y la entrada pasa a `retirada` (RN-LE-06 (a)). Vale también para una entrada `ofertada`: su oferta se da por rechazada y el hueco pasa al siguiente (RN-LE-06, D60).
- [ ] CA-5: el consultorio puede retirar la entrada desde el panel y pasa a `retirada` (RN-LE-06 (b)); también si está `ofertada` (D60).
- [ ] CA-6 (borde): hay **una sola entrada en curso (`activa` u `ofertada`) por paciente y prestación**; un segundo intento de anotarse con el mismo paciente y la misma prestación no crea otra entrada y devuelve la existente (RN-LE-07, decisión del autor 2026-10-05, D35 y D60). Como la prestación es obligatoria, no existe una entrada «cualquier prestación» (D78, que corrige D53).
- [ ] CA-7 (error): una entrada sin prestación se rechaza (RN-LE-07, D78).
- [ ] CA-8 (alta desde el panel; decisión del autor 2026-10-05, D103 y D107): el odontólogo o la recepcionista pueden anotar a un paciente desde el panel (`POST /lista-espera`), con las mismas reglas (prestación obligatoria, una sola entrada en curso por paciente y prestación); **la falta de consentimiento no bloquea el alta**: el consentimiento se registra con origen `panel` cuando el paciente lo da en persona, igual que al cargar un turno desde el panel (RN-LE-05, RN-PR-02; US-016 CA-7). En el link público sigue siendo obligatorio (CA-2).
**Orden**: 6
**Depende de**: US-016, US-020, US-070, US-092
**Reglas**: RN-TD-07, RN-TD-09, RN-LE-01, RN-LE-02, RN-LE-05, RN-LE-06, RN-LE-07

### US-022 — Cancelar o reprogramar por el paciente (CU-05)
**Como** paciente **quiero** cancelar o reprogramar desde el link del turno **para** liberar el horario con anticipación.
- [ ] CA-1: permitido hasta 24 h antes (configurable 24-48; se usa el valor vigente al momento de cancelar, RN-TD-03); después, el link indica contactar al consultorio. Un turno reservado con menos antelación que esa ventana está fuera de plazo desde el primer minuto: lo aceptó al reservar (RN-TD-10, US-020 CA-8 y CA-9).
- [ ] CA-2: la reprogramación aplica las mismas reglas que una reserva y conserva la seña ya acreditada (RN-TD-04, D66); lo de la seña se completa con US-050.
- [ ] CA-3: las acciones del link dependen del estado del turno (RN-TD-08, decisión del autor 2026-10-05, D77): **cancelar** en `pendiente_aprobacion`, `pendiente_sena`, `reservado` y `confirmado`; **reprogramar** solo en `reservado` y `confirmado` (no cambia el estado, DD-05). En un estado terminal (`cancelado_*`, `vencido`, `atendido`, `ausente`) el link solo muestra el estado. Una acción no permitida para el estado se rechaza con el error de dominio `RN-TD-11` (CA-5).
- [ ] CA-4: toda acción exige que el turno no haya empezado (`ahora < inicio`); cancelar y reprogramar exigen además estar dentro de plazo (CA-1). El token no tiene vencimiento propio: su validez sale del turno (RN-TD-08).
- [ ] CA-5 (error, RN-TD-11, decisión del autor 2026-10-05, D89): una acción pedida con el token que no está permitida por el estado del turno (RN-TD-08), o porque el turno ya empezó, se rechaza con el error de dominio `RN-TD-11` («acción no permitida para el estado del turno»), con estado HTTP propuesto `409` (se fija en el design). El mensaje indica el estado actual del turno y la lista de acciones permitidas en ese estado; no modifica el turno ni el historial. **Estar fuera de plazo para cancelar o reprogramar (CA-1) no es RN-TD-11: sigue siendo RN-TD-03.**
**Orden**: 5
**Depende de**: US-005, US-010, US-015, US-020
**Reglas**: RN-TD-03, RN-TD-04, RN-TD-08, RN-TD-11, RN-SP-04, RN-SP-06

## Épica 4: Recordatorio y confirmación por WhatsApp (CU-02)

### US-030 — Recordatorio 24 h antes
**Como** odontólogo **quiero** que el sistema recuerde el turno 24 h antes **para** reducir ausencias.
- [ ] CA-1 (`wa.me`, v1): el panel muestra la lista de recordatorios del día con el enlace listo para enviar; el odontólogo lo envía desde su WhatsApp y marca el mensaje como enviado.
- [ ] CA-2 (Cloud API, **Fase 2**, posterior a la v1): un adaptador sobre el puerto de mensajería envía el mensaje con plantilla y link de gestión (decisión del autor 2026-10-03, DD-06).
- [ ] CA-3: la marca «no contactar» (`Paciente.acepta_contacto = false`) la cargan el odontólogo o la recepcionista desde el panel (US-016 CA-4, que crea la columna); este change es el primero que la **aplica** (RN-PR-07, decisión del autor 2026-10-05, D81 y D95).
- [ ] CA-4 (borde): con `acepta_contacto = false` no se preparan recordatorios ni ningún otro mensaje. La tarea periódica verifica el campo justo antes de preparar cada mensaje, incluidos los ya programados: un mensaje programado para alguien que dejó de aceptar contacto no se genera y queda `descartado`. La ficha clínica, los turnos y el link de gestión no se ven afectados.
- [ ] CA-5: la tarea periódica prepara el recordatorio al llegar `inicio − 24 h`; los tests no necesitan Redis (RN-GL-05, D80).
- [ ] CA-6 (mensaje con el link de gestión; decisión del autor 2026-10-05, D93): desde este change, al crearse un turno (por el link público, el panel o la lista de espera) la tarea periódica prepara el mensaje `wa.me` con el link de gestión (`Mensaje` de tipo `confirmacion`), que el odontólogo envía igual que un recordatorio; el recordatorio también lleva el link. Antes de este change el link solo se entrega en la respuesta de la reserva (US-020 CA-11). El tipo `aviso_cancelacion` queda **reservado**: ninguna historia de la v1 lo usa.
**Orden**: 6
**Depende de**: US-005, US-010, US-016, US-020, US-092; dependencia técnica: change de la tarea periódica con Redis
**Reglas**: RN-WA-01, RN-WA-03, RN-TD-08, RN-PR-07, RN-GL-05

### US-031 — Confirmación por el link de gestión
**Como** odontólogo **quiero** registrar quién confirmó **para** saber qué huecos podrían liberarse.
- [ ] CA-1: el paciente confirma desde el link de gestión del turno; la confirmación cambia el estado a `confirmado` y queda en el historial (RN-WA-02).
- [ ] CA-2 (**Fase 2**): confirmar o cancelar respondiendo por el chat (Cloud API) queda fuera de la v1.
- [ ] CA-3 (error): confirmar solo es posible desde `reservado` y mientras `ahora < inicio`; en cualquier otro estado la acción se rechaza sin modificar el turno, y en un estado terminal el link solo muestra el estado (RN-TD-08, decisión del autor 2026-10-05, D77). El rechazo es el error de dominio `RN-TD-11`, con el estado actual y las acciones permitidas en el mensaje (RN-TD-11, D89).
- [ ] CA-4 (confirmar desde el panel; decisión del autor 2026-10-05, D113): el odontólogo o la recepcionista pueden confirmar un turno `reservado` desde el panel (por ejemplo, cuando el paciente confirma por teléfono) con `POST /turnos/{id}/confirmar`; el turno pasa a `confirmado` y queda en el historial con el usuario como actor (RN-AG-11). La acción vive en la **agenda del día** (interfaz de US-011), sin pantalla nueva. A diferencia del link del paciente, **no exige `ahora < inicio`** (asimetría deliberada, RN-WA-02, D117).
- [ ] CA-5 (error): confirmar desde el panel un turno que no está en `reservado` se rechaza con el error de dominio `RN-AG-12` y el turno no cambia; el dueño recibe `403` (RN-AU-05).
**Orden**: 6
**Depende de**: US-011 (agenda del día, CA-4), US-015, US-020, US-030, US-092
**Reglas**: RN-WA-02, RN-TD-08, RN-TD-11, RN-AG-11, RN-AG-12, RN-AU-05

## Épica 5: Lista de espera (CU-06) — diferenciador

### US-040 — Ofrecer hueco liberado
**Como** odontólogo **quiero** que un hueco liberado se ofrezca automáticamente a quien espera **para** convertir cancelaciones en turnos.
- [ ] CA-1: se ofrece por orden de llegada (FIFO por `creada_en`, RN-LE-02) a la primera entrada compatible: **el tramo común entre el hueco y alguna franja preferida alcanza para la duración de la prestación** (o la lista de preferencias está vacía y el hueco alcanza para la duración); no se exige que el hueco entre entero en la franja (RN-LE-01, D78, corregida por D88).
- [ ] CA-1b (ejemplo, D88): hueco de 9:00 a 13:00, preferencia de 10:00 a 12:00 y prestación de 30 minutos → compatible (tramo común de 10:00 a 12:00, 120 minutos ≥ 30); el turno se ofrece dentro del tramo común, por ejemplo a las 10:00. Hueco de 9:00 a 10:15 con la misma preferencia y prestación → no compatible (tramo común de 15 minutos).
- [ ] CA-1c: la oferta (`OfertaHueco.inicio` / `fin`) se arma con el **primer inicio posible dentro del tramo común, respetando la granularidad de la agenda**; su `fin` es `inicio + duración` de la prestación (RN-LE-01, D88).
- [ ] CA-1d (hueco; decisión del autor 2026-10-05, D97): el hueco es el **tramo libre contiguo, dentro del horario del profesional y sin bloqueos, que queda al liberarse un turno** (el intervalo liberado más el tiempo libre adyacente). La oferta exige `inicio ≥ ahora + antelacion_minima_reserva_horas` (RN-TD-02) y nunca ofrece un tramo pasado (RN-LE-01).
- [ ] CA-1e (hueco más largo que la prestación, D97): la oferta ocupa solo la duración de la prestación; el **resto del hueco se ofrece, en la misma corrida, a la siguiente entrada compatible** por orden de llegada (RN-LE-02), y lo que no se ofrezca queda libre para la reserva normal. Una oferta enviada **no bloquea** el horario (RN-LE-04 revalida al aceptar).
- [ ] CA-2: la oferta vence (2 horas por defecto, configurable, RN-LE-03); si vence o se rechaza, el hueco pasa al siguiente y la entrada **vuelve a `activa` conservando su lugar** (su `creada_en` no cambia; la entrada no tiene estado `vencida`) (RN-LE-03, decisión del autor 2026-10-05, D53).
- [ ] CA-2b: una entrada `ofertada` puede retirarse (el paciente desde su link o el consultorio desde el panel): su oferta se da por rechazada y el hueco pasa al siguiente (RN-LE-06, decisión del autor 2026-10-05, D60).
- [ ] CA-3: al aceptar, se revalida el solapamiento (RN-LE-04). Si el turno resultante empieza a menos de `antelacion_cancelacion_horas`, la aceptación exige la aceptación explícita de RN-TD-10 (D87). Aceptar una oferta efectivamente vencida la persiste como `vencida` y se rechaza; si el horario estaba ocupado por un turno `pendiente_sena` con la seña vencida, la aceptación persiste ese vencimiento antes de crear el turno (RN-GL-05 (a) y (c), D92).
- [ ] CA-4: el panel señala la entrada en curso que lleva **más de 7 días sin recibir una oferta compatible** (desde su `creada_en` o desde su última oferta, lo más reciente), para que el consultorio la gestione a mano; es un indicador del panel, no un mensaje de WhatsApp (RN-LE-08, decisión del autor 2026-10-05, D78).
- [ ] CA-5: no se ofrece un hueco a un paciente con `acepta_contacto = false`; la tarea periódica lo verifica justo antes de preparar la oferta (RN-PR-07, D81).
**Orden**: 6
**Depende de**: US-005, US-013, US-021, US-030, US-092
**Reglas**: RN-LE-01 a RN-LE-04, RN-LE-08, RN-TD-10, RN-PR-07, RN-GL-05

## Épica 6: Seña con Mercado Pago (CU-04)

### US-050 — Pagar seña al reservar
**Como** paciente **quiero** pagar la seña al reservar **para** asegurar mi turno.
- [ ] CA-1: se genera una preferencia de Checkout Pro en la cuenta del odontólogo (credenciales de prueba).
- [ ] CA-2: el webhook acreditado pasa el turno a `reservado`; notificaciones duplicadas no acreditan dos veces.
- [ ] CA-3: si no se paga a tiempo (30 minutos por defecto, configurable, RN-SP-03), el turno vence, la seña pasa a `vencida` y se libera el horario (decisión del autor 2026-10-05, D62).
- [ ] CA-4 (borde): si el webhook acredita el pago cuando el turno **ya no está activo** (`vencido` o cancelado), el turno **no cambia** (el horario pudo ocuparse) y la seña se registra como `devuelta`; en el prototipo, solo registro (RN-SP-11, decisión del autor 2026-10-05, D38 y D59). Vale también si la seña está efectivamente vencida y la tarea periódica todavía no lo persistió: el webhook persiste en su transacción la seña `pendiente` → `vencida` → `devuelta` y el turno a `vencido`, sin disparar efectos (RN-GL-05 (b), D92).
- [ ] CA-5: si se cancela un turno `pendiente_sena`, su seña `pendiente` pasa a `vencida` (RN-SP-11, D59).
- [ ] CA-6: si están activas a la vez la aprobación manual y la seña, el turno nace `pendiente_aprobacion` y **al aprobarlo pasa a `pendiente_sena`**: la `Sena` se crea en ese momento y su plazo de pago (`vence_en`) empieza ahí; sin seña exigida, al aprobar pasa a `reservado` (RN-SP-02, RN-TD-05; decisión del autor 2026-10-05, D76).
- [ ] CA-7: el vencimiento de la seña se evalúa al consultar (`vence_en` contra `utc_now()`): un turno `pendiente_sena` con la seña vencida no ocupa el horario aunque no haya corrido ninguna tarea; la tarea periódica persiste `vencido` y `vencida` y dispara la lista de espera (RN-SP-03, RN-GL-05, D80). Si antes una escritura necesita ese horario (crear o reprogramar un turno, aceptar una oferta), persiste ella el vencimiento en su misma transacción, sin disparar efectos (RN-GL-05 (a), D92).
- [ ] CA-8 (aviso de seña, RN-TD-10, decisión del autor 2026-10-05, D87): si la reserva exige seña y además cae dentro de la ventana de cancelación (`inicio − ahora < antelacion_cancelacion_horas`), el aviso previo a confirmar agrega que **la seña no se devuelve** si el paciente cancela o no asiste (RN-SP-04); si cancela el odontólogo, la seña se devuelve igual (RN-SP-05).
- [ ] CA-9 (pago desde el link, decisión del autor 2026-10-05, D89): el paciente con el turno en `pendiente_sena` puede pagar la seña desde el link de gestión; **ruta propuesta** `POST /public/turnos/{token}/pagar-sena`, que devuelve la URL de Checkout Pro de la preferencia (el contrato se fija en el design del change).
- [ ] CA-10 (error): pedir el pago de la seña con el token de un turno que no está en `pendiente_sena`, o que ya empezó, se rechaza con el error de dominio `RN-TD-11` (estado actual y acciones permitidas en el mensaje; sin modificar el turno ni el historial).
**Orden**: 7
**Depende de**: US-005, US-015 (historial), US-020, US-022 (link de gestión, RN-TD-11); dependencia técnica: change de la tarea periódica con Redis
**Reglas**: RN-SP-01, RN-SP-02, RN-SP-03, RN-SP-04, RN-SP-05, RN-SP-08, RN-SP-11, RN-SP-12, RN-TD-05, RN-TD-10, RN-TD-11, RN-GL-05

### US-051 — Retención / devolución de seña (**sujeta a revisión legal**)
**Como** odontólogo **quiero** que la seña quede retenida o devuelta según quién cancela y cuándo **para** que el prototipo refleje las reglas de seña del consultorio.
Describen el comportamiento del **prototipo con credenciales de prueba de Mercado Pago**; no afirman validez legal (P-01, fuera del alcance académico).
- [ ] CA-1: si el paciente queda `ausente`, la seña acreditada pasa a `retenida` (RN-SP-04 (a), decisión del autor 2026-10-03).
- [ ] CA-2: si el consultorio carga desde el panel una cancelación como cancelación del paciente fuera de plazo (`ahora > inicio − antelacion_cancelacion_horas`), la seña pasa a `retenida` (RN-SP-04 (b), RN-TD-03).
- [ ] CA-3: si el paciente cancela dentro de plazo, o cancela el odontólogo, la seña se devuelve y pasa a `devuelta` (RN-SP-06, RN-SP-05).
- [ ] CA-4 (borde): no hay retención parcial: la seña se retiene entera o se devuelve entera (RN-SP-04).
- [ ] CA-5: en el prototipo la devolución solo se registra con el estado `devuelta`; no se ejecuta una devolución real por la API de Mercado Pago (`11_integraciones_whatsapp_y_mercadopago.md`).
- [ ] CA-6: **acción del panel «devolver o retener la seña manualmente»**, solo para el rol `odontologo`, con registro en el historial (`sena_devuelta` o `sena_retenida`, con quién, cuándo, valor anterior y valor nuevo). Es el complemento de la corrección de marcado de US-014 (RN-SP-10, decisión del autor 2026-10-05, D34). **Precondición (D101):** retener a mano exige que el turno esté `ausente`; devolver a mano, que esté `atendido`; en cualquier otro caso se rechaza con `RN-SP-12`.
- [ ] CA-7: si se corrigió `ausente` → `atendido` (US-014 CA-7), la seña queda `retenida` hasta que el odontólogo la devuelva manualmente: `retenida` → `devuelta` (US-014 CA-10).
- [ ] CA-8: si se corrigió `atendido` → `ausente`, la seña sigue `acreditada` hasta que el odontólogo decida retenerla manualmente: `acreditada` → `retenida` (RN-SP-04 (a) aplica a un ausente; US-014 CA-10).
- [ ] CA-9 (error): la recepcionista y el dueño no pueden devolver ni retener manualmente (`403`, RN-AU-05). Sigue rigiendo «sujeta a revisión legal»; la devolución en el prototipo solo se registra (CA-5).
- [ ] CA-10 (error): la seña cambia de estado solo según la tabla de transiciones válidas de `Sena` (`04_modelo_de_datos.md`); cualquier otro cambio (por ejemplo, `devuelta` → `acreditada`) se rechaza con el error de dominio `RN-SP-12` («transición de seña inválida»), sin modificar la seña ni el historial (decisión del autor 2026-10-05, D61).
**Orden**: 7
**Depende de**: US-013, US-014, US-022, US-050
**Reglas**: RN-SP-04, RN-SP-05, RN-SP-06, RN-SP-10, RN-SP-12

## Épica 7: Ficha clínica mínima, presupuestos y pagos (CU-03)

### US-060 — Ficha del paciente
**Como** odontólogo **quiero** abrir la ficha en la consulta y registrar anamnesis y evolución **para** no depender de la carpeta de papel.
- [ ] CA-1: la ficha contiene los datos del paciente, la anamnesis y la evolución en texto (RN-FC-01); una evolución puede vincularse a un turno (Flujo 7). La ficha se lee con `GET /pacientes/{id}/ficha` (**ruta propuesta**; se fija en el design del change), que devuelve la anamnesis vigente y las evoluciones (decisión del autor 2026-10-05, D114).
- [ ] CA-2 (error): solo el rol `odontologo` lee y escribe los datos clínicos; la recepcionista que los pide recibe `403`, también en la ruta de lectura de la ficha (RN-FC-02, RN-AU-05).
- [ ] CA-3 (borde): la anamnesis tiene los campos `alergias`, `medicacion`, `enfermedades` y `observaciones`, todos opcionales; se puede guardar con todos vacíos (RN-FC-01, decisión del autor 2026-10-03).
- [ ] CA-4: la anamnesis se versiona: cada cambio crea una versión nueva (`version` + 1) sin sobrescribir la anterior (RN-FC-03).
- [ ] CA-5: la evolución es solo inserción; una corrección es una entrada nueva que referencia a la anterior y no hay borrado físico (RN-FC-03, `Evolucion.corrige_a_id`).
- [ ] CA-6: el autor de un dato clínico es **quien inició sesión**: tanto `Evolucion` como `Anamnesis` guardan `registrada_por` (FK a `Usuario`, no nulo); la evolución ya no se asocia a un `Profesional` (decisión del autor 2026-10-05, D50).
**Orden**: 8
**Depende de**: US-010, US-091, US-092 (roles: la recepcionista no ve datos clínicos, RN-FC-02)
**Reglas**: RN-FC-01, RN-FC-02, RN-FC-03

### US-061 — Presupuesto simple
**Como** odontólogo **quiero** armar un presupuesto simple para un paciente **para** informarle el costo de los tratamientos.
- [ ] CA-1: el presupuesto tiene ítems con descripción, cantidad y precio unitario, y su total se calcula a partir de los ítems; sin códigos ni valores de obras sociales (RN-FC-04).
- [ ] CA-2: el presupuesto nace `borrador`; el odontólogo lo pasa a `entregado` y luego a `aceptado` o `rechazado` (RN-FC-05).
- [ ] CA-3 (error): `aceptado` y `rechazado` son finales; cualquier cambio posterior, o un salto no previsto (por ejemplo, de `borrador` a `aceptado`), se rechaza con el error de dominio `RN-FC-05`.
- [ ] CA-4 (error): solo el odontólogo cambia el estado (RN-FC-05).
- [ ] CA-5 (error): se rechaza un ítem con cantidad menor o igual a 0 o con precio unitario negativo (`CHECK` de `04_modelo_de_datos.md`).
- [ ] CA-6 (error): los ítems solo se pueden agregar, editar o quitar mientras el presupuesto está en `borrador`; en otro estado se rechaza con el error de dominio `RN-FC-04` (decisión del autor 2026-10-05, D36).
- [ ] CA-7 (error): para pasar de `borrador` a `entregado` hace falta al menos un ítem; sin ítems se rechaza (RN-FC-04, RN-FC-05).
**Orden**: 8
**Depende de**: US-001, US-060
**Reglas**: RN-FC-04, RN-FC-05

### US-062 — Registro de pago simple
**Como** odontólogo o recepcionista **quiero** registrar un pago (pagado sí o no, monto y medio) **para** llevar el control de cobros sin una caja completa.
- [ ] CA-1: el registro guarda pagado sí o no, monto y medio (`efectivo`, `transferencia`, `mercado_pago`, `tarjeta` u `otro`); no emite comprobante fiscal (RN-SP-07).
- [ ] CA-2: el pago se asocia al paciente y, opcionalmente, a un presupuesto o a un turno (decisión del autor 2026-10-03).
- [ ] CA-3: se admiten pagos parciales: un cobro en cuotas son varios registros (RN-SP-09).
- [ ] CA-4: un registro no se edita; se corrige con un registro nuevo (`es_anulacion = false`) que apunta al anterior (`corrige_a_id`): el anterior deja de contar en totales y pendientes y el nuevo cuenta (RN-SP-09, decisión del autor 2026-10-05, D31).
- [ ] CA-5 (error): se rechaza un monto menor o igual a 0 (`CHECK` de `04_modelo_de_datos.md`).
- [ ] CA-6: **anulación sin reemplazo**: se crea un registro con `es_anulacion = true` que apunta al original (`corrige_a_id`), copia su monto y su medio y lleva `pagado = true`; el original deja de contar y la anulación no cuenta en totales ni en pendientes, pero aparece en el historial de pagos del paciente (RN-SP-09).
- [ ] CA-7 (error): un registro de anulación sin `corrige_a_id` se rechaza (`CHECK`); tampoco se puede apuntar (`corrige_a_id`) a un registro de anulación: se rechaza con el error de dominio `RN-SP-09`.
- [ ] CA-8 (error): un registro se corrige o anula una sola vez; un segundo registro que apunte al mismo original se rechaza (`UNIQUE` sobre `corrige_a_id` y error de dominio `RN-SP-09`).
**Orden**: 8
**Depende de**: US-060 (US-061 y US-010 no son dependencia: el pago puede asociarse a un presupuesto o a un turno, opcionalmente)
**Reglas**: RN-SP-07, RN-SP-09

## Épica 8: Privacidad y consentimiento (CU-07)

### US-070 — Consentimiento informado de datos
**Como** paciente **quiero** saber qué datos de salud se guardan y aceptar su tratamiento **para** reservar con conocimiento de cómo se usan mis datos.
- [ ] CA-1 (error): para reservar, el paciente debe aceptar el texto de consentimiento; sin aceptarlo, la reserva no se confirma (RN-PR-02, Flujo 2).
- [ ] CA-2: al aceptar se registra la versión del texto, la fecha-hora de aceptación y el origen (`link_publico` o `panel`) (RN-PR-02, `04_modelo_de_datos.md`).
- [ ] CA-3: el texto es un borrador marcado «no validado legalmente», y esa leyenda es visible dentro del propio texto que ve el paciente; la versión vigente es `v1-borrador` y el texto está en la sección «Texto de consentimiento — versión `v1-borrador`» de `05_reglas_de_negocio.md` (RN-PR-02, P-03 cerrada como fuera del alcance académico; D57).
- [ ] CA-4 (borde): si cambia la versión del texto, se vuelve a pedir en la siguiente reserva del paciente, que se reconoce según RN-TD-09 (teléfono, nombre y apellido normalizados); si se crea un paciente duplicado por un error de tipeo, el consentimiento se pide de nuevo (RN-PR-02, decisión del autor 2026-10-03; D48).
- [ ] CA-5: el consentimiento también se exige para anotarse en la lista de espera **por el link público** (RN-LE-05); desde el panel no bloquea el alta (US-021 CA-8, D107). Se completa con US-021 (orden 6).
- [ ] CA-6: cuando el consultorio carga un turno, o anota a un paciente en la lista de espera, desde el panel, el consentimiento **no bloquea** la creación del turno ni de la entrada; se registra con origen `panel` cuando el paciente lo da en persona. Por eso el primer change (`POST /turnos`, sin consentimiento) no incumple RN-PR-02. En el link público sigue siendo obligatorio (CA-1) (decisión del autor 2026-10-05, D37; lista de espera, D107). El registro desde el panel es US-016 CA-7, que se completa con este change.
**Orden**: 5
**Depende de**: Ninguna
**Reglas**: RN-PR-02, RN-PR-03, RN-LE-05, RN-TD-09

### Regla permanente: datos ficticios (RN-PR-01)
Esto **no es una historia implementable**: es una **regla dura del proyecto**, aplicable **desde el primer change**. Se registra en las reglas del agente (`CLAUDE.md`/`AGENTS.md`) y **no genera un change propio** (decisión del autor 2026-10-03). Seeds, tests, ejemplos y demos usan solo datos inventados (RN-PR-01 en `05_reglas_de_negocio.md`).

## Épica 9: Control del dueño

### US-080 — Reportes de ocupación, ausentismo y cobros pendientes (**extensión fuera del MVP de la sección D del informe**)
**Como** dueño **quiero** ver ocupación, ausentismo y señas/pagos pendientes **para** controlar el consultorio.
**Alcance**: **extensión fuera del MVP de la sección D del informe** (el informe, D.3, no la lista entre los imprescindibles). Queda en la v1 como **último orden** (decisión del autor 2026-10-03). El roadmap debe marcarla como extensión.
- [ ] CA-1: la ocupación es los minutos con turno (estados activos, `atendido` y `ausente`) sobre los minutos de horario disponible (horario recurrente menos bloqueos) (RN-RP-01; modificada por el autor el 2026-10-05, D41). La ocupación mide tiempo bloqueado, no tiempo trabajado; el ausentismo se mide aparte (CA-2).
- [ ] CA-2: el ausentismo es los turnos `ausente` sobre los turnos `atendido` más `ausente` (RN-RP-02).
- [ ] CA-3: ambos reportes se calculan con filtro por rango de fechas y con un filtro opcional por profesional (RN-RP-03).
- [ ] CA-4: el reporte de cobros pendientes lista las señas en estado `pendiente` **efectivo** (no las que ya vencieron al consultar, RN-GL-05) y los registros de pago con `pagado` falso, **excluyendo los registros de anulación (`es_anulacion = true`) y los registros apuntados por algún `corrige_a_id`** (`04_modelo_de_datos.md`, RN-SP-09).
- [ ] CA-5: los reportes son de solo lectura, los ven los roles `dueno` y `odontologo` (`03_actores_y_roles.md`) y no incluyen datos clínicos (RN-FC-02, RN-PR-03).
- [ ] CA-6 (borde): si en el rango no hay turnos `atendido` ni `ausente`, el ausentismo muestra «sin datos», no 0 % (RN-RP-02, decisión del autor 2026-10-05, D79).
- [ ] CA-7 (borde): si el horario disponible del rango es cero porque no hay horario recurrente configurado, la ocupación muestra «sin horario configurado»; si hay horario configurado pero el disponible es cero (por ejemplo, todo bloqueado), muestra «sin datos» (RN-RP-01, D79).
- [ ] CA-8: el filtro por profesional es un parámetro opcional (RN-RP-03, D79).
- [ ] CA-9: el horario disponible se calcula día por día, con las franjas vigentes en cada fecha (`vigente_desde` / `vigente_hasta`) menos los bloqueos (RN-RP-01, D79).
**Orden**: 9
**Depende de**: US-002, US-003, US-010, US-014, US-050, US-062, US-092
**Reglas**: RN-RP-01, RN-RP-02, RN-RP-03, RN-FC-02, RN-PR-03

## Épica 10: Usuarios y acceso

Decisión del autor 2026-10-03 (fila «Usuarios y acceso» de la tabla del 2026-10-03 en `10_preguntas_abiertas.md`): el panel se protege con JWT en esta épica (orden 3); hasta entonces `POST /turnos` del primer change y los endpoints de orden 1 y 2 van sin autenticación. Roles (`odontologo`, `recepcionista`, `dueno`) y matriz de permisos en `03_actores_y_roles.md`. Los detalles de sesión y contraseñas (access token de 15 minutos, refresh de 7 días, JWT HS256, hash bcrypt, invalidación en bloque por `token_version`, contraseña de 10 caracteres como mínimo y 72 bytes como máximo) son **decisión del autor (2026-10-05, D74; SU-09)**; el design del change define solo su implementación. **US-090, US-091, US-092, US-093 y US-094 quedan confirmadas por el autor (2026-10-05, D42 y D62);** los criterios nuevos de US-091, US-092, US-093 y US-094 incorporan las decisiones D43 a D46 del mismo día.

### US-090 — Iniciar sesión
**Como** odontólogo o recepcionista **quiero** iniciar sesión con email y contraseña **para** acceder al panel.
- [ ] CA-1: con credenciales válidas, `POST /auth/login` devuelve un access token JWT y un refresh token.
- [ ] CA-2: con email inexistente o contraseña incorrecta, responde `401` con el mismo mensaje genérico en ambos casos (RN-AU-04).
- [ ] CA-3: un usuario inactivo no puede iniciar sesión.
- [ ] CA-4 (decisión del autor 2026-10-05, D74; SU-09): el access token dura 15 minutos y el refresh token 7 días; ambos son JWT firmados con HS256 y las contraseñas se guardan con hash bcrypt.
**Orden**: 3
**Depende de**: Ninguna
**Reglas**: RN-AU-01, RN-AU-03, RN-AU-04

### US-091 — Roles odontólogo, recepcionista y dueño
**Como** odontólogo **quiero** que cada usuario tenga uno o más roles **para** que cada uno vea solo lo que le corresponde.
- [ ] CA-1: un usuario puede tener varios roles y sus permisos son la unión de los roles (el odontólogo independiente tiene `odontologo` + `dueno`).
- [ ] CA-2: la recepcionista ve los datos administrativos del paciente pero no la ficha clínica (anamnesis, evolución) (RN-FC-02).
- [ ] CA-3: un rol insuficiente recibe `403` en el endpoint protegido.
- [ ] CA-4: en la v1, asignar el rol `odontologo` a otro usuario **no crea un `Profesional`**: el único profesional queda vinculado al usuario del seed; un segundo profesional es **Fase 2** (multi-profesional) (decisión del autor 2026-10-05, D46).
- [ ] CA-5: los roles **se leen de la base en cada petición autenticada** (no viajan en el token como fuente de verdad): quitar o asignar un rol tiene efecto inmediato (RN-AU-02, decisión del autor 2026-10-05, D102).
**Orden**: 3
**Depende de**: US-090
**Reglas**: RN-AU-02, RN-AU-05, RN-FC-02

### US-092 — Proteger los endpoints del panel con JWT
**Como** odontólogo **quiero** que los endpoints del panel exijan un token válido **para** que nadie sin sesión modifique la agenda.
- [ ] CA-1: un endpoint del panel sin token o con token vencido responde `401`.
- [ ] CA-2: `POST /turnos` (que en el primer change va sin autenticación) y los demás endpoints de panel creados antes de esta épica (gestión de prestaciones y de sillón, historial: US-001, US-004, US-015) pasan a exigir JWT con el rol que corresponda (por ejemplo, `odontologo` o `recepcionista` para `POST /turnos`).
- [ ] CA-3: las rutas públicas de `03_actores_y_roles.md` siguen sin autenticación.
- [ ] CA-4: una petición con un token de un usuario **inactivo**, o con un `token_version` que ya no coincide con el del usuario, responde `401` aunque el token no haya vencido (RN-AU-03, RN-AU-04; decisión del autor 2026-10-05, D43).
**Orden**: 3
**Depende de**: US-090, US-091
**Reglas**: RN-AU-01, RN-AU-03, RN-AU-04, RN-AU-05

### US-093 — Gestión de usuarios del consultorio
**Como** odontólogo **quiero** crear, desactivar y asignar roles a los usuarios del consultorio **para** dar acceso a la recepcionista.
- [ ] CA-1: el odontólogo crea usuarios y les asigna roles; la recepcionista no puede.
- [ ] CA-2: el email es único, sin distinguir mayúsculas ni espacios en los extremos (un usuario inactivo sigue ocupando su email); si se repite, se rechaza con `409` y el error de dominio `RN-AU-08` (decisión del autor 2026-10-22, D243).
- [ ] CA-3: desactivar un usuario **corta su acceso de inmediato** (sus tokens dejan de valer, no solo su próximo inicio de sesión; `token_version` se incrementa); no se borra (RN-AU-03, RN-AU-04; decisión del autor 2026-10-05, D43).
- [ ] CA-4 (error): no se puede desactivar ni quitar el rol `odontologo` al **último odontólogo activo**; se rechaza con el error de dominio `RN-AU-06` (D44).
- [ ] CA-5 (error): un usuario **no puede desactivarse a sí mismo** (`RN-AU-06`, D44).
- [ ] CA-6: el odontólogo **define la contraseña inicial** al crear el usuario y **puede restablecerla**; el restablecimiento incrementa `token_version` (RN-AU-07, D45).
- [ ] CA-7: **cada usuario puede cambiar su propia contraseña**, pidiendo la actual; el cambio incrementa `token_version`, por lo que las demás sesiones del usuario dejan de valer (RN-AU-07, D45). Ruta propuesta: `POST /auth/cambiar-contrasena`.
- [ ] CA-8: en la v1, asignar el rol `odontologo` a otro usuario **no crea un `Profesional`**: el único profesional queda vinculado al usuario del seed; un segundo profesional es **Fase 2** (D46).
- [ ] CA-9 (error): la contraseña (inicial, restablecida o cambiada por el propio usuario) tiene **mínimo 10 caracteres y máximo 72 bytes** (el tope de bcrypt); fuera de ese rango se rechaza y no se modifica el usuario (RN-AU-07, decisión del autor 2026-10-05, D74).
**Orden**: 3
**Depende de**: US-090, US-091
**Reglas**: RN-AU-02, RN-AU-03, RN-AU-04, RN-AU-05, RN-AU-06, RN-AU-07, RN-AU-08

> Nota de implementación (C-09, archivado 2026-10-22): cubre CA-1 a CA-5, CA-8 y la parte inicial de CA-9 (contraseña inicial de 10 a 72 bytes, D242); lo restante de CA-6, CA-7 y CA-9 queda para C-10.

### US-094 — Renovar la sesión (confirmada por el autor 2026-10-05, D42 y D43)
**Como** usuario del panel **quiero** renovar mi sesión sin volver a ingresar la contraseña **para** no ser interrumpido durante la jornada.
- [ ] CA-1: `POST /auth/refresh` con un refresh token válido devuelve un nuevo access token.
- [ ] CA-2: un refresh token vencido o inválido responde `401`.
- [ ] CA-3: un refresh token de un usuario **inactivo**, o con un `token_version` que ya no coincide con el del usuario, responde `401` aunque no haya vencido (RN-AU-03, RN-AU-04; decisión del autor 2026-10-05, D43).
**Orden**: 3
**Depende de**: US-090
**Reglas**: RN-AU-03, RN-AU-04

## Épicas posteriores (no implementar en v1)

| Épica | Versión |
|---|---|
| Odontograma completo | v1.1 |
| Obras sociales (códigos y valores manuales) | v1.1 |
| Imágenes y radiografías | v2 |
| ARCA / facturación electrónica | v2 |
| Caja completa con arqueo | v2 |
| Agenda multi-profesional y multi-sillón en UI (CU-08) | Fase 2 |
| Sobreturnos (prohibidos en la v1, P-11) | Fase 2 |
| Split de pagos 1:N en Mercado Pago | Fase 2 |
| Excepción de horario puntual (descartada para la v1, RN-AG-04; D86) | Fase 2 |
| Fusión manual de pacientes duplicados (RN-TD-09) | Fase 2 |
| Corrección de un marcado pasadas las 24 horas (acción administrativa, RN-AG-13) | Fase 2 |
| Congelar la ventana de cancelación por turno (RN-TD-03) | Fase 2 |
| WhatsApp Cloud API oficial (adaptador sobre el puerto de mensajería; incluye la respuesta por chat) | Fase 2 |
| WhatsApp API oficial en producción (verificación de empresa, plantillas, costo) | Posterior |
| Google Calendar, API pública | Posterior |
| Devolución real por la API de Mercado Pago (el prototipo solo registra `devuelta`; D71) | Posterior |
| Exportación de los datos del paciente a pedido (RN-PR-05; decisión del autor 2026-10-05, D67) | Posterior |
