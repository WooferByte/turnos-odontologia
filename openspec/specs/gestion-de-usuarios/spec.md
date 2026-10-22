# gestion-de-usuarios Specification

## Purpose
Define la API con la que el odontólogo administra los usuarios del consultorio: listarlos, crearlos con su contraseña inicial, asignarles y quitarles roles, desactivarlos cortando su acceso y reactivarlos, sin que el consultorio quede sin un odontólogo activo (US-093; RN-AU-02 a RN-AU-08).

Convenciones de los escenarios: todos los instantes están en **UTC**. «Con el token de X» significa con la cabecera `Authorization: Bearer <access token>` de un access token vigente emitido para X por `POST /auth/login` (capability `sesion-del-panel`). «El `401` de sesión inválida» es la respuesta fija de `proteccion-del-panel`: `401` con `codigos` `["RN-AU-03"]` (D206); el `403` de permiso insuficiente es su `403` con `codigos` `["RN-AU-05"]` (D207), y los escenarios lo escriben con su código. Un error sale como `application/problem+json` con `codigos`. Los usuarios de los ejemplos son ficticios y del único consultorio de la instalación (D173): «la odontóloga» es `odontologa@consultorio-demo.test` (id 1, activa, `odontologo` + `dueno`), «la recepcionista» es `recepcion@consultorio-demo.test` (id 2, activa, `recepcionista`) y «el dueño» es un usuario activo con solo `dueno`. «Un odontólogo activo» es un usuario con `activo` verdadero y el rol `odontologo`. La contraseña de los ejemplos es ficticia. Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite por defecto, salvo que digan otra cosa.

## Requirements

### Requirement: Listar los usuarios del consultorio

`GET /usuarios` SHALL responder `200` con todos los usuarios del consultorio, activos e inactivos, ordenados por `id`, cada uno con `id`, `email` (normalizado, D199), `roles` (en el orden `odontologo`, `recepcionista`, `dueno`) y `activo`. La respuesta MUST NOT incluir el hash de la contraseña ni `token_version`. Pueden leer `odontologo` y `dueno` (matriz de `03`; RN-AU-05).

#### Scenario: US-093 CA-1 Feliz - la odontóloga lista los usuarios con sus roles

- **GIVEN** la odontóloga y la recepcionista de la demo, y un tercer usuario `administracion@consultorio-demo.test` inactivo con el rol `dueno`
- **WHEN** la odontóloga pide `GET /usuarios` con su token
- **THEN** el sistema responde `200` con tres usuarios en orden de `id`
- **AND** la odontóloga figura con `roles` `["odontologo", "dueno"]` y `activo` verdadero, y el tercero con `["dueno"]` y `activo` falso

#### Scenario: US-093 CA-1 Borde - la lista no expone la contraseña ni la versión del token

- **WHEN** la odontóloga pide `GET /usuarios` con su token
- **THEN** ningún usuario de la respuesta tiene otro campo que `id`, `email`, `roles` y `activo`

#### Scenario: US-093 CA-1 Borde - el dueño lee pero la recepcionista no

- **WHEN** el dueño pide `GET /usuarios` con su token, y la recepcionista pide lo mismo con el suyo
- **THEN** el dueño recibe `200` con la lista
- **AND** la recepcionista recibe `403` con `codigos` `["RN-AU-05"]`

### Requirement: Crear un usuario con su contraseña inicial y sus roles

`POST /usuarios` SHALL crear un usuario del consultorio con `email`, `contrasena` y `roles` (al menos uno, sin repetir, de los tres válidos) y responder `201` con el usuario creado, activo y con la forma de la lista. La contraseña MUST guardarse solo como hash bcrypt (RN-AU-07). Solo `odontologo` puede crear (RN-AU-05); un rechazo MUST NOT crear nada. Asignar `odontologo` MUST NOT crear un `Profesional` (D46).

#### Scenario: US-093 CA-1 Feliz - la odontóloga crea una recepcionista que inicia sesión

- **WHEN** la odontóloga pide `POST /usuarios` con su token y el cuerpo `{"email": "turnos@consultorio-demo.test", "contrasena": "clave-ficticia-2026", "roles": ["recepcionista"]}`
- **THEN** el sistema responde `201` con `id`, `email` `turnos@consultorio-demo.test`, `roles` `["recepcionista"]` y `activo` verdadero
- **AND** la base guarda un hash bcrypt y no la contraseña en claro, con `token_version` 0
- **AND** `POST /auth/login` con ese email y esa contraseña responde `200`, y con el access token recibido `POST /turnos` no responde `403`

