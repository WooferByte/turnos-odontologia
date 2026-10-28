# Design: agenda-del-dia

Fecha del design: **2026-10-28**. Change **C-14** (US-011; escenarios mínimos US-011 CA-1, CA-2, E4 y E12 de `CHANGES.md`). Gobernanza **BAJO** (`CHANGES.md` C-14): autonomía completa si los tests pasan; las elecciones que dependían de una pregunta (Q1 a Q11) se confirmaron con el autor antes del Apply, como en C-50. Motivación y alcance en `proposal.md`; el comportamiento, en `specs/consulta-de-turnos/spec.md` (API, 11 escenarios) y `specs/pantalla-de-agenda/spec.md` (pantalla, 13 escenarios).

Las decisiones se numeran **A1 a A20** («A» de agenda) para no confundirlas con las D1..D325 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores (D de C-01, I de C-02, H de C-03, P de C-04, S de C-05, J de C-06, R de C-07, F de C-08, U de C-09, T de C-11, H de C-12, B de C-13, L de C-49, K de C-10, Y de C-50). Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»). **Las preguntas Q1 a Q11 están respondidas** (2026-10-28, «Sí, todo»): el autor aceptó la recomendación de todas y todos los hallazgos H1 a H11 de `revisor-de-escenarios` (`docs/skills-mcp/evidencias/sesion-nueva/revision-de-escenarios-agenda-del-dia.md`) con su corrección propuesta. Quedaron registradas como **D315 a D325** en `knowledge-base/10_preguntas_abiertas.md`; no crean códigos RN nuevos. Las decisiones A que dependían de una pregunta ahora citan su D («Decisión del autor (D316)»).

## Context

**Lo que ya existe** (leído del código y de los specs, no supuesto):

- **Crear turnos** (`application/crear_turno.py`, `api/routers/turnos.py`): `POST /turnos` con `requiere(Permiso.TURNOS_CREAR)` (odontólogo y recepcionista); validación de entrada toda junta (`RN-GL-01`, `RN-GL-04` con **todas** las referencias), después `RN-AG-10d`, `RN-AG-04`, `RN-AG-04b` y el solapamiento (`409` con `RN-AG-05` y/o `RN-AG-08`). El profesional y el sillón omitidos se resuelven al único activo (RN-AG-14). El router ya tiene `GET /turnos/{id}/historial` (C-03) con `TurnoNoEncontrado` (`404` `RN-GL-04`, D166), y `RecursoDeLaUrlNoEncontrado` como base (D188).
- **Datos**: `turno` (con índices por profesional e inicio y por sillón e inicio), `paciente` (`nombre`, `apellido`, `telefono_whatsapp`), `prestacion` (`nombre`, `color`, `activa`), `consultorio.zona_horaria`. El repositorio de la agenda tiene `existe_turno`, `zona_horaria` y `turnos_activos_que_intersecan`; **no hay** lectura de turnos por día ni de un turno con su paciente y su prestación. **No hay** `GET /pacientes` (es de C-20).
- **Seed de la demo**: consultorio 1 (`America/Argentina/Buenos_Aires`), profesional 1, sillón 1, prestaciones 1 a 5 con color, pacientes 1 a 3 («Ana Ejemplo», «Bruno Ficticio», «Carla Inventada»), horario lunes a viernes 09:00-13:00 y 15:00-19:00; ningún turno.
- **Permisos** (`domain/acceso/roles.py`): 15 permisos; `_TODOS` para leer catálogos; la matriz de `03` da «R» de turnos a los tres roles y «C» al odontólogo y a la recepcionista.
- **Hora del consultorio** en el frontend: `features/bloqueos/horaDelConsultorio.ts` (`aUtc`, `aLocal`, solo `Intl`, D285) y la zona viene de la API (`GET /bloqueos` devuelve `zona_horaria`).
- **Rechazos en el frontend** (`shared/api/rechazos.ts`): un `409` da `ReglaRechazada` con **un solo** código (el primero) y un `422` da `EntradaRechazada` con `codigos` y `errores`, **sin** las `referencias` del cuerpo. E4 necesita los dos códigos y E12 las referencias.
- **Servidor falso** (`test/servidorFalso.ts`): tiene `TurnoFalso` (solo para los turnos afectados de C-13), `retener`, `caerse`, `fallarRuta`, `vencerAccess`, `invalidarRefresh`, `quitarPermiso`; **no** responde `GET /api/turnos` ni `POST /api/turnos`.
- **Barra del panel** (`pages/PanelBase.tsx`): cinco enlaces (Prestaciones, Usuarios, Horario, Bloqueos, Mi contraseña), el indicador de C-50 y «Cerrar sesión»; `/panel` muestra `InicioDelPanel`.

## Goals / Non-Goals

**Goals:**

- Que el odontólogo y la recepcionista vean en una pantalla los turnos de un día del consultorio y den un turno sin salir de ella, con cada rechazo de la API visible con su código.
- Que «el día» sea siempre el del consultorio (RN-GL-01) y que lo calcule la API, no el navegador.
- Reusar `POST /turnos` tal como está y no exponer de los pacientes más que lo que la agenda muestra.
- Sin dependencias, migraciones ni variables nuevas.

**Non-Goals:**

- Acciones sobre un turno (C-15 a C-19, C-27, C-33): la tabla queda lista para sumar una columna, pero no la tiene.
- Buscar o listar pacientes (C-20), filtros por profesional o sillón (Fase 2), vista semanal, huecos libres.
- Paginar la agenda: un día de un consultorio chico tiene decenas de turnos, no miles.
- Ocultar «Nuevo turno» según el rol (D312).

## Decisions

### A1. Dos capabilities nuevas — Decisión del autor (D315; Q1; sigue D241, D255, D271, D290 y D304)

