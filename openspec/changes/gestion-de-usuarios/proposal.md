# Proposal: gestion-de-usuarios

Change **C-09** de `CHANGES.md`, historia **US-093** («Gestión de usuarios del consultorio», parte de gestión: alta, roles y desactivación; las contraseñas restablecidas o cambiadas son C-10). Gobernanza **CRÍTICO**: el design se aprueba antes del Apply y ninguna decisión marcada «Propuesta» se implementa sin el ok del autor. Las once preguntas abiertas del design quedaron cerradas por el autor el 2026-10-22 con la recomendación del agente (D241 a D251), y U8 puntos 6 y 7 quedaron aprobados como D252 y D253. Depende de C-07 y C-08, los dos archivados (y usa lo que dejaron C-11 y C-49 en el panel).

## Why

Desde C-06 y C-07 el panel tiene usuarios, sesión y roles, pero los únicos usuarios son los dos del seed y los roles solo se cambian con SQL. US-093 pide que el odontólogo dé acceso a su recepcionista sin tocar la base: crear usuarios con su contraseña inicial, asignarles roles y desactivarlos cortando su acceso de inmediato, sin que el consultorio pueda quedar sin un odontólogo activo (RN-AU-06).

Va ahora porque sus dos dependencias están archivadas, el esquema ya tiene todo lo que hace falta (`usuario` con `activo` y `token_version`, `usuario_rol` con su `CHECK`, migraciones `0006` y `0007`) y C-10 (contraseñas) depende de este change.

## What Changes

- **API de usuarios** (Propuesta de contrato en el design, U4 a U8):
  - `GET /usuarios`: los usuarios del consultorio, activos e inactivos, por `id`, con `id`, `email`, `roles` y `activo`; nunca el hash ni `token_version`.
  - `POST /usuarios`: alta con `email`, `contrasena` (la contraseña inicial, RN-AU-07) y `roles` (al menos uno); el usuario nace activo y con `token_version` 0; la contraseña se guarda solo como hash bcrypt.
  - `PATCH /usuarios/{id}`: cambia `roles` (reemplaza el conjunto) y/o `activo`. Desactivar incrementa `token_version`, así los tokens emitidos dejan de valer en la petición siguiente (RN-AU-03, RN-AU-04, D43); reactivar no revive los tokens anteriores. Con `roles` y `activo` juntos, las reglas se evalúan sobre el resultado y se aplica todo o nada (D252); los roles de un usuario inactivo se pueden cambiar y sigue inactivo (D253). No hay borrado.
- **Permisos** (matriz de `03`, fila «Usuarios del consultorio»): leer, `odontologo` o `dueno`; crear y editar, solo `odontologo`. La recepcionista no ve nada (`403` `RN-AU-05`, D207), evaluado antes que la entrada (D208).
- **Reglas**:
  - **RN-AU-06** (D44), `409`: nadie se desactiva a sí mismo; no se puede desactivar ni quitar el rol `odontologo` al último odontólogo activo. En PostgreSQL dos pedidos simultáneos no pueden dejar al consultorio sin odontólogo (bloqueo de la fila de `consultorio`, D248).
  - **Email único** (US-093 CA-2), normalizado como en el login (D199): un email repetido se rechaza con `409` y el código nuevo **`RN-AU-08`** (D243, registrado en `05`); dos altas simultáneas con el mismo email también dan `409`, no `500`.
  - **Contraseña inicial de 10 caracteres a 72 bytes** (RN-AU-07, D74): `422` con `RN-AU-07` y error del campo `contrasena` (D242: es la parte inicial de US-093 CA-9, que `CHANGES.md` ponía en C-10; sin ella bcrypt rechaza con un `500` una contraseña de más de 72 bytes; la entrada de C-10 se ajusta al archivar).
  - Asignar el rol `odontologo` **no crea un `Profesional`** (D46, US-093 CA-8).
