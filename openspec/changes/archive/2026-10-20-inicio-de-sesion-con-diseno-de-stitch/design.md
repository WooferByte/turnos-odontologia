# Design: inicio-de-sesion-con-diseno-de-stitch

Fecha del design: **2026-10-20**. Gobernanza **MEDIO** (D240; ver `proposal.md`, «Gobernanza»).

**Respuesta del autor (2026-10-20): las seis preguntas abiertas se cierran con la recomendación del agente.** Quedan como decisiones del autor D235 (Q1, código C-49 al final del índice), D236 (Q2, L9: el «Cargando…» entra e `InicioDelPanel` no), D237 (Q3, L10: sin subtítulo), D238 (Q4, L6: ícono de espera), D239 (Q5, L8: estilos en `panel.css`) y D240 (Q6, gobernanza MEDIO), registradas en `knowledge-base/10_preguntas_abiertas.md`. Las demás decisiones marcadas «Propuesta» siguen así hasta que el autor apruebe el plan completo. En la misma revisión (`/opsx:update`) se incorporó el informe de `revisor-de-escenarios` (`revision-de-escenarios.md`, el «antes»): la spec pasa de 6 a **7 escenarios** (H1: US-090 CA-3 con escenario propio; H2: el de sesión terminada es US-092 CA-1; H3: la vuelta a «Ingresar» sin conexión dentro del escenario del botón; H4: STI-1 separa lo que verifica la suite de lo que verifica el navegador; H5: el ícono queda fijado por D238) y las tareas siguen siendo **16**. De los tres bordes sugeridos se adoptan dos (la usuaria inactiva, H1, y el ancho de 375 px en la prueba del navegador, L12); el del mensaje del `422` se descarta (ver «Contradicciones y huecos», punto 6).

Las decisiones se numeran **L1 a L12** («L» de *login*) para no confundirlas con las D1..D234 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores (D de C-01, I de C-02, H de C-03, P de C-04, S de C-05, J de C-06, R de C-07, F de C-08, T de C-11). Cada una dice si es **Decisión del autor** (ya tomada en la KB o en el pedido del 2026-10-20), **Propuesta** (elección de este design, a confirmar) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»).

## Context

Motivación y alcance: ver `proposal.md`. Requisitos: `specs/ingreso-al-panel/spec.md` (delta: un requisito nuevo).

**Lo que dejaron C-08 y C-11** (leído del código, no supuesto):

- **`frontend/src/features/ingreso/PaginaIngreso.tsx`** (C-08, F9): `<main>` con `<h1>Turnos Odontológicos AR</h1>` y un `<form method="post">` con `label`/`input` de «Email» (`type="email"`, `autoComplete="username"`) y «Contraseña» (`type="password"`), luego el aviso de sesión terminada (`<p role="status">`), luego el problema (`<p role="alert">` con uno de tres mensajes fijos: el genérico de RN-AU-04, «Revisá el email y la contraseña.» y el de conexión) y el botón `submit` («Ingresar» / «Ingresando…», `disabled` mientras espera). Mientras el proveedor verifica la sesión devuelve `<p>Cargando…</p>`. **Ninguna `className`.**
- **`ProveedorDeSesion.tsx`**: `iniciarSesion` borra el aviso (`setAviso(null)`) antes de enviar, así que el aviso de sesión terminada desaparece en cuanto se reintenta (comportamiento vigente que el spec delta hace explícito, no lo cambia).
- **`frontend/src/pages/RutaProtegida.tsx`**: también devuelve `<p>Cargando…</p>` sin clase; `InicioDelPanel.tsx` es un `<h1>Panel del consultorio</h1>` sin clase, pero se ve dentro de `PanelBase` (barra superior y `.contenido` de C-11).
- **Estilos de C-11** (`frontend/src/shared/estilos/`, importados en `main.tsx`): `tokens.css` (colores, radios, alturas, `--fuente: Inter, system-ui, sans-serif`, `body` con fondo `--fondo`) y `panel.css` (533 líneas: `.icono`, `.boton-primario`, `.aviso` y `.aviso-error` con ícono, `.campo`, `.campo label` en mayúsculas, `.ayuda`, `.nota-informativa`, …). Los selectores de campo de `panel.css` solo cubren `input[type='text']` y `input[type='number']`: **los campos `email` y `password` del login no quedan cubiertos**. `.campo label` pone las etiquetas en mayúsculas, que la pantalla de Stitch del login no usa (L5).
- **Íconos** (`frontend/src/shared/iconos/`): `Icono` (SVG en línea, `aria-hidden`, `focusable="false"`), `IconoDiente`, `IconoAlerta`, `IconoInfo`, entre otros. No hay ícono de espera.
- **`Aviso.tsx`** de prestaciones agrega un **título** dentro del `role="alert"` («Acceso restringido», «Sin conexión»). En el login eso rompería los tests vigentes, que comparan el `textContent` del `alert` con el mensaje exacto (`PaginaIngreso.test.tsx`, CA-2 y CA-3), y el requisito «los dos rechazos se ven idénticos».
- **Tests vigentes**: 8 en `PaginaIngreso.test.tsx` y 10 en `RutaProtegida.test.tsx` (por nombre de escenario), más los guards (`src/test/guards.test.ts`: sin `any`, sin `vi.mock`/`vi.fn`/`vi.stubGlobal`/`useFakeTimers`, sin `localStorage` ni `dangerouslySetInnerHTML`, sin *barrels*). El servidor falso (`src/test/servidorFalso.ts`) ya tiene `retener`, `caerse` y `emitirSesion`.
- **CSP de nginx** (`frontend/nginx.conf`): `default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`.

