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
Consultorio 1──N Usuario 1──N UsuarioRol   (el rol es un texto en UsuarioRol; no existe tabla Rol)
Consultorio 1──N Profesional ──(0..1)── Usuario
Consultorio 1──N Sillon                (MVP: exactamente 1, creado por seed)
Consultorio 1──N Prestacion
Profesional 1──N FranjaHoraria         (horario recurrente semanal)
Profesional 1──N Bloqueo ; Sillon 1──N Bloqueo   (bloqueo de profesional, de sillón o de todo el consultorio)

Paciente 1──N Turno N──1 Profesional
                Turno N──1 Sillon
                Turno N──1 Prestacion
Turno 1──N EventoTurno                 (historial inmutable)
Turno 1──0..1 Sena                    (el pago de la seña vive en Sena)
Turno 1──N Mensaje

Paciente 1──N EntradaListaEspera N──1 Prestacion
EntradaListaEspera 1──N OfertaHueco N──0..1 Turno (el turno creado al aceptar)

Paciente 1──N Consentimiento
Paciente 1──N Anamnesis (versionada) N──1 Usuario   (registrada_por)
Paciente 1──N Evolucion N──0..1 Turno ; Evolucion N──1 Usuario   (registrada_por)
Paciente 1──N Presupuesto 1──N ItemPresupuesto N──0..1 Prestacion
Paciente 1──N RegistroPago
```

## Convenciones comunes

Todas las entidades se describen con el mismo nivel de detalle: tabla de campos con tipo, nullability (**NN** = no nulo), restricciones y claves foráneas, más los índices. Los tipos son lógicos y se mapean a SQLAlchemy 2.x. El signo **(†)** marca una elección sin respaldo en la KB que el autor aceptó como **propuesta vigente** (2026-10-03, D28), **confirmó tras leer el modelo completo** (2026-10-05, D47) y que se sigue revisando en el `design.md` del change; el signo **(‡)** marcó las Suposiciones nuevas del agente (2026-10-03): **ya no queda ninguna sin confirmar** (2026-10-05, D55). Ambas están en la lista del final del archivo.

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
| `antelacion_cancelacion_horas` | entero | NN | Default 24; `CHECK` entre 24 y 48 (RN-TD-03; también define cuándo una reserva exige la aceptación explícita de RN-TD-10). Se usa el valor **vigente al momento de la cancelación**, no el de la creación del turno (D33) |
| `horizonte_reserva_dias` | entero | NN | Default 60; `CHECK > 0` (RN-TD-01) |
| `antelacion_minima_reserva_horas` | entero | NN | Default 2; `CHECK >= 0` (RN-TD-02, confirmado por el autor el 2026-10-02) |
| `aprobacion_manual_pacientes_nuevos` | bool | NN | Default `false` (RN-TD-05) |
| `requiere_sena` | bool | NN | Default `false`: la seña es opcional (R-03, SU-07). **No tiene efecto hasta el change de seña (US-050)**, que crea `Sena` (D99) |
| `monto_sena` | decimal | null | `CHECK > 0` si no es nulo; obligatorio si `requiere_sena` (validado en el dominio †) |
| `vencimiento_sena_minutos` | entero | NN | Default **30**; `CHECK > 0` (RN-SP-03; decisión del autor 2026-10-03) |
| `vencimiento_oferta_horas` | entero | NN | Default **2**; `CHECK > 0` (RN-LE-03; decisión del autor 2026-10-03; nombre del campo †) |
| `granularidad_agenda_minutos` | entero | NN | Default 5; `CHECK > 0` (P-14; configurable). Hasta que este change exista, las historias anteriores (US-001, US-012) usan 5 como constante (D99) |
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
| `activo` | bool | NN | Default `true`; un usuario inactivo no inicia sesión y, si ya tenía sesión, recibe `401` en la siguiente petición y en el refresh (RN-AU-04; decisión del autor 2026-10-05, D43) |
| `token_version` | entero | NN | Default 0. Viaja como claim dentro del access token y del refresh token y se compara en cada petición autenticada y en el refresh; si no coincide, `401`. Se **incrementa** al desactivar al usuario y al cambiar o restablecer su contraseña, con lo que todos los tokens emitidos antes dejan de valer (también si el usuario se reactiva después) (RN-AU-03; D43) |
| `creado_en` | fecha-hora | NN | — |

`UsuarioRol` (N:N entre usuario y rol; el rol es un enum de texto, sin tabla `Rol` †). Asignar el rol `odontologo` a otro usuario **no crea un `Profesional`** (ver `Profesional`):

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `usuario_id` | entero | NN | FK → Usuario; parte de la PK compuesta |
| `rol` | texto | NN | Valores: `odontologo`, `recepcionista`, `dueno`; parte de la PK compuesta |

### Profesional
**Change que la crea:** primer change (sin `usuario_id` ni `matricula`). MVP: 1 profesional; el modelo admite N (Fase 2). **En la v1, asignar el rol `odontologo` a otro usuario no crea un `Profesional`:** el único profesional queda vinculado al usuario del seed; un segundo profesional es **Fase 2** (multi-profesional) (decisión del autor 2026-10-05, D46).

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
**Change que la crea:** primer change con `nombre`, `apellido` y `telefono_whatsapp`. **`es_nuevo` la agrega el change de marcado atendido / ausente (US-014)**, el primero que la cambia (D99). **`dni`, `email`, `fecha_nacimiento`, `creado_en` y `acepta_contacto` las agrega el change de pacientes desde el panel (US-016)** (decisión del autor 2026-10-05, D95); el primer change que **aplica** `acepta_contacto` es el de recordatorios (US-030), el primero que prepara mensajes. **Datos siempre ficticios en seeds, tests y ejemplos** (RN-PR-01).

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
| `es_nuevo` | bool | NN | Default `true`; se usa para la aprobación manual (RN-TD-05). Pasa a `false` cuando el paciente tiene su **primer turno `atendido`**; una corrección posterior `atendido` → `ausente` **no lo revierte** (RN-TD-05; decisión del autor 2026-10-05, D52) |
| `acepta_contacto` | bool | NN | Default `true`. Con `false` no se prepara ningún mensaje ni se le ofrecen huecos de la lista de espera; la tarea periódica lo verifica justo antes de cada mensaje, incluidos los ya programados. Lo cambia el odontólogo o la recepcionista desde el panel. No afecta la ficha clínica, los turnos ni el link de gestión (RN-PR-07; decisión del autor 2026-10-05, D81) |
| `creado_en` | fecha-hora | NN | — |

Índice: `(consultorio_id, telefono_whatsapp)` para buscar al paciente, **sin `UNIQUE`** (†; SU-03: sin DNI, la búsqueda se apoya en el teléfono). Motivo de no hacerlo único: una madre o un padre puede reservar para sus hijos con el mismo número, por lo que varios pacientes distintos pueden compartir teléfono (decisión del autor 2026-10-05, D48).

**Reutilización en la reserva pública** (RN-TD-09; D48): la reserva pública y el alta en lista de espera **reutilizan un `Paciente` existente solo si coinciden los tres: teléfono, nombre y apellido normalizados**; si difiere cualquiera, crean un paciente nuevo. **Normalizado:** teléfono en E.164; nombre y apellido sin distinguir mayúsculas, sin acentos y sin espacios de más. El formulario público **no pisa datos ya cargados**: los opcionales (DNI, email) solo se completan si estaban vacíos (RN-PR-06). **Limitación conocida:** un error de tipeo («Gonzalez» / «Gonzales») crea un paciente duplicado, que vuelve a dar el consentimiento y puede tener su propia entrada en la lista de espera; la fusión manual de duplicados es **Fase 2**.

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
| `token_gestion` | texto | null | `UNIQUE` si no es nulo; firmado, para el link del paciente. La columna la crea el change de reserva pública (US-020), que además **genera el token de los turnos ya existentes**: desde entonces **todo turno tiene token, también el cargado desde el panel**, y sirve para el mismo flujo de gestión (D94). No tiene vencimiento propio: su validez sale del estado del turno (RN-TD-08, D77) |
| `creado_por` | entero | null | FK → Usuario (columna agregada cuando existe `Usuario` †) |
| `creado_en` | fecha-hora | NN | — |
| `actualizado_en` | fecha-hora | NN | — |
| `version` | entero | NN | Default 1; bloqueo optimista |

Índices: `(profesional_id, inicio, fin)` y `(sillon_id, inicio, fin)` para la búsqueda de solapamientos.

DD-04 confirmada por el autor (2026-10-02). **Decidido el qué (2026-10-05, D75):** en PostgreSQL se **agrega** una **restricción de exclusión** (por profesional y por sillón, solo estados activos, sobre el intervalo semiabierto `[inicio, fin)`) **además** de la validación de dominio de RN-AG-05/08; en SQLite (tests) la regla se valida solo en la capa de dominio. **Estado efectivo y estado persistido (D92):** la restricción mira el estado persistido y RN-AG-10 cuenta el efectivo; por eso la escritura que ocupa un horario con un turno `pendiente_sena` de seña vencida persiste antes ese vencimiento (turno a `vencido`, seña a `vencida`) en su misma transacción, sin disparar efectos (RN-GL-05 (a)). El **cómo** exacto (el SQL, la extensión `btree_gist`) queda para el design del change de infraestructura con PostgreSQL. **A verificar en el change** (verificar en el change de infraestructura con PostgreSQL, antes del change de reserva online): que la restricción funcione con los estados activos y con `[inicio, fin)`. Ver DD-04 y RN-AG-10c.

#### Máquina de estados del turno

```
(reserva) ──┬──► reservado ──(confirma)──► confirmado                          (caso normal)
            │
            ├──► pendiente_sena ──(pago acreditado)──► reservado
            │          └──(seña impaga)──► vencido
            │
            └──► pendiente_aprobacion ──(aprueba, sin seña exigida)──► reservado
                        ├──(aprueba, con seña exigida)──► pendiente_sena
                        └──(rechaza)──► cancelado_profesional

   cualquier estado activo ──► cancelado_paciente | cancelado_profesional
   reservado/confirmado ──(se atiende)──► atendido      reservado/confirmado ──(no asiste)──► ausente
   atendido ◄──(corrección, ≤ 24 h, solo odontólogo)──► ausente
