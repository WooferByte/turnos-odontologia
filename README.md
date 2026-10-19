# Turnos Odontológicos AR

Sistema de gestión de turnos y agenda para odontólogos independientes y consultorios chicos de Argentina. Reemplaza el papel, el Excel y el WhatsApp suelto.

**Qué entrega hasta ahora**:

- `crear-turno-sin-solapamientos` (C-01): una API con un solo endpoint, `POST /turnos`, que crea un turno en estado `reservado` (con `fin = inicio + duración de la prestación`) y rechaza con `409` el que se superpone con un turno activo del mismo profesional (`RN-AG-05`) o del mismo sillón (`RN-AG-08`), informando el código de la regla que falló.
- `infraestructura-postgresql` (C-02): la misma API sobre **PostgreSQL**, con esquema creado por migraciones (Alembic), una restricción de exclusión que hace que la base rechace por sí misma el solapamiento de turnos activos, el caso de uso que serializa las reservas simultáneas (el que llega segundo recibe el mismo `409`) y `docker compose up` para levantar todo.

- `historial-de-turnos` (C-03): `GET /turnos/{id}/historial` devuelve los eventos del turno en orden cronológico. `POST /turnos` registra el evento `creado` en la misma transacción que el turno (si el evento no se guarda, el turno tampoco), y en PostgreSQL la base rechaza modificar o borrar un evento (el historial es de solo inserción).

- `gestion-de-prestaciones` (C-04): `GET /prestaciones`, `POST /prestaciones` y `PATCH /prestaciones/{id}` para mantener el catálogo del consultorio (nombre único, duración múltiplo de 5, color, si se ofrece en la reserva online, activa o inactiva). Editar una prestación no cambia los turnos ya creados, y una prestación inactiva no admite turnos nuevos. La migración `0005` agrega `color` y `reservable_online`.

- `sesion-con-jwt` (C-06): `POST /auth/login` y `POST /auth/refresh`. Con el email y la contraseña de un usuario activo, el login devuelve un token de acceso (15 minutos) y uno de renovación (7 días), firmados con HS256; el refresh cambia el de renovación por un acceso nuevo, sin rotarlo. Cualquier rechazo del login es el mismo `401` (`RN-AU-04`) y cualquier rechazo del refresh, el mismo `401` (`RN-AU-03`). La migración `0006` crea la tabla `usuario` y el seed trae un usuario ficticio.

- `roles-y-proteccion-del-panel` (C-07): ahora **todas las rutas del panel** (`/turnos`, `/prestaciones`, `/sillones`) exigen el access token y un rol que las permita. Sin token válido responde `401` (`RN-AU-03`, siempre el mismo cuerpo); con token pero sin el rol que corresponde, `403` (`RN-AU-05`). Los roles son `odontologo`, `recepcionista` y `dueno`, se leen de la base en cada petición y sus permisos se suman. Los eventos del historial de turnos nuevos llevan el `actor_id` del usuario del token y el turno guarda quién lo creó (`creado_por`). La migración `0007` crea `usuario_rol` y las columnas `profesional.usuario_id`, `profesional.matricula` y `turno.creado_por`; el seed trae roles para la odontóloga y una recepcionista ficticia. Solo `/auth/login` y `/auth/refresh` (y `/docs`) se pueden llamar sin token.

- `panel-base-e-inicio-de-sesion` (C-08): la **primera interfaz**, en `frontend/` (React, TypeScript y Vite). La pantalla de inicio de sesión (`/ingresar`), el panel base vacío (`/panel`) con «Cerrar sesión», la sesión en el navegador (el access en memoria y el refresh en `sessionStorage`), la renovación automática ante un `401` y la vuelta al inicio de sesión cuando la sesión termina. La interfaz habla con la API por `/api` del mismo origen, sin cambios en la API.

La API se puede probar sin instalar nada más que Python (base SQLite en memoria) o sobre PostgreSQL con Docker; el panel necesita además Node 24 (ver «Panel (interfaz)»).

> Todos los datos del proyecto, de los tests y de la demo son **ficticios**. No hay datos reales de pacientes ni secretos.

## Requisitos

- **Python 3.11, 3.12 o 3.13.** No funciona con Python 3.14: una de las dependencias fijadas (`pydantic-core`) no publica binario para esa versión.
- Para instalar, correr los tests y probar la demo: nada más. **No hacen falta Docker, PostgreSQL ni Redis.**
- **Docker Desktop** (Docker Compose v2) solo para levantar la API sobre PostgreSQL y para el perfil opcional de tests con PostgreSQL.
- **Node 24 LTS (24.15 o superior)** solo para el panel (`frontend/`). Se comprueba con `node --version`, que tiene que mostrar `v24.`. Con otro Node, `npm ci` se detiene (`engine-strict`).

En Windows, el lanzador `py` sin versión puede usar Python 3.14; por eso los comandos piden una versión explícita.

## Instalación

Desde la raíz del repositorio, en Windows (PowerShell o cmd):

```
cd backend
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install --group test
```

`py -3.13` puede ser `py -3.11` o `py -3.12`. Se actualiza `pip` primero porque `--group` necesita `pip` 25.1 o superior.

En Linux y macOS cambian solo la creación y la activación del entorno:

```
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --group test
```

Todas las dependencias están en un único archivo, `backend/pyproject.toml`. No hay `requirements.txt`.

### Versiones fijadas

Las versiones exactas viven en `backend/pyproject.toml`:

| Paquete | Versión |
|---|---|
| `fastapi` | 0.115.14 |
| `starlette` | 0.46.2 |
| `pydantic` | 2.11.10 |
| `SQLAlchemy` | 2.0.54 |
| `uvicorn` | 0.54.0 |
| `tzdata` | 2026.4 |
| `psycopg[binary]` | 3.3.6 |
| `alembic` | 1.20.0 |
| `PyJWT` | 2.15.1 |
| `bcrypt` | 5.0.0 |
| `pytest` | 9.1.1 |
| `httpx` | 0.28.1 |

Imágenes de Docker (fijadas por etiqueta y digest en `docker-compose.yml` y `backend/Dockerfile`):

| Imagen | Etiqueta |
|---|---|
| `postgres` | `17.10-bookworm` |
| `python` | `3.13.15-slim-bookworm` |
| `node` (solo la construcción del frontend) | `24.21.0-bookworm-slim` |
| `nginxinc/nginx-unprivileged` (servidor del frontend) | `1.30.4-alpine` |

Las dependencias transitivas las resuelve `pip` el día de la instalación.

`tzdata` hace falta en Windows: ahí `zoneinfo` no trae base de zonas horarias y el sistema usa `America/Argentina/Buenos_Aires`.

## Tests

Desde `backend/`, con el entorno activado:

```
python -m pytest
```

Los tests corren con **SQLite en memoria**: no necesitan Docker, PostgreSQL ni Redis, ni ningún archivo de base de datos.

La corrida termina con **«528 passed, 47 deselected, 1 warning»**. Los 47 «deselected» son los del perfil opcional con PostgreSQL (más abajo), que la corrida por defecto excluye a propósito. El warning es un aviso de deprecación interno de Starlette (`starlette/testclient.py`, sobre `anyio.abc.BlockingPortal`): viene de una dependencia con versión fijada, no del código del proyecto, y no indica ningún problema.

### Escenario → test

Cada escenario del change tiene un test titular de integración (caso de uso real, repositorio real y SQLite en memoria), en `backend/tests/integration/test_crear_turno.py`:

| Escenario | Qué verifica | Test titular |
|---|---|---|
| E1 | Se crea un turno `reservado` con el fin calculado | `test_e1_feliz_crea_turno_reservado_con_fin_calculado` |
| E2 | Se rechaza el solapamiento con un turno activo del profesional (`RN-AG-05`) | `test_e2_profesional_ocupado_rechaza_con_rn_ag_05` |
| E3 | Se rechaza el solapamiento con un turno activo del sillón (`RN-AG-08`) | `test_e3_sillon_ocupado_rechaza_con_rn_ag_08` |
| E4 | Si chocan los dos, se informan los dos códigos | `test_e4_doble_conflicto_informa_los_dos_codigos` |
| E5 | Un turno que empieza justo cuando termina otro se acepta | `test_e5_borde_contiguo_se_acepta` |
| E6 | Solo los turnos activos bloquean | `test_e6_estado_no_activo_no_bloquea` |
| E7 | Un minuto de solapamiento se rechaza | `test_e7_borde_de_un_minuto_se_rechaza` |
| E12 | Una referencia inválida se rechaza con `RN-GL-04` | `test_e12_recurso_no_encontrado_rechaza_con_rn_gl_04` |

Los escenarios del historial (`historial-de-turnos`, C-03) están en `openspec/changes/historial-de-turnos/specs/` y se prueban en la suite por defecto, en `backend/tests/integration/test_historial.py` (caso de uso) y `backend/tests/api/test_historial.py` (HTTP):

| Escenario | Qué verifica | Test titular |
|---|---|---|
| E9 | Crear un turno registra el evento `creado` | `test_e9_crear_turno_registra_el_evento_creado` |
| E9 | Un rechazo no registra ningún evento | `test_e9_un_rechazo_no_registra_ningun_evento` |
| E9 | Si el evento no se puede guardar, el turno tampoco queda | `test_e9_si_el_evento_no_se_guarda_no_queda_el_turno` |
| E9 | Por HTTP, `POST /turnos` deja el evento en el historial | `test_e9_post_turnos_deja_el_evento_creado_en_el_historial` |
| US-015 CA-1 | El historial devuelve los eventos del turno pedido, en orden cronológico | `test_ca1_consultar_historial_devuelve_los_eventos_del_turno`, `test_ca1_consultar_historial_respeta_el_orden_cronologico` |
| US-015 CA-1 | Un turno sin eventos devuelve la lista vacía | `test_ca1_turno_sin_eventos_devuelve_lista_vacia` (por HTTP: `test_ca1_get_historial_de_turno_sin_eventos_responde_lista_vacia`) |
| US-015 CA-1 | La ruta del historial no admite modificaciones (`405`) | `test_ca1_la_ruta_del_historial_no_admite_modificaciones` (parametrizado) |
| HIS-1 | Un turno inexistente rechaza con `RN-GL-04` (`404` por HTTP) | `test_his1_turno_inexistente_rechaza_con_rn_gl_04`, `test_his1_get_historial_de_turno_inexistente_responde_404` |
| HIS-1 | Un id que no es número responde `422` sin código | `test_his1_id_que_no_es_numero_responde_422_sin_codigo` |

