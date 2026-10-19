# Design: panel-de-prestaciones

Fecha del design: **2026-10-19**. Gobernanza **BAJO** (pantalla sobre una API existente, sin datos de pacientes ni cambios de sesión o de esquema).

**Respuesta del autor (2026-10-19): las cinco preguntas abiertas se cierran con la recomendación del agente.** Quedan como decisiones del autor D229 (T1, capability nueva), D230 (T13, acciones visibles para todos y `403` de la API), D231 (T4, C-11 cablea `SesionTerminada`), D232 (T9, sin validación local de la duración) y D233 (T10, selector de color nativo), registradas en `knowledge-base/10_preguntas_abiertas.md`. Las demás decisiones marcadas «Propuesta» siguen así hasta que el autor apruebe el plan completo. En la misma revisión se incorporó el informe de `revisor-de-escenarios` (`revision-de-escenarios.md`, que queda como el «antes»): el spec pasó de 24 a 33 escenarios (H1 a H7 y los bordes sugeridos) y las tareas siguen siendo 20.

Las decisiones se numeran **T1 a T16** («T» de tabla de prestaciones) para no confundirlas con las D1..D228 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores (D de C-01, I de C-02, H de C-03, P de C-04, S de C-05, J de C-06, R de C-07, F de C-08). Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design, a confirmar) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»). Las que salieron de una pregunta abierta citan su D y su Q («Decisión del autor (D230; Q2)»).

## Context

Motivación y alcance: ver `proposal.md`. Requisitos: `specs/pantalla-de-prestaciones/spec.md`.

**Lo que dejaron C-04, C-07 y C-08** (leído del código y de los specs, no supuesto):

- **API de prestaciones** (`openspec/specs/gestion-de-prestaciones/spec.md`, `backend/app/api/routers/prestaciones.py`, `api/esquemas.py`, `api/errores.py`): `GET /prestaciones` (`200`, lista ordenada por `id` con `id`, `nombre`, `duracion_minutos`, `color`, `reservable_online`, `activa`), `POST /prestaciones` (`201`; `nombre`, `duracion_minutos`, `color` obligatorios, `reservable_online` opcional, `extra="forbid"`) y `PATCH /prestaciones/{id}` (solo los campos que llegan; un `null` explícito es de formato). `color` tiene que cumplir `^#[0-9A-Fa-f]{6}$` (mayúsculas o minúsculas). Rechazos en `application/problem+json` con `codigos`:
  - `422` con `codigos` `["RN-AG-01"]` y `errores` `[{"campo": "duracion_minutos", "codigo": "RN-AG-01", "mensaje": "El campo 'duracion_minutos' debe ser mayor que 0 y múltiplo de 5 minutos."}]` (validación de entrada del dominio, D176, D177);
  - `422` con `codigos` vacío y `errores` con `campo` y `codigo` `null` para el cuerpo mal formado (nombre vacío o solo de espacios, color inválido, campo de más);
  - `409` con `codigos` `["RN-AG-15"]` y `detail` «Ya existe una prestación llamada «…».» (regla de negocio, después de RN-AG-01);
  - `404` con `codigos` `["RN-GL-04"]` y `referencias` para un id inexistente en la URL (D166).
- **Protección** (`proteccion-del-panel`, `backend/app/domain/acceso/roles.py`): leer prestaciones, los tres roles; crear y editar, solo `odontologo` (D205). Sin sesión válida `401` `["RN-AU-03"]`; con rol insuficiente `403` `["RN-AU-05"]`, evaluados antes que la validación (D208).
- **Ningún token ni ruta informa los roles**: el access lleva solo el id del usuario (los roles se leen de la base en cada petición, D102) y no existe `GET /auth/yo` (D225). La interfaz no puede saber de antemano si el usuario puede editar (T13, D230).
- **Demo** (`backend/app/infrastructure/db/seed_demo.py`): las cinco prestaciones de `04` con ids 1 a 5, **todas activas**, y los usuarios `odontologa@consultorio-demo.test` (`odontologo` + `dueno`) y `recepcion@consultorio-demo.test` (`recepcionista`), con la contraseña de prueba del README.
- **Frontend de C-08** (`frontend/src/`): `App.tsx` con `/ingresar`, `/panel/*` protegido y el resto a `/panel`; `pages/PanelBase.tsx` (encabezado, «Cerrar sesión», «Panel del consultorio»); `shared/api/clienteHttp.ts` con `pedidoDelPanel` (Bearer, una renovación compartida, una repetición; devuelve al llamador los `4xx` que no son `401`, y `SinConexion` ante red caída o `5xx`); `shared/api/errores.ts` (`CredencialesRechazadas`, `EntradaRechazada`, `SesionTerminada`, `SinConexion`, cada una con un solo `codigo`); `shared/api/ProveedorDeSesion.tsx` (estados `verificando`, `con-sesion`, `sin-sesion`), que **no** expone `pedidoDelPanel` ni maneja `SesionTerminada` (desvío aceptado en C-08, F8: «queda para el primer change que use `pedidoDelPanel` (C-09)»); `test/servidorFalso.ts`, que solo conoce `GET /api/prestaciones` (responde `[]`) y en el que la recepcionista es la usuaria **inactiva** del login. **No hay ningún CSS**: el panel se ve con los estilos del navegador. La suite tiene 38 tests en 4 archivos.
- **Ninguna pantalla llama todavía a `pedidoDelPanel`**: C-11 es la primera, porque C-09 (que tenía el cableado en su alcance) no está hecho.

