# Guía de prueba manual de C-50

Para seguirla a mano, con el navegador, sin Docker. Cubre **C-50, usuario de la sesión**: el encabezado del panel muestra con qué usuario estás y con qué roles, a partir de la ruta nueva `GET /auth/yo`. Es el change que surgió de la prueba manual de C-09 y C-10, cuando no se distinguía de quién era cada ventana.

Cada paso dice qué hacer y **qué tenés que ver**. Si lo que ves no coincide, anotalo como se explica al final. Todos los datos son ficticios (emails `.test` y contraseñas de prueba); no uses ninguna contraseña real.

Tiempo estimado: 15 a 20 minutos.

---

## 0. Preparación

### 0.1 Levantar la demo (dos terminales)

Si todavía tenés abiertas las terminales de la prueba de C-09 y C-10, **cerralas con Ctrl+C**: la API de esa prueba corre el código anterior y no tiene la ruta nueva (sin ella el encabezado queda sin el indicador). Los puertos `8000` y `5173` tienen que quedar libres.

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

Tiene que decir `Local: http://127.0.0.1:5173/`. Si se queda en `bundling dependencies...`, ya está lista igual.

> La demo guarda todo en memoria: al reiniciar la terminal 1 vuelve al estado inicial. Esta guía parte de la demo recién arrancada.

### 0.2 Usuarios

La demo trae dos usuarios, los dos con la contraseña `demo-consultorio-2026`:

| Usuario | Roles |
|---|---|
| `odontologa@consultorio-demo.test` | Odontólogo y Dueño |
| `recepcion@consultorio-demo.test` | Recepcionista |

En el paso 6 creás uno más, `prueba@consultorio-demo.test`, con la contraseña `clave-ficticia-2026`.

### 0.3 Ventanas

- **Ventana A**: una ventana normal. En toda la guía está la **odontóloga**.
- **Ventana B**: una **ventana privada o de incógnito** (Ctrl+Shift+N en Chrome y Edge). Empieza con la **recepcionista**; en el paso 6 pasa a ser del usuario de prueba.

En las dos, la dirección es **http://127.0.0.1:5173** (no `localhost`). Esta vez no hace falta anotar quién está en cada ventana: **el encabezado lo dice**, y eso es justamente lo que se prueba.

Para ver las peticiones: F12 → pestaña **Red** (Network), con el filtro `auth`.

---

## 1. El encabezado muestra el usuario (ventana A, odontóloga)

1. En la ventana A abrí las herramientas (F12 → Red) e ingresá en `http://127.0.0.1:5173/ingresar` con `odontologa@consultorio-demo.test` / `demo-consultorio-2026`.

**Esperado:** a la derecha de la barra, antes de «Cerrar sesión», un círculo con un ícono de persona, el email `odontologa@consultorio-demo.test` y debajo, más chico, «Odontólogo · Dueño». En Red aparece `GET /api/auth/yo` con `200`, **dos veces seguidas**: es normal con `npm run dev` (React en desarrollo monta dos veces); la versión compilada lo pide una sola vez.

2. Pulsá en orden **Prestaciones**, **Usuarios**, **Horario**, **Bloqueos** y **Mi contraseña**.

**Esperado:** el indicador no cambia ni parpadea, y **no aparece ningún `GET /api/auth/yo` nuevo**: el usuario se pide una vez por entrada al panel.

3. Recargá la página (F5).

**Esperado:** primero `POST /api/auth/refresh`, después `GET /api/auth/yo`, y el indicador vuelve a aparecer con los mismos datos.

## 2. Dos usuarios a la vez (ventanas A y B)

1. En la ventana B (privada) ingresá con `recepcion@consultorio-demo.test` / `demo-consultorio-2026`.

**Esperado:** la ventana B muestra `recepcion@consultorio-demo.test` y «Recepcionista»; la ventana A sigue mostrando a la odontóloga con «Odontólogo · Dueño». Es el caso que originó el change: cada ventana dice de quién es.

## 3. Cambiar de usuario en la misma pestaña (ventana B)

