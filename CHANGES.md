# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto **Turnos Odontológicos AR**.
> Cada change es atómico: una capability, de 3 a 6 escenarios y alrededor de 20 tareas (una sesión de trabajo).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Identificar el change a implementar: el primero en estado `[ ]` cuyas dependencias estén en `openspec/changes/archive/`, respetando el orden de las fases.
2. Leer los archivos de la knowledge-base indicados en «Leer antes» (y `openspec/config.yaml`, que vale para todos).
3. Ejecutar `/opsx:propose <nombre-del-change>` con el nombre exacto en kebab-case; el nombre es inmutable y el código `C-NN` es solo el índice de este archivo.
4. Al terminar el change, archivarlo con `/opsx:archive <nombre-del-change>`.
5. Marcar el estado `[x]` en este archivo y repetir la «Verificación cruzada» del final si se editó alguna entrada.

**Leyenda de estados:** `[ ]` pendiente · `[~]` en curso (propuesto o en implementación) · `[x]` archivado.

**Niveles de gobernanza:** CRITICO (autenticación, seguridad, pagos y seña, auditoría e historial): análisis y aprobación del autor antes de escribir código · ALTO (configuración que afecta datos, consentimiento, datos personales y de salud): proponer y esperar revisión · MEDIO (lógica de negocio): implementar con puntos de control · BAJO (catálogos, CRUD simples, solo lectura): autonomía si los tests pasan.

**Reglas que valen para todos los changes** (no se repiten en cada entrada):
- **Datos ficticios** en seeds, tests, ejemplos y demos (RN-PR-01): es una regla, no un change.
- **API primero:** las fases 1 y 2 se implementan y se prueban como API (tests de dominio y de API). La interfaz empieza en la fase 3 con el inicio de sesión; desde ahí la interfaz de cada historia va en su change, sin pantallas que ningún criterio pide.
- Intervalos `[inicio, fin)`; fechas aware en UTC con la medianoche del consultorio para RN-AG-10d; SQLAlchemy 2.x sincrónico; suite por defecto en SQLite en memoria, sin PostgreSQL ni Redis; sin mocks de sesión ni de repositorio; TDD estricto.
- Los vencimientos se evalúan al consultar y solo la tarea periódica dispara efectos (RN-GL-05). WhatsApp en la v1 es el enlace `wa.me`. Sin sobreturnos ni excepción de horario. El paciente no tiene cuenta: usa un token.
- El archivo único de dependencias y sus versiones exactas se fijan en el `design.md` de C-01; cada change siguiente agrega sus dependencias a ese mismo archivo, con versión exacta, en su design (D116). Este índice no nombra versiones.
- **IDs de escenario:** `E#` y `US-NNN: CA-n` son los de `knowledge-base/06_funcionalidades.md`. Un ID con otro prefijo (`INF`, `TP`, `HIS`, `HOR`, `REP`, `CAN`, `CFG`, `DIS`, `VEN`, `APR`, `PUB`, `LNK`, `RPL`, `MSG`, `CNF`, `LEP`, `WHK`) lo define este índice donde la KB no da uno; `CA-a+CA-b` cuenta como un solo escenario.

---

## Árbol de dependencias

El árbol se lee por bloques: cada bloque es una fase y coincide con un `Orden` de `06_funcionalidades.md`. Un bloque no empieza hasta que el anterior está archivado. Entre paréntesis, las dependencias que vienen de otra rama.

```
BLOQUE 1 (orden 1) — hito de la consigna
C-01 crear-turno-sin-solapamientos               ← etiqueta Git al archivarlo

BLOQUE 2 (orden 2) — solo API
C-02 infraestructura-postgresql                  (C-01)   ← desbloquea todas las migraciones
  ├── C-03 historial-de-turnos                   (C-01)
  ├── C-04 gestion-de-prestaciones
  └── C-05 gestion-de-sillones

BLOQUE 3 (orden 3) — acceso; empieza la interfaz
C-06 sesion-con-jwt                              (C-02)
  └── C-07 roles-y-proteccion-del-panel          (C-03, C-04, C-05)
        └── C-08 panel-base-e-inicio-de-sesion   (C-06)   ← desbloquea toda la interfaz
              ├── C-09 gestion-de-usuarios       (C-07)
              │     └── C-10 contrasenas-de-usuarios
              ├── C-11 panel-de-prestaciones     (C-04)
              ├── C-12 horario-recurrente        (C-07)
              └── C-13 bloqueos-puntuales        (C-07)

BLOQUE 4 (orden 4) — operación diaria del panel
C-14 agenda-del-dia                              (C-07, C-08)
  ├── C-15 panel-historial-de-turno              (C-03)
  ├── C-16 reprogramar-turno                     (C-03)
  ├── C-17 cancelar-turno                        (C-03)
  └── C-18 marcar-atendido-o-ausente             (C-03)
        └── C-19 corregir-marcado-de-asistencia
C-20 pacientes-desde-el-panel                    (C-07, C-08)
  └── C-21 auditoria-y-duplicados-de-pacientes

BLOQUE 5 (orden 5) — reserva y autogestión del paciente
C-22 reglas-configurables                        (C-07, C-08)
C-23 consentimiento-de-datos                     (C-20)
C-24 disponibilidad-de-turnos                    (C-04, C-12, C-13, C-22)
  └── C-25 reserva-online-por-link               (C-03, C-23)
        ├── C-26 reserva-dentro-de-la-ventana-de-cancelacion   (C-22)
        │     └── C-28 pagina-publica-de-reserva (C-08, C-25)
        ├── C-27 aprobacion-manual-de-pacientes-nuevos         (C-14, C-18)
        └── C-29 gestion-del-turno-por-link      (C-08, C-17, C-22)
              └── C-30 reprogramar-por-link      (C-16, C-24)

BLOQUE 6 (orden 6) — mensajes y lista de espera
C-31 tarea-periodica-con-redis                   (C-02)
  └── C-32 recordatorios-por-wa-me               (C-20, C-22, C-25)
        └── C-33 confirmar-turno-por-link        (C-14, C-29)
C-34 lista-de-espera-publica                     (C-23, C-25, C-28)
  └── C-35 lista-de-espera-desde-el-panel        (C-20)
        └── C-36 oferta-de-huecos-liberados      (C-17, C-32)
              └── C-37 respuesta-a-ofertas-de-hueco            (C-26)

BLOQUE 7 (orden 7) — seña
C-38 sena-con-mercado-pago                       (C-27, C-28, C-29)
  ├── C-39 webhook-de-pago-de-sena
  │     └── C-41 retencion-y-devolucion-de-sena  (C-17, C-18, C-29)
  │           └── C-42 accion-manual-sobre-la-sena             (C-19)
  └── C-40 vencimiento-de-sena                   (C-30, C-31, C-37)

BLOQUE 8 (orden 8) — ficha, presupuestos y pagos
C-43 ficha-clinica                               (C-14, C-20)
  ├── C-44 presupuesto-simple                    (C-04)
  └── C-45 registro-de-pagos
        └── C-46 correccion-y-anulacion-de-pagos

BLOQUE 9 (orden 9) — extensión fuera del MVP de la sección D del informe
C-47 reporte-de-ocupacion                        (C-12, C-13, C-18)
  └── C-48 reportes-de-ausentismo-y-cobros       (C-40, C-46)
```

### Paralelismo por fase

> Cada puerta (gate) es un punto de sincronización. Los changes de una misma puerta no dependen entre sí. Como las migraciones de Alembic son lineales y el autor trabaja solo, «en paralelo» significa **proponer** en paralelo y **aplicar de a uno**; la excepción son los changes sin migración (C-08, C-11, C-15, C-28), que pueden aplicarse mientras otro change de backend está en curso.

```
GATE 0: ninguna
  → C-01 crear-turno-sin-solapamientos               (solo)

GATE 1: C-01 archivado y etiquetado
  → C-02 infraestructura-postgresql                  (solo)

GATE 2: C-02 archivado                                ← PRIMER FORK (3 paralelos)
  → C-03 historial-de-turnos                         [Agente A]
  → C-04 gestion-de-prestaciones                     [Agente B]
  → C-05 gestion-de-sillones                         [Agente B]

GATE 3: C-03 + C-04 + C-05 archivados
  → C-06 sesion-con-jwt → C-07 roles-y-proteccion-del-panel → C-08 panel-base-e-inicio-de-sesion   (en serie)

GATE 4: C-08 archivado                                ← FORK (4 paralelos)
  → C-09 gestion-de-usuarios                         [Agente A]   (después C-10)
  → C-12 horario-recurrente                          [Agente A]
  → C-13 bloqueos-puntuales                          [Agente B]
  → C-11 panel-de-prestaciones                       [Agente C]

GATE 5: fase 3 archivada
  → C-14 agenda-del-dia                              [Agente A]
  → C-20 pacientes-desde-el-panel                    [Agente B]

GATE 6: C-14 archivado                                ← FORK (4 paralelos)
  → C-16 reprogramar-turno                           [Agente A]
  → C-17 cancelar-turno                              [Agente A]
  → C-18 marcar-atendido-o-ausente                   [Agente B]   (después C-19)
  → C-15 panel-historial-de-turno                    [Agente C]
  → C-21 auditoria-y-duplicados-de-pacientes         [Agente B — si C-20 archivado]

GATE 7: fase 4 archivada
  → C-22 reglas-configurables                        [Agente A]
  → C-23 consentimiento-de-datos                     [Agente B]
  → C-24 disponibilidad-de-turnos                    [Agente A — si C-22 archivado]

GATE 8: C-23 + C-24 archivados
  → C-25 reserva-online-por-link                     (solo)

GATE 9: C-25 archivado                                ← FORK (3 paralelos)
  → C-26 reserva-dentro-de-la-ventana-de-cancelacion [Agente A]
  → C-27 aprobacion-manual-de-pacientes-nuevos       [Agente B]
  → C-29 gestion-del-turno-por-link                  [Agente B]   (después C-30)
  → C-28 pagina-publica-de-reserva                   [Agente C — si C-26 archivado]

GATE 10: fase 5 archivada
  → C-31 tarea-periodica-con-redis                   [Agente A]   (después C-32 y C-33)
  → C-34 lista-de-espera-publica                     [Agente B]   (después C-35)

GATE 11: C-32 + C-35 archivados
  → C-36 oferta-de-huecos-liberados → C-37 respuesta-a-ofertas-de-hueco   (en serie)

GATE 12: fase 6 archivada
  → C-38 sena-con-mercado-pago                       (solo)
  → C-39 webhook-de-pago-de-sena                     [Agente A — si C-38 archivado]   (después C-41 y C-42)
  → C-40 vencimiento-de-sena                         [Agente B — si C-38 archivado]

GATE 13: fase 7 archivada
  → C-43 ficha-clinica                               (solo)
  → C-44 presupuesto-simple                          [Agente A — si C-43 archivado]
  → C-45 registro-de-pagos                           [Agente B — si C-43 archivado]   (después C-46)

GATE 14: fase 8 archivada
  → C-47 reporte-de-ocupacion → C-48 reportes-de-ausentismo-y-cobros      (en serie)
```

### Camino crítico (15 changes — mínimo irreducible)

Es la cadena de dependencias más larga hasta el último change del MVP. Un atraso en cualquiera de ellos atrasa el MVP completo. Los reportes (C-47, C-48) no forman parte: son la extensión fuera del MVP.

```
C-01 → C-02 → C-03 → C-07 → C-08 → C-20 → C-23 → C-25 → C-26 → C-28 → C-34 → C-35 → C-36 → C-37 → C-40
```

### Plan óptimo con 3 agentes

El autor trabaja solo. Los tres «agentes» son roles de una misma persona con agentes de IA, no tres equipos: **A** aplica el change en curso con TDD estricto (uno por vez), **B** deja propuesto el siguiente change de backend, **C** aplica la interfaz cuando no toca migraciones. Los changes de gobernanza CRITICO y ALTO se revisan antes de aplicar.

