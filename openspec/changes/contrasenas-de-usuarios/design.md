# Design: contrasenas-de-usuarios

Fecha del design: **2026-10-26**. Change **C-10** (US-093 CA-6, CA-7 y la parte de CA-9 de la contraseña restablecida y la cambiada). Gobernanza **CRÍTICO** (`CHANGES.md` C-10): el autor aprueba este design **antes** del Apply; ninguna decisión «Propuesta» se implementa sin ese ok. Motivación y alcance en `proposal.md`; el comportamiento, en `specs/contrasenas-de-usuarios/spec.md` (API, 21 escenarios) y `specs/pantalla-de-contrasenas/spec.md` (pantalla, 17 escenarios).

Las decisiones se numeran **K1 a K22** («K» de clave) para no confundirlas con las D1..D303 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores (D de C-01, I de C-02, H de C-03, P de C-04, S de C-05, J de C-06, R de C-07, F de C-08, U de C-09, T de C-11, H de C-12, B de C-13, L de C-49). Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design, a confirmar) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»). **Las preguntas Q1 a Q12 están respondidas** (2026-10-26): el autor aceptó la recomendación de todas, con Q4 resuelta con un código propio, y todos los hallazgos H1 a H11 de `revisor-de-escenarios` (`docs/skills-mcp/evidencias/sesion-nueva/revision-de-escenarios-contrasenas-de-usuarios.md`). Quedaron registradas como **D290 a D301** en `knowledge-base/10_preguntas_abiertas.md`, más **D302** (la guía de prueba manual, hallazgos H5 a H7); crean los códigos **`RN-AU-09`** (D292) y **`RN-AU-10`** (D293), registrados en `05` y `06`. Las decisiones K que dependían de una pregunta ahora citan su D («Decisión del autor (D292)»).

## Context

**Lo que ya existe** (leído del código y de los specs, no supuesto):

- **Esquema** (migración `0006`): `usuario` con `hash_password`, `activo` y `token_version`. **No hace falta ninguna migración.**
- **Dominio** (`backend/app/domain/acceso/usuarios.py`): `MINIMO_DE_CARACTERES_DE_CONTRASENA = 10`, `MAXIMO_DE_BYTES_DE_CONTRASENA = 72`, `validar_contrasena_inicial(texto)` (levanta `EntradaInvalida((ContrasenaFueraDeRango(),))`) y las reglas RN-AU-06. `ContrasenaFueraDeRango(campo="contrasena")` (`domain/errors.py`) **ya acepta el nombre del campo**: sirve para `contrasena_nueva` sin cambiarla. `CredencialesInvalidas` (RN-AU-04) es solo del login.
- **Aplicación**: `iniciar_sesion` y `renovar_sesion` (`application/sesion.py`) firman con `claims_para(usuario, tipo, ahora, vigencia)`, que pone la `token_version` del usuario en el claim; `exigir_token_valido` compara esa versión en cada petición (`usuario_actual`) y en el refresh. `editar_usuario` (`application/usuarios.py`) ya incrementa `token_version` al desactivar con `guardar(replace(...))`. **`RepositorioUsuarios.guardar` solo escribe `activo` y `token_version`, no `hash_password`.** `HasherBcrypt.verificar` devuelve `False` (sin excepción) con más de 72 bytes; `hashear` levanta `ValueError` con más de 72 bytes.
- **API**: `requiere(permiso)` y `usuario_actual` (`api/seguridad.py`) dan el control de acceso en el orden de D208; `RESPUESTAS_DE_ACCESO` y `_respuesta_de_error` documentan los rechazos en OpenAPI; `post_login` pone `Cache-Control: no-store` con `_sin_cache` y responde `TokensSalida` (`access_token`, `refresh_token`, `token_type`, `expires_in`). El guard `tests/api/test_proteccion_de_rutas.py` exige token a toda ruta fuera de `RUTAS_PUBLICAS` (`/auth/login`, `/auth/refresh`): **`/auth/cambiar-contrasena` queda protegida sin tocar la lista**.
- **Frontend**: `crearSesion()` (`shared/api/sesion.ts`) tiene `guardar(access, refresh)` (el access en memoria y el refresh en `sessionStorage`, D219); `ProveedorDeSesion` expone `iniciarSesion`, `cerrarSesion` y `pedidoDelPanel`, **no** una forma de reemplazar los tokens desde una pantalla. Un `401` de una ruta del panel dispara la renovación y, si se repite, termina la sesión (`ingreso-al-panel`): por eso el rechazo de la contraseña actual **no puede ser `401`** (K7, D292). La pantalla de usuarios (C-09) tiene el panel lateral `cerrado | alta | edicion`, las acciones de fila deshabilitadas mientras esperan, `Aviso`, `mensajes.ts`, `IconoCerrar` e `IconoInfo`. El servidor falso ya lleva una versión de token por usuario (`versiones`) y la sube al desactivar.
- **Demo**: la odontóloga (id 1) y la recepcionista (id 2), con la contraseña de prueba del README (`demo-consultorio-2026`, `CONTRASENA_DEMO`, D197); la base en memoria se pierde al reiniciar, así que cambiar contraseñas en la demo no deja rastro.

## Goals / Non-Goals

**Goals:**

- Que el largo de la contraseña sea **una sola regla de dominio** para la inicial, la restablecida y la cambiada (RN-AU-07), y que las reglas nuevas sean funciones puras testeadas sin base.
- Que cambiar o restablecer una contraseña corte **todos** los tokens anteriores del usuario sin tabla de tokens (RN-AU-03), y que el cambio propio no cierre la sesión desde la que se hace (US-093 CA-7, «las demás sesiones», D291).
- Que ningún cambio de contraseña deje un token anterior vigente aunque dos cambios lleguen a la vez (K10, D299).
- Que la pantalla muestre lo que decide la API, con cada rechazo y su código, reutilizando las piezas de C-09 y C-11.
- Sin dependencias nuevas, sin migración y sin tocar el comportamiento de las rutas existentes.

**Non-Goals:**

- Recuperación por email, contraseñas temporales o vencidas, historial o complejidad de contraseñas (proposal, «Fuera de alcance»).
- Revocar sesiones de a una o listarlas (no hay tabla de tokens, RN-AU-03).
- Límite de peticiones o registro de eventos de seguridad en las rutas nuevas (como D195).
- Saber en el navegador quién inició sesión (D249): «Restablecer contraseña» aparece también en la propia fila y la API la rechaza (K5, D293).
- Cambiar `SEED_USUARIO_PASSWORD` o el seed (D197).

## Decisions

### K1. Dos capabilities nuevas — Decisión del autor (D290; Q1; sigue D241 y D271)