Los escenarios de la gestión de prestaciones (`gestion-de-prestaciones`, C-04) están en `openspec/changes/gestion-de-prestaciones/specs/` y se prueban en la suite por defecto: las reglas puras en `backend/tests/unit/test_prestaciones.py`, el repositorio en `backend/tests/integration/test_repositorio_prestaciones.py`, los casos de uso en `backend/tests/integration/test_prestaciones.py` y HTTP en `backend/tests/api/test_prestaciones.py`:

| Escenario | Qué verifica | Test titular |
|---|---|---|
| US-001 CA-1 | El alta responde `201` con los seis campos; nace activa y no reservable | `test_ca1_post_prestaciones_responde_201_con_los_seis_campos` (HTTP), `test_ca1_crear_prestacion_la_guarda_activa_y_no_reservable` |
| US-001 CA-1 | El nombre se guarda sin espacios de más y acepta `reservable_online` | `test_ca1_post_prestaciones_guarda_sin_espacios_de_mas_y_acepta_reservable_online` |
| US-001 CA-1 | El listado incluye las inactivas, por id; vacío si no hay ninguna | `test_ca1_get_prestaciones_lista_activas_e_inactivas_por_id`, `test_ca1_get_prestaciones_sin_ninguna_responde_lista_vacia` |
| US-001 CA-1 | Un cuerpo mal formado responde `422` sin código; una edición mal formada no cambia nada | `test_ca1_post_mal_formado_responde_422_sin_codigo` (parametrizado), `test_ca1_patch_mal_formado_no_cambia_nada` |
| US-001 CA-1 | Nombre repetido: `409` con `RN-AG-15` | `test_ca1_post_con_nombre_repetido_responde_409_con_rn_ag_15` (HTTP), `test_ca1_nombre_repetido_rechaza_con_rn_ag_15` |
| US-001 CA-1 | El nombre repetido ignora mayúsculas y acentos, también entre inactivas | `test_ca1_nombre_repetido_sin_mayusculas_ni_acentos_y_entre_inactivas`, `test_ca1_clave_de_nombre_ignora_mayusculas_acentos_y_espacios` (unitario) |
| US-001 CA-1 | Renombrar con el nombre de otra rechaza; con el propio, se acepta | `test_ca1_renombrar_con_el_nombre_de_otra_rechaza_y_no_cambia_nada`, `test_ca1_renombrar_con_su_propio_nombre_se_acepta` |
| US-001 CA-1 | Editar el color deja lo demás igual | `test_ca1_patch_del_color_responde_200_y_deja_lo_demas_igual` |
| US-001 CA-1 | Una prestación inexistente en la URL: `404` con `RN-GL-04` | `test_ca1_patch_de_una_prestacion_inexistente_responde_404_con_rn_gl_04` |
| US-001 CA-1 | Una prestación desactivada no admite turnos nuevos (`422`, `inactivo`) y se reactiva | `test_ca1_una_prestacion_desactivada_no_admite_turnos_nuevos` |
| US-001 CA-2 | Duración 47: `422` con `RN-AG-01`; se informa antes que el nombre repetido | `test_ca2_post_con_duracion_47_responde_422_con_rn_ag_01` (HTTP), `test_ca2_crear_con_duracion_invalida_rechaza_con_rn_ag_01` (parametrizado), `test_ca2_la_duracion_invalida_se_informa_antes_que_el_nombre_repetido` |
| US-001 CA-2 | La edición valida la duración igual que el alta; 5 minutos es el mínimo | `test_ca2_patch_con_duracion_invalida_responde_422`, `test_ca2_cinco_minutos_es_el_minimo_aceptado` |
| US-001 CA-3 | Alargar la duración no cambia el turno existente; el nuevo usa la duración nueva | `test_ca3_alargar_la_duracion_no_cambia_el_turno_existente` (HTTP), `test_ca3_editar_la_prestacion_no_modifica_la_fila_del_turno` |
| US-001 CA-3 | Acortarla no libera el horario del turno viejo (`409`) | `test_ca3_acortar_la_duracion_no_libera_el_horario` |
| US-001 CA-3 | Editar la prestación no agrega eventos al historial | `test_ca3_editar_la_prestacion_no_agrega_eventos_al_historial` |
| Seed de la demo | La demo lista las cinco prestaciones con su color | `test_la_demo_lista_las_cinco_prestaciones_con_su_color` (`backend/tests/api/test_demo.py`) |

Los escenarios de la gestión de sillones (`gestion-de-sillones`, C-05) están en `openspec/changes/gestion-de-sillones/specs/` y se prueban en la suite por defecto: el repositorio en `backend/tests/integration/test_repositorio_sillones.py`, los casos de uso en `backend/tests/integration/test_sillones.py` y HTTP en `backend/tests/api/test_sillones.py` (las rutas) y `backend/tests/api/test_sillones_y_turnos.py` (los sillones y `POST /turnos` juntos):

| Escenario | Qué verifica | Test titular |
|---|---|---|
| US-004 CA-3 | El alta responde `201` con `id`, `nombre` y `activo`; nace activo y el nombre se guarda sin espacios de más | `test_ca3_post_sillones_responde_201_con_id_nombre_y_activo`, `test_ca3_post_sillones_guarda_el_nombre_sin_espacios_de_mas` (HTTP), `test_ca3_crear_sillon_lo_guarda_activo` |
| US-004 CA-3 | El listado incluye los inactivos, por id; vacío si no hay ninguno | `test_ca3_get_sillones_lista_activos_e_inactivos_por_id`, `test_ca3_get_sillones_sin_sillones_responde_lista_vacia` |
| US-004 CA-3 | Un cuerpo mal formado responde `422` sin código; una edición mal formada no cambia nada; una edición vacía responde el sillón sin cambios | `test_ca3_post_mal_formado_responde_422_sin_codigo` (parametrizado), `test_ca3_patch_mal_formado_no_cambia_nada`, `test_ca3_patch_vacio_responde_200_sin_cambios` |
| US-004 CA-3 | Renombrar deja `activo` igual; `activo` `false` desactiva y el sillón sigue en el listado | `test_ca3_patch_del_nombre_conserva_activo`, `test_ca3_patch_activo_false_desactiva_el_sillon`, `test_ca3_renombrar_cambia_solo_el_nombre` |
| US-004 CA-3 | Un sillón inexistente en la URL: `404` con `RN-GL-04` | `test_ca3_patch_de_sillon_inexistente_responde_404_con_rn_gl_04` (HTTP), `test_ca3_editar_sillon_inexistente_rechaza_con_rn_gl_04` |
| US-004 CA-3 | Un sillón desactivado no admite turnos nuevos (`422`, `inactivo`), conserva los existentes y se reactiva | `test_ca3_un_sillon_desactivado_no_admite_turnos_nuevos`, `test_ca3_desactivar_no_modifica_los_turnos_del_sillon`, `test_ca3_reactivar_vuelve_a_admitir_turnos` |
| US-004 CA-3 | El sillón inactivo se informa junto con otra referencia inválida, en un solo `422` | `test_ca3_el_sillon_inactivo_se_informa_junto_con_otra_referencia` |
| US-004 CA-1 | Con un único sillón activo, el turno sin sillón va a ese | `test_ca1_con_un_unico_sillon_activo_el_turno_sin_sillon_va_a_ese` |
| US-004 CA-1 | Con dos activos, omitir el sillón responde `422` con `varios_activos` | `test_ca1_con_dos_sillones_activos_omitirlo_responde_varios_activos` |
| US-004 CA-1 | El sillón por defecto no es un id fijo; sin ninguno activo, `ninguno_activo` | `test_ca1_el_por_defecto_no_es_un_id_fijo`, `test_ca1_sin_sillones_activos_responde_ninguno_activo` |
| US-004 CA-2 | Dos profesionales a la misma hora en sillones distintos se admiten; el sillón nuevo también se ocupa (`409`, `RN-AG-08`) | `test_ca2_dos_profesionales_a_la_misma_hora_en_sillones_distintos`, `test_ca2_el_sillon_nuevo_tambien_se_ocupa` |
| Contrato | `/docs` declara los errores de `/sillones` con el esquema de problema | `test_openapi_declara_los_errores_de_sillones_con_el_esquema_problema` |

Los escenarios de la sesión del panel (`sesion-con-jwt`, C-06) están en `openspec/changes/sesion-con-jwt/specs/` y se prueban en la suite por defecto: las reglas puras en `backend/tests/unit/test_sesion.py`, el hasher y el firmador en `backend/tests/unit/test_seguridad.py`, la configuración en `backend/tests/unit/test_configuracion.py`, el repositorio en `backend/tests/integration/test_repositorio_usuarios.py`, los casos de uso en `backend/tests/integration/test_sesion.py`, el seed en `backend/tests/integration/test_seed_demo.py` y HTTP en `backend/tests/api/test_auth.py` (más `backend/tests/api/test_demo.py`):

