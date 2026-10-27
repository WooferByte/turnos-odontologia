# pantalla-de-contrasenas Specification

## Purpose
Define cómo el panel restablece desde el navegador la contraseña de un usuario (en la pantalla de usuarios) y cómo cada usuario cambia la suya desde «Mi contraseña», cómo se ven los rechazos de la API con su código y qué pasa con la sesión del navegador después del cambio (US-093 CA-6, CA-7, CA-9; US-092 CA-1).

Convenciones de los escenarios: la API es la de `contrasenas-de-usuarios`, que decide todas las reglas; la pantalla no valida el largo de las contraseñas, solo que estén los campos obligatorios y, en «Mi contraseña», que la nueva y su repetición coincidan (D296), y muestra cada rechazo con su código RN. «Con sesión de X» significa que X inició sesión en el panel (capability `ingreso-al-panel`). Los usuarios de partida de la suite son los de `pantalla-de-usuarios`: «la odontóloga» (`odontologa@consultorio-demo.test`, id 1, activa, `odontologo` + `dueno`), «la recepcionista» (`recepcion@consultorio-demo.test`, id 2, activa, `recepcionista`) y `administracion@consultorio-demo.test` (id 3, inactivo, `dueno`); «el dueño» es un usuario con sesión y solo `dueno`. Las contraseñas son ficticias: la actual de todos es `demo-consultorio-2026` y la nueva de los ejemplos, `clave-nueva-2026`. «El mensaje de conexión» es el de C-11, «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.». La pantalla no conoce el rol ni el id de quien inició sesión (D249): las acciones se ven para todos y la API decide. La disposición viene de las pantallas de Stitch (D234, D301): «Mi contraseña» `projects/14200813501064679723/screens/fa6faa69cae34252a7c79e2cb82210c5` y «Usuarios» con el panel «Restablecer contraseña» `projects/14200813501064679723/screens/925f1e4028294cb2bb9bdeeea81ffd09` (design, «Referencia visual (Stitch)»); lo puramente visual no tiene escenario. Los textos fijos son Propuesta del design (K14). Ninguna contraseña aparece fuera de su campo, en la URL ni en la consola. Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite del frontend (`npm test`) y se repiten en la prueba en el navegador, salvo los que dicen que solo se verifican contra el servidor falso.

## Requirements

### Requirement: Restablecer la contraseña desde la fila del usuario

Cada fila de la tabla de usuarios SHALL ofrecer «Restablecer contraseña», que abre el panel lateral con el email del usuario como texto, «Contraseña nueva» (campo de contraseña con la ayuda «De 10 caracteres a 72 bytes.») y la nota «Al guardar se cierran todas las sesiones de este usuario.». «Guardar» SHALL mandar `POST /usuarios/{id}/restablecer-contrasena` con la contraseña tal como se escribió; con `204` SHALL cerrar el panel, vaciar el campo y avisar en la tabla, sin cambiar ninguna fila.

#### Scenario: US-093 CA-6 Feliz - la odontóloga restablece la contraseña de la recepcionista

- **GIVEN** con sesión de la odontóloga, en la pantalla de usuarios
- **WHEN** pulsa «Restablecer contraseña» en la fila de la recepcionista, escribe `clave-nueva-2026` y pulsa «Guardar»
- **THEN** se manda un solo `POST /usuarios/2/restablecer-contrasena` con `{"contrasena": "clave-nueva-2026"}`
- **AND** el panel se cierra y el aviso de la tabla dice «Contraseña restablecida. Se cerraron las sesiones de recepcion@consultorio-demo.test.»
- **AND** la fila de la recepcionista sigue igual y, al volver a pulsar «Restablecer contraseña», el campo está vacío

#### Scenario: US-093 CA-9 Error de negocio - la contraseña corta se muestra debajo del campo

- **WHEN** la odontóloga intenta restablecer la contraseña de la recepcionista con `corta-123`
- **THEN** se manda el `POST` sin validarla antes, la API responde `422` `RN-AU-07` y debajo de «Contraseña nueva» se ve «La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).»
- **AND** el panel sigue abierto con lo escrito

#### Scenario: US-093 CA-6 Error de negocio - la odontóloga no restablece la propia

