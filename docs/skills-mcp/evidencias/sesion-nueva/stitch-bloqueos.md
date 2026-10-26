# Evidencia: pantalla de bloqueos con Stitch (C-13, `bloqueos-puntuales`)

Fecha: 2026-10-26. Regla que lo pide: D234 (toda pantalla del frontend parte de una pantalla generada en Stitch). Procedimiento: el de [stitch-horario.md](stitch-horario.md).

**Estado: hecha (2026-10-26, tarea 1.2 del change; D288).** La pantalla se generó con el MCP `stitch` al primer intento y el MCP devolvió su id directamente (ver la sección 3b). Esta evidencia conserva el pedido enviado (sección 2).

## 1. Proyecto y design system

- Proyecto existente `projects/14200813501064679723` (el de C-11, C-49, C-09 y C-12).
- Design system «Clinical Ops», `assets/b683d44391ab410db2dd48aa71ed0b47`.

## 2. Pantalla a pedir

`generate_screen_from_text`, de escritorio (`DESKTOP`), con el design system de arriba. Como mucho **dos intentos**. Texto del pedido (solo textos de los specs `bloqueos-puntuales` y `pantalla-de-bloqueos` y datos ficticios del seed; sin pacientes, sin contraseñas, sin secretos; «Dra. Demo Ficticia» y «Sillón 1» son el profesional y el sillón ficticios del seed):

> Pantalla de escritorio en español (Argentina): «Bloqueos» del panel de un consultorio odontológico chico. Herramienta administrativa sobria, coherente con las pantallas «Prestaciones», «Usuarios» y «Horario» de este proyecto (misma barra superior, marca y estilo «Clinical Ops»). Sin imágenes decorativas, sin fotos, sin textos de marketing.
>
> - Barra superior: marca con ícono simple de diente y «Turnos Odontológicos AR»; pastillas «Prestaciones», «Usuarios», «Horario» y «Bloqueos» (esta última activa); a la derecha, botón con borde «Cerrar sesión». Ningún dato del usuario.
> - Encabezado: título «Bloqueos», subtítulo «Fechas y horas del consultorio (America/Argentina/Buenos_Aires).»
> - Aviso informativo azul suave con ícono: «Un bloqueo impide dar turnos en ese horario (RN-AG-04b). Los turnos que ya estaban no se cancelan.»
> - Tarjeta «Nuevo bloqueo»: selector «Alcance» con «Todo el consultorio», «Un profesional» y «Un sillón»; un segundo selector con «Dra. Demo Ficticia» (visible cuando el alcance es un profesional); campos de fecha y hora «Desde» y «Hasta» (formato 24 h, dd/mm/aaaa hh:mm); campo de texto «Motivo»; botón primario «Bloquear» con ícono de candado o calendario.
> - Debajo del formulario, un aviso de éxito verde suave: «Bloqueo creado. Hay 2 turnos activos en ese horario: no se cancelaron, hay que reprogramarlos o cancelarlos.» y dos filas compactas: «Turno 7 · 02/11/2026 10:00 a 10:30 · reservado» y «Turno 8 · 02/11/2026 11:00 a 11:30 · confirmado».
> - Tarjeta «Bloqueos cargados» con una tabla de columnas «Alcance», «Desde», «Hasta», «Motivo» y una acción «Eliminar» con ícono de papelera por fila. Filas: «Profesional: Dra. Demo Ficticia» · 02/11/2026 09:00 · 02/11/2026 13:00 · Ausencia; «Profesional: Dra. Demo Ficticia» · 09/11/2026 00:00 · 14/11/2026 00:00 · Vacaciones; «Todo el consultorio» · 23/11/2026 00:00 · 24/11/2026 00:00 · Feriado.
> - Un error de ejemplo en rojo bajo el formulario (estado alternativo): «El bloqueo tiene que terminar después de empezar (RN-AG-17).» con el campo «Hasta» con borde rojo.
>
> Estilo: Inter, primario #0284C7, éxito verde suave, error #DC2626 sobre #FEF2F2, radio 4 px en campos y botones, 8 px en tarjetas, filas compactas, sin sombras fuertes.

Versión resumida para el segundo intento (si el primero termina por tiempo de espera): el mismo contenido en un párrafo, con los textos entre comillas exactamente iguales.

## 3. Resultado de la generación

