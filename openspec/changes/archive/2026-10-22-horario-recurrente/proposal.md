# Proposal: horario-recurrente

Change **C-12** de `CHANGES.md`, historia **US-002** («Horario recurrente») y la parte de horario de **E10** (US-010). Gobernanza **MEDIO**: se implementa por grupos con puntos de control y las decisiones no obvias se le muestran al autor. Las once preguntas abiertas del design quedaron cerradas por el autor el 2026-10-22 con la recomendación del agente (D255 a D265), y el plan se ajustó con `/opsx:update` al informe de `revisor-de-escenarios` (hallazgos H1 a H14 y seis bordes sugeridos) y, con un segundo `/opsx:update`, a su segunda revisión (hallazgos N1 a N7), con las cuatro elecciones que seguían «Propuesta» aprobadas como D266 a D269. Depende de C-07 y C-08, los dos archivados (y usa lo que dejaron C-09, C-11 y C-49 en el panel).

## Why

Hoy `POST /turnos` acepta un turno a cualquier hora del día: el sistema no sabe cuándo atiende el profesional. US-002 pide que el odontólogo cargue sus días y franjas de atención y que un turno solo se cree si cae **completo** dentro de una franja vigente de ese día (RN-AG-04), evaluado en la hora del consultorio (RN-GL-01). Es la base de los bloqueos (C-13), del cálculo de disponibilidad (C-24) y del reporte de ocupación (C-47).

Va ahora porque sus dos dependencias están archivadas, la protección por roles (C-07) y el panel (C-08) ya existen, y C-13 y C-24 lo necesitan.

## What Changes

- **Tabla `franja_horaria`** (modelo de `04`, «FranjaHoraria»): `profesional_id`, `dia_semana` (0 = lunes … 6 = domingo), `hora_inicio`, `hora_fin` (hora del consultorio, `CHECK hora_inicio < hora_fin`), `vigente_desde` y `vigente_hasta` nulas, índice `(profesional_id, dia_semana)`. Migración Alembic nueva **`0008`**, reversible.
- **API del horario** (Propuesta de contrato en el design, H4 a H8):
  - `GET /profesionales/{id}/horario`: las franjas del profesional, ordenadas por día y hora de inicio. Leen los tres roles (matriz de `03`, fila «Horario recurrente y bloqueos»).
  - `PUT /profesionales/{id}/horario`: reemplaza el horario semanal completo con la lista de franjas del cuerpo (lista vacía = sin horario). Solo `odontologo`; `403` `RN-AU-05` para los demás, evaluado antes que la entrada (D208).
  - Franjas del mismo día **sin superposición** (US-002 CA-1, HOR-1) y con `hora_inicio < hora_fin`: se rechazan todas juntas con `422` y un código nuevo **`RN-AG-16`** (D257, ya registrado en `05`). Franjas contiguas (09:00-13:00 y 13:00-17:00) no se superponen (intervalos semiabiertos).
  - Profesional inexistente o de otro consultorio en la URL: `404` `RN-GL-04`.
  - `GET /profesionales` de solo lectura (id, nombre, activo) para que la pantalla elija el profesional (D260).
- **`crear_turno` valida RN-AG-04** (E10, US-002 CA-2): el turno `[inicio, fin)` convertido a la zona del consultorio (`Consultorio.zona_horaria`) debe caer completo dentro de una franja del día de la semana local de `inicio`. Si no, `422` con `RN-AG-04` y no se crea nada. Orden de las reglas de negocio: validación de entrada → RN-AG-10d → **RN-AG-04** → solapamiento (el de `07` Flujo 1, pasos 4 a 6; design H8). Una sola franja, sin sumar contiguas (D258); solo cuentan las franjas vigentes (D259). Un profesional sin franjas no admite turnos (D256). Un turno que termina justo a las 00:00 del consultorio no cabe en ninguna franja (D265).
- **Seed de la demo**: el horario de ejemplo de `04` (D56) para el profesional 1: lunes a viernes 09:00-13:00 y 15:00-19:00, en SQLite y en PostgreSQL (repetible). Los ejemplos del README (`2026-11-02T13:00:00Z`, lunes 10:00 de Buenos Aires) siguen dando `201`.
- **Tests existentes**: las fábricas de test dan por defecto a cada profesional un horario de prueba que cubre toda la semana, para que los tests de C-01 a C-09 sigan probando lo mismo sin cambiar sus horas (D263; análisis en el design, «Riesgo: tests que se rompen»).
- **Pantalla «Horario»** en `/panel/horario`, a partir de la pantalla de **Stitch** con el design system «Clinical Ops» (D234): un día por fila, las franjas con «Desde» y «Hasta», «Agregar franja», «Quitar» y «Guardar horario»; los rechazos de la API con su código (`RN-AG-16`, `RN-AU-05`, `RN-GL-04`); la sesión que termina vuelve al inicio de sesión. Enlace «Horario» en la barra del panel. Pantalla de Stitch: `projects/14200813501064679723/screens/c3cccdb362364deba0d4eaac0d678b4d` (el MCP no devolvió el id; el autor lo copió del canvas), con lo que se toma y se rechaza en el design.

**BREAKING** (comportamiento, no contrato): `POST /turnos` empieza a rechazar con `422` `RN-AG-04` los turnos fuera del horario del profesional. La forma de las respuestas no cambia.

### Escenarios

Cubre los cuatro mínimos de la entrada C-12 de `CHANGES.md` (dentro del «3 a 6»):

