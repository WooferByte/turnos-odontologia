# Evidencia: pantallas de contraseñas con Stitch (C-10, `contrasenas-de-usuarios`)

Fecha: 2026-10-26. Regla que lo pide: D234 (toda pantalla del frontend parte de una pantalla generada en Stitch). Cuándo: antes de aprobar el plan (D301, como D288 de C-13). Procedimiento: el de [stitch-bloqueos.md](stitch-bloqueos.md).

**Estado: hechas (2026-10-26, tarea 1.2 del change; D301).** Las dos pantallas se generaron con el MCP `stitch` al primer intento cada una, y el MCP devolvió sus ids directamente (sección 3b). Esta evidencia conserva los pedidos enviados (sección 2).

## 1. Proyecto y design system

- Proyecto existente `projects/14200813501064679723` (el de C-11, C-49, C-09, C-12 y C-13).
- Design system «Clinical Ops», `assets/b683d44391ab410db2dd48aa71ed0b47` (confirmado con `list_design_systems` antes de generar).
- Pantalla de partida de la segunda: «Usuarios» de C-09, `projects/14200813501064679723/screens/a9ea01c76448418b9168e729229a36e5` (citada en el design archivado de `gestion-de-usuarios`). El pedido la describe como variante; Stitch generó una pantalla nueva en el mismo proyecto.

## 2. Pantallas pedidas

`generate_screen_from_text`, de escritorio (`DESKTOP`), modelo `GEMINI_3_8_FLASH`, con el design system de arriba. Como mucho **dos intentos** por pantalla. Solo textos de los specs `contrasenas-de-usuarios` y `pantalla-de-contrasenas` y del design (K14), y los emails ficticios del seed (`.test`); sin pacientes, sin contraseñas reales, sin secretos.

### 2.1 «Mi contraseña»

> Pantalla de escritorio en español (Argentina): «Mi contraseña» del panel de un consultorio odontológico chico. Herramienta administrativa sobria, coherente con las pantallas «Prestaciones», «Usuarios», «Horario» y «Bloqueos» de este proyecto (misma barra superior, marca y estilo «Clinical Ops»). Sin imágenes decorativas, sin fotos, sin textos de marketing.
>
> - Barra superior: marca con ícono simple de diente y «Turnos Odontológicos AR»; pastillas «Prestaciones», «Usuarios», «Horario», «Bloqueos» y «Mi contraseña» (esta última activa, con ícono de llave); a la derecha, botón con borde «Cerrar sesión». Ningún nombre, email ni dato del usuario que inició sesión.
> - Encabezado: título «Mi contraseña».
> - Una sola tarjeta angosta centrada a la izquierda (formulario), con tres campos de tipo contraseña (puntos, nunca el texto en claro), sin botón para ver la contraseña, sin medidor de fortaleza, sin generador: «Contraseña actual»; «Contraseña nueva» con la ayuda «De 10 caracteres a 72 bytes.»; «Repetir contraseña nueva». Debajo, botón primario «Cambiar contraseña» con ícono de llave o candado.
> - Estado de ejemplo de error (alternativo): el campo «Contraseña actual» con borde rojo y debajo el texto rojo con ícono «La contraseña actual no es correcta (RN-AU-09).»
> - Estado de ejemplo de éxito (alternativo, debajo del formulario): aviso verde suave con ícono «Contraseña cambiada. Tus otras sesiones se cerraron.»
>
> Estilo: Inter, primario #0284C7, éxito #16A34A sobre #F0FDF4, error #DC2626 sobre #FEF2F2, radio 4 px en campos y botones, 8 px en tarjetas, sin sombras fuertes.

### 2.2 «Usuarios» con el panel «Restablecer contraseña»