```
Paso │ Agente A (aplica backend)       │ Agente B (propone lo siguiente) │ Agente C (interfaz)
─────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────
  1  │ C-01                            │ C-02                            │ —
  2  │ C-02, C-03, C-04, C-05          │ C-06, C-07                      │ —
  3  │ C-06, C-07, C-09, C-10          │ C-12, C-13                      │ C-08, C-11
  4  │ C-12, C-13, C-14, C-16 a C-19   │ C-20, C-21                      │ C-15
  5  │ C-20 a C-27                     │ C-29, C-30                      │ C-28
  6  │ C-29 a C-37                     │ C-38, C-39, C-40                │ —
  7  │ C-38 a C-42                     │ C-43                            │ —
  8  │ C-43 a C-46                     │ C-47, C-48                      │ —
  9  │ C-47, C-48                      │ —                               │ —
```

### Mapeo historia → change

Cada historia tiene un change titular. Cuando una historia se partió, la tercera columna lista los demás changes que la implementan; la cuarta, los criterios que la KB marca como referencia hacia adelante y el change donde se completan. No se unieron historias de capabilities distintas, salvo las dos de sesión (US-090 con US-094) y las dos de acceso (US-091 con US-092).

| Historia | Change titular | Otros changes que la implementan | Criterios que se completan en otro change |
|---|---|---|---|
| US-001 | C-04 | C-11 | — |
| US-002 | C-12 | — | — |
| US-003 | C-13 | — | — |
| US-004 | C-05 | — | — |
| US-005 | C-22 | — | — |
| US-010 | C-01 | — | E9 en C-03; E10 en C-12 y C-13; E11 en C-02 |
| US-011 | C-14 | — | — |
| US-012 | C-16 | — | CA-3 en C-40 |
| US-013 | C-17 | — | CA-2 en C-36; CA-3 en C-41 |
| US-014 | C-18 | C-19 | CA-5 en C-41; CA-10 en C-42 |
| US-015 | C-03 | C-15 | — |
| US-016 | C-20 | C-21 | CA-7 en C-23 |
| US-020 | C-25 | C-24, C-26, C-27, C-28 | CA-10 en C-37; CA-3 en C-38 |
| US-021 | C-34 | C-35 | CA-4, CA-5 en C-37 |
| US-022 | C-29 | C-30 | CA-2 en C-40 |
| US-030 | C-32 | — | — |
| US-031 | C-33 | — | — |
| US-040 | C-36 | C-37 | — |
| US-050 | C-38 | C-39, C-40 | — |
| US-051 | C-41 | C-42 | — |
| US-060 | C-43 | — | — |
| US-061 | C-44 | — | — |
| US-062 | C-45 | C-46 | — |
| US-070 | C-23 | — | CA-1 en C-25; CA-5 en C-34 |
| US-080 | C-47 | C-48 | — |
| US-090 | C-06 | C-08 | — |
| US-091 | C-07 | — | CA-2 en C-43 |
| US-092 | C-07 | — | — |
| US-093 | C-09 | C-10 | — |
| US-094 | C-06 | — | — |

Changes técnicos (no son historias): C-02 `infraestructura-postgresql` y C-31 `tarea-periodica-con-redis`. Docker Compose no tiene change propio: cada servicio entra con el change que lo necesita (`api` y `postgres` en C-02, `frontend` en C-08, `redis` y `worker` en C-31).

### Tablas del modelo → change que las crea

| Tabla | Change que la crea | Columnas que agregan otros changes |
|---|---|---|
| `Consultorio` | C-01 | — |
| `Profesional` | C-01 | `usuario_id` y `matricula` en C-07 |
| `Sillon` | C-01 | — |
| `Prestacion` | C-01 | `color` y `reservable_online` en C-04 |
| `Paciente` | C-01 | `es_nuevo` en C-18; `dni`, `email`, `fecha_nacimiento`, `creado_en` y `acepta_contacto` en C-20 |
| `Turno` | C-01 | `creado_por` en C-07; `origen` y `token_gestion` en C-25; `actualizado_en` y `version` cuando su design los necesite (previsto en C-16) |
| `EventoTurno` | C-03 | — |
| `Usuario` | C-06 | — |
| `UsuarioRol` | C-07 | — |
| `FranjaHoraria` | C-12 | — |
| `Bloqueo` | C-13 | — |
| `EventoPaciente` | C-21 | — |
| `ConfiguracionReglas` | C-22 | — |
| `Consentimiento` | C-23 | — |
| `Mensaje` | C-32 | — |
| `EntradaListaEspera` | C-34 | — |
| `OfertaHueco` | C-36 | — |
| `Sena` | C-38 | — |
| `Anamnesis` | C-43 | — |
| `Evolucion` | C-43 | — |
| `Presupuesto` | C-44 | — |
| `ItemPresupuesto` | C-44 | — |
| `RegistroPago` | C-45 | `presupuesto_id` en C-44 si C-45 se archiva antes que C-44 |

### Resumen por fase

| Fase | Orden | Changes | Contenido |
|---|---|---|---|
| 1 | 1 | C-01 | Change de la consigna e hito de entrega |
| 2 | 2 | C-02 a C-05 | PostgreSQL, Alembic, historial, prestaciones y sillones (solo API) |
| 3 | 3 | C-06 a C-13 | Usuarios y acceso, primera interfaz, horario y bloqueos |
| 4 | 4 | C-14 a C-21 | Agenda, reprogramar, cancelar, marcar y pacientes |
| 5 | 5 | C-22 a C-30 | Reglas, consentimiento, reserva pública y link de gestión |
| 6 | 6 | C-31 a C-37 | Tarea periódica, recordatorios, confirmación y lista de espera |
| 7 | 7 | C-38 a C-42 | Seña con Mercado Pago |
| 8 | 8 | C-43 a C-46 | Ficha clínica, presupuestos y pagos |
| 9 | 9 | C-47 a C-48 | Reportes (extensión fuera del MVP de la sección D del informe) |

Primer change: `/opsx:propose crear-turno-sin-solapamientos`.

---

## FASE 1 — Change de la consigna (orden 1)

### [C-01] `crear-turno-sin-solapamientos`
- **Estado**: `[x]` archivado · **Orden**: 1 · **Gobernanza**: MEDIO
- **Objetivo** (US-010): crear un turno `reservado` para un paciente, una prestación, un profesional y un sillón, rechazando el solapamiento con turnos activos del profesional (RN-AG-05) y del sillón (RN-AG-08). Es el change de la consigna y el hito de entrega: al archivarlo se pone la etiqueta Git.
- **Alcance — dentro**: `Intervalo` semiabierto, `detectar_conflictos` y errores de dominio con código RN; caso de uso `crear_turno` con reloj inyectable y recursos por defecto (RN-AG-14); `POST /turnos` sin autenticación (DD-14) con cuerpo RFC 7807; tablas `Consultorio`, `Profesional`, `Sillon`, `Prestacion`, `Paciente` y `Turno` con `create_all` sobre SQLite en memoria; test unitario de `Intervalo` (E8, RN-AG-10d), test de ida y vuelta de zonas horarias, test de imports de `backend/app/domain` y test guard de fechas; archivo único de dependencias con versiones exactas (D116); README con el límite conocido.
- **Alcance — fuera**: historial `EventoTurno` (E9), horario y bloqueos (E10), concurrencia (E11), autenticación, interfaz gráfica, Alembic, PostgreSQL y Redis.
- **Depende de**: ninguna
- **Escenarios mínimos**: E1; E2; E3; E4; E5; E6; E7; E12 (8 escenarios: excepción registrada al «3 a 6», D123; sus tareas, agrupadas por tema, son la segunda excepción, al «alrededor de 20», D134)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-010 (tabla E1..E12 y nota del orden) · `knowledge-base/07_flujos_principales.md` Flujo 1
  - `knowledge-base/08_arquitectura_propuesta.md` §«Contrato del primer change», «Regla de capas», «Estrategia de tests», «Fixtures de test», «Reloj y zonas horarias», «Versiones y dependencias», «Definition of Done del primer change»
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-02, RN-AG-05, RN-AG-06, RN-AG-08, RN-AG-09, RN-AG-10, RN-AG-10d, RN-AG-14, RN-GL-01, RN-GL-02, RN-GL-04
  - `knowledge-base/04_modelo_de_datos.md` §«Subconjunto del primer change» · `knowledge-base/09_decisiones_y_supuestos.md` DD-02, DD-03, DD-12, DD-13, DD-14, SU-08

---

## FASE 2 — Base persistente y catálogos, solo API (orden 2)

> C-02 va primero. C-03, C-04 y C-05 no dependen entre sí. Ninguno tiene interfaz: se prueban con tests de dominio y de API.