| ID | Qué verifica | Dónde corre |
|---|---|---|
| US-002 CA-1 | Se cargan varias franjas por día (mañana y tarde) y se leen igual | pytest (API) + Vitest (pantalla) + navegador |
| US-002 CA-2 | Un turno que excede el fin de la franja se rechaza con `RN-AG-04` | pytest (dominio y API) + navegador (Swagger) |
| E10 (parte de horario) | Un turno fuera del horario se rechaza con `RN-AG-04`, evaluado en la zona del consultorio; los bordes del intervalo semiabierto se aceptan | pytest (dominio, integración y API) |
| HOR-1 | Dos franjas superpuestas del mismo día se rechazan (`422` `RN-AG-16`) y no cambia nada | pytest + Vitest + navegador |

Los specs los detallan en escenarios felices, de error de negocio y de borde (conteo en el design). La parte de E10 que habla de **bloqueos** (RN-AG-04b) queda para C-13.

## Fuera de alcance

- **Bloqueos puntuales** (RN-AG-04b, `GET/POST/DELETE /bloqueos`): C-13.
- **Excepción de horario puntual**: Fase 2 (D86, nota de RN-AG-04).
- **Cálculo de disponibilidad** (huecos libres, `GET /disponibilidad`): C-24.
- **Editar la vigencia** (`vigente_desde`, `vigente_hasta`) desde la API o la pantalla: las columnas se crean nulas (D259).
- **Cancelar, reprogramar o listar los turnos que quedan fuera** de un horario nuevo: el `PUT` no toca los turnos existentes (D261).
- **Alta, edición o desactivación de profesionales**: multi-profesional es Fase 2 (D46); `GET /profesionales` es solo lectura.
- Granularidad de las horas de una franja (US-005), franjas que crucen la medianoche o terminen a las 24:00 (D265), copiar el horario de un día a otro, plantillas.
- Varios consultorios por instalación (D173).

## Capabilities

### New Capabilities

- `horario-recurrente`: el contrato de la API del horario semanal de un profesional: leer y reemplazar sus franjas, las reglas de las franjas (inicio antes del fin, sin superposición en el mismo día), la lista de profesionales para elegir, quién puede usar cada ruta y el horario de la demo (US-002; RN-AG-04, RN-AG-16, RN-AU-05, RN-GL-04).
- `pantalla-de-horario`: cómo el panel muestra y edita ese horario desde el navegador: la semana por días, agregar y quitar franjas, guardar, los rechazos de la API con su código y qué pasa si la sesión termina en la pantalla (US-002, US-092 CA-1).

**Dos capabilities nuevas en un change** se aparta de la regla «una sola capability» (`openspec/config.yaml`, regla dura 12), como C-09 (D241): excepción registrada y limitada a C-12 (D255).

### Modified Capabilities

- `creacion-de-turnos`: se agrega el requisito de RN-AG-04 (el turno cae completo en una franja del profesional, en la zona del consultorio; E10) y su lugar en el orden de las reglas de negocio; el requisito del caso feliz (E1) pasa a exigir la franja.
- `persistencia-postgresql`: el requisito «Esquema de PostgreSQL creado por migraciones» suma la tabla `franja_horaria` y el escenario de deshacer solo la migración `0008`.

Se revisaron sin cambios: `proteccion-del-panel` (su matriz cubre «las rutas creadas antes» de C-07 y el guard de rutas protegidas ya alcanza a las nuevas; los permisos de `/profesionales` quedan en `horario-recurrente`, como hizo C-09), `historial-de-turnos` (un rechazo por RN-AG-04 no registra nada, como cualquier rechazo), `ingreso-al-panel`, `pantalla-de-prestaciones` y `pantalla-de-usuarios` (el enlace nuevo de la barra no cambia sus requisitos).

## Impact

- **Backend, código nuevo**: `backend/app/domain/agenda/horario.py` (franja, validación de franjas y RN-AG-04, puros), `backend/app/application/horario.py`, `backend/app/api/routers/profesionales.py`, `backend/app/infrastructure/repositories/horario.py`, errores nuevos en `domain/errors.py` y su traducción en `api/errores.py`, permisos `horario.leer`, `horario.editar` y `profesionales.leer` en `domain/acceso/roles.py`, modelo `FranjaHorariaModelo` en `infrastructure/db/modelos.py`, migración `0008_franja_horaria.py`. **Se modifica**: `application/crear_turno.py` (RN-AG-04), `application/puertos.py`, `infrastructure/unidad_de_trabajo.py`, `infrastructure/db/seed_demo.py` y `cargar_seed.py`, `tests/factories.py` (horario por defecto).
- **Frontend, código nuevo**: `frontend/src/features/horario/` (cliente, página, semana, mensajes y tests). **Se modifica**: `App.tsx`, `pages/PanelBase.tsx` (enlace «Horario»), `test/servidorFalso.ts`, `shared/estilos/panel.css` y `tokens.css`, un ícono SVG nuevo en `shared/iconos/`.
- **Esquema**: tabla nueva `franja_horaria` (migración `0008`); sin cambios en las tablas existentes.
- **Dependencias y variables de entorno**: ninguna nueva.
- **Documentación**: `README.md`; evidencia de Stitch en `docs/skills-mcp/evidencias/sesion-nueva/stitch-horario.md` y `stitch-horario-pantalla/` (captura y HTML). Ya registrados: D255 a D269 en `10`, `RN-AG-16` en `05` y en US-002 de `06`. Al archivar: la nota de E10 en `06`, `07` Flujo 1, `08`, `02` y `03`, el alcance de C-12 en `CHANGES.md` (`GET /profesionales`, D260), la regla dura 2 y el párrafo de estado de `CLAUDE.md` y `AGENTS.md` (lista completa en las «Notas para el archive» del design).
- **Tamaño**: 31 tareas en 13 grupos para 59 escenarios, frente a «alrededor de 20» de `CHANGES.md`: excepción limitada a C-12 (D264, como D251).
