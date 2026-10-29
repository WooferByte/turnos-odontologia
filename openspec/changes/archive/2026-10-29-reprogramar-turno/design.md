# Design: reprogramar-turno

Fecha del design: **2026-10-29**. Change **C-16** (US-012; escenarios mínimos US-012 CA-1, CA-2, CA-4 y REP-1 de `CHANGES.md`). Gobernanza **MEDIO** (`CHANGES.md` C-16): se implementa con checkpoints y las decisiones no obvias se le presentan al autor antes del Apply. Motivación y alcance en `proposal.md`; el comportamiento, en `specs/reprogramacion-de-turnos/spec.md` (15 escenarios), `specs/pantalla-de-reprogramacion/spec.md` (8) y el delta de `specs/pantalla-de-historial/spec.md` (dos requisitos MODIFIED con cuatro escenarios: `HIS-2b` y `HIS-2f` cambian; `HIS-2a` y `HIS-2c` son copia literal de C-15, porque un MODIFIED repite el requisito completo).

Las decisiones se numeran **M1 a M17** («M» por «mover», la letra libre más cercana, para no confundirlas con las D1..D342 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores: D de C-01, I de C-02, H de C-03 y C-12, P de C-04, S de C-05, J de C-06, R de C-07, F de C-08, U de C-09, T de C-11, B de C-13, L de C-49, K de C-10, Y de C-50, A de C-14, G de C-15). Cada una dice si es **Decisión del autor** (tomada en la KB), **Propuesta** (elección de este design sin pregunta propia) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»). **Las preguntas Q1 a Q11 están cerradas** (sección final): el autor aceptó el 2026-10-29 todas las recomendaciones, con dos precisiones (Q9: «Antes:» y «Después:» llevan también la duración; Q11: la corrección queda escrita en la entrada C-17 de `CHANGES.md`), y todos los hallazgos del informe de `revisor-de-escenarios` (H1 a H11); quedaron registradas como **D332 a D342** en `knowledge-base/10_preguntas_abiertas.md`.

## Context

**Lo que ya existe** (leído del código y de los specs, no supuesto):

- **Alta de un turno** (`application/crear_turno.py`, C-01 a C-13): validación de entrada toda junta (`exigir_utc` y referencias, `EntradaInvalida`), después `Intervalo.para_turno` (RN-AG-02 y RN-AG-10d), `exigir_dentro_del_horario` (RN-AG-04, C-12), `uow.bloqueos.que_intersecan` + `exigir_sin_bloqueos` (RN-AG-04b, C-13), `uow.agenda.bloquear_recursos` (profesional y después sillón, `FOR NO KEY UPDATE`, D157), `ocupados_en_el_intervalo` (una sentencia, cualquier estado) y `detectar_conflictos` (activos, un `Conflicto` por recurso con el que empieza primero, D129). El turno y su evento `creado` van en el mismo `with uow:`. Ante `SolapamientoEnLaBase` (23P01 o 40P01 traducidos en `RepositorioAgendaSqlAlchemy.agregar`) reintenta hasta `INTENTOS_ANTE_CARRERA = 3`.
- **Errores** (`domain/errors.py`, `api/errores.py`): `DuracionInvalida` (`RN-AG-01`, de entrada, dentro de `EntradaInvalida`, `422` con error de campo; D176), `FechaNoUTC` (`RN-GL-01`), `IntervaloInvalido` (`RN-AG-10d`, `422`), `FueraDeHorario` (`RN-AG-04`, `422`), `SobreBloqueo` (`RN-AG-04b`, `422`), `ErrorDeSolapamiento` (`409` con `codigos` y `conflictos`), `TurnoNoEncontrado` (`404` `RN-GL-04`). `duracion_valida` y `GRANULARIDAD_MINUTOS = 5` en `domain/agenda/prestaciones.py`.
- **Historial** (C-03): `EventoTurno` y `TipoEvento` con un solo valor, `creado`; `evento_creado` es puro; `RepositorioHistorial.registrar`; `evento_turno.tipo` sin `CHECK` (design H6), así que un tipo nuevo no necesita migración. La tabla es de solo inserción (disparador en PostgreSQL, D158).
- **Lectura de la agenda** (C-14): `GET /turnos/{id}` con `turnos.leer`, `404` para uno inexistente o de otro consultorio (D321), consultorio del usuario del token (D270).
- **Permisos** (`domain/acceso/roles.py`): 16 permisos; `TURNOS_CREAR` para odontólogo y recepcionista; `tests/unit/test_roles.py` cuenta `16 * 3`.
- **Turno** (`TurnoModelo`): sin `actualizado_en` ni `version` (`CHANGES.md` los prevé «cuando su design los necesite»); `CHECK inicio < fin` y `duracion_minutos > 0`; la restricción de exclusión de PostgreSQL (D145) también vale para un `UPDATE`.
- **Frontend** (C-14, C-15): `PaginaAgenda` con un estado `panel` (`ninguno` | `nuevo-turno` | `historial`), `TablaDeTurnos` con la columna «Acciones» y el botón «Historial», `PanelNuevoTurno` (fecha y hora del consultorio, `aUtc`, «Termina a las…»), `mensajes.ts` con los textos de los rechazos de `POST /turnos`, `features/historial/mensajes.ts` (`tituloDelEvento` con «Cambio registrado ({tipo})» para lo desconocido). `IconoCalendario` ya existe. El servidor falso no responde `PATCH /api/turnos/{id}`.
- **Hallazgo**: el frontend lista el estado `cancelado_consultorio` (`apiAgenda.ts`, `mensajes.ts`, un test de la agenda), pero la API y la KB usan `cancelado_profesional`; hoy no se nota porque nada crea turnos cancelados por el consultorio. Lo corrige C-17 (D342); hasta entonces los escenarios de la pantalla no usan ese estado.

