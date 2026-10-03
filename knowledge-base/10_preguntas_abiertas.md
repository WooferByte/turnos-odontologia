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
**Sin resolver (2026-10-02)**: no se concilia aquí; queda derivada a la pregunta legal P-01 (revisión legal). **2026-10-03:** P-01 se cierra como fuera del alcance académico; la conciliación requiere revisión legal antes de uso real.

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
| P-01 | Alta | **[CERRADA 2026-10-03: fuera del alcance académico; requiere revisión legal antes de uso real]** ¿Es **legalmente válida la retención de la seña** si el paciente cancela fuera de plazo (Ley 24.240, cláusulas abusivas, revocación)? ¿Y la devolución del 100%? **Requiere revisión legal; no se implementa con datos ni dinero reales.** | Uso real de RN-SP-04/05 (no bloquea el prototipo) | Asesor legal / autor |
| P-02 | Alta | **[CERRADA 2026-10-03: fuera del alcance académico; requiere revisión legal antes de uso real]** ¿Sigue vigente el **trámite de inscripción de la base en el Registro Nacional de Bases de Datos (AAIP)**, obligatorio con datos reales de pacientes (art. 21 Ley 25.326)? Documentar el procedimiento | Uso con datos reales | Autor / asesor legal |
| P-03 | Alta | **[CERRADA 2026-10-03: fuera del alcance académico; el consentimiento es un borrador «no validado legalmente»]** ¿Qué texto de **consentimiento** y qué base legal se usan para datos de salud (Ley 25.326; Ley 26.529 como referencia de historia clínica)? **No es asesoría legal** | US-070 | Autor / asesor legal |
| P-04 | Media | **[DIFERIDA a Fase 2 (Cloud API)]** ¿Es vigente el **límite de 5 números verificados** del número de prueba de Meta? (dato de terceros, a verificar en la documentación oficial de Meta) | Demo con Cloud API | Autor |
| P-05 | Media | **[DIFERIDA a Fase 2 (Cloud API)]** ¿Es viable configurar la **WhatsApp Cloud API en modo prueba** sin datos reales (cuenta de Meta para desarrolladores, número de prueba, webhook público)? Si no, se usa `wa.me` | Change de recordatorios | Autor |
| P-06 | Media | **[DIFERIDA a Fase 2 (Cloud API)]** **Costo por conversación** y requisitos de producción (verificación de empresa, plantillas) de la Cloud API: sin fuente verificada | Etapa posterior | Autor |
| P-07 | Media | **[DIFERIDA 2026-10-03: fuera de la v1]** ¿Qué **obras sociales** hay que soportar y **cómo se liquidan**? (v1.1: carga manual de códigos y valores) | v1.1 | Autor / odontólogo usuario |
| P-08 | Media | **[CERRADA 2026-10-03: seña 30 min, oferta 2 h, configurables]** ¿Plazo de **vencimiento de la seña impaga** y de la **oferta de lista de espera**? (sin valor de fuente; SU-05) | Changes de seña y lista de espera | Autor |
| P-09 | Media | ¿La recepcionista puede ver anamnesis y evolución? (SU-04) | RBAC de la ficha | Autor |
| P-10 | Media | ¿El primer change incluye validación de horario recurrente y bloqueos, o solo solapamientos por profesional y sillón? (recomendación: solo solapamientos + estados activos, para que sea chico) | Propose del change | Autor |
| P-11 | Media | ¿Se permite **sobreturno** (turno superpuesto intencional) desde el panel? Bilog [C], Naclix [AC] y Dentalink [C] lo ofrecen; esta KB lo **prohíbe** por RN-AG-05/08 | Reglas de agenda | Autor |
| P-12 | Baja | ¿Se permite al paciente cancelar fuera de plazo perdiendo la seña, o solo se bloquea la acción online? (KB: se bloquea; SU-06) | US-022 | Autor |
| P-13 | Baja | Identificación del paciente en la reserva pública: ¿DNI obligatorio? (SU-03) | US-020 | Autor |
| P-14 | Baja | ¿Granularidad de huecos (5, 10, 15 min)? (KB propone 5) | Disponibilidad | Autor |
| P-15 | Baja | **[DIFERIDA 2026-10-03: fuera de la v1]** Precio a publicar en ARS (diferenciador) frente a competidores gratuitos: sin definir | Comercial | Autor |
| P-16 | Baja | Completar la **"Verificación de fuentes"** del informe (mínimo 5 fuentes de tipos distintos, comprobadas personalmente) y el nombre del integrante (hoy "[Nombre del autor]") | Entrega de la Etapa 2 | Autor |
| P-17 | Baja | Versiones de Python, FastAPI, SQLAlchemy, PostgreSQL, Redis, React y Vite (no figuran en las fuentes; confirmados Python 3.11+ y SQLAlchemy 2.x). Política: un único archivo de dependencias con pins exactos, fijados en el `design.md` del primer change y verificados en clon limpio; toda dependencia de test declarada | Change de infraestructura | Autor |
| P-18 | Media | Para el primer change: confirmar tipo de clave primaria, tabla `Consultorio` mínima, estado inicial `reservado`, forma del error y del cuerpo RFC 7807, y qué hace el caso de uso ante una referencia inexistente o inactiva (E12). **Resuelta el 2026-10-03** (ver decisiones); las elecciones que siguen siendo Suposición están en SU-08 | `design.md` del primer change | Autor |
| P-19 | Baja | Confirmar la lista «A confirmar por el autor» de `04_modelo_de_datos.md` y las Suposiciones SU-08 (restantes) y SU-09 (tiempos de token, refresh, hash) | `design.md` de los changes correspondientes | Autor |

