# Modelo de Datos

> Convención: tipos lógicos (se mapean a SQLAlchemy). Todas las fechas-hora se guardan **con zona horaria (UTC)** y se presentan en `America/Argentina/Buenos_Aires` (ver DD-09). Los identificadores son **enteros autoincrementales** (decisión del autor 2026-10-03); los links públicos usan un token firmado aparte (`token_gestion`, `OfertaHueco.token`), por lo que el id no se expone como secreto.

## Dominios

| Dominio | Entidades | Versión |
|---|---|---|
| Identidad y acceso | Usuario, UsuarioRol | v1 |
| Consultorio y configuración | Consultorio, ConfiguracionReglas | v1 |
| Agenda | Profesional, Sillon (recurso), Prestacion, FranjaHoraria (horario recurrente), Bloqueo | v1 |
| Turnos | Turno, EventoTurno (historial) | v1 |
| Lista de espera | EntradaListaEspera, OfertaHueco | v1 |
| Mensajería | Mensaje (recordatorio / confirmación / oferta) | v1 |
| Seña y pagos | Sena, RegistroPago | v1 |
| Pacientes y ficha clínica | Paciente, Consentimiento, Anamnesis, Evolucion | v1 |
| Presupuestos | Presupuesto, ItemPresupuesto | v1 |
| Clínica ampliada | Odontograma, ObraSocial, CodigoPrestacionOS | v1.1 (no modelar en v1) |

## ERD

```
Consultorio 1──1 ConfiguracionReglas
Consultorio 1──N Usuario N──N Rol
Consultorio 1──N Profesional ──(0..1)── Usuario
Consultorio 1──N Sillon                (MVP: exactamente 1, creado por seed)
Consultorio 1──N Prestacion
Profesional 1──N FranjaHoraria         (horario recurrente semanal)
Profesional 1──N Bloqueo ; Sillon 1──N Bloqueo   (bloqueo de profesional, de sillón o de todo el consultorio)

Paciente 1──N Turno N──1 Profesional
                Turno N──1 Sillon
                Turno N──1 Prestacion
Turno 1──N EventoTurno                 (historial inmutable)
Turno 1──0..1 Sena 1──N RegistroPago(origen=MP)
Turno 1──N Mensaje

Paciente 1──N EntradaListaEspera N──0..1 Prestacion
EntradaListaEspera 1──N OfertaHueco N──0..1 Turno (el turno creado al aceptar)

Paciente 1──N Consentimiento
Paciente 1──N Anamnesis (versionada)
Paciente 1──N Evolucion N──0..1 Turno
Paciente 1──N Presupuesto 1──N ItemPresupuesto N──0..1 Prestacion
Paciente 1──N RegistroPago
```

## Convenciones comunes

Todas las entidades se describen con el mismo nivel de detalle: tabla de campos con tipo, nullability (**NN** = no nulo), restricciones y claves foráneas, más los índices. Los tipos son lógicos y se mapean a SQLAlchemy 2.x. El signo **(†)** marca una elección sin respaldo en la KB: está en la lista «A confirmar por el autor» al final del archivo.

- **Clave primaria:** `id` entero autoincremental en todas las tablas (decisión del autor 2026-10-03). Excepción: las tablas de unión con clave compuesta (`UsuarioRol`).
- **Fechas-hora:** `fecha-hora` = fecha-hora **aware en UTC**, con zona (`DateTime(timezone=True)`; RN-GL-01, DD-13). Los valores «ahora» los pone la aplicación con `utc_now()`, no el motor.
- **Enums de texto:** se persisten como texto con los valores listados, sin tipo enum nativo del motor, igual en SQLite y PostgreSQL (decisión del autor 2026-10-03 para `estado`; el mismo criterio se extiende a los demás enums †).
- **Claves foráneas:** `ON DELETE RESTRICT` (†); no hay borrado en cascada. Los datos clínicos no se borran físicamente (RN-FC-03).
- **Dinero:** `decimal(12,2)` (†), moneda ARS. **JSON:** columna `JSON` genérica (†).
- **Columna «Change que la crea»:** nombre descriptivo deducido de las épicas de `06_funcionalidades.md`; los nombres definitivos los fija el roadmap. El esquema se crea con `create_all` en el primer change y con **Alembic** desde el change de infraestructura con PostgreSQL (decisión del autor 2026-10-03, DD-15).

