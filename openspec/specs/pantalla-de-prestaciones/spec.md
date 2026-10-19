# pantalla-de-prestaciones Specification

## Purpose
Define cómo el panel muestra y mantiene el catálogo de prestaciones del consultorio desde el navegador: la tabla con activas e inactivas, el alta y la edición con el selector de color, desactivar y reactivar, el aviso de que cambiar la duración no toca los turnos y cómo se muestran los rechazos de la API con su código (US-001; RN-AG-01, RN-AG-02, RN-AG-15, RN-GL-03, RN-GL-04, RN-AU-05) y qué pasa si la sesión termina mientras se usa la pantalla (US-092 CA-1; RN-AU-03). El contrato de la API que consume está en `gestion-de-prestaciones` y `proteccion-del-panel`; la renovación y el aviso de sesión terminada, en `ingreso-al-panel`.

Convenciones de los escenarios: «la pantalla» es la de prestaciones del panel, en `/panel/prestaciones`, con una sesión iniciada (`ingreso-al-panel`). «El panel lateral» es el formulario de alta o de edición que se abre junto a la tabla. «La API» son `GET /prestaciones`, `POST /prestaciones` y `PATCH /prestaciones/{id}`, que la interfaz llama por el mismo origen. «La odontóloga» es `odontologa@consultorio-demo.test` (roles `odontologo` y `dueno`) y «la recepcionista» es `recepcion@consultorio-demo.test` (rol `recepcionista`, activa en estos escenarios). El catálogo de partida son las cinco prestaciones de la demo, con ids 1 a 5: «Consulta / control» 30 min `#1E88E5`, «Limpieza» 45 min `#43A047`, «Obturación» 60 min `#FB8C00`, «Extracción» 45 min `#E53935`, activas, y «Urgencia» 30 min `#8E24AA`, que en estos escenarios está **inactiva** (en la demo arranca activa; para verla inactiva se la desactiva antes desde la pantalla). Ninguna se ofrece en la reserva online. «El aviso de sesión terminada» es el de `ingreso-al-panel`, «Tu sesión terminó. Iniciá sesión de nuevo.». «El aviso del panel» es el aviso `role="alert"` arriba del formulario del panel lateral y «el aviso de la tabla» es el que aparece arriba de la tabla. «El listado general» es la tarjeta que contiene la tabla, con su contador, y «el botón «Cerrar»» es el de la esquina del encabezado del panel lateral (la disposición viene de la pantalla de Stitch, D234; lo puramente visual no tiene escenario). La granularidad es la constante de 5 minutos (D99). Los horarios de los ejemplos están en UTC. Todos los datos son ficticios (RN-PR-01). Los escenarios se verifican en la suite del frontend, con la API reemplazada por un servidor falso que respeta su contrato, y se repiten contra la API real en la prueba en el navegador.

## Requirements

### Requirement: Listar las prestaciones en la pantalla

La pantalla SHALL mostrar, en el orden en que las devuelve la API, todas las prestaciones del consultorio, activas e inactivas, cada una con su color, nombre, duración en minutos, si se ofrece en la reserva online y su estado. Una prestación inactiva SHALL verse atenuada y con la insignia «Inactiva», sin depender solo del color. El listado general SHALL mostrar cuántas prestaciones hay registradas, activas e inactivas, con el texto «N prestaciones registradas» («1 prestación registrada» si hay una), y MUST NOT mostrar el contador mientras carga, sin conexión ni con la lista vacía (US-001 CA-1).

#### Scenario: US-001 CA-1 Feliz - la tabla muestra activas e inactivas

- **GIVEN** la odontóloga en el panel, con el catálogo de partida
- **WHEN** pulsa «Prestaciones» en el encabezado del panel
- **THEN** la interfaz muestra `/panel/prestaciones` y pide `GET /prestaciones` una sola vez
- **AND** la tabla tiene cinco filas en orden de `id`, con «Limpieza», «45 min», una muestra de color `#43A047`, «No» en reserva online y la insignia «Activa»
- **AND** la fila de «Urgencia» se ve atenuada, con la insignia «Inactiva» y la acción «Reactivar»

#### Scenario: US-001 CA-1 Borde - mientras carga se ve «Cargando prestaciones…»