## Goals / Non-Goals

**Goals:**

- Que la pantalla muestre exactamente lo que decide la API: ninguna regla de prestaciones se duplica en el navegador, y todo rechazo se ve con su código RN.
- Que la lógica que habla con la API (listar, crear, editar y traducir los rechazos) sea TypeScript puro, testeable con el servidor falso inyectado, sin `vi.mock`.
- Que una sesión que termina mientras se usa la pantalla lleve al inicio de sesión con el aviso, como ya pide `ingreso-al-panel`.
- No tocar la API, el backend ni las dependencias.

**Non-Goals:**

- Saber el rol del usuario en el navegador (D230): la API es la que decide y la pantalla muestra su `403`.
- Actualizaciones optimistas, caché de peticiones o sincronización entre pestañas: la fila cambia cuando llega la respuesta.
- Un sistema de diseño reutilizable, componentes genéricos (tabla, modal, formulario) o tema oscuro: solo los tokens y estilos que esta pantalla y el encabezado necesitan.
- Cargar la fuente Inter desde un CDN (la CSP de nginx es `default-src 'self'`, F14 de C-08) o empaquetarla (sería una dependencia nueva).
- Accesibilidad certificada (WCAG formal): se cuidan etiquetas, foco, `role="alert"` y estado no solo por color, sin auditoría.

## Decisions

### T1. Una capability nueva, `pantalla-de-prestaciones` — Decisión del autor (D229; Q1; sigue D218)

Los requisitos de la pantalla van en una capability de interfaz nueva. `gestion-de-prestaciones` describe la API y no cambia; mezclar ahí el comportamiento del navegador repetiría lo que D218 evitó en C-08.

**Alternativas descartadas:** (a) delta a `gestion-de-prestaciones`: el mismo spec describiría la API y el navegador, y su suite de verificación (pytest) no corre los escenarios de la pantalla; (b) una capability amplia `panel` o `interfaz-del-panel`: crecería con cada pantalla (D218, alternativa b).

### T2. Ruta y navegación — Propuesta

- `/panel/prestaciones` dentro de las rutas protegidas. `PanelBase` pasa a ser el **diseño común** del panel: encabezado con «Turnos Odontológicos AR», un enlace «Prestaciones» (`NavLink`, marcado cuando está activo) y «Cerrar sesión»; debajo, un `<Outlet/>`.
- `/panel` (índice) sigue mostrando «Panel del consultorio» y cualquier otra `/panel/*` también (C-08 prueba que `/panel/algo` se respeta tras iniciar sesión).
- Rutas en `App.tsx`: `path="/panel"` con `RutaProtegida` y `PanelBase`, e hijas `index`, `prestaciones` y `*`. Comprobar **V3**.

**Alternativa descartada:** una ruta suelta `/panel/prestaciones` con su propio encabezado: duplicaría «Cerrar sesión» en cada pantalla futura.

### T3. Estructura de archivos — Propuesta (aplica `08`, «Estructura de directorios», y F4 de C-08)

```
frontend/src/
├── features/prestaciones/
│   ├── apiPrestaciones.ts          # listar, crear, editar (T5); usa pedidoDelPanel
│   ├── apiPrestaciones.test.ts
│   ├── PaginaPrestaciones.tsx      # estado de la pantalla (T7)
│   ├── PaginaPrestaciones.test.tsx
│   ├── TablaDePrestaciones.tsx     # filas, acciones Editar / Desactivar / Reactivar (T8)
│   ├── PanelDePrestacion.tsx       # formulario lateral de alta y edición (T9)
│   └── mensajes.ts                 # textos fijos de la pantalla (T11)
├── shared/api/
│   ├── errores.ts                  # + PermisoInsuficiente, ReglaRechazada, RecursoInexistente; EntradaRechazada con errores de campo (T6)
│   ├── rechazos.ts                 # traducirRechazo(respuesta): única traducción de un 4xx del panel a error (T6)
│   └── ProveedorDeSesion.tsx       # + pedidoDelPanel y SesionTerminada (T4)
├── shared/estilos/
│   ├── tokens.css                  # variables de «Clinical Ops» (T12)
│   └── panel.css                   # encabezado, tabla, panel lateral, errores de campo (T12)
└── test/servidorFalso.ts           # + contrato de prestaciones y roles (T14)
```