## Entidades

### Consultorio
**Change que la crea:** primer change (versión mínima; ver «Subconjunto del primer change»).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `nombre` | texto | NN | — |
| `slug` | texto | NN | `UNIQUE`; usado en el link público |
| `zona_horaria` | texto | NN | Default `America/Argentina/Buenos_Aires` |
| `creado_en` | fecha-hora | NN | — |

### ConfiguracionReglas (1:1 con Consultorio)
**Change que la crea:** reglas configurables (US-005). Valores **por defecto propuestos por el autor** (no estándares de mercado), todos editables (ver `05_reglas_de_negocio.md`).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `consultorio_id` | entero | NN | FK → Consultorio; `UNIQUE` (1:1) |
| `antelacion_cancelacion_horas` | entero | NN | Default 24; `CHECK` entre 24 y 48 (RN-TD-03) |
| `horizonte_reserva_dias` | entero | NN | Default 60; `CHECK > 0` (RN-TD-01) |
| `antelacion_minima_reserva_horas` | entero | NN | Default 2; `CHECK >= 0` (RN-TD-02, confirmado por el autor el 2026-10-02) |
| `aprobacion_manual_pacientes_nuevos` | bool | NN | Default `false` (RN-TD-05) |
| `requiere_sena` | bool | NN | Default `false`: la seña es opcional (R-03, SU-07) |
| `monto_sena` | decimal | null | `CHECK > 0` si no es nulo; obligatorio si `requiere_sena` (validado en el dominio †) |
| `vencimiento_sena_minutos` | entero | NN | Default **30**; `CHECK > 0` (RN-SP-03; decisión del autor 2026-10-03) |
| `vencimiento_oferta_horas` | entero | NN | Default **2**; `CHECK > 0` (RN-LE-03; decisión del autor 2026-10-03; nombre del campo †) |
| `granularidad_agenda_minutos` | entero | NN | Default 5; `CHECK > 0` (P-14; configurable) |
| `recordatorio_horas_antes` | entero | NN | Default 24; `CHECK > 0` (RN-WA-01) |
| `canal_whatsapp` | texto | NN | Default `wa_me`. Valores: `wa_me` (v1). `cloud_api` se agrega en Fase 2 (DD-06) |

Los plazos de seña y de oferta son **valores de diseño del autor, no de mercado** (decisión del autor 2026-10-03).

### Usuario y UsuarioRol
**Change que los crea:** usuarios y acceso (Épica 10, US-090 a US-094). Hasta entonces el sistema no tiene usuarios y `POST /turnos` va sin autenticación (DD-14).

`Usuario`:

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `consultorio_id` | entero | NN | FK → Consultorio |
| `email` | texto | NN | `UNIQUE` (índice de login) |
| `hash_password` | texto | NN | Hash adaptativo (SU-09); nunca la contraseña en claro |
| `activo` | bool | NN | Default `true`; un usuario inactivo no inicia sesión |
| `creado_en` | fecha-hora | NN | — |

`UsuarioRol` (N:N entre usuario y rol; el rol es un enum de texto, sin tabla `Rol` †):

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `usuario_id` | entero | NN | FK → Usuario; parte de la PK compuesta |
| `rol` | texto | NN | Valores: `odontologo`, `recepcionista`, `dueno`; parte de la PK compuesta |

### Profesional
**Change que la crea:** primer change (sin `usuario_id` ni `matricula`). MVP: 1 profesional; el modelo admite N (Fase 2).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `consultorio_id` | entero | NN | FK → Consultorio |
| `usuario_id` | entero | null | FK → Usuario; `UNIQUE` si no es nulo (change de usuarios) |
| `nombre` | texto | NN | — |
| `matricula` | texto | null | — |
| `activo` | bool | NN | Default `true` |

