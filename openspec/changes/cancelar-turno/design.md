# Design: cancelar-turno

Fecha del design: **2026-10-29**. Change **C-17** (US-013; escenarios mínimos US-013 CA-1, CA-2 y CAN-1 de `CHANGES.md`). Gobernanza **MEDIO** (`CHANGES.md` C-17): se implementa con checkpoints y las decisiones no obvias se le presentan al autor antes del Apply. Motivación y alcance en `proposal.md`; el comportamiento, en `specs/cancelacion-de-turnos/spec.md` (9 escenarios), `specs/pantalla-de-cancelacion/spec.md` (5) y el delta de `specs/pantalla-de-historial/spec.md` (dos requisitos MODIFIED con cuatro escenarios: `HIS-2b` y `HIS-2f` cambian; `HIS-2a` y `HIS-2c` son copia literal del spec vigente, porque un MODIFIED repite el requisito completo).

Las decisiones se numeran **X1 a X16** («X» por la cruz de «cancelar», una letra libre, para no confundirlas con las D1..D353 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores: D de C-01, I de C-02, H de C-03 y C-12, P de C-04, S de C-05, J de C-06, R de C-07, F de C-08, U de C-09, T de C-11, B de C-13, L de C-49, K de C-10, Y de C-50, A de C-14, G de C-15, M de C-16). Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design; si tiene pregunta abierta, la cita) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»). **Las preguntas Q1 a Q11 están cerradas** (sección final): el 2026-10-29 el autor aceptó las once recomendaciones («Sí, todo») y quedaron como **D343 a D353** en `knowledge-base/10_preguntas_abiertas.md`, junto con los hallazgos H1 a H9 de `revisor-de-escenarios` (`docs/skills-mcp/evidencias/sesion-nueva/revision-de-escenarios-cancelar-turno.md`), que el `/opsx:update` aplicó a los specs, a las tareas y a la KB (`02`, `03`, `05`, `06`, `08` y `10`). Las decisiones que una D respalda dicen **Decisión del autor**; el detalle que ninguna D fija sigue siendo **Propuesta**, con la autonomía de la gobernanza MEDIO.

## Context

**Lo que ya existe** (leído del código y de los specs, no supuesto):

- **Estados** (`domain/turnos/estados.py`): `EstadoTurno` con los nueve valores de `04`, incluido `CANCELADO_PROFESIONAL`, y `ESTADOS_ACTIVOS`. No hay ninguna función de transición: hasta hoy ningún change cambia el estado de un turno.
- **Reprogramar** (C-16, `application/reprogramar_turno.py`): dentro de un `with uow:` lee el consultorio del usuario (D270), lee el turno con bloqueo de fila (`uow.agenda.turno_para_reprogramar`, `FOR NO KEY UPDATE`, que SQLite omite; V2 de C-16), `TurnoNoEncontrado` si no existe o es de otro consultorio, `exigir_reprogramable` (`RN-AG-18`), guarda y registra `evento_reprogramado`. El patrón de cancelar es el mismo, más corto.
- **Errores** (`domain/errors.py`, `api/errores.py`): `TurnoNoReprogramable` (`RN-AG-18`, `409`) es el precedente de «estado del recurso → `409`». **No existe** un error para `RN-AG-12`, y `08` no le fijaba estado HTTP (hueco de la KB que cerró D345: `409`).
- **Historial** (C-03, C-16): `TipoEvento` con `creado` y `reprogramado`; `evento_turno.tipo` sin `CHECK`, así que `cancelado` no necesita migración.
- **Esquema**: `turno.estado` es `String` sin `CHECK`; la restricción de exclusión de la migración `0002` filtra `estado IN ('pendiente_aprobacion', 'pendiente_sena', 'reservado', 'confirmado')`, así que un turno cancelado ya libera el hueco también en PostgreSQL. **Sin migración.**
- **Permisos** (`domain/acceso/roles.py`): 17 permisos, `TURNOS_REPROGRAMAR` con `_ODONTOLOGO_Y_RECEPCION`; `tests/unit/test_roles.py` cuenta `17 * 3`.
- **Frontend** (C-14 a C-16): `PaginaAgenda` con `Panel` = `ninguno` | `nuevo-turno` | `historial` | `reprogramar`; `TablaDeTurnos` con «Reprogramar» (solo activos, `ESTADOS_ACTIVOS_DEL_TURNO`) e «Historial»; `PanelReprogramar` (su prop para cerrar se llama `onCancelar`); `servidorFalso.ts` con `responderAlReprogramar`, `retener`, `caerse`, `fallarRuta`, `vencerAccess`, `invalidarRefresh`. **El frontend lista `cancelado_consultorio`** en `ESTADOS_DEL_TURNO` (`apiAgenda.ts`), `ETIQUETAS_DE_ESTADO` y `TONOS_DE_ESTADO` (`mensajes.ts`) y el test `AGE-4c`, donde la API dice `cancelado_profesional`: hoy `apiAgenda.ts` rechazaría una agenda con un turno cancelado por el consultorio como «sin conexión». Lo corrige este change (D342).
- **Historial en pantalla** (`features/historial/mensajes.ts`): `tituloDelEvento` con un mapa `creado`/`reprogramado` y «Cambio registrado ({tipo})» para el resto; `detalleDelCreado` usa `ESTADOS_DEL_TURNO` y `ETIQUETAS_DE_ESTADO`.

