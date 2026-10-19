# Informe de aplicación: skill propia y MCP (Parte 2)

Agente: Claude Code (app de escritorio, Windows). Fecha: 2026-10-19. Change preparado: **C-11 `panel-de-prestaciones`** (el mismo de la ficha; no cambió la elección).

## 1. Resultados

| Incorporación | Resultado | Evidencia |
|---|---|---|
| Skill propia `revisor-de-escenarios` | Creada con `skill-creator`. En su evaluación, con la skill se cumplió el 100 % de los criterios y sin ella el 90 % (2 casos sobre C-04, 3 corridas cada uno). Está versionada en `.claude/skills/` con el script `inventario.py`. | [benchmark](evidencias/skill-creator/benchmark.md), [visor](evidencias/skill-creator/visor.html) |
| Uso en una sesión nueva | Se preguntó qué herramienta del proyecto revisa escenarios, sin nombrar la skill. El agente la encontró por `CLAUDE.md` y la corrió sobre C-04 archivado: «listo para implementar», 0 bloqueantes y 5 sugerencias. | [informe C-04](evidencias/sesion-nueva/revision-de-escenarios-gestion-de-prestaciones.md) |
| MCP Google Stitch | Configurado en `.mcp.json`, con la key en `STITCH_API_KEY`. Se ejecutaron `list_projects`, `create_project`, `generate_screen_from_text`, `get_project` y `list_screens`. | [conexión](evidencias/sesion-nueva/stitch-conexion.md), [diseño C-11](evidencias/sesion-nueva/stitch-c11.md) |
| Change C-11 | Propose completo (proposal, design, spec y tasks): 33 escenarios verificables (feliz 8, error de negocio 6, borde 19), 20 tareas con su verificación y `openspec validate --strict` sin errores. Quedó en `[~]` en `CHANGES.md`, sin implementar. | `openspec/changes/panel-de-prestaciones/` |

**Cómo se usaron en el change:**

- **Stitch** generó el design system «Clinical Ops» a partir de la descripción de la pantalla con datos ficticios. El `design.md` lo cita en la sección «Referencia visual (Stitch)» y en T8, T9 y T12: tabla con panel lateral de edición, tokens de color y tipografía, errores debajo del campo y filas inactivas atenuadas.
- **La skill** revisó el propose:
  - **Primera revisión:** «listo con correcciones menores», con 4 hallazgos a corregir y 3 sugerencias.
  - **Corrección:** con ese informe, `/opsx:update` agregó 9 escenarios y cerró las preguntas del design como decisiones del autor D229 a D233.
  - **Segunda revisión:** «listo para implementar», con los 11 puntos anteriores resueltos ([antes](evidencias/sesion-nueva/revision-de-escenarios-panel-de-prestaciones.md), [después](evidencias/sesion-nueva/revision-de-escenarios-panel-de-prestaciones-despues.md)).

## 2. Archivos modificados y motivo

| Archivo | Motivo |
|---|---|
| `.claude/skills/revisor-de-escenarios/SKILL.md` y `scripts/inventario.py` | Skill propia (nueva). El script cuenta escenarios, CA, códigos RN y tareas, para que esa parte de la revisión sea objetiva. |
| `.atl/skill-registry.md` | Registro de la skill: propósito, ubicación, cuándo usarla y sus reglas compactas. |
| `CLAUDE.md` y `AGENTS.md` (idénticos) | Cuándo usar la skill, qué necesita y cómo leer el informe; sección «Integraciones MCP» (Stitch como integración, no como skill); paso de revisión en el flujo de trabajo. |
| `.mcp.json` | Configuración reproducible de Stitch, sin secretos (`${STITCH_API_KEY}`). |
| `docs/skills-mcp/mcp-stitch.md` y `README.md` | Requisitos, pasos, variable de entorno, comprobación y solución de problemas, enlazados desde el README. |
| `openspec/config.yaml` | El contexto del agente menciona la skill y el MCP. |
| `knowledge-base/10_preguntas_abiertas.md` | Decisiones del autor D229 a D233 de C-11 (capability, 403 en la interfaz, sesión terminada, duración y selector de color). |
| `CHANGES.md` | C-11 pasa de `[ ]` a `[~]` (propuesto), según la leyenda del roadmap. |
| `openspec/changes/panel-de-prestaciones/` | Artefactos del change y las dos revisiones de la skill. |
| `docs/skills-mcp/investigacion.md` | Ficha recortada a dos páginas, con los pendientes de Stitch resueltos al conectar. |
| `docs/skills-mcp/evidencias/` | Evaluación de `skill-creator`, revisión crítica y evidencias de la sesión nueva. |