### [C-02] `infraestructura-postgresql`
- **Estado**: `[x]` archivado · **Orden**: 2 · **Gobernanza**: ALTO
- **Objetivo** (change técnico, sin historia): dejar el esquema bajo migraciones y PostgreSQL como base de ejecución, con la restricción de exclusión que hace atómico el anti-solapamiento (RN-AG-10c; E11 de US-010).
- **Alcance — dentro**: Docker Compose con los servicios `api` y `postgres`; Alembic con una migración inicial equivalente al esquema de C-01; restricción de exclusión por profesional y por sillón sobre `[inicio, fin)` y solo estados activos (DD-04); marcador de pytest del perfil opcional con PostgreSQL y su comando en el README; nombres definitivos de las variables de entorno y `.env.example`; carga del seed ficticio; sus dependencias se agregan al archivo único de C-01 (D116).
- **Alcance — fuera**: cambios en la suite por defecto, que sigue en SQLite en memoria (DD-03); Redis y worker (C-31); frontend; tablas nuevas.
- **Depende de**: C-01
- **Escenarios mínimos**: E11; INF-1 (una base vacía migrada queda con el esquema de C-01); INF-2 (la restricción rechaza E2 y E3 en la base); INF-3 (la restricción acepta E5 y E6); INF-4 (la suite por defecto corre sin PostgreSQL). Se implementó con 28 tareas: tercera excepción registrada al «alrededor de 20» (D152)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` nota «Changes técnicos y frontend» y §US-010 (E11)
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-03, DD-04, DD-15 · `knowledge-base/10_preguntas_abiertas.md` D75, D85, D105, D116, D119, D133, D137 (y, ya implementado, D142 a D157)
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-09, RN-AG-10, RN-AG-10c · `knowledge-base/04_modelo_de_datos.md` §Turno (nota de DD-04) y «Seed data inicial»
  - `knowledge-base/08_arquitectura_propuesta.md` §«Estrategia de tests» (perfil opcional con PostgreSQL), «Variables de entorno», «Versiones y dependencias», «Estructura de directorios»

### [C-03] `historial-de-turnos`
- **Estado**: `[x]` archivado · **Orden**: 2 · **Gobernanza**: CRITICO
- **Objetivo** (US-015): registrar todo cambio de turno en un historial inmutable y exponerlo en solo lectura (RN-AG-11).
- **Alcance — dentro**: tabla `EventoTurno` (solo inserción) con su migración; `crear_turno` registra el evento `creado` en la misma transacción (E9 de US-010); `GET /turnos/{id}/historial`, sin autenticación hasta C-07; `404` para un id inexistente en la URL.
- **Alcance — fuera**: pantalla del historial (C-15); eventos de reprogramación, cancelación, marcado y seña (los agrega cada change); `EventoPaciente` (C-21).
- **Depende de**: C-01, C-02
- **Escenarios mínimos**: E9; US-015: CA-1; HIS-1 (un id de turno inexistente en la URL responde `404`, RN-GL-04). Se implementó con 24 tareas: cuarta excepción registrada al «alrededor de 20» (D161)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-015 y §US-010 (E9)
  - `knowledge-base/04_modelo_de_datos.md` §EventoTurno y «Regla de reparto entre `EventoTurno` y `EventoPaciente`»
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-11, RN-GL-04 · `knowledge-base/10_preguntas_abiertas.md` (ya implementado, D158 a D170)
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Historial · `knowledge-base/03_actores_y_roles.md` matriz, fila «Historial de cambios de turno»

### [C-04] `gestion-de-prestaciones`
- **Estado**: `[x]` archivado · **Orden**: 2 · **Gobernanza**: BAJO
- **Objetivo** (US-001): dar de alta, editar y desactivar prestaciones con nombre único, duración por defecto y color (parte de API).
- **Alcance — dentro**: `GET/POST /prestaciones` y `PATCH /prestaciones/{id}` (sin borrado); migración con `Prestacion.color` y `reservable_online`; duración mayor que 0 y múltiplo de la constante de 5 minutos (RN-AG-01, D99); cambiar la duración no toca turnos existentes; sin autenticación hasta C-07.
- **Alcance — fuera**: pantalla (C-11); granularidad configurable (C-22); efecto de `reservable_online` (C-24).
- **Depende de**: C-02
- **Escenarios mínimos**: US-001: CA-1, CA-2, CA-3
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-001 y nota de orden (D99)
  - `knowledge-base/04_modelo_de_datos.md` §Prestacion
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-01, RN-AG-02, RN-AG-15, RN-GL-03, RN-GL-04 · `knowledge-base/10_preguntas_abiertas.md` (ya implementado, D171 a D182)
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Prestaciones

### [C-05] `gestion-de-sillones`
- **Estado**: `[x]` archivado · **Orden**: 2 · **Gobernanza**: BAJO
- **Objetivo** (US-004): gestionar el sillón como recurso, con alta y desactivación; el sillón por defecto es el único activo (RN-AG-14), no un sillón fijo.
- **Alcance — dentro**: `GET/POST /sillones` y `PATCH /sillones/{id}` (desactivar); un sillón inactivo rechaza turnos nuevos con RN-GL-04 y motivo `inactivo` (RN-AG-07); el turno sin sillón explícito usa el único sillón activo y, con más de uno activo, la petición debe indicarlo o se rechaza con RN-GL-04 (RN-AG-14, D138); sin autenticación hasta C-07.
- **Alcance — fuera**: interfaz (US-004 no tiene; la agenda multi-sillón es Fase 2); cambios de esquema (la tabla `Sillon` ya existe).
- **Depende de**: C-02
- **Escenarios mínimos**: US-004: CA-1, CA-2, CA-3
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-004
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-06, RN-AG-07, RN-AG-14, RN-GL-04 · `knowledge-base/10_preguntas_abiertas.md` (ya implementado, D183 a D194)
  - `knowledge-base/04_modelo_de_datos.md` §Sillon · `knowledge-base/09_decisiones_y_supuestos.md` DD-08
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Sillones

---

## FASE 3 — Usuarios y acceso, primera interfaz y horario (orden 3)

> C-06, C-07 y C-08 van en serie. Después, C-09, C-11, C-12 y C-13 no dependen entre sí. Desde C-08 cada change incluye su pantalla.

### [C-06] `sesion-con-jwt`
- **Estado**: `[ ]` pendiente · **Orden**: 3 · **Gobernanza**: CRITICO
- **Objetivo** (US-090, US-094): iniciar y renovar la sesión del panel con JWT (parte de API).
- **Alcance — dentro**: tabla `Usuario` con `activo` y `token_version`; hash bcrypt; `POST /auth/login` y `POST /auth/refresh`; access token de 15 minutos y refresh de 7 días, HS256, con el claim `token_version`; `401` genérico; usuario ficticio del seed; variables `JWT_*`.
- **Alcance — fuera**: roles y protección de endpoints (C-07); pantalla de inicio de sesión (C-08); gestión de usuarios y contraseñas (C-09, C-10); tabla de tokens (no existe en la v1).
- **Depende de**: C-02
- **Escenarios mínimos**: US-090: CA-1+CA-4, CA-2, CA-3; US-094: CA-1, CA-2, CA-3
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §«Épica 10: Usuarios y acceso» (introducción, US-090, US-094)
  - `knowledge-base/05_reglas_de_negocio.md` RN-AU-01, RN-AU-03, RN-AU-04 · `knowledge-base/09_decisiones_y_supuestos.md` SU-09
  - `knowledge-base/04_modelo_de_datos.md` §«Usuario y UsuarioRol» · `knowledge-base/07_flujos_principales.md` Flujo 8
  - `knowledge-base/08_arquitectura_propuesta.md` §Seguridad y «Variables de entorno»

### [C-07] `roles-y-proteccion-del-panel`
- **Estado**: `[ ]` pendiente · **Orden**: 3 · **Gobernanza**: CRITICO
- **Objetivo** (US-091, US-092): que cada endpoint del panel exija un JWT válido y el rol que le corresponde.
- **Alcance — dentro**: tabla `UsuarioRol`; dependencias de FastAPI que validan firma, expiración, `activo` y `token_version` y leen los roles de la base en cada petición; protección de `POST /turnos`, `GET /turnos/{id}/historial`, prestaciones y sillones según la matriz; `Profesional.usuario_id` y `matricula`; `Turno.creado_por`; el historial registra al usuario como actor.
- **Alcance — fuera**: gestión de usuarios (C-09); acceso a la ficha clínica (US-091 CA-2, se completa en C-43); interfaz.
- **Depende de**: C-03, C-04, C-05, C-06
- **Escenarios mínimos**: US-091: CA-1, CA-3, CA-5; US-092: CA-1+CA-3, CA-2, CA-4
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §«RBAC — Matriz de permisos» y «Rutas públicas»
  - `knowledge-base/05_reglas_de_negocio.md` RN-AU-01, RN-AU-02, RN-AU-03, RN-AU-04, RN-AU-05
  - `knowledge-base/06_funcionalidades.md` §US-091, §US-092 · `knowledge-base/07_flujos_principales.md` Flujo 8
  - `knowledge-base/08_arquitectura_propuesta.md` §Seguridad · `knowledge-base/04_modelo_de_datos.md` §«Usuario y UsuarioRol», §Profesional

### [C-08] `panel-base-e-inicio-de-sesion`
- **Estado**: `[ ]` pendiente · **Orden**: 3 · **Gobernanza**: CRITICO
- **Objetivo** (US-090): construir la base de la interfaz del panel y la pantalla de inicio de sesión (parte de interfaz); es el primer change con frontend.
- **Alcance — dentro**: proyecto `frontend/` con React, TypeScript y Vite; pantalla de inicio de sesión contra `POST /auth/login`; renovación con `POST /auth/refresh` y vuelta al inicio de sesión ante un `401`; rutas del panel protegidas; servicio `frontend` en Docker Compose.
- **Alcance — fuera**: pantallas de negocio (cada una va en su change); páginas públicas (C-28); cambios de API.
- **Depende de**: C-06, C-07
- **Escenarios mínimos**: US-090: CA-1, CA-2, CA-3; US-092: CA-1
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` nota «Changes técnicos y frontend» (D106) y §US-090
  - `knowledge-base/08_arquitectura_propuesta.md` §«Estructura de directorios» (frontend), párrafo «Interfaz» y §Seguridad
  - `knowledge-base/02_descripcion_general.md` §«Arquitectura general» y «Stack tecnológico»
  - `knowledge-base/07_flujos_principales.md` Flujo 8 · `knowledge-base/05_reglas_de_negocio.md` RN-AU-03, RN-AU-04

### [C-09] `gestion-de-usuarios`
- **Estado**: `[ ]` pendiente · **Orden**: 3 · **Gobernanza**: CRITICO
- **Objetivo** (US-093): que el odontólogo cree usuarios, les asigne roles y los desactive (parte de gestión).
- **Alcance — dentro**: `GET/POST /usuarios` y `PATCH /usuarios/{id}` (roles, activar o desactivar); email único; contraseña inicial definida al crear; desactivar incrementa `token_version`; error de dominio RN-AU-06 para el último odontólogo activo y para desactivarse a sí mismo; pantalla de usuarios del panel.
- **Alcance — fuera**: restablecer y cambiar contraseñas (C-10); crear un `Profesional` al asignar el rol `odontologo` (Fase 2, D46).
- **Depende de**: C-07, C-08
- **Escenarios mínimos**: US-093: CA-1, CA-2, CA-3, CA-4, CA-5, CA-8
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-093
  - `knowledge-base/05_reglas_de_negocio.md` RN-AU-02, RN-AU-03, RN-AU-04, RN-AU-05, RN-AU-06, RN-AU-07
  - `knowledge-base/03_actores_y_roles.md` matriz, fila «Usuarios del consultorio» · `knowledge-base/04_modelo_de_datos.md` §«Usuario y UsuarioRol»
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Usuarios

### [C-10] `contrasenas-de-usuarios`
- **Estado**: `[ ]` pendiente · **Orden**: 3 · **Gobernanza**: CRITICO
- **Objetivo** (US-093): restablecer la contraseña de un usuario y que cada usuario cambie la propia (parte de contraseñas).
- **Alcance — dentro**: `POST /usuarios/{id}/restablecer-contrasena` (solo odontólogo) y `POST /auth/cambiar-contrasena` (pide la actual); ambos incrementan `token_version`; largo de 10 caracteres como mínimo y 72 bytes como máximo, también para la contraseña inicial de C-09; formularios en el panel.
- **Alcance — fuera**: recuperación de contraseña por email (ninguna historia la pide); revocación de tokens de a uno.
- **Depende de**: C-09
- **Escenarios mínimos**: US-093: CA-6, CA-7, CA-9
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-093 (CA-6, CA-7, CA-9)
  - `knowledge-base/05_reglas_de_negocio.md` RN-AU-03, RN-AU-07
  - `knowledge-base/08_arquitectura_propuesta.md` §Seguridad · `knowledge-base/09_decisiones_y_supuestos.md` SU-09
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», filas Auth y Usuarios

### [C-11] `panel-de-prestaciones`
- **Estado**: `[ ]` pendiente · **Orden**: 3 · **Gobernanza**: BAJO
- **Objetivo** (US-001): dar a la gestión de prestaciones su pantalla del panel (parte de interfaz; la API es de C-04).
- **Alcance — dentro**: listado, alta, edición y desactivación de prestaciones contra la API de C-04; selector de color; muestra el error de dominio RN-AG-01; solo el rol `odontologo` edita, los demás leen.
- **Alcance — fuera**: cambios de API o de esquema; pantalla de sillones (US-004 no tiene interfaz).
- **Depende de**: C-04, C-08
- **Escenarios mínimos**: US-001: CA-1, CA-2, CA-3
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-001 y nota «Changes técnicos y frontend»
  - `knowledge-base/03_actores_y_roles.md` matriz, fila Prestaciones
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Prestaciones
  - `knowledge-base/08_arquitectura_propuesta.md` §«Estructura de directorios» (frontend) · `knowledge-base/05_reglas_de_negocio.md` RN-AG-01

### [C-12] `horario-recurrente`
- **Estado**: `[ ]` pendiente · **Orden**: 3 · **Gobernanza**: MEDIO
- **Objetivo** (US-002): configurar los días y las franjas de atención y que un turno solo se cree dentro de una franja vigente (RN-AG-04).
- **Alcance — dentro**: tabla `FranjaHoraria`; `GET/PUT /profesionales/{id}/horario`; franjas del mismo día sin superposición; `crear_turno` rechaza con RN-AG-04 el turno que no cae completo en una franja, evaluado en la zona del consultorio (parte de horario de E10, US-010); horario de ejemplo en el seed; pantalla de horario.
- **Alcance — fuera**: bloqueos (C-13); excepción de horario puntual (Fase 2, D86); cálculo de disponibilidad (C-24).
- **Depende de**: C-07, C-08
- **Escenarios mínimos**: US-002: CA-1, CA-2; E10; HOR-1 (dos franjas superpuestas del mismo día se rechazan)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-002 y §US-010 (E10)
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-04, RN-GL-01
  - `knowledge-base/04_modelo_de_datos.md` §FranjaHoraria y «Seed data inicial» · `knowledge-base/07_flujos_principales.md` Flujo 1 (paso 5 y casos de error)
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Horario