- **GIVEN** la odontóloga en el panel y la respuesta de `GET /prestaciones` retenida por el servidor falso
- **WHEN** se abre la pantalla
- **THEN** la interfaz muestra «Cargando prestaciones…» en lugar de la tabla, sin ninguna fila
- **AND** cuando llega la respuesta, el mensaje desaparece y la tabla muestra las cinco filas

#### Scenario: US-001 CA-1 Borde - un consultorio sin prestaciones

- **GIVEN** la API responde `GET /prestaciones` con una lista vacía
- **WHEN** se abre la pantalla
- **THEN** la interfaz muestra «Todavía no hay prestaciones.» en lugar de la tabla, y el botón «Nueva prestación»

#### Scenario: US-001 CA-1 Borde - sin conexión con la API

- **GIVEN** la API no responde, o responde un error `5xx`
- **WHEN** se abre la pantalla
- **THEN** la interfaz muestra «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» y un botón «Reintentar»
- **AND** al pulsar «Reintentar» con la API ya disponible, muestra la tabla

#### Scenario: US-001 CA-1 Feliz - la recepcionista ve el catálogo

- **GIVEN** la recepcionista en el panel
- **WHEN** abre la pantalla
- **THEN** la interfaz muestra las cinco prestaciones, igual que a la odontóloga (lectura: los tres roles, D205)

#### Scenario: US-001 CA-1 Feliz - el listado general cuenta las prestaciones registradas

- **GIVEN** la odontóloga en la pantalla, con el catálogo de partida
- **WHEN** la tabla termina de cargar
- **THEN** el listado general muestra «5 prestaciones registradas» (cuenta también «Urgencia», que está inactiva)
- **AND** después de crear «Blanqueamiento», 60 minutos, muestra «6 prestaciones registradas»
- **AND** después de pulsar «Desactivar» en «Extracción», sigue mostrando «6 prestaciones registradas»

#### Scenario: US-001 CA-1 Borde - el contador en singular y sin prestaciones

- **GIVEN** la API responde `GET /prestaciones` con una sola prestación, «Consulta / control»
- **WHEN** se abre la pantalla
- **THEN** el listado general muestra «1 prestación registrada»
- **AND** si la API responde una lista vacía, la interfaz muestra «Todavía no hay prestaciones.» y ningún contador; mientras carga o sin conexión tampoco hay contador

### Requirement: Dar de alta una prestación desde la pantalla

«Nueva prestación» SHALL abrir el panel lateral vacío con nombre, duración en minutos, un selector de color que muestra la muestra y el valor hex, y la casilla «Ofrecer en la reserva online». «Guardar» SHALL enviar `POST /prestaciones` y, con `201`, agregar la fila y cerrar el panel. MUST NOT enviar nada si el nombre o la duración están vacíos, ni enviar dos veces mientras espera (US-001 CA-1).

#### Scenario: US-001 CA-1 Feliz - alta de una prestación

- **GIVEN** la odontóloga en la pantalla, sin ninguna prestación «Blanqueamiento»
- **WHEN** pulsa «Nueva prestación», escribe «Blanqueamiento», duración 60, elige el color `#3A7BD5` y pulsa «Guardar»
- **THEN** la interfaz pide `POST /prestaciones` una sola vez con `nombre` «Blanqueamiento», `duracion_minutos` 60, `color` `#3A7BD5` (el hex en mayúsculas, como el catálogo de la demo) y `reservable_online` `false`
- **AND** la tabla muestra una sexta fila «Blanqueamiento», «60 min», activa, y el panel lateral se cierra

#### Scenario: US-001 CA-1 Borde - marcar la reserva online y campos vacíos

- **WHEN** la odontóloga crea «Control de ortodoncia», 30 minutos, con «Ofrecer en la reserva online» marcada
- **THEN** la interfaz manda `reservable_online` `true` y la nueva fila muestra «Sí»
- **AND** si pulsa «Guardar» con el nombre o la duración vacíos, la interfaz no hace ninguna petición y el panel sigue abierto

#### Scenario: US-001 CA-1 Borde - un segundo clic mientras espera no crea dos

- **GIVEN** un alta enviada cuya respuesta todavía no llegó
- **WHEN** se vuelve a pulsar «Guardar»
- **THEN** el botón está deshabilitado y la API recibió un solo `POST /prestaciones`

#### Scenario: US-001 CA-1 Borde - sin conexión al guardar el alta

