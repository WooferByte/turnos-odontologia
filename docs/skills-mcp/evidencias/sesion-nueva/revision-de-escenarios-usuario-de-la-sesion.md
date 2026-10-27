# Revisión de escenarios: `usuario-de-la-sesion` (C-50)

Fecha: 2026-10-27. Revisión estática (sin correr suites). Las preguntas Q1 a Q11 del design están abiertas (D304 a D314, «Propuesta»); los hallazgos que dependen de una se marcan «condicional a Qn» y no son bloqueantes por sí solos.

**Veredicto**: listo con correcciones menores (condicionado a que el autor responda Q1 a Q11 y a que el `/opsx:update` registre D304 a D314 y la ruta en `02` y `03`). No hay bloqueantes propios del change.
**Base**: 14 escenarios (feliz 3, error 4, borde 7, otros 0; el script marca los 4 errores como «sin clasificar» porque el título dice «Error» y no «Error de negocio»); CA mínimos 5/5 (SES-1 a SES-5 de la entrada C-50 de `CHANGES.md`); escenarios con tarea que los verifica 14/14 (el script marca «NO» porque las tareas citan `SES-n`, no un CA; cruzado a mano en «Cobertura»).

## Hallazgos

| ID | Severidad | Control | Ubicación | Hallazgo | Fuente | Corrección propuesta |
|----|-----------|---------|-----------|----------|--------|----------------------|
| H1 | A corregir | C2/C3 | specs/usuario-de-la-sesion/spec.md: `SES-3 Error` (x2); encabezado: `SES-5 Error`, `SES-4 Error` | Ningún título dice «Error de negocio». Los errores de la ruta son de control de acceso con código RN (`RN-AU-03`, `RN-AU-05`), igual que en C-07, que los titula «Error de negocio». Con el título actual el inventario no ve ninguno y la regla «al menos uno de error de negocio» no se ve cumplida. | `openspec/config.yaml` `rules.specs`; spec de `proteccion-del-panel` («US-092 CA-1 Error de negocio - un access token vencido responde 401»); D206, D207 | Titular `SES-3 Error de negocio - …` los dos de la API (401 y 403); en el encabezado, dejar «Error» donde no hay código RN. |
| H2 | A corregir | C6 | tasks 6.1, 6.2 | Tests del cliente rotulados con IDs que en las specs son de la API: `SES-3: un 403 devuelve null`, `SES-2: una respuesta con un rol desconocido…`, `SES-1: obtenerUsuarioDeLaSesion…`. SES-2 y SES-3 solo existen en `usuario-de-la-sesion`; además `SES-1`, `SES-3` y `SES-4` se repiten en 3, 4 y 4 escenarios, así que un nombre de test no identifica un escenario. | config.yaml `rules.tasks`; tasks 10.1 («cada escenario … tiene su test con el ID en el nombre») | Rotular los tests del cliente con el escenario del encabezado que prueban (SES-4/SES-5) y sumar un sufijo al nombre de cada test (p. ej. `SES-3 Borde`) para que 10.1 pueda comprobar uno por escenario. |
| H3 | A corregir | C7/C1 | design Y11 y tasks 6.2 vs specs/encabezado, requisito «Otra falla…» | El design y la tarea 6.2 hacen que «una respuesta con otra forma» (rol desconocido, sin email) deje el indicador oculto, pero el requisito y el escenario solo listan falla de red, `500` y `403`. Comportamiento con test y sin escenario. | config.yaml `rules.specs`; design Y11 | Sumar «o con un cuerpo que no es el de la API» al requisito y al escenario `SES-4 Error` (o quitarlo de Y11 y de 6.2). |
| H4 | A corregir | C6 | tasks 3.1, 6.2, 7.2, 8.1 | Fusionan RED con GREEN (3.1) o GREEN con TRIANGULATE/REFACTOR (6.2, 7.2, 8.1) en una sola tarea. Q11 pide la excepción de tamaño «con el criterio de D300», y D300 se justifica en que RED, GREEN y TRIANGULATE van separados. | config.yaml `rules.tasks`; D300; módulo Strict TDD | Separar 3.1 en RED y GREEN (y 6.2/7.2 si se conserva D300), o aclarar en Q11 que esas fusiones son parte de la excepción. Condicional a Q11 para el conteo (18 tareas pasarían a unas 22). |
| H5 | A corregir (condicional a Q10) | C7 | design «Notas para el archive» vs «Migration Plan» | Las notas dicen que `02` y `03` ya están hechos en el `/opsx:update` (D313), pero hoy ninguno lista `GET /auth/yo` (solo `10_preguntas_abiertas.md` la nombra como «yo»). El Migration Plan dice lo correcto: se hace en el update. `CHANGES.md` tampoco cita la ruta en «Alcance — dentro» (el verificador exige que toda ruta citada esté en 02/03). | design Q10; `scripts/verificar_changes.py` filas 4 y 8; 02 «API REST (resumen)», 03 matriz | Cambiar la nota a «a hacer en el `/opsx:update`» y asegurar que el update sume `02` y `03` antes de citar la ruta en `CHANGES.md`. |
| H6 | Sugerencia (condicional a Q1 y Q11) | C8 / `rules.proposal` | proposal «Capabilities» y «Escenarios»; tasks encabezado | Dos capabilities nuevas y 14 escenarios frente a «una capability» y «3 a 6». Está declarado como excepción y marcado «Propuesta», pero sin D hasta que el autor responda. | config.yaml `rules.proposal`/`specs`; D241, D255, D271, D290, D300; Q1, Q11 | Registrar D304 y D314 en el `/opsx:update`. No es defecto del change. |
| H7 | Sugerencia | C10 | spec API: `SES-1 Borde` (rol cambiado) y `SES-1 Feliz` | El orden fijo de `roles` (enum, D306) no se prueba: en ambos escenarios el orden de alta coincide con el del enum. Un fallo que devolviera el orden de la base pasaría. | design Y5; D306 | En `SES-1 Borde`, quitar y volver a sumar `odontologo` (o crear un usuario con `dueno` antes que `odontologo`) y esperar `["odontologo","dueno"]`. |
| H8 | Sugerencia | C10 | specs/encabezado, requisito «El encabezado muestra…»; design Y10 (bandera `vigente`) | No hay escenario de carrera: «Cerrar sesión» antes de que llegue `GET /auth/yo`. La bandera existe para que el email de la sesión anterior no aparezca; «otro usuario en la misma pestaña» solo cubre el caso en que la respuesta ya llegó. | design Y10; RN-AU-03 | Ver «Bordes sugeridos». |
| H9 | Sugerencia | C5 | spec API: `SES-3 Error` (5 causas) y `SES-3 Borde` (3 comportamientos); encabezado: `SES-4 Error` (3 corridas) | Escenarios con varias causas en un solo THEN. En `SES-3 Borde` el restablecimiento no dice qué contraseña nueva se usa (mínimo 10 caracteres). | config.yaml `rules.specs`; RN-AU-07; D211 | Aceptable si 4.3 y 7.3 parten en un test por causa (ya lo dicen); fijar un valor ficticio de contraseña en el WHEN. |
| H10 | Sugerencia | C3/C6 | spec API: requisito «La respuesta no expone…»; encabezado: requisito «El encabezado muestra…»; tasks 6.1, 6.2, 7.1 | Algunos requisitos y tareas de test no citan RN (config pide citar la regla). Los RN aparecen solo en Purpose o en otros requisitos. | config.yaml `rules.specs` y `rules.tasks` | Citar `RN-AU-02` en el requisito de no exponer y `RN-AU-03`/`RN-AU-05` en las tareas 6.1 y 7.1. |

