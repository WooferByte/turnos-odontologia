# Modelo de Datos

> Convención: tipos lógicos (se mapean a SQLAlchemy). Todas las fechas-hora se guardan **con zona horaria (UTC)** y se presentan en `America/Argentina/Buenos_Aires` (ver DD-09). Los identificadores son enteros autoincrementales o UUID (**Suposición:** UUID para entidades expuestas por link público, para no ser enumerables).

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

## Entidades

### Consultorio
- `id`, `nombre: str`, `slug: str` (único; usado en el link público), `zona_horaria: str` (default `America/Argentina/Buenos_Aires`), `creado_en: datetime`.

### ConfiguracionReglas (1:1 con Consultorio)
Valores **por defecto propuestos por el autor** (no estándares de mercado), todos editables (ver `05_reglas_de_negocio.md`):
- `antelacion_cancelacion_horas: int` = 24 (rango permitido 24-48) — RN-TD-03.
- `horizonte_reserva_dias: int` = 60 — RN-TD-01.
- `antelacion_minima_reserva_horas: int` = 2 — RN-TD-02.
- `aprobacion_manual_pacientes_nuevos: bool` = false — RN-TD-05.
- `requiere_sena: bool` = **Suposición:** false por defecto (la seña es opcional por riesgo R-03).
- `monto_sena: decimal | null`, `vencimiento_sena_minutos: int | null` (**Suposición**, ver pregunta abierta).
- `granularidad_agenda_minutos: int` = **Suposición:** 5 (paso para calcular huecos).
- `recordatorio_horas_antes: int` = 24 — RN-WA-01.
- `canal_whatsapp: enum(cloud_api, wa_me)`.

### Usuario / UsuarioRol
- `id`, `consultorio_id`, `email: str` (único), `hash_password: str`, `activo: bool`.
- Roles: `odontologo | recepcionista | dueno` (N:N).

### Profesional
- `id`, `consultorio_id`, `usuario_id: FK | null`, `nombre: str`, `matricula: str | null`, `activo: bool`.
- MVP: 1 profesional. El modelo admite N (Fase 2).

### Sillon (recurso)
- `id`, `consultorio_id`, `nombre: str` (p. ej. "Sillón 1"), `activo: bool`.
- **MVP: un único sillón creado por seed; todo turno se asigna a él por defecto** (RN-AG-06).

### Prestacion
- `id`, `consultorio_id`, `nombre: str`, `duracion_minutos: int` (> 0, múltiplo de la granularidad), `color: str` (hex), `reservable_online: bool`, `activa: bool`.
- Constraint: `UNIQUE(consultorio_id, nombre)`.
- La duración es **por defecto**: el turno guarda su propia duración/fin (RN-AG-02).

### FranjaHoraria (horario recurrente)
- `id`, `profesional_id`, `dia_semana: int` (0=lunes … 6=domingo), `hora_inicio: time`, `hora_fin: time`, `vigente_desde: date | null`, `vigente_hasta: date | null`.
- Constraint: `hora_inicio < hora_fin`; las franjas de un mismo profesional y día no se superponen.

### Bloqueo
- `id`, `consultorio_id`, `profesional_id: FK | null`, `sillon_id: FK | null` (ambos null = bloquea todo el consultorio), `inicio: datetime`, `fin: datetime`, `motivo: str` (vacaciones, feriado, ausencia, mantenimiento), `creado_por`.
- Constraint: `inicio < fin`.

### Paciente
- `id`, `consultorio_id`, `nombre: str`, `apellido: str`, `dni: str | null`, `telefono_whatsapp: str` (E.164), `email: str | null`, `fecha_nacimiento: date | null`, `es_nuevo: bool`, `creado_en`.
- **Datos siempre ficticios en seeds, tests y ejemplos** (RN-PR-01).
- **Suposición:** identificación del paciente en la reserva pública por teléfono + DNI (Bilog usa DNI + email [C] como referencia).

