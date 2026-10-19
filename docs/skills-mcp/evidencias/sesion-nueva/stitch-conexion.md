# Evidencia: conexión con el MCP de Stitch

Fecha: 2026-10-19. Sesión nueva de Claude Code (app de escritorio), con el servidor `stitch` declarado en `.mcp.json` y la cabecera `X-Goog-Api-Key: ${STITCH_API_KEY}`.

## Primer intento: sin la variable de entorno

- `STITCH_API_KEY` no estaba definida ni en el proceso ni en el entorno del usuario.
- `list_projects` respondió: `Incompatible auth server: does not support dynamic client registration`.
- Lectura: con la cabecera vacía, Stitch rechaza la petición y Claude Code intenta un flujo OAuth que el servidor no admite. No es un problema de la key: es que no hay key. Este mensaje todavía no figura en la tabla de problemas de `docs/skills-mcp/mcp-stitch.md`.

## Segundo intento: con la variable definida

- El autor definió `STITCH_API_KEY` (con `setx`) y reinició la app. El agente confirmó que la variable está definida, sin mostrar su valor.
- `list_projects` respondió con éxito: **1 proyecto** propio y privado, «Activia Trace Academic Orchestrator» (`projects/17553208001504011139`, de escritorio, con 5 pantallas y un design system). Es un proyecto previo del autor y no está relacionado con turnos-odontologia.
- Conclusión: el MCP de Stitch ejecuta herramientas reales. El proyecto de diseño de C-11 (`panel-de-prestaciones`) todavía no existe; se crea en su `/opsx:propose`.
