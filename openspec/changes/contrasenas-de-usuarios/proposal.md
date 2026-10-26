# Proposal: contrasenas-de-usuarios

Change **C-10** de `CHANGES.md`, historia **US-093** («Gestión de usuarios del consultorio», parte de contraseñas: restablecer la de otro usuario y cambiar la propia; la gestión de usuarios y la contraseña inicial son de C-09, archivado). Gobernanza **CRÍTICO**: el design se aprueba antes del Apply y ninguna decisión marcada «Propuesta» se implementa sin el ok del autor. Depende de C-09 (archivado el 2026-10-22). Las preguntas abiertas del design (Q1 a Q12) quedaron cerradas por el autor el 2026-10-26 con la recomendación del agente (Q4 con un código propio), junto con los hallazgos H1 a H11 de `revisor-de-escenarios`: decisiones **D290 a D303** de `knowledge-base/10_preguntas_abiertas.md` y códigos nuevos **`RN-AU-09`** y **`RN-AU-10`** en `05`.

## Why

Desde C-09 el odontólogo crea usuarios con su contraseña inicial, pero nadie puede cambiar una contraseña sin tocar la base: si la recepcionista la olvida o se sospecha que alguien la conoce, la única salida es SQL, y la propia odontóloga no puede cambiar la suya (`SEED_USUARIO_PASSWORD` solo vale al sembrar, D197). US-093 CA-6, CA-7 y CA-9 piden las dos operaciones que faltan, con el corte de sesiones por `token_version` que ya usa la desactivación (RN-AU-03, RN-AU-07).

Va ahora porque C-09 dejó listo todo lo que necesita (usuario con `hash_password` y `token_version`, la regla del largo de la contraseña en el dominio, `ContrasenaFueraDeRango` con su campo, la pantalla de usuarios con su panel lateral) y es el último change de usuarios de la fase 3.

## What Changes

- **Restablecer la contraseña de otro usuario** (US-093 CA-6; RN-AU-07): `POST /usuarios/{id}/restablecer-contrasena` con `{"contrasena": …}`, solo `odontologo` (matriz de `03`, fila «Usuarios del consultorio»). Guarda el hash bcrypt nuevo e **incrementa `token_version`**: todos los tokens del usuario dejan de valer en la petición siguiente y la contraseña anterior ya no inicia sesión. Responde `204` (Propuesta, design K4). Restablecer la **propia** contraseña por esta ruta se rechaza con `409` y el código propio `RN-AU-10` (D293) y restablecer la de un usuario inactivo se acepta sin reactivarlo (D294).
- **Cambiar la propia contraseña** (US-093 CA-7; RN-AU-07): `POST /auth/cambiar-contrasena` con `{"contrasena_actual": …, "contrasena_nueva": …}`, para cualquier usuario con sesión y rol (D298). Pide la actual; con la actual incorrecta se rechaza con `422` sin cambiar nada y **sin `401`**, con el código propio `RN-AU-09` (D292). Incrementa `token_version`, así **las demás sesiones** del usuario dejan de valer, y responde con un access y un refresh nuevos para que la sesión desde la que se cambió siga (D291).
- **Largo de la contraseña restablecida y la cambiada** (US-093 CA-9, la parte que C-09 dejó a C-10, D242): de 10 caracteres a 72 bytes en UTF-8, sin recortar; fuera de rango, `422` con `RN-AU-07` y el error del campo (`contrasena` o `contrasena_nueva`), como validación de entrada (RN-GL-02), sin cambiar nada.
- **Concurrencia**: dos cambios de contraseña simultáneos sobre el mismo usuario incrementan `token_version` dos veces (bloqueo de la fila del usuario, D299), para que ningún token emitido por uno siga valiendo después del otro.
- **Pantalla**:
  - En «Usuarios», la acción de fila **«Restablecer contraseña»**, que abre el panel lateral con «Contraseña nueva» y su ayuda, y muestra los rechazos con su código (`RN-AU-05`, `RN-AU-07`, `RN-AU-10`, `RN-GL-04`).
  - **«Mi contraseña»** (`/panel/contrasena`, enlace en la barra del panel, para todos los roles): contraseña actual, nueva y su repetición (la repetición se controla en el navegador, D296); al cambiarla, la sesión sigue con los tokens nuevos y se avisa que las otras sesiones se cerraron.
  - Las dos a partir de la pantalla de **Stitch** con el design system «Clinical Ops» (D234). Las dos pantallas se generaron en la tarea 1.2 antes de aprobar el plan (D301): «Mi contraseña» (`projects/14200813501064679723/screens/fa6faa69cae34252a7c79e2cb82210c5`) y «Usuarios» con el panel «Restablecer contraseña» (`projects/14200813501064679723/screens/925f1e4028294cb2bb9bdeeea81ffd09`); qué se toma y qué se rechaza, en el design («Referencia visual (Stitch)»), con una pregunta abierta para el autor (Q13).
