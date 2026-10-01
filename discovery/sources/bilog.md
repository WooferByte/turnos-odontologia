# Bilog

- **URL**: https://bilog.com.ar/
- **Fecha de investigación**: 2026-10-01

## Problema que resuelve

Digitaliza la gestión de consultorios y clínicas odontológicas: turnos, pacientes, historia clínica, recordatorios, liquidaciones a obras sociales e indicadores, en un solo sistema en la nube.

## Usuarios objetivo

Consultorios odontológicos y clínicas con múltiples profesionales (sillones/consultorios).

## Features detectadas

- Agenda diaria y por profesional, multi-profesional, sillones/consultorios
- Reserva, cancelación y consulta de turnos online por el paciente
- Recordatorios por WhatsApp y SMS
- Odontograma, galería de imágenes clínicas, presupuestos
- Liquidaciones y validaciones de obras sociales; facturación electrónica
- IA ("iAngela") para análisis radiográfico y gestión

## Pricing

(no publicado) en la home; la página indica moneda pesos argentinos pero sin planes. Se pide demo (/solicitar-demo).

## Posicionamiento

Sistema argentino para consultorios y clínicas, con foco en obras sociales, IA y escala (+1.500 clínicas, +5.000 usuarios, según la propia web).

## Diferenciadores

Afirma: IA radiográfica, validaciones/liquidaciones de obras sociales, multi-sucursal, centro de ayuda público (docs.bilog.com.ar).

## Notas del investigador

Extracción hecha vía WebFetch (resumen de la home). No se leyó docs.bilog.com.ar, por lo que las funciones son en su mayoría afirmaciones comerciales.

---

## Relevamiento detallado

Fuente: https://bilog.com.ar/ (consultada 2026-10-01). Etiquetas: [C] Comprobado = doc/precios/ayuda/demo pública; [AC] Afirmación comercial = marketing del proveedor; NE = No evidenciado.

- **Empresa / país / segmento**: Bilog, Argentina [AC]. Segmento: consultorio y clínica [AC].
- **Modalidad**: SaaS nube (app.bilog.com.ar) [AC].
- **Agenda**: vista diaria y por profesional, multi-profesional, sillones/consultorios [AC]. Duración variable, bloqueos, sobreturnos, anti-solapamiento: NE.
- **Turnos digitales**: reserva/cancelación/consulta online [AC]. Link/redes/chatbot/lista de espera/reprogramación: NE.
- **Automatización**: recordatorios WhatsApp y SMS [AC]. Ausentes, recuperación, campañas, controles periódicos: NE.
- **Clínica**: odontograma, galería de imágenes, presupuestos [AC]. Periodontograma: NE. Anamnesis/planes de tratamiento: NE.
- **Administración**: obras sociales (liquidaciones y validaciones) [AC]; facturación electrónica [AC]. Mercado Pago, señas, caja: NE.
- **Integraciones**: IA iAngela [AC]. WhatsApp API oficial, Google Calendar, API pública, ARCA explícito: NE. (Órbita lista a Bilog como integración, ver orbita.md.)
- **Operación**: roles [AC], múltiples sucursales [AC]; soporte WhatsApp y email [AC]; ayuda docs.bilog.com.ar (no leída). Auditoría/exportación: NE.
- **Seguridad/cumplimiento**: backup/redundancia y Ley 25.326: NE.
- **Modelo comercial**: precios en ARS (planes no publicados); prueba gratis NE; demo bajo solicitud [AC].
- **Evidencia de adopción**: "+1.500 clínicas y consultorios, +5.000 usuarios activos" [AC, cifra publicada por el proveedor].
- **Fortalezas/limitaciones**: amplitud funcional declarada; precios opacos; sin verificación independiente.


---

## Segunda pasada (2026-10-01)

Etiquetas: [C] Comprobado (documentación/precios/ficha de app), [AC] Afirmación comercial, NE No evidenciado. WebFetch dio resúmenes. Algunas páginas de docs son marcadores vacíos (faq, data-recovery; docs actualizados 2026-03-26). Cifras de precios vistas en resultados de búsqueda ($589,40 ARS; USD 25) no son verificables y probablemente obsoletas: no se usan.

**Correcciones importantes**
- **WhatsApp NO es automático** según la documentación: el envío individual es gratis en todos los planes, el masivo requiere módulo adicional, se manda desde un "número externo autorizado por BILOG", y "no se puede programar para que se envíe por sí sola" [C, https://docs.bilog.com.ar/schedule/reminders]. La nota previa era incompleta: es manual/semiautomático. Sí hay confirmación bidireccional por palabra clave ("confirmo"/"cancelo" cambian el estado del turno) [C]. API oficial vs. QR: no especificado.
- **Precios**: existe plan Freemium gratis, más Lite y Premium (el más elegido), cotizados por usuario sin precios publicados; pago mensual por tarjeta, transferencia o depósito; sin permanencia [C, https://bilog.com.ar/planes]. Corrige "(no publicado)" sin mención del plan gratuito. Agenda online gratuita limitada a 15 días; 30/60/90 días son pagos [C, /schedule/online-appointment]. Moneda ARS: inferida.
- **Reserva online** con link directo y QR [C, /schedule/online-appointment]. El paciente reserva con DNI + email + CAPTCHA; confirmación por email, sin WhatsApp [C, /schedule/app-appointment]. Cancelación por el paciente: opcional, la activa el profesional, con ventana mínima y tope de turnos activos [C]. Reprogramación: NE.
- **Agenda**: "Nuevo sobreturno" y anulación de turno para bloquear/extender atención [C, /schedule/appointments]; estados: Presente, Atendido, Ausente con/sin aviso, Confirmado, Cancelado, Sin confirmar. Bloqueo de feriados/vacaciones: solo en resumen de búsqueda, no confirmado en la página. Solapamiento, duración, recurrentes, lista de espera, historial de cambios: NE.
- **App móvil**: app nativa iOS "Bilog Gestión Odontológica" v7.21.1 (iPhone/iPad iOS 15.5+, gratis, sin calificaciones suficientes, "no recopila datos") [C, https://apps.apple.com/us/app/bilog-gesti%C3%B3n-odontol%C3%B3gica/id1554140449]. Google Play com.bilog.gomobile existe (aparece en búsqueda; ficha no legible por WebFetch: limitación). Hay además "App de turnos" (portal del paciente).
- **iAngela**: asistente IA para turnos/pacientes por chat, con confirmación previa de cada acción (changelog 2026-03-16) [C]. Análisis radiográfico: solo en resultados de búsqueda, no confirmado.
- **ARCA, backup, Ley 25.326, auditoría, exportación**: NE (FAQ y data-recovery vacías). Sí hay docs de presupuestos, laboratorio, prestaciones, pagos, liquidaciones y portal del paciente.
- **Adopción**: +1.500 clínicas y +5.000 usuarios sigue siendo [AC] sin verificación independiente. Mercado Pago/seña: NE (existe payments.bilog.com.ar, no leído). Empresa: BILOG S.R.L., Buenos Aires.