## Goals / Non-Goals

**Goals:**

- Cancelar un turno activo desde el panel indicando quién lo pidió, liberar su horario y dejarlo en el historial, con el mismo patrón y el mismo orden de rechazos que la reprogramación.
- Que dos escrituras simultáneas sobre el mismo turno nunca dejen dos eventos de cancelación ni una cancelación sobre un turno que ya no estaba activo.
- Que la agenda lo haga sin pantalla nueva, con un panel como los de C-14 a C-16, y que el historial lo muestre con su etiqueta.
- Dejar el nombre de estado del frontend igual al de la API (D342).

**Non-Goals:**

- Un servicio genérico de transiciones de estado (la tabla completa de `04`): C-18, C-19, C-27, C-33 y C-37 agregan las suyas. Este change solo codifica la fila «cualquier estado activo → cancelado» (X3); se generaliza cuando el segundo change lo necesite (D345).
- Disparar la lista de espera (C-36), tocar la seña (C-41), distinguir «fuera de plazo» (RN-TD-03, C-22 y C-41), avisar al paciente (C-31) y un motivo escrito (proposal, «Fuera de alcance»).
- Persistir vencimientos (RN-GL-05 (a)): cancelar no necesita ningún horario, así que no es una de esas escrituras.
- Control de versión optimista (como M7 de C-16).
- Cambiar la etiqueta «Cancelado por el consultorio» (D351).
- El estado efectivo de `pendiente_sena` con la seña vencida: llega con los changes de la seña (C-38 a C-40); hasta entonces se cancela por el estado **almacenado** (D317, D345).

## Decisions

### X1. Capabilities — Decisión del autor (D343; Q1)

Dos capabilities nuevas, `cancelacion-de-turnos` (API) y `pantalla-de-cancelacion` (interfaz), más un delta MODIFIED en `pantalla-de-historial` con dos requisitos: la etiqueta del evento `cancelado` (`HIS-2b`) y «un solo panel lateral a la vez» con los cuatro paneles (`HIS-2f`), así después del archive el spec principal del historial no contradice a `CAN-4c`. El evento `cancelado` se especifica donde nace, como `reprogramado` (D332). **No** hay delta de `pantalla-de-agenda` (la etiqueta de `AGE-4c` no cambia, Q9) ni de `pantalla-de-reprogramacion` (`REP-6c` sigue cierto; `CAN-4c` prueba la fila `cancelado_profesional`). **Alternativas descartadas**: una sola capability con API y pantalla (dos suites distintas); agregar los requisitos a `reprogramacion-de-turnos` (cancelar no es reprogramar); dejar el historial con «Cambio registrado (cancelado)». **Excepción** a «una sola capability» (regla dura 12), con el corte API / navegador de D241 a D332.

### X2. Contrato de `POST /turnos/{id}/cancelar` — Decisión del autor (D344; Q2)

- Cuerpo `CancelarTurnoEntrada` (Pydantic, `extra="forbid"`): `estado: Literal["cancelado_paciente", "cancelado_profesional"]`, **obligatorio**. Cualquier otro valor (`cancelado_consultorio`, `atendido`), el `null`, la ausencia o un campo de más (`motivo`) es formato: `422` sin código, antes de mirar el turno.
- El campo se llama `estado` porque US-013 CA-1 y `CHANGES.md` hablan del estado destino («pasa a `cancelado_profesional` o `cancelado_paciente`») y porque `POST /turnos/{id}/estado` de C-18 va a recibir un estado destino: el cliente aprende un solo idioma.
- Respuesta `200` con `TurnoSalida` (la de `POST /turnos` y `PATCH /turnos/{id}`).
- **Sin `motivo`**: el evento lo lleva vacío, como `reprogramado` (D338); agregarlo es un cambio compatible para más adelante.
- **Alternativas descartadas**: `{"pedido_por": "paciente" | "consultorio"}` (más legible, pero introduce un vocabulario nuevo que la API tendría que traducir a estados y que C-18 no comparte); dos rutas (`/cancelar-por-paciente`); `DELETE /turnos/{id}` (el turno no se borra: su historial lo impide, D164); un `motivo` opcional (otra validación y otro texto en la pantalla, sin pedido de la KB).

### X3. Estados, código y momento — Decisión del autor (D345; Q3; aplica RN-AG-12, D19, D65)

