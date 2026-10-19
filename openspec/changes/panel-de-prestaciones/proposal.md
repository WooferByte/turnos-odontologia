# Proposal: panel-de-prestaciones

Change **C-11** de `CHANGES.md`, historia **US-001** («Tabla de prestaciones», parte de interfaz; la API la implementó C-04 `gestion-de-prestaciones`). Gobernanza **BAJO**. Depende de C-04 y C-08, los dos archivados. Es la primera pantalla de negocio del panel y el primer change que usa la referencia visual de Stitch (MCP).

## Why

Desde C-04 el catálogo de prestaciones existe como API (`GET/POST /prestaciones`, `PATCH /prestaciones/{id}`) y desde C-08 el panel sabe iniciar sesión, pero el odontólogo todavía solo puede mantener sus prestaciones desde Swagger, pegando el token a mano. La historia US-001 está escrita para el odontólogo, no para quien lee OpenAPI: sin pantalla, la tabla de prestaciones (de la que sale la duración de cada turno) no es usable por el consultorio.

Va ahora porque las dos dependencias están archivadas, no lleva migración ni cambios de API (puede aplicarse en paralelo a un change de backend, `CHANGES.md` GATE 4) y es el primer uso real de `pedidoDelPanel` de C-08 desde una pantalla.

## What Changes

- **Pantalla «Prestaciones»** en `/panel/prestaciones` (Propuesta), a la que se llega desde un enlace del encabezado del panel base: tabla con color, nombre, duración en minutos, reserva online y estado de cada prestación del consultorio, activas e inactivas (las inactivas atenuadas y con la insignia «Inactiva», nunca solo por color).
- **Alta y edición en un panel lateral** (referencia visual de Stitch): nombre, duración en minutos (con la ayuda «Mayor que 0 y múltiplo de 5»), **selector de color** (el nativo del navegador, con la muestra y el valor hex) y la casilla «Ofrecer en la reserva online». La edición manda solo los campos que cambiaron y «Guardar» sin cambios no pide nada. La interfaz no valida la duración (D232) y el selector empieza en `#1E88E5` y manda el hex en mayúsculas (D233).
- **Desactivar y reactivar** desde la fila (`PATCH` con `activa`); no hay borrado (RN-GL-03).
- **Errores de la API mostrados con su código**: la duración inválida se muestra debajo del campo con `RN-AG-01` (US-001 CA-2), el nombre repetido debajo del nombre con `RN-AG-15`, la prestación inexistente con `RN-GL-04` y el rol sin permiso con `RN-AU-05`. La interfaz **no** reimplementa las reglas: las decide la API y la pantalla las muestra.
- **Aviso de CA-3** en la edición: «Cambiar la duración no modifica los turnos ya creados.» (US-001 CA-3; RN-AG-02 la cumple la API desde C-04).
- **Solo el rol `odontologo` edita; los demás leen** (matriz de `03`, D205): la API rechaza la escritura con `403` `RN-AU-05` y la pantalla lo muestra sin tocar la sesión, en el aviso del panel (conservando lo escrito) o arriba de la tabla. Las acciones se ven para todos los roles, porque ninguna ruta informa el rol (decisión del autor **D230**, Q2 del design).
- **Cableado de la sesión terminada**: el proveedor de sesión de C-08 pasa a ofrecer `pedidoDelPanel` a las pantallas y, ante `SesionTerminada`, vuelve a `/ingresar` con el aviso (requisito ya vigente de `ingreso-al-panel` que C-08 dejó sin cablear porque ninguna pantalla lo usaba; decisión del autor **D231**, Q3 del design). El spec lo cubre con un Requirement propio de la pantalla.
- **Estilos mínimos con los tokens de «Clinical Ops»** (Stitch): tipografía, colores, densidad de la tabla y errores de campo, en CSS propio sin dependencias nuevas.
- **Servidor falso de la API** ampliado con el contrato de `gestion-de-prestaciones` y roles; tests de Vitest por escenario; README con la pantalla, la tabla escenario → test y el recorrido.

No hay cambios en el backend ni en la API, ni dependencias nuevas. No hay **BREAKING**.

### Escenarios

Cubre los tres mínimos de la entrada C-11 de `CHANGES.md` (dentro del «3 a 6»); el spec los detalla en 33 escenarios (8 felices, 6 de error de negocio y 19 de borde):

