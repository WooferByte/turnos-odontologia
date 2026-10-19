# Ficha de investigación: skills y MCP (Parte 1)

Agente: Claude Code (app de escritorio, Windows). Fecha de consulta de todas las fuentes: 2026-10-19.

## 1. Necesidad detectada

Dos fricciones concretas del flujo OPSX del proyecto:

1. **Revisión de escenarios a mano.** Cada change lleva escenarios en `spec.md` y tasks en `tasks.md`; verificar que cada error lleve su código RN, que cada criterio de aceptación (CA) tenga escenario y que cada escenario tenga cómo probarse depende de releer la KB. Es repetitivo y se puede olvidar algo. Se resuelve con una **skill propia**.
2. **Falta de diseño visual.** Desde C-08 los changes incluyen pantalla, pero el proyecto no tiene diseños previos (ni Figma). Se resuelve con un **servidor MCP** que genere el diseño de la pantalla a partir de texto.

## 2. Change elegido

**C-11 `panel-de-prestaciones`** (US-001, gobernanza BAJO): listado, alta, edición y desactivación de prestaciones contra la API de C-04, selector de color, error de dominio RN-AG-01 y edición solo para `odontologo`. Depende de C-04 y C-08, ambos archivados. Escenarios mínimos: US-001 CA-1, CA-2, CA-3. Es un change de interfaz sin cambios de API ni de esquema, por eso un diseño previo aporta valor.

## 3. Skill creadora: `skill-creator`

| Ítem | Detalle |
|---|---|
| Fuente oficial | Anthropic, repo `anthropics/skills`, carpeta `skills/skill-creator`; listada en skills.sh |
| Qué hace | Guía el armado de una skill: borrador, casos de prueba, evaluación con y sin la skill, visor de resultados y optimización de la descripción para que se active bien |
| Compatibilidad | Formato `SKILL.md` (estándar Agent Skills, agentskills.io). skills.sh lista Claude Code entre los agentes, pero la página de la skill no declara compatibilidad por agente; en este equipo ya funciona con Claude Code |
| Instalación | (a) `npx skills add https://github.com/anthropics/skills --skill skill-creator` (comando que muestra skills.sh); (b) en Claude Code, `/plugin marketplace add anthropics/skills` y luego `/plugin install example-skills@anthropic-agent-skills`; (c) copiar la carpeta a `~/.claude/skills/`. **Pendiente:** el README del repo no nombra `skill-creator`, así que no se confirmó que venga dentro de `example-skills` |
| Estado en este equipo | Ya instalada en `~/.claude/skills/skill-creator/` (con `SKILL.md`, `scripts/`, `agents/`, `eval-viewer/`) |
| Comprobar | Figura en la lista de skills disponibles de Claude Code y su carpeta tiene `SKILL.md` con `name: skill-creator` |
| Uso | Pedir "usá skill-creator para crear una skill que revise escenarios"; se activa por su descripción |

## 4. Diseño de la skill propia: `revisor-de-escenarios`

| Ítem | Diseño |
|---|---|
| Propósito | Revisar la spec y las tasks de un change OpenSpec contra la KB y devolver un informe de hallazgos |
| Cuándo se activa | Al pedir revisar escenarios, spec o tasks de un change, o después de `/opsx:propose` y antes de `/opsx:apply` |
| Entradas | Nombre del change; `openspec/changes/<change>/specs/**/spec.md` y `tasks.md`; entrada del change en `CHANGES.md` (CA exigidos); `knowledge-base/05_reglas_de_negocio.md` y `06_funcionalidades.md` |
| Procedimiento | 1) leer los CA del change; 2) listar los escenarios de la spec; 3) comprobar que cada escenario de error cite su código RN; 4) comprobar que haya al menos uno de funcionamiento esperado, uno de error de negocio y uno de borde; 5) comprobar que cada CA tenga escenario; 6) comprobar que cada escenario tenga tarea de verificación en `tasks.md`; 7) detectar decisiones de dominio nuevas sin D/RN que las justifique |
| Resultado esperado | Informe con hallazgos clasificados (crítico, advertencia, sugerencia), cada uno con archivo, escenario y regla afectada; no modifica archivos |
| Criterios de revisión de la propia skill | Probada contra un change archivado (debe dar cero críticos) y contra una copia con defectos sembrados (debe detectarlos todos); descripción afinada con la optimización de `skill-creator` |
| Dónde se guarda | `.claude/skills/revisor-de-escenarios/SKILL.md` en el proyecto, versionada, junto a las skills `openspec-*`; Claude Code la descubre ahí por su `name` y `description` |

## 5. Comparación de servidores MCP

