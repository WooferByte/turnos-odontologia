# Design: panel-historial-de-turno

Fecha del design: **2026-10-28**. Change **C-15** (US-015; escenarios mínimos US-015 CA-1, E9 y HIS-2 de `CHANGES.md`). Gobernanza **BAJO** (`CHANGES.md` C-15): autonomía completa si los tests pasan; las elecciones que dependían de una pregunta (Q1 a Q6) se confirmaron con el autor antes del Apply, como en C-14. Motivación y alcance en `proposal.md`; el comportamiento, en `specs/pantalla-de-historial/spec.md` (6 escenarios).

Las decisiones se numeran **G1 a G14** («G» por la letra libre más cercana a «historial», para no confundirlas con las D1..D331 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores: D de C-01, I de C-02, H de C-03 y C-12, P de C-04, S de C-05, J de C-06, R de C-07, F de C-08, U de C-09, T de C-11, B de C-13, L de C-49, K de C-10, Y de C-50, A de C-14). Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»). **Las preguntas Q1 a Q6 están respondidas** (2026-10-28, «Sí, todo»): el autor aceptó la recomendación de todas y todos los hallazgos H1 a H7 de `revisor-de-escenarios` (`docs/skills-mcp/evidencias/sesion-nueva/revision-de-escenarios-panel-historial-de-turno.md`) con su corrección propuesta. Quedaron registradas como **D326 a D331** en `knowledge-base/10_preguntas_abiertas.md`; no crean códigos RN nuevos. Las decisiones G que dependían de una pregunta ahora citan su D («Decisión del autor (D327)»).

## Context

**Lo que ya existe** (leído del código y de los specs, no supuesto):

- **API del historial** (C-03, `api/routers/turnos.py`): `GET /turnos/{id}/historial` con `requiere(Permiso.HISTORIAL_LEER)`, que la matriz (`domain/acceso/roles.py`) da a **los tres roles** (`_TODOS`), así que el dueño, la recepcionista y el odontólogo ya pueden leerlo y un usuario sin roles recibe `403` `RN-AU-05`. Devuelve una lista de `EventoTurnoSalida` (`id`, `turno_id`, `tipo`, `actor_tipo`, `actor_id` como texto o `null`, `ocurrido_en` aware UTC, `antes`, `despues`, `motivo`), ordenada por `ocurrido_en` y, a igual momento, por `id` (D165); vacía si el turno no tiene eventos (D160); `404` `RN-GL-04` si el turno no existe (D166). Solo `GET` (D167).
- **Eventos que hoy existen**: solo `creado` con `actor_tipo` `usuario` (D163). Desde C-07 lleva el id del usuario del token (D210); los anteriores, `actor_id` vacío (D159). Su `despues` es la foto del turno al nacer: `estado`, `inicio`, `fin` (ISO UTC con `Z`), `duracion_minutos`, `paciente_id`, `prestacion_id`, `profesional_id` y `sillon_id` (D163).
- **Agenda del día** (C-14, `features/agenda/`): `PaginaAgenda` con un panel lateral «Nuevo turno» (`PanelNuevoTurno`), `TablaDeTurnos` sin columna de acciones (cuatro columnas), la zona del consultorio que trae `GET /turnos` (`dia.zona`), los textos fijos en `mensajes.ts` (`nombreDelDia`, etiquetas de estado) y el patrón de «bandera de vigencia por pedido» para mostrar solo la última respuesta.
- **Hora del consultorio** (`shared/horaDelConsultorio.ts`): `horaLocal` y `fechaLocal`, solo con `Intl` (D285).
- **Cliente HTTP** (`shared/api/`): `pedidoDelPanel` renueva la sesión y lanza `SesionTerminada` si no puede; `traducirRechazo` da `RecursoInexistente` para un `404`, `PermisoInsuficiente` para un `403` y `SinConexion` para lo demás.
- **Servidor falso** (`test/servidorFalso.ts`): tiene `TURNOS_DE_LA_AGENDA` (ids 11 a 13), `retener`, `caerse`, `vencerAccess`, `invalidarRefresh`, `quitarPermiso`; **no** responde `GET /api/turnos/{id}/historial`.
- **Íconos**: ya existe `shared/iconos/IconoReloj.tsx`.
- **Lo que la API no da**: el email o el nombre del usuario actor. `GET /usuarios` es solo para odontólogo y dueño (`usuarios.leer`), así que la recepcionista no podría resolverlo.