- **WHEN** la odontóloga pulsa «Restablecer contraseña» en su propia fila, escribe `clave-nueva-2026` y pulsa «Guardar»
- **THEN** la API responde `409` `RN-AU-10` y el aviso del panel dice «Tu propia contraseña se cambia desde «Mi contraseña» (RN-AU-10).»
- **AND** el panel sigue abierto y su sesión sigue

#### Scenario: US-093 CA-6 Error de negocio - el dueño ve el rechazo sin perder la sesión

- **GIVEN** con sesión del dueño, en la pantalla de usuarios
- **WHEN** restablece la contraseña de la recepcionista con `clave-nueva-2026`
- **THEN** el aviso del panel, que sigue abierto con lo escrito, dice «Tu usuario no tiene permiso para modificar usuarios (RN-AU-05).»
- **AND** no se pidió `POST /auth/refresh` y el dueño sigue en el panel

#### Scenario: US-093 CA-6 Borde - Cancelar, Cerrar y el campo vacío no piden nada

- **WHEN** la odontóloga abre «Restablecer contraseña» de la recepcionista y pulsa «Guardar» con el campo vacío; después escribe `clave-nueva-2026` y pulsa «Cancelar»; y después lo vuelve a abrir, escribe y pulsa el botón «Cerrar» del encabezado del panel
- **THEN** no se mandó ningún `POST`
- **AND** cada vez que vuelve a abrir el panel el campo está vacío

#### Scenario: US-093 CA-6 Borde - pulsar «Guardar» dos veces manda un solo pedido

- **GIVEN** con sesión de la odontóloga, restableciendo la contraseña de la recepcionista, y la respuesta del `POST` todavía pendiente
- **WHEN** pulsa «Guardar» y lo vuelve a pulsar
- **THEN** mientras espera, «Guardar» está deshabilitado y se mandó un solo `POST /usuarios/2/restablecer-contrasena`
- **AND** al llegar el `204` se ve el aviso de contraseña restablecida

#### Scenario: US-093 CA-6 Borde - sin conexión y un usuario que ya no existe

- **WHEN** la odontóloga guarda una contraseña válida con la API caída; y después, con la API de vuelta, la recepcionista deja de existir en el servidor falso y la odontóloga guarda otra vez
- **THEN** sin conexión, el aviso del panel dice el mensaje de conexión, lo escrito se conserva y «Guardar» vuelve a estar habilitado
- **AND** con el usuario que ya no existe, la API responde `404` `RN-GL-04`, el panel se cierra, el aviso de la tabla dice «El usuario ya no existe (RN-GL-04).» y la lista se vuelve a pedir
- **AND** la parte del usuario que ya no existe se verifica solo contra el servidor falso (la API real no borra usuarios)

### Requirement: Cambiar la propia contraseña desde «Mi contraseña»

El enlace «Mi contraseña» de la barra del panel SHALL llevar a `/panel/contrasena`, con «Contraseña actual», «Contraseña nueva» (con la ayuda «De 10 caracteres a 72 bytes.») y «Repetir contraseña nueva». «Cambiar contraseña» SHALL mandar `POST /auth/cambiar-contrasena` con la actual y la nueva tal como se escribieron, solo si la nueva y su repetición coinciden; con `200` SHALL vaciar los tres campos y avisar que las otras sesiones se cerraron.

#### Scenario: US-093 CA-7 Feliz - la recepcionista cambia la suya

- **GIVEN** con sesión de la recepcionista
- **WHEN** pulsa «Mi contraseña» en la barra del panel, escribe `demo-consultorio-2026` en «Contraseña actual» y `clave-nueva-2026` en «Contraseña nueva» y en «Repetir contraseña nueva», y pulsa «Cambiar contraseña»
- **THEN** se manda un solo `POST /auth/cambiar-contrasena` con `{"contrasena_actual": "demo-consultorio-2026", "contrasena_nueva": "clave-nueva-2026"}`
- **AND** se ve «Contraseña cambiada. Tus otras sesiones se cerraron.» y los tres campos quedan vacíos
- **AND** la recepcionista sigue en el panel

#### Scenario: US-093 CA-7 Error de negocio - la contraseña actual incorrecta se muestra debajo de la actual

- **WHEN** la recepcionista intenta cambiar la suya con `no-es-la-actual-2026` como actual
- **THEN** la API responde `422` `RN-AU-09` y debajo de «Contraseña actual» se ve «La contraseña actual no es correcta (RN-AU-09).»
- **AND** no se pidió `POST /auth/refresh`, la recepcionista sigue en el panel y los campos conservan lo escrito

