# Evidencia: reprogramar un turno con Stitch (C-16, `reprogramar-turno`)

Fecha: 2026-10-29. Regla que lo pide: D234 (toda pantalla del frontend parte de una pantalla generada en Stitch). Cuándo: en el propose, antes de aprobar el plan (como D301 de C-10, C-50, C-14 y C-15). Procedimiento: el de [stitch-agenda.md](stitch-agenda.md) y [stitch-historial.md](stitch-historial.md).

**Estado: hechas (2026-10-29, en el `/opsx:propose` del change).** Las dos pantallas se generaron con el MCP `stitch` al primer intento cada una, y el MCP devolvió sus ids directamente (sección 3b).

## 1. Proyecto y design system

- Proyecto existente `projects/14200813501064679723` (el de C-11, C-49, C-09, C-12, C-13, C-10, C-50, C-14 y C-15).
- Design system «Clinical Ops», `assets/b683d44391ab410db2dd48aa71ed0b47` (confirmado con `list_design_systems` antes de generar).

## 2. Pantallas pedidas

`generate_screen_from_text`, modelo `GEMINI_3_8_FLASH`, con el design system de arriba. Como mucho **dos intentos** por pantalla. Solo textos propuestos en el design de `reprogramar-turno` (Q8 y Q9, así que pueden cambiar si el autor responde otra cosa), los pacientes ficticios del seed («Ana Ejemplo», «Bruno Ficticio», «Carla Inventada»), las prestaciones y colores del seed y los emails ficticios de la demo (`.test`); sin pacientes reales, sin teléfonos, sin contraseñas, sin secretos.

### 2.1 Reprogramar turno con error, escritorio (`DESKTOP`)

> Pantalla de escritorio en español (Argentina): la «Agenda del día» del panel de un consultorio odontológico chico con el panel lateral «Reprogramar turno» abierto a la derecha, mostrando un error. Herramienta administrativa sobria, coherente con las pantallas «Agenda» e «Historial del turno» de este proyecto (misma barra superior horizontal, marca y estilo «Clinical Ops»; sin barra lateral de navegación). Sin imágenes decorativas, sin fotos, sin textos de marketing.
>
> - Barra superior: […] pastillas «Agenda» (activa), «Prestaciones», «Usuarios», «Horario», «Bloqueos» y «Mi contraseña»; a la derecha «recepcion@consultorio-demo.test» con «Recepcionista» […] y el botón con borde «Cerrar sesión».
> - A la izquierda: título «Agenda del día», subtítulo «Horas del consultorio (America/Argentina/Buenos_Aires).», botón primario «Nuevo turno»; barra de fecha con «Día anterior», «02/11/2026», «lunes 2 de noviembre de 2026», «Día siguiente» y «Hoy».
> - Tabla densa con columnas HORA, PACIENTE, PRESTACIÓN, ESTADO y ACCIONES. En ACCIONES, dos botones chicos con borde por fila: «Reprogramar» (ícono de calendario con flecha) y «Historial» (ícono de reloj). […] Filas (datos ficticios): «09:00 – 09:30» «Ana Ejemplo» […] «Consulta / control» chip «Reservado» — esta fila está seleccionada […]; «10:00 – 10:45» «Bruno Ficticio» […] «Limpieza» chip «Reservado»; «11:00 – 12:00» «Carla Inventada» […] «Obturación» chip «Confirmado»; «12:00 – 12:30» «Bruno Ficticio» […] «Consulta / control» chip rojo suave «Cancelado por el paciente» y en ACCIONES solo «Historial» (sin «Reprogramar»).
> - Panel lateral derecho (unos 420 px, borde izquierdo, sombra suave, sin oscurecer la agenda): título «Reprogramar turno» con ícono de calendario y botón «Cerrar» con ícono X. Debajo, el resumen en gris: «Ana Ejemplo · Consulta / control» y «Ahora: lunes 2 de noviembre de 2026, 09:00 – 09:30». Un subtítulo chico «Fecha y hora del consultorio.»
> - Arriba del formulario, un aviso de error rojo suave con ícono: «El profesional y el sillón ya tienen un turno activo en ese horario (RN-AG-05, RN-AG-08).» y debajo, en la misma caja, «El turno no cambió.»
> - Formulario con lo cargado conservado: «Fecha» (selector, 02/11/2026) y «Hora» (10:00) en una fila; «Duración (minutos)» con valor 30 y ayuda gris «Múltiplo de 5 minutos.»; texto gris «Termina a las 10:30.»
> - Pie del panel: botón con borde «Cancelar» y botón primario «Reprogramar».
>
> Estilo: Inter, primario #0284C7, texto #0F172A, texto secundario #64748B, bordes #E2E8F0, fondo #F8FAFC, radio 4 px en botones, 8 px en tarjetas, sin sombras fuertes salvo la del panel lateral, números tabulares en horas y fechas.

