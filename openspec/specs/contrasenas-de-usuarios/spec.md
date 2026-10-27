# contrasenas-de-usuarios Specification

## Purpose
Define la API de las contraseñas de los usuarios del consultorio después del alta: el odontólogo restablece la de otro usuario y cada usuario cambia la propia pidiendo la actual, con el largo de 10 caracteres a 72 bytes y el incremento de `token_version` que corta las sesiones anteriores (US-093 CA-6, CA-7, CA-9; RN-AU-03, RN-AU-05, RN-AU-07, RN-AU-09, RN-AU-10).

Convenciones de los escenarios: todos los instantes están en **UTC**. «Con el token de X» significa con la cabecera `Authorization: Bearer <access token>` de un access token vigente emitido para X por `POST /auth/login` (capability `sesion-del-panel`). «El `401` de sesión inválida» es la respuesta fija de `proteccion-del-panel`: `401` con `codigos` `["RN-AU-03"]` (D206); el `403` de permiso insuficiente es su `403` con `codigos` `["RN-AU-05"]` (D207). «El `401` genérico de inicio de sesión» es el de `sesion-del-panel`, con `codigos` `["RN-AU-04"]`. Un error sale como `application/problem+json` con `codigos`. Los usuarios de los ejemplos son ficticios y del único consultorio de la instalación (D173): «la odontóloga» es `odontologa@consultorio-demo.test` (id 1, activa, `odontologo` + `dueno`), «la recepcionista» es `recepcion@consultorio-demo.test` (id 2, activa, `recepcionista`), «el dueño» es un usuario activo con solo `dueno` y «la colega» es un usuario activo con solo `odontologo`; todos empiezan con la contraseña ficticia `demo-consultorio-2026` y `token_version` 0, salvo que el escenario diga otra cosa. «La contraseña nueva» de los ejemplos es la ficticia `clave-nueva-2026` (16 caracteres). «Nada cambia» significa que el hash guardado y `token_version` del usuario quedan como estaban y la contraseña anterior sigue iniciando sesión. Las elecciones que el design dejó como preguntas son decisiones del autor (D290 a D302); los códigos `RN-AU-09` (D292) y `RN-AU-10` (D293) están registrados en `knowledge-base/05_reglas_de_negocio.md`. Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite por defecto, salvo que digan otra cosa.

## Requirements

### Requirement: El odontólogo restablece la contraseña de otro usuario

`POST /usuarios/{id}/restablecer-contrasena` con `{"contrasena": …}` SHALL guardar el hash bcrypt de la contraseña nueva del usuario `id`, incrementar su `token_version` en 1 y responder `204` sin cuerpo (US-093 CA-6; RN-AU-07, RN-AU-03). Solo `odontologo` puede restablecer (matriz de `03`; RN-AU-05), y solo la de **otro** usuario: restablecer la propia SHALL rechazarse con `409` `RN-AU-10` (D293). Un usuario inactivo se restablece y sigue inactivo (D294). Restablecer y cambiar la propia leen al usuario con bloqueo de fila (D299). La contraseña MUST NOT guardarse en claro ni aparecer en ninguna respuesta. Un rechazo MUST NOT cambiar nada.

#### Scenario: US-093 CA-6 Feliz - la odontóloga restablece la contraseña de la recepcionista

- **GIVEN** la recepcionista inició sesión y tiene un access y un refresh vigentes
- **WHEN** la odontóloga pide `POST /usuarios/2/restablecer-contrasena` con su token y el cuerpo `{"contrasena": "clave-nueva-2026"}`
- **THEN** el sistema responde `204` sin cuerpo
- **AND** la base guarda para la recepcionista un hash bcrypt distinto del anterior y no la contraseña en claro, y su `token_version` pasa de 0 a 1
- **AND** `POST /auth/login` de la recepcionista con `clave-nueva-2026` responde `200`, y con `demo-consultorio-2026` responde el `401` genérico de inicio de sesión
- **AND** el access anterior de la recepcionista recibe el `401` de sesión inválida en `GET /prestaciones`, y su refresh anterior lo recibe en `POST /auth/refresh`
- **AND** el token de la odontóloga sigue sirviendo

#### Scenario: US-093 CA-6 Error de negocio - la recepcionista y el dueño no pueden restablecer

