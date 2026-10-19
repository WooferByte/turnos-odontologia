# Ficha de investigación: skills y MCP (Parte 1)

Agente: Claude Code (app de escritorio, Windows). Fuentes consultadas el 2026-10-19. Los pendientes de Stitch se confirmaron al conectar, el mismo día (marcados **Confirmado**).

## 1. Necesidad detectada

1. **Revisión de escenarios a mano.** Comprobar que cada CA tenga escenario, que cada error lleve su código RN y que cada escenario tenga cómo probarse exige releer la KB en cada change. Es repetitivo y fácil de olvidar → **skill propia**.
2. **Falta de diseño visual.** Desde C-08 los changes tienen pantalla, pero el proyecto no tiene diseños previos ni archivos de Figma → **MCP** que genere el diseño de una pantalla a partir de un texto.

## 2. Change elegido

**C-11 `panel-de-prestaciones`** (US-001, gobernanza BAJO): listado, alta, edición y desactivación de prestaciones contra la API de C-04, con selector de color, el error RN-AG-01 y edición solo para `odontologo`. Depende de C-04 y C-08, ya archivados. Escenarios mínimos: CA-1, CA-2 y CA-3. Es solo interfaz, así que un diseño previo aporta, y la skill revisa su spec antes del apply.

## 3. Skill creadora: `skill-creator`

- **Fuente**: Anthropic, repositorio `anthropics/skills`, carpeta `skills/skill-creator`; también listada en skills.sh.
- **Qué hace**: guía el armado de una skill (borrador, casos de prueba, evaluación con y sin la skill, visor y optimización de la descripción).
- **Compatibilidad**: usa el formato `SKILL.md` (estándar Agent Skills). skills.sh lista Claude Code entre los agentes compatibles.
- **Instalación**: `npx skills add https://github.com/anthropics/skills --skill skill-creator`, o el marketplace de plugins de Claude Code, o copiar la carpeta a `~/.claude/skills/`. En este equipo ya estaba en `~/.claude/skills/skill-creator/`.
- **Comprobar**: aparece en la lista de skills de Claude Code y su `SKILL.md` tiene `name: skill-creator`.
- **Pendiente**: el README del repositorio no nombra `skill-creator` dentro de `example-skills`.

## 4. Diseño de la skill propia: `revisor-de-escenarios`

- **Propósito**: revisar la spec y las tasks de un change contra la KB y devolver un informe de hallazgos. No edita nada.
- **Cuándo se activa**: al pedir revisar escenarios, spec o tasks, o después de `/opsx:propose` y antes de `/opsx:apply`.
- **Entradas**: el nombre del change, su `spec.md` y su `tasks.md`, la entrada en `CHANGES.md` y los archivos `05` y `06` de la KB.
- **Procedimiento**: leer los CA del change, listar los escenarios y comprobar:
  - que cada error cite su RN;
  - que haya al menos un escenario feliz, uno de error de negocio y uno de borde;
  - que cada CA tenga escenario;
  - que cada escenario tenga una tarea que lo verifique;
  - que no haya decisiones de dominio sin una D o una RN que las respalde.
- **Resultado**: hallazgos clasificados, cada uno con su ubicación y la regla que lo justifica.
- **Criterios de revisión**: contra C-04 archivado debe dar cero bloqueantes, y contra una copia con defectos plantados debe detectarlos todos.
- **Ubicación**: `.claude/skills/revisor-de-escenarios/`, versionada junto a las `openspec-*`. Claude Code la descubre por su `name` y su `description`.

## 5. Comparación de servidores MCP

| Criterio | Google Stitch | Figma MCP server |
|---|---|---|
| Propósito | Generar y editar pantallas de UI desde texto | Leer diseños de Figma y pasarlos a código |
| Herramientas | **Confirmado** (15): `list_projects`, `get_project`, `create_project`, `delete_project`, `list_screens`, `get_screen`, `generate_screen_from_text`, `edit_screens`, `generate_variants`, `list_design_systems`, `create_design_system`, `update_design_system`, `apply_design_system`, `upload_design_md`, `create_design_system_from_design_md` | `get_design_context`, `get_screenshot`, `get_metadata`, `get_variable_defs`, `use_figma`, entre otras |
| Conexión | HTTP remoto en `https://stitch.googleapis.com/mcp`, con la cabecera `X-Goog-Api-Key` (**Confirmado**) | `https://mcp.figma.com/mcp`, con autorización en el navegador |
| Credenciales y permisos | API key de Stitch; actúa sobre los proyectos de la cuenta | Cuenta Figma; escribir fuera de borradores requiere asiento Full |
| Costo | Sin costo según una guía de terceros, con cuotas sin cifra. **Pendiente**: el codelab de Google pide facturación de Google Cloud | 20 llamadas por mes en asientos View/Collab; más en planes pagos |
| Requisito previo | Ninguno: parte de un texto | Tener diseños en Figma |

**Elección: Stitch.** El proyecto no tiene archivos de Figma, así que Figma MCP no tendría qué leer. `context7` (ya conectado) sirve para documentación, no para diseñar. Riesgo asumido: Stitch es experimental y sus cuotas son inciertas.

## 6. Instalación y configuración (Stitch)

1. En Stitch: foto de perfil → Stitch settings → API key → Create key.
2. Definir `STITCH_API_KEY` en el entorno del usuario (`setx`, nunca en el repo) y reiniciar la app.
3. Versionar `.mcp.json` con un servidor `stitch` de tipo `http`, la URL anterior y `"X-Goog-Api-Key": "${STITCH_API_KEY}"`. Claude Code expande `${VAR}` también en las cabeceras. Después, aprobar el servidor de proyecto.
4. **Comprobar**: `claude mcp list` o `/mcp` muestra `stitch`; después, pedir «listá mis proyectos de Stitch» (`list_projects`).

Detalle y solución de problemas en [mcp-stitch.md](mcp-stitch.md).

## 7. Datos y límites

- **Qué puede hacer**: consultar y modificar solo proyectos de diseño de la cuenta del autor. No toca el código, la base de datos ni la API.
- **Qué recibe**: solo textos y datos ficticios del dominio; nunca datos de pacientes (RN-PR-01).
- **La key**: vive fuera del repo; si se filtra, se revoca en Stitch.
- **Peso del diseño**: es una referencia visual; la KB y la spec mandan.

## 8. Archivos de la fundación a actualizar

- **Skill**: `.claude/skills/revisor-de-escenarios/` (nueva) y `.atl/skill-registry.md`.
- **Instrucciones**: `CLAUDE.md` y `AGENTS.md` (idénticos) y `openspec/config.yaml`.
- **MCP**: `.mcp.json` (nuevo), y `README.md` con `docs/skills-mcp/mcp-stitch.md` enlazado.
- **Roadmap**: `CHANGES.md`, donde C-11 pasa a `[~]`.
- **Change**: los artefactos de `openspec/changes/panel-de-prestaciones/`.

## 9. Fuentes (consultadas el 2026-10-19)

- https://www.skills.sh/anthropics/skills/skill-creator
- https://github.com/anthropics/skills
- https://code.claude.com/docs/en/mcp
- https://codelabs.developers.google.com/design-to-code-with-antigravity-stitch
- https://aiidelist.com/blog/stitch-mcp-server-guide.md (de terceros, no oficial)
- https://stitch.withgoogle.com/docs/mcp/setup/ (oficial; no se pudo leer porque requiere JavaScript; la URL y la cabecera se confirmaron al conectar)
- https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/
- https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/
- https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/