#### Scenario: US-093 CA-1 Borde - el email se guarda normalizado

- **WHEN** la odontóloga crea un usuario con el email `  Turnos@Consultorio-Demo.TEST `
- **THEN** el usuario creado tiene el email `turnos@consultorio-demo.test` y con él inicia sesión

#### Scenario: US-093 CA-1 Error de negocio - la recepcionista y el dueño no pueden crear usuarios

- **WHEN** la recepcionista y el dueño piden, cada uno con su token, `POST /usuarios` con un cuerpo válido
- **THEN** cada petición recibe `403` con `codigos` `["RN-AU-05"]` y no se crea ningún usuario

#### Scenario: US-093 CA-1 Borde - un cuerpo mal formado se rechaza todo junto

- **WHEN** la odontóloga pide, en peticiones separadas, `POST /usuarios` con `roles` vacío, con `["administrador"]`, con `["recepcionista", "recepcionista"]`, con los emails `sin-arroba`, `a@`, `@b` y `a b@c.test` (D245), con un email válido de 255 caracteres (tope de 254, D245), o con un campo `activo` de más
- **THEN** cada petición recibe `422` con `codigos` vacío y un error del campo con problemas, y no se crea ningún usuario
- **AND** un alta por lo demás igual con un email válido de exactamente 254 caracteres recibe `201`
- **AND** una petición con el email `sin-arroba` y `roles` vacío a la vez recibe un solo `422` con `codigos` vacío y **dos** errores, uno del campo `email` y otro del campo `roles` (RN-GL-02)

#### Scenario: US-093 CA-1 Borde - sin sesión se responde 401 antes que la entrada

- **WHEN** se pide `POST /usuarios` sin la cabecera `Authorization` y con `roles` vacío
- **THEN** el sistema responde el `401` de sesión inválida, con `codigos` `["RN-AU-03"]`, y no `422` (D208)
- **AND** no se crea ningún usuario

#### Scenario: US-093 CA-8 Borde - asignar odontologo no crea un profesional

- **GIVEN** el consultorio con su único profesional, vinculado a la odontóloga
- **WHEN** la odontóloga crea `colega@consultorio-demo.test` con `roles` `["odontologo"]`
- **THEN** el sistema responde `201`
- **AND** el consultorio sigue con un solo profesional, vinculado a la odontóloga

### Requirement: La contraseña inicial tiene de 10 caracteres a 72 bytes

La contraseña inicial SHALL tener al menos 10 caracteres y como máximo 72 bytes en UTF-8, sin recortarla (RN-AU-07, D74; US-093 CA-9 en su parte de la contraseña inicial, que C-09 cubre por D242). Fuera de ese rango, `POST /usuarios` SHALL responder `422` con `codigos` `["RN-AU-07"]` y un error del campo `contrasena`, como validación de entrada (RN-GL-02), y MUST NOT crear el usuario. Esta validación corre después de la validación de formato: si el cuerpo tiene errores de formato, el `422` informa solo esos (D242; precedente D177).

#### Scenario: US-093 CA-9 Error de negocio - una contraseña inicial de 9 caracteres se rechaza

- **WHEN** la odontóloga pide `POST /usuarios` con la contraseña `corta-123` (9 caracteres)
- **THEN** el sistema responde `422` con `codigos` `["RN-AU-07"]` y un error del campo `contrasena` con el código `RN-AU-07`
- **AND** no se crea ningún usuario

#### Scenario: US-093 CA-9 Borde - 10 caracteres y 72 bytes se aceptan; 73 bytes no

- **WHEN** la odontóloga crea un usuario con una contraseña de exactamente 10 caracteres, otro con una de exactamente 72 bytes, y pide un tercero con una de 37 caracteres que ocupan 73 bytes (con letras con tilde)
- **THEN** los dos primeros reciben `201`
- **AND** el tercero recibe `422` con `codigos` `["RN-AU-07"]` y no se crea

#### Scenario: US-093 CA-9 Borde - el formato se informa antes que el largo de la contraseña

- **WHEN** la odontóloga pide `POST /usuarios` con el email `sin-arroba`, la contraseña `corta-123` (9 caracteres) y `roles` `["recepcionista"]`
- **THEN** el sistema responde `422` con `codigos` vacío y un solo error, del campo `email`, sin ningún error del campo `contrasena` ni el código `RN-AU-07` (D242, D177)
- **AND** no se crea ningún usuario

### Requirement: El email de un usuario es único

