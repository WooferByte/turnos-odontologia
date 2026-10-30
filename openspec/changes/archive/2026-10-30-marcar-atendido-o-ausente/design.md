# Design: marcar-atendido-o-ausente

Fecha del design: **2026-10-30**. Change **C-18** (US-014; escenarios mínimos US-014 CA-1, CA-2, CA-3, CA-4, CA-6 y CA-11 de `CHANGES.md`). Gobernanza **MEDIO** (`CHANGES.md` C-18): se implementa con checkpoints y las decisiones no obvias se le presentan al autor antes del Apply. Motivación y alcance en `proposal.md`; el comportamiento, en `specs/marcado-de-asistencia/spec.md` (13 escenarios), `specs/pantalla-de-asistencia/spec.md` (6), el delta de `specs/pantalla-de-historial/spec.md` (dos requisitos MODIFIED: cambian `HIS-2b` y `HIS-2f`; `HIS-2a` y `HIS-2c` son copia literal), el delta de `specs/pantalla-de-cancelacion/spec.md` (un requisito MODIFIED: cambia `CAN-4c`; `CAN-4a` y `CAN-4b` son copia literal) y el delta de `specs/persistencia-postgresql/spec.md` (un requisito MODIFIED: suma dos escenarios de la migración `0010`; los diez vigentes son copia literal).

Las decisiones se numeran **W1 a W17** («W», una letra libre, para no confundirlas con las D1..D365 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores: D de C-01, I de C-02, H de C-03 y C-12, P de C-04, S de C-05, J de C-06, R de C-07, F de C-08, U de C-09, T de C-11, B de C-13, L de C-49, K de C-10, Y de C-50, A de C-14, G de C-15, M de C-16, X de C-17). Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design; si tiene pregunta abierta, la cita) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»). **Las preguntas Q1 a Q12 están cerradas** (sección final): el 2026-10-30 el autor aceptó las doce recomendaciones («Sí, todo») y los hallazgos H1 a H6 de `revisor-de-escenarios` (`docs/skills-mcp/evidencias/sesion-nueva/revision-de-escenarios-marcar-atendido-o-ausente.md`); el `/opsx:update` las registró como **D354 a D365** en `knowledge-base/10_preguntas_abiertas.md` y escribió en la KB lo que cada una fija. Las W que responden a una Q pasan a **Decisión del autor**.

## Context

**Lo que ya existe** (leído del código y de los specs, no supuesto):

- **Estados** (`domain/turnos/estados.py`): `EstadoTurno` con los nueve valores de `04` y `ESTADOS_ACTIVOS`. **Cancelar** (C-17, `domain/turnos/cancelacion.py`) codificó solo la fila «cualquier activo → cancelado» con `exigir_cancelable` y `TransicionInvalida` (`RN-AG-12`); X3 de C-17 dejó la tabla general de transiciones para «cuando el segundo change lo necesite».
- **Caso de uso de cancelar** (`application/cancelar_turno.py`): dentro de un `with uow:` lee el consultorio del usuario (D270), lee el turno con bloqueo de fila (`uow.agenda.turno_para_cambiar`, `FOR NO KEY UPDATE`, que SQLite omite), `TurnoNoEncontrado` si no existe o es de otro consultorio, la regla, `uow.agenda.cambiar_estado` (un `UPDATE` con `flush` que devuelve el `Turno`) y `uow.historial.registrar(evento_cancelado(...))`. Marcar es el mismo patrón con una regla más (el momento) y una escritura más (`es_nuevo`).
- **Errores** (`domain/errors.py`, `api/errores.py`): `TransicionInvalida` (`RN-AG-12`, `409`, `/errores/transicion-invalida`) y `TurnoNoReprogramable` (`RN-AG-18`, `409`). **No existe** un error para `RN-AG-13`; `08` no le fijaba estado HTTP (hueco de la KB, cerrado con Q4, D357).
- **Historial** (C-03, C-16, C-17): `TipoEvento` con `creado`, `reprogramado` y `cancelado`; `evento_turno.tipo` sin `CHECK`. La lista de tipos de `04` ya incluye `estado_cambiado` (Q7).
- **Reloj**: los casos de uso reciben `reloj: Reloj = utc_now` y la API lo inyecta con `get_reloj`; los tests lo fijan. `crear_turno` no rechaza un horario pasado (el reloj solo da `creado_en`), así que la API puede crear un turno que ya empezó (lo usan `ASI-1b` y la prueba en el navegador; V4).
- **Paciente**: `PacienteModelo` (`id`, `consultorio_id`, `nombre`, `apellido`, `telefono_whatsapp`) y el `Paciente` de dominio (`id`, `consultorio_id`) en `domain/agenda/recursos.py`; `RepositorioAgenda.paciente(id)` lo lee. **No existe `es_nuevo`**: `04` dice que lo agrega este change (D99).
- **Migraciones**: `backend/app/infrastructure/db/migraciones/versions/` llega a **`0009_bloqueo.py`** (`revision = '0009'`). `tests/postgres/test_migraciones.py` compara el esquema migrado con el modelo y tiene un test de «deshacer solo la migración X» por cada migración desde `0006`. La suite por defecto usa `create_all` sobre SQLite. El seed de la demo (`seed_demo.py`) y el de PostgreSQL insertan pacientes sin `es_nuevo`.
- **Permisos** (`domain/acceso/roles.py`): 18 permisos; `TURNOS_CANCELAR` con `_ODONTOLOGO_Y_RECEPCION`; `tests/unit/test_roles.py` cuenta `18 * 3`. La matriz de `03` tiene una fila propia «Marcar turno atendido / ausente (RN-AG-13)»: «U» para el odontólogo y la recepcionista, «—» para el dueño.
- **Frontend** (C-14 a C-17): `PaginaAgenda` con `Panel` = `ninguno` | `nuevo-turno` | `historial` | `reprogramar` | `cancelar`; `TablaDeTurnos` con «Reprogramar» y «Cancelar» (solo activos, `ESTADOS_ACTIVOS_DEL_TURNO`) e «Historial»; `PanelCancelar` (radios sin valor inicial, «Volver», la prop `onVolver`); `mensajes.ts` ya tiene las etiquetas «Atendido» (verde) y «Ausente» (rojo); `servidorFalso.ts` con `responderAlCancelar`, `cambiarEstado`, `retener`, `caerse`, `fallarRuta`, `vencerAccess`, `invalidarRefresh`, `quitarPermiso`. `features/historial/mensajes.ts` tiene `TITULOS_DE_EVENTO` y `detalleDelCancelado`.

