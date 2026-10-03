# Decisiones y Supuestos

## Decisiones documentadas

### DD-00 — Segmento primario: odontólogo independiente (1 profesional, 1 sillón)
**Decisión**: el MVP apunta al odontólogo independiente.
**Contexto**: predominio del consultorio propio (85% en la encuesta de Dental Tribune, n=313, no probabilística) y baja digitalización declarada (68% historia clínica en papel, RePEc n=100 AMBA).
**Alternativas consideradas**: clínicas multisucursal (terreno de Bilog, ClinIA, Órbita, Dentalink); agendas multirrubro (Turnito, SimpleTurno).
**Justificación**: adopción sencilla; los competidores clínicos locales no publican precio o cobran en USD.
**Trade-offs aceptados**: compite con opciones gratuitas (Turnito, Naclix, Bilog freemium, Ulifeon).

### DD-01 — Stack: Python + FastAPI + JWT + SQLAlchemy + PostgreSQL + Redis + Docker; React + TS + Vite
**Decisión**: stack definido por el autor (Discovery, punto 9). Redis para tareas diferidas: en la v1, preparar los recordatorios `wa.me`, vencer señas impagas y vencer ofertas de lista de espera (Redis no envía mensajes; ver DD-06). Monolito modular + un worker.
**Contexto**: restricción del trabajo; no se reabre.
**Alternativas consideradas**: no aplica (decisión tomada).
**Justificación**: decisión del autor.
**Trade-offs aceptados**: más infraestructura de la que necesita el change de la consigna (ver DD-03).

### DD-02 — Reglas de agenda como funciones puras de dominio
**Decisión**: el solapamiento, la ventana de cancelación y las transiciones de estado se implementan en `domain/` sin dependencias de FastAPI ni SQLAlchemy.
**Contexto**: la consigna exige tests automatizados por escenario del spec.
**Alternativas consideradas**: validar en el router o solo con restricciones de base.
**Justificación**: tests rápidos y deterministas; el change puede entregarse como módulo sin UI.
**Trade-offs aceptados**: la atomicidad se garantiza aparte (DD-04).

### DD-03 — Tests del change sin PostgreSQL ni Redis
**Decisión**: la suite del change corre con **SQLite en memoria** y un doble de la cola; PostgreSQL y Redis solo en docker-compose.
**Contexto**: restricción "el repositorio debe poder clonarse y correr los tests solo con el README"; riesgo de reproducibilidad identificado en el Discovery.
**Alternativas consideradas**: Testcontainers / docker-compose obligatorio para tests.
**Justificación**: README reproducible en cualquier máquina con Python.
**Trade-offs aceptados**: diferencias de dialecto SQLite/PostgreSQL (zonas horarias, restricciones de exclusión). Mitigación: la regla vive en el dominio y se testea allí; las fechas se normalizan a UTC antes de persistir.
**Confirmada por el autor (2026-10-02).** El README debe decir explícitamente que los tests del change corren con SQLite en memoria, sin PostgreSQL ni Redis.

### DD-04 — Atomicidad del anti-solapamiento
**Decisión**: validar en dominio dentro de una transacción, y en PostgreSQL reforzar con restricción de exclusión sobre `tstzrange(inicio, fin, '[)')` por profesional y por sillón para estados activos (**Suposición:** la implementación exacta se decide en el design del change).
**Contexto**: RN-AG-10c (reservas concurrentes).
**Alternativas consideradas**: bloqueo `SELECT ... FOR UPDATE` del recurso; solo validación en aplicación.
**Justificación**: la base es la última línea de defensa; el intervalo `[)` coincide con RN-AG-09.
**Trade-offs aceptados**: la restricción no existe en SQLite; la concurrencia real solo se prueba en el perfil con PostgreSQL.
**Confirmada por el autor (2026-10-02).** La restricción de exclusión sigue siendo **Suposición** hasta que se defina en el `design.md` del change.

