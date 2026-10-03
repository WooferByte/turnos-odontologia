# Flujos Principales

## Flujo 1: Crear turno sin solapamientos (panel) — núcleo del change de la consigna

**Disparador**: la recepcionista u odontólogo agenda un turno.
**Actor**: `recepcionista` / `odontologo`. **En el primer change el endpoint va sin autenticación** (límite conocido, decisión del autor 2026-10-03, DD-14); con el change de usuarios y acceso exige JWT (US-092).

**Contrato del primer change:** la firma de la función pura de dominio, del caso de uso, del error de dominio y el mapeo a HTTP están en `08_arquitectura_propuesta.md` (sección «Contrato del primer change»). El primer change entrega el dominio, el caso de uso y el **endpoint `POST /turnos` (FastAPI)**, para probarlo desde Swagger (`/docs`) en el video (decisión del autor 2026-10-03). Sigue sin interfaz gráfica.

**Pasos**:
1. Frontend/cliente envía `POST /turnos` con `paciente_id`, `prestacion_id`, `inicio`, y opcionalmente `profesional_id` y `sillon_id`.
2. *(Fuera del primer change, DD-14)* API valida el JWT y el permiso (RN-AU-01, US-092). En el primer change este paso no existe: el caso de uso no depende de la autenticación.
3. Caso de uso `CrearTurno` resuelve defaults: profesional único y **sillón por defecto** si no vienen (RN-AG-06); verifica que prestación, paciente, profesional y sillón **existan y estén activos** (si no, `RN-GL-04`, E12); calcula `fin = inicio + duración` de la prestación (RN-AG-02).
4. Dominio valida `inicio < fin` y que las fechas sean aware en UTC (RN-AG-10d, RN-GL-01) al construir el `Intervalo`.
5. *(Fuera del primer change, decisión del autor 2026-10-02, P-10)* Dominio valida horario recurrente y bloqueos (RN-AG-04, RN-AG-04b). El primer change solo cubre los solapamientos por profesional y por sillón con estados activos.
6. Dentro de una transacción, el repositorio obtiene los turnos del profesional y del sillón que intersecan `[inicio, fin)`. El **filtro por estado activo** (RN-AG-10) lo aplica el dominio con la constante `ESTADOS_ACTIVOS` (decisión del autor 2026-10-03; así E6 se prueba como función pura).
7. Dominio aplica la función pura de solapamiento `a.inicio < b.fin and b.inicio < a.fin` (RN-AG-09) contra ambos conjuntos (RN-AG-05, RN-AG-08) y devuelve **todos** los conflictos encontrados.
8. Si no hay conflicto, persiste el turno en estado `reservado` y hace commit. *(El `EventoTurno(creado)` de RN-AG-11 queda fuera del primer change: change siguiente, decisión del autor 2026-10-03.)*
9. Responde `201` con el turno.

```
Cliente → API → CrearTurno → Dominio(validar) → Repo(turnos del recurso ∩ rango) → DB
                                      ← conflictos? ── sí → 409 {codigos: [RN-AG-05 y/o RN-AG-08]}
                                      ← no → INSERT turno → 201
```

**Casos de error**:
- Profesional ocupado → `409` con `RN-AG-05`.
- Sillón ocupado → `409` con `RN-AG-08`.
- Ambos ocupados → `409` con **los dos códigos** (`RN-AG-05` y `RN-AG-08`) (decisión del autor 2026-10-03).
- Prestación, paciente, profesional o sillón inexistente o inactivo → `422` con `RN-GL-04` («recurso no encontrado»; E12). Se rechaza antes de evaluar solapamientos y no persiste nada.
- Fuera de horario o sobre bloqueo → `422` con `RN-AG-04` / `RN-AG-04b` (fuera del primer change).
- Carrera concurrente → la segunda transacción falla (restricción de exclusión o bloqueo) y se responde `409` (RN-AG-10c; fuera del primer change, E11).