`contrasenas-de-usuarios` (el contrato de las dos rutas, pytest) y `pantalla-de-contrasenas` (el navegador, Vitest), con el corte por suite de C-09 (D241) y C-13 (D271), que quedaron limitados a su change: C-10 tiene su propia excepción a «un change, una capability» (regla dura 12), registrada en D290 y limitada a C-10 (hallazgo H4). Ninguna capability existente recibe delta: `gestion-de-usuarios` no cambia (el `PATCH` sigue rechazando `contrasena` con `422` de formato), `sesion-del-panel` ya especifica el `401` por `token_version` y el login, `proteccion-del-panel` ya exige token a toda ruta nueva, y `pantalla-de-usuarios` e `ingreso-al-panel` no cambian ningún requisito (la acción de fila y el enlace nuevos se describen en `pantalla-de-contrasenas`). **Alternativas** en Q1 y en D290.

### K2. Estructura del backend — Propuesta (aplica `08`, «Estructura de directorios», y la regla dura 3)

```
backend/app/domain/acceso/usuarios.py   validar_largo_de_contrasena(texto, campo) (K3); validar_contrasena_inicial queda como alias
                                        de validar_largo_de_contrasena(texto, "contrasena"); exigir_no_restablecer_la_propia (K5)
backend/app/domain/errors.py            ContrasenaActualIncorrecta (RN-AU-09, D292); RestablecerLaPropia (RN-AU-10, D293)
backend/app/domain/acceso/roles.py      Permiso.CONTRASENA_PROPIA (_TODOS) (K8, D298); restablecer usa Permiso.USUARIOS_EDITAR
backend/app/application/usuarios.py     restablecer_contrasena(usuario_id, contrasena, actor, uow, hasher)
backend/app/application/sesion.py       cambiar_contrasena(actor, actual, nueva, uow, hasher, firmador, vigencias, reloj) -> TokensDeSesion
backend/app/application/puertos.py      RepositorioUsuarios + obtener_para_cambiar(usuario_id) (FOR UPDATE, K10) y guardar con hash_password
backend/app/infrastructure/repositories/usuarios.py
backend/app/api/esquemas.py             RestablecerContrasenaEntrada, CambiarContrasenaEntrada (extra="forbid")
backend/app/api/errores.py              las dos clases nuevas en la tabla de clases y de textos fijos (K9)
backend/app/api/routers/usuarios.py     POST /usuarios/{usuario_id}/restablecer-contrasena
backend/app/api/routers/auth.py         POST /auth/cambiar-contrasena
```

`cambiar_contrasena` va en `application/sesion.py` porque firma tokens como `iniciar_sesion` (K6); `restablecer_contrasena`, en `application/usuarios.py`, junto a la administración de usuarios.

### K3. Una sola regla de largo — Decisión del autor (RN-AU-07, D74, D242) + Propuesta (forma)

`validar_largo_de_contrasena(texto, campo)`: al menos 10 caracteres (`len`) y como máximo 72 bytes en UTF-8, sin recortar ni normalizar; fuera de rango, `EntradaInvalida((ContrasenaFueraDeRango(campo),))` → `422` con `codigos` `["RN-AU-07"]` y el error del campo (`contrasena` al restablecer, `contrasena_nueva` al cambiar), con el mismo mensaje fijo de C-09 («La contraseña debe tener de 10 caracteres a 72 bytes.»), que no repite la contraseña. Es **validación de entrada del dominio** (RN-GL-02), después del formato de Pydantic (límite de D177 y D242: un cuerpo con errores de formato devuelve solo esos; escenario propio) y antes de toda regla de negocio. `validar_contrasena_inicial` queda como envoltorio (o se reemplaza en el REFACTOR) sin cambiar ningún test de C-09. `contrasena_actual` **no** pasa por esta regla: es una credencial a comparar, no una contraseña a guardar (K7).

### K4. Contrato de la API — Decisión del autor (D291, D292, D293, D298) + Propuesta (`204` al restablecer)

| Ruta | Cuerpo | Éxito | Rechazos (en orden, K9) |
|---|---|---|---|
| `POST /usuarios/{usuario_id}/restablecer-contrasena` | `contrasena` (texto); `extra="forbid"` | `204` sin cuerpo | `401`, `403` `RN-AU-05`, `422` de formato, `422` `RN-AU-07`, `404` `RN-GL-04`, `409` `RN-AU-10` (la propia, D293) |
| `POST /auth/cambiar-contrasena` | `contrasena_actual` (texto, al menos 1 carácter), `contrasena_nueva` (texto); `extra="forbid"` | `200` con `TokensSalida` y `Cache-Control: no-store` (D291) | `401`, `403` `RN-AU-05` (sin roles, D298), `422` de formato, `422` `RN-AU-07`, `422` `RN-AU-09` (actual incorrecta, D292) |

`204` al restablecer (Propuesta): la pantalla no necesita el usuario (la fila no cambia: `UsuarioSalida` no lleva nada de la contraseña) y no hay nada que devolver sin filtrar datos; el precedente es `DELETE /bloqueos/{id}` (C-13). El tipo `null` en `contrasena` es error de formato (`EntradaDeEdicion` no hace falta: los dos campos son obligatorios). Ninguna respuesta repite una contraseña.

### K5. Restablecer — Decisión del autor (D293, D294, D299)

`restablecer_contrasena(usuario_id, contrasena, actor, uow, hasher)`: (1) `validar_largo_de_contrasena(contrasena, "contrasena")`; (2) dentro de la transacción, `obtener_para_cambiar(usuario_id)` (bloqueo de fila, K10); si no existe → `UsuarioNoEncontrado` (`404` `RN-GL-04`, recurso `usuario`, como C-09); (3) `exigir_no_restablecer_la_propia(actor.id, usuario_id)` → `RestablecerLaPropia` (`409` `RN-AU-10`, D293); (4) `guardar` con `hash_password = hasher.hashear(contrasena)` y `token_version + 1`. Un usuario **inactivo** se restablece igual y sigue inactivo (D294, como D253: `activo` y la contraseña son independientes). No toca roles ni `profesional`.

### K6. Cambiar la propia — Decisión del autor (D291, D292, D295)

`cambiar_contrasena(actor, actual, nueva, uow, hasher, firmador, vigencias, reloj)`: (1) `validar_largo_de_contrasena(nueva, "contrasena_nueva")`; (2) dentro de la transacción, `obtener_para_cambiar(actor.id)`; (3) si `not hasher.verificar(actual, usuario.hash_password)` → `ContrasenaActualIncorrecta` (`422` `RN-AU-09`, D292; una actual de más de 72 bytes da `False` sin excepción, escenario propio); (4) `guardar` con el hash nuevo y `token_version + 1`; (5) firmar con `claims_para` un access y un refresh **con la versión nueva** y `ahora = reloj()` (`utc_now` inyectable, regla dura 2), como `iniciar_sesion`. La nueva igual a la actual se acepta (D295: ninguna fuente la prohíbe) y también sube la versión. El usuario sale del token (`actor`): **no hay id en la URL** y nadie cambia la contraseña de otro por esta ruta.