1. En la ventana B pulsá **Cerrar sesión** e ingresá con la odontóloga (`odontologa@consultorio-demo.test` / `demo-consultorio-2026`).

**Esperado:** el encabezado muestra a la odontóloga; el email de la recepcionista no aparece en ningún momento.

2. Volvé a la recepcionista: **Cerrar sesión** e ingresá con `recepcion@consultorio-demo.test` / `demo-consultorio-2026`.

**Esperado:** otra vez `recepcion@consultorio-demo.test` y «Recepcionista».

## 4. Un rol nuevo se ve al recargar (límite conocido, D309)

1. En la ventana A (odontóloga), en **Usuarios**, pulsá **Editar** en la fila de la recepcionista, marcá **Dueño** y **Guardar**.
2. En la ventana B (recepcionista) pulsá otra pantalla de la barra.

**Esperado:** el indicador **sigue** diciendo «Recepcionista». Es el límite conocido: el usuario se pide una vez por entrada.

3. En la ventana B recargá (F5).

**Esperado:** ahora dice «Recepcionista · Dueño». Los roles van siempre en el orden fijo de la API: Odontólogo, Recepcionista, Dueño (D306).

4. En la ventana A, **Editar** la recepcionista otra vez, desmarcá **Dueño** y **Guardar** (para dejarla como estaba).

## 5. El orden de los roles es fijo

1. En la ventana A, en **Usuarios**, mirá la fila de la odontóloga: tiene «Odontólogo» y «Dueño».

**Esperado:** el encabezado de la ventana A dice «Odontólogo · Dueño», en el orden fijo, sin importar en qué orden se asignaron (lo prueba el test SES-1d asignándolos al revés).

## 6. La sesión cortada lleva a ingresar (ventanas A y B)

1. En la ventana A, en **Usuarios**, **Nuevo usuario**: email `prueba@consultorio-demo.test`, contraseña inicial `clave-ficticia-2026`, rol **Recepcionista**. **Guardar**.
2. En la ventana B pulsá **Cerrar sesión** e ingresá con `prueba@consultorio-demo.test` / `clave-ficticia-2026`.

**Esperado:** el encabezado de la ventana B muestra `prueba@consultorio-demo.test` y «Recepcionista».

3. En la ventana A pulsá **Desactivar** en la fila de `prueba@consultorio-demo.test`.
4. En la ventana B recargá la página (F5).

**Esperado:** vuelve a `/ingresar` con el aviso «Tu sesión terminó. Iniciá sesión de nuevo.» y sin ningún email en pantalla.

## 7. Pantalla angosta (opcional)

1. En la ventana A, F12 → ícono de dispositivo (Ctrl+Shift+M) → ancho **390**.

**Esperado:** la barra se acomoda en filas: arriba la marca, después los enlaces, y abajo el indicador con «Cerrar sesión» a la derecha. Si el email no entra, se corta con «…»; al dejar el mouse encima se ve completo. No hay barra de desplazamiento horizontal.

2. Probá un ancho de **1024**.

**A tener en cuenta:** entre unos 720 y 1100 px los enlaces de la barra pueden ocupar dos líneas para dejarle lugar al indicador. Se dejó así porque D311 fija el corte en filas recién debajo de 720 px; si te parece feo, es una decisión tuya para un ajuste posterior.

---

## 8. Qué anotar si algo no coincide

1. **El número del paso** (por ejemplo «4, punto 3»).
2. **Qué esperabas ver** (copiá el texto de esta guía) y **qué viste** (el texto exacto o una captura).
3. **Qué ventana** y qué usuario mostraba su encabezado.
4. De la pestaña **Red**: la petición (por ejemplo `GET /api/auth/yo`), su estado (200, 401, 403) y, si lo hay, el campo `codigos` de la respuesta.
5. Si la terminal 1 muestra un error (una traza en rojo), copiá las últimas líneas.

## 9. Al terminar

- En las terminales 1 y 2, **Ctrl+C**.
- Cerrá la ventana privada.
- Hay una carpeta que dejó el Apply, `C:\c50-clon` (una copia del repositorio para la verificación final); ya no se usa y la podés borrar.