### [C-13] `bloqueos-puntuales`
- **Estado**: `[ ]` pendiente · **Orden**: 3 · **Gobernanza**: MEDIO
- **Objetivo** (US-003): bloquear días u horas del profesional, del sillón o de todo el consultorio para que no se reserven turnos.
- **Alcance — dentro**: tabla `Bloqueo` con `creado_por`; `GET/POST/DELETE /bloqueos`; crear un bloqueo lista los turnos activos afectados sin cancelarlos; `crear_turno` rechaza con RN-AG-04b el turno que interseca un bloqueo (parte de bloqueos de E10, US-010); pantalla de bloqueos.
- **Alcance — fuera**: cancelar o reprogramar automáticamente los turnos afectados (D83); horario recurrente (C-12).
- **Depende de**: C-07, C-08
- **Escenarios mínimos**: US-003: CA-1, CA-2; E10
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-003 y §US-010 (E10)
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-04b · `knowledge-base/10_preguntas_abiertas.md` D83
  - `knowledge-base/04_modelo_de_datos.md` §Bloqueo
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Horario · `knowledge-base/03_actores_y_roles.md` matriz, fila «Horario recurrente y bloqueos»

---

## FASE 4 — Operación diaria del panel (orden 4)

> C-14 y C-20 pueden empezar a la vez. C-15 a C-18 dependen de C-14 y no entre sí.

### [C-14] `agenda-del-dia`
- **Estado**: `[ ]` pendiente · **Orden**: 4 · **Gobernanza**: BAJO
- **Objetivo** (US-011): ver los turnos del día y crear un turno desde la agenda.
- **Alcance — dentro**: `GET /turnos` filtrado por fecha y `GET /turnos/{id}`; pantalla de agenda ordenada por inicio, con paciente, prestación, estado y color; formulario que crea el turno con `POST /turnos` y muestra los errores de dominio de US-010.
- **Alcance — fuera**: las acciones sobre un turno, que cada change suma a esta agenda sin pantalla nueva: reprogramar, cancelar y marcar (C-16 a C-19), aprobar o rechazar (C-27, D112) y confirmar (C-33, D113); alta de pacientes (C-20); agenda multi-profesional y multi-sillón (Fase 2).
- **Depende de**: C-07, C-08
- **Escenarios mínimos**: US-011: CA-1, CA-2; E4 (el formulario muestra los dos códigos); E12 (el formulario muestra RN-GL-04)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-011 y nota «Changes técnicos y frontend» (D110)
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Turnos · `knowledge-base/03_actores_y_roles.md` matriz, fila Turnos
  - `knowledge-base/07_flujos_principales.md` Flujo 1 · `knowledge-base/08_arquitectura_propuesta.md` §«Contrato del primer change» (mapeo a HTTP)
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-01, RN-GL-02, RN-GL-04

### [C-15] `panel-historial-de-turno`
- **Estado**: `[ ]` pendiente · **Orden**: 4 · **Gobernanza**: BAJO
- **Objetivo** (US-015): ver desde el panel quién cambió qué y cuándo en un turno (parte de interfaz; la API es de C-03).
- **Alcance — dentro**: vista de solo lectura del historial de un turno, abierta desde la agenda, contra `GET /turnos/{id}/historial`; visible para odontólogo, recepcionista y dueño.
- **Alcance — fuera**: editar o borrar eventos (no existe); historial para el paciente (D68); auditoría de pacientes (C-21).
- **Depende de**: C-03, C-14
- **Escenarios mínimos**: US-015: CA-1; E9 (el evento `creado` aparece en la vista); HIS-2 (los eventos se muestran en orden cronológico con actor y fecha)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-015
  - `knowledge-base/03_actores_y_roles.md` matriz, fila «Historial de cambios de turno»
  - `knowledge-base/04_modelo_de_datos.md` §EventoTurno
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-11

### [C-16] `reprogramar-turno`
- **Estado**: `[ ]` pendiente · **Orden**: 4 · **Gobernanza**: MEDIO
- **Objetivo** (US-012): mover un turno a otro horario o cambiar su duración desde el panel sin perder el historial.
- **Alcance — dentro**: `PATCH /turnos/{id}`; el turno se valida como uno nuevo excluyéndose a sí mismo (RN-AG-10b), con horario y bloqueos; duración nueva mayor que 0 y múltiplo de la constante de 5 minutos, con `fin` recalculado; evento `reprogramado` con el antes y el después (DD-05); acción en la agenda.
- **Alcance — fuera**: conservar la seña (US-012 CA-3, se completa en C-40); reprogramación por el paciente (C-30); granularidad configurable (C-22).
- **Depende de**: C-03, C-14
- **Escenarios mínimos**: US-012: CA-1, CA-2, CA-4; REP-1 (reprogramar sobre otro turno activo se rechaza con RN-AG-05 y RN-AG-08 y el turno no cambia)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-012
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-01, RN-AG-02, RN-AG-10b, RN-AG-11, RN-TD-03, RN-TD-04
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-05 · `knowledge-base/04_modelo_de_datos.md` §Turno y «Máquina de estados del turno»
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Turnos

### [C-17] `cancelar-turno`
- **Estado**: `[ ]` pendiente · **Orden**: 4 · **Gobernanza**: MEDIO
- **Objetivo** (US-013): cancelar un turno desde el panel y liberar su horario.
- **Alcance — dentro**: `POST /turnos/{id}/cancelar` indicando quién lo pidió (`cancelado_profesional` o `cancelado_paciente`), en cualquier momento; transición según la tabla (RN-AG-12); evento `cancelado`; acción en la agenda.
- **Alcance — fuera**: ofrecer el hueco a la lista de espera (US-013 CA-2, el disparo llega en C-36); efecto sobre la seña (CA-3, en C-41); cancelación por el paciente (C-29).
- **Depende de**: C-03, C-14
- **Escenarios mínimos**: US-013: CA-1, CA-2; CAN-1 (cancelar un turno en estado terminal se rechaza con RN-AG-12 y no cambia)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-013
  - `knowledge-base/04_modelo_de_datos.md` §«Máquina de estados del turno» (tabla de transiciones)
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-10, RN-AG-11, RN-AG-12, RN-TD-03
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Turnos

### [C-18] `marcar-atendido-o-ausente`
- **Estado**: `[ ]` pendiente · **Orden**: 4 · **Gobernanza**: MEDIO
- **Objetivo** (US-014): registrar si el paciente asistió, para medir el ausentismo (parte de marcado).
- **Alcance — dentro**: `POST /turnos/{id}/estado`; solo desde `reservado` o `confirmado` (si no, RN-AG-12) y con `ahora >= inicio` (si no, RN-AG-13); evento en el historial; columna `Paciente.es_nuevo`, que pasa a `false` con el primer `atendido`; acción en la agenda para odontólogo y recepcionista.
- **Alcance — fuera**: corregir el marcado (C-19); retener la seña al quedar ausente (US-014 CA-5, en C-41).
- **Depende de**: C-03, C-14
- **Escenarios mínimos**: US-014: CA-1, CA-2, CA-3, CA-4, CA-6, CA-11
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-014
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-10, RN-AG-11, RN-AG-12, RN-AG-13, RN-TD-05
  - `knowledge-base/04_modelo_de_datos.md` §«Máquina de estados del turno» y §Paciente (`es_nuevo`) · `knowledge-base/09_decisiones_y_supuestos.md` DD-16
  - `knowledge-base/07_flujos_principales.md` Flujo 7 · `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Turnos

### [C-19] `corregir-marcado-de-asistencia`
- **Estado**: `[ ]` pendiente · **Orden**: 4 · **Gobernanza**: MEDIO
- **Objetivo** (US-014): corregir un marcado equivocado entre `atendido` y `ausente` (parte de corrección).
- **Alcance — dentro**: corrección por `POST /turnos/{id}/estado`; solo el rol `odontologo` (los demás reciben `403`); dentro de las 24 horas del marcado original, leído de `EventoTurno` (después, RN-AG-12); evento con el valor anterior y el nuevo; `es_nuevo` no se revierte; acción en el panel.
- **Alcance — fuera**: efecto sobre la seña (US-014 CA-10, en C-42); corrección pasadas las 24 horas (Fase 2).
- **Depende de**: C-18
- **Escenarios mínimos**: US-014: CA-7, CA-8, CA-9
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-014 (CA-7 a CA-10)
  - `knowledge-base/05_reglas_de_negocio.md` RN-AG-12, RN-AG-13, RN-AU-05, RN-SP-10
  - `knowledge-base/04_modelo_de_datos.md` §«Máquina de estados del turno» (filas de corrección)
  - `knowledge-base/03_actores_y_roles.md` matriz, fila «Corregir el marcado» · `knowledge-base/10_preguntas_abiertas.md` D34

### [C-20] `pacientes-desde-el-panel`
- **Estado**: `[ ]` pendiente · **Orden**: 4 · **Gobernanza**: ALTO
- **Objetivo** (US-016): dar de alta, buscar y editar los datos administrativos de un paciente desde el panel (parte de datos administrativos).
- **Alcance — dentro**: `GET/POST /pacientes` y `GET/PATCH /pacientes/{id}`; columnas `dni`, `email`, `fecha_nacimiento`, `creado_en` y `acepta_contacto` de `Paciente`; teléfono en E.164; `422` por datos faltantes o inválidos, `403` por rol (el dueño solo lee) y `404` por id inexistente; pantalla de pacientes.
- **Alcance — fuera**: aviso de duplicado, auditoría y cambio de `acepta_contacto` (C-21); consentimiento en persona (C-23); datos clínicos (C-43).
- **Depende de**: C-07, C-08
- **Escenarios mínimos**: US-016: CA-1, CA-2, CA-3, CA-5, CA-6, CA-8
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-016
  - `knowledge-base/04_modelo_de_datos.md` §Paciente
  - `knowledge-base/03_actores_y_roles.md` matriz, filas «Pacientes: datos administrativos» · `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila «Pacientes y ficha»
  - `knowledge-base/05_reglas_de_negocio.md` RN-PR-01, RN-FC-02, RN-AU-05, RN-GL-04

### [C-21] `auditoria-y-duplicados-de-pacientes`
- **Estado**: `[ ]` pendiente · **Orden**: 4 · **Gobernanza**: CRITICO
- **Objetivo** (US-016): avisar de un posible duplicado al dar de alta un paciente y auditar los cambios de su registro (parte de auditoría).
- **Alcance — dentro**: tabla `EventoPaciente`, solo inserción (Propuesta a revisar en el design); `POST /pacientes` responde las coincidencias con su motivo y solo crea con la confirmación explícita (RN-TD-12); eventos `creado`, `editado`, `contacto_cambiado` y `posible_duplicado`; cambio de `acepta_contacto` por `PATCH /pacientes/{id}`; aviso en el panel con «usar el existente» o «crear uno nuevo».
- **Alcance — fuera**: fusión de duplicados (Fase 2); efectos de `acepta_contacto` (C-32, C-36); eventos por la reserva pública o la lista de espera (no se registran, D111).
- **Depende de**: C-20
- **Escenarios mínimos**: US-016: CA-4, CA-9, CA-10, CA-11, CA-12
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-016 (CA-4, CA-9 a CA-12)
  - `knowledge-base/04_modelo_de_datos.md` §EventoPaciente y «Regla de reparto entre `EventoTurno` y `EventoPaciente`»
  - `knowledge-base/05_reglas_de_negocio.md` RN-TD-09, RN-TD-12, RN-PR-07
  - `knowledge-base/10_preguntas_abiertas.md` D108, D109, D111

---

## FASE 5 — Reglas, consentimiento, reserva pública y link de gestión (orden 5)