### K7. El rechazo de la contraseña actual no es `401` — Decisión del autor (D292)

Si fuera `401`, el cliente del panel lo leería como sesión vencida: intentaría renovar, repetiría el pedido y, con el segundo `401`, cerraría la sesión (`ingreso-al-panel`). Además el `401` de las rutas protegidas es la respuesta fija de sesión inválida (D206). Por eso es una **regla de negocio** (necesita el hash guardado: RN-GL-02) que responde `422`, como las reglas que no son conflictos (`RN-AG-04`, `RN-AG-04b`), con `type` `/errores/contrasena-actual-incorrecta`, `title` «Contraseña actual incorrecta» y `detail` fijo «La contraseña actual no es correcta.». El código es **`RN-AU-09`** (nuevo; regla dura 4 y precedente de `RN-AU-08`, D243): «el cambio de la propia contraseña exige la contraseña actual; si no coincide, se rechaza sin cambiar nada». Registrado en `05` con D292 (hallazgo H1).

### K8. Permisos — Decisión del autor (matriz de `03` y D298)

Restablecer: `Permiso.USUARIOS_EDITAR` (solo `odontologo`; fila «Usuarios del consultorio», «restablecer contraseña»). Cambiar la propia: permiso nuevo `Permiso.CONTRASENA_PROPIA` con los tres roles (fila «Cambiar la propia contraseña», «U propio» para los tres), con `requiere(...)`, así un usuario sin roles recibe `403` como en el resto del panel (`proteccion-del-panel`, «un usuario sin roles no puede ni leer»). El test de la matriz (`tests/unit/test_roles.py`) suma la fila y el contador del guard de permisos sube en 1; el de rutas protegidas, en 2 (solo cambia el número esperado, como en C-12 y C-13).

### K9. Clases de rechazo y orden de evaluación — Propuesta (aplica RN-GL-02, D135 y D208)

| # | Clase | `POST /usuarios/{id}/restablecer-contrasena` | `POST /auth/cambiar-contrasena` |
|---|---|---|---|
| 0 | Límite de FastAPI | JSON roto: `422` sin código (D208) | igual |
| 1 | Control de acceso | `401` `RN-AU-03`; `403` `RN-AU-05` | igual |
| 2 | Validación de formato (Pydantic) | `422` con `codigos` vacío: campo ausente, `null`, no texto, campo de más | igual; los dos campos ausentes dan dos errores en el mismo `422` |
| 3 | Validación de entrada del dominio | `422` `RN-AU-07` en `contrasena` | `422` `RN-AU-07` en `contrasena_nueva` |
| 4 | Recurso de la URL | `404` `RN-GL-04` | — |
| 5 | Reglas de negocio, de a una | `409` `RN-AU-10` (la propia, D293) | `422` `RN-AU-09` (actual incorrecta, D292) |

El `404` va después de la entrada, como en el `PATCH` de C-09 (U13). La regla de la propia (fila 5) va después del `404` porque el id de la URL del propio usuario siempre existe. Cada orden que se puede cruzar tiene escenario: `401` antes que `422`, `403` antes que `404`, `422` antes que `404`, largo antes que `RN-AU-09` y que el `409` `RN-AU-10`, formato antes que largo (en las dos rutas, hallazgo H9).

Clases nuevas en `api/errores.py`: `ContrasenaActualIncorrecta` → `422` (K7); `RestablecerLaPropia` → `409` `RN-AU-10`, `/errores/restablecer-la-propia`, «Operación no permitida», `detail` fijo «La propia contraseña se cambia con POST /auth/cambiar-contrasena, pidiendo la actual.».

### K10. Concurrencia: bloqueo de la fila del usuario — Decisión del autor (D299; aplica DD-04 y el patrón de D248)

Hoy `editar_usuario` lee y escribe `token_version` sin bloqueo. Con dos cambios de contraseña simultáneos sobre el mismo usuario, los dos leerían la versión `v` y escribirían `v + 1`: los tokens que firma uno (`v + 1`) **seguirían valiendo después del otro**, que justo quería cortarlos (por ejemplo, la odontóloga restablece la contraseña de una sesión robada mientras el ladrón, que conoce la actual, la cambia). `obtener_para_cambiar(usuario_id)` lee el usuario con `SELECT … FROM usuario WHERE id = :id FOR UPDATE` dentro de la transacción; el segundo espera y lee la versión que el primero confirmó. En SQLite es un no-op (la suite por defecto es de un hilo), como `bloquear_administracion`. Se prueba en el perfil `postgres` con el arnés de `tests/postgres/carrera.py`, con dos escenarios: «dos cambios simultáneos … suben la versión dos veces» y «restablecer y cambiar la propia a la vez» (el caso del ladrón, hallazgo H8). La desactivación de C-09 (`editar_usuario`) **no se toca** (fuera del alcance; su carrera con un cambio de contraseña queda como límite conocido: si los dos escriben `v + 1`, el usuario igual queda inactivo y `activo` se verifica en cada petición, RN-AU-04). **A verificar en el change (V2, vale para restablecer y para el cambio propio: tareas 4.2 y 5.2, hallazgo H10):** hashear con bcrypt dentro de la transacción retiene la fila unos 250 ms con 12 rondas; si en SQLite retiene la conexión más de lo aceptable, se hashea antes de abrir la transacción (como V2 de C-09) y solo la comparación de la actual queda adentro.

### K11. Persistencia — Propuesta

`guardar(datos)` pasa a escribir también `hash_password` (hoy solo `activo` y `token_version`); los usos de C-09 pasan el mismo hash que leyeron, así que su comportamiento no cambia (lo cubren sus tests). `obtener_para_cambiar` usa `with_for_update()` sobre `UsuarioModelo`. Sin migración.

### K12. Sesión del navegador después del cambio — Decisión del autor (D291) + Propuesta (forma)

`ProveedorDeSesion` gana `reemplazarTokens(access, refresh)`, que llama a `sesion.guardar` (el refresh en `sessionStorage` bajo la misma clave versionada, D219) sin cambiar `estado` ni `aviso`. La pantalla «Mi contraseña» la llama con el `200`; la petición siguiente sale con el access nuevo, sin `POST /auth/refresh`, y recargar la página renueva con el refresh nuevo (escenarios propios). Las peticiones que estuvieran en vuelo con el access viejo reciben `401`, renuevan con el refresh **nuevo** (ya guardado) y se repiten: el comportamiento existente de `ingreso-al-panel` alcanza. No se agrega ninguna llamada nueva al cliente HTTP fuera de `pedidoDelPanel`.

