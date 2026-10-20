## ADDED Requirements

### Requirement: La pantalla de inicio de sesión sigue la pantalla de Stitch sin cambiar su comportamiento

La pantalla de inicio de sesión SHALL presentarse como la pantalla de Stitch citada en el design (D234): la marca como título, los avisos con su texto exacto y en su lugar, y el botón de espera con su nombre. MUST NOT cambiar textos, mensajes, roles accesibles, peticiones ni sesión de los demás requisitos de esta capability (RN-AU-01, RN-AU-04), y MUST NOT cargar fuentes, estilos, scripts ni íconos de otro origen.

#### Scenario: US-090 CA-1 Feliz - la pantalla muestra la marca y solo el formulario de ingreso

- **GIVEN** una pestaña sin sesión
- **WHEN** se abre `/ingresar`
- **THEN** la interfaz muestra un único título de primer nivel, «Turnos Odontológicos AR», que da nombre a la región (la tarjeta) que contiene el formulario, sin subtítulo (D237)
- **AND** los campos con nombre accesible «Email» y «Contraseña», y un único botón, «Ingresar»
- **AND** ningún enlace ni otro control (ni «Olvidé mi contraseña», ni «Recordarme», ni registro)

#### Scenario: US-090 CA-1 Feliz - al abrir la pantalla no hay avisos

- **GIVEN** una pestaña sin sesión y sin aviso pendiente
- **WHEN** se abre `/ingresar`
- **THEN** la interfaz no muestra ningún elemento con rol `alert` ni con rol `status`

#### Scenario: US-090 CA-2 Error de negocio - el rechazo se muestra en el aviso de error con el mensaje exacto

- **WHEN** se inicia sesión con `odontologa@consultorio-demo.test` y una contraseña que no es la suya, y la API responde `401` con `codigos` `["RN-AU-04"]`
- **THEN** la interfaz muestra un único elemento con rol `alert` cuyo texto es exactamente «El email o la contraseña no son correctos.», sin título ni código agregados
- **AND** ese aviso aparece después del campo «Contraseña» y antes del botón «Ingresar»

#### Scenario: US-090 CA-3 Error de negocio - la usuaria inactiva ve el mismo aviso que una contraseña incorrecta

- **GIVEN** `recepcion@consultorio-demo.test` está inactiva
- **WHEN** se inicia sesión con ese email y su contraseña correcta, y la API responde `401` con `codigos` `["RN-AU-04"]`
- **THEN** la interfaz muestra el mismo aviso que en el escenario de la contraseña incorrecta: un único elemento con rol `alert`, el texto exacto «El email o la contraseña no son correctos.», sin título ni código, después del campo «Contraseña» y antes del botón «Ingresar»
- **AND** no entra al panel

#### Scenario: US-092 CA-1 Borde - el aviso de sesión terminada va antes de los campos y se va al reintentar

- **GIVEN** una sesión guardada cuyo refresh la API ya no acepta (la renovación responde `401` con `codigos` `["RN-AU-03"]`), y se recarga `/panel`
- **WHEN** la interfaz muestra la pantalla de inicio de sesión
- **THEN** el elemento con rol `status` cuyo texto es exactamente «Tu sesión terminó. Iniciá sesión de nuevo.» aparece antes del campo «Email»
- **AND** si después se inicia sesión con una contraseña incorrecta, la interfaz muestra solo el aviso de error con el mensaje genérico y ya no el de sesión terminada

#### Scenario: US-090 CA-1 Borde - mientras espera, el botón conserva su nombre con el ícono de espera

- **GIVEN** un inicio de sesión enviado cuya respuesta todavía no llegó
- **WHEN** se mira el botón del formulario
- **THEN** está deshabilitado, contiene el ícono de espera (D238) y su nombre accesible es exactamente «Ingresando…» (el ícono no agrega texto)
- **AND** si la respuesta llega con `200`, la interfaz muestra el panel en `/panel`
- **AND** si en cambio la API no responde, el aviso de error muestra exactamente «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» en el mismo lugar que el mensaje genérico, sin título, y el botón vuelve a estar habilitado con el nombre «Ingresar» y sin el ícono

#### Scenario: STI-1 Borde - la pantalla no carga recursos de otro origen

- **WHEN** se revisan los estilos, los componentes y la página de entrada de la interfaz
- **THEN** ninguno pide un estilo, una fuente, un script ni un ícono a una dirección de otro origen (ni Tailwind, ni Google Fonts, ni Material Symbols); esto lo verifica la suite del frontend
- **AND** al abrir `/ingresar` servida por el servicio `frontend` de Compose, la consola del navegador no muestra violaciones de la política de seguridad de contenido (`default-src 'self'`); esto lo verifica la prueba en el navegador
