# Evidencia: agenda del día con Stitch (C-14, `agenda-del-dia`)

Fecha: 2026-10-28. Regla que lo pide: D234 (toda pantalla del frontend parte de una pantalla generada en Stitch). Cuándo: en el propose, antes de aprobar el plan (como D301 de C-10 y C-50). Procedimiento: el de [stitch-usuario-de-la-sesion.md](stitch-usuario-de-la-sesion.md) y [stitch-contrasenas.md](stitch-contrasenas.md).

**Estado: hechas (2026-10-28, en el `/opsx:propose` del change).** Las tres pantallas se generaron con el MCP `stitch` al primer intento cada una, y el MCP devolvió sus ids directamente (sección 3b).

## 1. Proyecto y design system

- Proyecto existente `projects/14200813501064679723` (el de C-11, C-49, C-09, C-12, C-13, C-10 y C-50).
- Design system «Clinical Ops», `assets/b683d44391ab410db2dd48aa71ed0b47` (confirmado con `list_design_systems` antes de generar).

## 2. Pantallas pedidas

`generate_screen_from_text`, modelo `GEMINI_3_8_FLASH`, con el design system de arriba. Como mucho **dos intentos** por pantalla. Solo textos de los specs `consulta-de-turnos` y `pantalla-de-agenda`, los pacientes ficticios del seed («Ana Ejemplo», «Bruno Ficticio», «Carla Inventada»), las prestaciones y colores del seed y los emails ficticios de la demo (`.test`); sin pacientes reales, sin teléfonos, sin contraseñas, sin secretos.

### 2.1 Agenda, escritorio (`DESKTOP`)

> Pantalla de escritorio en español (Argentina): «Agenda del día» del panel de un consultorio odontológico chico. Herramienta administrativa sobria, coherente con las pantallas «Prestaciones», «Usuarios», «Horario», «Bloqueos» y «Mi contraseña» de este proyecto (misma barra superior horizontal, marca y estilo «Clinical Ops»; sin barra lateral). Sin imágenes decorativas, sin fotos, sin textos de marketing.
>
> - Barra superior: marca con ícono simple de diente y «Turnos Odontológicos AR»; pastillas «Agenda» (activa, fondo celeste suave, con ícono de calendario), «Prestaciones», «Usuarios», «Horario», «Bloqueos» y «Mi contraseña»; a la derecha, el usuario de la sesión «odontologa@consultorio-demo.test» con «Odontólogo · Dueño» debajo en gris chico, una línea vertical fina y el botón con borde «Cerrar sesión».
> - Encabezado: título «Agenda del día», subtítulo «Horas del consultorio (America/Argentina/Buenos_Aires).» A la derecha, botón primario «Nuevo turno» con ícono de más.
> - Barra de fecha: botón con borde de flecha «Día anterior», un campo de fecha «02/11/2026» con el texto «lunes 2 de noviembre de 2026» al lado, botón con borde de flecha «Día siguiente» y un botón con borde «Hoy».
> - Tarjeta con una tabla densa ordenada por hora, columnas HORA, PACIENTE, PRESTACIÓN, ESTADO. Cada fila tiene a la izquierda una franja vertical fina del color de la prestación y en la columna PRESTACIÓN un punto de ese color antes del nombre. Filas (datos ficticios):
>   - «09:00 – 09:30» · «Ana Ejemplo» · punto azul #1E88E5 «Consulta / control» · chip «Reservado» (celeste)
>   - «10:00 – 10:45» · «Bruno Ficticio» · punto verde #43A047 «Limpieza» · chip «Reservado» (celeste)
>   - «11:00 – 12:00» · «Carla Inventada» · punto naranja #FB8C00 «Obturación» · chip «Confirmado» (verde)
>   - «15:30 – 16:15» · «Ana Ejemplo» · punto rojo #E53935 «Extracción» · chip «Cancelado por el paciente» (rojo suave, texto tachado no)
> - Pie de la tarjeta: «4 turnos».
> - Al costado o debajo, un estado vacío de referencia en gris: «No hay turnos para este día.»
>
> Estilo: Inter, primario #0284C7, texto #0F172A, texto secundario #64748B, bordes #E2E8F0, fondo #F8FAFC, radio 4 px en botones, 8 px en tarjetas, filas de 40 px, sin sombras fuertes, números tabulares en la columna HORA.

