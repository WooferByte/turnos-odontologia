# MCP de Google Stitch

Integración del agente (Claude Code) con **Stitch**, la herramienta de Google que genera diseños de pantallas a partir de texto. En este proyecto sirve para tener un diseño visual previo de las pantallas del panel, que no tiene diseños ni Figma. Es una **integración**, no una skill: no figura en `.atl/skill-registry.md`. Fuentes y fecha de consulta: [investigacion.md](investigacion.md).

## Requisitos

- Una cuenta de Google con acceso a Stitch.
- Claude Code (app de escritorio o terminal).
- Una API key de Stitch, guardada en la variable de entorno `STITCH_API_KEY`. La key **no se versiona**: no va en el repo, ni en `.mcp.json`, ni en capturas.

Para generar la key: en Stitch, foto de perfil, «Stitch settings», «API key», «Create key».

## Configuración en Windows

1. Definí la variable en tu usuario de Windows (PowerShell o CMD):

   ```powershell
   setx STITCH_API_KEY "<tu key>"
   ```

2. **Cerrá y volvé a abrir la app de Claude Code (y la terminal)**. `setx` no cambia la variable de los procesos que ya estaban abiertos: solo la ven los procesos nuevos. Este fue el problema de instalación que apareció (ver «Solución de problemas»).
3. Abrí Claude Code en la raíz del repo. El archivo `.mcp.json` versionado ya declara el servidor:

   ```json
   {
     "mcpServers": {
       "stitch": {
         "type": "http",
         "url": "https://stitch.googleapis.com/mcp",
         "headers": {
           "X-Goog-Api-Key": "${STITCH_API_KEY}"
         }
       }
     }
   }
   ```

   Claude Code reemplaza `${STITCH_API_KEY}` por el valor de la variable de entorno. Es la configuración de ejemplo: no tiene secretos y es la que está en el repo.
4. La primera vez, Claude Code pide **aprobar el servidor del proyecto** (viene de un `.mcp.json`). Aprobalo.

### Alternativa: configuración local, fuera del repo

Si preferís no usar la variable de entorno, registrá el servidor con alcance local (queda en tu configuración de usuario, no en el repo):

```bash
claude mcp add --transport http stitch https://stitch.googleapis.com/mcp --header "X-Goog-Api-Key: <tu key>"
```

En ese caso la key queda guardada en tu configuración local; no la copies a ningún archivo versionado.

## Comprobar la conexión

1. `claude mcp list` debe mostrar `stitch` como conectado.
2. Dentro de Claude Code, `/mcp` muestra el estado del servidor y sus herramientas.
3. Ejecutá una herramienta real, por ejemplo listar los proyectos de Stitch, y verificá que responde sin error.

> **Pendiente (se confirma al conectar)**: la lista exacta de herramientas del servidor y el resultado de la primera ejecución real. Según una guía de terceros serían: crear un proyecto, generar una pantalla desde un texto, y listar y obtener pantallas. No está confirmado con la documentación oficial.

## Qué datos ve y qué modifica

- Recibe los **textos que se le envían** (la descripción de la pantalla) y devuelve diseños. Los diseños se guardan en la cuenta de Google del autor, en Stitch.
- **No** tiene acceso al repositorio ni a la base de datos, y no modifica código del proyecto.

## Límites de uso

- Solo textos y datos **ficticios** del dominio. Nunca datos de pacientes (RN-PR-01) ni secretos.
- El diseño es una **referencia visual**: la KB y la spec mandan. Si el diseño contradice una regla, se sigue la KB.
- Se usa en el `/opsx:explore` o el `/opsx:propose` de changes con interfaz (previsto: C-11 `panel-de-prestaciones`), para fundamentar el `design.md`.
- La key vive fuera del repo, en `STITCH_API_KEY`.

## Uso en el proyecto

Desde el 2026-10-19, por decisión del autor (D234 en `knowledge-base/10_preguntas_abiertas.md`), **toda pantalla del frontend se implementa a partir de una pantalla generada en Stitch**, no solo a partir de los tokens del design system:

1. El `/opsx:explore` o el `/opsx:propose` del change genera la pantalla con el design system del proyecto («Clinical Ops») y guarda la evidencia (captura y HTML generado) en `docs/skills-mcp/evidencias/`.
2. El `design.md` cita el id de la pantalla (`projects/…/screens/…`) y esos archivos, y lista qué decisiones visuales toma de ella y cuáles rechaza (un texto o un dato que la KB no respalda se rechaza con su motivo).
3. El `/opsx:apply` traduce el HTML a los tokens CSS de `frontend/src/shared/estilos/`. No se copia tal cual: usa Tailwind, Google Fonts e íconos por CDN, que la CSP de nginx (`default-src 'self'`) bloquea y que serían dependencias nuevas.
4. La prueba en el navegador compara la implementación con la captura.

Si Stitch no entrega la pantalla (por ejemplo, por el tiempo de espera de la tabla de abajo), se reintenta: el change de interfaz no se cierra solo con los tokens. El primer caso fue C-11 (`panel-de-prestaciones`): ver [evidencias/sesion-nueva/stitch-c11.md](evidencias/sesion-nueva/stitch-c11.md), sección 3b.

## Solución de problemas

| Síntoma | Causa | Qué hacer |
|---|---|---|
| El servidor figura sin conexión o con la cabecera vacía aunque corriste `setx` | `setx` solo afecta a procesos nuevos; la app ya abierta no ve la variable | Cerrá del todo y reabrí la app y la terminal. Comprobá con `echo $env:STITCH_API_KEY` (PowerShell) |
| El servidor falla y la cabecera lleva el texto literal `${STITCH_API_KEY}` | La variable no está definida en el proceso que lanzó Claude Code | Definila con `setx` y reiniciá, o usá la alternativa local con `claude mcp add` |
| Al ejecutar una herramienta: `Incompatible auth server: does not support dynamic client registration` (visto el 2026-10-19) | `STITCH_API_KEY` no está definida: la cabecera va vacía, Stitch rechaza la petición y Claude Code intenta un flujo OAuth que Stitch no admite | Definí la variable con `setx STITCH_API_KEY "<tu key>"`, cerrá y reabrí la app, y repetí `list_projects` |
| `generate_screen_from_text` termina con `The operation timed out` | La generación tarda más que la espera del cliente; puede seguir en Stitch | No reintentes: consultá con `list_screens` o `get_screen` cada 30 segundos. El 2026-10-19 solo apareció el design system, no la pantalla |
| Error `401` o `403` al ejecutar una herramienta | Key inválida, vencida, revocada o sin permisos | Generá una key nueva en Stitch, actualizá la variable y reiniciá |
