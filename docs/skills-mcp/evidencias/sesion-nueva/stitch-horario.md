# Evidencia: pantalla de horario con Stitch (C-12, `horario-recurrente`)

Fecha: 2026-10-22. Herramientas del MCP `stitch` ejecutadas por el agente en la sesión del propose. Regla que lo pide: D234 (toda pantalla del frontend parte de una pantalla generada en Stitch).

## 1. Proyecto y design system

- Proyecto existente `projects/14200813501064679723` (el de C-11, C-49 y C-09).
- Design system «Clinical Ops», `assets/b683d44391ab410db2dd48aa71ed0b47` (el mismo de las pantallas de prestaciones, inicio de sesión y usuarios).

## 2. Pantalla pedida

`generate_screen_from_text`, de escritorio (`DESKTOP`), con el design system de arriba. Texto del primer intento (solo textos de los specs de `horario-recurrente` y `pantalla-de-horario` y datos ficticios; sin pacientes, sin contraseñas, sin secretos; «Dra. Demo Ficticia» es el profesional ficticio del seed):

> Pantalla de escritorio en español (Argentina): «Horario» del panel de un consultorio odontológico chico. Herramienta administrativa sobria, coherente con las pantallas «Prestaciones» y «Usuarios» de este proyecto (misma barra superior, marca y estilo «Clinical Ops»). Sin imágenes decorativas, sin fotos, sin textos de marketing.
>
> - Barra superior: marca con ícono simple de diente y «Turnos Odontológicos AR»; pastillas «Prestaciones», «Usuarios» y «Horario» (esta última activa); a la derecha, botón con borde «Cerrar sesión». Ningún dato del usuario.
> - Encabezado: título «Horario de atención», subtítulo «Franjas semanales en hora del consultorio (America/Argentina/Buenos_Aires).» A la derecha un selector «Profesional» con el valor «Dra. Demo Ficticia» y un botón primario «Guardar horario».
> - Tarjeta «Semana» con siete filas, una por día (Lunes a Domingo). Cada fila: el nombre del día a la izquierda y sus franjas como pares de campos de hora «Desde» y «Hasta» (formato 24 h) con un botón «Quitar» (ícono de papelera) por franja, y al final un botón de texto «Agregar franja» con ícono de más. Lunes a viernes: 09:00 a 13:00 y 15:00 a 19:00. Sábado y domingo: texto gris «Sin atención» y solo «Agregar franja».
> - En la fila del Miércoles, un error de ejemplo en rojo bajo las franjas: «Las franjas del miércoles se superponen.» con las dos franjas 09:00 a 13:00 y 12:00 a 16:00 con borde rojo.
> - Arriba de la tarjeta, un aviso informativo azul suave con ícono: «Los turnos solo se pueden crear dentro de una franja (RN-AG-04). Cambiar el horario no modifica los turnos ya dados.»
>
> Estilo: Inter, primario #0284C7, error #DC2626 sobre #FEF2F2, radio 4 px en campos y botones, 8 px en tarjetas, filas compactas, sin sombras fuertes.

## 3. Resultado de la generación desde el MCP

| Intento | Modelo | Texto | Resultado |
|---|---|---|---|
| 1 | `GEMINI_3_8_FLASH` | El de la sección 2 | `The operation timed out` (tiempo de espera del cliente) |
| 2 | `GEMINI_3_5_FLASH_LITE` | Versión resumida (mismo contenido, en un párrafo) | Respondió con un texto («He verificado y presentado la pantalla de «Horario de atención»…»), tres sugerencias y `sessionId` `15797912621055829697`, pero **sin el id de la pantalla** ni sus archivos |

- Justo después del segundo intento, `list_screens` y `get_project` todavía no mostraban ninguna pantalla de horario. No se generó de nuevo (máximo de dos intentos en el propose).
- Las sugerencias de Stitch («Editar franjas horarias», «Ver módulo de usuarios», «Configurar prestaciones») no se aceptaron.

## 3b. Pantalla obtenida (2026-10-22, en el propose)

- **Cómo se obtuvo el id**: la generación llegó al canvas de Stitch sin que el MCP devolviera su id. El autor abrió el proyecto en la web de Stitch y copió el `node-id` de la URL de la pantalla el 2026-10-22; el orquestador confirmó que `get_screen` la devuelve y el agente la trajo por ese id. No hace falta la tarea bloqueante «Pantalla de Stitch» que tuvo C-09.
- **Pantalla**: `projects/14200813501064679723/screens/c3cccdb362364deba0d4eaac0d678b4d`, «Horario de atención - Turnos Odontológicos AR», `DESKTOP`, 2560 × 2202 en Stitch.
- **Archivos guardados** en [stitch-horario-pantalla/](stitch-horario-pantalla/):
  - `pantalla.png`: la captura (`projects/14200813501064679723/files/f0c2181306b740e289c83c58cc41eaba`), descargada a 1280 × 1101 (el ancho de las de C-11, C-49 y C-09; el alto sigue la proporción);
  - `pantalla.html`: el HTML generado (`projects/14200813501064679723/files/f8d0ff2bd09f4c71b33093c665f12697`), el mismo que devuelve `download_file`. Usa Tailwind, Google Fonts (Inter) y Material Symbols por CDN, así que **no se copia**: la implementación lo traduce a los tokens CSS del proyecto, sin dependencias nuevas.