- **Demo y README**: sin datos nuevos; recorrido de restablecer y cambiar con la demo, tabla escenario → test y límites conocidos. **Guía de prueba manual de C-09 y C-10** para el autor (pedido explícito del autor), que el autor sigue y aprueba antes del archive.

No hay migración ni dependencias nuevas. No hay **BREAKING**: las rutas existentes no cambian. La lista de rutas públicas no cambia (`POST /auth/cambiar-contrasena` exige el access token).

### Escenarios

Cubre los tres mínimos de la entrada C-10 de `CHANGES.md` (US-093 CA-6, CA-7 y CA-9 en la parte de la contraseña restablecida y la cambiada), dentro del «3 a 6». El spec de la API los detalla en **21 escenarios** y el de la pantalla en **17** (38 en total: 4 felices, 10 de error de negocio y 24 de borde, después del `/opsx:update` con los hallazgos H3 y H8), con variantes cortas de las mismas reglas: el tamaño es una excepción aceptada por el autor (D300).

| ID | Qué verifica | Dónde corre |
|---|---|---|
| US-093 CA-6 | El odontólogo restablece la contraseña de otro usuario; `token_version` + 1, los tokens anteriores dan `401` y la contraseña anterior ya no inicia sesión; la recepcionista y el dueño reciben `403` | pytest (perfil `postgres` para la carrera) + Vitest + navegador |
| US-093 CA-7 | Cada usuario cambia la suya pidiendo la actual; `token_version` + 1, las demás sesiones caen y la actual sigue con los tokens nuevos; la actual incorrecta se rechaza sin cerrar la sesión | pytest + Vitest + navegador |
| US-093 CA-9 (restablecida y cambiada) | De 10 caracteres a 72 bytes: `422` `RN-AU-07` en el campo correspondiente y nada cambia | pytest + Vitest + navegador |

US-092 CA-1 (la sesión que termina en la pantalla vuelve al inicio de sesión) suma un escenario en el spec de la pantalla, como en C-09 y C-11, sin contarse entre los mínimos. Ningún criterio de US-093 queda fuera: C-09 cubrió CA-1 a CA-5, CA-8 y la parte inicial de CA-9.

## Fuera de alcance

- **Recuperación de contraseña por email** («olvidé mi contraseña», enlaces o códigos por correo): ninguna historia la pide (`CHANGES.md`).
- **Revocar tokens de a uno** o ver las sesiones abiertas de un usuario: no hay tabla de tokens (RN-AU-03); la invalidación es en bloque por `token_version`.
- **Contraseña generada por el sistema**, contraseña temporal que obliga a cambiarla al entrar, vencimiento de contraseñas, historial de contraseñas o política de complejidad más allá del largo (D74).
- **Límite de peticiones** en `POST /auth/cambiar-contrasena` y registro de eventos de seguridad: como D195 en `/auth/login`, queda como límite conocido del README.
- **Saber en el navegador el rol o el id de quien inició sesión** (`GET /auth/yo`): sin ruta nueva, como D249; las acciones se ven para todos y la API decide.
- Editar el email o borrar usuarios (C-09 ya lo dejó afuera); cambios del seed o de `SEED_USUARIO_PASSWORD` (D197).
- Mostrar u ocultar la contraseña con un botón («ojo»), medidor de fortaleza o generador de contraseñas en la pantalla.

## Capabilities

### New Capabilities

