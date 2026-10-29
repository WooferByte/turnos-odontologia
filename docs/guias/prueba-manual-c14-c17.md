# Guía de prueba manual de la mitad de la fase 4 (C-14 a C-17)

Paso a paso para que el autor pruebe a mano, con la demo, la agenda del día (C-14), el historial de un turno (C-15), la reprogramación (C-16) y la cancelación (C-17). Es una guía **temporal**: cuando la hagas (o decidas saltearla), se borra con un commit `chore:`. Todos los datos son ficticios.

## 0. Preparación (una sola vez)

Dos terminales, la demo **recién arrancada** (la base es SQLite en memoria: al reiniciar se pierden los turnos, y los pasos de abajo dependen de partir sin turnos).

Terminal 1, la API (desde `backend/`, con el entorno activado):

```
python -m uvicorn app.main:crear_app_demo --factory
```

Terminal 2, la interfaz (desde `frontend/`, después de `npm ci`):

```
npm run dev
```

- Interfaz: <http://127.0.0.1:5173> (inicio de sesión en `/ingresar`; la agenda, en `/panel/agenda`).
- Swagger: <http://127.0.0.1:8000/docs>.
- Usuarios de la demo, los dos con la contraseña de prueba `demo-consultorio-2026` (la del README):
  - `recepcion@consultorio-demo.test` (recepcionista): el que se usa casi siempre.
  - `odontologa@consultorio-demo.test` (odontólogo y dueño).
- Pacientes: 1 «Ana Ejemplo», 2 «Bruno Ficticio», 3 «Carla Inventada». Prestaciones: 1 «Consulta / control · 30 min», 2 «Limpieza · 45 min», 3 «Obturación · 60 min».
- Día de la prueba: **lunes 2 de noviembre de 2026** (`02/11/2026`). La demo atiende de lunes a viernes de 09:00 a 13:00 y de 15:00 a 19:00.
- Consola del navegador abierta (F12) durante toda la prueba: no tiene que aparecer ningún error de CSP ni ningún token, contraseña o dato de paciente en la URL.

## 1. Agenda del día y nuevo turno (C-14)

1. Ingresar con la recepcionista y pulsar «Agenda». Esperado: título «Agenda del día», subtítulo «Horas del consultorio (America/Argentina/Buenos_Aires).», el día de hoy, «No hay turnos para este día.» y el contador «0 turnos».
2. En el selector de fecha elegir `02/11/2026`. Esperado: «lunes 2 de noviembre de 2026». «Día siguiente», «Día anterior» y «Hoy» cambian de día.
3. «Nuevo turno». **Revisar la altura del campo «N.º de paciente»**: tiene que verse del mismo alto que «Fecha» y «Hora» (36 px; era un defecto de 20 px, corregido en a460df0). Escribir `1`, elegir «Consulta / control · 30 min», fecha `02/11/2026` y hora `09:00`. Esperado: «Termina a las 09:30.». «Crear turno» → «Turno creado.», el panel se cierra y aparece la fila «09:00 – 09:30», «Ana Ejemplo», «Consulta / control», «Reservado».
4. Repetir con el paciente `2`, «Limpieza · 45 min», `10:00` (queda de 10:00 a 10:45) y con el paciente `3`, «Obturación · 60 min», `11:00` (de 11:00 a 12:00). Esperado: tres filas ordenadas por hora, «3 turnos».
5. Superposición (E4): «Nuevo turno», paciente `2`, «Consulta / control», `02/11/2026`, `09:00`. Esperado: «El profesional y el sillón ya tienen un turno activo en ese horario (RN-AG-05, RN-AG-08).»; el panel sigue abierto y no se ve «Turno creado.».
6. Paciente `99`. Esperado: «Hay datos que no existen o no están activos: paciente 99 (no existe) (RN-GL-04).».
7. Fuera de horario: fecha `07/11/2026` (sábado), hora `10:00`. Esperado: «El turno no cae dentro del horario de atención del profesional (RN-AG-04).».
8. Dejar un campo vacío y «Crear turno». Esperado: «Completá paciente, prestación, fecha y hora.» sin ningún pedido en la pestaña de red.

## 2. Historial del turno (C-15)

Con los tres turnos del paso 1.

1. Pulsar «Historial» en la fila de Ana. Esperado: panel «Historial del turno» con «Ana Ejemplo · Consulta / control», «lunes 2 de noviembre de 2026, 09:00 – 09:30», «Solo lectura: el historial no se puede editar.» y una entrada «Turno creado» con «Por: Usuario n.º 2» y «Estado inicial: Reservado · 09:00 – 09:30». Un solo `GET /api/turnos/{id}/historial` en la pestaña de red; sin campos de edición.
2. «Cerrar»: el panel desaparece y el foco vuelve al botón «Historial» de la fila.
3. Con el historial abierto, pulsar «Nuevo turno»: el historial se cierra (un solo panel lateral a la vez). «Historial» en otra fila muestra el de ese turno. «Día siguiente» cierra el panel.
4. En `/docs`: `GET /turnos/1/historial` (con «Authorize» y el token de `POST /auth/login`) devuelve el mismo evento `creado` con `actor_id` `"2"`.

## 3. Reprogramar un turno (C-16)

