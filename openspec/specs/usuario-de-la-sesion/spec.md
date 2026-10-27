# usuario-de-la-sesion Specification

## Purpose
Define la ruta de la API que informa quién es el usuario del access token: su email y sus roles, leídos de la base en cada petición, sin ningún dato interno de la cuenta, para los tres roles del panel y con los mismos rechazos `401` y `403` que el resto de las rutas protegidas (RN-AU-01, RN-AU-02, RN-AU-03, RN-AU-04, RN-AU-05).

Convenciones de los escenarios: todos los instantes están en **UTC**. «Con el token de X» significa con la cabecera `Authorization: Bearer <access token>` de un access token vigente emitido para X por `POST /auth/login` (capability `sesion-del-panel`). «El `401` de sesión inválida» es la respuesta fija de `proteccion-del-panel`: `401` con `codigos` `["RN-AU-03"]`, texto fijo y `WWW-Authenticate: Bearer` (D206); «el `403` de permiso insuficiente» es su `403` con `codigos` `["RN-AU-05"]` (D207). Un error sale como `application/problem+json` con `codigos`. Los usuarios de los ejemplos son ficticios y del único consultorio de la instalación (D173): «la odontóloga» es `odontologa@consultorio-demo.test` (id 1, activa, `odontologo` + `dueno`), «la recepcionista» es `recepcion@consultorio-demo.test` (id 2, activa, `recepcionista`), «el dueño» es `administracion@consultorio-demo.test`, activo y con solo `dueno`, «la colega» es `colega@consultorio-demo.test`, activa, creada por la odontóloga con `POST /usuarios`, y «el usuario sin roles» es `sin-roles@consultorio-demo.test`, activo y sin ningún rol (la API no lo crea, pero la base lo admite; se arma en el test). El nombre de la ruta, los campos de la respuesta y el permiso son decisiones del autor (D305 a D307). Cada escenario tiene un ID propio (`SES-1a`, `SES-1b`…) que lleva el nombre de su test; el número es el escenario mínimo de `CHANGES.md` que cubre. Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite por defecto.

## Requirements

### Requirement: El usuario del token obtiene su email y sus roles

`GET /auth/yo` con el access token de un usuario con al menos un rol SHALL responder `200` con su `email`, tal como está guardado (normalizado, D199), y sus `roles` como lista de textos en el orden fijo `odontologo`, `recepcionista`, `dueno` (D306), sin importar el orden en que se asignaron. Los roles SHALL leerse de la base en la misma petición, así un rol asignado o quitado se ve en la petición siguiente sin iniciar sesión otra vez (RN-AU-02, D102). La ruta no recibe cuerpo ni parámetros y MUST NOT cambiar nada.

#### Scenario: SES-1a Feliz - la odontóloga obtiene su email y sus roles

- **GIVEN** la odontóloga inició sesión con ` Odontologa@Consultorio-Demo.TEST ` y su contraseña
- **WHEN** pide `GET /auth/yo` con su token
- **THEN** el sistema responde `200` con el cuerpo exacto `{"email": "odontologa@consultorio-demo.test", "roles": ["odontologo", "dueno"]}`
- **AND** su `token_version` y sus roles quedan como estaban

#### Scenario: SES-1b Feliz - la recepcionista y el dueño obtienen los suyos

- **WHEN** la recepcionista pide `GET /auth/yo` con su token, y el dueño pide lo mismo con el suyo
- **THEN** la primera respuesta es `200` con `{"email": "recepcion@consultorio-demo.test", "roles": ["recepcionista"]}`
- **AND** la segunda es `200` con `{"email": "administracion@consultorio-demo.test", "roles": ["dueno"]}`

#### Scenario: SES-1c Borde - un rol cambiado se ve en la petición siguiente

- **GIVEN** la recepcionista inició sesión y `GET /auth/yo` con su token responde `roles` `["recepcionista"]`
- **WHEN** la odontóloga le suma `dueno` con `PATCH /usuarios/2` y la recepcionista vuelve a pedir `GET /auth/yo` con el **mismo** token
- **THEN** el sistema responde `200` con `roles` `["recepcionista", "dueno"]`, sin un inicio de sesión nuevo
- **AND** después de que la odontóloga le quita `dueno`, la misma petición responde otra vez `["recepcionista"]`

#### Scenario: SES-1d Borde - los roles salen en el orden fijo aunque se hayan asignado en otro

- **GIVEN** la odontóloga creó a la colega con `POST /usuarios` y los roles `["dueno"]`, y después le sumó `odontologo` con `PATCH /usuarios/{id}` y `{"roles": ["dueno", "odontologo"]}`
- **WHEN** la colega inicia sesión y pide `GET /auth/yo` con su token
- **THEN** el sistema responde `200` con `roles` `["odontologo", "dueno"]` (el orden fijo de la API, no el de alta)

### Requirement: La respuesta no expone datos internos ni se guarda en caché

La respuesta de `GET /auth/yo` SHALL tener solo los campos `email` y `roles` (D306): MUST NOT incluir el hash de la contraseña, `token_version`, `activo`, el id del usuario, `consultorio_id`, la fecha de alta ni el token, porque la autorización la decide el servidor con lo que lee de la base y no con lo que la interfaz recibe (RN-AU-02). SHALL llevar `Cache-Control: no-store`, como las respuestas de `/auth/login` y `/auth/refresh`.

