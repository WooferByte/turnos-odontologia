# Reglas de Negocio

Cada regla tiene un código único `RN-{DOMINIO}-{NN}`. Origen de los valores: **decisiones de diseño del autor** (informe D.4 y Discovery punto 7). **Los valores por defecto son propuestos, no estándares de mercado verificados**, y son configurables por el odontólogo salvo que se indique "fija".

Dominios: **AG** agenda · **TD** turnos digitales (reserva, confirmación, cancelación, reprogramación), con subdominios **WA** (WhatsApp) y **LE** (lista de espera) · **SP** seña y pagos · **FC** ficha clínica · **PR** privacidad · **AU** autenticación · **GL** globales.

## Dominio: Agenda (RN-AG)

### Prestaciones y duración
- **RN-AG-01** (configurable): el odontólogo define una **tabla de prestaciones** con nombre, **duración por defecto en minutos** y color en la agenda. Duración > 0 y múltiplo de la granularidad de agenda.
- **RN-AG-02** (fija): la duración de un turno es la de su prestación al momento de crearlo, salvo que quien agenda desde el panel la modifique explícitamente. El turno persiste su `fin = inicio + duración`; cambiar la duración de la prestación **no altera turnos ya creados**.
- **RN-AG-03** (fija): el paciente que reserva por link no puede modificar la duración; solo elige prestación y horario.

### Horario recurrente y bloqueos
- **RN-AG-04** (configurable): cada profesional tiene un **horario recurrente semanal** (días y franjas). Un turno solo puede crearse si `[inicio, fin)` cae **completo** dentro de una franja vigente de ese día. **Nota (decisión del autor 2026-10-02):** la excepción de horario fue evaluada y descartada para la v1. Si el odontólogo necesita atender fuera de su horario habitual, debe modificar el horario recurrente para esa fecha (la Fase 2 puede evaluar una excepción puntual). **Alcance del primer change (P-10, decisión del autor 2026-10-02):** el primer change **no valida** esta regla ni RN-AG-04b; solo cubre solapamientos por profesional y por sillón con estados activos.
- **RN-AG-04b** (configurable): los **bloqueos puntuales** (vacaciones, feriados, ausencias) prevalecen sobre el horario recurrente. Un turno no puede intersecar un bloqueo del profesional, de su sillón o de todo el consultorio. Crear un bloqueo sobre turnos activos existentes **no los cancela automáticamente**: el sistema lista los turnos afectados para que el odontólogo los reprograme o cancele (**Suposición**).

### Sillones / boxes (recurso)
- **RN-AG-06** (fija): el **sillón/box es un recurso del dominio**. Todo turno ocupa exactamente **un profesional y un sillón**. En el MVP existe **un único sillón (valor por defecto 1)** y todo turno se asigna a él si no se indica otro.
- **RN-AG-07** (fija): un sillón inactivo no admite turnos nuevos.

### Prevención de solapamientos
> **Sobreturnos prohibidos en la v1 (P-11, decisión del autor 2026-10-02).** No existe acción de panel que permita superponer turnos intencionalmente. Queda como **Fase 2**. Es una decisión de alcance, no un desconocimiento del mercado: Bilog, Dentalink y Naclix hoy ofrecen sobreturnos (informe C.3).

- **RN-AG-05** (fija): **un profesional no puede tener dos turnos activos superpuestos.**
- **RN-AG-08** (fija): **un sillón no puede tener dos turnos activos a la vez.** RN-AG-05 y RN-AG-08 se evalúan **ambas e independientemente**: basta que falle una para rechazar el turno, y el error indica cuál recurso está ocupado (profesional, sillón o ambos).
- **RN-AG-09** (fija) — **definición de solapamiento**: los turnos son intervalos **semiabiertos `[inicio, fin)`**. Dos turnos A y B se solapan si y solo si `A.inicio < B.fin` **y** `B.inicio < A.fin`. Casos borde:
  - Un turno que **empieza exactamente cuando termina otro** (A 10:00-10:30, B 10:30-11:00) **es válido**: no hay solapamiento.
  - Un turno que termina exactamente cuando empieza otro es válido por la misma regla.
  - Solapamiento parcial de un minuto (A 10:00-10:30, B 10:29-11:00) **se rechaza**.
  - Un turno contenido en otro, o que contiene a otro, **se rechaza**.
  - Mismo inicio y fin que otro turno del mismo profesional o sillón **se rechaza**.
  - Turnos superpuestos en **distinto profesional y distinto sillón** son válidos (aplica en Fase 2).