## Goals / Non-Goals

**Goals:**

- Que `/ingresar` se vea como la pantalla de Stitch, con los tokens y estilos de C-11, sin dependencias nuevas.
- Que ningún comportamiento de `ingreso-al-panel` cambie: los 18 tests vigentes siguen en verde **sin modificarse**.
- Que lo visual con efecto observable (título, orden y contenido de los avisos, nombre del botón de espera, ningún recurso de otro origen) quede en escenarios con test.

**Non-Goals:**

- Cambiar mensajes, rutas, sesión, almacenamiento, renovación o el proveedor de sesión.
- Backend, API, Compose, `nginx.conf` o `frontend/package.json` (y su `package-lock.json`).
- Un sistema de componentes de formulario reutilizable entre el login y prestaciones; un diseño para celulares; modo oscuro.
- Cargar o empaquetar Inter (como en C-11: se usa si está instalada), Tailwind o Material Symbols.
- Rediseñar el panel base o la pantalla de prestaciones (C-11).

## Decisions

### L1. Un requisito nuevo en `ingreso-al-panel` — Decisión del autor (pedido del 2026-10-20; regla dura 12) + Propuesta (forma)

El autor pidió un change solo de interfaz sobre la capability existente. Los requisitos vigentes no cambian (no hay `MODIFIED`); se agrega uno (`ADDED`) con siete escenarios de presentación que sí son observables. **Alternativa descartada:** `skip_specs: true` (sin delta): dejaría sin escenario lo que el change promete (el aviso con el texto exacto, el orden de los avisos, el botón de espera y la ausencia de recursos externos) y el revisor de escenarios no tendría qué controlar. **Alternativa descartada:** una capability nueva de «estilos»: rompería la regla 12 y separaría la pantalla de su comportamiento.

### L2. Estructura del marcado — Propuesta (pantalla de Stitch)

`PaginaIngreso` pasa a: `<main className="pantalla-de-ingreso">` → `<section className="tarjeta-de-ingreso" aria-labelledby=…>` → encabezado de la tarjeta (`IconoDiente` + `<h1>Turnos Odontológicos AR</h1>`) → aviso de sesión terminada (si corresponde) → `<form>` con los dos campos, el aviso de problema y el botón. Se mantienen: el `h1` y su texto, los `id`/`htmlFor`, `name`, `type`, `autoComplete` y `required` de los campos, el `method="post"`, el `role` y el texto de cada aviso, y el texto del botón. Los mensajes siguen como constantes fuera del componente (F9, `vercel-react-best-practices`).