| Escenario | Qué verifica | Test titular |
|---|---|---|
| US-090 CA-1 | Con credenciales válidas, el login devuelve el acceso y la renovación (`200`, `token_type` `bearer`, `expires_in` 900) | `test_us090_ca1_login_valido_responde_200_con_dos_tokens` (HTTP), `test_us090_ca1_credenciales_validas_devuelven_access_y_refresh` |
| US-090 CA-1 | El email se normaliza (mayúsculas y espacios) | `test_us090_ca1_email_con_mayusculas_y_espacios_inicia_sesion`, `test_us090_ca1_normalizar_email` (unitario) |
| US-090 CA-1 | El acceso vence a los 15 minutos y la renovación a los 7 días | `test_us090_ca4_claims_de_access_vencen_a_los_15_minutos`, `test_us090_ca4_claims_de_refresh_vencen_a_los_7_dias` |
| US-090 CA-1 | La demo inicia sesión con el usuario del seed | `test_us090_ca1_la_demo_inicia_sesion_con_el_usuario_del_seed` (`test_demo.py`) |
| US-090 CA-1 | Un cuerpo mal formado o un JSON roto responde `422` sin código | `test_us090_ca1_login_mal_formado_responde_422_sin_codigo` (parametrizado), `test_us090_ca1_login_con_json_roto_responde_422_sin_codigo` |
| US-090 CA-2 | Contraseña incorrecta, email inexistente y usuario inactivo: el mismo `401` con `RN-AU-04` | `test_us090_ca2_los_tres_rechazos_del_login_son_el_mismo_401` (HTTP), `test_us090_ca2_email_inexistente_rechaza_con_rn_au_04`, `test_us090_ca2_contrasena_incorrecta_rechaza_con_rn_au_04` |
| US-090 CA-2 | Siempre se compara una contraseña (aunque el email no exista) y una de más de 72 bytes se rechaza sin error | `test_us090_ca2_siempre_se_compara_una_contrasena` (parametrizado), `test_us090_ca2_contrasena_de_73_bytes_rechaza_sin_error` |
| US-090 CA-3 | Un usuario inactivo no inicia sesión, ni con la contraseña correcta | `test_us090_ca3_usuario_inactivo_rechaza_con_rn_au_04` (parametrizado) |
| US-090 CA-4 | El hash es bcrypt y no la contraseña; el repositorio guarda el email normalizado y no admite uno repetido | `test_us090_ca4_el_hash_no_es_la_contrasena_y_usa_bcrypt_con_las_rondas_dadas`, `test_us090_ca4_agregar_guarda_el_email_normalizado_y_devuelve_el_usuario_con_id`, `test_us090_ca4_email_repetido_sin_distinguir_mayusculas` |
| US-090 CA-4 | El usuario de la demo tiene hash bcrypt y no se duplica | `test_us090_ca4_usuario_de_la_demo_con_hash_bcrypt`, `test_cargar_usuario_demo_si_falta_no_duplica` |
| US-094 CA-1 | Un refresh válido devuelve un acceso nuevo, sin refresh nuevo | `test_us094_ca1_refresh_valido_responde_200_sin_refresh_token` (HTTP), `test_us094_ca1_refresh_valido_devuelve_un_access_nuevo` |
| US-094 CA-2 | Refresh vencido (borde semiabierto), de otro secreto, alterado o ilegible: `401` con `RN-AU-03` | `test_us094_ca2_los_rechazos_del_refresh_son_el_mismo_401` (HTTP), `test_us094_ca2_refresh_vencido_en_el_instante_exacto`, `test_us094_ca2_refresh_de_otro_secreto_o_alterado`, `test_us094_ca2_vigencia_semiabierta` |
| US-094 CA-2 | Un acceso no sirve como refresh; un token con otro algoritmo (HS512) se rechaza | `test_us094_ca2_access_token_no_sirve_como_refresh`, `test_us094_ca2_token_hs512_firmado_con_el_mismo_secreto_se_rechaza` |
| US-094 CA-2 | Un refresh mal formado responde `422` sin código | `test_us094_ca2_refresh_mal_formado_responde_422_sin_codigo` (parametrizado) |
| US-094 CA-3 | Usuario desactivado, inexistente o con `token_version` distinta: `401`; reactivar no revive el token viejo | `test_us094_ca3_refresh_con_token_version_cambiada_responde_401` (HTTP), `test_us094_ca3_usuario_desactivado_despues_del_login`, `test_us094_ca3_token_version_cambiada`, `test_us094_ca3_reactivado_no_revive_el_token_viejo`, `test_us094_ca3_usuario_inexistente` |
| Configuración | `JWT_SECRET` de 32 bytes como mínimo; vigencias válidas; el repr no muestra el secreto; `SEED_USUARIO_PASSWORD` de 10 caracteres a 72 bytes | `test_sesion_con_secreto_ausente_vacio_o_corto_levanta_error_que_nombra_la_variable`, `test_sesion_con_vigencia_invalida_levanta_error_que_nombra_la_variable_y_no_su_valor`, `test_sesion_repr_no_muestra_el_secreto`, `test_leer_contrasena_del_seed_acepta_de_10_caracteres_a_72_bytes` |
| Contrato | `/docs` declara los `401` y `422` de `/auth` con el esquema de problema | `test_openapi_declara_401_y_422_de_auth_con_el_esquema_problema` |

Los escenarios de la protección del panel (`roles-y-proteccion-del-panel`, C-07) están en `openspec/changes/roles-y-proteccion-del-panel/specs/` y se prueban en la suite por defecto: la matriz pura en `backend/tests/unit/test_roles.py`, el repositorio en `backend/tests/integration/test_repositorio_usuarios.py`, los casos de uso en `backend/tests/integration/test_acceso.py` y `test_historial.py`, el seed en `test_seed_demo.py` y la API en `backend/tests/api/test_proteccion.py`, `test_proteccion_de_rutas.py` y `test_demo.py`:

| Escenario | Qué verifica | Test titular |
|---|---|---|
| US-091 CA-1 | Los roles de un usuario se guardan, se leen y no se repiten ni se mezclan entre usuarios; un usuario sin roles tiene el conjunto vacío | `test_us091_ca1_roles_de_un_usuario`, `test_us091_ca1_usuario_sin_roles`, `test_us091_ca1_rol_repetido_se_rechaza` (`test_repositorio_usuarios.py`) |
| US-091 CA-1 | Los permisos son la unión de los de sus roles (odontóloga con dos roles, recepcionista más dueño) | `test_us091_ca1_los_permisos_son_la_union_de_los_roles` (`test_roles.py`), `test_us091_ca1_odontologa_con_dos_roles_tiene_todos_los_permisos`, `test_us091_ca1_recepcionista_y_dueno_suman_permisos` (`test_acceso.py`) |
| US-091 CA-3 | La matriz de permisos por rol de la tabla de arriba; sin roles no hay ningún permiso | `test_us091_ca3_matriz_de_las_rutas_existentes` (parametrizado, 6 permisos por 3 roles), `test_us091_ca3_sin_roles_no_hay_ningun_permiso` (`test_roles.py`) |
| US-091 CA-3 | Un rol insuficiente es `PermisoInsuficiente` con `RN-AU-05` | `test_us091_ca3_exigir_permiso_levanta_rn_au_05` (`test_roles.py`), `test_us091_ca3_rol_insuficiente_levanta_permiso_insuficiente` (`test_acceso.py`) |
| US-091 CA-3 | Por HTTP: el dueño no crea turnos, la recepcionista no crea prestaciones y quien no tiene roles no lee el catálogo (`403`, `RN-AU-05`, sin crear nada) | `test_us091_ca3_el_dueno_no_crea_turnos`, `test_us091_ca3_la_recepcionista_no_crea_prestaciones`, `test_us091_ca3_un_usuario_sin_roles_no_lee_el_catalogo` (`test_proteccion.py`) |
| US-091 CA-3 | El `403` se informa antes que el `422` y el `404` | `test_us091_ca3_403_antes_que_422_y_404` (`test_proteccion.py`) |
| US-091 CA-3 | La recepcionista de la demo existe y recibe `403` en `POST /prestaciones` | `test_us091_ca3_recepcionista_de_la_demo` (`test_seed_demo.py`), `test_us091_ca3_la_recepcionista_de_la_demo_recibe_403_en_prestaciones` (`test_demo.py`) |
| US-091 CA-4 | El seed da roles y profesional vinculado al usuario, sin duplicar | `test_us091_ca4_usuario_del_seed_con_sus_roles_y_su_profesional` (`test_seed_demo.py`) |
| US-091 CA-4 | El profesional se vincula a un usuario y un segundo profesional no puede usar el mismo | `test_us091_ca4_el_profesional_se_vincula_a_un_usuario_y_el_vinculo_no_se_repite` (`test_repositorio_usuarios.py`) |
| US-091 CA-5 | Quitar o asignar un rol vale con el mismo token, en la siguiente petición | `test_us091_ca5_quitar_un_rol_vale_con_el_mismo_token`, `test_us091_ca5_asignar_un_rol_vale_con_el_mismo_token` (`test_acceso.py`), `test_us091_ca5_quitar_un_rol_por_http` (`test_proteccion.py`) |
| US-092 CA-1 | Un access vigente identifica al usuario con sus roles; sin token, ilegible, de otro secreto, un refresh o uno vencido en el instante exacto son `SesionInvalida` (`RN-AU-03`) | `test_us092_ca1_access_vigente_identifica_al_usuario_con_sus_roles`, `test_us092_ca1_sin_token_es_sesion_invalida`, `test_us092_ca1_access_vencido_en_el_instante_exacto`, `test_us092_ca1_refresh_no_sirve_como_access`, `test_us092_ca1_token_ilegible_o_de_otro_secreto` (`test_acceso.py`) |
| US-092 CA-1 | Por HTTP: toda causa de rechazo da el mismo `401` (`application/problem+json`, `WWW-Authenticate: Bearer`, `RN-AU-03`) y un segundo antes de vencer el token sirve | `test_us092_ca1_toda_causa_de_rechazo_responde_401_rn_au_03`, `test_us092_ca1_los_cuerpos_de_todos_los_401_son_iguales`, `test_us092_ca1_un_segundo_antes_de_vencer_responde_200` (`test_proteccion.py`) |
| US-092 CA-1 | El `401` se informa antes que el `404` y el `422`; la demo sin token responde `401` | `test_us092_ca1_401_antes_que_404_y_422` (`test_proteccion.py`), `test_us092_ca1_la_demo_sin_token_responde_401` (`test_demo.py`) |
| US-092 CA-2 | La matriz por HTTP: las siete rutas por los tres usuarios de los ejemplos | `test_us092_ca2_matriz_por_http` (parametrizado, `test_proteccion.py`) |
| US-092 CA-2 | El turno guarda quién lo creó (`creado_por`) y la respuesta de `POST /turnos` no cambia | `test_us092_ca2_turno_guarda_creado_por` (`test_repositorio_agenda.py`), `test_us092_ca2_el_turno_guarda_quien_lo_creo` (`test_proteccion.py`) |
| US-092 CA-3 | Toda ruta fuera de la lista pública exige el access token; `/auth/login` y `/auth/refresh` responden sin cabecera | `test_us092_ca3_toda_ruta_fuera_de_la_lista_publica_exige_el_access_token`, `test_us092_ca3_las_rutas_publicas_son_solo_login_y_refresh`, `test_us092_ca3_login_y_refresh_responden_sin_cabecera` (`test_proteccion_de_rutas.py`) |
| US-092 CA-4 | Usuario desactivado, inexistente, `token_version` cambiada o reactivado con un token viejo: el mismo `401` | `test_us092_ca4_usuario_desactivado_despues_del_login`, `test_us092_ca4_usuario_inexistente`, `test_us092_ca4_token_version_cambiada`, `test_us092_ca4_reactivado_no_revive_el_token_viejo` (`test_acceso.py`), `test_us092_ca4_usuario_inactivo_responde_el_mismo_401`, `test_us092_ca4_token_version_cambiada_responde_el_mismo_401` (`test_proteccion.py`) |
| E9 | El evento `creado` lleva el id del usuario como `actor_id`; cada turno, el de quien lo creó | `test_e9_el_evento_lleva_el_id_del_usuario` (`test_historial.py` de integración), `test_e9_cada_evento_lleva_al_usuario_que_creo_su_turno` (`test_historial.py` de API) |
| E9 | Un `401` o un `403` no registra ningún evento; los eventos anteriores a C-07 se siguen leyendo sin actor | `test_e9_un_401_o_un_403_no_registra_ningun_evento` (`test_proteccion.py`), `test_e9_los_eventos_anteriores_quedan_sin_actor` (`test_historial.py` de integración) |

