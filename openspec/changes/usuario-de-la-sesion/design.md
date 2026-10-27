# Design: usuario-de-la-sesion

Fecha del design: **2026-10-27**. Change **C-50** (change técnico y de frontend, sin historia; escenarios mínimos SES-1 a SES-5 de `CHANGES.md`). Gobernanza **ALTO** (`CHANGES.md` C-50): el autor aprueba este design **antes** del Apply; ninguna decisión «Propuesta» se implementa sin ese ok. Motivación y alcance en `proposal.md`; el comportamiento, en `specs/usuario-de-la-sesion/spec.md` (API, 13 escenarios) y `specs/encabezado-del-panel/spec.md` (encabezado, 11 escenarios).

Las decisiones se numeran **Y1 a Y18** («Y» de «yo») para no confundirlas con las D1..D303 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores (D de C-01, I de C-02, H de C-03, P de C-04, S de C-05, J de C-06, R de C-07, F de C-08, U de C-09, T de C-11, H de C-12, B de C-13, L de C-49, K de C-10). Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design, a confirmar) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»). **Las preguntas Q1 a Q11 están respondidas** (2026-10-27): el autor aceptó la recomendación de todas y todos los hallazgos H1 a H10 de `revisor-de-escenarios` (`docs/skills-mcp/evidencias/sesion-nueva/revision-de-escenarios-usuario-de-la-sesion.md`), incluidos los bordes sugeridos de H7 y H8. Quedaron registradas como **D304 a D314** en `knowledge-base/10_preguntas_abiertas.md`; no crean códigos RN nuevos. Las decisiones Y que dependían de una pregunta ahora citan su D («Decisión del autor (D305)»).

## Context

**Lo que ya existe** (leído del código y de los specs, no supuesto):

- **API de sesión** (`backend/app/api/routers/auth.py`): `POST /auth/login`, `POST /auth/refresh` (públicas) y `POST /auth/cambiar-contrasena` (C-10, con `requiere(Permiso.CONTRASENA_PROPIA)`); `_sin_cache` pone `Cache-Control: no-store`. **No hay ninguna ruta que devuelva el usuario del token** (D225, D249).
- **Control de acceso** (`api/seguridad.py`, `application/acceso.py`): `usuario_actual` lee el access, carga el usuario y **sus roles de la base en cada petición** (`identificar_usuario`, D102) y aplica `exigir_token_valido` (tipo, vencimiento, `activo`, `token_version`); toda causa es el mismo `401` de sesión inválida (D206). `requiere(permiso)` agrega el `403` `RN-AU-05` (D207) y devuelve `UsuarioDelPanel(id, roles)`: **sin el email**. `RESPUESTAS_DE_ACCESO` documenta `401` y `403` en OpenAPI.
- **Permisos** (`domain/acceso/roles.py`): `Permiso` con 14 valores y `MATRIZ`; `_TODOS` para los tres roles. El test de la matriz (`tests/unit/test_roles.py`) cuenta `14 * 3` casos; el guard `tests/api/test_proteccion_de_rutas.py` exige `usuario_actual` en toda ruta fuera de `RUTAS_PUBLICAS`.
- **Salida de usuarios** (`api/esquemas.py`): `UsuarioSalida` (C-09) ordena los roles por el enum, no por la base: el mismo criterio sirve acá. Lleva `id` y `activo`, que esta ruta no devuelve (Y5).
- **Frontend**: `ProveedorDeSesion` expone `estado`, `aviso`, `iniciarSesion`, `cerrarSesion`, `reemplazarTokens` y `pedidoDelPanel`; un `401` en `pedidoDelPanel` renueva una vez, repite una vez y, si sigue, pasa a `sin-sesion` con el aviso de sesión terminada (`ingreso-al-panel`); un `403` u otro `4xx` vuelve al llamador sin tocar la sesión; un `5xx` o una falla de red levantan `SinConexion`. `PanelBase.tsx` dibuja la barra (marca, cinco `NavLink`, «Cerrar sesión») y un `<Outlet/>`: **se monta una vez al entrar a `/panel` y no se desmonta al navegar entre sus pantallas hijas**; se desmonta al cerrar sesión (la ruta protegida lleva a `/ingresar`). Las etiquetas de los roles («Odontólogo», «Recepcionista», «Dueño») están en `features/usuarios/mensajes.ts` (`nombreDelRol`). El servidor falso tiene `vencerAccess`, `invalidarRefresh`, `quitarPermiso`, `retener`, `emitirSesion`, `caerse` y `responderConError` (estas dos, para **todas** las rutas).
- **Estilos**: `panel.css` (barra `.encabezado`, `.encabezado-interior` de alto fijo `--alto-barra`, `nav` con `flex: 1`) y un `@media (max-width: 720px)` para otras pantallas; la barra **no** tiene hoy acomodo propio para anchos angostos.

## Goals / Non-Goals

**Goals:**

- Que cada ventana del panel muestre de un vistazo con qué usuario y con qué roles se inició sesión, sin tocar la sesión de nadie para averiguarlo.
- Una ruta de solo lectura que no exponga nada de la cuenta salvo el email y los roles, con el mismo control de acceso que el resto del panel (D206, D207, D208).
- Que los roles mostrados salgan de la base (RN-AU-02), no del token ni de un estado adivinado.
- Sin dependencias, migraciones ni variables nuevas, y sin cambiar el comportamiento de las rutas y pantallas existentes.