## Goals / Non-Goals

**Goals:**

- Marcar un turno `reservado` o `confirmado` como `atendido` o `ausente` desde su inicio, liberar su horario, dejarlo en el historial y mantener `Paciente.es_nuevo`, con el mismo patrón y la misma familia de rechazos que la cancelación.
- Que dos escrituras simultáneas sobre el mismo turno nunca dejen dos eventos de cambio de estado.
- Que la agenda lo haga sin pantalla nueva, con un panel como los de C-14 a C-17, y que el historial lo muestre con su etiqueta.
- Dejar la tabla de transiciones en un solo lugar del dominio ahora que la usan dos acciones (W3).

**Non-Goals:**

- La corrección del marcado (C-19): la transición `atendido` ↔ `ausente` sigue rechazada con `RN-AG-12`; W3 deja el lugar donde C-19 la agrega con su condición.
- La seña (C-35 a C-42), la ficha clínica (C-43 en adelante) y los reportes (C-47).
- Usar `es_nuevo` (C-27) o mostrarlo (C-20): no viaja por ninguna respuesta de la API en este change.
- Ocultar «Asistencia» según el rol (D312) o según el reloj del navegador (W11).
- Control de versión optimista (como M7 de C-16 y X de C-17).

## Decisions

### W1. Capabilities — Decisión del autor (Q1, D354; hallazgo H1)

Dos capabilities nuevas, `marcado-de-asistencia` (API) y `pantalla-de-asistencia` (interfaz), más tres deltas MODIFIED: `pantalla-de-historial` (la etiqueta del `estado_cambiado` en `HIS-2b` y los cinco paneles en `HIS-2f`), `pantalla-de-cancelacion` (el requisito de la acción «Cancelar» completo: la frase de los paneles nombra los cinco y `CAN-4c` pide los cuatro botones de las filas 11 a 13 en el orden «Asistencia», «Reprogramar», «Cancelar», «Historial»; los títulos de los escenarios no cambian) y `persistencia-postgresql` (dos escenarios de la migración `0010`, como C-13 sumó los de `0009`). El evento y `es_nuevo` se especifican donde nacen, en `marcado-de-asistencia`, como `cancelado` (D343). **El delta de `pantalla-de-cancelacion` sale del hallazgo H1**: `CAN-4c` decía «los tres botones, en el orden…», una lista cerrada que con «Asistencia» deja de ser cierta, y su requisito nombraba cuatro paneles; sin delta, la spec principal quedaría describiendo una agenda que ya no existe. **No** hay delta de `pantalla-de-reprogramacion`: `REP-6c` dice que las filas activas «tienen los dos» botones, que sigue siendo cierto con botones de más, igual que C-17 sumó «Cancelar» sin tocarlo. **Alternativas descartadas**: una sola capability (dos suites distintas); agregar el marcado a `cancelacion-de-turnos` (otra acción, otra regla de momento, otro permiso); no hacer delta de `pantalla-de-cancelacion` y solo ajustar el test de `CAN-4c` (deja la spec principal desactualizada, H1). **Excepción** a «una sola capability» (regla dura 12), con el corte API / navegador de D241 a D343.

### W2. Contrato de `POST /turnos/{id}/estado` — Decisión del autor (Q2, D355)

- La ruta es la de `02` (fila Turnos: «`POST /turnos/{id}/estado` (marcar atendido o ausente; corregir el marcado, solo odontólogo)»). C-19 la reusa para la corrección, con la regla de su permiso y su plazo.
- Cuerpo `MarcarAsistenciaEntrada` (Pydantic, `extra="forbid"`): `estado: Literal["atendido", "ausente"]`, **obligatorio**. Cualquier otro valor (`reservado`, `cancelado_paciente`, `Atendido`), el `null`, la ausencia o un campo de más (`motivo`) es formato: `422` sin código, antes de mirar el turno. El nombre `estado` es el de `POST /turnos/{id}/cancelar` (D344, que lo eligió pensando en esta ruta): el cliente habla un solo idioma, el estado destino.
- Respuesta `200` con `TurnoSalida` (la de `POST /turnos`, `PATCH` y `/cancelar`). No suma `es_nuevo`: es un dato del paciente, no del turno.
- **Sin `motivo`**: el evento lo lleva vacío, como `reprogramado` y `cancelado`.
- **Alternativas descartadas**: dos rutas (`/atender`, `/ausente`), que C-19 tendría que duplicar; `{"asistio": true}` (otro vocabulario, que la API traduce y C-19 no comparte); `PATCH /turnos/{id}` con `estado` (mezcla reprogramar con una transición y rompe el contrato de D333).

### W3. Estados, código y tabla de transiciones — Decisión del autor (Q3, D356; aplica RN-AG-12, RN-AG-13, DD-16, D32)

- Solo `reservado` y `confirmado` se marcan (tabla de `04`; DD-16 confirma que `pendiente_sena` y `pendiente_aprobacion` tampoco, D32). Cualquier otro estado da **`RN-AG-12`** con **`409`** (D345): `pendiente_*`, los cancelados, `vencido`, y también `atendido` y `ausente`, **incluso** el mismo marcado repetido (no hay `200` idempotente, como en D345) y el contrario (la corrección, C-19).
- **Dominio puro**: `domain/turnos/asistencia.py` con `ESTADOS_DE_ASISTENCIA = {ATENDIDO, AUSENTE}`, `ESTADOS_QUE_SE_MARCAN = {RESERVADO, CONFIRMADO}` y `exigir_marcable(estado, inicio, ahora)`, que levanta `TransicionInvalida` si el estado no se marca y, si se marca, `MarcadoAntesDelInicio` si `ahora < inicio` (W4); y `deja_de_ser_nuevo(estado_nuevo) -> bool` (`True` solo con `atendido`, W8).
- **Tabla de transiciones**: no se arma la tabla general de `04` (Non-Goals de C-17); con dos acciones alcanza con dos funciones puras, cada una con su conjunto de origen. Se generaliza cuando C-19 sume la corrección con su condición (plazo y rol). **Alternativa descartada**: un `TRANSICIONES: dict[EstadoTurno, set[EstadoTurno]]` ahora, que no expresa las condiciones de momento, plazo y rol y obligaría a reescribir `exigir_cancelable`.
- **Estado almacenado**: se mira el estado guardado del turno (D317); `pendiente_sena` nunca se marca, así que el estado efectivo de la seña no cambia nada.