- Solo los turnos **activos** se cancelan. Uno terminal se rechaza con **`RN-AG-12`** («transición de estado inválida») y **`409`** (es el estado actual del recurso, como `RN-AG-18`, `RN-AU-06` y `RN-AU-10`), `type` `/errores/transicion-invalida`. Aquí sí es una transición (cambia el estado), así que corresponde el código genérico que `05` reserva para eso; no hace falta un código nuevo como `RN-AG-18`.
- **Pedir la misma cancelación otra vez también es `409`** (no `200` idempotente): `04` dice que los estados terminales no tienen salida, y CAN-1 de `CHANGES.md` pide el rechazo sin excepciones; además, un `200` escondería que otra persona ya lo canceló (y quién), que en la pantalla es `CAN-5a`.
- **En cualquier momento** (RN-TD-03, D65): no se mira `ahora` contra `inicio`; un turno pasado se cancela. Tampoco se distingue «dentro» o «fuera» de plazo: `antelacion_cancelacion_horas` llega con C-22 y su único efecto es sobre la seña (RN-SP-04), que llega con C-41.
- `pendiente_aprobacion` se cancela como cualquier activo; el **rechazo** de la aprobación manual (`POST /turnos/{id}/rechazar`, RN-TD-05) es otra acción de C-27, aunque también termine en `cancelado_profesional`.
- **Dominio puro**: `domain/turnos/cancelacion.py` con `ESTADOS_DE_CANCELACION = {CANCELADO_PACIENTE, CANCELADO_PROFESIONAL}` y `exigir_cancelable(estado)`, que levanta `TransicionInvalida` (nuevo en `domain/errors.py`, código `RN-AG-12`) si el estado no es activo. No se arma una tabla general de transiciones (Non-Goals).
- **Alternativas descartadas**: un código nuevo «turno no cancelable» (la KB ya tiene `RN-AG-12` para exactamente esto); `422` (no es un problema de la petición sino del estado del turno); `200` idempotente para la misma cancelación.
- **Estado almacenado**: se mira el estado guardado del turno (D317); el efectivo de un `pendiente_sena` con la seña vencida llega con la seña (Non-Goals).
- **Hueco de la KB, cerrado**: `08` no mapeaba `RN-AG-12` a un estado HTTP. El `/opsx:update` del 2026-10-29 sumó la fila a `08`, el `409` a RN-AG-12 de `05` y la referencia cruzada en RN-AG-18 (D345).

### X4. Clases de rechazo y orden de evaluación — Decisión del autor (D346; Q4; aplica RN-GL-02, D135, D208, D166)

1. **Acceso**: `401` sin sesión válida; `403` `RN-AU-05` sin `turnos.cancelar` (D208).
2. **Formato** (Pydantic): `422` sin código (id no entero, sin cuerpo, cuerpo sin `estado`, `estado` fuera de los dos valores, `null`, campo de más, tipo erróneo). No hay otra validación de entrada con código: el cuerpo no trae fechas ni referencias.
3. **Turno de la URL**: `404` `RN-GL-04` si no existe o es de otro consultorio (D166, D321).
4. **Regla de negocio**: `RN-AG-12` (`409`).

A diferencia del `PATCH` (donde el `404` va antes que `RN-AG-01`, porque la duración se valida en el dominio), aquí todo el cuerpo es formato y lo rechaza FastAPI antes de llamar al caso de uso: el turno 999 con un `estado` inválido da `422` (`CAN-3b`). El orden quedó escrito en `05` RN-GL-02 (D346) como la línea «Orden de evaluación de `POST /turnos/{id}/cancelar`», con el mismo límite del control de acceso: un cuerpo con JSON roto recibe `422` sin código antes que el `401` (D208). **Alternativa descartada**: mirar el turno antes de validar el cuerpo (obligaría a aceptar el cuerpo como `dict` y validarlo a mano, sin ganar nada).

### X5. Caso de uso y repositorio — Propuesta

`application/cancelar_turno.py`: `CancelarTurnoComando(turno_id, estado)` y `cancelar_turno(comando, usuario_id, uow, reloj, *, actor)`. Dentro de un `with uow:`: consultorio del usuario (D270); el turno **con bloqueo de fila**; `TurnoNoEncontrado` si no existe o es de otro consultorio; `exigir_cancelable(turno.estado)`; `uow.agenda.cambiar_estado(turno_id, estado)` (un `UPDATE` con `flush` que devuelve el `Turno`); `uow.historial.registrar(evento_cancelado(turno, guardado, actor, reloj()))`. Sin reintentos: un `UPDATE` de estado no puede violar la restricción de exclusión (solo libera).

El método de bloqueo de C-16 se llama `turno_para_reprogramar`; como ahora lo usan dos casos de uso, se renombra a **`turno_para_cambiar`** en el puerto, el repositorio y `reprogramar_turno` (REFACTOR que solo mueve nombres, con toda la suite en verde antes y después; tarea 3.4). **Alternativa descartada**: un segundo método igual (`turno_para_cancelar`), que duplica la consulta con bloqueo.

### X6. Concurrencia — Decisión del autor (D348; Q6; aplica D337)

- Una sola fila bloqueada, la del turno (`FOR NO KEY UPDATE`): dos cancelaciones del mismo turno se serializan y la segunda lee el estado ya cancelado → `RN-AG-12` (un solo evento). Una cancelación y una reprogramación del mismo turno también se serializan: la que llega segunda ve el turno como lo dejó la primera (`RN-AG-18` si la cancelación ganó). Cancelar no bloquea profesional ni sillón: no ocupa horario, solo lo libera, y una creación simultánea en ese hueco ve el turno todavía activo (y responde `409`) o ya cancelado (y responde `201`), ambas cosas correctas.
- **Prueba** solo en el perfil `postgres` (marcador `postgres`, con Docker), nunca en la suite por defecto (DD-03, regla dura 6): `tests/postgres/test_cancelaciones_simultaneas.py`, con el patrón de `carrera.py`, las dos corridas de `CAN-1d`.
- **Alternativa descartada**: `UPDATE … WHERE estado IN (activos)` sin bloqueo previo (también atómico, pero obliga a leer después para distinguir `404` de `409` y deja el evento sin el estado de antes leído bajo bloqueo).