**Non-Goals:**

- Ocultar enlaces o acciones según el rol (D312, Q9): D230 y D249 siguen; las pantallas siguen mostrando el `403` o el `409` de la API.
- Editar el perfil, nombre o apellido del usuario (no existen en `usuario`), listar sesiones abiertas o revocar sesiones de a una (RN-AU-03).
- Refrescar el indicador mientras se navega o cuando cambia un rol con la sesión abierta (D309, Q6; límite conocido).
- Menú desplegable del usuario, avatar, barra lateral o barra inferior (el design system de Stitch las sugiere; la barra del proyecto es horizontal desde C-08).

## Decisions

### Y1. Dos capabilities nuevas — Decisión del autor (D304; Q1; sigue D241, D255, D271 y D290; hallazgo H6)

`usuario-de-la-sesion` (el contrato de `GET /auth/yo`, pytest) y `encabezado-del-panel` (el navegador, Vitest), con el corte por suite de C-09, C-12, C-13 y C-10, que quedaron limitados a su change: C-50 tiene su propia excepción a «un change, una capability» (regla dura 12), registrada en D304 y limitada a C-50. Ninguna capability existente recibe delta: `sesion-del-panel` describe iniciar y renovar la sesión; `proteccion-del-panel` ya exige el token a toda ruta nueva fuera de la lista pública; `ingreso-al-panel` no cambia «Cerrar sesión» ni la renovación ante un `401`, que el encabezado reutiliza. `encabezado-del-panel` es el lugar natural para lo que el encabezado agregue después (por ejemplo, ocultar enlaces según el rol). **Alternativas** en Q1 y en D304.

### Y2. Estructura del backend — Propuesta (aplica `08`, «Estructura de directorios», y la regla dura 3)

```
backend/app/domain/acceso/roles.py      Permiso.SESION_LEER = "sesion.leer" en MATRIZ con _TODOS (Y6)
backend/app/application/acceso.py       usuario_de_la_sesion(actor, uow) -> UsuarioDeLaSesion(email, roles)
backend/app/api/esquemas.py             UsuarioDeLaSesionSalida(email: str, roles: list[Rol])
backend/app/api/routers/auth.py         GET /auth/yo con requiere(Permiso.SESION_LEER) y _sin_cache
```

`usuario_de_la_sesion` lee el usuario por `actor.id` con `uow.usuarios.obtener` (el email no viaja en `UsuarioDelPanel`) y toma los roles de `actor`, que `identificar_usuario` ya leyó de la base **en esta misma petición** (D102): no se leen dos veces. Si el usuario no existe (no puede pasar: no hay borrado de usuarios y `usuario_actual` acaba de leerlo), levanta `SesionInvalida`, que ya es el `401` fijo. Es un caso de uso de lectura, sin `commit()`. El dominio no cambia salvo el permiso.

### Y3. Nombre y forma de la ruta — Decisión del autor (D305; Q2)

**`GET /auth/yo`**, el nombre que usó D225 y que repiten D230 y D249, bajo el router `/auth` como pide `CHANGES.md`. Sin cuerpo ni parámetros; `HEAD` y otros métodos los responde FastAPI como hoy (`405`), sin escenario. La documentación de OpenAPI declara `200` con el esquema de Y5 y `RESPUESTAS_DE_ACCESO` (`401`, `403`).

### Y4. Clases de rechazo y orden de evaluación — Decisión del autor (D206, D207, D208; RN-GL-02)

| # | Clase | `GET /auth/yo` |
|---|---|---|
| 1 | Control de acceso | `401` `RN-AU-03` (sin cabecera, otro esquema, ilegible, refresh como access, vencido, usuario inexistente o inactivo, `token_version` vieja); `403` `RN-AU-05` (sin roles) |
| 2 | Validación de entrada | No hay: la ruta no recibe cuerpo ni parámetros; un parámetro de consulta desconocido se ignora, como en el resto de las rutas `GET` |
| 3 | Recurso de la URL | No hay: el usuario sale del token, no de la URL |
| 4 | Reglas de negocio | Ninguna |

No hay códigos RN nuevos ni clases nuevas en `api/errores.py`.

### Y5. Solo email y roles — Decisión del autor (D306; Q3)

`UsuarioDeLaSesionSalida` tiene **solo** `email` (el guardado, normalizado por D199) y `roles` (lista de `Rol` en el orden del enum, `odontologo`, `recepcionista`, `dueno`, como `UsuarioSalida.desde_usuario`), sin importar el orden en que se asignaron (escenario `SES-1d`, hallazgo H7). **No** lleva `id`, `activo` (con `200` siempre es `true`: un inactivo recibe `401`), `consultorio_id`, `creado_en`, `hash_password` ni `token_version` (`CHANGES.md`). El `id` serviría para ocultar «Desactivar» o «Restablecer contraseña» en la propia fila, que queda fuera (Q9); se suma cuando el change que lo use lo justifique, sin romper a nadie (agregar un campo no rompe el cliente, que valida solo lo que lee).

### Y6. Permiso para los tres roles y `403` sin roles — Decisión del autor (D307; Q4; sigue D298)

