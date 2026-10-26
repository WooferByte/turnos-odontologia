# Guía de prueba manual de C-09 y C-10

Para seguirla a mano, con el navegador, sin Docker. Cubre dos changes de la pantalla de usuarios:

- **C-09, gestión de usuarios**: listar, dar de alta, roles, desactivar y reactivar, y las reglas `RN-AU-05`, `RN-AU-06`, `RN-AU-07` y `RN-AU-08`.
- **C-10, contraseñas de usuarios**: restablecer la contraseña de otra persona, cambiar la propia desde «Mi contraseña», y las reglas `RN-AU-07`, `RN-AU-09` y `RN-AU-10`.

Cada paso dice qué hacer y **qué tenés que ver**. Si lo que ves no coincide, anotalo como se explica al final. Todos los datos son ficticios (emails `.test` y contraseñas de prueba); no uses ninguna contraseña real.

Tiempo estimado: 40 a 50 minutos.

---

## 0. Preparación

### 0.1 Levantar la demo (dos terminales)

Hace falta haber hecho antes la instalación del `README.md` (entorno de Python en `backend/` con `python -m pip install --group test`, y `npm ci` en `frontend/`). Los puertos `8000` y `5173` tienen que estar libres (si tenés Compose levantado, `docker compose stop`).

**Terminal 1, la API de demostración** (desde la raíz del repositorio, en PowerShell o cmd):

```
cd backend
.venv\Scripts\activate
python -m uvicorn app.main:crear_app_demo --factory
```

Tiene que decir `Uvicorn running on http://127.0.0.1:8000`.

**Terminal 2, la interfaz** (desde la raíz del repositorio):

```
cd frontend
npm run dev
```

Tiene que decir `Local: http://127.0.0.1:5173/`.

> **Importante: la demo guarda todo en memoria.** Cada vez que reiniciás la terminal 1 (Ctrl+C y volver a correrla) la demo vuelve al estado inicial: se pierden los usuarios que crees y las contraseñas que cambies. **Esta guía parte de la demo recién arrancada.** Si ya hiciste pasos y querés repetir, reiniciá la terminal 1 y empezá otra vez desde el principio.

### 0.2 Usuarios de partida

La demo trae solo estos dos usuarios. **La contraseña de los dos es `demo-consultorio-2026`.**

| Usuario | Roles | Lo llamamos |
|---|---|---|
| `odontologa@consultorio-demo.test` | Odontólogo y Dueño | «la odontóloga» |
| `recepcion@consultorio-demo.test` | Recepcionista | «la recepcionista» |

Los pasos de abajo necesitan dos usuarios más, que **creás vos desde la pantalla de usuarios** (en el paso 1.4 el dueño y en el 1.6 la colega). Su contraseña inicial, la que vos les ponés, es `clave-ficticia-2026`:

| Usuario | Roles | Lo llamamos |
|---|---|---|
| `dueno@consultorio-demo.test` | **solo** Dueño | «el dueño» |
| `colega@consultorio-demo.test` | **solo** Odontólogo | «la colega» |

### 0.3 Ventanas y sesiones

Vas a necesitar **varias sesiones abiertas a la vez**, cada una con un usuario distinto. La sesión del panel vive en la pestaña, así que:

- **Ventana A**: la odontóloga (una pestaña normal).
- **Ventana B**: la recepcionista, en una **ventana privada o de incógnito** nueva (Ctrl+Shift+N en Chrome y Edge, Ctrl+Shift+P en Firefox).
- **Ventana C**: una **segunda ventana privada** (o una pestaña nueva dentro de la privada, abierta escribiendo la dirección; **no uses «Duplicar pestaña»**, porque copia la sesión). Primero la usa el dueño; más adelante la reusás para una segunda sesión de la recepcionista y para la colega.

En todas, la dirección es **http://127.0.0.1:5173** (no uses `localhost`). Si una ventana te muestra algo raro porque quedó una sesión vieja, andá a `http://127.0.0.1:5173/ingresar`, y si hace falta «Cerrar sesión».

Qué es cada cosa de la pantalla: arriba hay una barra con **Prestaciones, Usuarios, Horario, Bloqueos, Mi contraseña** y «Cerrar sesión». «Usuarios» tiene la tabla y, a la derecha, un panel que se abre con «Nuevo usuario», «Editar» o «Restablecer contraseña». Los rechazos de la API se muestran con su código entre paréntesis, por ejemplo `(RN-AU-07)`.