### X7. El evento `cancelado` — Decisión del autor (D349; Q7; aplica RN-AG-11, D159, D209)

`TipoEvento.CANCELADO = "cancelado"` (el valor ya está en la lista de `04`) y `evento_cancelado(antes: Turno, despues: Turno, actor, ocurrido_en)` puro en `domain/turnos/eventos.py`: `antes` `{"estado": <anterior>}` y `despues` `{"estado": <nuevo>}`, que es lo único que cambia; `motivo` `None`; `ocurrido_en` del reloj inyectado; el actor es el usuario del token (`Actor(USUARIO, str(id))`). Mismo `with uow:` que el `UPDATE`: un rechazo no registra nada (`CAN-2b`) y, si el registro del evento falla, el estado tampoco queda (`CAN-2c`). La atomicidad se verifica **a nivel de caso de uso** con un disparador de SQLite que aborta el `INSERT` en `evento_turno`, sin dobles del repositorio (regla dura 6), como `test_rep2b_si_el_evento_falla_el_turno_no_se_mueve` de C-16. **Alternativa descartada**: la foto completa o el horario en `antes`/`despues` (no cambian; el horario del turno ya está en el turno y en su `creado`).

### X8. Permiso — Decisión del autor (D347; Q5)

`Permiso.TURNOS_CANCELAR = "turnos.cancelar"` con `_ODONTOLOGO_Y_RECEPCION` (matriz de `03`, fila Turnos: «CRUD» para el odontólogo y «CRU + cancelar» para la recepcionista, «R» para el dueño). El dueño y un usuario sin roles reciben `403` `RN-AU-05`. El contador de `test_roles.py` pasa a `18 * 3`; el guard de rutas protegidas encuentra la ruta nueva. **Alternativa descartada**: reusar `turnos.reprogramar` o `turnos.crear` (D336 eligió un permiso por acción).

### X9. Clases de rechazo de la pantalla — Decisión del autor (D350; Q8; aplica D323)

La pantalla no evalúa reglas: decide el texto por el tipo de error y el código (tabla del spec), nunca por el `detail`. Lo único que frena sin pedir nada es «Cancelar turno» sin opción elegida («Elegí quién pidió la cancelación.»): no hay nada que mandar. Cada rechazo suma «El turno no cambió.» (como D339). Un `422` no puede salir de esta pantalla (los dos valores son fijos), así que se muestra como el aviso de conexión, igual que un `5xx` y una respuesta de otra forma; cada una de esas causas tiene su corrida en `CAN-5b`.

### X10. Estructura del frontend — Decisión del autor en los textos (D350 a D352) + Propuesta (estructura; aplica A9, G8, M11 y `vercel-react-best-practices`)

- `apiAgenda.ts`: **`cancelado_consultorio` → `cancelado_profesional`** en `ESTADOS_DEL_TURNO` (D342); `cancelarTurno(id, estado)` con `POST /api/turnos/{id}/cancelar`, validando el `200` sin `any` (la forma de `TurnoCreado`); el tipo `EstadoDeCancelacion = 'cancelado_paciente' | 'cancelado_profesional'`.
- `mensajes.ts` de la agenda: la clave `cancelado_profesional` con la etiqueta **«Cancelado por el consultorio»** y el tono rojo (D351); `mensajeDeCancelacion(error)` con `RN-AG-12`, el `404` y el `403` propios y el aviso de conexión; las constantes «Turno cancelado.», «Elegí quién pidió la cancelación.», «¿Quién pidió la cancelación?», «El paciente», «El consultorio» y «El horario queda libre para otro turno.»; reusa `MENSAJE_EL_TURNO_NO_CAMBIO` de C-16.
- `PanelCancelar.tsx` (componente de nivel superior): un `fieldset` con `legend` «¿Quién pidió la cancelación?» y dos radios nativos sin valor inicial (estado local `EstadoDeCancelacion | null`), el aviso, «Volver» y «Cancelar turno» (destructivo). Sin `vi.mock`: se prueba sobre `<App/>` con el servidor falso.
- `TablaDeTurnos.tsx`: `onCancelar(turno)`; el botón «Cancelar» entre «Reprogramar» e «Historial», con el mismo ternario de `ESTADOS_ACTIVOS_DEL_TURNO` que «Reprogramar».
- `PaginaAgenda.tsx`: `Panel` suma `{ tipo: 'cancelar'; turno }`; un solo panel a la vez; `ir()` cierra también este panel; `cancelar()` con la guarda `enCurso` y la recarga del **mismo día** a la vista (el turno no se mueve); si la recarga falla, «Turno cancelado.» y el aviso de conexión con «Reintentar» (como `REP-6d`); el foco vuelve al botón «Cancelar» de la fila al cerrar. Para no confundir nombres, la función de la página se llama `cancelarElTurno` y la prop de `PanelCancelar` que cierra se llama `onVolver` (la `onCancelar` de `PanelReprogramar` no cambia).
- `features/historial/mensajes.ts`: `tituloDelEvento('cancelado')` → «Turno cancelado» y `detalleDelCancelado(antes, despues)` → «Estado: {etiqueta de antes} → {etiqueta de después}» con `ETIQUETAS_DE_ESTADO`, o `null` si alguno no trae un estado conocido (D352).