(Pedido resumido acá con «[…]»; los textos entre comillas son los enviados.)

### 2.2 Reprogramar turno, angosta (pedida como `MOBILE`)

> Pantalla angosta (celular, unos 390 px de ancho) en español (Argentina): el panel «Reprogramar turno» de la agenda de un consultorio odontológico chico, abierto a todo el ancho debajo de la barra. […] sin desplazamiento horizontal de la página. Sin imágenes decorativas.
>
> - Barra superior en varias filas: […] «odontologa@consultorio-demo.test» con «Odontólogo · Dueño» […] y el botón con borde «Cerrar sesión».
> - Panel a todo el ancho con borde superior: título «Reprogramar turno» con ícono de calendario y botón «Cerrar» con ícono X a la derecha. Resumen en gris: «Bruno Ficticio · Limpieza» y «Ahora: lunes 2 de noviembre de 2026, 10:00 – 10:45». Subtítulo chico «Fecha y hora del consultorio.»
> - Un aviso rojo suave con ícono: «La duración debe ser mayor que 0 y múltiplo de 5 minutos (RN-AG-01).» y debajo «El turno no cambió.»
> - Formulario en una columna: «Fecha» (03/11/2026), «Hora» (15:00), «Duración (minutos)» con valor 42 y borde rojo, ayuda gris «Múltiplo de 5 minutos.».
> - Pie: botón primario de ancho completo «Reprogramar» y debajo botón con borde de ancho completo «Cancelar».
> - Debajo del panel, separado por una línea punteada y con el rótulo gris «Después de reprogramar», un ejemplo chico: aviso verde suave «Turno reprogramado.» sobre una tarjeta de turno «15:00 – 15:45 · Bruno Ficticio · Limpieza · Reservado» con botones con borde «Reprogramar» e «Historial».
>
> Estilo: el mismo de 2.1.

## 3. Resultado de la generación

| Pantalla | Intento | Modelo | Resultado |
|---|---|---|---|
| Reprogramar con error, escritorio | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `13338213438722579541`); `status` `COMPLETE`. No hizo falta el segundo intento |
| Reprogramar, angosta | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `5060009838751063747`); `status` `COMPLETE`. Aunque se pidió `MOBILE`, la metadata dice `deviceType` `DESKTOP` y 2560 × 2220: la captura muestra la columna angosta (unos 390 px) centrada sobre el lienzo de escritorio, como en C-50, C-14 y C-15. Sirve como referencia del acomodo |

## 3b. Pantallas obtenidas (2026-10-29)

| Pantalla | Id | Título en Stitch | Captura (archivo de Stitch) | HTML (archivo de Stitch) |
|---|---|---|---|---|
| Reprogramar con error, escritorio | `projects/14200813501064679723/screens/291535f17cc64edc8c79e1ce09977c42` | «Agenda del día - Reprogramar turno con error - Turnos Odontológicos AR» | `projects/14200813501064679723/files/414bddb332c243acbbcc35a5a7b8a2eb` | `projects/14200813501064679723/files/a72fee8b50fd4670b87cad8b0392ea2e` |
| Reprogramar, angosta | `projects/14200813501064679723/screens/6557792ea9754df08b59484784462c27` | «Agenda del día - Reprogramar turno móvil (Turnos Odontológicos AR)» | `projects/14200813501064679723/files/2e2ea5da276b4473bb42ceccd1112752` | `projects/14200813501064679723/files/a9243826b47d4b24886ae575dcf8e1b6` |

