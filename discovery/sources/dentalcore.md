# DentalCore

- **URL**: https://dentalcore.app/
- **Fecha de investigación**: 2026-10-01

## Problema que resuelve

Software dental SaaS que integra historia clínica, agenda, facturación con obras sociales, marketing e IA (motores CDSS) en un plan único.

## Usuarios objetivo

Odontólogos y clínicas de Argentina y Latinoamérica (menciona preparación para varias sucursales).

## Features detectadas

- Agenda visual multi-profesional con drag and drop; portal del paciente con reserva 24/7
- WhatsApp por QR con 9 automatizaciones: confirmación SI/NO, post-operatorios, cumpleaños, recalls; el bot ofrece adelantar turnos en cancelaciones
- Odontograma con dictado por voz, periodontograma con evolución, presupuestos versionados con cobertura
- Factura electrónica ARCA (CAE y QR), 20+ convenios de obras sociales precargados, Mercado Pago con QR
- HL7 FHIR (exportación), derivaciones, teleodontología

## Pricing

Plan único: USD 50/mes con 2 usuarios, USD 10 por usuario adicional, pacientes ilimitados, 50 GB incluidos. Prueba de 14 días con garantía de reembolso (según el sitio).

## Posicionamiento

"Todo incluido", sin versiones recortadas, hecho en La Plata con foco en normativa argentina.

## Diferenciadores

Seguridad documentada con detalle, precio único publicado, automatización WhatsApp con confirmación.

## Notas del investigador

Cifras de clientes no publicadas (se menciona acceso directo al fundador). Seguridad es afirmación comercial; sin auditoría/certificado verificable.

---

## Relevamiento detallado

Fuente: https://dentalcore.app/ (2026-10-01); páginas /pricing, /faq, /privacy, /terms, /refunds enlazadas (no leídas individualmente).

- **Empresa/país**: DentalCore, Argentina (La Plata), fundador Alfredo Di Tullio [AC]. Segmento: consultorio a clínica [AC].
- **Modalidad**: SaaS nube [AC].
- **Agenda**: multi-profesional, drag and drop [AC]. Sillones, duración, bloqueos, sobreturnos, anti-solapamiento: NE.
- **Turnos digitales**: portal paciente 24/7 [AC]; WhatsApp bot; reprogramación asistida de cancelaciones [AC]; lista de espera formal: NE.
- **Automatización**: recordatorios con confirmación SI/NO, post-op, cumpleaños, recalls [AC].
- **Clínica**: odontograma con voz, periodontograma, órdenes de radiografía y almacenamiento, presupuestos versionados [AC].
- **Administración**: ARCA, obras sociales (PAMI, OSDE, Swiss Medical, IOMA, Galeno, Sancor), Mercado Pago [AC]. Liquidaciones: NE.
- **Integraciones**: WhatsApp (QR, no API oficial especificada), HL7 FHIR, Mercado Pago, ARCA [AC].
- **Operación**: roles por persona, auditoría de accesos a historias clínicas, "preparado para varias sucursales" [AC]; exportación FHIR [AC].
- **Seguridad**: TLS, base aislada por clínica, scrypt, AES-256-GCM, "cumple controles ISO/IEC 27001" (no certificación) [AC]. Ley 25.326: NE en lo leído.
- **Comercial**: USD 50/mes, trial 14 días, reembolso [AC, precios publicados].
- **Adopción**: NE.


---

## Segunda pasada (2026-10-01)

Etiquetas: [C] Comprobado (precios/privacidad/términos), [AC] Afirmación comercial, NE No evidenciado. WebFetch devolvió resúmenes (no texto literal), salvo citas entrecomilladas. /faq: respuestas en acordeones colapsados, no legibles (limitación).

**Confirmado**
- Precio: "USD 50 por mes con 2 usuarios incluidos", "USD 10 por cada persona que sumes"; pago con tarjeta, MercadoPago, PayPal o transferencia [C, https://dentalcore.app/pricing]. Moneda: USD.
- Prueba: NO hay prueba gratis; hay "14 días de garantía, te devolvemos el dinero" [C, /pricing]. Corrige la nota previa ("prueba de 14 días"): es garantía de reembolso, no trial.
- WhatsApp por QR, NO API oficial: "Escaneás un QR una vez y se conecta tu sesión de WhatsApp" y "No usamos WhatsApp Business API — funciona con tu número habitual" [AC, cita literal de https://dentalcore.app/]. Resuelve lo que la nota previa dejaba como "no especificada". Riesgo: sesión no oficial, sujeta a las políticas de Meta; los términos (/terms) no mencionan riesgos de WhatsApp [C].
- Confirmación bidireccional y relleno automático de huecos cancelados (el bot ofrece adelantar a otro paciente) [AC, home].
- Motor de reglas clínicas: "17 motores CDSS" basados en reglas (no IA generativa), 62 entidades de patología oral, protocolos IADT/Malamed, interacciones medicamentosas [AC, home]. Sin validación clínica externa.
- FHIR: "exportación HL7 FHIR" listada como inclusión del plan [C en /pricing como inclusión; interoperabilidad real no verificada].
- ARCA y MercadoPago listados como incluidos [C en /pricing como inclusión; sin documentación funcional]. Seña por MercadoPago: NO evidenciado como tal (el blog de mayo 2026 menciona "QR desde ficha" para cobro, https://dentalcore.app/blog/benchmark-software-dental-latinoamerica-2026).
- Privacidad [C, https://dentalcore.app/privacy]: cita Ley 25.326 y AAIP (corrige el "NE" anterior); NO cita Ley 26.529; TLS, cifrado en reposo, RBAC, backups automáticos, monitoreo de incidentes; infraestructura Supabase/AWS (datos fuera de Argentina presumiblemente; ubicación no especificada). Exportación en formato estándar a pedido; tras la baja, 30 días para exportar y luego borrado posible. Términos [C, /terms]: DentalCore es "encargado" y el odontólogo responsable; sin SLA ("mejores esfuerzos"); responsabilidad tope = pagos de 90 días; jurisdicción Buenos Aires.
- "Waiting room" en /pricing es sala de espera, no lista de espera de turnos [AC]. Sobreturnos, bloqueos, anti-solapamiento, recurrentes, cancelación por el paciente en el portal: NE.
- Adopción: sin cifras. El blog de dentalcore.app es contenido propio y autopromocional (comparativas), no evidencia independiente. Autor/fundador: Alfredo Di Tullio (MN 40.973) [AC].
- App móvil: NE.