`Permiso.SESION_LEER` con `_TODOS`; la ruta usa `requiere(Permiso.SESION_LEER)`, como toda ruta del panel (`api/seguridad.py`: «Toda ruta del panel pasa por `requiere`»). Un usuario activo **sin roles** (la API no lo crea, la base lo admite; `proteccion-del-panel`: «un usuario sin roles no puede ni leer») recibe `403` `RN-AU-05`, igual que en `POST /auth/cambiar-contrasena` (D298); que el usuario sin roles pueda iniciar sesión para el escenario `SES-3h` se comprueba en V4. El test de la matriz pasa de `14 * 3` a `15 * 3` casos; el guard de rutas protegidas encuentra la ruta protegida sin tocar `RUTAS_PUBLICAS`. **Alternativa** en Q4 y en D307.

### Y7. Sin caché — Propuesta

`_sin_cache` en la respuesta, como `/auth/login` y `/auth/refresh` (RFC 7234/9111: una respuesta personal no se guarda en cachés compartidas ni en la del navegador). Escenario `SES-2a`.

### Y8. Estructura del frontend — Propuesta (aplica K13 de C-10 y U17 de C-09)

```
frontend/src/features/sesion/apiSesion.ts (+ .test.ts)            obtenerUsuarioDeLaSesion(pedido) -> UsuarioDeLaSesion | null
frontend/src/features/sesion/IndicadorDeSesion.tsx                el email y los roles; nada mientras espera o si falla
frontend/src/features/sesion/IndicadorDeSesion.test.tsx           escenarios de encabezado-del-panel sobre <App/> en un MemoryRouter
frontend/src/shared/roles.ts                                       tipo Rol y nombreDelRol, movidos desde features/usuarios/mensajes.ts (REFACTOR)
frontend/src/shared/iconos/IconoPersona.tsx                        SVG en línea, aria-hidden y focusable="false"
frontend/src/pages/PanelBase.tsx                                   <IndicadorDeSesion/> inmediatamente antes de «Cerrar sesión»
frontend/src/test/servidorFalso.ts                                 GET /api/auth/yo y la falla de una sola ruta (Y14)
frontend/src/shared/estilos/panel.css                              sección «Usuario de la sesión» y el acomodo angosto de la barra (Y12)
```

`obtenerUsuarioDeLaSesion` valida la respuesta `200` sin `any` (`email` texto, `roles` lista de roles conocidos) y devuelve `null` para un `403` o una forma inesperada (un rol que no es uno de los tres, sin `email`; escenario `SES-4i`, hallazgo H3); un `401` sin renovación posible sale como `SesionTerminada` por `pedidoDelPanel` (Y11) y una falla de red o un `5xx` como `SinConexion`, que el componente atrapa (Y11).

### Y9. Etiquetas de los roles — Decisión del autor (D308; Q5)

Las de la pantalla de usuarios (C-09): «Odontólogo», «Recepcionista», «Dueño», en el orden de la API y separadas por « · » («Odontólogo · Dueño», como en la pantalla de Stitch). Una sola fuente: `nombreDelRol` pasa a `shared/roles.ts` y la pantalla de usuarios la importa de ahí (REFACTOR sin cambiar ningún test de C-09). No se usan formas por género («Odontóloga»): el sistema no guarda el género y la tabla de usuarios ya usa estas etiquetas. **Alternativa** en Q5 y en D308.

### Y10. Cuándo se pide — Decisión del autor (D309; Q6) + Propuesta (detalle; aplica `vercel-react-best-practices`)

`IndicadorDeSesion` pide `GET /api/auth/yo` en un efecto al montarse. Como vive en `PanelBase`, que se monta al entrar al panel y no se desmonta al navegar entre pantallas hijas, el pedido sale **una vez por entrada al panel**: después de iniciar sesión, al recargar la pestaña (después de la renovación de arranque de `ProveedorDeSesion`, porque `RutaProtegida` no monta el panel mientras `estado` es `verificando`) y al volver a iniciar sesión después de «Cerrar sesión», que desmonta el panel y descarta el estado (escenario «otro usuario en la misma pestaña»). El efecto ignora la respuesta si el componente se desmontó (bandera `vigente`, como `ProveedorDeSesion`): una respuesta que llega después de «Cerrar sesión» no se muestra (escenario `SES-4e`, hallazgo H8); en desarrollo, el `StrictMode` de React monta dos veces y puede salir un pedido de más, sin efecto visible (no corre en los tests ni en Compose). El email y los roles viven solo en el estado del componente: nada en `sessionStorage` ni `localStorage` (D219, guard F7). **Límite conocido**: un rol asignado o quitado mientras la sesión está abierta se ve al volver a entrar al panel o al recargar; la API ya lo aplica en la petición siguiente (RN-AU-02). **Alternativas** en Q6 y en D309.

### Y11. Fallas al pedir el usuario — Decisión del autor (D310; Q7)

- `401`: lo resuelve `pedidoDelPanel` como cualquier ruta del panel (`ingreso-al-panel`): renueva una vez y repite; si no se puede, `SesionTerminada`, el proveedor pasa a `sin-sesion` con el aviso de sesión terminada y la ruta protegida lleva a `/ingresar` (SES-5). El componente no agrega nada.
- `403` (usuario sin roles), `5xx`, falla de red o una respuesta `200` con otra forma (escenarios `SES-4f` a `SES-4i`; la forma inesperada quedó en el requisito por el hallazgo H3): el indicador **no se muestra**, sin aviso nuevo, sin reintento; la sesión sigue. Motivo: el indicador es informativo y no debe tapar ni duplicar el aviso que ya muestra la pantalla abierta si la API no responde; un usuario sin roles igual recibe el `403` en cada pantalla. **Alternativa** en Q7 y en D310.