| Intento | Modelo | Texto | Resultado |
|---|---|---|---|
| 1 de 2 | `GEMINI_3_8_FLASH` | El de la sección 2, exacto (`DESKTOP`, design system «Clinical Ops») | Generó la pantalla y **devolvió el id** (`sessionId` `3752066668136894253`); `get_screen` la devuelve por ese id. No hizo falta el segundo intento ni copiar el `node-id` del canvas |

## 3b. Pantalla obtenida (2026-10-26)

- **Pantalla**: `projects/14200813501064679723/screens/05d78d7e7d144f92bb9f77d0e4a220db`, «Bloqueos - Turnos Odontológicos AR», `DESKTOP`, 2560 × 2130 en Stitch.
- **Cómo se obtuvo el id**: a diferencia de C-09 y C-12, `generate_screen_from_text` devolvió el id de la pantalla. (Si otra vez no lo devolviera, `get_project` lista las `screenInstances` con sus ids y sirve de respaldo antes de `list_screens` o del `node-id` de la web.)
- **Archivos guardados** en [stitch-bloqueos-pantalla/](stitch-bloqueos-pantalla/):
  - `pantalla.png`: la captura (`projects/14200813501064679723/files/bd6b89f14ae64a6482a29da36c30f917`), a 1280 × 1065 (el ancho de las anteriores; el alto sigue la proporción);
  - `pantalla.html`: el HTML generado (`projects/14200813501064679723/files/38ffabcf2e4a4ee194d28e264970e785`). Usa Tailwind y Google Fonts por CDN, así que **no se copia**: la implementación lo traduce a los tokens CSS del proyecto, sin dependencias nuevas.
- **Revisión del HTML** (datos y secretos): solo el profesional ficticio del seed («Dra. Demo Ficticia»), «Sillón 1» y los datos ficticios del pedido; el HTML suma una segunda opción de profesional inventada por Stitch, «Dr. Roberto Pérez», que no está en el seed y **no se usa en ninguna parte**. Sin pacientes, teléfonos, documentos, emails, claves ni tokens.
- **Qué muestra**: la barra del panel con las cuatro pastillas y «Bloqueos» activa, y «Cerrar sesión» con borde; el título, el subtítulo con la zona y el aviso informativo azul con ícono (con el prefijo «Aviso operativo:»); dos columnas en escritorio: la tarjeta «Nuevo bloqueo» (a la izquierda, con la insignia «Alta de indisponibilidad», «Alcance», «Profesional asignado», «Desde» y «Hasta» como campos de texto monoespaciados con ayuda «24 h (dd/mm/aaaa hh:mm)», «Hasta» con borde rojo y «Formato o valor incorrecto», el error de `RN-AG-17` en rojo con el prefijo «Error de validación:», «Motivo» y «Bloquear» con candado) y, debajo, «Último resultado operativo» con el aviso verde y las dos filas de turnos afectados con su estado; y la tarjeta «Bloqueos cargados» (a la derecha, con «3 registros activos» y «Orden cronológico») con la tabla Alcance, Desde, Hasta, Motivo y «Eliminar» con papelera, una etiqueta de color por motivo y un pie con «Zona horaria: UTC-3»; más un pie de página institucional.
- **Sugerencias de Stitch no aceptadas**: «Agregar modal de confirmación para eliminar un bloqueo con turnos afectados» (contradice D286: «Eliminar» no pide confirmación y el bloqueo se puede volver a crear), «Ver el estado del formulario sin errores» (no hace falta: es el estado base) y «Diseñar la vista de reprogramación asistida para los turnos 7 y 8 afectados» (fuera del alcance: la reprogramación es de C-16, D83).
- **Qué se toma y qué se rechaza**: en el `design.md` de `bloqueos-puntuales`, sección «Referencia visual (Stitch)».

## 4. Cómo se completó (tarea 1.2 del change, hecha el 2026-10-26)

