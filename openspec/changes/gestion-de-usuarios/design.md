# Design: gestion-de-usuarios

Fecha del design: **2026-10-22**. Gobernanza **CRÍTICO** (`CHANGES.md` C-09): el autor aprueba este design **antes** del Apply; ninguna decisión «Propuesta» se implementa sin ese ok.

**Respuesta del autor (2026-10-22): las once preguntas abiertas se cierran con la recomendación del agente** («Aceptá Q1 a Q11 como se recomiendan»). Quedan como decisiones del autor D241 (U1, dos capabilities), D242 (U5, largo de la contraseña inicial en C-09, US-093 CA-9 parte inicial), D243 (U14, código nuevo `RN-AU-08`), D244 (U15, al menos un rol), D245 (U6, formato mínimo del email), D246 (U16, el profesional no cambia), D247 (U11, quitarse el propio rol `odontologo` con otro activo), D248 (U12, bloqueo de `consultorio`), D249 (U20, sin `GET /auth/yo`), D250 (U18, sin confirmación al desactivar) y D251 (U22, tamaño del Apply), registradas en `knowledge-base/10_preguntas_abiertas.md`; `RN-AU-08` quedó registrado en `knowledge-base/05_reglas_de_negocio.md`. Las demás decisiones marcadas «Propuesta» siguen así hasta que el autor apruebe el plan completo. En la misma revisión (`/opsx:update`) se incorporó el informe de `revisor-de-escenarios` (`docs/skills-mcp/evidencias/sesion-nueva/revision-de-escenarios-gestion-de-usuarios.md`, que queda como el «antes»): las correcciones H1 a H7, las sugerencias H8 a H12 y seis de los bordes sugeridos; los specs pasan de 45 a **54 escenarios** y las tareas siguen siendo 35. **Segunda revisión (2026-10-22):** con el informe `docs/skills-mcp/evidencias/sesion-nueva/revision-de-escenarios-gestion-de-usuarios-despues.md` el autor aprobó U8 puntos 6 y 7 como **D252** y **D253** y pidió corregir N1 a N5 con el tope de 254 caracteres del email en la API; los specs pasan a **56 escenarios** (34 de la API y 22 de la pantalla) y las tareas siguen siendo 35 en 14 grupos.

Las decisiones se numeran **U1 a U22** («U» de usuarios) para no confundirlas con las D1..D253 de `knowledge-base/10_preguntas_abiertas.md` ni con las de los designs anteriores (D de C-01, I de C-02, H de C-03, P de C-04, S de C-05, J de C-06, R de C-07, F de C-08, T de C-11, L de C-49). Cada una dice si es **Decisión del autor** (ya tomada en la KB), **Propuesta** (elección de este design, a confirmar) o **A verificar en el change** (comprobación técnica pendiente, con su «antes de qué»). Las que salieron de una pregunta abierta citan su D y su Q («Decisión del autor (D243; Q3)»).

## Context

Motivación y alcance: ver `proposal.md`. Requisitos: `specs/gestion-de-usuarios/spec.md` (API) y `specs/pantalla-de-usuarios/spec.md` (pantalla).

**Lo que ya existe** (leído del código y de los specs, no supuesto):

- **Esquema** (migraciones `0006` y `0007`): `usuario` (`id`, `consultorio_id`, `email` con `uq_usuario_email`, `hash_password`, `activo`, `token_version`, `creado_en`) y `usuario_rol` (PK `usuario_id` + `rol`, `CHECK` `ck_usuario_rol_rol_valido`, D213). `profesional.usuario_id` (FK nula, `UNIQUE`). **No hace falta ninguna migración.**
- **Dominio** (`backend/app/domain/acceso/`): `Rol`, `Permiso`, `MATRIZ`, `UsuarioDelPanel(id, roles)`, `puede`, `exigir_permiso` (`roles.py`); `DatosUsuario` y `normalizar_email` (`usuarios.py`, D199); `PermisoInsuficiente`, `SesionInvalida`, `CredencialesInvalidas` en `domain/errors.py`. `ReferenciaInvalida.recurso` acepta `prestacion`, `paciente`, `profesional`, `sillon` y `turno`: **no** `usuario`.
- **Aplicación**: `identificar_usuario` y `autorizar` (`application/acceso.py`); el puerto `RepositorioUsuarios` tiene `por_email`, `obtener`, `agregar` (levanta `EmailRepetidoEnLaBase`), `roles_de`, `asignar_rol` y `quitar_rol`; **no** tiene listar ni guardar. `HasherDeContrasenas` (bcrypt 5.0.0, 12 rondas) **levanta `ValueError` al hashear más de 72 bytes** (`infrastructure/seguridad/contrasenas.py`, `MAXIMO_DE_BYTES`): sin una validación previa, un alta con una contraseña larga sería un `500`.
- **API**: `requiere(permiso)` y `usuario_actual` (`api/seguridad.py`) dan el control de acceso en el orden de D208; `api/errores.py` traduce cada error de dominio por clase; `EntradaDeEdicion` rechaza el `null` explícito (D178). El guard `tests/api/test_proteccion_de_rutas.py` falla si una ruta nueva no exige token.
- **Configuración**: `MINIMO_DE_CARACTERES_DE_CONTRASENA = 10` y `MAXIMO_DE_BYTES_DE_CONTRASENA = 72` viven en `infrastructure/configuracion.py` (los usa la validación de `SEED_USUARIO_PASSWORD`, D197), no en el dominio.
- **Demo** (`seed_demo.py`): la odontóloga (id 1, `odontologo` + `dueno`, vinculada al profesional 1) y la recepcionista (id 2, `recepcionista`), con la contraseña de prueba del README.
- **Frontend** (C-08, C-11, C-49): `pedidoDelPanel` en el contexto de `ProveedorDeSesion` con `SesionTerminada` cableado (D231); `traducirRechazo` (`shared/api/rechazos.ts`) con `PermisoInsuficiente`, `ReglaRechazada`, `RecursoInexistente`, `EntradaRechazada` (con `codigos` y `errores`) y `SinConexion`; la pantalla de prestaciones como modelo (página, tabla, panel lateral, `Aviso`, `mensajes.ts`, íconos SVG en `shared/iconos/`, estilos en `panel.css` y `tokens.css`); `PanelBase` con la barra y un solo enlace «Prestaciones». El servidor falso conoce login, refresh y prestaciones, con un mapa fijo `ROLES` por email y la recepcionista **inactiva para el login** (US-090 CA-3 de C-08).

## Goals / Non-Goals

**Goals:**