## Goals / Non-Goals

**Goals:**

- Mover un turno o cambiarle la duración desde el panel, sobre el mismo registro, con las mismas reglas y el mismo orden que el alta, sin duplicar su código.
- Que dos escrituras simultáneas nunca dejen dos turnos activos en el mismo hueco ni un historial con un `antes` que no fue cierto.
- Que la agenda lo haga sin pantalla nueva, con un panel como los de C-14 y C-15, y que el historial lo muestre con su etiqueta.

**Non-Goals:**

- Control de versión optimista (`version`, `If-Match`) ni columna `actualizado_en` (M7).
- Cambiar paciente, prestación, profesional o sillón; un motivo escrito; avisar al paciente; ofrecer el hueco liberado (proposal, «Fuera de alcance»).
- Validar la duración en el navegador (como D232) ni evaluar reglas de agenda en la pantalla.
- Refactorizar `crear_turno` más allá de extraer lo que las dos operaciones comparten (M5).
- El vencimiento efectivo de un `pendiente_sena` (RN-GL-05 (a), RN-AG-10): reprogramar sobre el horario de un `pendiente_sena` con la seña vencida no persiste ese vencimiento, porque en la v1 todavía no hay seña ni plazo; llega con el change de la seña (C-37). Hasta entonces el solapamiento usa el estado almacenado (D317).
- Corregir `cancelado_consultorio` en el frontend (D342, C-17).
- Ponerle a la duración de las **prestaciones** el tope de 1440 minutos: es un límite conocido de C-04 que queda para un change futuro (D333).

## Decisions

### M1. Capabilities — Decisión del autor (D332)

Dos capabilities nuevas, `reprogramacion-de-turnos` (API) y `pantalla-de-reprogramacion` (interfaz), más un delta MODIFIED en `pantalla-de-historial`. El evento `reprogramado` se especifica en `reprogramacion-de-turnos`, donde nace (como `creado` nació con el alta), y no como delta de `historial-de-turnos`, cuyos requisitos no cambian. **Alternativas descartadas**: una sola capability con API y pantalla (mezcla contratos que se prueban con suites distintas); agregar los requisitos a `creacion-de-turnos` y `pantalla-de-agenda` (crecen dos specs ajenos); dejar el historial sin etiqueta (C-15 dejó escrito, en G5, que el change que agrega el tipo le pone su etiqueta y su escenario, y `HIS-2b` usa `reprogramado` como ejemplo de tipo desconocido: quedaría falso). **Excepción** a «una sola capability» (`config.yaml`, regla dura 12), limitada a C-16, con el mismo corte API / navegador de D241, D255, D271, D290, D304 y D315 (D332). El delta MODIFIED de `pantalla-de-historial` lleva **dos requisitos**: el de la etiqueta del evento y el de «un solo panel lateral a la vez», que ahora nombra los tres paneles («Nuevo turno», «Historial» y «Reprogramar»), así después del archive el spec principal del historial no contradice a `REP-6c` (hallazgo H5).

### M2. Contrato de `PATCH /turnos/{id}` — Decisión del autor (D333)

- Cuerpo `ReprogramarTurnoEntrada` (Pydantic, `extra="forbid"`, base `EntradaDeEdicion` de C-04 para rechazar el `null` explícito): `inicio: datetime | None` y `duracion_minutos: int | None`, los dos opcionales. Un campo omitido conserva el valor del turno; la duración que se conserva es la **del turno**, no la actual de su prestación (RN-AG-02, US-001 CA-3).
- `duracion_minutos` mayor que 0, múltiplo de 5 y **como máximo 1440** (24 horas): por encima es `RN-AG-01`, validación de entrada, junto con las otras dos condiciones (hallazgo H3). El tope se evalúa en el dominio antes de calcular `fin`, así una duración desmedida (por ejemplo, 1000000000) nunca termina en un `OverflowError` de `timedelta` ni en un entero que la base no guarda (un `500`; precedente D322). Vive en `domain/turnos/reprogramacion.py` (`DURACION_MAXIMA_DEL_TURNO_MINUTOS = 1440` y `exigir_duracion_del_turno`, que usa `duracion_valida` de C-04 y suma el tope) y **no** cambia `duracion_valida`: las prestaciones no tienen tope (límite conocido de C-04, anotado en `05` RN-AG-01 y en `10`; lo corrige un change futuro). Con 1440 el turno siempre cruza la medianoche del consultorio, así que la respuesta es `RN-AG-10d`: el tope solo separa la entrada desmedida de la regla de negocio.
- Respuesta `200` con `TurnoSalida`, la misma forma que `201` de `POST /turnos`.
- Una petición que **no cambia nada** (`{}`, o `inicio` y duración iguales a los del turno) responde `200` con el turno sin evaluar reglas de negocio (tampoco `RN-AG-18`) ni registrar evento: como `PATCH /sillones/{id}` con `{}` (C-05). Vale también para un turno terminal (`REP-5b`, hallazgo H2). «Igual» compara instantes (el `inicio` en UTC) y la duración entera. Así reenviar el mismo pedido no falla por un bloqueo creado después del turno (D83) ni ensucia el historial.
- **Alternativas descartadas**: `inicio` obligatorio (obliga a reenviar el horario para cambiar solo la duración); `POST /turnos/{id}/reprogramar` (la ruta de `02` ya es `PATCH /turnos/{id}`); `422` para el cuerpo vacío (contradice C-05).

