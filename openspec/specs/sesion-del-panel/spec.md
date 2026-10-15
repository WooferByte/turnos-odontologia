# sesion-del-panel Specification

## Purpose

Define cómo un usuario del consultorio obtiene y renueva su sesión del panel: el usuario con su contraseña guardada como hash, el inicio de sesión con email y contraseña, la vida de los tokens, su renovación y el `401` genérico que no revela qué falló (RN-AU-01, RN-AU-03, RN-AU-04; US-090, US-094).

Convenciones de los escenarios: todos los instantes están en **UTC**; «el reloj marca 12:00» significa que el reloj del sistema devuelve `2026-10-07T12:00:00Z`. Los intervalos de vigencia son semiabiertos: un token emitido a las 12:00 con 15 minutos de vida sirve hasta antes de las 12:15 y a las 12:15 ya venció. Las operaciones son `POST /auth/login` y `POST /auth/refresh`, rutas públicas (`03`, «Rutas públicas»). Un error sale como `application/problem+json` con la lista `codigos`. «El `401` genérico de inicio de sesión» es siempre la misma respuesta: estado `401`, `codigos` `["RN-AU-04"]`, el mismo `type`, `title` y `detail`, y la cabecera `WWW-Authenticate: Bearer`. «El `401` de sesión inválida» es siempre la misma respuesta: estado `401`, `codigos` `["RN-AU-03"]`, el mismo `type`, `title` y `detail`, y la cabecera `WWW-Authenticate: Bearer`. Hay un solo consultorio por instalación (D173). Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite por defecto, salvo que digan otra cosa.

## Requirements

### Requirement: Usuario del panel con la contraseña protegida

El sistema SHALL guardar cada usuario del panel con su consultorio, su email, el hash bcrypt de su contraseña (nunca la contraseña en claro), su estado `activo` y su `token_version`, que empieza en 0 (RN-AU-03, RN-AU-07, SU-09). El email SHALL guardarse sin espacios en los extremos y en minúsculas, y MUST NOT haber dos usuarios con el mismo email así normalizado. La instalación de demostración SHALL traer un usuario ficticio activo.

#### Scenario: US-090 CA-4 Feliz - la contraseña del usuario del seed se guarda como hash bcrypt

- **GIVEN** una base recién sembrada con los datos de demostración
- **WHEN** se lee el usuario `odontologa@consultorio-demo.test`
- **THEN** está activo, pertenece al consultorio de demostración y su `token_version` es 0
- **AND** lo guardado en lugar de la contraseña es un hash bcrypt, distinto de la contraseña de demostración, que la verifica

#### Scenario: US-090 CA-4 Borde - el email es único sin distinguir mayúsculas ni espacios

- **GIVEN** un usuario con email `odontologa@consultorio-demo.test`
- **WHEN** se intenta guardar otro usuario con email ` Odontologa@Consultorio-Demo.TEST `
- **THEN** el sistema lo rechaza y queda un solo usuario con ese email

#### Scenario: US-090 CA-4 Borde - un volumen sembrado antes de este change recibe el usuario

- **GIVEN** una base PostgreSQL migrada que ya tiene el consultorio de demostración pero ningún usuario
- **WHEN** se ejecuta la carga del seed
- **THEN** el usuario de demostración queda creado y el resto de los datos no se duplica
- **AND** el siguiente usuario creado sin id explícito no choca con el id del usuario sembrado
- **AND** este escenario se verifica en el perfil opcional con PostgreSQL

### Requirement: Iniciar sesión con email y contraseña

Con credenciales válidas de un usuario activo, `POST /auth/login` SHALL responder `200` con un access token y un refresh token (RN-AU-01, RN-AU-03). Ambos SHALL ser JWT firmados con HS256 que identifican al usuario, dicen de qué tipo son y llevan su `token_version`. El access SHALL vencer a los 15 minutos y el refresh a los 7 días de emitidos, contados con el reloj del sistema (D74, SU-09). El email se compara normalizado.

#### Scenario: US-090 CA-1 Feliz - credenciales válidas devuelven access y refresh

- **GIVEN** el usuario activo `odontologa@consultorio-demo.test` con `token_version` 0, y el reloj marca 12:00
- **WHEN** se pide `POST /auth/login` con ese email y su contraseña
- **THEN** el sistema responde `200` con un access token, un refresh token, el tipo `bearer` y la vida del access en segundos (900)
- **AND** la respuesta no se guarda en cachés (`Cache-Control: no-store`)

