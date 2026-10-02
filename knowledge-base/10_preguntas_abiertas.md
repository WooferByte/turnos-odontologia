# Preguntas Abiertas

> **Conclusión transversal del Discovery:** la evidencia de mercado es **mayormente afirmación comercial [AC]**. Solo Open Dental tiene confianza alta (manual y API documentados). Lo comprobado [C] se limita en general a precios, políticas de privacidad y algunas páginas de ayuda. Las notas se obtuvieron con `WebFetch`, que devuelve **resúmenes automáticos** y no texto literal. La matriz de puntuación es preliminar y está sujeta a demos y a las demos. La **verificación personal de las 5 fuentes** del informe fue completada por el autor el 2026-10-02 (ver P-16); en el informe falta solo el nombre del autor.

## Inconsistencias detectadas

### IN-01 — Conteo de sistemas por grupo
**`docs/discovery/informe-discovery.md` dice**: 31 sistemas = 13 argentinos (9 con módulo odontológico + 4 multirrubro), 9 latinoamericanos/hispanohablantes y 9 internacionales.
**`discovery/discovery.md` (punto 4) dice**: 9 de Argentina, 8 de Latinoamérica, 8 internacionales y 6 regionales o con presencia local sin evidencia.
**Impacto**: bajo; confunde al lector del entregable.
**Resolución propuesta**: tomar el informe (segunda pasada, prevalece) y corregir `discovery.md`.
**Resuelta (2026-10-02)**: prevalece el conteo del informe (31 = 13 argentinos + 9 latinoamericanos/hispanohablantes + 9 internacionales); se corrigió `discovery/discovery.md`.

### IN-02 — Historial de cambios de turno en competidores
**Informe (C.3.3)**: la trazabilidad de cambios de turno "solo aparece en Naclix (auditoría [C])".
**`discovery.md` (punto 11)**: "Historial de cambios de agenda: no evidenciado".
**Impacto**: matiza el diferenciador "horario recurrente + trazabilidad".
**Resolución propuesta**: la auditoría de Naclix está comprobada en su **política de privacidad** (auditoría e historial de versiones), no como historial de cambios de turno visible en la agenda. Redactar: "historial de cambios de turno: no evidenciado como función de agenda; Naclix declara auditoría en su política [C]". Confianza: **media-baja**.
**Resuelta (2026-10-02)**: se aplicó la redacción propuesta en el informe (C.3.3) y en `discovery/discovery.md` (punto 11).

### IN-03 — Confianza de Naclix y DentalCore
**Informe (A.1/B)**: Naclix y DentalCore con confianza **Medio**.
**`discovery.md` (punto 4)**: Naclix "—", DentalCore "baja".
**Resolución propuesta**: usar los valores del informe (más recientes y con criterio documentado).
**Resuelta (2026-10-02)**: se usan los niveles del informe (Naclix y DentalCore: Medio); se corrigió `discovery/discovery.md`.