### M3. Estados y momento — Decisión del autor (D334; aplica D65)

Solo se reprograman los turnos **activos** (`ESTADOS_ACTIVOS`). Un turno terminal se rechaza con un código nuevo, **`RN-AG-18`** («el turno no se puede reprogramar en su estado»), `409` (es el estado actual del recurso, como `RN-AU-06` y `RN-AU-10`), con `type` `/errores/turno-no-reprogramable`. `RN-AG-18` es **específico de la reprogramación desde el panel**: `RN-AG-12` sigue siendo el código genérico de una transición de estado inválida y `RN-TD-11` el del token de gestión; quedó escrito así en `05`. Reprogramar no cambia el estado. El panel puede reprogramar **en cualquier momento** (D65): no se rechaza un turno ya pasado ni un `inicio` nuevo en el pasado (el alta desde el panel tampoco lo hace; RN-TD-01 y RN-TD-02 son de la reserva online). Tampoco se exige que el profesional, el sillón o la prestación del turno sigan activos: no son referencias del cuerpo (RN-GL-04), el turno ya los ocupa y desactivarlos «no modifica los turnos existentes» (RN-AG-07, US-001 CA-3, D184). **Alternativas descartadas**: reusar `RN-AG-12` («transición de estado inválida»; reprogramar no es una transición, `04` lo dice explícitamente); reusar `RN-TD-11` (es del token de gestión, D89); permitir reprogramar `atendido`/`ausente` (corregiría el pasado sin dejar claro qué pasó).

### M4. Clases de rechazo y orden de evaluación — Decisión del autor (D335; aplica RN-GL-02, D135, D208, D166)

1. **Acceso**: `401` sin sesión válida; `403` `RN-AU-05` sin `turnos.reprogramar` (D208).
2. **Formato** (Pydantic): `422` sin código (id no entero, campo de más, `null`, tipo erróneo).
3. **Turno de la URL**: `404` `RN-GL-04` si no existe o es de otro consultorio (D166, D321), como `editar_prestacion` hace antes de validar la duración.
4. **Validación de entrada, toda junta**: `RN-GL-01` (`inicio` sin zona UTC) y `RN-AG-01` (duración: mayor que 0, múltiplo de 5 y hasta 1440) en un único `422` (`EntradaInvalida`).
5. **Sin cambios** → `200` (M2), también si el turno es terminal (`REP-5b`).
6. **Reglas de negocio, de a una**: `RN-AG-18` (estado) → `RN-AG-10d` → `RN-AG-04` → `RN-AG-04b` → solapamiento (`RN-AG-05` y `RN-AG-08` juntos, D139), igual que el alta (D280).

El estado va después de la entrada porque es una regla de negocio (solo con entrada válida). Este orden quedó escrito en `05` RN-GL-02 («Orden de evaluación de `PATCH /turnos/{id}`»), junto con el «sin cambios → `200`» (hallazgo H1). **Alternativas descartadas**: estado antes de la entrada (daría `409` a una petición mal formada); `RN-AG-18` antes del «sin cambios» (un reenvío idéntico sobre un turno que ya terminó daría `409` sin que nadie pidiera un cambio).

### M5. Reuso del alta — Propuesta

Se extrae de `_intentar_crear_turno` una función de aplicación privada que evalúa las reglas del horario de un candidato (`Intervalo.para_turno`, horario, bloqueos, `bloquear_recursos`, ocupados y `detectar_conflictos`), con un parámetro `excluir_turno_id: int | None`. `crear_turno` la llama con `None` (REFACTOR que no cambia ningún test de `creacion-de-turnos`); `reprogramar_turno` con el id del turno. El filtro de RN-AG-10b es **dominio puro**: `detectar_conflictos(..., excluir_turno_id=None)` descarta los ocupados con ese id antes de buscar choques (test unitario sin base). **Alternativa descartada**: copiar la secuencia en `reprogramar_turno` (dos órdenes que pueden divergir) o filtrar en el repositorio (la regla quedaría fuera del dominio, regla dura 3).