### Y12. Disposición y anchos angostos — Decisión del autor (D311; Q8; sale de las pantallas de Stitch)

- En escritorio, el indicador va a la derecha de la navegación e inmediatamente antes de «Cerrar sesión», separado por una línea vertical fina: un ícono de persona en un círculo gris, el email en una línea (seminegrita, `--texto`) y debajo los roles (chico, `--texto-suave`). Es texto: no es un botón ni un menú.
- Debajo de 720 px (el corte que ya usa `panel.css`), la barra deja el alto fijo y se acomoda en filas: la marca; la navegación, cuyas pastillas pasan a la línea siguiente; y una fila con el indicador a la izquierda y «Cerrar sesión» a la derecha. El **email se corta con puntos suspensivos** (`overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0`) y el texto completo sigue en el DOM (lo leen los lectores de pantalla) y en el atributo `title`; los roles no se cortan. Sin desplazamiento horizontal de la página a 390 px.
- No se prueba en jsdom (no calcula estilos): se verifica en la prueba en el navegador a 1280 y a 390 px (tarea 9.1); el CSS va en la tarea 8.1.

### Y13. Accesibilidad — Propuesta

El indicador está dentro del `header` (rol `banner`) como un párrafo con dos líneas de texto; el ícono es decorativo (`aria-hidden`). No lleva rol propio ni `aria-live`: aparece una vez al entrar al panel y los lectores lo leen en orden antes de «Cerrar sesión». Los tests lo encuentran con `within(screen.getByRole('banner'))`.

### Y14. Servidor falso y tests — Decisión del autor (D211, D222, D227; reglas duras 5 y 6) + Propuesta (detalle)

- **Backend**: unidad (`tests/unit/test_roles.py`: la fila nueva de la matriz), integración (`tests/integration/test_acceso.py`: `usuario_de_la_sesion` con la base en memoria) y API (`tests/api/test_usuario_de_la_sesion.py`, con access tokens reales firmados con `SECRETO_DE_PRUEBA`, sin `dependency_overrides`; el usuario sin roles se arma en la base del test; el access vencido con el reloj inyectable). Sin mocks de sesión ni de repositorio. Cada test lleva el ID propio de su escenario (`test_ses1a_…`; hallazgo H2).
- **Frontend**: el servidor falso suma `GET /api/auth/yo` (email y roles del usuario del access, en el orden de la API; `401` con las mismas reglas que las demás rutas, también después de `vencerAccess`, de desactivar o de restablecer; `403` para un usuario sin permiso con `quitarPermiso`) y **una forma de hacer fallar una sola ruta** (`fallarRuta(ruta, falla)`, con `'red'`, un estado o un cuerpo `200` de otra forma), porque `caerse` y `responderConError` hacen fallar todas y los escenarios de Y11 necesitan que «Prestaciones» siga cargando. `SES-4e` usa el `retener` existente sobre `/api/auth/yo`. Los tests del cliente y del componente llevan el ID del escenario del encabezado que prueban (`'SES-4a: …'`), nunca uno de la API (hallazgo H2). Vitest sin `vi.mock`, `vi.fn`, `vi.stubGlobal` ni temporizadores falsos. **A verificar en el change (V2, antes de 7.1):** que sumar `GET /api/auth/yo` al montar `PanelBase` no cambia lo que verifican los tests de C-08 a C-13 que cuentan peticiones (`peticiones`, `llamadas`, `rutasPedidas`) o que esperan una ruta exacta; si alguno cuenta todas las peticiones, se ajusta solo su número esperado, como los contadores de los guards, y se anota.

### Y15. Versiones y dependencias — Propuesta

**Sin dependencias nuevas** ni cambios de versión: `backend/pyproject.toml`, `frontend/package.json` y `package-lock.json` no cambian; no hay pins nuevos que fijar (regla de `config.yaml`).

### Y16. Demo y README — Propuesta

- **Demo**: sin datos nuevos; `GET /auth/yo` se prueba con la odontóloga y la recepcionista del seed.
- **README**: `GET /auth/yo` en «Probar desde Swagger» (con cada usuario de la demo, el `401` sin token y después de desactivar), el indicador en «Panel (interfaz)», la tabla escenario → test con la cantidad real de tests, y los límites conocidos: se **quitan** «El panel no muestra quién inició sesión» y «Tampoco hay `GET /auth/yo`»; los de D249 en las pantallas de usuarios, horario, bloqueos y contraseñas pasan a decir que las acciones se ven con cualquier rol **aunque el panel ya sabe quién inició sesión** (D312); se suma el del rol cambiado con la sesión abierta (Y10).

### Y17. Prueba en el navegador — Decisión del autor (D234, `rules.tasks`) + Propuesta (detalle)

El agente repite los escenarios de `encabezado-del-panel` con la demo (salvo `SES-4e` a `SES-4i`, que se verifican solo contra el falso), con **dos ventanas privadas a la vez**, una con la odontóloga y otra con la recepcionista (el caso que originó el change), y en Compose; compara con las capturas de Stitch a 1280 y a 390 px y anota las diferencias. Le deja al autor el paso a paso. La repetición manual del autor es **opcional** (ALTO no es CRÍTICO; `rules.tasks`), salvo que el agente no quede conforme.

