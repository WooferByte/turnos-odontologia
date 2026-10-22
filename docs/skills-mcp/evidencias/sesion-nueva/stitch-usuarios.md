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