### DD-05 — Reprogramar modifica el mismo turno
**Decisión**: reprogramar cambia `inicio/fin` del turno y registra `EventoTurno(reprogramado)` con antes/después.
**Alternativas consideradas**: cancelar y crear uno nuevo.
**Justificación**: conserva seña, token y trazabilidad en un solo registro.
**Trade-offs aceptados**: reportes de ocupación deben leer el historial para conocer horarios previos.
**Confirmada por el autor (2026-10-02)**, sin cambios.

### DD-06 — WhatsApp en la v1: enlace `wa.me` (semiautomático); Cloud API oficial en Fase 2
**Decisión**: en la v1 el canal es el **enlace `wa.me`**: el sistema arma el mensaje con el link de gestión y el odontólogo lo envía desde su WhatsApp. **La Cloud API oficial pasa a Fase 2.** Se conserva el **puerto de mensajería** (`MensajeriaPort`) con el adaptador `WaMeAdapter`, para sumar el `CloudApiAdapter` después sin tocar el dominio. Con `wa.me`, la confirmación del paciente llega por el **link de gestión** del turno (RN-WA-02).
**Esto invierte la preferencia anterior** (Cloud API en modo prueba preferida, `wa.me` como alternativa).
**Contexto**: ningún competidor documenta la API oficial (informe C.3); DentalCore usa sesión por QR (riesgo de bloqueo), Bilog envía manual/semiautomático, Neocita usa enlace en el plan gratis.
**Justificación**: `wa.me` está a la par del mercado, no requiere cuenta ni webhook público, y reduce el riesgo del trabajo individual.
**Trade-offs aceptados**: no hay envío automático ni respuesta por el chat en la v1; en producción la Cloud API requeriría verificación de empresa, plantillas aprobadas y costo por conversación (sin fuente verificada; P-04, P-05 y P-06 diferidas a Fase 2). **Descartado**: sesión por QR/no oficial.
**Qué queda para Redis en la v1 (Suposición del agente; el autor pidió definirlo, no lo decidió)**: preparar el recordatorio a `inicio − 24 h` (estado `generado_link`), vencer señas impagas (30 min) y vencer ofertas de lista de espera (2 h). No se necesita para enviar mensajes.
**Origen**: decisión del autor 2026-10-03.

### DD-07 — Mercado Pago Checkout Pro con cuenta única del odontólogo
**Decisión**: v1 usa Checkout Pro en la cuenta del odontólogo, solo con credenciales de prueba. Split 1:N = Fase 2.
**Contexto**: la seña con MP es estándar en las agendas argentinas (Turnito [C], SimpleTurno Pro [C], Neocita pago [C]) pero no está evidenciada en los sistemas clínicos DentalCore ni Bilog (vacío C.3.4).
**Trade-offs aceptados**: la retención de la seña requiere revisión legal; no se cobra dinero real.

### DD-08 — Sillón como recurso con valor 1 por defecto
**Decisión**: `Sillon` es entidad de primer nivel; todo turno referencia un sillón; el seed crea uno.
**Justificación**: el change "crear turno sin solapamientos por profesional y por sillón" encaja sin ampliar el MVP, y la Fase 2 multi-sillón no requiere rediseño.

### DD-09 — Intervalos semiabiertos `[inicio, fin)` y fechas en UTC
**Decisión**: turnos como intervalos semiabiertos; persistencia en UTC con zona; reglas de horario en `America/Argentina/Buenos_Aires`.
**Justificación**: un turno que empieza cuando termina otro es válido (caso borde exigido por la consigna).

### DD-10 — Reglas de negocio configurables con defaults propuestos
**Decisión**: las reglas de negocio son configurables por el odontólogo y parten de los valores que siguen, separados según su estado.
**Contexto**: informe D.4: "decisiones de diseño del autor, no hechos de mercado".

**Decisiones de diseño confirmadas por el autor (2026-10-02)**:
- Antelación mínima de reserva: 2 h (IN-06 / RN-TD-02).
- Granularidad de huecos: 5 minutos (P-14).
- Cancelación fuera de plazo: bloqueada online (P-12 / RN-TD-03).

**Plazos de diseño confirmados por el autor (2026-10-03), configurables; son valores de diseño del autor, no de mercado**:
- Seña impaga: vence a los **30 minutos** (RN-SP-03).
- Oferta de lista de espera: vence a las **2 horas** (RN-LE-03).

