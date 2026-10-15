# Flujos Principales

## Flujo 1: Crear turno sin solapamientos (panel) — núcleo del change de la consigna

**Disparador**: la recepcionista u odontólogo agenda un turno.
**Actor**: `recepcionista` / `odontologo`. **En el primer change el endpoint va sin autenticación** (límite conocido, decisión del autor 2026-10-03, DD-14); con el change de usuarios y acceso exige JWT (US-092). **Desde C-07 (`roles-y-proteccion-del-panel`) la excepción ya no vale**: todas las rutas del panel exigen JWT y rol (D214).

**Contrato del primer change:** la firma de la función pura de dominio, del caso de uso, del error de dominio y el mapeo a HTTP están en `08_arquitectura_propuesta.md` (sección «Contrato del primer change»). El primer change entrega el dominio, el caso de uso y el **endpoint `POST /turnos` (FastAPI)**, para probarlo desde Swagger (`/docs`) en el video (decisión del autor 2026-10-03). Sigue sin interfaz gráfica.

**Pasos**:
1. Frontend/cliente envía `POST /turnos` con `paciente_id`, `prestacion_id`, `inicio`, y opcionalmente `profesional_id` y `sillon_id`.
2. *(Fuera del primer change, DD-14)* API valida el JWT y el permiso (RN-AU-01, US-092). En el primer change este paso no existe: el caso de uso no depende de la autenticación.
3. Caso de uso `CrearTurno`, **validación de entrada** (RN-GL-02, D135; se junta todo lo que falle y se informa en un único `422`): verifica que `inicio` sea aware en UTC (RN-GL-01, D128); resuelve defaults: si no vienen, el **único profesional activo** y el **único sillón activo** del consultorio (RN-AG-06, RN-AG-14; si no hay uno solo, `RN-GL-04`); verifica que prestación, profesional y sillón **existan, estén activos y sean del consultorio del profesional**, y que el paciente **exista y sea de ese consultorio** (si no, `RN-GL-04`, E12, informando **todas** las referencias inválidas; D126, D127, D136). Si hubo algún problema, termina acá con los códigos que correspondan (`RN-GL-01`, `RN-GL-04` o los dos) y no evalúa ninguna regla de negocio.
4. **Reglas de negocio, de a una** (RN-GL-02, D135), solo con la entrada válida. Primera: calcula `fin = inicio + duración` de la prestación (RN-AG-02) y el dominio, al construir el `Intervalo`, exige que `inicio` y `fin` caigan en la misma fecha local del consultorio, sin cruzar su medianoche (RN-AG-10d, D63); si falla, se rechaza solo con `RN-AG-10d`. `inicio < fin` se cumple siempre acá, porque la duración es positiva.
5. *(Fuera del primer change, decisión del autor 2026-10-02, P-10)* Dominio valida horario recurrente y bloqueos (RN-AG-04, RN-AG-04b). El primer change solo cubre los solapamientos por profesional y por sillón con estados activos.
6. Dentro de una transacción, el repositorio obtiene los turnos del profesional y del sillón que intersecan `[inicio, fin)`. El **filtro por estado activo** (RN-AG-10) lo aplica el dominio con la constante `ESTADOS_ACTIVOS` (decisión del autor 2026-10-03; así E6 se prueba como función pura).
7. Segunda regla de negocio: el dominio aplica la función pura de solapamiento `a.inicio < b.fin and b.inicio < a.fin` (RN-AG-09) contra ambos conjuntos (RN-AG-05, RN-AG-08) y devuelve **todos** los conflictos encontrados. Es **una sola regla que mira dos recursos**: puede informar uno o dos códigos (E4; RN-GL-02, D135).
8. Si no hay conflicto, persiste el turno en estado `reservado` y hace commit. *(El `EventoTurno(creado)` de RN-AG-11 quedó fuera del primer change por decisión del autor 2026-10-03. **Desde C-03 (2026-10-14, D165):** en este mismo paso, dentro de la misma transacción y justo después de persistir el turno, se inserta el `EventoTurno(creado)` con `actor_tipo = usuario` y `actor_id` vacío hasta C-07 (D159) y `despues` con la foto del turno (D163); si el registro falla, se deshace también el turno. Un rechazo anterior no registra nada.)*
9. Responde `201` con el turno.