#### Scenario: US-090 CA-4 Feliz - vida, firma y claims de los dos tokens

- **GIVEN** el inicio de sesión del escenario anterior, a las 12:00
- **WHEN** se leen los dos tokens con el secreto de la instalación
- **THEN** los dos están firmados con HS256, identifican al usuario y llevan `token_version` 0
- **AND** el access es de tipo `access` y vence a las 12:15; el refresh es de tipo `refresh` y vence a las 12:00 del 2026-10-14

#### Scenario: US-090 CA-1 Borde - el email con mayúsculas y espacios inicia sesión

- **WHEN** se pide `POST /auth/login` con email ` Odontologa@Consultorio-Demo.TEST ` y la contraseña correcta
- **THEN** el sistema responde `200` con los dos tokens

#### Scenario: US-090 CA-1 Error de formato - cuerpo incompleto o mal formado

- **WHEN** se pide `POST /auth/login` sin la contraseña, o con un campo de más, o con la contraseña vacía
- **THEN** el sistema responde `422` con `codigos` vacío y un error que nombra el campo
- **AND** no emite ningún token

### Requirement: Las credenciales inválidas responden un 401 genérico

Si el email no corresponde a ningún usuario o la contraseña no coincide, `POST /auth/login` SHALL responder el `401` genérico de inicio de sesión, sin distinguir cuál de los dos falló (RN-AU-04), y MUST NOT emitir ningún token. El usuario inexistente SHALL recibir la respuesta después de una comparación de contraseña de costo equivalente, para que el tiempo de respuesta no revele si el email existe.

#### Scenario: US-090 CA-2 Error de negocio - email inexistente

- **WHEN** se pide `POST /auth/login` con email `nadie@consultorio-demo.test` y cualquier contraseña
- **THEN** el sistema responde el `401` genérico de inicio de sesión

#### Scenario: US-090 CA-2 Error de negocio - contraseña incorrecta

- **GIVEN** el usuario activo `odontologa@consultorio-demo.test`
- **WHEN** se pide `POST /auth/login` con ese email y una contraseña distinta de la suya
- **THEN** el sistema responde el `401` genérico de inicio de sesión

#### Scenario: US-090 CA-2 Borde - las dos respuestas son idénticas

- **WHEN** se compara la respuesta del email inexistente con la de la contraseña incorrecta
- **THEN** tienen el mismo estado, las mismas cabeceras de autenticación y el mismo cuerpo
- **AND** en los dos casos se hizo una comparación de contraseña

#### Scenario: US-090 CA-2 Borde - una contraseña de más de 72 bytes no inicia sesión

- **GIVEN** el usuario activo `odontologa@consultorio-demo.test`
- **WHEN** se pide `POST /auth/login` con su email y una contraseña de 73 bytes cuyos primeros 72 coinciden con la suya
- **THEN** el sistema responde el `401` genérico de inicio de sesión, no un error del servidor

### Requirement: Un usuario inactivo no inicia sesión

Un usuario con `activo` falso MUST NOT iniciar sesión, aunque su contraseña sea correcta: `POST /auth/login` SHALL responder el mismo `401` genérico de inicio de sesión que ante credenciales inválidas (RN-AU-04, D43), sin revelar que la cuenta existe o está inactiva.

#### Scenario: US-090 CA-3 Error de negocio - usuario inactivo con la contraseña correcta

- **GIVEN** el usuario `recepcion@consultorio-demo.test` con `activo` falso
- **WHEN** se pide `POST /auth/login` con ese email y su contraseña correcta
- **THEN** el sistema responde el `401` genérico de inicio de sesión, idéntico al de una contraseña incorrecta
- **AND** no emite ningún token

#### Scenario: US-090 CA-3 Borde - el usuario inactivo con contraseña incorrecta recibe lo mismo

- **GIVEN** el mismo usuario inactivo
- **WHEN** se pide `POST /auth/login` con una contraseña incorrecta
- **THEN** el sistema responde el mismo `401` genérico de inicio de sesión

### Requirement: Renovar la sesión con el refresh token

`POST /auth/refresh` con un refresh token vigente de un usuario activo cuya `token_version` coincide con la del token SHALL responder `200` con un access token nuevo de 15 minutos desde el momento de la renovación (RN-AU-03, US-094). La renovación MUST NOT emitir un refresh token nuevo ni extender el vencimiento del que se usó.

#### Scenario: US-094 CA-1 Feliz - un refresh válido devuelve un access nuevo