### Y18. Skills aplicadas

- `auth-implementation-patterns`: el servidor decide y la interfaz solo muestra; la respuesta no expone nada de la cuenta salvo email y roles (sin hash, sin `token_version`); `401` genérico sin revelar la causa (D206); roles leídos de la base, no del token (RN-AU-02); sin caché en respuestas personales. **No aplicadas** por la KB (regla dura 9): límite de peticiones y registro de eventos (D195); el consejo de cookies `httpOnly` (D219 ya fijó dónde viven los tokens).
- `fastapi-templates`: router por recurso, esquema de salida separado (nunca el modelo ORM), dependencias inyectadas (`requiere`). **No aplica** su parte asíncrona (DD-12, regla dura 5).
- `python-testing-patterns`: TDD estricto, `parametrize` para triangular las causas del `401`, base real en memoria y tokens reales, sin mocks (regla dura 6).
- `python-error-handling` y `python-design-patterns`: sin errores nuevos; el caso de uso solo orquesta y el router no toca el ORM.
- `vercel-react-best-practices` (SPA de Vite): un solo pedido por montaje del panel (deduplicado por la estructura, sin SWR ni dependencias nuevas), efecto con dependencias primitivas y bandera de vigencia, ternario en vez de `&&`, sin componentes definidos dentro de otros, sin *barrels*.
- `database-migration` y `supabase-postgres-best-practices`: **no aplican** (sin esquema).

## Referencia visual (Stitch)

**Regla (D234, Decisión del autor):** toda pantalla del frontend se implementa a partir de una pantalla generada en Stitch con el design system «Clinical Ops»; el design cita el id y su evidencia; si Stitch no entrega la pantalla, el change de interfaz no se cierra; la KB y el spec mandan sobre el contenido. Las pantallas se consiguieron **en este propose** (2026-10-27), antes de aprobar el plan.

- **Escritorio**: `projects/14200813501064679723/screens/96c5900aaf8b4db18311a9baa8eafe75` («Prestaciones con usuario en sesión - Turnos Odontológicos AR»).
- **Angosta**: `projects/14200813501064679723/screens/3078f94a4d474bff80154f884ccfa84f` («Prestaciones - Móvil (Turnos Odontológicos AR)»; pedida como `MOBILE`, Stitch la entregó como columna de 390 px centrada en un lienzo de escritorio).
- Las dos con el design system «Clinical Ops» (`assets/b683d44391ab410db2dd48aa71ed0b47`), al primer intento.
- **Evidencia**: `docs/skills-mcp/evidencias/sesion-nueva/stitch-usuario-de-la-sesion.md` (pedidos, ids, revisión de datos y sugerencias no aceptadas) y `stitch-usuario-de-la-sesion-pantalla/` (`encabezado-escritorio.png` y `.html`; `encabezado-angosto.png` y `.html`; capturas a 1280 × 1024).

**Qué se toma:**
- El indicador a la derecha de la navegación e inmediatamente antes de «Cerrar sesión», separado por una línea vertical fina (`--borde`).
- Un ícono de persona dentro de un círculo gris claro, el email en una línea en seminegrita oscura y los roles debajo en texto chico gris, separados por « · ».
- En la angosta: la barra en tres filas (marca; pastillas que pasan a otra línea; indicador a la izquierda y «Cerrar sesión» a la derecha, debajo de una línea fina), el email cortado con puntos suspensivos y el rol sin cortar.
- El resto de la barra (marca, pastillas, pastilla activa, «Cerrar sesión» con borde e ícono) ya es la de C-08 a C-10 y no cambia.

**Qué se rechaza (motivo):**
- La tarjeta «Listado general», «Módulo administrativo», el color en hexadecimal, «Mostrando 3 de 3 registros», «Agenda sincronizada», «Sincronizado» y los pies de página institucionales («Módulo de Prestaciones y Catálogo Clínico», «Sede Central»): son del fondo de referencia, no de este change; la pantalla de prestaciones es la de C-11 y no hay sedes (D173).
- «+ Nueva» abreviado y las tarjetas por prestación de la angosta: la pantalla de prestaciones no cambia en este change.
- El ícono de la marca de la captura de escritorio dentro de un recuadro: la marca de C-08 no cambia.
- Cualquier menú, avatar con foto o interacción sobre el indicador: el spec lo define como texto (Y12).
- Las sugerencias de Stitch (sección «Sugerencias no aceptadas» de la evidencia): son de otras pantallas.
- Tailwind, Google Fonts y Material Symbols por CDN (CSP `default-src 'self'`): se traduce a `tokens.css` y `panel.css` y a marcado de React **sin dependencias nuevas**; el ícono de persona en SVG en línea con `aria-hidden="true"` y `focusable="false"`.

**Ya decidido sin la pantalla, por la KB y los specs** (se mantiene aunque Stitch muestre otra cosa): los textos y el orden de los roles (Y9); que el indicador no aparezca mientras espera ni si falla (Y11); que no se oculte ninguna acción (D312). La prueba en el navegador (9.1) compara la implementación con `encabezado-escritorio.png` y `encabezado-angosto.png` y anota las diferencias en la evidencia.

