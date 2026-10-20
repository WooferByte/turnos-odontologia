# Revisión de escenarios: `inicio-de-sesion-con-diseno-de-stitch` (después del update)

Fecha: 2026-10-20, después del `/opsx:update` que cerró Q1 a Q6 como D235 a D240 y corrigió H1 a H5 de `revision-de-escenarios.md` (el «antes»). Informe de la skill `revisor-de-escenarios`: no edita los artefactos.

**Veredicto**: listo con correcciones menores
**Base**: 7 escenarios (feliz 2, error de negocio 2, borde 3, otros 0); CA mínimos 3/3; tareas cruzadas 7/7. El script marca «NO» en STI-1 porque busca un CA, pero la tarea 4.1 lo cita por su ID y la 5.2 verifica la consola.

## Estado de los hallazgos del «antes»

| ID | Estado | Dónde quedó |
|----|--------|-------------|
| H1 | Resuelto | Escenario nuevo «US-090 CA-3 Error de negocio - la usuaria inactiva ve el mismo aviso que una contraseña incorrecta»; test en la tarea 2.3 |
| H2 | Resuelto | El escenario de sesión terminada se titula «US-092 CA-1 Borde …» y cita RN-AU-03; tarea 2.3 y tabla de la proposal actualizadas; no se suma a los mínimos (US-092 es de C-07 en el mapeo), con el motivo en la proposal |
| H3 | Resuelto | El escenario del botón suma el `AND` de la vuelta a «Ingresar» sin conexión, con el mensaje exacto en el lugar del genérico; la tarea 4.4 lo cita |
| H4 | Resuelto | STI-1 dice qué parte verifica la suite y qué parte la prueba en el navegador |
| H5 | Resuelto | El ícono queda fijado por D238 y el escenario lo cita |

De los bordes sugeridos: la usuaria inactiva entró (H1); el ancho de 375 px entró a la prueba del navegador (tarea 5.2, design L12) sin escenario, con el motivo (jsdom no calcula disposición); el del mensaje del `422` se descartó con motivo (design, «Contradicciones y huecos» 6: sumaría un mensaje al contrato de la capability). Me parecen descartes razonables y con fuente.

## Hallazgos

| ID | Severidad | Control | Ubicación | Hallazgo | Fuente | Corrección propuesta |
|----|-----------|---------|-----------|----------|--------|----------------------|
| H6 | A corregir | C6 | `tasks.md` 5.2; `proposal.md`, tabla de escenarios (fila US-090 CA-3, «Suite del frontend + prueba en el navegador») | En la demo la recepcionista está **activa** (`backend/app/infrastructure/db/seed_demo.py`, `cargar_recepcionista_demo_si_falta`, `activo=True`, D212), así que en el navegador `recepcion@consultorio-demo.test` con su contraseña **entra al panel**: no reproduce US-090 CA-3. La tarea 5.2 dice «→ el mismo aviso (según los datos de la demo)», que es ambiguo, y la proposal promete verificar CA-3 en el navegador. Solo el servidor falso de la suite tiene a la recepcionista inactiva. | `seed_demo.py` (D212); `frontend/src/test/servidorFalso.ts` (comentario de `EMAIL_INACTIVA`); `config.yaml` `rules.tasks` (la prueba en el navegador recorre los escenarios con su respuesta) | En la proposal, dejar CA-3 como «Suite del frontend» y, en la tarea 5.2, reemplazar el paso de la recepcionista por «la usuaria inactiva no existe en la demo: CA-3 queda cubierto por el test de la tarea 2.3» (o, si el autor quiere verlo en el navegador, desactivarla antes; la API de usuarios es de C-09, así que hoy no hay cómo sin tocar la base). |

No encontré bloqueantes. Los textos de los avisos son los de la spec vigente; RN-AU-03 y RN-AU-04 existen en 05 y dicen lo que el delta les atribuye; no hay estados HTTP nuevos ni cambios de API (C4, C8); D235 a D240 están registradas en `10_preguntas_abiertas.md` y los valores visuales restantes siguen marcados «Propuesta» (C7); los datos son ficticios con dominio `.test` (C9).

## Cobertura

| CA | Escenarios | Tarea que lo verifica |
|----|------------|-----------------------|
| US-090 CA-1 | F1 (marca y solo el formulario), F2 (sin avisos al abrir), B2 (botón de espera y vuelta a «Ingresar» sin conexión) | 2.1, 2.3, 4.2, 4.3, 4.4; 5.2 |
| US-090 CA-2 | E1 (aviso de error con el mensaje exacto, RN-AU-04) | 2.1; 5.2 |
| US-090 CA-3 | E2 (la usuaria inactiva ve el mismo aviso, RN-AU-04) | 2.3 (en el navegador no se puede reproducir con la demo: H6) |
| US-092 CA-1 (borde, fuera de los mínimos) | B1 (aviso de sesión terminada antes de los campos, RN-AU-03) | 2.3; 5.2 |
| STI-1 | B3 (sin recursos de otro origen) | 4.1 (guard); 5.2 (consola sin violaciones de CSP) |

## Bordes sugeridos

Ninguno nuevo. Los bordes de la interfaz que aplican al change (error de red, estado de carga, doble envío) ya están cubiertos: el error de red en B2, el «Cargando…» en la tarea 3.3 sobre el escenario vigente de US-092 CA-1, y el doble envío en el escenario vigente «un segundo clic mientras espera no manda otro login».

## Lo que no pude verificar

- Que `compareDocumentPosition` dé el orden esperado en jsdom 30.1.2: el design lo deja como V1, antes de cerrar la tarea 2.2.
- La regla `rules.specs` pide el ID de escenario (E#) en el título; la spec vigente de `ingreso-al-panel` usa `US-090 CA-n` y `US-092 CA-n` porque los E# de 06 son solo de US-010, y el delta sigue esa convención. No lo cuento como hallazgo.
