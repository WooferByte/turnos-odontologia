# Funcionalidades

Organizadas por **épica** y **historia de usuario** (US-NNN). Versión: **v1** salvo indicación. Cada historia referencia el caso de uso (CU) de `01_vision_y_objetivos.md` y las reglas de `05_reglas_de_negocio.md`.

Cada historia lleva dos líneas de planificación:

- `**Orden**: N` (1 a 9): **orden de implementación, no importancia** (decisión del autor 2026-10-03). Todas las historias de la v1 pertenecen al MVP de la sección D del informe, **salvo US-080 (reportes), que es una extensión fuera de ese MVP**. Dentro de un mismo orden, las dependencias fijan la secuencia.
- `**Depende de**`: historias que deben existir antes. Las historias de panel que distinguen roles dependen de US-092 (Épica 10).

Resumen del orden: **1** US-010 · **2** US-015, US-001, US-004 · **3** Épica 10 (US-090 a US-094), US-002, US-003 · **4** US-011, US-012, US-013, US-014 · **5** US-070, US-020, US-022, US-005 · **6** US-030, US-031, US-021, US-040 · **7** US-050, US-051 · **8** US-060, US-061, US-062 · **9** US-080.

**Notas del orden (decisión del autor 2026-10-03):**
- US-010 depende conceptualmente de US-001 y US-004, pero va **primero** porque el primer change crea el subconjunto mínimo (prestación y sillón por seed); US-001 y US-004 agregan después la gestión (alta, edición, desactivación).
- Las historias de orden 1 y 2 (US-010, US-015, US-001, US-004) crean endpoints antes de la Épica 10 (orden 3): van **sin autenticación** hasta que US-092 los proteja (ver US-092 CA-2) (propuesta aceptada por el autor 2026-10-03, derivada de DD-14; se revisa en el design del change).
- Las historias que leen reglas configurables (RN-GL-03) dependen de US-005, que crea `ConfiguracionReglas` (`04_modelo_de_datos.md`): US-020, US-022, US-030, US-040 y US-050 (propuesta aceptada por el autor 2026-10-03; se revisa en el design del change).
- US-013 CA-2 se completa con US-040 (orden 6) y CA-3 con US-051 (orden 7); US-014 CA-5 se completa con US-051 (orden 7): son referencias hacia adelante, no dependencias.

Los criterios de US-010 usan IDs estables `E1..E12` (compartidos con `07_flujos_principales.md` y con el spec y los tests del change). El autor implementará el proyecto completo antes de fin de año, change por change (decisión 2026-10-03); US-010 es el primero y el hito de entrega de la consigna.

## Épica 1: Configuración de agenda

### US-001 — Tabla de prestaciones
**Como** odontólogo **quiero** definir prestaciones con nombre, duración por defecto y color **para** que cada turno ocupe el tiempo real que necesita.
- [ ] CA-1: puedo crear, editar y desactivar prestaciones; el nombre es único en el consultorio.
- [ ] CA-2: la duración debe ser > 0 y múltiplo de la granularidad; si no, se rechaza.
- [ ] CA-3: cambiar la duración no modifica turnos existentes.
**Orden**: 2
**Depende de**: Ninguna
**Reglas**: RN-AG-01, RN-AG-02, RN-GL-03

### US-002 — Horario recurrente
**Como** odontólogo **quiero** configurar mis días y franjas de atención **para** que solo se ofrezcan turnos dentro de ese horario.
- [ ] CA-1: puedo cargar varias franjas por día (p. ej. mañana y tarde) sin que se superpongan entre sí.
- [ ] CA-2: un turno que excede el fin de la franja se rechaza.
**Orden**: 3
**Depende de**: US-092
**Reglas**: RN-AG-04

### US-003 — Bloqueos puntuales
**Como** odontólogo **quiero** bloquear días u horas (vacaciones, feriados, ausencias) **para** que no se reserven turnos en esos momentos.
- [ ] CA-1: el bloqueo puede ser del profesional, del sillón o de todo el consultorio.
- [ ] CA-2: al crear un bloqueo sobre turnos activos, el sistema lista los afectados.
**Orden**: 3
**Depende de**: US-092
**Reglas**: RN-AG-04b

