# Integraciones: WhatsApp y Mercado Pago

> Restricción transversal: **presupuesto cero, datos ficticios, sin cuentas creadas con datos reales y sin contactar proveedores** (Discovery, punto 9). Todo lo de esta página es para el prototipo con credenciales y números de prueba.

## WhatsApp

### Situación del mercado (informe C.3.1)

| Competidor | Mecanismo | Evidencia |
|---|---|---|
| DentalCore | Sesión por QR, **no API oficial** (cita del sitio) | [C] en el sitio |
| Bilog | Envío manual/semiautomático; masivo con módulo adicional; confirmación por palabra clave | [C] centro de ayuda |
| Neocita | Manual gratis por enlace; automático en plan pago | [C] |
| Dentalink | Servicio adicional pago, mensaje fijo, confirmación bidireccional; mecanismo no indicado | [C] ayuda |
| Turnito / SimpleTurno | Cupos de mensajes por plan; mecanismo no indicado | [C] precios |
| Naclix | "Canal oficial, tu mismo número" | [AC], no documentado |
| Doctocliq | "Meta Business Partner" | [AC], no documentado |
| Ulifeon | No integra WhatsApp: solo compartir el link | [AC] |

**Conclusión:** un enlace `wa.me` semiautomático está **a la par del mercado**, no por debajo.

### Opción A (preferida): WhatsApp Cloud API en modo prueba
- Meta crea un **número de pruebas** al empezar. El límite de **5 destinatarios verificados proviene de fuentes de terceros: a verificar** (P-04).
- Uso: mensajes de plantilla para recordatorio (RN-WA-01) y oferta de huecos (RN-LE); webhook entrante para respuestas (RN-WA-02).
- Requisitos técnicos: token, `phone_number_id`, webhook HTTPS público con verificación (`hub.verify_token`) y validación de firma. **Suposición:** en desarrollo local se necesita un túnel HTTPS para recibir el webhook.
- **Producción (etapa posterior):** verificación de empresa, plantillas aprobadas y costo por conversación (**sin fuente verificada**, P-06).

### Opción B (alternativa): enlace `wa.me` semiautomático
- El sistema arma el texto (paciente ficticio, fecha, prestación, link de gestión) y genera `https://wa.me/<numero>?text=<texto-codificado>`.
- El odontólogo lo abre y envía desde su WhatsApp. La confirmación vuelve por el **link de gestión**, no por respuesta al chat.
- Sin cuenta, sin costo, sin webhook. Precaución: el texto no debe incluir datos clínicos (RN-PR-06).

### Descartado
- Sesiones no oficiales por QR (modelo de DentalCore): riesgo de bloqueo del número y fuera de los términos de Meta.

## Mercado Pago

### Situación del mercado
- Seña con MP **comprobada** en agendas multirrubro argentinas: Turnito (incluso plan gratis, comisión 5%; 0% en Pro) [C], SimpleTurno Pro [C], Neocita plan pago [C]; Ulifeon [AC] (el paciente paga 2,2% + IVA); Naclix [AC].
- En los sistemas clínicos: **no evidenciada** en DentalCore (MP figura como "incluido" en /pricing sin documentación funcional) ni en Bilog. **Vacío "seña + clínica en un mismo producto"** (C.3.4).

### Diseño v1: Checkout Pro, cuenta única del odontólogo
1. Crear preferencia con ítem "Seña turno <fecha>", monto configurado, `external_reference = turno_id`, URLs de retorno y `notification_url`.
2. Redirigir al paciente al `init_point`.
3. Acreditar **solo** por webhook + consulta del pago (no por la URL de retorno).
4. Idempotencia por `payment_id` (RN-SP-08).
5. Devolución (RN-SP-05) en el prototipo: se **registra** el estado `devuelta`; **Suposición:** la devolución real por API queda para cuando haya revisión legal.

### Fase 2: split 1:N
- Varios profesionales cobrando en un mismo consultorio (marketplace / split). Documentado, no implementado.

### Restricciones
- Solo **credenciales de prueba** (`TEST-...`) y usuarios de prueba de Mercado Pago.
- **La regla de retención de seña está sujeta a revisión legal (P-01)** y no se aplica con dinero real.
- Comisiones de Mercado Pago para el odontólogo: **no relevadas** en las fuentes.

## Integraciones fuera de la v1

| Integración | Etapa | Referencia de mercado |
|---|---|---|
| ARCA / facturación electrónica | v2 | Naclix (AFIP con CAE [AC]), DentalCore (listado [C] sin documentación), ClinIA, Sigo [AC] |
| Obras sociales (códigos y valores manuales) | v1.1 | Bilog, Órbita, OdontoGRAMA [AC] |
| PUCO / RENAPER / receta electrónica | Posterior | ClinIA [AC] |
| Google Calendar | Posterior | Naclix, Ulifeon, SimpleTurno, Doctocliq [AC] |
| Radiología, firma digital | Posterior | — |
| API pública | Posterior | Open Dental (API REST documentada [C]) |
