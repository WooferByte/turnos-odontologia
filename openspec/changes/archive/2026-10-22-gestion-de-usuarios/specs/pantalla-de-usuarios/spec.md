# Spec Delta: pantalla-de-usuarios

## Purpose

Define cómo el panel muestra y mantiene los usuarios del consultorio desde el navegador: la tabla, el alta con la contraseña inicial y los roles, la edición de roles, desactivar y reactivar, cómo se ven los rechazos de la API con su código y qué pasa si la sesión termina en la pantalla (US-093, US-092 CA-1).

Convenciones de los escenarios: la API es la de `gestion-de-usuarios`, que decide todas las reglas; la pantalla no valida roles, contraseñas ni emails más allá de los campos obligatorios, y muestra cada rechazo con su código RN. «Con sesión de X» significa que X inició sesión en el panel (capability `ingreso-al-panel`). Los usuarios de partida de la suite son ficticios: «la odontóloga» (`odontologa@consultorio-demo.test`, activa, `odontologo` + `dueno`), «la recepcionista» (`recepcion@consultorio-demo.test`, activa, `recepcionista`) y `administracion@consultorio-demo.test` (inactivo, `dueno`); «el dueño» es un usuario con sesión y solo `dueno`. «El botón «Cerrar»» es el de la esquina del encabezado del panel lateral (la disposición viene de la pantalla de Stitch, D234; lo puramente visual no tiene escenario). La pantalla no conoce el rol ni el id de quien inició sesión (D249): las acciones se ven para todos y la API decide. Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite del frontend (`npm test`) y se repiten en la prueba en el navegador, salvo los que dicen que solo se verifican contra el servidor falso.

## ADDED Requirements

### Requirement: La pantalla lista los usuarios del consultorio

La ruta `/panel/usuarios`, a la que se llega desde el enlace «Usuarios» de la barra del panel, SHALL mostrar una tabla con el email, los roles («Odontólogo», «Recepcionista», «Dueño»), el estado («Activo» o «Inactivo», no solo por color) y las acciones de cada usuario, en el orden de la API, con el contador «N usuarios registrados». Mientras carga SHALL mostrar «Cargando usuarios…» y sin conexión, el mensaje de conexión con «Reintentar».

#### Scenario: US-093 CA-1 Feliz - la odontóloga ve los tres usuarios

- **GIVEN** con sesión de la odontóloga
- **WHEN** pulsa «Usuarios» en la barra del panel
- **THEN** la pantalla muestra tres filas en orden: la odontóloga con «Odontólogo» y «Dueño», «Activo», «Editar» y «Desactivar»; la recepcionista con «Recepcionista»; y `administracion@consultorio-demo.test` con «Dueño», «Inactivo» y «Reactivar»
- **AND** el contador dice «3 usuarios registrados» y se hizo una sola petición `GET /usuarios`

#### Scenario: US-093 CA-1 Borde - mientras carga y sin conexión

- **GIVEN** con sesión de la odontóloga
- **WHEN** abre `/panel/usuarios` con la respuesta todavía pendiente, y después la API no responde
- **THEN** primero se ve «Cargando usuarios…» sin filas ni contador
- **AND** después se ve «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» con «Reintentar», que al responder la API muestra la tabla

#### Scenario: US-093 CA-1 Error de negocio - la recepcionista no ve los usuarios

- **GIVEN** con sesión de la recepcionista
- **WHEN** abre `/panel/usuarios`
- **THEN** la API responde `403` `RN-AU-05` y la pantalla muestra «Tu usuario no tiene permiso para ver los usuarios (RN-AU-05).» en lugar de la tabla, sin «Nuevo usuario»
- **AND** la sesión sigue: el enlace «Prestaciones» sigue funcionando

#### Scenario: US-093 CA-1 Borde - el dueño ve la tabla

- **GIVEN** con sesión del dueño
- **WHEN** abre `/panel/usuarios`
- **THEN** la pantalla muestra la tabla con los tres usuarios

### Requirement: Alta de un usuario con su contraseña inicial

