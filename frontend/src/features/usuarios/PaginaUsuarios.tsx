// Pantalla de usuarios (design U18): una sola petición al montar. El estado del listado se deriva de lo que
// respondió la API; la pantalla no evalúa reglas.
import { useEffect, useMemo, useState } from 'react'
import { PermisoInsuficiente, RecursoInexistente, SesionTerminada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { Aviso } from '../../shared/componentes/Aviso'
import { AvisoDeExito } from '../../shared/componentes/AvisoDeExito'
import { IconoMas } from '../../shared/iconos/IconoMas'
import { crearApiContrasenas } from '../contrasenas/apiContrasenas'
import { avisoDeRestablecida, erroresDeRestablecimiento } from '../contrasenas/mensajes'
import { crearApiUsuarios, rolesCambiados, type DatosDeAltaDeUsuario, type Usuario } from './apiUsuarios'
import {
  avisoDeAccionDeFila,
  MENSAJE_CARGANDO,
  MENSAJE_SIN_CONEXION,
  MENSAJE_SIN_PERMISO_DE_LECTURA,
  MENSAJE_USUARIO_INEXISTENTE,
  SIN_ERRORES,
  SUBTITULO_DE_PANTALLA,
  textoDelContador,
  tituloDelAviso,
  erroresDelPanel,
  type ErroresDelPanel,
} from './mensajes'
import { PanelDeRestablecimiento, PanelDeUsuario } from './PanelDeUsuario'
import { TablaDeUsuarios } from './TablaDeUsuarios'

type Listado =
  | { tipo: 'cargando' }
  | { tipo: 'lista'; usuarios: readonly Usuario[] }
  | { tipo: 'sin-conexion' }
  | { tipo: 'sin-permiso' }

type Panel =
  | { modo: 'cerrado' }
  | { modo: 'alta' }
  | { modo: 'edicion'; usuario: Usuario }
  | { modo: 'restablecer'; usuario: Usuario }

const SIN_OCUPADOS: ReadonlySet<number> = new Set()

function conUsuarioNuevo(listado: Listado, nuevo: Usuario): Listado {
  return listado.tipo === 'lista' ? { tipo: 'lista', usuarios: [...listado.usuarios, nuevo] } : listado
}

function conUsuarioReemplazado(listado: Listado, nuevo: Usuario): Listado {
  return listado.tipo === 'lista'
    ? { tipo: 'lista', usuarios: listado.usuarios.map((u) => (u.id === nuevo.id ? nuevo : u)) }
    : listado
}

export function PaginaUsuarios() {
  const { pedidoDelPanel } = useSesionDelPanel()
  const api = useMemo(() => crearApiUsuarios(pedidoDelPanel), [pedidoDelPanel])
  const apiContrasenas = useMemo(() => crearApiContrasenas(pedidoDelPanel), [pedidoDelPanel])
  const [listado, setListado] = useState<Listado>({ tipo: 'cargando' })
  const [recarga, setRecarga] = useState(0)
  const [panel, setPanel] = useState<Panel>({ modo: 'cerrado' })
  const [guardando, setGuardando] = useState(false)
  const [errores, setErrores] = useState<ErroresDelPanel>(SIN_ERRORES)
  const [avisoDeTabla, setAvisoDeTabla] = useState<string | null>(null)
  const [exitoDeTabla, setExitoDeTabla] = useState<string | null>(null)
  const [ocupados, setOcupados] = useState<ReadonlySet<number>>(SIN_OCUPADOS)

  useEffect(() => {
    let vigente = true
    api.listarUsuarios().then(
      (usuarios) => {
        if (vigente) setListado({ tipo: 'lista', usuarios })
      },
      (error: unknown) => {
        // Si la sesión terminó, el proveedor ya llevó al inicio de sesión: la pantalla no muestra nada más.
        if (!vigente || error instanceof SesionTerminada) return
        setListado({ tipo: error instanceof PermisoInsuficiente ? 'sin-permiso' : 'sin-conexion' })
      },
    )
    return () => {
      vigente = false
    }
  }, [api, recarga])

  function reintentar(): void {
    setListado({ tipo: 'cargando' })
    setRecarga((n) => n + 1)
  }

  function abrirPanel(nuevo: Panel): void {
    setErrores(SIN_ERRORES)
    setAvisoDeTabla(null)
    setExitoDeTabla(null)
    setPanel(nuevo)
  }

  /** El usuario ya no existe (404): se cierra el panel, se avisa y se vuelve a pedir la lista. */
  function usuarioInexistente(): void {
    setPanel({ modo: 'cerrado' })
    setAvisoDeTabla(MENSAJE_USUARIO_INEXISTENTE)
    setRecarga((n) => n + 1)
  }

  async function restablecer(usuario: Usuario, contrasena: string): Promise<void> {
    setGuardando(true)
    setErrores(SIN_ERRORES)
    try {
      await apiContrasenas.restablecerContrasena(usuario.id, contrasena)
      setPanel({ modo: 'cerrado' })
      setExitoDeTabla(avisoDeRestablecida(usuario.email))
    } catch (error: unknown) {
      if (error instanceof RecursoInexistente) usuarioInexistente()
      else if (!(error instanceof SesionTerminada)) setErrores(erroresDeRestablecimiento(error))
    } finally {
      setGuardando(false)
    }
  }

  async function guardar(datos: DatosDeAltaDeUsuario): Promise<void> {
    if (panel.modo === 'cerrado') return
    if (panel.modo === 'edicion' && !rolesCambiados(panel.usuario.roles, datos.roles)) {
      abrirPanel({ modo: 'cerrado' })
      return
    }
    setGuardando(true)
    setErrores(SIN_ERRORES)
    try {
      if (panel.modo === 'edicion') {
        const editado = await api.editarUsuario(panel.usuario.id, { roles: datos.roles })
        setListado((anterior) => conUsuarioReemplazado(anterior, editado))
      } else {
        const nuevo = await api.crearUsuario(datos)
        setListado((anterior) => conUsuarioNuevo(anterior, nuevo))
      }
      setPanel({ modo: 'cerrado' })
    } catch (error: unknown) {
      if (error instanceof RecursoInexistente) usuarioInexistente()
      else if (!(error instanceof SesionTerminada)) setErrores(erroresDelPanel(error))
    } finally {
      setGuardando(false)
    }
  }

  async function cambiarActivo(usuario: Usuario): Promise<void> {
    setAvisoDeTabla(null)
    setExitoDeTabla(null)
    setOcupados((anteriores) => new Set(anteriores).add(usuario.id))
    try {
      const editado = await api.editarUsuario(usuario.id, { activo: !usuario.activo })
      setListado((anterior) => conUsuarioReemplazado(anterior, editado))
    } catch (error: unknown) {
      if (error instanceof RecursoInexistente) usuarioInexistente()
      else if (!(error instanceof SesionTerminada)) setAvisoDeTabla(avisoDeAccionDeFila(error))
    } finally {
      setOcupados((anteriores) => {
        const restantes = new Set(anteriores)
        restantes.delete(usuario.id)
        return restantes
      })
    }
  }

  return (
    <section aria-labelledby="titulo-usuarios">
      <div className="barra-de-pantalla">
        <div>
          <h1 id="titulo-usuarios">Usuarios</h1>
          <p className="subtitulo-de-pantalla">{SUBTITULO_DE_PANTALLA}</p>
        </div>
        {listado.tipo === 'lista' ? (
          <button type="button" className="boton-primario" onClick={() => abrirPanel({ modo: 'alta' })}>
            <IconoMas />
            Nuevo usuario
          </button>
        ) : null}
      </div>
      <div className="pantalla-con-panel">
        <div className="zona-de-tabla">
          {exitoDeTabla === null ? null : <AvisoDeExito mensaje={exitoDeTabla} />}
          {avisoDeTabla === null ? null : <Aviso mensaje={avisoDeTabla} titulo={tituloDelAviso(avisoDeTabla)} />}
          {listado.tipo === 'cargando' ? <p>{MENSAJE_CARGANDO}</p> : null}
          {listado.tipo === 'sin-permiso' ? (
            <Aviso
              mensaje={MENSAJE_SIN_PERMISO_DE_LECTURA}
              titulo={tituloDelAviso(MENSAJE_SIN_PERMISO_DE_LECTURA)}
            />
          ) : null}
          {listado.tipo === 'sin-conexion' ? (
            <Aviso mensaje={MENSAJE_SIN_CONEXION} titulo={tituloDelAviso(MENSAJE_SIN_CONEXION)}>
              <button type="button" className="boton-secundario" onClick={reintentar}>
                Reintentar
              </button>
            </Aviso>
          ) : null}
          {listado.tipo === 'lista' ? (
            <section className="tarjeta" aria-labelledby="titulo-listado">
              <div className="tarjeta-encabezado">
                <h2 id="titulo-listado">Listado general</h2>
                <span className="insignia-contador">{textoDelContador(listado.usuarios.length)}</span>
              </div>
              <TablaDeUsuarios
                usuarios={listado.usuarios}
                ocupadas={ocupados}
                editandoId={panel.modo === 'edicion' ? panel.usuario.id : null}
                onEditar={(usuario) => abrirPanel({ modo: 'edicion', usuario })}
                onRestablecer={(usuario) => abrirPanel({ modo: 'restablecer', usuario })}
                onCambiarActivo={(usuario) => void cambiarActivo(usuario)}
              />
            </section>
          ) : null}
        </div>
        {panel.modo === 'restablecer' ? (
          <PanelDeRestablecimiento
            key={`restablecer-${panel.usuario.id}`}
            usuario={panel.usuario}
            guardando={guardando}
            errores={errores}
            onGuardar={(contrasena) => void restablecer(panel.usuario, contrasena)}
            onCancelar={() => abrirPanel({ modo: 'cerrado' })}
          />
        ) : null}
        {panel.modo === 'cerrado' || panel.modo === 'restablecer' ? null : (
          <PanelDeUsuario
            key={panel.modo === 'edicion' ? panel.usuario.id : 'alta'}
            usuario={panel.modo === 'edicion' ? panel.usuario : null}
            guardando={guardando}
            errores={errores}
            onGuardar={(datos) => void guardar(datos)}
            onCancelar={() => abrirPanel({ modo: 'cerrado' })}
          />
        )}
      </div>
    </section>
  )
}