> C-22 y C-23 van primero y no dependen entre sí. C-25 necesita C-23 y C-24. Después, C-26, C-27 y C-29 no dependen entre sí.

### [C-22] `reglas-configurables`
- **Estado**: `[ ]` pendiente · **Orden**: 5 · **Gobernanza**: ALTO
- **Objetivo** (US-005): ajustar antelaciones, horizonte, aprobación de pacientes nuevos, seña y granularidad, partiendo de valores por defecto.
- **Alcance — dentro**: tabla `ConfiguracionReglas` (1:1 con el consultorio) con sus valores por defecto y sus `CHECK`; `GET/PUT /configuracion/reglas` (solo el odontólogo edita); la granularidad configurada reemplaza la constante de 5 minutos de C-04 y C-16; `monto_sena` obligatorio si `requiere_sena`; pantalla de configuración.
- **Alcance — fuera**: efecto de `requiere_sena` (C-38) y de la aprobación manual (C-27); congelar la ventana de cancelación por turno (Fase 2).
- **Depende de**: C-07, C-08
- **Escenarios mínimos**: US-005: CA-1, CA-2; CFG-1 (una duración que no es múltiplo de la granularidad configurada se rechaza con RN-AG-01); CFG-2 (`requiere_sena` sin monto se rechaza)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-005 y nota de orden (D99)
  - `knowledge-base/04_modelo_de_datos.md` §ConfiguracionReglas
  - `knowledge-base/05_reglas_de_negocio.md` RN-GL-03, RN-AG-01, RN-TD-01, RN-TD-02, RN-TD-03, RN-TD-05, RN-SP-01
  - `knowledge-base/09_decisiones_y_supuestos.md` DD-10 · `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Configuración

### [C-23] `consentimiento-de-datos`
- **Estado**: `[ ]` pendiente · **Orden**: 5 · **Gobernanza**: ALTO
- **Objetivo** (US-070): registrar la aceptación del texto de consentimiento con su versión, su fecha y su origen.
- **Alcance — dentro**: tabla `Consentimiento`; versión vigente `v1-borrador` como constante y texto con la leyenda «Borrador no validado legalmente»; regla de dominio que dice si un paciente debe aceptar (sin registro o con otra versión); `POST /pacientes/{id}/consentimientos` con origen `panel` (US-016 CA-7) y su acción en la pantalla de pacientes, sin bloquear los turnos del panel.
- **Alcance — fuera**: exigirlo en la reserva pública (US-070 CA-1, en C-25) y en la lista de espera (CA-5, en C-34); guardar la IP (D51); validación legal del texto (P-03).
- **Depende de**: C-20
- **Escenarios mínimos**: US-070: CA-2, CA-3, CA-4, CA-6; US-016: CA-7
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-070 y §US-016 (CA-7)
  - `knowledge-base/05_reglas_de_negocio.md` RN-PR-02, RN-PR-03 y §«Texto de consentimiento — versión `v1-borrador`»
  - `knowledge-base/04_modelo_de_datos.md` §Consentimiento · `knowledge-base/10_preguntas_abiertas.md` D30, D37, D57
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila «Pacientes y ficha»

### [C-24] `disponibilidad-de-turnos`
- **Estado**: `[ ]` pendiente · **Orden**: 5 · **Gobernanza**: MEDIO
- **Objetivo** (US-020): calcular los huecos reservables de una prestación (parte de disponibilidad).
- **Alcance — dentro**: `GET /disponibilidad`, `GET /public/{slug}/prestaciones` (solo las `reservable_online`) y `GET /public/{slug}/disponibilidad`; huecos = franjas menos bloqueos menos turnos activos, en pasos de la granularidad, entre `ahora` más la antelación mínima y el horizonte de reserva; es una lectura y nunca persiste (RN-GL-05).
- **Alcance — fuera**: reservar (C-25); página pública (C-28); estado efectivo de una seña vencida (C-40).
- **Depende de**: C-04, C-12, C-13, C-22
- **Escenarios mínimos**: US-020: CA-1; DIS-1 (sin horario configurado no hay huecos); DIS-2 (una prestación que no es `reservable_online` no se ofrece, RN-TD-06); DIS-3 (borde: el hueco que empieza justo en la antelación mínima se ofrece)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-020 (CA-1) · `knowledge-base/07_flujos_principales.md` Flujo 2 (pasos 1 y 2)
  - `knowledge-base/05_reglas_de_negocio.md` RN-TD-01, RN-TD-02, RN-TD-06, RN-AG-04, RN-AG-04b, RN-AG-09, RN-AG-10, RN-GL-05
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», filas Disponibilidad y Público
  - `knowledge-base/03_actores_y_roles.md` §«Rutas públicas»

### [C-25] `reserva-online-por-link`
- **Estado**: `[ ]` pendiente · **Orden**: 5 · **Gobernanza**: CRITICO
- **Objetivo** (US-020): que el paciente reserve sin cuenta y reciba el link de gestión de su turno (parte de reserva; es el change titular de la historia).
- **Alcance — dentro**: `POST /public/{slug}/reservas` sobre el caso de uso de C-01; exige el consentimiento (US-070 CA-1); reutiliza un paciente solo si coinciden teléfono, nombre y apellido normalizados, con respuesta idéntica y sin pisar datos; `Turno.origen` y `Turno.token_gestion` firmado, con la migración que genera el token de los turnos existentes; devuelve el link; límite de peticiones; E11 se verifica en el perfil con PostgreSQL.
- **Alcance — fuera**: aceptación de RN-TD-10 (C-26); aprobación manual (C-27); página (C-28); seña (C-38); mensaje `wa.me` (C-32).
- **Depende de**: C-03, C-23, C-24
- **Escenarios mínimos**: US-020: CA-2, CA-2b, CA-4, CA-5, CA-6, CA-11
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-020 · `knowledge-base/07_flujos_principales.md` Flujo 2
  - `knowledge-base/05_reglas_de_negocio.md` RN-TD-08, RN-TD-09, RN-PR-02, RN-PR-06, RN-AG-03, RN-AG-10c
  - `knowledge-base/04_modelo_de_datos.md` §Turno (`origen`, `token_gestion`) y §Paciente («Reutilización en la reserva pública») · `knowledge-base/09_decisiones_y_supuestos.md` DD-04, DD-11, SU-03
  - `knowledge-base/08_arquitectura_propuesta.md` §Seguridad (token de gestión, límite de peticiones) · `knowledge-base/03_actores_y_roles.md` §«Rutas públicas»

### [C-26] `reserva-dentro-de-la-ventana-de-cancelacion`
- **Estado**: `[ ]` pendiente · **Orden**: 5 · **Gobernanza**: MEDIO
- **Objetivo** (US-020): exigir la aceptación explícita cuando el turno reservado empieza a menos de la ventana de cancelación (parte de RN-TD-10).
- **Alcance — dentro**: en `POST /public/{slug}/reservas`, si `inicio − ahora` es menor que la ventana vigente, la petición sin el indicador de aceptación se rechaza con RN-TD-10 y no crea el turno; con el indicador, la aceptación queda en el evento `creado`; no aplica a los turnos del panel.
- **Alcance — fuera**: texto del aviso y botón (US-020 CA-8, en C-28); oferta de lista de espera (CA-10, en C-37); aviso de seña (C-38).
- **Depende de**: C-22, C-25
- **Escenarios mínimos**: US-020: CA-9; VEN-1 (borde: una reserva justo en el límite de la ventana no exige la aceptación); VEN-2 (un turno del panel dentro de la ventana se crea sin el indicador)
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md` RN-TD-02, RN-TD-03, RN-TD-10, RN-GL-03
  - `knowledge-base/06_funcionalidades.md` §US-020 (CA-8 a CA-10)
  - `knowledge-base/04_modelo_de_datos.md` §EventoTurno (`despues`) y §ConfiguracionReglas · `knowledge-base/07_flujos_principales.md` Flujo 2 (paso 5)
  - `knowledge-base/10_preguntas_abiertas.md` D33, D87