### K13. Estructura del frontend — Propuesta (aplica U17 de C-09 y B14 de C-13)

```
frontend/src/features/contrasenas/apiContrasenas.ts (+ .test.ts)   restablecerContrasena(pedido, id, contrasena), cambiarContrasena(pedido, actual, nueva) -> tokens
frontend/src/features/contrasenas/PaginaMiContrasena.tsx (+ .test.tsx)   «Mi contraseña»: tres campos, «Cambiar contraseña», avisos
frontend/src/features/contrasenas/mensajes.ts (+ .test.ts)        textos fijos de K14
frontend/src/features/usuarios/PanelDeUsuario.tsx                  + modo "restablecer" (campo, ayuda, nota)
frontend/src/features/usuarios/TablaDeUsuarios.tsx                 + acción de fila «Restablecer contraseña»
frontend/src/features/usuarios/PaginaUsuarios.tsx (+ .test.tsx)   + estado del panel `restablecer` y aviso de la tabla; los escenarios nuevos
                                                                     van en un archivo propio, RestablecerContrasena.test.tsx
frontend/src/shared/api/ProveedorDeSesion.tsx                      + reemplazarTokens (K12)
frontend/src/shared/iconos/                                         + ícono de llave o candado (SVG en línea, aria-hidden)
frontend/src/App.tsx, pages/PanelBase.tsx                          ruta hija "contrasena" y enlace «Mi contraseña»
frontend/src/test/servidorFalso.ts                                 las dos rutas con el orden de K9, hash ficticio por usuario
                                                                     (la contraseña en claro del falso, que nunca sale de los tests), versión por usuario,
                                                                     login con la contraseña vigente de cada usuario, respuesta retenida y falla de red
```

### K14. Mensajes fijos de la pantalla — Propuesta (como U19 de C-09: no se muestra el `detail` de la API)

| Situación | Mensaje | Dónde |
|---|---|---|
| Restablecer, `204` | «Contraseña restablecida. Se cerraron las sesiones de <email>.» | Aviso de la tabla |
| Restablecer, nota del panel | «Al guardar se cierran todas las sesiones de este usuario.» | Panel lateral |
| `422` `RN-AU-07` | «La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).» (el de C-09) | Debajo de «Contraseña nueva» |
| `409` `RN-AU-10` (la propia) | «Tu propia contraseña se cambia desde «Mi contraseña» (RN-AU-10).» | Aviso del panel |
| `403` `RN-AU-05` al restablecer | «Tu usuario no tiene permiso para modificar usuarios (RN-AU-05).» (el de C-09) | Aviso del panel |
| `404` `RN-GL-04` | «El usuario ya no existe (RN-GL-04).» (el de C-09; cierra el panel y recarga) | Aviso de la tabla |
| Cambiar, `200` | «Contraseña cambiada. Tus otras sesiones se cerraron.» | Aviso de éxito de «Mi contraseña» |
| `422` `RN-AU-09` | «La contraseña actual no es correcta (RN-AU-09).» | Debajo de «Contraseña actual» |
| Repetición distinta (local) | «Las contraseñas nuevas no coinciden.» | Debajo de «Repetir contraseña nueva» |
| `403` `RN-AU-05` al cambiar | «Tu usuario no tiene permiso para cambiar la contraseña (RN-AU-05).» | Aviso de «Mi contraseña» (solo un usuario sin roles; se prueba como función pura de `mensajes.ts`, sin escenario) |
| `422` de otro campo | «Revisá los datos.» | Aviso (red; función pura, sin escenario, como H5 de C-09) |
| Sin conexión | El de C-11 | Aviso del panel o de la pantalla |

### K15. Pantalla «Mi contraseña» — Decisión del autor (D296, D297) + Propuesta (detalle; aplica `vercel-react-best-practices`)

Ruta hija `contrasena` de `/panel`, enlace «Mi contraseña» en la barra junto a los demás, para todos los roles (no hay datos del usuario en la pantalla, D225). Tres campos `type="password"` con `required` y `autocomplete` (`current-password` en la actual, `new-password` en la nueva y la repetición), sin `minlength` ni `maxlength` (la API decide el largo, D232). La repetición se compara en el navegador antes de mandar (D296): es un control de tipeo de un campo oculto, no una regla de la API, y evita que alguien quede sin poder entrar por un error de tipeo en su propia contraseña. Con `200`: `reemplazarTokens`, campos vacíos y aviso de éxito. Las contraseñas viven solo en el estado del formulario y se descartan al salir de la pantalla. «Cambiar contraseña» deshabilitado mientras espera. Sin «Cancelar» (no hay panel que cerrar; salir de la pantalla descarta).

### K16. Restablecer en la pantalla de usuarios — Decisión del autor (D296, D297) + Propuesta (detalle; aplica U18 de C-09)

Acción de fila «Restablecer contraseña» (en todas las filas, también la propia y las inactivas; sin conocer el rol, D249) que abre el panel lateral en un tercer modo `restablecer`: título «Restablecer contraseña», el email como texto, «Contraseña nueva» (`type="password"`, `required`, `autocomplete="new-password"`, con la ayuda) y la nota de K14; pie con «Cancelar» y «Guardar» y el botón «Cerrar» del encabezado (D254). Con `204`: cierra el panel, vacía el campo y muestra el aviso de la tabla. **Sin campo de repetición** (D296: un error de tipeo se corrige restableciendo otra vez). Mientras espera, «Guardar» se deshabilita (escenario propio). Con `404`, cierra el panel y recarga la lista, como la edición de C-09.

### K17. Tests y servidor falso — Decisión del autor (D211, D222, D227, reglas duras 5 y 6) + Propuesta (detalle)

- **Backend**: unidad (`tests/unit/test_usuarios.py`: largo con bordes 9/10 caracteres y 72/73 bytes en los dos campos, no restablecer la propia; `tests/unit/test_roles.py`: el permiso nuevo), integración (`tests/integration/test_repositorio_usuarios.py`: `guardar` con hash, `obtener_para_cambiar`; `tests/integration/test_contrasenas.py`: los dos casos de uso), API (`tests/api/test_contrasenas.py`, con access tokens reales, sin `dependency_overrides`, con la app de pocas rondas de bcrypt como C-09) y perfil `postgres` (`tests/postgres/test_contrasenas_concurrentes.py` con el arnés de carrera). Sin mocks de sesión ni de repositorio. Nombres con el escenario (`US-093 CA-6: …`).
- **Frontend**: Vitest con el servidor falso inyectado, sin `vi.mock`, `vi.fn`, `vi.stubGlobal` ni temporizadores falsos. **A verificar en el change (V3, antes de 8.1):** cómo autentica hoy el login del falso (usa `EMAIL_ACTIVA` y una contraseña fija): tiene que aceptar la contraseña vigente de cada usuario sin cambiar lo que verifican los tests de C-08, C-09, C-11, C-12 y C-13.

