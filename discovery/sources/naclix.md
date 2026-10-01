# Naclix

- **URL**: https://naclix.com/ (app: https://app.naclix.com/ ; App Store AR: https://apps.apple.com/ar/app/naclix/id6756287334)
- **Fecha de investigación**: 2026-10-01
- **Verificación de producto**: URL oficial hallada por WebSearch; el sitio, el App Store y los términos coinciden en titular (Mariano Pedro Rebord Palazzo, CUIT 20-33644082-4, Argentina). Es el producto correcto: gestión de turnos/fichas/pagos con WhatsApp, AFIP y MercadoPago. OJO: es multi-rubro (médicos, psicólogos, nutricionistas, estética, veterinarias, odontología), NO un software exclusivamente dental.

## Problema que resuelve

Reducir ausencias (no-shows) y automatizar el consultorio: recordatorios y confirmación por WhatsApp, reserva online 24/7, ficha clínica, cobros y facturación.

## Usuarios objetivo

Profesionales de salud/bienestar de Latinoamérica (el sitio muestra 17 países); odontología es una especialidad más ("Odontograma, presupuestos con firma y trabajos a laboratorio").

## Features detectadas

- Reserva online 24/7 con disponibilidad en tiempo real; sync bidireccional con Google Calendar
- Recordatorios WhatsApp 24h/3h/1h con confirmación "confirmar" y respuestas automáticas por keywords; "canal oficial de WhatsApp, tu mismo número"
- Sobreturnos (marcados como tal, drag and drop); lista de espera con aviso automático al siguiente
- Ficha clínica con formularios personalizables; odontograma (solo web); historial de auditoría (plan Profesional)
- MercadoPago (señas/cobros), facturación electrónica AFIP con CAE y QR, copagos/obras sociales, planes de pago
- Multi-consultorio con números de WhatsApp separados (planes altos); app iOS (v1.10.0), login biométrico

## Pricing

ARS/mes: Gratuito (sin vencimiento, 30 días con funciones Pro), Inicio $9.800, Profesional $39.800, Negocio $89.000, A medida. Sin reembolsos por períodos parciales.

## Posicionamiento

"Reducí ausencias y automatizá tu consultorio"; precios transparentes; fundador individual.

## Notas del investigador

Proveedor unipersonal (riesgo de continuidad). Sin cifras de adopción. Base de datos en São Paulo (Fly.io), backups en EE. UU. (AWS): transferencia internacional de datos de salud.

---

## Relevamiento detallado

Etiquetas: [C] Comprobado (precios/términos/privacidad/ficha de app), [AC] Afirmación comercial, NE No evidenciado. Todas las fuentes consultadas 2026-10-01. Limitación: WebFetch devuelve resúmenes, no texto literal, salvo citas entrecomilladas.

- **Precios ARS** [C]: https://naclix.com/ (planes). Prueba: plan gratuito + 30 días Pro [C]. /precios da 404 (los planes están en la home, #plans).
- **WhatsApp** [AC]: "Canal oficial de WhatsApp. Tu mismo número"; Meta figura como subprocesador en la política de privacidad [C] (https://naclix.com/privacy). Si es Cloud API de Meta o conexión por QR: no se dice expresamente; "canal oficial" apunta a API oficial pero no está documentado. Confirmación bidireccional ("confirmar") [AC]. Términos: sin cláusulas de WhatsApp [C, https://naclix.com/terms].
- **Reserva online / lista de espera / sobreturnos** [AC, home]. Bloqueos, anti-solapamiento, recurrentes: NE. Cancelación/reprogramación por el paciente: NE (la "cancelación" citada es del profesional).
- **Auditoría/trazabilidad**: "historial de auditoría" en plan Profesional [AC, home]; la privacidad dice "registros de auditoría completos e historiales de versiones" [C].
- **Odontograma/presupuestos**: [AC] "Odontograma, presupuestos con firma y trabajos a laboratorio"; numeración FDI/Universal [AC, resultado de búsqueda]. Periodontograma: NE.
- **MercadoPago** (señas/cobros) [AC]; **AFIP** con CAE y QR [AC]; documentación pública de ARCA: NE; usa la sigla AFIP (no ARCA).
- **Obras sociales**: "copagos con integración de planes de salud" [AC]; liquidaciones a obras sociales, convenios: NE.
- **Exportación** [C]: JSON/CSV desde plan Inicio (términos 7.1 y privacidad).
- **Seguridad/privacidad** [C]: cita Ley 25.326 y 26.529; HTTPS y cifrado en reposo; aislamiento multi-tenant; RBAC; backups diarios 1 semana, semanales 2 meses, mensuales 13 meses; retención clínica 10 años según la ley; subprocesadores Fly.io, AWS, Vercel, Meta, Google, MercadoPago, OpenAI, Sentry, PostHog. El profesional es responsable de los datos, Naclix es encargado (términos 7.1). Responsabilidad limitada a 12 meses de pagos (9.2). Jurisdicción CABA.
- **App móvil**: App iOS gratuita, v1.10.0, calificación 5.0 con 3 reseñas, etiquetas de privacidad: datos de salud, contacto, fotos, identificadores [C, App Store AR]. Google Play: no verificado.
- **Adopción**: sin cifras publicadas; "17 países" es una afirmación basada en banderas del pie [AC débil].
- **Comparativa propia** (https://naclix.com/comparar/dentalink, verificada por Naclix el 2026-09-25) [AC de competidor interesado]: afirma que Dentalink no publica precios, cobra WhatsApp como adicional y que su facturación electrónica no cubre Argentina.