**Escenarios del spec (dado/cuando/entonces), con IDs estables** — exigidos por la consigna (feliz, error de negocio, borde). Los **E1..E7 y E12 entran en el primer change** (un test por escenario). La tabla completa E1..E12 está en `06_funcionalidades.md` (US-010); E8 a E11 quedan fuera del spec. Todos los horarios se expresan en UTC.
- **E1 Feliz**: dado un profesional sin turnos de 10:00 a 11:00, cuando creo un turno de 30 min a las 10:00, entonces se crea `reservado` con fin 10:30.
- **E2 Error (profesional)**: dado un turno activo 10:00-10:30 del profesional en otro sillón, cuando creo otro con ese profesional a las 10:15 en un sillón libre, entonces se rechaza solo con `RN-AG-05`.
- **E3 Error (sillón)**: dado un turno activo 10:00-10:30 en el sillón con otro profesional, cuando creo un turno en ese sillón a las 10:00 con un profesional libre, entonces se rechaza solo con `RN-AG-08`.
- **E4 Doble conflicto**: dado un turno activo 10:00-10:30 del mismo profesional y del mismo sillón (el caso normal del MVP, con 1 profesional y 1 sillón), cuando creo otro a las 10:00 con ese profesional y ese sillón, entonces se rechaza con los dos errores, `RN-AG-05` y `RN-AG-08`.
- **E5 Borde contiguo**: dado un turno 10:00-10:30, cuando creo otro a las 10:30, entonces se acepta (y lo mismo si el nuevo termina justo a las 10:00).
- **E6 Estado no activo**: dado un turno cancelado 10:00-10:30 (o vencido, atendido o ausente), cuando creo otro a las 10:00, entonces se acepta.
- **E7 Borde de un minuto**: dado un turno activo 10:00-10:30 del profesional en otro sillón, cuando creo otro con ese profesional a las 10:29, entonces se rechaza con `RN-AG-05` (un solapamiento de un minuto es solapamiento).
- **E12 Recurso no encontrado**: dado que no existe la prestación 999 (o el paciente, el profesional o el sillón; o está inactivo), cuando creo un turno con esa referencia, entonces se rechaza con `RN-GL-04` indicando el recurso y el motivo, y no se crea ningún turno.

## Flujo 2: Reserva online 24/7 por link (CU-01)

**Disparador**: el paciente abre `/reservar/{slug}`.
**Actor**: paciente (sin cuenta).

1. Frontend pide `GET /public/{slug}/prestaciones` y `GET /public/{slug}/disponibilidad?prestacion_id&desde&hasta`.
2. API calcula huecos: franjas del horario recurrente − bloqueos − turnos activos, en pasos de la granularidad, dentro de [ahora + 2 h, hoy + 60 días] (RN-TD-01, RN-TD-02).
3. **Si no hay huecos** → se ofrece anotarse en la lista de espera (Flujo 6) (RN-TD-07).
4. El paciente elige hueco, carga datos de contacto (**teléfono obligatorio, DNI opcional**; sin cuenta, SU-03) y **acepta el consentimiento** (RN-PR-02); si cambió la versión del texto desde la última vez, se vuelve a pedir (D25).
5. `POST /public/{slug}/reservas` → ejecuta el mismo caso de uso que el Flujo 1 (revalida solapamientos de forma atómica).
6. Estado inicial: `pendiente_aprobacion` (paciente nuevo + aprobación activa), `pendiente_sena` (si se exige seña → Flujo 4) o `reservado`.
7. Se genera `token_gestion` y se **prepara con `wa.me`** el mensaje con el link del turno (el odontólogo lo envía; la Cloud API es Fase 2).

**Casos de error**: hueco tomado entre la consulta y la reserva → `409` y se recargan los huecos; fuera de horizonte/antelación → `422`.

## Flujo 3: Recordatorio y confirmación por WhatsApp (CU-02)

**Canal v1: enlace `wa.me` (semiautomático)** (decisión del autor 2026-10-03, DD-06). La Cloud API oficial es Fase 2; el puerto de mensajería queda preparado para sumarla.
**Disparador**: al crear el turno se programa una tarea en Redis para `inicio − 24 h` (RN-WA-01).

1. El worker toma la tarea; si el turno ya no está activo, la descarta.
2. El worker crea el `Mensaje` con estado `generado_link` y el enlace `https://wa.me/<telefono>?text=<mensaje>` (sin datos clínicos, RN-PR-06), con el link de gestión del turno.
3. El panel muestra «Recordatorios de hoy» con el enlace listo; el odontólogo lo abre, lo envía desde su WhatsApp y marca el mensaje como `enviado`.
4. El paciente **confirma desde el link de gestión**: la API valida el token, pasa el turno a `confirmado` e inserta `EventoTurno` (RN-WA-02). Cancelar sigue el Flujo 5.

**Casos de error**: link de gestión con token inválido o vencido → `401`/`404` sin revelar datos del turno.
**Fase 2 (no implementada):** envío por Cloud API con plantilla y respuesta del paciente por `POST /webhooks/whatsapp` (verificación de firma, reintentos y estado `fallido`).

## Flujo 4: Seña con Mercado Pago (CU-04)