**Defaults propuestos (sin valor de mercado de referencia)**:
- Ventana de cancelación: 24 h, configurable entre 24 y 48.
- Horizonte de reserva: 60 días.
- Paciente nuevo: reserva directa, con aprobación manual opcional.

**Suposiciones sujetas a revisión legal (P-01)**:
- Seña retenida si el paciente cancela fuera de plazo.
- Seña devuelta al 100% si cancela el odontólogo o si el paciente cancela dentro de plazo (SU-06).

### DD-11 — Paciente sin cuenta, gestionado por token
**Decisión**: el paciente reserva y gestiona su turno con un token firmado, sin crear cuenta.
**Justificación**: objetivo de reserva en menos de 30 s (CU-01); menos datos personales almacenados.
**Confirmada por el autor (2026-10-02).** En la reserva pública, el **teléfono es obligatorio y el DNI es opcional** (ver SU-03).

### DD-12 — Backend síncrono y tests sin mocks de sesión
**Decisión**: el primer change usa **SQLAlchemy 2.x síncrono**. Los tests corren sobre SQLite en memoria (`sqlite+pysqlite:///:memory:` con `StaticPool`), **sin `aiosqlite` ni `pytest-asyncio`**. El dominio se testea **sin base de datos**. **No se usan mocks de sesión ni de repositorio.**
**Contexto**: DD-03 (tests sin PostgreSQL ni Redis) y la restricción de reproducibilidad con solo el README. Los mocks de sesión pueden divergir del comportamiento real de la base, y las dependencias de test no declaradas rompen el clon limpio.
**Alternativas consideradas**: pila asíncrona (SQLAlchemy async con aiosqlite); mocks de `Session` y de repositorio.
**Justificación**: menos dependencias, menos puntos de falla en un clon limpio, y los tests ejercen consultas reales.
**Trade-offs aceptados**: si más adelante se necesita asincronía (por ejemplo, el worker), se evalúa en el change que la requiera. La concurrencia real no se prueba con SQLite (DD-04).
**Origen**: decisión del autor 2026-10-03. Detalle de fixtures en `08_arquitectura_propuesta.md` («Fixtures de test»).

### DD-13 — Reloj único `utc_now()` y datetimes aware en UTC
**Decisión**: la hora actual sale de un único `utc_now()` **inyectable**; el **dominio recibe solo datetimes aware en UTC**; el **adaptador de persistencia normaliza** lo que lee; un **test guard** exige que toda columna de fecha-hora tenga zona.
**Contexto**: DD-09 y RN-GL-01 ya fijan UTC y `[inicio, fin)`; esta decisión define cómo se garantiza en el código.
**Alternativas consideradas**: dejar la conversión repartida por el código; usar datetimes naive en UTC.
**Justificación**: un datetime naive es ambiguo y su mezcla con uno aware falla o produce desfasajes; el reloj inyectable hace deterministas los tests.
**Trade-offs aceptados**: costo de normalizar en el adaptador.
**Origen**: decisión del autor 2026-10-03 (aprobación de las propuestas de ajuste de la KB).
**Suposición a verificar en el change**: SQLite no conserva la zona horaria y puede devolver datetimes naive aunque la columna sea con zona (relacionada con R-10). Se verifica con un test de ida y vuelta en el change.

### DD-14 — El primer change expone `POST /turnos` sin autenticación (límite conocido)
**Decisión**: el primer change expone `POST /turnos` (FastAPI) para poder mostrarlo desde Swagger (`/docs`) en el video, **sin autenticación**. Es un **límite conocido**: el endpoint se protege con JWT cuando se implemente el change de usuarios y acceso (Épica 10, US-092). El README del change lo declara.
**Contexto**: la consigna admite un módulo sin interfaz gráfica; el autor prefiere demostrar el endpoint. Los usuarios no existen hasta la Épica 10.
**Justificación**: mantener el primer change chico y autocontenido.
**Trade-offs aceptados**: un endpoint de escritura abierto; aceptable solo con datos ficticios y sin despliegue público.
**Origen**: decisión del autor 2026-10-03.