### K18. Versiones y dependencias — Propuesta

**Sin dependencias nuevas** ni cambios de versión: bcrypt 5.0.0, PyJWT y SQLAlchemy 2.0 ya instalados; en el frontend nada nuevo. `backend/pyproject.toml`, `frontend/package.json` y `package-lock.json` no cambian; no hay pins nuevos que fijar (regla de `config.yaml`).

### K19. Demo, README y guía de prueba manual — Propuesta + Decisión del autor (la guía, D302)

- **Demo**: sin datos nuevos. El recorrido restablece y cambia contraseñas de la demo en memoria (se pierden al reiniciar).
- **README**: sección «Contraseñas» en «Probar desde Swagger» (restablecer, el `401` del token anterior, cambiar la propia con los tokens nuevos, `RN-AU-07`, `RN-AU-09`, el `409` de la propia), «Pantalla de contraseñas» en «Panel (interfaz)», la tabla escenario → test con la cantidad real de tests y los límites conocidos (sin límite de peticiones en el cambio, como D195; «Restablecer contraseña» visible en la propia fila, D249; la carrera entre desactivar y cambiar la contraseña, K10). El límite de D197 («no hay restablecimiento») se actualiza: ahora la contraseña de un usuario sembrado se cambia por la API.
- **Guía de prueba manual de C-09 y C-10** (`docs/guias/prueba-manual-c09-c10.md`, ubicación confirmada por el autor, D302, hallazgo H7), pedida por el autor: cómo levantar la demo sin Docker (API y frontend), los usuarios del seed y su contraseña de prueba, **la creación del dueño y de la colega** (un segundo `odontologo`) por la pantalla de usuarios antes de los pasos que los usan (la demo solo trae a la odontóloga y a la recepcionista; hallazgo H5), y el paso a paso con el **resultado esperado** de cada paso para C-09 (listar, alta con contraseña inicial, `RN-AU-07`, `RN-AU-08`, roles, desactivar y ver el corte de sesión en otra ventana privada, reactivar, los dos `409` `RN-AU-06`, el `403` de la recepcionista y del dueño) y para C-10 (restablecer la de la recepcionista y ver que su sesión abierta vuelve a `/ingresar`, entrar con la nueva y no con la vieja, la propia rechazada, cambiar la propia en «Mi contraseña» y ver que otra sesión abierta cae y la actual sigue, la actual incorrecta, la repetición distinta, la corta), sin ninguna contraseña real. El agente **ejecuta él mismo cada paso de C-09 y de C-10 con la demo** antes de escribirlo (no solo los de su prueba en el navegador; hallazgo H5) y **el autor la sigue y la aprueba antes del archive** (tarea del autor); si el código o la guía cambian después de ese ok, el agente le vuelve a avisar antes de archivar (D302, hallazgo H6).

### K20. Prueba en el navegador — Decisión del autor (D234, `rules.tasks`) + Propuesta (detalle)

El agente repite los escenarios de `pantalla-de-contrasenas` con la demo (salvo el del usuario que ya no existe, solo contra el falso) y en Compose, compara con las capturas de Stitch y anota las diferencias. Por ser **CRÍTICO**, la repetición manual del autor va como tarea, ahora con la guía de K19, que cubre también C-09 (pedido del autor).

### K21. Tamaño — Decisión del autor (D300)

**29 tareas en 13 grupos** para **38 escenarios** (21 de la API y 17 de la pantalla, después del `/opsx:update` con los hallazgos H3 y H8), frente a «alrededor de 20» de `CHANGES.md`: RED, GREEN y TRIANGULATE separados (TDD estricto), dos rutas con su orden de rechazos, el perfil `postgres`, la tarea bloqueante de Stitch, la guía manual y la tarea del autor. Excepción aceptada por el autor y limitada a C-10 (D300, hallazgo H4).

### K22. Skills aplicadas

- `auth-implementation-patterns`: hash adaptativo (bcrypt) y nunca la contraseña en claro, en logs ni en respuestas; **el cambio propio pide la actual**; invalidación en bloque por `token_version` al cambiar o restablecer (RN-AU-03); la sesión desde la que se cambia recibe tokens nuevos; mensajes de rechazo fijos que no repiten secretos; el servidor decide (la interfaz reacciona). **No aplicadas** por la KB (regla dura 9): límite de peticiones y registro de eventos de seguridad (D195), política de complejidad más allá del largo (D74).
- `fastapi-templates`: routers por recurso, esquemas de entrada separados, dependencias inyectadas, `204` sin cuerpo. **No aplica** su parte asíncrona (DD-12, regla dura 5).
- `python-error-handling`: errores de dominio con código; entrada junta y reglas de a una (RN-GL-02); el `401` reservado a la sesión (K7).
- `python-testing-patterns`: TDD estricto, bordes de los límites (9/10, 72/73), sin mocks (regla dura 6), arnés de carrera en el perfil `postgres`.
- `python-design-patterns`: reglas puras en el dominio y casos de uso como orquestadores; una sola regla de largo (K3).
- `vercel-react-best-practices` (SPA de Vite): estado derivado en el render, `setState` funcional, sin componentes definidos dentro de otros, ternario en vez de `&&`, sin *barrels*.
- `database-migration` y `supabase-postgres-best-practices`: **no aplican** (sin migración); el bloqueo `FOR UPDATE` sigue el patrón ya usado (D248).

## Referencia visual (Stitch)

**Regla (D234, Decisión del autor):** toda pantalla del frontend se implementa a partir de una pantalla generada en Stitch con el design system «Clinical Ops»; el design cita el id de la pantalla y su evidencia; si Stitch no entrega la pantalla, el change de interfaz no se cierra; la KB y el spec mandan sobre el contenido. Las pantallas se consiguieron antes de aprobar el plan (D301), en la tarea 1.2.