## Goals / Non-Goals

**Goals:**

- Que cualquiera de los tres roles vea, sin salir de la agenda, qué pasó con un turno, cuándo y quién lo hizo, en el orden del historial.
- Reusar la API tal como está: ni rutas, ni permisos, ni forma de respuesta nuevos.
- Que un tipo de evento que agregue un change posterior (C-16 a C-19) se vea aunque esta pantalla todavía no lo conozca, sin romperla.

**Non-Goals:**

- Mostrar el nombre o el email del actor (D328) ni el detalle completo de `antes`/`despues` (ids de paciente, prestación, profesional y sillón).
- Una ruta propia del historial (`/panel/turnos/:id/historial`) o un enlace compartible (D327).
- Paginar el historial: un turno tiene pocos eventos.
- Refrescar el historial solo si otro usuario cambia el turno mientras el panel está abierto.

## Decisions

### G1. Una capability nueva, sin deltas — Decisión del autor (D326; Q1)

`pantalla-de-historial` reúne el botón «Historial» de la fila, el panel que abre y la regla de un solo panel lateral a la vez (hallazgo H1). `pantalla-de-agenda` no recibe delta: sus requisitos describen qué se ve de cada turno, el cambio de día y el alta, y el botón nuevo no cambia ninguno; `historial-de-turnos` no cambia. Así el change cumple «una sola capability» de `config.yaml` sin excepción. **Alternativa descartada**: un delta en `pantalla-de-agenda` que agregue «cada fila tiene acciones» (dos capabilities, y C-16 a C-19 tendrían que volver a modificarlo).

### G2. Dónde se abre — Decisión del autor (D327; Q2; aplica D112)

Un **panel lateral** al costado de la agenda, igual que «Nuevo turno» (C-14, D110), abierto por un botón con borde «Historial» (con `IconoReloj`) en una quinta columna de la tabla. La columna lleva el encabezado «Acciones», como en la pantalla de usuarios (Stitch la deja sin título: se prefiere la coherencia con el panel y la accesibilidad de la tabla), y el botón un nombre accesible propio, «Historial del turno de Ana Ejemplo, 09:00», para que cada fila se distinga. **Un solo panel lateral a la vez**: abrir «Historial» cierra «Nuevo turno» y al revés; cambiar de día cierra el historial (el turno ya no está a la vista) sin pedirlo de nuevo, y una respuesta que llega después no lo reabre (requisito propio del spec y escenario `HIS-2f`, hallazgos H1, H2 y H6). La fila del turno abierto se marca como seleccionada (lo toma de Stitch). **Alternativa descartada**: una ruta propia `/panel/turnos/:id/historial`, que es una «pantalla nueva» (D112) y necesitaría `GET /turnos/{id}` para el resumen.

### G3. Qué datos se piden — Propuesta

Un solo `GET /api/turnos/{id}/historial` al abrir el panel (sin cascada): el resumen (paciente, prestación, día y horario) sale de la fila de la agenda ya cargada y la zona horaria del día de la agenda (`dia.zona`); no se pide `GET /turnos/{id}` ni nada más. Un pedido nuevo (otro turno, «Reintentar») invalida al anterior con la misma bandera de vigencia de la agenda, así que solo se muestra la última respuesta (`HIS-2f`); cerrar el panel o cambiar de día también la invalida, así que una respuesta tardía no reabre nada (`HIS-2c`, `HIS-2f`; hallazgo H6). **Alternativa descartada**: guardar en caché el historial ya leído; puede cambiar entre dos aperturas (C-16 en adelante) y es un pedido barato.

### G4. El actor — Decisión del autor (D328; Q3)

«Por: Usuario n.º {actor_id}» con `actor_tipo` `usuario` y un id; «Por: Usuario del panel (sin identificar)» con `actor_tipo` `usuario` y `actor_id` vacío (D159). Un `actor_tipo` que la pantalla no conoce (los de `03`: `paciente`, `sistema`, `webhook`, que llegan con changes posteriores) se muestra como «Por: {actor_tipo}», sin inventar textos que fija cada change; la API de hoy no lo produce, así que es un test unitario sin escenario (`'G4: …'`, hallazgo H1). **Motivo**: la API no trae el email y la recepcionista no puede leer usuarios; el dueño, que es quien pide la trazabilidad (US-015), sí puede buscar el número en «Usuarios». **Alternativa descartada**: agregar `actor_email` a la respuesta del historial; cambia el contrato de `historial-de-turnos` (otra capability, tests de backend, exponer el email de los usuarios a la recepcionista), demasiado para un change BAJO. Queda como límite conocido en el README.