- **Revisión del HTML** (datos y secretos): solo el profesional ficticio del seed («Dra. Demo Ficticia») y dos nombres de profesionales que Stitch inventó para el selector («Dr. Marcos González», «Dra. Silvia Álvarez»), ficticios y que no se usan. Sin pacientes, teléfonos, documentos, emails, claves ni tokens.
- **Qué muestra**: la barra del panel (marca, pastillas «Prestaciones», «Usuarios» y «Horario» activa, «Cerrar sesión», sin datos del usuario); «Horario de atención» con el subtítulo con la zona del consultorio; el selector «PROFESIONAL:» y el botón primario «Guardar horario» con ícono de guardar; el aviso informativo azul con «Aviso regulatorio:» y el texto de RN-AG-04; la tarjeta «Semana» con la insignia «7 días» y el texto «Doble turno estándar y atención programada»; una fila por día con el nombre y «2 franjas» o «Cerrado», las franjas como cajas con «Desde» y «Hasta» (campos de texto de 24 h) y un ícono de papelera, y «Agregar franja»; el miércoles con las dos franjas en borde rojo, «Conflicto detectado», borde izquierdo rojo y el error «Las franjas del miércoles se superponen.»; sábado y domingo «Sin atención»; el pie de la tarjeta («Configuración activa para la agenda online y recepción», «Zona horaria clínica: UTC-3 (Buenos Aires)») y el pie de página («Módulo de Control de Horarios y Disponibilidad Clínica · Sede Central»).
- **Qué se toma y qué se rechaza**: en el `design.md` de `horario-recurrente`, sección «Referencia visual (Stitch)».

## 4. Cómo se usa en el change

Es la **referencia visual** del `design.md` de `horario-recurrente`. La KB y los specs mandan: los textos son los de `pantalla-de-horario` y del design (H17), y nada de la pantalla agrega reglas de dominio. El error del miércoles del pedido era un ejemplo visual: el mensaje real es el de `RN-AG-16` del spec. La traducción visual y la comparación con la captura en el navegador se hacen en el Apply y se anotan acá al cerrar el change.

## 5. Prueba en el navegador (tarea 12.1, 2026-10-22)

La hizo el agente en el navegador del panel, con la demo (`crear_app_demo`, recién arrancada) y `npm run dev` (`127.0.0.1:5173`), y con el escritorio a 1280 × 1100. Todos los datos y contraseñas son ficticios. Ningún token ni contraseña apareció en una URL (solo `/ingresar`, `/panel` y `/panel/horario`) ni en la consola.

### API (demo)

Ejecutado con los pedidos del README sobre la demo. Antes, se comprobó que `/docs` responde `200`.

| Paso | Esperado | Observado | Ok |
|---|---|---|---|
| `GET /profesionales` y `GET /profesionales/1/horario` (odontóloga) | `200`, diez franjas, zona `America/Argentina/Buenos_Aires` | Igual | sí |
| `PUT` con el miércoles 12:00-16:00 sumado al final | `422` `["RN-AG-16"]`, error en `franjas.10` con el mensaje fijo | Igual | sí |
| `PUT` de la recepcionista | `403` `["RN-AU-05"]` | Igual | sí |
| `POST /turnos` el miércoles a las `13:00Z` | `201` | Igual | sí |
| `POST /turnos` el miércoles a las `11:00Z` (08:00 local) | `422` `["RN-AG-04"]` | Igual | sí |
| `POST /turnos` el sábado a las `13:00Z`, antes de guardar el sábado | `422` `["RN-AG-04"]` | Igual | sí |
| El mismo `POST`, después de guardar el sábado 09:00-12:00 por la pantalla | `201` | Igual | sí |
| `POST /turnos` el viernes a las `19:00Z` (16:00 local), después de quitar la tarde del viernes | `422` `["RN-AG-04"]` | Igual | sí |

### Pantalla (demo)

| Paso | Esperado | Observado | Ok |
|---|---|---|---|
| La odontóloga pulsa «Horario» | Selector «Dra. Demo Ficticia», subtítulo con la zona, nota de `RN-AG-04`, lunes a viernes con dos franjas, sábado y domingo «Sin atención» | Igual (captura `implementacion-semana.jpg`) | sí |
| Agregar al miércoles 12:00-16:00 y «Guardar horario» | `422`; quedan marcadas 12-16 y 15-19, la de 09-13 no (D266); un solo mensaje de `RN-AG-16` en la fila; lo editado se conserva | Igual (captura `implementacion-error-miercoles.jpg`) | sí |
| Sábado 12:00 a 09:00 y «Guardar horario» | El `PUT` se manda; `RN-AG-16` marcado en el sábado | Igual | sí |
| Corregir el sábado a 09:00-12:00, quitar la tarde del viernes y guardar | `200` y «Horario guardado.»; la semana muestra lo guardado | Igual | sí |
| La recepcionista abre «Horario» | Ve la semana guardada | Igual | sí |
| La recepcionista agrega el domingo y guarda | `403`, aviso «Acceso restringido» con `RN-AU-05`, sigue en el panel sin perder la sesión | Igual (captura `implementacion-403-recepcionista.jpg`) | sí |