### US-004 — Sillón como recurso
**Como** odontólogo **quiero** que el consultorio tenga un sillón por defecto **para** que la agenda controle su ocupación sin configuración extra.
- [ ] CA-1: el seed crea "Sillón 1"; todo turno sin sillón explícito se asigna a él.
- [ ] CA-2: el modelo admite agregar más sillones (la UI multi-sillón es Fase 2).
**Orden**: 2
**Depende de**: Ninguna
**Reglas**: RN-AG-06, RN-AG-07

### US-005 — Reglas configurables
**Como** odontólogo **quiero** ajustar antelaciones, horizonte, aprobación de nuevos y seña **para** adaptar el sistema a mi forma de trabajo.
- [ ] CA-1: la antelación de cancelación solo acepta valores entre 24 y 48 h.
- [ ] CA-2: todos los valores arrancan con los defaults propuestos.
**Orden**: 5
**Depende de**: US-092
**Reglas**: RN-TD-01, RN-TD-02, RN-TD-03, RN-TD-05, RN-SP-01

## Épica 2: Gestión de turnos (núcleo)

### US-010 — Crear turno sin solapamientos por profesional y por sillón ⭐ (change candidato de la consigna)
**Como** recepcionista (o el propio odontólogo) **quiero** crear un turno para un paciente, prestación, profesional y sillón **para** agendarlo sin superponerlo con otro.

**Escenarios con ID estable** (decisión del autor 2026-10-03; reemplazan a los antiguos CA-1..CA-8). Cada escenario del primer change (E1..E7 y E12) tiene **un test**:

| ID | Escenario | ¿Entra en el primer change? |
|---|---|---|
| E1 | **Feliz**: hueco libre; el turno se crea `reservado` con `fin = inicio + duración de la prestación` (RN-AG-02) | **Sí** |
| E2 | **Error de negocio (profesional)**: el profesional tiene un turno activo que se superpone; se rechaza con `RN-AG-05` | **Sí** |
| E3 | **Error de negocio (sillón)**: el sillón tiene un turno activo que se superpone (aunque sea de otro profesional); se rechaza con `RN-AG-08` | **Sí** |
| E4 | **Doble conflicto**: el turno choca con el profesional y con el sillón a la vez; se informan **los dos** errores (`RN-AG-05` y `RN-AG-08`) | **Sí** |
| E5 | **Borde contiguo**: un turno que empieza exactamente cuando termina otro se acepta (RN-AG-09) | **Sí** |
| E6 | **Estado no activo**: un turno cancelado, vencido, atendido o ausente no bloquea el horario (RN-AG-10) | **Sí** |
| E7 | **Borde de un minuto**: un solapamiento de un minuto se rechaza | **Sí** |
| E8 | Intervalo inválido (`inicio >= fin`, naive o fuera de UTC) se rechaza (RN-AG-10d, RN-GL-01) | **No como escenario del spec**: lo cubre un test unitario del value object `Intervalo` (decisión del autor 2026-10-03) |
| E9 | La creación queda registrada en el historial (antes CA-7; RN-AG-11) | **No: fuera del primer change; change siguiente** (decisión del autor 2026-10-03) |
| E10 | Un turno fuera del horario o sobre un bloqueo se rechaza (RN-AG-04/04b; antes CA-8) | **No** (decisión del autor 2026-10-02, P-10) |
| E11 | Dos reservas concurrentes del mismo hueco: solo una gana (RN-AG-10c) | **No** (no verificable con SQLite; perfil PostgreSQL posterior, decisión del autor 2026-10-03) |
| E12 | **Recurso no encontrado**: prestación, paciente, profesional o sillón inexistente o inactivo se rechaza con `RN-GL-04` (RN-AG-07); en HTTP, `422` | **Sí** (decisión del autor 2026-10-03; código y status propuestos por el agente, SU-08) |