### 0.4 Cómo iniciar sesión (se repite mucho)

Abrí `http://127.0.0.1:5173/ingresar`, escribí el email y la contraseña y pulsá «Ingresar». Entrás a «Panel del consultorio». Cuando una sesión se corta y volvés a ingresar, te deja en la pantalla donde estabas.

**Regla para ver un corte de sesión:** la sesión caída se nota recién cuando esa ventana pide algo al servidor. Por eso, en los pasos que dicen «pulsá X» para ver el corte, pulsá una pantalla de la barra **distinta de la que estás mirando**.

---

## 1. C-09: gestión de usuarios

### 1.1 Listar los usuarios (ventana A)

1. En la ventana A, ingresá con `odontologa@consultorio-demo.test` / `demo-consultorio-2026`.
2. Pulsá **Usuarios** en la barra (`/panel/usuarios`).

**Esperado:** el contador dice «2 usuarios registrados» y la tabla tiene dos filas, las dos «Activo»:

- `odontologa@consultorio-demo.test`, roles «Odontólogo» y «Dueño».
- `recepcion@consultorio-demo.test`, rol «Recepcionista».

Cada fila tiene los botones «Editar», «Restablecer contraseña» y «Desactivar». No hay botón de borrar.

### 1.2 Alta con una contraseña corta: `RN-AU-07`

1. Pulsá **Nuevo usuario**. Se abre un panel a la derecha («Nuevo usuario»).
2. Email: `dueno@consultorio-demo.test`. Contraseña inicial: `corta-123`. Marcá el rol **Dueño**. Pulsá **Guardar**.

**Esperado:** debajo de «Contraseña inicial», en rojo: «La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).». El panel sigue abierto con lo escrito y la tabla no cambia (2 usuarios).

### 1.3 Alta con un email repetido: `RN-AU-08`

1. Con el panel todavía abierto, cambiá el email a `recepcion@consultorio-demo.test` y la contraseña a `clave-ficticia-2026` (el rol Dueño queda marcado). Pulsá **Guardar**.

**Esperado:** debajo de «Email», en rojo: «Ya existe un usuario con ese email (RN-AU-08).». El panel sigue abierto y la tabla no cambia.

### 1.4 Alta del dueño (el usuario que necesita C-10)

1. Cambiá el email a `dueno@consultorio-demo.test` (la contraseña `clave-ficticia-2026` y el rol Dueño siguen). Pulsá **Guardar**.

**Esperado:** el panel se cierra, aparece una tercera fila `dueno@consultorio-demo.test` con el rol «Dueño», «Activo», y el contador dice «3 usuarios registrados». Si pulsás «Nuevo usuario» otra vez, los campos están vacíos (cerrá el panel con «Cancelar»).

### 1.5 Quitarse el rol de Odontólogo siendo la única: `RN-AU-06`

1. En la fila de la odontóloga pulsá **Editar**. Se abre «Editar usuario» con su email como texto, los roles marcados (Odontólogo y Dueño) y la nota «Quitar o asignar un rol vale desde la próxima acción del usuario, sin cerrar su sesión.». La fila se marca «Editando».
2. Desmarcá **Odontólogo** y pulsá **Guardar**.

**Esperado:** dentro del panel (que sigue abierto), un aviso «No se pudo completar» con «El consultorio no puede quedar sin un odontólogo activo y nadie puede desactivarse a sí mismo (RN-AU-06).». La fila de la odontóloga sigue con «Odontólogo» y «Dueño». Pulsá **Cancelar**.

### 1.6 Alta de la colega

1. **Nuevo usuario**: email `colega@consultorio-demo.test`, contraseña inicial `clave-ficticia-2026`, rol **Odontólogo** (solo ese). **Guardar**.

**Esperado:** el panel se cierra y la tabla tiene cuatro filas; la última es `colega@consultorio-demo.test` con «Odontólogo», «Activo». El contador dice «4 usuarios registrados».

### 1.7 Desactivarse a sí misma: `RN-AU-06` (aunque haya otra odontóloga)

1. En la fila de la odontóloga pulsá **Desactivar**.