- Que las reglas de US-093 (RN-AU-06, email único, largo de la contraseña inicial) sean **funciones puras de dominio** testeadas sin base, y que la API las aplique en el orden de RN-GL-02 y D208.
- Que desactivar a un usuario corte **todos** sus tokens en la petición siguiente sin tabla de tokens (RN-AU-03), y que reactivarlo no los reviva.
- Que ninguna carrera entre dos odontólogos deje al consultorio sin odontólogo activo (U12, D248), y que dos altas simultáneas con el mismo email no terminen en un `500` (U7).
- Que la pantalla muestre lo que decide la API, con cada rechazo y su código, reutilizando las piezas de C-11 sin duplicarlas.
- Sin dependencias nuevas, sin migración y sin tocar las rutas existentes.

**Non-Goals:**

- Contraseñas restablecidas o cambiadas (C-10) y su invalidación de sesiones.
- `Profesional` por usuario (Fase 2, D46): el único profesional sigue vinculado a la odontóloga del seed, aunque ella deje de ser odontóloga o se la desactive (D246).
- Saber en el navegador el rol o el id de quien inició sesión (D249).
- Registro de auditoría de los cambios de usuarios o de roles (no hay `EventoUsuario`; ninguna historia lo pide).
- Validación completa de formato de email (RFC 5322) o verificación por correo (U6).
- Optimistic UI, caché o sincronización entre pestañas (como C-11).

## Decisions

### U1. Dos capabilities nuevas: `gestion-de-usuarios` (API) y `pantalla-de-usuarios` (interfaz) — Decisión del autor (D241; Q1; sigue D218 y D229)

C-09 trae API y pantalla en el mismo change (`CHANGES.md`). El proyecto separó siempre el contrato de la API (`gestion-de-prestaciones`, `sesion-del-panel`, `proteccion-del-panel`) del comportamiento del navegador (`ingreso-al-panel`, `pantalla-de-prestaciones`), porque cada spec se verifica con su suite (pytest o Vitest). Se mantiene ese corte y la excepción a «una sola capability» (`openspec/config.yaml`, regla dura 12) queda registrada en D241, limitada a C-09. `proteccion-del-panel` **no** recibe delta: su matriz habla de «las rutas creadas antes de este change» y su guard ya exige token a toda ruta nueva; los permisos de `/usuarios` quedan en `gestion-de-usuarios` (U9).

### U2. Estructura de archivos del backend — Propuesta (aplica `08`, «Estructura de directorios», y la regla dura 3)

```
backend/app/
├── domain/acceso/
│   ├── usuarios.py        # + validar_contrasena_inicial, exigir_que_quede_un_odontologo, exigir_no_desactivarse (U5, U10, U11)
│   └── roles.py           # + Permiso.USUARIOS_LEER, Permiso.USUARIOS_EDITAR en MATRIZ (U9)
├── domain/errors.py       # + ContrasenaFueraDeRango (RN-AU-07), EmailRepetido (RN-AU-08), AdministracionSinOdontologo (RN-AU-06), UsuarioNoEncontrado (RN-GL-04, recurso "usuario")
├── application/
│   ├── usuarios.py        # listar_usuarios, crear_usuario, editar_usuario (U7, U8)
│   └── puertos.py         # RepositorioUsuarios + del_consultorio, guardar, reemplazar_roles, odontologos_activos, bloquear_administracion (U12)
├── infrastructure/repositories/usuarios.py  # implementación SQLAlchemy de lo anterior
├── api/esquemas.py        # CrearUsuarioEntrada, EditarUsuarioEntrada, UsuarioSalida (U4)
├── api/errores.py         # + las tres clases nuevas en _CLASES_DE_ERROR y _ERRORES_DE_TEXTO_FIJO (U13)
└── api/routers/usuarios.py  # GET/POST /usuarios, PATCH /usuarios/{usuario_id}
```

`MINIMO_DE_CARACTERES_DE_CONTRASENA` y `MAXIMO_DE_BYTES_DE_CONTRASENA` **se mudan al dominio** (`domain/acceso/usuarios.py`) y `configuracion.py` los importa de ahí, para que el seed y el alta usen la misma regla (RN-AU-07); los tests de `test_configuracion.py` no cambian.

### U3. Rutas y orden de los casos de uso — Propuesta

Endpoints síncronos (`def`, D12), con `requiere(...)` como dependencia (D208). `editar_usuario` recibe además al **usuario del token** (`UsuarioDelPanel`), porque la regla de no desactivarse depende de quién pide (U11): la ruta usa `Depends(requiere(Permiso.USUARIOS_EDITAR))` como parámetro, no solo en `dependencies`.

### U4. Contrato de la API — Propuesta

| Ruta | Cuerpo | Éxito | Rechazos (en orden de evaluación, U13) |
|---|---|---|---|
| `GET /usuarios` | — | `200`, lista por `id` | `401`, `403` |
| `POST /usuarios` | `email` (texto, 1 a 254), `contrasena` (texto), `roles` (lista de `Rol`, 1 a 3, sin repetir); `extra="forbid"` | `201`, el usuario | `401`, `403`, `422` de formato, `422` `RN-AU-07`, `409` `RN-AU-08` |
| `PATCH /usuarios/{usuario_id}` | `roles` (como arriba) y/o `activo` (bool), los dos opcionales; `extra="forbid"`; `null` explícito de formato (`EntradaDeEdicion`) | `200`, el usuario | `401`, `403`, `422` de formato, `404` `RN-GL-04`, `409` `RN-AU-06` |

`UsuarioSalida`: `id`, `email`, `roles` (ordenados como el enum: `odontologo`, `recepcionista`, `dueno`, para que la respuesta no dependa del orden de la base), `activo`. **Nunca** `hash_password`, `token_version`, `consultorio_id` ni `creado_en` (este último no lo pide ninguna historia; se puede sumar sin romper). Un `PATCH` con `{}` responde `200` con el usuario sin cambios (ni `token_version`), como los catálogos (escenario propio, H6). El `email` y la `contrasena` no se editan por `PATCH` (`extra="forbid"`: `422` de formato); la contraseña es C-10.

### U5. Largo de la contraseña inicial en C-09 — Decisión del autor (D242; Q2; aplica RN-AU-07 y D74) + Propuesta (forma)

Los escenarios y los tests de esta regla llevan la etiqueta **US-093 CA-9** (la parte de la contraseña inicial), no CA-1: C-09 suma CA-9 (parte inicial) a su cobertura y C-10 se queda con la restablecida y la cambiada. La entrada de C-10 en `CHANGES.md` se ajusta al archivar (D242).