#### Scenario: US-093 CA-9 Error de negocio - la contraseña nueva corta se muestra debajo de la nueva

- **WHEN** la recepcionista intenta cambiar la suya con `corta-123` como nueva y como repetición
- **THEN** se manda el `POST` sin validarla antes, la API responde `422` `RN-AU-07` y debajo de «Contraseña nueva» se ve «La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).»

#### Scenario: US-093 CA-7 Borde - la repetición distinta no manda nada

- **WHEN** la recepcionista escribe la actual, `clave-nueva-2026` como nueva y `clave-nueva-2027` como repetición, y pulsa «Cambiar contraseña»
- **THEN** no se manda ninguna petición y debajo de «Repetir contraseña nueva» se ve «Las contraseñas nuevas no coinciden.»
- **AND** con un campo vacío tampoco se manda ninguna petición

#### Scenario: US-093 CA-7 Borde - pulsar dos veces, sin conexión y salir de la pantalla

- **GIVEN** con sesión de la recepcionista, en «Mi contraseña» con los tres campos completos
- **WHEN** pulsa «Cambiar contraseña» dos veces con la respuesta todavía pendiente; después repite el cambio con la API caída; y después va a «Prestaciones» y vuelve a «Mi contraseña»
- **THEN** mientras espera, «Cambiar contraseña» está deshabilitado y se mandó un solo `POST`
- **AND** sin conexión se ve el mensaje de conexión, lo escrito se conserva y el botón vuelve a estar habilitado
- **AND** al volver a la pantalla los tres campos están vacíos

#### Scenario: US-093 CA-7 Borde - todos los roles ven «Mi contraseña»

- **WHEN** la odontóloga, la recepcionista y el dueño miran la barra del panel
- **THEN** los tres ven el enlace «Mi contraseña»

### Requirement: Después de cambiar la propia, la sesión sigue con los tokens nuevos

Con el `200` de `POST /auth/cambiar-contrasena`, la interfaz SHALL reemplazar el access y el refresh de la sesión por los de la respuesta (el refresh, donde ya lo guarda `ingreso-al-panel`), así la sesión desde la que se cambió sigue sin renovar ni volver a `/ingresar` (D291).

#### Scenario: US-093 CA-7 Borde - la siguiente petición usa el token nuevo sin renovar

- **GIVEN** la recepcionista acaba de cambiar su contraseña en «Mi contraseña» y el servidor falso ya no acepta sus tokens anteriores
- **WHEN** pulsa «Prestaciones» en la barra del panel
- **THEN** ve la lista de prestaciones
- **AND** la petición `GET /prestaciones` lleva el access nuevo y no se pidió `POST /auth/refresh`

#### Scenario: US-093 CA-7 Borde - recargar después de cambiarla conserva la sesión

- **GIVEN** la recepcionista acaba de cambiar su contraseña en «Mi contraseña»
- **WHEN** recarga la página
- **THEN** la interfaz renueva la sesión con el refresh nuevo y sigue en el panel, sin el aviso de sesión terminada

### Requirement: La sesión que termina en estas pantallas vuelve al inicio de sesión

Si la sesión no se puede renovar al restablecer o al cambiar una contraseña, la interfaz SHALL volver a `/ingresar` con «Tu sesión terminó. Iniciá sesión de nuevo.» y MUST NOT mostrar el mensaje de conexión (US-092 CA-1; cableado de C-11, D231).

#### Scenario: US-092 CA-1 Borde - una sesión irrenovable al cambiar la propia

- **GIVEN** con sesión de la recepcionista, en «Mi contraseña» con los tres campos completos, y la sesión que ya no se puede renovar
- **WHEN** pulsa «Cambiar contraseña»
- **THEN** la interfaz vuelve a `/ingresar` con el aviso de sesión terminada
- **AND** la contraseña de la recepcionista no cambió en el servidor falso

#### Scenario: US-092 CA-1 Borde - una sesión irrenovable al restablecer

- **GIVEN** con sesión de la odontóloga, restableciendo la contraseña de la recepcionista con `clave-nueva-2026` escrita, y la sesión que ya no se puede renovar
- **WHEN** pulsa «Guardar»
- **THEN** la interfaz vuelve a `/ingresar` con el aviso de sesión terminada, sin el mensaje de conexión
- **AND** la contraseña de la recepcionista no cambió en el servidor falso