Además, E1, E4 y E12 se prueban por HTTP en `backend/tests/api/test_post_turnos.py` (`test_e1_post_turnos_responde_201`, `test_e4_post_turnos_responde_409_con_los_dos_codigos`, `test_e12_post_turnos_responde_422_con_rn_gl_04`), y las reglas puras tienen tests unitarios sin base de datos en `backend/tests/unit/`.

## Perfil opcional con PostgreSQL

Una parte de los tests (la que prueba lo que solo PostgreSQL garantiza) está fuera de la corrida por defecto y lleva el marcador `postgres`. **Docker Desktop hace falta solo para esto**: la instalación y los tests de las secciones anteriores no lo usan.

1. Desde la raíz del repositorio, copiá `.env.example` a `.env` (si no existe) y levantá la base. Queda publicada en `127.0.0.1:5434` (el puerto 5434 del host tiene que estar libre) y crea las bases `turnos` y `turnos_test`:

   ```
   docker compose up -d postgres
   docker compose ps
   ```

   Si tenés otra copia del repositorio con su Compose en la misma máquina, agregá `-p otro-nombre` a **todos** los comandos de `docker compose` de esta sección (por ejemplo, `docker compose -p otro-nombre up -d postgres`) y detené antes el de la otra copia, porque los puertos son los mismos. Sin `-p`, las dos copias comparten contenedores y volumen (ver «Límites conocidos»).

   Esperá a que `postgres` figure como `healthy`.

2. Desde `backend/`, con el entorno activado, definí `TEST_DATABASE_URL` en esa terminal y corré el perfil. La base tiene que terminar en `_test`: el perfil **borra y recrea** su esquema `public`.

   PowerShell:

   ```
   $env:TEST_DATABASE_URL = "postgresql+psycopg://app:app@127.0.0.1:5434/turnos_test"
   python -m pytest -m postgres
   ```

   bash:

   ```
   TEST_DATABASE_URL=postgresql+psycopg://app:app@127.0.0.1:5434/turnos_test python -m pytest -m postgres
   ```

   Se usa `127.0.0.1` y no `localhost`: en Windows `localhost` resuelve primero a IPv6 y la conexión espera varios segundos antes de caer a IPv4.

Con la base levantada, la corrida termina con **«47 passed, 528 deselected, 1 warning»**. **Si PostgreSQL no está disponible** (Docker apagado, `TEST_DATABASE_URL` sin definir o base que no responde), los 47 tests del perfil **se omiten con el motivo en el resumen** (**«47 skipped, 528 deselected»**) y la corrida termina con código de salida 0. Si la base de `TEST_DATABASE_URL` no termina en `_test`, el perfil falla a propósito para no borrar otra base.

El esquema de estos tests sale siempre de las migraciones, nunca de `create_all`. Por eso el perfil también comprueba que las migraciones y los modelos coinciden (INF-1): si alguien cambia un modelo sin escribir su migración, ese test se pone en rojo. **La suite por defecto no avisa de esto**: hay que correr el perfil cada vez que se toque el esquema.

Para detener la base: `docker compose down` (conserva los datos); `docker compose down -v` los borra.

### Escenario → test (perfil con PostgreSQL)

Los escenarios están en `openspec/changes/infraestructura-postgresql/specs/persistencia-postgresql/spec.md` (y los de E9 y US-015 CA-1 en `openspec/changes/historial-de-turnos/specs/`); los tests, en `backend/tests/postgres/`.

| Escenario | Qué verifica | Test titular |
|---|---|---|
| INF-1 | Una base vacía migrada queda con el esquema de los modelos (siete tablas desde C-03; con `color` y `reservable_online` desde C-04; ocho con `usuario` desde C-06; nueve con `usuario_rol` desde C-07), sin diferencias | `test_inf1_base_vacia_migrada_queda_con_el_esquema_del_modelo` (`test_migraciones.py`) |
| INF-1 | Deshacer las migraciones deja la base vacía | `test_inf1_deshacer_las_migraciones_deja_la_base_vacia` (`test_migraciones.py`) |
| INF-1 | Deshacer solo las migraciones del historial deja el esquema de C-01 | `test_inf1_deshacer_las_migraciones_del_historial_deja_el_esquema_de_c01` (`test_migraciones.py`) |
| INF-1 | La migración `0005` completa las prestaciones existentes con gris (`#9E9E9E`) y `reservable_online` en `false` (D174) | `test_inf1_la_migracion_0005_completa_las_prestaciones_existentes` (`test_migraciones.py`) |
| INF-1 | La migración `0006` crea la tabla `usuario` (ocho tablas desde C-06); deshacer solo esa migración deja el esquema anterior | `test_inf1_deshacer_solo_la_migracion_de_usuarios_deja_el_esquema_anterior` (`test_migraciones.py`) |
| INF-1 | La migración `0007` crea `usuario_rol` y las columnas `profesional.usuario_id`, `profesional.matricula` y `turno.creado_por`; deshacer solo esa migración deja el esquema de C-06 con los datos que ya había | `test_inf1_deshacer_solo_la_migracion_de_roles_deja_el_esquema_de_la_sesion` (`test_migraciones.py`) |
| US-091 CA-1 | La base rechaza un rol fuera de la lista (`CHECK`) | `test_us091_ca1_la_base_rechaza_un_rol_invalido` (`test_migraciones.py`) |
| US-091 CA-4 | Un volumen sembrado en C-06 (usuario sin roles) recibe los roles, el vínculo y la recepcionista, sin duplicar nada y con la secuencia de `usuario` avanzada | `test_us091_ca4_volumen_sembrado_en_c06_recibe_roles_y_vinculo` (`test_seed_y_api.py`) |
| US-091 CA-3 | Sobre PostgreSQL, la recepcionista recibe `403` en `POST /prestaciones` y `201` en `POST /turnos` | `test_us091_ca3_la_recepcionista_recibe_403_en_prestaciones_y_201_en_turnos` (`test_seed_y_api.py`) |
| US-092 CA-1 | Sobre PostgreSQL, `POST /turnos` sin token responde `401` con `RN-AU-03`; con el token del login, la petición de ejemplo funciona (`201`, y repetida `409`) | `test_us092_ca1_el_recorrido_sin_token_responde_401_sobre_postgresql`, `test_la_peticion_de_ejemplo_del_readme_responde_201_sobre_postgresql` (`test_seed_y_api.py`) |
| US-090 CA-4 | Un volumen ya sembrado sin usuario recibe el usuario del seed | `test_us090_ca4_volumen_sembrado_sin_usuario_recibe_el_usuario` (`test_seed_y_api.py`) |
| US-090 CA-1 | El seed sobre PostgreSQL permite iniciar sesión (`200`) y rechaza otra contraseña (`401`) | `test_us090_ca1_inicio_de_sesion_sobre_postgresql` (`test_seed_y_api.py`) |
| INF-2 | La base rechaza el solapamiento por profesional (E2) y por sillón (E3) | `test_inf2_la_base_rechaza_el_solapamiento_de_e2`, `test_inf2_la_base_rechaza_el_solapamiento_de_e3` (`test_restriccion_de_exclusion.py`) |
| INF-2 | Cualquier estado activo bloquea | `test_inf2_cualquier_estado_activo_bloquea` (parametrizado) |
| INF-3 | La base acepta el turno contiguo (E5) y un turno no activo no bloquea (E6) | `test_inf3_la_base_acepta_el_turno_contiguo_de_e5`, `test_inf3_un_turno_no_activo_no_bloquea` (parametrizado) |
| E11 | La reserva que pierde la carrera recibe el rechazo con los códigos completos | `test_e11_la_reserva_que_pierde_la_carrera_recibe_el_rechazo_por_solapamiento` (`test_reservas_simultaneas.py`) |
| E11 | Ocho peticiones a la vez crean un solo turno | `test_e11_de_ocho_peticiones_a_la_vez_se_crea_un_solo_turno` |
| E11 | Por HTTP, el que pierde recibe `409` | `test_e11_post_turnos_responde_409_al_que_pierde_la_carrera` |
| E9 | Ocho reservas simultáneas dejan un solo turno y un solo evento `creado` | `test_e9_de_ocho_reservas_simultaneas_queda_un_solo_evento` (`test_reservas_simultaneas.py`) |
| US-015 CA-1 | La base rechaza `UPDATE`, `DELETE` y `TRUNCATE` sobre un evento | `test_ca1_la_base_rechaza_modificar_o_borrar_un_evento` (parametrizado: `update_del_tipo`, `delete`, `truncate`; `test_historial_inmutable.py`) |
| US-015 CA-1 | La base acepta un evento nuevo del mismo turno | `test_ca1_la_base_acepta_un_evento_nuevo_del_mismo_turno` (`test_historial_inmutable.py`) |
| US-004 CA-2 | El alta de un sillón tras el seed no choca con el id fijo: la secuencia de `sillon` queda ajustada y el primer `POST /sillones` recibe un `id` distinto de 1 | `test_ca2_el_alta_de_un_sillon_tras_el_seed_no_choca_con_el_id_fijo` (`test_seed_y_api.py`) |
| INF-4 | La suite por defecto corre sin PostgreSQL y el perfil se omite | Ningún test: se comprueba con los dos comandos de esta sección y de «Tests» (arriba) en una máquina sin Docker ni variables de entorno |

