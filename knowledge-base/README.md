# Turnos Odontológicos AR — Base de Conocimiento

Base de conocimiento generada (modo silencioso, `kb-creator`) a partir de `docs/discovery/informe-discovery.md`, `discovery/discovery.md`, la sección `discovery` de `.active-orchestrator-state.json` y la consigna del trabajo (Etapas 3 y 6). Fecha: 2026-10-01.

## Índice de Archivos

| Archivo | Contenido |
|---|---|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, segmento, objetivos por actor, casos de uso CU-01..08, alcance v1, diferenciadores, fuera de alcance |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack, arquitectura general, integraciones, resumen de API REST |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Actores, matriz RBAC, rutas públicas |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Dominios, ERD, convenciones, todas las entidades con tabla de campos (tipo, nullability, restricciones, FK, índices, enums), máquina de estados del turno, subconjunto del primer change, seed ficticio, lista «A confirmar por el autor» |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | RN-AG (prestaciones, sillones, solapamientos con casos borde), RN-TD/WA/LE, RN-SP, RN-FC, RN-PR, RN-AU, RN-GL |
| [06_funcionalidades.md](06_funcionalidades.md) | Épicas e historias US-NNN con criterios de aceptación, `Orden` de implementación (1 a 9) y `Depende de`; escenarios E1..E12 de US-010; Épica 10 de usuarios y acceso; US-080 marcada como extensión fuera del MVP |
| [07_flujos_principales.md](07_flujos_principales.md) | Crear turno sin solapamientos, reserva, WhatsApp, seña, cancelar/reprogramar, lista de espera, ficha, auth |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones, directorios, regla de capas, contrato del primer change, seguridad, variables de entorno, estrategia y fixtures de tests, reloj/UTC, versiones, Definition of Done |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | DD-00..15, supuestos SU-01..09, riesgos R-01..10 |
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

**Change de la consigna (Etapa 6):** "Crear un turno evitando solapamientos por profesional y por sillón/box" → US-010, Flujo 1, RN-AG-05/08/09/10, RN-GL-04, DD-02/03/04/12/13/14. Escenarios con ID estable: **E1..E7 y E12** entran en el spec (feliz, profesional, sillón, doble conflicto, borde contiguo, estado no activo, borde de un minuto, recurso no encontrado); E8 a E11 quedan fuera (tabla en US-010). **El change expone `POST /turnos` (FastAPI) para mostrarlo en Swagger, sin autenticación (límite conocido, DD-14) y sin interfaz gráfica.** Tests sin PostgreSQL ni Redis: SQLAlchemy 2.x **síncrono** y SQLite en memoria con `StaticPool`, sin mocks de sesión ni de repositorio (DD-03, DD-12; el README del change debe decirlo explícitamente). Alcance (P-10): solo solapamientos por profesional y por sillón con estados activos; sin validar horario de atención ni bloqueos; **sin historial `EventoTurno`** (change siguiente, decisión del autor 2026-10-03). Contrato (firmas, error de dominio, RFC 7807, doble conflicto) y Definition of Done en `08_arquitectura_propuesta.md`; subconjunto del modelo en `04_modelo_de_datos.md`. Sobreturnos prohibidos en la v1 (P-11, Fase 2).

**Alcance del proyecto (decisión del autor 2026-10-03):** el autor implementará el **proyecto completo antes de fin de año**, change por change; el change de la consigna es el primero. Decisiones recientes: WhatsApp en la v1 por enlace `wa.me` (Cloud API en Fase 2, DD-06); plazos de seña (30 min) y de oferta de lista de espera (2 h); Épica 10 de usuarios y acceso con JWT; preguntas legales cerradas como fuera del alcance académico (requieren revisión legal antes de uso real); obras sociales y precio diferidos; Alembic desde el change de infraestructura con PostgreSQL (DD-15). Preguntas realmente abiertas: ver `10_preguntas_abiertas.md` (P-16, P-17 y P-19).

## Resumen Ejecutivo

Sistema de turnos y agenda para el **odontólogo independiente argentino** (1 profesional, 1 sillón modelado como recurso). Su núcleo es una agenda confiable (duraciones por prestación, horario recurrente, bloqueos, anti-solapamiento por profesional y por sillón) con reserva 24/7 por link, confirmación por WhatsApp (enlace `wa.me`), seña con Mercado Pago, lista de espera, trazabilidad de cambios y ficha clínica mínima. **Datos de pacientes siempre ficticios**; las reglas de seña están sujetas a revisión legal.