«Nuevo usuario» SHALL abrir un panel lateral con «Email», «Contraseña inicial» (campo de contraseña, con la ayuda «De 10 caracteres a 72 bytes.») y las casillas de roles. «Guardar» SHALL mandar `POST /usuarios` con el email y la contraseña tal como se escribieron y los roles marcados; con `201` SHALL agregar la fila, cerrar el panel y vaciar el formulario (email, contraseña y casillas). Un `422` de formato en el email SHALL verse debajo del email («Ingresá un email válido.»). La contraseña MUST NOT mostrarse fuera del campo.

#### Scenario: US-093 CA-1 Feliz - alta de una recepcionista

- **GIVEN** con sesión de la odontóloga, en la pantalla de usuarios
- **WHEN** pulsa «Nuevo usuario», escribe `turnos@consultorio-demo.test` y `clave-ficticia-2026`, marca «Recepcionista» y pulsa «Guardar»
- **THEN** se manda un solo `POST /usuarios` con `{"email": "turnos@consultorio-demo.test", "contrasena": "clave-ficticia-2026", "roles": ["recepcionista"]}`
- **AND** el panel se cierra, la tabla tiene una cuarta fila «turnos@consultorio-demo.test», «Recepcionista», «Activo», y el contador dice «4 usuarios registrados»
- **AND** al volver a pulsar «Nuevo usuario», el email, la contraseña y las casillas están vacíos

#### Scenario: US-093 CA-2 Error de negocio - el email repetido se muestra debajo del email

- **WHEN** la odontóloga intenta crear un usuario con el email de la recepcionista
- **THEN** la API responde `409` `RN-AU-08` y debajo del email se ve «Ya existe un usuario con ese email (RN-AU-08).»
- **AND** el panel sigue abierto con lo escrito y la tabla no cambia

#### Scenario: US-093 CA-9 Error de negocio - la contraseña inicial corta se muestra debajo de la contraseña

- **WHEN** la odontóloga intenta crear un usuario con la contraseña `corta-123`
- **THEN** se manda el `POST` sin validarla antes, la API responde `422` `RN-AU-07` y debajo de la contraseña se ve «La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).»
- **AND** la tabla no cambia

#### Scenario: US-093 CA-1 Borde - un email que la API rechaza se muestra debajo del email

- **WHEN** la odontóloga intenta crear un usuario con un email de 255 caracteres (que el campo de email del navegador acepta), una contraseña válida y «Recepcionista»
- **THEN** se manda el `POST`, la API responde `422` con `codigos` vacío y un error del campo `email`, y debajo del email se ve «Ingresá un email válido.»
- **AND** el panel sigue abierto con lo escrito y la tabla no cambia

#### Scenario: US-093 CA-1 Borde - sin roles, campos vacíos y sin conexión

- **WHEN** la odontóloga pulsa «Guardar» en el alta con el email o la contraseña vacíos; después completa los dos sin marcar ningún rol; y después marca uno con la API caída
- **THEN** con un campo vacío no se manda ninguna petición
- **AND** sin roles, la API responde `422` y debajo de los roles se ve «Elegí al menos un rol.»
- **AND** sin conexión, el aviso del panel dice el mensaje de conexión, lo escrito se conserva y «Guardar» vuelve a estar habilitado

#### Scenario: US-093 CA-1 Borde - cerrar el alta borra la contraseña

- **WHEN** la odontóloga escribe una contraseña en el alta, pulsa «Cancelar» y vuelve a abrir «Nuevo usuario»
- **THEN** no se mandó ninguna petición y los campos están vacíos
- **AND** la contraseña no aparece en la tabla ni en ningún otro texto de la pantalla

### Requirement: Edición de los roles de un usuario

«Editar» SHALL abrir el panel lateral con el email como texto de solo lectura y las casillas con los roles actuales, y marcar la fila como «Editando». «Guardar» SHALL mandar `PATCH /usuarios/{id}` con solo `roles` si cambiaron; sin cambios SHALL cerrar el panel sin pedir nada. Con `200` SHALL reemplazar la fila. El panel de edición SHALL mostrar la nota «Quitar o asignar un rol vale desde la próxima acción del usuario, sin cerrar su sesión.» (los roles valen desde la petición siguiente, RN-AU-02, D254); el alta MUST NOT mostrarla. «Cancelar» SHALL cerrar el panel sin pedir nada, y el botón «Cerrar» del encabezado del panel SHALL hacer lo mismo, en el alta y en la edición: quita la marca «Editando» y descarta lo escrito, incluida la contraseña (D254).