### W4. RN-AG-13: estado HTTP y borde — Decisión del autor (Q4, D357; aplica RN-AG-13, D34)

- `MarcadoAntesDelInicio` (nuevo en `domain/errors.py`, código **`RN-AG-13`**) → **`409`**, `type` `/errores/marcado-antes-del-inicio`. Motivo: la petición está bien formada (solo trae `atendido` o `ausente`, sin ninguna fecha) y lo que falla es el **estado actual del recurso** respecto del reloj, como `RN-AG-12`; repetir la misma petición más tarde puede funcionar. `422` se reserva en este proyecto para un problema de la petición o del horario pedido (`RN-AG-10d`, `RN-AG-04`, `RN-AG-04b`), y aquí la petición no pide ningún horario.
- **Borde**: `ahora >= inicio` se admite con igualdad (`ASI-1b`), comparando dos fechas aware en UTC; el reloj es el `utc_now()` inyectado (regla dura 2). No hay plazo máximo para marcar (un turno de hace días se marca, `ASI-1b`).
- **Hueco de la KB, cerrado**: `05` definía el código y `08` no lo mapeaba. El `/opsx:update` del 2026-10-30 sumó la fila a `08` y el `409` con su `type` a RN-AG-13 de `05` (D357).
- **Alternativa descartada**: `422`, con el argumento de que «la agenda no admite» el marcado como no admite un turno fuera de horario; pero aquí no hay un horario pedido que corregir.

### W5. Clases de rechazo y orden de evaluación — Decisión del autor (Q5, D358; aplica RN-GL-02, D135, D208, D166, D346)

1. **Acceso**: `401` sin sesión válida; `403` `RN-AU-05` sin `turnos.marcar` (D208).
2. **Formato** (Pydantic): `422` sin código. No hay validación de entrada con código: el cuerpo no trae fechas ni referencias.
3. **Turno de la URL**: `404` `RN-GL-04` si no existe o es de otro consultorio (D166, D321).
4. **Regla de negocio, de a una**: `RN-AG-12` (estado, `409`) → `RN-AG-13` (momento, `409`).

Igual que `POST /turnos/{id}/cancelar` (D346): todo el cuerpo es formato, así que el turno 999 con un `estado` inválido da `422` (`ASI-4b`). `RN-AG-12` va antes que `RN-AG-13` porque un turno que no admite el marcado no lo admite nunca, y el momento solo importa si el estado lo admite (un cancelado futuro informa `RN-AG-12`, `ASI-1d`); es además el orden de `05` y del Flujo 7. Vale el mismo límite de D208: JSON roto → `422` antes que `401`. La línea «Orden de evaluación de `POST /turnos/{id}/estado`» quedó en RN-GL-02 de `05` con el `/opsx:update` del 2026-10-30 (D358).

### W6. Caso de uso y repositorio — Propuesta

`application/marcar_asistencia.py`: `MarcarAsistenciaComando(turno_id, estado)` y `marcar_asistencia(comando, usuario_id, uow, reloj, *, actor) -> Turno`. Dentro de un `with uow:`: consultorio del usuario (D270); el turno con `uow.agenda.turno_para_cambiar` (bloqueo de fila); `TurnoNoEncontrado` si no existe o es de otro consultorio; `ahora = reloj()`; `exigir_marcable(turno.estado, turno.inicio, ahora)`; `uow.agenda.cambiar_estado(turno.id, estado)`; si `deja_de_ser_nuevo(estado)`, `uow.agenda.marcar_paciente_no_nuevo(turno.paciente_id)`; `uow.historial.registrar(evento_estado_cambiado(turno, guardado, actor, ahora))`. Un solo `reloj()` por petición: el mismo instante decide `RN-AG-13` y queda en `ocurrido_en`. Sin reintentos: cambiar el estado a uno no activo solo libera horario. **No relee** el profesional, el sillón ni la prestación: un turno cuyos recursos se desactivaron después de crearlo se marca igual, porque `RN-AG-07` y `RN-GL-04` solo rechazan lo inactivo al crear o reprogramar (`ASI-1f`, hallazgo H4).

`marcar_paciente_no_nuevo(paciente_id)` es un `UPDATE paciente SET es_nuevo = false WHERE id = :id AND es_nuevo` con `flush` (idempotente, sin leer antes); va en `RepositorioAgenda` porque ya es el que lee `paciente(id)` para los turnos (no hay repositorio de pacientes hasta C-20). `paciente(id)` pasa a leer también `es_nuevo` en el `Paciente` de dominio (`es_nuevo: bool = True`, con valor por defecto para no tocar los usos existentes). **Alternativa descartada**: un repositorio de pacientes nuevo (C-20 lo crea con su gestión).

### W7. El evento `estado_cambiado` — Decisión del autor (Q7, D360; aplica RN-AG-11, D159, D209)

`TipoEvento.ESTADO_CAMBIADO = "estado_cambiado"` (el valor ya está en la lista de `04`) y `evento_estado_cambiado(antes: Turno, despues: Turno, actor, ocurrido_en)` puro en `domain/turnos/eventos.py`, con la misma forma que `evento_cancelado`: `antes` `{"estado": <anterior>}`, `despues` `{"estado": <nuevo>}`, `motivo` `None`, actor el usuario del token. `04` dice que en una corrección `antes` lleva el valor anterior: C-19 reusa el mismo tipo y la misma forma. Mismo `with uow:` que los dos `UPDATE`: un rechazo no registra nada (`ASI-2b`) y, si el registro falla, ni el estado ni `es_nuevo` quedan (`ASI-2c`, verificado con un disparador de SQLite, sin dobles; regla dura 6). **Alternativas descartadas**: tipos `atendido` y `ausente` (no están en la lista de `04` y duplican lo que dice `despues`); un `EventoPaciente` por `es_nuevo` (`04`: «Las consecuencias sobre el paciente de un hecho de turno no generan un `EventoPaciente`»).

