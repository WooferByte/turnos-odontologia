# Discovery — Sistema de gestión de turnos y agenda para consultorios odontológicos (Argentina)

**Fecha**: 2026-10-01
**Contexto**: Trabajo integrador de Metodología I (Tecnicatura Universitaria en Programación). Trabajo individual. Entrega aproximada a fin de año, sin fecha definida.
**Fuentes investigadas**: 31 sistemas (ver `discovery/sources/`) y el informe completo en `docs/discovery/informe-discovery.md`.

> **Nota de evidencia.** Las notas de competidores se obtuvieron con `WebFetch`, que devuelve resúmenes automáticos y no el texto literal, y se apoyan sobre todo en páginas comerciales. Casi todo es afirmación comercial. La puntuación del informe es preliminar y está sujeta a demo y a la verificación personal de fuentes.

## 1. Problema que resuelve

Los odontólogos independientes y los consultorios chicos de Argentina gestionan turnos y fichas con papel, Excel y WhatsApp, lo que genera ausentismo evitable y datos sin trazabilidad, porque las soluciones existentes son caras o no se integran con WhatsApp ni con el cobro local.

**Evidencia de contexto (indiciaria, no probabilística):**
- 85% de los odontólogos encuestados tiene consultorio propio y 54% lo comparte (Dental Tribune Latin America, encuesta durante la covid-19, n=313, convocatoria abierta).
- 68% usa historia clínica en papel y 66% no usa software de diagnóstico (RePEc, n=100, CABA y GBA, relevamiento enero-agosto 2024).
- 53.011 odontólogos según el Censo Nacional Económico (INDEC), citado por la UNCuyo.
- **Descartado:** la cifra de "3% de adopción tecnológica" y la de ausentismo del 60-70% no tienen fuente verificada.

## 2. Usuarios / roles

Segmento primario: **odontólogo independiente** (1 profesional, 1 sillón).

- **Odontólogo** — atender: ve la agenda del día, abre la ficha y registra la evolución.
- **Recepcionista o el propio odontólogo** — agendar y confirmar: da turnos, reprograma, gestiona la lista de espera y cobra señas.
- **Dueño del consultorio** — controlar: mira ocupación, ausentismo y cobros pendientes (en el independiente es el mismo odontólogo).
- **Paciente** — reservar y confirmar: saca turno online 24/7, recibe el recordatorio y confirma o cancela.

Decisión de producto: en el independiente, quien usa el sistema todos los días es el propio odontólogo haciendo de recepcionista. La experiencia del paciente es secundaria en uso, pero es el principal diferenciador frente al papel.

## 3. Casos de uso

1. **Reserva online.** Como paciente, quiero reservar un turno disponible desde el celular en menos de 30 segundos para no depender del horario de atención.
2. **Recordatorio y confirmación por WhatsApp.** Como odontólogo, quiero que el sistema recuerde el turno 24 horas antes y registre quién confirmó para ofrecer los huecos liberados.
3. **Ficha clínica mínima.** Como odontólogo, quiero abrir la ficha del paciente en la consulta y registrar anamnesis y evolución para no depender de la carpeta de papel. El odontograma completo pasa a v1.1.
4. **Seña con Mercado Pago.** Como paciente, quiero pagar la seña al reservar para asegurar mi turno. La cobra la cuenta del odontólogo.
5. **Cancelar o reprogramar.** Como paciente, quiero cancelar o reprogramar mi turno con anticipación para liberar el horario.
6. **Lista de espera.** Como odontólogo, quiero ofrecer un hueco liberado a los pacientes en espera para convertir cancelaciones en turnos.
7. **Consentimiento y privacidad.** Como paciente, quiero saber qué datos de salud se guardan y aceptar su tratamiento.
8. **Agenda multi-profesional y multi-sillón** — *Fase 2.* Como titular de un consultorio compartido, quiero ver en una vista a varios profesionales y sillones sin solapamientos.

**Regla de modelado:** el sillón es un recurso del dominio con valor 1 por defecto. La regla de solapamiento se define por profesional y por sillón, aunque el MVP use uno solo. Esto permite que el change de la consigna ("crear un turno sin solapamientos") encaje sin ampliar el MVP.