## Contradicciones y huecos encontrados en las fuentes

1. **D225, D230 y D249 dicen que el panel «no muestra quién inició sesión»** y que la ruta «merece su propio change»: este change es ese change. D225 queda superada en lo que muestra el encabezado; D230 y D249 siguen valiendo para las acciones (D312). Registrado con D304 a D314 en el `/opsx:update` del 2026-10-27; los límites del README se ajustan en el Apply (Y16).
2. **`02` y `03` no listan `GET /auth/yo`**: `02` («API REST (resumen)», fila Auth) lista solo `login`, `refresh` y `cambiar-contrasena`, y la matriz de `03` no tiene una fila para leer el propio usuario. `scripts/verificar_changes.py` (filas 4 y 8) exige que toda ruta que cite `CHANGES.md` esté en `02` o `03`. → D313 (Q10): **resuelto en el `/opsx:update` del 2026-10-27**: `02` lista `GET /auth/yo` en la fila Auth, `03` tiene la fila «Ver el propio usuario de la sesión (email y roles)» con «R propio» para los tres roles, y recién después `CHANGES.md` cita la ruta en la entrada de C-50.
3. **Un usuario sin roles**: la matriz de `03` da la fila a los tres roles; la base admite un usuario sin ninguno. → D307 (Q4): `403`, como D298.
4. **Etiquetas de los roles**: la KB no dice cómo se muestran los roles fuera de la pantalla de usuarios (C-09 usa «Odontólogo», «Recepcionista», «Dueño»); una forma por género («Odontóloga», como se diría de la usuaria de la demo) no es posible porque el sistema no guarda el género. → D308 (Q5).
5. **«Leer antes» de C-50** pide `06` §US-090 y nota «Changes técnicos y frontend»: la nota dice que la interfaz va «sin inventar pantallas que ningún criterio pide». El indicador no es una pantalla nueva sino un agregado al encabezado existente, pedido por el autor al sumar C-50 (2026-10-27); se deja asentado en D304.
6. **El servidor falso** no puede hacer fallar una sola ruta. → Y14.

## Risks / Trade-offs

- [El email de un usuario queda visible en pantalla para quien mira el monitor] → es el email del propio usuario que inició sesión, dato del personal, no de pacientes (RN-PR-01 no aplica); el panel es interno. «Cerrar sesión» lo quita.
- [Un rol cambiado con la sesión abierta no se ve hasta volver a entrar al panel] → límite conocido (Y10); la API aplica el cambio igual (RN-AU-02) y la pantalla muestra el `403` si corresponde.
- [Se interpreta el indicador como control de acceso] → no lo es: las acciones siguen visibles para todos y la API decide (D230, D249); se aclara en el README.
- [Un pedido de más al entrar al panel] → una lectura liviana por entrada (no por pantalla); `usuario_actual` ya lee el usuario en cada petición.
- [Tests de C-08 a C-13 que cuentan peticiones cambian por el pedido nuevo] → V2 (Y14).
- [El servidor falso se aparta de la API] → cuerpos copiados del spec; la prueba en el navegador repite los escenarios contra la API real.

## A verificar en el change

- **V1** (antes de la tarea 4.2): que FastAPI 0.115 documenta en OpenAPI el `200` de `GET /auth/yo` con solo `email` y `roles` (el esquema de salida, sin campos heredados) y que el guard de rutas protegidas reconoce la ruta por `usuario_actual` dentro de `requiere`.
- **V2** (antes de la tarea 7.1): los tests de C-08 a C-13 que cuentan peticiones o rutas pedidas, con el pedido nuevo de `PanelBase` (Y14).
- **V3** (antes de la tarea 9.1, en Compose): consola sin violaciones de la CSP con el ícono nuevo y sin desplazamiento horizontal a 390 px.
- **V4** (al empezar el Apply, tarea 1.1; duda que `revisor-de-escenarios` no pudo confirmar): si `POST /auth/login` (`sesion-del-panel`) admite iniciar sesión a un usuario activo **sin roles**, como da por hecho `SES-3h`. Si lo admite, el test inicia sesión como en los demás; si lo rechaza, el test arma el access token con `SECRETO_DE_PRUEBA` (token real, sin `dependency_overrides`), el escenario sigue igual y se anota el resultado acá.
  - **Resultado (Apply, 2026-10-27): `POST /auth/login` admite a un usuario activo sin roles** (`iniciar_sesion` no mira los roles; lo prueba `test_us093_ca7_…_un_usuario_sin_roles_no`, que inicia sesión con `200` y recibe `403` `RN-AU-05` en la ruta). `SES-3h` inicia sesión como los demás escenarios; no hace falta armar el token a mano.

## Migration Plan

1. **Hecho (2026-10-27):** con las respuestas del autor a Q1 a Q11 y a los hallazgos H1 a H10, un `/opsx:update` registró D304 a D314 en `knowledge-base/10_preguntas_abiertas.md`, sumó `GET /auth/yo` a `02` y la fila de la matriz y el permiso `sesion.leer` a `03` (D313), citó la ruta y D304 a D314 en la entrada C-50 de `CHANGES.md`, actualizó el párrafo de estado de la KB en `CLAUDE.md` y `AGENTS.md` y el rango de `openspec/config.yaml`, ajustó los artefactos y repitió `scripts/verificar_changes.py` (décima corrida, sin diferencias). Con el ok del autor al plan (ALTO), se commitean los artefactos (con el `[~]` de C-50 en `CHANGES.md`) y, aparte, el `docs(kb)` de las decisiones.
2. El Apply no lleva migración ni variables nuevas: `docker compose up --build -d` reconstruye `api` y `frontend`.
3. **Efecto visible**: desde este change, cada ventana del panel muestra el email y los roles de quien inició sesión.
4. **Vuelta atrás**: revertir los commits del change; no hay datos que migrar.