### M6. Caso de uso y repositorio — Propuesta

`application/reprogramar_turno.py`: `ReprogramarTurnoComando(turno_id, inicio | None, duracion_minutos | None)` y `reprogramar_turno(comando, usuario_id, uow, reloj, *, actor)`. Dentro de un `with uow:`: lee el consultorio del usuario (D270); lee el turno **con bloqueo de fila** (`uow.agenda.turno_para_reprogramar(id)`, `SELECT … FOR NO KEY UPDATE`, que SQLite omite); `404` si no existe o es de otro consultorio; valida la entrada; decide «sin cambios»; aplica `exigir_reprogramable(estado)` (dominio, `domain/turnos/reprogramacion.py`); evalúa las reglas (M5) con el profesional y el sillón del turno; guarda con `uow.agenda.reprogramar(turno_id, inicio, fin, duracion)` (un `UPDATE` con `flush`, que traduce 23P01 y 40P01 a `SolapamientoEnLaBase` como `agregar`); y registra `evento_reprogramado(antes, despues, actor, reloj())`. Ante `SolapamientoEnLaBase` reintenta con el mismo `INTENTOS_ANTE_CARRERA`.

### M7. Concurrencia — Decisión del autor (D337; aplica D142 a D157)

- **Orden de bloqueos**: primero la fila del turno, después profesional y sillón (`bloquear_recursos`, el mismo orden fijo que el alta). El alta no bloquea filas de `turno`, así que no hay ciclo con ella; dos reprogramaciones de turnos distintos toman cada una su turno y después esperan por el mismo profesional; dos del **mismo** turno se serializan en su fila, y la segunda lee el horario que dejó la primera (su `antes` encadena, `REP-1e`).
- **Última defensa**: la restricción de exclusión de PostgreSQL vale para el `UPDATE`; si el dominio y la base no coinciden tras los reintentos, `SolapamientoEnLaBase` sube sin traducir (como el alta).
- **Sin `version` ni `actualizado_en`, sin migración**: el bloqueo de fila evita la escritura perdida dentro de la API, el historial ya dice cuándo cambió y quién, y una reprogramación hecha sobre una agenda vieja es una decisión válida de quien la hace (la agenda se recarga después). **Alternativa descartada**: `version` con `If-Match` y `412` (migración, cabecera nueva en el cliente y un rechazo más para la pantalla, sin pedido de la KB).
- **Prueba**: `tests/postgres/test_reprogramaciones_simultaneas.py` con el patrón de `carrera.py` (barrera y dos hilos), las tres corridas de `REP-1e`. **Corre solo en el perfil `postgres`** (marcador `postgres`, con Docker), nunca en la suite por defecto: SQLite no puede probarlo (DD-03) y la suite por defecto corre sin Docker (regla dura 6).

### M8. El evento `reprogramado` — Decisión del autor (D338; aplica DD-05, D159, D163, D209)

`TipoEvento.REPROGRAMADO = "reprogramado"` y `evento_reprogramado(antes: Turno, despues: Turno, actor, ocurrido_en)` puro en `domain/turnos/eventos.py`: `antes` y `despues` con `inicio`, `fin` (`a_texto_utc`) y `duracion_minutos`, que es lo único que puede cambiar; `motivo` `None`; `ocurrido_en` el reloj inyectado (el turno no tiene `actualizado_en`). El actor es el usuario del token (`Actor(USUARIO, str(id))`). Va en el mismo `with uow:` que el `UPDATE`: o quedan los dos o ninguno (`REP-2b`). Se registra **solo cuando algo cambia**: un rechazo y una petición sin cambios no registran nada (`REP-2b`, `REP-4c`, `REP-5b`), con test en la integración y en la API. **Alternativa descartada**: la foto completa del turno en `antes`/`despues` (repite ids que no cambian y obliga a la pantalla a buscar la diferencia).

### M9. Permiso — Decisión del autor (D336)

`Permiso.TURNOS_REPROGRAMAR = "turnos.reprogramar"` con `_ODONTOLOGO_Y_RECEPCION` (matriz de `03`, fila Turnos: «CRUD» y «CRU + cancelar», el dueño «R»). El dueño y un usuario sin roles reciben `403` con `RN-AU-05` (`05`, «un endpoint con rol insuficiente devuelve `403`»). El contador de `test_roles.py` pasa a `17 * 3` y el guard de rutas protegidas encuentra la ruta nueva. El permiso quedó escrito en `03`. **Alternativa descartada**: reusar `turnos.crear` (mezcla dos acciones que C-17 a C-19 también van a separar: cancelar, marcar; un permiso por acción es lo que hicieron C-04 a C-14).

### M10. Clases de rechazo de la pantalla — Decisión del autor (D323, D339)