```
Cliente → API → CrearTurno → validar entrada ── falla → 422 {codigos: [RN-GL-01 y/o RN-GL-04]}
                            → Dominio(Intervalo) ── cruza la medianoche → 422 {codigos: [RN-AG-10d]}
                            → Repo(turnos del recurso ∩ rango) → DB
                                      ← conflictos? ── sí → 409 {codigos: [RN-AG-05 y/o RN-AG-08]}
                                      ← no → INSERT turno → 201
```

**Casos de error**:
- Profesional ocupado → `409` con `RN-AG-05`.
- Sillón ocupado → `409` con `RN-AG-08`.
- Ambos ocupados → `409` con **los dos códigos** (`RN-AG-05` y `RN-AG-08`) (decisión del autor 2026-10-03); un `Conflicto` por recurso, con el turno existente que empieza primero (D129).
- Fecha sin zona o con desfase distinto de UTC → `422` con `RN-GL-01` (D128).
- Fecha inválida **y** referencias inválidas en la misma petición → **un** `422` con los dos códigos, `RN-GL-01` y `RN-GL-04` (validación de entrada, todo junto; RN-GL-02, D135).
- El turno cruza la medianoche del consultorio → `422` solo con `RN-AG-10d` (regla de negocio; no se evalúa el solapamiento).
- Prestación, profesional o sillón inexistente, inactivo o de otro consultorio, paciente inexistente o de otro consultorio (D136), o sillón / profesional omitido sin un único activo (RN-AG-14) → `422` con `RN-GL-04` («recurso no encontrado»; E12; el error lista **todas** las referencias inválidas, D127), porque la referencia viaja en el cuerpo (un recurso inexistente identificado en la URL daría `404`, con `RN-GL-04` desde C-03: `GET /turnos/999/historial`; D73, D166). Se rechaza antes de evaluar cualquier regla de negocio y no persiste nada.
- Fuera de horario o sobre bloqueo → `422` con `RN-AG-04` / `RN-AG-04b` (fuera del primer change).
- Carrera concurrente → la segunda transacción falla (restricción de exclusión o bloqueo) y se responde `409` (RN-AG-10c; fuera del primer change, E11). En C-02 (2026-10-13, D157): `crear_turno` toma el bloqueo de fila del profesional y después del sillón antes de leer los ocupados, así que la segunda reserva espera, ve el turno confirmado y responde el `409` con los códigos completos sin reintento; la restricción de exclusión queda como última defensa.

**Escenarios del spec (dado/cuando/entonces), con IDs estables** — exigidos por la consigna (feliz, error de negocio, borde). Los **E1..E7 y E12 entran en el primer change** (un test por escenario). La tabla completa E1..E12 está en `06_funcionalidades.md` (US-010); E8 a E11 quedan fuera del spec. Todos los horarios se expresan en UTC.
- **E1 Feliz**: dado un profesional sin turnos de 10:00 a 11:00, cuando creo un turno de 30 min a las 10:00, entonces se crea `reservado` con fin 10:30.
- **E2 Error (profesional)**: dado un turno activo 10:00-10:30 del profesional en otro sillón, cuando creo otro con ese profesional a las 10:15 en un sillón libre, entonces se rechaza solo con `RN-AG-05`.
- **E3 Error (sillón)**: dado un turno activo 10:00-10:30 en el sillón con otro profesional, cuando creo un turno en ese sillón a las 10:00 con un profesional libre, entonces se rechaza solo con `RN-AG-08`.
- **E4 Doble conflicto**: dado un turno activo 10:00-10:30 del mismo profesional y del mismo sillón (el caso normal del MVP, con 1 profesional y 1 sillón), cuando creo otro a las 10:00 con ese profesional y ese sillón, entonces se rechaza con los dos errores, `RN-AG-05` y `RN-AG-08`.
- **E5 Borde contiguo**: dado un turno 10:00-10:30, cuando creo otro a las 10:30, entonces se acepta (y lo mismo si el nuevo termina justo a las 10:00).
- **E6 Estado no activo**: dado un turno cancelado 10:00-10:30 (o vencido, atendido o ausente), cuando creo otro a las 10:00, entonces se acepta.
- **E7 Borde de un minuto**: dado un turno activo 10:00-10:30 del profesional en otro sillón, cuando creo otro con ese profesional a las 10:29, entonces se rechaza con `RN-AG-05` (un solapamiento de un minuto es solapamiento).
- **E12 Recurso no encontrado**: dado que no existe la prestación 999 (o el paciente, el profesional o el sillón; o la prestación, el profesional o el sillón está inactivo: el paciente solo puede ser inexistente, D136), cuando creo un turno con esa referencia, entonces se rechaza con `RN-GL-04` indicando el recurso y el motivo, y no se crea ningún turno.

