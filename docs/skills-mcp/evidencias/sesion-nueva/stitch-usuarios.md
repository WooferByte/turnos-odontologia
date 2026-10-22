# Evidencia: pantalla de usuarios con Stitch (C-09, `gestion-de-usuarios`)

Fecha: 2026-10-22. Herramientas del MCP `stitch` ejecutadas por el agente en la sesión del propose. Regla que lo pide: D234 (toda pantalla del frontend parte de una pantalla generada en Stitch).

## 1. Proyecto y design system

- Proyecto existente `projects/14200813501064679723` (el de C-11 y C-49).
- Design system «Clinical Ops», `assets/b683d44391ab410db2dd48aa71ed0b47` (el mismo de las pantallas de prestaciones y de inicio de sesión).

## 2. Pantalla pedida

`generate_screen_from_text`, de escritorio (`DESKTOP`), con el design system de arriba. Texto del primer intento (solo textos de los specs de `gestion-de-usuarios` y `pantalla-de-usuarios` y datos ficticios; sin pacientes, sin contraseñas, sin secretos):

> Pantalla de escritorio en español (Argentina): «Usuarios» del panel de un consultorio odontológico chico. Herramienta administrativa sobria, coherente con las pantallas «Prestaciones» e «Inicio de sesión» de este proyecto (misma barra superior, marca, tokens y estilo «Clinical Ops»). Sin imágenes decorativas, sin avatares con fotos, sin textos de marketing.
>
> - Barra superior: marca con ícono simple de diente y «Turnos Odontológicos AR»; navegación con dos pastillas «Prestaciones» y «Usuarios» (esta última marcada como activa); a la derecha, botón con borde «Cerrar sesión» con ícono de salida. Ningún nombre ni dato del usuario que inició sesión.
> - Encabezado de la pantalla: título «Usuarios», subtítulo «Usuarios del consultorio: acceso al panel y roles.» y a la derecha un botón primario «Nuevo usuario» con ícono de más.
> - Tarjeta «Listado general» con una insignia «3 usuarios registrados». Tabla densa (filas de 40 px, encabezado en mayúsculas de 11 px) con columnas EMAIL, ROLES, ESTADO, ACCIONES: odontologa@consultorio-demo.test (insignias «Odontólogo» y «Dueño», «Activo», «Editar» y «Desactivar»); recepcion@consultorio-demo.test («Recepcionista», «Activo», fila resaltada como en edición con la insignia «Editando»); administracion@consultorio-demo.test («Dueño», «Inactivo» en gris con las celdas atenuadas, «Editar» y «Reactivar»).
> - A la derecha, panel lateral de edición: ícono de lápiz, «Editar usuario», subtítulo «Modificando los roles de «recepcion@consultorio-demo.test»», botón «Cerrar» (X); el email de solo lectura; grupo «ROLES» con las casillas «Odontólogo», «Recepcionista» (marcada) y «Dueño»; pie con «Cancelar» y «Guardar».
> - Arriba de la tabla, aviso de error con ícono, fondo rojo suave y borde rojo: «El consultorio no puede quedar sin un odontólogo activo, y nadie puede desactivarse a sí mismo (RN-AU-06).»
> - Como referencia chica, una tarjeta del panel en modo alta: «EMAIL», «CONTRASEÑA INICIAL» (tipo contraseña, vacía, con la ayuda «De 10 caracteres a 72 bytes»), las casillas de roles sin marcar y un error de campo bajo el email: «Ya existe un usuario con ese email (RN-AU-08).»
>
> Estilo: Inter, primario #0284C7, error #DC2626 sobre #FEF2F2, éxito #16A34A sobre #F0FDF4, radio 4 px en campos y botones, 8 px en paneles, sin sombras fuertes.

## 3. Resultado: la pantalla no quedó disponible

| Intento | Modelo | Texto | Resultado |
|---|---|---|---|
| 1 | `GEMINI_3_8_FLASH` | El de la sección 2 | `The operation timed out` (tiempo de espera del cliente) |
| 2 | `GEMINI_3_8_FLASH` | El mismo, más corto | `The operation timed out` |
| 3 | `GEMINI_3_5_FLASH_LITE` | Versión resumida (sin la tarjeta de alta) | Respondió con un texto («Ya tenemos disponible la pantalla de «Usuarios» del panel de control odontológico… Puedes visualizarla en el canvas.») y tres sugerencias, pero **sin el id de la pantalla** ni sus archivos |