#### Scenario: SES-2a Borde - la respuesta trae solo el email y los roles, sin caché

- **WHEN** la odontóloga pide `GET /auth/yo` con su token
- **THEN** el cuerpo de la respuesta tiene exactamente las claves `email` y `roles`, y ningún valor del cuerpo contiene el hash guardado de su contraseña ni su access token
- **AND** la respuesta lleva la cabecera `Cache-Control: no-store`
- **AND** la documentación de la API describe la respuesta `200` con esos dos campos y ningún otro

### Requirement: Sin sesión válida responde el 401 de sesión inválida

`GET /auth/yo` SHALL responder el `401` de sesión inválida (`RN-AU-03`, D206) a toda petición sin un access token que sirva: sin cabecera `Authorization`, con otro esquema, con un token ilegible o mal firmado, con un refresh token en lugar del access, con un access vencido, de un usuario inactivo (RN-AU-04) o con una `token_version` vieja (RN-AU-03). La respuesta SHALL ser la misma en todos los casos y MUST NOT informar si el usuario existe ni cuál fue la causa.

#### Scenario: SES-3a Error de negocio - sin la cabecera Authorization se responde 401

- **WHEN** se pide `GET /auth/yo` sin la cabecera `Authorization`
- **THEN** el sistema responde el `401` de sesión inválida con `codigos` `["RN-AU-03"]`, sin el email de nadie

#### Scenario: SES-3b Error de negocio - con otro esquema de autorización se responde 401

- **WHEN** se pide `GET /auth/yo` con `Authorization: Basic` y un valor cualquiera (`dXN1YXJpbzp4`)
- **THEN** el sistema responde el `401` de sesión inválida con `codigos` `["RN-AU-03"]`, con el mismo cuerpo que en `SES-3a`

#### Scenario: SES-3c Error de negocio - un token ilegible se responde 401

- **WHEN** se pide `GET /auth/yo` con `Authorization: Bearer no-es-un-jwt`
- **THEN** el sistema responde el `401` de sesión inválida con `codigos` `["RN-AU-03"]`, con el mismo cuerpo que en `SES-3a`

#### Scenario: SES-3d Error de negocio - el refresh token usado como access se responde 401

- **GIVEN** la odontóloga inició sesión y tiene su access y su refresh
- **WHEN** pide `GET /auth/yo` con su refresh token como Bearer
- **THEN** el sistema responde el `401` de sesión inválida con `codigos` `["RN-AU-03"]`, con el mismo cuerpo que en `SES-3a` y sin su email

#### Scenario: SES-3e Error de negocio - un access vencido se responde 401

- **GIVEN** la odontóloga inició sesión a las 12:00 y su access vence a las 12:15
- **WHEN** pide `GET /auth/yo` con ese access cuando el reloj marca 12:15
- **THEN** el sistema responde el `401` de sesión inválida con `codigos` `["RN-AU-03"]`, con el mismo cuerpo que en `SES-3a` y sin su email

#### Scenario: SES-3f Borde - un usuario desactivado recibe 401

- **GIVEN** el dueño inició sesión y `GET /auth/yo` con su token responde `200`
- **WHEN** la odontóloga lo desactiva con `PATCH` y `{"activo": false}`, y el dueño vuelve a pedir `GET /auth/yo` con el mismo token
- **THEN** el sistema responde el `401` de sesión inválida (RN-AU-04), sin su email

#### Scenario: SES-3g Borde - restablecer la contraseña corta todas las sesiones y el inicio de sesión nuevo vuelve a servir

- **GIVEN** la recepcionista tiene dos sesiones abiertas, A y B
- **WHEN** la odontóloga restablece su contraseña con `POST /usuarios/2/restablecer-contrasena` y `{"contrasena": "clave-nueva-2026"}`
- **THEN** `GET /auth/yo` con el access de la sesión A y con el de la sesión B recibe el `401` de sesión inválida (`token_version` vieja, RN-AU-03)
- **AND** después de un inicio de sesión nuevo de la recepcionista con `clave-nueva-2026`, `GET /auth/yo` con su token nuevo responde `200` con su email

### Requirement: Un usuario sin roles recibe 403

`GET /auth/yo` SHALL exigir el permiso de leer la propia sesión, `sesion.leer`, que tienen los tres roles (D307; matriz de `03`). Un usuario activo con un token válido y **sin ningún rol** SHALL recibir el `403` de permiso insuficiente (`RN-AU-05`), como en el resto de las rutas del panel; el control de acceso va antes que cualquier otra cosa (D208).

#### Scenario: SES-3h Error de negocio - un usuario sin roles no obtiene su usuario

- **GIVEN** el usuario sin roles inició sesión y tiene un access vigente
- **WHEN** pide `GET /auth/yo` con su token
- **THEN** el sistema responde `403` con `codigos` `["RN-AU-05"]`, sin su email ni sus roles en el cuerpo
- **AND** su sesión sigue: su `token_version` no cambia
