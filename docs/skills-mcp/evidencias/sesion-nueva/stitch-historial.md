# Evidencia: historial del turno con Stitch (C-15, `panel-historial-de-turno`)

Fecha: 2026-10-28. Regla que lo pide: D234 (toda pantalla del frontend parte de una pantalla generada en Stitch). Cuándo: en el propose, antes de aprobar el plan (como D301 de C-10, C-50 y C-14). Procedimiento: el de [stitch-agenda.md](stitch-agenda.md).

**Estado: hechas (2026-10-28, en el `/opsx:propose` del change).** Las dos pantallas se generaron con el MCP `stitch` al primer intento cada una, y el MCP devolvió sus ids directamente (sección 3b).

## 1. Proyecto y design system

- Proyecto existente `projects/14200813501064679723` (el de C-11, C-49, C-09, C-12, C-13, C-10, C-50 y C-14).
- Design system «Clinical Ops», `assets/b683d44391ab410db2dd48aa71ed0b47` (confirmado con `list_design_systems` antes de generar).

## 2. Pantallas pedidas

`generate_screen_from_text`, modelo `GEMINI_3_8_FLASH`, con el design system de arriba. Como mucho **dos intentos** por pantalla. Solo textos del spec `pantalla-de-historial`, los pacientes ficticios del seed («Ana Ejemplo», «Bruno Ficticio», «Carla Inventada»), las prestaciones y colores del seed y los emails ficticios de la demo (`.test`); sin pacientes reales, sin teléfonos, sin contraseñas, sin secretos. Los textos del panel son los propuestos en el design (Q3 a Q5), así que pueden cambiar si el autor responde otra cosa.

### 2.1 Historial del turno, escritorio (`DESKTOP`)

> Pantalla de escritorio en español (Argentina): la «Agenda del día» del panel de un consultorio odontológico chico con el panel lateral «Historial del turno» abierto a la derecha. Herramienta administrativa sobria, de solo lectura, coherente con las pantallas «Agenda», «Prestaciones» y «Bloqueos» de este proyecto (misma barra superior horizontal, marca y estilo «Clinical Ops»; sin barra lateral de navegación). Sin imágenes decorativas, sin fotos, sin textos de marketing.
>
> - Barra superior: marca con ícono simple de diente y «Turnos Odontológicos AR»; pastillas «Agenda» (activa, …), «Prestaciones», «Usuarios», «Horario», «Bloqueos» y «Mi contraseña»; a la derecha «recepcion@consultorio-demo.test» con «Recepcionista» debajo en gris chico, una línea vertical fina y el botón con borde «Cerrar sesión».
> - A la izquierda: título «Agenda del día», subtítulo «Horas del consultorio (America/Argentina/Buenos_Aires).», botón primario «Nuevo turno»; barra de fecha con «Día anterior», «02/11/2026», «lunes 2 de noviembre de 2026», «Día siguiente» y «Hoy».
> - Tabla densa con columnas HORA, PACIENTE, PRESTACIÓN, ESTADO y una última columna sin título con un botón chico con borde «Historial» (ícono de reloj) en cada fila. […] Filas (datos ficticios): «09:00 – 09:30» «Ana Ejemplo» […] «Consulta / control» chip «Reservado» — esta fila está seleccionada […]; «10:00 – 10:45» «Bruno Ficticio» […] «Limpieza» […]; «11:00 – 12:00» «Carla Inventada» […] «Obturación» […].
> - Panel lateral derecho (unos 420 px, borde izquierdo, sin oscurecer la agenda): título «Historial del turno» y botón «Cerrar» con ícono X. Debajo, un resumen del turno en gris: «Ana Ejemplo · Consulta / control», «lunes 2 de noviembre de 2026, 09:00 – 09:30». Una nota chica gris: «Solo lectura: el historial no se puede editar.»
> - Una línea de tiempo vertical […] con los eventos del más antiguo al más reciente […]: 1. «Turno creado» […] «lunes 26 de octubre de 2026, 10:15» […] «Por: Usuario n.º 2»; detalle gris «Estado inicial: Reservado · 09:00 – 09:30». 2. «Turno creado» de otro ejemplo para mostrar un actor sin identificar: «martes 27 de octubre de 2026, 08:40», «Por: Usuario del panel (sin identificar)».
> - Debajo, separado por una línea punteada y con el rótulo gris «Estados alternativos», tres ejemplos chicos: «Este turno no tiene eventos registrados.»; un aviso rojo suave «El turno ya no existe (RN-GL-04).»; y un aviso «No se pudo conectar con el servidor. Probá de nuevo en unos minutos.» con un botón con borde «Reintentar».
> - Pie del panel: solo el botón con borde «Cerrar». Ningún botón de editar, borrar ni guardar.
>
> Estilo: Inter, primario #0284C7, texto #0F172A, texto secundario #64748B, bordes #E2E8F0, fondo #F8FAFC, radio 4 px en botones, 8 px en tarjetas, sin sombras fuertes salvo la del panel lateral, números tabulares en horas y fechas.

(Pedido resumido acá con «[…]»; los textos entre comillas son los enviados.)