1. Al reservar con seña requerida, el turno queda `pendiente_sena` (ocupa el horario) y se crea `Sena(pendiente, vence_en)`.
2. API crea una **preferencia de Checkout Pro** con las credenciales de prueba del odontólogo y `external_reference = turno_id`; devuelve la URL de pago.
3. El paciente paga en Mercado Pago y vuelve a la URL de retorno (informativa; **no** acredita).
4. Mercado Pago notifica `POST /webhooks/mercadopago`; la API consulta el pago, y si está aprobado marca `Sena(acreditada)`, pasa el turno a `reservado` e inserta `EventoTurno(sena_acreditada)`. Idempotente por `mp_payment_id` (RN-SP-08).
5. Si vence sin pago (30 minutos por defecto, configurable) → worker pasa el turno a `vencido`, libera el horario y dispara Flujo 6 (RN-SP-03).
6. **Retención y devolución** (prototipo con credenciales de prueba; **sujeto a revisión legal**, RN-SP-04/05/06): la seña acreditada pasa a `retenida` si el paciente queda `ausente` o si el consultorio carga desde el panel una cancelación del paciente fuera de plazo; pasa a `devuelta` si el paciente cancela dentro de plazo o cancela el odontólogo. No hay retención parcial y la devolución solo se registra, sin devolución real por API (decisión del autor 2026-10-03).

## Flujo 5: Cancelación o reprogramación por el paciente (CU-05)

1. El paciente abre `/turno/{token}` (link de gestión).
2. API valida el token y verifica la ventana: `ahora ≤ inicio − antelacion_cancelacion_horas` (RN-TD-03).
3. **Cancelar**: turno → `cancelado_paciente`; seña según RN-SP-06 (devuelta, dentro de plazo) (**sujeto a revisión legal**); evento en historial; dispara Flujo 6.
4. **Reprogramar**: el paciente elige un nuevo hueco; se ejecuta la validación del Flujo 1 excluyendo el propio turno (RN-AG-10b); se actualizan `inicio/fin`, se registra `EventoTurno(reprogramado)` con antes/después, se reprograma el recordatorio y el hueco anterior dispara Flujo 6.
5. Fuera de plazo → el link muestra que debe contactar al consultorio. Si el consultorio carga desde el panel la cancelación como cancelación del paciente, el turno pasa a `cancelado_paciente` y la seña se retiene (RN-SP-04 (b); decisión del autor 2026-10-03, D21).

## Flujo 6: Lista de espera y oferta de huecos (CU-06) — diferenciador

1. Disparador: un horario se libera (cancelación, vencimiento, reprogramación).
2. Worker busca entradas `activas` compatibles (duración de la prestación ≤ hueco, preferencias) en orden de alta (RN-LE-02).
3. Crea `OfertaHueco(enviada, vence_en)` (vence a las 2 horas por defecto, configurable, RN-LE-03) y deja el mensaje listo con `wa.me` en el panel; el odontólogo lo envía.
4. El paciente acepta desde el link → se revalida el solapamiento (RN-LE-04) → se crea el turno con `origen = lista_espera`, la entrada pasa a `asignada`.
5. Rechazo o vencimiento (el worker vence la oferta) → se ofrece a la siguiente entrada compatible.
6. **Alta y baja de la lista:** anotarse exige aceptar el consentimiento de datos (RN-LE-05). Se sale de la lista de dos formas, ambas a `retirada`: el paciente se retira desde su link, o el consultorio la retira desde el panel (RN-LE-06) (decisión del autor 2026-10-03, D20).

## Flujo 7: Atención y ficha clínica (CU-03)

1. El odontólogo abre la agenda del día y selecciona el turno.
2. Abre la ficha del paciente: datos, última versión de la anamnesis, evoluciones previas.
3. Registra la evolución en texto (vinculada al turno) y marca el turno `atendido` (o `ausente`); también puede marcarlo la recepcionista (RN-AG-13). Solo se puede desde `reservado` o `confirmado`; en otro estado se rechaza con `RN-AG-12`. Si queda `ausente` con seña acreditada, la seña se retiene (RN-SP-04 (a)).
4. Opcional: crea un presupuesto simple y/o un registro de pago.

## Flujo 8: Autenticación del panel

*(Change de usuarios y acceso, Épica 10. El primer change no lo usa: `POST /turnos` va sin autenticación, DD-14.)*

1. `POST /auth/login` con email y contraseña → valida el hash → emite access token JWT (15 minutos, propuesta aceptada por el autor 2026-10-03, SU-09) y refresh token (7 días, propuesta aceptada).
2. Cada request al panel envía `Authorization: Bearer <jwt>`; un dependency de FastAPI valida firma, expiración y roles.
3. `POST /auth/refresh` renueva el access token.
**Errores**: credenciales inválidas → `401` genérico; token ausente o vencido → `401`; rol insuficiente → `403`.
