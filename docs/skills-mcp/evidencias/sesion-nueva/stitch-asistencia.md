# Evidencia: registrar la asistencia de un turno con Stitch (C-18, `marcar-atendido-o-ausente`)

Fecha: 2026-10-30. Regla que lo pide: D234 (toda pantalla del frontend parte de una pantalla generada en Stitch). Cuándo: en el propose, antes de aprobar el plan (como D301 de C-10, C-50 y C-14 a C-17). Procedimiento: el de [stitch-agenda.md](stitch-agenda.md) y [stitch-cancelar.md](stitch-cancelar.md).

**Estado: hechas (2026-10-30, en el `/opsx:propose` del change).** Las dos pantallas se generaron con el MCP `stitch` al primer intento cada una, y el MCP devolvió sus ids directamente (sección 3b).

## 1. Proyecto y design system

- Proyecto existente `projects/14200813501064679723` (el de C-11, C-49, C-09, C-12, C-13, C-10, C-50 y C-14 a C-17).
- Design system «Clinical Ops», `assets/b683d44391ab410db2dd48aa71ed0b47` (confirmado con `list_design_systems` antes de generar).

## 2. Pantallas pedidas

`generate_screen_from_text`, modelo `GEMINI_3_8_FLASH`, con el design system de arriba. Como mucho **dos intentos** por pantalla. Solo los textos **propuestos** en el design de `marcar-atendido-o-ausente` (preguntas Q8 a Q10, así que pueden cambiar si el autor responde otra cosa), los pacientes ficticios del seed («Ana Ejemplo», «Bruno Ficticio», «Carla Inventada»), las prestaciones del seed y los emails ficticios de la demo (`.test`); sin pacientes reales, sin teléfonos, sin contraseñas, sin secretos.

### 2.1 Registrar asistencia con error, escritorio (`DESKTOP`)

> Pantalla de escritorio en español (Argentina): la «Agenda del día» del panel de un consultorio odontológico chico con el panel lateral «Registrar asistencia» abierto a la derecha, mostrando un error. Coherente con las pantallas «Agenda», «Historial del turno», «Reprogramar turno» y «Cancelar turno» de este proyecto. […]
>
> - Barra superior: […] «recepcion@consultorio-demo.test» con «Recepcionista» y el botón con borde «Cerrar sesión».
> - A la izquierda: título «Agenda del día», botón primario «Nuevo turno»; barra de fecha con […] «viernes 30 de octubre de 2026» […].
> - Tabla densa con columnas HORA, PACIENTE, PRESTACIÓN, ESTADO y ACCIONES. En ACCIONES, botones chicos con borde por fila, en este orden: «Asistencia» (ícono de tilde en un círculo), «Reprogramar» (ícono de calendario), «Cancelar» (ícono de círculo con X, texto rojo, estilo destructivo fantasma) e «Historial» (ícono de reloj). Filas (datos ficticios): «09:00 – 09:30» «Ana Ejemplo» «Consulta / control» chip verde suave «Atendido» y en ACCIONES solo «Historial»; «10:00 – 10:45» «Bruno Ficticio» «Limpieza» chip verde «Confirmado» con los cuatro botones; «16:00 – 17:00» «Carla Inventada» «Obturación» chip celeste «Reservado» con los cuatro botones — esta fila está seleccionada […]; «17:30 – 18:00» «Bruno Ficticio» «Consulta / control» chip rojo suave «Ausente» y solo «Historial».
> - Panel lateral derecho (unos 420 px, borde fino, sin oscurecer la agenda): título «Registrar asistencia» con ícono de tilde en círculo y botón «Cerrar» con ícono X. Debajo, el resumen en gris: «Carla Inventada · Obturación» y «viernes 30 de octubre de 2026, 16:00 – 17:00» con el chip «Reservado».
> - Arriba del formulario, un aviso de error rojo suave con ícono: «El turno todavía no empezó: la asistencia se registra desde su hora de inicio (RN-AG-13).» y debajo, en la misma caja, «El turno no cambió.»
> - Un grupo de opciones (radios en filas con borde) con el rótulo en tipografía normal «¿Cómo terminó el turno?»: «Atendido» (marcado, borde azul) y «Ausente». Sin descripciones debajo de las opciones. Debajo, ayuda gris con ícono de información: «El horario queda libre para otro turno.»
> - Pie del panel: botón con borde «Volver» y botón primario azul «Registrar asistencia».
>
> Estilo: Inter, primario #0284C7, destructivo #DC2626, éxito #16A34A, texto #0F172A, bordes #CBD5E1, fondo #F8FAFC, radios de 4 px, números tabulares en horas y fechas. Sin pie de página institucional, sin textos de «tiempo real».

(Pedido resumido acá con «[…]»; los textos entre comillas son los enviados.)

