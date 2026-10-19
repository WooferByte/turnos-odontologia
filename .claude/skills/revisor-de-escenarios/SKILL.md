---
name: revisor-de-escenarios
description: Revisa los escenarios de un change OpenSpec de turnos-odontologia (specs/*/spec.md y tasks.md) contra la knowledge-base y CHANGES.md, y entrega un informe de hallazgos sin editar nada. Detecta criterios de aceptación sin escenario, falta de un caso feliz, uno de error de negocio o uno de borde, errores de negocio sin código RN o con un código que no existe, códigos HTTP que no siguen RN-GL-02 y RN-GL-04, reglas de dominio inventadas sin una D o una RN que las respalde, escenarios que no se pueden verificar y escenarios sin tarea que los pruebe. Usala siempre que se pida revisar, auditar o controlar la spec, los escenarios, los casos de borde o las tasks de un change; después de un /opsx:propose o un /opsx:update y antes de aprobar el plan o de arrancar el /opsx:apply; o cuando alguien pregunte si un change «está listo para implementar», aunque no nombre la skill.
---

# Revisor de escenarios

Esta skill revisa si los escenarios de un change de **turnos-odontologia** están completos, son verificables y respetan la base de conocimiento. Antes de implementar un change, la spec es el contrato. Los tests de Strict TDD salen de sus escenarios: un borde que falta en la spec es un test que nadie va a escribir, y una regla inventada termina siendo código que contradice la KB. Por eso conviene revisar antes de aprobar el plan y no después de escribir el código.

**La skill no edita los artefactos.** Su resultado es un informe. Las correcciones las hace el autor, o el agente de `/opsx:propose` o `/opsx:update`, con el informe a la vista. Así queda registrado el antes y el después de cada corrección.

## Entradas

- El nombre del change en kebab-case, por ejemplo `panel-de-prestaciones`. También sirve la ruta a su carpeta. Puede ser un change activo (`openspec/changes/<nombre>/`) o uno archivado.
- Si no se indica ninguno, usá el único change activo que muestre `openspec list --json`. Si hay más de uno, preguntá cuál.

## Procedimiento

### 1. Hacé el inventario con el script

Desde la raíz del repositorio:

```bash
PYTHONIOENCODING=utf-8 python .claude/skills/revisor-de-escenarios/scripts/inventario.py <change>
```

El script lista cada escenario con su tipo (lo saca del título: Feliz, Error de negocio, Error de formato, Borde), los CA y los códigos RN que cita, y si su CA aparece en `tasks.md`. También compara con los CA mínimos de `CHANGES.md` y con los códigos que existen en `knowledge-base/05_reglas_de_negocio.md`. Es la parte objetiva de la revisión: no cuentes a mano lo que el script ya contó. Lo que marca «FALTA» o «NO» es un punto de partida, no un veredicto: confirmalo leyendo el archivo.

### 2. Leé las fuentes, en este orden

1. La entrada del change en `CHANGES.md`: alcance (dentro y fuera), «Escenarios mínimos» y «Leer antes».
2. Las US del change en `knowledge-base/06_funcionalidades.md`, con sus criterios de aceptación. Los escenarios tienen que cubrir lo que dicen esos CA, no solo citar su número.
3. Las reglas `RN-` que cita el change, en `knowledge-base/05_reglas_de_negocio.md`. Leé siempre RN-GL-02 (orden y forma de los errores) y RN-GL-04 (referencias inválidas).
4. Las decisiones del autor en `knowledge-base/10_preguntas_abiertas.md` que cita el change, o que cubren su tema.
5. Las reglas `specs` y `tasks` de `openspec/config.yaml`. Mandan sobre esta skill si alguna vez se contradicen.
6. Los artefactos del change: `specs/*/spec.md`, `tasks.md` y, para las decisiones, `design.md`.

### 3. Aplicá los controles

Cada control tiene su razón. Entenderla te sirve para juzgar los casos dudosos.

| # | Control | Por qué importa |
|---|---|---|
| C1 | Cada CA de «Escenarios mínimos» tiene al menos un escenario, y ese escenario prueba lo que el CA dice (no solo lo nombra). | Es el contrato que el roadmap le pide al change. |
| C2 | La spec tiene al menos un escenario feliz, uno de error de negocio y uno de borde. | Es regla de `config.yaml` y de la consigna. Sin los tres, el diseño queda probado a medias. |
| C3 | Cada error de negocio lleva su código `RN-` en `codigos`, el código existe en 05 y la regla citada dice eso. | Regla dura 4: no hay error de negocio sin su código. Un código equivocado es igual de grave que uno ausente. |
| C4 | Los estados HTTP siguen RN-GL-02 y RN-GL-04: la validación de entrada va toda junta en un `422` con `codigos` vacío; una referencia inválida en el cuerpo da `422`; un recurso de la URL que no existe da `404`; las reglas de negocio se informan de a una. Lo de acceso (`401` y `403` con `RN-AU-05`) va antes que la validación (D208). | Si el estado está mal, el cliente reacciona mal. Es un error que se repite. |
| C5 | Cada escenario es verificable: tiene GIVEN/WHEN/THEN con valores concretos, horarios en UTC y un resultado observable (estado, cuerpo, pantalla o fila). No sirven «funciona bien» ni «muestra un error». | Si no se puede convertir en un test, no es un escenario. |
| C6 | Cada escenario tiene una tarea que lo verifica en `tasks.md` (un test RED con su nombre o su CA, o una prueba en el navegador o en `/docs`) y dice cómo se comprueba. | La consigna lo pide, y TDD estricto lo necesita para que el escenario no quede sin test. |
| C7 | Ninguna regla de dominio nueva aparece sin respaldo: cada número, límite, mensaje o comportamiento que no salga de la KB cita una `D` del autor o está marcado como «Propuesta» en `design.md`. | Regla dura 9 y consigna: la KB manda. Lo que el agente inventa tiene que verse como propuesta. |
| C8 | Nada se sale del alcance: no hay escenarios de lo que CHANGES.md pone en «fuera», ni cambios de API en un change de solo interfaz. Un escenario que **comprueba** un efecto observable en otra capability ya implementada (por ejemplo, que después de desactivar una prestación `POST /turnos` la rechace) no se sale del alcance: solo se sale si pide **implementar o cambiar** el comportamiento de esa otra capability. | Regla dura 12: un change, una capability. Habla de lo que se implementa, no de lo que se verifica. |
| C9 | Datos ficticios: no hay nombres, DNI ni teléfonos que parezcan reales. Los emails usan dominios de prueba (`.test`). | RN-PR-01 y regla dura 1. |
| C10 | Bordes que faltan. Buscá los que este dominio suele olvidar y que aplican al change: intervalo semiabierto `[inicio, fin)` (un turno que termina 10:00 no choca con uno que empieza 10:00); granularidad de 5 minutos (D99); mayúsculas, acentos y espacios en nombres (RN-AG-15); elementos inactivos; rol sin permiso (`403`) y sesión vencida (`401`); fechas en el límite del día del consultorio (RN-AG-10d); listas vacías; doble envío o concurrencia; en la interfaz, error de red y estado de carga. | La mitad de los defectos de este proyecto aparecieron en los bordes. Sugerí solo los que corresponden al alcance del change. |

### 4. Clasificá cada hallazgo

- **Bloqueante**: impide implementar sin riesgo. Por ejemplo: un CA mínimo sin escenario, la ausencia de alguno de los tres tipos, un error de negocio sin RN o con un RN inexistente, una regla que contradice la KB o un escenario sin verificación posible.
- **A corregir**: hay que arreglarlo antes del apply, aunque no traba el diseño. Por ejemplo: un estado HTTP mal clasificado, un escenario sin tarea, un valor sin respaldo no marcado como «Propuesta».
- **Sugerencia**: un borde que conviene agregar o una redacción que conviene aclarar.

Cada hallazgo cita **la fuente que lo justifica**: archivo y sección, código RN, decisión D o regla de `config.yaml`. Un hallazgo sin fuente es una opinión, y se dice así o no se reporta. Antes de reportar un borde como faltante, buscalo en la spec: puede estar cubierto dentro de otro escenario.

## Formato del informe

Respondé en español con esta estructura:

```markdown
# Revisión de escenarios: `<change>`

**Veredicto**: listo para implementar | listo con correcciones menores | no listo
**Base**: <n> escenarios (feliz <a>, error de negocio <b>, borde <c>, otros <d>); CA mínimos <cubiertos>/<total>; tareas cruzadas <x>/<n>.

## Hallazgos
| ID | Severidad | Control | Ubicación | Hallazgo | Fuente | Corrección propuesta |
|----|-----------|---------|-----------|----------|--------|----------------------|
| H1 | Bloqueante | C3 | specs/x/spec.md:42 | … | 05 RN-AG-15 | … |

## Cobertura
| CA | Escenarios | Tarea que lo verifica |
|----|------------|-----------------------|

## Bordes sugeridos
- <escenario propuesto en GIVEN/WHEN/THEN> — <por qué aplica> (<fuente>)

## Lo que no pude verificar
- <dudas, fuentes que faltan o reglas ambiguas en la KB>
```

Si no hay hallazgos de algún tipo, decilo. Un informe que dice «no encontré bloqueantes» también sirve. No completes la tabla con problemas inventados para que parezca exhaustivo. Si la propia KB es ambigua sobre algo, eso va en «Lo que no pude verificar», no como un hallazgo del change.

Si el usuario pide guardar el informe, guardalo en `openspec/changes/<change>/revision-de-escenarios.md` (es un archivo de trabajo, no un artefacto de OpenSpec) o donde indique.

## Límites

- No edites `spec.md`, `tasks.md`, `design.md` ni la KB. El informe propone y la corrección la decide el autor.
- No corras la suite ni levantes servidores: esta revisión es estática.
- No marques ninguna tarea ni cambies el estado del change en `CHANGES.md`.
