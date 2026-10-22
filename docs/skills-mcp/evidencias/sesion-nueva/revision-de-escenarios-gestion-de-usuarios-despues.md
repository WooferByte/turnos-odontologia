> Segunda revisión de la skill `revisor-de-escenarios` sobre el change activo `gestion-de-usuarios` (C-09), hecha el 2026-10-22 después del `/opsx:update` que registró D241 a D251 en `knowledge-base/10_preguntas_abiertas.md`, agregó `RN-AU-08` a `05` y corrigió los hallazgos del primer informe (`revision-de-escenarios-gestion-de-usuarios.md`, que queda como el «antes»). Revisión estática: no se editó ningún artefacto ni la KB y no se corrió la suite.

# Revisión de escenarios: `gestion-de-usuarios` (después)

**Veredicto**: listo con correcciones menores (un punto a corregir, N1; la tarea 1.2 de Stitch sigue siendo el bloqueante conocido del frontend).
**Base**: 54 escenarios (feliz 9, error de negocio 13, borde 32, otros 0; 32 en `gestion-de-usuarios` y 22 en `pantalla-de-usuarios`); CA mínimos 6/6 (US-093 CA-1, CA-2, CA-3, CA-4, CA-5, CA-8) más US-093 CA-9 (parte inicial, D242) y US-092 CA-1; tareas cruzadas 54/54 (leí los nombres de test de 2.1 a 11.2: cada escenario nuevo tiene su test).

Los doce hallazgos del primer informe (y el H13) quedaron resueltos. No hay bloqueantes propios de la spec o de las tasks. Hay un punto a corregir y cuatro sugerencias, todos nuevos. Tarea 1.2 (id de la pantalla de Stitch): bloqueante conocido de los grupos 9 a 13 por D234, no se repite.

## Estado de H1 a H13

| ID | Estado | Dónde quedó resuelto |
|----|--------|----------------------|
| H1 (CA-9 fuera de los mínimos de C-09) | Resuelto | Escenarios y tests con la etiqueta `US-093 CA-9` (`gestion` l.77 y l.83; `pantalla` l.60); Requirement de la contraseña inicial cita D242; design U5 y D242; `05` RN-AU-07 anota que la inicial la valida C-09. El ajuste de `CHANGES.md` (mínimos de C-09, entrada de C-10) queda para el archivo, declarado en design «Notas para el archive». |
| H2 (errores de negocio sin código) | Resuelto | `gestion` l.27-31, l.49-52, l.135-138 y l.200-203 escriben `403` con `codigos` `["RN-AU-05"]`. |
| H3 («todo junto» sin combinar errores) | Resuelto | `gestion` l.54-58: cuerpo con email `sin-arroba` y `roles` vacío a la vez, con dos errores; tarea 4.3. |
| H4 (botones deshabilitados sin escenario) | Resuelto | `pantalla` l.131-136 y test en 11.1. |
| H5 (mensajes de U19 sin test) | Resuelto | «Ingresá un email válido.» con el escenario de `pantalla` l.66 (email de 255 caracteres, tarea 10.3); «Revisá los datos del usuario.» con un test de función pura en `mensajes.test.ts` (10.3). Ver N1: lo que provoca el escenario no tiene prueba en la API. |
| H6 (`PATCH {}` y carrera de altas) | Resuelto | `gestion` l.151-155 (`{}`) y l.110-116 (dos altas, perfil `postgres`, tareas 5.3 y 6.4); la traducción a `409` está en el Requirement del email (l.91). |
| H7 (`RN-AU-08` inexistente) | Resuelto | `05` RN-AU-08 (l.354), D243 en `10` (l.456), US-093 CA-2 de `06`, fila «Usuarios» de `03`; el comando `inventario.py` ya no lo marca. Falta, para el archivo, sumarlo al «Leer antes» de C-09 y C-10 en `CHANGES.md` (declarado en las notas de archivo). |
| H8 (resultado ambiguo en la carrera) | Resuelto | `gestion` l.236-242: la perdedora recibe solo `409` `RN-AU-06`; design U12 dice que el `401` es otro escenario. |
| H9 (mitad de CA-4 no alcanzable por la API) | Resuelto | Requirement de `gestion` l.214 y design U10; tarea 2.1 la prueba en el dominio y 6.4 en `postgres`. |
| H10 (usuario inexistente solo en el falso) | Resuelto | `pantalla` l.140 lo declara «solo contra el servidor falso»; 13.1 lo excluye. |
| H11 (texto de `RN-AU-06` sin literal) | Resuelto | `pantalla` l.105 y l.128 citan el texto de U19. |
| H12 (sin sesión del dueño en la prueba del navegador) | Resuelto | Tarea 13.1 crea por la pantalla un usuario solo `dueno` y repite los `403` de escritura. |
| H13 (tamaño y dos capabilities) | Resuelto | D241 y D251; design U1 y U22. |

