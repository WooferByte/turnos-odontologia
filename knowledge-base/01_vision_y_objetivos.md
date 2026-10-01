# Visión y Objetivos

> Fuentes: `docs/discovery/informe-discovery.md` (secciones C y D), `discovery/discovery.md` (puntos 1 a 6) y la sección `discovery` de `.active-orchestrator-state.json`. Fecha de las fuentes: 2026-10-01.

## Propósito del sistema

**Una agenda confiable para el odontólogo independiente argentino**: turnos sin solapamientos, reserva 24/7 por link, confirmación por WhatsApp, seña con Mercado Pago y una ficha clínica mínima, con un historial de cada cambio de turno.

Los odontólogos independientes y los consultorios chicos de Argentina gestionan turnos y fichas con papel, Excel y WhatsApp. Eso genera ausentismo evitable y datos sin trazabilidad, porque las soluciones existentes son caras o no se integran con WhatsApp ni con el cobro local (problema aprobado por el autor en el Discovery).

Evidencia de contexto (indiciaria, no probabilística; ver `12_contexto_de_mercado.md`):
- 85% de los odontólogos encuestados atiende en consultorio propio y 54% lo comparte (Dental Tribune, n=313, contexto de pandemia).
- 68% lleva la historia clínica en papel (RePEc, n=100, CABA y GBA, 2024).
- Se descartaron por falta de fuente las cifras de "3% de adopción tecnológica" y "60-70% de ausentismo". **No se usa ninguna cifra de ausentismo como hecho de diseño.**

## Contexto académico

Trabajo integrador individual de Metodología I (Tecnicatura Universitaria en Programación). La KB documenta el **producto completo y el MVP recomendado**, pero la consigna solo exige implementar **un único change** del MVP como API o módulo sin interfaz gráfica, con tests automatizados por escenario (Etapa 6 de la consigna). El change recomendado por la consigna y alineado con esta KB es **"Crear un turno evitando solapamientos por profesional y por sillón/box"** (ver `05_reglas_de_negocio.md`, RN-AG-05 a RN-AG-09, y `07_flujos_principales.md`, Flujo 1).

## Segmento primario

**Odontólogo independiente: 1 profesional, 1 sillón.** El sillón se modela como **recurso** del dominio con valor 1 por defecto, y la regla de solapamiento se aplica por profesional y por sillón, para que el crecimiento a varios sillones (Fase 2) no requiera rediseñar la lógica.

En el independiente, quien usa el sistema todos los días es el propio odontólogo haciendo de recepcionista. La experiencia del paciente es secundaria en uso, pero es el principal diferenciador frente al papel.

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|---|---|---|
| Odontólogo | Atender: ver la agenda del día, abrir la ficha y registrar la evolución | Configurar prestaciones, horario y reglas; no tener turnos superpuestos |
| Recepcionista (o el propio odontólogo) | Agendar y confirmar: dar turnos, reprogramar, gestionar la lista de espera | Cobrar señas; enviar recordatorios; registrar pagos |
| Dueño del consultorio (en el independiente, el mismo odontólogo) | Controlar: ocupación, ausentismo, cobros pendientes | Ver el historial de cambios de turno |
| Paciente | Reservar y confirmar: sacar turno online 24/7 desde el celular | Pagar la seña, cancelar o reprogramar dentro de las reglas, anotarse en lista de espera, conocer y aceptar el tratamiento de sus datos |

## Casos de uso (CU)

| Código | Caso de uso | Actor principal | Versión |
|---|---|---|---|
| CU-01 | Reserva online 24/7 desde el celular (objetivo: menos de 30 segundos) | Paciente | v1 |
| CU-02 | Recordatorio 24 h antes y confirmación por WhatsApp | Sistema / Odontólogo | v1 |
| CU-03 | Ficha clínica mínima (datos, anamnesis, evolución en texto) | Odontólogo | v1 |
| CU-04 | Seña con Mercado Pago al reservar (la cobra la cuenta del odontólogo) | Paciente | v1 |
| CU-05 | Cancelar o reprogramar el turno con anticipación | Paciente | v1 |
| CU-06 | Lista de espera: ofrecer un hueco liberado a pacientes en espera | Odontólogo / Sistema | v1 |
| CU-07 | Consentimiento y privacidad de datos de salud | Paciente | v1 |
| CU-08 | Agenda multi-profesional y multi-sillón sin solapamientos | Titular de consultorio compartido | Fase 2 (el modelo de datos ya lo soporta) |