- `contrasenas-de-usuarios`: el contrato de la API para las contraseñas después del alta: restablecer la de otro usuario (solo `odontologo`), cambiar la propia pidiendo la actual, el largo de 10 caracteres a 72 bytes, el incremento de `token_version` que corta las sesiones y el orden de los rechazos (US-093 CA-6, CA-7, CA-9; RN-AU-03, RN-AU-05, RN-AU-07).
- `pantalla-de-contrasenas`: cómo el panel restablece la contraseña de un usuario desde la pantalla de usuarios y cómo cada usuario cambia la suya desde «Mi contraseña», con los rechazos de la API y su código, y qué pasa con la sesión del navegador después del cambio (US-093 CA-6, CA-7, CA-9; US-092 CA-1).

**Dos capabilities en un change** se aparta de la regla «una sola capability» (`openspec/config.yaml`, regla dura 12): el autor la aceptó como excepción limitada a C-10 (**D290**), con el criterio de D241 y D271 de separar el contrato de la API (pytest) del comportamiento del navegador (Vitest). Las alternativas (deltas en cuatro capabilities existentes, o generalizar la regla) están en el design.

### Modified Capabilities

Ninguna (D290). Se revisaron:
- `gestion-de-usuarios`: sus requisitos siguen valiendo tal cual (el `PATCH` sigue rechazando `contrasena` con `422` de formato; la contraseña inicial sigue siendo de C-09); restablecer va en la capability nueva.
- `sesion-del-panel`: el login con la contraseña nueva y el `401` por `token_version` vieja ya están especificados («la token_version del usuario cambió», US-094 CA-3); cambiar la contraseña no es iniciar ni renovar la sesión.
- `proteccion-del-panel`: su guard ya exige el access token a toda ruta nueva fuera de la lista pública, y la lista no cambia; los permisos de las dos rutas quedan en `contrasenas-de-usuarios`, como hizo C-09.
- `pantalla-de-usuarios` e `ingreso-al-panel`: la acción de fila nueva y el enlace «Mi contraseña» no cambian ninguno de sus requisitos; el comportamiento nuevo va en `pantalla-de-contrasenas`.

## Impact

- **Backend, código nuevo o ampliado**: en `backend/app/domain/acceso/usuarios.py`, la regla del largo para cualquier contraseña y la regla de no restablecer la propia; `ContrasenaActualIncorrecta` (`RN-AU-09`, D292) y `RestablecerLaPropia` (`RN-AU-10`, D293) en `domain/errors.py`; el permiso del cambio propio en `domain/acceso/roles.py` (D298); casos de uso `restablecer_contrasena` y `cambiar_contrasena`; métodos del repositorio de usuarios para guardar la contraseña con el incremento de `token_version` bajo bloqueo de fila; rutas en `api/routers/usuarios.py` y `api/routers/auth.py`; esquemas de entrada; traducción en `api/errores.py`. Tests de unidad, integración, API y del perfil `postgres`.
- **Frontend**: `frontend/src/features/contrasenas/` (cliente, pantalla «Mi contraseña», mensajes y tests); en `features/usuarios/`, la acción «Restablecer contraseña» y el modo del panel lateral; `ProveedorDeSesion` gana una forma de reemplazar los tokens de la sesión (D291); `App.tsx` (ruta), `PanelBase.tsx` (enlace), `test/servidorFalso.ts` (las dos rutas y `token_version` por usuario), `panel.css` y `tokens.css` según la pantalla de Stitch, un ícono SVG nuevo.
- **Esquema y migraciones**: sin cambios (`usuario.hash_password` y `usuario.token_version` existen desde `0006`).
- **Dependencias y variables de entorno**: ninguna nueva.
- **Documentación**: `README.md`; guía de prueba manual de C-09 y C-10 (`docs/guias/prueba-manual-c09-c10.md`, D302); evidencia de Stitch en `docs/skills-mcp/evidencias/sesion-nueva/stitch-contrasenas.md` y `stitch-contrasenas-pantalla/`. Las respuestas a Q1 a Q12 quedaron registradas en `knowledge-base/10_preguntas_abiertas.md` (D290 a D303); `RN-AU-09` y `RN-AU-10`, en `05` y en US-093 de `06`.
- **`CHANGES.md`**: C-10 pasa a `[~]` en curso con este propose (como C-13).
- **Tamaño**: 29 tareas en 13 grupos para 38 escenarios, frente a «alrededor de 20» de `CHANGES.md`: excepción aceptada por el autor y limitada a C-10 (**D300**).
