# proteccion-del-panel Specification

## Purpose

Define quién puede usar cada ruta del panel: los roles del usuario y la unión de sus permisos, el access token que cada petición del panel debe presentar, el `401` sin sesión válida, el `403` con rol insuficiente, la lista cerrada de rutas públicas y el registro del usuario que crea un turno (RN-AU-01, RN-AU-02, RN-AU-03, RN-AU-04, RN-AU-05; US-091, US-092).

Convenciones de los escenarios: todos los instantes están en **UTC**; «el reloj marca 12:00» significa que el reloj del sistema devuelve `2026-10-07T12:00:00Z`, y los turnos son del día 2026-11-02 («10:00» es `2026-11-02T10:00:00Z`). «Con el token de X» significa con la cabecera `Authorization: Bearer <access token>` de un access token vigente emitido para X por `POST /auth/login` (capability `sesion-del-panel`). «El `401` de sesión inválida» es siempre la misma respuesta: estado `401`, `codigos` `["RN-AU-03"]`, el mismo `type`, `title` y `detail`, y la cabecera `WWW-Authenticate: Bearer` (D206). «El `403` de permiso insuficiente» es siempre la misma respuesta: estado `403`, `codigos` `["RN-AU-05"]`, el mismo `type`, `title` y `detail` (D207). Un error sale como `application/problem+json`. Los usuarios de los ejemplos son ficticios: `odontologa@consultorio-demo.test` con `odontologo` + `dueno`, «la recepcionista» con solo `recepcionista`, «el dueño» con solo `dueno`. Las demás capabilities (`creacion-de-turnos`, `historial-de-turnos`, `gestion-de-prestaciones`, `gestion-de-sillones`) describen sus rutas para un usuario con permiso. Hay un solo consultorio por instalación (D173). Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite por defecto, salvo que digan otra cosa.

## Requirements

### Requirement: Cada usuario del panel tiene uno o más roles

El sistema SHALL guardar los roles de cada usuario del panel; los únicos roles válidos son `odontologo`, `recepcionista` y `dueno`, y un usuario MUST NOT tener el mismo rol dos veces (RN-AU-05, D213). Un usuario sin roles existe, pero no tiene ningún permiso. La instalación de demostración SHALL traer a `odontologa@consultorio-demo.test` con `odontologo` y `dueno`, vinculada al profesional de demostración (D46, D202), y a una recepcionista ficticia con solo `recepcionista` (D212).

#### Scenario: US-091 CA-4 Feliz - el usuario del seed tiene sus dos roles y su profesional

- **GIVEN** una base recién sembrada con los datos de demostración
- **WHEN** se leen los roles de `odontologa@consultorio-demo.test` y el profesional de demostración
- **THEN** el usuario tiene exactamente los roles `odontologo` y `dueno`
- **AND** el profesional de demostración está vinculado a ese usuario

#### Scenario: US-091 CA-1 Borde - un rol que no existe no se guarda

- **GIVEN** un usuario del panel
- **WHEN** se intenta guardarle el rol `administrador`, o el rol `odontologo` dos veces
- **THEN** el sistema lo rechaza y los roles del usuario no cambian

#### Scenario: US-091 CA-4 Borde - un volumen sembrado antes de este change recibe los roles

- **GIVEN** una base PostgreSQL migrada que ya tiene el consultorio, el profesional y el usuario de demostración, pero ningún rol ni vínculo
- **WHEN** se ejecuta la carga del seed
- **THEN** el usuario de demostración queda con `odontologo` y `dueno`, el profesional queda vinculado a él y ningún otro dato se duplica
- **AND** volver a ejecutar la carga no cambia nada
- **AND** este escenario se verifica en el perfil opcional con PostgreSQL

### Requirement: Las rutas del panel exigen un access token válido

