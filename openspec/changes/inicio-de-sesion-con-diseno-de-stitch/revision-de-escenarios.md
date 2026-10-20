# Revisión de escenarios: `inicio-de-sesion-con-diseno-de-stitch`

Fecha: 2026-10-20, sobre el propose (antes de que el autor responda Q1 a Q6). Informe de la skill `revisor-de-escenarios`: no edita los artefactos.

**Veredicto**: listo con correcciones menores
**Base**: 6 escenarios en el delta (feliz 2, error de negocio 1, borde 3, otros 0); CA mínimos 2/3 con escenario en el delta (US-090 CA-3 solo en los escenarios vigentes de `ingreso-al-panel`); tareas cruzadas 6/6 (el script marca «NO» en STI-1 porque busca un CA, pero la tarea 4.1 lo cita por su ID).

## Hallazgos

| ID | Severidad | Control | Ubicación | Hallazgo | Fuente | Corrección propuesta |
|----|-----------|---------|-----------|----------|--------|----------------------|
| H1 | A corregir | C1 | `specs/ingreso-al-panel/spec.md` (delta) y `CHANGES.md` C-49 | «Escenarios mínimos» de C-49 lista US-090 CA-3, pero el delta no tiene ningún escenario con CA-3. La proposal dice que lo cubren los escenarios vigentes («usuario inactivo con la contraseña correcta» y «los dos rechazos se ven idénticos»), que no cambian; eso es cierto para el comportamiento, pero el aspecto nuevo del aviso (ícono, sin título, ubicación) no queda probado para la usuaria inactiva. | `CHANGES.md` C-49 «Escenarios mínimos»; 06 US-090 CA-3; RN-AU-04 («mismo mensaje genérico») | O bien sumar al escenario de error (E1) un `AND` «con `recepcion@consultorio-demo.test` inactiva y su contraseña correcta, el aviso es idéntico: mismo texto, mismo rol y misma ubicación» (y su caso en la tarea 2.1), o bien quitar CA-3 de los mínimos de C-49 y dejar «US-090: CA-1, CA-2; STI-1» (sigue dentro de 3 a 6). Recomendado lo primero: es un test barato y es justamente lo que RN-AU-04 exige que no cambie. |
| H2 | A corregir | C5 | `specs/ingreso-al-panel/spec.md`, escenario «US-090 CA-2 Borde - el aviso de sesión terminada va antes de los campos y se va al reintentar»; `tasks.md` 2.3; `proposal.md`, tabla de escenarios | El escenario trata de la sesión que termina (refresh rechazado al recargar), que en la spec vigente es **US-092 CA-1** con RN-AU-03 («al recargar, un refresh rechazado vuelve al inicio de sesión»), no US-090 CA-2 (credenciales rechazadas). El ID equivocado haría que el test aparezca bajo el criterio que no verifica. | spec principal `ingreso-al-panel`, requisito «Un 401 de la API se renueva una vez o termina la sesión»; 06 US-090 CA-2 y US-092 CA-1 | Retitular a «US-092 CA-1 Borde - …», el nombre del test de la tarea 2.3 a `US-092 CA-1: …` y la fila de la tabla de la proposal. Revisar si «Escenarios mínimos» de C-49 debe sumar «US-092: CA-1» (el mapeo de `CHANGES.md` le asigna US-092 solo a C-07; si se suma, hay que agregar C-49 a la fila US-092 del mapeo y a la historia del Objetivo, o el script falla en la fila 2). Alternativa más simple: dejarlo como borde de presentación sin agregarlo a los mínimos. |
| H3 | Sugerencia | C6 | `tasks.md` 4.4 | El test `US-090 CA-2: sin conexión, el botón vuelve a «Ingresar» sin el ícono de espera` no corresponde a ningún escenario del delta: triangula B2 contra el escenario vigente «sin conexión con la API se muestra otro mensaje». | `config.yaml` `rules.tasks` («cada tarea de test cita el escenario (E#) y la regla (RN)») | Nombrar en la tarea el escenario vigente que triangula, o sumar al escenario B2 un `AND` «si la API no responde, el botón vuelve a habilitarse con el nombre «Ingresar» y sin el ícono». |
| H4 | Sugerencia | C5 | `specs/ingreso-al-panel/spec.md`, escenario STI-1 | El WHEN mezcla dos verificaciones de naturaleza distinta (revisión de los archivos y la consola en Compose). Es verificable (tarea 4.1 con el guard y tarea 5.2 en el navegador), pero el THEN de la consola no tiene test automático. | `config.yaml` `rules.specs` (escenarios verificables) | Aceptable como está; si se prefiere, partir en dos `AND` dejando claro cuál corre en la suite y cuál en la prueba del agente. |
| H5 | Sugerencia | C7 | `design.md` L6 / `tasks.md` 4.2 a 4.4 | El escenario B2 exige un `svg` de espera dentro del botón, pero el ícono depende de Q4 (abierta). Si el autor elige «rechazarlo», el escenario y las tareas 4.2 a 4.4 cambian. | `design.md` Q4 | Al cerrar Q4, ajustar B2 (con o sin la línea del ícono) antes del Apply; el resto del escenario («Ingresando…» deshabilitado) ya está cubierto por C-08. |

No encontré bloqueantes. Los textos de los avisos son los de la spec vigente (RN-AU-04, aviso de sesión terminada); RN-AU-04 y RN-AU-03 existen en 05; no hay estados HTTP nuevos ni cambios de API (C4 y C8 sin hallazgos); los valores visuales (400 px, 40 px, tokens nuevos) están marcados «Propuesta» en el design (C7); los datos son ficticios con dominio `.test` (C9).

## Cobertura

| CA | Escenarios | Tarea que lo verifica |
|----|------------|-----------------------|
| US-090 CA-1 | F1 (marca y solo el formulario), F2 (sin avisos al abrir), B2 (botón de espera) | 2.1, 2.3, 4.2, 4.3; prueba en el navegador 5.2 |
| US-090 CA-2 | E1 (aviso de error con el mensaje exacto, RN-AU-04); B1 (titulado CA-2, pero es US-092 CA-1: H2) | 2.1, 2.3; 5.2 |
| US-090 CA-3 | Ninguno en el delta (H1); escenarios vigentes de `ingreso-al-panel` | Tests vigentes de C-08 (`PaginaIngreso.test.tsx`, CA-3 y «los dos rechazos se ven idénticos»), sin editar |
| STI-1 | B3 (sin recursos de otro origen) | 4.1 (guard); 5.2 (consola sin violaciones de CSP) |

## Bordes sugeridos

- GIVEN la pantalla de inicio de sesión, WHEN la API responde `422` al login, THEN el aviso de error muestra exactamente «Revisá el email y la contraseña.», con el mismo estilo y lugar que el genérico y sin título — aplica porque el design cambia la forma del aviso para los tres mensajes y solo dos tienen escenario (fuente: `PaginaIngreso.tsx`, mensajes de F9 de C-08; ver «Lo que no pude verificar»).
- GIVEN la usuaria inactiva `recepcion@consultorio-demo.test`, WHEN inicia sesión con su contraseña correcta, THEN el aviso es idéntico en texto, rol y ubicación al de una contraseña incorrecta — es el borde de H1 (06 US-090 CA-3; RN-AU-04).
- GIVEN un ancho de ventana chico (por ejemplo 375 px), WHEN se abre `/ingresar`, THEN la tarjeta no desborda horizontalmente — la proposal lo promete en «Fuera de alcance» («solo se cuida que la tarjeta no desborde»), pero no tiene escenario ni verificación; alcanza con sumarlo a la prueba del navegador 5.2 (fuente: `proposal.md`).

## Lo que no pude verificar

- El mensaje «Revisá el email y la contraseña.» (respuesta `422` del login) existe en el código de C-08 pero no en la spec principal de `ingreso-al-panel`; no es un hallazgo de este change, pero si se suma el borde sugerido conviene que el autor confirme que ese texto es parte del contrato.
- Q1 a Q6 del design siguen abiertas; Q2 (pantallas sin pantalla propia de Stitch frente a D234) y Q4 (ícono de espera) pueden cambiar el alcance de las tareas 3.3 y 4.2 a 4.4. La revisión se hizo con las opciones recomendadas.
- La regla `rules.specs` pide «el ID de escenario (E#) en el título»; la spec vigente de `ingreso-al-panel` usa `US-090 CA-n` y `US-092 CA-n` porque los E# de 06 son solo de US-010. El delta sigue la convención de la spec vigente; no lo cuento como hallazgo.