- **Pantalla «Usuarios»** en `/panel/usuarios`, a partir de la pantalla generada en **Stitch** con el design system «Clinical Ops» (D234; id y evidencia en el design): tabla con email, roles, estado y acciones; alta y edición de roles en el panel lateral; desactivar y reactivar desde la fila; los rechazos de la API con su código (`RN-AU-05`, `RN-AU-06`, `RN-AU-07`, `RN-AU-08`, `RN-GL-04`); la sesión que termina vuelve al inicio de sesión (reutiliza el cableado de C-11, D231). Enlace «Usuarios» en la barra del panel.
- **Demo**: sin datos nuevos obligatorios (los dos usuarios del seed alcanzan para el recorrido); README con el recorrido, la tabla escenario → test y los límites conocidos.

No hay migración ni dependencias nuevas. No hay **BREAKING**: las rutas existentes no cambian.

### Escenarios

Cubre los seis mínimos de la entrada C-09 de `CHANGES.md` (dentro del «3 a 6») y la parte inicial de US-093 CA-9 (D242). El spec de la API los detalla en 34 escenarios y el de la pantalla en 24 (58 en total: 9 felices, 13 de error de negocio y 36 de borde), después de incorporar los dos informes de `revisor-de-escenarios` y los dos escenarios de D254 (botón «Cerrar» y nota de roles de la pantalla de Stitch).

| ID | Qué verifica | Dónde corre |
|---|---|---|
| US-093 CA-1 | El odontólogo lista, crea usuarios con su contraseña inicial y les asigna roles; el dueño solo lee; la recepcionista no puede | pytest (API) + Vitest (pantalla) + navegador |
| US-093 CA-2 | El email es único, sin distinguir mayúsculas ni espacios, también frente a un usuario inactivo y con dos altas simultáneas (`RN-AU-08`, D243) | pytest (perfil `postgres` para la carrera) + Vitest + navegador |
| US-093 CA-3 | Desactivar corta el acceso de inmediato (`token_version` + 1, `401` con el token anterior y en el login) y no borra; reactivar no revive tokens | pytest + Vitest + navegador |
| US-093 CA-4 | No se puede quitar el rol `odontologo` (ni desactivar) al último odontólogo activo: `409` `RN-AU-06`; también con pedidos simultáneos en PostgreSQL | pytest (perfil `postgres` para la carrera) + Vitest + navegador |
| US-093 CA-5 | Nadie se desactiva a sí mismo: `409` `RN-AU-06` | pytest + Vitest + navegador |
| US-093 CA-8 | Asignar `odontologo` no crea un `Profesional` | pytest |
| US-093 CA-9 (parte inicial) | La contraseña inicial tiene de 10 caracteres a 72 bytes: `422` `RN-AU-07` (D242) | pytest + Vitest + navegador |

Quedan fuera **CA-6, CA-7 y la parte de CA-9 de la contraseña restablecida o cambiada**: son de C-10. La parte de CA-9 que habla de la **contraseña inicial** entra en C-09 (D242). US-092 CA-1 (la sesión que termina en la pantalla) suma un escenario en el spec de la pantalla, como en C-11, sin contarse entre los mínimos.

## Fuera de alcance

- **Restablecer la contraseña de otro usuario y cambiar la propia** (`POST /usuarios/{id}/restablecer-contrasena`, `POST /auth/cambiar-contrasena`): C-10.
- **Crear o desactivar un `Profesional`** al asignar o quitar el rol `odontologo`, o al desactivar al usuario vinculado: multi-profesional es Fase 2 (D46).
- **Editar el email** de un usuario, borrarlo o agregarle nombre u otros datos personales (el modelo de `04` no los tiene).
- **Saber el rol o el id del usuario en el navegador** (`GET /auth/yo`): sin ruta nueva, como D225 y D230 (D249).
- **Límite de peticiones o registro de auditoría** de las altas y cambios de usuarios: no lo pide ninguna historia (como D195).
- Invitaciones por email, verificación del email, contraseña generada por el sistema, política de complejidad más allá del largo.
- Búsqueda, filtros, orden por columna o paginación de usuarios.
- Varios consultorios por instalación (D173): hay un solo consultorio.

