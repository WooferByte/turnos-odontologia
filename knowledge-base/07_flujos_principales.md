# Flujos Principales

## Flujo 1: Crear turno sin solapamientos (panel) — núcleo del change de la consigna

**Disparador**: la recepcionista u odontólogo agenda un turno.
**Actor**: `recepcionista` / `odontologo` (JWT).

**Pasos**:
1. Frontend/cliente envía `POST /turnos` con `paciente_id`, `prestacion_id`, `inicio`, y opcionalmente `profesional_id` y `sillon_id`.
2. API valida el JWT y el permiso (RN-AU-01).
3. Caso de uso `CrearTurno` resuelve defaults: profesional único y **sillón por defecto** si no vienen (RN-AG-06); calcula `fin = inicio + duración` de la prestación (RN-AG-02).
4. Dominio valida `inicio < fin` (RN-AG-10d).
5. *(Opcional en el primer change)* Dominio valida horario recurrente y bloqueos (RN-AG-04, RN-AG-04b).
6. Dentro de una transacción, el repositorio obtiene los turnos **activos** del profesional y del sillón que intersecan `[inicio, fin)` (RN-AG-10).
7. Dominio aplica la función pura de solapamiento `a.inicio < b.fin and b.inicio < a.fin` (RN-AG-09) contra ambos conjuntos (RN-AG-05, RN-AG-08).
8. Si no hay conflicto, persiste el turno en estado `reservado` (o `pendiente_sena`) e inserta `EventoTurno(creado)` (RN-AG-11). Commit.
9. Responde `201` con el turno.

```
Cliente → API → CrearTurno → Dominio(validar) → Repo(turnos activos ∩ rango) → DB
                                      ← conflicto? ── sí → 409 {codigo: RN-AG-05 | RN-AG-08}
                                      ← no → INSERT turno + evento → 201
```

**Casos de error**:
- Profesional ocupado → `409` con `RN-AG-05`.
- Sillón ocupado → `409` con `RN-AG-08` (si ambos, se informan ambos).
- Prestación inexistente o inactiva, paciente inexistente → `404`/`422`.
- Fuera de horario o sobre bloqueo → `422` con `RN-AG-04` / `RN-AG-04b`.
- Carrera concurrente → la segunda transacción falla (restricción de exclusión o bloqueo) y se responde `409` (RN-AG-10c).

**Escenarios mínimos del spec (dado/cuando/entonces)** — exigidos por la consigna (feliz, error de negocio, borde):
1. *Feliz*: dado un profesional sin turnos de 10:00 a 11:00, cuando creo un turno de 30 min a las 10:00, entonces se crea con fin 10:30.
2. *Error*: dado un turno activo 10:00-10:30 del profesional, cuando creo otro a las 10:15, entonces se rechaza con RN-AG-05.
3. *Error (sillón)*: dado un turno activo 10:00-10:30 en el sillón con otro profesional, cuando creo un turno en ese sillón a las 10:00, entonces se rechaza con RN-AG-08.
4. *Borde*: dado un turno 10:00-10:30, cuando creo otro a las 10:30, entonces se acepta.
5. *Borde*: dado un turno cancelado 10:00-10:30, cuando creo otro a las 10:00, entonces se acepta.

## Flujo 2: Reserva online 24/7 por link (CU-01)

**Disparador**: el paciente abre `/reservar/{slug}`.
**Actor**: paciente (sin cuenta).

1. Frontend pide `GET /public/{slug}/prestaciones` y `GET /public/{slug}/disponibilidad?prestacion_id&desde&hasta`.
2. API calcula huecos: franjas del horario recurrente − bloqueos − turnos activos, en pasos de la granularidad, dentro de [ahora + 2 h, hoy + 60 días] (RN-TD-01, RN-TD-02).
3. **Si no hay huecos** → se ofrece anotarse en la lista de espera (Flujo 6) (RN-TD-07).
4. El paciente elige hueco, carga datos de contacto y **acepta el consentimiento** (RN-PR-02).
5. `POST /public/{slug}/reservas` → ejecuta el mismo caso de uso que el Flujo 1 (revalida solapamientos de forma atómica).
6. Estado inicial: `pendiente_aprobacion` (paciente nuevo + aprobación activa), `pendiente_sena` (si se exige seña → Flujo 4) o `reservado`.
7. Se genera `token_gestion` y se envía (o se prepara con `wa.me`) el mensaje con el link del turno.

**Casos de error**: hueco tomado entre la consulta y la reserva → `409` y se recargan los huecos; fuera de horizonte/antelación → `422`.

