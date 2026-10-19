# ingreso-al-panel Specification

## Purpose
Define cómo una persona del consultorio entra al panel desde el navegador y se mantiene adentro: la pantalla de inicio de sesión y su mensaje genérico, dónde vive la sesión, la renovación ante un `401`, la vuelta al inicio de sesión, las rutas del panel protegidas y el cierre de sesión (RN-AU-01, RN-AU-03, RN-AU-04; US-090, US-092 CA-1). El contrato de la API que consume está en `sesion-del-panel` y `proteccion-del-panel`.

Convenciones de los escenarios: «la interfaz» es la aplicación web del panel servida en el navegador; habla con la API por el mismo origen. «La pantalla de inicio de sesión» es `/ingresar` y «el panel» es `/panel` y lo que cuelga de él. «El mensaje genérico» es siempre el mismo texto, «El email o la contraseña no son correctos.». «El aviso de sesión terminada» es «Tu sesión terminó. Iniciá sesión de nuevo.». «Una ruta del panel de la API» es cualquiera protegida por `proteccion-del-panel` (por ejemplo `GET /prestaciones`). El access token vive 15 minutos y el refresh 7 días (`sesion-del-panel`); los instantes de los ejemplos están en UTC: «el reloj marca 12:00» es `2026-10-07T12:00:00Z`. Los usuarios son ficticios: `odontologa@consultorio-demo.test` activa y `recepcion@consultorio-demo.test`, que en los escenarios de inactividad está inactiva (RN-PR-01). Los escenarios se verifican en la suite del frontend, con la API reemplazada por un servidor falso que respeta su contrato, y se repiten contra la API real en la prueba en el navegador.

## Requirements

### Requirement: Iniciar sesión desde la pantalla de inicio de sesión

La interfaz SHALL ofrecer una pantalla con email y contraseña que los envía a `POST /auth/login` (RN-AU-01). Con `200`, SHALL guardar la sesión y llevar a la persona al panel, o a la ruta del panel que había pedido. Mientras espera la respuesta MUST NOT permitir un segundo envío, y MUST NOT enviar nada si falta el email o la contraseña.

#### Scenario: US-090 CA-1 Feliz - credenciales válidas llevan al panel

- **GIVEN** la pantalla de inicio de sesión, sin sesión
- **WHEN** se ingresa `odontologa@consultorio-demo.test` con su contraseña y se pulsa «Ingresar»
- **THEN** la interfaz pide `POST /auth/login` una sola vez, con ese email y esa contraseña en el cuerpo
- **AND** muestra el panel en `/panel`, con el botón «Cerrar sesión»

#### Scenario: US-090 CA-1 Borde - vuelve a la ruta del panel que se había pedido

- **GIVEN** sin sesión, se abrió `/panel/algo` y la interfaz llevó a la pantalla de inicio de sesión
- **WHEN** se inicia sesión con credenciales válidas
- **THEN** la interfaz muestra `/panel/algo`, no `/panel`

#### Scenario: US-090 CA-1 Borde - campos vacíos no se envían

- **GIVEN** la pantalla de inicio de sesión
- **WHEN** se pulsa «Ingresar» con el email o la contraseña vacíos
- **THEN** la interfaz no hace ninguna petición a la API y sigue en la pantalla de inicio de sesión

#### Scenario: US-090 CA-1 Borde - un segundo clic mientras espera no manda otro login

- **GIVEN** un inicio de sesión enviado cuya respuesta todavía no llegó
- **WHEN** se vuelve a pulsar «Ingresar»
- **THEN** el botón está deshabilitado y la API recibió una sola petición de inicio de sesión

### Requirement: Las credenciales rechazadas muestran un mensaje genérico

Si `POST /auth/login` responde `401`, la interfaz SHALL mostrar el mensaje genérico, el mismo para email inexistente, contraseña incorrecta y usuario inactivo (RN-AU-04), MUST NOT guardar ninguna sesión ni entrar al panel, y SHALL vaciar la contraseña conservando el email. Una falla de conexión o un error del servidor SHALL mostrar otro mensaje, que no habla de las credenciales.

#### Scenario: US-090 CA-2 Error de negocio - email inexistente

- **WHEN** se inicia sesión con `nadie@consultorio-demo.test` y cualquier contraseña
- **THEN** la API responde `401` con `codigos` `["RN-AU-04"]`
- **AND** la interfaz muestra el mensaje genérico, sigue en la pantalla de inicio de sesión y no guardó ningún token