## 4. Competidores / soluciones existentes

Se relevaron **31 sistemas**: 13 con origen o presencia en Argentina, 9 latinoamericanos y 9 internacionales (agrupación del informe). Detalle en `docs/discovery/informe-discovery.md`.

| Ranking preliminar | Puntaje | Confianza | Nota |
|---|---|---|---|
| Naclix | 3,75 | Medio | Multi-rubro, no solo odontológico; proveedor unipersonal; datos alojados en São Paulo y EE. UU. |
| DentalCore | 3,65 | Medio | WhatsApp por QR, no API oficial; casi todo es afirmación comercial. |
| Bilog | 3,15 | — | Recordatorios de WhatsApp manuales o semiautomáticos. |
| ClinIA | 3,15 | baja | Agenda por sillón, PUCO y receta electrónica, solo como afirmación comercial. |
| Órbita | 3,00 | baja | Capa de IA sobre WhatsApp; se integra con Dentalink y Bilog. |

**Demo prioritaria:** Naclix, DentalCore, Bilog, Turnito (referencia barata para el independiente) y Dentalink (referente regional). Alternativas: ClinIA, SimpleTurno o Neocita.

**Hallazgos de la segunda pasada que corrigen la primera:**
- DentalCore: la "prueba de 14 días" es una garantía de reembolso.
- Dentalink: su facturación electrónica cubre solo Colombia y México según su ayuda; es referente regional, no local.
- Ulifeon: no integra WhatsApp ni Instagram, solo permite compartir el link.
- Turnito: es una agenda multirrubro, no odontológica; el plan gratis no incluye WhatsApp.
- Naclix: la lista de espera y los sobreturnos son **solo afirmación comercial**; lo comprobado es la auditoría, la exportación y los precios en ARS.
- Ningún competidor documenta el uso de la API oficial de WhatsApp.

## 5. Funcionalidades necesarias (v1)

- Agenda con duraciones variables por prestación, configurables por el odontólogo.
- Horario recurrente configurable y bloqueos puntuales.
- Prevención de solapamientos por profesional y por sillón.
- Reserva 24/7 por link, con flujo definido cuando no hay horarios disponibles.
- Recordatorio y confirmación por WhatsApp.
- Cancelación y reprogramación por el paciente.
- Seña con Mercado Pago (Checkout Pro, cuenta única del odontólogo).
- Trazabilidad de los cambios de turno (quién hizo qué y cuándo).
- Lista de espera.
- Ficha clínica mínima (datos, anamnesis, evolución en texto).
- Presupuestos simples y registro de pago (sí o no, monto, medio).

## 6. Funcionalidades opcionales

- **v1.1:** odontograma completo; configuración manual de códigos y valores de obras sociales.
- **v2:** imágenes y radiografías; ARCA y facturación electrónica; caja completa con arqueo.
- **Posteriores:** Google Calendar, interfaz multi-profesional y multi-sillón, API pública, split de pagos 1:N en Mercado Pago.

## 7. Reglas de negocio

Todas configurables por el odontólogo. Los valores son **defaults propuestos**, no estándares de mercado verificados.

- Antelación mínima para cancelar o reprogramar: 24 horas (configurable entre 24 y 48).
- Reserva hasta 60 días hacia adelante y antelación mínima de reserva configurable (propuesta: 2 horas).
- La duración de cada prestación, su nombre y su color en la agenda los define el odontólogo en una tabla de prestaciones.
- Un profesional no puede tener dos turnos superpuestos, ni un sillón dos turnos a la vez.
- El paciente nuevo reserva directo; la aprobación manual es opcional.
- Seña retenida si el paciente cancela fuera de plazo; devuelta al 100% si cancela el odontólogo. **Sujeta a revisión legal.**
- Todo cambio de turno queda registrado.

## 8. Integraciones