### DD-15 — Migraciones con Alembic desde el change de infraestructura con PostgreSQL
**Decisión**: Alembic se usa **a partir del change de infraestructura con PostgreSQL**. El primer change **no lo usa**: los tests crean el esquema con `create_all`.
**Justificación**: el primer change debe correr sin servicios externos; las migraciones solo agregan valor cuando hay un esquema persistente en PostgreSQL.
**Trade-offs aceptados**: las columnas que el primer change no crea se agregan después con migraciones (`04_modelo_de_datos.md`).
**Origen**: decisión del autor 2026-10-03.

## Supuestos inferidos

### SU-01 — Impacto del recordatorio sobre el ausentismo
**Supuesto**: el recordatorio por WhatsApp reduce el ausentismo.
**Origen**: Discovery, riesgos. No hay dato propio ni cifra con fuente (la de 60-70% se descartó).
**Riesgo si es falso**: el diferenciador principal pierde valor.
**Cómo validar**: medir ausentismo con y sin recordatorio en un piloto (fuera del alcance académico).

### SU-02 — Duraciones y horario del seed
**Supuesto**: prestaciones (30-60 min) y horario (L-V 9-13 y 15-19) del seed son ilustrativos.
**Origen**: inferido; no hay fuente.
**Riesgo si es falso**: ninguno funcional (son configurables).
**Cómo validar**: preguntar a un odontólogo en la demo.

### SU-03 — Identificación del paciente sin cuenta
**Supuesto**: alcanza con teléfono de WhatsApp (obligatorio) + DNI (opcional) y email (opcional), y token por turno.
**Origen**: patrón de Bilog (DNI + email [C]) y Turnito ("reserva sin registro" [AC]).
**Riesgo si es falso**: duplicados de pacientes; suplantación si el link se comparte.
**Cómo validar**: definir en el change de reserva pública.
**Confirmada por el autor (2026-10-02)** con ajuste: **teléfono obligatorio, DNI opcional**, email opcional; paciente sin cuenta gestionado por token (DD-11). Sin DNI, la detección de duplicados se apoya en el teléfono.

### SU-04 — Recepcionista sin acceso a datos clínicos
**Supuesto**: la recepcionista ve los datos **administrativos** del paciente (identificación, contacto, turnos, pagos) pero no los **clínicos** (anamnesis, evolución, odontograma), por minimización de datos sensibles.
**Riesgo si es falso**: fricción operativa en consultorios con recepcionista.
**Cómo validar**: confirmar con el autor.
**Confirmada por el autor (2026-10-02)** con ese matiz: acceso a datos administrativos, no a clínicos.

### SU-05 — Plazos de vencimiento de seña y de oferta de lista de espera
**Supuesto**: existen y son configurables.
**Origen**: inferido (Open Dental y Dentally documentan ofertas de huecos [C] pero no se relevó el plazo).
**Confirmada por el autor (2026-10-03)**: seña impaga vence a los **30 minutos** y la oferta de lista de espera a las **2 horas**, ambos por defecto y configurables. Son valores de diseño del autor, no de mercado (P-08 cerrada).

### SU-06 — Devolución de seña al cancelar dentro de plazo
**Supuesto**: si el paciente cancela dentro de plazo, la seña se devuelve.
**Origen**: inferido de "ventana de cancelación sin penalidad" (informe D.4).
**Cómo validar**: confirmar con el autor y revisión legal.
**Confirmada por el autor (2026-10-02).** La retención por cancelación fuera de plazo (RN-SP-04) sigue sujeta a revisión legal (P-01).

### SU-07 — Monto y obligatoriedad de la seña
**Supuesto**: la seña es opcional (desactivada por defecto) y su monto lo fija el odontólogo.
**Origen**: riesgo "seña no usada" del Discovery.
**Confirmada por el autor (2026-10-02).**