### L3. Orden de los avisos — Propuesta (pantalla de Stitch; spec «el aviso de sesión terminada va antes de los campos»)

- **Sesión terminada** (`role="status"`), **arriba de los campos**, como en la tarjeta de referencia de Stitch: es un estado de la llegada a la pantalla, no del envío. Hoy está entre la contraseña y el botón; moverlo no cambia su rol ni su texto.
- **Problema del envío** (`role="alert"`), **entre la contraseña y el botón**, como en la tarjeta principal de Stitch (es el lugar actual).

### L4. Avisos con ícono y sin título — Propuesta (pantalla de Stitch) + Decisión del autor (RN-AU-04, mensajes fijos de F9)

Cada aviso lleva un ícono SVG en línea decorativo (`IconoAlerta` en el de error, `IconoInfo` en el informativo) y el mensaje en un único elemento de texto. **No** lleva título (a diferencia de `Aviso.tsx` de C-11) ni código RN visible: el `textContent` del `alert` tiene que seguir siendo exactamente el mensaje (tests de C-08 y escenario de error del delta). No se reutiliza `features/prestaciones/Aviso.tsx` (agrega el título y vive en otra *feature*); se reutilizan sus clases `.aviso` y `.aviso-error` de `panel.css` y se agrega `.aviso-informativo` (fondo `--primario-suave`, borde `--primario-borde`, ícono y texto en el tono primario oscuro, que hoy no es token: se suma `--primario-oscuro` en `tokens.css`, sin repetir valores sueltos).

### L5. Campos y etiquetas — Propuesta (pantalla de Stitch)

Etiquetas en tipografía normal y peso medio, **sin mayúsculas** (así se ven en la pantalla de Stitch del login; la de prestaciones las usa en el panel lateral), campos de 40 px de alto (`--alto-campo-grande`, nuevo token; «Clinical Ops» define 36 y 40 px) con borde `--borde-fuerte`, radio `--radio` y foco con el borde y el anillo del primario. Se agregan como clases propias del login (`.campo-de-ingreso`), sin tocar `.campo` de C-11, para no cambiar la pantalla de prestaciones.

### L6. Botón y estado de espera — Propuesta (pantalla de Stitch); el ícono, Decisión del autor (D238; Q4)

Botón primario de ancho completo y 40 px (`.boton-primario` de C-11 más `.boton-ancho-completo`). Mientras espera: deshabilitado, más claro y con el texto «Ingresando…». **Ícono de espera (D238; Q4):** un `IconoEspera` nuevo en `shared/iconos/` (SVG en línea con `aria-hidden`, sin texto, así el nombre accesible sigue siendo «Ingresando…»), animado con `@keyframes` en `panel.css` y **sin animación** bajo `prefers-reduced-motion: reduce`.

### L7. Disposición de la página — Propuesta (pantalla de Stitch)

`.pantalla-de-ingreso` ocupa el alto de la ventana y centra la tarjeta en los dos ejes sobre `--fondo`; la tarjeta mide hasta 400 px de ancho (`max-width`, así no desborda en un ancho chico), con superficie blanca, borde de 1 px, radio `--radio-panel`, relleno de 32 px y la sombra suave `--sombra-tarjeta` que ya usa C-11. Encabezado de la tarjeta: ícono de diente en el primario (28 px) y la marca en 18 px semibold. **Sin barra superior ni pie** (L10).

### L8. Estilos y archivos — Decisión del autor (D239; Q5)

**Decisión del autor (D239; Q5).** Los estilos del login van en una sección nueva de `panel.css` («Pantalla de inicio de sesión»), con valores tomados de `tokens.css`; los tokens nuevos (L4, L5) se agregan a `tokens.css`. **Alternativa considerada:** un `ingreso.css` aparte importado desde `PaginaIngreso.tsx`: separa mejor, pero `main.tsx` es hoy el único lugar que importa CSS y C-11 dejó todo el panel en un archivo; se prefiere no abrir un segundo patrón. Ninguna dependencia nueva: Vite importa CSS de fábrica.

### L9. «Cargando…» de la verificación de sesión — Decisión del autor (D236; Q2)