#### Scenario: US-093 CA-1 Feliz - sumar el rol dueno a la recepcionista

- **GIVEN** con sesión de la odontóloga, en la pantalla de usuarios
- **WHEN** pulsa «Editar» en la fila de la recepcionista, marca «Dueño» y pulsa «Guardar»
- **THEN** se manda un solo `PATCH /usuarios/2` con `{"roles": ["recepcionista", "dueno"]}`
- **AND** la fila muestra «Recepcionista» y «Dueño» y ya no dice «Editando»

#### Scenario: US-093 CA-1 Borde - guardar sin cambios no pide nada

- **WHEN** la odontóloga abre «Editar» de la recepcionista y pulsa «Guardar» sin tocar nada
- **THEN** el panel se cierra y no se manda ningún `PATCH`

#### Scenario: US-093 CA-1 Borde - el botón «Cerrar» del panel no pide nada

- **GIVEN** con sesión de la odontóloga, editando a la recepcionista, con «Dueño» marcado
- **WHEN** pulsa el botón «Cerrar» del encabezado del panel
- **THEN** el panel lateral se cierra, la fila sigue con «Recepcionista», sin la marca «Editando», y no se mandó ningún `PATCH`
- **AND** si abre «Nuevo usuario», escribe `turnos@consultorio-demo.test` y `clave-ficticia-2026`, marca «Recepcionista» y pulsa «Cerrar», el panel se cierra, no se mandó ningún `POST`, la tabla sigue con tres filas y, al volver a pulsar «Nuevo usuario», el email, la contraseña y las casillas están vacíos

#### Scenario: US-093 CA-1 Borde - la edición avisa desde cuándo valen los roles

- **GIVEN** con sesión de la odontóloga, en la pantalla de usuarios
- **WHEN** pulsa «Editar» en la fila de la recepcionista
- **THEN** el panel muestra la nota «Quitar o asignar un rol vale desde la próxima acción del usuario, sin cerrar su sesión.»
- **AND** al pulsar «Nuevo usuario», el panel de alta no muestra esa nota

#### Scenario: US-093 CA-4 Error de negocio - la única odontóloga no puede dejar su rol

- **GIVEN** la odontóloga es la única con el rol `odontologo`
- **WHEN** abre «Editar» en su propia fila, desmarca «Odontólogo» y pulsa «Guardar»
- **THEN** la API responde `409` `RN-AU-06` y el aviso del panel dice «El consultorio no puede quedar sin un odontólogo activo y nadie puede desactivarse a sí mismo (RN-AU-06).»
- **AND** el panel sigue abierto con lo marcado y la fila sigue con «Odontólogo» y «Dueño»

### Requirement: Desactivar y reactivar desde la fila

«Desactivar» SHALL mandar `PATCH /usuarios/{id}` con `{"activo": false}` y, con `200`, mostrar la fila «Inactivo» con «Reactivar»; «Reactivar» SHALL mandar `{"activo": true}`. Mientras espera, los botones de la fila SHALL quedar deshabilitados. Un rechazo SHALL verse en el aviso de la tabla y la fila MUST NOT cambiar. No hay acción de borrar.

#### Scenario: US-093 CA-3 Feliz - desactivar a la recepcionista

- **GIVEN** con sesión de la odontóloga, en la pantalla de usuarios
- **WHEN** pulsa «Desactivar» en la fila de la recepcionista
- **THEN** se manda un solo `PATCH /usuarios/2` con `{"activo": false}`
- **AND** la fila queda atenuada con «Inactivo» y «Reactivar», sigue en la tabla y el contador no cambia
- **AND** ninguna fila ofrece borrar

#### Scenario: US-093 CA-3 Borde - reactivar a un usuario inactivo

- **WHEN** la odontóloga pulsa «Reactivar» en la fila de `administracion@consultorio-demo.test`
- **THEN** se manda `{"activo": true}` y la fila queda «Activo» con «Desactivar»

#### Scenario: US-093 CA-5 Error de negocio - la odontóloga no puede desactivarse