`validar_contrasena_inicial(texto)` (dominio puro): al menos **10 caracteres** (`len`) y como máximo **72 bytes** en UTF-8. Fuera de rango → `EntradaInvalida((ContrasenaFueraDeRango(),))`, `422` con `codigos` `["RN-AU-07"]` y `errores` `[{"campo": "contrasena", "codigo": "RN-AU-07", "mensaje": "La contraseña debe tener de 10 caracteres a 72 bytes."}]`. Es **validación de entrada del dominio**, como RN-AG-01 en C-04 (D176, D177): corre después de la validación de formato de Pydantic, así que un cuerpo con errores de formato devuelve solo esos (límite heredado de C-04, D177). Ese límite «formato antes que largo» tiene escenario propio en el spec de la API (N5): el email `sin-arroba` con la contraseña `corta-123` da `422` con `codigos` vacío y solo el error del campo `email` (tarea 4.3). La contraseña **no se recorta ni se normaliza** (los espacios cuentan). El mensaje del `422` nunca repite la contraseña.

### U6. Email del alta — Decisión del autor (D245; Q5; incluye el tope de 254 caracteres)

Se guarda normalizado con `normalizar_email` (D199). Formato mínimo (D245), en Pydantic y **sin dependencia nueva**: después de recortar, una sola `@` con texto a los dos lados y sin espacios; si no, `422` de formato con `codigos` vacío. **Se descarta `EmailStr`**: necesita el paquete `email-validator` (dependencia nueva) y además rechaza los dominios de uso especial como `.test`, que son los de la demo (`consultorio-demo.test`). **A verificar en el change (antes de la tarea 4.1):** que el `pattern` elegido acepta los emails de la demo y rechaza `sin-arroba`, `a@`, `@b` y `a b@c.test`. El tope de **254 caracteres** (U4) **queda decidido** (2026-10-22, corrección de N1) como parte del chequeo mínimo de D245, sin una D nueva: la API lo impone en el esquema de entrada, con escenario y test propios (254 se acepta con `201`, 255 da `422` de formato en el campo `email`; tarea 4.3), y el servidor falso lo copia (tarea 8.1). Es lo único del formato que la pantalla puede provocar con un campo `type="email"` (el navegador ya bloquea los otros casos) y lo usa el escenario de pantalla del email inválido (U19).

### U7. Alta — Propuesta

`crear_usuario(comando, uow, hasher, reloj)`: (1) `validar_contrasena_inicial`; (2) si `por_email(normalizado)` existe → `EmailRepetido` (`409` `RN-AU-08`, D243); (3) `hasher.hashear` (bcrypt, fuera de la transacción si se puede: **A verificar en el change, antes de la tarea 4.2**, que hashear dentro del `with uow` no retiene la conexión de SQLite más de lo aceptable; si no, se hashea antes de abrirla); (4) `agregar` con `activo` verdadero, `token_version` 0 y `creado_en = reloj()` (`utc_now` inyectable, regla dura 2); (5) `reemplazar_roles`. `EmailRepetidoEnLaBase` (carrera de dos altas iguales) se traduce a `EmailRepetido`: la perdedora recibe `409` `RN-AU-08` y no `500`. Esa carrera no se puede producir en la suite por defecto (SQLite, un hilo): se prueba en el perfil `postgres` con el arnés de `tests/postgres/carrera.py` (la ganadora inserta con `flush()` sin confirmar, el `INSERT` de la perdedora espera la restricción `uq_usuario_email` y falla al confirmar la ganadora; escenario «dos altas simultáneas con el mismo email», H6). **No toca `profesional`** (D46, US-093 CA-8).

### U8. Edición: roles y activo — Propuesta (puntos 1 a 5) + Decisión del autor (puntos 6 y 7: D252, D253) (aplica RN-AU-02, RN-AU-03, D43, D102)

`editar_usuario(usuario_id, comando, actor, uow)`, dentro de una transacción:

1. `obtener(usuario_id)`; si no existe → `UsuarioNoEncontrado` (`404` `RN-GL-04`, recurso `usuario`; D166). Se amplía `ReferenciaInvalida.recurso` y `RecursoDeLaUrlNoEncontrado` con `"usuario"`.
2. `bloquear_administracion(consultorio_id)` (U12) si el pedido puede bajar la cantidad de odontólogos activos (quita `odontologo` o desactiva).
3. Reglas RN-AU-06 en el orden de U13.
4. **Roles** (`roles` presente): **reemplazan** el conjunto (Propuesta: más simple de probar y de mandar desde las casillas que agregar y quitar de a uno; el `PATCH` es idempotente). No cambia `token_version` (D102).
5. **Activo**: `true → false` incrementa `token_version` en 1 (RN-AU-03); `false → true` no la cambia (los tokens viejos siguen sin servir porque su versión ya quedó atrás); pedir el mismo valor no cambia nada (ni `token_version`).
6. **Roles y `activo` en el mismo `PATCH`** (Decisión del autor, D252): las reglas de RN-AU-06 se evalúan sobre el resultado combinado del pedido (roles nuevos y `activo` nuevo), y si una rechaza **no se aplica ninguna de las dos partes** (todo dentro de la misma transacción). Ejemplo: la única odontóloga pide `{"roles": ["dueno"], "activo": false}` sobre sí misma → `409` `RN-AU-06` (gana «no desactivarse», U13) y no cambia ni el rol ni `activo`; el `detail` es «Nadie puede desactivarse a sí mismo.» (N4). Caso de éxito (N2): con la odontóloga y la colega como odontólogos activos, el `PATCH` de la colega con `{"roles": ["dueno"], "activo": false}` responde `200` y aplica las dos partes (roles `["dueno"]`, `activo` falso, `token_version` 1).
7. **Roles de un usuario inactivo** (Decisión del autor, D253; la KB no lo decía): **se pueden editar**. Roles y `activo` son independientes (RN-AU-02, RN-AU-04): el usuario sigue inactivo, su `token_version` no cambia y, si se lo reactiva, entra con los roles nuevos. Como un odontólogo inactivo no cuenta para RN-AU-06 (U10), cambiarle los roles nunca baja la cantidad de odontólogos activos: no toma el bloqueo ni puede dar `409`. Es lo más simple y coherente con el contrato de U4 (los dos campos son opcionales e independientes); no abre una pregunta nueva.

### U9. Permisos — Decisión del autor (matriz de `03`, fila «Usuarios del consultorio»; RN-AU-05) + Propuesta (nombres)

`Permiso.USUARIOS_LEER` → `odontologo`, `dueno`; `Permiso.USUARIOS_EDITAR` → `odontologo`. La recepcionista no lee (`—` en la matriz). Va contra lo que dice `02` («Odontólogo (el dueño solo lee)»), que coincide: no hay contradicción. El test de la matriz (`tests/unit/test_roles.py`) suma las dos filas.