`consulta-de-turnos` (contrato de las dos rutas de lectura; pytest) y `pantalla-de-agenda` (navegador; Vitest), con el corte por suite que el autor ya aceptó cinco veces, cada vez limitado a su change; D315 lo acepta como excepción limitada a C-14. `creacion-de-turnos` no recibe delta: `POST /turnos` no cambia y leer es otro contrato; `proteccion-del-panel` ya exige el token a toda ruta nueva. Los nombres describen comportamientos durables: C-16 a C-19 sumarán sus requisitos a capabilities propias o a `pantalla-de-agenda` (las acciones en la agenda).

### A2. Estructura del backend — Propuesta (aplica `08`, «Estructura de directorios», y las reglas duras 3 y 5)

```
backend/app/domain/agenda/dia.py               rango_del_dia(fecha, zona) -> (inicio_utc, fin_utc); hoy_en(ahora_utc, zona) -> date
backend/app/domain/acceso/roles.py             Permiso.TURNOS_LEER = "turnos.leer" con _TODOS
backend/app/application/consultar_turnos.py    agenda_del_dia(fecha | None, usuario_id, uow, reloj) -> AgendaDelDia
                                               turno_de_la_agenda(turno_id, usuario_id, uow) -> TurnoDeLaAgenda
backend/app/application/puertos.py             RepositorioAgenda: turnos_del_dia(consultorio_id, desde, hasta), turno_de_la_agenda(turno_id)
backend/app/infrastructure/repositories/agenda.py   una consulta con join a paciente y prestacion, ORDER BY inicio, id
backend/app/api/esquemas.py                    TurnoDeLaAgendaSalida, AgendaDelDiaSalida
backend/app/api/routers/turnos.py              GET /turnos y GET /turnos/{turno_id}
```

`TurnoDeLaAgenda` es un tipo de lectura de la capa de aplicación (dataclass congelada con el turno y los datos del paciente y de la prestación), no una entidad del dominio. El consultorio sale del usuario del token (`uow.usuarios.obtener(usuario_id).consultorio_id`, D270), como en C-12 y C-13. Lectura pura: un solo `with uow:`, sin `commit()`.

### A3. El día del consultorio — Decisión del autor (D316, regla) + Propuesta (cálculo; RN-GL-01; regla dura 2)

La agenda del día es una excepción más de RN-GL-01, registrada en `05` (D316). `rango_del_dia(fecha, zona)` devuelve `[medianoche local de fecha, medianoche local de fecha + 1 día)` convertido a UTC, aware, con `zoneinfo` (biblioteca estándar, permitido en el dominio). `hoy_en(ahora_utc, zona)` es la fecha local de `ahora_utc`; el `ahora` sale del `utc_now()` inyectable (`get_reloj`), nunca de `datetime.now()`. El repositorio filtra `inicio >= desde AND inicio < hasta`: alcanza con el inicio porque un turno no puede cruzar la medianoche del consultorio (RN-AG-10d). Con horario de verano el día tendría 23 o 25 horas; el cálculo por medianoches locales lo cubre sin caso especial (lo prueba un test de dominio con una zona que lo tiene, por ejemplo `America/Santiago`).

### A4. Contrato de `GET /turnos` — Decisión del autor (D316; Q2; hallazgos H2 y H5)

- `fecha` opcional, de tipo fecha de calendario (`aaaa-mm-dd`, de `0001-01-02` a `9999-12-30`, D322). Sin `fecha`, el día de hoy del consultorio (A3). Así el navegador nunca calcula «hoy» y la pantalla puede pedir la agenda antes de conocer la zona.
- Respuesta `200`: `{"fecha": "aaaa-mm-dd", "zona_horaria": "...", "turnos": [...]}`, con `turnos` ordenado por `inicio` y luego `id` (desempate estable; escenario `AGE-1f`, hallazgo H2).
- **Lectura de US-011 CA-1** (hallazgo H5): «los turnos del profesional» son, en la v1, los del consultorio del usuario, porque hay un solo profesional (RN-AG-14); la lista no filtra por profesional hasta la agenda multi-profesional de la Fase 2. Quedó anotada en `06` §US-011.
- **Alternativas descartadas**: `fecha` obligatoria (`02` la escribía `GET /turnos?fecha`) y el navegador calcula hoy con la zona que traería otra ruta; o `desde` y `hasta` en UTC (más general, pero mueve al cliente el cálculo del día, que es una regla del consultorio).

### A5. Qué estados se listan — Decisión del autor (D317; Q3; hallazgo H10)

**Todos los estados**, con su etiqueta. La agenda es lo que pasó y lo que va a pasar en el día: un turno cancelado o ausente sigue siendo información para quien atiende, y C-17 a C-19 los van a producir desde esta misma pantalla. Hasta C-16 la API real solo crea `reservado`. **Se muestra el `estado` almacenado** (hallazgo H10): RN-GL-05 evalúa los vencimientos al consultar, pero no hay turnos `pendiente_sena` ni vencimientos hasta la seña (C-35); el change que los introduzca decide si la agenda muestra el estado efectivo. **Alternativa descartada**: solo los activos (RN-AG-10), con un filtro «Mostrar cancelados» más adelante.

### A6. Forma de un turno de la agenda y datos del paciente — Decisión del autor (D318; Q4; RN-PR-01)

`id`, `inicio`, `fin`, `duracion_minutos`, `estado`, `profesional_id`, `sillon_id`, `paciente` `{id, nombre, apellido}` y `prestacion` `{id, nombre, color}`. **No** van `telefono_whatsapp` ni ningún otro dato del paciente (minimización: la agenda solo muestra el nombre); tampoco `consultorio_id` ni `creado_en`, que la pantalla no usa. `prestacion` sale de la prestación aunque esté inactiva (el turno ya existe; US-001 CA-3). `GET /turnos/{id}` devuelve la misma forma, que C-15 a C-19 van a usar. **Alternativa**: solo ids y que la pantalla cruce con `GET /prestaciones` y con `GET /pacientes` (que no existe hasta C-20).