- **Nota del orden**: US-010 es el change de la consigna y el hito de entrega. Depende conceptualmente de US-001 y US-004, pero va primero porque este change crea el subconjunto mínimo (prestación y sillón por seed); US-001 y US-004 agregan después la gestión (decisión del autor 2026-10-03).
- **Estado inicial** del turno en el primer change: `reservado` (decisión del autor 2026-10-03; `pendiente_sena` depende de la seña, fuera del primer change).
- **Endpoint:** el primer change expone `POST /turnos` (FastAPI) para probarlo desde Swagger (`/docs`), **sin autenticación** (límite conocido, decisión del autor 2026-10-03, DD-14); se protege con JWT en el change de usuarios y acceso (US-092). Sin interfaz gráfica.
**Orden**: 1
**Depende de**: Ninguna (conceptualmente usa US-001 y US-004; ver nota del orden). E10 dependería además de US-002 y US-003
**Reglas**: RN-AG-02, RN-AG-05, RN-AG-06, RN-AG-08, RN-AG-09, RN-AG-10, RN-AG-10b (reprogramar: fuera del primer change), RN-AG-10c, RN-AG-10d, RN-AG-11 (historial: **fuera del primer change**), RN-GL-01, RN-GL-02, RN-GL-04

### US-011 — Agenda del día
**Como** odontólogo **quiero** ver los turnos del día con color por prestación y estado **para** organizar la atención.
- [ ] CA-1: se listan los turnos del profesional ordenados por inicio, con paciente, prestación y estado.
**Orden**: 4
**Depende de**: US-010, US-092
**Reglas**: RN-AG-01

### US-012 — Reprogramar turno (panel)
**Como** recepcionista **quiero** mover un turno a otro horario **para** acomodar cambios sin perder el historial.
- [ ] CA-1: se valida como un turno nuevo, excluyéndose a sí mismo.
- [ ] CA-2: el historial guarda el horario anterior y el nuevo.
**Orden**: 4
**Depende de**: US-010, US-015, US-092
**Reglas**: RN-AG-10b, RN-AG-11

### US-013 — Cancelar turno (panel) y liberar horario
**Como** recepcionista **quiero** cancelar un turno **para** liberar el horario y ofrecerlo a la lista de espera.
- [ ] CA-1: el turno pasa a `cancelado_profesional` o `cancelado_paciente` según quién lo pidió.
- [ ] CA-2: el horario queda libre y se dispara la búsqueda en la lista de espera.
- [ ] CA-3: si había seña y cancela el odontólogo, la seña se marca para devolución.
**Orden**: 4
**Depende de**: US-010, US-015, US-092 (CA-2 se completa con US-040; CA-3 con US-051)
**Reglas**: RN-AG-10, RN-LE-01, RN-SP-05

### US-014 — Marcar atendido / ausente
**Como** odontólogo o recepcionista **quiero** marcar si el paciente asistió **para** medir el ausentismo.
*(Criterios propuestos por el agente, 2026-10-03; a revisar por el autor.)*
- [ ] CA-1: el odontólogo y la recepcionista pueden marcar un turno como `atendido` o `ausente` (RN-AG-13, decisión del autor 2026-10-03).
- [ ] CA-2: solo desde `reservado` o `confirmado`; al marcarlo, el turno deja de ser activo y libera el horario (RN-AG-12, RN-AG-10).
- [ ] CA-3 (error): si el turno está en otro estado (por ejemplo `cancelado_paciente`, `vencido` o `pendiente_sena`), se rechaza con el error de dominio `RN-AG-12` y el turno no cambia.
- [ ] CA-4: el cambio queda en el historial con quién lo hizo y cuándo (RN-AG-11).
- [ ] CA-5: si el turno queda `ausente` y tiene seña acreditada, la seña pasa a `retenida` (RN-SP-04 (a)); este criterio se completa con US-051.
**Orden**: 4
**Depende de**: US-010, US-015, US-092
**Reglas**: RN-AG-10, RN-AG-11, RN-AG-12, RN-AG-13, RN-SP-04