- **GIVEN** la odontóloga con el panel de alta abierto, con «Blanqueamiento» y duración 60, y la API que no responde o responde un error `5xx`
- **WHEN** pulsa «Guardar»
- **THEN** el aviso del panel muestra «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.»
- **AND** el panel sigue abierto con «Blanqueamiento» y 60, «Guardar» vuelve a estar habilitado y la tabla sigue con cinco filas

### Requirement: El nombre repetido se muestra con RN-AG-15

Si la API rechaza el alta o la edición con `409` y `RN-AG-15`, la pantalla SHALL mostrar debajo del campo nombre «Ya existe una prestación con ese nombre (RN-AG-15).», conservar todo lo escrito en el panel lateral y MUST NOT cambiar la tabla (US-001 CA-1; RN-AG-15).

#### Scenario: US-001 CA-1 Error de negocio - nombre repetido en el alta

- **GIVEN** la odontóloga en la pantalla, con «Limpieza» activa
- **WHEN** crea una prestación «limpieza», 45 minutos
- **THEN** la API responde `409` con `codigos` `["RN-AG-15"]`
- **AND** la interfaz muestra «Ya existe una prestación con ese nombre (RN-AG-15).» debajo del nombre, el panel sigue abierto con «limpieza» y 45, y la tabla sigue con cinco filas

#### Scenario: US-001 CA-1 Error de negocio - renombrar con el nombre de otra prestación

- **GIVEN** la odontóloga editando «Extracción»
- **WHEN** cambia el nombre a «LIMPIEZA» y pulsa «Guardar»
- **THEN** la interfaz muestra el mismo mensaje con `RN-AG-15` debajo del nombre y la fila sigue diciendo «Extracción»

#### Scenario: US-001 CA-1 Borde - un nombre solo de espacios se rechaza como entrada

- **WHEN** la odontóloga crea una prestación con nombre «   » y duración 30
- **THEN** la API responde `422` con `codigos` vacío y un error del campo `nombre`
- **AND** la interfaz muestra «Ingresá un nombre.» debajo del nombre y no agrega ninguna fila

### Requirement: La duración inválida se muestra con RN-AG-01

Si la API rechaza el alta o la edición con `422` y un error del campo `duracion_minutos` con `RN-AG-01`, la pantalla SHALL mostrar debajo de la duración «La duración debe ser mayor que 0 y múltiplo de 5 minutos (RN-AG-01).», conservar lo escrito y MUST NOT cambiar la tabla. La interfaz MUST NOT validar la duración por su cuenta: la decide la API (US-001 CA-2; RN-AG-01).

#### Scenario: US-001 CA-2 Error de negocio - una duración que no es múltiplo de 5

- **GIVEN** la odontóloga en la pantalla
- **WHEN** crea «Blanqueamiento» con duración 47 y pulsa «Guardar»
- **THEN** la interfaz manda el `POST` con `duracion_minutos` 47 y la API responde `422` con `codigos` `["RN-AG-01"]`
- **AND** la interfaz muestra «La duración debe ser mayor que 0 y múltiplo de 5 minutos (RN-AG-01).» debajo de la duración, el campo queda marcado como inválido y la tabla sigue con cinco filas

#### Scenario: US-001 CA-2 Feliz - una duración múltiplo de 5 se acepta

- **WHEN** la odontóloga crea «Blanqueamiento» con duración 45
- **THEN** la nueva fila muestra «45 min» y no hay ningún mensaje de error

#### Scenario: US-001 CA-2 Borde - el cero y los negativos

- **WHEN** la odontóloga crea una prestación con duración 0, o con duración -5
- **THEN** la interfaz manda la petición y muestra el mensaje de `RN-AG-01` debajo de la duración

#### Scenario: US-001 CA-2 Borde - la edición muestra el mismo error y la fila no cambia

- **GIVEN** la odontóloga editando «Limpieza» (45 minutos)
- **WHEN** cambia la duración a 52 y pulsa «Guardar»
- **THEN** la interfaz muestra el mensaje de `RN-AG-01` debajo de la duración y la fila sigue en «45 min»
- **AND** al corregirla a 50 y guardar, la fila muestra «50 min» y el mensaje desaparece

#### Scenario: US-001 CA-2 Borde - con duración inválida y nombre repetido se ve solo RN-AG-01

