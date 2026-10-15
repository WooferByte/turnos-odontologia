# Proposal: sesion-con-jwt

Change **C-06** de `CHANGES.md`, historias **US-090** («Iniciar sesión») y **US-094** («Renovar la sesión»), parte de API. Gobernanza **CRÍTICO** (autenticación): solo planificación; nada se implementa hasta que el autor apruebe el plan completo. Las nueve preguntas del propose quedaron cerradas por el autor el 2026-10-14 (D195 a D203; ver `design.md`).

## Why

Hoy el sistema no tiene usuarios: `POST /turnos`, el historial y los catálogos de prestaciones y sillones responden a cualquiera que llegue a la API (DD-14), y eso solo es aceptable porque los datos son ficticios y los puertos se publican en `127.0.0.1`. Antes de proteger esas rutas (C-07) y de construir la pantalla de inicio de sesión (C-08) hace falta lo que ambos usan: un usuario del consultorio con su contraseña guardada como hash, y una forma de obtener y renovar un JWT.

Va ahora porque abre la fase 3 y está en el camino de C-07 y C-08, que van en serie; depende solo de C-02 (migraciones y PostgreSQL), ya archivado.

## What Changes

- **Tabla `usuario`** (migración `0006`, reversible) con los campos de `04` §«Usuario y UsuarioRol»: `consultorio_id`, `email` único, `hash_password` (bcrypt, nunca la contraseña en claro), `activo`, `token_version` y `creado_en`. Sin `UsuarioRol` (C-07).
- **`POST /auth/login`** con email y contraseña: `200` con un access token (15 minutos) y un refresh token (7 días), ambos JWT firmados con HS256 y con el claim `token_version` (RN-AU-03, D74, SU-09).
- **`401` genérico** (RN-AU-04): email inexistente, contraseña incorrecta y usuario inactivo reciben la misma respuesta, con el código `RN-AU-04`. El usuario inexistente también pasa por una comparación bcrypt, para que el tiempo de respuesta no lo delate.
- **`POST /auth/refresh`** con el refresh token: `200` con un access token nuevo. Responde `401` si el token está vencido, mal firmado, es un access token, o si el usuario ya no está activo o su `token_version` cambió (RN-AU-03, RN-AU-04, D43).
- **Reloj inyectado** (regla dura 2): la emisión y el vencimiento usan `utc_now()`; los tests mueven el reloj sin bibliotecas para congelar el tiempo.
- **Configuración** desde el entorno: `JWT_SECRET` (obligatoria en `crear_app_desde_entorno`, con un largo mínimo), `JWT_ACCESS_MINUTES` y `JWT_REFRESH_DAYS` (opcionales, 15 y 7 por defecto). La suite por defecto y la demo sin Docker no leen variables (D148).
- **Usuario ficticio del seed** (`odontologa@consultorio-demo.test`) en la demo sin Docker y en Compose; en un volumen de PostgreSQL ya sembrado se agrega igual, porque se siembra aparte del consultorio.
- **Dos dependencias nuevas** en `backend/pyproject.toml`, con versión exacta: `PyJWT` y `bcrypt` (pins y fechas en `design.md`).
- **`docker-compose.yml`** pasa las variables nuevas a la API. **`.env.example` lo edita el autor a mano** con las líneas exactas que fija el design (tarea del autor).
- **README**: variables nuevas, ejemplos de `/auth/login` y `/auth/refresh` sobre la demo, tabla escenario → test y límites conocidos.

No hay cambios **BREAKING**: ninguna ruta existente pasa a exigir token (eso es C-07); `POST /turnos`, el historial, `/prestaciones` y `/sillones` responden igual.

### Escenarios

Cubre los seis mínimos de la entrada C-06 de `CHANGES.md` (dentro del «3 a 6»), más el ajuste de INF-1 que pide una tabla nueva (D158):

| ID | Qué verifica | Dónde corre |
|---|---|---|
| US-090 CA-1 + CA-4 | Con credenciales válidas, `200` con access (15 min) y refresh (7 días), JWT HS256 con `token_version`; la contraseña se guarda con bcrypt | Suite por defecto |
| US-090 CA-2 | Email inexistente y contraseña incorrecta: el mismo `401` genérico (`RN-AU-04`) | Suite por defecto |
| US-090 CA-3 | Un usuario inactivo no inicia sesión, aunque la contraseña sea correcta: el mismo `401` | Suite por defecto |
| US-094 CA-1 | `POST /auth/refresh` con un refresh válido devuelve un access nuevo | Suite por defecto |
| US-094 CA-2 | Refresh vencido o inválido (firma, tipo, formato): `401` | Suite por defecto |
| US-094 CA-3 | Refresh de un usuario inactivo o con otro `token_version`: `401` aunque no haya vencido | Suite por defecto |
| INF-1 (delta) | La base migrada incluye `usuario`; deshacer solo la migración `0006` deja el esquema de C-05 | Perfil `postgres` |