### Sillon (recurso)
**Change que la crea:** primer change. **MVP: un único sillón creado por seed; todo turno se asigna a él por defecto** (RN-AG-06).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `consultorio_id` | entero | NN | FK → Consultorio |
| `nombre` | texto | NN | p. ej. «Sillón 1» |
| `activo` | bool | NN | Default `true`; un sillón inactivo no admite turnos nuevos (RN-AG-07) |

### Prestacion
**Change que la crea:** primer change con `nombre`, `duracion_minutos` y `activa`; `color` y `reservable_online` los agrega el change de configuración de agenda (US-001). La duración es **por defecto**: el turno guarda su propia duración y fin (RN-AG-02).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `consultorio_id` | entero | NN | FK → Consultorio |
| `nombre` | texto | NN | `UNIQUE(consultorio_id, nombre)` |
| `duracion_minutos` | entero | NN | `CHECK > 0`; múltiplo de la granularidad (validado en el dominio, RN-AG-01) |
| `color` | texto | NN | Hex `#RRGGBB` (formato validado en la API †) |
| `reservable_online` | bool | NN | Default `false` (†); solo estas se ofrecen en la reserva pública (RN-TD-06) |
| `activa` | bool | NN | Default `true` |

### FranjaHoraria (horario recurrente)
**Change que la crea:** horario recurrente (US-002).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `profesional_id` | entero | NN | FK → Profesional |
| `dia_semana` | entero | NN | `CHECK` entre 0 y 6 (0 = lunes … 6 = domingo) |
| `hora_inicio` | hora | NN | `CHECK hora_inicio < hora_fin` |
| `hora_fin` | hora | NN | — |
| `vigente_desde` | fecha | null | — |
| `vigente_hasta` | fecha | null | `CHECK` mayor o igual que `vigente_desde` si ambas existen (†) |

Índice: `(profesional_id, dia_semana)`. Que las franjas de un mismo profesional y día no se superpongan lo valida el dominio (US-002 CA-1).

### Bloqueo
**Change que la crea:** bloqueos puntuales (US-003).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `consultorio_id` | entero | NN | FK → Consultorio |
| `profesional_id` | entero | null | FK → Profesional; con `sillon_id` nulo bloquea al profesional |
| `sillon_id` | entero | null | FK → Sillon; ambos nulos = bloquea todo el consultorio |
| `inicio` | fecha-hora | NN | `CHECK inicio < fin` |
| `fin` | fecha-hora | NN | — |
| `motivo` | texto | NN | Vacaciones, feriado, ausencia, mantenimiento |
| `creado_por` | entero | null | FK → Usuario (columna agregada cuando existe `Usuario` †) |

Índices: `(profesional_id, inicio, fin)` y `(sillon_id, inicio, fin)` (†).

### Paciente
**Change que la crea:** primer change con `nombre`, `apellido` y `telefono_whatsapp`; el resto de las columnas las agrega el change de reserva pública (US-020) o el de ficha clínica (US-060). **Datos siempre ficticios en seeds, tests y ejemplos** (RN-PR-01).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `consultorio_id` | entero | NN | FK → Consultorio |
| `nombre` | texto | NN | — |
| `apellido` | texto | NN | — |
| `dni` | texto | null | Opcional |
| `telefono_whatsapp` | texto | NN | E.164 (formato validado en la API †); obligatorio |
| `email` | texto | null | Opcional |
| `fecha_nacimiento` | fecha | null | — |
| `es_nuevo` | bool | NN | Default `true`; se usa para la aprobación manual (RN-TD-05) |
| `creado_en` | fecha-hora | NN | — |

Índice: `(consultorio_id, telefono_whatsapp)` para detectar duplicados, sin `UNIQUE` (†; SU-03: sin DNI, el duplicado se apoya en el teléfono).