- **GIVEN** «Limpieza» activa
- **WHEN** la odontóloga crea «Limpieza» con duración 47
- **THEN** la interfaz muestra solo el mensaje de `RN-AG-01`, sin el de `RN-AG-15` (la API informa la entrada antes que la regla de negocio, RN-GL-02)

### Requirement: Editar una prestación desde la pantalla

«Editar» SHALL abrir el panel lateral con los valores actuales de la fila. «Guardar» SHALL enviar `PATCH /prestaciones/{id}` solo con los campos que cambiaron y, con `200`, actualizar la fila con la respuesta y cerrar el panel. «Cancelar» SHALL cerrar el panel sin pedir nada, y el botón «Cerrar» del encabezado del panel SHALL hacer lo mismo, en el alta y en la edición. Mientras el panel edita una prestación, su fila SHALL llevar la marca «Editando», ninguna otra fila MUST llevarla y el encabezado del panel SHALL decir «Modificando los atributos de «<nombre>»»; la marca SHALL desaparecer cuando el panel se cierra (US-001 CA-1).

#### Scenario: US-001 CA-1 Feliz - cambiar solo el color

- **GIVEN** la odontóloga en la pantalla
- **WHEN** pulsa «Editar» en «Limpieza», elige el color `#F9A825` y pulsa «Guardar»
- **THEN** la interfaz pide `PATCH /prestaciones/2` con un cuerpo que tiene solo `color`
- **AND** la fila de «Limpieza» muestra la muestra `#F9A825`, con su nombre, «45 min» y su estado sin cambios

#### Scenario: US-001 CA-1 Borde - cancelar no pide nada

- **GIVEN** la odontóloga editando «Limpieza», con el nombre cambiado a «Limpieza profunda»
- **WHEN** pulsa «Cancelar»
- **THEN** el panel lateral se cierra, la fila sigue diciendo «Limpieza» y la API no recibió ningún `PATCH`

#### Scenario: US-001 CA-1 Borde - guardar sin cambios no pide nada

- **GIVEN** la odontóloga editando «Limpieza», sin tocar ningún campo
- **WHEN** pulsa «Guardar»
- **THEN** el panel lateral se cierra, la fila de «Limpieza» no cambia y la API no recibió ningún `PATCH`

#### Scenario: US-001 CA-1 Feliz - la fila en edición se marca «Editando»

- **GIVEN** la odontóloga en la pantalla, con el catálogo de partida
- **WHEN** pulsa «Editar» en «Limpieza»
- **THEN** la fila de «Limpieza» muestra la marca «Editando» y ninguna otra fila la muestra
- **AND** el encabezado del panel lateral dice «Editar prestación» y «Modificando los atributos de «Limpieza»»

#### Scenario: US-001 CA-1 Borde - la marca «Editando» sigue al panel

- **GIVEN** la odontóloga editando «Limpieza»
- **WHEN** pulsa «Editar» en «Obturación»
- **THEN** la marca «Editando» pasa a la fila de «Obturación» y la de «Limpieza» ya no la tiene
- **AND** al cambiar la duración de «Obturación» a 50 y guardar, el panel se cierra y ninguna fila muestra «Editando»
- **AND** al pulsar «Nueva prestación», ninguna fila muestra «Editando»

#### Scenario: US-001 CA-1 Borde - el botón «Cerrar» del panel no pide nada

- **GIVEN** la odontóloga editando «Limpieza», con el nombre cambiado a «Limpieza profunda»
- **WHEN** pulsa el botón «Cerrar» del encabezado del panel
- **THEN** el panel lateral se cierra, la fila sigue diciendo «Limpieza», sin la marca «Editando», y la API no recibió ningún `PATCH`
- **AND** si abre «Nueva prestación», escribe «Blanqueamiento» y pulsa «Cerrar», el panel se cierra, la API no recibió ningún `POST` y la tabla sigue con cinco filas

#### Scenario: US-001 CA-1 Error de negocio - la prestación ya no existe

- **GIVEN** la odontóloga editando «Urgencia» (id 5), con la duración cambiada a 40, y el servidor falso que ya no tiene la prestación 5 (se quitó después de listar, como pasa si la base de la demo se recrea con la pantalla abierta)
- **WHEN** pulsa «Guardar»
- **THEN** la interfaz pide `PATCH /prestaciones/5` y la API responde `404` con `codigos` `["RN-GL-04"]`
- **AND** la interfaz cierra el panel, muestra «La prestación ya no existe (RN-GL-04).» en el aviso de la tabla y vuelve a pedir `GET /prestaciones` una vez: la tabla queda con cuatro filas, sin «Urgencia»