### G5. Qué se muestra de cada evento — Decisión del autor (D329; Q4)

- **Título**: `creado` → «Turno creado». Un tipo que esta pantalla todavía no conoce → «Cambio registrado ({tipo})» (HIS-2b): el evento se ve igual, con su fecha y su actor, y el change que agregue el tipo le pone su etiqueta.
- **Cuándo**: `ocurrido_en` en hora del consultorio, «{nombreDelDia(fechaLocal)}, {horaLocal}» («lunes 26 de octubre de 2026, 10:15»), reusando `nombreDelDia` de la agenda.
- **Detalle del `creado`**: «Estado inicial: {etiqueta del estado} · {horaLocal(inicio)} – {horaLocal(fin)}», con las etiquetas de estado de la agenda (`ETIQUETAS_DE_ESTADO`). Si `despues` no trae un `estado` conocido o un `inicio` y un `fin` de texto, el detalle no se muestra (la entrada sí; test unitario sin escenario `'G5: …'`, hallazgo H1).
- **Motivo**: si `motivo` no es `null`, «Motivo: {motivo}».
- **No se muestran** los ids de `despues` (paciente, prestación, profesional, sillón): el resumen del panel ya dice de qué turno se trata.

### G6. Textos fijos del panel — Decisión del autor (D330; Q5; sigue D323)

| Situación | Texto |
|---|---|
| Título | «Historial del turno» |
| Nota | «Solo lectura: el historial no se puede editar.» |
| Cargando | «Cargando historial…» |
| Lista vacía | «Este turno no tiene eventos registrados.» |
| `404` `RN-GL-04` | «El turno ya no existe (RN-GL-04).» (sin «Reintentar») |
| `403` `RN-AU-05` | «Tu usuario no tiene permiso para ver el historial (RN-AU-05).» (sin «Reintentar») |
| Sin conexión / `5xx` / respuesta de otra forma | «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» con «Reintentar» |
| Sesión irrenovable | vuelve al inicio de sesión (`SesionTerminada`, como en la agenda) |

La pantalla decide por el tipo de error y el código, nunca por el `detail` de la API (D323).

### G7. Clases de rechazo y orden — Decisión del autor (RN-GL-02, D135, D166, D208)

La pantalla no evalúa reglas. El orden lo fija la API: primero el acceso (`401` → renovación o inicio de sesión; `403` `RN-AU-05`), después la ruta (`422` si el id no es entero, que desde la agenda no puede pasar porque el id sale de la respuesta de `GET /turnos`) y después la existencia (`404` `RN-GL-04`, regla de la URL). No hay reglas de negocio en una lectura.

### G8. Estructura del frontend — Propuesta (aplica A9 de C-14 y `vercel-react-best-practices`)

- `src/features/historial/apiHistorial.ts`: `crearApiHistorial(pedidoDelPanel)` con `obtenerHistorial(turnoId)`; valida cada evento sin `any` (`tipo`, `actor_tipo` texto; `actor_id` texto o `null`; `ocurrido_en` texto; `antes`/`despues` objeto o `null`; `motivo` texto o `null`); una respuesta de otra forma es `SinConexion` (test unitario sin escenario `'G8: …'`, hallazgo H1).
- `src/features/historial/mensajes.ts`: los textos de G6 y las funciones puras `tituloDelEvento`, `textoDelActor`, `cuandoOcurrio` y `detalleDelCreado` (G4, G5), testeadas aparte.
- `src/features/historial/PanelHistorial.tsx`: el panel (componente de nivel superior, no definido dentro de otro), con su propio pedido y su estado derivado de la respuesta.
- `features/agenda/TablaDeTurnos.tsx`: la quinta columna con el botón y la fila seleccionada (`onVerHistorial(turno)`, `turnoSeleccionadoId`), con ternarios en vez de `&&` en el render.
- `features/agenda/PaginaAgenda.tsx`: un estado `panel` (`ninguno` | `nuevo-turno` | `historial` con el turno) en lugar del booleano `panelAbierto`, para que haya un solo panel a la vez (G2). REFACTOR acotado: el comportamiento de «Nuevo turno» no cambia.
- Sin dependencias nuevas, sin `vi.mock`, sin `localStorage`; el `useEffect` del pedido usa la bandera de vigencia.

