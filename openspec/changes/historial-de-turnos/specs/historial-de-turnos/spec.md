# Spec Delta: historial-de-turnos

## Purpose

Registra en un historial inmutable, de solo inserción, cada hecho que le pasa a un turno (quién, cuándo y qué cambió) y permite consultarlo en solo lectura, para que el consultorio tenga trazabilidad de sus turnos (RN-AG-11, US-015).

Convenciones de los escenarios: todos los horarios están en **UTC**; los turnos son del día 2026-11-02 («10:00» significa `2026-11-02T10:00:00Z`) y el reloj del sistema marca `2026-10-07T12:00:00Z`. Las fechas se escriben con `Z`. La creación es `POST /turnos` (capability `creacion-de-turnos`) y la consulta es `GET /turnos/{id}/historial`. Todos los datos son ficticios (RN-PR-01). Salvo que se diga otra cosa, los escenarios se verifican en la suite por defecto.

## ADDED Requirements

### Requirement: Crear un turno registra el evento `creado`

Al crear un turno, el sistema SHALL registrar en su historial exactamente un evento de tipo `creado`, en la misma operación que guarda el turno: o quedan los dos o no queda ninguno (RN-AG-11). El evento SHALL llevar el momento de la creación, el actor y los datos con los que nació el turno. Un rechazo MUST NOT registrar ningún evento.

#### Scenario: E9 Feliz - la creación queda registrada en el historial

- **GIVEN** un profesional y un sillón activos y libres a las 10:00, y una prestación activa de 30 minutos
- **WHEN** se pide crear un turno de esa prestación para un paciente existente con `inicio` 10:00, y el sistema responde `201`
- **THEN** el historial de ese turno tiene exactamente un evento, de `tipo` `creado`
- **AND** el evento tiene `ocurrido_en` `2026-10-07T12:00:00Z`, igual al `creado_en` del turno
- **AND** el evento tiene `actor_tipo` `usuario` y `actor_id` vacío, porque la creación no está autenticada todavía
- **AND** `antes` y `motivo` están vacíos
- **AND** `despues` lleva el estado `reservado`, `inicio` `2026-11-02T10:00:00Z`, `fin` `2026-11-02T10:30:00Z`, `duracion_minutos` 30 y los identificadores del paciente, la prestación, el profesional y el sillón del turno

#### Scenario: E9 Error de negocio - un rechazo no registra ningún evento

- **GIVEN** un turno activo de 10:00 a 10:30 del profesional A en el sillón 1, con su evento `creado`
- **WHEN** se pide crear otro turno de 30 minutos con el profesional A en el sillón 1 con `inicio` 10:00, y el sistema responde `409` (RN-AG-05, RN-AG-08)
- **THEN** en el sistema sigue habiendo un solo evento, el del turno existente
- **AND** lo mismo ocurre si la petición se rechaza con `422` por una referencia inválida (RN-GL-04)

#### Scenario: E9 Borde - si el evento no se puede guardar, el turno tampoco queda

- **GIVEN** un profesional y un sillón activos y libres a las 10:00, y una prestación activa de 30 minutos
- **WHEN** se pide crear un turno con `inicio` 10:00 y el registro del evento `creado` falla después de que el turno ya se envió a la base
- **THEN** la creación termina con error
- **AND** no queda ningún turno ni ningún evento

### Requirement: Consultar el historial de un turno

El sistema SHALL devolver, con `GET /turnos/{id}/historial` y estado `200`, la lista de los eventos del turno identificado en la URL, del más antiguo al más reciente (por `ocurrido_en` y, a igual momento, por orden de registro). Cada evento SHALL mostrar `id`, `turno_id`, `tipo`, `actor_tipo`, `actor_id`, `ocurrido_en`, `antes`, `despues` y `motivo`. La lista MUST NOT incluir eventos de otros turnos.

#### Scenario: US-015 CA-1 Feliz - el historial muestra los eventos del turno pedido