### X11. Interacción y anchos angostos — Decisión del autor (D350; Q8) + Propuesta (medidas; sale de las pantallas de Stitch)

En escritorio el panel va al costado de la agenda (unos 420 px), como los otros tres. Debajo de 720 px va a todo el ancho debajo de la barra, con «Cancelar turno» arriba y «Volver» debajo, a todo el ancho; en las tarjetas de la agenda angosta los tres botones van al pie de cada tarjeta (con salto de línea si no entran, sin desplazamiento horizontal a 390 px). Al abrir, el foco va a la primera opción; al cerrar con «Volver» o «Cerrar», vuelve al botón «Cancelar» de la fila. Las opciones son radios nativos dentro de filas con borde, de 44 px de alto como mínimo (área táctil). **El botón de cierre del pie se llama «Volver» y no «Cancelar»**, para que «Cancelar» no signifique dos cosas opuestas en el mismo panel.

### X12. Servidor falso y tests — Decisión del autor (D222, D227; reglas duras 6 y 8) + Propuesta (detalle)

`servidorFalso.ts` suma `POST /api/turnos/{id}/cancelar` con tres comportamientos mínimos: `404` `RN-GL-04` si el turno no está; `409` `RN-AG-12` si el turno no está en un estado activo; y, si no, `200` con el turno en el estado pedido (y lo guarda, así la agenda recargada lo muestra). Los demás rechazos salen de `responderAlCancelar(estado, codigos)`, de una sola vez, como `responderAlReprogramar`. Respeta `retener`, `caerse`, `vencerAccess`, `invalidarRefresh`, `quitarPermiso` y `fallarRuta`; cuenta las peticiones y guarda el cuerpo del último `POST`. Para `CAN-5a`, una opción `cambiarEstado(id, estado)` cambia un turno del falso sin pasar por la API (la «otra sesión»). Backend: tokens reales en los tests de API (D211), reloj fijo inyectado, SQLite en memoria; los turnos que la API no puede crear (en estados distintos de `reservado`, pasados, que empiezan en minutos o de otro consultorio: `CAN-1b`, `CAN-1c`, `CAN-2b`, `CAN-3b`) se cargan con la fábrica de tests, que ya escribe el estado directo en la base.

### X13. Versiones y dependencias — Propuesta

No se agrega ni cambia ningún paquete: ni `backend/pyproject.toml` ni `frontend/package.json` ni `package-lock.json`. La política de pins (D133) no aplica porque no se elige ninguna versión.

### X14. Demo y README — Propuesta

Sin datos nuevos de seed. El README suma `POST /turnos/{id}/cancelar` en «Probar desde Swagger» (con la recepcionista: crear un turno el lunes 2 de noviembre de 2026, cancelarlo como del paciente, volver a cancelarlo y ver `409` `RN-AG-12`, crear otro turno en el mismo hueco, el dueño con `403`, un `estado` inválido con `422`, y el historial con el `cancelado`), «Cancelar un turno» en «Panel (interfaz)», las tablas escenario → test y los límites conocidos (el dueño ve la acción, D312; la lista de espera llega con C-36; la seña con C-41; no se distingue la cancelación fuera de plazo hasta C-22 y C-41). Perfil `postgres`: la prueba nueva en la lista del README. **Guía acumulada de la fase 4**: C-17 es el cuarto change archivado de la fase (C-14, C-15, C-16 y C-17), así que al archivarlo va la guía acumulada de mitad de fase, `docs/guias/prueba-manual-c14-c17.md` (memoria «Prueba en navegador antes de archivar»: en la fase 4, de C-14 a C-21, la primera va después de archivar el cuarto change), con los recorridos de C-14 a C-17 (tarea 12.2).

### X15. Prueba en el navegador — Decisión del autor (D234, `rules.tasks`) + Propuesta (detalle)

Con la demo (`crear_app_demo` y `npm run dev`): la recepcionista crea dos turnos el lunes 2 de noviembre de 2026, cancela uno como del paciente (`CAN-4a`) y crea otro en el mismo hueco; cancela el otro como del consultorio y ve «Cancelado por el consultorio» (`CAN-4b`); intenta cancelar sin elegir (`CAN-5b`); abre dos pestañas y cancela el mismo turno en las dos (`CAN-5a`); abre el historial y ve «Turno cancelado» con «Estado: Reservado → Cancelado por el paciente» (`HIS-2b`); el dueño recibe `RN-AU-05` (`CAN-5b`); en `/docs`, el mismo `POST`. Comparar con las dos capturas de Stitch a 1280 y 390 px, guardar las capturas de la implementación junto a las de Stitch y anotar las diferencias en la sección 4 de `stitch-cancelar.md`. Consola sin errores ni datos sensibles; sin desplazamiento horizontal a 390 px (ahora con tres botones por fila). Después un recorrido breve en Compose (`http://127.0.0.1:5173`) para ver la CSP.

### X16. Skills aplicadas