**Esperado:** arriba de la tabla, un aviso «No se pudo completar» con «El consultorio no puede quedar sin un odontólogo activo y nadie puede desactivarse a sí mismo (RN-AU-06).». La odontóloga sigue «Activo» y su sesión sigue (aunque ahora hay otra odontóloga: nadie puede desactivarse a sí mismo).

### 1.8 Sumar y quitar roles

1. En la fila de la recepcionista pulsá **Editar**. Marcá **Dueño** (además de Recepcionista) y pulsá **Guardar**.
2. Esperado: el panel se cierra y la fila muestra los roles «Recepcionista» y «Dueño».
3. Pulsá **Editar** otra vez en la recepcionista, desmarcá **Dueño** y **Guardar**.
4. Esperado: la fila vuelve a mostrar solo «Recepcionista».

(Si en «Editar» pulsás «Guardar» sin cambiar nada, no pasa nada: el panel se cierra sin pedirle nada al servidor.)

### 1.9 El dueño puede ver, pero no modificar: `RN-AU-05` (ventana C)

1. En la ventana C ingresá con `dueno@consultorio-demo.test` / `clave-ficticia-2026` y pulsá **Usuarios**.

   **Esperado:** el dueño **ve** la tabla con los 4 usuarios.

2. En la fila de `colega@consultorio-demo.test` pulsá **Desactivar**.

**Esperado:** arriba de la tabla, un aviso «Acceso restringido» con «Tu usuario no tiene permiso para modificar usuarios (RN-AU-05).». La colega sigue «Activo» y el dueño **sigue dentro del panel** (no lo manda a ingresar). Dejá la ventana C así, con el dueño adentro: la usás en el paso 2.4.

### 1.10 La recepcionista no ve los usuarios: `RN-AU-05` (ventana B)

1. En la ventana B (privada), ingresá con `recepcion@consultorio-demo.test` / `demo-consultorio-2026`.
2. Pulsá **Usuarios**.

**Esperado:** en lugar de la tabla, un aviso «Acceso restringido» con «Tu usuario no tiene permiso para ver los usuarios (RN-AU-05).». Sigue con la sesión iniciada. **Dejá la ventana B abierta con la recepcionista adentro**, la usás en el paso siguiente.

### 1.11 Desactivar a un usuario y ver el corte de su sesión

1. En la **ventana A**, en la fila de la recepcionista pulsá **Desactivar**.

   **Esperado:** la fila queda atenuada, con «Inactivo» y el botón «Reactivar» (y «Editar» y «Restablecer contraseña» siguen). El contador no cambia.

2. En la **ventana B** (la recepcionista, que seguía adentro), pulsá **Prestaciones** en la barra.

   **Esperado:** la interfaz vuelve sola a `/ingresar` con el aviso «Tu sesión terminó. Iniciá sesión de nuevo.». (La sesión se cortó al instante, sin esperar a que venza.)

3. En la ventana B intentá ingresar con `recepcion@consultorio-demo.test` / `demo-consultorio-2026`.

   **Esperado:** «El email o la contraseña no son correctos.» (el mismo mensaje que con una contraseña equivocada: no revela que el usuario está desactivado).

### 1.12 Reactivar

1. En la **ventana A** pulsá **Reactivar** en la fila de la recepcionista.

   **Esperado:** la fila vuelve a «Activo», con «Desactivar».

2. En la **ventana B** ingresá otra vez con la recepcionista (`demo-consultorio-2026`).

   **Esperado:** entra al panel y te deja en «Prestaciones». **Dejá la ventana B abierta, con la recepcionista adentro.**

---

## 2. C-10: contraseñas de usuarios

Estado de partida: ventana A con la odontóloga, ventana B con la recepcionista (contraseña `demo-consultorio-2026`) y ventana C con el dueño.

### 2.1 Restablecer con una contraseña corta: `RN-AU-07` (ventana A)

1. En la ventana A, en «Usuarios», pulsá **Restablecer contraseña** en la fila de la recepcionista. Se abre el panel «Restablecer contraseña» con su email como texto, el campo «Contraseña nueva» con la ayuda «De 10 caracteres a 72 bytes.» y la nota «Al guardar se cierran todas las sesiones de este usuario.».
2. Escribí `corta-123` y pulsá **Guardar**.

**Esperado:** debajo del campo, en rojo: «La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).». El panel sigue abierto con lo escrito.

