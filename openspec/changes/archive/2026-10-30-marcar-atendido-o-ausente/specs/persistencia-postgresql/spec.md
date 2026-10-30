## Purpose

Delta de C-18 (`marcar-atendido-o-ausente`) sobre `persistencia-postgresql`: la migración `0010` agrega `paciente.es_nuevo` con su relleno (US-014 CA-11, RN-TD-05; D361). Un MODIFIED repite el requisito completo: sus escenarios vigentes son copia literal y se suman dos escenarios de la migración nueva, como C-13 sumó los de `0009`. Las convenciones de los escenarios son las del spec vigente; los datos son ficticios (RN-PR-01).

## MODIFIED Requirements

### Requirement: Esquema de PostgreSQL creado por migraciones

El sistema SHALL crear y modificar el esquema de PostgreSQL únicamente con migraciones versionadas y reversibles (DD-15). Una base vacía migrada hasta la última versión SHALL quedar exactamente con el esquema del modelo de datos de la aplicación: sus tablas, columnas, claves e índices, sin tablas de más ni de menos. Las fechas SHALL guardarse con zona (RN-GL-01).

#### Scenario: INF-1 Feliz - una base vacía migrada queda con el esquema del primer change

- **GIVEN** una base PostgreSQL vacía
- **WHEN** se aplican todas las migraciones
- **THEN** existen exactamente las tablas del modelo de datos de la aplicación (desde C-13: `consultorio`, `profesional`, `sillon`, `prestacion`, `paciente`, `turno`, `evento_turno`, `usuario`, `usuario_rol`, `franja_horaria` y `bloqueo`), y ninguna otra tabla de la aplicación
- **AND** comparar el esquema de la base con el modelo de datos de la aplicación no encuentra ninguna diferencia de tablas, columnas, tipos, nulabilidad, claves ni índices
- **AND** toda columna de fecha-hora es una fecha con zona (desde C-13: `inicio`, `fin` y `creado_en` de `turno`, `ocurrido_en` de `evento_turno`, `creado_en` de `usuario` e `inicio` y `fin` de `bloqueo`); las horas de `franja_horaria` son horas del día sin fecha ni zona, porque son horas del consultorio (RN-AG-04)

#### Scenario: INF-1 Borde - deshacer las migraciones deja la base vacía

- **GIVEN** una base PostgreSQL migrada hasta la última versión
- **WHEN** se deshacen todas las migraciones
- **THEN** no queda ninguna tabla, restricción, función ni disparador de la aplicación
- **AND** volver a aplicarlas todas termina sin errores

#### Scenario: INF-1 Borde - deshacer solo las migraciones del historial deja el esquema del primer change

- **GIVEN** una base PostgreSQL migrada hasta la última versión
- **WHEN** se deshacen solo las migraciones del historial, hasta la versión que dejó el change de infraestructura
- **THEN** quedan exactamente las seis tablas del primer change, sin `evento_turno` ni su función ni sus disparadores
- **AND** los turnos guardados siguen en la base

#### Scenario: INF-1 Borde - deshacer solo la migración de usuarios deja el esquema anterior

- **GIVEN** una base PostgreSQL migrada hasta la última versión, con turnos y eventos guardados
- **WHEN** se deshace solo la migración de usuarios, hasta la versión que dejó el change de prestaciones
- **THEN** existen exactamente las tablas anteriores (`consultorio`, `profesional`, `sillon`, `prestacion`, `paciente`, `turno` y `evento_turno`), sin `usuario`
- **AND** los turnos y los eventos guardados siguen en la base
- **AND** volver a aplicar la migración de usuarios termina sin errores

#### Scenario: INF-1 Borde - deshacer solo la migración de roles deja el esquema del change de sesión

- **GIVEN** una base PostgreSQL migrada hasta la última versión, con un usuario con roles, un profesional vinculado a él y un turno creado por él con su evento
- **WHEN** se deshace solo la migración de roles, hasta la versión que dejó el change de sesión
- **THEN** no existe `usuario_rol`, `profesional` no tiene `usuario_id` ni `matricula` y `turno` no tiene `creado_por`
- **AND** el usuario, el profesional, el turno y su evento siguen en la base
- **AND** volver a aplicar la migración de roles termina sin errores

#### Scenario: INF-1 Borde - deshacer solo la migración del horario deja el esquema del change de roles