### 2.2 «Nuevo turno» con error, escritorio (`DESKTOP`)

> Pantalla de escritorio en español (Argentina): la misma «Agenda del día» del panel de un consultorio odontológico chico, ahora con el panel lateral «Nuevo turno» abierto a la derecha mostrando un error. Estilo «Clinical Ops», sobrio, coherente con las pantallas «Prestaciones» y «Bloqueos» de este proyecto (misma barra superior horizontal; sin barra lateral de navegación). Sin imágenes decorativas, sin fotos, sin textos de marketing.
>
> - Barra superior: marca con ícono de diente y «Turnos Odontológicos AR»; pastillas «Agenda» (activa), «Prestaciones», «Usuarios», «Horario», «Bloqueos» y «Mi contraseña»; a la derecha «recepcion@consultorio-demo.test» con «Recepcionista» debajo en gris chico, línea vertical fina y botón con borde «Cerrar sesión».
> - A la izquierda, atenuada detrás del panel: título «Agenda del día», barra de fecha «02/11/2026 · lunes 2 de noviembre de 2026» y la tabla con columnas HORA, PACIENTE, PRESTACIÓN, ESTADO: «10:00 – 10:30» «Ana Ejemplo» punto azul «Consulta / control» chip «Reservado»; «11:00 – 12:00» «Carla Inventada» punto naranja «Obturación» chip «Reservado».
> - Panel lateral derecho (unos 420 px, borde izquierdo, título «Nuevo turno» y botón «Cerrar» con ícono X):
>   - Campo numérico «N.º de paciente» con el valor «2» y ayuda gris «El número de ficha del paciente.»
>   - Selector «Prestación» con «Consulta / control · 30 min» seleccionada y un punto azul #1E88E5.
>   - Campo de fecha y hora «Inicio» con «02/11/2026 10:00» (24 h) y ayuda gris «Hora del consultorio. Termina a las 10:30.»
>   - Un aviso de error rojo (#DC2626 sobre #FEF2F2, con ícono de alerta) arriba de los botones: título «El horario está ocupado», texto «El profesional y el sillón ya tienen un turno activo en ese horario.» y debajo dos chips de código monoespaciados «RN-AG-05» y «RN-AG-08».
>   - Debajo, un segundo ejemplo de error en el mismo estilo (estado alternativo): «Hay datos que no existen o no están activos: paciente 99 (inexistente).» con el chip «RN-GL-04».
>   - Pie del panel: botón primario «Crear turno» y botón con borde «Cancelar».
>
> Estilo: Inter, primario #0284C7, texto #0F172A, secundario #64748B, bordes #E2E8F0, fondo #F8FAFC, radio 4 px en campos y botones, 8 px en tarjetas, sin sombras fuertes salvo la del panel lateral.

### 2.3 Agenda, angosta (pedida como `MOBILE`)

> Pantalla angosta (celular, unos 390 px de ancho) en español (Argentina): «Agenda del día» del panel de un consultorio odontológico chico. Estilo «Clinical Ops», sobrio, sin imágenes, sin fotos, sin barra lateral ni barra inferior de navegación nueva, sin desplazamiento horizontal de la página.
>
> - Barra superior en varias filas: fila 1, marca con ícono de diente y «Turnos Odontológicos AR»; fila 2, pastillas «Agenda» (activa, fondo celeste suave), «Prestaciones», «Usuarios», «Horario», «Bloqueos» y «Mi contraseña», que pasan a la línea siguiente si no entran; fila 3, a la izquierda «recepcion@consultorio-demo.test» (cortado con puntos suspensivos si no entra) con «Recepcionista» debajo en gris chico y a la derecha el botón con borde «Cerrar sesión».
> - Título «Agenda del día», subtítulo «Horas del consultorio (America/Argentina/Buenos_Aires).» y botón primario de ancho completo «Nuevo turno».
> - Barra de fecha compacta: botón de flecha izquierda, «lun 02/11/2026» en el centro, botón de flecha derecha y botón con borde «Hoy».
> - La lista de turnos en tarjetas apiladas (una por turno), cada una con una franja vertical a la izquierda del color de la prestación: arriba la hora «09:00 – 09:30» en números tabulares y a la derecha el chip de estado; debajo el paciente en seminegrita y la prestación con un punto de color. Datos ficticios: «09:00 – 09:30» «Ana Ejemplo» «Consulta / control» «Reservado»; «10:00 – 10:45» «Bruno Ficticio» «Limpieza» «Reservado»; «11:00 – 12:00» «Carla Inventada» «Obturación» «Confirmado».
> - Pie: «3 turnos».
>
> Estilo: Inter, primario #0284C7, texto #0F172A, secundario #64748B, bordes #E2E8F0, fondo #F8FAFC, radio 4 px en botones, 8 px en tarjetas.

(Pedido 2.3 resumido acá en la lista de turnos; los textos entre comillas son los enviados.)

## 3. Resultado de la generación

| Pantalla | Intento | Modelo | Resultado |
|---|---|---|---|
| Agenda, escritorio | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `3453493581658038854`); `status` `COMPLETE`. No hizo falta el segundo intento |
| «Nuevo turno» con error | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `10512776049193643696`); `status` `COMPLETE` |
| Agenda, angosta | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `3311310672459611287`); `status` `COMPLETE`. Aunque se pidió `MOBILE`, la metadata dice `deviceType` `DESKTOP` y 2560 × 2048: la captura muestra la columna angosta (unos 390 px) centrada sobre el lienzo de escritorio, como en C-50. Sirve como referencia del acomodo |