### IN-04 — Indicador de la encuesta RePEc
**Informe**: "66% no usa software de **gestión**". **`discovery.md`**: "66% no usa software de **diagnóstico**".
**Resolución propuesta**: verificar en la fuente original (https://ideas.repec.org/a/cwf/dentar/dent2025127.html) y unificar.
**Resuelta (2026-10-02)**: el autor verificó la fuente. El 66% no usa software de **diagnóstico y diseño de tratamientos**; el informe y `discovery.md` ya dicen lo mismo.

### IN-05 — Ley 24.240 y la seña
**Informe (D.4)**: la retención de la seña "podría tener implicancias según la Ley 24.240" (revocación, cláusulas abusivas).
**`discovery.md` (riesgos)**: la Ley 24.240 **excluye** a los profesionales liberales con título y matrícula (su publicidad sí queda alcanzada), pero el análisis puede cambiar si el cliente es una clínica o se evalúa la relación con el proveedor del software.
**Resolución propuesta**: no son contradictorias pero no están conciliadas → pregunta legal P-01. **No es asesoría legal.**
**Sin resolver (2026-10-02)**: no se concilia aquí; queda derivada a la pregunta legal P-01 (revisión legal).

### IN-06 — Antelación mínima de reserva
**Informe (D.4)**: "Configurable (sin valor de mercado de referencia)". **Discovery**: propuesta 2 h.
**Resolución propuesta**: KB adopta 2 h como default **propuesto** (RN-TD-02); confirmar.
**Resuelta (2026-10-02)**: el autor confirmó la antelación mínima de reserva de 2 horas como default propuesto (configurable).

## Funcionalidades "No evidenciado" en el Discovery

Metodología: lectura de sitio oficial, precios, ayuda y privacidad con `WebFetch` (resúmenes automáticos). "No evidenciado" **no significa que no exista**: significa que no pudo constatarse. Nivel de confianza del hallazgo de vacío: **bajo a medio**.

| # | Funcionalidad | Qué se encontró | Confianza | Qué verificar (demo) |
|---|---|---|---|---|
| NE-01 | **Prevención de solapamientos** | Solo afirmación comercial: Órbita ("no permite dos pacientes en el mismo sillón") y EXACT ("sin doble turno", no local). Ningún sistema lo comprueba | Baja-media | Naclix, DentalCore, Dentalink |
| NE-02 | **Horarios recurrentes configurables con excepciones** | Ningún sistema lo evidencia. Lo más cercano: "horario por dentista" en Dentalink [C]; intervalos 15/30/40 min y bloqueo de feriados en Dentidesk [C]; reservas recurrentes en planes Advance/Pro de Turnito [C] (son reservas del cliente, no horario del profesional) | Media | Naclix, Dentalink |
| NE-03 | **Reprogramación por el paciente** | **Comprobada solo en Dentally** (cambio/cancelación por link) [C]. Turnito, ClinIA y Clinicorp la declaran [AC]. Bilog permite cancelar con ventana mínima [C] | Media | Turnito, Bilog |
| NE-04 | **Historial de cambios de turno** | No evidenciado como función de agenda; Naclix declara auditoría e historial de versiones en su privacidad [C] (ver IN-02) | Media-baja | Naclix |
| NE-05 | **API oficial de WhatsApp Business en competidores** | Ningún competidor la documenta. DentalCore la descarta (sesión por QR); Bilog manual/semiautomático; Neocita enlace en plan gratis; Dentalink adicional pago sin mecanismo; Naclix ("canal oficial") y Doctocliq ("Meta Business Partner") lo sugieren sin documentar | Media | Naclix, DentalCore, Dentalink |
| NE-06 | Lista de espera con flujo documentado (estados, prioridad, vencimiento) en sistemas locales | Naclix la declara con aviso automático [AC]; DentalCore declara que el bot ofrece huecos [AC]. Documentado solo en Open Dental y Dentally [C] | Media | Naclix, DentalCore |
| NE-07 | Seña con Mercado Pago en sistemas clínicos | No evidenciada en DentalCore ni Bilog; Naclix la declara [AC] | Media | DentalCore |

## Preguntas abiertas (priorizadas)

| ID | Prioridad | Pregunta | Bloquea | Decisor |
|---|---|---|---|---|
| P-01 | Alta | ¿Es **legalmente válida la retención de la seña** si el paciente cancela fuera de plazo (Ley 24.240, cláusulas abusivas, revocación)? ¿Y la devolución del 100%? **Requiere revisión legal; no se implementa con datos ni dinero reales.** | Uso real de RN-SP-04/05 (no bloquea el prototipo) | Asesor legal / autor |
| P-02 | Alta | ¿Sigue vigente el **trámite de inscripción de la base en el Registro Nacional de Bases de Datos (AAIP)**, obligatorio con datos reales de pacientes (art. 21 Ley 25.326)? Documentar el procedimiento | Uso con datos reales | Autor / asesor legal |
| P-03 | Alta | ¿Qué texto de **consentimiento** y qué base legal se usan para datos de salud (Ley 25.326; Ley 26.529 como referencia de historia clínica)? **No es asesoría legal** | US-070 | Autor / asesor legal |
| P-04 | Media | ¿Es vigente el **límite de 5 números verificados** del número de prueba de Meta? (dato de terceros, a verificar en la documentación oficial de Meta) | Demo con Cloud API | Autor |
| P-05 | Media | ¿Es viable configurar la **WhatsApp Cloud API en modo prueba** sin datos reales (cuenta de Meta para desarrolladores, número de prueba, webhook público)? Si no, se usa `wa.me` | Change de recordatorios | Autor |
| P-06 | Media | **Costo por conversación** y requisitos de producción (verificación de empresa, plantillas) de la Cloud API: sin fuente verificada | Etapa posterior | Autor |
| P-07 | Media | ¿Qué **obras sociales** hay que soportar y **cómo se liquidan**? (v1.1: carga manual de códigos y valores) | v1.1 | Autor / odontólogo usuario |
| P-08 | Media | ¿Plazo de **vencimiento de la seña impaga** y de la **oferta de lista de espera**? (sin valor de fuente; SU-05) | Changes de seña y lista de espera | Autor |
| P-09 | Media | ¿La recepcionista puede ver anamnesis y evolución? (SU-04) | RBAC de la ficha | Autor |
| P-10 | Media | ¿El primer change incluye validación de horario recurrente y bloqueos, o solo solapamientos por profesional y sillón? (recomendación: solo solapamientos + estados activos, para que sea chico) | Propose del change | Autor |
| P-11 | Media | ¿Se permite **sobreturno** (turno superpuesto intencional) desde el panel? Bilog [C], Naclix [AC] y Dentalink [C] lo ofrecen; esta KB lo **prohíbe** por RN-AG-05/08 | Reglas de agenda | Autor |
| P-12 | Baja | ¿Se permite al paciente cancelar fuera de plazo perdiendo la seña, o solo se bloquea la acción online? (KB: se bloquea; SU-06) | US-022 | Autor |
| P-13 | Baja | Identificación del paciente en la reserva pública: ¿DNI obligatorio? (SU-03) | US-020 | Autor |
| P-14 | Baja | ¿Granularidad de huecos (5, 10, 15 min)? (KB propone 5) | Disponibilidad | Autor |
| P-15 | Baja | Precio a publicar en ARS (diferenciador) frente a competidores gratuitos: sin definir | Comercial | Autor |
| P-16 | Baja | Completar la **"Verificación de fuentes"** del informe (mínimo 5 fuentes de tipos distintos, comprobadas personalmente) y el nombre del integrante (hoy "[Nombre del autor]") | Entrega de la Etapa 2 | Autor |
| P-17 | Baja | Versiones mínimas de Python, FastAPI, SQLAlchemy, PostgreSQL, Redis, React y Vite (no figuran en las fuentes; la KB supone Python 3.11+ y SQLAlchemy 2.x) | Change de infraestructura | Autor |

### Decisiones del autor (2026-10-02)

Las preguntas P-01 a P-08 y P-15 **siguen abiertas**. Las restantes quedaron así (se conservan en la tabla como registro):

| ID | Estado | Decisión del autor |
|---|---|---|
| P-09 | **Resuelta (2026-10-02)** | Confirmada SU-04 con matiz: la recepcionista ve datos **administrativos** (identificación, contacto, turnos, pagos) pero no **clínicos** (anamnesis, evolución, odontograma). Ajustados RN-FC-02 y la matriz de `03_actores_y_roles.md` |
| P-10 | **Resuelta (2026-10-02)** | El primer change cubre **solo** solapamientos por profesional y por sillón, con estados activos. No valida horario de atención ni bloqueos (RN-AG-04/04b quedan fuera) |
| P-11 | **Resuelta (2026-10-02)** | Sobreturnos **prohibidos en la v1**; quedan como **Fase 2**. Bilog, Dentalink y Naclix hoy los ofrecen: es una decisión de alcance, no un desconocimiento del mercado |
| P-12 | **Resuelta (2026-10-02)** | Sin cambios: la cancelación fuera de plazo queda **bloqueada online** (SU-06 confirmada) |
| P-13 | **Resuelta (2026-10-02)** | Paciente sin cuenta, gestionado por token (DD-11, SU-03 confirmadas). **Teléfono obligatorio, DNI opcional** |
| P-14 | **Resuelta (2026-10-02)** | Granularidad de huecos de **5 minutos**, como default propuesto (configurable) |
| P-16 | **Parcial (2026-10-02)** | Las 5 fuentes del informe fueron verificadas por el autor el 2026-10-02. Falta solo el nombre del autor en el informe (hoy "[Nombre del autor]") |
| P-17 | **Parcial (2026-10-02)** | Confirmadas Python 3.11+ y SQLAlchemy 2.x. Las versiones de FastAPI, PostgreSQL, Redis, React y Vite se fijan en el README cuando se implemente el change |

Decisiones de diseño confirmadas sin pregunta propia: DD-03 (tests con SQLite en memoria; el README debe decirlo explícitamente), DD-04 (la restricción de exclusión sigue como Suposición a definir en el `design.md` del change), DD-05 (reprogramar modifica el mismo turno), DD-11 y SU-06/SU-07 (ver `09_decisiones_y_supuestos.md`).

## Discovery de la KB (`state.kb.discovery`)

- `[DISCOVERY]` `system_type` inferido como `web_app` (API REST FastAPI + SPA React + rutas públicas). Confianza alta; el change de la consigna se entrega como API/módulo sin UI, lo que no cambia el tipo del producto.
- `[DISCOVERY]` `scale` inferido como `team` (un consultorio con pocos usuarios internos, más pacientes que acceden por link público sin cuenta). **Confianza alta** (confirmada por el autor el 2026-10-02): un consultorio con pocos usuarios internos; los pacientes no tienen cuenta (acceden por token), por lo que no son usuarios del sistema y no corresponde `public_multi_user`.
