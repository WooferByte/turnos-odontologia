# Evidencia: cancelar un turno con Stitch (C-17, `cancelar-turno`)

Fecha: 2026-10-29. Regla que lo pide: D234 (toda pantalla del frontend parte de una pantalla generada en Stitch). Cuándo: en el propose, antes de aprobar el plan (como D301 de C-10, C-50, C-14, C-15 y C-16). Procedimiento: el de [stitch-agenda.md](stitch-agenda.md) y [stitch-reprogramar.md](stitch-reprogramar.md).

**Estado: hechas (2026-10-29, en el `/opsx:propose` del change).** Las dos pantallas se generaron con el MCP `stitch` al primer intento cada una, y el MCP devolvió sus ids directamente (sección 3b).

## 1. Proyecto y design system

- Proyecto existente `projects/14200813501064679723` (el de C-11, C-49, C-09, C-12, C-13, C-10, C-50, C-14, C-15 y C-16).
- Design system «Clinical Ops», `assets/b683d44391ab410db2dd48aa71ed0b47` (confirmado con `list_design_systems` antes de generar).

## 2. Pantallas pedidas

`generate_screen_from_text`, modelo `GEMINI_3_8_FLASH`, con el design system de arriba. Como mucho **dos intentos** por pantalla. Solo textos propuestos en el design de `cancelar-turno` (Q7 a Q9, así que pueden cambiar si el autor responde otra cosa), los pacientes ficticios del seed («Ana Ejemplo», «Bruno Ficticio», «Carla Inventada»), las prestaciones y colores del seed y los emails ficticios de la demo (`.test`); sin pacientes reales, sin teléfonos, sin contraseñas, sin secretos.

### 2.1 Cancelar turno con error, escritorio (`DESKTOP`)

> Pantalla de escritorio en español (Argentina): la «Agenda del día» del panel de un consultorio odontológico chico con el panel lateral «Cancelar turno» abierto a la derecha, mostrando un error. […] coherente con las pantallas «Agenda», «Historial del turno» y «Reprogramar turno» de este proyecto […]
>
> - Barra superior: […] «recepcion@consultorio-demo.test» con «Recepcionista» […] y el botón con borde «Cerrar sesión».
> - A la izquierda: título «Agenda del día», […] botón primario «Nuevo turno»; barra de fecha […].
> - Tabla densa con columnas HORA, PACIENTE, PRESTACIÓN, ESTADO y ACCIONES. En ACCIONES, botones chicos con borde por fila: «Reprogramar» (ícono de calendario), «Cancelar» (ícono de círculo con X, texto rojo, estilo destructivo fantasma) e «Historial» (ícono de reloj). Filas (datos ficticios): «09:00 – 09:30» «Ana Ejemplo» […] chip «Reservado» — esta fila está seleccionada […]; «10:00 – 10:45» «Bruno Ficticio» […] «Reservado»; «11:00 – 12:00» «Carla Inventada» […] «Confirmado»; «12:00 – 12:30» «Bruno Ficticio» […] chip rojo suave «Cancelado por el consultorio» y en ACCIONES solo «Historial» (sin «Reprogramar» ni «Cancelar»).
> - Panel lateral derecho (unos 420 px, […] sin oscurecer la agenda): título «Cancelar turno» con ícono de círculo con X y botón «Cerrar» con ícono X. Debajo, el resumen en gris: «Ana Ejemplo · Consulta / control» y «lunes 2 de noviembre de 2026, 09:00 – 09:30 · Reservado».
> - Arriba del formulario, un aviso de error rojo suave con ícono: «Este turno ya no se puede cancelar por su estado (RN-AG-12).» y debajo, en la misma caja, «El turno no cambió.»
> - Un grupo de opciones (radios) con el rótulo «¿Quién pidió la cancelación?»: «El paciente» (marcado) y «El consultorio». Debajo, ayuda gris: «El horario queda libre para otro turno.»
> - Pie del panel: botón con borde «Volver» y botón destructivo rojo «Cancelar turno».
>
> Estilo: Inter, primario #0284C7, destructivo #DC2626, texto #0F172A, […] números tabulares en horas y fechas.

(Pedido resumido acá con «[…]»; los textos entre comillas son los enviados.)

### 2.2 Cancelar turno, angosta (pedida como `MOBILE`)