```

- **Estados activos (ocupan el horario):** `pendiente_aprobacion`, `pendiente_sena`, `reservado`, `confirmado`.
- **Estados terminales (liberan el horario):** `cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido`, `ausente`. **Excepción:** `atendido` y `ausente` admiten una corrección entre sí (ver la tabla de transiciones); ambos siguen siendo no activos y la corrección no tiene efecto sobre los solapamientos.
- **Reprogramar** no es un estado: cambia `inicio/fin` del mismo turno y registra un `EventoTurno` de tipo `reprogramado` (DD-05).

**Tabla de transiciones válidas** (decisión del autor 2026-10-03, D19; derivada del diagrama anterior). Cualquier otro cambio de estado se rechaza con el error de dominio `RN-AG-12` (ver `05_reglas_de_negocio.md`):

| Desde | Hacia | Cuándo |
|---|---|---|
| (reserva) | `reservado` | Caso normal |
| (reserva) | `pendiente_sena` | Se exige seña (RN-SP-02) |
| (reserva) | `pendiente_aprobacion` | Paciente nuevo con aprobación manual activa (RN-TD-05); si además se exige seña, la `Sena` se crea recién al aprobar |
| `pendiente_aprobacion` | `reservado` | El odontólogo aprueba y no se exige seña (RN-TD-05) |
| `pendiente_aprobacion` | `pendiente_sena` | El odontólogo aprueba y se exige seña: la `Sena` se crea en ese momento y su plazo de pago (`vence_en`) empieza ahí (RN-TD-05, RN-SP-02; D76) |
| `pendiente_aprobacion` | `cancelado_profesional` | El odontólogo rechaza (RN-TD-05); libera el horario y dispara RN-LE-01 (D76) |
| `pendiente_sena` | `reservado` | Pago de la seña acreditado (RN-SP-02) |
| `pendiente_sena` | `vencido` | La seña no se acredita a tiempo (RN-SP-03); la seña pasa a `vencida` |
| `reservado` | `confirmado` | El paciente o el consultorio confirman |
| `reservado`, `confirmado` | `atendido` | Se atiende (RN-AG-13) |
| `reservado`, `confirmado` | `ausente` | El paciente no asiste (RN-AG-13) |
| `atendido` | `ausente` | Corrección del marcado: solo el rol `odontologo`, dentro de las 24 horas posteriores al marcado original (RN-AG-13; D34) |
| `ausente` | `atendido` | Corrección del marcado: solo el rol `odontologo`, dentro de las 24 horas posteriores al marcado original (RN-AG-13; D34) |
| cualquier estado activo | `cancelado_paciente`, `cancelado_profesional` | Cancelación |

Los estados terminales no tienen transiciones de salida, **salvo la corrección entre `atendido` y `ausente`** (dos últimas filas con condición). El momento del marcado original sale del historial `EventoTurno`; la seña no acompaña la corrección (RN-SP-10). Marcar `atendido` o `ausente` solo es posible si `ahora >= inicio` del turno (RN-AG-13). El rechazo de la aprobación manual (RN-TD-05) lleva a `cancelado_profesional`, sin estado nuevo (decisión del autor 2026-10-05, D76). Los vencimientos se evalúan al consultar y los persiste la tarea periódica o, antes, la escritura que depende de ellos (RN-GL-05, D92).

### EventoTurno (historial de cambios)
**Change que la crea:** historial de cambios de turno (US-015); **no entra en el primer change** (decisión del autor 2026-10-03). **Inmutable**: solo inserción (RN-AG-11).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `turno_id` | entero | NN | FK → Turno |
| `tipo` | texto | NN | Valores: `creado`, `reprogramado`, `confirmado`, `cancelado`, `estado_cambiado`, `sena_acreditada`, `sena_retenida`, `sena_devuelta`, `nota` |
| `actor_tipo` | texto | NN | Valores: `usuario`, `paciente`, `sistema`, `webhook_mp`. `webhook_wa` se agrega en Fase 2 |
| `actor_id` | texto | null | Id del usuario o del token, según `actor_tipo` |
| `ocurrido_en` | fecha-hora | NN | — |
| `antes` | json | null | Estado previo (horario, estado). En una corrección de marcado, el valor anterior (`atendido` o `ausente`) |
| `despues` | json | null | Estado nuevo. En el evento `creado` de una reserva con menos antelación que la ventana de cancelación, registra además la **aceptación explícita** del paciente (RN-TD-10, D87) |
| `motivo` | texto | null | — |

Índice: `(turno_id, ocurrido_en)`. Ni la aplicación ni la base exponen `UPDATE` ni `DELETE` sobre esta tabla.

### EntradaListaEspera
**Change que la crea:** lista de espera (US-021).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `consultorio_id` | entero | NN | FK → Consultorio |
| `paciente_id` | entero | NN | FK → Paciente |
| `prestacion_id` | entero | NN | FK → Prestacion. **Obligatoria** (decisión del autor 2026-10-05, D78, que corrige D53): el turno exige una prestación, así que una entrada sin ella no podría convertirse en turno al aceptar la oferta |
| `preferencias` | json | NN | Lista de franjas preferidas `{dia_semana, desde, hasta}`, con `dia_semana` entre 0 (lunes) y 6 (domingo) y `desde` y `hasta` en **hora del consultorio**. **Lista vacía = cualquier horario** (RN-LE-01; D78). Un hueco es compatible si el **tramo común** entre el hueco y alguna franja alcanza para la duración de la prestación; no se exige que el hueco entre entero en la franja (RN-LE-01; D88) |
| `estado` | texto | NN | Default `activa`. Valores: `activa`, `ofertada`, `asignada`, `retirada` (no hay estado `vencida` en la entrada: lo que vence es la oferta, D53) |
| `creada_en` | fecha-hora | NN | Define la prioridad FIFO (RN-LE-02) |
| `token` | texto | NN | `UNIQUE`; firmado, para que el paciente se retire desde su link (RN-LE-06). Es propio de la entrada porque el token de gestión identifica un único turno (RN-TD-08) y en la lista de espera todavía no hay turno (D29) |

Índice: `(estado, creada_en)` (†). Se llega a `retirada` de **dos formas** (decisión del autor 2026-10-03, D20): el paciente se retira desde su link, o el consultorio lo retira desde el panel (RN-LE-06). Al anotarse se exige el consentimiento de datos (RN-LE-05). **Oferta rechazada o vencida:** la entrada vuelve a `activa` **conservando su lugar** (su `creada_en` no cambia) (RN-LE-03; decisión del autor 2026-10-05, D53). **Retiro con oferta en curso:** una entrada `ofertada` también puede pasar a `retirada` (el paciente desde su link o el consultorio desde el panel); su oferta se da por rechazada y el hueco pasa al siguiente (RN-LE-06; decisión del autor 2026-10-05, D60). **Unicidad:** hay una sola entrada **en curso** (`activa` u `ofertada`) por paciente y prestación (RN-LE-07); se valida en el dominio (D35, D60); como la prestación es obligatoria, no existe una entrada «cualquier prestación» (D78). El paciente se reconoce según RN-TD-09 (D48). **Aviso al odontólogo (RN-LE-08, D78):** una entrada en curso con más de 7 días sin una oferta compatible (desde `creada_en` o desde su última `OfertaHueco`, lo más reciente) se señala en el panel; se calcula al consultar y no requiere un campo. **Alta desde el panel (D103):** el consultorio también puede anotar a un paciente; el consentimiento se registra con origen `panel` (RN-LE-05).

### OfertaHueco
**Change que la crea:** oferta de huecos (US-040).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `entrada_id` | entero | NN | FK → EntradaListaEspera |
| `inicio` | fecha-hora | NN | `CHECK inicio < fin`. Es el **primer inicio posible dentro del tramo común** entre el hueco y la franja preferida, respetando la granularidad de la agenda (RN-LE-01; D88). Exige `inicio ≥ ahora + antelacion_minima_reserva_horas` (RN-TD-02); nunca un tramo pasado (D97) |
| `fin` | fecha-hora | NN | `inicio` + duración de la prestación de la entrada (no el fin del hueco) (RN-LE-01; D88). Si el hueco es más largo, el resto se ofrece en la misma corrida a la siguiente entrada compatible (D97) |
| `profesional_id` | entero | NN | FK → Profesional |
| `sillon_id` | entero | NN | FK → Sillon |
| `token` | texto | NN | `UNIQUE`; firmado, para aceptar o rechazar |
| `enviada_en` | fecha-hora | NN | Con `wa.me`, el momento en que la oferta queda preparada en el panel |
| `vence_en` | fecha-hora | NN | `enviada_en` + `vencimiento_oferta_horas` (2 h por defecto, RN-LE-03) |
| `estado` | texto | NN | Valores: `enviada`, `aceptada`, `rechazada`, `vencida` |
| `turno_id` | entero | null | FK → Turno (el turno creado al aceptar) |

Índice: `(entrada_id)`. **Hueco** (RN-LE-01, D97): tramo libre contiguo, dentro del horario del profesional y sin bloqueos, que queda al liberarse un turno (el intervalo liberado más el tiempo libre adyacente). Una oferta enviada **no bloquea** el horario: no hay turno hasta que se acepta, y RN-LE-04 revalida al aceptar. Aceptar una oferta efectivamente vencida la persiste como `vencida` y se rechaza (RN-GL-05 (c), D92).

### Mensaje
**Change que la crea:** recordatorios por WhatsApp (US-030).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `turno_id` | entero | null | FK → Turno |
| `oferta_id` | entero | null | FK → OfertaHueco |
| `tipo` | texto | NN | Valores: `recordatorio` (US-030), `confirmacion` (mensaje con el link de gestión que se prepara al crearse un turno, US-030; D93), `oferta_hueco` (US-040) y `aviso_cancelacion` (**reservado**: ninguna historia de la v1 lo usa) |
| `canal` | texto | NN | Valor v1: `wa_me`. `cloud_api` se agrega en Fase 2 |
| `estado` | texto | NN | Valores v1: `programado`, `generado_link`, `enviado` (el odontólogo lo marca al enviarlo) y `descartado` (el mensaje ya no corresponde: el paciente dejó de aceptar contacto, RN-PR-07, D81, o el turno dejó de estar activo antes de prepararlo; la tarea periódica no lo genera o lo retira antes de enviarlo). `entregado`, `respondido` y `fallido` quedan reservados para la Cloud API (Fase 2). Estados de la v1 confirmados por el autor (2026-10-05, D80, D81) |
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
| `estado` | texto | NN | Valores: `pendiente`, `acreditada`, `retenida`, `devuelta`, `vencida`. Transiciones válidas en la tabla que sigue |
| `mp_preference_id` | texto | null | — |
| `mp_payment_id` | texto | null | `UNIQUE` si no es nulo (idempotencia, RN-SP-08) |
| `creada_en` | fecha-hora | NN | — |
| `vence_en` | fecha-hora | NN | `creada_en` + `vencimiento_sena_minutos` (30 min por defecto, RN-SP-03) |

#### Transiciones válidas de la seña

Decisión del autor 2026-10-05 (D49; ampliada en D59 y D61); derivada de RN-SP-02 a RN-SP-06, RN-SP-10 y RN-SP-11. `devuelta` es **final**. La seña cambia de estado **solo** según esta tabla; cualquier otro cambio se rechaza con el error de dominio `RN-SP-12` («transición de seña inválida»), sin modificar la seña ni el historial (RN-SP-12; espejo de RN-AG-12 para el turno).

| Desde | Hacia | Cuándo |
|---|---|---|
| (creación) | `pendiente` | El turno pasa a `pendiente_sena` y se genera la seña (RN-SP-02): al reservar, o **al aprobar** un turno `pendiente_aprobacion` cuando se exige seña (D76); el plazo `vence_en` cuenta desde ese momento |
| `pendiente` | `acreditada` | El webhook de Mercado Pago acredita el pago (RN-SP-02, RN-SP-08) |
| `pendiente` | `vencida` | El turno `pendiente_sena` pasa a `vencido` porque no se paga a tiempo (RN-SP-03), **o** se cancela mientras la seña sigue `pendiente` (D59). El vencimiento lo persiste la tarea periódica o, antes, una escritura que depende de él (RN-GL-05 (a) y (b), D92) |
| `vencida` | `devuelta` | El webhook acredita el pago cuando el turno **ya no está activo** (`vencido` o cancelado); el turno no cambia (RN-SP-11, D59). Si la seña estaba efectivamente vencida sin persistir, el webhook persiste en la misma transacción `pendiente` → `vencida` y el turno a `vencido` antes de este paso (RN-GL-05 (b), D92) |
| `acreditada` | `retenida` | El paciente queda `ausente` (RN-SP-04 (a)); el consultorio carga desde el panel la cancelación del paciente fuera de plazo (RN-SP-04 (b)); retención manual del odontólogo tras corregir `atendido` → `ausente` (RN-SP-10; exige que el turno esté `ausente`, D101) |
| `acreditada` | `devuelta` | Cancela el odontólogo (RN-SP-05); cancela el paciente dentro de plazo (RN-SP-06) |
| `retenida` | `devuelta` | Devolución manual del odontólogo tras corregir `ausente` → `atendido` (RN-SP-10; exige que el turno esté `atendido`, D101) |

Las transiciones manuales (RN-SP-10) solo las hace el rol `odontologo` y quedan en el historial (`sena_retenida`, `sena_devuelta`). En el prototipo la devolución solo se registra. Una acción manual con el turno en otro estado se rechaza con `RN-SP-12` (D101). El estado `vencida` por vencimiento lo evalúa la consulta y lo persiste la tarea periódica o, antes, una escritura que depende de él (RN-SP-03, RN-GL-05, D92).

### RegistroPago
**Change que la crea:** registro de pago simple (US-062). Registro **simple** (no es caja; la caja completa es v2). **Pagos parciales = varios registros. Un registro no se edita**: se corrige con un registro nuevo que apunta al anterior mediante `corrige_a_id`, y el apuntado deja de contar en los totales (RN-SP-09; decisión del autor 2026-10-03, D24). Anular **sin reemplazar** se hace con un registro nuevo con `es_anulacion = true` (decisión del autor 2026-10-05, D31). El pago de la seña vive en `Sena`, no en esta tabla (D27). **Decisión del autor 2026-10-03:** el pago se asocia al paciente y, opcionalmente, a un presupuesto o a un turno; US-061 (presupuesto) **no es dependencia** de US-062. Por eso, si US-062 se implementa antes que US-061, la columna `presupuesto_id` se agrega con el change de US-061, que es quien crea la tabla `Presupuesto`.

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
| `registrado_por` | entero | null | FK → Usuario (†). El webhook de Mercado Pago no crea registros en esta tabla: el pago de la seña vive en `Sena` (D27) |
| `es_anulacion` | bool | NN | Default `false`. `true` si este registro anula a otro sin reemplazarlo (D31) |
| `corrige_a_id` | entero | null | FK → RegistroPago; el registro que este corrige o anula (D24, D31). **Obligatorio si `es_anulacion = true`** (`CHECK`). **`UNIQUE` si no es nulo**: un registro se corrige o anula una sola vez. **No puede apuntar a un registro de anulación** (validado en el dominio) |

Dos usos de `corrige_a_id` (decisión del autor 2026-10-05, D31):

- **Corrección con reemplazo:** registro nuevo con `es_anulacion = false` que apunta al anterior; el anterior deja de contar y el nuevo cuenta.
- **Anulación sin reemplazo:** registro nuevo con `es_anulacion = true` que apunta al original, **copia su monto y su medio** (el `CHECK monto > 0` sigue valiendo) y lleva `pagado = true` (la anulación se registra como operación hecha y no cuenta en nada).

**Cálculo (RN-SP-09):** los **totales** son los registros con `pagado = true`, `es_anulacion = false` y que ningún `corrige_a_id` apunte; los **pendientes** son los registros con `pagado = false`, `es_anulacion = false` y que ningún `corrige_a_id` apunte. Un registro de anulación nunca aparece en totales ni en pendientes, pero **sí en el historial de pagos del paciente** (trazabilidad). Un registro apuntado por un `corrige_a_id` (anulado o reemplazado) tampoco cuenta en totales ni en pendientes.

### Consentimiento
**Change que la crea:** consentimiento de datos (US-070). El texto de consentimiento es un **borrador, no validado legalmente** (decisión del autor 2026-10-03, ver P-03). Si cambia la versión del texto, se vuelve a pedir en la siguiente reserva del paciente (RN-PR-02; decisión del autor 2026-10-03, D25); la versión vigente es una constante de la aplicación (decisión del autor 2026-10-05, D30). El texto vigente (`v1-borrador`) está en `05_reglas_de_negocio.md`, sección «Texto de consentimiento — versión `v1-borrador`» (D57).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `paciente_id` | entero | NN | FK → Paciente |
| `version_texto` | texto | NN | Versión del texto aceptado (RN-PR-02); hoy `v1-borrador`, ver la sección «Texto de consentimiento» de `05_reglas_de_negocio.md` |
| `aceptado_en` | fecha-hora | NN | — |
| `origen` | texto | NN | Valores: `link_publico`, `panel` |

No se guarda la IP del paciente: dato personal sin uso definido; minimización (Ley 25.326) (decisión del autor 2026-10-05, D51).

### Anamnesis
**Change que la crea:** ficha clínica (US-060). Se versiona, no se sobrescribe (RN-FC-03). **Campos simples y opcionales** (decisión del autor 2026-10-03, D22): se eligieron **columnas de texto** en lugar de un JSON genérico por ser lo más simple y portable entre SQLite y PostgreSQL (elección del agente, †).

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `paciente_id` | entero | NN | FK → Paciente |
| `alergias` | texto | null | Opcional (decisión del autor 2026-10-03, D22) |
| `medicacion` | texto | null | Opcional |
| `enfermedades` | texto | null | Opcional |
| `observaciones` | texto | null | Opcional |
| `version` | entero | NN | `UNIQUE(paciente_id, version)` |
| `registrada_por` | entero | NN | FK → Usuario: quien inició sesión (D50) |
| `registrada_en` | fecha-hora | NN | — |

### Evolucion
**Change que la crea:** ficha clínica (US-060). Solo inserción; las correcciones se hacen con una nueva entrada que referencia a la anterior.

| Campo | Tipo | Null | Restricciones / FK / nota |
|---|---|---|---|
| `id` | entero | NN | PK |
| `paciente_id` | entero | NN | FK → Paciente |
| `turno_id` | entero | null | FK → Turno |
| `texto` | texto | NN | — |
| `registrada_por` | entero | NN | FK → Usuario: quien inició sesión y registró la evolución, igual que `Anamnesis.registrada_por` (decisión del autor 2026-10-05, D50) |
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
| `estado` | texto | NN | Default `borrador`. Valores: `borrador`, `entregado`, `aceptado`, `rechazado`. Transiciones: `borrador` → `entregado` → `aceptado` o `rechazado`; `aceptado` y `rechazado` son finales; solo el odontólogo cambia el estado (RN-FC-05; decisión del autor 2026-10-03, D23) |
| `total` | decimal | NN | Calculado desde los ítems (RN-FC-04) |
| `observaciones` | texto | null | — |

`ItemPresupuesto` (los ítems solo se agregan, editan o quitan mientras el presupuesto está en `borrador`, y para pasar a `entregado` hace falta al menos uno: RN-FC-04, D36):

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
**Columnas que NO crea** (las agregan los changes indicados en cada tabla): `Consultorio.creado_en` †; `Profesional.usuario_id`, `matricula`; `Prestacion.color`, `reservable_online`; `Paciente.dni`, `email`, `fecha_nacimiento`, `es_nuevo`, `acepta_contacto`, `creado_en`; `Turno.origen`, `token_gestion`, `creado_por`, `actualizado_en`, `version`.
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
- Prestaciones de ejemplo (**datos ilustrativos confirmados por el autor el 2026-10-05, D56**, sin fuente de mercado): Consulta / control 30 min; Limpieza 45 min; Obturación 60 min; Extracción 45 min; Urgencia 30 min. Cada una con un color.
- Horario recurrente de ejemplo: lunes a viernes 09:00-13:00 y 15:00-19:00 (dato ilustrativo confirmado por el autor el 2026-10-05, D56, sin fuente de mercado).
- 2-3 pacientes ficticios (nombres inventados, teléfonos con prefijo de prueba, sin DNI real).

## Propuestas aceptadas y Suposiciones resueltas

**Propuestas aceptadas por el autor (2026-10-03, D28); confirmadas tras leer el modelo completo (2026-10-05, D47: tablas, tipos, índices y estas propuestas); se siguen revisando en el `design.md` de cada change** (marcadas con † en las tablas):

1. `decimal(12,2)` para dinero y columna `JSON` genérica para `antes`/`despues` y `preferencias`.
2. Claves foráneas con `ON DELETE RESTRICT` y enums de texto para todos los enums.
3. `UsuarioRol` con el rol como texto (sin tabla `Rol`).
4. `Prestacion.reservable_online` con default `false`; formato `#RRGGBB` de `color` y E.164 del teléfono validados en la API.
5. Nombre del campo `vencimiento_oferta_horas` y de `Evolucion.corrige_a_id`.
6. Índices no pedidos por una regla: Paciente `(consultorio_id, telefono_whatsapp)` sin `UNIQUE`, `Bloqueo`, `EntradaListaEspera` `(estado, creada_en)`, `Mensaje` `(estado, programado_para)`.
7. `CHECK` adicionales: `vigente_hasta >= vigente_desde`, `Mensaje` con `turno_id` u `oferta_id` no nulo, y `monto_sena` obligatorio si `requiere_sena` (esto último en el dominio).
8. Columnas `creado_por` y `registrado_por` nulas hasta que exista `Usuario`; `Consultorio.creado_en` fuera del primer change.
9. ~~`Consentimiento.ip`.~~ **Quitado por el autor (2026-10-05, D51):** dato personal sin uso definido.
10. Los nombres de changes de la columna «Change que la crea» (descriptivos; los fija el roadmap).
11. Anamnesis como cuatro columnas de texto en lugar de un JSON (D22).

