# Contexto de Mercado y Competencia

> Resumen del informe de Discovery (`docs/discovery/informe-discovery.md`, 2026-10-01) para que la KB no describa un producto genérico. Marcas: **[C]** comprobado (documentación, ayuda, precios, privacidad, ficha oficial) · **[AC]** afirmación comercial · **No evidenciado** · **[3ro]** tercero. Detalle por sistema en `discovery/sources/*.md`.

## Alcance del relevamiento

31 sistemas: 13 argentinos (9 con módulo odontológico, 4 agendas multirrubro), 9 latinoamericanos/hispanohablantes y 9 internacionales de referencia. **La evidencia es mayormente comercial**: solo Open Dental tiene confianza alta.

## Ranking preliminar (matriz B, top argentinos)

| Rank | Sistema | Total | Confianza | Lectura |
|---|---|---|---|---|
| 1 | Naclix | 3,75 | Medio | Multirrubro de salud; precio en ARS con plan gratis [C]; lista de espera y sobreturnos [AC]; auditoría, exportación JSON/CSV y cita de Leyes 25.326 y 26.529 [C]; proveedor unipersonal; datos en São Paulo y EE. UU. [C] |
| 2 | DentalCore | 3,65 | Medio | USD 50/mes [C]; garantía de reembolso, no prueba gratis [C]; WhatsApp por QR, no API oficial; agenda casi toda No evidenciada |
| 3 | Bilog | 3,15 | Medio | Freemium; reserva por link con DNI + email [C]; sobreturnos [C]; recordatorios manuales/semiautomáticos [C] |
| 3 | ClinIA | 3,15 | Bajo | Agenda por sillón, PUCO, RENAPER, receta [AC] |
| 5 | Órbita | 3,00 | Bajo | "No permite dos pacientes en el mismo sillón" [AC]; IA sobre WhatsApp |

Diferencias < 0,2 puntos no son concluyentes. **El ranking mide evidencia pública, no calidad.**

## Paridad mínima (C.1)
Agenda multiprofesional (a menudo por sillón), recordatorios por WhatsApp o email, reserva online por link, historia clínica con odontograma y presupuestos, seña con Mercado Pago en agendas argentinas, plan gratuito en el segmento chico (no es diferencial).

## Vacíos del mercado argentino (C.3) → cómo los toma esta KB

| Vacío | Respuesta en la KB |
|---|---|
| WhatsApp sin API oficial documentada | DD-06: Cloud API en modo prueba + `wa.me` (a la par del mercado) |
| Lista de espera existe [AC] pero sin flujo documentado | Flujo 6 y RN-LE con estados, prioridad y vencimiento |
| Reglas finas de agenda: horario recurrente con excepciones, anti-solapamiento solo [AC], reprogramación por el paciente solo [C] en Dentally, trazabilidad solo en Naclix | RN-AG-01 a RN-AG-11, RN-TD-03/04 |
| Seña + clínica en un mismo producto | RN-SP + ficha mínima (RN-FC) |
| Cumplimiento normativo explícito (solo Naclix cita la 26.529) | RN-PR, consentimiento (CU-07) |
| Transparencia de precios en sistemas clínicos | Diferenciador: precio publicado en ARS |
| Referentes regionales sin adaptación local (Dentalink y Doctocliq no facturan en Argentina [C]) | Foco local: MP, WhatsApp, ARS |

## Competidores prioritarios para demo (D.1)
1. **Naclix** — flujo real de lista de espera, mecanismo de WhatsApp, anti-solapamiento, horarios recurrentes, cancelación por el paciente.
2. **DentalCore** — riesgo de la sesión por QR, si existe seña MP, sobreturnos/bloqueos/solapamientos.
3. **Bilog** — recordatorio manual vs. masivo, reglas de cancelación, reprogramación.
4. **Turnito** — sustituto barato del independiente con seña MP comprobada; cancelación/reprogramación [AC].
5. **Dentalink** — referente regional con la agenda más comprobada (sobreturnos, sillones, reprogramación masiva).
Alternativas: ClinIA, SimpleTurno, Neocita.

## Referencias de experiencia de usuario (D.2)
- **Open Dental** (Web Sched + ASAP List) [C] → modelo de la lista de espera.
- **Dentally** (portal 24/7 con depósito, cambio/cancelación por link, listas con estados) [C] → modelo de autogestión con seña.
- **Clinicorp** (link público + estados en tiempo real) → referente latinoamericano del canal.

## Limitaciones a tener presentes
Resúmenes automáticos de `WebFetch`; mayormente páginas comerciales; sin demos; comparativas publicadas por competidores (sesgadas); verificación personal de fuentes **pendiente** (ver P-16).