## Flujo 2: Reserva online 24/7 por link (CU-01)

**Disparador**: el paciente abre `/reservar/{slug}`.
**Actor**: paciente (sin cuenta).

1. Frontend pide `GET /public/{slug}/prestaciones` y `GET /public/{slug}/disponibilidad?prestacion_id&desde&hasta`.
2. API calcula huecos: franjas del horario recurrente − bloqueos − turnos activos, en pasos de la granularidad, dentro de [ahora + 2 h, hoy + 60 días] (RN-TD-01, RN-TD-02).
3. **Si no hay huecos** → se ofrece anotarse en la lista de espera (Flujo 6) (RN-TD-07).
4. El paciente elige hueco, carga datos de contacto (**teléfono obligatorio, DNI opcional**; sin cuenta, SU-03) y **acepta el consentimiento** (RN-PR-02, texto `v1-borrador`); si cambió la versión del texto desde la última vez, se vuelve a pedir (D25). El sistema **reutiliza un paciente existente solo si coinciden teléfono, nombre y apellido normalizados**; si no, crea uno nuevo (RN-TD-09). La respuesta es la misma en ambos casos y no se pisan datos ya cargados (RN-PR-06).
5. **Aviso de reserva fuera de plazo (RN-TD-10, D87):** si `inicio − ahora < antelacion_cancelacion_horas` (valor vigente), antes de confirmar se avisa que el turno **no va a poder cancelarse ni reprogramarse online** (y, si aplica seña, que **la seña no se devuelve** si el paciente cancela o no asiste, RN-SP-04) y el botón dice **«Confirmar sin derecho a cancelación»**.
   `POST /public/{slug}/reservas` → ejecuta el mismo caso de uso que el Flujo 1 (revalida solapamientos de forma atómica). En esa condición la petición debe traer la **aceptación explícita**; si no, se rechaza con `RN-TD-10` y no se crea el turno. La aceptación queda en el historial (evento de creación).
6. Estado inicial: `pendiente_aprobacion` (paciente nuevo + aprobación activa), `pendiente_sena` (si se exige seña → Flujo 4) o `reservado`. **Aprobación manual:** el odontólogo aprueba o rechaza desde el panel, en la agenda del día (US-020 CA-12, D112). Si **rechaza**, el turno pasa a `cancelado_profesional`, libera el horario y dispara el Flujo 6. Si **aprueba**, pasa a `reservado` o, si se exige seña, a `pendiente_sena` (la `Sena` se crea en ese momento y su plazo empieza ahí; Flujo 4) (RN-TD-05, D76).
7. Se genera `token_gestion` y **la respuesta de la reserva devuelve el link de gestión**, que la pantalla de confirmación muestra (RN-TD-08, D93). Desde US-030, la tarea periódica prepara además el mensaje `wa.me` con ese link (el odontólogo lo envía; la Cloud API es Fase 2); antes de US-030 no se prepara ningún mensaje.

**Casos de error**: hueco tomado entre la consulta y la reserva → `409` y se recargan los huecos; fuera de horizonte/antelación → `422`; reserva dentro de la ventana de cancelación sin la aceptación explícita → error de dominio `RN-TD-10`, sin crear el turno.

## Flujo 3: Recordatorio y confirmación por WhatsApp (CU-02)

**Canal v1: enlace `wa.me` (semiautomático)** (decisión del autor 2026-10-03, DD-06). La Cloud API oficial es Fase 2; el puerto de mensajería queda preparado para sumarla.
**Disparador**: al crear el turno se programa el recordatorio para `inicio − 24 h` (`Mensaje` en estado `programado`; RN-WA-01), junto con el mensaje que lleva el link de gestión (tipo `confirmacion`, D93). Lo prepara la **tarea periódica con Redis**, la única que dispara efectos (RN-GL-05).