Componentes en PascalCase, uno por archivo y nunca definidos dentro de otro; sin archivos *barrel* (el guard de C-08 lo controla). Los CSS se importan una vez desde `main.tsx` (no desde los componentes), así los tests no dependen de ellos.

### T4. Sesión terminada desde una pantalla — Decisión del autor (D231; Q3; cumple `ingreso-al-panel`, «Un 401 de la API se renueva una vez o termina la sesión»)

`ProveedorDeSesion` agrega `pedidoDelPanel(ruta, opciones)` a su contexto: llama al de `clienteHttp` y, si recibe `SesionTerminada`, pasa a `sin-sesion` con el aviso `sesion-terminada` y vuelve a lanzar el error (la pantalla no muestra nada más: `RutaProtegida` redirige a `/ingresar`, que muestra «Tu sesión terminó. Iniciá sesión de nuevo.»). El resto de los errores llegan intactos a la pantalla. Es lo que C-08 (F8, «Notas para el archive» b) dejó para «el primer change que use `pedidoDelPanel`»; `CHANGES.md` lo tiene en C-09, que todavía no se hizo, y su entrada se ajusta al archivar (no ahora). Como el cableado es comportamiento de esta pantalla, el spec lo cubre con el Requirement «La sesión que termina en la pantalla vuelve al inicio de sesión» (tres escenarios `US-092 CA-1`: renovación que sigue, sesión irrenovable al abrir y al guardar), sin cambiar el requisito de `ingreso-al-panel`.

### T5. Cliente de prestaciones — Propuesta

`apiPrestaciones.ts` recibe la función `pedidoDelPanel` (inyectada; la pantalla la toma del contexto) y expone:

- `listarPrestaciones(): Promise<Prestacion[]>` — `GET /api/prestaciones`.
- `crearPrestacion(datos: DatosDeAlta): Promise<Prestacion>` — `POST /api/prestaciones` con `nombre`, `duracion_minutos`, `color` y `reservable_online`.
- `editarPrestacion(id, cambios: CambiosDePrestacion): Promise<Prestacion>` — `PATCH /api/prestaciones/{id}` con solo los campos presentes en `cambios` (tipo con propiedades opcionales; con `exactOptionalPropertyTypes` no se mandan `undefined`).
- `cambiosEntre(original, editado): CambiosDePrestacion` — función pura que devuelve solo lo que cambió (el nombre se compara tal cual: cambiar solo mayúsculas cuenta como cambio y la API lo acepta, `gestion-de-prestaciones`).

Una respuesta `2xx` se valida en tiempo de ejecución (forma de `Prestacion`) sin `any`; una respuesta que no tiene la forma esperada se trata como `SinConexion`. Todo `4xx` pasa por `traducirRechazo` (T6).

### T6. Clases de rechazo y orden de evaluación — Propuesta (aplica RN-GL-02 y D208 desde el lado del cliente)

La interfaz no evalúa reglas: clasifica lo que recibe, en este orden (el mismo en que la API evalúa, así que nunca llegan dos a la vez):

| # | Clase | Origen | Error de TypeScript | Qué muestra la pantalla |
|---|---|---|---|---|
| 1 | Validación local | Nombre o duración vacíos; duración no entera (`required`, `type="number"`, `step="1"`) | — (no se envía nada) | El navegador marca el campo |
| 2 | Control de acceso | `401` → renovación o `SesionTerminada` (C-08 F8 y T4); `403` `RN-AU-05` | `SesionTerminada`, `PermisoInsuficiente` | Inicio de sesión con el aviso; mensaje de permiso (T11) |
| 3 | Validación de entrada (API) | `422`: error de campo `duracion_minutos` con `RN-AG-01`; error de campo `nombre` (código `null`); otro error de formato | `EntradaRechazada` con `codigos` y `errores` (`campo`, `codigo`) | Mensaje debajo del campo; mensaje general para un campo que la pantalla no tiene |
| 4 | Regla de negocio (API) | `409` `RN-AG-15` | `ReglaRechazada` con `codigos` | Mensaje debajo del nombre |
| 5 | Recurso de la URL (API) | `404` `RN-GL-04` en el `PATCH` | `RecursoInexistente` | Mensaje y recarga de la lista |
| 6 | Transporte | Red caída, `5xx`, cuerpo ilegible | `SinConexion` | Mensaje de conexión (y «Reintentar» en el listado) |

