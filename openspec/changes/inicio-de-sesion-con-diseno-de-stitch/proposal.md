# Proposal: inicio-de-sesion-con-diseno-de-stitch

Change **C-49** de `CHANGES.md` (D235), historia **US-090** (parte de interfaz: el aspecto de la pantalla de inicio de sesión que construyó C-08). Gobernanza **MEDIO** (D240; ver «Gobernanza»). Depende de C-08 (`panel-base-e-inicio-de-sesion`) y de C-11 (`panel-de-prestaciones`), los dos archivados. Lo pidió el autor el 2026-10-20: un change nuevo, solo de interfaz, en lugar de sumarlo a C-09.

**Actualización del 2026-10-20 (`/opsx:update`).** El autor aceptó las seis preguntas del design con la recomendación del agente: quedan como D235 a D240 en `knowledge-base/10_preguntas_abiertas.md`. Se incorporó el informe de `revisor-de-escenarios` (`revision-de-escenarios.md`, el «antes»): la spec pasa de 6 a **7 escenarios** (US-090 CA-3 con escenario propio, el de sesión terminada retitulado US-092 CA-1 y la vuelta a «Ingresar» sin conexión dentro del escenario del botón) y las tareas siguen siendo **16**.

## Why

La pantalla `/ingresar` de C-08 se archivó el 2026-10-19, antes de la regla **D234** («toda pantalla del frontend se implementa a partir de una pantalla generada en Stitch»), y no tiene estilos propios: `frontend/src/features/ingreso/PaginaIngreso.tsx` no tiene ninguna `className` y solo hereda el `body` de `tokens.css`. Es la primera pantalla que ve toda persona del consultorio y hoy se ve con los estilos del navegador, al lado de un panel (C-11) que ya sigue «Clinical Ops».

Va ahora porque C-11 ya dejó los tokens (`tokens.css`), los estilos del panel (`panel.css`) y los íconos SVG propios que esta pantalla reutiliza, y porque no lleva migración ni cambios de API (puede aplicarse en paralelo a un change de backend, como C-08 y C-11).

## What Changes

- **La pantalla de inicio de sesión sigue la pantalla de Stitch** `projects/14200813501064679723/screens/d62ed0eb0edc43df833c9b24a24942b6` («Inicio de sesión - Turnos Odontológicos AR», generada el 2026-10-20 con «Clinical Ops»): una tarjeta centrada sobre el fondo del panel, la marca con el ícono de diente, los campos «Email» y «Contraseña» con su etiqueta, el aviso de error con ícono, el aviso de sesión terminada informativo arriba de los campos y el botón primario de ancho completo, que muestra «Ingresando…» deshabilitado mientras espera.
- **Sin cambio de comportamiento**: los textos, los mensajes (el genérico de RN-AU-04, el de conexión, el de entrada y el aviso de sesión terminada), los roles accesibles (`alert` y `status`), el envío, la redirección, la sesión y la renovación quedan como los fija `ingreso-al-panel`. Los 8 tests de `PaginaIngreso.test.tsx` y los 10 de `RutaProtegida.test.tsx` siguen en verde sin cambiar lo que verifican.
- **Un requisito nuevo en `ingreso-al-panel`** que vuelve verificable la parte visual que tiene efecto observable: el título de la marca, el aviso de sesión terminada antes de los campos, el aviso de error que conserva el mensaje exacto (sin título ni código agregados), el botón de espera con su nombre accesible y que la pantalla no carga recursos de otro origen (CSP `default-src 'self'`).
- **CSS propio** en una sección nueva de `panel.css` y tokens nuevos en `tokens.css` (D239), **sin dependencias nuevas**: el HTML de Stitch usa Tailwind, Google Fonts y Material Symbols por CDN y se traduce a los tokens del proyecto y a SVG en línea.
- **Se rechaza de la pantalla de Stitch** lo que la KB no respalda: la barra superior con «Acceso Seguro de Operatoria» y la insignia «Servidor Clínico Operativo», el pie «Módulo de Control de Acceso Clínico · Sede Central», el subtítulo «Acceso al panel administrativo» (D237) y las etiquetas «Referencia: …» de las tarjetas de estado (design, «Qué se rechaza»).
- **Ícono de espera** en el botón «Ingresando…», decorativo y sin animación si el sistema pide menos movimiento (D238).
- **El «Cargando…»** de la verificación de sesión toma la disposición de la pantalla de ingreso (D236).
- **README**: la pantalla en la sección del panel y la tabla escenario → test.

No hay cambios en el backend ni en la API, ni dependencias nuevas. No hay **BREAKING**.

### Escenarios

Cubre los cuatro mínimos de la entrada C-49 (dentro del «3 a 6»). Los escenarios ya vigentes de `ingreso-al-panel` no cambian; el requisito nuevo suma **7 escenarios** (2 felices, 2 de error de negocio y 3 de borde):