> Pantalla angosta (celular, unos 390 px de ancho) en español (Argentina): el panel «Cancelar turno» de la agenda […], abierto a todo el ancho debajo de la barra. […] sin desplazamiento horizontal de la página.
>
> - Barra superior en varias filas: […] «odontologa@consultorio-demo.test» con «Odontólogo · Dueño» […] y el botón con borde «Cerrar sesión».
> - Panel a todo el ancho […]: título «Cancelar turno» con ícono de círculo con X y botón «Cerrar» […]. Resumen en gris: «Bruno Ficticio · Limpieza» y «lunes 2 de noviembre de 2026, 10:00 – 10:45 · Reservado».
> - Un aviso ámbar suave con ícono: «Elegí quién pidió la cancelación.»
> - Un grupo de opciones (radios, ninguna marcada) con el rótulo «¿Quién pidió la cancelación?»: «El paciente» y «El consultorio» […]. Debajo, ayuda gris: «El horario queda libre para otro turno.»
> - Pie: botón destructivo rojo de ancho completo «Cancelar turno» y debajo botón con borde de ancho completo «Volver».
> - Debajo del panel, […] con el rótulo gris «Después de cancelar», un ejemplo chico: aviso verde suave «Turno cancelado.» sobre una tarjeta de turno «10:00 – 10:45 · Bruno Ficticio · Limpieza» con chip rojo suave «Cancelado por el paciente» y solo el botón con borde «Historial».
>
> Estilo: el mismo de 2.1.

## 3. Resultado de la generación

| Pantalla | Intento | Modelo | Resultado |
|---|---|---|---|
| Cancelar con error, escritorio | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `12920991655664972717`); `status` `COMPLETE`. No hizo falta el segundo intento |
| Cancelar, angosta | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `2415624735876371518`); `status` `COMPLETE`. Aunque se pidió `MOBILE`, la metadata dice `deviceType` `DESKTOP` y 2560 × 2048: la captura muestra la columna angosta (unos 390 px) centrada sobre el lienzo de escritorio, como en C-50, C-14, C-15 y C-16. Sirve como referencia del acomodo |

## 3b. Pantallas obtenidas (2026-10-29)

| Pantalla | Id | Título en Stitch | Captura (archivo de Stitch) | HTML (archivo de Stitch) |
|---|---|---|---|---|
| Cancelar con error, escritorio | `projects/14200813501064679723/screens/e382a7e3a92f4cb18df0f6e7e9d677ca` | «Agenda del día - Cancelar turno con error - Turnos Odontológicos AR» | `projects/14200813501064679723/files/3fb4938f6fff4b7191844a6627a3abf8` | `projects/14200813501064679723/files/d0cecc46a7bd4f93aa08441bc4bcc2c9` |
| Cancelar, angosta | `projects/14200813501064679723/screens/fcd2a428cdc44c5689b398cc8bf1936f` | «Agenda del día - Cancelar turno móvil - Turnos Odontológicos AR» | `projects/14200813501064679723/files/28c4071b269c44cd9effc89b8487504a` | `projects/14200813501064679723/files/82a9e03d19084b15b5185fed07675031` |

- **Cómo se descargaron**: con el `downloadUrl` de cada archivo y la cabecera `X-Goog-Api-Key` (la clave sale de `STITCH_API_KEY` en el entorno, nunca escrita en el repo); la respuesta es un JSON con `dataString` (el HTML como texto; la imagen en base64), que se decodificó sin cambios. Las capturas se reducen de 2560 de ancho a 1280, como las anteriores.
- **Archivos guardados** en [stitch-cancelar-pantalla/](stitch-cancelar-pantalla/): `cancelar-escritorio.png` y `cancelar-escritorio.html`; `cancelar-angosta.png` y `cancelar-angosta.html`.
- Los dos HTML usan Tailwind y Google Fonts por CDN: **no se copian**; la implementación los traduce a los tokens CSS del proyecto, sin dependencias nuevas (CSP `default-src 'self'`).
- **Revisión del HTML** (datos y secretos): solo los emails ficticios de la demo (`recepcion@consultorio-demo.test` en la de escritorio y `odontologa@consultorio-demo.test` en la angosta), los tres pacientes ficticios del seed y las prestaciones y colores del seed. Sin teléfonos, documentos, contraseñas, claves de API ni tokens; Stitch no inventó pacientes ni profesionales.