- Después de cada intento se consultó `list_screens` (devuelve `{}` para este proyecto, también para las pantallas de C-11 y C-49, que `get_screen` sí encuentra por id) y `get_project` (no trae `screenInstances`; su `updateTime` avanzó con cada intento, señal de que la generación llegó al proyecto).
- Con el MCP **no hay forma de obtener el id** de la pantalla generada: no se descargó captura ni HTML y la carpeta `stitch-usuarios-pantalla/` todavía no existe.
- Las sugerencias de Stitch («Ver pantalla de Prestaciones», «Simular alta de nuevo usuario», «Modificar permisos de roles») no se aceptaron.

## 3b. Pantalla obtenida (tarea 1.2, 2026-10-22)

- **Cómo se obtuvo el id**: la tercera generación del propose quedó en el canvas de Stitch sin que el MCP devolviera su id. El autor abrió el proyecto en la web de Stitch y copió el `node-id` de la URL de la pantalla el 2026-10-22.
- **Pantalla**: `projects/14200813501064679723/screens/a9ea01c76448418b9168e729229a36e5`, «Usuarios - Turnos Odontológicos AR», `DESKTOP`, 2560 × 2126 en Stitch. `get_screen` la devuelve por su id.
- **Rareza de `list_screens`**: después de obtener el id, `list_screens` sigue devolviendo `{}` para el proyecto (como con las pantallas de C-11 y C-49). La única forma de llegar a una pantalla desde el MCP es tener su id; si una generación no lo devuelve, hay que sacarlo del canvas.
- **Archivos guardados** en [stitch-usuarios-pantalla/](stitch-usuarios-pantalla/):
  - `pantalla.png`: la captura (`projects/14200813501064679723/files/2cb23b170419458e8df3b9b10d82c07a`), descargada a 1280 × 1063 (el ancho de las de C-11 y C-49; el alto sigue la proporción de la pantalla);
  - `pantalla.html`: el HTML generado (`projects/14200813501064679723/files/7a554220d1964fafb7a1d17791bec5e6`), descargado con `download_file`. Usa Tailwind, Google Fonts (Inter) y Material Symbols por CDN, así que **no se copia**: la implementación lo traduce a los tokens CSS del proyecto, sin dependencias nuevas.
- **Revisión del HTML** (datos y secretos): solo emails ficticios del dominio `consultorio-demo.test` (`odontologa@`, `recepcion@`, `administracion@`); sin nombres de personas, pacientes, teléfonos ni documentos. Trae, en el campo «Contraseña inicial» de la tarjeta de alta, un valor de ejemplo inventado por Stitch (`type="password"`, se ve como puntos): no es un secreto del proyecto, no se usa y la implementación arranca con los campos vacíos. Ninguna clave ni token.
- **Qué muestra**: la barra del panel (marca, pastillas «Prestaciones» y «Usuarios» activa, «Cerrar sesión», sin datos de quien inició sesión); «Usuarios» con el subtítulo y «Nuevo usuario»; el aviso de `RN-AU-06` con el título «No se pudo completar:» y el texto exacto de U19; la tarjeta «Listado general» con «3 usuarios registrados» y la tabla EMAIL / ROLES / ESTADO / ACCIONES (odontóloga con «Odontólogo» y «Dueño»; recepcionista «Editando»; `administracion@` inactivo, atenuado, con «Reactivar»); el panel «Editar usuario» (subtítulo «Modificando los roles de «recepcion@consultorio-demo.test»», casillas de roles, «Cancelar» y «Guardar»); y la tarjeta de referencia «Nuevo usuario» con el error «Ya existe un usuario con ese email (RN-AU-08).» y la ayuda «De 10 caracteres a 72 bytes».
- **Lo que Stitch agregó sin que se pidiera** (se rechaza en el design, «Referencia visual (Stitch)»): la insignia «OPS DENTAL», la etiqueta «CONTROL CLÍNICO», el pie de la tabla («Módulo administrativo con control de integridad clínica», «Filtrado: 3 de 3 registros»), la insignia «Alta administrativa», el botón «Crear usuario», el «+» repetido en «+ Nuevo usuario», el tachado del email inactivo, el botón «Cerrar» (X) del panel y la nota «Quitar o asignar un rol vale desde la próxima acción del usuario, sin cerrar su sesión.» (estos dos últimos quedan como pregunta Q12 del design).