| Criterio | Google Stitch | Figma MCP server |
|---|---|---|
| Propósito | Generar y editar diseños de pantallas de UI desde texto (Google Labs) | Leer diseños de Figma y pasarlos a código; también escribe en archivos de Figma |
| Herramientas | Según una guía de terceros (no oficial): `list_projects`, `get_project`, `create_project`, `list_screens`, `get_screen`, `generate_screen_from_text`, `edit_screens`, `generate_variants`. **Pendiente:** confirmar con la lista real al conectar | Documentadas por Figma: `get_design_context`, `get_screenshot`, `get_metadata`, `get_variable_defs`, `search_design_system`, `use_figma`, `generate_figma_design`, `whoami`, entre otras |
| Compatibilidad con Claude Code | Transporte HTTP remoto; Google publica un codelab con Antigravity; la guía de terceros trae el comando para Claude Code | Documentada por Figma: `claude mcp add --transport http figma https://mcp.figma.com/mcp` o el plugin `figma@claude-plugins-official` |
| Conexión | `https://stitch.googleapis.com/mcp` con cabecera `X-Goog-Api-Key` (dato de guía de terceros) | `https://mcp.figma.com/mcp`, autenticación por navegador (Allow access) |
| Credenciales | API key creada en Stitch (foto de perfil, Stitch settings, API key, Create key; según el codelab de Google) | Cuenta Figma, sin clave manual |
| Permisos | La key actúa sobre los proyectos de la cuenta Google | Acceso a los archivos de la cuenta Figma; escribir fuera de borradores requiere asiento Full |
| Costo | Uso sin costo según la guía de terceros, con cuotas de generación por cuenta sin cifra publicada. **Pendiente:** el codelab de Google lista un proyecto de Google Cloud con facturación habilitada como requisito (es el flujo de Antigravity; no verificado para Claude Code) | Límites por plan: asientos View/Collab 20 llamadas por mes; Full/Dev en Professional 200 por día y 10 por minuto. La página no dice si el plan gratuito tiene acceso completo. Algunas herramientas gastan créditos de IA |
| Requisito previo | Ninguno de diseño: parte de texto | Tener diseños en Figma |

**Alternativa descartada:** `context7` ya está conectado, pero sirve para documentación de librerías, no para diseñar pantallas.

**Elección: Stitch.** El proyecto no tiene archivos de Figma, así que Figma MCP no tendría qué leer; Stitch genera la pantalla desde una descripción textual del C-11 y esa salida fundamenta el `design.md`. Riesgo asumido: la herramienta es experimental y las cuotas son inciertas.

## 6. Instalación y configuración (Stitch)

1. En Stitch, crear la API key (foto de perfil, Stitch settings, API key, Create key). Copiarla una sola vez.
2. Definir `STITCH_API_KEY` como variable de entorno del usuario de Windows (nunca en el repo) y reiniciar la app de Claude Code.
3. Crear `.mcp.json` versionado en la raíz:

```json
{
  "mcpServers": {
    "stitch": {
      "type": "http",
      "url": "https://stitch.googleapis.com/mcp",
      "headers": { "X-Goog-Api-Key": "${STITCH_API_KEY}" }
    }
  }
}
```

4. Aprobar el servidor de proyecto cuando Claude Code lo pida.
5. **Comprobar la conexión:** `claude mcp list` debe mostrar `stitch` como Connected; en sesión, `/mcp` muestra el servidor y su cantidad de herramientas. Si la variable no existe, el servidor carga con el texto literal `${STITCH_API_KEY}` y `claude mcp list` avisa.
6. **Ejecutar una herramienta:** pedir "listá mis proyectos de Stitch" (`list_projects`); después crear un proyecto y generar la pantalla de prestaciones con `generate_screen_from_text`.

Verificado en la documentación de Claude Code: `.mcp.json` con `"type": "http"`, expansión `${VAR}` y `${VAR:-default}` también en `headers`, y aprobación previa de servidores de proyecto. **Pendiente:** la URL y la cabecera de Stitch no pudieron leerse en su documentación oficial (carga solo con JavaScript); se confirman al conectar.

## 7. Datos y límites

- **Puede consultar y modificar:** proyectos y pantallas de diseño de la cuenta Google del autor (listar, crear, editar). No toca el código, la base ni la API del proyecto.
- **Datos que ve:** solo el texto que se le envía.
- **Límites:** solo textos y datos ficticios del dominio (nombres de prestaciones de ejemplo, duraciones, colores); nunca datos de pacientes (RN-PR-01); la API key vive fuera del repo; los diseños quedan en la cuenta del autor; si la key se filtra, se revoca y se regenera en Stitch.

## 8. Archivos de la fundación a actualizar

`.claude/skills/revisor-de-escenarios/SKILL.md` (nueva); `.atl/skill-registry.md`; `CLAUDE.md` y `AGENTS.md` (idénticos); `README.md` o `docs/skills-mcp/mcp-stitch.md` enlazado; `.mcp.json` (nuevo); `openspec/config.yaml` si corresponde; `CHANGES.md` (C-11 pasa a `[~]` al proponerse); artefactos de `openspec/changes/panel-de-prestaciones/`.

## 9. Fuentes (consultadas el 2026-10-19)

- https://www.skills.sh/anthropics/skills/skill-creator (comando de instalación, agentes listados)
- https://github.com/anthropics/skills (instalación por marketplace de plugins, formato de skill, licencia)
- https://code.claude.com/docs/en/mcp (`.mcp.json`, `${VAR}` en headers, `claude mcp list`, `/mcp`, aprobación)
- https://codelabs.developers.google.com/design-to-code-with-antigravity-stitch (Google: obtención de la API key, requisitos, verificación)
- https://aiidelist.com/blog/stitch-mcp-server-guide.md (tercero, no oficial: URL, cabecera, herramientas, comando para Claude Code)
- https://stitch.withgoogle.com/docs/mcp/setup/ (documentación oficial de Stitch: no se pudo leer, **pendiente**)
- https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/ (instalación en Claude Code)
- https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/ (herramientas)
- https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/ (límites y costos)
- https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server (servidor remoto y planes)