La pantalla no evalúa reglas: decide el texto por el tipo de error y el código (tabla del spec), nunca por el `detail`. Lo que frena sin pedir nada no son reglas de agenda: campos vacíos o una duración que no es un entero sin signo (no hay número que mandar) y una petición sin cambios (M2: la API respondería `200` sin hacer nada, y «Turno reprogramado.» engañaría). La duración `0` o `42` sí se manda y la rechaza la API con `RN-AG-01` (como D232 en prestaciones). Cada rechazo suma «El turno no cambió.» porque, a diferencia del alta, el turno ya existe y el usuario necesita saber que quedó como estaba (tomado de Stitch).

### M11. Estructura del frontend — Decisión del autor (D339, D340) + Propuesta (detalle; aplica A9, G8 y `vercel-react-best-practices`)

- `apiAgenda.ts`: `reprogramarTurno(id, { inicio, duracion_minutos })` con `PATCH /api/turnos/{id}`, validando el `200` sin `any` (la forma de `TurnoCreado`); los rechazos los traduce `traducirRechazo` como hoy.
- `mensajes.ts` de la agenda: `mensajeDeReprogramacion(error)` reusando los textos de `mensajeDeCreacion` para los códigos compartidos, más `RN-AG-01`, `RN-AG-18`, el `404` y el `403` propios, y las constantes «Turno reprogramado.», «El turno no cambió.», «Completá fecha, hora y duración.» y «No cambiaste la fecha, la hora ni la duración.».
- `PanelReprogramar.tsx` (componente de nivel superior): estado local de los tres campos, «Termina a las…» derivado en el render (reusa `horaDeFin` de `PanelNuevoTurno`, que pasa a un módulo compartido de la agenda: REFACTOR sin cambio de comportamiento).
- `TablaDeTurnos.tsx`: `onReprogramar(turno)`; el botón solo si `ESTADOS_ACTIVOS_DEL_TURNO.includes(turno.estado)` (lista en `apiAgenda.ts`, la de RN-AG-10), con ternario, así que **ningún estado no activo** lo tiene (`REP-6c` lo prueba con `cancelado_paciente`, `atendido`, `ausente` y `vencido`; `cancelado_profesional` entra cuando C-17 corrija el nombre, D342); la fila seleccionada (`fila-seleccionada`) también para el panel de reprogramar.
- `PaginaAgenda.tsx`: `Panel` suma `{ tipo: 'reprogramar'; turno }`; un solo panel a la vez; `ir()` cierra también este panel; `reprogramar()` con la misma guarda `enCurso` y la misma recarga del día local del nuevo inicio que `crear()` (si la recarga falla, «Turno reprogramado.» y el aviso de conexión con «Reintentar», como el alta; `REP-6d`); `ir()` cierra también este panel; el foco vuelve al botón «Reprogramar» de la fila al cerrar con «Cancelar» o «Cerrar» (como G9), con test (`REP-6a`, `REP-6c`; hallazgo H4).
- `features/historial/mensajes.ts`: `tituloDelEvento('reprogramado')` → «Turno reprogramado» y `detalleDelReprogramado(evento, zona)` → las líneas «Antes: {día}, {hh:mm} – {hh:mm} ({n} min)» y «Después: …», con el día completo aunque no cambie (D340; por ejemplo «Antes: lunes 2 de noviembre de 2026, 09:00 – 09:30 (30 min)»), o ninguna si `antes` o `despues` no traen `inicio` y `fin` de texto y `duracion_minutos` entero.

### M12. Interacción y anchos angostos — Decisión del autor (D339; sale de las pantallas de Stitch)

En escritorio el panel va al costado de la agenda (unos 420 px), como «Nuevo turno» e «Historial». Debajo de 720 px va a todo el ancho debajo de la barra, con «Reprogramar» y «Cancelar» a todo el ancho; en las tarjetas de la agenda angosta los dos botones van al pie de cada tarjeta. Al abrir, el foco va al campo «Fecha»; al cerrar con «Cancelar» o «Cerrar», vuelve al botón «Reprogramar» de la fila. El foco y la fila seleccionada tienen escenario y test (`REP-6a`, `REP-6c`).

### M13. Servidor falso y tests — Decisión del autor (D222, D227; reglas duras 6 y 8) + Propuesta (detalle)

`servidorFalso.ts` suma `PATCH /api/turnos/{id}` con tres comportamientos mínimos: `404` `RN-GL-04` si el turno no está; `409` `RN-AG-05` y `RN-AG-08` si el horario nuevo choca con otro turno activo de la lista (excluyéndose); y, si no, `200` con el turno movido (y lo guarda, así la agenda recargada lo muestra). Los demás rechazos salen de una opción `responderAlReprogramar(estado, codigos)` de una sola vez, como `responderAlCrear`. Respeta `retener`, `caerse`, `vencerAccess`, `invalidarRefresh`, `quitarPermiso` y `fallarRuta` (con `fallarRuta` sobre `GET /api/turnos` después del `PATCH` se prueba `REP-6d`), cuenta las peticiones y guarda el cuerpo del último `PATCH`. Los turnos de prueba en estados no activos usan los nombres de estado que el frontend conoce hoy (D342). Ningún test anterior cambia lo que verifica. Backend: tokens reales en los tests de API (D211), reloj fijo inyectado, SQLite en memoria; la fábrica de tests ya carga un horario de 00:00 a 23:59 (D263), así que los escenarios que dependen del horario de 08:00 a 20:00 lo cargan explícitamente.