- **WHEN** la odontóloga pulsa «Desactivar» en su propia fila
- **THEN** la API responde `409` `RN-AU-06` y el aviso de la tabla dice «El consultorio no puede quedar sin un odontólogo activo y nadie puede desactivarse a sí mismo (RN-AU-06).»
- **AND** su fila sigue «Activo» y su sesión sigue

#### Scenario: US-093 CA-3 Borde - mientras espera, los botones de la fila quedan deshabilitados

- **GIVEN** con sesión de la odontóloga, en la pantalla de usuarios, y la respuesta del `PATCH` todavía pendiente
- **WHEN** pulsa «Desactivar» en la fila de la recepcionista y vuelve a pulsarlo
- **THEN** mientras espera, «Editar» y «Desactivar» de esa fila están deshabilitados y se mandó un solo `PATCH /usuarios/2`
- **AND** al llegar el `200`, la fila muestra «Inactivo» y «Reactivar» habilitado

#### Scenario: US-093 CA-3 Borde - un usuario que ya no existe

- **GIVEN** la pantalla muestra a la recepcionista, que después deja de existir en el servidor falso (la API real no borra usuarios: este escenario se verifica solo contra el servidor falso, no en la prueba en el navegador)
- **WHEN** la odontóloga pulsa «Desactivar» en esa fila
- **THEN** la API responde `404` `RN-GL-04`, el aviso de la tabla dice «El usuario ya no existe (RN-GL-04).» y la lista se vuelve a pedir

### Requirement: Un rol sin permiso ve el rechazo de la API sin perder la sesión

Si la API responde `403` `RN-AU-05` a un alta, una edición o una acción de fila, la pantalla SHALL mostrar «Tu usuario no tiene permiso para modificar usuarios (RN-AU-05).» en el aviso del panel (que sigue abierto con lo escrito) o en el aviso de la tabla, sin cambiar ninguna fila y MUST NOT cerrar la sesión.

#### Scenario: US-093 CA-1 Error de negocio - el dueño intenta crear y desactivar

- **GIVEN** con sesión del dueño, en la pantalla de usuarios
- **WHEN** intenta crear un usuario y después pulsa «Desactivar» en la fila de la recepcionista
- **THEN** el aviso del panel y después el aviso de la tabla muestran «Tu usuario no tiene permiso para modificar usuarios (RN-AU-05).»
- **AND** la tabla no cambia, no se pidió `POST /auth/refresh` y el dueño sigue en el panel

#### Scenario: US-093 CA-1 Error de negocio - el dueño intenta editar roles y reactivar

- **GIVEN** con sesión del dueño, en la pantalla de usuarios
- **WHEN** abre «Editar» en la fila de la recepcionista, marca «Dueño» y pulsa «Guardar»; y después pulsa «Reactivar» en la fila de `administracion@consultorio-demo.test`
- **THEN** la API responde `403` `RN-AU-05` a los dos pedidos: primero el aviso del panel (que sigue abierto con lo marcado) y después el aviso de la tabla dicen «Tu usuario no tiene permiso para modificar usuarios (RN-AU-05).»
- **AND** la recepcionista sigue con «Recepcionista», `administracion@consultorio-demo.test` sigue «Inactivo» y el dueño sigue en el panel

#### Scenario: US-093 CA-1 Borde - sin permiso y con una contraseña corta se ve el permiso

- **WHEN** el dueño intenta crear un usuario con la contraseña `corta-123`
- **THEN** se ve el mensaje de `RN-AU-05` y no el de `RN-AU-07` (D208)

### Requirement: La sesión que termina en la pantalla vuelve al inicio de sesión

Si la sesión no se puede renovar mientras se usa la pantalla, la interfaz SHALL volver a `/ingresar` con «Tu sesión terminó. Iniciá sesión de nuevo.» y MUST NOT mostrar el mensaje de conexión ni dejar nada a medio guardar (US-092 CA-1; cableado de C-11, D231).

#### Scenario: US-092 CA-1 Borde - una sesión irrenovable al guardar un alta

- **GIVEN** con sesión de la odontóloga, el panel de alta completo y la sesión que ya no se puede renovar
- **WHEN** pulsa «Guardar»
- **THEN** la interfaz vuelve a `/ingresar` con el aviso de sesión terminada
- **AND** no se creó ningún usuario