| ID | Qué verifica en la pantalla | Dónde corre |
|---|---|---|
| US-090 CA-1 | La pantalla muestra la marca como título y los campos con su etiqueta, y al abrirse no hay avisos (felices); mientras espera, el botón deshabilitado conserva el nombre «Ingresando…» con el ícono de espera, y sin conexión el aviso muestra el mensaje de conexión en el mismo lugar y el botón vuelve a «Ingresar» (borde) | Suite del frontend + prueba en el navegador |
| US-090 CA-2 | El rechazo (RN-AU-04) se muestra en el aviso de error con el mensaje genérico exacto, sin título ni código agregados, entre la contraseña y el botón (error de negocio) | Suite del frontend + prueba en el navegador |
| US-090 CA-3 | La usuaria inactiva con su contraseña correcta ve el mismo aviso, con el mismo texto, rol y lugar, que una contraseña incorrecta (error de negocio; RN-AU-04) | Suite del frontend (tarea 2.3). No se reproduce en el navegador: en la demo la recepcionista está activa |
| US-092 CA-1 | El aviso de sesión terminada (RN-AU-03) va antes de los campos y desaparece al reintentar (borde). No se suma a los mínimos: es un borde de presentación de un escenario vigente, y US-092 es de C-07 en el mapeo de `CHANGES.md` | Suite del frontend + prueba en el navegador |
| STI-1 | La pantalla no pide fuentes, estilos, scripts ni íconos a otro origen (borde; guard de la suite y consola del navegador sin violaciones de CSP) | Suite del frontend + prueba en el navegador |

No queda fuera ningún criterio de US-090 que tenga interfaz; CA-4 (duración y firma de los tokens) es de la API (C-06).

## Fuera de alcance

- **Cambios de comportamiento de `ingreso-al-panel`**: ningún requisito ni escenario vigente cambia; tampoco los mensajes, las rutas, la sesión, el almacenamiento ni la renovación.
- **Cambios de API, de esquema o de backend** (`backend/` no se toca) y **dependencias nuevas** (`frontend/package.json` y `package-lock.json` no cambian).
- **Lo que Stitch agregó sin respaldo en la KB**: barra superior y pie institucionales, estado del servidor, subtítulo, «Olvidé mi contraseña», «Recordarme», registro o inicio de sesión con terceros (no existen en la v1; la recuperación por email está fuera, `CHANGES.md` C-10).
- **Otras pantallas**: el panel base y la pantalla de prestaciones (C-11) no cambian; el inicio del panel (`InicioDelPanel.tsx`) queda fuera (D236; el «Cargando…» de la verificación de sesión sí entra).
- **Pantalla para celulares**: la pantalla de Stitch es de escritorio; solo se cuida que la tarjeta no desborde en un ancho chico (se comprueba a 375 px en la prueba del navegador), sin diseño móvil propio.
- **El mensaje «Revisá el email y la contraseña.»** (respuesta `422` del login, F9 de C-08): no se le agrega escenario, porque la spec vigente de `ingreso-al-panel` no lo incluye y sumarlo cambiaría el contrato de la capability, no su presentación; su aviso usa el mismo componente que el genérico.
- Modo oscuro, internacionalización, cargar o empaquetar la fuente Inter (se usa si está instalada, como en C-11), pruebas de extremo a extremo con navegador real.
- Sobreturnos y excepción de horario: fuera de la v1.

## Gobernanza

**MEDIO (Decisión del autor, D240).** El dominio es autenticación (C-06, C-07 y C-08 son CRITICO), pero este change no toca la lógica de sesión, los tokens ni la API: cambia el marcado y los estilos de `PaginaIngreso.tsx`. El riesgo real es una regresión de comportamiento por mover el marcado (por ejemplo, que el aviso de error deje de tener el texto exacto o que el botón pierda su nombre accesible). Por eso no alcanza BAJO («autonomía si los tests pasan»): se implementa con puntos de control y la red de seguridad son los 18 tests vigentes de C-08 (`PaginaIngreso` y `RutaProtegida`), que no se modifican, más los nuevos.

## Capabilities

### New Capabilities

Ninguna. Regla dura 12 («un change, una capability»): el change modifica solo `ingreso-al-panel`.

### Modified Capabilities

- `ingreso-al-panel`: se agrega el requisito «La pantalla de inicio de sesión sigue la pantalla de Stitch sin cambiar su comportamiento», con escenarios de presentación verificables (título de la marca, orden y contenido de los avisos para los tres rechazos de RN-AU-04 y la sesión terminada, botón de espera, sin recursos de otro origen). Los requisitos vigentes no cambian.

## Impact

- **Código que se modifica**: `frontend/src/features/ingreso/PaginaIngreso.tsx` (marcado y clases), `frontend/src/shared/estilos/panel.css` y, si hace falta, `tokens.css` (estilos de la tarjeta, de los campos `email` y `password` y del aviso informativo), y los tests `frontend/src/features/ingreso/PaginaIngreso.test.tsx`, `frontend/src/pages/RutaProtegida.test.tsx` y `frontend/src/test/guards.test.ts` (solo se agregan casos). Por D236, `frontend/src/pages/RutaProtegida.tsx` («Cargando…»).
- **Código que se reutiliza**: `shared/iconos/` (`IconoDiente`, `IconoAlerta`, `IconoInfo`); un ícono de espera nuevo en SVG en línea (D238).
- **Backend, API y Compose**: sin cambios.
- **Documentación**: `README.md`; evidencia de Stitch en `docs/skills-mcp/evidencias/sesion-nueva/stitch-ingreso.md` y `stitch-ingreso-pantalla/`. `knowledge-base/10_preguntas_abiertas.md` ya registra D235 a D240 (update del 2026-10-20). Al archivar: `CHANGES.md` (C-49 `[x]`), y en `CLAUDE.md` y `AGENTS.md` el párrafo «Estado de `10_preguntas_abiertas.md`» con D235 a D240 y el total de 49 changes.
- **Tamaño**: 7 escenarios nuevos y 16 tareas en 6 grupos, dentro del «alrededor de 20».
