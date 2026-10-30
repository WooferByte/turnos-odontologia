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

Pendiente: la completa la prueba del agente en el navegador del Apply (tarea 12.1).