`EntradaRechazada` (de C-08) gana los campos `codigos: readonly string[]` y `errores: readonly ErrorDeCampo[]` sin romper su uso en el login. `rechazos.ts` lee el cuerpo `problem+json` (validación de tipos a mano, sin `any`) y es la **única** traducción de un `4xx` del panel, para que C-12 en adelante la reutilicen. Los tests verifican el código, no el texto.

### T7. Estado de la pantalla — Propuesta (aplica `vercel-react-best-practices`)

`PaginaPrestaciones` tiene dos estados con `useState`:

- **Listado**: `{ tipo: 'cargando' } | { tipo: 'lista', prestaciones } | { tipo: 'sin-conexion' }`. Una sola petición al montar, en un efecto con limpieza (bandera `vigente`) y dependencia primitiva (un contador de recarga que sube con «Reintentar» o tras un `404`). No hay cascadas: es una sola petición.
- **Panel lateral**: `{ modo: 'cerrado' } | { modo: 'alta' } | { modo: 'edicion', prestacion }`.

Con `201` se agrega la fila devuelta; con `200` se reemplaza por `id` (actualización funcional de `setState`). Lo que se puede calcular (si la lista está vacía, la acción de cada fila) se deriva en el render, no se copia en el estado. Mensajes de error de la pantalla (permiso, conexión, `404`) en un estado aparte que se limpia al abrir o cerrar el panel. Sin SWR ni TanStack Query: tres peticiones y ninguna duplicación (registro de la skill).

### T8. Tabla — Propuesta (referencia visual de Stitch)