Hoy, mientras el proveedor verifica, `PaginaIngreso` y `RutaProtegida` muestran un `<p>Cargando…</p>` sin estilo. **Decisión (D236):** se le da la misma disposición centrada (`.pantalla-de-ingreso`) con el texto en `--texto-tenue`, sin tarjeta ni ícono, en los dos lugares, con el texto y el elemento sin cambios (`US-092 CA-1` «mientras verifica la sesión no muestra el panel» sigue igual). No hay pantalla de Stitch para este estado; se apoya en la de ingreso (es el mismo fondo y la misma disposición). `InicioDelPanel.tsx` queda **fuera** (D236): ya se ve dentro de la barra y el contenido de C-11 y su contenido lo definirá la pantalla que lo reemplace.

### L10. Qué se rechaza de la pantalla de Stitch — Decisión del autor (D234: la KB y la spec mandan) + Propuesta (detalle)

- **Barra superior** con «Turnos Odontológicos | Acceso Seguro de Operatoria» y la insignia **«Servidor Clínico Operativo»**: inventa un estado del servidor que ninguna ruta informa (no hay ruta de salud en `02`) y repite la marca de la tarjeta. Tampoco se toma la barra del panel de C-11: sin sesión no hay navegación ni «Cerrar sesión».
- **Pie** «Turnos Odontológicos AR · Módulo de Control de Acceso Clínico · Sede Central»: ninguna fuente de la KB habla de «sedes» ni de «módulos»; texto sin respaldo.
- **Subtítulo** «Acceso al panel administrativo» (D237; Q3): texto que ninguna fuente pide y que el spec no tiene.
- **Las etiquetas «Referencia: Sesión expirada» y «Referencia: Estado de carga»** y los puntos de color de esas tarjetas: son marcas del lienzo de Stitch para mostrar estados, no parte de la pantalla. La pantalla muestra un estado por vez.
- **Campos deshabilitados** en las tarjetas de referencia (la de sesión terminada muestra el formulario deshabilitado): el formulario del spec está siempre habilitado salvo el botón mientras espera.
- **El valor de ejemplo de la contraseña** que el HTML de la tarjeta «Estado de carga» trae en un campo deshabilitado (texto ficticio generado por Stitch, no un secreto del proyecto): no se copia nada del HTML tal cual.
- **El placeholder `••••••••`** del campo contraseña: la pantalla actual no tiene placeholders y un placeholder no reemplaza la etiqueta; no aporta.
- **Tailwind, Google Fonts (Inter) y Material Symbols** por CDN: la CSP `default-src 'self'` los bloquea y serían dependencias nuevas; se traducen a CSS propio y a SVG en línea (`IconoDiente`, `IconoAlerta`, `IconoInfo` ya existen).
- **Los colores del tema Material de Stitch** (`primary: #006194`, `error: #ba1a1a`, …) que aparecen en el HTML: se usan los tokens de «Clinical Ops» ya traducidos en `tokens.css` (primario `#0284C7`, error `#DC2626`), como en C-11.

### L11. Tests — Decisión del autor (D222, D227) + Propuesta (detalle)

- Los tests nuevos van en `PaginaIngreso.test.tsx` (incluido el de la usuaria inactiva, que compara texto, rol y lugar del aviso con los del escenario de la contraseña incorrecta; y uno en `RutaProtegida.test.tsx` para el aviso de sesión terminada, `US-092 CA-1`, que necesita un refresh rechazado al recargar), sobre `<App/>` en un `MemoryRouter` con el servidor falso inyectado; **sin `vi.mock`, `vi.fn` ni temporizadores falsos**. Nombres con el escenario: `it('US-090 CA-2: el rechazo se muestra en el aviso de error con el mensaje exacto')`.
- El orden de los elementos se verifica con `compareDocumentPosition` (aviso antes del campo «Email»; aviso de error después de «Contraseña» y antes del botón), no con clases CSS: **ningún test depende de una clase ni de un estilo** (como en C-11).
- STI-1 en la suite: un caso nuevo en `guards.test.ts` que falla si algún archivo de `frontend/src` o `frontend/index.html` contiene `http://` o `https://` en un `@import`, `url(`, `<link`, `<script` o un `src`/`href` (Tailwind, Google Fonts o Material Symbols por CDN); la parte de la consola del navegador se verifica en la prueba del agente (L12). **A verificar en el change (V2)**.
- Los 18 tests vigentes no se editan; si alguno falla por el marcado, se corrige el marcado, no el test (Safety net de TDD estricto).