Identificación del paciente en la reserva pública (decisión del autor 2026-10-02, SU-03 / DD-11 / P-13): **teléfono de WhatsApp obligatorio, DNI opcional**, email opcional; el paciente no tiene cuenta y gestiona su turno por token (Bilog usa DNI + email [C] como referencia).

### Turno
**Change que la crea:** primer change (sin `origen`, `token_gestion`, `creado_por`, `actualizado_en` ni `version`, que se agregan cuando el change correspondiente los necesite).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `consultorio_id` | entero | NN | FK → Consultorio |
| `paciente_id` | entero | NN | FK → Paciente |
| `profesional_id` | entero | NN | FK → Profesional |
| `sillon_id` | entero | NN | FK → Sillon |
| `prestacion_id` | entero | NN | FK → Prestacion |
| `inicio` | fecha-hora | NN | `CHECK inicio < fin` |
| `fin` | fecha-hora | NN | Calculado como `inicio + duracion_minutos` y persistido (RN-AG-02) |
| `duracion_minutos` | entero | NN | `CHECK > 0` |
| `estado` | texto | NN | Enum de texto, ver máquina de estados |
| `origen` | texto | NN | Default `panel`. Valores: `panel`, `link_publico`, `lista_espera` |
| `token_gestion` | texto | null | `UNIQUE` si no es nulo; firmado, para el link del paciente (change de reserva pública) |
| `creado_por` | entero | null | FK → Usuario (columna agregada cuando existe `Usuario` †) |
| `creado_en` | fecha-hora | NN | — |
| `actualizado_en` | fecha-hora | NN | — |
| `version` | entero | NN | Default 1; bloqueo optimista |

Índices: `(profesional_id, inicio, fin)` y `(sillon_id, inicio, fin)` para la búsqueda de solapamientos.

DD-04 confirmada por el autor (2026-10-02). **Suposición (producción):** en PostgreSQL se puede reforzar RN-AG-05/08 con una restricción de exclusión (`EXCLUDE USING gist` sobre `tstzrange(inicio, fin, '[)')` filtrada por estados activos). En SQLite (tests) la regla se valida en la capa de dominio. Ver DD-04.

#### Máquina de estados del turno

```
                    ┌─────────────── pendiente_aprobacion ──(aprueba)──┐
(reserva) ──┬──────►│                                                  ▼
            ├──────► pendiente_sena ──(pago acreditado)──────────► reservado ──(confirma)──► confirmado
            └──────────────────────────────────────────────────────►    │                        │
                                                                        ▼                        ▼
   cualquier estado activo ──► cancelado_paciente | cancelado_profesional | vencido (seña impaga)
   reservado/confirmado ──(se atiende)──► atendido      reservado/confirmado ──(no asiste)──► ausente
```

- **Estados activos (ocupan el horario):** `pendiente_aprobacion`, `pendiente_sena`, `reservado`, `confirmado`.
- **Estados terminales (liberan el horario):** `cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido`, `ausente`.
- **Reprogramar** no es un estado: cambia `inicio/fin` del mismo turno y registra un `EventoTurno` de tipo `reprogramado` (DD-05).

### EventoTurno (historial de cambios)
**Change que la crea:** historial de cambios de turno (US-015); **no entra en el primer change** (decisión del autor 2026-10-03). **Inmutable**: solo inserción (RN-AG-11).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `turno_id` | entero | NN | FK → Turno |
| `tipo` | texto | NN | Valores: `creado`, `reprogramado`, `confirmado`, `cancelado`, `estado_cambiado`, `sena_acreditada`, `nota` |
| `actor_tipo` | texto | NN | Valores: `usuario`, `paciente`, `sistema`, `webhook_mp`. `webhook_wa` se agrega en Fase 2 |
| `actor_id` | texto | null | Id del usuario o del token, según `actor_tipo` |
| `ocurrido_en` | fecha-hora | NN | — |
| `antes` | json | null | Estado previo (horario, estado) |
| `despues` | json | null | Estado nuevo |
| `motivo` | texto | null | — |

