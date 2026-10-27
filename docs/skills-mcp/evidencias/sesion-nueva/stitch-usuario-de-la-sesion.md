# Evidencia: encabezado del panel con el usuario de la sesión en Stitch (C-50, `usuario-de-la-sesion`)

Fecha: 2026-10-27. Regla que lo pide: D234 (toda pantalla del frontend parte de una pantalla generada en Stitch). Cuándo: en el propose, antes de aprobar el plan (como D301 de C-10). Procedimiento: el de [stitch-contrasenas.md](stitch-contrasenas.md).

**Estado: hechas (2026-10-27, en el `/opsx:propose` del change).** Las dos pantallas se generaron con el MCP `stitch` al primer intento cada una, y el MCP devolvió sus ids directamente (sección 3b).

## 1. Proyecto y design system

- Proyecto existente `projects/14200813501064679723` (el de C-11, C-49, C-09, C-12, C-13 y C-10).
- Design system «Clinical Ops», `assets/b683d44391ab410db2dd48aa71ed0b47` (confirmado con `list_design_systems` antes de generar).
- La pantalla de fondo es «Prestaciones» (C-11): el change solo cambia la barra superior, compartida por todas las pantallas del panel.

## 2. Pantallas pedidas

`generate_screen_from_text`, modelo `GEMINI_3_8_FLASH`, con el design system de arriba. Como mucho **dos intentos** por pantalla. Solo textos de los specs `usuario-de-la-sesion` y `encabezado-del-panel` y los emails ficticios del seed (`.test`); sin pacientes, sin contraseñas, sin secretos.

### 2.1 Escritorio (`DESKTOP`)

> Pantalla de escritorio en español (Argentina): panel de un consultorio odontológico chico con la barra superior que ahora muestra qué usuario inició sesión. Herramienta administrativa sobria, coherente con las pantallas «Prestaciones», «Usuarios», «Horario», «Bloqueos» y «Mi contraseña» de este proyecto (misma barra superior horizontal, marca y estilo «Clinical Ops»; sin barra lateral). Sin imágenes decorativas, sin fotos ni avatares con foto, sin textos de marketing.
>
> - Barra superior (lo importante de esta pantalla), de izquierda a derecha: marca con ícono simple de diente y «Turnos Odontológicos AR»; pastillas de navegación «Prestaciones» (activa, fondo celeste suave), «Usuarios», «Horario», «Bloqueos» y «Mi contraseña»; a la derecha, un indicador del usuario de la sesión: ícono simple de persona, el email «odontologa@consultorio-demo.test» en texto oscuro y debajo, en texto chico gris, los roles «Odontólogo · Dueño»; separado por una línea vertical fina, el botón con borde «Cerrar sesión» con ícono de salida. El indicador es solo texto, no es un menú desplegable ni un botón.
> - Debajo, el contenido de la pantalla «Prestaciones» como fondo de referencia: título «Prestaciones», subtítulo «Catálogo de prestaciones del consultorio.», botón primario «Nueva prestación», y una tabla densa con columnas NOMBRE, DURACIÓN, COLOR, ESTADO, ACCIONES y tres filas ficticias: «Consulta» 30 min, «Limpieza» 45 min, «Extracción simple» 60 min, todas «Activa», con acciones «Editar» y «Desactivar».
>
> Estilo: Inter, primario #0284C7, texto #0F172A, texto secundario #64748B, bordes #E2E8F0, fondo #F8FAFC, radio 4 px en botones, 8 px en tarjetas, sin sombras fuertes.

### 2.2 Angosta (pedida como `MOBILE`)

> Pantalla angosta (celular, unos 390 px de ancho) en español (Argentina): el mismo panel de un consultorio odontológico chico, con la barra superior que muestra qué usuario inició sesión. Estilo «Clinical Ops», sobrio, sin imágenes, sin fotos ni avatares con foto, sin barra lateral ni barra inferior de navegación nueva.
>
> - Barra superior que se acomoda en varias filas, sin desplazamiento horizontal de la página:
>   - Fila 1: marca con ícono simple de diente y «Turnos Odontológicos AR».
>   - Fila 2: las pastillas de navegación «Prestaciones» (activa, fondo celeste suave), «Usuarios», «Horario», «Bloqueos» y «Mi contraseña», que pasan a la línea siguiente si no entran.
>   - Fila 3: a la izquierda, el indicador del usuario de la sesión: ícono simple de persona, el email «recepcion@consultorio-demo.test» en texto oscuro (si no entra, se corta con puntos suspensivos al final) y debajo, en texto chico gris, el rol «Recepcionista»; a la derecha, el botón con borde «Cerrar sesión» con ícono de salida. El indicador es solo texto, no es un menú.
> - Debajo, como fondo de referencia: título «Prestaciones» y una lista de tres prestaciones ficticias («Consulta» 30 min, «Limpieza» 45 min, «Extracción simple» 60 min), todas «Activa».
>
> Estilo: Inter, primario #0284C7, texto #0F172A, texto secundario #64748B, bordes #E2E8F0, fondo #F8FAFC, radio 4 px en botones, 8 px en tarjetas.