### W8. `Paciente.es_nuevo` y la migración `0010` — Decisión del autor (Q8, D361; aplica RN-TD-05, D52, D99; skills `database-migration` y `supabase-postgres-best-practices`)

- **Modelo**: `PacienteModelo.es_nuevo: Mapped[bool] = mapped_column(default=True, server_default=sa.true())`. La suite por defecto (`create_all`) y el seed de la demo no cambian: los pacientes nacen nuevos.
- **Migración `0010_paciente_es_nuevo.py`** (`revision = '0010'`, `down_revision = '0009'`), generada con autogenerate y revisada a mano: `op.add_column('paciente', sa.Column('es_nuevo', sa.Boolean(), server_default=sa.true(), nullable=False))` (con `server_default`, agregar una columna no nula a una tabla con filas es inmediato en PostgreSQL 17 y no necesita el patrón expand/contract), y **relleno** en la misma migración: `UPDATE paciente SET es_nuevo = false WHERE EXISTS (SELECT 1 FROM turno WHERE turno.paciente_id = paciente.id AND turno.estado = 'atendido')`. Hoy ningún camino de la API deja un turno `atendido`, así que en una base real el relleno no cambia nada; existe para que la columna sea cierta por definición (D52) en cualquier base migrada, incluida una cargada a mano. **Se conserva el `server_default`** (no se quita después del relleno): un `INSERT` sin la columna, como el del seed, sigue valiendo. `downgrade` borra la columna (se pierde el dato; se recalcula con el relleno al volver a aplicar).
- **Escritura**: solo con `atendido` (W6); `ausente` y un rechazo no la tocan; una corrección posterior `atendido` → `ausente` no la revierte (D52; lo cumple C-19 por no tocarla).
- **No se expone** por la API: los escenarios `ASI-3a/b` la leen con el repositorio, a nivel de caso de uso. **Alternativa descartada**: sumarla a la agenda o a `TurnoSalida` (C-20 y C-27 la necesitan en sus propias respuestas; ponerla ahora es un contrato sin uso).
- **Alternativa descartada**: calcular `es_nuevo` al vuelo (`NOT EXISTS` turno atendido) sin columna: `04` y D99 piden la columna, y una corrección `atendido` → `ausente` la cambiaría, contra D52.
- **Tests**: `test_migraciones.py` suma el test de deshacer solo `0010` y el del relleno (perfil `postgres`, `INF-1`); el que compara el esquema migrado con el modelo cubre la columna sin cambios.

### W9. Permiso — Decisión del autor (Q6, D359)

`Permiso.TURNOS_MARCAR = "turnos.marcar"` con `_ODONTOLOGO_Y_RECEPCION` (fila «Marcar turno atendido / ausente» de `03`: «U», «U», «—»; RN-AG-13, D19). El dueño y un usuario sin roles reciben `403` `RN-AU-05`. El contador de `test_roles.py` pasa a `19 * 3`; el guard de rutas protegidas encuentra la ruta nueva. C-19 agrega su propio permiso para la corrección (solo el odontólogo). **Alternativa descartada**: reusar `turnos.cancelar` (otra fila de `03`; D336 y D347 eligieron un permiso por acción).

### W10. Concurrencia — Decisión del autor (Q9, D362; aplica D337, D348)

Una sola fila bloqueada, la del turno (`turno_para_cambiar`): dos marcados del mismo turno se serializan y el segundo lee `atendido` o `ausente` → `RN-AG-12` (un solo evento). Un marcado y una cancelación (o una reprogramación) del mismo turno también se serializan: el segundo ve el estado terminal y responde `RN-AG-12` o `RN-AG-18`. `es_nuevo` no necesita bloqueo propio: dos `atendido` simultáneos de dos turnos del mismo paciente escriben los dos `false` (idempotente). **Prueba** solo en el perfil `postgres` (`tests/postgres/test_marcados_simultaneos.py`, con el patrón de `carrera.py` y la espera forzada con `pg_stat_activity` que C-17 necesitó, V3 de C-17), las dos corridas de `ASI-1e`.

### W11. Clases de rechazo de la pantalla y momento — Decisión del autor (Q10, D363; aplica D323)

La pantalla no evalúa reglas: decide el texto por el tipo de error y el código (tabla del spec), nunca por el `detail`. **No compara la hora del turno con el reloj del navegador**: «Asistencia» se ve en todo turno `reservado` o `confirmado`, también de un día futuro, y el `409` `RN-AG-13` de la API se muestra con su texto (`ASI-6b`). Motivo: el reloj del navegador puede no coincidir con el de la API, y D323 deja las reglas en la API. Lo único que frena sin pedir nada es «Registrar asistencia» sin opción. Cada rechazo suma «El turno no cambió.». Un `422` no puede salir de esta pantalla (los dos valores son fijos): se muestra como el aviso de conexión, igual que un `5xx`.

### W12. Estructura del frontend — Decisión del autor (Q10, Q11, D363, D364) + Propuesta (detalle; aplica A9, G8, M11, X10 y `vercel-react-best-practices`)