- **Cómo se descargaron**: con el `downloadUrl` de cada archivo y la cabecera `X-Goog-Api-Key` (la clave sale de `STITCH_API_KEY` en el entorno, nunca escrita en el repo); la respuesta es un JSON con `dataString` (el HTML como texto; la imagen en base64), que se decodificó sin cambios. Las capturas se reducen de 2560 de ancho a 1280, como las anteriores.
- **Archivos guardados** en [stitch-reprogramar-pantalla/](stitch-reprogramar-pantalla/): `reprogramar-escritorio.png` y `reprogramar-escritorio.html`; `reprogramar-angosta.png` y `reprogramar-angosta.html`.
- Los dos HTML usan Tailwind (`cdn.tailwindcss.com`) y Google Fonts por CDN (Inter): **no se copian**; la implementación los traduce a los tokens CSS del proyecto, sin dependencias nuevas (CSP `default-src 'self'`).
- **Revisión del HTML** (datos y secretos): solo los emails ficticios de la demo (`recepcion@consultorio-demo.test` en la de escritorio y `odontologa@consultorio-demo.test` en la angosta), los tres pacientes ficticios del seed y las prestaciones y colores del seed. Sin teléfonos, documentos, contraseñas, claves de API ni tokens; Stitch no inventó pacientes ni profesionales.

### Qué muestra la de escritorio

La barra del panel con «Agenda» activa; la agenda a la izquierda (sin atenuar) con la columna «ACCIONES» y, en cada fila activa, los botones con borde «Reprogramar» (ícono de calendario) e «Historial» (ícono de reloj); la fila cancelada solo con «Historial»; la fila de Ana Ejemplo resaltada (fondo celeste y franja izquierda), con su «Reprogramar» con borde azul; el pie «4 turnos agendados» con «Agenda sincronizada en tiempo real». A la derecha, el panel «Reprogramar turno» con ícono de calendario y X; el resumen «Ana Ejemplo · Consulta / control», «Ahora: lunes 2 de noviembre de 2026, 09:00 – 09:30» y «Fecha y hora del consultorio.»; el aviso rojo suave con ícono de alerta, el texto de `RN-AG-05` y `RN-AG-08` (los códigos en negrita subrayada) y «El turno no cambió.»; «Fecha» y «Hora» en una fila (la hora con borde rojo), «Duración (minutos)» con 30, «Múltiplo de 5 minutos.» a la izquierda y «Termina a las 10:30.» a la derecha; y el pie fijo con «Cancelar» y «Reprogramar». Un pie de página institucional («Módulo de Agenda y Turnos del Día · Sede Central»).

### Qué muestra la angosta

Una columna de unos 390 px con la barra en tres filas (marca; pastillas en dos líneas; usuario y «Cerrar sesión») y debajo el panel a todo el ancho (la agenda no se ve): «Reprogramar turno» con la X, el resumen de Bruno Ficticio, el aviso rojo de `RN-AG-01` con «El turno no cambió.», los tres campos en una columna (la duración 42 con borde rojo e ícono de alerta), «Reprogramar» primario a todo el ancho y «Cancelar» debajo; después el separador «DESPUÉS DE REPROGRAMAR» con el aviso verde «Turno reprogramado.» y la tarjeta del turno de las 15:00 con «Reprogramar» e «Historial»; y un pie «Módulo de Agenda Móvil».

### Sugerencias de Stitch no aceptadas

- Escritorio: «Diseñar el estado exitoso tras reprogramar el turno» (la angosta ya lo muestra), «Diseñar la versión móvil…» (es 2.2) y «Ver el modal de confirmación al cancelar un turno activo» (cancelar es de C-17).
- Angosta: «Simular la vista con el modal de confirmación antes de guardar» (el design no pide confirmación), «Diseñar el modal de Historial del turno en versión móvil» (ya existe, C-15) y «Adaptar la vista a estado de error de superposición horaria (RN-AG-05)» (la de escritorio ya lo muestra).

**Qué se toma y qué se rechaza**: en el `design.md` de `reprogramar-turno`, sección «Referencia visual (Stitch)».

## 4. Comparación con la implementación

Hecha el 2026-10-29 en la tarea 12.1, con la demo (`crear_app_demo` y `npm run dev`) y después con Compose, en el navegador integrado de la app. Capturas en `stitch-reprogramar-pantalla/`: `implementacion-reprogramar-escritorio.jpg` (1280 px, REP-1 con el panel abierto) e `implementacion-reprogramar-angosta.jpg` (390 px, el panel). Para que el panel del navegador entrara completo, las capturas se tomaron con la página escalada (`transform: scale`) sin cambiar el ancho de la ventana emulada (1280 y 390 px).

### Recorrido del README («Reprogramar un turno desde la agenda») y resultado