- `fastapi-templates`: router → caso de uso → repositorio; `TurnoSalida` en la respuesta, nunca el modelo ORM; `Depends(requiere(...))`; `def` síncrono; `Literal` en el esquema para el formato.
- `python-design-patterns`: reglas puras en `domain/` (`exigir_cancelable`, `evento_cancelado`); un solo método de bloqueo compartido con la reprogramación (X5); nada de una abstracción general de transiciones hasta que haga falta.
- `python-error-handling`: `TransicionInvalida` con su código; acceso antes que validación; formato antes que existencia (X4).
- `python-testing-patterns`: AAA, `parametrize` para los estados y los valores, SQLite real, reloj inyectado, marcador `postgres` para la concurrencia.
- `auth-implementation-patterns`: un permiso por acción, chequeado en la dependencia de la ruta antes que nada (`403` sin revelar si el turno existe).
- `supabase-postgres-best-practices` (solo verificar): una sola fila bloqueada, transacción corta, la exclusión parcial de `0002` ya libera el hueco.
- `vercel-react-best-practices`: abrir el panel no pide nada, estado derivado en el render, componentes de nivel superior, ternarios en vez de `&&`.
- `revisor-de-escenarios`: se corre después de este propose y antes del Apply.

## Referencia visual (Stitch)

Pantallas generadas en este propose con el MCP `stitch`, proyecto `projects/14200813501064679723`, design system «Clinical Ops» (`assets/b683d44391ab410db2dd48aa71ed0b47`), modelo `GEMINI_3_8_FLASH`, cada una al primer intento. Pedidos, ids de archivos y revisión de datos en [`docs/skills-mcp/evidencias/sesion-nueva/stitch-cancelar.md`](../../../docs/skills-mcp/evidencias/sesion-nueva/stitch-cancelar.md). Los textos que se pidieron son los de las recomendaciones de Q8 a Q10, que el autor aceptó (D350 a D352).

| Pantalla | Id | Evidencia |
|---|---|---|
| Cancelar turno con error (`RN-AG-12`), escritorio | `projects/14200813501064679723/screens/e382a7e3a92f4cb18df0f6e7e9d677ca` | `stitch-cancelar-pantalla/cancelar-escritorio.png` y `.html` |
| Cancelar turno sin opción elegida y el resultado, angosta | `projects/14200813501064679723/screens/fcd2a428cdc44c5689b398cc8bf1936f` | `stitch-cancelar-pantalla/cancelar-angosta.png` y `.html` |

**Se toma**: el botón con borde «Cancelar» con ícono de círculo con X y texto rojo (estilo destructivo fantasma) entre «Reprogramar» e «Historial», y su ausencia en la fila cancelada; la fila del turno abierto resaltada; el panel lateral sin oscurecer la agenda, con el título con ícono rojo, la X y el resumen con el chip del estado actual; el aviso de error con ícono, el texto con el código y «El turno no cambió.» en una segunda línea; el rótulo «¿Quién pidió la cancelación?» y las dos opciones como filas con borde y radio (la elegida con borde azul); la ayuda «El horario queda libre para otro turno.» con ícono de información; el pie con «Volver» con borde y «Cancelar turno» rojo; en angosto, el resumen en una caja gris, las opciones en filas altas, los botones a todo el ancho con el destructivo arriba, el aviso ámbar para «Elegí quién pidió la cancelación.» y el aviso verde «Turno cancelado.».

**Se rechaza** (la KB y el spec mandan sobre el contenido):

- **Las descripciones bajo cada opción** que Stitch inventó («Cancelación solicitada por el usuario o vía recepción», «Por fuerza mayor clínica o indisponibilidad del odontólogo»): no están en la KB, y la segunda restringe sin motivo cuándo cancela el consultorio. Las opciones van solo con su nombre.
- El rótulo en mayúsculas: va en tipografía normal, como los demás rótulos de los paneles.
- El bloque «Después de cancelar» de la angosta: es una muestra; en la pantalla el panel se cierra y la agenda recargada muestra la fila.
- La franja roja a la izquierda de la tarjeta cancelada: la franja de la fila es el color de la prestación (C-14).
- «Agenda sincronizada en tiempo real», «4 turnos agendados» en el pie y el pie institucional: no hay tiempo real en la v1 y C-14 a C-16 ya los rechazaron.

El HTML de Stitch (Tailwind y Google Fonts por CDN) **no se copia**: se traduce a `panel.css` y, si hace falta, a `tokens.css` (por ejemplo, el rojo del botón destructivo, si todavía no hay un token), sin dependencias nuevas, sin CDN y con los íconos en SVG en línea (CSP `default-src 'self'`). Sin la comparación con estas capturas (X15), el change no se cierra (D234).

## Contradicciones y huecos encontrados en las fuentes

Todos quedaron resueltos con D343 a D353 (2026-10-29), escritas en la KB por el `/opsx:update`.