### Requirement: Desactivar y reactivar una prestación

La acción de la fila SHALL decir «Desactivar» en una prestación activa y «Reactivar» en una inactiva, y SHALL enviar `PATCH /prestaciones/{id}` solo con `activa` `false` o `true`. Con `200`, la fila SHALL seguir en la tabla con su nuevo estado. No hay acción de borrar (US-001 CA-1; RN-GL-03).

#### Scenario: US-001 CA-1 Feliz - desactivar deja la fila atenuada

- **GIVEN** la odontóloga en la pantalla, con «Extracción» activa
- **WHEN** pulsa «Desactivar» en «Extracción»
- **THEN** la interfaz pide `PATCH /prestaciones/4` con el cuerpo `{"activa": false}`
- **AND** la fila de «Extracción» sigue en la tabla, atenuada, con la insignia «Inactiva» y la acción «Reactivar»

#### Scenario: US-001 CA-1 Borde - reactivar una inactiva

- **GIVEN** «Urgencia» inactiva
- **WHEN** la odontóloga pulsa «Reactivar» en «Urgencia»
- **THEN** la interfaz pide `PATCH /prestaciones/5` con `{"activa": true}` y la fila muestra «Activa», sin atenuar, con la acción «Desactivar»
- **AND** ninguna fila ofrece una acción de borrar

#### Scenario: US-001 CA-1 Borde - sin conexión al desactivar

- **GIVEN** la odontóloga en la pantalla, con «Extracción» activa, y la API que no responde o responde un error `5xx`
- **WHEN** pulsa «Desactivar» en «Extracción»
- **THEN** el aviso de la tabla muestra «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.»
- **AND** la fila de «Extracción» sigue «Activa», sin atenuar, y sus botones vuelven a estar habilitados

### Requirement: La edición avisa que la duración no cambia los turnos existentes

El panel lateral de edición SHALL mostrar «Cambiar la duración no modifica los turnos ya creados.» junto a la duración. Cambiar la duración SHALL enviar solo `duracion_minutos` a `PATCH /prestaciones/{id}` y MUST NOT pedir ni modificar ningún turno (US-001 CA-3; RN-AG-02, RN-GL-03).

#### Scenario: US-001 CA-3 Feliz - cambiar la duración actualiza solo la prestación

- **GIVEN** la odontóloga editando «Consulta / control» (30 minutos)
- **WHEN** ve el aviso «Cambiar la duración no modifica los turnos ya creados.», cambia la duración a 60 y pulsa «Guardar»
- **THEN** la interfaz pide `PATCH /prestaciones/1` con un cuerpo que tiene solo `duracion_minutos` 60 y la fila muestra «60 min»
- **AND** la interfaz no hizo ninguna petición a una ruta de turnos

#### Scenario: US-001 CA-3 Borde - el alta no muestra el aviso

- **WHEN** la odontóloga pulsa «Nueva prestación»
- **THEN** el panel lateral no muestra el aviso sobre los turnos ya creados (una prestación nueva no tiene turnos)

### Requirement: Solo el odontólogo modifica; los demás roles leen

«Nueva prestación», «Editar», «Desactivar» y «Reactivar» se muestran a todos los roles: la interfaz no conoce el rol y la regla la garantiza la API (D230). Si la API rechaza un alta, una edición, una desactivación o una reactivación con `403` y `RN-AU-05`, la pantalla SHALL mostrar «Tu usuario no tiene permiso para modificar prestaciones (RN-AU-05).» en el aviso del panel, con el panel abierto y lo escrito conservado, si vino de «Guardar», o en el aviso de la tabla si vino de una acción de fila; MUST NOT cambiar la tabla y MUST NOT terminar ni renovar la sesión. Como la API evalúa el permiso antes que la entrada, un usuario sin permiso ve el mensaje de `RN-AU-05` y nunca uno de validación (matriz de `03`, RN-GL-02, D205, D207, D208).

#### Scenario: US-001 CA-1 Error de negocio - la recepcionista no puede crear