- **Pantalla «Mi contraseña»**: `projects/14200813501064679723/screens/fa6faa69cae34252a7c79e2cb82210c5` («Mi contraseña - Turnos Odontológicos AR», `DESKTOP`).
- **Pantalla «Usuarios» con el panel «Restablecer contraseña»**: `projects/14200813501064679723/screens/925f1e4028294cb2bb9bdeeea81ffd09` («Usuarios - Restablecer contraseña - Turnos Odontológicos AR», `DESKTOP`), variante de la de C-09 (`projects/14200813501064679723/screens/a9ea01c76448418b9168e729229a36e5`).
- Las dos se generaron con el design system «Clinical Ops» (`assets/b683d44391ab410db2dd48aa71ed0b47`) al primer intento, el 2026-10-26; el MCP devolvió los ids directamente y `get_screen` devuelve cada una por su id.
- **Evidencia**: `docs/skills-mcp/evidencias/sesion-nueva/stitch-contrasenas.md` (pedidos, intentos, ids, revisión de datos y sugerencias no aceptadas) y `stitch-contrasenas-pantalla/` (`mi-contrasena.png` y `mi-contrasena.html`; `usuarios-restablecer.png` y `usuarios-restablecer.html`; capturas a 1280 × 1024).

**Qué se toma — «Mi contraseña»:**
- La barra del panel compartida (C-08, C-11, C-09, C-12 y C-13) con el enlace nuevo «Mi contraseña» al final, con ícono de llave (SVG en línea) y la pastilla activa como las demás.
- El título «Mi contraseña» sin subtítulo y una sola tarjeta angosta (formulario) alineada a la izquierda, con el aviso de éxito verde suave con ícono **debajo de la tarjeta**.
- Las etiquetas chicas en mayúsculas sobre los campos (como C-09 y C-13), la ayuda «De 10 caracteres a 72 bytes.» debajo de «Contraseña nueva» y «Cambiar contraseña» primario a todo el ancho de la tarjeta, con ícono de candado.
- El estilo del error de campo de `RN-AU-09` (y de `RN-AU-07` y de la repetición distinta): borde rojo en el campo con `aria-invalid="true"` y el texto rojo con ícono de alerta debajo; los textos son los de K14.

**Qué se toma — «Usuarios» con «Restablecer contraseña»:**
- La pantalla de C-09 sin cambios (encabezado, «Listado general», tabla y panel lateral), con la acción de fila nueva entre «Editar» y «Desactivar» o «Reactivar», con ícono de llave; su texto visible es **«Restablecer contraseña»** (el del spec), no el «Restablecer» abreviado de Stitch.
- El panel lateral en el modo `restablecer`: ícono de llave y título «Restablecer contraseña» en el encabezado, con el botón «Cerrar» de D254; «Contraseña nueva» con la ayuda; la nota informativa azul con ícono (la `nota-informativa` de C-11 y C-09) con el texto de K14; el pie «Cancelar» y «Guardar» de C-09.
- El aviso de éxito verde suave con ícono arriba de la tabla, a todo el ancho (el aviso de la tabla de C-09), con el texto de K14.
- El error de `RN-AU-07` bajo «Contraseña nueva» con el estilo de error de campo de C-09.

**Qué se rechaza (motivo):**
- Los asteriscos de obligatorio: las etiquetas son las del spec, como en C-13.
- El ícono de alerta **dentro** del campo con error: el ícono va con el texto del error, como en C-09 y C-13.
- El pie de página institucional («Módulo de Seguridad y Credenciales · Sede Central»): no hay sedes (D173) ni existe en las otras pantallas.
- Los íconos en todas las pastillas de la barra (variante de usuarios): la barra existente no cambia; solo se suma el enlace «Mi contraseña» con su ícono.
- El email del panel en un campo de solo lectura con candado y la etiqueta «USUARIO / EMAIL»: el spec dice «el email del usuario como texto», como el panel de edición de C-09.
- La insignia «Modificando» y el resaltado de la fila mientras el panel restablece: no hay escenario que lo pida (en C-09 la marca «Editando» es solo de la edición, con su escenario); no se implementa (Q13 → D303: sin resaltar la fila).
- La negrita de «Contraseña restablecida.» dentro del aviso: el texto de K14 va entero, como los demás avisos de C-09.
- El pie de la tabla («Módulo administrativo con control de integridad clínica», «Filtrado: 3 de 3 registros»): ya rechazado en C-09 (sin respaldo en la KB).
- La tarjeta «Estado alternativo / Validación» con «Referencia: Error de validación (RN-AU-07)»: es una referencia del pedido; el error va debajo del campo del panel.
- El ancho de la columna ACCIONES que en la captura corta los botones: la tabla de C-09 ya acomoda sus acciones; si con la acción nueva no entran, se resuelve en la traducción visual (11.1) sin quitar ninguna acción, y se anota en la comparación de 12.1.
- Los valores precargados en campos de contraseña del HTML (`secretpassword123`, `corta`): los campos de contraseña arrancan vacíos y nunca se precargan.
- Las sugerencias de Stitch: validación en vivo (D232, D296: la API decide el largo), modal de confirmación antes de invalidar las otras sesiones (sin respaldo, como D250), vista móvil propia (sin escenario), y las que no son de este change.
- Tailwind, Google Fonts y Material Symbols por CDN (CSP `default-src 'self'`): se traduce a `tokens.css` y `panel.css` (sección «Contraseñas») y a marcado de React **sin dependencias nuevas**; íconos en SVG en línea con `aria-hidden="true"` y `focusable="false"`.

**Ya decidido sin la pantalla, por la KB y los specs** (se mantiene aunque Stitch muestre otra cosa): los textos de K14; ninguna contraseña visible fuera de su campo; sin datos de quien inició sesión (D225); sin «ver contraseña», medidor de fortaleza ni generador (proposal, «Fuera de alcance»); las acciones visibles para todos (D249); la repetición solo en «Mi contraseña» (D296). La prueba en el navegador (12.1) compara la implementación con `mi-contrasena.png` y `usuarios-restablecer.png` y anota las diferencias en la evidencia.

## Contradicciones y huecos encontrados en las fuentes