### M14. Versiones y dependencias — Propuesta

No se agrega ni cambia ningún paquete: ni `backend/pyproject.toml` ni `frontend/package.json` ni `package-lock.json`. La política de pins (D133) no aplica porque no se elige ninguna versión.

### M15. Demo y README — Propuesta

Sin datos nuevos de seed. El README suma `PATCH /turnos/{id}` en «Probar desde Swagger» (con la recepcionista: crear un turno el lunes 2 de noviembre de 2026, moverlo, cambiarle la duración, REP-1 contra otro turno, `RN-AG-01` con 42 y con 1445, `RN-AG-04` a las 07:30, el dueño con `403`, y su historial con el `reprogramado`), «Reprogramar un turno» en «Panel (interfaz)», las tablas escenario → test y los límites conocidos (sin control de versión; el dueño ve la acción, D312; la seña llega con C-40; las prestaciones todavía no tienen el tope de 1440 minutos, D333; un `inicio` del 31 de diciembre de 9999 desborda, como en el alta). Perfil `postgres`: la prueba nueva en la lista del README. **Sin guía en `docs/guias/`**: MEDIO, y la guía acumulada de la fase 4 va después del cuarto change archivado (C-16 es el tercero).

### M16. Prueba en el navegador — Decisión del autor (D234, `rules.tasks`) + Propuesta (detalle)

Con la demo (`crear_app_demo` y `npm run dev`): la recepcionista crea dos turnos el lunes 2 de noviembre de 2026, reprograma uno a otro horario (REP-6a), a otro día **dentro del horario de 08:00 a 20:00** y solo la duración (REP-6b; la corrida de las 22:00 que cruza la medianoche UTC queda solo en Vitest, porque la API real respondería `RN-AG-04`, hallazgo H8), lo intenta sobre el otro (REP-7a), con 42 minutos (`RN-AG-01`) y a las 07:30 (`RN-AG-04`); abre su historial y ve «Turno reprogramado» con «Antes:» y «Después:», cada una con su duración (D340); el dueño recibe `RN-AU-05` (REP-7d); en `/docs`, el mismo `PATCH`. Comparar con las dos capturas de Stitch a 1280 y 390 px, guardar las capturas de la implementación junto a las de Stitch y anotar las diferencias en la sección 4 de `stitch-reprogramar.md`. Consola sin errores ni datos sensibles; sin desplazamiento horizontal a 390 px. Después un recorrido breve en Compose (`http://127.0.0.1:5173`) para ver la CSP.

### M17. Skills aplicadas

- `fastapi-templates`: router → caso de uso → repositorio; `TurnoSalida` en la respuesta, nunca el modelo ORM; `Depends(requiere(...))`; `def` síncrono.
- `python-design-patterns`: reglas puras en `domain/` (`exigir_reprogramable`, `evento_reprogramado`, el filtro de RN-AG-10b); una sola secuencia de reglas compartida con el alta (M5).
- `python-error-handling`: `TurnoNoReprogramable` con su código; entrada junta, negocio de a una; acceso antes que validación.
- `python-testing-patterns`: AAA, `parametrize` para las causas, SQLite real, reloj inyectado, marcador `postgres` para la concurrencia.
- `supabase-postgres-best-practices` (solo verificar): orden de bloqueos fijo, transacción corta, la exclusión como última defensa.
- `vercel-react-best-practices`: sin pedidos en cascada (abrir el panel no pide nada), estado derivado en el render, componentes de nivel superior, ternarios en vez de `&&`.
- `revisor-de-escenarios`: se corre después de este propose y antes del Apply.

## Referencia visual (Stitch)

Pantallas generadas en este propose con el MCP `stitch`, proyecto `projects/14200813501064679723`, design system «Clinical Ops» (`assets/b683d44391ab410db2dd48aa71ed0b47`), modelo `GEMINI_3_8_FLASH`, cada una al primer intento. Pedidos, ids de archivos y revisión de datos en [`docs/skills-mcp/evidencias/sesion-nueva/stitch-reprogramar.md`](../../../docs/skills-mcp/evidencias/sesion-nueva/stitch-reprogramar.md).

| Pantalla | Id | Evidencia |
|---|---|---|
| Reprogramar turno con error (REP-1), escritorio | `projects/14200813501064679723/screens/291535f17cc64edc8c79e1ce09977c42` | `stitch-reprogramar-pantalla/reprogramar-escritorio.png` y `.html` |
| Reprogramar turno con `RN-AG-01` y el resultado, angosta | `projects/14200813501064679723/screens/6557792ea9754df08b59484784462c27` | `stitch-reprogramar-pantalla/reprogramar-angosta.png` y `.html` |

