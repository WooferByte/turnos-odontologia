# Spec Delta: persistencia-postgresql

## MODIFIED Requirements

### Requirement: Esquema de PostgreSQL creado por migraciones

El sistema SHALL crear y modificar el esquema de PostgreSQL únicamente con migraciones versionadas y reversibles (DD-15). Una base vacía migrada hasta la última versión SHALL quedar exactamente con el esquema del modelo de datos de la aplicación: sus tablas, columnas, claves e índices, sin tablas de más ni de menos. Las fechas SHALL guardarse con zona (RN-GL-01).

#### Scenario: INF-1 Feliz - una base vacía migrada queda con el esquema del primer change

- **GIVEN** una base PostgreSQL vacía
- **WHEN** se aplican todas las migraciones
- **THEN** existen exactamente las tablas del modelo de datos de la aplicación (desde C-07: `consultorio`, `profesional`, `sillon`, `prestacion`, `paciente`, `turno`, `evento_turno`, `usuario` y `usuario_rol`), y ninguna otra tabla de la aplicación
- **AND** comparar el esquema de la base con el modelo de datos de la aplicación no encuentra ninguna diferencia de tablas, columnas, tipos, nulabilidad, claves ni índices
- **AND** toda columna de fecha-hora es una fecha con zona (desde C-06: `inicio`, `fin` y `creado_en` de `turno`, `ocurrido_en` de `evento_turno` y `creado_en` de `usuario`)

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