### A7. Permiso y consultorio — Decisión del autor (D321; Q7; sigue D298, D307 y D270)

`Permiso.TURNOS_LEER` con `_TODOS` en las dos rutas; un usuario sin roles recibe `403` `RN-AU-05`. Un turno de otro consultorio no aparece en la lista y su id da el mismo `404` `RN-GL-04` que uno inexistente (como D126 para las referencias del cuerpo): no se revela que existe. El test de la matriz pasa de `15 * 3` a `16 * 3` y el contador de rutas protegidas sube en 2 (solo cambia el número).

### A8. Clases de rechazo y orden de evaluación — Decisión del autor (RN-GL-02, D135, D208, D322; Q8; hallazgo H7)

| # | Clase | `GET /turnos` | `GET /turnos/{id}` |
|---|---|---|---|
| 1 | Control de acceso | `401` `RN-AU-03`; `403` `RN-AU-05` (sin roles) | igual |
| 2 | Validación de entrada | `fecha` que no es `aaaa-mm-dd`, o fuera de `0001-01-02` a `9999-12-30` → `422` con `codigos` vacío y el campo `fecha` en `errores` (el manejador de formato existente); un parámetro desconocido se ignora | id no entero → `422` con `codigos` vacío |
| 3 | Recurso de la URL | — | `404` `RN-GL-04` (`TurnoNoEncontrado`, inexistente o de otro consultorio) |
| 4 | Reglas de negocio | Ninguna | Ninguna |

`fecha` mal formada **no** usa `RN-GL-01`: ese código es de un instante sin zona o con desfase distinto de UTC, y `fecha` es un día de calendario del consultorio, que por definición no lleva zona. **Extremos del calendario** (hallazgo H7, D322): `rango_del_dia` suma un día y pasa a UTC, así que `9999-12-31` desbordaría `datetime` (y `0001-01-01`, en una zona al este de UTC) y daría un `500`; el borde de la API acepta `fecha` de `0001-01-02` a `9999-12-30` (por ejemplo, con los límites del tipo del parámetro) y fuera de ese rango responde el mismo `422` de formato. El dominio documenta ese rango como precondición y no trata el desborde. **Alternativas descartadas** (Q8): informar `RN-GL-01` en ese `422`; un `200` vacío para los extremos. Un detalle a cuidar: el manejador de formato dice «la ruta no tiene el formato esperado» cuando el error no viene del cuerpo; con un parámetro de consulta el texto es el mismo (el `detail` no es contrato). **A verificar en el change (V1, antes de la tarea 4.2)**: que FastAPI 0.115 valida `fecha: date | None` y rechaza `2026-11-02T03:00:00Z` (un `datetime` no es un `date` válido en Pydantic 2 en modo estricto de fecha); si lo aceptara truncando, se declara el parámetro con un patrón `^\d{4}-\d{2}-\d{2}$` y se anota.

No hay códigos RN nuevos ni clases nuevas en `api/errores.py`.

### A9. Estructura del frontend — Propuesta (aplica T de C-11, B14 de C-13)

```
frontend/src/features/agenda/apiAgenda.ts (+ .test.ts)      obtenerAgenda(pedido, fecha?) , crearTurno(pedido, nuevo), obtenerPrestacionesActivas(pedido)
frontend/src/features/agenda/PaginaAgenda.tsx (+ .test.tsx)  el día, la barra de fecha, la tabla y el panel
frontend/src/features/agenda/TablaDeTurnos.tsx              filas; en angosto, tarjetas (A14)
frontend/src/features/agenda/PanelNuevoTurno.tsx            el formulario y sus avisos
frontend/src/features/agenda/mensajes.ts (+ .test.ts)       etiquetas de estados, texto de cada rechazo, nombre del día
frontend/src/shared/horaDelConsultorio.ts                   horaLocal y fechaLocal nuevas (RED y GREEN), + aUtc y aLocal movidos desde features/bloqueos (REFACTOR)
frontend/src/shared/api/errores.ts, rechazos.ts             ReglaRechazada con codigos; EntradaRechazada con referencias (A12)
frontend/src/App.tsx, pages/PanelBase.tsx                   ruta /panel/agenda y enlace «Agenda» primero, con IconoAgenda (SVG en línea)
frontend/src/test/servidorFalso.ts                          GET y POST /api/turnos (A16)
frontend/src/shared/estilos/panel.css                       sección «Agenda» y su acomodo angosto
```

Las respuestas `2xx` se validan sin `any` (cada campo con su tipo, el estado entre los nueve conocidos; una respuesta de otra forma se trata como `SinConexion`, como C-13).

### A10. Cómo elige el formulario al paciente — Decisión del autor (D319; Q5)

Un campo numérico **«N.º de paciente»** con la ayuda «El número de ficha del paciente.», hasta que C-20 lo cambie por una búsqueda. El número que no existe vuelve como `RN-GL-04` (E12), que es justamente uno de los escenarios mínimos. **Alternativas**: (b) sumar ahora un `GET /pacientes` de solo lectura (invade C-20, que es ALTO y define filtros, campos y permisos de esa ruta); (c) un selector con los pacientes que ya aparecen en la agenda (no sirve para el primer turno de un paciente). Límite conocido en el README: los números de los pacientes de la demo (1 a 3).

### A11. Profesional y sillón — Decisión del autor (D320; Q6; RN-AG-14)