### U10. «No quedarse sin odontólogo activo» — Decisión del autor (RN-AU-06, D44) + Propuesta (forma)

Función pura `exigir_que_quede_un_odontologo(odontologos_activos_despues: int)`: si el pedido dejaría **cero** usuarios activos con `odontologo` → `AdministracionSinOdontologo` (`409` `RN-AU-06`). El caso de uso calcula el «después» con el estado leído bajo el bloqueo (U12): los odontólogos activos de la base, menos el usuario editado si deja de serlo (pierde el rol o se desactiva). Un usuario inactivo con `odontologo` no cuenta. Como quien edita tiene que ser odontólogo activo para tener el permiso, el caso «desactivar al último» solo se alcanza sobre uno mismo (y gana U11) o en una carrera (U12); «quitar el rol al último» sí se alcanza sobre uno mismo. Por eso el spec prueba la regla con quitarse el rol y con la carrera, y el Requirement de la API anota que la mitad «desactivar al último» se verifica en el dominio (tarea 2.1) y en el perfil `postgres` (tarea 6.4), no en `tests/api` (H9).

### U11. «Nadie se desactiva a sí mismo» — Decisión del autor (RN-AU-06, D44; D247; Q7) + Propuesta (forma)

Función pura `exigir_no_desactivarse(actor_id, usuario_id, activo_pedido)`: si `activo_pedido is False` y `actor_id == usuario_id` → `AdministracionSinOdontologo` con el detalle «Nadie puede desactivarse a sí mismo.» (mismo código `RN-AU-06`, otra frase; los dos `detail` son fijos, U13). Vale aunque haya otros odontólogos. **Quitarse el propio rol `odontologo`** con otro odontólogo activo **está permitido** (RN-AU-06 solo prohíbe desactivarse): D247.

### U12. Concurrencia de RN-AU-06 — Decisión del autor (D248; Q8; aplica DD-04 y el patrón de `bloquear_recursos`)

Dos odontólogos que se desactivan uno al otro al mismo tiempo leerían cada uno «queda otro» y dejarían cero. Se **serializan** las ediciones que pueden bajar la cantidad de odontólogos activos con `SELECT … FROM consultorio WHERE id = :id FOR UPDATE` (`bloquear_administracion`), tomado **antes** de contar, dentro de la misma transacción; el segundo espera, y al continuar lee lo que el primero confirmó. En SQLite el bloqueo es un no-op (la suite por defecto es de un solo hilo), como `bloquear_recursos`. Se prueba en el perfil `postgres` con el arnés de `tests/postgres/carrera.py` (escenario «dos odontólogos no se desactivan a la vez»), al nivel del caso de uso: las dos peticiones ya pasaron el control de acceso (sus actores son odontólogos activos); la ganadora toma el bloqueo, desactiva y **no confirma**; la perdedora corre en otro hilo y espera en el bloqueo; al confirmar la ganadora, la perdedora lee el estado nuevo y recibe **`409` `RN-AU-06`**. Ese es el **único resultado esperado** de la perdedora (H8): el `401` que recibiría una petición que llega después de la desactivación es el escenario de US-093 CA-3, no el de la carrera. **A verificar en el change (antes de la tarea 6.4):** que `with_for_update()` sobre `ConsultorioModelo` emite `FOR UPDATE` en PostgreSQL y nada en SQLite, y que el arnés de carrera admite dos usuarios distintos. Sin migración: la fila de `consultorio` ya existe.

### U13. Clases de rechazo y orden de evaluación — Propuesta (aplica RN-GL-02, D135 y D208)

| # | Clase | `POST /usuarios` | `PATCH /usuarios/{id}` |
|---|---|---|---|
| 0 | Límite de FastAPI | JSON roto: `422` sin código (D208) | igual |
| 1 | Control de acceso | `401` `RN-AU-03`; `403` `RN-AU-05` | igual |
| 2 | Validación de formato (Pydantic) | `422` con `codigos` vacío y un error por campo: email, roles (vacía, inválida, repetida, más de 3), tipos, campo de más | `422` con `codigos` vacío: roles, `activo` no booleano, `null` explícito, campo de más (`email`, `contrasena`) |
| 3 | Validación de entrada del dominio | `422` `RN-AU-07` (U5) | — |
| 4 | Recurso de la URL | — | `404` `RN-GL-04` |
| 5 | Reglas de negocio, de a una | `409` `RN-AU-08` | `409` `RN-AU-06`: primero desactivarse a sí mismo (U11), después último odontólogo (U10) |

El orden de las filas 1, 2 y 4 tiene escenario propio en el spec de la API: `401` antes que `422` (alta sin token con `roles` vacío), `403` antes que `404` (el dueño sobre `/usuarios/999`) y `422` antes que `404` (`PATCH /usuarios/999` con `roles` vacío).

Clases nuevas en `api/errores.py`: `ContrasenaFueraDeRango` viaja dentro de `EntradaInvalida` (como `DuracionInvalida`, con su error de campo); `EmailRepetido` → `409`, `/errores/email-repetido`, «Email repetido», `detail` fijo «Ya existe un usuario con ese email.» (sin repetir el email); `AdministracionSinOdontologo` → `409`, `/errores/administracion-sin-odontologo`, «Operación no permitida», `detail` fijo según la causa (U10, U11); `UsuarioNoEncontrado` hereda de `RecursoDeLaUrlNoEncontrado`.

### U14. Código nuevo `RN-AU-08` para el email repetido — Decisión del autor (D243; Q3; aplica la regla dura 4)

US-093 CA-2 («el email es único») no tenía código RN y la regla dura 4 prohíbe un rechazo de negocio sin código. Se usa **`RN-AU-08`** (fija; «el email de un usuario es único en la instalación, comparado sin espacios en los extremos ni mayúsculas, D199; un alta repetida se rechaza con `409`»), el camino de `RN-AG-15` (D171). Ya está registrado en `knowledge-base/05_reglas_de_negocio.md` (y citado en US-093 CA-2 de `06` y en la fila «Usuarios del consultorio» de `03`) con la respuesta del autor; al archivar solo se marca como implementado.

### U15. Roles al crear y editar: al menos uno — Decisión del autor (D244; Q4)

`roles` es obligatorio en el alta y, si llega en el `PATCH`, tiene que tener **al menos un rol**: `422` de formato. Así la pantalla nunca crea un usuario que no puede hacer nada. Un usuario sin roles sigue siendo posible en la base (`proteccion-del-panel` lo prueba con un usuario creado por el test) pero no por la API.

### U16. El profesional vinculado — Decisión del autor (D246; Q6; aplica D46)