## Flujo 3: Recordatorio y confirmación por WhatsApp (CU-02)

**Disparador**: al crear el turno se programa una tarea en Redis para `inicio − 24 h` (RN-WA-01).

1. Worker toma la tarea; si el turno ya no está activo, la descarta.
2. **Modo Cloud API (preferido, modo prueba)**: envía mensaje de plantilla al número de prueba con botones/opciones "Confirmo" / "Cancelo" y el link de gestión. Registra `Mensaje(enviado)`.
3. Meta llama a `POST /webhooks/whatsapp` con la respuesta → API verifica la firma, identifica el turno, aplica confirmación (`confirmado`) o cancelación (Flujo 5) e inserta `EventoTurno` (RN-WA-02).
4. **Modo `wa.me` (alternativa)**: el worker marca el mensaje como `generado_link`; el panel muestra "Recordatorios de hoy" con un enlace `https://wa.me/<telefono>?text=<mensaje>` que el odontólogo envía a mano. El paciente confirma desde el link de gestión.

**Casos de error**: fallo de envío → reintento con backoff y luego `fallido` visible en el panel; webhook con firma inválida → `401` y se descarta.

## Flujo 4: Seña con Mercado Pago (CU-04)

1. Al reservar con seña requerida, el turno queda `pendiente_sena` (ocupa el horario) y se crea `Sena(pendiente, vence_en)`.
2. API crea una **preferencia de Checkout Pro** con las credenciales de prueba del odontólogo y `external_reference = turno_id`; devuelve la URL de pago.
3. El paciente paga en Mercado Pago y vuelve a la URL de retorno (informativa; **no** acredita).
4. Mercado Pago notifica `POST /webhooks/mercadopago`; la API consulta el pago, y si está aprobado marca `Sena(acreditada)`, pasa el turno a `reservado` e inserta `EventoTurno(sena_acreditada)`. Idempotente por `mp_payment_id` (RN-SP-08).
5. Si vence sin pago → worker pasa el turno a `vencido`, libera el horario y dispara Flujo 6 (RN-SP-03).

## Flujo 5: Cancelación o reprogramación por el paciente (CU-05)

1. El paciente abre `/turno/{token}` (link de gestión).
2. API valida el token y verifica la ventana: `ahora ≤ inicio − antelacion_cancelacion_horas` (RN-TD-03).
3. **Cancelar**: turno → `cancelado_paciente`; seña según RN-SP-04/RN-SP-06 (**sujeto a revisión legal**); evento en historial; dispara Flujo 6.
4. **Reprogramar**: el paciente elige un nuevo hueco; se ejecuta la validación del Flujo 1 excluyendo el propio turno (RN-AG-10b); se actualizan `inicio/fin`, se registra `EventoTurno(reprogramado)` con antes/después, se reprograma el recordatorio y el hueco anterior dispara Flujo 6.
5. Fuera de plazo → el link muestra que debe contactar al consultorio.

## Flujo 6: Lista de espera y oferta de huecos (CU-06) — diferenciador

1. Disparador: un horario se libera (cancelación, vencimiento, reprogramación).
2. Worker busca entradas `activas` compatibles (duración de la prestación ≤ hueco, preferencias) en orden de alta (RN-LE-02).
3. Crea `OfertaHueco(enviada, vence_en)` y envía el mensaje (Cloud API) o lo deja listo con `wa.me` en el panel.
4. El paciente acepta desde el link → se revalida el solapamiento (RN-LE-04) → se crea el turno con `origen = lista_espera`, la entrada pasa a `asignada`.
5. Rechazo o vencimiento → se ofrece a la siguiente entrada compatible.

## Flujo 7: Atención y ficha clínica (CU-03)

1. El odontólogo abre la agenda del día y selecciona el turno.
2. Abre la ficha del paciente: datos, última versión de la anamnesis, evoluciones previas.
3. Registra la evolución en texto (vinculada al turno) y marca el turno `atendido` (o `ausente`).
4. Opcional: crea un presupuesto simple y/o un registro de pago.

## Flujo 8: Autenticación del panel

1. `POST /auth/login` con email y contraseña → valida hash → emite access token JWT (corto) y refresh token.
2. Cada request al panel envía `Authorization: Bearer <jwt>`; un dependency de FastAPI valida firma, expiración y roles.
3. `POST /auth/refresh` renueva el access token.
**Errores**: credenciales inválidas → `401` genérico; rol insuficiente → `403`.
