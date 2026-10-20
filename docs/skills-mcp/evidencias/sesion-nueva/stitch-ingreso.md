# Evidencia: pantalla de inicio de sesión con Stitch (C-49, `inicio-de-sesion-con-diseno-de-stitch`)

Fecha: 2026-10-20. Herramientas del MCP `stitch` ejecutadas por el agente en la sesión del propose. Regla que lo pide: D234 (toda pantalla del frontend parte de una pantalla generada en Stitch).

## 1. Proyecto y design system

- Proyecto existente `projects/14200813501064679723` (el de C-11).
- Design system «Clinical Ops», `assets/b683d44391ab410db2dd48aa71ed0b47` (el mismo de la pantalla de prestaciones).

## 2. Pantalla pedida

`generate_screen_from_text`, de escritorio (`DESKTOP`), modelo `GEMINI_3_8_FLASH`, con este texto (solo los textos de la spec `ingreso-al-panel` y datos ficticios; sin pacientes ni secretos):

> Pantalla de escritorio en español (Argentina): «Inicio de sesión» del panel de un consultorio odontológico chico. Herramienta administrativa sobria, coherente con la pantalla «Prestaciones» de este proyecto (misma marca, tokens y estilo «Clinical Ops»). No es una landing: sin imágenes decorativas, sin ilustraciones, sin textos de marketing.
>
> - Fondo claro. En el centro, una tarjeta blanca angosta (unos 400 px) con borde de 1 px y radio de 8 px.
> - Arriba de la tarjeta: la marca con un ícono simple de diente y el texto «Turnos Odontológicos AR» como título.
> - Formulario con dos campos con etiqueta: «Email» (con el valor ficticio odontologa@consultorio-demo.test) y «Contraseña» (vacío, de tipo contraseña).
> - Debajo de los campos, un aviso de error con ícono de alerta, fondo rojo suave y borde rojo: «El email o la contraseña no son correctos.» (exactamente ese texto, sin título ni código).
> - Un botón primario de ancho completo: «Ingresar».
> - Nada más: sin «Olvidé mi contraseña», sin «Recordarme», sin registro, sin inicio de sesión con Google, sin pie con enlaces.
> - A la derecha de la tarjeta principal, y más chica, una segunda tarjeta de referencia que muestra el mismo formulario vacío con un aviso informativo neutro (no de error), con ícono «i», arriba de los campos: «Tu sesión terminó. Iniciá sesión de nuevo.»
> - Una tercera tarjeta de referencia, también chica, con el botón deshabilitado mostrando «Ingresando…».
>
> Estilo: tipografía Inter, alto contraste, accesible, primario #0284C7, error #DC2626 sobre #FEF2F2.

## 3. Resultado

- **Sin timeout**: la generación terminó en la misma llamada, con estado `COMPLETE`.
- **Pantalla**: `projects/14200813501064679723/screens/d62ed0eb0edc43df833c9b24a24942b6`, «Inicio de sesión - Turnos Odontológicos AR» (2560 × 2048 en Stitch).
- **Archivos guardados** en [stitch-ingreso-pantalla/](stitch-ingreso-pantalla/):
  - `pantalla.png`: la captura, descargada a 1280 × 1024 (el mismo tamaño que la de C-11);
  - `pantalla.html`: el HTML generado (`projects/14200813501064679723/files/7102a0fc2bae419e914299966b4d1a19`). Usa Tailwind, Google Fonts (Inter) y Material Symbols por CDN, así que **no se copia**: la implementación lo traduce a los tokens CSS del proyecto, sin dependencias nuevas. Trae, en un campo deshabilitado de la tarjeta «Estado de carga», un valor de contraseña de ejemplo inventado por Stitch: no es un secreto del proyecto y no se usa.
- **Qué muestra**: la tarjeta principal con la marca (ícono de diente y «Turnos Odontológicos AR»), los campos «Email» (con `odontologa@consultorio-demo.test`) y «Contraseña», el aviso de error con ícono y el texto exacto del mensaje genérico, y el botón «Ingresar»; una tarjeta «Sesión expirada» con el aviso informativo «Tu sesión terminó. Iniciá sesión de nuevo.» arriba de los campos; y una tarjeta «Estado de carga» con el botón deshabilitado, un ícono de espera y «Ingresando…».
- **Lo que Stitch agregó sin que se pidiera** (se rechaza en el design, L10): una barra superior con «Turnos Odontológicos | Acceso Seguro de Operatoria» y la insignia «Servidor Clínico Operativo», el subtítulo «Acceso al panel administrativo», un pie «Módulo de Control de Acceso Clínico · Sede Central», las etiquetas «Referencia: …» de las tarjetas de estado y los campos deshabilitados de esas tarjetas.
- Stitch ofreció tres sugerencias de seguimiento (espaciado de las tarjetas, versión móvil y validación en tiempo real); no se aceptó ninguna: la pantalla alcanza para el change y la validación en tiempo real no está en la spec.

## 4. Cómo se usa en el change

Es la **referencia visual** del `design.md` de `inicio-de-sesion-con-diseno-de-stitch` (sección «Referencia visual (Stitch)» y decisiones L2 a L10). La KB y la spec mandan: los textos y el comportamiento son los de `ingreso-al-panel`, y nada de la pantalla agrega reglas de dominio.

## 5. Comparación de la implementación con la pantalla

Pendiente: la hace la tarea 5.2 del change, en el Apply.
