# Spec Delta: persistencia-postgresql

## MODIFIED Requirements

### Requirement: Esquema de PostgreSQL creado por migraciones

El sistema SHALL crear y modificar el esquema de PostgreSQL únicamente con migraciones versionadas y reversibles (DD-15). Una base vacía migrada hasta la última versión SHALL quedar exactamente con el esquema del modelo de datos de la aplicación: sus tablas, columnas, claves e índices, sin tablas de más ni de menos. Las fechas SHALL guardarse con zona (RN-GL-01).

#### Scenario: INF-1 Feliz - una base vacía migrada queda con el esquema del primer change

- **GIVEN** una base PostgreSQL vacía
- **WHEN** se aplican todas las migraciones
- **THEN** existen exactamente las tablas del modelo de datos de la aplicación (desde C-03: `consultorio`, `profesional`, `sillon`, `prestacion`, `paciente`, `turno` y `evento_turno`), y ninguna otra tabla de la aplicación
- **AND** comparar el esquema de la base con el modelo de datos de la aplicación no encuentra ninguna diferencia de tablas, columnas, tipos, nulabilidad, claves ni índices
- **AND** toda columna de fecha-hora es una fecha con zona (desde C-03: `inicio`, `fin` y `creado_en` de `turno` y `ocurrido_en` de `evento_turno`)

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