> Pantalla de escritorio en español (Argentina): «Usuarios» del panel de un consultorio odontológico chico, variante de la pantalla «Usuarios» existente de este proyecto (misma barra superior, tabla y panel lateral, estilo «Clinical Ops»), ahora con el panel lateral en modo «Restablecer contraseña». Sin imágenes decorativas, sin avatares con fotos, sin textos de marketing.
>
> - Barra superior: marca con ícono simple de diente y «Turnos Odontológicos AR»; pastillas «Prestaciones», «Usuarios» (activa), «Horario», «Bloqueos» y «Mi contraseña»; a la derecha, botón con borde «Cerrar sesión». Ningún nombre ni dato del usuario que inició sesión.
> - Encabezado: título «Usuarios», subtítulo «Usuarios del consultorio: acceso al panel y roles.» y a la derecha el botón primario «Nuevo usuario» con ícono de más.
> - Arriba de la tabla, aviso de éxito verde suave con ícono: «Contraseña restablecida. Se cerraron las sesiones de recepcion@consultorio-demo.test.»
> - Tabla densa con columnas EMAIL, ROLES, ESTADO, ACCIONES. En ACCIONES de cada fila: «Editar», «Restablecer contraseña» (con ícono de llave) y «Desactivar» o «Reactivar». Filas: odontologa@consultorio-demo.test (insignias «Odontólogo» y «Dueño», «Activo»); recepcion@consultorio-demo.test («Recepcionista», «Activo», fila resaltada como seleccionada); administracion@consultorio-demo.test («Dueño», «Inactivo» en gris con las celdas atenuadas, «Reactivar»).
> - A la derecha, panel lateral: ícono de llave, título «Restablecer contraseña», botón «Cerrar» (X) en el encabezado; el email «recepcion@consultorio-demo.test» como texto de solo lectura; campo de tipo contraseña (puntos, vacío) «Contraseña nueva» con la ayuda «De 10 caracteres a 72 bytes.»; nota informativa con ícono: «Al guardar se cierran todas las sesiones de este usuario.»; pie con «Cancelar» (con borde) y «Guardar» (primario). Sin campo de repetición, sin botón para ver la contraseña, sin medidor de fortaleza ni generador.
> - Como referencia chica (estado alternativo), un error rojo bajo «Contraseña nueva»: «La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).» con el campo con borde rojo.
>
> Estilo: Inter, primario #0284C7, éxito #16A34A sobre #F0FDF4, error #DC2626 sobre #FEF2F2, radio 4 px en campos y botones, 8 px en paneles, sin sombras fuertes.

## 3. Resultado de la generación

| Pantalla | Intento | Modelo | Resultado |
|---|---|---|---|
| «Mi contraseña» | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `4535800185049862126`); `get_screen` la devuelve por ese id. No hizo falta el segundo intento |
| «Usuarios» con «Restablecer contraseña» | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `17192703812869987033`); el MCP reescribió el pedido en uno más detallado (lo devuelve en `prompt`) y sumó por su cuenta un pie de tabla y la insignia «Modificando». No hizo falta el segundo intento |

## 3b. Pantallas obtenidas (2026-10-26)

| Pantalla | Id | Título en Stitch | Tamaño en Stitch | Captura (archivo de Stitch) | HTML (archivo de Stitch) |
|---|---|---|---|---|---|
| «Mi contraseña» | `projects/14200813501064679723/screens/fa6faa69cae34252a7c79e2cb82210c5` | «Mi contraseña - Turnos Odontológicos AR», `DESKTOP` | 2560 × 2048 | `projects/14200813501064679723/files/65cd8733c7324495923097c626f82159` | `projects/14200813501064679723/files/1ec6ad1e21144766a6fc4256a402db0f` |
| «Usuarios» con «Restablecer contraseña» | `projects/14200813501064679723/screens/925f1e4028294cb2bb9bdeeea81ffd09` | «Usuarios - Restablecer contraseña - Turnos Odontológicos AR», `DESKTOP` | 2560 × 2048 | `projects/14200813501064679723/files/b7ee454e82a44c0caf2930db12e307fc` | `projects/14200813501064679723/files/e3bfea639b3248f6864a4d61e24ff4dc` |

- **Cómo se confirmó**: `get_screen` devuelve cada una de las dos pantallas por su id, con los mismos archivos; las dos salieron de `generate_screen_from_text` con `screenMetadata.status` `COMPLETE`.
- **Cómo se descargaron**: con el `downloadUrl` de cada archivo y la cabecera `X-Goog-Api-Key` (la clave sale de `STITCH_API_KEY` en el entorno, nunca escrita en el repo); la respuesta es un JSON con `dataString` (el HTML o la imagen en base64), que se decodificó sin cambios. Las capturas se reducen a 1280 de ancho, como las anteriores.
- **Archivos guardados** en [stitch-contrasenas-pantalla/](stitch-contrasenas-pantalla/):
  - `mi-contrasena.png` (1280 × 1024) y `mi-contrasena.html`;
  - `usuarios-restablecer.png` (1280 × 1024) y `usuarios-restablecer.html`.
  - Los dos HTML usan Tailwind y Google Fonts por CDN (el de usuarios, también Material Symbols): **no se copian**; la implementación los traduce a los tokens CSS del proyecto, sin dependencias nuevas (CSP `default-src 'self'`).
- **Revisión del HTML** (datos y secretos): solo los emails ficticios del seed (`odontologa@`, `recepcion@` y `administracion@consultorio-demo.test`). Sin pacientes, teléfonos, documentos, claves de API ni tokens. Dos valores de ejemplo que **inventó Stitch** dentro de campos de contraseña, ficticios y que no se usan en ninguna parte: `value="secretpassword123"` en «Contraseña actual» de «Mi contraseña» (para mostrar los puntos del estado de error) y `value="corta"` en la tarjeta de referencia del error de `RN-AU-07`. No son contraseñas reales ni de la demo; la implementación nunca precarga un campo de contraseña.