### 2.2 Historial del turno, angosta (pedida como `MOBILE`)

> Pantalla angosta (celular, unos 390 px de ancho) en español (Argentina): el panel «Historial del turno» de la agenda de un consultorio odontológico chico, abierto a todo el ancho sobre la agenda. […] sin desplazamiento horizontal de la página.
>
> - Barra superior en varias filas, igual que la agenda angosta del proyecto […] «odontologa@consultorio-demo.test» […] con «Odontólogo · Dueño» […] «Cerrar sesión».
> - Panel a todo el ancho con borde superior: título «Historial del turno» y botón «Cerrar» con ícono X a la derecha. Debajo, el resumen del turno en gris: «Bruno Ficticio · Limpieza» y «lunes 2 de noviembre de 2026, 10:00 – 10:45». Nota chica gris «Solo lectura: el historial no se puede editar.»
> - Línea de tiempo vertical […] con un evento […]: «Turno creado» […]; «viernes 30 de octubre de 2026, 16:05» […]; «Por: Usuario n.º 1»; detalle gris «Estado inicial: Reservado · 10:00 – 10:45».
> - Debajo, separado por una línea punteada y con el rótulo gris «Estados alternativos»: «Cargando historial…» con un ícono de espera simple, y un aviso «Tu usuario no tiene permiso para ver el historial (RN-AU-05).» en rojo suave.
> - Pie: botón con borde de ancho completo «Cerrar». Ningún botón de editar, borrar ni guardar.
>
> Estilo: el mismo de 2.1.

## 3. Resultado de la generación

| Pantalla | Intento | Modelo | Resultado |
|---|---|---|---|
| Historial, escritorio | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `7927310079713986893`); `status` `COMPLETE`. No hizo falta el segundo intento |
| Historial, angosta | 1 de 2 | `GEMINI_3_8_FLASH` | Generó la pantalla y **devolvió el id** (`sessionId` `15945235497347978157`); `status` `COMPLETE`. Aunque se pidió `MOBILE`, la metadata dice `deviceType` `DESKTOP` y 2560 × 2144: la captura muestra la columna angosta (unos 390 px) centrada sobre el lienzo de escritorio, como en C-50 y C-14. Sirve como referencia del acomodo |

## 3b. Pantallas obtenidas (2026-10-28)

| Pantalla | Id | Título en Stitch | Captura (archivo de Stitch) | HTML (archivo de Stitch) |
|---|---|---|---|---|
| Historial, escritorio | `projects/14200813501064679723/screens/2955e5e29bba4982a0b515329e0ff4e1` | «Agenda del día - Historial del turno - Turnos Odontológicos AR» | `projects/14200813501064679723/files/9712cd3d330341dd99d8c04037c0ac79` | `projects/14200813501064679723/files/92dc123be38e428c83aa9878b3d22b1a` |
| Historial, angosta | `projects/14200813501064679723/screens/c80d02b8dbac4e48be68ca11ff787857` | «Agenda del día - Historial del turno móvil - Turnos Odontológicos AR» | `projects/14200813501064679723/files/026899bfc9304c38b7bcc858751fe2a6` | `projects/14200813501064679723/files/810d6c8c7ca24368969481ee5d50dfce` |

- **Cómo se descargaron**: con el `downloadUrl` de cada archivo y la cabecera `X-Goog-Api-Key` (la clave sale de `STITCH_API_KEY` en el entorno, nunca escrita en el repo); la respuesta es un JSON con `dataString` (el HTML como texto; la imagen en base64), que se decodificó sin cambios. Las capturas se reducen de 2560 de ancho a 1280, como las anteriores.
- **Archivos guardados** en [stitch-historial-pantalla/](stitch-historial-pantalla/): `historial-escritorio.png` y `historial-escritorio.html`; `historial-angosta.png` y `historial-angosta.html`.
- Los dos HTML usan Tailwind (`cdn.tailwindcss.com`) y Google Fonts por CDN (Inter): **no se copian**; la implementación los traduce a los tokens CSS del proyecto, sin dependencias nuevas (CSP `default-src 'self'`).
- **Revisión del HTML** (datos y secretos): solo los emails ficticios de la demo (`odontologa@consultorio-demo.test` y `recepcion@consultorio-demo.test`), los tres pacientes ficticios del seed y las prestaciones y colores del seed. La única coincidencia de «contraseña» es la pastilla «Mi contraseña» de la barra. Sin teléfonos, documentos, contraseñas, claves de API ni tokens; Stitch no inventó pacientes ni profesionales.

### Qué muestra el historial de escritorio