**Suposiciones nuevas de esta tanda (‡); resueltas todas el 2026-10-05, ya no queda ninguna pendiente:**

1. ~~`EntradaListaEspera.token` y la ruta pública para retirarse desde el link.~~ **Confirmada por el autor (2026-10-05, D29).**
2. ~~La versión vigente del texto de consentimiento como constante de la aplicación.~~ **Confirmada por el autor (2026-10-05, D30).**
3. ~~Anular un pago sin reemplazo con un registro nuevo (`corrige_a_id`, `pagado` falso).~~ **Reemplazada por el autor (2026-10-05, D31):** campo `es_anulacion`, ver `RegistroPago`.
4. ~~La tabla de transiciones válidas del turno se derivó del diagrama.~~ **Confirmada por el autor (2026-10-05, D55).** El destino del rechazo de la aprobación manual, que quedaba «No definido», se definió el mismo día: `cancelado_profesional` (D76).
5. ~~Los IDs nuevos de regla.~~ **Confirmados por el autor (2026-10-05, D55):** RN-AG-12, RN-AG-13, RN-LE-05, RN-LE-06, RN-LE-07, RN-SP-09, RN-SP-10, RN-SP-11, RN-FC-05, RN-RP-01 a RN-RP-03 y las reglas creadas el 2026-10-05 (RN-TD-09, RN-AU-06, RN-AU-07).