### [C-27] `aprobacion-manual-de-pacientes-nuevos`
- **Estado**: `[ ]` pendiente · **Orden**: 5 · **Gobernanza**: MEDIO
- **Objetivo** (US-020): que el odontólogo apruebe o rechace el turno de un paciente nuevo cuando la aprobación manual está activa (parte de aprobación).
- **Alcance — dentro**: con la regla activa, la reserva pública de un paciente con `es_nuevo` nace `pendiente_aprobacion` y ocupa el horario; `POST /turnos/{id}/aprobar` (pasa a `reservado`) y `POST /turnos/{id}/rechazar` (pasa a `cancelado_profesional`), solo el odontólogo; eventos en el historial; los turnos `pendiente_aprobacion` se ven en la agenda del día de C-14 con las acciones aprobar y rechazar, sin pantalla nueva (D112).
- **Alcance — fuera**: aprobar con seña exigida, que lleva a `pendiente_sena` (C-38); ofrecer el hueco rechazado a la lista de espera (C-36).
- **Depende de**: C-14, C-18, C-25
- **Escenarios mínimos**: US-020: CA-3, CA-12; APR-1 (el rechazo deja el turno `cancelado_profesional` y libera el horario); APR-2 (un paciente que ya no es nuevo reserva directo)
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md` RN-TD-05, RN-AG-12, RN-AU-05
  - `knowledge-base/04_modelo_de_datos.md` §«Máquina de estados del turno» y §Paciente (`es_nuevo`)
  - `knowledge-base/06_funcionalidades.md` §US-020 (CA-3, CA-12) · `knowledge-base/07_flujos_principales.md` Flujo 2 (paso 6)
  - `knowledge-base/03_actores_y_roles.md` matriz, fila «Aprobar o rechazar el turno de un paciente nuevo» · `knowledge-base/10_preguntas_abiertas.md` D52, D76, D112

### [C-28] `pagina-publica-de-reserva`
- **Estado**: `[ ]` pendiente · **Orden**: 5 · **Gobernanza**: ALTO
- **Objetivo** (US-020): dar al paciente la página pública para reservar desde el celular (parte de interfaz).
- **Alcance — dentro**: página de reserva por `slug`: elegir prestación y hueco, cargar los datos (teléfono obligatorio; DNI y email opcionales), leer y aceptar el texto de consentimiento, confirmar y ver el link de gestión; aviso y botón «Confirmar sin derecho a cancelación»; ante un `409` recarga los huecos.
- **Alcance — fuera**: anotarse en la lista de espera (C-34); pagar la seña (C-38); gestionar el turno (C-29); cambios de API.
- **Depende de**: C-08, C-25, C-26
- **Escenarios mínimos**: US-020: CA-1, CA-2, CA-8, CA-11; PUB-1 (si el hueco se ocupó entre la consulta y la reserva, la página avisa y recarga los huecos)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-020 y nota «Changes técnicos y frontend» · `knowledge-base/07_flujos_principales.md` Flujo 2
  - `knowledge-base/05_reglas_de_negocio.md` RN-TD-10, RN-PR-06 y §«Texto de consentimiento — versión `v1-borrador`»
  - `knowledge-base/02_descripcion_general.md` §«Arquitectura general» (rutas de la SPA) y §«API REST (resumen)», fila Público
  - `knowledge-base/03_actores_y_roles.md` §«Rutas públicas»

### [C-29] `gestion-del-turno-por-link`
- **Estado**: `[ ]` pendiente · **Orden**: 5 · **Gobernanza**: CRITICO
- **Objetivo** (US-022): que el paciente vea su turno y lo cancele desde el link de gestión (parte de ver y cancelar; es el change titular de la historia).
- **Alcance — dentro**: `GET /public/turnos/{token}` (datos mínimos y acciones permitidas) y `POST /public/turnos/{token}/cancelar`; validación del token firmado; acciones según el estado (RN-TD-08); fuera de plazo con el valor vigente, RN-TD-03; acción no permitida o turno empezado, RN-TD-11; token inválido sin revelar datos; página del turno.
- **Alcance — fuera**: reprogramar (C-30); confirmar (C-33); pagar la seña (C-38); devolver la seña al cancelar (C-41).
- **Depende de**: C-08, C-17, C-22, C-25
- **Escenarios mínimos**: US-022: CA-1, CA-3, CA-4, CA-5; LNK-1 (un token inválido se rechaza sin revelar datos del turno)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-022
  - `knowledge-base/05_reglas_de_negocio.md` RN-TD-03, RN-TD-08 (tabla de acciones por estado), RN-TD-11, RN-PR-06
  - `knowledge-base/07_flujos_principales.md` Flujo 5 y Flujo 3 (casos de error) · `knowledge-base/03_actores_y_roles.md` §«Rutas públicas»
  - `knowledge-base/08_arquitectura_propuesta.md` §Seguridad (token de gestión) · `knowledge-base/10_preguntas_abiertas.md` D77, D89

### [C-30] `reprogramar-por-link`
- **Estado**: `[ ]` pendiente · **Orden**: 5 · **Gobernanza**: MEDIO
- **Objetivo** (US-022): que el paciente reprograme su turno desde el link de gestión (parte de reprogramar).
- **Alcance — dentro**: `POST /public/turnos/{token}/reprogramar`; solo en `reservado` o `confirmado`, dentro de plazo y sin haber empezado; mismas reglas que una reserva nueva (horario, bloqueos, solapamiento excluyéndose, horizonte y antelación mínima); no cambia el estado; evento `reprogramado` con el paciente como actor; elección del nuevo hueco en la página del turno.
- **Alcance — fuera**: conservar la seña (US-022 CA-2, se completa en C-40); reprogramar el recordatorio (C-32).
- **Depende de**: C-16, C-24, C-29
- **Escenarios mínimos**: US-022: CA-2, CA-3; RPL-1 (fuera de plazo se rechaza con RN-TD-03 y el link indica contactar al consultorio); RPL-2 (el nuevo horario ocupado responde `409` y el turno no cambia)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-022 (CA-2, CA-3)
  - `knowledge-base/05_reglas_de_negocio.md` RN-TD-03, RN-TD-04, RN-TD-08, RN-TD-11, RN-AG-10b
  - `knowledge-base/07_flujos_principales.md` Flujo 5 (paso 4) · `knowledge-base/09_decisiones_y_supuestos.md` DD-05
  - `knowledge-base/03_actores_y_roles.md` §«Rutas públicas»

---

## FASE 6 — Tarea periódica, mensajes y lista de espera (orden 6)

> C-31 va antes de C-32. La rama de mensajes (C-31, C-32, C-33) y el comienzo de la lista de espera (C-34, C-35) no dependen entre sí; C-36 necesita las dos.

### [C-31] `tarea-periodica-con-redis`
- **Estado**: `[ ]` pendiente · **Orden**: 6 · **Gobernanza**: MEDIO
- **Objetivo** (change técnico, sin historia): tener el worker y Redis que ejecutan la tarea periódica, la única que dispara notificaciones y efectos en cadena (RN-GL-05).
- **Alcance — dentro**: servicios `redis` y `worker` en Docker Compose; `app/worker.py` y la función de la tarea, que se puede llamar sin Redis; variables `QUEUE_ENABLED` y `REDIS_URL`; mecanismo para detectar los vencimientos ya persistidos cuyos efectos no se dispararon (se fija en este design); corridas repetidas sin duplicar efectos.
- **Alcance — fuera**: recordatorios (C-32), ofertas (C-36) y vencimiento de señas (C-40), que agregan cada uno su paso a la tarea; Redis en los tests.
- **Depende de**: C-02
- **Escenarios mínimos**: TP-1 (la función de la tarea corre en un test sin Redis); TP-2 (la API levanta con la cola deshabilitada); TP-3 (dos corridas seguidas no repiten efectos)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` nota «Changes técnicos y frontend» (tarea periódica con Redis)
  - `knowledge-base/08_arquitectura_propuesta.md` §«Vencimientos y tarea periódica (Redis en la v1)», «Variables de entorno», «Estructura de directorios»
  - `knowledge-base/05_reglas_de_negocio.md` RN-GL-05 · `knowledge-base/09_decisiones_y_supuestos.md` DD-01, DD-06, DD-18
  - `knowledge-base/03_actores_y_roles.md` §«Actores del sistema» (Sistema) · `knowledge-base/10_preguntas_abiertas.md` D80, D92

### [C-32] `recordatorios-por-wa-me`
- **Estado**: `[ ]` pendiente · **Orden**: 6 · **Gobernanza**: MEDIO
- **Objetivo** (US-030): preparar el recordatorio y el mensaje con el link de gestión como enlaces `wa.me` que el odontólogo envía.
- **Alcance — dentro**: tabla `Mensaje`; puerto de mensajería con el adaptador `wa.me`; la tarea prepara el recordatorio al llegar `inicio − 24 h` y el mensaje `confirmacion` al crearse un turno; queda `descartado` si el paciente no acepta contacto o el turno dejó de estar activo; `GET /mensajes` y `POST /mensajes/{id}/enviado`; pantalla «Recordatorios de hoy»; reprogramar reprograma el recordatorio.
- **Alcance — fuera**: Cloud API y respuesta por chat (US-030 CA-2, Fase 2); tipo `aviso_cancelacion` (reservado); mensajes de oferta (C-36).
- **Depende de**: C-20, C-22, C-25, C-31
- **Escenarios mínimos**: US-030: CA-1, CA-3+CA-4, CA-5, CA-6; MSG-1 (el recordatorio de un turno cancelado antes de prepararlo queda `descartado`)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-030 · `knowledge-base/07_flujos_principales.md` Flujo 3
  - `knowledge-base/05_reglas_de_negocio.md` RN-WA-01, RN-WA-02, RN-WA-03, RN-PR-07, RN-TD-08, RN-GL-05
  - `knowledge-base/04_modelo_de_datos.md` §Mensaje · `knowledge-base/09_decisiones_y_supuestos.md` DD-06
  - `knowledge-base/11_integraciones_whatsapp_y_mercadopago.md` §WhatsApp · `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Mensajes

### [C-33] `confirmar-turno-por-link`
- **Estado**: `[ ]` pendiente · **Orden**: 6 · **Gobernanza**: MEDIO
- **Objetivo** (US-031): que el paciente confirme su turno desde el link de gestión, o el consultorio desde la agenda, y quede registrado. **Nota de alcance:** el nombre dice «por link» porque es inmutable, pero el change cubre las dos vías; desde el panel no se exige `ahora < inicio` (D117).
- **Alcance — dentro**: `POST /public/turnos/{token}/confirmar` (de `reservado` a `confirmado`, con evento `confirmado` y el paciente como actor); rechazo con RN-TD-11; botón de confirmar en la página del turno; `POST /turnos/{id}/confirmar` para el odontólogo y la recepcionista, con el usuario como actor y rechazo con RN-AG-12 desde otro estado; acción de confirmar en la agenda del día de C-14, sin pantalla nueva (D113).
- **Alcance — fuera**: confirmar o cancelar respondiendo por el chat (US-031 CA-2, Fase 2).
- **Depende de**: C-14, C-29, C-32
- **Escenarios mínimos**: US-031: CA-1, CA-3, CA-4, CA-5; CNF-1 (confirmar un turno ya empezado se rechaza con RN-TD-11); CNF-2 (en un estado terminal el link solo muestra el estado)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-031
  - `knowledge-base/05_reglas_de_negocio.md` RN-WA-02, RN-TD-08, RN-TD-11, RN-AG-11, RN-AG-12, RN-AU-05
  - `knowledge-base/04_modelo_de_datos.md` §«Máquina de estados del turno» · `knowledge-base/07_flujos_principales.md` Flujo 3 (paso 4)
  - `knowledge-base/03_actores_y_roles.md` matriz, fila «Confirmación de turno», y §«Rutas públicas» · `knowledge-base/10_preguntas_abiertas.md` D113

### [C-34] `lista-de-espera-publica`
- **Estado**: `[ ]` pendiente · **Orden**: 6 · **Gobernanza**: ALTO
- **Objetivo** (US-021): que el paciente se anote en la lista de espera cuando no hay horarios y pueda retirarse desde su link (parte pública; es el change titular de la historia).
- **Alcance — dentro**: tabla `EntradaListaEspera` con su token; `POST /public/{slug}/lista-espera` con consentimiento obligatorio (US-070 CA-5), prestación obligatoria, preferencias y reutilización del paciente; una sola entrada en curso por paciente y prestación; `POST /public/lista-espera/{token}/retirar`; la página de reserva ofrece anotarse cuando no hay huecos.
- **Alcance — fuera**: alta y retiro desde el panel (C-35); ofertas (C-36); retiro de una entrada `ofertada` (C-37).
- **Depende de**: C-23, C-25, C-28
- **Escenarios mínimos**: US-021: CA-1, CA-2, CA-3, CA-4, CA-6, CA-7
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-021 · `knowledge-base/07_flujos_principales.md` Flujo 6 (paso 6)
  - `knowledge-base/05_reglas_de_negocio.md` RN-TD-07, RN-TD-09, RN-LE-01, RN-LE-02, RN-LE-05, RN-LE-06, RN-LE-07, RN-PR-06
  - `knowledge-base/04_modelo_de_datos.md` §EntradaListaEspera
  - `knowledge-base/03_actores_y_roles.md` §«Rutas públicas» · `knowledge-base/10_preguntas_abiertas.md` D29, D78

### [C-35] `lista-de-espera-desde-el-panel`
- **Estado**: `[ ]` pendiente · **Orden**: 6 · **Gobernanza**: MEDIO
- **Objetivo** (US-021): que el consultorio anote y retire pacientes de la lista de espera desde el panel (parte de panel).
- **Alcance — dentro**: `GET/POST /lista-espera` y `POST /lista-espera/{id}/retirar`; el alta no exige el consentimiento (se registra con origen `panel` cuando el paciente lo da); mismas reglas de prestación obligatoria y entrada única; pantalla de lista de espera.
- **Alcance — fuera**: ofertar a mano (no existe en la v1, D96); indicador de 7 días sin oferta (C-36); retiro de una entrada `ofertada` (C-37).
- **Depende de**: C-20, C-34
- **Escenarios mínimos**: US-021: CA-5, CA-8; LEP-1 (un segundo alta del mismo paciente y prestación devuelve la entrada existente); LEP-2 (el dueño recibe `403` al anotar)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-021 (CA-5, CA-8)
  - `knowledge-base/05_reglas_de_negocio.md` RN-LE-05, RN-LE-06, RN-LE-07, RN-PR-02
  - `knowledge-base/03_actores_y_roles.md` matriz, fila «Lista de espera» · `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila «Lista de espera»
  - `knowledge-base/10_preguntas_abiertas.md` D96, D103, D107

### [C-36] `oferta-de-huecos-liberados`
- **Estado**: `[ ]` pendiente · **Orden**: 6 · **Gobernanza**: MEDIO
- **Objetivo** (US-040): que la tarea periódica ofrezca cada hueco liberado a la primera entrada compatible (parte de oferta; es el change titular de la historia).
- **Alcance — dentro**: tabla `OfertaHueco` con su token; cálculo del hueco y de la compatibilidad por tramo común; orden de llegada; primer inicio posible según la granularidad; el resto del hueco pasa a la siguiente entrada en la misma corrida; salta a quien no acepta contacto; mensaje `oferta_hueco` listo en el panel; indicador de 7 días sin oferta; disparo por cancelación (US-013 CA-2), por rechazo de una aprobación y por reprogramación.
- **Alcance — fuera**: aceptar, rechazar y vencer la oferta (C-37); disparo por vencimiento de seña (C-40).
- **Depende de**: C-17, C-32, C-35
- **Escenarios mínimos**: US-040: CA-1+CA-1b, CA-1c, CA-1d, CA-1e, CA-4, CA-5
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-040 · `knowledge-base/07_flujos_principales.md` Flujo 6 (pasos 1 a 3 y 7)
  - `knowledge-base/05_reglas_de_negocio.md` RN-LE-01, RN-LE-02, RN-LE-08, RN-TD-02, RN-PR-07, RN-GL-05
  - `knowledge-base/04_modelo_de_datos.md` §OfertaHueco y §EntradaListaEspera
  - `knowledge-base/10_preguntas_abiertas.md` D88, D97