Los seis bordes sugeridos que el update dice haber incorporado están (401 antes que 422, `gestion` l.60; 422 antes que 404, l.146; roles y `activo` juntos, l.205; roles de un inactivo, l.157; contraseña vacía al reabrir, `pantalla` l.52; `403` al editar y reactivar, `pantalla` l.155). El séptimo (formato del email) quedó a medias: ver N1.

## Hallazgos nuevos
| ID | Severidad | Control | Ubicación | Hallazgo | Fuente | Corrección propuesta |
|----|-----------|---------|-----------|----------|--------|----------------------|
| N1 | A corregir | C6, C7 | `specs/gestion-de-usuarios/spec.md` l.54-58; `tasks.md` 4.3 y 8.1; `specs/pantalla-de-usuarios/spec.md` l.66 | El tope de 254 caracteres del email (design U4 y U6, marcado «Propuesta», no es parte de D245) no tiene escenario ni test en la API: el escenario de formato de `gestion` lista `sin-arroba`, `a@`, `@b` y `a b@c.test`, y la tarea 4.3 no prueba un email de 255. El escenario de la pantalla (l.66) lo da por hecho: solo lo ejerce el servidor falso, que la tarea 8.1 hace rechazar los 254+ por su cuenta. Si la API real no impone el tope, el falso y la prueba en el navegador (13.1) se apartan de ella sin que ninguna suite lo note. | design U4, U6, U19; `config.yaml` operations.apply (código de producción sin test que falle antes); bordes sugeridos n.º 7 del primer informe | Agregar al escenario de formato de `gestion` el email de 255 caracteres (y uno de 254 que se acepta) y su test en 4.3; o quitar el tope y el escenario de la pantalla que depende de él. |
| N2 | Sugerencia | C10 | `specs/gestion-de-usuarios/spec.md` Requirement «Asignar y quitar roles» y l.205-211 | Falta el caso de éxito de roles y `activo` en el mismo `PATCH` (design U8 punto 6): hoy solo se prueba el rechazo atómico. Ejemplo: con otro odontólogo activo, `PATCH` de la colega con `{"roles": ["dueno"], "activo": false}` responde `200`, aplica las dos partes y `token_version` pasa a 1. Sin él, una implementación que aplique solo una parte pasa todos los tests. | design U8.5 y U8.6 | Agregar un escenario Borde y su test en 6.3 (o 5.3); opcional: reactivar con roles nuevos en el mismo pedido. |
| N3 | Sugerencia | C7 | `specs/gestion-de-usuarios/spec.md` l.120 (Requirement de roles), l.157-162 y l.205-211 | Las dos Propuestas de U8 (puntos 6 y 7) están escritas como contrato de la spec y de las tasks (5.3, 6.3), pero siguen «Propuesta» en el design: el Apply no puede arrancar sin el ok al plan completo. Cuando el autor las apruebe tienen que pasar a D252 en adelante en `10` (design «Notas para el archive» ya lo prevé). Si las rechaza, caen los escenarios de l.157 y l.205. | design U8.6, U8.7 y «Migration Plan» 1; gobernanza CRÍTICO | Registrar la respuesta como D252 y D253 antes del Apply. |
| N4 | Sugerencia | C5 | `specs/gestion-de-usuarios/spec.md` l.205-211 | El escenario de roles y `activo` juntos usa `roles ["dueno"]` y `activo` falso sobre uno mismo: dos reglas de `RN-AU-06` fallarían a la vez, y el THEN no dice cuál de los dos textos fijos se espera (design U13: gana «nadie se desactiva a sí mismo»). Un test puede pasar con cualquiera. | design U11, U13 | Escribir en el THEN que gana la causa de desactivarse a sí mismo (detalle «Nadie puede desactivarse a sí mismo.»), o usar `roles ["dueno"]` sobre otro caso en que solo falle una. |
| N5 | Sugerencia | C10 | `specs/gestion-de-usuarios/spec.md` Requirement de la contraseña inicial (l.73-75) | «Formato antes que largo» (design U5): un cuerpo con una contraseña corta y un email inválido informa solo el error de formato. RN-GL-02 pide informar juntos todos los problemas de entrada; la desviación tiene respaldo (D242 y el precedente D177 de C-04) y el README la documentará como límite, pero ningún escenario la fija. | `05` RN-GL-02; D177; design U5 | Agregar un escenario Borde («email sin `@` y contraseña de 9 caracteres: `422` con `codigos` vacío y solo el error de `email`») para que el límite quede probado y no sea un accidente. |

## Las dos Propuestas de U8 contra la KB