- **GIVEN** la recepcionista en la pantalla
- **WHEN** completa «Blanqueamiento», 60 minutos, y pulsa «Guardar»
- **THEN** la API responde `403` con `codigos` `["RN-AU-05"]`
- **AND** el aviso del panel muestra «Tu usuario no tiene permiso para modificar prestaciones (RN-AU-05).», el panel sigue abierto con «Blanqueamiento» y 60, la tabla sigue con cinco filas y la recepcionista sigue en el panel, sin ninguna petición `POST /auth/refresh`

#### Scenario: US-001 CA-1 Borde - la recepcionista no puede editar

- **GIVEN** la recepcionista editando «Limpieza»
- **WHEN** cambia la duración a 50 y pulsa «Guardar»
- **THEN** la API responde `403` con `codigos` `["RN-AU-05"]` al `PATCH /prestaciones/2`
- **AND** el aviso del panel muestra el mensaje de `RN-AU-05`, el panel sigue abierto con 50 y la fila de «Limpieza» sigue en «45 min»

#### Scenario: US-001 CA-1 Borde - la recepcionista no puede desactivar ni reactivar

- **GIVEN** la recepcionista en la pantalla, con «Limpieza» activa y «Urgencia» inactiva
- **WHEN** pulsa «Desactivar» en «Limpieza» y después «Reactivar» en «Urgencia»
- **THEN** la API responde `403` con `codigos` `["RN-AU-05"]` a los dos `PATCH`
- **AND** el aviso de la tabla muestra el mensaje de `RN-AU-05`, «Limpieza» sigue «Activa» y «Urgencia» sigue «Inactiva»

#### Scenario: US-001 CA-1 Borde - sin permiso se ve RN-AU-05 antes que RN-AG-01

- **GIVEN** la recepcionista en la pantalla
- **WHEN** crea «Blanqueamiento» con duración 47 y pulsa «Guardar»
- **THEN** la API responde `403` con `codigos` `["RN-AU-05"]` (el control de acceso va antes que la validación de entrada, D208)
- **AND** el aviso del panel muestra el mensaje de `RN-AU-05` y debajo de la duración no aparece el mensaje de `RN-AG-01`

### Requirement: La sesión que termina en la pantalla vuelve al inicio de sesión

Las peticiones de la pantalla SHALL pasar por la sesión del panel: un `401` se renueva una vez y la pantalla sigue sin interrupción; si la sesión no se puede renovar, la interfaz SHALL volver a `/ingresar` con el aviso de sesión terminada y MUST NOT mostrar en la pantalla un mensaje de error propio ni aplicar ningún cambio a la tabla. Es el requisito «Un 401 de la API se renueva una vez o termina la sesión» de `ingreso-al-panel` (US-092 CA-1; RN-AU-03), que esta pantalla es la primera en usar (D231).

#### Scenario: US-092 CA-1 Feliz - un access vencido se renueva y la tabla carga

- **GIVEN** la odontóloga con una sesión iniciada a las 12:00 y el reloj marca 12:15 (el access venció; el refresh sigue vigente)
- **WHEN** abre la pantalla
- **THEN** `GET /prestaciones` recibe `401`, la interfaz pide `POST /auth/refresh` una vez y repite el `GET` con el access nuevo
- **AND** la tabla muestra las cinco prestaciones, sin pasar por `/ingresar`

#### Scenario: US-092 CA-1 Error de negocio - una sesión irrenovable al abrir la pantalla vuelve a /ingresar

- **GIVEN** la odontóloga con el access vencido y un refresh que la API ya no acepta
- **WHEN** abre la pantalla
- **THEN** `GET /prestaciones` recibe `401` y `POST /auth/refresh` responde `401` con `codigos` `["RN-AU-03"]`
- **AND** la interfaz muestra `/ingresar` con el aviso de sesión terminada, sin el mensaje de conexión de la pantalla

#### Scenario: US-092 CA-1 Borde - la sesión termina al guardar un alta

- **GIVEN** la odontóloga con el panel de alta abierto, con «Blanqueamiento» y duración 60, cuando el access vence y el refresh deja de valer
- **WHEN** pulsa «Guardar»
- **THEN** `POST /prestaciones` recibe `401` y `POST /auth/refresh` responde `401` con `codigos` `["RN-AU-03"]`
- **AND** la interfaz muestra `/ingresar` con el aviso de sesión terminada y la prestación no se creó en el servidor falso