### 2.2 Registrar asistencia, angosta (pedida como `MOBILE`)

> Pantalla angosta (celular, unos 390 px de ancho) en español (Argentina): el panel «Registrar asistencia» de la agenda del día […], abierto a todo el ancho debajo de la barra. […] Sin desplazamiento horizontal de la página.
>
> - Barra superior en varias filas: […] «odontologa@consultorio-demo.test» con «Odontólogo · Dueño» y el botón con borde «Cerrar sesión».
> - Panel a todo el ancho […]: título «Registrar asistencia» con ícono de tilde en círculo y botón «Cerrar» […]. Resumen en una caja gris: «Bruno Ficticio · Limpieza» y «viernes 30 de octubre de 2026, 10:00 – 10:45» con el chip verde «Confirmado».
> - Un aviso ámbar suave con ícono: «Elegí si el paciente fue atendido o estuvo ausente.»
> - Un grupo de opciones (radios en filas altas con borde, ninguna marcada, sin descripciones) con el rótulo en tipografía normal «¿Cómo terminó el turno?»: «Atendido» y «Ausente». Debajo, ayuda gris con ícono de información: «El horario queda libre para otro turno.»
> - Pie: botón primario azul de ancho completo «Registrar asistencia» y debajo botón con borde de ancho completo «Volver».
> - Debajo del panel, […] con el rótulo gris «Después de registrar», un ejemplo chico: aviso verde suave «Asistencia registrada.» sobre una tarjeta de turno «10:00 – 10:45 · Bruno Ficticio · Limpieza» con chip verde suave «Atendido» y solo el botón con borde «Historial» (ícono de reloj).
>
> Estilo: Inter, primario #0284C7, éxito #16A34A, advertencia #D97706, […] Sin barra inferior de navegación, sin pie institucional.

## 3. Resultado de la generación

| Pantalla | Intento | Modelo | Resultado |
|---|---|---|---|
| Registrar asistencia con error, escritorio | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `4193719274151042902`); `status` `COMPLETE`. No hizo falta el segundo intento |
| Registrar asistencia, angosta | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `7445720737976637050`); `status` `COMPLETE`. Aunque se pidió `MOBILE`, la metadata dice `deviceType` `DESKTOP` y 2560 × 2048: la captura muestra la columna angosta (unos 390 px) centrada sobre el lienzo de escritorio, como en C-50 y C-14 a C-17. Sirve como referencia del acomodo |

## 3b. Pantallas obtenidas (2026-10-30)

| Pantalla | Id | Título en Stitch | Captura (archivo de Stitch) | HTML (archivo de Stitch) |
|---|---|---|---|---|
| Registrar asistencia con error, escritorio | `projects/14200813501064679723/screens/b64bb7234a344397b127fc921f0fc733` | «Agenda del día - Registrar asistencia con error - Turnos Odontológicos AR» | `projects/14200813501064679723/files/d391e4288c3f428aabe2dc7182ae8bd0` | `projects/14200813501064679723/files/88d842668d6e466d8bf1a1c33504390b` |
| Registrar asistencia, angosta | `projects/14200813501064679723/screens/7c88173529aa4877952728a3abe6c05c` | «Agenda del día - Registrar asistencia móvil - Turnos Odontológicos AR» | `projects/14200813501064679723/files/79d3ca47d39a41eab12e2a61d1b3089b` | `projects/14200813501064679723/files/15016b3af2f64a8ca563a8a3b06a20c1` |

- **Cómo se descargaron**: con el `downloadUrl` de cada archivo y la cabecera `X-Goog-Api-Key` (la clave sale de `STITCH_API_KEY` en el entorno, nunca escrita en el repo); la respuesta es un JSON con `dataString` (el HTML como texto; la imagen en base64), que se decodificó sin cambios. Las capturas se reducen de 2560 de ancho a 1280, como las anteriores.
- **Archivos guardados** en [stitch-asistencia-pantalla/](stitch-asistencia-pantalla/): `asistencia-escritorio.png` y `asistencia-escritorio.html`; `asistencia-angosta.png` y `asistencia-angosta.html`.
- Los dos HTML usan Tailwind, Google Fonts y Material Symbols por CDN: **no se copian**; la implementación los traduce a los tokens CSS del proyecto, sin dependencias nuevas (CSP `default-src 'self'`).
- **Revisión del HTML** (datos y secretos): solo los emails ficticios de la demo (`recepcion@consultorio-demo.test` en la de escritorio y `odontologa@consultorio-demo.test` en la angosta), los tres pacientes ficticios del seed y las prestaciones del seed. Sin teléfonos, documentos, contraseñas, claves de API ni tokens (la única coincidencia de «contraseña» es el enlace «Mi contraseña» de la barra); Stitch no inventó pacientes ni profesionales.

### Qué muestra la de escritorio