En la consola solo aparecen los «Failed to load resource» del navegador, por los `422` y el `403` esperados; no hay ningún error de la aplicación.

Un detalle observado, que no es un error: al quitar la franja que causaba la superposición, la marca roja de la otra franja sigue visible hasta el próximo guardado. Las marcas reflejan la última respuesta de la API, sin validación local (D232, H15).

### Compose

Se levantó con `docker compose up -d --build`, con imágenes reconstruidas sobre el código actual, en `127.0.0.1:5173`. Los tres servicios quedaron `healthy`.

- El inicio de sesión con el usuario del seed funcionó con la contraseña de prueba de `.env.example`.
- El volumen de PostgreSQL ya existía, y al arrancar `cargar_horario_demo_si_falta` le cargó el horario de ejemplo (D263 y H12).
- La pantalla «Horario» muestra la semana de la demo.
- Se agregó el sábado 09:00-12:00 y se guardó: «Horario guardado.». Después se quitó esa franja y se guardó de nuevo, para dejar el horario como estaba.
- La consola no registró ningún mensaje: no hay violaciones de la CSP ni recursos de otro origen.
- Al terminar se corrió `docker compose stop`, sin borrar volúmenes.

### Comparación con `stitch-horario-pantalla/pantalla.png`

Las capturas de la implementación están en [stitch-horario-pantalla/](stitch-horario-pantalla/), tomadas a 1280 px de ancho y entregadas a 800 px por el panel de capturas:

- `implementacion-semana.jpg`: la semana de la demo;
- `implementacion-error-miercoles.jpg`: el error `RN-AG-16` del miércoles;
- `implementacion-403-recepcionista.jpg`: el `403` de la recepcionista.

Coincide con Stitch en:

- **Encabezado**: barra con la pastilla «Horario» activa, título y subtítulo con la zona, «PROFESIONAL» con el selector y el botón primario «Guardar horario» con ícono.
- **Nota y tarjeta**: nota informativa azul con ícono y tarjeta «Semana» con una fila por día.
- **Franjas**: cajas grises con «Desde» y «Hasta», papelera y «+ Agregar franja»; «Sin atención» en cursiva gris.
- **Error**: borde rojo en las franjas informadas, fondo rosado y borde izquierdo rojo en la fila, y un solo mensaje con ícono debajo.

Diferencias, todas previstas en «Referencia visual (Stitch)» del `design.md` o en H17:

| Diferencia | Motivo |
|---|---|
| Sin «Aviso regulatorio:», sin la insignia «7 días», sin «Doble turno estándar…» y sin el ícono de la tarjeta | Textos y adornos sin respaldo en la KB |
| Sin «2 franjas», «Cerrado» ni «Conflicto detectado» bajo cada día | Datos que repiten lo que se ve; el error ya se marca en la fila |
| Sin el pie de la tarjeta ni el pie de página | Textos inventados («agenda online», «Sede Central») |
| El mensaje del error es el de `RN-AG-16` (H17), no «Las franjas del miércoles se superponen.» | El spec fija el texto |
| Se marcan solo las franjas que informa la API, no las dos de un par | D266: se informa la posterior de cada superposición |
| Las horas son `<input type="time">`, no campos de texto | Control nativo, sin validación local (H15) |
| El selector solo muestra a los profesionales de la API (en la demo, uno) | Stitch inventó dos profesionales más |
| Las pastillas van a la izquierda, junto a la marca | Es la barra compartida de C-08 y C-11 |
| La fuente es Inter solo si está instalada en el equipo | Sin CDN (CSP `default-src 'self'`) |

### Paso a paso para el autor (opcional, gobernanza MEDIO)

Con la demo recién arrancada (`python -m uvicorn app.main:crear_app_demo --factory` en `backend/` y `npm run dev` en `frontend/`), usuarios `odontologa@consultorio-demo.test` y `recepcion@consultorio-demo.test`, contraseña `demo-consultorio-2026`:

1. Ingresá como la odontóloga y pulsá «Horario». Deberías ver de lunes a viernes de 09:00 a 13:00 y de 15:00 a 19:00, y el sábado y el domingo «Sin atención».
2. Agregá al miércoles una franja de 12:00 a 16:00 y pulsá «Guardar horario». Se marcan en rojo 12-16 y 15-19, con un solo mensaje `RN-AG-16`.
3. Quitá esa franja, agregá el sábado de 09:00 a 12:00 y guardá. Deberías ver «Horario guardado.». En `/docs`, un `POST /turnos` el sábado `2026-11-07T13:00:00Z` da `201`.
4. Cerrá sesión, ingresá como la recepcionista, cambiá algo y guardá. Deberías ver «Acceso restringido» con `RN-AU-05` y seguir en el panel.