#### Scenario: US-090 CA-2 Error de negocio - contraseña incorrecta

- **WHEN** se inicia sesión con `odontologa@consultorio-demo.test` y una contraseña que no es la suya
- **THEN** la interfaz muestra el mensaje genérico, con el email todavía escrito y la contraseña vacía
- **AND** no guardó ningún token

#### Scenario: US-090 CA-2 Borde - los dos rechazos se ven idénticos

- **WHEN** se compara lo que muestra la interfaz tras un email inexistente con lo que muestra tras una contraseña incorrecta
- **THEN** el mensaje, su ubicación y el estado de la pantalla son los mismos

#### Scenario: US-090 CA-3 Error de negocio - usuario inactivo con la contraseña correcta

- **GIVEN** `recepcion@consultorio-demo.test` está inactiva
- **WHEN** se inicia sesión con ese email y su contraseña correcta
- **THEN** la interfaz muestra el mensaje genérico, idéntico al de una contraseña incorrecta, y no entra al panel

#### Scenario: US-090 CA-2 Borde - sin conexión con la API se muestra otro mensaje

- **GIVEN** la API no responde, o responde un error `5xx`
- **WHEN** se inicia sesión con credenciales válidas
- **THEN** la interfaz muestra «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.», distinto del mensaje genérico
- **AND** conserva el email y la contraseña escritos y no guardó ningún token

### Requirement: La sesión vive en el navegador sin exponer los tokens

La interfaz SHALL guardar el access token solo en memoria y el refresh token solo durante la pestaña (RN-AU-03), para que recargar la página no pida la contraseña y cerrar la pestaña termine la sesión. MUST NOT poner un token ni la contraseña en la URL, MUST NOT escribirlos en la consola y MUST NOT guardar la contraseña.

#### Scenario: US-092 CA-1 Feliz - recargar el panel conserva la sesión

- **GIVEN** una sesión iniciada en una pestaña, y el reloj marca 12:30 (el access emitido a las 12:00 ya venció; el refresh no)
- **WHEN** se recarga `/panel`
- **THEN** la interfaz pide `POST /auth/refresh` con el refresh guardado, recibe un access nuevo y muestra el panel sin pasar por la pantalla de inicio de sesión

#### Scenario: US-092 CA-1 Borde - mientras verifica la sesión no muestra el panel

- **GIVEN** una sesión guardada y la renovación del arranque todavía sin respuesta
- **WHEN** se abre `/panel`
- **THEN** la interfaz muestra «Cargando…» y no muestra el contenido del panel hasta que la renovación responda

#### Scenario: US-092 CA-1 Borde - ningún token aparece en la URL

- **WHEN** se inicia sesión, se recarga el panel y se cierra la sesión
- **THEN** ninguna URL visitada contiene el access token, el refresh token ni la contraseña

#### Scenario: US-092 CA-1 Borde - sin almacenamiento disponible la sesión dura lo que la página

- **GIVEN** el almacenamiento de la pestaña no está disponible o rechaza las escrituras
- **WHEN** se inicia sesión con credenciales válidas
- **THEN** la interfaz entra al panel igual
- **AND** al recargar la página pide iniciar sesión de nuevo, sin mostrar un error

### Requirement: Las rutas del panel exigen una sesión

La interfaz MUST NOT mostrar ninguna ruta del panel sin una sesión (RN-AU-01): sin sesión SHALL llevar a la pantalla de inicio de sesión, recordando la ruta pedida. Con una sesión, la pantalla de inicio de sesión SHALL llevar al panel. Cualquier otra ruta SHALL llevar al panel.

#### Scenario: US-092 CA-1 Error de negocio - el panel sin sesión lleva al inicio de sesión

- **GIVEN** una pestaña nueva, sin sesión guardada
- **WHEN** se abre `/panel`
- **THEN** la interfaz muestra la pantalla de inicio de sesión en `/ingresar` sin pedir nada a la API

#### Scenario: US-092 CA-1 Borde - con sesión, la pantalla de inicio de sesión lleva al panel

- **GIVEN** una sesión iniciada
- **WHEN** se abre `/ingresar`
- **THEN** la interfaz muestra el panel en `/panel`

#### Scenario: US-092 CA-1 Borde - una ruta desconocida lleva al panel o al inicio de sesión