Índice: `(turno_id, ocurrido_en)`. Ni la aplicación ni la base exponen `UPDATE` ni `DELETE` sobre esta tabla.

### EntradaListaEspera
**Change que la crea:** lista de espera (US-021).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `consultorio_id` | entero | NN | FK → Consultorio |
| `paciente_id` | entero | NN | FK → Paciente |
| `prestacion_id` | entero | null | FK → Prestacion |
| `preferencias` | json | null | Días y franjas preferidas |
| `estado` | texto | NN | Default `activa`. Valores: `activa`, `ofertada`, `asignada`, `retirada`, `vencida` |
| `creada_en` | fecha-hora | NN | Define la prioridad FIFO (RN-LE-02) |

Índice: `(estado, creada_en)` (†).

### OfertaHueco
**Change que la crea:** oferta de huecos (US-040).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `entrada_id` | entero | NN | FK → EntradaListaEspera |
| `inicio` | fecha-hora | NN | `CHECK inicio < fin` |
| `fin` | fecha-hora | NN | — |
| `profesional_id` | entero | NN | FK → Profesional |
| `sillon_id` | entero | NN | FK → Sillon |
| `token` | texto | NN | `UNIQUE`; firmado, para aceptar o rechazar |
| `enviada_en` | fecha-hora | NN | Con `wa.me`, el momento en que la oferta queda preparada en el panel |
| `vence_en` | fecha-hora | NN | `enviada_en` + `vencimiento_oferta_horas` (2 h por defecto, RN-LE-03) |
| `estado` | texto | NN | Valores: `enviada`, `aceptada`, `rechazada`, `vencida` |
| `turno_id` | entero | null | FK → Turno (el turno creado al aceptar) |

Índice: `(entrada_id)`.

### Mensaje
**Change que la crea:** recordatorios por WhatsApp (US-030).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `turno_id` | entero | null | FK → Turno |
| `oferta_id` | entero | null | FK → OfertaHueco |
| `tipo` | texto | NN | Valores: `recordatorio`, `confirmacion`, `oferta_hueco`, `aviso_cancelacion` |
| `canal` | texto | NN | Valor v1: `wa_me`. `cloud_api` se agrega en Fase 2 |
| `estado` | texto | NN | Valores v1: `programado`, `generado_link`, `enviado` (el odontólogo lo marca al enviarlo). `entregado`, `respondido` y `fallido` quedan reservados para la Cloud API (Fase 2) |
| `programado_para` | fecha-hora | NN | — |
| `enviado_en` | fecha-hora | null | — |
| `respuesta` | texto | null | Fase 2 |
| `id_externo` | texto | null | Fase 2 |

`CHECK`: al menos uno de `turno_id` y `oferta_id` no nulo (†). Índice: `(estado, programado_para)` (†).

### Sena
**Change que la crea:** seña con Mercado Pago (US-050).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `turno_id` | entero | NN | FK → Turno; `UNIQUE` |
| `monto` | decimal | NN | `CHECK > 0` |
| `moneda` | texto | NN | Default `ARS` |
| `estado` | texto | NN | Valores: `pendiente`, `acreditada`, `retenida`, `devuelta`, `vencida` |
| `mp_preference_id` | texto | null | — |
| `mp_payment_id` | texto | null | `UNIQUE` si no es nulo (idempotencia, RN-SP-08) |
| `creada_en` | fecha-hora | NN | — |
| `vence_en` | fecha-hora | NN | `creada_en` + `vencimiento_sena_minutos` (30 min por defecto, RN-SP-03) |