El email SHALL ser único en la instalación, comparado ya normalizado (D199). Un alta con un email que ya usa otro usuario, activo o inactivo, SHALL rechazarse con `409` y `codigos` `["RN-AU-08"]` (RN-AU-08, D243), como regla de negocio evaluada después de la validación de entrada, sin crear nada (US-093 CA-2). Dos altas simultáneas con el mismo email MUST NOT terminar en un `500`: la restricción `UNIQUE` de la base se traduce al mismo `409`.

#### Scenario: US-093 CA-2 Error de negocio - un email repetido con otras mayúsculas se rechaza

- **WHEN** la odontóloga pide `POST /usuarios` con el email ` RECEPCION@consultorio-demo.test` y una contraseña válida
- **THEN** el sistema responde `409` con `codigos` `["RN-AU-08"]`
- **AND** sigue habiendo un solo usuario con ese email

#### Scenario: US-093 CA-2 Borde - el email de un usuario inactivo sigue ocupado

- **GIVEN** `administracion@consultorio-demo.test` inactivo
- **WHEN** la odontóloga pide crear otro usuario con ese email
- **THEN** el sistema responde `409` con `codigos` `["RN-AU-08"]`

#### Scenario: US-093 CA-2 Borde - con email repetido y contraseña corta se informa la entrada

- **WHEN** la odontóloga pide crear un usuario con el email de la recepcionista y la contraseña `corta-123`
- **THEN** el sistema responde `422` con `codigos` `["RN-AU-07"]` y no `409`

#### Scenario: US-093 CA-2 Borde - dos altas simultáneas con el mismo email

- **GIVEN** en PostgreSQL, ningún usuario con el email `turnos@consultorio-demo.test`
- **WHEN** dos altas con ese email llegan a la vez y la segunda inserta mientras la primera todavía no confirmó (arnés de carrera)
- **THEN** la primera crea el usuario y la segunda recibe `409` con `codigos` `["RN-AU-08"]`, no un `500`
- **AND** queda exactamente un usuario con ese email
- **AND** este escenario se verifica en el perfil opcional con PostgreSQL

### Requirement: Asignar y quitar roles

`PATCH /usuarios/{id}` con `roles` SHALL reemplazar el conjunto de roles del usuario por el pedido (al menos uno, sin repetir) y responder `200` con el usuario. El cambio SHALL valer desde la petición siguiente del usuario, con el mismo token, y MUST NOT cambiar su `token_version` (RN-AU-02, D102). Los roles de un usuario inactivo también se pueden cambiar: sigue inactivo y su `token_version` no cambia (D253). Si el pedido trae `roles` y `activo` a la vez, las reglas de RN-AU-06 SHALL evaluarse sobre el resultado combinado y se aplican las dos partes o ninguna (D252). Un `PATCH` con `{}` SHALL responder `200` sin cambiar nada. Solo `odontologo` puede editar; un `id` inexistente SHALL responder `404` con `codigos` `["RN-GL-04"]`, después del control de acceso y de la validación de entrada (D208, RN-GL-02).

#### Scenario: US-093 CA-1 Feliz - la odontóloga suma el rol dueno a la recepcionista

- **GIVEN** un access token vigente de la recepcionista, que recibe el `403` de permiso insuficiente en `GET /usuarios`
- **WHEN** la odontóloga pide `PATCH /usuarios/2` con su token y `{"roles": ["recepcionista", "dueno"]}`
- **THEN** el sistema responde `200` con `roles` `["recepcionista", "dueno"]`
- **AND** con el mismo token de antes, la recepcionista recibe `200` en `GET /usuarios`, y su `token_version` no cambió

#### Scenario: US-093 CA-8 Borde - pasar a odontologo a otro usuario no crea un profesional

- **WHEN** la odontóloga pide `PATCH /usuarios/2` con `{"roles": ["odontologo"]}`
- **THEN** el sistema responde `200`
- **AND** el consultorio sigue con un solo profesional, vinculado a la odontóloga

#### Scenario: US-093 CA-1 Error de negocio - el dueño no puede cambiar roles

- **WHEN** el dueño pide `PATCH /usuarios/2` con `{"roles": ["dueno"]}`, y también `PATCH /usuarios/999`
- **THEN** las dos peticiones reciben `403` con `codigos` `["RN-AU-05"]`, no `200` ni `404`, y los roles no cambian

#### Scenario: US-093 CA-1 Borde - un usuario inexistente o un cuerpo inválido

- **WHEN** la odontóloga pide `PATCH /usuarios/999` con `{"roles": ["dueno"]}`, y `PATCH /usuarios/2` con `{"roles": []}`, con `{"email": "otro@consultorio-demo.test"}` o con `{"activo": null}`
- **THEN** la primera recibe `404` con `codigos` `["RN-GL-04"]`
- **AND** las otras reciben `422` con `codigos` vacío, y nada cambia

