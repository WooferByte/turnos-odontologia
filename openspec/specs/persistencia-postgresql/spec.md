# persistencia-postgresql Specification

## Purpose

Define qué garantiza el sistema cuando corre sobre PostgreSQL: qué esquema deja una base migrada, qué turnos rechaza la base por sí sola aunque la aplicación no los haya filtrado, qué pasa con dos reservas simultáneas del mismo hueco, y qué necesita quien clona el repositorio para correr los tests.

Convenciones de los escenarios: todos los horarios están en **UTC** y son del día 2026-11-02; «10:00» significa `2026-11-02T10:00:00Z`. Los intervalos son semiabiertos `[inicio, fin)`. Un turno «activo» está en `pendiente_aprobacion`, `pendiente_sena`, `reservado` o `confirmado`. «Guardar directamente» significa escribir el turno en la base sin pasar por la validación de solapamiento de la aplicación. Todos los datos son ficticios (RN-PR-01). Salvo INF-4, los escenarios se verifican en el perfil opcional de tests con PostgreSQL.

## Requirements

### Requirement: Esquema de PostgreSQL creado por migraciones

El sistema SHALL crear y modificar el esquema de PostgreSQL únicamente con migraciones versionadas y reversibles (DD-15). Una base vacía migrada hasta la última versión SHALL quedar exactamente con el esquema del modelo de datos de la aplicación: sus tablas, columnas, claves e índices, sin tablas de más ni de menos. Las fechas SHALL guardarse con zona (RN-GL-01).

#### Scenario: INF-1 Feliz - una base vacía migrada queda con el esquema del primer change

- **GIVEN** una base PostgreSQL vacía
- **WHEN** se aplican todas las migraciones
- **THEN** existen exactamente las tablas del modelo de datos de la aplicación (desde C-06: `consultorio`, `profesional`, `sillon`, `prestacion`, `paciente`, `turno`, `evento_turno` y `usuario`), y ninguna otra tabla de la aplicación
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

### Requirement: La base rechaza turnos activos solapados

En PostgreSQL, la base SHALL rechazar por sí misma el alta de un turno activo cuyo intervalo `[inicio, fin)` se solapa (RN-AG-09) con el de otro turno activo (RN-AG-10) del mismo profesional (RN-AG-05) o del mismo sillón (RN-AG-08), aunque la aplicación no lo haya validado (DD-04, RN-AG-10c). El rechazo SHALL identificar qué recurso chocó. El sistema MUST NOT guardar el turno rechazado.

#### Scenario: INF-2 Error de negocio - la base rechaza el solapamiento de E2 (profesional)

- **GIVEN** un turno activo de 10:00 a 10:30 del profesional A en el sillón 1
- **WHEN** se guarda directamente un turno activo de 10:15 a 10:45 del profesional A en el sillón 2
- **THEN** la base rechaza el alta e identifica al profesional como el recurso en conflicto (RN-AG-05)
- **AND** en la base sigue habiendo un solo turno

#### Scenario: INF-2 Error de negocio - la base rechaza el solapamiento de E3 (sillón)

- **GIVEN** un turno activo de 10:00 a 10:30 del profesional A en el sillón 1
- **WHEN** se guarda directamente un turno activo de 10:00 a 10:30 del profesional B en el sillón 1
- **THEN** la base rechaza el alta e identifica al sillón como el recurso en conflicto (RN-AG-08)
- **AND** en la base sigue habiendo un solo turno

#### Scenario: INF-2 Borde - cualquier estado activo bloquea en la base

- **GIVEN** un turno de 10:00 a 10:30 del profesional A en el sillón 1, en uno de los cuatro estados activos
- **WHEN** se guarda directamente un turno `reservado` de 10:29 a 10:59 del profesional A en el sillón 2
- **THEN** la base rechaza el alta, sea cual sea el estado activo del turno existente

### Requirement: La base admite turnos contiguos y turnos no activos

En PostgreSQL, la base MUST aceptar un turno que empieza en el instante exacto en que termina otro del mismo profesional y sillón, o que termina cuando el otro empieza (RN-AG-09). La base MUST aceptar un turno que se superpone con otro en estado no activo: `cancelado_paciente`, `cancelado_profesional`, `vencido`, `atendido` o `ausente` (RN-AG-10).

#### Scenario: INF-3 Borde - la base acepta el turno contiguo de E5