### US-015 — Historial de cambios
**Como** dueño **quiero** ver quién cambió qué y cuándo en cada turno **para** tener trazabilidad.
- [ ] CA-1: el historial es de solo lectura y no puede editarse.
**Orden**: 2
**Depende de**: US-010
**Reglas**: RN-AG-11

## Épica 3: Reserva y autogestión del paciente

### US-020 — Reserva online 24/7 por link (CU-01)
**Como** paciente **quiero** elegir prestación y horario desde el celular **para** sacar turno en menos de 30 segundos sin depender del horario de atención.
- [ ] CA-1: solo se muestran huecos que respetan horario, bloqueos, solapamientos, horizonte (60 días) y antelación mínima (2 h).
- [ ] CA-2: debo aceptar el consentimiento de datos para confirmar.
- [ ] CA-2b: no necesito cuenta; ingreso mi teléfono de WhatsApp (obligatorio) y, opcionalmente, DNI y email; gestiono el turno por token (DD-11, SU-03).
- [ ] CA-3: si soy paciente nuevo y la aprobación manual está activa, el turno queda `pendiente_aprobacion`.
- [ ] CA-4: si dos personas reservan el mismo hueco a la vez, solo una lo obtiene.
**Orden**: 5
**Depende de**: US-001, US-002, US-003, US-005, US-010, US-070; dependencia técnica: change de infraestructura con PostgreSQL (concurrencia, RN-AG-10c / E11)
**Reglas**: RN-TD-01, RN-TD-02, RN-TD-05, RN-TD-06, RN-AG-10c, RN-PR-02

### US-021 — Sin horarios: lista de espera (CU-06)
**Como** paciente **quiero** anotarme en lista de espera cuando no hay horarios **para** que me avisen si se libera uno.
*(Criterios propuestos por el agente, 2026-10-03; a revisar por el autor.)*
- [ ] CA-1: cuando la disponibilidad no devuelve huecos en el rango pedido, la reserva pública ofrece anotarse en la lista de espera (RN-TD-07, Flujo 2).
- [ ] CA-2 (error): para anotarse el paciente debe aceptar el consentimiento de datos; sin aceptarlo no se crea la entrada (RN-LE-05, RN-PR-02).
- [ ] CA-3: la entrada se crea en estado `activa` con el paciente (teléfono de WhatsApp obligatorio, DNI opcional, SU-03), la prestación (opcional) y las preferencias de días y franjas; su `creada_en` define el orden FIFO (RN-LE-02). No requiere cuenta ni autenticación (`POST /public/{slug}/lista-espera`).
- [ ] CA-4: el paciente puede retirarse desde su link y la entrada pasa a `retirada` (RN-LE-06 (a)).
- [ ] CA-5: el consultorio puede retirar la entrada desde el panel y pasa a `retirada` (RN-LE-06 (b)).
**Orden**: 6
**Depende de**: US-020, US-070, US-092
**Reglas**: RN-TD-07, RN-LE-01, RN-LE-02, RN-LE-05, RN-LE-06

### US-022 — Cancelar o reprogramar por el paciente (CU-05)
**Como** paciente **quiero** cancelar o reprogramar desde el link del turno **para** liberar el horario con anticipación.
- [ ] CA-1: permitido hasta 24 h antes (configurable 24-48); después, el link indica contactar al consultorio.
- [ ] CA-2: la reprogramación aplica las mismas reglas que una reserva.
**Orden**: 5
**Depende de**: US-005, US-010, US-015, US-020
**Reglas**: RN-TD-03, RN-TD-04, RN-TD-08, RN-SP-04, RN-SP-06

## Épica 4: Recordatorio y confirmación por WhatsApp (CU-02)

### US-030 — Recordatorio 24 h antes
**Como** odontólogo **quiero** que el sistema recuerde el turno 24 h antes **para** reducir ausencias.
- [ ] CA-1 (`wa.me`, v1): el panel muestra la lista de recordatorios del día con el enlace listo para enviar; el odontólogo lo envía desde su WhatsApp y marca el mensaje como enviado.
- [ ] CA-2 (Cloud API, **Fase 2**, posterior a la v1): un adaptador sobre el puerto de mensajería envía el mensaje con plantilla y link de gestión (decisión del autor 2026-10-03, DD-06).
**Orden**: 6
**Depende de**: US-005, US-010, US-092
**Reglas**: RN-WA-01, RN-WA-03