Quitar `odontologo` o desactivar a la odontóloga del seed (cuando hay otro odontólogo activo) **no toca** `profesional`: sigue activo y vinculado a ella, la agenda sigue funcionando y los turnos se siguen creando con ese profesional. Límite conocido del README hasta el change multi-profesional (Fase 2).

### U17. Estructura del frontend — Propuesta (aplica T3 de C-11)

```
frontend/src/
├── features/usuarios/
│   ├── apiUsuarios.ts             # listarUsuarios, crearUsuario, editarUsuario, rolesCambiados (U18)
│   ├── apiUsuarios.test.ts
│   ├── PaginaUsuarios.tsx         # estado de la pantalla (como T7)
│   ├── PaginaUsuarios.test.tsx
│   ├── TablaDeUsuarios.tsx        # filas, insignias de rol y estado, Editar / Desactivar / Reactivar
│   ├── PanelDeUsuario.tsx         # alta (email, contraseña inicial, roles) y edición (roles)
│   └── mensajes.ts                # textos fijos (U19)
├── shared/iconos/IconoUsuarios.tsx  # ícono del enlace de la barra (SVG en línea)
├── pages/PanelBase.tsx            # + enlace «Usuarios»
├── App.tsx                        # + ruta hija usuarios
└── test/servidorFalso.ts          # + contrato de gestion-de-usuarios (U21)
```

`Aviso.tsx` de `features/prestaciones/` se reutiliza; si hace falta en las dos pantallas se mueve a `shared/` (REFACTOR del grupo 10, sin cambiar su comportamiento ni los tests de C-11). Sin archivos *barrel*; componentes en PascalCase.

### U18. Cliente y pantalla — Propuesta (aplica `vercel-react-best-practices` y T5 a T9 de C-11)

- `apiUsuarios.ts` recibe `pedidoDelPanel` inyectado; valida las respuestas `2xx` sin `any`; todo `4xx` pasa por `traducirRechazo` (sin traducción nueva). `rolesCambiados(original, marcados)` es pura y compara conjuntos (el orden no cuenta).
- `PaginaUsuarios`: listado `cargando | lista | sin-conexion | sin-permiso` (este último cuando el `GET` da `403`: la recepcionista); panel `cerrado | alta | edicion`. Una sola petición al montar, contador derivado en el render.
- **Panel de alta**: «Email» (`type="email"`, `required`, `autocomplete="off"`), «Contraseña inicial» (`type="password"`, `required`, `autocomplete="new-password"`, sin `minlength` ni `maxlength`: la regla la decide la API, como D232) con la ayuda «De 10 caracteres a 72 bytes.», y las casillas «Odontólogo», «Recepcionista», «Dueño» dentro de un `fieldset` con `legend` «Roles». La contraseña vive solo en el estado del formulario y se descarta al cerrar el panel; nunca se registra en la consola ni en la URL.
- **Panel de edición**: el email como texto, las casillas con los roles actuales, «Guardar» manda solo `roles` si cambiaron; la fila se marca «Editando» (como T17).
- **Acciones de fila**: «Desactivar» o «Reactivar», sin confirmación (D250), deshabilitadas mientras esperan (un solo pedido aunque se pulse dos veces; escenario propio, H4); con `404` se recarga la lista.
- **Después de un alta con `201`**: el panel se cierra y el formulario queda vacío (email, contraseña y casillas); al reabrir «Nuevo usuario» no queda nada de lo anterior (escenario de alta).

### U19. Mensajes fijos de la pantalla — Propuesta (como T11 de C-11: no se muestra el `detail` de la API)

| Situación | Mensaje | Dónde |
|---|---|---|
| `409` `RN-AU-08` | «Ya existe un usuario con ese email (RN-AU-08).» | Debajo del email |
| `422` `RN-AU-07` en `contrasena` | «La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).» | Debajo de la contraseña |
| `422` con error del campo `roles` | «Elegí al menos un rol.» | Debajo de los roles |
| `422` con error del campo `email` | «Ingresá un email válido.» | Debajo del email |
| `422` de otro campo | «Revisá los datos del usuario.» | Aviso del panel |
| `409` `RN-AU-06` | «El consultorio no puede quedar sin un odontólogo activo y nadie puede desactivarse a sí mismo (RN-AU-06).» | Aviso del panel o de la tabla |
| `403` `RN-AU-05` al leer | «Tu usuario no tiene permiso para ver los usuarios (RN-AU-05).» | En lugar de la tabla |
| `403` `RN-AU-05` al escribir | «Tu usuario no tiene permiso para modificar usuarios (RN-AU-05).» | Aviso del panel (con lo escrito) o de la tabla |
| `404` `RN-GL-04` | «El usuario ya no existe (RN-GL-04).» | Aviso de la tabla (recarga la lista) |
| Sin conexión | «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» | Como en C-11 |
| Cargando | «Cargando usuarios…» | En lugar de la tabla |
| Roles | «Odontólogo», «Recepcionista», «Dueño» | Insignias y casillas |

El mensaje de `RN-AU-06` junta las dos causas porque la pantalla decide por el código y las dos comparten `RN-AU-06`; distinguirlas exigiría leer el `detail` (descartado por F9 de C-08). Los escenarios de la pantalla citan los textos literales (H11).

Cómo se prueba cada texto (H5): «Ingresá un email válido.» tiene escenario de pantalla con un email de 255 caracteres (el navegador lo acepta como `type="email"` y la API lo rechaza por el tope de U4, `422` de formato en el campo `email`); «Revisá los datos del usuario.» es la red para un `422` de un campo sin mensaje propio, que la pantalla no puede provocar (sus únicos campos son email, contraseña y roles): se prueba como **función pura** de `mensajes.ts` con un rechazo `EntradaRechazada` armado en el test (sin servidor y sin mocks), sin escenario de spec.

### U20. Rol y usuario actual en la interfaz — Decisión del autor (D249; Q9; sigue D225 y D230)

El enlace «Usuarios» y todas las acciones se muestran a todos los roles. La recepcionista ve el mensaje de `403` en lugar de la tabla; el dueño ve la tabla y recibe `403` al escribir; la odontóloga ve «Desactivar» en su propia fila y recibe `409` `RN-AU-06`. **Sin `GET /auth/yo`**. Va como límite conocido del README.

### U21. Tests y servidor falso — Decisión del autor (D222, D227, reglas duras 5 y 6) + Propuesta (detalle)