### G9. Interacción y anchos angostos — Propuesta (sale de las pantallas de Stitch)

En escritorio el panel va al costado de la agenda (unos 420 px), como «Nuevo turno». Debajo de 720 px el panel ocupa el ancho y va debajo de la barra, como en la captura angosta; «Cerrar» (X arriba y botón abajo) vuelve a la agenda. En la tabla angosta (tarjetas de C-14) el botón «Historial» va al pie de cada tarjeta. Al abrir, el foco va al título del panel (enfocable con `tabIndex={-1}`); al cerrar, vuelve al botón «Historial» de la fila. Se conserva por accesibilidad y se prueba (hallazgo H1): el spec lo dice en su primer requisito, `HIS-2a` y `HIS-2c` lo verifican y la tarea 4.1 tiene un test para cada lado, con `toHaveFocus` de Testing Library, que en jsdom sigue a `document.activeElement` de forma confiable.

### G10. Servidor falso y tests — Decisión del autor (D222, D227; reglas duras 6 y 8) + Propuesta (detalle)

`servidorFalso.ts` suma la opción `historiales?: Readonly<Record<number, readonly EventoFalso[]>>` y la ruta `GET /api/turnos/{id}/historial`: devuelve los eventos de ese turno tal como están (el falso **no** reordena, para que HIS-2b pruebe que la pantalla tampoco lo hace), `[]` si el turno existe y no tiene, y `404` `RN-GL-04` si el id no está entre los turnos de partida. Respeta los modos que ya existen (`retener`, `caerse`, `vencerAccess`, `invalidarRefresh`, `quitarPermiso`), cuenta las peticiones y no cambia ningún test anterior. Los tests van sobre `<App/>` en un `MemoryRouter` (como `PaginaAgenda.test.tsx`), sin `vi.mock`, `vi.fn`, `vi.stubGlobal` ni temporizadores falsos; cada causa de un escenario de varias causas es un test propio, con el ID en el nombre (`'HIS-2a: …'`); los casos defensivos sin escenario llevan la decisión que prueban (`'G4: …'`, `'G5: …'`, `'G8: …'`). El `500` de `HIS-2e` usa `fallarRuta` con `500` en la ruta del historial (hallazgo H4) y el `403` de `HIS-2d` usa `quitarPermiso` con la agenda ya cargada (hallazgo H5).

### G11. Versiones y dependencias — Propuesta

No se agrega ni cambia ningún paquete: ni `backend/pyproject.toml` ni `frontend/package.json` ni `package-lock.json`. La política de pins (D133) no aplica porque no se elige ninguna versión.

### G12. Demo y README — Propuesta

Sin datos nuevos de seed: el historial se ve con un turno creado desde la agenda de la demo. El README suma «Historial del turno» en «Panel (interfaz)» (dar un turno, abrir su historial con la recepcionista y con el dueño), la tabla escenario → test (`HIS-2a` a `HIS-2f`) y los límites conocidos: el actor se ve por número (D328); la API no filtra el historial por consultorio (D331); el historial no se refresca solo. **Sin guía en `docs/guias/`** (proceso del 2026-10-28 para los BAJO de la fase 4).

### G13. Prueba en el navegador — Decisión del autor (D234, `rules.tasks`) + Propuesta (detalle)

Con la demo (`crear_app_demo` y `npm run dev`): crear un turno en la agenda con la recepcionista, abrir su historial («Turno creado», fecha y hora del consultorio, «Por: Usuario n.º 2», estado inicial), cerrarlo, abrirlo con el dueño y con la odontóloga, y ver en `/docs` el mismo `GET /turnos/{id}/historial`. Comparar con las dos capturas de Stitch a 1280 y 390 px, guardar las capturas de la implementación junto a las de Stitch y anotar las diferencias en la sección 4 de `stitch-historial.md`. Consola sin errores ni datos sensibles; sin desplazamiento horizontal a 390 px. Después un recorrido breve en Compose (`http://127.0.0.1:5173`) para ver la CSP.