El formulario no los pide: el `POST` va sin `profesional_id` ni `sillon_id` y la API usa el único activo. Si hay más de uno activo (posible con la gestión de sillones de C-05), la API responde `422` `RN-GL-04` con «hay más de uno activo» y la pantalla lo muestra (A12). Elegir profesional o sillón es la agenda multi-recurso de la Fase 2. **Alternativa**: un selector de sillón con los activos de `GET /sillones` (C-05 ya permite tener varios); se descarta por alcance, y el README lo deja como límite.

### A12. Textos de la pantalla y de los rechazos — Decisión del autor (D323; Q9; hallazgos H6 y H8)

La pantalla decide por el **código**, nunca por el texto de la API.

Al **cargar o cambiar de día** (`GET /turnos`):

| Situación | Texto en la agenda |
|---|---|
| esperando la respuesta | «Cargando agenda…», sin filas |
| `200` sin turnos | «No hay turnos para este día.» dentro de la tarjeta de la tabla |
| sin conexión, `5xx` o una respuesta de otra forma | «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» **con «Reintentar»**, que repite el mismo pedido (es el único lugar con «Reintentar») |
| `403` `RN-AU-05` (usuario sin roles; hallazgo H8) | «Tu usuario no tiene permiso para ver la agenda (RN-AU-05).», sin tabla, sin «Reintentar» y sin tocar la sesión |
| `401` con el refresh vigente | se renueva una vez y se repite el pedido, sin aviso (`ingreso-al-panel`) |
| `401` irrenovable | `SesionTerminada`: vuelve a `/ingresar` (D231) |

En el **formulario**, con un campo vacío: «Completá paciente, prestación, fecha y hora.», sin mandar nada (hallazgo H6). Al **crear** (`POST /turnos`):

| Respuesta de `POST /turnos` | Texto en el panel |
|---|---|
| `409` `["RN-AG-05", "RN-AG-08"]` (E4) | «El profesional y el sillón ya tienen un turno activo en ese horario (RN-AG-05, RN-AG-08).» |
| `409` `["RN-AG-05"]` | «El profesional ya tiene un turno activo en ese horario (RN-AG-05).» |
| `409` `["RN-AG-08"]` | «El sillón ya tiene un turno activo en ese horario (RN-AG-08).» |
| `422` `["RN-AG-04"]` | «El turno no cae dentro del horario de atención del profesional (RN-AG-04).» |
| `422` `["RN-AG-04b"]` | «Ese horario está bloqueado (RN-AG-04b).» |
| `422` `["RN-AG-10d"]` | «El turno no puede pasar de la medianoche del consultorio (RN-AG-10d).» |
| `422` con `RN-GL-04` (E12) | «Hay datos que no existen o no están activos: <referencias> (RN-GL-04).»; cada referencia es «<recurso> <id> (<motivo>)», separadas por coma: recurso «paciente», «prestación», «profesional», «sillón»; motivo «no existe», «inactiva»/«inactivo» según el recurso, «no hay ninguno activo», «hay más de uno activo» (sin id cuando se omitió). Además vuelve a pedir `GET /prestaciones` |
| `422` con `RN-GL-01` | «La fecha y hora no es válida (RN-GL-01).» (no debería pasar: la pantalla manda UTC) |
| `422` con otro código o sin código | «Revisá los datos del turno.» |
| `403` `RN-AU-05` | «Tu usuario no tiene permiso para crear turnos (RN-AU-05).» |
| sin conexión, `5xx` | «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» (sin «Reintentar») |
| `401` con el refresh vigente | se renueva una vez y se repite el `POST` (el `401` llega antes de procesar nada, D208) |
| `401` irrenovable | `SesionTerminada`: vuelve a `/ingresar` (cableado de C-11, D231) |

Para esto `ReglaRechazada` suma `codigos` (todos, no solo el primero) y `EntradaRechazada` suma `referencias` (`recurso`, `recurso_id`, `motivo`), leídas sin `any` en `rechazos.ts`; `codigo` sigue siendo el primero, así ningún test de C-08 a C-13 cambia lo que verifica. Los textos de `RN-AG-05`/`RN-AG-08` repiten los del `detail` de la API (`api/errores.py`) para que Swagger y la pantalla digan lo mismo.

### A13. Interacción de la pantalla — Decisión del autor (D324, ruta; D323, textos; Q10) + Propuesta (detalle; aplica `vercel-react-best-practices`)

- **Ruta y enlace**: `/panel/agenda` con el enlace «Agenda» **primero** en la barra (es la pantalla diaria). `/panel` sigue mostrando `InicioDelPanel` (no se cambia a dónde lleva el login: es de `ingreso-al-panel`). **Alternativa descartada** (Q10): que `/panel` redirija a la agenda.
- **Día**: al abrir, `GET /turnos` sin `fecha`, con «Cargando agenda…» mientras llega (A12); la respuesta fija la fecha mostrada y la zona. «Día anterior» y «Día siguiente» suman o restan un día de calendario a la fecha mostrada (aritmética de fechas sin hora: no hace falta la zona; cruza fin de mes y de año, que la tarea 8.3 triangula, hallazgo H11); el selector de fecha nativo (`input type="date"`) pide ese día; «Hoy» vuelve a pedir sin `fecha`. Un pedido por cambio de día; si llegan fuera de orden, se muestra solo la respuesta del último pedido (bandera de vigencia por pedido). Si el pedido falla por conexión, «Reintentar» repite el mismo pedido (A12).
- **Nombre del día**: «lunes 2 de noviembre de 2026» con `Intl.DateTimeFormat('es-AR', { dateStyle: 'full', timeZone: 'UTC' })` sobre la fecha de calendario (la fecha ya es del consultorio). **A verificar en el change (V2, antes de la tarea 8.2)**: que jsdom y el Node 24 de los tests dan exactamente ese texto (ICU completo); si no, se arma con dos listas fijas de días y meses en `mensajes.ts`.
- **Hora de cada fila**: `inicio` y `fin` a «hh:mm» en la zona del consultorio (`shared/horaDelConsultorio.ts`), «09:00 – 09:30».
- **Color**: una franja a la izquierda de la fila y un punto antes del nombre de la prestación, con el `color` de la API como `style` en línea (es un dato, no un token); el texto no depende del color (accesible sin verlo).
- **Formulario**: panel lateral como el de C-11 (`PanelDePrestacion`), con «N.º de paciente» (`inputMode="numeric"`), «Prestación» (las activas de `GET /prestaciones`, pedidas al abrir el panel, «Consulta / control · 30 min»), «Fecha» (`type="date"`, el día mostrado) y «Hora» (`type="time"`, 24 h). Debajo, «Termina a las hh:mm.» calculado con la duración elegida (solo informativo: la API decide). Con un campo vacío, «Completá paciente, prestación, fecha y hora.» sin mandar nada (A12). «Crear turno» deshabilitado mientras espera; «Cancelar» y «Cerrar» lo cierran sin mandar nada. La fecha y la hora se pasan a UTC con la zona del consultorio (`aUtc`), así que las 22:00 del 3 de noviembre son `2026-11-04T01:00:00Z`. Con el `201`: «Turno creado.», se cierra el panel y se pide `GET /turnos?fecha=<fecha local del inicio>` (`fechaLocal`, la del consultorio y no la de UTC: `2026-11-03` en ese ejemplo; escenario `AGE-5h`, hallazgo H3).
- Sin `&&` para renderizar (ternarios), sin componentes definidos dentro de otros, sin *barrels*, sin `useEffect` para derivar estado.