- `apiAgenda.ts`: `ESTADOS_QUE_SE_MARCAN_DEL_TURNO = ['reservado', 'confirmado']`; el tipo `EstadoDeAsistencia = 'atendido' | 'ausente'`; `marcarAsistencia(id, estado)` con `POST /api/turnos/{id}/estado`, validando el `200` sin `any` (la forma de `TurnoCreado`).
- `mensajes.ts` de la agenda: `mensajeDeAsistencia(error)` con `RN-AG-12`, `RN-AG-13`, el `404`, el `403` y el aviso de conexión; las constantes «Asistencia registrada.», «Elegí si el paciente fue atendido o estuvo ausente.», «¿Cómo terminó el turno?», «Atendido», «Ausente», «Registrar asistencia»; reusa `AYUDA_DE_CANCELACION` («El horario queda libre para otro turno.») renombrada a un nombre común si el REFACTOR lo pide, y `MENSAJE_EL_TURNO_NO_CAMBIO`.
- `PanelAsistencia.tsx` (componente de nivel superior), con la forma de `PanelCancelar`: un `fieldset` con `legend` «¿Cómo terminó el turno?» y dos radios nativos sin valor inicial (estado local `EstadoDeAsistencia | null`), el aviso, «Volver» (prop `onVolver`) y «Registrar asistencia» (**primario**, no destructivo: marcar no borra nada). Si el REFACTOR muestra que los dos paneles comparten la estructura, se extrae un componente común sin cambiar los tests (tarea 12.1).
- `TablaDeTurnos.tsx`: `onRegistrarAsistencia(turno)`; el botón «Asistencia» (ícono de tilde en círculo, SVG en línea en `shared/iconos/IconoAsistencia.tsx`) **primero** en la fila, solo en `ESTADOS_QUE_SE_MARCAN_DEL_TURNO`, con el nombre accesible «Registrar la asistencia del turno de {paciente}, {hora}».
- `PaginaAgenda.tsx`: `Panel` suma `{ tipo: 'asistencia'; turno }`; un solo panel a la vez; `ir()` lo cierra; `registrarAsistencia()` con la guarda `enCurso` y la recarga del mismo día; si la recarga falla, «Asistencia registrada.» y el aviso con «Reintentar» (como `CAN-4b`); el foco vuelve al botón de la fila al cerrar.
- `features/historial/mensajes.ts`: `TITULOS_DE_EVENTO.estado_cambiado = 'Cambio de estado'` y el detalle «Estado: {antes} → {después}» con las etiquetas de la agenda; `detalleDelCancelado` se generaliza a `detalleDelCambioDeEstado` y lo usan los dos tipos (REFACTOR, tarea 11.4).

### W13. Interacción y anchos — Decisión del autor (Q10, D363; sale de las pantallas de Stitch)

En escritorio el panel va al costado de la agenda (unos 420 px), como los otros cuatro. **Hallazgo de Stitch**: con el panel abierto a 1280 px, cuatro botones por fila no entran y la columna «Acciones» se corta (captura de escritorio, «Historial» tapado). Se resuelve en CSS: los botones de la columna se acomodan con salto de línea (`flex-wrap`) dentro de la celda cuando no entran, sin desplazamiento horizontal de la página ni de la tabla; la prueba en el navegador mide `scrollWidth` a 1280 px con el panel abierto y a 390 px (W15). Debajo de 720 px el panel va a todo el ancho debajo de la barra, con «Registrar asistencia» arriba y «Volver» debajo, y en las tarjetas los cuatro botones van al pie con salto de línea. Al abrir, el foco va a la primera opción; al cerrar, vuelve al botón «Asistencia» de la fila. Las opciones son filas con borde de 44 px de alto como mínimo.

### W14. Servidor falso y tests — Propuesta (aplica D222, D227; reglas duras 6 y 8)

`servidorFalso.ts` suma `POST /api/turnos/{id}/estado` con tres comportamientos mínimos: `404` `RN-GL-04` si el turno no está; `409` `RN-AG-12` si no está `reservado` ni `confirmado`; y, si no, `200` con el turno en el estado pedido (y lo guarda). No evalúa el momento: `RN-AG-13` y los demás rechazos salen de `responderAlMarcar(estado, codigos)`, de una sola vez, como `responderAlCancelar`. Reusa `cambiarEstado(id, estado)` para la «otra sesión» de `ASI-6a`. Respeta `retener`, `caerse`, `vencerAccess`, `invalidarRefresh`, `quitarPermiso` y `fallarRuta`; guarda el cuerpo del último `POST`. Backend: tokens reales en los tests de API (D211), reloj fijo inyectado por test (en `2026-11-02T13:10:00Z` salvo los bordes), SQLite en memoria; los turnos en otros estados, ya empezados o de otro consultorio se cargan con la fábrica de tests (`un_turno(..., estado=...)`); `un_paciente` acepta `es_nuevo`. Los datos de partida respetan D52 (hallazgo H3): un paciente con un turno `atendido` cargado con la fábrica tiene `es_nuevo` `false` (Carla Inventada, y Bruno en `ASI-3b`), y los turnos activos cargados con la fábrica no se superponen en el mismo profesional y sillón (`ASI-1c`), para que el escenario valga también en PostgreSQL. `ASI-1f` desactiva el profesional, el sillón y la prestación con la fábrica después de crear el turno.

### W15. Prueba en el navegador — Decisión del autor (D234, `rules.tasks`, acuerdo del 2026-10-30) + Propuesta (detalle)

**La prueba del agente es la verificación** (acuerdo del autor del 2026-10-30): no hay guía manual en `docs/guias/`. Con la demo (`crear_app_demo` y `npm run dev`): la recepcionista crea **hoy**, desde el formulario «Nuevo turno», un turno que ya empezó y otro más tarde (la demo usa el reloj real; V4, con su plan B si la hora no lo permite); registra «Atendido» en el primero (`ASI-5a`) y crea otro turno en el mismo horario; intenta registrar el de más tarde y ve `RN-AG-13` (`ASI-6b`); registra «Ausente» en otro ya empezado (`ASI-5b`); intenta sin elegir (`ASI-6c`); abre dos pestañas y registra el mismo turno en las dos (`ASI-6a`); abre el historial y ve «Cambio de estado» con «Estado: Reservado → Atendido» (`HIS-2b`); el dueño recibe `RN-AU-05` (`ASI-6c`); en `/docs`, el mismo `POST`. Comparar con las dos capturas de Stitch a 1280 y 390 px, guardar las capturas de la implementación junto a las de Stitch y anotar las diferencias en la sección 4 de `stitch-asistencia.md`. Consola sin errores ni datos sensibles; sin desplazamiento horizontal a 1280 px con el panel abierto ni a 390 px. Después un recorrido breve en Compose (`http://127.0.0.1:5173`) para ver la CSP y que la API de Compose corre la migración `0010`.

### W16. Versiones, demo y README — Propuesta