### US-031 — Confirmación por el link de gestión
**Como** odontólogo **quiero** registrar quién confirmó **para** saber qué huecos podrían liberarse.
- [ ] CA-1: el paciente confirma desde el link de gestión del turno; la confirmación cambia el estado a `confirmado` y queda en el historial (RN-WA-02).
- [ ] CA-2 (**Fase 2**): confirmar o cancelar respondiendo por el chat (Cloud API) queda fuera de la v1.
**Orden**: 6
**Depende de**: US-015, US-020, US-030
**Reglas**: RN-WA-02, RN-AG-11

## Épica 5: Lista de espera (CU-06) — diferenciador

### US-040 — Ofrecer hueco liberado
**Como** odontólogo **quiero** que un hueco liberado se ofrezca automáticamente a quien espera **para** convertir cancelaciones en turnos.
- [ ] CA-1: se ofrece por orden de alta a la primera entrada compatible.
- [ ] CA-2: la oferta vence (2 horas por defecto, configurable, RN-LE-03); si vence o se rechaza, pasa al siguiente.
- [ ] CA-3: al aceptar, se revalida el solapamiento.
**Orden**: 6
**Depende de**: US-005, US-013, US-021, US-030, US-092
**Reglas**: RN-LE-01 a RN-LE-04

## Épica 6: Seña con Mercado Pago (CU-04)

### US-050 — Pagar seña al reservar
**Como** paciente **quiero** pagar la seña al reservar **para** asegurar mi turno.
- [ ] CA-1: se genera una preferencia de Checkout Pro en la cuenta del odontólogo (credenciales de prueba).
- [ ] CA-2: el webhook acreditado pasa el turno a `reservado`; notificaciones duplicadas no acreditan dos veces.
- [ ] CA-3: si no se paga a tiempo (30 minutos por defecto, configurable, RN-SP-03), el turno vence y libera el horario.
**Orden**: 7
**Depende de**: US-005, US-020
**Reglas**: RN-SP-01, RN-SP-02, RN-SP-03, RN-SP-08

### US-051 — Retención / devolución de seña (**sujeta a revisión legal**)
**Como** odontólogo **quiero** que la seña quede retenida o devuelta según quién cancela y cuándo **para** que el prototipo refleje las reglas de seña del consultorio.
*(Criterios propuestos por el agente, 2026-10-03; a revisar por el autor.)* Describen el comportamiento del **prototipo con credenciales de prueba de Mercado Pago**; no afirman validez legal (P-01, fuera del alcance académico).
- [ ] CA-1: si el paciente queda `ausente`, la seña acreditada pasa a `retenida` (RN-SP-04 (a), decisión del autor 2026-10-03).
- [ ] CA-2: si el consultorio carga desde el panel una cancelación como cancelación del paciente fuera de plazo (`ahora > inicio − antelacion_cancelacion_horas`), la seña pasa a `retenida` (RN-SP-04 (b), RN-TD-03).
- [ ] CA-3: si el paciente cancela dentro de plazo, o cancela el odontólogo, la seña se devuelve y pasa a `devuelta` (RN-SP-06, RN-SP-05).
- [ ] CA-4 (borde): no hay retención parcial: la seña se retiene entera o se devuelve entera (RN-SP-04).
- [ ] CA-5: en el prototipo la devolución solo se registra con el estado `devuelta`; no se ejecuta una devolución real por la API de Mercado Pago (`11_integraciones_whatsapp_y_mercadopago.md`).
**Orden**: 7
**Depende de**: US-013, US-014, US-022, US-050
**Reglas**: RN-SP-04, RN-SP-05, RN-SP-06

## Épica 7: Ficha clínica mínima, presupuestos y pagos (CU-03)