- **WhatsApp:** API oficial (WhatsApp Cloud API) en modo prueba si la configuración técnica es viable; enlace `wa.me` como alternativa. Meta crea un número de pruebas al empezar; el límite de 5 números verificados proviene de fuentes de terceros y está **a verificar**. En producción haría falta verificación de empresa, plantillas aprobadas y pago por conversación (precios sin verificar).
- **Mercado Pago:** Checkout Pro con **cuenta única del odontólogo** en la v1. El split 1:N queda documentado como Fase 2.
- **Fuera de la v1:** Google Calendar, ARCA, integración de obras sociales, radiología y firma digital.

## 9. Restricciones

- Trabajo individual; entrega aproximada a fin de año, sin fecha definida.
- La consigna evalúa **un solo change** implementado como API o módulo, sin interfaz gráfica, con tests por escenario.
- Datos ficticios: no se usan datos reales de pacientes.
- Presupuesto cero. No se contactan proveedores ni se crean cuentas con datos reales.
- **Stack definido:** Python, FastAPI, JWT, SQLAlchemy, PostgreSQL, Redis, Docker y Docker Compose en el backend; React, TypeScript y Vite en el frontend.
- La competencia gratuita (Turnito, Ulifeon, Naclix, plan freemium de Bilog) condiciona el precio.
- El repositorio debe poder clonarse y correr los tests solo con el README.

## 10. Riesgos

- **Impacto no probado:** se supone que el recordatorio por WhatsApp reduce el ausentismo, pero no hay dato propio ni cifra con fuente.
- **Adopción:** el odontólogo independiente puede no adoptar un sistema nuevo, o preferir las opciones gratuitas.
- **Seña no usada:** el odontólogo puede no querer cobrar señas, o el paciente rechazarlas.
- **Marco legal:** la Ley 25.326 aplica a los datos de pacientes. La Ley 24.240 excluye a los profesionales liberales con título y matrícula (su publicidad sí queda alcanzada), pero el análisis puede cambiar si el cliente es una clínica o se evalúa la relación con el proveedor del software. La seña requiere revisión legal y **no se implementa con datos reales** en el prototipo.
- **Evidencia débil:** casi todo el estudio es afirmación comercial leída con resúmenes automáticos.
- **Dependencias externas:** Meta y Mercado Pago pueden cambiar políticas o precios.
- **Alcance:** trabajo individual con un MVP mayor que lo implementable.
- **Reproducibilidad:** correr los tests con PostgreSQL y Redis complica el README. Conviene que los tests del change no los requieran, por ejemplo usando SQLite en memoria.
- **Datos de contexto:** las encuestas citadas son pequeñas y no representativas.

## 11. Preguntas abiertas

- ¿Es válida legalmente la retención de la seña? **Requiere revisión legal.**
- ¿Es vigente el límite de 5 números verificados del número de prueba de Meta?
- ¿Qué obras sociales hay que soportar y cómo se liquidan?
- ¿Sigue vigente el trámite de inscripción de la base de datos en el Registro Nacional de Bases de Datos (AAIP)? Es obligatorio si hay datos reales de pacientes (art. 21 de la Ley 25.326); hay que documentar el trámite.
- **Funcionalidades "No evidenciado" en el estudio.** Se documentan con su metodología de búsqueda (lectura de sitio oficial, precios, ayuda y privacidad con `WebFetch`) y un nivel de confianza **bajo a medio**:
  - **Anti-solapamiento:** solo como afirmación comercial (Órbita y EXACT); ninguno lo comprueba.
  - **Horarios recurrentes configurables con excepciones:** ningún sistema lo evidencia. Dentalink muestra "horario por dentista" y Dentidesk, intervalos y bloqueo de feriados.
  - **Reprogramación por el paciente:** comprobada solo en Dentally; Turnito, ClinIA y Clinicorp la declaran como afirmación comercial.
  - **Historial de cambios de turno:** no evidenciado como función de agenda; Naclix declara auditoría en su política [C] (confianza media-baja).
  - **API oficial de WhatsApp:** ningún competidor la documenta.
- ¿Qué decisiones de arquitectura concretas tomará la KB sobre el stack? Se resuelve en `kb-creator`.