- **WHEN** se abre `/` o `/cualquier-cosa`, con y sin sesión
- **THEN** con sesión la interfaz muestra `/panel`; sin sesión, la pantalla de inicio de sesión

### Requirement: Un 401 de la API se renueva una vez o termina la sesión

Cuando una ruta del panel de la API responde `401`, la interfaz SHALL renovar la sesión con `POST /auth/refresh` una sola vez y repetir la petición una sola vez (RN-AU-03). Si la renovación responde `401`, o la petición repetida vuelve a dar `401`, SHALL borrar la sesión y mostrar la pantalla de inicio de sesión con el aviso de sesión terminada. Varias peticiones rechazadas a la vez SHALL compartir una sola renovación.

#### Scenario: US-092 CA-1 Feliz - access vencido con refresh vigente se renueva sin interrumpir

- **GIVEN** una sesión iniciada a las 12:00 y el reloj marca 12:15 (el access venció)
- **WHEN** la interfaz pide una ruta del panel de la API y recibe `401`
- **THEN** pide `POST /auth/refresh` una vez, recibe un access nuevo y repite la petición con él
- **AND** quien hizo la petición recibe la respuesta de la repetición, sin ver la pantalla de inicio de sesión

#### Scenario: US-092 CA-1 Error de negocio - refresh rechazado vuelve al inicio de sesión

- **GIVEN** una sesión cuyo refresh ya no sirve (venció, o el usuario fue desactivado o cambió su `token_version`)
- **WHEN** una ruta del panel de la API responde `401` y la renovación también responde `401` con `codigos` `["RN-AU-03"]`
- **THEN** la interfaz borra los dos tokens y muestra la pantalla de inicio de sesión con el aviso de sesión terminada

#### Scenario: US-092 CA-1 Error de negocio - al recargar, un refresh rechazado vuelve al inicio de sesión

- **GIVEN** una sesión guardada cuyo refresh la API ya no acepta
- **WHEN** se recarga `/panel`
- **THEN** la interfaz muestra la pantalla de inicio de sesión con el aviso de sesión terminada y no guarda ningún token

#### Scenario: US-092 CA-1 Borde - tres peticiones rechazadas comparten una renovación

- **GIVEN** una sesión con el access vencido y el refresh vigente
- **WHEN** tres peticiones a rutas del panel de la API reciben `401` al mismo tiempo
- **THEN** la API recibe una sola petición `POST /auth/refresh` y las tres peticiones se repiten con el access nuevo

#### Scenario: US-092 CA-1 Borde - la repetición rechazada no vuelve a renovar

- **GIVEN** una renovación que responde `200`
- **WHEN** la petición repetida con el access nuevo vuelve a recibir `401`
- **THEN** la interfaz no pide otra renovación: borra la sesión y muestra el aviso de sesión terminada

#### Scenario: US-092 CA-1 Borde - un 403 no termina la sesión

- **GIVEN** una sesión iniciada
- **WHEN** una ruta del panel de la API responde `403` con `codigos` `["RN-AU-05"]`
- **THEN** la interfaz no renueva ni borra la sesión, y quien hizo la petición recibe el rechazo con su código

#### Scenario: US-090 CA-2 Borde - un 401 del propio inicio de sesión no intenta renovar

- **GIVEN** un refresh guardado de una sesión anterior
- **WHEN** `POST /auth/login` responde `401`
- **THEN** la interfaz no pide `POST /auth/refresh` y muestra el mensaje genérico

### Requirement: Cerrar sesión desde el panel

El panel SHALL ofrecer «Cerrar sesión», que borra el access y el refresh del navegador y lleva a la pantalla de inicio de sesión sin dejar el panel en el historial de navegación. La interfaz MUST NOT pedir nada a la API al cerrar sesión (no hay revocación de a uno, RN-AU-03).

#### Scenario: US-090 CA-1 Feliz - cerrar sesión vuelve al inicio de sesión

- **GIVEN** una sesión iniciada en el panel
- **WHEN** se pulsa «Cerrar sesión»
- **THEN** la interfaz muestra la pantalla de inicio de sesión, sin tokens guardados y sin haber pedido nada a la API

#### Scenario: US-092 CA-1 Borde - después de cerrar sesión el panel no vuelve

- **GIVEN** una sesión cerrada con «Cerrar sesión»
- **WHEN** se usa «Atrás» del navegador o se abre `/panel`
- **THEN** la interfaz muestra la pantalla de inicio de sesión y no el panel