### SU-08 — Elecciones para el primer change
**Confirmadas por el autor (2026-10-03):**
1. Clave primaria **entera autoincremental**.
2. Tabla `Consultorio` mínima.
3. El turno nace `reservado`.
4. El filtro de estados activos (`ESTADOS_ACTIVOS`) lo aplica el dominio.
5. Forma del error de dominio y del cuerpo RFC 7807 con lista de códigos y conflictos.
6. E8 (intervalo inválido) y E11 (concurrencia) **no** son escenarios del spec; E11 se cubre cuando exista el perfil con PostgreSQL.
7. **E12 entra** como escenario del spec (recurso no encontrado).
8. El primer change **expone `POST /turnos`** sin autenticación (DD-14).
9. Alembic desde el change de infraestructura con PostgreSQL (DD-15).

**Siguen como Suposición (propuestas del agente, a confirmar en el `design.md` del change):**
- El código `RN-GL-04` y el status `422` para E12 (un único status para inexistente e inactivo; el autor delegó la elección).
- El valor del campo `type` del cuerpo RFC 7807 (URI relativa) y los nombres exactos de clases y funciones del contrato.
- El alcance exacto de los tests de API (E1, E4 y E12 como mínimo).
- Los nombres de columnas y demás elecciones del modelo completo, listadas en «A confirmar por el autor» de `04_modelo_de_datos.md`.
**Cómo validar**: confirmar con el autor al redactar el `design.md` del primer change.

### SU-09 — Autenticación: tiempos de token, refresh y hash (propuesta simple)
**Supuesto** (propuesta concreta del agente, 2026-10-03; el autor no la decidió): access token JWT de **15 minutos**; refresh token JWT de **7 días**, sin revocación en la v1 (sin tabla de tokens); hash de contraseña **bcrypt**; firma HS256 con secreto de entorno.
**Origen**: valores de ejemplo ya presentes en la variable de entorno `JWT_ACCESS_MINUTES`/`JWT_REFRESH_DAYS` de `08_arquitectura_propuesta.md`; sin fuente de mercado.
**Riesgo si es falso**: ninguno funcional; son configurables por variable de entorno.
**Cómo validar**: confirmar con el autor al implementar el change de usuarios y acceso.

## Riesgos (del Discovery)

| Código | Riesgo | Mitigación |
|---|---|---|
| R-01 | Impacto no probado del recordatorio sobre el ausentismo | Medir (SU-01); no prometer cifras |
| R-02 | Adopción frente a opciones gratuitas (Turnito, Naclix, Bilog freemium, Ulifeon) | Diferenciadores: lista de espera, horario + trazabilidad, precio en ARS |
| R-03 | Seña no usada (odontólogo no la quiere, paciente la rechaza) | Seña opcional y configurable |
| R-04 | Marco legal: Ley 25.326 aplica; Ley 24.240 excluye a profesionales liberales con título y matrícula pero requiere revisión (cambia si el cliente es una clínica o se evalúa la relación con el proveedor del software); Ley 26.529 como referencia | Datos ficticios; seña sin dinero real; revisión legal antes de uso real |
| R-05 | Evidencia de mercado débil (mayormente afirmación comercial leída con resúmenes automáticos) | Verificación personal de fuentes (5 fuentes completadas el 2026-10-02, P-16) y demos (pendientes) |
| R-06 | Dependencia de políticas y precios de Meta y Mercado Pago | Puertos/adaptadores; en la v1 `wa.me` (sin dependencia de Meta); Cloud API en Fase 2 |
| R-07 | Alcance: MVP mayor que lo implementable individualmente | La consigna exige un solo change; roadmap por changes chicos |
| R-08 | Reproducibilidad de tests con PostgreSQL y Redis | DD-03: SQLite en memoria y doble de cola |
| R-09 | Encuestas de contexto pequeñas y no representativas | No usarlas como hecho de diseño |
| R-10 | Diferencias SQLite vs PostgreSQL (zonas horarias, exclusión) | Regla en dominio; UTC; perfil opcional con PostgreSQL |

## Nota de proceso

Estructura y nivel de detalle revisados contra la documentación de un proyecto anterior del autor (2026-10-03); no se reutilizó contenido de dominio.
