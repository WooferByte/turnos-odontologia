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

## 4. Qué falta (tarea 1.2 del change, bloqueante para el frontend)

1. Obtener el id de la pantalla «Usuarios» desde el canvas de Stitch en el navegador (el autor puede copiarlo de la URL), o regenerarla con el texto de la sección 2.
2. `get_screen` con ese id y `download_file` de la captura y del HTML a `stitch-usuarios-pantalla/pantalla.png` y `pantalla.html`.
3. Completar esta evidencia (sección 3b) y sumar al `design.md` del change, con `/opsx:update`, el id y qué se toma y qué se rechaza de la pantalla.

Sin la pantalla, el change de interfaz no se cierra (D234). La API (grupos 2 a 7 de `tasks.md`) no depende de ella.