- **Backend**: dominio puro en `tests/unit/test_usuarios.py` (largo de la contraseña con bordes 9/10 caracteres y 72/73 bytes con caracteres de dos bytes, RN-AU-06 en sus dos formas, matriz); repositorio en `tests/integration/test_repositorio_usuarios.py` (listar, guardar, reemplazar roles, contar odontólogos activos); casos de uso en `tests/integration/test_usuarios.py`; API en `tests/api/test_usuarios.py` con access tokens reales (D211, sin `dependency_overrides`); la carrera en `tests/postgres/test_administracion_concurrente.py`. Sin mocks de sesión ni de repositorio; SQLite en memoria con `StaticPool`. Los tests de la API crean la app con `ConfiguracionDeSesion` de pocas rondas de bcrypt (`rondas_bcrypt`, como ya hace `un_usuario` de `tests/factories.py` con 4 rondas, J17), para que las altas no hagan lenta la suite.
- **Frontend**: el servidor falso pasa a tener un **catálogo de usuarios** (`USUARIOS_DE_PARTIDA`: odontóloga, recepcionista y `administracion@consultorio-demo.test` inactivo con `dueno`) del que salen los roles de cada sesión (reemplaza el mapa fijo `ROLES`), implementa `GET`/`POST`/`PATCH /api/usuarios[/{id}]` con el contrato de U4 y U13 (incluido el orden `403` → `422` → `404` → `409`), invalida los tokens de un usuario desactivado, rechaza con `422` de formato un email de más de 254 caracteres (U4, para el escenario de U19) y ofrece `quitarUsuario(id)` (para el `404`), la respuesta retenida de un `PATCH` (para el escenario de los botones deshabilitados mientras espera, como la respuesta retenida del listado de C-11) y `emitirSesion` para el dueño. El escenario de `quitarUsuario` se verifica **solo contra el servidor falso**: la API real no borra usuarios y no puede producir ese estado (H10). **La recepcionista sigue inactiva para el login del falso** (C-08): el catálogo la muestra activa porque es lo que devuelve la API real; el alias que lo explica queda documentado (como `EMAIL_RECEPCIONISTA` en C-11). **A verificar en el change (antes de la tarea 8.1):** que los 18 tests de C-08 y los de C-11 siguen en verde con los roles salidos del catálogo.
- Nombres de test con el escenario (`US-093 CA-4: …`). Sin `vi.mock`, `vi.fn`, `vi.stubGlobal` ni temporizadores falsos (guard de C-08).

### U22. Demo, README, prueba en el navegador y tamaño — Decisión del autor (D251; Q11) + Propuesta (detalle)

- **Demo**: sin datos nuevos; el recorrido crea sus propios usuarios (uno para el alta y uno solo `dueno` para los `403` de escritura, H12). README: sección «Usuarios» (API, en «Probar desde Swagger») y «Pantalla de usuarios» (en «Panel (interfaz)»), con la tabla escenario → test y los límites conocidos (U16, U20, U5 «formato antes que largo», sin auditoría).
- **Prueba en el navegador**: el agente recorre los escenarios con la demo y en Compose, y compara con la captura de Stitch (D234); quedan fuera los que solo el servidor falso puede producir (el usuario que deja de existir, H10). Por ser **CRÍTICO**, la repetición manual del autor **va como tarea** (regla `rules.tasks` de `config.yaml`).
- **Tamaño**: **35 tareas en 14 grupos** para **56 escenarios** (34 de la API y 22 de la pantalla), frente a «alrededor de 20» de `CHANGES.md`: excepción aceptada por el autor y limitada a C-09 (D251). Los escenarios que sumaron las dos revisiones entran en las tareas existentes, sin tareas nuevas.

### Skills aplicadas

- `auth-implementation-patterns`: hash adaptativo y nunca la contraseña en claro ni en logs; invalidación en bloque por `token_version` al desactivar; el servidor decide los permisos (la interfaz reacciona al `403`); mensajes de rechazo fijos que no repiten datos sensibles. **No aplicadas** por la KB (regla dura 9): límite de peticiones (D195) y política de complejidad de contraseñas más allá del largo (D74).
- `fastapi-templates`: routers por recurso, esquemas de entrada y salida separados, dependencias inyectadas. **No aplica** su parte asíncrona (`async def`, sesiones asíncronas): el proyecto es síncrono (DD-12, regla dura 5).
- `python-error-handling`: jerarquía de errores de dominio con código; validación de entrada junta y reglas de a una (RN-GL-02); la carrera de la base se traduce al mismo error de dominio (`EmailRepetidoEnLaBase` → `EmailRepetido`).
- `python-testing-patterns`: TDD estricto, tests por escenario con nombres que lo citan, bordes de los límites (9/10, 72/73), sin mocks (regla dura 6).
- `vercel-react-best-practices` (SPA de Vite; no aplican Next.js ni RSC): una sola petición al montar, estado derivado en el render, `setState` funcional, sin componentes definidos dentro de otros, ternario en vez de `&&`, JSX estático fuera de los componentes, sin *barrels*.

## Referencia visual (Stitch)

**Regla (D234, Decisión del autor):** toda pantalla del frontend se implementa a partir de una pantalla generada en Stitch con el design system del proyecto; el design cita el id de la pantalla y su evidencia; si Stitch no entrega la pantalla, el change de interfaz no se cierra; la KB y el spec mandan sobre el contenido.

**Estado en el propose (2026-10-22): la pantalla NO quedó disponible.** Evidencia de los intentos en `docs/skills-mcp/evidencias/sesion-nueva/stitch-usuarios.md`:

- Proyecto `projects/14200813501064679723` y design system «Clinical Ops» (`assets/b683d44391ab410db2dd48aa71ed0b47`), los de C-11 y C-49.
- Dos llamadas a `generate_screen_from_text` con `GEMINI_3_8_FLASH` superaron el tiempo de espera del cliente; una tercera con `GEMINI_3_5_FLASH_LITE` respondió con un texto («Ya tenemos disponible la pantalla de «Usuarios»… Puedes visualizarla en el canvas») pero **sin el id de la pantalla**.
- `list_screens` devuelve una lista vacía para el proyecto (también para las pantallas de C-11 y C-49, que `get_screen` sí encuentra por id) y `get_project` no trae `screenInstances`: **no hay forma de obtener el id desde el MCP**.

**Qué falta, antes del grupo 9 de `tasks.md` (tarea 1.2, bloqueante):** obtener el id de la pantalla «Usuarios» (desde el canvas de Stitch en el navegador, donde la generación dice estar, o regenerándola), descargar con `get_screen` y `download_file` la captura (`stitch-usuarios-pantalla/pantalla.png`) y el HTML (`stitch-usuarios-pantalla/pantalla.html`), completar la evidencia y sumar a este design, con `/opsx:update`, el id y la lista de **qué se toma y qué se rechaza** de la pantalla. Sin eso el change no se archiva (D234).