### Qué muestra la de escritorio

La barra del panel con «Agenda» activa; la agenda a la izquierda (sin atenuar) con la columna «ACCIONES» y, en cada fila activa, los botones con borde «Reprogramar» (calendario), «Cancelar» (texto e ícono rojos, círculo con X) e «Historial» (reloj); la fila «Cancelado por el consultorio» solo con «Historial»; la fila de Ana Ejemplo resaltada (fondo celeste y franja izquierda) con su «Cancelar» con borde rojo; el pie «4 turnos agendados» con «Agenda sincronizada en tiempo real». A la derecha, el panel «Cancelar turno» con ícono rojo y X; el resumen «Ana Ejemplo · Consulta / control» y «lunes 2 de noviembre de 2026, 09:00 – 09:30» con el chip «Reservado»; el aviso rojo suave con el texto de `RN-AG-12` y «El turno no cambió.»; el rótulo en mayúsculas «¿QUIÉN PIDIÓ LA CANCELACIÓN?» y dos opciones en tarjetas con radio, «El paciente» (marcada, con borde azul) y «El consultorio», **cada una con una línea de descripción que Stitch agregó por su cuenta** («Cancelación solicitada por el usuario o vía recepción», «Por fuerza mayor clínica o indisponibilidad del odontólogo»); la ayuda «El horario queda libre para otro turno.» con ícono de información; el pie fijo con «Volver» y «Cancelar turno» rojo con X. Un pie de página institucional.

### Qué muestra la angosta

Una columna de unos 390 px con la barra en tres filas y debajo el panel a todo el ancho (la agenda no se ve): «Cancelar turno» con la X, el resumen de Bruno Ficticio en una caja gris con el chip «Reservado», el aviso ámbar «Elegí quién pidió la cancelación.», las dos opciones sin marcar en filas altas, la ayuda, «Cancelar turno» rojo a todo el ancho y «Volver» debajo; después el separador «DESPUÉS DE CANCELAR» con el aviso verde «Turno cancelado.» y la tarjeta del turno con franja roja, chip «Cancelado por el paciente» y solo «Historial»; y un pie «Módulo de Agenda Móvil».

### Sugerencias de Stitch no aceptadas

- Escritorio: «Diseñar la versión móvil de Cancelar turno con error» (es 2.2), «Ver el modal o estado exitoso de cancelación de turno» (la angosta ya lo muestra) y «Añadir confirmación previa con advertencia de tiempo límite» (el panel ya es la confirmación; el plazo de RN-TD-03 es del paciente por el link, C-29, y el panel cancela en cualquier momento, D65).
- Angosta: «Ver el estado cuando se selecciona “El paciente” con el botón activo» (lo muestra la de escritorio), «Mostrar estado de error cuando el turno ya fue cancelado por otra sesión» (lo muestra la de escritorio) y «Adaptar este mismo panel a la vista de escritorio» (es 2.1).

**Qué se toma y qué se rechaza**: en el `design.md` de `cancelar-turno`, sección «Referencia visual (Stitch)».

## 4. Comparación con la implementación

Hecha el 2026-10-29 en la tarea 12.1 con la demo (`crear_app_demo` y `npm run dev`, con la recepcionista y una usuaria solo `dueno` creada para la prueba) y después con Compose, en el navegador integrado de la app. Capturas en `stitch-cancelar-pantalla/`: `implementacion-cancelar-escritorio.jpg` (1280 px, el panel con el error «Elegí quién pidió la cancelación.») e `implementacion-cancelar-angosta.jpg` (390 px, el panel debajo de la agenda). Para que el panel entrara completo a 390 px, la captura se tomó con la ventana emulada de ese ancho y la página desplazada hasta el panel.

### Recorrido y resultado (fecha 02/11/2026)