`crear_turno` toma un bloqueo de fila sobre el profesional y el sillón antes de leer los turnos ocupados (`SELECT ... FOR NO KEY UPDATE`): la segunda reserva del mismo recurso espera, ve el turno ya confirmado y responde su `409` sin reintentar. La restricción de exclusión de la base sigue siendo la última defensa.

## Levantar la API y probarla a mano (demo sin Docker)

Desde `backend/`, con el entorno activado:

```
python -m uvicorn app.main:crear_app_demo --factory
```

Swagger queda en <http://127.0.0.1:8000/docs>. Para detener el servidor, `Ctrl+C`.

La demo usa una base SQLite en memoria con datos ficticios. Cada arranque parte de los mismos datos y al reiniciar se pierden los turnos creados. Los endpoints de lectura son el historial de un turno y los listados de prestaciones y de sillones; el resto de los identificadores son fijos:

| Qué | Identificadores |
|---|---|
| Consultorio | 1 — «Consultorio Demo» |
| Profesional | 1 — «Dra. Demo Ficticia» |
| Sillón | 1 — «Sillón 1» |
| Prestaciones | 1 «Consulta / control» (30 min, `#1E88E5`), 2 «Limpieza» (45 min, `#43A047`), 3 «Obturación» (60 min, `#FB8C00`), 4 «Extracción» (45 min, `#E53935`), 5 «Urgencia» (30 min, `#8E24AA`); ninguna es reservable online |
| Pacientes | 1 «Ana Ejemplo», 2 «Bruno Ficticio», 3 «Carla Inventada» |

Los usuarios de prueba, con la contraseña `demo-consultorio-2026`:

| Usuario | Roles |
|---|---|
| 1 — `odontologa@consultorio-demo.test` | `odontologo` y `dueno` (puede todo) |
| 2 — `recepcion@consultorio-demo.test` | `recepcionista` (crea turnos y lee; no edita prestaciones ni sillones) |

**Todas las rutas de los recorridos de abajo piden el access token.** Antes de empezar, obtené uno con `POST /auth/login` y pegalo en «Authorize» de `/docs`, o mandalo con `curl`; el paso a paso está en «Protección del panel» (más abajo). Sin token, cada petición de estos recorridos responde `401`.

El profesional y el sillón se pueden omitir en la petición: como la demo tiene uno solo de cada uno, se usan esos. Si se da de alta un segundo sillón activo, omitir el sillón deja de funcionar (ver «Sillones» más abajo).

### Petición de ejemplo

`POST /turnos` con el cuerpo:

```json
{"paciente_id": 1, "prestacion_id": 1, "inicio": "2026-11-02T13:00:00Z"}
```

El `inicio` va en UTC (termina en `Z`).

### Recorrido

0. Con el token de la odontóloga en «Authorize» (o en la cabecera `Authorization`) para todo lo que sigue. La misma petición sin token → `401`, con `codigos` igual a `["RN-AU-03"]`.
1. Esa petición → `201`, con el turno `reservado` en el profesional 1 y el sillón 1.
2. La misma petición otra vez → `409`, con `codigos` igual a `["RN-AG-05", "RN-AG-08"]`.
3. La misma con `"prestacion_id": 999` → `422`, con el código `RN-GL-04` (no se registra ningún evento).
4. `GET /turnos/1/historial` → `200`, con una lista de un solo evento: `tipo` `creado`, `actor_tipo` `usuario` y `actor_id` `"1"` (el id del usuario del token: la odontóloga). El `409` y el `422` de los pasos 2 y 3 no agregan eventos: repetir la consulta sigue mostrando uno.
5. `GET /turnos/999/historial` → `404`, con el código `RN-GL-04`.

Con `curl`:

```
curl -i -X POST http://127.0.0.1:8000/turnos -H "Authorization: Bearer PEGAR_EL_ACCESS_TOKEN" -H "Content-Type: application/json" -d "{\"paciente_id\": 1, \"prestacion_id\": 1, \"inicio\": \"2026-11-02T13:00:00Z\"}"
curl -i http://127.0.0.1:8000/turnos/1/historial -H "Authorization: Bearer PEGAR_EL_ACCESS_TOKEN"
```

(`PEGAR_EL_ACCESS_TOKEN` es el `access_token` del login; vale 15 minutos.) La demo parte siempre sin turnos, así que el primero que se crea es el `1`. En la API sobre PostgreSQL el id lo asigna la base y puede ser otro: usá el `id` que devolvió el `201`.

### Prestaciones

Las tres rutas piden el access token (leer: los tres roles; `POST` y `PATCH`: solo `odontologo`) y trabajan sobre el único consultorio de la instalación (el cuerpo no lleva `consultorio_id`). Con la demo levantada y el token de la odontóloga, en Swagger o con `curl`:

1. `GET /prestaciones` → `200`, con las cinco prestaciones de la tabla de arriba, ordenadas por `id`, cada una con `id`, `nombre`, `duracion_minutos`, `color`, `reservable_online` (`false`) y `activa` (`true`). Incluye las inactivas.
2. `POST /prestaciones` con `{"nombre": "Blanqueamiento", "duracion_minutos": 60, "color": "#3A7BD5"}` → `201`, con `id` 6, `reservable_online` `false` y `activa` `true`.
3. El mismo `POST` otra vez, o con `"nombre": "blanqueamiento"` (se ignoran mayúsculas, acentos y espacios de más; también cuenta entre las inactivas) → `409`, con `codigos` igual a `["RN-AG-15"]`.
4. `POST /prestaciones` con `{"nombre": "Prueba", "duracion_minutos": 47, "color": "#3A7BD5"}` → `422`, con `codigos` igual a `["RN-AG-01"]` (la duración tiene que ser mayor que 0 y múltiplo de 5).
5. `PATCH /prestaciones/2` con `{"color": "#000000"}` → `200`, con la Limpieza igual que antes salvo el color. En el `PATCH` solo se cambia lo que viene en el cuerpo.
6. `PATCH /prestaciones/999` con `{"color": "#000000"}` → `404`, con `codigos` igual a `["RN-GL-04"]`.

Editar la duración no toca los turnos ya creados (CA-3):

1. `POST /turnos` con `{"paciente_id": 1, "prestacion_id": 1, "inicio": "2026-11-02T13:00:00Z"}` → `201`, `duracion_minutos` 30 y `fin` `2026-11-02T13:30:00Z`.
2. `PATCH /prestaciones/1` con `{"duracion_minutos": 60}` → `200`.
3. `POST /turnos` con `{"paciente_id": 2, "prestacion_id": 1, "inicio": "2026-11-02T13:30:00Z"}` → `201`, `duracion_minutos` 60 y `fin` `2026-11-02T14:30:00Z`: el turno viejo sigue terminando a las 13:30, así que el nuevo cabe pegado.

Y una prestación inactiva no admite turnos nuevos:

1. `PATCH /prestaciones/5` con `{"activa": false}` → `200`.
2. `POST /turnos` con `{"paciente_id": 1, "prestacion_id": 5, "inicio": "2026-11-03T13:00:00Z"}` → `422`, con `codigos` igual a `["RN-GL-04"]` y en `referencias` `{"recurso": "prestacion", "recurso_id": 5, "motivo": "inactivo"}`. Con `{"activa": true}` se reactiva.

Con `curl` (el alta y la edición del color):

```
curl -i -X POST http://127.0.0.1:8000/prestaciones -H "Authorization: Bearer PEGAR_EL_ACCESS_TOKEN" -H "Content-Type: application/json" -d "{\"nombre\": \"Blanqueamiento\", \"duracion_minutos\": 60, \"color\": \"#3A7BD5\"}"
curl -i -X PATCH http://127.0.0.1:8000/prestaciones/2 -H "Authorization: Bearer PEGAR_EL_ACCESS_TOKEN" -H "Content-Type: application/json" -d "{\"color\": \"#000000\"}"
```

En la API sobre PostgreSQL el id de la prestación nueva lo asigna la base (mayor que 5) y los de la 1 a la 5 son los del seed.

### Sillones

Las tres rutas piden el access token (leer: los tres roles; `POST` y `PATCH`: solo `odontologo`) y trabajan sobre el único consultorio de la instalación (el cuerpo no lleva `consultorio_id`). El nombre del sillón no es único (D183). Con la demo **recién arrancada** y el token de la odontóloga (los pasos dependen unos de otros y el reinicio los reinicia), en Swagger o con `curl`:

1. `GET /sillones` → `200`, con `[{"id": 1, "nombre": "Sillón 1", "activo": true}]`. Incluye los inactivos, ordenados por `id`.
2. `POST /sillones` con `{"nombre": "Sillón 2"}` → `201`, con `{"id": 2, "nombre": "Sillón 2", "activo": true}`. El alta recibe solo el nombre.
3. El `POST /turnos` de la petición de ejemplo (sin `sillon_id`) → `422`, con `codigos` igual a `["RN-GL-04"]` y en `referencias` `{"recurso": "sillon", "recurso_id": null, "motivo": "varios_activos"}`: con dos sillones activos hay que indicar cuál. No se crea ningún turno.
4. La misma con `"sillon_id": 2` → `201`, con el turno en el sillón 2.
5. `PATCH /sillones/2` con `{"activo": false}` → `200`, con `activo` `false`; el sillón sigue en `GET /sillones` y el turno del paso 4 sigue `reservado`.
6. `POST /turnos` con `{"paciente_id": 2, "prestacion_id": 1, "inicio": "2026-11-02T14:00:00Z"}` (sin `sillon_id`) → `201`, en el sillón 1: el único activo vuelve a ser el de por defecto. Con `"sillon_id": 2` → `422`, con `referencias` `{"recurso": "sillon", "recurso_id": 2, "motivo": "inactivo"}`. Con `{"activo": true}` en el `PATCH` se reactiva.
7. Sin ningún sillón activo (`PATCH /sillones/1` con `{"activo": false}` estando el 2 inactivo), `POST /turnos` sin `sillon_id` → `422`, con `recurso_id` `null` y `motivo` `ninguno_activo`. Se desactiva el último sillón a propósito (D184); `PATCH /sillones/1` con `{"activo": true}` lo reactiva.
8. `PATCH /sillones/999` con `{"activo": true}` → `404`, con `codigos` igual a `["RN-GL-04"]`.
9. `PATCH /sillones/1` con `{"nombre": "Sillón principal", "activo": true}` → `200`, con el nombre nuevo. El `PATCH` acepta `nombre` y `activo` (D185) y solo cambia lo que viene en el cuerpo.

Con `curl` (el alta, la edición y el turno sin sillón; en el JSON, `\u00f3` es la «ó», para que la consola de Windows no altere el cuerpo):

```
curl -i http://127.0.0.1:8000/sillones -H "Authorization: Bearer PEGAR_EL_ACCESS_TOKEN"
curl -i -X POST http://127.0.0.1:8000/sillones -H "Authorization: Bearer PEGAR_EL_ACCESS_TOKEN" -H "Content-Type: application/json" -d "{\"nombre\": \"Sill\u00f3n 2\"}"
curl -i -X POST http://127.0.0.1:8000/turnos -H "Authorization: Bearer PEGAR_EL_ACCESS_TOKEN" -H "Content-Type: application/json" -d "{\"paciente_id\": 1, \"prestacion_id\": 1, \"inicio\": \"2026-11-02T13:00:00Z\"}"
curl -i -X PATCH http://127.0.0.1:8000/sillones/2 -H "Authorization: Bearer PEGAR_EL_ACCESS_TOKEN" -H "Content-Type: application/json" -d "{\"activo\": false}"
```

En la API sobre PostgreSQL el id del sillón nuevo lo asigna la base: el seed deja la secuencia ajustada y el primer alta recibe el 2, pero si ya hubo otras altas será mayor; usá el `id` que devolvió el `201`.

## Sesión del panel

`POST /auth/login` y `POST /auth/refresh` están en la demo y en la API sobre PostgreSQL. Son las dos únicas rutas del panel que se llaman sin token; todas las demás lo exigen (ver «Protección del panel», abajo).

El usuario ficticio de la demo es `odontologa@consultorio-demo.test`, con la contraseña de prueba `demo-consultorio-2026`. En PostgreSQL el email es el mismo y la contraseña es la de `SEED_USUARIO_PASSWORD`: con el `.env` copiado tal cual de `.env.example`, es la misma `demo-consultorio-2026`, así que el recorrido de abajo vale sin cambios. La recepcionista (`recepcion@consultorio-demo.test`) usa la misma contraseña. Si cambiaste esa variable, usá tu valor (y mirá en «Límites conocidos» qué pasa con un usuario ya sembrado). Con la demo levantada, en Swagger o con `curl`:

1. `POST /auth/login` con `{"email": "odontologa@consultorio-demo.test", "contrasena": "demo-consultorio-2026"}` → `200`, con `access_token`, `refresh_token`, `token_type` `bearer` y `expires_in` `900` (segundos), y la cabecera `Cache-Control: no-store`. El email se compara sin mayúsculas ni espacios de más.
2. El mismo `POST` con otra contraseña, o con `"email": "nadie@consultorio-demo.test"` → `401`, con `application/problem+json`, la cabecera `WWW-Authenticate: Bearer` y `codigos` igual a `["RN-AU-04"]`. Los dos casos (y el de un usuario inactivo) devuelven exactamente el mismo cuerpo: no se revela si el email existe.
3. `POST /auth/refresh` con `{"refresh_token": "<el refresh_token del paso 1>"}` → `200`, con un `access_token` nuevo, `token_type` `bearer` y `expires_in` `900`. **No** devuelve un refresh nuevo: el de renovación no rota (D201) y sigue valiendo hasta su vencimiento.
4. `POST /auth/refresh` con el `access_token` del paso 1 en lugar del refresh → `401`, con `WWW-Authenticate: Bearer` y `codigos` igual a `["RN-AU-03"]`. Con `{"refresh_token": "abc"}` (o uno vencido, alterado, de un usuario desactivado o de una versión anterior) → el mismo `401`.
5. Un cuerpo mal formado (por ejemplo, el login sin `contrasena`) → `422`, con `codigos` igual a `[]` y el detalle en `errores`: la validación de entrada no lleva código de regla.

Los dos tokens son JWT firmados con HS256. El acceso vale 15 minutos y el de renovación 7 días (`JWT_ACCESS_MINUTES` y `JWT_REFRESH_DAYS`). Para ver el vencimiento, pegá la parte del medio del token (entre los dos puntos) en un decodificador de base64 y leé `exp` (segundos desde 1970 en UTC) junto con `iat`, `typ` (`access` o `refresh`) y `token_version`.

Con `curl` (en cmd; en el segundo comando se pega el `refresh_token` del primero):

```
curl -i -X POST http://127.0.0.1:8000/auth/login -H "Content-Type: application/json" -d "{\"email\": \"odontologa@consultorio-demo.test\", \"contrasena\": \"demo-consultorio-2026\"}"
curl -i -X POST http://127.0.0.1:8000/auth/refresh -H "Content-Type: application/json" -d "{\"refresh_token\": \"PEGAR_EL_REFRESH_TOKEN\"}"
```

Los tokens de la demo dejan de valer al reiniciarla: cada arranque genera un secreto efímero (D196). En la API sobre PostgreSQL el secreto sale de `JWT_SECRET` (32 bytes como mínimo) y los tokens sobreviven a un reinicio.

## Protección del panel

Desde C-07, **toda ruta del panel exige un access token** y un rol que la permita. Solo `POST /auth/login`, `POST /auth/refresh`, `/docs` y `/openapi.json` se pueden llamar sin token.

### Obtener el token y usarlo

1. `POST /auth/login` (en `/docs`, o con `curl`) con `{"email": "odontologa@consultorio-demo.test", "contrasena": "demo-consultorio-2026"}` → `200`. Copiá el valor de `access_token` (vale 15 minutos; después, volvé a iniciar sesión o usá `/auth/refresh`).
2. En `/docs`, tocá el botón **Authorize** (arriba a la derecha), pegá el `access_token` **sin** el prefijo `Bearer` y confirmá. Desde ahí, «Try it out» manda la cabecera `Authorization` solo.
3. Con `curl`, agregá `-H "Authorization: Bearer <access_token>"` a cada petición:

```
curl -i http://127.0.0.1:8000/sillones -H "Authorization: Bearer PEGAR_EL_ACCESS_TOKEN"
```

Sin token, con uno vencido, alterado, de refresh, o de un usuario desactivado o con `token_version` cambiada, la respuesta es siempre **el mismo `401`**: `application/problem+json`, cabecera `WWW-Authenticate: Bearer` y `codigos` igual a `["RN-AU-03"]`. Con un token válido pero sin el rol que la ruta pide: `403` con `codigos` igual a `["RN-AU-05"]`. El `401` se informa antes que cualquier otro error (también antes de un `404` o un `422`), y el `403` antes que el `422` y el `404`.

### Qué puede hacer cada rol

Un usuario puede tener varios roles y sus permisos **se suman**. Los roles se leen de la base en **cada petición**: quitar o dar un rol vale desde la petición siguiente, con el mismo token.

| Ruta | `odontologo` | `recepcionista` | `dueno` |
|---|---|---|---|
| `POST /turnos` | sí | sí | no |
| `GET /turnos/{id}/historial` | sí | sí | sí |
| `GET /prestaciones` | sí | sí | sí |
| `POST /prestaciones`, `PATCH /prestaciones/{id}` | sí | no | no |
| `GET /sillones` | sí | sí | sí |
| `POST /sillones`, `PATCH /sillones/{id}` | sí | no | no |

### Usuarios de prueba

| Email | Roles | Dónde |
|---|---|---|
| `odontologa@consultorio-demo.test` | `odontologo` y `dueno` | La demo y el seed de PostgreSQL |
| `recepcion@consultorio-demo.test` | `recepcionista` | La demo y el seed de PostgreSQL |

La contraseña de los dos es `demo-consultorio-2026` (la de prueba de `SEED_USUARIO_PASSWORD` en `.env.example`; la demo siempre usa esa). La odontóloga puede todo, así que el `403` se ve con la recepcionista.

### Recorrido de la protección (demo sin Docker)

Con la demo recién arrancada:

1. `POST /turnos` con la petición de ejemplo y **sin** token → `401`, con `codigos` igual a `["RN-AU-03"]`.
2. `POST /auth/login` con la odontóloga y «Authorize» con su `access_token`. `POST /turnos` → `201`; repetido → `409` con `["RN-AG-05", "RN-AG-08"]`; con `"prestacion_id": 999` → `422` con `RN-GL-04`.
3. `GET /turnos/1/historial` → `200`, con `actor_id` `"1"`.
4. `POST /auth/login` con la recepcionista y «Authorize» con su token (reemplaza al anterior). `POST /prestaciones` con `{"nombre": "Prueba", "duracion_minutos": 30, "color": "#3A7BD5"}` → `403`, con `codigos` igual a `["RN-AU-05"]`. `POST /turnos` con `{"paciente_id": 2, "prestacion_id": 1, "inicio": "2026-11-02T14:00:00Z"}` → `201`.

### Recorrido de los roles sobre PostgreSQL (Compose)

Con `docker compose up --build -d` hecho y el token de la odontóloga en «Authorize». Los roles viven en la tabla `usuario_rol`; se cambian con SQL desde el contenedor de la base (con otra copia del repositorio, agregá `-p otro-nombre`). Un volumen sembrado antes de C-07 recibe los roles al arrancar la API: `docker compose logs api` dice «Seed cargado.».