1. La tarea periódica toma el recordatorio; si el turno ya no está activo, el mensaje queda `descartado`. **Justo antes de prepararlo verifica `Paciente.acepta_contacto`**: si es `false`, el mensaje no se genera y queda `descartado` (RN-PR-07, D81).
2. La tarea pasa el `Mensaje` de `programado` a `generado_link` y arma el enlace `https://wa.me/<telefono>?text=<mensaje>` (sin datos clínicos, RN-PR-06), con el link de gestión del turno.
3. El panel muestra «Recordatorios de hoy» con el enlace listo; el odontólogo lo abre, lo envía desde su WhatsApp y marca el mensaje como `enviado`.
4. El paciente **confirma desde el link de gestión**: la API valida el token, pasa el turno a `confirmado` e inserta `EventoTurno` (RN-WA-02). El consultorio también puede confirmar un turno `reservado` desde la agenda del panel, con `POST /turnos/{id}/confirmar` (US-031 CA-4, D113). Cancelar sigue el Flujo 5.

**Casos de error**: link de gestión con token inválido → `401`/`404` sin revelar datos del turno. El token no vence por sí mismo: según el estado del turno el link permite ciertas acciones (confirmar solo desde `reservado`) o solo muestra el estado (RN-TD-08, D77); una acción no permitida se rechaza con `RN-TD-11` (D89).
**Fase 2 (no implementada):** envío por Cloud API con plantilla y respuesta del paciente por `POST /webhooks/whatsapp` (verificación de firma, reintentos y estado `fallido`).

## Flujo 4: Seña con Mercado Pago (CU-04)

1. Al reservar con seña requerida, el turno queda `pendiente_sena` (ocupa el horario) y se crea `Sena(pendiente, vence_en)`. Si además está activa la aprobación manual, el turno nace `pendiente_aprobacion` y **recién al aprobarlo** pasa a `pendiente_sena`: la `Sena` se crea en ese momento y `vence_en` cuenta desde ahí (RN-SP-02, D76).
2. API crea una **preferencia de Checkout Pro** con las credenciales de prueba del odontólogo y `external_reference = turno_id`; devuelve la URL de pago. Si el paciente no paga en ese momento, puede hacerlo después desde su link de gestión (`POST /public/turnos/{token}/pagar-sena`, **ruta propuesta**, que devuelve la URL de la preferencia; solo con el turno en `pendiente_sena`, RN-TD-08; en otro estado, `RN-TD-11`; D89). Si la reserva cae dentro de la ventana de cancelación, el aviso previo suma que la seña no se devuelve (RN-TD-10, D87).
3. El paciente paga en Mercado Pago y vuelve a la URL de retorno (informativa; **no** acredita).
4. Mercado Pago notifica `POST /webhooks/mercadopago`; la API consulta el pago, y si está aprobado marca `Sena(acreditada)`, pasa el turno a `reservado` e inserta `EventoTurno(sena_acreditada)`. Idempotente por `mp_payment_id` (RN-SP-08). **Pago acreditado tarde:** si el webhook llega con el turno **ya no activo** (`vencido` o cancelado), el turno no cambia y la seña (pasada a `vencida`) se registra `devuelta` (solo registro en el prototipo; RN-SP-11, D38, D59). Si la seña estaba **efectivamente vencida** y la tarea todavía no lo había persistido, el webhook persiste en su transacción `pendiente` → `vencida` → `devuelta` y el turno a `vencido`, sin disparar efectos (RN-GL-05 (b), D92). Si se cancela un turno `pendiente_sena`, su seña `pendiente` pasa a `vencida` (D59). Cualquier otra transición de la seña se rechaza con `RN-SP-12` (D61).
5. Si vence sin pago (30 minutos por defecto, configurable): el vencimiento se **evalúa al consultar** (`vence_en` contra `utc_now()`), por lo que el turno deja de ocupar el horario aunque no haya corrido ninguna tarea; la **tarea periódica** pasa el turno a `vencido` y la seña a `vencida`, y es la única que dispara el Flujo 6 (RN-SP-03, RN-GL-05, D80). Si antes una escritura necesita ese horario (crear o reprogramar un turno, aceptar una oferta), persiste ella el vencimiento en su misma transacción, sin disparar efectos, para que la restricción de exclusión de PostgreSQL no rechace lo que el dominio aceptó (RN-GL-05 (a), D92). Las transiciones de la seña están en `04_modelo_de_datos.md`.
6. **Retención y devolución** (prototipo con credenciales de prueba; **sujeto a revisión legal**, RN-SP-04/05/06): la seña acreditada pasa a `retenida` si el paciente queda `ausente` o si el consultorio carga desde el panel una cancelación del paciente fuera de plazo; pasa a `devuelta` si el paciente cancela dentro de plazo o cancela el odontólogo. La retención o devolución **manual** (RN-SP-10) exige que el turno esté `ausente` o `atendido`, respectivamente (D101). No hay retención parcial y la devolución solo se registra, sin devolución real por API (decisión del autor 2026-10-03).