## Capabilities

### New Capabilities

- `gestion-de-usuarios`: el contrato de la API para administrar los usuarios del consultorio: listar, crear con la contraseña inicial, asignar y quitar roles, desactivar y reactivar, el email único, el largo de la contraseña inicial, la regla de no quedarse sin odontólogo activo ni desactivarse a sí mismo y quién puede usar cada ruta (US-093; RN-AU-02 a RN-AU-08).
- `pantalla-de-usuarios`: cómo el panel muestra y mantiene esos usuarios desde el navegador: la tabla, el alta y la edición de roles en el panel lateral, desactivar y reactivar, cómo se ven los rechazos de la API con su código y qué pasa si la sesión termina en la pantalla (US-093, US-092 CA-1).

**Dos capabilities en un change** se aparta de la regla «una sola capability» (`openspec/config.yaml`, regla dura 12): excepción aceptada por el autor y limitada a C-09 (**D241**), con el criterio de D218 y D229 de separar el contrato de la API del comportamiento del navegador, porque cada spec se verifica con su propia suite.

### Modified Capabilities

Ninguna. Se revisaron:
- `proteccion-del-panel`: su requisito de matriz cubre «las rutas creadas antes de este change» y el de rutas públicas ya exige token a «las que agreguen los changes siguientes»; los permisos de `/usuarios` quedan en `gestion-de-usuarios`, como `creacion-de-turnos` y las demás describen sus rutas.
- `sesion-del-panel`: el login de un usuario inactivo y el `401` por `token_version` no cambian; este change solo crea usuarios y mueve esos valores.
- `ingreso-al-panel` y `pantalla-de-prestaciones`: el enlace nuevo de la barra no cambia sus requisitos.

## Impact

- **Backend, código nuevo**: `backend/app/application/usuarios.py` (casos de uso), reglas puras en `backend/app/domain/acceso/usuarios.py` (RN-AU-06, largo de la contraseña), `backend/app/api/routers/usuarios.py`, esquemas en `api/esquemas.py`, errores nuevos en `domain/errors.py` y su traducción en `api/errores.py`; permisos `usuarios.leer` y `usuarios.editar` en `domain/acceso/roles.py`; métodos nuevos del repositorio de usuarios (listar, guardar, bloquear el consultorio). Tests de unidad, integración, API y del perfil `postgres`.
- **Frontend, código nuevo**: `frontend/src/features/usuarios/` (cliente de la API, página, tabla, panel lateral, mensajes y tests). **Se modifica**: `App.tsx` (ruta), `pages/PanelBase.tsx` (enlace «Usuarios»), `test/servidorFalso.ts` (contrato de usuarios), `shared/estilos/panel.css` y `tokens.css` (lo que pida la pantalla de Stitch), un ícono SVG nuevo en `shared/iconos/`.
- **Esquema y migraciones**: sin cambios (D248 usa un bloqueo de fila sobre `consultorio`, no una tabla ni restricción nueva).
- **Dependencias y variables de entorno**: ninguna nueva (`backend/pyproject.toml`, `frontend/package.json` y `package-lock.json` no cambian).
- **Documentación**: `README.md`; evidencia de Stitch en `docs/skills-mcp/evidencias/sesion-nueva/stitch-usuarios.md` y `stitch-usuarios-pantalla/`. Las respuestas a Q1 a Q12 ya están registradas en `knowledge-base/10_preguntas_abiertas.md` (D241 a D254) y el código nuevo `RN-AU-08` en `05` (citado en US-093 CA-2 de `06` y en la matriz de `03`).
- **Tamaño**: 36 tareas en 14 grupos para 58 escenarios, frente a «alrededor de 20» de `CHANGES.md`: excepción aceptada por el autor y limitada a C-09 (**D251**, ampliada por **D254**).