- **RN-AG-10** (fija): solo cuentan para el solapamiento los turnos en **estado activo** (`pendiente_aprobacion`, `pendiente_sena`, `reservado`, `confirmado`). Un turno cancelado, vencido, atendido o ausente **libera** el horario.
- **RN-AG-10b** (fija): al **reprogramar**, el turno se excluye a sí mismo de la verificación de solapamientos.
- **RN-AG-10c** (fija): la verificación de solapamiento debe ser **atómica** frente a reservas concurrentes (dos pacientes reservando el mismo hueco a la vez: uno solo gana). Ver DD-04.
- **RN-AG-10d** (fija): `inicio < fin`; no se aceptan turnos de duración cero o negativa ni turnos que crucen la medianoche (**Suposición**).

### Trazabilidad
- **RN-AG-11** (fija): **todo cambio de turno queda registrado** (creación, reprogramación, confirmación, cancelación, cambio de estado, acreditación de seña) con quién (usuario, paciente, sistema o webhook), cuándo y qué cambió (antes/después). El historial es **inmutable** (solo inserción).

## Dominio: Turnos digitales (RN-TD)

- **RN-TD-01** (configurable, default **60 días**): el paciente puede reservar hasta 60 días hacia adelante.
- **RN-TD-02** (configurable, default propuesto **2 horas**, confirmado por el autor el 2026-10-02): antelación mínima para reservar online. El informe D.4 indica que no hay valor de mercado de referencia.
- **RN-TD-03** (configurable, default **24 horas**, rango **24-48**): el paciente puede **cancelar o reprogramar** sin penalidad hasta 24 h antes del inicio del turno. Fuera de ese plazo, la acción online queda bloqueada y se indica contactar al consultorio (confirmado por el autor el 2026-10-02, P-12; **Suposición:** el odontólogo sí puede cancelar/reprogramar en cualquier momento desde el panel).
- **RN-TD-04** (fija): la reprogramación por el paciente aplica las mismas reglas que una reserva nueva (RN-AG-04 a RN-AG-10, RN-TD-01, RN-TD-02) y conserva la seña ya acreditada (**Suposición**).
- **RN-TD-05** (configurable, default **reserva directa**): el **paciente nuevo reserva directo**; el odontólogo puede activar la **aprobación manual opcional**, en cuyo caso el turno queda `pendiente_aprobacion` (ocupando el horario) hasta que lo apruebe o rechace.
- **RN-TD-06** (fija): la reserva pública solo ofrece prestaciones marcadas como `reservable_online` y huecos que cumplen horario, bloqueos y solapamientos.
- **RN-TD-07** (fija): si **no hay horarios disponibles** en el rango pedido, la reserva pública ofrece anotarse en la **lista de espera** (informe D.3, punto 5).
- **RN-TD-08** (fija): toda acción del paciente sobre su turno se hace con un **token de gestión firmado** enviado por WhatsApp; el token identifica un único turno. El paciente **no tiene cuenta** (DD-11). En la reserva pública el **teléfono de WhatsApp es obligatorio** y el **DNI es opcional** (decisión del autor 2026-10-02, SU-03).

### Subdominio WhatsApp (RN-WA)
- **RN-WA-01** (configurable, default **24 h antes**): el sistema envía un recordatorio del turno.
- **RN-WA-02** (fija): con **Cloud API**, la respuesta del paciente (confirmar / cancelar) cambia el estado del turno y queda en el historial. Con **`wa.me`**, el sistema genera el mensaje con el link de gestión y el odontólogo lo envía; la confirmación llega por el link.
- **RN-WA-03** (fija): en el prototipo solo se envían mensajes a **números de prueba** con datos ficticios.

### Subdominio Lista de espera (RN-LE)
- **RN-LE-01** (fija): cuando se libera un hueco (cancelación, vencimiento de seña, reprogramación), el sistema identifica entradas activas compatibles (prestación cuya duración entra en el hueco y preferencias).
- **RN-LE-02** (**Suposición:** orden FIFO por fecha de alta): el hueco se ofrece a la primera entrada compatible.
- **RN-LE-03** (**Suposición:** configurable; sin valor de fuente): la oferta vence tras un plazo; si vence o se rechaza, se ofrece al siguiente.
- **RN-LE-04** (fija): aceptar una oferta crea el turno **revalidando** solapamientos (el hueco pudo ocuparse mientras tanto); si ya no está libre, la oferta se informa como no disponible.

## Dominio: Seña y pagos (RN-SP)

> **Sujeto a revisión legal (Ley 24.240 y otras).** Las reglas de retención y devolución **no se implementan con datos ni dinero reales**; en el prototipo se usan solo credenciales de prueba de Mercado Pago. Ver `10_preguntas_abiertas.md`.