### A14. Disposición y anchos angostos — Propuesta (sale de las pantallas de Stitch)

- Escritorio: encabezado con título, subtítulo con la zona y «Nuevo turno» a la derecha; tarjeta con la barra de fecha («Día anterior», selector, nombre del día, «Día siguiente», «Hoy» a la derecha); tarjeta con la tabla (HORA, PACIENTE, PRESTACIÓN, ESTADO), filas de 40 px, números tabulares, chips de estado; pie «N turnos». El panel «Nuevo turno» a la derecha, de unos 420 px, sobre la agenda atenuada.
- Debajo de 720 px (el corte de `panel.css`): «Nuevo turno» a ancho completo, barra de fecha compacta (flechas, «lun 02/11/2026», «Hoy») y cada turno como tarjeta (hora y chip arriba, paciente y prestación debajo), sin desplazamiento horizontal a 390 px; el panel ocupa el ancho de la pantalla.
- No se prueba en jsdom: se verifica en la prueba en el navegador a 1280 y 390 px (tarea 11.1).

### A15. Etiquetas y colores de los estados — Propuesta

«Pendiente de aprobación», «Pendiente de seña», «Reservado», «Confirmado», «Cancelado por el paciente», «Cancelado por el consultorio», «Vencido», «Atendido» y «Ausente». Chip celeste para `reservado`; verde para `confirmado` y `atendido`; ámbar para los dos pendientes; rojo suave para los dos cancelados, `vencido` y `ausente` (los cuatro chips del design system «Clinical Ops»). Una sola fuente en `features/agenda/mensajes.ts`.

### A16. Servidor falso y tests — Decisión del autor (D211, D222, D227; reglas duras 5 y 6) + Propuesta (detalle)

- **Backend**: dominio (`tests/unit/test_dia.py`: `rango_del_dia` y `hoy_en`, con `parametrize`, sin base), unidad de la matriz (`test_roles.py`), integración (`tests/integration/test_consultar_turnos.py`, con la base en memoria y el reloj fijo inyectado) y API (`tests/api/test_agenda.py`, tokens reales, turnos cargados con las fábricas existentes y estados puestos directamente en la base). Sin mocks de sesión ni de repositorio. Cada test lleva el ID de su escenario (`test_age1a_…`).
- **Frontend**: el falso suma la opción `hoy` (por defecto `2026-11-02`), `pacientes` (los tres de la demo) y amplía `TurnoFalso` con `prestacion_id` opcional (los tests de C-13 no cambian); responde `GET /api/turnos` (filtra por el día con UTC−3 fijo, ordena y arma `paciente` y `prestacion` desde su catálogo) y `POST /api/turnos` con **tres comportamientos mínimos**, sin copiar el dominio: referencias (paciente inexistente o prestación inactiva → `422` `RN-GL-04` con todas), solapamiento con un turno activo del mismo día (→ `409` con los dos códigos, porque el falso tiene un solo profesional y un solo sillón) y, si no, `201` `reservado`. Los demás rechazos (`RN-AG-05` solo, `RN-AG-08` solo, `RN-AG-04`, `RN-AG-04b`, `RN-AG-10d`, sin código) se fuerzan con un `responderAlCrear(estado, codigos)` de una sola vez. `retener`, `caerse`, `fallarRuta`, `quitarPermiso` (el `403` de la lectura en `AGE-4d` y el de crear en `AGE-5f`), `vencerAccess` (la renovación de `AGE-6a`) e `invalidarRefresh` se reusan. El falso no evalúa el horario del profesional, por eso `AGE-5h` (las 22:00) solo se verifica contra él. Vitest sin `vi.mock`, `vi.fn`, `vi.stubGlobal` ni temporizadores falsos.
- **A verificar en el change (V3, antes de la tarea 8.1)**: que sumar el enlace «Agenda» primero en la barra no cambia lo que verifican los tests de C-08 a C-50 que recorren la barra (por ejemplo, el orden de los enlaces o el primer enlace con `getAllByRole('link')`); si alguno depende del orden, se ajusta solo el índice y se anota.

### A17. Versiones y dependencias — Propuesta