1. «Reprogramar» en la fila de Ana. Esperado: «Reprogramar turno», «Ahora: lunes 2 de noviembre de 2026, 09:00 – 09:30», «Fecha» `02/11/2026`, «Hora» `09:00`, «Duración (minutos)» `30` (**mismo alto que los otros dos campos**) y «Termina a las 09:30.». Foco en «Fecha» y la fila de Ana resaltada.
2. «Hora» `12:30` → «Termina a las 13:00.». «Reprogramar». Esperado: un solo `PATCH`, «Turno reprogramado.», panel cerrado y Ana de 12:30 a 13:00, después de Carla.
3. Solo la duración: «Reprogramar» en Bruno, «Duración (minutos)» `60` → «Termina a las 11:00.»; la fila queda de 10:00 a 11:00. A otro día: «Reprogramar» en Ana, fecha `03/11/2026`, hora `10:00` → la agenda pasa al «martes 3 de noviembre de 2026» con el turno de 10:00 a 10:30.
4. Volver al `02/11/2026`. «Reprogramar» en Bruno, «Hora» `11:30` (sobre Carla). Esperado: «El profesional y el sillón ya tienen un turno activo en ese horario (RN-AG-05, RN-AG-08).» y «El turno no cambió.»; el panel sigue abierto y Bruno sigue de 10:00 a 11:00.
5. Duración `42`: «La duración debe ser mayor que 0 y múltiplo de 5 minutos (RN-AG-01).». Hora `07:30`: «El turno no cae dentro del horario de atención del profesional (RN-AG-04).». Campo vacío: «Completá fecha, hora y duración.». Sin cambiar nada: «No cambiaste la fecha, la hora ni la duración.» (ninguno de los tres hace un pedido). «Cancelar» cierra el panel y devuelve el foco al botón de la fila.
6. Historial de Ana: «Turno creado» y un «Turno reprogramado» por cada cambio, con «Por: Usuario n.º 2» y las líneas «Antes: …» y «Después: …» con día, horas y duración.

## 4. Cancelar un turno (C-17)

Para esta parte conviene reiniciar la demo (los turnos quedan de nuevo en cero) y dar de nuevo los de la sección 1 (Ana 09:00, Bruno 10:00, Carla 11:00). Los resultados se probaron en el navegador con la demo (2026-10-29).

1. «Cancelar» en la fila de Ana (botón rojo, entre «Reprogramar» e «Historial»). Esperado: panel «Cancelar turno», «Ana Ejemplo · Consulta / control», «lunes 2 de noviembre de 2026, 09:00 – 09:30 · Reservado», «¿Quién pidió la cancelación?» con «El paciente» y «El consultorio» **sin marcar**, «El horario queda libre para otro turno.», y los botones «Volver» y «Cancelar turno». Foco en «El paciente» y fila resaltada. Ningún pedido.
2. Sin elegir (CAN-5b): «Cancelar turno». Esperado: «Elegí quién pidió la cancelación.» y ningún pedido; el aviso desaparece al marcar una opción.
3. «El paciente» y «Cancelar turno» (CAN-4a). Esperado: un solo `POST /api/turnos/{id}/cancelar` con `{"estado": "cancelado_paciente"}`, «Turno cancelado.», panel cerrado y Ana con «Cancelado por el paciente», solo con «Historial».
4. El horario queda libre: «Nuevo turno», paciente `1`, «Consulta / control», `02/11/2026`, `09:00`. Esperado: «Turno creado.» y una fila nueva de 09:00 a 09:30 junto a la cancelada.
5. Por el consultorio (CAN-4b): «Cancelar» en Carla, «El consultorio» y «Cancelar turno». Esperado: el `POST` lleva `{"estado": "cancelado_profesional"}` y Carla queda con «Cancelado por el consultorio».
6. Dos pestañas (CAN-5a): abrir `/panel/agenda` del `02/11/2026` en dos pestañas (iniciar sesión en cada una), cancelar a Bruno en la primera; en la segunda, sin recargar, «Cancelar» de Bruno, «El paciente», «Cancelar turno». Esperado: «Este turno ya no se puede cancelar por su estado (RN-AG-12).» y «El turno no cambió.»; el panel sigue abierto con la opción marcada y sin «Turno cancelado.». «Día siguiente» y «Día anterior» recargan y muestran a Bruno cancelado.
7. El dueño (CAN-5b): en «Usuarios» (con la odontóloga) crear un usuario con solo el rol «Dueño» y una contraseña de prueba de 10 caracteres o más; «Cerrar sesión» e ingresar con él. Esperado: ve «Cancelar» en las filas activas y al confirmar recibe «Tu usuario no tiene permiso para cancelar turnos (RN-AU-05).» y «El turno no cambió.».
8. Historial (HIS-2b), con la recepcionista: «Historial» en Ana. Esperado: «Turno creado» y «Turno cancelado», los dos con «Por: Usuario n.º 2», y en el segundo «Estado: Reservado → Cancelado por el paciente». «Cancelar», «Reprogramar», «Historial» y «Nuevo turno» no conviven: un solo panel lateral a la vez.
9. En `/docs`: `POST /turnos/{id}/cancelar` con un turno activo y `{"estado": "cancelado_profesional"}` → `200`; repetido → `409` con `["RN-AG-12"]`; `{"estado": "confirmado"}` → `422`; id `999` → `404` con `["RN-GL-04"]`; con el token del usuario «Dueño» → `403` con `["RN-AU-05"]`.
10. Pantalla angosta: con las herramientas de desarrollo (F12) emular 390 px de ancho. Esperado: sin desplazamiento horizontal, los tres botones al pie de cada tarjeta («Reprogramar» y «Cancelar» en una fila, «Historial» debajo) y, al abrir «Cancelar», el panel debajo de la agenda con opciones de 44 px de alto.

## 5. Al terminar

`Ctrl+C` en las dos terminales. Si alguna prueba no da lo esperado, anotar el paso y qué se vio.
