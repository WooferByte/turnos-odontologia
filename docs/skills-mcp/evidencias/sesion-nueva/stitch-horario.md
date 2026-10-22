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