**Se toma**: el botón con borde «Reprogramar» con ícono de calendario antes de «Historial» en la columna «Acciones», y su ausencia en la fila cancelada; la fila del turno abierto resaltada (fondo celeste y franja izquierda); el panel lateral sin oscurecer la agenda, con el título con ícono de calendario, la X y el resumen en dos líneas («Ana Ejemplo · Consulta / control» y «Ahora: …»); la nota «Fecha y hora del consultorio.»; el aviso de error con ícono, el texto con los códigos y «El turno no cambió.» en una segunda línea; «Fecha» y «Hora» en una fila y «Duración (minutos)» debajo, con «Múltiplo de 5 minutos.» a la izquierda y «Termina a las…» a la derecha; el pie con «Cancelar» y «Reprogramar» primario; en angosto, los campos en una columna y los botones a todo el ancho; el aviso verde «Turno reprogramado.».

**Se rechaza** (la KB y el spec mandan sobre el contenido):

- Los códigos en negrita subrayada dentro del aviso: van entre paréntesis en el texto, como en la agenda (D323).
- El borde rojo en el campo «Hora» ante un solapamiento y en «Duración» ante `RN-AG-01`: la pantalla no sabe qué campo causó una regla de negocio y no valida la duración (M10); el aviso alcanza.
- El ícono de alerta dentro del campo de duración: mismo motivo.
- El bloque «Después de reprogramar» de la angosta: es una muestra; en la pantalla el panel se cierra y la agenda recargada muestra la fila.
- «Agenda sincronizada en tiempo real», «4 turnos agendados» en el pie y el pie institucional: no hay tiempo real en la v1 y C-14 y C-15 ya los rechazaron.

El HTML de Stitch (Tailwind y Google Fonts por CDN) **no se copia**: se traduce a `panel.css` y, si hace falta, a `tokens.css`, sin dependencias nuevas, sin CDN y con los íconos en SVG en línea (CSP `default-src 'self'`). Sin la comparación con estas capturas (M16), el change no se cierra (D234).

## Contradicciones y huecos encontrados en las fuentes

- **REP-1 no está en la KB**: lo define `CHANGES.md` («reprogramar sobre otro turno activo se rechaza con RN-AG-05 y RN-AG-08 y el turno no cambia»); el spec lo toma tal cual como `REP-1c` (API) y `REP-7a` (pantalla).
- **Qué estados se reprograman desde el panel**: la KB no lo fijaba. `04` dice que reprogramar no es un estado; RN-TD-08 (D77) solo lo permite con el token en `reservado` y `confirmado`; D65 dice que el consultorio puede reprogramar «en cualquier momento». Resuelto: «los activos», con el código nuevo `RN-AG-18` (D334).
- **RN-TD-04 nombra RN-TD-01 y RN-TD-02** («las mismas reglas que una reserva nueva»): son de la reserva online y RN-TD-03 dice que el panel puede reprogramar en cualquier momento (D65); para el panel no aplican (D334).
- **«Se valida como un turno nuevo»** (US-012 CA-1) podría leerse como volver a exigir que la prestación, el profesional y el sillón estén activos; RN-GL-04 habla de referencias del **cuerpo** y RN-AG-07 de turnos **nuevos**, así que no se exige (D334).
- **`cancelado_consultorio` en el frontend** contra `cancelado_profesional` en la API y en `04`: se corrige en C-17 (D342).
- **La duración sin tope**: RN-AG-01 no fijaba un máximo y una duración desmedida daba un `500`; D333 fija 1440 minutos para la duración del turno al reprogramar. La misma falta en las prestaciones de C-04 (archivado) queda como límite conocido en `05` y en `10`.

## Risks / Trade-offs

- [Extraer la secuencia de reglas del alta rompe algo de `creacion-de-turnos`] → La extracción es un REFACTOR con toda la suite en verde antes y después (tarea 3.4), y el perfil `postgres` de E11 se corre en la verificación final.
- [Interbloqueo entre una reprogramación y un alta] → El alta no bloquea filas de `turno`; las dos bloquean profesional y sillón en el mismo orden. Si PostgreSQL detecta un 40P01 igual, se traduce y se reintenta (M6). V3 lo comprueba.
- [Una reprogramación sobre una agenda vieja pisa la de otro usuario] → Aceptado (M7): el historial guarda las dos con su `antes` real; queda como límite conocido en el README.
- [El botón visible para el dueño] → D312, como «Nuevo turno»; el `403` se muestra con su texto.
- [Una cuarta columna de botones en la agenda angosta] → V1 revisa los tests de la agenda que cuentan botones; M12 los pone al pie de la tarjeta.
- [Un `inicio` cerca del año 9999 más la duración desborda `datetime` y daría un `500`] → Es el mismo límite que ya tiene `POST /turnos` (C-01) y ningún hallazgo lo pidió; queda como límite conocido del README, fuera de C-16 (regla dura 12). Con el tope de 1440 minutos solo lo alcanza un `inicio` del 31 de diciembre de 9999.

## A verificar en el change