#### Scenario: US-093 CA-1 Borde - la entrada se evalúa antes que el usuario de la URL

- **WHEN** la odontóloga pide `PATCH /usuarios/999` con `{"roles": []}`
- **THEN** el sistema responde `422` con `codigos` vacío y no `404` (RN-GL-02)

#### Scenario: US-093 CA-1 Borde - un PATCH vacío no cambia nada

- **WHEN** la odontóloga pide `PATCH /usuarios/2` con `{}`
- **THEN** el sistema responde `200` con la recepcionista como estaba: `roles` `["recepcionista"]` y `activo` verdadero
- **AND** su `token_version` no cambió

#### Scenario: US-093 CA-1 Borde - se cambian los roles de un usuario inactivo

- **GIVEN** `administracion@consultorio-demo.test` inactivo, con `dueno` y `token_version` 1
- **WHEN** la odontóloga pide `PATCH` de ese usuario con `{"roles": ["recepcionista"]}`
- **THEN** el sistema responde `200` con `roles` `["recepcionista"]` y `activo` falso
- **AND** su `token_version` sigue en 1 y sigue sin poder iniciar sesión

### Requirement: Desactivar a un usuario corta su acceso de inmediato

`PATCH /usuarios/{id}` con `{"activo": false}` SHALL dejar al usuario inactivo e incrementar su `token_version` en uno, así todo token emitido antes recibe el `401` de sesión inválida y el usuario no inicia sesión (RN-AU-03, RN-AU-04, D43). El usuario MUST NOT borrarse: sigue en la lista. Con `{"activo": true}` SHALL reactivarse sin cambiar `token_version`. Pedir el estado que ya tiene MUST NOT cambiar nada.

#### Scenario: US-093 CA-3 Feliz - desactivar a la recepcionista corta su sesión

- **GIVEN** un access token y un refresh token vigentes de la recepcionista, con `token_version` 0
- **WHEN** la odontóloga pide `PATCH /usuarios/2` con su token y `{"activo": false}`
- **THEN** el sistema responde `200` con `activo` falso, y la `token_version` de la recepcionista es 1
- **AND** el access token anterior recibe el `401` de sesión inválida en `GET /prestaciones`, el refresh anterior recibe `401` en `POST /auth/refresh` y `POST /auth/login` con su contraseña responde `401`
- **AND** `GET /usuarios` la sigue mostrando, inactiva

#### Scenario: US-093 CA-3 Borde - reactivar no revive los tokens anteriores

- **GIVEN** la recepcionista desactivada después de emitir un access token con `token_version` 0
- **WHEN** la odontóloga pide `PATCH /usuarios/2` con `{"activo": true}`
- **THEN** el sistema responde `200` con `activo` verdadero y la `token_version` sigue en 1
- **AND** el access token anterior sigue recibiendo el `401` de sesión inválida, y un inicio de sesión nuevo responde `200`

#### Scenario: US-093 CA-3 Borde - desactivar a quien ya está inactivo no cambia nada

- **GIVEN** `administracion@consultorio-demo.test` inactivo con `token_version` 1
- **WHEN** la odontóloga pide `PATCH` de ese usuario con `{"activo": false}`
- **THEN** el sistema responde `200` y la `token_version` sigue en 1

### Requirement: Nadie se desactiva a sí mismo

Un usuario MUST NOT desactivarse a sí mismo: `PATCH /usuarios/{id}` con `{"activo": false}` sobre el usuario del token SHALL responder `409` con `codigos` `["RN-AU-06"]` y no cambiar nada, aunque haya otros odontólogos activos (RN-AU-06, D44; US-093 CA-5). Es una regla de negocio: se evalúa después del control de acceso, de la validación de entrada y del `404`.

#### Scenario: US-093 CA-5 Error de negocio - la odontóloga no puede desactivarse

- **GIVEN** la odontóloga y otro odontólogo activo, `colega@consultorio-demo.test`
- **WHEN** la odontóloga pide `PATCH /usuarios/1` con su token y `{"activo": false}`
- **THEN** el sistema responde `409` con `codigos` `["RN-AU-06"]`
- **AND** la odontóloga sigue activa, con la misma `token_version`, y su token sigue sirviendo

#### Scenario: US-093 CA-5 Borde - el permiso y la entrada se evalúan antes