### 2.2 Restablecer bien

1. Cambiá el texto por `clave-nueva-2026` y pulsá **Guardar**.

**Esperado:** el panel se cierra y arriba de la tabla se ve, en verde, «Contraseña restablecida. Se cerraron las sesiones de recepcion@consultorio-demo.test.». Ninguna fila cambia. Si volvés a pulsar «Restablecer contraseña» en esa fila, el campo está **vacío** (la contraseña nunca queda en la pantalla).

Mientras el panel está abierto, ni **«Guardar» con el campo vacío**, ni **«Cancelar»**, ni la **X** de «Cerrar» cambian la contraseña: probalos (con el campo vacío no pasa nada; con algo escrito, «Cancelar» y la X cierran el panel y al reabrirlo el campo está vacío). Cerrá el panel con «Cancelar».

### 2.3 Restablecer la propia: `RN-AU-10` (ventana A)

1. En la fila de la **odontóloga** pulsá **Restablecer contraseña**, escribí `clave-nueva-2026` y **Guardar**.

**Esperado:** dentro del panel, que sigue abierto, el aviso «Tu propia contraseña se cambia desde «Mi contraseña» (RN-AU-10).». Su sesión sigue (comprobalo en el paso siguiente, pulsando «Prestaciones» y volviendo a «Usuarios»). Cerrá el panel con «Cancelar».

### 2.4 El dueño no puede restablecer: `RN-AU-05` (ventana C)

1. En la ventana C (el dueño, que quedó en «Usuarios»), pulsá **Restablecer contraseña** en la fila de la recepcionista, escribí `clave-nueva-2026` y **Guardar**.

**Esperado:** dentro del panel, que sigue abierto con lo escrito, el aviso «Acceso restringido» con «Tu usuario no tiene permiso para modificar usuarios (RN-AU-05).». El dueño **sigue dentro del panel**. (La contraseña de la recepcionista no cambió por esto: ya la había cambiado la odontóloga en el 2.2.) Cerrá el panel con «Cancelar».

### 2.5 La sesión de la recepcionista cae, y entra solo con la nueva (ventana B)

1. En la **ventana B** (la recepcionista, que sigue «adentro» desde el 1.12, mirando «Prestaciones») pulsá **Horario**. (Pulsá una pantalla *distinta* de la que estás mirando: si pulsás la misma, la pantalla no vuelve a pedir nada al servidor y no se entera de que la sesión cayó.)

   **Esperado:** vuelve a `/ingresar` con «Tu sesión terminó. Iniciá sesión de nuevo.».

2. Intentá ingresar con la contraseña **vieja**, `demo-consultorio-2026`.

   **Esperado:** «El email o la contraseña no son correctos.».

3. Ingresá con la **nueva**, `clave-nueva-2026`.

   **Esperado:** entra al panel. **Dejá la ventana B abierta con la recepcionista.**

### 2.6 Una segunda sesión de la recepcionista (ventana C)

1. En la ventana C pulsá **Cerrar sesión** (volvés a `/ingresar`) e ingresá con `recepcion@consultorio-demo.test` / `clave-nueva-2026`.

**Esperado:** entra al panel (puede abrirse en «Usuarios» con el aviso «Acceso restringido»: es normal, la recepcionista no ve esa tabla). Ahora la recepcionista tiene dos sesiones abiertas: B y C.

### 2.7 Cambiar la propia en «Mi contraseña» (ventana B)

1. En la ventana B pulsá **Mi contraseña** en la barra (`/panel/contrasena`). Esperado: tres campos, «Contraseña actual», «Contraseña nueva» (con «De 10 caracteres a 72 bytes.») y «Repetir contraseña nueva», y el botón «Cambiar contraseña».
2. **Repetición distinta.** Contraseña actual `clave-nueva-2026`, nueva `otra-clave-2026`, repetición `otra-clave-2027`. Pulsá **Cambiar contraseña**.

   **Esperado:** debajo de «Repetir contraseña nueva», «Las contraseñas nuevas no coinciden.». No se manda nada al servidor (si abrís las herramientas del navegador, pestaña Red, no aparece ninguna petición a `cambiar-contrasena`).