- **V1** (antes de la tarea 8.2): qué tests de `pantalla-de-agenda` y `pantalla-de-historial` dependen de la cantidad de botones de la fila (`getAllByRole('button')`) o del orden de los botones; si alguno cambia, se ajusta solo su número.
- **V2** (antes de la tarea 3.2): que el `UPDATE` de SQLAlchemy sobre `TurnoModelo` dentro de la misma sesión que leyó el turno con `with_for_update(key_share=True)` emite en PostgreSQL `FOR NO KEY UPDATE` y que SQLite lo omite sin error (como en `bloquear_recursos`).
- **V3** (antes de la tarea 5.2): en el perfil `postgres`, que el `UPDATE` que viola la restricción de exclusión levanta 23P01 con el nombre de la restricción (`diag.constraint_name`) igual que el `INSERT`, para reusar la traducción de `agregar`.
- **V4** (antes de la tarea 12.1): en la demo, que el `PATCH` de la recepcionista deja en el historial `actor_id` `"2"` y que el panel del historial muestra «Turno reprogramado» con «Antes:» y «Después:».

## Migration Plan

Sin migraciones. La ruta nueva y el permiso nuevo se despliegan con la API; la acción, con el frontend. Volver atrás es revertir los commits del change: los eventos `reprogramado` ya registrados quedan en el historial (es de solo inserción) y la pantalla de C-15 los muestra como «Cambio registrado (reprogramado)».

## Notas para el archive

- Marcar C-16 con `[x]` en `CHANGES.md` y correr `python scripts/verificar_changes.py`.
- Registrar los resultados de V1 a V4 en `knowledge-base/10_preguntas_abiertas.md`, como «Cierre de C-16» después de la tabla de D332 a D342.
- Completar la sección 4 de `stitch-reprogramar.md` con la comparación.
- C-16 es el tercer change archivado de la fase 4: la guía acumulada va después del cuarto.

## Open Questions

**Cerradas el 2026-10-29.** El autor aceptó la recomendación de cada pregunta y quedaron como D332 a D342 en `knowledge-base/10_preguntas_abiertas.md`; el `/opsx:update` del mismo día ajustó los specs, las tareas y la KB.

- **Q1 → D332 (capabilities).** Sí: `reprogramacion-de-turnos` y `pantalla-de-reprogramacion` nuevas, más el delta MODIFIED de `pantalla-de-historial` (dos requisitos: la etiqueta del evento y un solo panel para los tres paneles, hallazgo H5), sin delta en `historial-de-turnos`; excepción a «una sola capability» limitada a C-16 (M1).
- **Q2 → D333 (contrato del `PATCH`).** Sí (M2), más el tope de 1440 minutos de la duración como `RN-AG-01` de entrada (hallazgo H3) y la petición sin cambios que responde `200` sin evento, también en un turno terminal (hallazgo H2).
- **Q3 → D334 (qué turnos y cuándo).** Sí (M3): solo los activos; `RN-AG-18` con `409` es **específico de la reprogramación** y `RN-AG-12` sigue siendo el código genérico de transición de estado; registrado en `05`.
- **Q4 → D335 (orden de evaluación).** Sí, tal como se propuso (M4); la línea quedó en `05` RN-GL-02 (hallazgo H1).
- **Q5 → D336 (permiso).** Sí (M9): `turnos.reprogramar` para el odontólogo y la recepcionista; `403` con `RN-AU-05` (`05`) para el dueño y el usuario sin roles.
- **Q6 → D337 (concurrencia).** Sí (M7): la prueba de concurrencia corre **solo** en el perfil `postgres`.
- **Q7 → D338 (el evento).** Sí (M8): el `reprogramado` se registra **solo** cuando algo cambia, con escenario y test.
- **Q8 → D339 (la pantalla).** Sí (M10 a M12), con escenario y test de que «Reprogramar» **no aparece** en los turnos no activos (`REP-6c`), del foco y la fila seleccionada (hallazgo H4) y de la recarga que falla después del `200` (`REP-6d`, hallazgo H9); en el navegador, `REP-6b` solo dentro del horario (hallazgo H8).
- **Q9 → D340 (el historial).** Sí, con una precisión del autor: «Antes:» y «Después:» llevan inicio, fin **y duración**, por ejemplo «Antes: lunes 2 de noviembre de 2026, 09:00 – 09:30 (30 min)» (M11).
- **Q10 → D341 (tamaño).** Sí: **25 escenarios nuevos o cambiados** (15 de la API, 8 de la pantalla y 2 modificados del historial, `HIS-2b` y `HIS-2f`; el delta repite además `HIS-2a` y `HIS-2c` de C-15 sin cambios, así que los tres archivos suman 27) y **32 tareas en 12 grupos**, por encima del «3 a 6» y de «alrededor de 20» de `config.yaml`, como excepción limitada a C-16 con el criterio de D300, D314 y D325 (hallazgos H6 y H11).
- **Q11 → D342 (`cancelado_consultorio`).** Sí, en C-17: la entrada C-17 de `CHANGES.md` lo dice en «Alcance — dentro» (`apiAgenda.ts`, `mensajes.ts` y el test de `PaginaAgenda`).