No se toca ningún escenario de US-010, US-015, US-001 ni US-004.

## Fuera de alcance

- **Roles** (`UsuarioRol`), **protección de endpoints** con JWT y `403` (C-07, US-091, US-092). El usuario del seed queda sin roles hasta C-07.
- `Profesional.usuario_id`, `Turno.creado_por` y el usuario como actor del historial (C-07).
- **Pantalla de inicio de sesión** y dónde guarda los tokens el panel (C-08).
- **Gestión de usuarios** (alta, desactivación, restablecer contraseña; C-09) y **cambio de la propia contraseña** (`POST /auth/cambiar-contrasena`, C-10). Por eso este change no incrementa `token_version` en ningún lado: solo lo compara.
- **Tabla de tokens**, revocación de a uno y cierre de sesión en el servidor (no existen en la v1, RN-AU-03).
- **Rotación del refresh token** (el refresh vence a los 7 días del inicio de sesión; ver `design.md`).
- **Límite de peticiones** y **registro de eventos de seguridad** en `/auth/login` (D195).
- OAuth2, SSO, MFA, cookies de sesión y CSRF (fuera de la v1).
- Cuenta de paciente (el paciente no tiene cuenta) y tokens de gestión de turnos (C-25 en adelante).
- Sobreturnos y excepción de horario: fuera de la v1.

## Capabilities

### New Capabilities

- `sesion-del-panel`: cómo un usuario del consultorio obtiene y renueva su sesión del panel: el usuario con su contraseña en bcrypt, `POST /auth/login`, `POST /auth/refresh`, la vida de los tokens y el `401` genérico (RN-AU-01, RN-AU-03, RN-AU-04; US-090, US-094). C-07 agrega la validación del access token en cada petición; C-10, el cambio de contraseña.

### Modified Capabilities

- `persistencia-postgresql`: solo cambia la lista de ejemplo del escenario INF-1 (agrega `usuario` y su `creado_en`) y se suma un escenario de borde para deshacer la migración `0006`. El texto del requisito no cambia. Es lo que D158 fijó para todo change que agregue tablas («toca solo la lista del escenario, no el requisito»).

Se revisaron las demás: `creacion-de-turnos`, `historial-de-turnos`, `gestion-de-prestaciones` y `gestion-de-sillones` no cambian. Ninguna ruta suya pasa a exigir token en este change, y el actor del historial sigue siendo `usuario` sin id hasta C-07 (D159).

## Impact

- **Código nuevo**: dominio de acceso en `backend/app/domain/acceso/` (dato del usuario, claims y reglas de vigencia, puro); errores `CredencialesInvalidas` y `SesionInvalida` en `domain/errors.py`; casos de uso en `application/sesion.py`; adaptadores de bcrypt y JWT en `infrastructure/seguridad/`; repositorio `infrastructure/repositories/usuarios.py`; router `api/routers/auth.py`; migración `0006`; y sus tests (unitarios, de integración, de API y del perfil `postgres`).
- **Código que se modifica**: `application/puertos.py` y `infrastructure/unidad_de_trabajo.py` (puertos nuevos), `infrastructure/configuracion.py` (`JWT_*`), `infrastructure/db/modelos.py` (`UsuarioModelo`), `seed_demo.py` y `cargar_seed.py` (usuario del seed), `api/errores.py` y `api/esquemas.py` (`401`), `main.py` (configuración de sesión en las tres fábricas), `docker-compose.yml`, `README.md` y `tests/postgres/test_migraciones.py` / `test_seed_y_api.py` (INF-1 y el entorno de la API sobre PostgreSQL).
- **API**: dos operaciones nuevas en `/auth`. Los contratos existentes no cambian.
- **Base**: tabla nueva `usuario` (migración `0006`).
- **Dependencias**: `PyJWT` y `bcrypt` en el grupo `app`.
- **Entorno**: variables `JWT_SECRET`, `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS` y `SEED_USUARIO_PASSWORD` (D197). El autor agrega las líneas a `.env.example` y a su `.env` (una regla de permisos impide que el agente toque esos archivos).
- **Documentación**: `README.md`. Al archivar, `CHANGES.md` marca C-06 y la KB registra las decisiones que el autor confirme (commit `docs(kb)` aparte, como en C-02 a C-05).