No se regeneró la fundación ni se marcaron como hechas etapas que no se hicieron. La resincronización de `CLAUDE.md` y `AGENTS.md` con D229 a D233 y el ajuste de la entrada de C-09 quedan para el archivado de C-11, como dice su `design.md`.

## 3. Revisión crítica

1. **Sugerencia inadecuada de la skill (control C8).**
   - **Qué pasó:** en la evaluación, la skill marcó como fuera de alcance un escenario de C-04 que solo **comprueba** el efecto de desactivar una prestación en `POST /turnos`.
   - **Cómo se detectó:** en otra corrida, el mismo escenario sin cambios no había sido marcado.
   - **Fuentes que lo corrigen:** D175 no prohíbe verificar ese efecto, y la regla dura 12 habla de lo que se **implementa**, no de lo que se verifica.
   - **Corrección:** se precisó C8 en `SKILL.md`. El antes y el después están en [revision-critica-C8.md](evidencias/skill-creator/revision-critica-C8.md).
2. **Omisiones del agente en el propose de C-11, detectadas con la skill.**
   - **Qué faltaba:** el agente que escribió la spec dejó sin escenario tres comportamientos que sí tenían test:
     - guardar sin cambios;
     - el estado «Cargando…»;
     - el cableado de la sesión terminada.
     También escribió un escenario que no se podía verificar: «la prestación ya no existe», sin un id concreto.
   - **Fuentes:** la skill citó `config.yaml` (cada escenario con su test) y el control C5.
   - **Corrección:** se corrigió con `/opsx:update`. El antes y el después están en los dos informes.
3. **Pedido inadecuado a Stitch.**
   - **Qué pasó:** el texto que envió el agente pedía ocultar «Nueva prestación» a quien no es odontólogo.
   - **Por qué es inadecuado:** la interfaz no puede saberlo, porque el access token no lleva roles y no existe `GET /auth/yo`.
   - **Cómo se detectó:** el agente del propose lo contrastó con C-07 y C-08.
   - **Corrección:** el design muestra las acciones a todos y presenta el `403` `RN-AU-05` de la API (D230). El diseño de Stitch quedó como referencia visual y la KB manda.
4. **Problema de conexión resuelto.**
   - **Síntoma:** el primer intento de Stitch falló con `Incompatible auth server: does not support dynamic client registration`.
   - **Causa:** `STITCH_API_KEY` no estaba definida, así que la cabecera iba vacía y Claude Code intentaba un flujo OAuth que Stitch no admite.
   - **Solución:** el autor definió la variable con `setx` y reinició la app. La causa y la solución quedaron en la tabla de problemas de `mcp-stitch.md`.

## 4. Limitaciones

- **Pantalla de Stitch:** `generate_screen_from_text` superó el tiempo de espera del cliente. Durante unos 15 minutos de consultas, Stitch generó el design system pero la pantalla no apareció en el proyecto. El design se apoya solo en los tokens y en el texto enviado, no en una imagen de la pantalla.
- **Qué hace la skill:** revisa en forma estática; no corre tests ni contrasta la spec con el código. Los textos de interfaz marcados como «Propuesta» no tienen fuente en la KB contra la cual compararlos.
- **Ambigüedad de configuración sin resolver:** `config.yaml` pide «E#» en el título de los escenarios, pero desde C-04 se usa `US-NNN CA-N`. Queda para que el autor aclare la regla.
- **Costo y facturación de Stitch:** no se verificaron. Bastó la API key, pero no se revisó la facturación de la cuenta de Google.
- **Implementación:** C-11 queda preparado; su implementación y su archivado son de una instancia posterior.
