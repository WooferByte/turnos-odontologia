# encabezado-del-panel Specification

## Purpose
Define qué muestra el encabezado del panel sobre la sesión del navegador: el email y los roles del usuario que inició sesión, junto a «Cerrar sesión», cuándo los pide a la API y qué pasa ante un `401` o ante otra falla, para distinguir de quién es cada ventana abierta (RN-AU-02, RN-AU-03, RN-AU-05).

Convenciones de los escenarios: la API es la de `usuario-de-la-sesion` (`GET /auth/yo`), que decide qué devuelve; la interfaz no decodifica el token ni guarda el email o los roles en el almacenamiento del navegador, solo en la pantalla abierta. «Con sesión de X» significa que X inició sesión en el panel (capability `ingreso-al-panel`). Los usuarios de partida de la suite son los de `pantalla-de-usuarios`: «la odontóloga» (`odontologa@consultorio-demo.test`, `odontologo` + `dueno`) y «la recepcionista» (`recepcion@consultorio-demo.test`, `recepcionista`). «El indicador» es el texto del encabezado del panel (región `banner`) con el email y, debajo, los roles con las etiquetas de la pantalla de usuarios, separados por « · » y en el orden fijo de la API: «Odontólogo», «Recepcionista», «Dueño» (D308). «El aviso de sesión terminada» es el de `ingreso-al-panel`. Las etiquetas, el momento del pedido y el comportamiento ante fallas son decisiones del autor (D308 a D310). La disposición viene de las pantallas de Stitch (D234): escritorio `projects/14200813501064679723/screens/96c5900aaf8b4db18311a9baa8eafe75` y angosta `projects/14200813501064679723/screens/3078f94a4d474bff80154f884ccfa84f` (design, «Referencia visual (Stitch)»); lo puramente visual, como el corte del email en anchos angostos (D311), no tiene escenario y se compara en la prueba en el navegador. Cada escenario tiene un ID propio (`SES-4a`, `SES-4b`…) que lleva el nombre de su test; el número es el escenario mínimo de `CHANGES.md` que cubre. Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite del frontend (`npm test`) y se repiten en la prueba en el navegador, salvo los que dicen que solo se verifican contra el servidor falso.

## Requirements

### Requirement: El encabezado muestra el usuario de la sesión

Al entrar al panel con una sesión (después de iniciar sesión o al abrir la pestaña con un refresh guardado), la interfaz SHALL pedir `GET /auth/yo` **una vez** y mostrar en el encabezado, inmediatamente antes de «Cerrar sesión», el email tal como lo devuelve la API y los roles con sus etiquetas (D308, D309); los roles son los que la API leyó de la base, no los que la interfaz supone (RN-AU-02). Navegar entre las pantallas del panel MUST NOT volver a pedirlo. Mientras espera, el indicador no muestra ningún email. Una respuesta que llega después de «Cerrar sesión» MUST NOT mostrarse (RN-AU-03).

#### Scenario: SES-4a Feliz - después de iniciar sesión el encabezado muestra el email y los roles

- **GIVEN** una pestaña sin sesión
- **WHEN** la odontóloga inicia sesión desde `/ingresar` y llega al panel
- **THEN** el encabezado muestra «odontologa@consultorio-demo.test» y «Odontólogo · Dueño», y a continuación el botón «Cerrar sesión»
- **AND** la interfaz pidió `GET /api/auth/yo` una sola vez, con el access recibido

#### Scenario: SES-4b Borde - navegar entre pantallas no vuelve a pedir el usuario

- **GIVEN** la recepcionista inició sesión y el encabezado muestra «recepcion@consultorio-demo.test» y «Recepcionista»
- **WHEN** abre «Prestaciones», «Horario», «Bloqueos» y «Mi contraseña», una después de otra
- **THEN** el encabezado sigue mostrando su email y su rol en cada pantalla
- **AND** la interfaz pidió `GET /api/auth/yo` una sola vez en total

#### Scenario: SES-4c Borde - al recargar la pestaña el usuario se muestra después de renovar

- **GIVEN** la odontóloga inició sesión y su refresh quedó guardado en la pestaña
- **WHEN** se recarga la pestaña en `/panel/prestaciones` y la respuesta de `GET /api/auth/yo` todavía no llegó
- **THEN** la interfaz renovó la sesión con `POST /api/auth/refresh` antes de pedir `GET /api/auth/yo`, y el encabezado todavía no muestra ningún email
- **AND** cuando llega la respuesta, el encabezado muestra «odontologa@consultorio-demo.test» y «Odontólogo · Dueño»

#### Scenario: SES-4d Borde - otro usuario en la misma pestaña ve sus propios datos

- **GIVEN** la odontóloga inició sesión y el encabezado muestra su email
- **WHEN** pulsa «Cerrar sesión» y la recepcionista inicia sesión en la misma pestaña
- **THEN** el encabezado muestra «recepcion@consultorio-demo.test» y «Recepcionista», y en ningún momento después del ingreso de la recepcionista muestra el email de la odontóloga
- **AND** la interfaz pidió `GET /api/auth/yo` una vez por cada inicio de sesión