## Notas para el archive

No se editan ahora ni durante el Apply:

- `CHANGES.md`: marcar C-50 con `[x]` y repetir `scripts/verificar_changes.py`. La ruta (`GET /auth/yo`) en «Alcance — dentro» y D304 a D314 en «Leer antes» ya quedaron con el `/opsx:update` (hallazgo H5).
- `knowledge-base/02_descripcion_general.md` («API REST (resumen)», fila Auth) y `03_actores_y_roles.md` (fila «Ver el propio usuario de la sesión (email y roles)», «R propio» para los tres roles, con el permiso `sesion.leer`): hechos en el `/opsx:update` del 2026-10-27 (D313; hallazgo H5); al archivar, solo comprobar que siguen coincidiendo con lo implementado.
- `knowledge-base/08_arquitectura_propuesta.md`: `features/sesion/` y `shared/roles.ts` en la «Estructura de directorios»; en §Seguridad, que el panel muestra el usuario del token con `GET /auth/yo` (sin caché, solo email y roles).
- `knowledge-base/06_funcionalidades.md`, nota «Changes técnicos y frontend»: sumar C-50 como change técnico y de frontend sin historia.
- `knowledge-base/10_preguntas_abiertas.md`: D304 a D314 ya quedaron registradas con el `/opsx:update`; al cerrar, D225 con la nota de que C-50 la superó en el encabezado, D230 y D249 con la nota de que siguen para las acciones (D312), las «Propuesta» que el autor apruebe y los resultados de V1 a V4.
- `openspec/config.yaml` (el rango D1..D314), `CLAUDE.md` y `AGENTS.md` (idénticos): el párrafo de estado de la KB con D304 a D314 ya quedó con el `/opsx:update`; al archivar, solo comprobar.
- `docs/skills-mcp/evidencias/sesion-nueva/stitch-usuario-de-la-sesion.md`: la comparación de la prueba en el navegador (sección 4).

## Open Questions

**Cerradas.** Las once preguntas del propose quedaron cerradas por el autor el 2026-10-27 con la recomendación del agente, junto con los hallazgos H1 a H10 de `revisor-de-escenarios` («Acepto Q1-Q11 con la recomendación y todos los hallazgos H1-H10 del revisor (incluidos los bordes sugeridos de H7 y H8).»):

- **Q1 → D304.** Dos capabilities nuevas (`usuario-de-la-sesion` y `encabezado-del-panel`), sin deltas, como excepción a «una sola capability» limitada a C-50 (Y1; hallazgo H6).
- **Q2 → D305.** La ruta es `GET /auth/yo` (Y3).
- **Q3 → D306.** La respuesta trae solo `email` y `roles`, con los roles en el orden fijo del enum (Y5; escenario `SES-1d`, hallazgo H7).
- **Q4 → D307.** Permiso nuevo `sesion.leer` para los tres roles; un usuario sin roles recibe `403` `RN-AU-05` (Y6; V4).
- **Q5 → D308.** Las etiquetas de la pantalla de usuarios, separadas por « · », con una sola fuente en `shared/roles.ts` (Y9).
- **Q6 → D309.** Un pedido por entrada al panel, en el encabezado, con la bandera `vigente` (Y10; escenario `SES-4e`, hallazgo H8).
- **Q7 → D310.** Ante `403`, `5xx`, falla de red o una respuesta de otra forma, el indicador no se muestra, sin aviso ni reintento (Y11; escenarios `SES-4f` a `SES-4i`, hallazgo H3).
- **Q8 → D311.** Debajo de 720 px la barra pasa a filas y el email se corta con puntos suspensivos (Y12).
- **Q9 → D312.** Ocultar enlaces y acciones según el rol queda para un change posterior; D230 y D249 siguen.
- **Q10 → D313.** `GET /auth/yo` quedó en `02` y en la matriz de `03` con este `/opsx:update` (hallazgo H5).
- **Q11 → D314.** 24 tareas en 10 grupos para 24 escenarios, excepción limitada a C-50, con RED, GREEN, TRIANGULATE y REFACTOR separados (hallazgos H4 y H9).

Texto de las preguntas tal como se respondieron:

- **Q1. Capabilities (→ D304).** (a) **Dos nuevas**, `usuario-de-la-sesion` (API) y `encabezado-del-panel` (navegador), sin deltas, como excepción limitada a C-50 (Y1); (b) requisitos nuevos (`ADDED`) en dos capabilities existentes, `sesion-del-panel` (la ruta) y `ingreso-al-panel` (el encabezado), sin capabilities nuevas; (c) una sola capability nueva con la API y el navegador juntos (cumple «una capability», pero mezcla pytest y Vitest, lo que D218 evitó). **Recomendación: (a)**: sigue el corte de D241, D255, D271 y D290 que el autor aceptó cuatro veces, deja a `sesion-del-panel` con iniciar y renovar, y da un lugar a lo que el encabezado sume después (Q9). (b) es igual de válida y evita dos capabilities más; se descarta solo por consistencia.
- **Q2. Nombre de la ruta (→ D305).** (a) **`GET /auth/yo`** (el de D225, D230 y D249); (b) `GET /auth/sesion`; (c) `GET /usuarios/yo` (fuera de `/auth`, contra `CHANGES.md`). **Recomendación: (a)**: es el nombre que la KB ya usó tres veces y está bajo `/auth`, como pide `CHANGES.md`.
- **Q3. Campos de la respuesta (→ D306).** (a) **Solo `email` y `roles`**; (b) sumar el `id` (para el change que oculte acciones en la propia fila). **Recomendación: (a)**: es lo que pide `CHANGES.md` y lo mínimo para el problema; el `id` se agrega sin romper nada cuando un change lo use (Y5).
- **Q4. Usuario sin roles (→ D307).** (a) **`403` `RN-AU-05`** con un permiso nuevo `sesion.leer` para los tres roles, como D298; (b) `200` con `roles` vacío (la ruta solo exigiría sesión, sin `requiere`). **Recomendación: (a)**: mantiene la regla de `proteccion-del-panel` («un usuario sin roles no puede ni leer») y el patrón de toda ruta del panel; (b) le mostraría a ese usuario su email, que hoy no puede hacer nada con él.
- **Q5. Etiquetas de los roles (→ D308).** (a) **Las de la pantalla de usuarios** («Odontólogo», «Recepcionista», «Dueño»), en el orden de la API, separadas por « · », con una sola fuente en `shared/roles.ts`; (b) formas por género («Odontóloga»), que el sistema no puede saber; (c) los valores crudos (`odontologo`). **Recomendación: (a)**: consistentes con la tabla de usuarios y con la captura de Stitch.
- **Q6. Cuándo pide el frontend el usuario (→ D309).** (a) **Una vez por entrada al panel** (al iniciar sesión o al recargar), en el encabezado, con el límite del rol cambiado con la sesión abierta; (b) en cada cambio de pantalla (siempre fresco, un pedido más por navegación); (c) dentro de `ProveedorDeSesion`, después del login y de la renovación de arranque (lo acopla a la sesión y a cada renovación del access). **Recomendación: (a)**: un pedido por sesión de pantalla, sin tocar el proveedor de C-08; el rol cambiado es raro y la API lo aplica igual.
- **Q7. Fallas que no son `401` (→ D310).** (a) **El indicador no se muestra**, sin aviso ni reintento, y la sesión sigue; (b) un texto fijo en su lugar («Usuario no disponible»); (c) reintentar al navegar. **Recomendación: (a)**: el indicador es informativo y la pantalla abierta ya avisa si no hay conexión; (b) agrega un mensaje y su escenario sin ayudar a resolver nada.
- **Q8. Anchos angostos (→ D311).** (a) **Debajo de 720 px la barra pasa a filas y el email se corta con puntos suspensivos**, con el texto completo en el DOM y en `title`, como la pantalla angosta de Stitch; (b) ocultar el email y dejar solo los roles; (c) no tocar la barra (hoy en 390 px desborda). **Recomendación: (a)**: el email es justamente lo que distingue las ventanas; sin escenario automático, se verifica en el navegador (9.1).
- **Q9. Ocultar enlaces y acciones según el rol (→ D312).** (a) **Dejarlo para un change posterior**: D230 y D249 siguen y el indicador solo informa; (b) hacerlo ahora (ocultar «Usuarios» a la recepcionista, acciones de escritura a quien no es `odontologo`, «Desactivar» y «Restablecer contraseña» en la propia fila, lo que pide además el `id`). **Recomendación: (a)**: (b) toca las cinco pantallas, sus tests y sus specs (`pantalla-de-*`), suma el `id` (Q3) y al menos un escenario por pantalla; no hay una razón fuerte para hacerlo ya, porque la API decide y las pantallas muestran el rechazo con su código. Si el autor lo quiere, se suma a `CHANGES.md` como change propio con dependencia de C-50.
- **Q10. Registro de la ruta en la KB (→ D313).** (a) **En el `/opsx:update` que registra las respuestas**: `GET /auth/yo` en la fila Auth de `02` y una fila «Ver el propio usuario de la sesión (email y roles)» con «R propio» para los tres roles en la matriz de `03`, y repetir `scripts/verificar_changes.py`; (b) recién al archivar. **Recomendación: (a)**: el verificador exige que toda ruta citada en `CHANGES.md` exista en `02` o `03`, y la KB debe describir el contrato antes de implementarlo.
- **Q11. Tamaño (→ D314).** En el propose, **18 tareas en 10 grupos** (dentro de «alrededor de 20») para **14 escenarios** (7 de la API y 7 del encabezado), frente a «3 a 6» de `config.yaml`. **Recomendación: aceptar la excepción limitada a C-50**, como D300: cada escenario es una variante corta de los cinco mínimos (SES-1 a SES-5) y separar los de borde (rol cambiado, recarga, otro usuario en la misma pestaña) es lo que cubre el problema que originó el change. Con el `/opsx:update` (hallazgos H3, H4, H7, H8 y H9) quedaron **24 tareas en 10 grupos** para **24 escenarios** (13 de la API y 11 del encabezado).