| Paso | Resultado |
|---|---|
| V4: turno de Ana (09:00) cancelado por la recepcionista, historial | «Turno creado» y «Turno cancelado», los dos con «Por: Usuario n.º 2»; el segundo con «Estado: Reservado → Cancelado por el paciente»; por la API, `actor_id` `"2"` en `creado` y en `cancelado` |
| Dos turnos (Ana 09:00, Bruno 10:00); «Cancelar» de Ana | Panel «Cancelar turno» con «Ana Ejemplo · Consulta / control», «lunes 2 de noviembre de 2026, 09:00 – 09:30 · Reservado», el foco en el primer radio, la fila resaltada y los tres botones por fila |
| CAN-5b: «Cancelar turno» sin elegir | «Elegí quién pidió la cancelación.»; ningún pedido; el aviso desaparece al elegir una opción |
| CAN-4a: «El paciente» y «Cancelar turno» | «Turno cancelado.», panel cerrado, fila «Cancelado por el paciente» solo con «Historial» |
| Otro turno en el mismo hueco (Carla, 09:00) | `201`: el hueco quedó libre |
| CAN-4b: Carla, «El consultorio» | Fila «Cancelado por el consultorio» (la API recibe `cancelado_profesional`) |
| CAN-5a: Bruno con el panel abierto y «El paciente» marcado; el turno se cancela por la API desde otra sesión; «Cancelar turno» | «Este turno ya no se puede cancelar por su estado (RN-AG-12).» y «El turno no cambió.»; el panel sigue abierto con la opción marcada; no se ve «Turno cancelado.» |
| Un solo panel a la vez | Con el panel de Bruno abierto, «Historial» de Ana lo cierra y abre el historial |
| Usuaria solo `dueno` (D312) | Ve «Cancelar» en las filas activas y recibe «Tu usuario no tiene permiso para cancelar turnos (RN-AU-05).» con «El turno no cambió.» |
| API (`fetch` con los tokens de la demo; el mismo recorrido que en `/docs`) | dueña: `403` `["RN-AU-05"]`; `{"estado": "confirmado"}`: `422` sin códigos; turno 999: `404` `["RN-GL-04"]`; recepcionista: `200` con `cancelado_profesional`; repetido: `409` `["RN-AG-12"]`; `/openapi.json` tiene `/turnos/{turno_id}/cancelar` |
| 390 px (demo) | Sin desplazamiento horizontal (`scrollWidth` 390) con tres botones en la tarjeta («Reprogramar» y «Cancelar» en una fila, «Historial» debajo); radios de 44 px de alto |
| Compose (`http://127.0.0.1:5173`), turno del 07/12/2026 | Cancelado como del paciente con un solo `POST`; consola sin mensajes (ninguna violación de la CSP); a 390 px sin desplazamiento horizontal; ningún token, contraseña ni dato de paciente en la URL |

### Diferencias con Stitch y su motivo

- **Sin chip de estado en el resumen del panel**: el resumen es texto plano («… 09:00 – 09:30 · Reservado»), como pide la spec (CAN-4 y X10); Stitch dibuja un chip «Reservado».
- **Las opciones no llevan línea de descripción**: Stitch agregó por su cuenta «Cancelación solicitada por el usuario…» y «Por fuerza mayor clínica…»; no están en las recomendaciones aceptadas (D350) y se descartaron en el design.
- **El panel va dentro de la página, al costado de la agenda** (con el pie dentro de la tarjeta), como «Nuevo turno», «Historial» y «Reprogramar», y no como columna de alto completo; a 390 px va **debajo** de la agenda y no la reemplaza, como los otros tres paneles.
- Sin los pies «Agenda sincronizada en tiempo real», «4 turnos agendados» ni el pie institucional; el total va en el chip del título, como en C-14.
- **El aviso va con el código entre paréntesis** y sin chip ni borde en los campos, como en C-16.
- A 1280 px, con un panel abierto, la tabla se angosta y en las filas activas «Historial» pasa a una segunda línea bajo «Reprogramar» y «Cancelar» (con el panel cerrado entran los tres en una línea). Se acepta: no hay desbordamiento y los tres botones se ven.

### Hallazgos fuera del alcance de C-17

- Un mensaje de éxito anterior («Turno creado.», «Turno reprogramado.») puede quedar visible junto a un rechazo posterior de «Cancelar», de «Reprogramar» o de «Nuevo turno» (por ejemplo, «Turno creado.» encima del panel con «Elegí quién pidió la cancelación.»). Lo introdujo C-14; queda para un change posterior.
- Tras el rechazo `RN-AG-12` de `CAN-5a` la fila sigue mostrando «Reservado» hasta recargar el día: es lo que dice la spec (el turno no cambió para esta sesión); «Día anterior» y «Día siguiente» recargan.