### US-060 — Ficha del paciente
**Como** odontólogo **quiero** abrir la ficha en la consulta y registrar anamnesis y evolución **para** no depender de la carpeta de papel.
*(Criterios propuestos por el agente, 2026-10-03; a revisar por el autor.)*
- [ ] CA-1: la ficha contiene los datos del paciente, la anamnesis y la evolución en texto (RN-FC-01); una evolución puede vincularse a un turno (Flujo 7).
- [ ] CA-2 (error): solo el rol `odontologo` lee y escribe los datos clínicos; la recepcionista que los pide recibe `403` (RN-FC-02, RN-AU-05).
- [ ] CA-3 (borde): la anamnesis tiene los campos `alergias`, `medicacion`, `enfermedades` y `observaciones`, todos opcionales; se puede guardar con todos vacíos (RN-FC-01, decisión del autor 2026-10-03).
- [ ] CA-4: la anamnesis se versiona: cada cambio crea una versión nueva (`version` + 1) sin sobrescribir la anterior (RN-FC-03).
- [ ] CA-5: la evolución es solo inserción; una corrección es una entrada nueva que referencia a la anterior y no hay borrado físico (RN-FC-03, `Evolucion.corrige_a_id`).
**Orden**: 8
**Depende de**: US-010, US-091, US-092 (roles: la recepcionista no ve datos clínicos, RN-FC-02)
**Reglas**: RN-FC-01, RN-FC-02, RN-FC-03

### US-061 — Presupuesto simple
**Como** odontólogo **quiero** armar un presupuesto simple para un paciente **para** informarle el costo de los tratamientos.
*(Criterios propuestos por el agente, 2026-10-03; a revisar por el autor.)*
- [ ] CA-1: el presupuesto tiene ítems con descripción, cantidad y precio unitario, y su total se calcula a partir de los ítems; sin códigos ni valores de obras sociales (RN-FC-04).
- [ ] CA-2: el presupuesto nace `borrador`; el odontólogo lo pasa a `entregado` y luego a `aceptado` o `rechazado` (RN-FC-05).
- [ ] CA-3 (error): `aceptado` y `rechazado` son finales; cualquier cambio posterior, o un salto no previsto (por ejemplo, de `borrador` a `aceptado`), se rechaza con el error de dominio `RN-FC-05`.
- [ ] CA-4 (error): solo el odontólogo cambia el estado (RN-FC-05).
- [ ] CA-5 (error): se rechaza un ítem con cantidad menor o igual a 0 o con precio unitario negativo (`CHECK` de `04_modelo_de_datos.md`).
**Orden**: 8
**Depende de**: US-001, US-060
**Reglas**: RN-FC-04, RN-FC-05

### US-062 — Registro de pago simple
**Como** odontólogo o recepcionista **quiero** registrar un pago (pagado sí o no, monto y medio) **para** llevar el control de cobros sin una caja completa.
*(Criterios propuestos por el agente, 2026-10-03; a revisar por el autor.)*
- [ ] CA-1: el registro guarda pagado sí o no, monto y medio (`efectivo`, `transferencia`, `mercado_pago`, `tarjeta` u `otro`); no emite comprobante fiscal (RN-SP-07).
- [ ] CA-2: el pago se asocia al paciente y, opcionalmente, a un presupuesto o a un turno (decisión del autor 2026-10-03).
- [ ] CA-3: se admiten pagos parciales: un cobro en cuotas son varios registros (RN-SP-09).
- [ ] CA-4: un registro no se edita; se corrige con un registro nuevo que referencia al anterior (`corrige_a_id`) y lo anula, y el anulado no cuenta en los totales (RN-SP-09).
- [ ] CA-5 (error): se rechaza un monto menor o igual a 0 (`CHECK` de `04_modelo_de_datos.md`).
**Orden**: 8
**Depende de**: US-060 (US-061 y US-010 no son dependencia: el pago puede asociarse a un presupuesto o a un turno, opcionalmente)
**Reglas**: RN-SP-07, RN-SP-09

## Épica 8: Privacidad y consentimiento (CU-07)