## 3. Resultado de la generación

| Pantalla | Intento | Modelo | Resultado |
|---|---|---|---|
| Escritorio | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `7721969686606026323`); `status` `COMPLETE`. No hizo falta el segundo intento |
| Angosta | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `10655379982725096401`); `status` `COMPLETE`. Aunque se pidió `MOBILE`, la metadata dice `deviceType` `DESKTOP` y 2560 × 2048: la captura muestra la columna angosta (unos 390 px) centrada sobre el lienzo de escritorio. Sirve como referencia del acomodo en tres filas; no hizo falta el segundo intento |

## 3b. Pantallas obtenidas (2026-10-27)

| Pantalla | Id | Título en Stitch | Captura (archivo de Stitch) | HTML (archivo de Stitch) |
|---|---|---|---|---|
| Escritorio | `projects/14200813501064679723/screens/96c5900aaf8b4db18311a9baa8eafe75` | «Prestaciones con usuario en sesión - Turnos Odontológicos AR» | `projects/14200813501064679723/files/8b3e7d6848a949768e421edcb7b567e4` | `projects/14200813501064679723/files/7e963da4d02e420aa882a240b65e1d2d` |
| Angosta | `projects/14200813501064679723/screens/3078f94a4d474bff80154f884ccfa84f` | «Prestaciones - Móvil (Turnos Odontológicos AR)» | `projects/14200813501064679723/files/41d5929845d449f78b29c8e6adfcfa92` | `projects/14200813501064679723/files/2f7445c288e4405d9ecc5e50197f5b3a` |

- **Cómo se descargaron**: con el `downloadUrl` de cada archivo y la cabecera `X-Goog-Api-Key` (la clave sale de `STITCH_API_KEY` en el entorno, nunca escrita en el repo); la respuesta es un JSON con `dataString` (el HTML como texto; la imagen en base64), que se guardó sin cambios. Las capturas se reducen de 2560 × 2048 a 1280 × 1024, como las anteriores.
- **Archivos guardados** en [stitch-usuario-de-la-sesion-pantalla/](stitch-usuario-de-la-sesion-pantalla/):
  - `encabezado-escritorio.png` y `encabezado-escritorio.html`;
  - `encabezado-angosto.png` y `encabezado-angosto.html`.
  - Los dos HTML usan Tailwind (`cdn.tailwindcss.com`), Google Fonts y Material Symbols por CDN: **no se copian**; la implementación los traduce a los tokens CSS del proyecto, sin dependencias nuevas (CSP `default-src 'self'`).
- **Revisión del HTML** (datos y secretos): solo los emails ficticios del seed (`odontologa@consultorio-demo.test` y `recepcion@consultorio-demo.test`) y los colores de las prestaciones de ejemplo. Sin pacientes, teléfonos, documentos, contraseñas, claves de API ni tokens.

### Qué muestra la de escritorio

La barra del panel con la marca, las cinco pastillas («Prestaciones» activa) y, a la derecha, un círculo gris con un ícono de persona, el email en seminegrita oscura y debajo «Odontólogo · Dueño» en gris chico, una línea vertical fina y «Cerrar sesión» con borde e ícono. Debajo, «Prestaciones» con «Nueva prestación», una tarjeta «Listado general» con «3 prestaciones» y «Módulo administrativo», la tabla con el color en código hexadecimal, el pie «Mostrando 3 de 3 registros» y «Agenda sincronizada», y un pie de página institucional («Módulo de Prestaciones y Catálogo Clínico»).

### Qué muestra la angosta

Una columna de unos 390 px con la barra en tres filas: la marca; las pastillas que pasan a una segunda línea («Mi contraseña» abajo); y, separada por una línea fina, el indicador (círculo con persona, `recepcion@consultorio-demo...` cortado con puntos suspensivos y «Recepcionista» debajo) a la izquierda y «Cerrar sesión» a la derecha. Debajo, «Prestaciones» con «+ Nueva», tarjetas por prestación con su duración y acciones, el pie «Sincronizado» y un pie de página «Sede Central».

### Sugerencias de Stitch no aceptadas

- Escritorio: «¿Querés que prepare el modal o panel lateral para crear una "Nueva prestación"?» (es de C-11, ya implementado), «¿Te gustaría ver el estado cuando el usuario activo tiene solo el rol "Recepcionista"?» (lo cubre la angosta y el spec) y «¿Deseás ajustar las columnas o agregar filtros…?» (otro change).
- Angosta: «Ver el modal de edición de una prestación en versión móvil», «Adaptar la vista de Horarios…» y «Simular el estado al presionar "Cerrar sesión"…» (fuera de este change; cerrar sesión ya está especificado en `ingreso-al-panel`).

**Qué se toma y qué se rechaza**: en el `design.md` de `usuario-de-la-sesion`, sección «Referencia visual (Stitch)».

## 4. Comparación con la implementación

Pendiente de la prueba en el navegador del Apply (tarea 9.1 del change): capturas de la implementación a 1280 px y a 390 px junto a estas, con las diferencias y su motivo.