### L12. Prueba en el navegador y comparación con la captura — Propuesta (regla `rules.tasks` de D234)

Con la demo (`crear_app_demo` + `npm run dev`) y después con Compose (`http://127.0.0.1:5173`): abrir `/ingresar`, rechazo con contraseña incorrecta, usuaria inactiva, espera (con la red lenta del navegador o con la API detenida un momento para ver «Ingresando…» y después el mensaje de conexión), ingreso válido, y sesión terminada (reiniciar la demo, cuyo secreto es efímero (D196), y recargar `/panel`: el refresh guardado deja de valer). **Comparar con `docs/skills-mcp/evidencias/sesion-nueva/stitch-ingreso-pantalla/pantalla.png`** (tarjeta principal con el error; tarjeta de sesión terminada; tarjeta de espera): disposición, jerarquía, estados y textos, anotando las diferencias y su motivo (las de L10 son esperadas). Consola sin violaciones de CSP. Además, con la ventana a 375 px de ancho, la tarjeta no desborda horizontalmente (lo único que se cuida para pantallas chicas; sin escenario porque jsdom no calcula la disposición). Por gobernanza MEDIO (D240), la repetición del autor es opcional: el agente le deja el paso a paso.

### Skills aplicadas

- `vercel-react-best-practices` (SPA de Vite; **no aplican** Next.js, RSC ni `server-*`). **Aplicadas:** JSX estático (mensajes) fuera del componente; ningún componente definido dentro de otro; ternario en vez de `&&` en el JSX (como ya está); sin *barrels*. **No aplicadas:** memoización (pantalla chica, sin listas).
- `auth-implementation-patterns`: el mensaje genérico idéntico para los tres rechazos (RN-AU-04) se conserva; el diseño no agrega pistas (ni código RN visible, ni un título distinto por causa).
- Las skills de Python, de base de datos y `multi-stage-dockerfile` no aplican: el backend, el esquema y las imágenes no cambian.

### Clases de rechazo y orden de evaluación

No cambian (regla de `config.yaml` para el design): la interfaz no valida nada nuevo. Siguen las de C-08: campos vacíos no se envían (validación del navegador con `required`); `401` del login → mensaje genérico (RN-AU-04, la API decide); `422` → «Revisá el email y la contraseña.»; red caída o `5xx` → mensaje de conexión. El orden de evaluación es el de la API (`sesion-del-panel`).

### Versiones (pins)

Ninguna dependencia nueva ni cambio de versión: `frontend/package.json` y `package-lock.json` no cambian (regla de `config.yaml` para el design).

## Referencia visual (Stitch)

**Regla (D234, Decisión del autor):** toda pantalla del frontend se implementa a partir de una pantalla generada en Stitch con el design system del proyecto; el design cita el id de la pantalla; si Stitch no entrega la pantalla, el change de interfaz no se cierra; la KB y el spec mandan sobre el contenido.

**Pantalla:** `projects/14200813501064679723/screens/d62ed0eb0edc43df833c9b24a24942b6`, «Inicio de sesión - Turnos Odontológicos AR», generada el 2026-10-20 en el proyecto de C-11 con el design system «Clinical Ops» (`assets/b683d44391ab410db2dd48aa71ed0b47`), de escritorio, modelo `GEMINI_3_8_FLASH`, estado `COMPLETE` (sin timeout). Muestra tres tarjetas: la principal con el rechazo (RN-AU-04), una de referencia con el aviso de sesión terminada y otra con el botón «Ingresando…». **Evidencia:**