Toda ruta del panel SHALL exigir la cabecera `Authorization: Bearer` con un access token firmado con HS256 por la instalación, de tipo `access` y vigente según el reloj del sistema (RN-AU-01, RN-AU-03). Si falta, tiene otro esquema, no se puede leer, venció o es un refresh token, SHALL responder el `401` de sesión inválida, sin revelar la causa, y MUST NOT ejecutar la operación.

#### Scenario: US-092 CA-1 Error de negocio - una ruta del panel sin token responde 401

- **GIVEN** un profesional, un sillón y una prestación activos, y un paciente existente
- **WHEN** se pide `POST /turnos` sin la cabecera `Authorization`
- **THEN** el sistema responde el `401` de sesión inválida
- **AND** no se crea ningún turno ni ningún evento del historial

#### Scenario: US-092 CA-1 Error de negocio - un access token vencido responde 401

- **GIVEN** un access token de `odontologa@consultorio-demo.test` emitido a las 12:00, y el reloj marca 12:15 del mismo día
- **WHEN** se pide `GET /prestaciones` con ese token
- **THEN** el sistema responde el `401` de sesión inválida

#### Scenario: US-092 CA-1 Borde - un segundo antes de vencer el access token sigue sirviendo

- **GIVEN** un access token de `odontologa@consultorio-demo.test` emitido a las 12:00, y el reloj marca 12:14:59 del mismo día
- **WHEN** se pide `GET /prestaciones` con ese token
- **THEN** el sistema responde `200`

#### Scenario: US-092 CA-1 Borde - un refresh token, un token alterado o otro esquema no sirven

- **WHEN** se pide `GET /prestaciones` con un refresh token vigente de `odontologa@consultorio-demo.test`, con un access token firmado con otro secreto o con un carácter cambiado, con un texto que no es un JWT, o con la cabecera `Authorization: Basic` en lugar de `Bearer`
- **THEN** cada petición recibe el mismo `401` de sesión inválida

#### Scenario: US-092 CA-1 Borde - sin sesión no se revela si el recurso existe ni si la petición es válida

- **WHEN** se pide sin token `GET /turnos/999/historial` (un turno que no existe), o `POST /turnos` con un cuerpo con una prestación inexistente
- **THEN** las dos peticiones reciben el `401` de sesión inválida, no un `404` ni un `422`

### Requirement: El token de un usuario inactivo o con otra versión responde 401

Aunque el access token esté vigente y bien firmado, el sistema SHALL responder el `401` de sesión inválida si su usuario ya no existe, tiene `activo` falso o su `token_version` actual es distinta de la del token (RN-AU-03, RN-AU-04, D43). Las dos condiciones SHALL leerse de la base en cada petición.

#### Scenario: US-092 CA-4 Error de negocio - el usuario se desactivó después del inicio de sesión

- **GIVEN** un access token vigente de `odontologa@consultorio-demo.test`, y después el usuario pasa a `activo` falso
- **WHEN** se pide `GET /sillones` con ese token
- **THEN** el sistema responde el `401` de sesión inválida

#### Scenario: US-092 CA-4 Error de negocio - la token_version del usuario cambió

- **GIVEN** un access token vigente emitido con `token_version` 0, y después la `token_version` del usuario pasa a 1
- **WHEN** se pide `GET /sillones` con ese token
- **THEN** el sistema responde el `401` de sesión inválida

#### Scenario: US-092 CA-4 Borde - reactivar al usuario no revive el token anterior

- **GIVEN** un access token vigente emitido con `token_version` 0; después el usuario se desactiva con `token_version` 1 y se vuelve a activar
- **WHEN** se pide `GET /sillones` con ese token
- **THEN** el sistema responde el `401` de sesión inválida
- **AND** con un access token de un inicio de sesión nuevo (con `token_version` 1) responde `200`

### Requirement: Un rol insuficiente responde 403