**Lo que la pantalla tiene que traer** (texto enviado, solo datos ficticios, sin pacientes ni secretos; ver la evidencia): la barra del panel con «Prestaciones» y «Usuarios», el encabezado con «Nuevo usuario», la tarjeta «Listado general» con el contador, la tabla email / roles / estado / acciones con una fila «Editando» y una inactiva, el aviso de `RN-AU-06`, el panel lateral de edición con las casillas de roles y una tarjeta de referencia del alta con «Contraseña inicial» y el error de `RN-AU-08`.

**Ya decidido sin la pantalla, por la KB y el spec** (se mantiene aunque Stitch muestre otra cosa): sin datos de quien inició sesión (D225); sin avatares, nombres ni datos personales (el modelo no los tiene); acciones visibles para todos (U20); los textos de U19; la contraseña nunca visible fuera de su campo; ningún estado combinado imposible (por ejemplo `RN-AU-05` junto a `RN-AU-07`, D208). El HTML de Stitch **no se copia**: se traduce a `frontend/src/shared/estilos/tokens.css` y `panel.css` y a marcado de React, **sin dependencias nuevas** (ni Tailwind ni fuentes o íconos por CDN; la CSP de nginx es `default-src 'self'`), con íconos en SVG en línea.

## Contradicciones y huecos encontrados en las fuentes

1. **El largo de la contraseña inicial**: RN-AU-07 y US-093 CA-9 lo exigen «tanto la inicial como la restablecida», pero `CHANGES.md` pone CA-9 en C-10 («también para la contraseña inicial de C-09»); y bcrypt 5 levanta `ValueError` con más de 72 bytes, así que sin la regla el alta de C-09 respondería `500`. → U5 y D242 (resuelto: C-09 valida la inicial con la etiqueta US-093 CA-9; C-10 se ajusta al archivar).
2. **US-093 CA-2 sin código RN** contra la regla dura 4. → U14 y D243 (resuelto: `RN-AU-08` en `05`).
3. **«Un change, una capability»** contra un change con API y pantalla, y el corte de D218 y D229. → U1 y D241 (resuelto: excepción registrada para C-09).
4. **«Desactivar al último odontólogo activo»** solo se alcanza sobre uno mismo (donde ya rige «no desactivarse») o en una carrera. → U10, U12 y el escenario del perfil `postgres`.
5. **`ReferenciaInvalida.recurso`** no admite `usuario`. → U8: se amplía el `Literal`.
6. **El servidor falso** tiene a la recepcionista inactiva para el login y activa como rol (C-08, C-11), y el catálogo de usuarios la mostrará activa. → U21: se documenta, sin cambiar los tests de C-08.
7. **`02` dice «el dueño solo lee»** y `03` dice `R` para el dueño y `—` para la recepcionista: coinciden. Ninguna fuente dice si la recepcionista lee; se sigue `03` (D205: `03` es la matriz).
8. **Stitch no entregó el id de la pantalla** en el propose. → «Referencia visual (Stitch)» y tarea 1.2.

## Risks / Trade-offs

- [La odontóloga se quita su propio rol `odontologo` (con otro odontólogo activo) y pierde la gestión de usuarios en la petición siguiente] → Es lo que permite RN-AU-06 (D247); el otro odontólogo puede devolvérselo. La pantalla lo muestra con los `403` siguientes.
- [Desactivar sin confirmación corta la sesión de alguien que está trabajando] → Es reversible con «Reactivar» (con un inicio de sesión nuevo); D250.
- [El bloqueo de `consultorio` serializa todas las ediciones de usuarios que bajan odontólogos] → Son operaciones raras y cortas; el bloqueo se toma solo cuando el pedido puede bajar la cantidad (U8).
- [bcrypt con 12 rondas hace lentos los tests de alta] → Los tests usan `rondas_bcrypt` bajas (U21); la demo y Compose siguen con 12.
- [El profesional queda vinculado a una usuaria desactivada] → Límite conocido (U16, D46).
- [Stitch no entregó la pantalla] → Tarea 1.2 bloqueante antes del frontend; el backend (grupos 2 a 7) no depende de ella.
- [El servidor falso se aparta de la API] → Cuerpos copiados del spec y de `api/errores.py`; la prueba en el navegador repite los escenarios contra la API real.

## A verificar en el change

- **V1** (antes de la tarea 4.1): el `pattern` del email de U6.
- **V2** (antes de la tarea 4.2): hashear dentro o fuera de la transacción (U7).
- **V3** (antes de la tarea 6.4): `with_for_update()` sobre `consultorio` en PostgreSQL y SQLite, y el arnés de carrera con dos usuarios (U12).
- **V4** (antes de la tarea 8.1): los tests de C-08 y C-11 en verde con los roles salidos del catálogo del falso (U21).
- **V5** (antes de la tarea 13.1, en Compose): consola sin violaciones de la CSP con la pantalla nueva y sus íconos.

## Migration Plan

1. Q1 a Q11 ya están respondidas (D241 a D251, 2026-10-22), U8 puntos 6 y 7 aprobados (D252, D253) y los artefactos ajustados con `/opsx:update` (dos revisiones); falta el ok del autor al plan completo (CRÍTICO) antes del Apply. Con ese ok, se commitean los artefactos y, en un commit `docs(kb)` aparte, D241 a D253 y `RN-AU-08` ya registrados en la KB.
2. El Apply no lleva migración ni variables nuevas: `docker compose up --build -d` reconstruye `api` y `frontend`.
3. **Vuelta atrás**: revertir los commits del change. Los usuarios creados en una base PostgreSQL quedan (no hay borrado); si hace falta, se desactivan por la API antes de revertir.

## Notas para el archive

No se editan ahora ni durante el Apply:

- `CHANGES.md`: marcar C-09 con `[x]`; por D231, quitar de su entrada el cableado de `pedidoDelPanel` y `SesionTerminada` (pendiente desde C-11); por D242, sumar a los «Escenarios mínimos» de C-09 «CA-9 (parte inicial)» y quitar de la entrada de C-10 «también para la contraseña inicial de C-09» (C-10 queda con la restablecida y la cambiada); por D243, sumar `RN-AU-08` al «Leer antes» de C-09 y C-10; repetir `scripts/verificar_changes.py`.
- `knowledge-base/05_reglas_de_negocio.md`: `RN-AU-08` ya está registrado (D243, 2026-10-22); al archivar, «a implementar en C-09» pasa a «implementada en C-09».
- `knowledge-base/06_funcionalidades.md` US-093: nota de qué criterios cubrió C-09 (CA-1 a CA-5, CA-8 y la parte inicial de CA-9); CA-2 ya cita `RN-AU-08`.
- `knowledge-base/08_arquitectura_propuesta.md`, «Estructura de directorios»: `features/usuarios/`.
- `knowledge-base/10_preguntas_abiertas.md`: D241 a D253 ya están registradas (2026-10-22; D252 y D253 son U8 puntos 6 y 7); al cerrar se registran las demás decisiones «Propuesta» que el autor apruebe con el plan y los hallazgos del Apply (V1 a V5).
- `openspec/config.yaml` y `CLAUDE.md`/`AGENTS.md`: el párrafo de estado de la KB con las decisiones nuevas.
- `docs/skills-mcp/evidencias/sesion-nueva/stitch-usuarios.md`: la comparación de la prueba en el navegador.