- `docs/skills-mcp/evidencias/sesion-nueva/stitch-ingreso.md`: el texto enviado (solo textos de la spec y datos ficticios, sin pacientes ni secretos), el id y lo que devolvió;
- `docs/skills-mcp/evidencias/sesion-nueva/stitch-ingreso-pantalla/pantalla.png`: la captura (1280 × 1024) con la que se compara la implementación (L12);
- `docs/skills-mcp/evidencias/sesion-nueva/stitch-ingreso-pantalla/pantalla.html`: el HTML generado (Tailwind, Google Fonts y Material Symbols por CDN): **no se copia**; se traduce a los tokens de `frontend/src/shared/estilos/` (L4 a L8).

**Qué se toma** (todo visual; lo observable tiene escenario en el delta):

- Tarjeta centrada de unos 400 px sobre el fondo claro, con borde de 1 px, radio de 8 px y sombra suave (L7).
- Marca con el ícono de diente y «Turnos Odontológicos AR» como título (escenario feliz 1; el texto ya era el `h1`).
- Etiquetas sobre cada campo, sin mayúsculas; campos de 40 px; foco con el primario (L5).
- Aviso de error con ícono de alerta, fondo y borde rojo suave, **sin título ni código**, entre la contraseña y el botón, igual para los tres rechazos de RN-AU-04 y para el mensaje de conexión (L3, L4; escenarios de error de CA-2 y CA-3 y el borde del botón).
- Aviso informativo de sesión terminada con ícono «i», fondo celeste suave, **arriba de los campos** (L3, L4; escenario de borde).
- Botón primario de ancho completo «Ingresar»; en espera, deshabilitado, más claro, con ícono de espera y «Ingresando…» (L6; escenario de borde).

**Qué se rechaza:** ver L10 (barra superior, insignia del servidor, pie, subtítulo, etiquetas «Referencia», campos deshabilitados, placeholder, CDN y colores del tema Material).

**Dónde manda la KB sobre Stitch:** los textos de los avisos son los de `ingreso-al-panel` (Stitch los reprodujo exactos, porque se le enviaron); RN-AU-04 exige el mismo aviso para los tres rechazos, así que no se agrega un título que pudiera variar; la pantalla no ofrece recuperación de contraseña ni registro (fuera de la v1).

## Contradicciones y huecos encontrados en las fuentes

1. **C-08 ya está archivado y CHANGES.md no tiene un change para el ajuste visual.** → Change nuevo C-49 (pedido del autor). Los códigos de `CHANGES.md` deben ser consecutivos **en el orden en que aparecen** (fila 12 de `scripts/verificar_changes.py`), así que C-49 no puede ir dentro de la fase 3 sin renumerar C-14 a C-48 (y cada cita de esos códigos). → D235 (Q1): sección nueva al final, Orden 3.
2. **D234 pide una pantalla de Stitch para «toda pantalla»**, pero el «Cargando…» de la verificación y `InicioDelPanel` no tienen una propia. → D236 (Q2): el «Cargando…» entra con la disposición del ingreso; `InicioDelPanel` queda fuera.
3. **La pantalla de Stitch de prestaciones pone las etiquetas en mayúsculas y la del login no.** → Se sigue la del login, con clases propias, sin tocar la de C-11 (L5).
4. **`Aviso.tsx` de C-11 agrega un título dentro del `alert`**, que en el login rompería RN-AU-04 tal como la verifican los tests de C-08 (`textContent` exacto). → L4: avisos sin título.
5. **La gobernanza**: CHANGES.md clasifica la autenticación como CRITICO, pero este change no toca la autenticación. → D240 (Q6): MEDIO.
6. **El mensaje «Revisá el email y la contraseña.»** (respuesta `422` del login) existe en el código de C-08 (F9) pero no en la spec principal de `ingreso-al-panel`. → No se le agrega escenario: sería sumar un mensaje al contrato de la capability, no su presentación; el aviso lo muestra el mismo componente que el genérico, así que hereda el diseño sin test propio. Queda para el autor si quiere incorporarlo a la spec en otro change.

## Risks / Trade-offs

