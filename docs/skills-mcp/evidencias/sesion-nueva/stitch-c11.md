# Evidencia: diseño de C-11 (`panel-de-prestaciones`) con Stitch

Fecha: 2026-10-19. Herramientas del MCP `stitch` ejecutadas por el agente en la sesión del propose.

## 1. Proyecto

`create_project` → `projects/14200813501064679723`, «Turnos Odontológicos AR — C-11 panel-de-prestaciones», privado, de escritorio.

## 2. Pantalla pedida

`generate_screen_from_text` (escritorio), con este texto (solo datos ficticios del dominio, sin pacientes ni secretos):

> Pantalla de escritorio en español (Argentina) del panel de un consultorio odontológico chico: «Prestaciones». Es una herramienta administrativa sobria y clara, no una landing.
>
> - Barra superior simple del panel con el nombre «Turnos Odontológicos» y un botón «Cerrar sesión». Sin datos personales del usuario.
> - Título «Prestaciones» y un botón primario «Nueva prestación» (solo visible para el rol odontólogo).
> - Tabla con columnas: Color (un círculo con el color hex), Nombre, Duración (en minutos), Reserva online (Sí/No), Estado (insignia «Activa» o «Inactiva»), Acciones («Editar», «Desactivar» o «Reactivar»). Las filas inactivas se ven atenuadas pero siguen en la lista.
> - Datos de ejemplo ficticios: Consulta / control 30 min #1E88E5 activa; Limpieza 45 min #43A047 activa; Obturación 60 min #FB8C00 activa; Extracción 45 min #E53935 activa; Urgencia 30 min #8E24AA inactiva.
> - A la derecha, un panel lateral abierto «Editar prestación» con: campo Nombre, campo Duración en minutos (con ayuda «Mayor que 0 y múltiplo de 5»), selector de color con muestra y valor hex, casilla «Ofrecer en la reserva online», botones «Guardar» y «Cancelar».
> - En el campo Duración se ve un error de validación con el valor 47: «La duración debe ser mayor que 0 y múltiplo de 5 (RN-AG-01)».
> - Un aviso de error junto al nombre, para el caso de nombre repetido: «Ya existe una prestación llamada «Limpieza» (RN-AG-15)».
> - Una nota discreta bajo la tabla: «Cambiar la duración no modifica los turnos ya creados».
>
> Estilo: fondo claro, tipografía legible, alto contraste, accesible, sin imágenes decorativas.

Resultado: la llamada superó el tiempo de espera del cliente (`The operation timed out`). Según las instrucciones de la herramienta, no se reintentó; se consultó el proyecto con `list_screens` y `get_project` durante unos 6 minutos.

## 3. Lo que devolvió Stitch

- **Design system generado: «Clinical Ops»** (`get_project`), pensado para operación interna de consultorios odontológicos:
  - Tipografía Inter en todos los roles, escala compacta (11 a 28 px) y cifras tabulares para números y horarios.
  - Fondo `#F8FAFC`, superficies blancas con borde de 1 px (`#E2E8F0` / `#CBD5E1`) y sin sombras en tablas y tarjetas.
  - Acento primario `#0284C7` (botón primario, foco); error `#DC2626` sobre `#FEF2F2`, con el texto de ayuda debajo del campo; éxito `#16A34A` sobre `#F0FDF4`.
  - Radio de 4 px en campos, botones y celdas, y de 6 a 8 px en tarjetas y paneles.
  - Tablas: encabezado `#F1F5F9` en mayúsculas de 11 px, filas de 40 px y fila seleccionada con borde izquierdo de 3 px.
  - Insignias de estado de 22 px (por ejemplo, «Activa» en verde y «Inactiva» en gris o rojo).
  - Campos de 36 o 40 px; en estado de error, borde rojo y mensaje debajo con un ícono.
- **Pantalla**: `list_screens` seguía vacío al cerrar esta evidencia, aunque el proyecto ya tiene miniatura (`thumbnailScreenshot`). Si la pantalla aparece más tarde, se agrega acá.

## 4. Cómo se usa en el change

Es una **referencia visual** para el `design.md` de C-11 (tokens, densidad, tabla, panel lateral de edición y errores de campo). La KB y la spec mandan: ante un conflicto se sigue la KB, y nada de esto agrega reglas de dominio.