### [C-37] `respuesta-a-ofertas-de-hueco`
- **Estado**: `[ ]` pendiente · **Orden**: 6 · **Gobernanza**: MEDIO
- **Objetivo** (US-040): que el paciente acepte o rechace una oferta y que una oferta sin respuesta venza (parte de respuesta).
- **Alcance — dentro**: `POST /public/ofertas/{token}/aceptar` y `POST /public/ofertas/{token}/rechazar`; aceptar revalida el solapamiento y crea el turno con origen `lista_espera`; aceptación explícita de RN-TD-10 dentro de la ventana (US-020 CA-10); la oferta vencida se persiste y se rechaza; rechazo o vencimiento devuelven la entrada a `activa` sin perder su lugar; retiro de una entrada `ofertada` desde el link o desde el panel (US-021 CA-4 y CA-5); página de la oferta.
- **Alcance — fuera**: persistir el vencimiento de una seña al aceptar (RN-GL-05, caso (a), en C-40).
- **Depende de**: C-26, C-36
- **Escenarios mínimos**: US-040: CA-2, CA-2b, CA-3; US-020: CA-10
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-040 (CA-2 a CA-3) y §US-020 (CA-10)
  - `knowledge-base/05_reglas_de_negocio.md` RN-LE-03, RN-LE-04, RN-LE-06, RN-TD-10, RN-GL-05
  - `knowledge-base/04_modelo_de_datos.md` §OfertaHueco · `knowledge-base/07_flujos_principales.md` Flujo 6 (pasos 4 y 5)
  - `knowledge-base/03_actores_y_roles.md` §«Rutas públicas» · `knowledge-base/10_preguntas_abiertas.md` D53, D60

---

## FASE 7 — Seña con Mercado Pago (orden 7)

> Toda la fase es de gobernanza CRITICO y usa solo credenciales de prueba: las reglas de seña están sujetas a revisión legal. C-39 y C-40 no dependen entre sí.

### [C-38] `sena-con-mercado-pago`
- **Estado**: `[ ]` pendiente · **Orden**: 7 · **Gobernanza**: CRITICO
- **Objetivo** (US-050): exigir la seña al reservar y generar su cobro con Checkout Pro (parte de cobro; es el change titular de la historia).
- **Alcance — dentro**: tabla `Sena` con su tabla de transiciones (RN-SP-12); puerto de pagos con el adaptador de Mercado Pago, sin credenciales en los tests; con `requiere_sena`, la reserva nace `pendiente_sena` y crea la preferencia; con aprobación manual, la seña se crea al aprobar (US-020 CA-3); `POST /public/turnos/{token}/pagar-sena`; aviso de que la seña no se devuelve dentro de la ventana; pago desde la página del turno.
- **Alcance — fuera**: webhook y acreditación (C-39); vencimiento (C-40); retención y devolución (C-41); split de pagos (Fase 2); dinero real.
- **Depende de**: C-27, C-28, C-29
- **Escenarios mínimos**: US-050: CA-1, CA-6, CA-8, CA-9, CA-10
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-050 · `knowledge-base/07_flujos_principales.md` Flujo 4 (pasos 1 a 3)
  - `knowledge-base/05_reglas_de_negocio.md` RN-SP-01, RN-SP-02, RN-SP-12, RN-TD-05, RN-TD-10, RN-TD-11
  - `knowledge-base/04_modelo_de_datos.md` §Sena («Transiciones válidas de la seña») y §ConfiguracionReglas
  - `knowledge-base/11_integraciones_whatsapp_y_mercadopago.md` §«Mercado Pago» · `knowledge-base/09_decisiones_y_supuestos.md` DD-07

### [C-39] `webhook-de-pago-de-sena`
- **Estado**: `[ ]` pendiente · **Orden**: 7 · **Gobernanza**: CRITICO
- **Objetivo** (US-050): acreditar la seña cuando Mercado Pago notifica el pago (parte de acreditación).
- **Alcance — dentro**: `POST /webhooks/mercadopago` con verificación de firma y consulta del pago; la seña pasa a `acreditada` y el turno a `reservado`, con evento `sena_acreditada`; idempotencia por `mp_payment_id`; pago de un turno que ya no está activo: la seña queda `devuelta` y el turno no cambia; seña efectivamente vencida: se persiste el vencimiento sin disparar efectos; tests con notificaciones simuladas.
- **Alcance — fuera**: devolución real por la API de Mercado Pago (Posterior, D71); persistencia del vencimiento por la tarea (C-40).
- **Depende de**: C-38
- **Escenarios mínimos**: US-050: CA-2, CA-4; WHK-1 (una notificación con firma inválida se rechaza sin cambiar la seña ni el turno)
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-050 (CA-2, CA-4) · `knowledge-base/07_flujos_principales.md` Flujo 4 (paso 4)
  - `knowledge-base/05_reglas_de_negocio.md` RN-SP-02, RN-SP-08, RN-SP-11, RN-GL-05
  - `knowledge-base/04_modelo_de_datos.md` §Sena («Transiciones válidas de la seña») · `knowledge-base/08_arquitectura_propuesta.md` §Seguridad (webhooks)
  - `knowledge-base/11_integraciones_whatsapp_y_mercadopago.md` §«Mercado Pago» · `knowledge-base/10_preguntas_abiertas.md` D38, D59, D71

### [C-40] `vencimiento-de-sena`
- **Estado**: `[ ]` pendiente · **Orden**: 7 · **Gobernanza**: CRITICO
- **Objetivo** (US-050): que una seña impaga libere el horario sin depender de que haya corrido la tarea (parte de vencimiento).
- **Alcance — dentro**: estado efectivo: un turno `pendiente_sena` con la seña vencida no ocupa el horario en la disponibilidad ni en el solapamiento; la tarea persiste `vencido` y `vencida` y dispara la oferta del hueco; crear o reprogramar un turno o aceptar una oferta sobre ese horario persiste antes el vencimiento, sin efectos, verificado también en el perfil con PostgreSQL; cancelar un `pendiente_sena` deja la seña `vencida`; reprogramar conserva la seña.
- **Alcance — fuera**: retención y devolución de una seña acreditada (C-41).
- **Depende de**: C-30, C-31, C-37, C-38
- **Escenarios mínimos**: US-050: CA-3, CA-5, CA-7; US-012: CA-3; US-022: CA-2
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md` RN-GL-05, RN-SP-03, RN-SP-11, RN-AG-10, RN-AG-10c, RN-TD-04
  - `knowledge-base/08_arquitectura_propuesta.md` §«Vencimientos y tarea periódica (Redis en la v1)» · `knowledge-base/09_decisiones_y_supuestos.md` DD-04, DD-18
  - `knowledge-base/04_modelo_de_datos.md` §Turno (nota «Estado efectivo y estado persistido») y §Sena
  - `knowledge-base/06_funcionalidades.md` §US-050 (CA-3, CA-5, CA-7) · `knowledge-base/07_flujos_principales.md` Flujo 4 (paso 5)

### [C-41] `retencion-y-devolucion-de-sena`
- **Estado**: `[ ]` pendiente · **Orden**: 7 · **Gobernanza**: CRITICO
- **Objetivo** (US-051): retener o devolver la seña acreditada según quién cancela y cuándo (parte automática; es el change titular de la historia).
- **Alcance — dentro**: la seña pasa a `retenida` al marcar `ausente` (US-014 CA-5) y al cargar desde el panel una cancelación del paciente fuera de plazo; pasa a `devuelta` si cancela el odontólogo (US-013 CA-3) o el paciente dentro de plazo; se retiene o se devuelve entera; la devolución solo se registra; eventos `sena_retenida` y `sena_devuelta`; otra transición se rechaza con RN-SP-12.
- **Alcance — fuera**: acción manual del odontólogo (C-42); devolución real por la API de Mercado Pago; validez legal (P-01).
- **Depende de**: C-17, C-18, C-29, C-39
- **Escenarios mínimos**: US-051: CA-1, CA-2, CA-3, CA-4, CA-5, CA-10
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-051
  - `knowledge-base/05_reglas_de_negocio.md` RN-SP-04, RN-SP-05, RN-SP-06, RN-SP-12, RN-TD-03
  - `knowledge-base/04_modelo_de_datos.md` §Sena («Transiciones válidas de la seña») · `knowledge-base/09_decisiones_y_supuestos.md` DD-17
  - `knowledge-base/07_flujos_principales.md` Flujo 4 (paso 6) y Flujo 5

### [C-42] `accion-manual-sobre-la-sena`
- **Estado**: `[ ]` pendiente · **Orden**: 7 · **Gobernanza**: CRITICO
- **Objetivo** (US-051): que el odontólogo devuelva o retenga la seña a mano después de corregir un marcado (parte manual).
- **Alcance — dentro**: `POST /turnos/{id}/sena/devolver` y `POST /turnos/{id}/sena/retener`, solo el rol `odontologo`; retener exige el turno `ausente` y devolver exige `atendido` (si no, RN-SP-12); cada acción queda en el historial; la corrección del marcado no mueve la seña (US-014 CA-10); acción en el panel.
- **Alcance — fuera**: mover la seña automáticamente al corregir el marcado (prohibido por RN-SP-10); retención parcial.
- **Depende de**: C-19, C-41
- **Escenarios mínimos**: US-051: CA-6, CA-7, CA-8, CA-9; US-014: CA-10
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-051 (CA-6 a CA-9) y §US-014 (CA-10)
  - `knowledge-base/05_reglas_de_negocio.md` RN-SP-10, RN-SP-12, RN-AU-05
  - `knowledge-base/04_modelo_de_datos.md` §Sena («Transiciones válidas de la seña») · `knowledge-base/03_actores_y_roles.md` matriz, fila «Corregir el marcado»
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Turnos · `knowledge-base/10_preguntas_abiertas.md` D34, D101

---

## FASE 8 — Ficha clínica, presupuestos y pagos (orden 8)

> C-43 va primero. C-44 y C-45 no dependen entre sí.

### [C-43] `ficha-clinica`
- **Estado**: `[ ]` pendiente · **Orden**: 8 · **Gobernanza**: ALTO
- **Objetivo** (US-060): abrir la ficha del paciente en la consulta y registrar la anamnesis y la evolución.
- **Alcance — dentro**: tablas `Anamnesis` (versionada) y `Evolucion` (solo inserción, con `corrige_a_id`); `POST /pacientes/{id}/anamnesis` y `POST /pacientes/{id}/evoluciones`; lectura con `GET /pacientes/{id}/ficha` (ruta propuesta, D114), que devuelve la anamnesis vigente y las evoluciones; `registrada_por` es el usuario de la sesión; solo el rol `odontologo` lee y escribe (completa US-091 CA-2); evolución vinculable a un turno; pantalla de ficha; logs sin datos clínicos.
- **Alcance — fuera**: odontograma (v1.1); imágenes y radiografías (v2); borrado físico de datos clínicos.
- **Depende de**: C-14, C-20
- **Escenarios mínimos**: US-060: CA-1, CA-2, CA-3, CA-4, CA-5, CA-6
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-060 · `knowledge-base/07_flujos_principales.md` Flujo 7
  - `knowledge-base/05_reglas_de_negocio.md` RN-FC-01, RN-FC-02, RN-FC-03, RN-PR-03, RN-AU-05
  - `knowledge-base/04_modelo_de_datos.md` §Anamnesis y §Evolucion · `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila «Pacientes y ficha»
  - `knowledge-base/03_actores_y_roles.md` matriz, fila «Ficha clínica» · `knowledge-base/08_arquitectura_propuesta.md` §Seguridad (datos sensibles)