## 3b. Pantallas obtenidas (2026-10-28)

| Pantalla | Id | Título en Stitch | Captura (archivo de Stitch) | HTML (archivo de Stitch) |
|---|---|---|---|---|
| Agenda, escritorio | `projects/14200813501064679723/screens/cd19642b8b1b4bcda5162e35d6291e10` | «Agenda del día - Turnos Odontológicos AR» | `projects/14200813501064679723/files/3f69a5a08c0b49bcb73b7c3d5d52cd9a` | `projects/14200813501064679723/files/86f23db4ebad4082b323b6af7870944c` |
| «Nuevo turno» con error | `projects/14200813501064679723/screens/5371dfaf7cc441c08af62712e311c326` | «Agenda del día - Nuevo turno con error - Turnos Odontológicos AR» | `projects/14200813501064679723/files/bc8f0313a81d4f00aa3c1447cc5d481e` | `projects/14200813501064679723/files/161328d214d84939bdcee426d0f83066` |
| Agenda, angosta | `projects/14200813501064679723/screens/20bcd71b007a43f7874a05ae70a45753` | «Agenda del día - Móvil (Turnos Odontológicos AR)» | `projects/14200813501064679723/files/d98d09bc32a24ebba5764326556fd0d7` | `projects/14200813501064679723/files/626c8d19b3da4a30a45bb581acc332ac` |

- **Cómo se descargaron**: con el `downloadUrl` de cada archivo y la cabecera `X-Goog-Api-Key` (la clave sale de `STITCH_API_KEY` en el entorno, nunca escrita en el repo); la respuesta es un JSON con `dataString` (el HTML como texto; la imagen en base64), que se decodificó sin cambios. Las capturas se reducen de 2560 × 2048 a 1280 × 1024, como las anteriores.
- **Archivos guardados** en [stitch-agenda-pantalla/](stitch-agenda-pantalla/):
  - `agenda-escritorio.png` y `agenda-escritorio.html`;
  - `nuevo-turno-con-error.png` y `nuevo-turno-con-error.html`;
  - `agenda-angosta.png` y `agenda-angosta.html`.
  - Los tres HTML usan Tailwind (`cdn.tailwindcss.com`) y Google Fonts por CDN (Inter y, en el panel, JetBrains Mono para los códigos): **no se copian**; la implementación los traduce a los tokens CSS del proyecto, sin dependencias nuevas (CSP `default-src 'self'`).
