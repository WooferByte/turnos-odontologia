# Proposal: panel-historial-de-turno

Change **C-15** de `CHANGES.md` (US-015, fase 4, orden 4). Gobernanza **BAJO**: autonomía completa si los tests pasan. Depende de C-03 (historial por la API, archivado el 2026-10-14) y de C-14 (agenda del día, archivado el 2026-10-28). Las preguntas **Q1 a Q6** del design quedaron respondidas por el autor el 2026-10-28 con la recomendación del agente, junto con los hallazgos H1 a H7 de `revisor-de-escenarios` con su corrección propuesta («Sí, todo»), y están registradas como **D326 a D331** en `knowledge-base/10_preguntas_abiertas.md`.

## Why

Desde C-03 cada turno guarda su historial (RN-AG-11) y desde C-07 cada evento lleva al usuario que lo produjo, pero solo se puede leer desde Swagger con `GET /turnos/{id}/historial`. US-015 pide que el dueño (y el odontólogo y la recepcionista, matriz de `03`) vean «quién cambió qué y cuándo» en un turno. Va ahora porque C-14 ya dejó la agenda donde se suman las acciones sobre un turno «sin pantalla nueva» (D112), y porque C-16 a C-19 agregarán eventos que conviene poder ver desde el primer día.

## What Changes

- **Botón «Historial» en cada fila de la agenda** (`/panel/agenda`, C-14) que abre un **panel lateral «Historial del turno»** de solo lectura, con el resumen del turno (paciente, prestación, día y horario, tomados de la fila) y sus eventos del más antiguo al más reciente, en el orden de la API. **Un solo panel lateral a la vez** («Historial» cierra «Nuevo turno» y al revés) y el historial se cierra al cambiar de día (D327).
- **Cada evento** muestra qué pasó («Turno creado»), cuándo (fecha y hora **del consultorio**, con la zona que trae la agenda) y quién («Usuario n.º 2»; «Usuario del panel (sin identificar)» para los eventos anteriores a C-07, D159); el `creado` suma «Estado inicial: Reservado · 09:00 – 09:30» a partir de su `despues` (D328 y D329).
- **Estados del panel**: cargando, sin eventos (turnos anteriores a la migración `0003`, D160), `404` `RN-GL-04`, `403` `RN-AU-05`, sin conexión o `5xx` con «Reintentar» y la sesión que termina (D330).
- **Sin cambios de API**: usa `GET /turnos/{id}/historial` tal como lo dejó C-03 (D166, D167), que ya admite a los tres roles con `historial.leer` (matriz de C-07). Sin migraciones, sin dependencias nuevas, sin variables de entorno nuevas. No hay **BREAKING**.
- **Pantallas de Stitch** (D234), generadas en este propose con «Clinical Ops»: historial de escritorio `projects/14200813501064679723/screens/2955e5e29bba4982a0b515329e0ff4e1` y angosta `projects/14200813501064679723/screens/c80d02b8dbac4e48be68ca11ff787857`; qué se toma y qué se rechaza, en el design.
- **README**: el historial en «Panel (interfaz)», la tabla escenario → test y los límites conocidos. **Sin guía de prueba manual** en `docs/guias/`: los changes BAJO de la fase 4 reciben una guía acumulada después del cuarto archivado (proceso del 2026-10-28).

### Escenarios

Cubre los mínimos de la entrada C-15 de `CHANGES.md`: **US-015 CA-1** (el historial es de solo lectura), **E9** (el evento `creado` aparece en la vista) y **HIS-2** (los eventos se muestran en orden cronológico con actor y fecha). El spec los detalla en **6 escenarios** (`HIS-2a` a `HIS-2f`, después del `/opsx:update` con el informe de `revisor-de-escenarios`), dentro del «3 a 6» de `config.yaml`: con uno feliz, uno de error de negocio y cuatro de borde. `HIS-2` vive en `CHANGES.md` (la KB solo define `HIS-1`, de C-03), y el «Como dueño» de US-015 se lee con la matriz de `03`: los tres roles leen el historial (D68; hallazgo H7).