1. Quitar el rol y probar **con el mismo token**:

   ```
   docker compose exec postgres psql -U app -d turnos -c "DELETE FROM usuario_rol WHERE usuario_id = 1 AND rol = 'odontologo'"
   ```

   `POST /turnos` → `403` (`RN-AU-05`: el dueño no crea turnos) y `GET /turnos/{id}/historial` → `200` (el dueño sí lo lee).
2. Restaurar el rol:

   ```
   docker compose exec postgres psql -U app -d turnos -c "INSERT INTO usuario_rol (usuario_id, rol) VALUES (1, 'odontologo')"
   ```

   Con el mismo token, `POST /turnos` vuelve a responder `201` (con un horario libre).
3. Invalidar el token:

   ```
   docker compose exec postgres psql -U app -d turnos -c "UPDATE usuario SET token_version = token_version + 1 WHERE id = 1"
   ```

   El mismo token → `401`; un login nuevo → `200` y el token nuevo sirve.

## Panel (interfaz)

Desde C-08 hay una interfaz en `frontend/`. Para el panel, el archivo de dependencias es `frontend/package.json` (con `frontend/package-lock.json`), con versiones exactas; para la API sigue siendo `backend/pyproject.toml`.

### Instalación y tests

Hace falta Node 24 LTS (24.15 o superior; ver «Requisitos»). Desde la raíz del repositorio:

```
cd frontend
npm ci
npm test
npm run typecheck
```

`npm test` corre **38 tests en 4 archivos** («Tests 38 passed (38)»); no necesita el backend, Docker ni red. `npm run typecheck` (`tsc --noEmit`) termina sin salida. `npm run build` genera `frontend/dist/`.

### Probar el panel (demo sin Docker, dos terminales)

Terminal 1, la API de demostración (desde `backend/`, con el entorno activado como en «Instalación»):

```
python -m uvicorn app.main:crear_app_demo --factory
```

Terminal 2, la interfaz (desde `frontend/`, después de `npm ci`):

```
npm run dev
```

Abrí <http://127.0.0.1:5173>. El servidor de desarrollo reenvía `/api/...` a la API en `127.0.0.1:8000` (quitando el prefijo `/api`), así que el navegador habla siempre con un solo origen. Los puertos `5173` y `8000` tienen que estar libres.

Usuarios de prueba (los de «Protección del panel», con la contraseña `demo-consultorio-2026`): `odontologa@consultorio-demo.test` y `recepcion@consultorio-demo.test`. En la demo los dos están activos; el caso del usuario inactivo (US-090 CA-3) se prueba en la suite y en Compose (más abajo).

Recorrido:

1. Abrir `/panel` sin sesión → te lleva a `/ingresar`.
2. Ingresar con la odontóloga y una contraseña incorrecta, y después con `nadie@consultorio-demo.test`: los dos muestran **el mismo** mensaje («El email o la contraseña no son correctos.»); en la pestaña de red, `POST /api/auth/login` responde `401` con `codigos` `["RN-AU-04"]`.
3. Ingresar con la contraseña correcta → «Panel del consultorio» y el botón «Cerrar sesión».
4. Recargar la página → seguís dentro: se ve un `POST /api/auth/refresh` con `200`.
5. «Cerrar sesión» → volvés a `/ingresar` y el botón «Atrás» del navegador no muestra el panel.

Ningún token ni la contraseña aparecen en la URL.

### Panel con Compose

`docker compose up --build -d` (ver «Levantar la API con PostgreSQL») levanta también el servicio `frontend`: nginx sin privilegios que sirve la interfaz en <http://127.0.0.1:5173> y reenvía `/api/` a la API. `docker compose ps` tiene que mostrar `postgres`, `api` y `frontend` como `healthy`. Es la misma dirección que `npm run dev`: se usa una o la otra, y se detiene antes la que esté corriendo. El recorrido es el de arriba; además, con Compose se puede ver al usuario inactivo (US-090 CA-3) y la sesión invalidada (US-092 CA-1):

```
docker compose exec postgres psql -U app -d turnos -c "UPDATE usuario SET activo = false WHERE email = 'recepcion@consultorio-demo.test'"
```

La recepcionista ve el mismo mensaje genérico que con una contraseña incorrecta. Para restaurarla:

```
docker compose exec postgres psql -U app -d turnos -c "UPDATE usuario SET activo = true WHERE email = 'recepcion@consultorio-demo.test'"
```

Con la odontóloga adentro, `UPDATE usuario SET token_version = token_version + 1 WHERE id = 1` (con el mismo `docker compose exec postgres psql ...`) y recargar `/panel` te lleva a `/ingresar` con el aviso «Tu sesión terminó. Iniciá sesión de nuevo.». Con otra copia del repositorio, agregá `-p otro-nombre` a todos los comandos de `docker compose`.

### Versiones fijadas del frontend

Las versiones exactas viven en `frontend/package.json`; `frontend/package-lock.json` se generó con `npm install --before=2026-10-12` (ningún paquete publicado desde esa fecha) y se instala siempre con `npm ci`.

| Paquete | Versión |
|---|---|
| `react`, `react-dom` | 19.3.0 |
| `react-router` | 7.18.4 |
| `typescript` | 6.0.3 |
| `vite` | 8.3.4 |
| `@vitejs/plugin-react` | 6.1.2 |
| `vitest` | 5.0.3 |
| `jsdom` | 30.1.2 |
| `@testing-library/react` | 16.3.3 |
| `@testing-library/dom` | 10.4.2 |
| `@testing-library/user-event` | 14.6.7 |
| `@types/react`, `@types/react-dom` | 19.3.0 |
| `@types/node` | 24.19.2 |

### Escenario → test (frontend)

La API se reemplaza en los tests por un servidor falso escrito a mano (`frontend/src/test/servidorFalso.ts`) que se inyecta por parámetro; no hay `vi.mock`.

| Escenario | Test titular |
|---|---|
| US-090 CA-1 (credenciales válidas) | `src/features/ingreso/PaginaIngreso.test.tsx` — «US-090 CA-1: credenciales válidas llevan al panel» |
| US-090 CA-2 (rechazo genérico) | `PaginaIngreso.test.tsx` — «US-090 CA-2: email inexistente muestra el mensaje genérico» y «US-090 CA-2: los dos rechazos se ven idénticos» |
| US-090 CA-3 (usuaria inactiva) | `PaginaIngreso.test.tsx` — «US-090 CA-3: la usuaria inactiva ve el mismo mensaje y no entra» |
| US-092 CA-1 (sesión inválida o vencida) | `src/pages/RutaProtegida.test.tsx` — «US-092 CA-1: el panel sin sesión lleva a /ingresar sin pedir nada a la API»; `src/shared/api/clienteHttp.test.ts` — «US-092 CA-1: access vencido se renueva una vez y repite la petición» |

Hay además tests de la renovación compartida, del `403`, del cierre de sesión y de que ninguna URL contenga un token, y cuatro guards (`src/test/guards.test.ts`) que fallan si aparece `any`, `vi.mock`, `localStorage`, `dangerouslySetInnerHTML` o un archivo `index.ts` de reexportación.

Resultado actual de las dos suites: frontend «Tests 38 passed (38)»; backend «528 passed, 47 deselected, 1 warning».

## Levantar la API con PostgreSQL

Necesita Docker Desktop. Los datos son los mismos de la demo y todos son ficticios.

1. Desde la raíz del repositorio, copiá `.env.example` a `.env` (Compose lo lee solo; Python no lee `.env`).
2. Construí y levantá todo:

   ```
   docker compose up --build -d
   docker compose ps
   ```

   Con otra copia del repositorio en la misma máquina, usá `-p otro-nombre` en **todos** los comandos de `docker compose` de esta sección (`up`, `ps`, `logs`, `restart`, `down`), por ejemplo `docker compose -p otro-nombre up --build -d`, y detené antes el Compose de la otra copia, porque los puertos son los mismos.

   Esperá a que `postgres` y `api` figuren como `healthy`. Al arrancar, el contenedor de la API aplica las migraciones (`alembic upgrade head`), carga el seed ficticio si falta (también les da los roles al usuario y a la recepcionista de un volumen sembrado antes de C-07) y recién entonces levanta el servidor: `docker compose logs api` lo muestra. Una segunda vez el log dice «El seed ya estaba cargado: no hizo falta.». Esto vale para una sola réplica de la API.
3. Swagger queda en <http://127.0.0.1:8000/docs>, con los mismos identificadores, la misma petición de ejemplo y el mismo recorrido de la demo (con el token de «Protección del panel»). A diferencia de la demo, los turnos **persisten**: tras `docker compose restart api`, repetir la primera petición devuelve `409`.

Los puertos se publican solo en `127.0.0.1`: `8000` para la API y `5434` para PostgreSQL (el 5434 y no el 5432, para no chocar con un PostgreSQL local). Los dos tienen que estar libres en el host; si no, `docker compose up` falla y hay que cambiar el mapeo en `docker-compose.yml` (y la URL de `TEST_DATABASE_URL`). Se usa `127.0.0.1` y no `localhost` por la razón explicada arriba.

Para detener: `docker compose down` (conserva los datos); `docker compose down -v` los borra y la próxima vez la base arranca vacía.

### Variables de entorno

| Variable | Quién la lee | Valor de prueba |
|---|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | La imagen de PostgreSQL y `docker-compose.yml` | `app`, `app`, `turnos` |
| `DATABASE_URL` | La API (`crear_app_desde_entorno`), Alembic y la carga del seed | Dentro de Compose la arma `docker-compose.yml`: `postgresql+psycopg://app:app@postgres:5432/turnos`. Desde tu máquina: `postgresql+psycopg://app:app@127.0.0.1:5434/turnos` |
| `TEST_DATABASE_URL` | Solo el perfil `postgres` de pytest | `postgresql+psycopg://app:app@127.0.0.1:5434/turnos_test` |
| `JWT_SECRET` | La API (`crear_app_desde_entorno`) | Secreto de prueba de 32 bytes como mínimo; está en `.env.example`. Sin él, la API sobre PostgreSQL no arranca |
| `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS` | La API | `15` y `7` (los valores por defecto si faltan) |
| `SEED_USUARIO_PASSWORD` | La carga del seed (`cargar_seed`) | Contraseña de prueba del usuario del seed, de 10 caracteres a 72 bytes; está en `.env.example`. Sin ella, el seed no corre |