### Decisiones del autor (2026-10-02)

Al 2026-10-02, las preguntas P-01 a P-08 y P-15 seguían abiertas; **se cerraron o difirieron el 2026-10-03** (ver la tabla de decisiones del 2026-10-03). Las restantes quedaron así (se conservan en la tabla como registro):

| ID | Estado | Decisión del autor |
|---|---|---|
| P-09 | **Resuelta (2026-10-02)** | Confirmada SU-04 con matiz: la recepcionista ve datos **administrativos** (identificación, contacto, turnos, pagos) pero no **clínicos** (anamnesis, evolución, odontograma). Ajustados RN-FC-02 y la matriz de `03_actores_y_roles.md` |
| P-10 | **Resuelta (2026-10-02)** | El primer change cubre **solo** solapamientos por profesional y por sillón, con estados activos. No valida horario de atención ni bloqueos (RN-AG-04/04b quedan fuera) |
| P-11 | **Resuelta (2026-10-02)** | Sobreturnos **prohibidos en la v1**; quedan como **Fase 2**. Bilog, Dentalink y Naclix hoy los ofrecen: es una decisión de alcance, no un desconocimiento del mercado |
| P-12 | **Resuelta (2026-10-02)** | Sin cambios: la cancelación fuera de plazo queda **bloqueada online** (SU-06 confirmada) |
| P-13 | **Resuelta (2026-10-02)** | Paciente sin cuenta, gestionado por token (DD-11, SU-03 confirmadas). **Teléfono obligatorio, DNI opcional** |
| P-14 | **Resuelta (2026-10-02)** | Granularidad de huecos de **5 minutos**, como default propuesto (configurable) |
| P-16 | **Resuelta (2026-10-03)** | Las 5 fuentes del informe fueron verificadas por el autor el 2026-10-02 y el nombre del integrante ya figura en el informe |
| P-17 | **Parcial (2026-10-02; política 2026-10-03)** | Confirmadas Python 3.11+ y SQLAlchemy 2.x. Las demás versiones **no se inventan**: se fijan con pins exactos en un único archivo de dependencias, en el `design.md` del primer change, y se verifican en clon limpio con el README. Alembic no se usa en el primer change |

### Decisiones del autor (2026-10-03)