- **GIVEN** un refresh token emitido a las 12:00 para el usuario activo `odontologa@consultorio-demo.test`, y el reloj marca 13:00 del mismo día
- **WHEN** se pide `POST /auth/refresh` con ese refresh token
- **THEN** el sistema responde `200` con un access token de tipo `access`, con la `token_version` actual del usuario, que vence a las 13:15, y la vida en segundos (900)
- **AND** la respuesta no trae refresh token

#### Scenario: US-094 CA-1 Borde - un segundo antes de vencer el refresh sigue sirviendo

- **GIVEN** un refresh token emitido el 2026-10-07 a las 12:00
- **WHEN** se pide `POST /auth/refresh` con el reloj en 2026-10-14 11:59:59
- **THEN** el sistema responde `200` con un access token nuevo

### Requirement: Un refresh token vencido o inválido responde 401

`POST /auth/refresh` SHALL responder el `401` de sesión inválida, sin emitir ningún token, si el token ya venció, no tiene la firma HS256 del secreto de la instalación, no es un JWT, le falta un dato obligatorio o es un access token (RN-AU-03, US-094 CA-2). La respuesta MUST NOT revelar cuál de esas causas fue.

#### Scenario: US-094 CA-2 Error de negocio - el refresh token venció

- **GIVEN** un refresh token emitido el 2026-10-07 a las 12:00
- **WHEN** se pide `POST /auth/refresh` con el reloj en 2026-10-14 12:00, el instante exacto del vencimiento
- **THEN** el sistema responde el `401` de sesión inválida

#### Scenario: US-094 CA-2 Error de negocio - firma de otro secreto o alterada

- **WHEN** se pide `POST /auth/refresh` con un refresh token firmado con otro secreto, o con uno válido al que se le cambió un carácter de la firma o del contenido
- **THEN** el sistema responde el `401` de sesión inválida

#### Scenario: US-094 CA-2 Borde - un access token no sirve como refresh

- **GIVEN** un access token vigente del usuario activo
- **WHEN** se pide `POST /auth/refresh` con ese access token
- **THEN** el sistema responde el `401` de sesión inválida

#### Scenario: US-094 CA-2 Borde - texto que no es un JWT o firmado sin algoritmo

- **WHEN** se pide `POST /auth/refresh` con un texto que no es un JWT, o con un token sin firma (algoritmo `none`), o firmado con un algoritmo distinto de HS256
- **THEN** el sistema responde el `401` de sesión inválida

#### Scenario: US-094 CA-2 Error de formato - cuerpo sin refresh token

- **WHEN** se pide `POST /auth/refresh` sin el refresh token, o con un refresh token vacío
- **THEN** el sistema responde `422` con `codigos` vacío y un error que nombra el campo

### Requirement: El refresh de un usuario inactivo o con otra versión de token responde 401

Aunque el refresh token no haya vencido y su firma sea válida, `POST /auth/refresh` SHALL responder el `401` de sesión inválida si el usuario ya no existe, tiene `activo` falso o su `token_version` actual es distinta de la del token (RN-AU-03, RN-AU-04, D43). Las dos condiciones SHALL leerse de la base en cada renovación.

#### Scenario: US-094 CA-3 Error de negocio - el usuario se desactivó después de iniciar sesión

- **GIVEN** un refresh token vigente de `odontologa@consultorio-demo.test`, y después el usuario pasa a `activo` falso
- **WHEN** se pide `POST /auth/refresh` con ese refresh token
- **THEN** el sistema responde el `401` de sesión inválida

#### Scenario: US-094 CA-3 Error de negocio - la token_version del usuario cambió

- **GIVEN** un refresh token vigente emitido con `token_version` 0, y después la `token_version` del usuario pasa a 1
- **WHEN** se pide `POST /auth/refresh` con ese refresh token
- **THEN** el sistema responde el `401` de sesión inválida

#### Scenario: US-094 CA-3 Borde - reactivar al usuario no revive los tokens anteriores

- **GIVEN** un refresh token vigente emitido con `token_version` 0; después el usuario se desactiva con `token_version` 1 y se vuelve a activar
- **WHEN** se pide `POST /auth/refresh` con ese refresh token
- **THEN** el sistema responde el `401` de sesión inválida
- **AND** un inicio de sesión nuevo emite tokens con `token_version` 1, que sí renuevan

#### Scenario: US-094 CA-3 Borde - el usuario del token no existe

- **WHEN** se pide `POST /auth/refresh` con un refresh token bien firmado y vigente de un id de usuario que no existe
- **THEN** el sistema responde el `401` de sesión inválida