- **U8 punto 6 (roles y `activo` en un `PATCH`, reglas evaluadas sobre el resultado combinado, todo o nada): no contradice la KB.** RN-AU-06 (`05`) prohíbe dejar al consultorio sin odontólogo activo y desactivarse a sí mismo; evaluar el estado resultante cumple ambas, y el todo o nada se apoya en que RN-GL-02 informa «de a una» y en que el rechazo no deja cambios (US-093 CA-4, CA-5). RN-AU-02 y D102 (los roles se leen de la base y no tocan `token_version`) y RN-AU-03 (`token_version` solo en `true → false`) no se alteran. La KB no dice nada de un `PATCH` combinado: es una elección del design, correcta, que conviene ratificar (N3) y completar con un caso de éxito (N2).
- **U8 punto 7 (se pueden editar los roles de un usuario inactivo; sigue inactivo; `token_version` sin cambios): no contradice la KB.** RN-AU-02 hace los roles independientes del token, RN-AU-04 solo impide iniciar sesión, y RN-AU-06 solo cuenta odontólogos activos, así que cambiar roles de un inactivo nunca baja ese conteo (coherente con el escenario `gestion` l.223). Ninguna fuente de `03`, `05`, `06` o `10` dice que un usuario inactivo sea de solo lectura. Coherente con D43 (desactivar sube `token_version`; nada más lo hace).

## Cobertura
| CA | Escenarios (spec, línea) | Tarea que lo verifica |
|----|--------------------------|-----------------------|
| US-093 CA-1 (crear con roles; la recepcionista no puede; listar; editar roles) | `gestion` l.15, 22, 27, 37, 44, 49, 54, 60, 122, 135, 140, 146, 151, 157; `pantalla` l.15, 22, 29, 36, 46, 66, 72, 79, 89, 96, 148, 155, 162 | 4.1, 4.3, 5.1, 5.3, 8.1, 8.3, 9.1, 9.3, 10.1, 10.3, 11.1, 11.2 |
| US-093 CA-2 (email único, `RN-AU-08`) | `gestion` l.93, 99, 105, 110; `pantalla` l.54 | 4.1, 4.3, 6.4, 8.1, 10.3 |
| US-093 CA-3 (desactivar corta el acceso; reactivar) | `gestion` l.168, 176, 183; `pantalla` l.112, 120, 131, 138 | 5.1, 5.3, 11.1, 11.2 |
| US-093 CA-4 (último odontólogo activo) | `gestion` l.216, 223, 229, 236; `pantalla` l.101 | 6.1, 6.3, 6.4, 11.1 |
| US-093 CA-5 (no desactivarse a sí mismo) | `gestion` l.193, 200, 205; `pantalla` l.125 | 6.1, 6.3, 11.1 |
| US-093 CA-8 (asignar `odontologo` no crea `Profesional`) | `gestion` l.66, 129 | 4.3, 5.3 |
| US-093 CA-9, parte inicial (D242) | `gestion` l.77, 83; `pantalla` l.60 | 2.1, 2.3, 4.1, 4.3, 8.1, 10.3 |
| US-092 CA-1 (sesión que termina en la pantalla) | `pantalla` l.171 | 10.3 |
| Prueba en el navegador | — | 13.1 (agente), 13.2 (autor), 14.2 (clon limpio) |

## Bordes sugeridos
- **Roles y `activo` en un `PATCH` que se acepta**: GIVEN la odontóloga y `colega@consultorio-demo.test` (odontólogo activo); WHEN `PATCH` de la colega con `{"roles": ["dueno"], "activo": false}`; THEN `200`, roles `["dueno"]`, `activo` falso y `token_version` 1. (design U8.5 y U8.6; N2)
- **Email de 255 y de 254 caracteres**: GIVEN la odontóloga; WHEN `POST /usuarios` con un email de 255 caracteres y otro de 254; THEN el primero recibe `422` con `codigos` vacío y error del campo `email`, el segundo `201`. (design U4, U6; N1)
- **Formato antes que largo**: WHEN `POST /usuarios` con el email `sin-arroba` y la contraseña `corta-123`; THEN `422` con `codigos` vacío y solo el error de `email`. (design U5; N5)

## Lo que no pude verificar
- **`CHANGES.md`, `CLAUDE.md`/`AGENTS.md` y `openspec/config.yaml`**: todavía no mencionan D241 a D251 ni `RN-AU-08` en el «Leer antes» de C-09 y C-10, ni los mínimos de C-09 con CA-9; el design lo deja para el archivo («Notas para el archive»), así que no lo cuento como defecto.
- **El patrón del email de V1** y que `with_for_update()` emita `FOR UPDATE` (V3): son verificaciones del Apply y no leí código del backend.
- **Ids del seed** (la odontóloga con `id` 1, la recepcionista con `id` 2) y el mapa de roles del servidor falso: salen de C-07 y C-08, sin releer `seed_demo.py` ni `servidorFalso.ts`.
- **`config.yaml` rules.specs[1]** (ID `E#` en el título) contra la convención `US-NNN CA-N <Tipo> - …`: ambigüedad de la configuración, no del change.