La barra del panel con «Agenda» activa, la agenda a la izquierda (sin atenuar) con una columna final de botones «Historial» con ícono de reloj, la fila de Ana Ejemplo resaltada, y el pie «3 turnos agendados» con «Agenda sincronizada en tiempo real». A la derecha, el panel lateral «Historial del turno» con una etiqueta «SOLO LECTURA», la X, el resumen («Ana Ejemplo · Consulta / control», «lunes 2 de noviembre de 2026, 09:00 – 09:30») y la nota en itálica; el rótulo «TRAZABILIDAD DE EVENTOS» y una línea de tiempo con dos tarjetas («Turno creado», fecha, «Por: Usuario n.º 2», «Estado inicial: Reservado · 09:00 – 09:30» con un punto azul; la segunda con «Por: Usuario del panel (sin identificar)» en itálica), cada una con un rótulo «EV-01» / «EV-02»; el separador «ESTADOS ALTERNATIVOS» con el vacío (recuadro punteado), el `RN-GL-04` en rojo suave con el código en monoespaciada y el de conexión en ámbar con «Reintentar»; y el pie con «Cerrar» a todo el ancho del panel. Un pie de página institucional («Módulo de Agenda y Turnos del Día · Sede Central»).

### Qué muestra la angosta

Una columna de unos 390 px con la barra en tres filas (marca; pastillas en dos líneas; usuario y «Cerrar sesión»), y debajo el panel a todo el ancho (la agenda no se ve): «Historial del turno» con «SOLO LECTURA» y la X, el resumen de Bruno Ficticio, la nota, «TRAZABILIDAD DE EVENTOS» con «1 evento registrado», una tarjeta («Turno creado», «viernes 30 de octubre de 2026, 16:05», «Por: Usuario n.º 1», «Estado inicial: Reservado · 10:00 – 10:45», «EV-01»), el separador con «Cargando historial…» (ícono de espera) y el aviso rojo de `RN-AU-05`, y «Cerrar» a ancho completo.

### Sugerencias de Stitch no aceptadas

- Escritorio: «Ver versión responsive para dispositivos móviles de este panel» (es 2.2), «Agregar evento de cancelación o reprogramación en la línea de tiempo» (esos eventos los crean C-16 y C-17; este change solo tiene `creado`) y «Diseñar el modal de confirmación al reintentar la conexión» (reintentar no necesita confirmación).
- Angosta: «Agregar un evento de cancelación o reprogramación…» (ídem), «Ver la versión con múltiples eventos históricos acumulados» (la escritorio ya muestra dos) y «Adaptar la vista de error de conexión con botón de reintento» (la escritorio ya lo muestra).

**Qué se toma y qué se rechaza**: en el `design.md` de `panel-historial-de-turno`, sección «Referencia visual (Stitch)».

## 4. Comparación con la implementación

Hecha el 2026-10-29 en la tarea 6.1, con la demo (`crear_app_demo` y `npm run dev`) y después con Compose, en el navegador integrado de la app. Capturas de la implementación en `stitch-historial-pantalla/`: `implementacion-historial-escritorio.jpg` (1280 px) e `implementacion-historial-angosta.jpg` (390 px).

### Recorrido y resultado

| Paso | Resultado |
|---|---|
| V3: la recepcionista da un turno el lunes 2/11/2026 a las 09:00 (paciente 1, Consulta / control) y pulsa «Historial» | Panel «Historial del turno» con «Ana Ejemplo · Consulta / control», «lunes 2 de noviembre de 2026, 09:00 – 09:30», «Solo lectura: el historial no se puede editar.» y «Turno creado» con la hora del consultorio (08:25), «Por: Usuario n.º 2» y «Estado inicial: Reservado · 09:00 – 09:30». Sin campos ni acciones de edición; el foco va al título |
| «Cerrar» (botón del pie) | El panel se cierra, ningún pedido nuevo y el foco vuelve al botón «Historial» de la fila |
| Un solo panel a la vez | «Nuevo turno» cierra el historial y «Historial» cierra «Nuevo turno»; «Día siguiente» cierra el historial |
| La odontóloga y una usuaria solo `dueno` (creada para la prueba) | Ven el mismo historial |
| `GET /turnos/1/historial` (API) | El mismo evento `creado`, con `actor_id` `"2"`; `/openapi.json` lista la ruta |
| Pedidos al abrir | En la demo con `npm run dev` se ven dos `GET …/historial`: es el `StrictMode` de React, que en desarrollo monta los efectos dos veces. En Compose (build de producción) hay **uno solo**, como dice el README |
| Compose (`http://127.0.0.1:5173`), turno del 9/11/2026 | El historial se abre con su evento `creado`; consola vacía (ninguna violación de la CSP) |
| 390 px (demo y Compose) | Sin desplazamiento horizontal (`scrollWidth` = 390); el panel queda debajo de la agenda |

### Diferencias con Stitch y su motivo

- **El panel va dentro de la página, al costado de la agenda**, y no como columna de alto completo pegada al borde: es el mismo panel lateral de «Nuevo turno» (D327).
- **Sin la etiqueta «SOLO LECTURA» ni «EV-01»**, sin el subtítulo «Trazabilidad de eventos» ni la sección «Estados alternativos»: la nota de solo lectura es un texto (D330), los ids no se muestran (D329) y los estados alternativos de la captura son los mensajes del panel, que aparecen de a uno.
- **El aviso de error lleva el código entre paréntesis** y no en un chip (D323, D330).
- **Sin «Agenda sincronizada en tiempo real»** ni pie de página, igual que en C-14.
- A 390 px el botón «Historial» va en la tarjeta del turno y el panel debajo de la agenda, como en la captura angosta.