### G14. Skills aplicadas

- `vercel-react-best-practices`: un solo pedido por apertura (sin cascada), estado derivado de la respuesta, componentes de nivel superior, ternarios en vez de `&&`.
- `python-testing-patterns` y `fastapi-templates`: **no aplican** (no se toca el backend).
- `revisor-de-escenarios`: se corre después de este propose y antes del Apply (CLAUDE.md, «Flujo de Trabajo»).

## Referencia visual (Stitch)

Pantallas generadas en este propose con el MCP `stitch`, proyecto `projects/14200813501064679723`, design system «Clinical Ops» (`assets/b683d44391ab410db2dd48aa71ed0b47`), modelo `GEMINI_3_8_FLASH`, cada una al primer intento. Pedidos, ids de archivos y revisión de datos en [`docs/skills-mcp/evidencias/sesion-nueva/stitch-historial.md`](../../../docs/skills-mcp/evidencias/sesion-nueva/stitch-historial.md).

| Pantalla | Id | Evidencia |
|---|---|---|
| Historial del turno, escritorio | `projects/14200813501064679723/screens/2955e5e29bba4982a0b515329e0ff4e1` | `stitch-historial-pantalla/historial-escritorio.png` y `.html` |
| Historial del turno, angosta | `projects/14200813501064679723/screens/c80d02b8dbac4e48be68ca11ff787857` | `stitch-historial-pantalla/historial-angosta.png` y `.html` |

**Se toma**: el botón con borde «Historial» con ícono de reloj en una columna final de la tabla; la fila del turno abierto resaltada (fondo celeste suave); el panel lateral sin oscurecer la agenda, con borde izquierdo y la sombra suave del panel; el encabezado con título, X y el resumen del turno en dos líneas grises; la nota de solo lectura en gris; la línea de tiempo vertical (punto y línea fina) con una tarjeta por evento: título en seminegrita, fecha en números tabulares, «Por: …», y el detalle separado por una línea fina; el actor sin identificar en itálica; el vacío en un recuadro punteado; los avisos de error con el estilo de `Aviso`; «Cerrar» a todo el ancho al pie; en angosto, el panel a todo el ancho debajo de la barra.

**Se rechaza** (la KB y el spec mandan sobre el contenido):

- La etiqueta «SOLO LECTURA» junto al título: repite la nota de solo lectura, que es la que pide el spec.
- El rótulo «TRAZABILIDAD DE EVENTOS» y el contador «1 evento registrado»: textos que el spec no fija.
- Los identificadores «EV-01» / «EV-02» en cada tarjeta: no son el `id` del evento ni le dicen nada al usuario.
- El bloque «Estados alternativos»: en Stitch se pidieron juntos como muestra; en la pantalla se ve uno por vez, según la respuesta.
- El aviso de conexión en ámbar: se usa el mismo aviso de error que la agenda (D323), con «Reintentar».
- El código del `404` en monoespaciada: los códigos van entre paréntesis en el texto (D323), como en la agenda.
- «Agenda sincronizada en tiempo real» y el pie «Módulo de Agenda y Turnos del Día · Sede Central»: no hay tiempo real en la v1 y la agenda de C-14 ya los rechazó.

El HTML de Stitch (Tailwind y Google Fonts por CDN) **no se copia**: se traduce a `panel.css` y, si hace falta, a `tokens.css`, sin dependencias nuevas, sin CDN y con los íconos en SVG en línea (CSP `default-src 'self'`). Sin la comparación con estas capturas (G13), el change no se cierra (D234).

## Contradicciones y huecos encontrados en las fuentes