| ID | Qué verifica | Dónde corre |
|---|---|---|
| HIS-2a | Desde la agenda, «Historial» muestra el evento `creado` con su fecha y hora del consultorio, su actor y el estado inicial, para los tres roles, sin ninguna acción de edición y con el foco en el título (US-015 CA-1, E9) | Vitest + navegador |
| HIS-2b | Varios eventos salen en el orden de la API, cada uno con su actor y su fecha; un actor sin id y un tipo que la pantalla todavía no conoce también se ven (HIS-2) | Vitest |
| HIS-2c | Un turno sin eventos; «Cerrar» sin petición nueva y con el foco de vuelta en la fila; una respuesta que llega después de cerrar no lo reabre | Vitest + navegador |
| HIS-2d | `404` `RN-GL-04` y `403` `RN-AU-05` (el permiso se pierde con la agenda ya cargada) con su texto, sin «Reintentar» | Vitest |
| HIS-2e | Cargando, sin conexión o `500` con «Reintentar», y la sesión que se renueva sola o vuelve al inicio de sesión | Vitest |
| HIS-2f | Otro turno muestra solo el último pedido; un solo panel lateral a la vez; cambiar de día cierra el historial y una respuesta tardía no lo reabre | Vitest |

**Quedan fuera**: los escenarios de la API del historial (E9, US-015 CA-1 y HIS-1 de `historial-de-turnos`), que ya cubrió C-03 y no cambian.

## Fuera de alcance

- **Editar, borrar o agregar eventos**: el historial es de solo lectura (US-015 CA-1, RN-AG-11); la API solo tiene `GET` (D167) y el panel no muestra ningún control de edición.
- **Historial para el paciente** (D68): la vista es solo del panel; el link de gestión (C-29) no la muestra.
- **Auditoría de pacientes** (`EventoPaciente`, C-21).
- **Acciones sobre el turno** (reprogramar C-16, cancelar C-17, marcar C-18 y C-19) y los eventos que ellas agregan; cada change suma la etiqueta y el detalle de su tipo de evento.
- **El nombre o el email del actor**: la API devuelve solo `actor_id`; mostrar el email exigiría cambiar `GET /turnos/{id}/historial` y que la recepcionista lea usuarios, que hoy no puede (D328).
- **Cambios en la API del historial**, incluido filtrar por el consultorio del usuario (D331: la v1 tiene un solo consultorio).
- **Ocultar «Historial» según el rol** (D312): los tres roles pueden leerlo, así que no hace falta.

## Capabilities

### New Capabilities

- `pantalla-de-historial`: cómo el panel muestra en el navegador el historial de un turno abierto desde la agenda: qué se ve de cada evento, en qué orden, que es de solo lectura, y cómo se ven la carga, el vacío, los rechazos y la sesión que termina (US-015 CA-1; E9; HIS-2; RN-AG-11, RN-GL-04, RN-AU-05).

Una sola capability, como pide `config.yaml` (D326).

### Modified Capabilities

Ninguna. Se revisaron:
- `historial-de-turnos`: `GET /turnos/{id}/historial` no cambia (ni la forma de la respuesta ni los permisos).
- `pantalla-de-agenda`: la fila suma el botón «Historial», pero sus requisitos (qué se ve de cada turno, cómo se cambia de día, el alta) no cambian; el botón y lo que abre, y el panel único, quedan en `pantalla-de-historial` (D326).
- `proteccion-del-panel` y `consulta-de-turnos`: sin rutas ni permisos nuevos.

## Impact

- **Frontend**: `src/features/historial/` nuevo (cliente `apiHistorial.ts`, `PanelHistorial.tsx`, `mensajes.ts` y sus tests); `features/agenda/TablaDeTurnos.tsx` (columna con el botón «Historial») y `PaginaAgenda.tsx` (qué panel lateral está abierto); `test/servidorFalso.ts` (`GET /api/turnos/{id}/historial` con eventos de partida, `404` para un turno inexistente y los modos de falla que ya existen); `panel.css` y, si hace falta, `tokens.css`; un ícono SVG de reloj en `shared/iconos/`.
- **Backend, esquema y migraciones**: sin cambios.
- **Dependencias y variables de entorno**: ninguna nueva.
- **Documentación**: `README.md`; evidencia de Stitch en `docs/skills-mcp/evidencias/sesion-nueva/stitch-historial.md` y `stitch-historial-pantalla/`. Las respuestas a Q1 a Q6 quedaron en `knowledge-base/10_preguntas_abiertas.md` (D326 a D331) con el `/opsx:update` del 2026-10-28, que también anotó en `06` §US-015 la lectura de «Como dueño» con la matriz de `03` y en `02` (fila Historial) el límite de D331.
- **`CHANGES.md`**: C-15 pasa a `[~]` en curso con este propose.
- **Tamaño**: 16 tareas en 6 grupos para 6 escenarios, dentro de lo que pide `config.yaml`; no hace falta excepción.