- **Revisión del HTML** (datos y secretos): solo los emails ficticios de la demo (`odontologa@consultorio-demo.test` y `recepcion@consultorio-demo.test`), los tres pacientes ficticios del seed y las prestaciones y colores del seed. Sin teléfonos, documentos, contraseñas, claves de API ni tokens; Stitch no inventó pacientes ni profesionales.

### Qué muestra la agenda de escritorio

La barra del panel con «Agenda» activa primero (con ícono de calendario), las otras cinco pastillas, el usuario de la sesión y «Cerrar sesión» (la marca y «Mi contraseña» partidos en dos líneas). Debajo, «Agenda del día» con la zona y «Nuevo turno» primario; una tarjeta con «Día anterior», el campo «02/11/2026», «lunes 2 de noviembre de 2026», «Día siguiente» y «Hoy» a la derecha; la tabla con HORA, PACIENTE (seminegrita), PRESTACIÓN (punto de color), ESTADO (chips celeste, verde y rojo suave) y una columna ACCIONES con «Ver ficha», la franja de color a la izquierda de cada fila, y el pie «4 turnos» con «Agenda sincronizada en tiempo real»; una tarjeta aparte punteada «Referencia de estado» con «No hay turnos para este día.» y una sugerencia de ir a Bloqueos; y un pie de página institucional («Módulo de Agenda y Turnos del Día · Sede Central»).

### Qué muestra «Nuevo turno» con error

La agenda atenuada a la izquierda (dos turnos, «2 turnos agendados») y, a la derecha, el panel «Nuevo turno» con un ícono de más, «Cerrar» (X), «N.º de paciente» con «2» y su ayuda, «Prestación» con el punto azul y «Consulta / control · 30 min» y la ayuda «Duración calculada automáticamente según la práctica.», «Inicio» con «02/11/2026 10:00» con borde rojo y la ayuda «Hora del consultorio. Termina a las 10:30.», el aviso rojo «El horario está ocupado» con su texto y los chips «RN-AG-05» y «RN-AG-08», un separador «Estado alternativo de validación · Referencia clínica» con el aviso de `RN-GL-04`, y el pie con «Cancelar» y «Crear turno».

### Qué muestra la angosta

Una columna de unos 390 px con la barra en tres filas (marca; pastillas en dos líneas; usuario y «Cerrar sesión»), «Agenda del día» con la zona, «Nuevo turno» a ancho completo, la barra de fecha compacta (flechas, «lun 02/11/2026», «Hoy»), tres tarjetas de turno con la franja de color, la hora y el chip arriba y el paciente y la prestación debajo, y el pie «3 turnos» con «Sede Central».

### Sugerencias de Stitch no aceptadas

- Agenda de escritorio: «Agregar modal emergente para "Nuevo turno"» (ya se pidió como panel lateral en 2.2), «Ver versión para dispositivos móviles de la agenda» (es 2.3) e «Incorporar filtros por profesional u odontólogo» (Fase 2, fuera de C-14).
- «Nuevo turno» con error: «Ver el estado de éxito al crear el turno sin conflictos» (el spec lo define: «Turno creado.» y el panel se cierra), «Diseñar la versión modal centrada en lugar de panel lateral drawer» (se sigue el panel lateral de C-11) y «Simular la vista con el paciente seleccionado y su historial previo» (historial de C-15, pacientes de C-20).
- Angosta: «Diseñar el modal o drawer móvil para "Nuevo turno"» (el panel ocupa el ancho en angosto, design A14), «Ver el estado vacío cuando no hay turnos agendados en el día» (texto fijado en el spec) y «Diseñar el detalle al tocar un turno específico» (acciones de C-15 a C-19).

**Qué se toma y qué se rechaza**: en el `design.md` de `agenda-del-dia`, sección «Referencia visual (Stitch)».

## 4. Comparación con la implementación

Pendiente: se completa en el Apply, tarea 11.1 (prueba en el navegador a 1280 y 390 px contra las tres capturas).