No se agrega ni cambia ningún paquete: ni `backend/pyproject.toml` ni `frontend/package.json` ni `package-lock.json`; la política de pins (D133) no aplica. Sin datos nuevos de seed (los pacientes nacen con `es_nuevo` `true`). El README suma `POST /turnos/{id}/estado` en «Probar desde Swagger» (con la recepcionista: crear un turno hoy ya empezado, marcarlo `atendido`, repetir y ver `409` `RN-AG-12`, crear otro en el mismo hueco, un turno futuro con `409` `RN-AG-13`, un `estado` inválido con `422`, el dueño con `403` y el historial con el `estado_cambiado`), «Registrar la asistencia» en «Panel (interfaz)», la migración `0010` y la prueba nueva del perfil `postgres`, las tablas escenario → test y los límites conocidos (la corrección llega con C-19; la seña con C-41; `es_nuevo` no se ve hasta C-20; el dueño ve la acción, D312; «Asistencia» se ve también en un turno futuro, W11).

### W17. Skills aplicadas

- `fastapi-templates`: router → caso de uso → repositorio; `TurnoSalida` en la respuesta, nunca el modelo ORM; `Depends(requiere(...))`; `def` síncrono; `Literal` en el esquema para el formato.
- `python-design-patterns`: reglas puras en `domain/` (`exigir_marcable`, `deja_de_ser_nuevo`, `evento_estado_cambiado`); el bloqueo compartido `turno_para_cambiar`; sin una abstracción general de transiciones hasta que C-19 la necesite (W3).
- `python-error-handling`: `MarcadoAntesDelInicio` con su código; acceso antes que validación; formato antes que existencia; `RN-AG-12` antes que `RN-AG-13` (W5).
- `python-testing-patterns`: AAA, `parametrize` para los estados y los valores, SQLite real, reloj inyectado, marcador `postgres` para la concurrencia y la migración.
- `auth-implementation-patterns`: un permiso por acción, chequeado en la dependencia de la ruta antes que nada (`403` sin revelar si el turno existe).
- `database-migration`: una migración reversible por cambio de esquema; columna nueva con valor por defecto; el relleno en la misma transacción de la migración; nada destructivo salvo el `downgrade` documentado; autogenerate revisado a mano.
- `supabase-postgres-best-practices` (solo lo genérico): `boolean NOT NULL DEFAULT true` sin reescritura de la tabla; transacción corta con una sola fila bloqueada; la exclusión parcial de `0002` ya libera el hueco.
- `vercel-react-best-practices`: abrir el panel no pide nada, estado derivado en el render, componentes de nivel superior, ternarios en vez de `&&`.
- `revisor-de-escenarios`: se corre después de este propose y antes del Apply.

## Referencia visual (Stitch)

Pantallas generadas en este propose con el MCP `stitch`, proyecto `projects/14200813501064679723`, design system «Clinical Ops» (`assets/b683d44391ab410db2dd48aa71ed0b47`), modelo `GEMINI_3_8_FLASH`, cada una al primer intento. Pedidos, ids de archivos y revisión de datos en [`docs/skills-mcp/evidencias/sesion-nueva/stitch-asistencia.md`](../../../docs/skills-mcp/evidencias/sesion-nueva/stitch-asistencia.md). Los textos pedidos son los de las recomendaciones de Q10 y Q11, **aceptadas por el autor** el 2026-10-30 (D363, D364); ante cualquier diferencia, el texto lo manda el spec.

| Pantalla | Id | Evidencia |
|---|---|---|
| Registrar asistencia con error (`RN-AG-13`), escritorio | `projects/14200813501064679723/screens/b64bb7234a344397b127fc921f0fc733` | `stitch-asistencia-pantalla/asistencia-escritorio.png` y `.html` |
| Registrar asistencia sin opción elegida y el resultado, angosta | `projects/14200813501064679723/screens/7c88173529aa4877952728a3abe6c05c` | `stitch-asistencia-pantalla/asistencia-angosta.png` y `.html` |

**Se toma**: el botón con borde «Asistencia» con ícono de tilde en círculo como primero de la fila y su ausencia en las filas «Atendido» y «Ausente»; la fila del turno abierto resaltada y su botón «Asistencia» con borde azul; el panel lateral sin oscurecer la agenda, con el título con ícono azul, la X y el resumen en una caja gris con el chip del estado actual; el aviso de error rojo suave con ícono, el texto con el código y «El turno no cambió.» en una segunda línea; el rótulo «¿Cómo terminó el turno?» en tipografía normal y las dos opciones como filas con borde y radio (la elegida con borde azul y fondo celeste); la ayuda con ícono de información; el pie con «Volver» con borde y «Registrar asistencia» primario azul; en angosto, las opciones en filas altas, los botones a todo el ancho con el primario arriba, el aviso ámbar para «Elegí si el paciente fue atendido o estuvo ausente.» y el aviso verde «Asistencia registrada.».

**Se rechaza** (la KB y el spec mandan sobre el contenido):

- **La columna «Acciones» cortada** con el panel abierto: se corrige con el salto de línea de W13.
- El subtítulo «Horas del consultorio (America/Argentina/Buenos_Aires).» y el campo «30/10/2026» que Stitch dibujó en la barra de fecha: la agenda de C-14 ya tiene su propio encabezado y no cambia en este change.
- El bloque «Después de registrar» de la angosta: es una muestra; en la pantalla el panel se cierra y la agenda recargada muestra la fila.
- La franja verde a la izquierda de la tarjeta atendida: la franja de la fila es el color de la prestación (C-14).
- El chip «Confirmado» en verde fuerte dentro de la fila: los tonos de estado son los de `TONOS_DE_ESTADO` (C-14), sin cambios.

El HTML de Stitch (Tailwind, Google Fonts y Material Symbols por CDN) **no se copia**: se traduce a `panel.css` y, si hace falta, a `tokens.css`, sin dependencias nuevas, sin CDN y con los íconos en SVG en línea (CSP `default-src 'self'`). Sin la comparación con estas capturas (W15), el change no se cierra (D234).

## Contradicciones y huecos encontrados en las fuentes