| Tema | Decisión |
|---|---|
| Historial (`EventoTurno`, RN-AG-11, antes CA-7) | **Fuera del primer change**; se implementa en el change siguiente. Se mantiene en US-010 marcado como E9 |
| Modo de ejecución | **SQLAlchemy 2.x síncrono**; tests con SQLite en memoria y `StaticPool`; sin `aiosqlite` ni `pytest-asyncio`; sin mocks de sesión ni de repositorio (DD-12) |
| Doble conflicto | Si el turno choca con profesional y sillón a la vez, se informan **los dos** errores (lista de códigos); escenario propio E4 |
| Ajustes de la KB | Aprobadas las propuestas de ajuste (contrato del change, subconjunto del modelo, DD-12, DD-13, escenarios E1..E12, regla de capas, `config.yaml`, Definition of Done, política de versiones, restricciones del roadmap) |
| Alcance del proyecto | El autor implementará el **proyecto completo antes de fin de año**, change por change; el change de la consigna es el primero |
| Primer change: E12 | **Entra** como escenario del spec: recurso no encontrado (`RN-GL-04`, `422`; código y status propuestos por el agente) |
| Primer change: endpoint | Expone **`POST /turnos`** (FastAPI) para mostrarlo en Swagger, **sin autenticación** (límite conocido, DD-14); se protege con JWT en el change de usuarios y acceso |
| Primer change: confirmaciones | Confirmados: clave primaria entera, el turno nace `reservado`, tabla `Consultorio` mínima, filtro de estados activos en el dominio, forma del error RFC 7807, E8 y E11 fuera del spec |
| Usuarios y acceso | Nueva Épica 10 en `06_funcionalidades.md` (US-090 a US-094); detalles de tokens y hash como Suposición (SU-09) |
| P-04, P-05, P-06 (WhatsApp Cloud API) | **Diferidas a Fase 2** (DD-06) |
| WhatsApp en la v1 | Enlace **`wa.me`** (semiautomático); la Cloud API pasa a Fase 2 y se conserva el puerto de mensajería (invierte la preferencia anterior de DD-06). La confirmación llega por el link de gestión |
| P-08 (plazos) | **Cerrada**: seña impaga vence a los 30 minutos y oferta de lista de espera a las 2 horas; configurables; valores de diseño del autor, no de mercado |
| P-01, P-02, P-03 (legales) | **Cerradas como fuera del alcance académico; requieren revisión legal antes de uso real.** La seña solo con credenciales de prueba, datos siempre ficticios y el texto de consentimiento es un borrador marcado «no validado legalmente». No se afirma nada legal nuevo |
| P-07 (obras sociales), P-15 (precio) | **Diferidas**, fuera de la v1 |
| Modelo de datos | Todo el modelo de `04_modelo_de_datos.md` llevado al detalle del subconjunto del primer change; lo no respaldado está en «A confirmar por el autor» |
| Migraciones | Alembic desde el change de infraestructura con PostgreSQL; el primer change usa `create_all` (DD-15) |
| Orden de implementación (D10) | `Prioridad` pasa a ser `Orden` (1 a 9, orden de implementación, no importancia) en cada historia de `06_funcionalidades.md`; el change de la consigna (US-010) es el primero |
| Dependencias (D11, D14, D18) | US-060 a US-062, US-070 y US-080 con sus dependencias; US-013, US-014 y US-031 escriben en el historial y dependen de US-015; US-020 tiene como dependencia técnica el change de infraestructura con PostgreSQL (concurrencia, RN-AG-10c / E11) |
| Criterios faltantes (D15) | Criterios propuestos por el agente para US-014, US-021, US-051, US-060, US-061, US-062, US-070 y US-080; a revisar por el autor |
| Reportes (D16) | US-080 es una **extensión fuera del MVP de la sección D del informe**; queda en la v1 como último orden |
| Datos ficticios (D17) | US-071 deja de ser historia: es una regla dura del proyecto (RN-PR-01), se registra en `CLAUDE.md`/`AGENTS.md` y no genera un change propio |
| Rol `dueno` | Se mantienen los tres roles; en el odontólogo independiente la misma persona tiene `odontologo` y `dueno` |

Decisiones de diseño confirmadas sin pregunta propia: DD-03 (tests con SQLite en memoria; el README debe decirlo explícitamente), DD-04 (la restricción de exclusión sigue como Suposición a definir en el `design.md` del change), DD-05 (reprogramar modifica el mismo turno), DD-11 y SU-06/SU-07 (ver `09_decisiones_y_supuestos.md`).

## Discovery de la KB (`state.kb.discovery`)

- `[DISCOVERY]` `system_type` inferido como `web_app` (API REST FastAPI + SPA React + rutas públicas). Confianza alta; el change de la consigna se entrega como API/módulo sin UI, lo que no cambia el tipo del producto.
- `[DISCOVERY]` `scale` inferido como `team` (un consultorio con pocos usuarios internos, más pacientes que acceden por link público sin cuenta). **Confianza alta** (confirmada por el autor el 2026-10-02): un consultorio con pocos usuarios internos; los pacientes no tienen cuenta (acceden por token), por lo que no son usuarios del sistema y no corresponde `public_multi_user`.