#### Scenario: SES-4e Borde - una respuesta tardía después de cerrar sesión no se muestra

- **GIVEN** la odontóloga inició sesión y la respuesta de `GET /api/auth/yo` está retenida en el servidor falso
- **WHEN** pulsa «Cerrar sesión» y después se libera la respuesta
- **THEN** la pantalla de inicio de sesión no muestra «odontologa@consultorio-demo.test» ni «Odontólogo · Dueño»
- **AND** este escenario se verifica solo contra el servidor falso

### Requirement: Un 401 al pedir el usuario sigue el camino de la sesión

Si `GET /auth/yo` responde `401`, la interfaz SHALL seguir el requisito de `ingreso-al-panel` sobre el `401`: renovar la sesión una vez y repetir el pedido una vez; si la renovación o la repetición vuelven a dar `401`, SHALL borrar la sesión y mostrar la pantalla de inicio de sesión con el aviso de sesión terminada (RN-AU-03).

#### Scenario: SES-5a Error de negocio - un 401 sin renovación posible vuelve al inicio de sesión

- **GIVEN** la recepcionista inició sesión y, antes de que el panel pida su usuario, su sesión dejó de servir en la API (la odontóloga la desactivó)
- **WHEN** `GET /api/auth/yo` responde `401` con `codigos` `["RN-AU-03"]` y `POST /api/auth/refresh` también
- **THEN** la interfaz muestra la pantalla de inicio de sesión con el aviso de sesión terminada, sin tokens guardados
- **AND** el encabezado del panel ya no se muestra

#### Scenario: SES-5b Borde - un 401 con el refresh vigente renueva y muestra el usuario

- **GIVEN** la odontóloga inició sesión y su access venció antes de que el panel pida su usuario (su refresh sigue vigente)
- **WHEN** `GET /api/auth/yo` responde `401` con `codigos` `["RN-AU-03"]`
- **THEN** la interfaz pide `POST /api/auth/refresh` una sola vez, repite `GET /api/auth/yo` con el access nuevo y el encabezado muestra su email y sus roles, sin pasar por la pantalla de inicio de sesión

### Requirement: Otra falla al pedir el usuario no interrumpe el panel

Si `GET /auth/yo` no responde (sin conexión), responde con un error del servidor, responde `403` (usuario sin roles, RN-AU-05) o responde `200` con un cuerpo que no es el de la API (por ejemplo, un rol que no es uno de los tres o sin `email`), el encabezado SHALL quedar sin el indicador, sin ningún aviso nuevo y sin reintentar, y la sesión SHALL seguir: la pantalla abierta, la navegación y «Cerrar sesión» funcionan como antes (D310). Estos escenarios se verifican solo contra el servidor falso.

#### Scenario: SES-4f Error - sin conexión el panel sigue sin el indicador

- **GIVEN** el servidor falso no responde `GET /api/auth/yo` (falla de red) y responde las demás rutas
- **WHEN** la odontóloga inicia sesión y llega al panel
- **THEN** el encabezado muestra «Cerrar sesión» y ningún email ni rol, y la interfaz no muestra ningún aviso por esa falla ni vuelve a pedir `GET /api/auth/yo`
- **AND** la sesión sigue: «Prestaciones» carga su lista y «Cerrar sesión» lleva a la pantalla de inicio de sesión

#### Scenario: SES-4g Error - con un error del servidor el panel sigue sin el indicador

- **GIVEN** el servidor falso responde `GET /api/auth/yo` con `500` y responde las demás rutas
- **WHEN** la odontóloga inicia sesión y llega al panel
- **THEN** el encabezado muestra «Cerrar sesión» y ningún email ni rol, y la interfaz no muestra ningún aviso por esa falla ni vuelve a pedir `GET /api/auth/yo`
- **AND** la sesión sigue: «Prestaciones» carga su lista

#### Scenario: SES-4h Error de negocio - con 403 el panel sigue sin el indicador

- **GIVEN** el servidor falso responde `GET /api/auth/yo` con `403` y `codigos` `["RN-AU-05"]`
- **WHEN** la odontóloga inicia sesión y llega al panel
- **THEN** el encabezado muestra «Cerrar sesión» y ningún email ni rol, y la interfaz no muestra ningún aviso por esa falla ni vuelve a pedir `GET /api/auth/yo`
- **AND** la sesión sigue: «Cerrar sesión» lleva a la pantalla de inicio de sesión

#### Scenario: SES-4i Error - con una respuesta de otra forma el panel sigue sin el indicador

- **GIVEN** el servidor falso responde `GET /api/auth/yo` con `200` y el cuerpo `{"email": "odontologa@consultorio-demo.test", "roles": ["administrador"]}`
- **WHEN** la odontóloga inicia sesión y llega al panel
- **THEN** el encabezado muestra «Cerrar sesión» y ningún email ni rol, y la interfaz no muestra ningún aviso ni vuelve a pedir `GET /api/auth/yo`
- **AND** la sesión sigue: «Prestaciones» carga su lista