- **`RN-AG-13` sin estado HTTP**: `05` definía el código y `08` no lo mapeaba. Cerrado con D357: `409`.
- **El cuerpo de `POST /turnos/{id}/estado`**: `02` nombraba la ruta sin cuerpo. Cerrado con D355: `{"estado": "atendido" | "ausente"}`, el idioma de D344.
- **Orden entre `RN-AG-12` y `RN-AG-13`**: la KB los lista en ese orden (`05`, Flujo 7) pero RN-GL-02 no fijaba el orden de esta ruta. Cerrado con D358.
- **Tipo del evento**: `04` lista `estado_cambiado` pero ninguna regla decía qué evento registra el marcado. Cerrado con D360.
- **Permiso**: `03` tiene una fila propia para el marcado, distinta de «Turnos»; cerrado con D359, un permiso propio.
- **`es_nuevo` y los pacientes existentes**: `04` fija el default `true` pero no qué pasa con un paciente que ya tenga un `atendido` al migrar; cerrado con D361, el relleno.
- **US-014 CA-2 «libera el horario»**: un turno marcado ya empezó, así que el hueco liberado es el resto del turno (o el pasado); la creación en el mismo horario de `ASI-1b` lo prueba igual porque la API no rechaza horarios pasados (V4).
- **Botones por fila**: cuatro botones no entran con el panel abierto a 1280 px (Stitch); W13.
- **`CAN-4c` dice «los tres botones»**: con el botón nuevo son cuatro. `revisor-de-escenarios` lo marcó (H1) y el autor lo aceptó: se suma el delta MODIFIED de `pantalla-de-cancelacion` (W1, D354).

## Risks / Trade-offs

- [Cuatro botones desbordan la fila con el panel abierto] → W13 con salto de línea; la prueba mide `scrollWidth` a 1280 y 390 px; V1 revisa los tests que cuentan botones.
- [«Asistencia» visible en turnos futuros genera rechazos `RN-AG-13`] → Es la consecuencia de no evaluar reglas en el navegador (W11, D323); el texto explica desde cuándo se puede. Alternativa en Q10.
- [Marcar por error] → El panel obliga a elegir sin opción por defecto; la corrección dentro de 24 h llega con C-19 (solo el odontólogo). Hasta C-19 no hay vuelta atrás.
- [La migración `0010` sobre una base con datos] → `ADD COLUMN ... DEFAULT true NOT NULL` no reescribe la tabla en PostgreSQL 17; el relleno es un `UPDATE` acotado; `downgrade` probado (`INF-1`).
- [Generalizar `detalleDelCancelado` rompe `HIS-2b`] → REFACTOR con los tests de `HIS-2b` en verde antes y después (tarea 11.4).
- [El reloj de la demo es el real] → La prueba en el navegador crea turnos de hoy ya empezados y futuros (V4); los tests usan reloj fijo.

## A verificar en el change

- **V1** (antes de la tarea 9.2): qué tests de `pantalla-de-agenda`, `pantalla-de-historial`, `pantalla-de-reprogramacion` y `pantalla-de-cancelacion` dependen de la cantidad o del orden absoluto de los botones de la fila. El de `CAN-4c` cambia con su delta (tarea 9.1: espera los cuatro botones); si algún otro depende de la cantidad, se ajusta solo su número.
- **V2** (antes de la tarea 4.2): que `marcar_paciente_no_nuevo` con `flush` en la misma sesión que el `UPDATE` del turno se deshace junto con él cuando falla el `INSERT` del evento (lo prueba `ASI-2c`), y que en PostgreSQL pasar a `atendido` o `ausente` no dispara la restricción de exclusión.
- **V3** (antes de la tarea 3.2): en el perfil `postgres`, que la migración `0010` sobre `0009` con datos rellena `es_nuevo` como dice `INF-1`, que su `downgrade` deja el esquema de `0009` y que el test de esquema migrado contra el modelo sigue sin diferencias (tipo `boolean`, `server_default`, no nula).
- **V4** (antes de las tareas 7.1 y 13.1): en la demo, que `POST /turnos` **y el formulario «Nuevo turno» de la agenda** aceptan un turno de hoy que ya empezó dentro del horario del profesional (lunes a viernes, 09:00-13:00 y 15:00-19:00 del consultorio; la prueba lo necesita) y que el historial muestra `actor_id` `"2"` con «Cambio de estado». **Plan B** (hallazgo H6) si la prueba cae fuera de ese horario (fin de semana, antes de las 09:00, entre las 13:00 y las 15:00 o después de las 19:00): crear el turno ya empezado en el **último día hábil anterior**, dentro de las franjas (por ejemplo, el viernes a las 09:00), ir a ese día en la agenda y marcarlo desde ahí (no hay plazo máximo para marcar, D356); el turno «futuro» de `ASI-6b` va en el próximo día hábil. Si el formulario no acepta un inicio en el pasado, se frena y se avisa al autor (MEDIO): la API sí lo acepta y la prueba no inventa otra vía.

## Migration Plan

Una migración nueva, `0010`, que se aplica con `alembic upgrade head` (la API de Compose la corre al arrancar, como las anteriores). Después se despliega la API (ruta y permiso nuevos) y luego el frontend. Volver atrás: revertir el frontend y la API y, si hace falta, `alembic downgrade 0009` (se pierde `es_nuevo`, que se recalcula al volver a migrar por el relleno). Los turnos ya marcados siguen `atendido` o `ausente` (un estado terminal no tiene salida hasta C-19) y los eventos `estado_cambiado` quedan en el historial (solo inserción); el frontend anterior ya muestra esos estados y el evento como «Cambio registrado (estado_cambiado)».

## Notas para el archive

- Marcar C-18 con `[x]` en `CHANGES.md` y correr `python scripts/verificar_changes.py`.
- Registrar los resultados de V1 a V4 en `knowledge-base/10_preguntas_abiertas.md`, como «Cierre de C-18» después de la tabla de D354 a D365.
- Completar la sección 4 de `stitch-asistencia.md` con la comparación.
- Sin guía manual (acuerdo del autor del 2026-10-30): la prueba del agente es la verificación.

## Open Questions

**Cerradas el 2026-10-30.** El autor aceptó las doce recomendaciones («Sí, todo»), que quedaron como **D354 a D365** en `knowledge-base/10_preguntas_abiertas.md`, y los hallazgos H1 a H6 de `revisor-de-escenarios`. Se conserva el texto de cada pregunta como registro; donde un hallazgo cambió el alcance (Q1 con H1, Q12 con H1 y H4) se anota.