**Sin dependencias nuevas** ni cambios de versión: `backend/pyproject.toml`, `frontend/package.json` y `package-lock.json` no cambian; no hay pins nuevos que fijar. `zoneinfo` y `tzdata` ya están (C-01, C-12).

### A18. Demo y README — Propuesta

- **Demo**: sin datos nuevos de seed (los pacientes 1 a 3 alcanzan). El recorrido crea los turnos por la pantalla o por `POST /turnos`.
- **README**: `GET /turnos` y `GET /turnos/{id}` en «Probar desde Swagger» (con la odontóloga, la recepcionista, sin `fecha`, con una fecha mal formada y con un id inexistente); la agenda en «Panel (interfaz)» (dar un turno al paciente 1, repetirlo para ver E4, el paciente 99 para E12, un sábado para `RN-AG-04`); la tabla escenario → test con la cantidad real; límites conocidos: el paciente se elige por número hasta C-20, sin selector de profesional ni de sillón (Fase 2), la agenda no se refresca sola, el dueño ve «Nuevo turno» y recibe `RN-AU-05` (D312).

### A19. Prueba en el navegador — Decisión del autor (D234, `rules.tasks`) + Propuesta (detalle)

El agente repite con la demo los escenarios de `pantalla-de-agenda` que no son solo del falso: abre la agenda (hoy vacía), cambia al lunes 2 de noviembre de 2026, da tres turnos (pacientes 1 a 3), repite uno para E4, usa el paciente 99 para E12, un sábado para `RN-AG-04`, un bloqueo creado en `/panel/bloqueos` para `RN-AG-04b`, entra como el dueño para `RN-AU-05` y como la recepcionista para crear; prueba las dos rutas en `/docs`; y después Compose con un recorrido breve. Compara con las tres capturas de Stitch a 1280 y 390 px y anota las diferencias en la evidencia. Le deja al autor el paso a paso. La repetición manual del autor es **opcional** (BAJO; `rules.tasks`), salvo que el agente no quede conforme; por eso **no** hay tarea de guía manual en `docs/guias/`.

### A20. Skills aplicadas

- `fastapi-templates`: router por recurso, esquemas de salida separados (nunca el modelo ORM), dependencias inyectadas (`get_uow`, `get_reloj`, `requiere`), handlers `def`. **No aplica** su parte asíncrona (DD-12, regla dura 5).
- `python-design-patterns`: el cálculo del día es una función pura del dominio; el caso de uso solo orquesta; el repositorio hace una sola consulta con join (sin N+1).
- `python-error-handling`: sin errores nuevos; `TurnoNoEncontrado` existente; validación de formato en el borde.
- `python-testing-patterns`: TDD estricto, AAA, `parametrize` para triangular los bordes del día y los estados, base real en memoria, reloj fijo inyectado (sin freezegun).
- `vercel-react-best-practices` (SPA de Vite): un pedido por cambio de día con bandera de vigencia, `GET /prestaciones` recién al abrir el panel (no en cascada con la agenda), estado derivado en el render, ternarios, sin componentes anidados. Las reglas de Next/RSC no aplican.
- `auth-implementation-patterns`: la interfaz solo muestra y la API decide (D230, D249, D312); `401` y `403` como el resto del panel.
- `database-migration` y `supabase-postgres-best-practices`: sin esquema nuevo. **A verificar en el change (V4, antes de la tarea 11.2, en el perfil `postgres`)**: que la consulta por consultorio y rango de `inicio` usa un índice en PostgreSQL; hoy los índices son `(profesional_id, inicio, fin)` y `(sillon_id, inicio, fin)`. Con un solo profesional el volumen es chico y no se agrega índice en este change (no hay migración); si `EXPLAIN` en el perfil `postgres` muestra un recorrido completo, se anota como mejora para un change posterior.

## Referencia visual (Stitch)

**Regla (D234, Decisión del autor):** toda pantalla del frontend se implementa a partir de una pantalla generada en Stitch con el design system «Clinical Ops»; el design cita el id y su evidencia; si Stitch no entrega la pantalla, el change de interfaz no se cierra; la KB y el spec mandan sobre el contenido. Las pantallas se consiguieron **en este propose** (2026-10-28), antes de aprobar el plan, cada una al primer intento.

- **Agenda, escritorio**: `projects/14200813501064679723/screens/cd19642b8b1b4bcda5162e35d6291e10` («Agenda del día - Turnos Odontológicos AR»).
- **Nuevo turno con error, escritorio**: `projects/14200813501064679723/screens/5371dfaf7cc441c08af62712e311c326` («Agenda del día - Nuevo turno con error - Turnos Odontológicos AR»).
- **Agenda, angosta**: `projects/14200813501064679723/screens/20bcd71b007a43f7874a05ae70a45753` («Agenda del día - Móvil (Turnos Odontológicos AR)»; pedida como `MOBILE`, Stitch la entregó como columna de unos 390 px centrada en un lienzo de escritorio, como en C-50).
- Las tres con el design system «Clinical Ops» (`assets/b683d44391ab410db2dd48aa71ed0b47`) y el modelo `GEMINI_3_8_FLASH`.
- **Evidencia**: `docs/skills-mcp/evidencias/sesion-nueva/stitch-agenda.md` (pedidos, ids, revisión de datos y sugerencias no aceptadas) y `stitch-agenda-pantalla/` (`agenda-escritorio`, `nuevo-turno-con-error` y `agenda-angosta`, cada una `.png` a 1280 × 1024 y `.html`).