### RegistroPago
**Change que la crea:** registro de pago simple (US-062). Registro **simple** (no es caja; la caja completa es v2). **Decisión del autor 2026-10-03:** el pago se asocia al paciente y, opcionalmente, a un presupuesto o a un turno; US-061 (presupuesto) **no es dependencia** de US-062. Por eso, si US-062 se implementa antes que US-061, la columna `presupuesto_id` se agrega con el change de US-061, que es quien crea la tabla `Presupuesto`.

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `paciente_id` | entero | NN | FK → Paciente |
| `turno_id` | entero | null | FK → Turno |
| `presupuesto_id` | entero | null | FK → Presupuesto |
| `monto` | decimal | NN | `CHECK > 0` |
| `medio` | texto | NN | Valores: `efectivo`, `transferencia`, `mercado_pago`, `tarjeta`, `otro` |
| `pagado` | bool | NN | — |
| `fecha` | fecha-hora | NN | — |
| `registrado_por` | entero | null | FK → Usuario; nulo si lo registra el sistema (webhook) (†) |

### Consentimiento
**Change que la crea:** consentimiento de datos (US-070). El texto de consentimiento es un **borrador, no validado legalmente** (decisión del autor 2026-10-03, ver P-03).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `paciente_id` | entero | NN | FK → Paciente |
| `version_texto` | texto | NN | Versión del texto aceptado (RN-PR-02) |
| `aceptado_en` | fecha-hora | NN | — |
| `origen` | texto | NN | Valores: `link_publico`, `panel` |
| `ip` | texto | null | **Suposición** |

### Anamnesis
**Change que la crea:** ficha clínica (US-060). Se versiona, no se sobrescribe (RN-FC-03).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `paciente_id` | entero | NN | FK → Paciente |
| `contenido` | json | NN | Antecedentes, alergias, medicación (formato †) |
| `version` | entero | NN | `UNIQUE(paciente_id, version)` |
| `registrada_por` | entero | NN | FK → Usuario |
| `registrada_en` | fecha-hora | NN | — |

### Evolucion
**Change que la crea:** ficha clínica (US-060). Solo inserción; las correcciones se hacen con una nueva entrada que referencia a la anterior.

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `paciente_id` | entero | NN | FK → Paciente |
| `turno_id` | entero | null | FK → Turno |
| `texto` | texto | NN | — |
| `profesional_id` | entero | NN | FK → Profesional |
| `registrada_en` | fecha-hora | NN | — |
| `corrige_a_id` | entero | null | FK → Evolucion (la entrada que corrige) (nombre †) |

### Presupuesto e ItemPresupuesto
**Change que los crea:** presupuesto simple (US-061).

`Presupuesto`:

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `paciente_id` | entero | NN | FK → Paciente |
| `fecha` | fecha | NN | — |
| `estado` | texto | NN | Default `borrador`. Valores: `borrador`, `entregado`, `aceptado`, `rechazado` |
| `total` | decimal | NN | Calculado desde los ítems (RN-FC-04) |
| `observaciones` | texto | null | — |

`ItemPresupuesto`:

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `presupuesto_id` | entero | NN | FK → Presupuesto |
| `prestacion_id` | entero | null | FK → Prestacion |
| `descripcion` | texto | NN | — |
| `cantidad` | entero | NN | `CHECK > 0` |
| `precio_unitario` | decimal | NN | `CHECK >= 0` |

## Subconjunto del primer change

El primer change ("crear turno sin solapamientos por profesional y por sillón", ver `06_funcionalidades.md` US-010) **no implementa el modelo completo**: crea solo las tablas que necesita. El resto se agrega change por change; el autor implementará el proyecto completo antes de fin de año (decisión 2026-10-03).

**Origen:** el alcance viene de decisiones del autor (2026-10-03: `EventoTurno` fuera del primer change; clave primaria entera, turno nace `reservado` y tabla `Consultorio` mínima confirmados; 2026-10-02, P-10: solo solapamientos con estados activos).