- **WHEN** la recepcionista pide `PATCH /usuarios/2` con su token y `{"activo": false}`, y la odontóloga pide `PATCH /usuarios/1` con `{"activo": false, "roles": []}`
- **THEN** la primera recibe `403` con `codigos` `["RN-AU-05"]` y la segunda `422` con `codigos` vacío, no `409`

#### Scenario: US-093 CA-5 Borde - roles y activo en el mismo pedido no cambian nada si se rechaza

- **GIVEN** la odontóloga es el único odontólogo activo
- **WHEN** pide `PATCH /usuarios/1` con su token y `{"roles": ["dueno"], "activo": false}`
- **THEN** el sistema responde `409` con `codigos` `["RN-AU-06"]` y el `detail` «Nadie puede desactivarse a sí mismo.»: de las dos causas de RN-AU-06 que fallan, gana la de desactivarse a sí mismo (design U13)
- **AND** sigue activa, con `odontologo` y `dueno` y la misma `token_version`: no se aplicó ninguna de las dos partes (D252)

### Requirement: El consultorio no se queda sin odontólogo activo

El sistema MUST NOT dejar al consultorio sin un odontólogo activo: quitar el rol `odontologo` o desactivar al último odontólogo activo SHALL responder `409` con `codigos` `["RN-AU-06"]` sin cambiar nada (RN-AU-06, D44; US-093 CA-4). Un odontólogo inactivo no cuenta. En PostgreSQL, dos pedidos simultáneos MUST NOT poder dejar al consultorio sin odontólogo activo. Por la API, en un pedido solo, «desactivar al último odontólogo activo» únicamente se alcanza sobre uno mismo, donde gana «nadie se desactiva a sí mismo»: esa mitad de US-093 CA-4 se verifica en el dominio (con la cuenta de odontólogos activos) y en el perfil `postgres` (la carrera), no en la suite de la API (design U10).

#### Scenario: US-093 CA-4 Error de negocio - la única odontóloga no puede quitarse el rol odontologo

- **GIVEN** la odontóloga es el único odontólogo activo
- **WHEN** pide `PATCH /usuarios/1` con su token y `{"roles": ["dueno"]}`
- **THEN** el sistema responde `409` con `codigos` `["RN-AU-06"]`
- **AND** sigue con `odontologo` y `dueno`

#### Scenario: US-093 CA-4 Borde - un odontólogo inactivo no cuenta

- **GIVEN** `colega@consultorio-demo.test` con el rol `odontologo`, inactivo
- **WHEN** la odontóloga pide `PATCH /usuarios/1` con `{"roles": ["dueno"]}`
- **THEN** el sistema responde `409` con `codigos` `["RN-AU-06"]`

#### Scenario: US-093 CA-4 Feliz - con otro odontólogo activo la odontóloga deja su rol

- **GIVEN** `colega@consultorio-demo.test` con el rol `odontologo`, activo
- **WHEN** la odontóloga pide `PATCH /usuarios/1` con `{"roles": ["dueno"]}`
- **THEN** el sistema responde `200` con `roles` `["dueno"]`
- **AND** con el mismo token, su `POST /usuarios` siguiente recibe `403` con `codigos` `["RN-AU-05"]`

#### Scenario: US-093 CA-4 Borde - roles y activo de otro odontólogo en el mismo pedido se aplican juntos

- **GIVEN** la odontóloga y `colega@consultorio-demo.test` (rol `odontologo`, activa, `token_version` 0) son los odontólogos activos
- **WHEN** la odontóloga pide `PATCH` de la colega con su token y `{"roles": ["dueno"], "activo": false}`
- **THEN** el sistema responde `200` con `roles` `["dueno"]` y `activo` falso: se aplicaron las dos partes (D252)
- **AND** la `token_version` de la colega es 1 y queda un odontólogo activo, la odontóloga

#### Scenario: US-093 CA-4 Borde - dos odontólogos no se desactivan a la vez uno al otro

- **GIVEN** en PostgreSQL, la odontóloga y `colega@consultorio-demo.test` son los únicos odontólogos activos
- **WHEN** las dos peticiones ya pasaron el control de acceso y, al mismo tiempo, la odontóloga pide desactivar a la colega y la colega pide desactivar a la odontóloga; la primera toma el bloqueo y todavía no confirmó cuando la segunda llega (arnés de carrera)
- **THEN** la primera recibe `200` y la segunda espera el bloqueo y, al continuar, recibe `409` con `codigos` `["RN-AU-06"]` sin cambiar nada
- **AND** queda exactamente un odontólogo activo
- **AND** este escenario se verifica en el perfil opcional con PostgreSQL