**Qué se toma:**
- El enlace «Agenda» activo primero en la barra, con ícono de calendario; el resto de la barra (C-08 a C-50) no cambia.
- Título «Agenda del día», subtítulo con la zona y «Nuevo turno» primario a la derecha (a ancho completo en angosto).
- La barra de fecha en una tarjeta: «Día anterior», el selector con la fecha, el nombre del día, «Día siguiente» y «Hoy» separado a la derecha; en angosto, flechas solas, «lun 02/11/2026» y «Hoy».
- La tabla densa con HORA, PACIENTE (seminegrita), PRESTACIÓN (punto de color) y ESTADO (chip), la franja de color a la izquierda de cada fila, números tabulares y el pie «N turnos»; en angosto, una tarjeta por turno con la franja de color, la hora y el chip arriba, y el paciente y la prestación debajo.
- El panel lateral «Nuevo turno» de unos 420 px con «Cerrar» (X), campos con asterisco de obligatorio y su ayuda gris, el aviso de error rojo con título, texto y los códigos como chips monoespaciados, y el pie con «Cancelar» y «Crear turno».
- El estado vacío como texto gris dentro de la tarjeta de la tabla («No hay turnos para este día.»).

**Qué se rechaza (motivo):**
- La columna ACCIONES con «Ver ficha»: las acciones son de C-15 a C-19 y la ficha de C-43; no hay a dónde llevar.
- «Agenda sincronizada en tiempo real» y el punto verde: la agenda no se refresca sola (non-goal).
- La tarjeta «Referencia de estado» con «Podés asignar un turno nuevo o bloquear franjas desde la sección de Bloqueos.» y el estado vacío como tarjeta aparte: el spec fija el texto «No hay turnos para este día.» dentro de la tabla.
- El bloque «Estado alternativo de validación» y «Referencia clínica» del panel: era un segundo ejemplo pedido para ver el estilo; el panel muestra un solo aviso por vez.
- Un solo campo «Inicio» con fecha y hora: se separa en «Fecha» (precargada con el día mostrado) y «Hora» (A13), y la ayuda «Hora del consultorio. Termina a las hh:mm.» queda como «Termina a las hh:mm.»; «Duración calculada automáticamente según la práctica.» se reemplaza por la duración dentro de cada opción.
- El título del aviso «El horario está ocupado» con el texto en otra línea: se usa el texto único de A12, con los códigos dentro del texto (el spec lo fija así); los chips de código se toman como estilo de los códigos si la traducción lo permite sin duplicar el texto.
- Los pies de página institucionales («Módulo de Agenda y Turnos del Día», «Sede Central»): no hay sedes (D173) y el panel no tiene pie.
- La marca de dos líneas y «Mi contraseña» partido en la captura de escritorio: la barra de C-50 no cambia.
- Tailwind, Google Fonts, JetBrains Mono y Material Symbols por CDN (CSP `default-src 'self'`): se traduce a `tokens.css` y `panel.css` y a marcado de React **sin dependencias nuevas**; los íconos (calendario, flechas, más, alerta) en SVG en línea con `aria-hidden="true"` y `focusable="false"`.
- Las sugerencias de Stitch (sección «Sugerencias no aceptadas» de la evidencia).

**Ya decidido sin la pantalla, por la KB y los specs** (se mantiene aunque Stitch muestre otra cosa): los textos de los rechazos y de los estados (A12, A15); que el formulario no pide profesional ni sillón (A11); que el paciente se pide por número (A10); que no se oculta ninguna acción según el rol (D312). La prueba en el navegador (11.1) compara la implementación con las tres capturas y anota las diferencias en la evidencia.

## Contradicciones y huecos encontrados en las fuentes

1. **`02` escribía `GET /turnos?fecha`** sin decir si `fecha` es obligatoria, ni qué es «el día» (¿UTC o del consultorio?). RN-GL-01 dice que todo se trabaja en UTC salvo RN-AG-10d y RN-AG-04, que usan la zona del consultorio; la agenda «del día» es, por su nombre, un día del consultorio. → A3, A4 (D316). **Resuelto con el `/opsx:update` del 2026-10-28**: RN-GL-01 suma «la agenda del día» a sus excepciones en `05`, y la fila Turnos de `02` dice que `fecha` es opcional y es un día del consultorio.
2. **US-011 CA-1 dice «los turnos del profesional»** y la v1 tiene un solo profesional; la agenda multi-profesional es Fase 2 (`CHANGES.md`). → La agenda lista los del consultorio (que en la v1 son los del único profesional) y no filtra (D316; Q2, hallazgo H5). Quedó anotado en `06` §US-011.
3. **No hay forma de elegir paciente** sin `GET /pacientes` (C-20), y C-14 no depende de C-20 (pueden ir en paralelo, `CHANGES.md`). → A10 (D319).
4. **La matriz de `03` da «R» de turnos al dueño** pero el «C» solo al odontólogo y la recepcionista: el dueño ve «Nuevo turno» (D312) y recibe `403`. → AGE-5f.
5. **`rechazos.ts` pierde información** que el spec necesita (el segundo código de E4 y las referencias de E12). → A12: se amplían los errores sin cambiar `codigo`.
6. **La regla «una sola capability»** otra vez. → A1 (D315).
7. **El tamaño** (24 escenarios, 30 tareas). → D325.

## Risks / Trade-offs

- [El paciente por número es incómodo para la recepción] → es transitorio hasta C-20; el error `RN-GL-04` lo explica; el README lista los números de la demo.
- [La agenda devuelve nombre y apellido de pacientes a los tres roles] → es lo que la matriz permite (`03`, «Pacientes: datos administrativos», «R» para los tres) y lo mínimo para que la agenda sirva; no viaja el teléfono (A6).
- [Una agenda abierta queda vieja si otro usuario da un turno] → límite conocido; el `409` de la API protege igual y la pantalla lo muestra.
- [Un día con horario de verano en otra zona] → A3 lo cubre y un test de dominio lo prueba.
- [El servidor falso se aparta de la API] → cuerpos copiados del spec y de `api/errores.py`; la prueba en el navegador repite los escenarios contra la API real.
- [Tests existentes que dependen del orden de los enlaces] → V3 (A16).