- [Mover el marcado cambia sin querer un rol, un texto o el orden que verifican los tests de C-08] → Los 18 tests vigentes se corren antes (red de seguridad) y después de cada paso y no se editan; los escenarios nuevos fijan el orden de los avisos.
- [El ícono de espera animado molesta o distrae] → Sin animación con `prefers-reduced-motion: reduce` (D238).
- [Inter no está instalada en el equipo del consultorio] → Se ve con la fuente del sistema, como C-11; límite ya conocido del README.
- [`panel.css` crece y mezcla login y panel] → Sección propia con su comentario; L8 deja anotada la alternativa del archivo aparte.
- [La captura de Stitch muestra tres tarjetas a la vez y la pantalla real un solo estado] → La comparación de L12 se hace estado por estado.

## A verificar en el change

- **V1** (antes de cerrar la tarea 2.2): que `compareDocumentPosition` en jsdom 30.1.2 informa el orden de documento esperado entre el `status`, el campo «Email», el `alert` y el botón (si no, se usa el índice en `querySelectorAll('*')`).
- **V2** (antes de cerrar la tarea 4.1): que el guard nuevo de STI-1 no da falsos positivos con lo que ya hay en `frontend/src` (por ejemplo, URLs en comentarios o el `xmlns` de un SVG); si los da, se acota el patrón a `@import`, `url(`, `<link`, `<script`, `src=` y `href=` con `http(s)://`.
- **V3** (antes de cerrar la tarea 5.1, en Compose): que con la CSP de `nginx.conf` la pantalla se ve sin violaciones en la consola (estilos, íconos SVG en línea y la animación del ícono de espera).
- **V4** (antes de cerrar la tarea 3.2): que los estilos nuevos no cambian la pantalla de prestaciones (se abre `/panel/prestaciones` en la demo y se compara con `stitch-c11-pantalla/implementacion.jpg`).

## Migration Plan

1. Con el ok del autor, se commitean los artefactos de este propose, la entrada C-49 de `CHANGES.md` y la evidencia de Stitch.
2. El Apply cambia solo `frontend/src/` y `README.md`; no hay migración, variables ni imágenes nuevas. `docker compose up --build -d` reconstruye el contenedor `frontend`.
3. **Vuelta atrás:** revertir los commits del change; la API, la base y el comportamiento no se tocaron.

## Notas para el archive

No se editan ahora ni durante el Apply:

- `CHANGES.md`: marcar C-49 con `[x]` y repetir `scripts/verificar_changes.py`.
- `knowledge-base/10_preguntas_abiertas.md`: D235 a D240 ya están registradas (update del 2026-10-20); al cerrar se registran las demás decisiones «Propuesta» que el autor apruebe con el plan y los hallazgos del Apply (V1 a V4).
- `openspec/config.yaml`: el comentario de cabecera dice «D1..D234»; pasa a «D1..D240».
- `CLAUDE.md` y `AGENTS.md`: «48 changes en 9 fases» del «Roadmap de Changes» pasa a 49, y el párrafo «Estado de `10_preguntas_abiertas.md`» suma D235 a D240 (re-sincronizar los dos; regla del encabezado de esos archivos).
- `docs/skills-mcp/evidencias/sesion-nueva/stitch-ingreso.md`: sumar el resultado de la comparación de L12 y la captura de la implementación.

## Open Questions

Ninguna. Las seis preguntas del propose quedaron cerradas por el autor el 2026-10-20, todas con la recomendación del agente:

- **Q1 → D235.** `C-49`, en la sección «Changes agregados después del índice original» al final de `CHANGES.md`, con Orden 3 y su nodo en el bloque 3 bajo C-08 con `(C-11)`.
- **Q2 → D236.** El «Cargando…» de la verificación de sesión entra con la disposición de la pantalla de ingreso (L9); `InicioDelPanel` queda fuera.
- **Q3 → D237.** Se rechaza el subtítulo «Acceso al panel administrativo» (L10).
- **Q4 → D238.** Ícono de espera en SVG en línea, decorativo y sin animación con `prefers-reduced-motion` (L6).
- **Q5 → D239.** Sección nueva en `panel.css` y tokens nuevos en `tokens.css` (L8).
- **Q6 → D240.** Gobernanza MEDIO.