1. [hecho] En una sesión con el MCP `stitch` conectado (`STITCH_API_KEY` en el entorno, `.mcp.json` del repo), enviar el pedido de la sección 2.
2. [no hizo falta: el MCP devolvió el id] Si `generate_screen_from_text` no devuelve el id y `list_screens` vuelve vacío (problema conocido de C-09 y C-12), abrir el proyecto en la web de Stitch y copiar el `node-id` de la URL de la pantalla.
3. [hecho] Con el id, traer la captura y el HTML (`get_screen`, `download_file`) a `stitch-bloqueos-pantalla/pantalla.png` (1280 de ancho, como las anteriores) y `pantalla.html`. El HTML usa Tailwind, Google Fonts y Material Symbols por CDN: **no se copia**, se traduce a los tokens del proyecto.
4. [hecho] Revisar el HTML: solo datos ficticios, sin pacientes, teléfonos, documentos, emails, claves ni tokens.
5. [hecho] Anotar acá el id, los intentos y qué muestra la pantalla, y completar con un `/opsx:update` la sección «Referencia visual (Stitch)» del `design.md` (qué se toma y qué se rechaza).

## 5. Cómo se usa en el change

Es la **referencia visual** del `design.md` de `bloqueos-puntuales`. La KB y los specs mandan: los textos son los de `pantalla-de-bloqueos` y del design (B17), y nada de la pantalla agrega reglas de dominio. La traducción visual (tarea 8.1) y la comparación con la captura en el navegador (tarea 9.1) se hacen en el Apply y se anotan acá al cerrar el change.

## 6. Prueba en el navegador (tarea 9.1, 2026-10-26)

La hizo el agente en el navegador del panel (escritorio, 1440 × 900), con la demo (`crear_app_demo`, recién arrancada) y `npm run dev`, y después con Compose en `http://127.0.0.1:5173` (PostgreSQL, nginx). Todos los datos y contraseñas son ficticios. Ningún token ni contraseña apareció en una URL (solo `/ingresar`, `/panel` y `/panel/bloqueos`) ni en la consola. Las capturas están en [stitch-bloqueos-pantalla/](stitch-bloqueos-pantalla/) junto a `pantalla.png`.

### API (demo)

Ejecutado con los pedidos del README (con `curl`; `/docs` responde y es el mismo contrato):

| Paso | Esperado | Observado | Ok |
|---|---|---|---|
| `GET /bloqueos` (recepcionista) | `200`, zona del consultorio, lista vacía | Igual | sí |
| `POST /turnos` a las `13:00Z` | `201` | Igual | sí |
| `POST /bloqueos` del profesional de `12:00Z` a `16:00Z` | `201`, el turno en `turnos_afectados` y sigue `reservado` | Igual | sí |
| `POST /turnos` a las `14:00Z` | `422` `["RN-AG-04b"]`, `bloqueo_id` 1 | Igual | sí |
| Bloqueo invertido | `422` `["RN-AG-17"]` en `fin` | Igual | sí |
| `POST` y `DELETE` de la recepcionista | `403` `["RN-AU-05"]` | Igual | sí |
| `DELETE /bloqueos/1` (odontóloga) y repetir `POST /turnos` a las `14:00Z` | `204`, después `201` | Igual | sí |
| `DELETE /bloqueos/99` | `404` `["RN-GL-04"]` | Igual | sí |
| Bloqueo de todo el consultorio el 23/11/2026 | `201`, `alcance` `consultorio`, sin afectados | Igual | sí |
| `profesional_id` y `sillon_id` juntos | `422` de formato, `codigos` vacío | Igual | sí |

### Pantalla (demo, y Compose con PostgreSQL)

| Paso | Esperado | Observado | Ok |
|---|---|---|---|
| La odontóloga pulsa «Bloqueos» | Subtítulo con la zona, nota de `RN-AG-04b`, formulario a la izquierda y «No hay bloqueos cargados.» a la derecha | Igual (`implementacion-lista-vacia.jpg`) | sí |
| «Todo el consultorio», 23/11/2026 00:00 a 24/11/2026 00:00, «Feriado» | «Bloqueo creado. No hay turnos activos en ese horario.» y la fila | Igual | sí |
| Un profesional, 02/11/2026 09:00 a 13:00, «Ausencia» | Aviso con el turno afectado, etiqueta «reservado» | Igual (`implementacion-lista-con-afectados.jpg`); en Compose, con tres turnos de una corrida anterior del volumen, el plural «Hay 3 turnos activos» (`implementacion-compose-afectados.jpg`) | sí |
| Hasta antes que desde | `RN-AG-17`, «Hasta» en rojo, lo cargado se conserva | Igual (`implementacion-error-rn-ag-17.jpg`) | sí |
| «Eliminar» | `204`, «Bloqueo eliminado.», la fila desaparece sin confirmación | Igual | sí |
| La recepcionista abre «Bloqueos» y pulsa «Eliminar» | Ve la lista; `403`, aviso «Acceso restringido» con `RN-AU-05`, sigue en el panel, sin `POST /api/auth/refresh` después del `403` | Igual (`implementacion-403-recepcionista.jpg`) | sí |