Si falta `DATABASE_URL`, la API sin Docker (`crear_app_desde_entorno`) **no cae a SQLite**: falla con un mensaje que nombra la variable; lo mismo pasa con `JWT_SECRET` y `SEED_USUARIO_PASSWORD`. Las credenciales y los secretos son de prueba. `docker-compose.yml` pasa las cuatro variables nuevas al servicio `api`.

Para levantar la API sobre PostgreSQL sin construir la imagen (con la base ya levantada, desde `backend/`):

```
# PowerShell
$env:DATABASE_URL = "postgresql+psycopg://app:app@127.0.0.1:5434/turnos"
$env:JWT_SECRET = "<un secreto de prueba de 32 bytes como mínimo>"
$env:SEED_USUARIO_PASSWORD = "<una contraseña de prueba de 10 caracteres como mínimo>"
python -m alembic upgrade head
python -m app.infrastructure.db.cargar_seed
python -m uvicorn app.main:crear_app_desde_entorno --factory
```

### Migraciones

El esquema de PostgreSQL sale solo de migraciones (`backend/app/infrastructure/db/migraciones/versions/`: `0001` crea las seis tablas, `0002` agrega las restricciones de exclusión, `0003` crea la tabla `evento_turno` del historial y `0004` agrega los disparadores que hacen que la base rechace `UPDATE`, `DELETE` y `TRUNCATE` sobre esa tabla, `0005` agrega `color` y `reservable_online` a `prestacion`: completa las filas que ya existían con gris `#9E9E9E` y `false`, y después quita esos valores por defecto porque la API exige el color, `0006` crea la tabla `usuario` del panel: email único en minúsculas, hash bcrypt, `activo` y `token_version`, y `0007` crea `usuario_rol` —clave compuesta, con un `CHECK` que solo admite `odontologo`, `recepcionista` y `dueno`— y las columnas nulas `profesional.usuario_id` (único), `profesional.matricula` y `turno.creado_por`; no escribe datos: los roles los pone el seed). Son solo para PostgreSQL; la suite por defecto crea el esquema con `create_all` sobre SQLite. Desde `backend/`, con `DATABASE_URL` definida como arriba:

```
python -m alembic current
python -m alembic upgrade head
python -m alembic downgrade base
python -m alembic revision --autogenerate --rev-id 0008 -m "descripcion"
```

La migración autogenerada **se revisa a mano** antes de usarla, y cada change que toque un modelo agrega la suya y corre el perfil opcional (INF-1).

## Límites conocidos

- Los datos de la demo sin Docker viven en memoria y se pierden al reiniciar; los de la API sobre PostgreSQL persisten en el volumen de Docker.
- La coincidencia entre migraciones y modelos (INF-1), la protección ante reservas simultáneas (E11, y el evento único de E9 con ocho reservas) y la garantía de que la base rechaza modificar o borrar un evento (US-015 CA-1, migración `0004`) **solo se prueban en el perfil opcional con PostgreSQL**: la suite por defecto no las ejerce. En SQLite (demo y suite por defecto) la inmutabilidad del historial se garantiza solo desde la aplicación: no hay métodos para modificarlo y la ruta responde `405`.
- **El estado de los sillones cambia el resultado del recorrido de la demo**: con un segundo sillón activo, `POST /turnos` sin `sillon_id` responde `422` con `varios_activos` (RN-AG-14), y sin ninguno activo, `ninguno_activo`. En PostgreSQL los sillones persisten, así que un sillón dado de alta en una prueba sigue ahí en la siguiente: desactivalo con `PATCH` o usá `docker compose down -v`.
- Desactivar un sillón y crear un turno en él **al mismo tiempo** puede dejar un turno nuevo en un sillón recién desactivado: `crear_turno` valida el sillón antes de tomar el bloqueo de fila (S15). Sin usuarios ni panel todavía, se acepta; el turno queda igual de válido y no se cancela.
- Un volumen de PostgreSQL sembrado antes de la migración `0005` (por ejemplo, el de las pruebas manuales de C-02 y C-03) **no se vuelve a sembrar**: sus cinco prestaciones quedan con el color gris `#9E9E9E` hasta que se edite cada una con `PATCH /prestaciones/{id}` (D174). Con `docker compose down -v` la base arranca vacía y el seed trae los colores de la demo.
- Los eventos `creado` anteriores a C-07 tienen `actor_tipo` `usuario` y **`actor_id` vacío para siempre** (D159): completarlo después sería modificar el historial. Los turnos anteriores a C-07 tampoco tienen `creado_por` (queda vacío). Los eventos y turnos nuevos sí llevan al usuario del token.
- **`/docs` y `/openapi.json` son públicos** (D214): se pueden leer sin token (las rutas que documentan, no). Es aceptable porque la API se publica solo en `127.0.0.1` y hay solo datos ficticios.
- **Un cuerpo con JSON roto responde `422` antes que `401`** (design R12): FastAPI lee el cuerpo antes de evaluar el token. Un cuerpo bien formado sin token sí responde `401`, antes de cualquier validación.
- **Deshacer la migración `0007` pierde los roles** (`alembic downgrade 0006` borra `usuario_rol`), el vínculo profesional-usuario y `creado_por`; los usuarios, los turnos y los eventos quedan.
- **El rol se lee en cada petición, pero el token no se revoca de a uno**: tras quitarle **un** rol a un usuario, su access token sigue sirviendo hasta 15 minutos para lo que sus **otros** roles permiten (y deja de servir para lo que solo daba el rol quitado). Desactivar al usuario o subir su `token_version` lo corta en la petición siguiente. Todavía no hay ruta para dar o quitar roles ni para desactivar usuarios: se hace en la base, como en «Protección del panel».
- **`profesional.matricula` existe pero nadie la escribe ni la lee todavía** (D215).
- Los turnos guardados antes de la migración `0003` (por ejemplo, los de la prueba manual de C-02 en el volumen de PostgreSQL) **no tienen historial**: la consulta devuelve `200` con `[]` (D160). La migración no inventa eventos del pasado.
- **`/auth/login` no tiene límite de peticiones** (D195): cualquiera que llegue a la API puede probar contraseñas. Se acepta porque la API se publica solo en `127.0.0.1` y bcrypt con 12 rondas ya frena cada intento; el límite se decide en el change de la reserva pública. Tampoco hay registro de eventos de seguridad.
- **No hay cierre de sesión en el servidor** ni revocación de un token puntual (RN-AU-03): un refresh vale hasta su vencimiento o hasta que cambie la `token_version` del usuario.
- **Cerrar sesión en el panel no revoca el refresh en el servidor**: la interfaz solo borra los tokens del navegador (no hay ruta de cierre); el refresh sigue valiendo en la API hasta su vencimiento o hasta que cambie la `token_version`.
- **La sesión del panel no se comparte entre pestañas ni sobrevive al cierre del navegador**: el access vive en memoria y el refresh en `sessionStorage`. Recargar la pestaña la conserva; otra pestaña pide iniciar sesión. Si `sessionStorage` no está disponible, la sesión vive solo en memoria.
- **El refresh en `sessionStorage` lo podría leer un script inyectado (XSS)**: lo mitigan React (escapa el texto), la ausencia de HTML crudo y la política de contenido de nginx. La alternativa, una cookie `HttpOnly`, cambiaría el contrato de `/auth/refresh` y queda fuera de C-08.
- **El panel renueva el access solo cuando recibe un `401`** (no antes de que venza): un `401` extra cada 15 minutos de uso.
- **El panel base no muestra quién inició sesión** (no hay ruta que lo informe) y todavía no tiene pantallas de negocio.
- Un volumen de PostgreSQL sembrado antes de C-06 recibe el usuario del seed al próximo arranque, pero **un usuario ya sembrado no cambia su contraseña** aunque cambie `SEED_USUARIO_PASSWORD`. Con `docker compose down -v` la base arranca vacía.
- El puerto 5434 (PostgreSQL), el 8000 (API) y el 5173 (interfaz) del host tienen que estar libres.
- El proyecto de Compose tiene nombre fijo (`turnos-odontologia`): **dos copias del repositorio en la misma máquina comparten contenedores y volumen**, y un `docker compose down -v` en una borra los datos de la otra. Para levantar una segunda copia aparte, usá otro nombre de proyecto en todos los comandos: `docker compose -p otro-nombre up -d`.
- En Windows, si el repositorio está en una ruta muy larga (más de unos 200 caracteres), el perfil opcional falla al importar `psycopg` con «El nombre del archivo o la extensión es demasiado largo». Cloná en una ruta corta.
- Las credenciales, la contraseña del usuario del seed y el `JWT_SECRET` de los ejemplos y de `.env.example` son de prueba. No hay configuración de producción: TLS, copias de respaldo, roles con privilegios mínimos ni ajuste del pool.
- La API migra al arrancar el contenedor: sirve para una sola réplica.
- No se valida el horario de atención del profesional ni del consultorio.
- No hay Redis ni pantallas de negocio (turnos, prestaciones, sillones) en la interfaz: llegan en changes posteriores.
- En `/docs`, las respuestas `409` y `422` figuran bajo `application/problem+json` y también bajo `application/json`. La respuesta real sale siempre como `application/problem+json`.
- Los mensajes de validación de formato que genera Pydantic salen en inglés.

## Estructura

La consigna muestra `src/` y `tests/` y aclara que los nombres pueden variar. Acá la correspondencia es:

| Consigna | Este repositorio |
|---|---|
| `src/` | `backend/app/` |
| `tests/` | `backend/tests/` |
| (interfaz) | `frontend/src/` y `frontend/src/**/*.test.ts(x)` |

`backend/app/` tiene las capas `domain` (reglas puras, sin FastAPI ni SQLAlchemy), `application` (casos de uso), `infrastructure` (SQLAlchemy, SQLite y PostgreSQL, migraciones de Alembic, seed de la demo) y `api` (FastAPI). La documentación del dominio está en `knowledge-base/` y el plan de changes en `CHANGES.md`.