La barra del panel con «Agenda» activa; la agenda a la izquierda (sin atenuar) con la columna «ACCIONES» y, en las filas «Confirmado» y «Reservado», los botones con borde «Asistencia» (tilde en círculo), «Reprogramar» (calendario), «Cancelar» (texto e ícono rojos) e «Historial» (reloj); las filas «Atendido» (verde) y «Ausente» (rojo suave) solo con «Historial»; la fila de Carla Inventada resaltada (fondo celeste y franja izquierda) con su «Asistencia» con borde azul. **Con el panel abierto a 1280 px, los cuatro botones no entran**: la columna «ACCIONES» se corta a la derecha y «Historial» queda tapado (hallazgo para el design, X11). A la derecha, el panel «Registrar asistencia» con ícono azul y X; el resumen «Carla Inventada · Obturación» y «viernes 30 de octubre de 2026, 16:00 – 17:00» con el chip «Reservado»; el aviso rojo suave con el texto de `RN-AG-13` y «El turno no cambió.»; el rótulo «¿Cómo terminó el turno?» en tipografía normal y dos opciones en filas con borde y radio, «Atendido» (marcada, con borde azul) y «Ausente», sin descripciones; la ayuda «El horario queda libre para otro turno.» con ícono de información; el pie fijo con «Volver» y «Registrar asistencia» azul. Sin pie institucional. Agregó por su cuenta un subtítulo «Horas del consultorio (America/Argentina/Buenos_Aires).» y un campo de fecha «30/10/2026», que ya existen en la agenda de C-14.

### Qué muestra la angosta

Una columna de unos 390 px con la barra en filas y debajo el panel a todo el ancho (la agenda no se ve): «Registrar asistencia» con la X, el resumen de Bruno Ficticio en una caja gris con el chip «Confirmado», el aviso ámbar «Elegí si el paciente fue atendido o estuvo ausente.», las dos opciones sin marcar en filas altas, la ayuda, «Registrar asistencia» azul a todo el ancho y «Volver» debajo; después el separador «DESPUÉS DE REGISTRAR» con el aviso verde «Asistencia registrada.» y la tarjeta del turno con franja verde, chip «Atendido» y solo «Historial».

### Sugerencias de Stitch no aceptadas

- Escritorio: «Diseñar el estado de éxito tras registrar la asistencia con notificación toast o badge actualizado» (la angosta ya lo muestra; la agenda usa su aviso, no toasts), «Diseñar la versión responsive móvil del flujo de Registrar asistencia» (es 2.2) y «Añadir modal de confirmación cuando se marca como “Ausente” para liberar el turno» (el panel ya es la confirmación: obliga a elegir una opción sin valor por defecto).
- Angosta: «Ver el estado con la opción “Ausente” seleccionada» (lo muestra la de escritorio con «Atendido»), «Mostrar el estado con error de validación cuando el turno todavía no empezó» (lo muestra la de escritorio) y «Generar la versión móvil del listado general de la agenda del día» (existe desde C-14).

**Qué se toma y qué se rechaza**: en el `design.md` de `marcar-atendido-o-ausente`, sección «Referencia visual (Stitch)».

## 4. Comparación con la implementación

Hecha el 2026-10-30 en la tarea 13.1 (a las 11:07 de la hora del consultorio, un viernes: dentro del horario de la demo, sin plan B), con la demo (`crear_app_demo` y `npm run dev`, con la recepcionista y una usuaria solo `dueno` creada para la prueba) y después con Compose, en el navegador integrado de la app. Capturas en `stitch-asistencia-pantalla/`: `implementacion-escritorio-panel-abierto.jpg` (1280 px, panel abierto, cuatro botones en dos líneas), `implementacion-escritorio-rn-ag-13.jpg` (1280 px, el rechazo `RN-AG-13`) e `implementacion-angosta-panel-abierto.jpg` (390 px, panel debajo de la agenda), para comparar con `asistencia-escritorio.png` y `asistencia-angosta.png`.

### Recorrido y resultado (viernes 30/10/2026)