## 4. Cómo se usa en el change

Es la **referencia visual** del `design.md` de `gestion-de-usuarios` (sección «Referencia visual (Stitch)»: qué se toma y qué se rechaza). La KB y los specs mandan: los textos son los de U19 y de `pantalla-de-usuarios`, y nada de la pantalla agrega reglas de dominio. La traducción visual es la tarea 12.1 y la comparación con la captura, la prueba en el navegador (grupo 13), que se anota acá al cerrar el change.

## 5. Prueba en el navegador (tarea 13.1, 2026-10-22)

Hecha por el agente en el navegador del panel, con la demo (`crear_app_demo`, recién arrancada) y `npm run dev` (`127.0.0.1:5173`). La «otra ventana privada» se simuló con una segunda pestaña: el refresh token vive en `sessionStorage`, que es propio de cada pestaña, así que las dos sesiones (odontóloga y recepcionista) no se pisan. Datos y contraseñas ficticios; ningún token ni contraseña apareció en una URL (solo `/panel/usuarios` e `/ingresar`) ni en la consola.

### Resultado paso a paso (demo)

| Paso | Esperado | Observado | Ok |
|---|---|---|---|
| Listar como odontóloga | Tabla con 2 usuarios, «2 usuarios registrados», `GET /api/usuarios` `200` | Igual | sí |
| Alta `turnos@consultorio-demo.test` | `201`, panel cerrado, 3.ª fila, «3 usuarios registrados»; al reabrir, campos vacíos | Igual | sí |
| Contraseña `corta-123` | `422`, «La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).» bajo el campo | Igual | sí |
| Email de la recepcionista | `409`, «Ya existe un usuario con ese email (RN-AU-08).» bajo el email | Igual (captura `implementacion-alta-409.jpg`) | sí |
| X «Cerrar» del panel | Cierra sin pedir nada; la tabla no cambia | Igual | sí |
| «Editar» y «Guardar» sin cambios | Sin `PATCH` | Sin petición; el panel se cierra | sí |
| Sumar «Dueño» a la recepcionista | `PATCH /api/usuarios/2` con cuerpo solo `roles`, `200` | Cuerpo `{"roles":["recepcionista","dueno"]}`, `200` | sí |
| Desactivar a la recepcionista (con su pestaña abierta) | `PATCH {"activo":false}` `200`; fila atenuada, «Inactivo», «Reactivar» | Igual (captura `implementacion-edicion-e-inactiva.jpg`) | sí |
| Siguiente acción de la recepcionista | `401`, refresh `401`, vuelve a `/ingresar` con «Tu sesión terminó. Iniciá sesión de nuevo.» | Igual | sí |
| Reactivar y nuevo inicio de sesión de ella | `PATCH {"activo":true}` `200`; login `200` | Igual | sí |
| Odontóloga: «Desactivar» en su fila | `409` `RN-AU-06`, aviso «No se pudo completar» + texto de U19 | Igual (captura `implementacion-aviso-rn-au-06.jpg`) | sí |
| Odontóloga: quitarse «Odontólogo» y «Guardar» | `409` `RN-AU-06` en el aviso del panel, que sigue abierto | Igual; cuerpo `{"roles":["dueno"]}` (captura `implementacion-aviso-panel-rn-au-06.jpg`) | sí |
| Recepcionista sin «Dueño» abre «Usuarios» | `403`, «Acceso restringido» + «Tu usuario no tiene permiso para ver los usuarios (RN-AU-05).» | Igual | sí |
| Recepcionista (con la tabla ya cargada) «Desactivar» | `403` `RN-AU-05` «…modificar usuarios…», sin perder la sesión | Igual | sí |
| Alta por la pantalla de `dueno@consultorio-demo.test` (solo «Dueño») | `201` con `roles: ["dueno"]` | Igual | sí |
| Ese usuario inicia sesión y ve la tabla | Tabla completa | Igual (vuelve a `/panel/usuarios`) | sí |
| Como dueño: crear, desactivar, editar roles y reactivar | `403` `RN-AU-05` en cada uno, sin perder la sesión | `POST` y `PATCH` (desactivar, roles y reactivar) → `403`; mismo aviso; seguía en `/panel/usuarios` | sí |
| «Un usuario que ya no existe» | Solo contra el servidor falso (la API real no borra, H10) | No se repite acá (lo cubre `PaginaUsuarios.test.tsx`) | n/a |