- **GIVEN** una base PostgreSQL migrada hasta la última versión, con un profesional con franjas y un turno
- **WHEN** se deshace solo la migración del horario, hasta la versión que dejó el change de roles
- **THEN** no existe `franja_horaria` y el resto del esquema es el del change de roles
- **AND** el profesional y el turno siguen en la base
- **AND** volver a aplicar la migración del horario termina sin errores

#### Scenario: INF-1 Borde - la base rechaza una franja inválida

- **GIVEN** una base PostgreSQL migrada hasta la última versión y un profesional
- **WHEN** se guarda directamente una franja con `hora_inicio` 13:00 y `hora_fin` 09:00, otra con `dia_semana` 7 y otra con `vigente_desde` 2026-11-10 y `vigente_hasta` 2026-11-09
- **THEN** la base rechaza cada una por su restricción `CHECK` y no se guarda ninguna
- **AND** una franja con `vigente_desde` y `vigente_hasta` iguales, o con una sola de las dos, se guarda (D259)

#### Scenario: INF-1 Borde - deshacer solo la migración de los bloqueos deja el esquema del change de horario

- **GIVEN** una base PostgreSQL migrada hasta la última versión, con un profesional con franjas, un turno y un bloqueo del profesional
- **WHEN** se deshace solo la migración de los bloqueos, hasta la versión que dejó el change de horario
- **THEN** no existe `bloqueo` y el resto del esquema es el del change de horario
- **AND** el profesional, sus franjas y el turno siguen en la base
- **AND** volver a aplicar la migración de los bloqueos termina sin errores

#### Scenario: INF-1 Borde - la base rechaza un bloqueo que no termina después de empezar

- **GIVEN** una base PostgreSQL migrada hasta la última versión, un consultorio, un profesional y un usuario
- **WHEN** se guarda directamente un bloqueo con `inicio` `2026-11-02T15:00:00Z` y `fin` `2026-11-02T13:00:00Z`, y otro con `inicio` y `fin` iguales
- **THEN** la base rechaza cada uno por su restricción `CHECK` y no se guarda ninguno
- **AND** un bloqueo de todo el consultorio (sin profesional ni sillón) con `inicio` anterior a `fin` se guarda

#### Scenario: INF-1 Borde - la base rechaza un bloqueo con profesional y sillón a la vez

- **GIVEN** una base PostgreSQL migrada hasta la última versión, un consultorio, un profesional, un sillón y un usuario
- **WHEN** se guarda directamente un bloqueo con `profesional_id` y `sillon_id` a la vez, con `inicio` anterior a `fin`
- **THEN** la base lo rechaza por su restricción `CHECK` y no se guarda (D272)
- **AND** un bloqueo solo con `profesional_id` y otro solo con `sillon_id` se guardan

#### Scenario: INF-1 Borde - la migración de es_nuevo agrega la columna y rellena los pacientes ya atendidos

- **GIVEN** una base PostgreSQL migrada hasta la versión que dejó el change de bloqueos (`0009`), con tres pacientes: Ana Ejemplo con un turno `atendido`, Bruno Ficticio con un turno `ausente` y Carla Inventada con un turno `reservado`
- **WHEN** se aplica la migración de `es_nuevo` (`0010`)
- **THEN** `paciente` tiene la columna `es_nuevo`, booleana, no nula y con valor por defecto `true`
- **AND** Ana Ejemplo queda con `es_nuevo` `false` y Bruno Ficticio y Carla Inventada con `es_nuevo` `true` (RN-TD-05, D52: solo un turno `atendido` deja de considerar nuevo al paciente)
- **AND** un paciente guardado directamente después, sin indicar `es_nuevo`, queda con `es_nuevo` `true`

#### Scenario: INF-1 Borde - deshacer solo la migración de es_nuevo deja el esquema del change de bloqueos

- **GIVEN** una base PostgreSQL migrada hasta la última versión, con un paciente con `es_nuevo` `false`, un turno `atendido` suyo y su evento
- **WHEN** se deshace solo la migración de `es_nuevo`, hasta la versión que dejó el change de bloqueos
- **THEN** `paciente` no tiene `es_nuevo` y el resto del esquema es el del change de bloqueos
- **AND** el paciente, el turno y su evento siguen en la base
- **AND** volver a aplicar la migración de `es_nuevo` termina sin errores y el paciente queda con `es_nuevo` `false` por el relleno