| Paso | Resultado |
|---|---|
| V4: el formulario «Nuevo turno» de la agenda acepta un inicio ya pasado de hoy | Ana a las 09:00 y Carla a las 09:30 (con las 11:07 ya pasadas): «Turno creado.» las dos veces; el historial muestra «Por: Usuario n.º 2» |
| Tres turnos (Ana 09:00, Carla 09:30, Bruno 18:00) | Cada fila `reservado` con «Asistencia», «Reprogramar», «Cancelar» e «Historial», en ese orden |
| ASI-6c: «Registrar asistencia» sin elegir | «Elegí si el paciente fue atendido o estuvo ausente.»; ningún pedido; el aviso desaparece al marcar una opción |
| ASI-5a: Ana, «Atendido» | Un solo `POST /api/turnos/1/estado` con `{"estado":"atendido"}`, «Asistencia registrada.», panel cerrado, un `GET /api/turnos?fecha=…` y la fila solo con «Historial» |
| Otro turno en el mismo horario (Bruno, 09:00) | «Turno creado.»: el horario del marcado quedó libre |
| ASI-5b: Carla, «Ausente» | El `POST` lleva `{"estado":"ausente"}` y la fila queda «Ausente» |
| ASI-6b: Bruno 18:00 (todavía no empezó) | `409` `RN-AG-13`: «El turno todavía no empezó: la asistencia se registra desde su hora de inicio (RN-AG-13).» y «El turno no cambió.»; el panel sigue abierto con «Atendido» marcado y el turno sigue «Reservado» |
| ASI-6a: dos pestañas con su propia sesión de la misma usuaria; la segunda marca a Bruno 09:00 y la primera (sin recargar) lo intenta | «Este turno ya no admite registrar la asistencia por su estado (RN-AG-12).» y «El turno no cambió.»; el panel sigue abierto con la opción marcada y sin «Asistencia registrada.» |
| Historial de Ana | «Turno creado» (con «Estado inicial: Reservado · 09:00 – 09:30») y **«Cambio de estado»** con «Por: Usuario n.º 2» y «Estado: Reservado → Atendido» |
| Un solo panel a la vez entre cinco | «Nuevo turno», «Asistencia», «Reprogramar», «Cancelar» e «Historial» en secuencia: en cada paso hay un solo título de panel |
| Usuaria solo `dueno` (D312) | Ve «Asistencia» en el turno `reservado` y al registrar recibe «Tu usuario no tiene permiso para registrar la asistencia (RN-AU-05).» con «El turno no cambió.» |
| API (`curl`, el mismo recorrido que en `/docs`, que responde `200`) | `409` `["RN-AG-13"]` (turno futuro), `422` sin códigos con el cuerpo vacío, `409` `["RN-AG-12"]` sobre un turno ya marcado; `/openapi.json` tiene `/turnos/{turno_id}/estado`; la agenda y el turno no traen `es_nuevo` |
| 1280 px (demo), panel abierto | Los cuatro botones pasan a dos líneas dentro de la celda («Asistencia» y «Reprogramar» arriba; «Cancelar» e «Historial» abajo); sin desplazamiento horizontal (`scrollWidth` 1280) |
| 390 px (demo), panel abierto | Sin desplazamiento horizontal (`scrollWidth` 390); los botones en dos filas de dos dentro de la tarjeta; el panel va debajo de la agenda, con las opciones de 44 px y «Registrar asistencia» y «Volver» a todo el ancho |
| Compose (`http://127.0.0.1:5173`), turnos del 30/10/2026 | La API aplicó `0010` al arrancar (`alembic_version` `0010`); un turno ya empezado marcado «Atendido» con un solo `POST`; el futuro, `RN-AG-13`; consola sin mensajes de la CSP; a 1280 y a 390 px sin desplazamiento horizontal con el panel abierto; ningún token, contraseña ni dato de paciente en la URL |

### Diferencias con Stitch y su motivo

- **El panel va dentro de la página, al costado de la agenda** (con el pie dentro de la tarjeta), como los otros tres paneles, y no como columna de alto completo con el pie fijo abajo; a 390 px va debajo de la agenda y no la reemplaza.
- **La tabla de Stitch recorta la columna «Acciones»** (se ve «AC» y «H»); no se toma: en la implementación los cuatro botones pasan a otra línea dentro de la celda y se ven completos a 1280 px.
- **Sin el aviso verde ni la muestra «Después de registrar»** de la captura angosta (decisión del design): el éxito se ve como «Asistencia registrada.» sobre la tabla.
- **La opción marcada de la captura de escritorio** se dibuja con borde celeste y círculo relleno, como en la implementación; Stitch la pone un poco más gruesa. Diferencia menor, aceptada.
- El aviso lleva el código entre paréntesis y «El turno no cambió.» en la misma caja, como en C-16 y C-17; el aviso ámbar de «Elegí si…» de la captura angosta es el mismo componente de aviso del panel.
- Sin el pie institucional ni textos de relleno.

### Hallazgos fuera del alcance de C-18

- **1024 px con un panel abierto**: la tarjeta de la tabla (`overflow: hidden`) recorta unos 20 px del borde derecho de los botones («Asistencia» y «Historial» a 1024 px; la tabla mide 557 px en una tarjeta de 548). No hay desplazamiento horizontal de la página. Los anchos pedidos por la tarea (1280 y 390 px) están bien. No se comprobó contra C-17 (sin «Asistencia»); el ancho mínimo de la celda lo marca «Reprogramar». Queda como mejora para un change de pulido de la agenda.