## Open Questions

Ninguna. Las once preguntas del propose quedaron cerradas por el autor el 2026-10-22, todas con la recomendación del agente:

- **Q1 → D241.** Dos capabilities nuevas, `gestion-de-usuarios` (API) y `pantalla-de-usuarios` (interfaz), como excepción a «una sola capability» limitada a C-09 (U1).
- **Q2 → D242.** C-09 valida la contraseña inicial de 10 caracteres a 72 bytes con `422` `RN-AU-07` (US-093 CA-9, parte inicial); C-10 la restablecida y la cambiada; la entrada de C-10 se ajusta al archivar (U5).
- **Q3 → D243.** Código nuevo `RN-AU-08` con `409` para el email repetido, ya registrado en `05` (U14).
- **Q4 → D244.** Al menos un rol en el alta y en el `PATCH` (`422` de formato) (U15).
- **Q5 → D245.** Formato mínimo propio del email (una `@`, texto a los dos lados, sin espacios), sin `EmailStr` ni dependencia nueva (U6).
- **Q6 → D246.** El profesional vinculado no cambia al quitar el rol o desactivar a la odontóloga; límite conocido hasta Fase 2 (U16).
- **Q7 → D247.** Quitarse el propio rol `odontologo` está permitido si queda otro odontólogo activo (U11).
- **Q8 → D248.** Bloqueo `FOR UPDATE` de la fila de `consultorio` antes de contar, probado en el perfil `postgres` (U12).
- **Q9 → D249.** Sin `GET /auth/yo`: enlace y acciones visibles para todos; la pantalla muestra el `403` o el `409` de la API (U20).
- **Q10 → D250.** Sin confirmación al desactivar (U18).
- **Q11 → D251.** 35 tareas en 14 grupos (56 escenarios tras la segunda revisión) como excepción limitada a C-09 (U22).

Texto de las preguntas tal como se propusieron (para la trazabilidad):

- **Q1. Capabilities.** (a) Dos nuevas, `gestion-de-usuarios` (API) y `pantalla-de-usuarios` (interfaz), con la excepción a «una sola capability» registrada; (b) una sola `gestion-de-usuarios` con los requisitos de la API y de la pantalla juntos; (c) partir C-09 en dos changes (API y pantalla) en `CHANGES.md`. **Recomendación: (a)**, el corte de D218 y D229 (cada spec con su suite) sin cambiar el índice de `CHANGES.md` (U1).
- **Q2. Largo de la contraseña inicial.** (a) C-09 valida de 10 caracteres a 72 bytes la contraseña inicial con `422` `RN-AU-07` (y C-10 la restablecida y la cambiada); (b) C-09 solo corta en 72 bytes para evitar el `500` y el mínimo llega con C-10; (c) todo en C-10 (el alta acepta cualquier largo y responde `500` por encima de 72 bytes). **Recomendación: (a)**: RN-AU-07 ya lo exige para la inicial y bcrypt no admite más de 72 bytes (U5). Al archivar se ajusta la entrada de C-10.
- **Q3. Código del email repetido.** (a) Código nuevo `RN-AU-08` con `409`; (b) reutilizar `RN-AU-06` o `RN-AU-07`; (c) `409` sin código. **Recomendación: (a)** (regla dura 4; precedente de `RN-AG-15`, D171) (U14).
- **Q4. Un usuario siempre con al menos un rol.** (a) La API exige al menos un rol en el alta y en el `PATCH` (`422` de formato); (b) se permite un usuario sin roles (existe, pero no puede hacer nada). **Recomendación: (a)** (U15).
- **Q5. Formato del email sin dependencia nueva.** (a) Chequeo mínimo propio (una `@`, texto a los dos lados, sin espacios); (b) `EmailStr` con el paquete `email-validator` (dependencia nueva, y rechaza el dominio `.test` de la demo); (c) sin chequeo, como el login. **Recomendación: (a)** (U6).
- **Q6. El profesional vinculado a una odontóloga que deja de serlo o se desactiva.** (a) Nada cambia en `profesional` (límite conocido hasta Fase 2); (b) una regla nueva que impida quitarle el rol o desactivar al usuario vinculado al profesional. **Recomendación: (a)** (D46; la regla (b) no está en la KB) (U16).
- **Q7. Quitarse el propio rol `odontologo`.** (a) Permitido si queda otro odontólogo activo (RN-AU-06 solo prohíbe desactivarse); (b) prohibido como desactivarse. **Recomendación: (a)** (U11).
- **Q8. Carrera entre dos odontólogos.** (a) Bloqueo de la fila de `consultorio` (`FOR UPDATE`) antes de contar, probado en el perfil `postgres`; (b) aislamiento `SERIALIZABLE` en esa transacción, con reintento; (c) sin protección, como límite conocido. **Recomendación: (a)**: el mismo patrón que `bloquear_recursos`, sin migración (U12).
- **Q9. Rol e id del usuario en la interfaz.** (a) Sin ruta nueva: enlace y acciones visibles para todos, y la pantalla muestra el `403` o el `409` de la API (como D230); (b) agregar `GET /auth/yo` (id y roles) para ocultar el enlace a la recepcionista y «Desactivar» en la propia fila. **Recomendación: (a)**: (b) es un cambio de API de sesión que merece su propio change (U20).
- **Q10. Confirmar antes de desactivar.** (a) Sin confirmación, como C-11 (reversible con «Reactivar»); (b) una confirmación propia en la fila («¿Desactivar a …? Su sesión se cierra.») con un estado más y sus escenarios. **Recomendación: (a)**; (b) se puede sumar en un change de interfaz si el autor lo pide.
- **Q11. Tamaño y gobernanza del Apply.** (a) Aceptar **35 tareas en 14 grupos** como excepción registrada al «alrededor de 20» (API y pantalla en el mismo change, perfil `postgres`, tarea bloqueante de Stitch y la prueba manual del autor por CRÍTICO); (b) juntar RED y GREEN para bajar a unas 24 (contra el TDD estricto); (c) Q1 (c), partir el change. **Recomendación: (a)**, con las tareas agrupadas por tema y la excepción limitada a C-09.