En Compose (PostgreSQL, migración `0009` aplicada al arrancar) el recorrido breve de la odontóloga (alta con afectados, error `RN-AG-17`, «Eliminar») dio los mismos resultados; el bloqueo se borró al final y `docker compose down` dejó el volumen como estaba. La consola no mostró ninguna violación de la CSP: solo el «Failed to load resource» del navegador por el `422` esperado (y por el `403` en la demo).

### Comparación con `pantalla.png`

**Coincide**: la barra con las cuatro pastillas y «Bloqueos» activa, el título y el subtítulo con la zona, el aviso azul con ícono, las dos columnas (alta a la izquierda, lista a la derecha), el ícono de calendario del título «Nuevo bloqueo», las etiquetas chicas en mayúsculas, «Bloquear» con candado a todo el ancho, «Hasta» con borde rojo y la caja roja con ícono para `RN-AG-17`, el aviso de éxito verde con una fila por turno y su etiqueta de estado, y la tabla con «Eliminar» en rojo con papelera.

**Difiere, con su motivo** (todo está en «Qué se rechaza» del `design.md`): sin los prefijos «Aviso operativo:» y «Error de validación:» (los textos los fijan B17 y el spec); sin la insignia «Alta de indisponibilidad», «3 registros activos» y «Orden cronológico» (sin respaldo en la KB); la etiqueta «Profesional» en lugar de «Profesional asignado» y sin asteriscos; campos `datetime-local` nativos en lugar de texto monoespaciado, y sin las ayudas «24 h…» y «Formato o valor incorrecto» (B15, D286); sin el encabezado «Último resultado operativo»; el motivo como texto y no como etiqueta de color, y sin el punto de color del alcance (D283); sin el pie «sincronizado en tiempo real», ni «Zona horaria: UTC-3», ni el pie institucional (D173, D285); la barra superior no es fija; y «Dr. Roberto Pérez» no existe (las opciones salen de la API). Además, en la implementación el error de `RN-AG-17` se muestra con el texto del spec y la caja roja debajo del botón, y en la captura de Stitch está entre «Hasta» y «Motivo»: el orden de los bloques de estado es el de B16 (debajo del formulario). Ninguna diferencia nueva respecto de lo decidido.

### Hallazgo de la prueba

Con la demo, justo después de iniciar sesión, un `GET /profesionales` respondió `500` una vez (`ValueError: '' is not a valid Rol` en `UsuarioRepositorio.roles_de`, `backend/app/infrastructure/repositories/usuarios.py`) mientras `GET /bloqueos` y `GET /sillones` iban en paralelo; el modo estricto de React repitió las tres peticiones y la segunda tanda dio `200`. Es el patrón de la conexión única de SQLite en memoria (`StaticPool`) compartida por varios hilos de la API de demostración; no ocurre en Compose (PostgreSQL) y no es de C-13 (es de C-07). Se deja como hallazgo para el archive; no se tocó código.

### Paso a paso para repetirlo (opcional; gobernanza MEDIO)

1. Terminal 1, en `backend/` con el entorno activado: `python -m uvicorn app.main:crear_app_demo --factory`. Terminal 2, en `frontend/`: `npm run dev`. Con la demo recién arrancada, crear el turno con `POST /turnos` (`paciente_id` 1, `prestacion_id` 1, `inicio` `2026-11-02T13:00:00Z`) desde `/docs` con el token de la odontóloga.
2. Abrir <http://127.0.0.1:5173>, ingresar como `odontologa@consultorio-demo.test` y pulsar «Bloqueos». Seguir el recorrido de «Pantalla de bloqueos» del README (pasos 1 a 6) y mirar que cada resultado coincida con la tabla de arriba.
3. Comparar con `stitch-bloqueos-pantalla/pantalla.png` y con las capturas `implementacion-*.jpg` de esa carpeta.
4. Compose: `docker compose up --build -d`, abrir <http://127.0.0.1:5173>, repetir un alta con afectados, el error de `RN-AG-17` y «Eliminar», y mirar la consola del navegador (no tiene que haber violaciones de la CSP). Al final, `docker compose down`.
5. Detener las dos terminales con Ctrl+C.