1. **«Las demás sesiones» y `token_version`**: US-093 CA-7 dice que el cambio invalida «las demás sesiones», pero RN-AU-03 incrementa una sola versión por usuario y el token con que se pide el cambio también la lleva: sin tokens nuevos, la sesión actual también cae. → Q2 → D291: tokens nuevos en el `200` (K6, K12).
2. **El rechazo de la contraseña actual** no tenía código ni estado en la KB (RN-AU-04 es del login y su `401` rompe el cliente del panel). → Q3 → D292: `RN-AU-09` con `422` (K7), registrado en `05` y `06`.
3. **«Puede restablecer la de cualquier usuario»** (RN-AU-07) incluye literalmente la propia, pero la misma regla dice que la propia se cambia «pidiendo la actual»; restablecerla sin la actual le saltea esa protección a quien tenga el access de la odontóloga. → Q4 → D293: código propio `RN-AU-10` con `409` (K5); RN-AU-07 de `05` ya dice «cualquier **otro**» (hallazgo H2).
4. **Restablecer a un usuario inactivo** y **la nueva igual a la actual**: la KB no decía nada. → Q5 y Q6 → D294 y D295.
5. **«U propio» para los tres roles** (`03`) frente a un usuario sin roles, que la API de C-09 no crea pero la base admite. → Q9 → D298 (K8).
6. **Carrera de `token_version`**: C-09 lee y escribe la versión sin bloqueo; dos cambios simultáneos pueden dejar vigentes los tokens de uno. → Q10 → D299 (K10).
7. **`RepositorioUsuarios.guardar`** no escribe `hash_password`. → K11.
8. **La entrada de C-10 en `CHANGES.md`** no lista `RN-AU-08` en «Leer antes» aunque el archive de C-09 lo pedía (D243); no afecta a C-10 (no hay emails nuevos) y se corrige al archivar.
9. **Stitch desconectado** en el propose. → Q12 → D301: tarea 1.2 antes de aprobar el plan; las dos pantallas se obtuvieron el 2026-10-26 («Referencia visual (Stitch)»).

## Risks / Trade-offs

- [Un access robado de cualquier usuario permite probar contraseñas actuales en `POST /auth/cambiar-contrasena` sin límite] → bcrypt con 12 rondas limita el ritmo por proceso y la API se publica en `127.0.0.1`; límite conocido del README, como D195 en el login.
- [Un access robado de la odontóloga restablece la contraseña de cualquier otro usuario] → Inherente a CA-6 (el odontólogo administra usuarios); el access vive 15 minutos y el usuario afectado lo nota al no poder entrar. `RN-AU-10` (D293) impide al menos que la use para cambiar la propia sin la actual.
- [Tokens que siguen valiendo tras una carrera] → K10, con escenario en el perfil `postgres`; la carrera con la desactivación de C-09 queda como límite conocido (el usuario queda inactivo igual).
- [bcrypt dentro de la transacción retiene la fila] → V2 (K10); son operaciones raras y cortas.
- [La sesión del navegador queda con tokens viejos si `reemplazarTokens` falla] → el `401` siguiente renueva con el refresh guardado; si el refresh también es viejo, la sesión termina con el aviso de sesión terminada, que es el comportamiento seguro.
- [El servidor falso se aparta de la API] → cuerpos copiados del spec y de `api/errores.py`; la prueba en el navegador repite los escenarios contra la API real.
- [Stitch no entrega la pantalla] → tarea 1.2 bloqueante para el frontend y el archive; el backend (grupos 2 a 7) no depende de ella.

## A verificar en el change

- **V1** (antes de la tarea 2.1): que `validar_contrasena_inicial` se pueda expresar con la regla general sin cambiar ningún test de C-09 (`tests/unit/test_usuarios.py`, `tests/api/test_usuarios.py`, `tests/unit/test_configuracion.py`). **Resultado (Apply, 2026-10-26): sí; `validar_contrasena_inicial` quedó como envoltorio de `validar_largo_de_contrasena(texto, "contrasena")` y ningún test de C-09 cambió.**
- **V2** (antes de la tarea 4.2; la decisión vale también para 5.2, hallazgo H10): hashear dentro o fuera de la transacción con el bloqueo de fila (K10), en restablecer y en el cambio propio. **Resultado (Apply, 2026-10-26): bcrypt con 12 rondas tarda unos 343 ms al hashear y 348 ms al verificar. Se hashea la contraseña nueva **antes** de abrir la transacción (restablecer y cambiar la propia); solo la verificación de la actual queda adentro, con la fila bloqueada, porque debe compararse con el hash ya confirmado (H8).**
- **V3** (antes de la tarea 8.1): el login del servidor falso con la contraseña vigente de cada usuario, con los tests de C-08 a C-13 en verde (K17). **Resultado (Apply, 2026-10-26): el login del falso solo aceptaba a la odontóloga con `CONTRASENA_FICTICIA`. Ahora busca al usuario del catálogo, exige que esté activo y compara con su contraseña vigente (mapa por usuario): la odontóloga conserva `CONTRASENA_FICTICIA` y los demás parten de `CONTRASENA_DEMO` (`demo-consultorio-2026`, la «actual de todos» del spec), así la recepcionista sigue sin poder entrar con `CONTRASENA_FICTICIA` (US-090 CA-3 de C-08). Los 204 tests de C-08 a C-13 siguieron en verde sin cambiar ninguno.**
- **V4** (antes de la tarea 6.1, con Docker): que `with_for_update()` sobre `UsuarioModelo` emite `FOR UPDATE` en PostgreSQL y nada en SQLite, y que el arnés de carrera admite dos restablecimientos del mismo usuario y un restablecimiento con un cambio propio a la vez. **Resultado (Apply, 2026-10-26): sí; el SQL de `with_for_update()` sobre `UsuarioModelo` termina en `FOR UPDATE` en PostgreSQL y no lleva nada en SQLite, y el arnés admitió los dos casos; sin el bloqueo los dos tests del perfil `postgres` fallan (versión 1 en vez de 2, y el cambio propio no responde `RN-AU-09`). Hallazgo: `obtener_para_cambiar` usa `populate_existing` para no leer una copia vieja del mapa de identidad después de esperar.**
- **V5** (antes de la tarea 12.1, en Compose): consola sin violaciones de la CSP con las pantallas nuevas y sus íconos. **Resultado (Apply, 2026-10-26): sin violaciones; con Compose (nginx con `default-src 'self'`) se recorrieron «Usuarios» con el panel «Restablecer contraseña» y «Mi contraseña», con un oyente de `securitypolicyviolation` (0 eventos) y la consola sin mensajes de la CSP; detalle en `docs/skills-mcp/evidencias/sesion-nueva/stitch-contrasenas.md`, sección 6.**

## Migration Plan

1. **Hecho (2026-10-26):** con las respuestas del autor a Q1 a Q12 y a los hallazgos H1 a H11, un `/opsx:update` registró D290 a D303 en `knowledge-base/10_preguntas_abiertas.md`, `RN-AU-09` y `RN-AU-10` en `05` (y en US-093 de `06`), y ajustó los artefactos. La revisión de `revisor-de-escenarios` va antes de aprobar el plan (`CLAUDE.md`, «Flujo de Trabajo»). Con el ok del autor al plan completo (CRÍTICO), se commitean los artefactos (con el `[~]` de C-10 en `CHANGES.md`) y, aparte, el `docs(kb)` de las decisiones.
2. El Apply no lleva migración ni variables nuevas: `docker compose up --build -d` reconstruye `api` y `frontend`.
3. **Efecto visible**: desde este change, las contraseñas se pueden restablecer y cambiar por la API y el panel; un cambio corta los tokens anteriores del usuario.
4. **Vuelta atrás**: revertir los commits del change. Las contraseñas cambiadas en una base PostgreSQL quedan cambiadas (el hash es válido para el login de C-06); no hay datos que migrar.