- **WHEN** la recepcionista pide, con su token, `POST /usuarios/1/restablecer-contrasena` con `{"contrasena": "clave-nueva-2026"}`, y el dueño pide lo mismo sobre `/usuarios/2` con el suyo
- **THEN** cada petición recibe `403` con `codigos` `["RN-AU-05"]`
- **AND** nada cambia para la odontóloga ni para la recepcionista

#### Scenario: US-093 CA-6 Borde - restablecer a un usuario inactivo no lo reactiva

- **GIVEN** `administracion@consultorio-demo.test` inactivo, con `token_version` 1
- **WHEN** la odontóloga restablece su contraseña a `clave-nueva-2026`
- **THEN** el sistema responde `204`, el usuario sigue inactivo y su `token_version` pasa a 2
- **AND** `POST /auth/login` con `clave-nueva-2026` responde el `401` genérico de inicio de sesión mientras siga inactivo
- **AND** después de reactivarlo con `PATCH /usuarios/{id}` y `{"activo": true}`, inicia sesión con `clave-nueva-2026` y no con la anterior

#### Scenario: US-093 CA-6 Error de negocio - la propia contraseña no se restablece

- **WHEN** la odontóloga pide, con su token, `POST /usuarios/1/restablecer-contrasena` con `{"contrasena": "clave-nueva-2026"}`
- **THEN** el sistema responde `409` con `codigos` `["RN-AU-10"]` y el `detail` fijo «La propia contraseña se cambia con POST /auth/cambiar-contrasena, pidiendo la actual.»
- **AND** nada cambia para la odontóloga y su token sigue sirviendo

#### Scenario: US-093 CA-6 Borde - el usuario de la URL se evalúa después del permiso y de la entrada

- **WHEN** la odontóloga pide `POST /usuarios/999/restablecer-contrasena` con un cuerpo válido; el dueño pide lo mismo con el suyo; y la odontóloga pide `POST /usuarios/999/restablecer-contrasena` con `{}`
- **THEN** la primera recibe `404` con `codigos` `["RN-GL-04"]`
- **AND** la del dueño recibe `403` con `codigos` `["RN-AU-05"]` y no `404`
- **AND** la última recibe `422` con `codigos` vacío y un error del campo `contrasena`, y no `404` (RN-GL-02, D208)

#### Scenario: US-093 CA-6 Borde - sin sesión se responde 401 antes que la entrada

- **WHEN** se pide `POST /usuarios/2/restablecer-contrasena` sin la cabecera `Authorization` y con `{}`
- **THEN** el sistema responde el `401` de sesión inválida, con `codigos` `["RN-AU-03"]`, y no `422` (D208)
- **AND** nada cambia para la recepcionista

#### Scenario: US-093 CA-6 Borde - un cuerpo mal formado se rechaza todo junto

- **WHEN** la odontóloga pide, en peticiones separadas, `POST /usuarios/2/restablecer-contrasena` con `{}`, con `{"contrasena": 1234567890}`, con `{"contrasena": null}` y con `{"contrasena": "clave-nueva-2026", "token_version": 0}`
- **THEN** cada petición recibe `422` con `codigos` vacío y un error del campo con problemas
- **AND** nada cambia para la recepcionista

#### Scenario: US-093 CA-6 Borde - dos cambios simultáneos sobre el mismo usuario suben la versión dos veces

- **GIVEN** en PostgreSQL, la recepcionista con `token_version` 0
- **WHEN** dos restablecimientos de su contraseña llegan a la vez y el segundo lee el usuario mientras el primero todavía no confirmó (arnés de carrera)
- **THEN** el segundo espera al primero, los dos responden `204` y la `token_version` de la recepcionista queda en 2
- **AND** la contraseña que inicia sesión es la del pedido que confirmó último
- **AND** este escenario se verifica en el perfil `postgres` y no en la suite por defecto

#### Scenario: US-093 CA-6 Borde - restablecer y cambiar la propia a la vez no deja vigente el cambio propio

- **GIVEN** en PostgreSQL, la recepcionista con `token_version` 0 y la odontóloga restableciendo su contraseña a `clave-nueva-2026`, con el usuario ya leído y el restablecimiento sin confirmar (arnés de carrera)
- **WHEN** la recepcionista pide, con su token, `POST /auth/cambiar-contrasena` con `{"contrasena_actual": "demo-consultorio-2026", "contrasena_nueva": "otra-clave-2026"}` mientras el restablecimiento no confirmó
- **THEN** el cambio propio espera al restablecimiento, verifica la actual contra el hash ya confirmado y responde `422` con `codigos` `["RN-AU-09"]`, sin tokens nuevos
- **AND** el restablecimiento responde `204`, la `token_version` de la recepcionista queda en 1 y solo `clave-nueva-2026` inicia sesión
- **AND** este escenario se verifica en el perfil `postgres` y no en la suite por defecto (D299)