Si el token es válido pero ninguno de los roles del usuario tiene el permiso que pide la ruta, el sistema SHALL responder el `403` de permiso insuficiente y MUST NOT ejecutar la operación ni modificar nada (RN-AU-05, US-091 CA-3). La autenticación SHALL evaluarse antes que la autorización, y la autorización antes que la validación del cuerpo y que la existencia del recurso de la URL (D208).

#### Scenario: US-091 CA-3 Error de negocio - el dueño no puede crear un turno

- **GIVEN** un profesional, un sillón y una prestación activos y libres a las 10:00, y un paciente existente
- **WHEN** se pide `POST /turnos` con el token del dueño, para ese paciente y esa prestación con `inicio` 10:00
- **THEN** el sistema responde el `403` de permiso insuficiente
- **AND** no se crea ningún turno ni ningún evento del historial

#### Scenario: US-091 CA-3 Error de negocio - la recepcionista no puede editar el catálogo

- **GIVEN** la prestación «Limpieza» activa de 45 minutos
- **WHEN** se pide `POST /prestaciones` o `PATCH` de esa prestación con el token de la recepcionista
- **THEN** cada petición recibe el `403` de permiso insuficiente
- **AND** el catálogo de prestaciones no cambia

#### Scenario: US-091 CA-3 Borde - un usuario sin roles no puede ni leer

- **GIVEN** un usuario activo sin ningún rol
- **WHEN** se pide `GET /prestaciones` con su token
- **THEN** el sistema responde el `403` de permiso insuficiente

#### Scenario: US-091 CA-3 Borde - el 403 va antes que el 422 y que el 404

- **WHEN** el dueño pide `POST /turnos` con una prestación inexistente en el cuerpo, o la recepcionista pide `PATCH /sillones/999` (un sillón que no existe)
- **THEN** las dos peticiones reciben el `403` de permiso insuficiente, no un `422` ni un `404`

### Requirement: Los permisos son la unión de los roles

Un usuario con varios roles SHALL tener todos los permisos de cada uno de sus roles: basta con que uno de ellos lo tenga (RN-AU-02, US-091 CA-1).

#### Scenario: US-091 CA-1 Feliz - la odontóloga con odontologo y dueno edita el catálogo y crea turnos

- **GIVEN** un profesional, un sillón y una prestación activos y libres a las 10:00, y un paciente existente
- **WHEN** `odontologa@consultorio-demo.test` pide con su token `POST /sillones` con nombre «Sillón 2» y `POST /turnos` para ese paciente y esa prestación con `inicio` 10:00
- **THEN** el sistema responde `201` a las dos

#### Scenario: US-091 CA-1 Borde - recepcionista más dueño suma los permisos de los dos

- **GIVEN** un usuario activo con los roles `recepcionista` y `dueno`, y un profesional, un sillón y una prestación activos y libres a las 10:00
- **WHEN** pide con su token `POST /turnos` con `inicio` 10:00 y `GET /turnos/{id}/historial` de ese turno
- **THEN** el sistema responde `201` y `200`, aunque el rol `dueno` solo no pueda crear turnos
- **AND** `POST /prestaciones` con el mismo token responde el `403` de permiso insuficiente, porque ninguno de sus dos roles lo permite

### Requirement: Los roles se leen de la base en cada petición

El sistema SHALL decidir los permisos con los roles que el usuario tiene en la base al momento de cada petición, no con los que tenía al iniciar sesión: quitar o asignar un rol SHALL tener efecto en la petición siguiente, con el mismo token y sin cambiar `token_version` (RN-AU-02, D102, US-091 CA-5).

#### Scenario: US-091 CA-5 Feliz - quitar un rol vale con el mismo token