## Notas para el archive

No se editan ahora ni durante el Apply:

- `CHANGES.md`: marcar C-10 con `[x]`; sumar `RN-AU-08` (D243, contradicción 8), `RN-AU-09` (D292) y `RN-AU-10` (D293) al «Leer antes» de C-10; repetir `scripts/verificar_changes.py`.
- `knowledge-base/05_reglas_de_negocio.md`: RN-AU-07 «la restablecida y la cambiada, C-10» pasa a implementada; `RN-AU-09` y `RN-AU-10` pasan de «se implementa en C-10» a implementadas (la precisión de RN-AU-07 sobre la propia ya quedó con el `/opsx:update`, D293).
- `knowledge-base/06_funcionalidades.md` US-093: nota de que C-10 cubrió CA-6, CA-7 y el resto de CA-9 (US-093 completa).
- `knowledge-base/02_descripcion_general.md` y `03_actores_y_roles.md`: sin cambios de rutas (ya listan las dos); `08`: `features/contrasenas/` en la «Estructura de directorios» y las filas de `RN-AU-09` (`422`) y `RN-AU-10` (`409`) en el «Mapeo a HTTP».
- `knowledge-base/04_modelo_de_datos.md` o `08`: la nota de D197 («no hay restablecimiento») pasa a decir que la contraseña de un usuario sembrado se cambia por la API.
- `knowledge-base/10_preguntas_abiertas.md`: D290 a D303 ya quedaron registradas con el `/opsx:update`; al cerrar, las «Propuesta» que el autor apruebe y los hallazgos del Apply (V1 a V5).
- `openspec/config.yaml` (el rango D1..D303), `CLAUDE.md` y `AGENTS.md` (idénticos): el párrafo de estado de la KB con D290 a D303, `RN-AU-09` y `RN-AU-10`.
- `docs/skills-mcp/evidencias/sesion-nueva/stitch-contrasenas.md`: la comparación de la prueba en el navegador.

## Open Questions

**Cerrada** (sale de la pantalla de Stitch de la tarea 1.2, como Q12 de C-09; el autor la cerró el 2026-10-26 con la recomendación al aprobar el plan, «Q13 (a): sin resaltar la fila» → **D303**):

- **Q13. Marcar la fila mientras el panel restablece su contraseña.** La pantalla de Stitch marca la fila de la recepcionista (borde izquierdo y la insignia «Modificando») con el panel «Restablecer contraseña» abierto. (a) **No marcarla**: ningún escenario lo pide y el panel ya muestra el email del usuario; (b) marcarla como la edición de C-09 (fondo suave, borde izquierdo y la insignia «Editando», que se quita al cerrar, cancelar o guardar), con un escenario nuevo en `pantalla-de-contrasenas` y su test en 9.3. **Recomendación: (a)**: no suma comportamiento y evita un escenario más en un change que ya es excepción de tamaño (D300); (b) da más contexto visual con la tabla larga.

**Cerradas.** Las doce preguntas del propose quedaron cerradas por el autor el 2026-10-26 con la recomendación del agente, con Q4 resuelta con un código propio, junto con los hallazgos H1 a H11 de `revisor-de-escenarios` («Acepto Q1-Q12 con la recomendación (Q4 con código propio) y todos los hallazgos H1-H11 del revisor. La guía va en docs/guias/.»):

- **Q1 → D290.** Dos capabilities nuevas (`contrasenas-de-usuarios` y `pantalla-de-contrasenas`), sin deltas, como excepción a «una sola capability» limitada a C-10 (K1; hallazgo H4).
- **Q2 → D291.** El cambio propio responde `200` con access y refresh nuevos y sin caché: la sesión actual sigue y las demás caen (K4, K6, K12).
- **Q3 → D292.** Código nuevo `RN-AU-09` con `422` para la contraseña actual incorrecta, regla de negocio después de `RN-AU-07`, nunca `401`; registrado en `05` y en US-093 CA-7 de `06` (K7; hallazgo H1).
- **Q4 → D293.** Restablecer la propia se rechaza con un **código propio**, `RN-AU-10`, con `409` y el `detail` que indica la otra ruta (no con `RN-AU-07`); registrado en `05` (con la precisión de RN-AU-07: «cualquier otro usuario») y en US-093 CA-6 de `06` (K5, K9, K14; hallazgo H2).
- **Q5 → D294.** Un usuario inactivo se restablece y sigue inactivo (K5).
- **Q6 → D295.** La nueva igual a la actual se acepta y sube `token_version` (K6).
- **Q7 → D296.** La repetición de la nueva, solo en «Mi contraseña» y comparada en el navegador (K15, K16).
- **Q8 → D297.** «Restablecer contraseña» como acción de fila con el panel lateral en modo `restablecer`, y «Mi contraseña» en `/panel/contrasena` con enlace en la barra (K15, K16).
- **Q9 → D298.** Permiso nuevo `contrasena.propia` para los tres roles; un usuario sin roles recibe `403` `RN-AU-05` (K8).
- **Q10 → D299.** Bloqueo `FOR UPDATE` de la fila del usuario, probado en el perfil `postgres` con dos restablecimientos y con un restablecimiento y un cambio propio a la vez (K10; hallazgo H8).
- **Q11 → D300.** 29 tareas en 13 grupos para 38 escenarios, excepción limitada a C-10 (K21; hallazgo H4).
- **Q12 → D301.** Las pantallas de Stitch se consiguen antes de aprobar el plan (tarea 1.2; «Referencia visual (Stitch)»).
- **Hallazgos H5 a H7 → D302.** La guía va en `docs/guias/prueba-manual-c09-c10.md`; el agente ejecuta él mismo cada paso de C-09 y de C-10 y la guía crea al dueño y a la colega; si el código o la guía cambian después del ok del autor, se le vuelve a avisar (K19; tareas 12.2 y 13.1).

Los hallazgos H3 (escenario de la sesión irrenovable al restablecer), H8 (escenario del perfil `postgres` con un restablecimiento y un cambio propio a la vez), H9 (formato antes que largo también en el cambio propio), H10 (V2 vale para 4.2 y 5.2) y H11 (un test por comportamiento en 9.3 y 10.3) se aplicaron directamente a los specs, a las tareas y a este design, sin decisión D propia.
