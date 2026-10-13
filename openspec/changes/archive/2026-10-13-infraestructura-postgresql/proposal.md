# Proposal: infraestructura-postgresql

Change **C-02** de `CHANGES.md`. Change técnico, sin historia de usuario (nota «Changes técnicos y frontend» de `knowledge-base/06_funcionalidades.md`, D100 y D105). Gobernanza **ALTO**: se propone y el autor revisa antes de escribir nada.

## Why

Después de C-01 el sistema solo vive en SQLite en memoria: el esquema se crea con `create_all`, los datos se pierden al reiniciar y dos peticiones simultáneas al mismo hueco pueden crear dos turnos, porque la validación de dominio no ve lo que otra transacción todavía no confirmó (RN-AG-10c; E11 de US-010 quedó fuera de C-01).

Va ahora, en el orden 2, por decisión del autor (D105, DD-15): empezar con migraciones cuando hay seis tablas evita rehacerlas sobre muchas, y todos los changes siguientes agregan tablas y columnas con migraciones. La reserva pública (US-020) depende de la garantía de concurrencia que este change deja probada (D85).

## What Changes

- **PostgreSQL como base de ejecución.** Un `docker-compose.yml` en la raíz con los servicios `api` y `postgres`, y un `backend/Dockerfile` para la API. Los datos persisten entre reinicios.
- **Esquema bajo migraciones (Alembic, DD-15).** Una migración inicial equivalente al esquema de C-01 (las seis tablas, sin columnas nuevas) y una segunda con la restricción de exclusión. Las dos son reversibles.
- **Restricción de exclusión (DD-04, D75).** Una por profesional y otra por sillón, sobre el intervalo semiabierto `[inicio, fin)` y solo para los estados activos. Se **agrega** a la validación de dominio de C-01, no la reemplaza.
- **Anti-solapamiento atómico (RN-AG-10c, E11).** Cuando la base rechaza un alta por la restricción, el que pierde recibe el mismo `409` de C-01, con `RN-AG-05`, `RN-AG-08` o los dos, y el turno contra el que chocó. El contrato HTTP de `POST /turnos` no cambia.
- **Perfil opcional de tests con PostgreSQL (D75).** Marcador de pytest `postgres`, excluido de la corrida por defecto, con su comando exacto en el README. Si PostgreSQL no está disponible, esos tests se omiten con un motivo visible; no fallan.
- **Variables de entorno.** Quedan fijados los nombres definitivos y se crea `.env.example` en la raíz, solo con valores de prueba.
- **Seed ficticio en PostgreSQL.** Los mismos datos e identificadores de la demo de C-01, con una carga que se puede repetir sin duplicar.
- **Dependencias.** Se agregan al archivo único `backend/pyproject.toml` (D116), con versión exacta: el driver sincrónico de PostgreSQL y Alembic. Las imágenes de Docker también van con versión exacta.
- **README.** Suma la sección de Docker Compose, el comando del perfil opcional, las variables de entorno y los límites que cambian. La sección de instalación y tests sin Docker se mantiene.

No hay cambios **BREAKING**: `POST /turnos` responde igual y la demo sin Docker (`crear_app_demo`) sigue funcionando.

### Escenarios

Cubre los cinco de la entrada C-02 de `CHANGES.md` (dentro del «3 a 6»):

| ID | Qué verifica | Dónde corre |
|---|---|---|
| INF-1 | Una base vacía migrada queda con el esquema de C-01 | Perfil `postgres` |
| INF-2 | La restricción rechaza en la base los solapamientos de E2 y E3 | Perfil `postgres` |
| INF-3 | La restricción acepta los casos de E5 y E6 | Perfil `postgres` |
| E11 | De dos reservas simultáneas del mismo hueco, una sola gana (RN-AG-10c) | Perfil `postgres` |
| INF-4 | La suite por defecto corre sin PostgreSQL ni Docker | Suite por defecto |

De US-010 cubre **E11**. No modifica E1 a E7 ni E12 (C-01, ya archivado): sus tests siguen en la suite por defecto, sin tocar. Siguen fuera E8 (test unitario de `Intervalo`, ya hecho), E9 (historial, C-03) y E10 (horario y bloqueos).

## Fuera de alcance

- **Cambios en la suite por defecto**: sigue en SQLite en memoria, con engine por test y `create_all` (DD-03). Solo se le agregan tests nuevos que tampoco necesitan PostgreSQL.
- **Redis, worker y tarea periódica** (C-31). El `docker-compose.yml` no trae `redis` ni `worker`.
- **Frontend** (empieza en la fase 3) y **autenticación** (`POST /turnos` sigue sin JWT, DD-14).
- **Tablas o columnas nuevas.** El esquema migrado es exactamente el de C-01. El historial (`EventoTurno`) es de C-03.
- **Endpoints nuevos**, incluidos los de lectura y uno de estado de salud.
- **Vencimiento de la seña frente a la restricción** (D92, RN-GL-05 (a)): no hay seña todavía; lo resuelve el change que la crea.
- **Reprogramar** (RN-AG-10b): la restricción ya lo soporta, pero el caso de uso es de otro change.
- **Despliegue público, copias de respaldo, roles de base con privilegios mínimos y pool de conexiones afinado**: es un entorno local con datos ficticios.
- **Sobreturnos y excepción de horario**: fuera de la v1.

## Capabilities

### New Capabilities

- `persistencia-postgresql`: la base de ejecución en PostgreSQL. Qué esquema deja una base migrada, qué garantiza la base por sí sola frente a turnos solapados y a reservas simultáneas, y qué necesita (y qué no) quien clona el repositorio para correr los tests. Aloja E11 e INF-1 a INF-4, y es donde los changes siguientes anotan las garantías que dependen de PostgreSQL.

### Modified Capabilities

Ninguna. `creacion-de-turnos` no cambia ningún requisito: sus escenarios E1 a E7 y E12 valen igual en SQLite y en PostgreSQL. E11 se aloja en la capability nueva porque es una garantía que solo existe con PostgreSQL (motivo y alternativa en `design.md`, decisión I1). Así el change toca una sola capability.

## Impact

- **Código nuevo**: `docker-compose.yml`, `.env.example` y `.dockerignore` (raíz); `backend/Dockerfile`, `backend/alembic.ini`, el directorio de migraciones dentro de `backend/app/infrastructure/db/`, la lectura de la configuración, el comando de carga del seed y los tests del perfil `postgres`.
- **Código que se modifica**: `backend/pyproject.toml` (dos dependencias y el marcador), `backend/app/infrastructure/db/motor.py`, `modelos.py` (convención de nombres de restricciones), `seed_demo.py`, el repositorio de agenda, `application/puertos.py`, `application/crear_turno.py` y `app/main.py` (una fábrica más). `backend/app/domain` y `backend/app/api` no se tocan.
- **API**: sin cambios de contrato.
- **Dependencias**: `psycopg[binary]` y `alembic` en el archivo único; imágenes `postgres` y `python` con versión exacta. Pins en `design.md`.
- **Documentación**: `README.md`. Al archivar, `CHANGES.md` marca C-02.
- **Quien clona el repositorio**: no cambia nada si no usa Docker. La instalación trae dos paquetes más, que no necesitan un servidor PostgreSQL para instalarse.
- **Base de conocimiento**: no se modifica en este change. Las contradicciones y huecos encontrados están listados en `design.md` para que el autor decida.