Consola de la demo: solo los «Failed to load resource» del navegador por los `4xx` esperados (`401`, `403`, `409`, `422`); ningún error de la aplicación. Se vio un «[vite] server connection lost» sin consecuencias (reinicio del servidor de desarrollo).

### Compose y V5

Con `docker compose up -d --build` (imágenes reconstruidas con el código actual; `127.0.0.1:5173` y `127.0.0.1:8000`):

- **V5 parcial**: la respuesta trae `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'`; el paquete servido contiene la pantalla de usuarios (textos «Usuarios del consultorio» y `RN-AU-06`); solo se cargan `/assets/index-*.js` e `index-*.css` del mismo origen; con una contraseña equivocada se ve el `401` `RN-AU-04` y la consola solo muestra los `401` esperados, sin violaciones de la CSP. Revisión estática de `frontend/src`: la pantalla de usuarios no usa atributos `style=`, `url(...)`, `@import` ni direcciones externas (el único `style` del proyecto es el color de relleno de `TablaDePrestaciones`, de C-11, que React aplica por CSSOM). Los íconos son SVG en línea.
- **Lo que no se pudo hacer**: iniciar sesión en Compose, porque la contraseña del usuario del seed está en `SEED_USUARIO_PASSWORD` de `.env`, que el agente no lee. Por eso la pantalla de usuarios **no se vio renderizada bajo la CSP** (consola de V5 con la pantalla abierta y su recorrido abreviado): quedan para la tarea 13.2 del autor.
- Al terminar: `docker compose stop` (sin borrar volúmenes).

### Comparación con `stitch-usuarios-pantalla/pantalla.png`

Capturas de la implementación en [stitch-usuarios-pantalla/](stitch-usuarios-pantalla/), con el escritorio a 1280 px de ancho y reducidas al 62,5 % (el panel de capturas solo entrega 800 × 625 píxeles; la página de 1280 se escaló con un `transform` puesto desde la consola para que entrara entera, sin tocar el código):

- `implementacion-alta-409.jpg`: panel de alta con el `409` `RN-AU-08`;
- `implementacion-edicion-e-inactiva.jpg`: fila en edición («Editando», «Editar» relleno), fila inactiva atenuada con «Reactivar» y el panel de edición con la nota de roles;
- `implementacion-aviso-rn-au-06.jpg`: el aviso «No se pudo completar» de la tabla;
- `implementacion-aviso-panel-rn-au-06.jpg`: el mismo aviso dentro del panel de edición.

Coincide con Stitch en: encabezado y botón «Nuevo usuario», tarjeta «Listado general» con contador, tabla densa (EMAIL / ROLES / ESTADO / ACCIONES), insignias, «Activo» verde e «Inactivo» gris, fila «Editando» con borde izquierdo azul, fila inactiva atenuada, panel de edición con email de solo lectura, casillas en columna, nota informativa, «Cancelar» / «Guardar», botón X, aviso rojo con ícono y título, error de campo en rojo y ayuda «De 10 caracteres a 72 bytes.».

Diferencias, todas previstas en «Referencia visual (Stitch)» del `design.md`:

| Diferencia | Motivo |
|---|---|
| Las pastillas «Prestaciones» / «Usuarios» van a la izquierda, junto a la marca (Stitch las centra) | La barra del panel es la de C-08 y C-11, compartida; este change no la rediseña |
| Sin «OPS DENTAL», «CONTROL CLÍNICO» ni el pie de la tabla («Filtrado: 3 de 3 registros») | Textos sin respaldo en la KB; no hay filtros ni paginación |
| No hay tarjeta de alta bajo la de edición: el panel es uno solo (`cerrado / alta / edicion`) | U18; la tarjeta de alta era una referencia |
| El alta usa «Cancelar» / «Guardar», no «Crear usuario» ni «Alta administrativa» | El spec dice «Guardar» |
| El email de la fila inactiva no va tachado | No sugerir un borrado (RN-GL-03) |
| «Desactivar» es rojo también en la fila en edición (Stitch lo muestra neutro ahí) | Una sola regla de estilo para la acción |
| El aviso de `RN-AU-06` aparece solo cuando ocurre; tras un error en el panel se ve dentro de él | Los estados no se muestran todos a la vez; U19 |
| Fuente Inter solo si está instalada en el equipo | Sin CDN (CSP `default-src 'self'`) |
| Las insignias de rol son todas iguales (Stitch las coloreaba por rol) | El rol lo dice el texto; el color no significa nada |
| La captura de Stitch muestra tres filas de ejemplo con otros datos (`administracion@…`) | Los datos de la demo son otros; el diseño de la fila inactiva es el mismo |

### Paso a paso para el autor (tarea 13.2)

Con la demo recién arrancada (`python -m uvicorn app.main:crear_app_demo --factory` en `backend/` y `npm run dev` en `frontend/`), usuarios `odontologa@consultorio-demo.test` y `recepcion@consultorio-demo.test`, contraseña `demo-consultorio-2026`. Para la segunda sesión abrí una **ventana privada** (o una pestaña nueva: la sesión es por pestaña).

1. Ingresá como la odontóloga y pulsá «Usuarios». Deberías ver 2 usuarios y «2 usuarios registrados».
2. **Corte de sesión al desactivar.** En la ventana privada ingresá como la recepcionista y dejala en una pantalla del panel. En la primera ventana, «Desactivar» a la recepcionista (la fila queda atenuada con «Inactivo»). En la ventana privada hacé cualquier acción (por ejemplo, pulsar «Prestaciones»): deberías volver a `/ingresar` con «Tu sesión terminó. Iniciá sesión de nuevo.». Mientras esté inactiva, su contraseña no entra. «Reactivar» en la primera ventana y volvé a ingresar como ella: entra.
3. **Los dos `409` `RN-AU-06`.** Como la odontóloga: (a) «Desactivar» en su propia fila → aviso rojo «No se pudo completar» con «El consultorio no puede quedar sin un odontólogo activo y nadie puede desactivarse a sí mismo (RN-AU-06).»; (b) «Editar» en su fila, desmarcá «Odontólogo», «Guardar» → el mismo mensaje dentro del panel, que sigue abierto. Ninguna de las dos cambia la tabla.
4. **Alta y errores.** «Nuevo usuario»: `turnos@consultorio-demo.test` / `clave-ficticia-2026` / «Recepcionista» → aparece la fila (3 usuarios). Repetilo con la contraseña `corta-123` (error `RN-AU-07` bajo la contraseña) y con el email `recepcion@consultorio-demo.test` (error `RN-AU-08` bajo el email). La X cierra el panel sin pedir nada.
5. **Roles.** «Editar» en la recepcionista, sumá «Dueño», «Guardar»: la fila muestra los dos roles. Después sacale «Dueño». «Editar» + «Guardar» sin tocar nada no hace nada.
6. **Sin permiso.** Con la recepcionista sin «Dueño», «Usuarios» muestra «Acceso restringido» con «…permiso para ver los usuarios (RN-AU-05)». Creá por la pantalla un usuario solo «Dueño»; ingresá con él: ve la tabla, pero crear, desactivar, editar roles y reactivar dan «…permiso para modificar usuarios (RN-AU-05)» sin cerrar la sesión.
7. **Compose** (`docker compose up -d`, `http://127.0.0.1:5173`, el usuario del seed con la contraseña de `SEED_USUARIO_PASSWORD` de tu `.env`): repetí un recorrido breve (listar, alta, desactivar y reactivar) con la consola abierta: no deben aparecer errores de CSP («Refused to…») ni recursos de otro origen, y los íconos deben verse. Al terminar: `docker compose stop`.
8. Ningún token ni contraseña debe aparecer en la barra de direcciones ni en la consola.
