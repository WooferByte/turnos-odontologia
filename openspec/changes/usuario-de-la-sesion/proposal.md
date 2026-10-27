# Proposal: usuario-de-la-sesion

Change **C-50** de `CHANGES.md`, **change técnico y de frontend, sin historia** (ninguna CA de la Épica 10 lo pide; `06`, nota «Changes técnicos y frontend»). Gobernanza **ALTO**: el design se aprueba antes del Apply y ninguna decisión marcada «Propuesta» se implementa sin el ok del autor. Depende de C-07 (archivado el 2026-10-15) y de C-08 (archivado el 2026-10-19). Las preguntas del design (**Q1 a Q11**) quedaron cerradas por el autor el 2026-10-27 con la recomendación del agente, junto con los hallazgos H1 a H10 de `revisor-de-escenarios`, y están registradas como **D304 a D314** en `knowledge-base/10_preguntas_abiertas.md`.

## Why

El panel no muestra con qué usuario se inició sesión: D225, D230 y D249 lo dejaron fuera a propósito porque ninguna ruta de la API informa el usuario del token («merece su propio change»). En la prueba manual de C-09 y C-10 (2026-10-27), con varias ventanas abiertas con usuarios distintos, el autor no podía distinguir de quién era cada sesión y llegó a desactivar y reactivar un usuario para averiguarlo, lo que le cortó otra sesión (RN-AU-03, RN-AU-04). Va ahora porque todos los changes de usuarios y contraseñas de la fase 3 están archivados y el problema aparece en cada prueba con más de un rol.

## What Changes

- **Ruta nueva de solo lectura `GET /auth/yo`** (D305; D225 la nombró «yo»): con el access token de cualquiera de los tres roles, responde `200` con **solo** `email` y `roles` del usuario del token, con los roles en un orden fijo (D306), leídos de la base en esa misma petición (RN-AU-02, D102), con `Cache-Control: no-store`. **Nunca** el hash, `token_version`, `activo`, `consultorio_id` ni el id. Sin sesión válida (sin cabecera, token ilegible, refresh usado como access, vencido, usuario inactivo o `token_version` vieja) responde el `401` de sesión inválida (`RN-AU-03`, D206); un usuario sin roles, el `403` `RN-AU-05` (permiso nuevo `sesion.leer` para los tres roles, D307). No hay cuerpo ni validación de entrada.
- **Indicador del usuario en el encabezado del panel**: junto a «Cerrar sesión», el email y los roles con las etiquetas de la pantalla de usuarios, «Odontólogo · Dueño» (D308). Se pide una vez cada vez que se entra al panel (al iniciar sesión o al recargar), no en cada pantalla, y una respuesta que llega después de «Cerrar sesión» no se muestra (D309). Un `401` sigue el camino existente de `ingreso-al-panel`: renueva una vez y, si no se puede, vuelve al inicio de sesión con el aviso de sesión terminada. Cualquier otra falla (sin conexión, error del servidor, `403` o una respuesta de otra forma) deja el indicador sin mostrar y la sesión sigue (D310). En anchos angostos el indicador baja a su propia fila y el email se corta con puntos suspensivos sin perder el texto (D311).
- **Pantalla de Stitch** (D234), generada en este propose con el design system «Clinical Ops»: escritorio `projects/14200813501064679723/screens/96c5900aaf8b4db18311a9baa8eafe75` y angosta `projects/14200813501064679723/screens/3078f94a4d474bff80154f884ccfa84f`; qué se toma y qué se rechaza, en el design («Referencia visual (Stitch)»).
- **Demo y README**: sin datos nuevos; recorrido de `GET /auth/yo` en «Probar desde Swagger», el indicador en «Panel (interfaz)», tabla escenario → test y los límites conocidos actualizados («el panel no muestra quién inició sesión» deja de valer; las acciones siguen visibles para todos, D230 y D249).

No hay migración, ni dependencias, ni variables de entorno nuevas. No hay **BREAKING**: ninguna ruta existente cambia y la lista de rutas públicas tampoco (`GET /auth/yo` exige el access token).

### Escenarios

Cubre los cinco mínimos de la entrada C-50 de `CHANGES.md`. El spec de la API los detalla en **13 escenarios** y el del encabezado en **11** (24 en total: 3 felices, 11 de error, de los que 8 son de negocio con código RN, y 10 de borde), por encima del «3 a 6» de `config.yaml`: excepción aceptada en **D314** (Q11), con el criterio de D300. Cada escenario tiene un ID propio (`SES-1a`, `SES-1b`…) que lleva el nombre de su test; el número es el escenario mínimo que cubre.

| ID | Qué verifica | Dónde corre |
|---|---|---|
| SES-1 | El token de cada rol obtiene su email y sus roles; un rol asignado o quitado se ve en la petición siguiente; los roles salen en un orden fijo | pytest + navegador |
| SES-2 | La respuesta trae solo `email` y `roles`: nunca el hash, `token_version`, `activo` ni el id; sin caché | pytest |
| SES-3 | Sin sesión válida, el `401` de sesión inválida (también usuario inactivo y `token_version` vieja); sin roles, `403` `RN-AU-05` | pytest |
| SES-4 | El encabezado muestra el email y los roles junto a «Cerrar sesión», con un solo pedido por entrada al panel; otro usuario en la misma pestaña ve sus datos; una respuesta tardía después de «Cerrar sesión» no se muestra; una falla que no es `401` no rompe el panel | Vitest + navegador |
| SES-5 | Un `401` en esa ruta, sin renovación posible, vuelve al inicio de sesión con el aviso de sesión terminada | Vitest + navegador |

