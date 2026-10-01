# Neocita

- **URL**: https://www.neocita.com/
- **Fecha de investigación**: 2026-10-01

## Problema que resuelve

Gestión de turnos online (web + app Android) con ficha de paciente y caja, para profesionales y comercios (médicos, odontólogos, psicólogos, canchas, estética, etc.).

## Usuarios objetivo

Multirrubro; odontología aparece solo como uno de varios rubros (sin foco odontológico dedicado).

## Features detectadas

- Sitio web de solicitud de turnos, QR, app Android y panel web
- Bot de turnos por WhatsApp (plan pago)
- Recordatorios WhatsApp (manuales gratis; automáticos con costo extra)
- Seña/cobro con Mercado Pago (plan pago)
- Caja diaria; ficha de paciente con "historia clínica, estudios e imágenes" [Afirmación comercial]

## Pricing

Gratis: 1 agenda, hasta 30 clientes, hasta 50 turnos/mes. Pago: ARS 5.900/mes (500+ clientes, turnos ilimitados). Recordatorios WhatsApp automáticos: ARS 6.000+IVA (50) a 24.000+IVA (200) por mes.

## Posicionamiento

"La forma más inteligente de gestionar tus agendas": agenda genérica con ficha simple, económica.

## Diferenciadores

Bot WhatsApp, caja integrada, app Android propia.

## Notas del investigador

Empresa en La Plata (Calle 18 225, según resultado de búsqueda; no verificado en la página). Solo Android evidenciado.

---

## Relevamiento detallado

Fuentes (todas leídas 2026-10-01 vía WebFetch, que RESUME y no da texto literal): https://www.neocita.com/ ; /precios.php ; /recordatorios-turnos-whatsapp.php ; /bot-turnos-whatsapp.php ; /contacto.php ; /privacidad.php ; https://play.google.com/store/apps/datasafety?id=com.neocita.neocita&hl=es

- **Plan gratis** [Comprobado, precios.php]: 1 agenda, 30 pacientes, 50 turnos/mes; excluye seña MP, factura digital, bot WhatsApp, administradores extra, marca propia. Recordatorios solo manuales.
- **Pago/seña MP** [Comprobado, precios.php]: solo en plan pago ARS 5.900/mes. Comisión propia: No evidenciado.
- **Recordatorios WhatsApp** [Comprobado, recordatorios-turnos-whatsapp.php]: los manuales abren un link y el mensaje "sale desde tu whatsapp" (enlace, no API). Automáticos con "bot de notificaciones", ARS 6.000/12.000/18.000/24.000+IVA por 50/100/150/200 mensajes/mes. API oficial: No evidenciado.
- **Bot WhatsApp** [Comprobado que existe; mecanismo No evidenciado]: usa "tu número de whatsapp vinculado con neocita".
- **Reserva online/QR** [Comprobado, precios.php].
- **Ficha/odontograma/presupuestos**: ficha con historia clínica, estudios e imágenes [Afirmación comercial, home]. Odontograma/presupuestos: No evidenciado. Es genérico, NO odontológico.
- **Caja** [Afirmación comercial, home]. Facturación digital en plan pago [Comprobado, precios].
- **Lista de espera, horarios recurrentes/bloqueos, cancelación por paciente, historial de cambios, exportación**: No evidenciado.
- **Privacidad** [Comprobado, privacidad.php]: no menciona Ley 25.326 ni AAIP; no trata datos de salud explícitamente; datos compartidos con proveedores y "advertising partners"; sin hosting declarado; sin exportación; baja por email (hasta 72 h hábiles, contacto.php).
- **Google Play data safety** [Comprobado]: recoge email e identificadores de dispositivo; "no se comparten datos con terceros"; cifrado en tránsito; permite pedir borrado (contradice parcialmente la política web).
- **Ficha Google Play** [Limitación]: la fetch de la ficha principal devolvió contenido truncado/vacío. "100K+ descargas" proviene solo de un snippet de búsqueda, NO verificado. Rating/reseñas: No evidenciado. Sin iOS evidenciado.
- **Soporte** [Comprobado, contacto.php]: email Gmail soporteneocita@gmail.com; sin SLA.
- **Adopción**: "cientos de personas" [Afirmación comercial].
- **Lectura crítica**: soporte con cuenta Gmail, política sin Ley 25.326, plan gratis muy chico: riesgo medio para datos clínicos.