**Tablas que crea:** `Consultorio`, `Profesional`, `Sillon`, `Prestacion`, `Paciente` y `Turno`.
**Columnas que NO crea** (las agregan los changes indicados en cada tabla): `Consultorio.creado_en` †; `Profesional.usuario_id`, `matricula`; `Prestacion.color`, `reservable_online`; `Paciente.dni`, `email`, `fecha_nacimiento`, `es_nuevo`, `creado_en`; `Turno.origen`, `token_gestion`, `creado_por`, `actualizado_en`, `version`.
**Quedan fuera del primer change:** `EventoTurno`, `FranjaHoraria`, `Bloqueo`, `ConfiguracionReglas`, `Usuario`/`UsuarioRol` y todo lo de lista de espera, mensajería, seña, ficha y presupuestos.

- **Estado inicial:** el turno nace `reservado` (decisión del autor 2026-10-03). `pendiente_sena` y `pendiente_aprobacion` dependen de seña y aprobación manual, fuera del primer change.
- **`estado` como enum de texto** (decisión del autor 2026-10-03), con `ESTADOS_ACTIVOS` como constante del dominio (RN-AG-10).
- **Sin restricción de exclusión en el primer change:** la regla vive en el dominio (DD-02) y SQLite no soporta `EXCLUDE`; ver DD-04.
- **Creación del esquema:** `create_all` en los tests; Alembic desde el change de infraestructura con PostgreSQL (DD-15).

## Seed data inicial

Todos los datos son **ficticios** (RN-PR-01). El seed del primer change incluye `Consultorio`, `Profesional`, `Sillon`, `Prestacion` y `Paciente`; el resto se agrega con el change que crea cada tabla (`Usuario`, `ConfiguracionReglas`, horario):

- 1 `Consultorio` ("Consultorio Demo", slug `consultorio-demo`) con `ConfiguracionReglas` por defecto.
- 1 `Usuario` con roles `odontologo` + `dueno` (credenciales de prueba definidas en un archivo de ejemplo de entorno, nunca reales).
- 1 `Profesional` vinculado a ese usuario.
- 1 `Sillon` ("Sillón 1") — el recurso por defecto del MVP.
- Prestaciones de ejemplo (**Suposición:** nombres y duraciones ilustrativas, sin fuente de mercado): Consulta / control 30 min; Limpieza 45 min; Obturación 60 min; Extracción 45 min; Urgencia 30 min. Cada una con un color.
- Horario recurrente de ejemplo: lunes a viernes 09:00-13:00 y 15:00-19:00 (**Suposición**).
- 2-3 pacientes ficticios (nombres inventados, teléfonos con prefijo de prueba, sin DNI real).

## A confirmar por el autor

Elecciones de este archivo sin respaldo en la KB (marcadas con † en las tablas); **Suposiciones** del agente del 2026-10-03:

1. `decimal(12,2)` para dinero y columna `JSON` genérica para `antes`/`despues`, `preferencias` y `contenido`.
2. Claves foráneas con `ON DELETE RESTRICT` y enums de texto para todos los enums (la decisión del autor cubre solo `estado` del turno).
3. `UsuarioRol` con el rol como texto (sin tabla `Rol`).
4. `Prestacion.reservable_online` con default `false`; formato `#RRGGBB` de `color` y E.164 del teléfono validados en la API.
5. Nombre del campo `vencimiento_oferta_horas` y de `Evolucion.corrige_a_id`.
6. Índices no pedidos por una regla: Paciente `(consultorio_id, telefono_whatsapp)` sin `UNIQUE`, `Bloqueo`, `EntradaListaEspera` `(estado, creada_en)`, `Mensaje` `(estado, programado_para)`.
7. `CHECK` adicionales: `vigente_hasta >= vigente_desde`, `Mensaje` con `turno_id` u `oferta_id` no nulo, y `monto_sena` obligatorio si `requiere_sena` (esto último en el dominio).
8. Columnas `creado_por` y `registrado_por` nulas hasta que exista `Usuario`; `Consultorio.creado_en` fuera del primer change.
9. `Anamnesis.contenido` como JSON no nulo.
10. `Consentimiento.ip` (ya era Suposición).
11. Los nombres de changes de la columna «Change que la crea» (descriptivos; los fija el roadmap).