No hay historias ni criterios que queden fuera: el change no tiene historia (`CHANGES.md`).

## Fuera de alcance

- **Ocultar enlaces o acciones según el rol** (el enlace «Usuarios» a la recepcionista, «Desactivar» o «Restablecer contraseña» en la propia fila): D230 y D249 siguen valiendo; queda para un change posterior (D312, Q9).
- **Editar el perfil** (email, nombre) o ver las sesiones abiertas; no hay tabla de tokens (RN-AU-03).
- **Cambios de esquema** o de datos del seed; nombre o apellido del usuario (no existen en `usuario`, `04`).
- **Recuperación de contraseña** por email (ningún criterio la pide).
- **Refrescar el indicador** mientras se navega: un rol cambiado con la sesión abierta se ve al volver a entrar al panel o al recargar (límite conocido, D309); la API ya aplica el cambio en la petición siguiente (RN-AU-02).
- **Menú desplegable** del usuario, avatar o foto, y la barra lateral o la barra inferior que sugiere el design system de Stitch.

## Capabilities

### New Capabilities

- `usuario-de-la-sesion`: el contrato de la API para saber quién es el usuario del access token: `GET /auth/yo` con email y roles, qué no devuelve nunca, sin caché, quién la puede usar y los rechazos `401` y `403` (RN-AU-01, RN-AU-02, RN-AU-03, RN-AU-04, RN-AU-05).
- `encabezado-del-panel`: qué muestra el encabezado del panel sobre la sesión en el navegador: el email y los roles junto a «Cerrar sesión», cuándo se piden, qué pasa ante un `401` o ante otra falla, y el cambio de usuario en la misma pestaña (RN-AU-03, RN-AU-05).

**Dos capabilities en un change** se apartan de «una sola capability» (`openspec/config.yaml`, regla dura 12): es una excepción registrada y limitada a C-50 (**D304**, Q1), con el criterio de D241, D255, D271 y D290 de separar el contrato de la API (pytest) del comportamiento del navegador (Vitest). La alternativa (requisitos nuevos en `sesion-del-panel` y en `ingreso-al-panel`) está en el design (Q1).

### Modified Capabilities

Ninguna (D304). Se revisaron:
- `sesion-del-panel`: describe iniciar y renovar la sesión; `GET /auth/yo` no inicia ni renueva nada.
- `proteccion-del-panel`: su guard ya exige el access token a toda ruta nueva fuera de la lista pública (requisito «Solo las rutas públicas se usan sin token»), y la lista no cambia; el permiso de la ruta nueva queda en `usuario-de-la-sesion`, como hicieron C-09 y C-10.
- `ingreso-al-panel`: «Cerrar sesión» y la renovación ante un `401` no cambian; el indicador nuevo y su pedido se describen en `encabezado-del-panel`.

## Impact

- **Backend**: `domain/acceso/roles.py` (`Permiso.SESION_LEER` para los tres roles); `application/acceso.py` (caso de uso `usuario_de_la_sesion`); `api/esquemas.py` (`UsuarioDeLaSesionSalida`); `api/routers/auth.py` (`GET /auth/yo` con `requiere(Permiso.SESION_LEER)` y `Cache-Control: no-store`). Tests de unidad, integración y API; los contadores de los guards de permisos y de rutas protegidas suben en 1 (solo cambia el número esperado).
- **Frontend**: `src/features/sesion/` (cliente `apiSesion.ts`, componente `IndicadorDeSesion.tsx` y sus tests); `shared/roles.ts` con las etiquetas de los roles (movidas desde `features/usuarios/mensajes.ts` en el REFACTOR, sin cambiar lo que verifica ningún test de C-09); `pages/PanelBase.tsx` (el indicador junto a «Cerrar sesión»); `test/servidorFalso.ts` (`GET /api/auth/yo`); `panel.css` y, si hace falta, `tokens.css`; un ícono SVG de persona.
- **Esquema y migraciones**: sin cambios.
- **Dependencias y variables de entorno**: ninguna nueva.
- **Documentación**: `README.md`; evidencia de Stitch en `docs/skills-mcp/evidencias/sesion-nueva/stitch-usuario-de-la-sesion.md` y `stitch-usuario-de-la-sesion-pantalla/`. Las respuestas a Q1 a Q11 quedaron registradas en `knowledge-base/10_preguntas_abiertas.md` (D304 a D314) con el `/opsx:update` del 2026-10-27, que además sumó `GET /auth/yo` a `02` («API REST (resumen)», fila Auth) y una fila con el permiso `sesion.leer` a la matriz de `03` (D313), así `scripts/verificar_changes.py` sigue en verde con la ruta citada en `CHANGES.md`; el párrafo de estado de la KB de `CLAUDE.md` y `AGENTS.md` y el rango de `openspec/config.yaml` llegan a D314.
- **`CHANGES.md`**: C-50 pasa a `[~]` en curso con este propose (como C-10 y C-13); el `/opsx:update` suma la ruta y D304 a D314 a su entrada.
- **Tamaño**: 24 tareas en 10 grupos para 24 escenarios, con RED, GREEN, TRIANGULATE y REFACTOR separados; excepción aceptada en D314.