### Qué muestra «Mi contraseña»

La barra del panel con las pastillas «Prestaciones», «Usuarios», «Horario», «Bloqueos» y «Mi contraseña» (activa, con ícono de llave y fondo celeste suave) y «Cerrar sesión» con borde e ícono; el título «Mi contraseña»; una tarjeta angosta a la izquierda con las etiquetas chicas en mayúsculas y asterisco rojo de obligatorio, «Contraseña actual» con borde rojo, ícono de alerta dentro del campo y el error de `RN-AU-09` debajo con ícono, «Contraseña nueva» con la ayuda, «Repetir contraseña nueva» y «Cambiar contraseña» primario a todo el ancho con ícono de candado; debajo de la tarjeta, el aviso de éxito verde suave con ícono; y un pie de página institucional («Módulo de Seguridad y Credenciales · Sede Central»).

### Qué muestra «Usuarios» con «Restablecer contraseña»

La barra con las cinco pastillas, cada una con un ícono, «Usuarios» activa; el encabezado de C-09 con «Nuevo usuario»; el aviso de éxito verde a todo el ancho con «Contraseña restablecida.» en negrita; dos columnas: la tarjeta «Listado general» con «3 usuarios registrados», la tabla con la fila de la recepcionista marcada con borde izquierdo y la insignia «Modificando», la de administración atenuada, y en ACCIONES «Editar», un botón con ícono de llave y el texto **«Restablecer»** (abreviado) y «Desactivar» o «Reactivar» (en la captura la columna ACCIONES queda cortada por el ancho de la tarjeta; el HTML tiene los tres botones), más el pie de tabla «Módulo administrativo con control de integridad clínica» y «Filtrado: 3 de 3 registros»; a la derecha, el panel «Restablecer contraseña» con ícono de llave y «Cerrar» (X), el email en un campo de solo lectura gris con candado («USUARIO / EMAIL»), «CONTRASEÑA NUEVA *» con la ayuda, la nota informativa azul con ícono y el pie «Cancelar» y «Guardar»; debajo, una tarjeta de referencia «Estado alternativo / Validación» con el campo en rojo y el error de `RN-AU-07` en una caja roja suave con ícono.

### Sugerencias de Stitch no aceptadas

- «Mi contraseña»: «Ver versión interactiva con validación en vivo al enviar» (la pantalla no valida el largo: la API decide, D232, D296), «Crear modal de confirmación antes de invalidar otras sesiones» (sin respaldo en la KB; como D250, sin confirmación) y «Generar la vista móvil responsiva» (las pantallas del panel se apilan con el CSS existente; no hay escenario de móvil).
- «Usuarios»: «¿Querés ver el flujo cuando se desactiva un usuario?» (es de C-09, ya implementado), «¿Ajustamos alguna regla o mensaje del estado alternativo?» (los textos son los de K14) y «¿Pasamos a diseñar la pantalla de Agenda o Turnos?» (otro change).

**Qué se toma y qué se rechaza**: en el `design.md` de `contrasenas-de-usuarios`, sección «Referencia visual (Stitch)».

## 4. Cómo se completó (tarea 1.2 del change, hecha el 2026-10-26)

1. [hecho] En una sesión con el MCP `stitch` conectado (`STITCH_API_KEY` en el entorno, `.mcp.json` del repo), confirmar el design system con `list_design_systems` y enviar los dos pedidos de la sección 2.
2. [no hizo falta: el MCP devolvió los ids] Si `generate_screen_from_text` no devuelve el id, buscarlo con `get_project` o `list_screens`, o copiar el `node-id` de la URL del canvas.
3. [hecho] Con los ids, traer la captura y el HTML de cada pantalla (`get_screen` y la descarga de sus archivos) a `stitch-contrasenas-pantalla/`.
4. [hecho] Revisar los HTML: solo datos ficticios, sin pacientes, teléfonos, documentos, claves ni tokens (los dos valores inventados por Stitch están anotados arriba).
5. [hecho] Anotar acá los ids, los intentos y qué muestra cada pantalla, y completar con el `/opsx:update` la sección «Referencia visual (Stitch)» del `design.md` (qué se toma y qué se rechaza).

## 5. Cómo se usa en el change

Son la **referencia visual** del `design.md` de `contrasenas-de-usuarios`. La KB y los specs mandan: los textos son los de `pantalla-de-contrasenas` y del design (K14), y nada de las pantallas agrega reglas de dominio. La traducción visual (tarea 11.1) y la comparación con las capturas en el navegador (tarea 12.1) se hacen en el Apply y se anotan acá al cerrar el change.