3. **Actual incorrecta: `RN-AU-09`.** Cambiá la actual por `no-es-la-actual-2026` y la repetición por `otra-clave-2026`. **Cambiar contraseña**.

   **Esperado:** debajo de «Contraseña actual», en rojo: «La contraseña actual no es correcta (RN-AU-09).». Sigue en el panel (no te manda a ingresar) y los campos conservan lo escrito.

4. **Nueva corta: `RN-AU-07`.** Actual `clave-nueva-2026`, nueva `corta-123` y repetición `corta-123`. **Cambiar contraseña**.

   **Esperado:** debajo de «Contraseña nueva», en rojo: «La contraseña debe tener de 10 caracteres a 72 bytes (RN-AU-07).».

5. **Bien.** Actual `clave-nueva-2026`, nueva `otra-clave-2026` y repetición `otra-clave-2026`. **Cambiar contraseña**.

   **Esperado:** los tres campos quedan vacíos y debajo de la tarjeta se ve, en verde, «Contraseña cambiada. Tus otras sesiones se cerraron.». Seguís dentro del panel.

(Con un campo vacío tampoco se manda nada.)

### 2.8 La sesión actual sigue y la otra cae

1. En la **ventana B** pulsá **Prestaciones**.

   **Esperado:** se ve la lista de prestaciones; no te manda a ingresar (la sesión recibió credenciales nuevas al cambiar).

2. En la ventana B recargá la página (F5).

   **Esperado:** seguís dentro del panel, sin el aviso de sesión terminada.

3. En la **ventana C** (la otra sesión de la recepcionista) pulsá **Prestaciones** (si C ya estaba mirando «Prestaciones», pulsá «Horario»).

   **Esperado:** vuelve a `/ingresar` con «Tu sesión terminó. Iniciá sesión de nuevo.».

4. En la ventana C ingresá con la contraseña **nueva** (`otra-clave-2026`): entra.

### 2.9 Todos los roles ven «Mi contraseña»

**Esperado:** la barra de la ventana A (odontóloga), de la B y C (recepcionista) tiene el enlace «Mi contraseña». El dueño también lo vio en los pasos 1.9 y 2.4.

### 2.10 Sesión que se corta mientras se cambia (opcional, usa a la colega)

1. En la ventana C pulsá **Cerrar sesión** e ingresá con `colega@consultorio-demo.test` / `clave-ficticia-2026`. Pulsá **Mi contraseña** y completá los tres campos: actual `clave-ficticia-2026`, nueva y repetición `colega-nueva-2026`. **No pulses el botón todavía.**
2. En la **ventana A**, en «Usuarios», **Restablecer contraseña** en la fila de la colega, con `clave-colega-2026`, **Guardar** (aviso verde de contraseña restablecida).
3. En la ventana C pulsá **Cambiar contraseña**.

**Esperado:** vuelve a `/ingresar` con «Tu sesión terminó. Iniciá sesión de nuevo.» (no el mensaje de conexión). La contraseña **no** quedó en `colega-nueva-2026`: ingresar con ella da «El email o la contraseña no son correctos.», y con `clave-colega-2026` (la que puso la odontóloga) entra.

---

## 3. Qué anotar si algo no coincide

Para cada paso que no dé lo esperado, escribí:

1. **El número del paso** (por ejemplo «2.7, punto 3»).
2. **Qué esperabas ver** (copiá el texto de esta guía) y **qué viste** (el texto exacto en pantalla, o una captura).
3. **Qué ventana y con qué usuario** estabas.
4. Si el problema es de la interfaz o de la API: abrí las herramientas del navegador (F12), pestaña **Red**, y anotá la petición (por ejemplo `POST /api/usuarios/2/restablecer-contrasena`), su **estado** (200, 204, 401, 403, 409, 422) y, en la pestaña «Respuesta», el campo `codigos`.
5. Si la terminal 1 muestra un error (una traza en rojo), copiá las últimas líneas.
6. Si la demo estaba recién arrancada o la habías usado antes (recordá que se resetea al reiniciar la terminal 1).

**No pegues** en ninguna nota una contraseña ni un token que no sean los ficticios de esta guía.

Con eso, el agente corrige el código o la guía antes de archivar el change.

## 4. Al terminar

- En las terminales 1 y 2, **Ctrl+C**.
- Cerrá las ventanas privadas.
- Si querés repetir la prueba, volvé a arrancar la terminal 1: la demo parte de cero.