- **Q1 → D354 (capabilities).** ¿Dos capabilities nuevas, `marcado-de-asistencia` y `pantalla-de-asistencia`, más los deltas MODIFIED de `pantalla-de-historial` (etiqueta del `estado_cambiado` y los cinco paneles) y `persistencia-postgresql` (migración `0010`), sin delta de `pantalla-de-cancelacion` ni `pantalla-de-reprogramacion`? **Recomendación: sí**, como excepción a «una sola capability» limitada a C-18, con el corte API / navegador de D343 (W1). **Aceptada (D354), con H1**: se suma además un delta MODIFIED de `pantalla-de-cancelacion` (`CAN-4c` con los cuatro botones y la frase de los cinco paneles).
- **Q2 → D355 (contrato).** ¿`POST /turnos/{id}/estado` con cuerpo obligatorio `{"estado": "atendido" | "ausente"}`, sin `motivo`, con cualquier otro valor como `422` de formato sin código y respuesta `200` con el turno (sin `es_nuevo`)? **Recomendación: sí, aceptada** (W2): es el idioma de D344 y C-19 lo reusa.
- **Q3 → D356 (estados).** ¿Solo `reservado` y `confirmado` se marcan; cualquier otro estado da `409` `RN-AG-12`, **también** el mismo marcado repetido y el contrario (`atendido` ↔ `ausente`, que habilita C-19); sin plazo máximo para marcar un turno pasado? **Recomendación: sí, aceptada** (W3), como D345.
- **Q4 → D357 (`RN-AG-13`).** ¿`RN-AG-13` con **`409`**, `type` `/errores/marcado-antes-del-inicio`, admitiendo `ahora == inicio`? **Recomendación: sí, aceptada** (W4): falla el estado del recurso respecto del reloj, no la petición; sumar el `409` a `05` y a `08`. Alternativa: `422`, como las reglas de horario.
- **Q5 → D358 (orden).** ¿Acceso (`401`, `403` `RN-AU-05`) → formato (`422`) → `404` `RN-GL-04` → `RN-AG-12` → `RN-AG-13`, escrito en RN-GL-02 de `05`? **Recomendación: sí, aceptada** (W5): un turno que no admite el marcado no lo admite nunca, así que el estado va antes que el momento.
- **Q6 → D359 (permiso).** ¿Permiso nuevo `turnos.marcar` para el odontólogo y la recepcionista; el dueño y un usuario sin roles con `403` `RN-AU-05`? **Recomendación: sí, aceptada** (W9), registrado en `03` sobre la fila que ya existe.
- **Q7 → D360 (evento).** ¿Tipo `estado_cambiado` (ya en la lista de `04`) con `antes` `{"estado": anterior}` y `despues` `{"estado": nuevo}`, `motivo` vacío, actor el usuario del token, en la misma transacción, y nada ante un rechazo; sin `EventoPaciente` por `es_nuevo`? **Recomendación: sí, aceptada** (W7): C-19 reusa el mismo tipo para la corrección.
- **Q8 → D361 (`es_nuevo`).** ¿Columna `paciente.es_nuevo` `boolean NOT NULL DEFAULT true` en la migración `0010`, con relleno a `false` de los pacientes que ya tengan un turno `atendido`, conservando el `server_default`; pasa a `false` con el `atendido` en la misma transacción, `ausente` no la toca, y no se expone por la API hasta C-20/C-27? **Recomendación: sí, aceptada** (W8).
- **Q9 → D362 (concurrencia).** ¿Bloqueo de fila del turno (`turno_para_cambiar`), sin bloquear el paciente, con la prueba de concurrencia (`ASI-1e`: dos marcados; marcado contra cancelación) **solo** en el perfil `postgres`? **Recomendación: sí, aceptada** (W10), como D348.
- **Q10 → D363 (la pantalla).** ¿Botón «Asistencia» **primero** en la fila, solo en `reservado` y `confirmado` y **también en turnos que todavía no empezaron** (la API responde `RN-AG-13`); panel lateral «Registrar asistencia» con el resumen, «¿Cómo terminó el turno?» con «Atendido» y «Ausente» **sin opción marcada**, «El horario queda libre para otro turno.», «Volver» y «Registrar asistencia» (primario); frena sin opción con «Elegí si el paciente fue atendido o estuvo ausente.»; con `200`, «Asistencia registrada.» y la recarga del mismo día; los textos de la tabla del spec con «El turno no cambió.»; un solo panel entre los cinco; los botones de la fila con salto de línea cuando no entran? **Recomendación: sí, aceptada** (W11 a W13). Alternativas: ocultar «Asistencia» en los turnos futuros según el reloj del navegador (contra D323), o dos botones directos «Atendido» / «Ausente» en la fila (cinco botones y sin confirmación).
- **Q11 → D364 (el historial).** ¿«Cambio de estado» como título del `estado_cambiado` con una línea «Estado: {antes} → {después}» con las etiquetas de la agenda (por ejemplo, «Estado: Reservado → Atendido»), que no se muestra si falta un estado conocido? **Recomendación: sí, aceptada** (W12): un título genérico sirve también para la corrección de C-19. Alternativa: «Asistencia registrada», más específico pero que C-19 tendría que cambiar.
- **Q12 → D365 (tamaño).** ¿**22 escenarios nuevos o cambiados** (12 de la API, 6 de la pantalla, 2 modificados del historial y 2 nuevos de la migración; los cuatro archivos suman 34 con los repetidos) y **34 tareas en 13 grupos**, por encima del «3 a 6» y de «alrededor de 20» de `config.yaml`, como excepción limitada a C-18 con el criterio de D341 y D353? **Aceptada (D365), con H1 y H4**: quedan **24 escenarios nuevos o cambiados** (13 de la API con `ASI-1f`, 6 de la pantalla, 2 del historial, 1 de cancelación, `CAN-4c`, y 2 de la migración; los cinco archivos suman 38 con los repetidos) y las mismas **34 tareas en 13 grupos**. **Recomendación: sí**: la API sola cubre seis criterios de aceptación, la concurrencia, el evento, `es_nuevo` y el acceso, y partir el change dejaría la acción sin API o la columna sin uso.
