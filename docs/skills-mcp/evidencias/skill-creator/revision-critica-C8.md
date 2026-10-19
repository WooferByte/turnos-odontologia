# Revisión crítica: sugerencia inadecuada del control C8

## Qué pasó

En la evaluación con skill-creator (iteración 1), el informe de `eval-2` (copia de C-04 con defectos plantados, carpeta `eval-2-c04-con-defectos/with_skill/informe.md`, hallazgo H6) marcó como **A corregir** el escenario archivado «US-001 CA-1 Feliz - una prestación desactivada no admite turnos nuevos», con este argumento:

> El escenario incluye comportamiento de `POST /turnos` (`422` `RN-GL-04` inactivo y reactivación `201`), que pertenece a `creacion-de-turnos` (D175: E12 ya lo cubre). Mezcla dos capabilities en un escenario.

## Cómo se detectó

1. **Inconsistencia entre corridas**: el mismo escenario, sin cambios, está en el change original revisado en `eval-1`, y ahí la skill no lo marcó.
2. **Contraste con la fuente citada**: D175 (`knowledge-base/10_preguntas_abiertas.md`) dice que `gestion-de-prestaciones` va **sin deltas** sobre otras capabilities porque `creacion-de-turnos` (E12) ya cubre la prestación inactiva. No prohíbe comprobar ese efecto. El escenario no agrega ni cambia comportamiento de `POST /turnos`: verifica el efecto observable de desactivar, que es lo que pide US-001 CA-1.
3. **Regla dura 12** («un change, una capability») habla del alcance de lo que se **implementa**. El escenario no implementa nada fuera de C-04.

## Corrección

Se precisó el control C8 de `.claude/skills/revisor-de-escenarios/SKILL.md`.

**Antes**

> C8 | Nada se sale del alcance: no hay escenarios de lo que CHANGES.md pone en «fuera», ni cambios de API en un change de solo interfaz. | Regla dura 12: un change, una capability.

**Después**

> C8 | Nada se sale del alcance: no hay escenarios de lo que CHANGES.md pone en «fuera», ni cambios de API en un change de solo interfaz. Un escenario que **comprueba** un efecto observable en otra capability ya implementada (por ejemplo, que después de desactivar una prestación `POST /turnos` la rechace) no se sale del alcance: solo se sale si pide **implementar o cambiar** el comportamiento de esa otra capability. | Regla dura 12: un change, una capability. Habla de lo que se implementa, no de lo que se verifica.

Los otros hallazgos del mismo informe (los tres defectos plantados) eran correctos y no cambiaron.