- **GIVEN** dos turnos creados con `POST /turnos`: uno a las 10:00 y otro a las 11:00
- **WHEN** se consulta el historial del turno de las 10:00
- **THEN** el sistema responde `200` con una lista de un solo evento, de `tipo` `creado` y `turno_id` igual al del turno de las 10:00
- **AND** el evento del turno de las 11:00 no aparece

#### Scenario: US-015 CA-1 Borde - los eventos salen en orden cronológico

- **GIVEN** un turno con tres eventos guardados directamente en la base, en este orden de registro: uno con `ocurrido_en` `2026-10-07T12:00:00Z`, otro con `2026-10-07T11:00:00Z` y un tercero también con `2026-10-07T11:00:00Z`
- **WHEN** se consulta su historial
- **THEN** el sistema responde `200` con los tres eventos en este orden: el segundo registrado, el tercero registrado y el primero registrado

#### Scenario: US-015 CA-1 Borde - un turno sin eventos devuelve una lista vacía

- **GIVEN** un turno que existe en la base pero que se guardó antes de que existiera el historial, sin ningún evento
- **WHEN** se consulta su historial
- **THEN** el sistema responde `200` con una lista vacía

### Requirement: Un turno inexistente en la URL responde 404

Si el turno identificado en la URL no existe, el sistema SHALL responder `404` con un error que lleva el código `RN-GL-04` y la referencia al turno con su identificador y el motivo `inexistente` (RN-GL-04, RN-GL-02). Un identificador que no es un número entero SHALL rechazarse como petición mal formada, con `422` y sin código RN.

#### Scenario: HIS-1 Error de negocio - id de turno inexistente

- **GIVEN** que no existe el turno 999
- **WHEN** se consulta `GET /turnos/999/historial`
- **THEN** el sistema responde `404` y `codigos` es exactamente `["RN-GL-04"]`
- **AND** `referencias` tiene un solo elemento, con `recurso` `turno`, `recurso_id` 999 y `motivo` `inexistente`

#### Scenario: HIS-1 Borde - id que no es un número

- **WHEN** se consulta `GET /turnos/abc/historial`
- **THEN** el sistema responde `422` con `codigos` vacío y un error que señala el identificador del turno

### Requirement: El historial es de solo lectura

El sistema MUST NOT ofrecer ninguna operación que modifique o borre un evento del historial (US-015 CA-1, RN-AG-11). La ruta del historial SHALL aceptar solo la lectura: una petición `POST`, `PUT`, `PATCH` o `DELETE` a ella SHALL responder `405` y MUST NOT cambiar el historial.

#### Scenario: US-015 CA-1 Error de negocio - no se puede modificar el historial por la API

- **GIVEN** un turno creado con `POST /turnos`, con su evento `creado`
- **WHEN** se envía `PUT`, `PATCH`, `DELETE` o `POST` a `/turnos/{id}/historial` de ese turno
- **THEN** cada petición responde `405`
- **AND** al consultar el historial después, sigue teniendo el mismo único evento, sin cambios

### Requirement: La base impide modificar el historial

En PostgreSQL, la base SHALL rechazar por sí misma toda modificación, borrado o vaciado de los eventos del historial, aunque no pase por la aplicación (RN-AG-11; «ni la aplicación ni la base exponen `UPDATE` ni `DELETE`»). La base SHALL seguir aceptando eventos nuevos. Estos escenarios se verifican en el perfil opcional con PostgreSQL.

#### Scenario: US-015 CA-1 Error de negocio - la base rechaza modificar o borrar un evento

- **GIVEN** una base PostgreSQL migrada con un turno y su evento `creado`
- **WHEN** se intenta, directamente en la base, cambiar el `tipo` del evento, borrarlo o vaciar la tabla del historial
- **THEN** la base rechaza cada intento con un error que dice que el historial es de solo inserción
- **AND** el evento sigue igual que antes

#### Scenario: US-015 CA-1 Borde - la base acepta un evento nuevo del mismo turno

- **GIVEN** la misma base, con el turno y su evento `creado`
- **WHEN** se guarda directamente un segundo evento para ese turno
- **THEN** la base lo acepta y el turno queda con dos eventos
