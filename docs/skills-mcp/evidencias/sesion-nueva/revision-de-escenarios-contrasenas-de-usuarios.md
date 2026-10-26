# Revisión de escenarios: `contrasenas-de-usuarios` (C-10)

Fecha: 2026-10-26. Revisión estática (sin correr suites). Las preguntas Q1 a Q12 del design están abiertas; los hallazgos que dependen de una se marcan «condicional a Qn».

**Veredicto**: listo con correcciones menores (condicionado a que el autor responda Q1 a Q12 y a que Stitch entregue la pantalla antes del frontend). No hay bloqueantes propios del change; los dos puntos que tocan la KB dependen de Q3 y Q4.
**Base**: 36 escenarios (feliz 4, error de negocio 10, borde 22, otros 0); CA mínimos 3/3 (US-093 CA-6, CA-7, CA-9); escenarios con tarea que los verifica 36/36 (el script marca «sí» en todos).

## Hallazgos

| ID | Severidad | Control | Ubicación | Hallazgo | Fuente | Corrección propuesta |
|----|-----------|---------|-----------|----------|--------|----------------------|
| H1 | A corregir (condicional a Q3) | C3 | specs/contrasenas-de-usuarios/spec.md:91, 98, 146; pantalla:72; tasks 2.1, 5.1 | `RN-AU-09` no existe en `05` (el script lo marca). Es una propuesta del design, sin D ni RN que la respalde. Hoy la regla dura 4 exige código existente. | 05 (RN-AU-01..08); regla dura 4; precedente RN-AU-08 / D243 | Registrar la D (desde D290) y dar de alta `RN-AU-09` en `05` con el `/opsx:update` antes del Apply. Si Q3 elige (b) o (c), reescribir los 4 escenarios y el estado (`422` con `RN-AU-07` en `contrasena_actual`, o `401` `RN-AU-04`, que rompe el cliente: K7). |
| H2 | A corregir (condicional a Q4) | C7 | spec API:37-41; pantalla:27-31; tasks 4.3, 9.3 | La odontóloga no restablece la propia (`409` `RN-AU-07`) contradice la letra de RN-AU-07 («puede restablecer la de cualquier usuario») y de US-093 CA-6. Además se reutiliza `RN-AU-07` (largo, entrada) para una regla distinta (conflicto, negocio). Está marcada como Propuesta, pero sin D no tiene respaldo. | 05 RN-AU-07; 06 US-093 CA-6; RN-GL-02 | Con la respuesta a Q4, registrar la D y precisar RN-AU-07 en `05` (o darle un código propio, p. ej. el siguiente libre, para no mezclar entrada y negocio). Si Q4 elige (b), quitar los dos escenarios y la clase `RestablecerLaPropia`. |
| H3 | A corregir | C1/C6 | specs/pantalla-de-contrasenas:119-128; tasks 10.3 | El requisito «La sesión que termina... al restablecer o al cambiar» promete ambos casos, pero el único escenario es el de cambiar la propia. Falta el de restablecer con sesión irrenovable (y la tarea). | spec pantalla:121; US-092 CA-1; D231 | Agregar escenario «US-092 CA-1 Borde: una sesión irrenovable al restablecer» (GIVEN restableciendo con sesión sin renovación, WHEN Guardar, THEN vuelve a `/ingresar`, sin mensaje de conexión, nada cambió) y sumarlo a 9.3; o acotar el requisito a «cambiar la propia». |
| H4 | A corregir (condicional a Q1 y Q11) | C8 / regla `proposal` | design K1, K21; tasks.md encabezado | Dos capabilities nuevas y 29 tareas contra «una sola capability» y «alrededor de 20». Está declarado como excepción, pero sin D que la respalde hasta que el autor conteste. | config.yaml `rules.proposal`; D241, D251, D271, D287 | Registrar las D de Q1 y Q11 al hacer el `/opsx:update`; el plan no se aprueba con la excepción sin respaldo. |
| H5 | A corregir | C6 (tareas 12.2 y 12.3) | tasks 12.1-12.3; design K19 | La guía de C-09 no tiene respaldo en 12.1 (que solo prueba C-10): la verificación de 12.2 dice «en 12.1 o al escribirla», pero 12.1 no ejecuta los pasos de C-09 (alta, `RN-AU-07`/`RN-AU-08`, roles, desactivar, reactivar, los dos `RN-AU-06`). Además la demo solo trae la odontóloga y la recepcionista: la guía necesita pasos explícitos para crear el dueño y la colega por la pantalla. | tasks 12.2; config.yaml `rules.tasks` (el agente deja el paso a paso probado) | En 12.2, decir que el agente ejecuta él mismo cada paso de C-09 con la demo al escribir la guía y que la guía incluye la creación del dueño (y de un segundo `odontologo` si hace falta) antes de los pasos que los usan. |
| H6 | Sugerencia | C6 | tasks 12.2-12.3, 13.1 | 12.3 (el autor da el ok) va antes de 13.1/13.2; si la verificación final obliga a cambiar código, el ok queda viejo. Es coherente con «lo que no coincida se corrige antes de 13.1», pero no cubre cambios posteriores. | tasks 12.3, 13.1 | Agregar a 13.1: «si cambia código o la guía después del ok de 12.3, se vuelve a avisar al autor». |
| H7 | Sugerencia | C6 | tasks 12.2 | La guía va en `docs/guias/prueba-manual-c09-c10.md`; esa carpeta no existe hoy (solo `discovery`, `explore`, `skills-mcp`). | design K19 (ubicación marcada Propuesta) | Confirmar la ubicación con el autor al responder las Q (o dejarla en `docs/` sin subcarpeta nueva). |
| H8 | Sugerencia | C10 | spec API:146-156; tasks 6.1 | El escenario de concurrencia usa dos restablecimientos, pero el caso que motiva K10 es restablecer más cambiar la propia (el ladrón con la actual). Con un restablecimiento y un cambio propio simultáneos no hay escenario. | design K10 | Sumar un segundo escenario (o cambiar el del GIVEN) «restablecer y cambiar la propia a la vez»: `token_version` 2 y los tokens del cambio propio quedan inválidos o la actual se verifica contra el hash ya reemplazado; verificar en el perfil `postgres`. |
| H9 | Sugerencia | C10 | spec API:152-156 | «Formato antes que largo» solo se prueba al restablecer; en `cambiar-contrasena` (campo de más con `contrasena_nueva` corta) no hay escenario, aunque K9 lo declara igual en las dos rutas. | design K9; D242, D177 | Extender el escenario a las dos rutas y su tarea 5.3. |
| H10 | Sugerencia | C6 | tasks 4.2, 5.2; design V2 | V2 (bcrypt dentro o fuera de la transacción) está antes de 4.2 pero también afecta a `cambiar_contrasena` (5.2), que hashea y verifica con la fila bloqueada. | design K10, V2 | Indicar que V2 vale para 4.2 y 5.2. |
| H11 | Sugerencia | C5 | pantalla spec:53-58, 89-95 | Dos escenarios agrupan 3 comportamientos cada uno («sin conexión y un usuario que ya no existe»; «pulsar dos veces, sin conexión y salir»). Un solo THEN largo es más difícil de convertir en un test que falle por una causa. | config.yaml `rules.specs` | Aceptable si 9.3 y 10.3 los parten en un test por comportamiento (las tareas ya dicen «con su ID»); aclararlo en las tareas. |