- **HIS-2 no está definido en la KB**: `CHANGES.md` lo nombra como escenario mínimo de C-15 («los eventos se muestran en orden cronológico con actor y fecha») y la KB solo tiene HIS-1 (C-03). Se toma la definición de `CHANGES.md` y se detalla en `HIS-2a` a `HIS-2f`; quedó anotado junto a D326 a D331 y en la convención del spec (hallazgo H7).
- **US-015 dice «Como dueño»** pero la matriz de `03` da «R» a los tres roles; manda la matriz (D68, como ya resolvió C-03 con `historial.leer`). Quedó anotado en `06` §US-015 y junto a D326 a D331 (hallazgo H7).
- **El historial no se filtra por consultorio** (D331; Q6): `GET /turnos/{id}` (C-14, D321) da `404` a un turno de otro consultorio, pero `GET /turnos/{id}/historial` (C-03) devuelve el historial de cualquier turno que exista. En la v1 hay un solo consultorio, así que no tiene efecto; queda como límite conocido, anotado en `02` (fila Historial).
- **El actor solo trae un id** (D328; Q3): RN-AG-11 pide «quién»; la API lo da como id del usuario, sin nombre.

## Risks / Trade-offs

- [El actor por número no dice quién es a la recepcionista] → El dueño y el odontólogo lo resuelven en «Usuarios»; queda como límite conocido y D328 deja la alternativa con la API para un change posterior.
- [Un change posterior agrega un tipo de evento y se ve como «Cambio registrado (tipo)»] → Es intencional (G5): el evento nunca se oculta; el change que lo agrega suma su etiqueta y su escenario.
- [La quinta columna rompe un test de la agenda que cuenta celdas o botones] → V1 lo comprueba antes del GREEN; solo se ajusta el número, nunca lo que verifica.
- [Un `despues` con otra forma en un evento viejo] → El detalle se omite y la entrada se ve igual (G5); un test lo cubre.

## A verificar en el change

- **V1** (antes de la tarea 3.2): qué tests de `pantalla-de-agenda` dependen de la cantidad de columnas, de celdas o de botones de la fila (`getAllByRole('button')`, `getAllByRole('cell')`); si alguno cambia, se ajusta solo su número.
- **V2** (antes de la tarea 2.2): que `traducirRechazo` da `RecursoInexistente` con `codigo` `RN-GL-04` para el `404` del historial que arma el falso con el mismo cuerpo que la API real (`problem+json` con `codigos`).
- **V3** (antes de la tarea 6.1): en la demo, que el evento `creado` de un turno creado por la recepcionista trae `actor_id` `"2"` (D212) y que la página muestra «Usuario n.º 2».

## Migration Plan

Sin migraciones ni cambios de API. Se despliega con el frontend; volver atrás es revertir los commits del change (la API queda igual).

## Notas para el archive

- Marcar C-15 con `[x]` en `CHANGES.md` y correr `python scripts/verificar_changes.py`.
- Registrar los resultados de V1 a V3 en `knowledge-base/10_preguntas_abiertas.md`, junto a D326 a D331.
- Completar la sección 4 de `stitch-historial.md` con la comparación.
- Contar C-15 para la guía acumulada de los BAJO de la fase 4 (después del cuarto archivado).

## Open Questions

**Cerradas.** Las seis preguntas del propose quedaron cerradas por el autor el 2026-10-28 con la recomendación del agente, junto con los hallazgos H1 a H7 de `revisor-de-escenarios` con su corrección propuesta («Sí, todo»):

- **Q1 → D326.** Una sola capability nueva, `pantalla-de-historial`, sin delta en `pantalla-de-agenda` ni en `historial-de-turnos` (G1); suma el requisito de un solo panel lateral a la vez (hallazgo H1).
- **Q2 → D327.** Botón «Historial» en cada fila de la agenda y un panel lateral como «Nuevo turno», con un solo panel a la vez y que se cierra al cambiar de día (G2; escenario `HIS-2f`, hallazgos H1 a H3 y H6).
- **Q3 → D328.** «Por: Usuario n.º 2» con el id de la API y «Por: Usuario del panel (sin identificar)» sin id, sin cambiar la API; el nombre del actor queda para un change posterior (G4).
- **Q4 → D329.** Título, fecha y hora del consultorio, actor, «Estado inicial: …» solo para el `creado` y «Motivo: …» si lo hay, sin los ids de `despues` (G5).
- **Q5 → D330.** Los textos de G6, decididos por el tipo de error y el código (D323); el `5xx` muestra el aviso de conexión con «Reintentar» (`HIS-2e`, hallazgo H4).
- **Q6 → D331.** El historial no filtra por consultorio: límite conocido de la v1 (un solo consultorio); se corrige en la Fase 2 o en el primer change que toque esa ruta.