### Requirement: Cada usuario cambia su propia contraseña pidiendo la actual

`POST /auth/cambiar-contrasena` con `{"contrasena_actual": …, "contrasena_nueva": …}` SHALL, si la actual coincide con la del usuario del token, guardar el hash bcrypt de la nueva, incrementar su `token_version` en 1 y responder `200` con un access y un refresh nuevos, con la forma de `POST /auth/login` y sin caché (US-093 CA-7; RN-AU-07, RN-AU-03; D291). Si la actual no coincide, SHALL responder `422` con `codigos` `["RN-AU-09"]` sin cambiar nada (D292). Lo pueden usar los tres roles (matriz de `03`, «U propio»; permiso `contrasena.propia`, D298); la nueva igual a la actual se acepta (D295).

#### Scenario: US-093 CA-7 Feliz - la recepcionista cambia la suya y sus otras sesiones caen

- **GIVEN** la recepcionista inició sesión dos veces (sesión A y sesión B), cada una con su access y su refresh
- **WHEN** pide, con el access de la sesión A, `POST /auth/cambiar-contrasena` con `{"contrasena_actual": "demo-consultorio-2026", "contrasena_nueva": "clave-nueva-2026"}`
- **THEN** el sistema responde `200` con `access_token`, `refresh_token`, `token_type` `bearer` y `expires_in`, y la cabecera `Cache-Control: no-store`
- **AND** su `token_version` pasa de 0 a 1 y la base guarda un hash bcrypt nuevo, no la contraseña en claro
- **AND** con el access nuevo `GET /prestaciones` responde `200`, y con el refresh nuevo `POST /auth/refresh` responde `200`
- **AND** el access y el refresh de la sesión B, y el access de la sesión A usado en el pedido, reciben el `401` de sesión inválida
- **AND** `POST /auth/login` con `clave-nueva-2026` responde `200`, y con `demo-consultorio-2026` el `401` genérico de inicio de sesión

#### Scenario: US-093 CA-7 Borde - el odontólogo y el dueño también cambian la suya y un usuario sin roles no

- **GIVEN** un usuario activo sin ningún rol, creado directamente en la base
- **WHEN** la odontóloga y el dueño cambian cada uno su contraseña con la actual correcta, y el usuario sin roles pide lo mismo con su token
- **THEN** la odontóloga y el dueño reciben `200` y su `token_version` sube en 1
- **AND** el usuario sin roles recibe `403` con `codigos` `["RN-AU-05"]` y nada cambia para él

#### Scenario: US-093 CA-7 Error de negocio - con la contraseña actual incorrecta no cambia nada

- **WHEN** la recepcionista pide, con su token, `POST /auth/cambiar-contrasena` con `{"contrasena_actual": "no-es-la-actual-2026", "contrasena_nueva": "clave-nueva-2026"}`
- **THEN** el sistema responde `422` con `codigos` `["RN-AU-09"]` y el `detail` fijo «La contraseña actual no es correcta.», que no repite ninguna de las dos contraseñas
- **AND** la respuesta no es `401` y el token con que lo pidió sigue sirviendo en `GET /prestaciones`
- **AND** nada cambia para la recepcionista

#### Scenario: US-093 CA-7 Borde - una contraseña actual de más de 72 bytes cuenta como incorrecta

- **WHEN** la recepcionista pide el cambio con una `contrasena_actual` de 73 bytes y una `contrasena_nueva` válida
- **THEN** el sistema responde `422` con `codigos` `["RN-AU-09"]`, no `500`
- **AND** nada cambia para la recepcionista

#### Scenario: US-093 CA-7 Borde - la nueva igual a la actual se acepta

- **WHEN** la recepcionista pide el cambio con `contrasena_actual` y `contrasena_nueva` iguales a `demo-consultorio-2026`
- **THEN** el sistema responde `200` con tokens nuevos y su `token_version` pasa de 0 a 1
- **AND** `POST /auth/login` con `demo-consultorio-2026` sigue respondiendo `200`