## A verificar en el change

- **V1** (antes de la tarea 4.2): el tipo `date` de FastAPI 0.115 / Pydantic 2.11 para `fecha` rechaza un instante con hora (A8).
- **V2** (antes de la tarea 8.2): el nombre del día con `Intl` en jsdom (A13).
- **V3** (antes de la tarea 8.1): tests de C-08 a C-50 que dependen del orden de los enlaces de la barra (A16).
- **V4** (antes de la tarea 11.2, en el perfil `postgres`): el plan de la consulta del día en PostgreSQL (A20).

## Migration Plan

1. **Hecho (2026-10-28)**: con las respuestas del autor a Q1 a Q11 y los hallazgos H1 a H11, el `/opsx:update` registró D315 a D325 en `knowledge-base/10_preguntas_abiertas.md`, la excepción de la agenda del día en RN-GL-01 de `05`, la fila Turnos de `02`, la nota de `turnos.leer` en `03` y la lectura de US-011 CA-1 en `06`; ajustó los artefactos; actualizó el párrafo de estado de la KB y la regla dura 2 en `CLAUDE.md` y `AGENTS.md`, el rango de `openspec/config.yaml` y el «Leer antes» de C-14 en `CHANGES.md`; y repitió `scripts/verificar_changes.py`. Con el ok del autor se commitean los artefactos (con el `[~]` de C-14) y, aparte, el `docs(kb)` de las decisiones.
2. El Apply no lleva migración ni variables nuevas: `docker compose up --build -d` reconstruye `api` y `frontend`.
3. **Efecto visible**: el panel tiene «Agenda» y desde ahí se dan turnos.
4. **Vuelta atrás**: revertir los commits del change; no hay datos que migrar.

## Notas para el archive

- `CHANGES.md`: marcar C-14 con `[x]` y repetir `scripts/verificar_changes.py`.
- `knowledge-base/02_descripcion_general.md`, fila Turnos: ya precisa que `fecha` es opcional y es un día del consultorio (hecho en el `/opsx:update`, D316).
- `knowledge-base/06_funcionalidades.md` §US-011: nota de implementación (C-14) con CA-1 y CA-2 cubiertas y el límite del paciente por número hasta C-20 (la lectura de CA-1, D316, ya quedó en el `/opsx:update`).
- `knowledge-base/08_arquitectura_propuesta.md`: `features/agenda/`, `shared/horaDelConsultorio.ts` y `domain/agenda/dia.py` en la estructura.
- `knowledge-base/10_preguntas_abiertas.md`: un párrafo «Cierre de C-14» bajo D315 a D325 con los resultados de V1 a V4 y cómo quedaron las «Propuesta» del design.
- `docs/skills-mcp/evidencias/sesion-nueva/stitch-agenda.md`: la comparación de la prueba en el navegador (sección 4).

## Open Questions

**Cerradas.** Las once preguntas del propose quedaron cerradas por el autor el 2026-10-28 con la recomendación del agente, junto con los hallazgos H1 a H11 de `revisor-de-escenarios` con su corrección propuesta («Sí, todo»):

- **Q1 → D315.** Dos capabilities nuevas (`consulta-de-turnos` y `pantalla-de-agenda`), sin deltas, como excepción a «una sola capability» limitada a C-14 (A1).
- **Q2 → D316.** `fecha` opcional, día de calendario del consultorio; sin ella, hoy del consultorio según el reloj de la API; la respuesta trae `fecha` y `zona_horaria`; orden por `inicio` y por `id` (A3, A4; escenario `AGE-1f`, hallazgo H2). Es una excepción más de RN-GL-01 (en `05`) y «los turnos del profesional» de US-011 CA-1 son los del consultorio mientras haya un solo profesional (hallazgo H5, anotado en `06`).
- **Q3 → D317.** Todos los estados, con su etiqueta; el `estado` es el almacenado hasta la seña (A5; hallazgo H10).
- **Q4 → D318.** `paciente` con `id`, `nombre` y `apellido`, y `prestacion` con `id`, `nombre` y `color`, sin teléfono (A6).
- **Q5 → D319.** Un campo «N.º de paciente» hasta C-20 (A10).
- **Q6 → D320.** El formulario no pide profesional ni sillón (A11).
- **Q7 → D321.** `turnos.leer` para los tres roles; sin roles, `403` `RN-AU-05`; un turno de otro consultorio no se lista y su id da `404` `RN-GL-04` (A7; nota en `03`).
- **Q8 → D322.** `fecha` mal formada, o fuera de `0001-01-02` a `9999-12-30`, da `422` de formato con `codigos` vacío, sin `RN-GL-01` y nunca `500` (A8; escenario `AGE-3a`, hallazgo H7).
- **Q9 → D323.** Los textos de A12, decididos por el código; además «Cargando agenda…», «Reintentar» solo al cargar el día, «Completá paciente, prestación, fecha y hora.» (hallazgo H6) y el `403` de la lectura con su texto (hallazgo H8; escenarios `AGE-4d` y `AGE-6a`).
- **Q10 → D324.** `/panel/agenda`, primer enlace de la barra, y `/panel` sin cambios (A13).
- **Q11 → D325.** **24 escenarios** (11 de la API y 13 de la pantalla) y **30 tareas en 11 grupos**, como excepción limitada a C-14; cada causa de un escenario con varias tiene su test (hallazgo H9) y la tarea 7.3 solo mueve código (hallazgo H4).

Los demás hallazgos se reflejan así: H1, `AGE-2b` y `AGE-3b` titulados «Error de negocio»; H3, escenario `AGE-5h` (un turno el 3 de noviembre a las 22:00, `2026-11-04T01:00:00Z`, recarga `fecha=2026-11-03`) en la tarea 9.3; H11, fin de mes y de año en la tarea 8.3.
