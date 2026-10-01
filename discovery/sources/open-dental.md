# Open Dental

- **URL**: https://www.opendental.com/
- **Fecha de investigación**: 2026-10-01

## Problema que resuelve

Software de gestión de consultorio odontológico (agenda, ficha clínica, facturación, seguros) con precio publicado y API abierta; el home habla de "affordable price" y de cientos de puentes ("Bridges") a otros programas.

## Usuarios objetivo

Consultorios y clínicas dentales, principalmente en EE.UU. (precio publicado "por ubicación", hasta 3 dentistas por local). Segmento exacto fuera de EE.UU.: (no publicado).

## Features detectadas

- Agenda con módulo de citas, ASAP List (lista de pacientes que quieren turno más temprano) [Comprobado, manual]
- Web Sched: Recall, New Patient, Existing Patient y ASAP; crean/actualizan turnos y alertan al staff [Comprobado, manual/sitio]
- eReminders, mensajes automáticos de agradecimiento, texting integrado, Patient Portal, Web Forms [Comprobado, página de precios]
- Odontograma gráfico 3D ("3D tooth chart") [Afirmación comercial, home]
- 20+ clearinghouses, 100s de bridges, conversión desde 200+ sistemas [Afirmación comercial]
- API REST pública (130+ grupos de recursos) [Comprobado, documentación]

## Pricing

- USD 199/mes por ubicación, contrato inicial de 12 meses; luego baja a una tarifa reducida cuya cifra no se muestra en la página leída. Hasta 3 dentistas por ubicación.
- Incluye software, releases, soporte telefónico, módulo de imágenes Acquire/Video Capture, Web Forms, Patient Portal, eReminders, agradecimientos automáticos.
- Web Sched: "cada servicio tiene tarifas adicionales por mes/por ubicación" (monto no publicado en las páginas leídas). Garantía 90 días. Capacitación y conversión de datos con costo extra.
- Precios fuera de EE.UU.: documento aparte, no leído.

## Posicionamiento

Software completo, económico, con ecosistema abierto de integraciones y comunidad de usuarios.

## Diferenciadores

API pública documentada, precio transparente, modos de API local y remoto, amplia conversión de datos (según su discurso).

## Notas del investigador

Ver "Relevamiento detallado". Limitación: WebFetch devuelve resúmenes; varias URLs del manual dieron 404.

## Relevamiento detallado

**Fuentes (consultadas 2026-10-01)**: https://www.opendental.com/ ; https://opendental.com/site/order.html ; https://www.opendental.com/site/websched.html ; https://www.opendental.com/manual/asaplist.html ; https://opendental.com/site/apiimplementation.html ; búsqueda que cita https://www.opendental.com/site/apispecification.html y https://www.opendental.com/resources/OpenDentalAPI.pdf (no leídos directamente).

- **Empresa / país**: Open Dental Software. País: no mostrado en home; la tarifa es en USD y "U.S." (inferencia: EE.UU., no confirmado en página). [No evidenciado explícitamente]
- **Segmento**: consultorios general/multi-local. [Comprobado: precio por ubicación]
- **Modalidad**: Local (servidor) y API remota/local. Nube/hosting propio: No evidenciado. [Comprobado: API Remote vs Local]
- **Agenda**: módulo de citas y ASAP List con filtros por profesional, clínica, procedimiento [Comprobado]. Vistas, sillones/operatorios, bloqueos, sobreturnos, anti-solapamiento: No evidenciado (URL del manual del módulo dio 404).
- **Turnos digitales**: reserva online New/Existing Patient y Recall; link único para reclamar/rechazar hueco en ASAP [Comprobado]. Confirmación/cancelación por paciente: No evidenciado. Chatbot / redes: No evidenciado.
- **Automatización**: recordatorios automáticos con link Web Sched Recall; ASAP por texto (en doc. de la ASAP List solo texto; en Web Sched también email). Documentación de ASAP: no menciona seguimiento de respuestas. [Comprobado]. Campañas / recuperación de ausentes: No evidenciado.
- **Clínica**: odontograma 3D [Afirmación comercial]; periodontograma e imágenes: No evidenciado en la página leída (imágenes: módulo Acquire/Video Capture incluido, según precios). Presupuestos/planes: No evidenciado.
- **Administración**: facturación con "Billing Defaults" mencionada en novedades v26.2; clearinghouses 20+ [Afirmación comercial]. Señas, seguros detalle: No evidenciado.
- **Integraciones**: API REST con Developer Key + Customer Key; endpoint https://api.opendental.com/api/v1; paginación 100 (1000 local); throttling 1 req/5 s (ApiReadAll) o 1/s [Comprobado]. Google Calendar, WhatsApp, pagos: No evidenciado.
- **Operación**: multi-ubicación (precio por ubicación). Roles, auditoría, exportación: No evidenciado. Soporte telefónico incluido, 2 consultas por contacto [Comprobado].
- **Seguridad/cumplimiento**: No evidenciado (solo "Secure Email").
- **Modelo comercial**: ver Pricing. Sin plan gratis; garantía 90 días.
- **Fortalezas**: precio claro, API abierta. **Limitaciones**: agenda con intervención manual en ASAP; sin pricing de Web Sched.
- **Adopción**: No evidenciado en las páginas leídas.
- **Aplicabilidad Argentina**: idioma inglés (localización a español: No evidenciado); moneda USD; facturación ARCA y obras sociales: No evidenciado (orientado a seguros EE.UU.). Útil como referencia de flujo ASAP + Web Sched y de API abierta.