## Flujo 5: Cancelación o reprogramación por el paciente (CU-05)

1. El paciente abre `/turno/{token}` (link de gestión).
2. API valida el token y el **estado del turno** (qué acciones permite, RN-TD-08, D77: en un estado terminal el link solo muestra el estado), verifica que el turno no haya empezado (`ahora < inicio`) y la ventana: `ahora ≤ inicio − antelacion_cancelacion_horas`, con el valor **vigente al momento de la cancelación** (RN-TD-03, RN-GL-03). Una acción no permitida por el estado, o con el turno ya empezado, se rechaza con `RN-TD-11` (estado actual y acciones permitidas en el mensaje; sin modificar turno ni historial; D89); estar **fuera de plazo** sigue siendo RN-TD-03 (paso 5).
3. **Cancelar**: turno → `cancelado_paciente`; seña según RN-SP-06 (devuelta, dentro de plazo) (**sujeto a revisión legal**); evento en historial; dispara Flujo 6.
4. **Reprogramar**: el paciente elige un nuevo hueco (el turno conserva la seña ya acreditada, RN-TD-04, D66); se ejecuta la validación del Flujo 1 excluyendo el propio turno (RN-AG-10b); se actualizan `inicio/fin`, se registra `EventoTurno(reprogramado)` con antes/después, se reprograma el recordatorio y el hueco anterior dispara Flujo 6.
5. Fuera de plazo → el link muestra que debe contactar al consultorio. Si el consultorio carga desde el panel la cancelación como cancelación del paciente, el turno pasa a `cancelado_paciente` y la seña se retiene (RN-SP-04 (b); decisión del autor 2026-10-03, D21).

## Flujo 6: Lista de espera y oferta de huecos (CU-06) — diferenciador

1. Disparador: un horario se libera (cancelación, rechazo de una aprobación manual, vencimiento, reprogramación). El **hueco** es el tramo libre contiguo, dentro del horario del profesional y sin bloqueos, que queda al liberarse el turno (el intervalo liberado más el tiempo libre adyacente); solo se ofrece desde `ahora + antelacion_minima_reserva_horas` y nunca un tramo pasado (RN-LE-01, RN-TD-02; D97).
2. La tarea periódica busca entradas `activa` compatibles en orden de llegada, FIFO por `creada_en` (RN-LE-02): el **tramo común** entre el hueco y alguna franja preferida alcanza para la duración de la prestación (o la lista de preferencias está vacía y el hueco alcanza); no se exige que el hueco entre entero en la franja (RN-LE-01, D78, D88). Ejemplo: hueco de 9:00 a 13:00, preferencia de 10:00 a 12:00 y prestación de 30 minutos → compatible; se ofrece dentro del tramo común (a las 10:00). Hueco de 9:00 a 10:15 con la misma preferencia → no compatible. **Salta a los pacientes con `acepta_contacto = false`**, que verifica justo antes de preparar la oferta (RN-PR-07, D81).
3. Crea `OfertaHueco(enviada, vence_en)` con `inicio` = el primer inicio posible dentro del tramo común (respetando la granularidad de la agenda) y `fin` = `inicio` + duración de la prestación (RN-LE-01, D88); vence a las 2 horas por defecto, configurable (RN-LE-03) y deja el mensaje listo con `wa.me` en el panel; el odontólogo lo envía. La entrada pasa a `ofertada`. Si el hueco es más largo que la prestación, el **resto se ofrece en la misma corrida a la siguiente entrada compatible** y lo que no se ofrezca queda libre para la reserva normal; una oferta enviada **no bloquea** el horario (D97).
4. El paciente acepta desde el link (si el turno resultante empieza a menos de `antelacion_cancelacion_horas`, la aceptación exige la aceptación explícita de RN-TD-10, D87) → se revalida el solapamiento (RN-LE-04) → se crea el turno con `origen = lista_espera`, la entrada pasa a `asignada`.
5. **Rechazo o vencimiento** (el vencimiento se evalúa al consultar y lo persiste la tarea periódica, o la aceptación tardía, que se rechaza; RN-GL-05) → la oferta pasa a `rechazada` o `vencida`, la entrada **vuelve a `activa` conservando su lugar** (su `creada_en` no cambia; D53) y el hueco se ofrece a la siguiente entrada compatible. **Retiro de una entrada `ofertada`** (RN-LE-06) → la oferta se da por `rechazada`, la entrada pasa a **`retirada`** (no vuelve a `activa`) y el hueco se ofrece a la siguiente.
6. **Alta y baja de la lista:** anotarse por el link público exige aceptar el consentimiento de datos (RN-LE-05); el paciente se reconoce según RN-TD-09 y hay una sola entrada en curso (`activa` u `ofertada`) por paciente y prestación, con la prestación obligatoria (RN-LE-07, D78). El consultorio también puede anotar a un paciente desde el panel: ahí la falta de consentimiento no bloquea el alta y el consentimiento se registra con origen `panel` cuando el paciente lo da en persona (D103, D107). Se sale de la lista de dos formas, ambas a `retirada`: el paciente se retira desde su link, o el consultorio la retira desde el panel (RN-LE-06) (decisión del autor 2026-10-03, D20).
7. **Aviso en el panel:** una entrada en curso con más de 7 días sin recibir una oferta compatible (desde `creada_en` o desde su última oferta) se señala en el panel para que el consultorio la gestione a mano; es un indicador del panel, no un mensaje, y se calcula al consultar (RN-LE-08, D78).