## Alcance v1 (MVP imprescindible, informe D.3)

1. Agenda con **duraciones variables por prestación** (tabla de prestaciones: nombre, duración por defecto, color).
2. **Horario recurrente configurable** (días y franjas de atención).
3. **Bloqueos puntuales** (vacaciones, feriados, ausencias).
4. **Prevención de solapamientos por profesional y por sillón.**
5. **Reserva 24/7 por link**, con flujo definido cuando no hay horarios (ofrecer la lista de espera).
6. **Recordatorio y confirmación por WhatsApp**: WhatsApp Cloud API en modo prueba (preferida) o enlace `wa.me` semiautomático (alternativa).
7. **Cancelación y reprogramación por el paciente** dentro de las reglas configuradas.
8. **Seña con Mercado Pago** (Checkout Pro, cuenta única del odontólogo).
9. **Trazabilidad de cambios de turno** (quién, cuándo, qué cambió).
10. **Lista de espera.**
11. **Ficha clínica mínima**: datos del paciente, anamnesis y evolución en texto.
12. **Presupuestos simples** y **registro de pago simple** (sí o no, monto, medio).

### Diferenciadores (informe D.3)

- Lista de espera que **ofrece los huecos liberados por WhatsApp** (semiautomática). En el mercado local solo hay afirmaciones comerciales sin flujo documentado (Naclix, DentalCore).
- **Horario recurrente + trazabilidad** de cada cambio de agenda: no está evidenciado en conjunto en ningún sistema relevado.
- **Precio publicado en ARS**, frente a sistemas clínicos que cotizan a pedido (Bilog, ClinIA, Órbita, Dentalink) o cobran en USD (DentalCore).
- **Confianza**: política que cite las Leyes 25.326 y 26.529 y exportación de datos documentada (hoy solo Naclix lo hace de forma comprobada).

## Fuera de alcance

| Versión | Funcionalidad |
|---|---|
| v1.1 | Odontograma completo |
| v1.1 | Configuración manual de códigos y valores de obras sociales |
| v2 | Imágenes y radiografías |
| v2 | ARCA y facturación electrónica |
| v2 | Caja completa con arqueo |
| Fase 2 | Split de pagos 1:N en Mercado Pago (varios profesionales cobrando) |
| Posterior | WhatsApp por API oficial **en producción** (verificación de empresa, plantillas aprobadas, costo por conversación) |
| Posterior | Sincronización con Google Calendar |
| Posterior | Interfaz multi-profesional y multi-sillón |
| Posterior | API pública |
| Nunca en el prototipo | Datos reales de pacientes; cuentas reales en Meta o Mercado Pago creadas con datos reales; cobro real de señas |

## Métricas de éxito

**Suposición:** ninguna fuente fija metas numéricas de producto. Se proponen métricas observables, sin valores objetivo, hasta tener datos propios:

- Cero turnos superpuestos por profesional o por sillón (verificable por tests y por consulta a la base).
- Tiempo de reserva del paciente por link (objetivo declarado en CU-01: menos de 30 segundos).
- Proporción de turnos confirmados por WhatsApp sobre turnos con recordatorio enviado.
- Proporción de huecos liberados que se vuelven a ocupar vía lista de espera.
- Ausentismo (turnos `ausente` sobre turnos atendidos + ausentes). **El impacto del recordatorio sobre el ausentismo no está probado** (riesgo en `09_decisiones_y_supuestos.md`).

Para el trabajo académico, el criterio de éxito verificable es: el change elegido implementado con tests automatizados que cubren cada escenario del spec (feliz, error de negocio y borde), ejecutables con solo seguir el README.