### US-070 — Consentimiento informado de datos
**Como** paciente **quiero** saber qué datos de salud se guardan y aceptar su tratamiento **para** reservar con conocimiento de cómo se usan mis datos.
*(Criterios propuestos por el agente, 2026-10-03; a revisar por el autor.)*
- [ ] CA-1 (error): para reservar, el paciente debe aceptar el texto de consentimiento; sin aceptarlo, la reserva no se confirma (RN-PR-02, Flujo 2).
- [ ] CA-2: al aceptar se registra la versión del texto, la fecha-hora de aceptación y el origen (`link_publico` o `panel`) (RN-PR-02, `04_modelo_de_datos.md`).
- [ ] CA-3: el texto es un borrador marcado «no validado legalmente» (RN-PR-02, P-03 cerrada como fuera del alcance académico).
- [ ] CA-4 (borde): si cambia la versión del texto, se vuelve a pedir en la siguiente reserva del paciente (RN-PR-02, decisión del autor 2026-10-03).
- [ ] CA-5: el consentimiento también se exige para anotarse en la lista de espera (RN-LE-05).
**Orden**: 5
**Depende de**: Ninguna
**Reglas**: RN-PR-02, RN-PR-03, RN-LE-05

### Regla permanente: datos ficticios (RN-PR-01)
Esto **no es una historia implementable**: es una **regla dura del proyecto**, aplicable **desde el primer change**. Se registra en las reglas del agente (`CLAUDE.md`/`AGENTS.md`) y **no genera un change propio** (decisión del autor 2026-10-03). Seeds, tests, ejemplos y demos usan solo datos inventados (RN-PR-01 en `05_reglas_de_negocio.md`).

## Épica 9: Control del dueño

### US-080 — Reportes de ocupación, ausentismo y cobros pendientes (**extensión fuera del MVP de la sección D del informe**)
**Como** dueño **quiero** ver ocupación, ausentismo y señas/pagos pendientes **para** controlar el consultorio.
**Alcance**: **extensión fuera del MVP de la sección D del informe** (el informe, D.3, no la lista entre los imprescindibles). Queda en la v1 como **último orden** (decisión del autor 2026-10-03). El roadmap debe marcarla como extensión.
*(Criterios propuestos por el agente, 2026-10-03; a revisar por el autor.)*
- [ ] CA-1: la ocupación es los minutos con turno (estados activos y `atendido`) sobre los minutos de horario disponible (horario recurrente menos bloqueos) (RN-RP-01).
- [ ] CA-2: el ausentismo es los turnos `ausente` sobre los turnos `atendido` más `ausente` (RN-RP-02).
- [ ] CA-3: ambos reportes se calculan con filtro por rango de fechas (RN-RP-03).
- [ ] CA-4: el reporte de cobros pendientes lista las señas en estado `pendiente` y los registros de pago con `pagado` falso, sin contar los registros anulados (`04_modelo_de_datos.md`, RN-SP-09).
- [ ] CA-5: los reportes son de solo lectura, los ven los roles `dueno` y `odontologo` (`03_actores_y_roles.md`) y no incluyen datos clínicos (RN-FC-02, RN-PR-03).
**Orden**: 9
**Depende de**: US-002, US-003, US-010, US-014, US-050, US-062, US-092
**Reglas**: RN-RP-01, RN-RP-02, RN-RP-03, RN-FC-02, RN-PR-03

## Épica 10: Usuarios y acceso

Decisión del autor 2026-10-03 (D1/D2): el panel se protege con JWT en esta épica (orden 3); hasta entonces `POST /turnos` del primer change y los endpoints de orden 1 y 2 van sin autenticación. Roles (`odontologo`, `recepcionista`, `dueno`) y matriz de permisos en `03_actores_y_roles.md`. Los detalles (duración de tokens, refresh, hash) son una propuesta aceptada por el autor (2026-10-03, SU-09), que se revisa en el design del change.