## Flujo 7: Atención y ficha clínica (CU-03)

1. El odontólogo abre la agenda del día y selecciona el turno.
2. Abre la ficha del paciente: datos, última versión de la anamnesis, evoluciones previas (`GET /pacientes/{id}/ficha`, ruta propuesta, D114).
3. Registra la evolución en texto (vinculada al turno; queda firmada por el usuario que inició sesión, `registrada_por`, D50) y marca el turno `atendido` (o `ausente`); también puede marcarlo la recepcionista (RN-AG-13). Solo se puede desde `reservado` o `confirmado`; en otro estado se rechaza con `RN-AG-12`. Solo si `ahora >= inicio` del turno (si no, `RN-AG-13`). Cuando es el primer turno `atendido` del paciente, `Paciente.es_nuevo` pasa a `false` (RN-TD-05). Si queda `ausente` con seña acreditada, la seña se retiene (RN-SP-04 (a)). **Corrección del marcado:** dentro de las 24 horas del marcado original, solo el odontólogo puede pasar `atendido` ↔ `ausente` (pasado el plazo, `RN-AG-12`); la seña no acompaña el cambio y el odontólogo la devuelve o retiene manualmente, con registro (RN-AG-13, RN-SP-10; decisión del autor 2026-10-05, D34).
4. Opcional: crea un presupuesto simple y/o un registro de pago.

## Flujo 8: Autenticación del panel

*(Change de usuarios y acceso, Épica 10. El primer change no lo usa: `POST /turnos` va sin autenticación, DD-14.) **Desde C-07 (`roles-y-proteccion-del-panel`) la excepción ya no vale**: todas las rutas del panel exigen JWT y rol (D214).*

1. `POST /auth/login` con email y contraseña → valida el hash → emite access token JWT (15 minutos, decisión del autor 2026-10-05, D74, SU-09) y refresh token (7 días, decisión del autor), ambos con el claim `token_version` del usuario.
2. Cada request al panel envía `Authorization: Bearer <jwt>`; un dependency de FastAPI valida firma y expiración, lee los roles del usuario de la base en cada petición (RN-AU-02, D102), y verifica que el usuario siga `activo` y que `token_version` coincida con el del usuario (RN-AU-03, RN-AU-04; D43).
3. `POST /auth/refresh` renueva el access token, con las mismas verificaciones de `activo` y `token_version`.
4. Al desactivar al usuario, o al cambiar o restablecer su contraseña, `token_version` se incrementa y todos sus tokens anteriores dejan de valer (RN-AU-07).
**Errores**: credenciales inválidas → `401` genérico; token ausente, vencido, de un usuario inactivo o con `token_version` viejo → `401`; rol insuficiente → `403`.