## Cobertura

| CA | Escenarios | Tarea que lo verifica |
|----|------------|-----------------------|
| US-093 CA-6 (restablecer; incrementa `token_version`) | API: feliz, 403, inactivo, la propia, orden URL/entrada, sin sesión, cuerpo mal formado, concurrencia. Pantalla: feliz, la propia, 403, cancelar/cerrar/vacío, doble envío, sin conexión/404 | 2.1, 4.1, 4.3, 6.1, 8.1, 8.2, 9.1, 9.3 |
| US-093 CA-7 (cambiar la propia pidiendo la actual) | API: feliz, roles y usuario sin roles, actual incorrecta, actual de más de 72 bytes, nueva igual, sin sesión, cuerpo mal formado. Pantalla: feliz, actual incorrecta, repetición distinta, doble envío/sin conexión, todos los roles, token nuevo, recargar | 5.1, 5.3, 8.1, 10.1, 10.3 |
| US-093 CA-9 (10 caracteres a 72 bytes) | API: 9 caracteres en las dos rutas, bordes 10/72/73, largo antes que reglas, formato antes que largo. Pantalla: corta al restablecer y al cambiar | 2.1, 2.3, 4.1, 4.3, 5.1, 5.3, 9.1, 10.3 |
| US-092 CA-1 (cableado) | Pantalla: una sesión irrenovable al cambiar (falta el caso de restablecer, H3) | 10.3 |

Los controles C2 (feliz, error de negocio y borde presentes en las dos specs), C4 (401 antes que 422, 403 antes que 404, 422 antes que 404, formato antes que largo, RN-GL-02/04/D208) y C9 (todo ficticio, emails `.test`, contraseñas de ejemplo) pasan sin hallazgos. Los textos fijos (`detail`, avisos) son Propuesta del design (K7, K9, K14) y la spec lo declara en su párrafo de convenciones.

## Bordes sugeridos

- **Restablecer y cambiar la propia a la vez** (H8): GIVEN en PostgreSQL la recepcionista con `token_version` 0 y la odontóloga restableciendo su contraseña; WHEN la recepcionista pide `cambiar-contrasena` mientras el restablecimiento no confirmó; THEN el segundo espera, `token_version` queda en 2 y el access que emitió el cambio propio no sirve — corta el caso del ladrón que motiva K10 (design K10).
- **Formato antes que largo en el cambio propio** (H9): GIVEN la recepcionista con sesión; WHEN pide el cambio con `contrasena_nueva` `corta-123` y un campo `email` de más; THEN `422` con `codigos` vacío, solo el error del campo de más (D242, D177).
- **Sesión irrenovable al restablecer** (H3): ver hallazgo.

## Lo que no pude verificar

- Si Stitch entrega la pantalla y qué trae: no hay id; la spec de la pantalla es textual hasta la tarea 1.2 (D234, precedente D288).
- La corrida de la guía de prueba manual y de las verificaciones V1 a V5: dependen del Apply y de Docker.
- Si `docs/guias/` es la ubicación que prefiere el autor (H7).
- Si `RN-AU-07` debe seguir cubriendo el `409` de la propia o llevar código nuevo: la KB es ambigua («cualquier usuario» frente a «la propia pidiendo la actual») y lo decide el autor (Q4).

## Sobre las tareas 12.2 y 12.3 (pedido del autor)

Son coherentes con el design (K19, K20) y con `config.yaml` (`rules.tasks`: paso a paso del agente; repetición del autor porque el change es CRÍTICO): 12.1 prueba, 12.2 escribe la guía a partir de lo probado, 12.3 es del autor y bloquea el archive, y 13.1 corre después. Observaciones: H5 (los pasos de C-09 no tienen quién los ejecute antes de la guía, y la demo no trae dueño ni colega), H6 y H7. Ningún cambio de código de C-09 entra en C-10: la guía solo documenta.