- **GIVEN** un access token vigente de `odontologa@consultorio-demo.test`, con `odontologo` y `dueno`, y una prestación activa de 30 minutos, un profesional y un sillón libres a las 10:00
- **WHEN** se le quita el rol `odontologo` en la base y pide con el mismo token `POST /turnos` con `inicio` 10:00
- **THEN** el sistema responde el `403` de permiso insuficiente
- **AND** con el mismo token `GET /turnos/{id}/historial` de un turno existente sigue respondiendo `200`, porque `dueno` lo permite
- **AND** la `token_version` del usuario no cambió

#### Scenario: US-091 CA-5 Borde - asignar un rol vale con el mismo token

- **GIVEN** un access token vigente del dueño, que recibe `403` en `POST /turnos`
- **WHEN** se le asigna el rol `recepcionista` en la base y repite la misma petición con el mismo token
- **THEN** el sistema responde `201`

### Requirement: Cada ruta del panel exige el permiso de la matriz

Las rutas creadas antes de este change SHALL exigir, además del token válido, estos roles (matriz de `03_actores_y_roles.md`; US-092 CA-2): `POST /turnos`, `odontologo` o `recepcionista`; `GET /turnos/{id}/historial`, `GET /prestaciones` y `GET /sillones`, cualquiera de los tres; `POST` y `PATCH` de `/prestaciones` y de `/sillones`, solo `odontologo` (D205).

#### Scenario: US-092 CA-2 Feliz - con el rol que corresponde, cada ruta responde como antes

- **GIVEN** un profesional, un sillón y una prestación activos y libres a las 10:00, y un paciente existente
- **WHEN** la recepcionista pide con su token `POST /turnos` con `inicio` 10:00, y después cada uno de los tres usuarios de los ejemplos pide `GET /turnos/{id}/historial` de ese turno, `GET /prestaciones` y `GET /sillones`
- **THEN** `POST /turnos` responde `201` y cada lectura responde `200`, con el mismo contenido que sin protección

#### Scenario: US-092 CA-2 Error de negocio - sin el rol de la matriz cada escritura responde 403

- **GIVEN** una prestación y un sillón activos
- **WHEN** el dueño pide `POST /turnos`, `POST /prestaciones`, `PATCH` de la prestación, `POST /sillones` y `PATCH` del sillón, y la recepcionista pide las cuatro de catálogo
- **THEN** cada petición recibe el `403` de permiso insuficiente y nada cambia

#### Scenario: US-092 CA-2 Borde - el turno guarda quién lo creó

- **GIVEN** un profesional, un sillón y una prestación activos y libres a las 10:00, y un paciente existente
- **WHEN** la recepcionista pide con su token `POST /turnos` con `inicio` 10:00, y el sistema responde `201`
- **THEN** el turno queda guardado con la recepcionista como usuario que lo creó (D209)
- **AND** los turnos guardados antes de este change siguen sin usuario creador

### Requirement: Solo las rutas públicas se usan sin token

`POST /auth/login` y `POST /auth/refresh` SHALL seguir respondiendo sin la cabecera `Authorization` (`03`, «Rutas públicas»; RN-AU-01, US-092 CA-3). La documentación interactiva de la API (`/docs` y su esquema) SHALL seguir sin token (D214). Toda otra ruta de la API SHALL exigir el access token, también las que agreguen los changes siguientes.

#### Scenario: US-092 CA-3 Feliz - el inicio de sesión y la renovación siguen sin token

- **GIVEN** el usuario activo `odontologa@consultorio-demo.test`
- **WHEN** se pide `POST /auth/login` con sus credenciales y después `POST /auth/refresh` con el refresh token recibido, las dos sin la cabecera `Authorization`
- **THEN** el sistema responde `200` a las dos

#### Scenario: US-092 CA-3 Borde - ninguna ruta fuera de la lista pública queda sin protección

- **WHEN** se recorren todas las rutas de la API
- **THEN** toda ruta que no es `POST /auth/login`, `POST /auth/refresh` ni la documentación interactiva exige el access token
- **AND** la documentación de la API declara para cada ruta protegida el esquema de seguridad Bearer y las respuestas `401` y `403`