| ID | Qué verifica en la pantalla | Dónde corre |
|---|---|---|
| US-001 CA-1 | Listar (también mientras carga, vacío y sin conexión), crear, editar (también sin cambios), desactivar y reactivar; el nombre repetido se muestra con `RN-AG-15`; la prestación inexistente con `RN-GL-04`; el rol sin permiso con `RN-AU-05`, antes que cualquier error de entrada; sin conexión al guardar o al desactivar | Suite del frontend + prueba en el navegador |
| US-001 CA-2 | Una duración que no es mayor que 0 o no es múltiplo de 5 se muestra debajo del campo con `RN-AG-01`, en el alta y en la edición, y no cambia nada | Suite del frontend + prueba en el navegador |
| US-001 CA-3 | La edición avisa que cambiar la duración no toca los turnos existentes y cambia solo la prestación | Suite del frontend + prueba en el navegador (la invariancia de los turnos ya la prueba la API, C-04) |

No queda fuera ningún criterio de US-001. US-092 CA-1 (la sesión que termina mientras se está en la pantalla) es un requisito ya vigente de `ingreso-al-panel`; como C-11 lo cablea (D231), el spec suma tres escenarios `US-092 CA-1` vistos desde esta pantalla (renovación que sigue, sesión irrenovable al abrir y al guardar), sin contarlos entre los mínimos de C-11 y sin cambiar `ingreso-al-panel`.

## Fuera de alcance

- **Cambios de API o de esquema**: sin rutas nuevas (tampoco `GET /auth/yo`), sin campos nuevos, sin borrado de prestaciones (`CHANGES.md` C-11).
- **Pantalla de sillones**: US-004 no tiene interfaz (`06`, «Changes técnicos y frontend»).
- **Validar las reglas en el navegador**: la duración (RN-AG-01) y el nombre repetido (RN-AG-15) los decide la API; la interfaz solo exige que los campos obligatorios no estén vacíos.
- **Efecto de `reservable_online`** en la reserva pública (C-24) y **granularidad configurable** (C-22, US-005): la ayuda y el mensaje dicen 5 minutos (D99).
- **Menú o pantallas según el rol** (D230: sin `GET /auth/yo`, las acciones se ven para todos); gestión de usuarios (C-09).
- Búsqueda, filtros, orden por columna, paginación, arrastrar para reordenar, eliminar.
- Biblioteca de componentes, sistema de diseño completo, modo oscuro, internacionalización, pruebas de extremo a extremo con navegador real.
- Sobreturnos y excepción de horario: fuera de la v1.

## Capabilities

### New Capabilities

- `pantalla-de-prestaciones`: cómo el panel muestra y mantiene el catálogo de prestaciones del consultorio desde el navegador: la tabla con activas e inactivas, el alta y la edición en el panel lateral con el selector de color, desactivar y reactivar, el aviso de CA-3 y cómo se muestran los rechazos de la API con su código (`RN-AG-01`, `RN-AG-15`, `RN-GL-04`, `RN-AU-05`) y qué pasa si la sesión termina mientras se usa la pantalla (US-001, US-092 CA-1; decisión del autor **D229**, Q1 del design). Es una capability de interfaz, como `ingreso-al-panel` (D218): `gestion-de-prestaciones` sigue siendo el contrato de la API y `proteccion-del-panel` el de quién puede llamar a cada ruta.

### Modified Capabilities

Ninguna. Se revisaron `gestion-de-prestaciones` y `proteccion-del-panel` (describen la API, que no cambia) e `ingreso-al-panel`: su requisito «Un 401 de la API se renueva una vez o termina la sesión» ya pide volver al inicio de sesión con el aviso; este change lo cablea en el proveedor sin cambiar el requisito.

## Impact

- **Código nuevo**: `frontend/src/features/prestaciones/` (cliente de la API de prestaciones, página, tabla, panel lateral, mensajes y sus tests) y `frontend/src/shared/estilos/` (tokens y estilos del panel).
- **Código que se modifica**: `frontend/src/App.tsx` (ruta `/panel/prestaciones`), `frontend/src/pages/PanelBase.tsx` (encabezado con el enlace y lugar para la pantalla), `frontend/src/shared/api/ProveedorDeSesion.tsx` (expone `pedidoDelPanel` y maneja `SesionTerminada`), `frontend/src/shared/api/errores.ts` (errores de la API con código y errores de campo), `frontend/src/test/servidorFalso.ts` (contrato de prestaciones y roles) y `README.md`.
- **Backend y API**: sin cambios (`backend/` no se toca).
- **Dependencias**: ninguna nueva; `frontend/package.json` y `package-lock.json` no cambian. Sin variables de entorno nuevas.
- **Documentación**: `README.md`. `knowledge-base/10_preguntas_abiertas.md` registra D229 a D233 (respuesta del autor a Q1 a Q5). Al archivar, `CHANGES.md` marca C-11 y, por D231, la entrada de C-09 deja de listar el cableado de `SesionTerminada`; `CLAUDE.md` y `AGENTS.md` se re-sincronizan con D229 a D233.
- **Tamaño**: 20 tareas en 9 grupos, dentro del «alrededor de 20» de `CHANGES.md`, para 33 escenarios.