- **`RN-AG-12` sin estado HTTP**: `05` define el código y `08` no lo mapea (solo mapea `RN-AG-18`). D345 fija `409`.
- **El cuerpo de `POST /turnos/{id}/cancelar`**: `02` nombra la ruta sin cuerpo; `CHANGES.md` dice «indicando quién lo pidió (`cancelado_profesional` o `cancelado_paciente`)». D344 fija `{"estado": …}`.
- **US-013 «Como recepcionista»** y la matriz de `03` (la recepcionista «CRU + cancelar», el odontólogo «CRUD»): coinciden; la historia no excluye al odontólogo (D347).
- **US-013 CA-2 tiene dos partes**: liberar el horario (este change, `CAN-1b`) y disparar la lista de espera (C-36). `CHANGES.md` lo dice en «Alcance — fuera».
- **`pendiente_aprobacion` → `cancelado_profesional`** aparece dos veces en `04` (el rechazo de RN-TD-05 y la fila genérica «cualquier estado activo»): son dos acciones distintas que llegan al mismo estado; C-17 implementa la genérica y el rechazo queda en C-27 (X3).
- **«Cancelado por el consultorio»**: el estado de la API dice «profesional» y la pantalla dice «consultorio» desde C-14; la KB no fija la etiqueta. D351 la conserva (RN-TD-03 y D65 hablan de «el odontólogo o el consultorio»).
- **`cancelado_consultorio` en el frontend** contra `cancelado_profesional` en la API y en `04`: se corrige aquí (D342).

## Risks / Trade-offs

- [Renombrar `turno_para_reprogramar` rompe algo de C-16] → Es un REFACTOR de nombre con toda la suite (y el perfil `postgres` de `REP-1e`) en verde antes y después (tareas 3.4 y 5.2).
- [Un tercer botón por fila desborda la agenda angosta] → X11 los pone al pie de la tarjeta con salto de línea; la prueba en el navegador mide `scrollWidth` a 390 px (X15). V1 revisa los tests que cuentan botones.
- [«Cancelar» significa dos cosas en la misma pantalla] → El botón de cierre del panel nuevo es «Volver» (X11); «Nuevo turno» y «Reprogramar» conservan su «Cancelar», que cierra; los nombres accesibles de la fila son únicos («Cancelar el turno de …»).
- [Cancelar por error un turno] → No hay vuelta atrás (estado terminal); el panel pide elegir quién lo pidió sin opción por defecto, lo que obliga a una segunda decisión explícita antes de mandar. Deshacer queda fuera de la v1.
- [El botón visible para el dueño] → D312, como «Nuevo turno» y «Reprogramar»; el `403` se muestra con su texto.
- [Corregir el nombre del estado cambia el test `AGE-4c`] → Solo cambia el dato de partida (`cancelado_profesional`); lo que verifica (la etiqueta de cada estado) sigue igual, y la etiqueta no cambia (D351).

## A verificar en el change

- **V1** (antes de la tarea 8.2): qué tests de `pantalla-de-agenda`, `pantalla-de-historial` y `pantalla-de-reprogramacion` dependen de la cantidad o del orden de los botones de la fila (`getAllByRole('button')`); si alguno cambia, se ajusta solo su número.
- **V2** (antes de la tarea 3.2): que `cambiar_estado` con un `UPDATE` de `TurnoModelo.estado` en la sesión que leyó el turno con bloqueo devuelve el turno actualizado y que, en PostgreSQL, pasar a `cancelado_*` no dispara la restricción de exclusión (solo filtra activos).
- **V3** (antes de la tarea 5.2): en el perfil `postgres`, que la segunda de dos cancelaciones simultáneas espera el bloqueo de fila y lee el estado ya cancelado (y no el de antes), y que una cancelación contra una reprogramación simultánea nunca deja un `reprogramado` posterior a un `cancelado`.
- **V4** (antes de la tarea 12.1): en la demo, que el `POST` de la recepcionista deja en el historial `actor_id` `"2"` y que el panel del historial muestra «Turno cancelado» con la línea «Estado:».

## Migration Plan

Sin migraciones. La ruta nueva y el permiso nuevo se despliegan con la API; la acción y la corrección del nombre del estado, con el frontend. Volver atrás es revertir los commits del change: los turnos ya cancelados siguen cancelados (no hay salida de un estado terminal) y los eventos `cancelado` ya registrados quedan en el historial (es de solo inserción); con el frontend anterior, un turno `cancelado_profesional` haría que la agenda de ese día se vea como «sin conexión» (el defecto de D342), así que la vuelta atrás del frontend debería conservar la corrección del nombre.

## Notas para el archive

- Marcar C-17 con `[x]` en `CHANGES.md` y correr `python scripts/verificar_changes.py`.
- Quitar (o dejar como historia) la frase sobre `cancelado_consultorio` de las convenciones de `openspec/specs/pantalla-de-reprogramacion/spec.md` («El frontend todavía nombra `cancelado_consultorio` … lo corrige C-17 (D342)»), que queda desactualizada: es solo texto, sin cambio de comportamiento, con un commit `chore:` aparte (hallazgo H6).
- Registrar los resultados de V1 a V4 en `knowledge-base/10_preguntas_abiertas.md`, como «Cierre de C-17» después de la tabla de D343 a D353.
- Completar la sección 4 de `stitch-cancelar.md` con la comparación.
- C-17 es el cuarto change archivado de la fase 4: va la guía acumulada de mitad de fase, `docs/guias/prueba-manual-c14-c17.md` (escrita en la tarea 12.2), que se borra con un commit `chore:` cuando el autor la haga o decida saltearla.

## Open Questions

**Cerradas el 2026-10-29.** El autor aceptó las once recomendaciones («Sí, todo»); cada pregunta quedó como una decisión firme en `knowledge-base/10_preguntas_abiertas.md` (D343 a D353) y el `/opsx:update` ajustó specs, tareas y KB. Las preguntas se conservan como registro.