### US-090 — Iniciar sesión
**Como** odontólogo o recepcionista **quiero** iniciar sesión con email y contraseña **para** acceder al panel.
- [ ] CA-1: con credenciales válidas, `POST /auth/login` devuelve un access token JWT y un refresh token.
- [ ] CA-2: con email inexistente o contraseña incorrecta, responde `401` con el mismo mensaje genérico en ambos casos (RN-AU-04).
- [ ] CA-3: un usuario inactivo no puede iniciar sesión.
- [ ] CA-4 (propuesta aceptada por el autor 2026-10-03, SU-09): el access token dura 15 minutos y el refresh token 7 días.
**Orden**: 3
**Depende de**: Ninguna
**Reglas**: RN-AU-01, RN-AU-03, RN-AU-04

### US-091 — Roles odontólogo, recepcionista y dueño
**Como** odontólogo **quiero** que cada usuario tenga uno o más roles **para** que cada uno vea solo lo que le corresponde.
- [ ] CA-1: un usuario puede tener varios roles y sus permisos son la unión de los roles (el odontólogo independiente tiene `odontologo` + `dueno`).
- [ ] CA-2: la recepcionista ve los datos administrativos del paciente pero no la ficha clínica (anamnesis, evolución) (RN-FC-02).
- [ ] CA-3: un rol insuficiente recibe `403` en el endpoint protegido.
**Orden**: 3
**Depende de**: US-090
**Reglas**: RN-AU-02, RN-AU-05, RN-FC-02

### US-092 — Proteger los endpoints del panel con JWT
**Como** odontólogo **quiero** que los endpoints del panel exijan un token válido **para** que nadie sin sesión modifique la agenda.
- [ ] CA-1: un endpoint del panel sin token o con token vencido responde `401`.
- [ ] CA-2: `POST /turnos` (que en el primer change va sin autenticación) y los demás endpoints de panel creados antes de esta épica (gestión de prestaciones y de sillón, historial: US-001, US-004, US-015) pasan a exigir JWT con el rol que corresponda (por ejemplo, `odontologo` o `recepcionista` para `POST /turnos`).
- [ ] CA-3: las rutas públicas de `03_actores_y_roles.md` siguen sin autenticación.
**Orden**: 3
**Depende de**: US-090, US-091
**Reglas**: RN-AU-01, RN-AU-05

### US-093 — Gestión de usuarios del consultorio
**Como** odontólogo **quiero** crear, desactivar y asignar roles a los usuarios del consultorio **para** dar acceso a la recepcionista.
- [ ] CA-1: el odontólogo crea usuarios y les asigna roles; la recepcionista no puede.
- [ ] CA-2: el email es único.
- [ ] CA-3: desactivar un usuario impide su próximo inicio de sesión; no se borra.
**Orden**: 3
**Depende de**: US-090, US-091
**Reglas**: RN-AU-02, RN-AU-05

### US-094 — Renovar la sesión (propuesta aceptada por el autor 2026-10-03)
**Como** usuario del panel **quiero** renovar mi sesión sin volver a ingresar la contraseña **para** no ser interrumpido durante la jornada.
- [ ] CA-1: `POST /auth/refresh` con un refresh token válido devuelve un nuevo access token.
- [ ] CA-2: un refresh token vencido o inválido responde `401`.
**Orden**: 3
**Depende de**: US-090
**Reglas**: RN-AU-03

## Épicas posteriores (no implementar en v1)

| Épica | Versión |
|---|---|
| Odontograma completo | v1.1 |
| Obras sociales (códigos y valores manuales) | v1.1 |
| Imágenes y radiografías | v2 |
| ARCA / facturación electrónica | v2 |
| Caja completa con arqueo | v2 |
| Agenda multi-profesional y multi-sillón en UI (CU-08) | Fase 2 |
| Sobreturnos (prohibidos en la v1, P-11) | Fase 2 |
| Split de pagos 1:N en Mercado Pago | Fase 2 |
| WhatsApp Cloud API oficial (adaptador sobre el puerto de mensajería; incluye la respuesta por chat) | Fase 2 |
| WhatsApp API oficial en producción (verificación de empresa, plantillas, costo) | Posterior |
| Google Calendar, API pública | Posterior |