#### Scenario: US-093 CA-7 Borde - sin sesión o con una sesión que ya no vale se responde 401

- **WHEN** se pide `POST /auth/cambiar-contrasena` sin la cabecera `Authorization` y con `{}`; y la recepcionista lo pide con un access emitido antes de que la odontóloga le restableciera la contraseña
- **THEN** las dos peticiones reciben el `401` de sesión inválida, con `codigos` `["RN-AU-03"]`, y no `422` (D208)
- **AND** nada cambia

#### Scenario: US-093 CA-7 Borde - un cuerpo mal formado se rechaza todo junto

- **WHEN** la recepcionista pide, en peticiones separadas, el cambio sin `contrasena_actual`, con `contrasena_actual` vacía, sin `contrasena_nueva`, y con un campo `email` de más
- **THEN** cada petición recibe `422` con `codigos` vacío y un error del campo con problemas
- **AND** una petición sin ninguno de los dos campos recibe un solo `422` con **dos** errores, de `contrasena_actual` y de `contrasena_nueva` (RN-GL-02)
- **AND** nada cambia para la recepcionista

### Requirement: La contraseña restablecida o cambiada tiene de 10 caracteres a 72 bytes

La contraseña restablecida y la nueva del cambio propio SHALL tener al menos 10 caracteres y como máximo 72 bytes en UTF-8, sin recortarlas (RN-AU-07, D74; US-093 CA-9 en su parte de la contraseña restablecida y la cambiada). Fuera de ese rango, la ruta SHALL responder `422` con `codigos` `["RN-AU-07"]` y un error del campo (`contrasena` o `contrasena_nueva`) como validación de entrada (RN-GL-02), después de la de formato y antes de toda regla de negocio, sin cambiar nada.

#### Scenario: US-093 CA-9 Error de negocio - una contraseña restablecida de 9 caracteres se rechaza

- **WHEN** la odontóloga pide `POST /usuarios/2/restablecer-contrasena` con `{"contrasena": "corta-123"}` (9 caracteres)
- **THEN** el sistema responde `422` con `codigos` `["RN-AU-07"]` y un error del campo `contrasena` con el código `RN-AU-07`
- **AND** nada cambia para la recepcionista

#### Scenario: US-093 CA-9 Error de negocio - una contraseña nueva de 9 caracteres se rechaza

- **WHEN** la recepcionista pide `POST /auth/cambiar-contrasena` con la actual correcta y `contrasena_nueva` `corta-123`
- **THEN** el sistema responde `422` con `codigos` `["RN-AU-07"]` y un error del campo `contrasena_nueva` con el código `RN-AU-07`
- **AND** nada cambia para la recepcionista y su token sigue sirviendo

#### Scenario: US-093 CA-9 Borde - 10 caracteres y 72 bytes se aceptan; 73 bytes no

- **WHEN** en cada una de las dos rutas se pide una contraseña de exactamente 10 caracteres, después una de exactamente 72 bytes, y después una de 37 caracteres que ocupan 73 bytes (con letras con tilde)
- **THEN** en las dos rutas las dos primeras se aceptan (`204` al restablecer, `200` al cambiar)
- **AND** la de 73 bytes recibe `422` con `codigos` `["RN-AU-07"]` y no cambia nada
- **AND** una contraseña con espacios en los extremos se guarda tal cual: solo inicia sesión escrita con esos espacios

#### Scenario: US-093 CA-9 Borde - el largo se informa antes que las reglas de negocio

- **WHEN** la recepcionista pide el cambio con una `contrasena_actual` incorrecta y `contrasena_nueva` `corta-123`; y la odontóloga pide restablecer **su propia** contraseña con `corta-123`
- **THEN** las dos peticiones reciben `422` con `codigos` `["RN-AU-07"]`, sin `RN-AU-09` en la primera ni `409` `RN-AU-10` en la segunda (RN-GL-02)
- **AND** nada cambia

#### Scenario: US-093 CA-9 Borde - el formato se informa antes que el largo

- **WHEN** la odontóloga pide restablecer con `{"contrasena": "corta-123", "activo": true}`; y la recepcionista pide el cambio con la actual correcta, `contrasena_nueva` `corta-123` y un campo `email` de más
- **THEN** las dos peticiones reciben `422` con `codigos` vacío y solo el error del campo de más, sin el código `RN-AU-07` (como D242 y D177)
- **AND** nada cambia para la recepcionista
