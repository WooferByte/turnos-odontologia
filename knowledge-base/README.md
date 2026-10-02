# Turnos Odontológicos AR — Base de Conocimiento

Base de conocimiento generada (modo silencioso, `kb-creator`) a partir de `docs/discovery/informe-discovery.md`, `discovery/discovery.md`, la sección `discovery` de `.active-orchestrator-state.json` y la consigna del trabajo (Etapas 3 y 6). Fecha: 2026-10-01.

## Índice de Archivos

| Archivo | Contenido |
|---|---|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, segmento, objetivos por actor, casos de uso CU-01..08, alcance v1, diferenciadores, fuera de alcance |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack, arquitectura general, integraciones, resumen de API REST |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Actores, matriz RBAC, rutas públicas |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Dominios, ERD, entidades (Sillón como recurso), máquina de estados del turno, seed ficticio |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | RN-AG (prestaciones, sillones, solapamientos con casos borde), RN-TD/WA/LE, RN-SP, RN-FC, RN-PR, RN-AU, RN-GL |
| [06_funcionalidades.md](06_funcionalidades.md) | Épicas e historias US-NNN con criterios de aceptación |
| [07_flujos_principales.md](07_flujos_principales.md) | Crear turno sin solapamientos, reserva, WhatsApp, seña, cancelar/reprogramar, lista de espera, ficha, auth |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones, directorios, seguridad, variables de entorno, estrategia de tests |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | DD-00..11, supuestos SU-01..07, riesgos R-01..10 |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Inconsistencias, puntos "No evidenciado", preguntas priorizadas (legales, Meta, obras sociales, AAIP) |
| [11_integraciones_whatsapp_y_mercadopago.md](11_integraciones_whatsapp_y_mercadopago.md) | Cloud API vs `wa.me`, Checkout Pro, restricciones de prueba |
| [12_contexto_de_mercado.md](12_contexto_de_mercado.md) | Competidores, ranking, vacíos del mercado y cómo los toma la KB |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md), [12](12_contexto_de_mercado.md)
2. Entender los datos → [04](04_modelo_de_datos.md)
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [10](10_preguntas_abiertas.md)

**Change de la consigna (Etapa 6):** "Crear un turno evitando solapamientos por profesional y por sillón/box" → US-010, Flujo 1, RN-AG-05/08/09/10, DD-02/03/04. Tests sin PostgreSQL ni Redis (SQLite en memoria, DD-03; el README del change debe decirlo explícitamente). Alcance (P-10): solo solapamientos por profesional y por sillón con estados activos; sin validar horario de atención ni bloqueos. Sobreturnos prohibidos en la v1 (P-11, Fase 2).

## Resumen Ejecutivo

Sistema de turnos y agenda para el **odontólogo independiente argentino** (1 profesional, 1 sillón modelado como recurso). Su núcleo es una agenda confiable (duraciones por prestación, horario recurrente, bloqueos, anti-solapamiento por profesional y por sillón) con reserva 24/7 por link, confirmación por WhatsApp, seña con Mercado Pago, lista de espera, trazabilidad de cambios y ficha clínica mínima. **Datos de pacientes siempre ficticios**; las reglas de seña están sujetas a revisión legal.