### Turno
- `id`, `consultorio_id`, `paciente_id`, `profesional_id`, `sillon_id`, `prestacion_id`.
- `inicio: datetime`, `fin: datetime` (calculado como `inicio + duracion` y persistido), `duracion_minutos: int`.
- `estado: enum` — ver máquina de estados abajo.
- `origen: enum(panel, link_publico, lista_espera)`.
- `token_gestion: str` (firmado, para el link del paciente), `creado_por`, `creado_en`, `actualizado_en`, `version: int` (bloqueo optimista).
- Constraints: `inicio < fin`; índices `(profesional_id, inicio, fin)` y `(sillon_id, inicio, fin)` para la búsqueda de solapamientos.
- **Suposición (producción):** en PostgreSQL se puede reforzar RN-AG-05/08 con una restricción de exclusión (`EXCLUDE USING gist` sobre `tstzrange(inicio, fin, '[)')` filtrada por estados activos). En SQLite (tests) la regla se valida en la capa de dominio. Ver DD-04.

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
- `id`, `turno_id`, `tipo: enum(creado, reprogramado, confirmado, cancelado, estado_cambiado, sena_acreditada, nota)`, `actor_tipo: enum(usuario, paciente, sistema, webhook_mp, webhook_wa)`, `actor_id: str | null`, `ocurrido_en: datetime`, `antes: json`, `despues: json`, `motivo: str | null`.
- **Inmutable**: solo inserción (RN-AG-11).

### EntradaListaEspera
- `id`, `paciente_id`, `prestacion_id: FK | null`, `preferencias: json` (días/franjas preferidas), `estado: enum(activa, ofertada, asignada, retirada, vencida)`, `creada_en` (define la prioridad FIFO, RN-LE-02).

### OfertaHueco
- `id`, `entrada_id`, `inicio`, `fin`, `profesional_id`, `sillon_id`, `token`, `enviada_en`, `vence_en`, `estado: enum(enviada, aceptada, rechazada, vencida)`, `turno_id: FK | null`.

### Mensaje
- `id`, `turno_id: FK | null`, `oferta_id: FK | null`, `tipo: enum(recordatorio, confirmacion, oferta_hueco, aviso_cancelacion)`, `canal: enum(cloud_api, wa_me)`, `estado: enum(programado, enviado, entregado, respondido, fallido, generado_link)`, `programado_para`, `enviado_en`, `respuesta: str | null`, `id_externo: str | null`.

### Sena
- `id`, `turno_id` (único), `monto: decimal`, `moneda: str` = `ARS`, `estado: enum(pendiente, acreditada, retenida, devuelta, vencida)`, `mp_preference_id`, `mp_payment_id`, `creada_en`, `vence_en`.

### RegistroPago
- `id`, `paciente_id`, `turno_id: FK | null`, `presupuesto_id: FK | null`, `monto: decimal`, `medio: enum(efectivo, transferencia, mercado_pago, tarjeta, otro)`, `pagado: bool`, `fecha`, `registrado_por`.
- Registro **simple** (no es caja; la caja completa es v2).

### Consentimiento
- `id`, `paciente_id`, `version_texto: str`, `aceptado_en: datetime`, `origen: enum(link_publico, panel)`, `ip: str | null` (**Suposición**).

### Anamnesis
- `id`, `paciente_id`, `contenido: json | text` (antecedentes, alergias, medicación), `version: int`, `registrada_por`, `registrada_en`. Se versiona, no se sobrescribe (RN-FC-03).

### Evolucion
- `id`, `paciente_id`, `turno_id: FK | null`, `texto: text`, `profesional_id`, `registrada_en`. Solo inserción; las correcciones se hacen con una nueva entrada que referencia a la anterior.

### Presupuesto / ItemPresupuesto
- Presupuesto: `id`, `paciente_id`, `fecha`, `estado: enum(borrador, entregado, aceptado, rechazado)`, `total: decimal`, `observaciones`.
- Item: `id`, `presupuesto_id`, `prestacion_id: FK | null`, `descripcion: str`, `cantidad: int`, `precio_unitario: decimal`.

## Seed data inicial

Todos los datos son **ficticios** (RN-PR-01):

- 1 `Consultorio` ("Consultorio Demo", slug `consultorio-demo`) con `ConfiguracionReglas` por defecto.
- 1 `Usuario` con roles `odontologo` + `dueno` (credenciales de prueba definidas en un archivo de ejemplo de entorno, nunca reales).
- 1 `Profesional` vinculado a ese usuario.
- 1 `Sillon` ("Sillón 1") — el recurso por defecto del MVP.
- Prestaciones de ejemplo (**Suposición:** nombres y duraciones ilustrativas, sin fuente de mercado): Consulta / control 30 min; Limpieza 45 min; Obturación 60 min; Extracción 45 min; Urgencia 30 min. Cada una con un color.
- Horario recurrente de ejemplo: lunes a viernes 09:00-13:00 y 15:00-19:00 (**Suposición**).
- 2-3 pacientes ficticios (nombres inventados, teléfonos con prefijo de prueba, sin DNI real).