### [C-44] `presupuesto-simple`
- **Estado**: `[ ]` pendiente · **Orden**: 8 · **Gobernanza**: MEDIO
- **Objetivo** (US-061): armar un presupuesto simple para un paciente y seguir su estado.
- **Alcance — dentro**: tablas `Presupuesto` e `ItemPresupuesto`; `GET/POST /presupuestos` y `PATCH /presupuestos/{id}`; total calculado desde los ítems; estados `borrador`, `entregado`, `aceptado` y `rechazado`, que cambia solo el odontólogo; ítems editables solo en `borrador`; pantalla de presupuestos.
- **Alcance — fuera**: códigos y valores de obras sociales (v1.1); comprobante fiscal (v2).
- **Depende de**: C-04, C-43
- **Escenarios mínimos**: US-061: CA-1, CA-2+CA-4, CA-3, CA-5, CA-6, CA-7
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-061
  - `knowledge-base/05_reglas_de_negocio.md` RN-FC-04, RN-FC-05
  - `knowledge-base/04_modelo_de_datos.md` §«Presupuesto e ItemPresupuesto»
  - `knowledge-base/03_actores_y_roles.md` matriz, fila Presupuestos · `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Presupuestos

### [C-45] `registro-de-pagos`
- **Estado**: `[ ]` pendiente · **Orden**: 8 · **Gobernanza**: CRITICO
- **Objetivo** (US-062): registrar los pagos de un paciente (pagado sí o no, monto y medio) sin una caja completa (parte de registro; es el change titular de la historia).
- **Alcance — dentro**: tabla `RegistroPago` con `es_anulacion` y `corrige_a_id` y sus restricciones; `GET/POST /pagos`; el pago se asocia al paciente y, opcionalmente, a un turno o a un presupuesto; pagos parciales como varios registros; monto mayor que 0; pantalla de pagos del paciente.
- **Alcance — fuera**: corrección y anulación (C-46); comprobante fiscal y caja con arqueo (v2); pago de la seña, que vive en `Sena`.
- **Depende de**: C-43
- **Escenarios mínimos**: US-062: CA-1, CA-2, CA-3, CA-5
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-062
  - `knowledge-base/05_reglas_de_negocio.md` RN-SP-07, RN-SP-09
  - `knowledge-base/04_modelo_de_datos.md` §RegistroPago
  - `knowledge-base/03_actores_y_roles.md` matriz, fila «Registro de pagos y señas» · `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Pagos

### [C-46] `correccion-y-anulacion-de-pagos`
- **Estado**: `[ ]` pendiente · **Orden**: 8 · **Gobernanza**: CRITICO
- **Objetivo** (US-062): corregir o anular un pago sin editar el registro original (parte de corrección).
- **Alcance — dentro**: por `POST /pagos`, corrección con reemplazo (registro nuevo que apunta al anterior) y anulación sin reemplazo (copia monto y medio); un registro se corrige o anula una sola vez y no se apunta a una anulación (RN-SP-09); cálculo de totales y pendientes; historial de pagos del paciente con las anulaciones; acciones en la pantalla de pagos.
- **Alcance — fuera**: editar o borrar un registro (no existe); reporte de cobros pendientes (C-48).
- **Depende de**: C-45
- **Escenarios mínimos**: US-062: CA-4, CA-6, CA-7, CA-8
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-062 (CA-4, CA-6 a CA-8)
  - `knowledge-base/05_reglas_de_negocio.md` RN-SP-09
  - `knowledge-base/04_modelo_de_datos.md` §RegistroPago («Dos usos de `corrige_a_id`» y «Cálculo»)
  - `knowledge-base/10_preguntas_abiertas.md` D31

---

## FASE 9 — Reportes: extensión fuera del MVP de la sección D del informe (orden 9)

> Los dos changes de esta fase son la **extensión fuera del MVP de la sección D del informe** (US-080). Se implementan al final y no forman parte del camino crítico.

### [C-47] `reporte-de-ocupacion`
- **Estado**: `[ ]` pendiente · **Orden**: 9 · **Gobernanza**: BAJO
- **Objetivo** (US-080): mostrar al dueño la ocupación del consultorio en un rango de fechas (extensión fuera del MVP; es el change titular de la historia).
- **Alcance — dentro**: `GET /reportes/ocupacion` con rango de fechas y profesional opcional; minutos con turno (estados activos, `atendido` y `ausente`) sobre minutos de horario disponible, calculado día por día con las franjas vigentes menos los bloqueos; mensajes «sin horario configurado» y «sin datos»; solo los roles `dueno` y `odontologo`; pantalla de reportes; es una lectura y nunca persiste.
- **Alcance — fuera**: ausentismo y cobros pendientes (C-48); datos clínicos en los reportes; exportación.
- **Depende de**: C-12, C-13, C-18
- **Escenarios mínimos**: US-080: CA-1, CA-3+CA-8, CA-5, CA-7, CA-9
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-080
  - `knowledge-base/05_reglas_de_negocio.md` RN-RP-01, RN-RP-03, RN-FC-02, RN-PR-03, RN-GL-05
  - `knowledge-base/04_modelo_de_datos.md` §FranjaHoraria y §Bloqueo · `knowledge-base/03_actores_y_roles.md` matriz, fila Reportes
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Reportes · `knowledge-base/10_preguntas_abiertas.md` D41, D79

### [C-48] `reportes-de-ausentismo-y-cobros`
- **Estado**: `[ ]` pendiente · **Orden**: 9 · **Gobernanza**: BAJO
- **Objetivo** (US-080): mostrar el ausentismo y los cobros pendientes (extensión fuera del MVP).
- **Alcance — dentro**: `GET /reportes/ausentismo` (ausentes sobre atendidos más ausentes, con «sin datos» si no hay ninguno) y `GET /reportes/cobros-pendientes` (señas en estado `pendiente` efectivo y registros de pago no pagados, sin anulaciones ni registros corregidos); mismos filtros y roles que C-47; se suman a la pantalla de reportes.
- **Alcance — fuera**: ocupación (C-47); gestión de cobranza; exportación.
- **Depende de**: C-40, C-46, C-47
- **Escenarios mínimos**: US-080: CA-2, CA-3, CA-4, CA-6
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-080 (CA-2, CA-4, CA-6)
  - `knowledge-base/05_reglas_de_negocio.md` RN-RP-02, RN-RP-03, RN-SP-09, RN-GL-05
  - `knowledge-base/04_modelo_de_datos.md` §RegistroPago («Cálculo») y §Sena
  - `knowledge-base/02_descripcion_general.md` §«API REST (resumen)», fila Reportes · `knowledge-base/03_actores_y_roles.md` matriz, fila Reportes

---

## Verificación cruzada

**Fecha de la verificación: 2026-10-14** (quinta corrida, posterior a C-01, C-02, C-03, C-04 y C-05 archivados y a las decisiones de la knowledge-base hasta D194; las anteriores fueron del 2026-10-05). Se hizo con un script que lee este archivo y la knowledge-base tal como estaban ese día y compara los identificadores uno por uno; el script no modifica nada y no forma parte del repositorio. **Hay que repetirla cada vez que se edite este archivo o los archivos 02 a 06, 09 o 10 de la knowledge-base**: el resultado vale solo para el contenido verificado.

Qué compara cada fila: las cinco primeras son las verificaciones pedidas por el autor (la tercera se muestra separada en reglas, decisiones y escenarios); las marcadas «Adicional» se agregaron para cubrir el resto del índice. En la fila 6 «criterio» es un par (historia, CA-n) distinto y «cita» cada aparición en el archivo; no se cuentan solo las de «Escenarios mínimos» (178 citas, 158 pares), que es lo que midió por error la corrida del 2026-10-14 anterior a esta aclaración.

| # | Verificación | Elementos revisados | Resultado |
|---|---|---|---|
| 1 | Dependencias: cada dependencia citada en una entrada es un change que existe en este archivo, y ningún change depende de uno de orden posterior | 104 dependencias en 48 changes | sin diferencias |
| 2 | Historias: cada US-NNN de `06_funcionalidades.md` (v1) tiene exactamente una fila y un change titular en «Mapeo historia → change»; las historias del Objetivo de cada entrada coinciden con ese mapeo; toda US citada existe en 06 | 30 historias de 06; 30 citadas | sin diferencias |
| 3a | Reglas: cada RN-XX-NN citada está definida en `05_reglas_de_negocio.md` | 79 reglas distintas (05 define 81) | sin diferencias |
| 3b | Decisiones: cada DD-NN citada existe en `09_decisiones_y_supuestos.md` | 17 decisiones distintas (09 define 19) | sin diferencias |
| 3c | Escenarios: cada E# citado existe en la tabla de US-010 de 06 | 12 escenarios distintos (06 define 12) | sin diferencias |
| 4 | Rutas: cada ruta HTTP citada (método y ruta) existe en `02_descripcion_general.md` o en `03_actores_y_roles.md` | 67 rutas citadas (02 y 03 listan 69, dos de ellas de Fase 2) | sin diferencias |
| 5 | Tablas: cada entidad de `04_modelo_de_datos.md` tiene un change que la crea en «Tablas del modelo → change que las crea», ese change implementa la historia que nombra la columna «Change que la crea» de 04 y su entrada nombra la tabla | 23 tablas | sin diferencias |
| 6 | Adicional: cada criterio CA-n citado como escenario, o como criterio que se completa en otro change, existe en su historia de 06 | 165 criterios distintos (pares historia y CA), en 260 citas de todo el índice (incluye «Leer antes» y el mapeo) | sin diferencias |
| 7 | Adicional: cada decisión D-NN citada figura en el registro de `10_preguntas_abiertas.md`, cada SU-NN en 09 y cada P-NN en 10 | 63 D, 3 SU y 2 P | sin diferencias |
| 8 | Adicional: cada ruta de la v1 listada en 02 y 03 está citada en alguna entrada (ninguna ruta queda sin change) | 67 rutas de la v1 | sin diferencias |
| 9 | Adicional: cada sección («…», §), flujo e ID de «Leer antes» aparece en el archivo de la KB que la entrada indica, y el archivo existe | 516 referencias | sin diferencias |
| 10 | Adicional: el árbol por bloques muestra el mismo nombre, bloque y dependencias que cada entrada, y las puertas nombran los 48 changes | 48 nodos | sin diferencias |
| 11 | Adicional: el camino crítico es una cadena de dependencias directas y es la más larga hasta un change del MVP | 15 changes | sin diferencias |
| 12 | Adicional, formato: códigos consecutivos, nombres kebab-case únicos, 12 líneas como máximo por entrada, 3 a 6 escenarios (8 en C-01), 3 o 4 líneas de «Leer antes», sin emoji | 48 entradas | sin diferencias |

**Qué no cubre.** La verificación compara identificadores, no significados: confirma que una regla, una ruta o una tabla citada existe y está asignada, no que la entrada la interprete bien. Los IDs de escenario propios de este índice (`INF`, `TP`, `HIS` y los demás de la leyenda) no existen en la KB y por eso no se comparan. Las páginas de la interfaz no son rutas HTTP y quedan fuera de la fila 4.

**Observaciones sobre la KB.** Las cinco de la primera corrida quedaron resueltas en la knowledge-base el mismo día y este índice ya las refleja: dónde se aprueba un turno de paciente nuevo (D112; US-020 CA-12, en C-27), la confirmación desde el panel (D113; US-031 CA-4 y CA-5, en C-33), la ruta de lectura de la ficha clínica (D114; en C-43), las referencias hacia adelante que faltaba declarar (D115; ya estaban asignadas en el mapeo) y quién elige el archivo único de dependencias (D116; C-01 lo crea y los demás changes agregan las suyas). No queda ninguna observación abierta.