Columnas: **Color** (muestra circular con nombre accesible «Color #43A047»), **Nombre**, **Duración** («45 min»), **Reserva online** («Sí»/«No»), **Estado** (insignia «Activa» o «Inactiva») y **Acciones** («Editar» y «Desactivar» o «Reactivar», con el nombre de la prestación en su nombre accesible, por ejemplo «Desactivar Limpieza»). Las filas inactivas se atenúan (opacidad) **y** llevan la insignia: el estado no depende solo del color. Mientras una acción de una fila espera respuesta, sus botones quedan deshabilitados. Desactivar no pide confirmación (es reversible con «Reactivar»). No hay acción de borrar (RN-GL-03).

### T9. Panel lateral de alta y edición — Propuesta (referencia visual de Stitch)

`<aside aria-labelledby>` junto a la tabla con el título «Nueva prestación» o «Editar prestación» y un `<form>` con:

- **Nombre**: `type="text"`, `required`. No se recorta ni se normaliza (lo hace la API).
- **Duración en minutos**: `type="number"`, `required`, `step="1"`, sin `min` ni múltiplo (D232), con la ayuda «Mayor que 0 y múltiplo de 5.» y, en la edición, el aviso de CA-3 «Cambiar la duración no modifica los turnos ya creados.».
- **Color**: selector de color (T10).
- **Ofrecer en la reserva online**: casilla.
- «Guardar» (primario; deshabilitado y «Guardando…» mientras espera) y «Cancelar».

Errores de campo debajo del campo, enlazados con `aria-describedby` y `aria-invalid`, con el texto de T11. Un error que no es de un campo (permiso, conexión) va en el **aviso del panel**, un aviso `role="alert"` arriba del formulario, y el panel sigue abierto con lo escrito y «Guardar» habilitado; el `404` cierra el panel (T11). En la edición, «Guardar» sin cambios cierra el panel sin pedir nada (escenario «guardar sin cambios no pide nada»). Al abrir, el foco va al nombre.

### T10. Selector de color — Decisión del autor (D233; Q5)

El selector **nativo** del navegador (`<input type="color">`), sin dependencia nueva, con la muestra y el valor hex al lado como texto de solo lectura (`<output>`). El navegador entrega el hex en minúsculas; la interfaz lo manda **en mayúsculas** (`#3A7BD5`), como el catálogo de la demo, para que la tabla no mezcle estilos. El alta empieza con `#1E88E5` (el color de «Consulta / control»; el control nativo necesita un valor). Como el control solo produce `#rrggbb`, el `422` de color inválido no se puede provocar desde la pantalla. Comprobar **V1**.

**Alternativas descartadas:** (a) un campo de texto hex editable: permite valores inválidos y suma un error de formato que la pantalla tendría que explicar; (b) una paleta fija de colores: es una decisión de producto que ninguna historia pide; (c) una biblioteca de selector de color: dependencia nueva sin necesidad.

### T11. Mensajes fijos de la pantalla — Propuesta (como F9 de C-08: no se muestra el `detail` de la API)

| Situación | Mensaje | Dónde |
|---|---|---|
| `422` `RN-AG-01` en `duracion_minutos` | «La duración debe ser mayor que 0 y múltiplo de 5 minutos (RN-AG-01).» | Debajo de la duración |
| `422` con error del campo `nombre` | «Ingresá un nombre.» | Debajo del nombre |
| `422` de otro campo o sin campo | «Revisá los datos de la prestación.» | Aviso del panel |
| `409` `RN-AG-15` | «Ya existe una prestación con ese nombre (RN-AG-15).» | Debajo del nombre |
| `403` `RN-AU-05` | «Tu usuario no tiene permiso para modificar prestaciones (RN-AU-05).» | Aviso del panel, que sigue abierto con lo escrito; si vino de una acción de fila, aviso de la tabla (arriba de la tabla) |
| `404` `RN-GL-04` | «La prestación ya no existe (RN-GL-04).» | Arriba de la tabla (se cierra el panel y se recarga la lista) |
| Sin conexión | «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» | Al guardar, aviso del panel (conserva lo escrito); en una acción de fila, aviso de la tabla (la fila no cambia); al listar, en lugar de la tabla con «Reintentar» |
| Lista vacía | «Todavía no hay prestaciones.» | En lugar de la tabla |
| Cargando | «Cargando prestaciones…» | En lugar de la tabla |

El «5 minutos» es la constante de D99; cuando US-005 (C-22) haga configurable la granularidad, el mensaje tendrá que salir del valor configurado (límite del README). El mensaje del `409` no repite el nombre existente, para no depender del `detail` del servidor.

### T12. Estilos — Propuesta (tokens de «Clinical Ops», ver «Referencia visual (Stitch)»)

CSS propio, sin dependencias ni preprocesador (Vite importa CSS de fábrica): `tokens.css` con variables (`--fondo: #F8FAFC`, `--superficie: #FFFFFF`, `--borde: #E2E8F0`, `--borde-fuerte: #CBD5E1`, `--primario: #0284C7`, `--error: #DC2626`, `--fondo-error: #FEF2F2`, `--exito: #16A34A`, `--fondo-exito: #F0FDF4`, `--encabezado-tabla: #F1F5F9`, `--radio: 4px`, `--radio-panel: 8px`, `--alto-fila: 40px`, `--alto-campo: 36px`, fuente `Inter, system-ui, sans-serif` con cifras tabulares) y `panel.css` con el encabezado, la tabla (encabezado en mayúsculas de 11 px, filas de 40 px, sin sombras), las insignias, el panel lateral y los errores de campo (borde rojo y mensaje debajo). Si Inter no está instalada se usa la fuente del sistema (Non-Goals). El color de cada muestra se aplica con la propiedad `style` de React (CSSOM), que la CSP de nginx no bloquea: comprobar **V2**.

### T13. Rol del usuario en la interfaz — Decisión del autor (D230; Q2)

La interfaz **no conoce el rol** (ninguna ruta lo informa y el token no lo lleva). «Nueva prestación», «Editar», «Desactivar» y «Reactivar» se muestran a todos; si el usuario no es odontólogo, la API responde `403` `RN-AU-05` y la pantalla muestra el mensaje de T11 (aviso del panel, con lo escrito conservado, o aviso de la tabla), sin cambiar nada ni tocar la sesión (el `403` no renueva, C-08 F8). Como la API evalúa el permiso antes que la entrada (D208), la recepcionista nunca ve un error de validación: con duración 47 ve `RN-AU-05` y no `RN-AG-01`. «Solo el odontólogo edita» lo garantiza la API (D205); la pantalla lo hace visible. Va como límite conocido del README.

**Alternativas descartadas** (detalle en D230): (a) `GET /auth/yo` con los roles: cambio de API, fuera de alcance de C-11; (b) ocultar los botones después del primer `403`: estado adivinado, y la recepcionista vería botones que desaparecen; (c) decodificar el JWT: no lleva roles.

### T14. Tests y servidor falso — Decisión del autor (D222, D227) + Propuesta (detalle)

- **Servidor falso**: `crearServidorFalso(opciones?)` acepta `prestaciones` iniciales (por defecto `[]`, para que los tests de C-08 no cambien) e implementa en memoria el contrato de `gestion-de-prestaciones`: `GET`, `POST` y `PATCH /api/prestaciones[/{id}]` con la normalización del nombre (espacios, mayúsculas y tildes), `422` `RN-AG-01` con su error de campo, `422` de formato (nombre vacío o solo de espacios, color inválido, campo desconocido) con `codigos` vacío, `409` `RN-AG-15` después de RN-AG-01, `404` `RN-GL-04`, cuerpos `problem+json` copiados del spec. **Roles**: la odontóloga tiene `odontologo` y `dueno`; la recepcionista, `recepcionista` (escribir da `403` `RN-AU-05` antes de validar la entrada, como la API por D208; leer `200`). `quitarPrestacion(id)` saca una prestación del falso después de listar, para el escenario de la prestación que ya no existe (la API no borra, RN-GL-03; en la demo pasa si la base se recrea con la pantalla abierta). La recepcionista sigue **inactiva para el login** (US-090 CA-3 de C-08); los tests de la pantalla la usan con una sesión emitida (`emitirSesion`) y un alias `EMAIL_RECEPCIONISTA` que lo explica. Se agrega un registro de los cuerpos recibidos por ruta, para verificar que el `PATCH` manda solo lo que cambió y que no hubo peticiones a rutas de turnos. Exportar el catálogo de partida (`PRESTACIONES_DE_PARTIDA`, con «Urgencia» inactiva) para los tests.
- **Capas**: (a) **unidad** de `apiPrestaciones.ts` y `rechazos.ts` con el falso y un `pedidoDelPanel` real de `clienteHttp`; (b) **componentes** con Testing Library y `user-event` sobre `<App/>` en un `MemoryRouter` en `/panel/prestaciones`, con sesión guardada como en `RutaProtegida.test.tsx`. El selector de color se cambia con `fireEvent.input` de Testing Library (no es un mock; **V1**).
- Nombres de test con el escenario (`it('US-001 CA-2: duración 47 muestra RN-AG-01 debajo del campo')`). Sin `vi.mock`, `vi.fn`, `vi.stubGlobal` ni temporizadores falsos: el guard de C-08 sigue valiendo.

### T15. README — Propuesta

Sección «Pantalla de prestaciones» dentro de «Panel (interfaz)»: cómo llegar, el recorrido con la demo (listar, crear, duración 47 → `RN-AG-01`, nombre repetido → `RN-AG-15`, editar color, desactivar y reactivar, la recepcionista → `RN-AU-05`), la tabla escenario → test (US-001 CA-1, CA-2, CA-3) con la cantidad real de tests, y límites conocidos nuevos: los botones de edición se ven para todos los roles y la API rechaza con `RN-AU-05` (T13); el mensaje de `RN-AG-01` dice 5 minutos hasta US-005 (T11); Inter solo si está instalada (T12); la demo arranca con todas las prestaciones activas.

### T16. Prueba en el navegador y tamaño — Propuesta

Prueba del agente con la demo (`crear_app_demo` + `npm run dev`) y en Compose (`http://127.0.0.1:5173`), recorriendo los escenarios contra la API real y revisando la pestaña de red (método, cuerpo, estado y `codigos`) y la consola (sin errores ni violaciones de CSP). Por ser gobernanza BAJO, la repetición del autor no va como tarea (regla `rules.tasks` de `config.yaml`): el agente le deja el paso a paso. **20 tareas en 9 grupos**, dentro del «alrededor de 20», para **33 escenarios**: los nueve que sumó la revisión de escenarios entran en las tareas RED y TRIANGULATE de su tema, sin tareas nuevas. Los estilos de Stitch se aplican en las tareas GREEN que crean cada pieza visual (no hay tarea aparte).

### Skills aplicadas

- `vercel-react-best-practices` (SPA de Vite; **no aplican** Next.js, RSC ni `server-*`). **Aplicadas:** una sola petición al montar, sin cascadas; sin imports *barrel*; estado derivado en el render; `setState` funcional al agregar o reemplazar filas; `useState` perezoso donde haya un valor inicial calculado; dependencias primitivas en el único efecto; ningún componente definido dentro de otro; ternario en vez de `&&` en el JSX; JSX estático (mensajes fijos) fuera de los componentes; búsqueda de la fila por `id` con un `Map` derivado si hace falta. **No aplicadas** (registro): SWR o TanStack Query (pocas peticiones, sin duplicación) y `React.lazy` (pantalla chica).
- `auth-implementation-patterns`: el servidor decide los permisos y la interfaz solo reacciona al `403` (T13); un `403` no toca la sesión.
- Las skills de Python, de base de datos y `multi-stage-dockerfile` no aplican: el backend, el esquema y las imágenes no cambian.

## Referencia visual (Stitch)

El orquestador usó el MCP de Stitch en este propose; la evidencia está en `docs/skills-mcp/evidencias/sesion-nueva/stitch-c11.md` (proyecto `projects/14200813501064679723`, «Turnos Odontológicos AR — C-11 panel-de-prestaciones», con el texto exacto enviado, solo datos ficticios del dominio y sin pacientes ni secretos). La generación de la pantalla superó el tiempo de espera y `list_screens` seguía vacío al cerrar la evidencia; lo que sí devolvió es el design system **«Clinical Ops»**.

**Qué decisiones fundamenta:**

- **Disposición**: tabla del catálogo con un **panel lateral** de alta y edición a la derecha (T8, T9), en lugar de un modal o de una página aparte.
- **Tokens** (T12): Inter, fondo `#F8FAFC`, superficies blancas con borde de 1 px, primario `#0284C7`, error `#DC2626` sobre `#FEF2F2`, éxito `#16A34A` sobre `#F0FDF4`, radio de 4 px en campos y botones, 6 a 8 px en paneles, filas de 40 px con encabezado `#F1F5F9` en mayúsculas de 11 px, insignias de estado de 22 px, campos de 36 o 40 px.
- **Errores de campo debajo del campo**, con borde rojo (T9, T11).
- **Filas inactivas atenuadas** con la insignia «Inactiva», sin salir de la lista (T8).
- La ayuda «Mayor que 0 y múltiplo de 5» bajo la duración y la nota sobre los turnos ya creados (T9, T11).

**Dónde manda la KB sobre Stitch:**

- El texto enviado decía «Nueva prestación (solo visible para el rol odontólogo)»; sin una ruta que informe el rol y sin cambios de API, la interfaz no puede saberlo (T13, D230).
- Los mensajes de error del texto enviado («La duración debe ser mayor que 0 y múltiplo de 5 (RN-AG-01)», el del nombre repetido con el nombre) se ajustan a los de T11.
- La nota de CA-3 va en el panel de edición, junto a la duración (spec), y no bajo la tabla.
- Stitch no agrega reglas de dominio ni comportamiento: es referencia visual. Ante cualquier conflicto se siguen la KB y el spec.

## Contradicciones y huecos encontrados en las fuentes

1. **«Solo el rol `odontologo` edita, los demás leen» (`CHANGES.md` C-11) vs. ninguna ruta que informe el rol y «cambios de API» fuera de alcance.** → T13 y D230: la API decide y la pantalla muestra el `403`.
2. **El cableado de `SesionTerminada` en `ProveedorDeSesion` está en el alcance de C-09** (`CHANGES.md`, por la nota de C-08), pero C-11 es el primer change que usa `pedidoDelPanel` y puede aplicarse antes. → T4 y D231: lo cablea C-11; al archivar se quita de la entrada de C-09.
3. **«Muestra el error de dominio RN-AG-01» vs. un formulario que podría validarlo solo** (`min`, `step=5`): si el navegador bloquea el 47, el error de dominio nunca se ve. → T9 y D232: la interfaz no valida la duración.
4. **RN-AG-01 es «validación de entrada» (`422`) en `05` y en `gestion-de-prestaciones`, pero US-001 CA-2 lo llama «error de dominio»** y el spec de C-04 tituló su escenario «Error de negocio». → Se mantiene el título de C-04 para CA-2 (convención de los escenarios) y T6 lo clasifica como validación de entrada, como la API.
5. **La demo arranca con las cinco prestaciones activas**; el spec usa «Urgencia» inactiva para los escenarios de la suite. → El spec lo aclara en sus convenciones; la prueba en el navegador la desactiva primero desde la pantalla.
6. **En el servidor falso de C-08 la recepcionista es la usuaria inactiva del login** (US-090 CA-3); para C-11 hace falta una recepcionista con sesión y rol. → T14: sesión emitida y alias documentado, sin cambiar los tests de C-08.
7. **La granularidad de 5 minutos** se escribe en la ayuda y en el mensaje (D99); con US-005 deja de ser fija. → Límite del README (T11).
8. **No hay CSS en el frontend** y la CSP de nginx es `default-src 'self'`. → T12: CSS propio servido por el mismo origen y colores dinámicos por CSSOM (V2).

## Risks / Trade-offs

- [La recepcionista ve botones que terminan en `403`] → Mensaje claro con `RN-AU-05` y límite del README; si molesta, la alternativa (b) de D230 (una ruta de roles) en otro change.
- [El servidor falso puede apartarse de la API real] → Cuerpos copiados de `gestion-de-prestaciones` y de `api/errores.py`; la prueba en el navegador repite los escenarios contra la API real (T16).
- [El mensaje de RN-AG-01 dice 5 minutos aunque la granularidad cambie] → Límite del README; C-22 lo actualiza.
- [Dos pestañas editando la misma prestación] → La última gana (la API no tiene control de versiones); la fila muestra lo que devolvió la API. Fuera de alcance.
- [Un `404` en la demo tras reiniciarla] → La pantalla recarga la lista (T11); los ids de la demo son fijos.
- [El selector nativo de color se ve distinto en cada navegador] → Aceptado: sin dependencia nueva; el valor hex se muestra siempre al lado.

## A verificar en el change

- **V1** (antes de cerrar la tarea 4.2): que jsdom 30.1.2 admite `<input type="color">` y que `fireEvent.input` de Testing Library cambia su valor y dispara el `onChange` de React; si no, se usa `fireEvent.change`. En el navegador (tarea 8.1), que Chrome entrega el hex en minúsculas y la interfaz lo manda en mayúsculas.
- **V2** (antes de cerrar la tarea 8.1, en Compose): que con la CSP de `nginx.conf` las muestras de color (propiedad `style` de React) y el CSS construido se ven sin violaciones en la consola.
- **V3** (antes de la tarea 3.1): que React Router 7.18.4 renderiza las rutas hijas (`index`, `prestaciones`, `*`) de `path="/panel"` dentro del `<Outlet/>` de `PanelBase` y que `/panel/algo` sigue mostrando «Panel del consultorio» sin cambiar la URL (los tests de C-08 siguen en verde).
- **V4** (antes de la tarea 2.1): que la API real responde al nombre «   » con `422`, `codigos` vacío y un error con `campo` `nombre` (leyendo `backend/tests/api/test_prestaciones.py` o con la demo), para copiarlo tal cual en el servidor falso.

## Migration Plan

1. Con el ok del autor, se commitean los artefactos de este propose y, en un commit `docs(kb)` aparte, las decisiones D229 a D233 ya registradas en `knowledge-base/10_preguntas_abiertas.md`.
2. El Apply cambia solo `frontend/` y `README.md`; no hay migración, variables ni imágenes nuevas. `docker compose up --build -d` reconstruye el contenedor `frontend`.
3. **Vuelta atrás:** revertir los commits del change; la API y la base no se tocaron.

## Notas para el archive

No se editan ahora ni durante el Apply:

- `CHANGES.md`: marcar C-11 con `[x]`; por D231, quitar de la entrada de C-09 «cablear `pedidoDelPanel` y `SesionTerminada` en `ProveedorDeSesion`»; repetir `scripts/verificar_changes.py`.
- `knowledge-base/10_preguntas_abiertas.md`: D229 a D233 ya están registradas (2026-10-19); al cerrar se registran las demás decisiones «Propuesta» que el autor apruebe con el plan y los hallazgos del Apply (V1 a V4).
- `CLAUDE.md` y `AGENTS.md`: re-sincronizar el párrafo «Estado de `10_preguntas_abiertas.md`» con D229 a D233 (no se editan en el update).
- `knowledge-base/08_arquitectura_propuesta.md`, «Estructura de directorios»: `features/prestaciones/` y `shared/estilos/` (T3).
- `knowledge-base/06_funcionalidades.md`, US-001: nota de que la pantalla llegó con C-11 (como la de la API en CA-1).
- `docs/skills-mcp/evidencias/sesion-nueva/stitch-c11.md`: si la pantalla de Stitch aparece después, agregarla (la evidencia ya lo prevé).

## Open Questions

Ninguna. Las cinco preguntas del propose quedaron cerradas por el autor el 2026-10-19, todas con la recomendación del agente:

- **Q1 → D229.** Capability nueva `pantalla-de-prestaciones`; `gestion-de-prestaciones` sigue describiendo solo la API (T1).
- **Q2 → D230.** «Nueva prestación», «Editar», «Desactivar» y «Reactivar» visibles para todos los roles; la API rechaza con `403` `RN-AU-05` y la pantalla lo muestra sin tocar la sesión. Sin `GET /auth/yo` (T13).
- **Q3 → D231.** C-11 cablea `pedidoDelPanel` y `SesionTerminada` en `ProveedorDeSesion`; la entrada de C-09 en `CHANGES.md` se ajusta al archivar, no ahora (T4).
- **Q4 → D232.** Sin validación de la duración en el navegador (solo `required` y entero): 47, 0 y -5 llegan a la API y la pantalla muestra su `RN-AG-01` (T9).
- **Q5 → D233.** Selector nativo `<input type="color">`, con el hex visible y enviado en mayúsculas; el alta empieza en `#1E88E5` (T10).