- **RN-SP-01** (configurable): el odontólogo decide si exige seña y su monto. La seña se cobra con **Mercado Pago Checkout Pro** en la **cuenta única del odontólogo** (split 1:N = Fase 2).
- **RN-SP-02** (fija): si se exige seña, el turno nace `pendiente_sena` y ocupa el horario; pasa a `reservado` cuando el webhook de Mercado Pago confirma el pago acreditado.
- **RN-SP-03** (**Suposición:** configurable; sin valor de fuente): si la seña no se acredita en el plazo de vencimiento, el turno pasa a `vencido` y libera el horario (dispara RN-LE-01).
- **RN-SP-04** (configurable, **sujeta a revisión legal**): si el paciente cancela **fuera de plazo** (RN-TD-03), la seña **se retiene**.
- **RN-SP-05** (configurable, **sujeta a revisión legal**): si **cancela el odontólogo**, la seña se **devuelve al 100%**.
- **RN-SP-06** (confirmada por el autor el 2026-10-02): si el paciente cancela **dentro de plazo**, la seña se devuelve (la fuente no lo dice explícitamente; se infiere de "ventana de cancelación sin penalidad"). Sigue sujeta a revisión legal (P-01).
- **RN-SP-07** (fija): el **registro de pago simple** guarda pagado sí/no, monto y medio; no emite comprobante fiscal (ARCA es v2).
- **RN-SP-08** (fija): los webhooks de Mercado Pago se procesan de forma **idempotente** (la misma notificación no acredita dos veces).

## Dominio: Ficha clínica (RN-FC)

- **RN-FC-01** (fija): la ficha mínima contiene datos del paciente, **anamnesis** y **evolución en texto**. Odontograma completo = v1.1.
- **RN-FC-02** (fija): solo el rol `odontologo` lee y escribe datos **clínicos** (anamnesis, evolución, odontograma). El rol `recepcionista` ve y gestiona los datos **administrativos** del paciente (identificación, contacto, turnos, pagos), pero **no** los clínicos (decisión del autor 2026-10-02, SU-04).
- **RN-FC-03** (fija): la anamnesis se **versiona** y la evolución es **solo inserción**; no hay borrado físico de datos clínicos (Ley 26.529 como referencia; **no es asesoría legal**).
- **RN-FC-04** (fija): los presupuestos son simples (ítems con descripción, cantidad y precio; total calculado). Sin códigos ni valores de obras sociales en v1.

## Dominio: Privacidad (RN-PR)

- **RN-PR-01** (fija): **los datos de pacientes en seeds, tests, ejemplos y demos son SIEMPRE ficticios.** Nunca se versionan datos reales en el repositorio.
- **RN-PR-02** (fija): para reservar, el paciente debe **aceptar el texto de consentimiento** sobre qué datos de salud se guardan y para qué; se registra versión del texto y fecha (CU-07).
- **RN-PR-03** (fija): los datos de salud son datos sensibles según la **Ley 25.326**; acceso mínimo por rol (RN-FC-02) y transporte cifrado (HTTPS).
- **RN-PR-04** (fija): si alguna vez hubiera **datos reales**, la base debe inscribirse en el Registro Nacional de Bases de Datos de la **AAIP** (art. 21 de la Ley 25.326, según el Discovery). Vigencia del trámite: pregunta abierta.
- **RN-PR-05** (**Suposición**): el paciente puede solicitar la exportación de sus datos (diferenciador de "confianza" del informe C.4); el formato se define en un change posterior.
- **RN-PR-06** (fija): los enlaces públicos no exponen datos clínicos ni datos de otros pacientes; nunca se ponen datos personales en query strings.

## Dominio: Autenticación (RN-AU)

- **RN-AU-01** (fija): el panel requiere JWT; las rutas públicas se limitan a las listadas en `03_actores_y_roles.md`.
- **RN-AU-02** (fija): los permisos se calculan como la unión de los roles del usuario.
- **RN-AU-03** (**Suposición**): el access token tiene vida corta y se renueva con refresh token.

## Excepciones globales (RN-GL)

- **RN-GL-01** (fija): todas las fechas-hora se guardan en UTC con zona; las reglas de horario se evalúan en la zona del consultorio (`America/Argentina/Buenos_Aires`).
- **RN-GL-02** (fija): un rechazo por regla de negocio devuelve un error de dominio con el código RN que lo causó (p. ej. `RN-AG-05` profesional ocupado, `RN-AG-08` sillón ocupado), para que los tests puedan verificarlo.
- **RN-GL-03** (fija): toda regla configurable tiene un valor por defecto, y cambiarla no afecta retroactivamente turnos ya creados.