- **GIVEN** un turno activo de 10:00 a 10:30 del profesional A en el sillón 1
- **WHEN** se guarda directamente un turno activo de 10:30 a 11:00 del profesional A en el sillón 1
- **THEN** la base lo acepta
- **AND** también acepta uno de 09:30 a 10:00 del mismo profesional y sillón

#### Scenario: INF-3 Borde - un turno no activo no bloquea en la base (E6)

- **GIVEN** un turno de 10:00 a 10:30 del profesional A en el sillón 1, en uno de los cinco estados no activos
- **WHEN** se guarda directamente un turno `reservado` de 10:00 a 10:30 del profesional A en el sillón 1
- **THEN** la base lo acepta, sea cual sea el estado no activo del turno existente

### Requirement: De dos reservas simultáneas del mismo hueco gana una sola

En PostgreSQL, cuando dos peticiones de crear un turno para el mismo hueco se procesan a la vez, el sistema SHALL crear exactamente un turno (RN-AG-10c). La petición que pierde SHALL recibir el mismo rechazo que si hubiera llegado después: `409` con los códigos del solapamiento (`RN-AG-05`, `RN-AG-08` o ambos) y el turno contra el que chocó (RN-GL-02).

#### Scenario: E11 Error de negocio - la reserva que pierde la carrera recibe el rechazo por solapamiento

- **GIVEN** un profesional y un sillón activos y libres a las 10:00, y una prestación activa de 30 minutos
- **AND** una reserva de 10:00 a 10:30 para ese profesional y ese sillón que ya se escribió pero todavía no se confirmó
- **WHEN** se pide crear otro turno de 30 minutos para el mismo profesional y sillón con `inicio` 10:00, y recién después se confirma la primera
- **THEN** la segunda petición termina rechazada con `codigos` exactamente `["RN-AG-05", "RN-AG-08"]`
- **AND** cada conflicto lleva el identificador del turno que ganó
- **AND** en la base queda un solo turno de 10:00 a 10:30

#### Scenario: E11 Feliz - de varias peticiones lanzadas a la vez se crea un solo turno

- **GIVEN** un profesional y un sillón activos y libres a las 10:00, y una prestación activa de 30 minutos
- **WHEN** ocho peticiones idénticas de crear un turno con `inicio` 10:00 se lanzan al mismo tiempo
- **THEN** exactamente una crea el turno en estado `reservado`
- **AND** las otras siete terminan rechazadas por solapamiento, con `RN-AG-05` y `RN-AG-08`
- **AND** en la base queda un solo turno activo para ese profesional y ese sillón a las 10:00

#### Scenario: E11 Borde - la carrera por un solo recurso informa solo ese código

- **GIVEN** el profesional A libre a las 10:00, los sillones 1 y 2 libres, y una reserva sin confirmar de 10:00 a 10:30 del profesional A en el sillón 1
- **WHEN** se pide crear un turno de 30 minutos del profesional A en el sillón 2 con `inicio` 10:15, y recién después se confirma la primera
- **THEN** la segunda petición termina rechazada con `codigos` exactamente `["RN-AG-05"]`
- **AND** no se crea el segundo turno

### Requirement: La suite por defecto no necesita PostgreSQL

La suite de tests por defecto SHALL correr completa con el comando del README, sobre SQLite en memoria, sin Docker, sin PostgreSQL y sin ninguna variable de entorno (DD-03). Los tests que necesitan PostgreSQL SHALL quedar fuera de esa corrida y ejecutarse solo cuando se piden por su marcador (D75). Si se piden y PostgreSQL no está disponible, SHALL omitirse informando el motivo, sin fallar.

#### Scenario: INF-4 Feliz - la suite por defecto corre sin PostgreSQL

- **GIVEN** un clon del repositorio con las dependencias instaladas, sin Docker en ejecución, sin PostgreSQL y sin variables de entorno definidas
- **WHEN** se corre la suite con el comando por defecto del README
- **THEN** todos los tests ejecutados pasan, incluidos los de E1 a E7 y E12 del primer change
- **AND** ningún test que necesite PostgreSQL se ejecuta ni figura como fallado

#### Scenario: INF-4 Borde - el perfil opcional sin PostgreSQL se omite

- **GIVEN** el mismo clon, sin PostgreSQL disponible
- **WHEN** se piden los tests del perfil opcional por su marcador
- **THEN** esos tests figuran como omitidos, con un motivo que dice qué falta
- **AND** la corrida no informa ningún test fallado