| Paso | Resultado |
|---|---|
| 1. Recepcionista, 02/11/2026, tres turnos (Ana 09:00, Bruno 10:00, Carla 11:00) | Las tres filas tienen «Reprogramar» e «Historial». «Reprogramar» en Ana: «Reprogramar turno», «Ana Ejemplo · Consulta / control», «Ahora: lunes 2 de noviembre de 2026, 09:00 – 09:30», Fecha `2026-11-02`, Hora `09:00`, Duración `30`, «Termina a las 09:30.»; foco en «Fecha», fila de Ana resaltada, ningún pedido |
| 2. Hora 12:30 | «Termina a las 13:00.»; un solo `PATCH /api/turnos/1` y después `GET /api/turnos?fecha=2026-11-02`; «Turno reprogramado.», panel cerrado, Ana de 12:30 a 13:00 después de Carla |
| 3. Solo la duración (Bruno, 60) y a otro día (Ana, 03/11 10:00) | Bruno de 10:00 a 11:00 («Termina a las 11:00.»); la agenda pasa al «martes 3 de noviembre de 2026» con Ana de 10:00 a 10:30 |
| 4. REP-1 (Bruno a las 11:30, sobre Carla) | «El profesional y el sillón ya tienen un turno activo en ese horario (RN-AG-05, RN-AG-08).» y «El turno no cambió.»; el panel sigue abierto y Bruno sigue de 10:00 a 11:00 |
| 5. Duración 42, las 07:30 y controles locales | RN-AG-01 y RN-AG-04 con «El turno no cambió.»; vacío y «media» → «Completá fecha, hora y duración.»; sin cambios → «No cambiaste la fecha, la hora ni la duración.»; ninguno de los tres hace un pedido; «Cancelar» cierra y devuelve el foco a «Reprogramar el turno de Bruno Ficticio, 10:00» |
| 6. Usuaria solo `dueno` (creada para la prueba) | Ve «Reprogramar» en las filas activas (D312) y recibe «Tu usuario no tiene permiso para reprogramar turnos (RN-AU-05).» con «El turno no cambió.» |
| 7. Historial de Ana (V4) | «Turno creado» y dos «Turno reprogramado» con «Por: Usuario n.º 2», «Antes: lunes 2 de noviembre de 2026, 09:00 – 09:30 (30 min)» / «Después: lunes 2 de noviembre de 2026, 12:30 – 13:00 (30 min)» y «Antes: … 12:30 – 13:00 (30 min)» / «Después: martes 3 de noviembre de 2026, 10:00 – 10:30 (30 min)»; «Reprogramar» cierra el historial y «Día siguiente» cierra el panel |
| 8. API | `PATCH /turnos/2` con `{"inicio": "2026-11-02T14:30:00Z"}` → el mismo `409` con `["RN-AG-05", "RN-AG-08"]` y `conflictos`; `/openapi.json` tiene `patch` en `/turnos/{turno_id}` |
| Compose (`http://127.0.0.1:5173`), turno del 9/11/2026 | Reprogramado de 10:15 a 16:00 con un solo `PATCH` y la recarga del día; consola vacía (ninguna violación de la CSP); a 390 px sin desplazamiento horizontal (`scrollWidth` = 390) |

### Corrección hecha en la prueba

- **El campo «Duración (minutos)» salía con 20 px de alto** en lugar de 36 px, como «Fecha» y «Hora». La regla general `.campo input[type='text']` trae `flex: 1 1 0%`, que en la columna flexible de `.campo` le ganaba al `height`. Afectaba también a «N.º de paciente» de «Nuevo turno» (C-14). Se agregó `flex: none` a la regla de los campos de `.panel-de-turno` (que también cubre el panel de reprogramar) y ahora los tres miden 36 px, en la demo y en Compose.

### Diferencias con Stitch y su motivo

- **El panel va dentro de la página, al costado de la agenda**, con el pie dentro de la tarjeta, como «Nuevo turno» e «Historial» (D339), y no como columna de alto completo pegada al borde.
- **El aviso lleva el código entre paréntesis** y no en un chip; los campos no se pintan de rojo (D339).
- **La fila seleccionada** conserva la franja del color de la prestación (C-14) y resalta el botón «Reprogramar».
- Sin el pie «Agenda sincronizada en tiempo real» ni «4 turnos agendados»: el total va en el chip del título, como en C-14.
- A 390 px los campos quedan en una columna, el botón primario arriba de «Cancelar» a todo el ancho y los dos botones de la fila al pie de la tarjeta, como en la captura angosta.