- **Q1 → D343 (capabilities).** ¿Dos capabilities nuevas, `cancelacion-de-turnos` y `pantalla-de-cancelacion`, más el delta MODIFIED de `pantalla-de-historial` (etiqueta del `cancelado` y los cuatro paneles), sin delta en `historial-de-turnos`, `pantalla-de-agenda` ni `pantalla-de-reprogramacion`? **Respuesta del autor: sí** (D343), como excepción a «una sola capability» limitada a C-17, con el corte API / navegador de D332 (X1).
- **Q2 → D344 (contrato del `POST`).** ¿Cuerpo `{"estado": "cancelado_paciente" | "cancelado_profesional"}` obligatorio, sin `motivo`, con cualquier otro valor como `422` de formato sin código y respuesta `200` con el turno? **Respuesta del autor: sí** (D344) (X2); la alternativa más legible, `{"pedido_por": "paciente" | "consultorio"}`, introduce un vocabulario que C-18 no comparte.
- **Q3 → D345 (estados, código y momento).** ¿Solo los turnos activos se cancelan; un terminal da `409` con `RN-AG-12` (`type` `/errores/transicion-invalida`), **también** si se pide la misma cancelación otra vez; en cualquier momento, también un turno pasado, sin distinguir el plazo de RN-TD-03 hasta C-22 y C-41? **Respuesta del autor: sí** (D345) (X3), y sumar el `409` de `RN-AG-12` a `08` y a `05`, que hoy no le fijan estado HTTP.
- **Q4 → D346 (orden de evaluación).** ¿Acceso (`401`, `403` `RN-AU-05`) → formato (`422` sin código) → `404` `RN-GL-04` del turno de la URL → `RN-AG-12` (`409`), escrito en `05` RN-GL-02? **Respuesta del autor: sí** (D346) (X4).
- **Q5 → D347 (permiso).** ¿Permiso nuevo `turnos.cancelar` para el odontólogo y la recepcionista; el dueño y un usuario sin roles con `403` `RN-AU-05`? **Respuesta del autor: sí** (D347) (X8), registrado en `03`.
- **Q6 → D348 (concurrencia).** ¿Bloqueo de fila del turno (el método de C-16, renombrado `turno_para_cambiar`), sin bloquear profesional ni sillón, sin migración, con la prueba de concurrencia (`CAN-1d`: dos cancelaciones; cancelación contra reprogramación) **solo** en el perfil `postgres`? **Respuesta del autor: sí** (D348) (X5, X6).
- **Q7 → D349 (el evento).** ¿Tipo `cancelado` con `antes` `{"estado": anterior}` y `despues` `{"estado": nuevo}`, `motivo` vacío, actor el usuario del token, en la misma transacción, y nada ante un rechazo? **Respuesta del autor: sí** (D349) (X7).
- **Q8 → D350 (la pantalla).** ¿Botón «Cancelar» (rojo, con borde) entre «Reprogramar» e «Historial», solo en los turnos activos; panel lateral «Cancelar turno» con el resumen, «¿Quién pidió la cancelación?» con «El paciente» y «El consultorio» **sin opción marcada**, «El horario queda libre para otro turno.», «Volver» (no «Cancelar») y «Cancelar turno»; frena sin opción con «Elegí quién pidió la cancelación.»; con `200`, «Turno cancelado.» y la recarga del mismo día; los rechazos de la tabla con «El turno no cambió.»; un solo panel entre los cuatro? **Respuesta del autor: sí** (D350) (X9 a X11); la opción sin marcar obliga a decidir y evita cancelar con el valor por defecto equivocado (su efecto sobre la seña llega en C-41).
- **Q9 → D351 (etiqueta y corrección de D342).** ¿El frontend pasa a `cancelado_profesional` y la etiqueta sigue siendo «Cancelado por el consultorio» (sin delta de `pantalla-de-agenda`), con la opción «El consultorio» que manda `cancelado_profesional`? **Respuesta del autor: sí** (D351): la pantalla ya le habla así al usuario (C-14), coincide con D65 («el odontólogo o el consultorio») y no obliga a cambiar `AGE-4c`. Alternativa: «Cancelado por el profesional» en la etiqueta y en la opción, con un delta de `pantalla-de-agenda`.
- **Q10 → D352 (el historial).** ¿«Turno cancelado» con una línea «Estado: {antes} → {después}» con las etiquetas de la agenda (por ejemplo, «Estado: Reservado → Cancelado por el paciente»), que no se muestra si falta un estado conocido? **Respuesta del autor: sí** (D352) (X10): dice a la vez quién lo pidió y desde qué estado, con textos que la pantalla ya tiene.
- **Q11 → D353 (tamaño).** ¿**16 escenarios nuevos o cambiados** (9 de la API, con `CAN-2b` partido en `CAN-2b` y `CAN-2c` por el hallazgo H2; 5 de la pantalla y 2 modificados del historial; los tres archivos suman 18 con `HIS-2a` y `HIS-2c` repetidos) y **32 tareas en 12 grupos**, por encima del «3 a 6» de la API y de «alrededor de 20» tareas de `config.yaml`, como excepción limitada a C-17 con el criterio de D300, D314, D325 y D341? **Respuesta del autor: sí** (D353): la API sola cubre CA-1, CA-2, CAN-1, la concurrencia, el evento y el acceso, y partir el change dejaría la acción sin API o la API sin uso.