## Cobertura

| CA | Escenarios | Tarea que lo verifica |
|----|------------|-----------------------|
| SES-1 (el token de cada rol obtiene su email y sus roles) | API: Feliz odontóloga; Feliz recepcionista y dueño; Borde rol cambiado | 3.1, 4.1, 4.3 (+ 2.1 permiso) |
| SES-2 (sin hash ni `token_version`) | API: Borde «solo email y roles, sin caché» | 4.1 (+ 4.3 por mutación) |
| SES-3 (sin sesión válida, 401; sin roles, 403) | API: Error 401 (5 causas); Borde inactivo y `token_version` vieja; Error 403 sin roles | 2.1, 4.3 |
| SES-4 (el encabezado muestra email y roles) | Encabezado: Feliz; Borde navegar; Borde recargar; Borde otro usuario; Error sin conexión/500/403 | 7.1, 7.3, 9.1 (+ 6.1, 6.2 cliente) |
| SES-5 (un 401 vuelve al inicio de sesión) | Encabezado: Error 401 sin renovación; Borde 401 con refresh vigente | 6.1, 7.3, 9.1 |

Alcance (C8): sin hallazgos. Las specs no piden nada de lo que `CHANGES.md` deja fuera; ocultar acciones por rol quedó fuera (Q9). La tarea 7.2 mueve `nombreDelRol` a `shared/roles.ts` sin cambiar lo que verifica ningún test de C-09. Datos (C9): todos ficticios, dominio `.test`. Horarios: UTC con reloj inyectable; el access vencido a las 12:15 coincide con el criterio ya vigente en `proteccion-del-panel`.

## Bordes sugeridos

- **Respuesta tardía tras cerrar sesión**: GIVEN la odontóloga con sesión y `GET /api/auth/yo` retenido; WHEN pulsa «Cerrar sesión» y luego se libera la respuesta; THEN la pantalla de inicio de sesión no muestra «odontologa@consultorio-demo.test». Aplica porque Y10 declara la bandera `vigente` sin escenario. (H8; design Y10)
- **Orden fijo de roles**: GIVEN un usuario al que se le quitó y se volvió a sumar `odontologo` después de `dueno`; WHEN pide `GET /auth/yo`; THEN `roles` es `["odontologo","dueno"]`. (H7; D306)

## Lo que no pude verificar

- Si `POST /auth/login` admite iniciar sesión a un usuario activo sin roles: `SES-3 Error` (403) lo da por hecho. Confirmarlo contra `sesion-del-panel` en el Apply; si el login lo rechaza, el escenario debe armar el token a mano.
- El conteo de 18 tareas es correcto hoy; cambia si se acepta H4.
- La KB no tiene aún la fila de la matriz de `03` ni la ruta en `02` (propuesta de Q10).
