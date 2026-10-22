// Pantalla de usuarios (design U18): una sola petición al montar. El estado del listado se deriva de lo que
// respondió la API; la pantalla no evalúa reglas.
import { useEffect, useMemo, useState } from 'react'
import { PermisoInsuficiente, SesionTerminada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { Aviso } from '../../shared/componentes/Aviso'
import { IconoMas } from '../../shared/iconos/IconoMas'
import { crearApiUsuarios, type DatosDeAltaDeUsuario, type Usuario } from './apiUsuarios'
import {
  MENSAJE_CARGANDO,
  MENSAJE_SIN_CONEXION,
  MENSAJE_SIN_PERMISO_DE_LECTURA,
  SIN_ERRORES,
  SUBTITULO_DE_PANTALLA,
  textoDelContador,
  tituloDelAviso,
  erroresDelPanel,
  type ErroresDelPanel,
} from './mensajes'
import { PanelDeUsuario } from './PanelDeUsuario'
import { TablaDeUsuarios } from './TablaDeUsuarios'

type Listado =
  | { tipo: 'cargando' }
  | { tipo: 'lista'; usuarios: readonly Usuario[] }
  | { tipo: 'sin-conexion' }
  | { tipo: 'sin-permiso' }

type Panel = { modo: 'cerrado' } | { modo: 'alta' }

function conUsuarioNuevo(listado: Listado, nuevo: Usuario): Listado {
  return listado.tipo === 'lista' ? { tipo: 'lista', usuarios: [...listado.usuarios, nuevo] } : listado
}

export function PaginaUsuarios() {
  const { pedidoDelPanel } = useSesionDelPanel()
  const api = useMemo(() => crearApiUsuarios(pedidoDelPanel), [pedidoDelPanel])
  const [listado, setListado] = useState<Listado>({ tipo: 'cargando' })
  const [recarga, setRecarga] = useState(0)
  const [panel, setPanel] = useState<Panel>({ modo: 'cerrado' })
  const [guardando, setGuardando] = useState(false)
  const [errores, setErrores] = useState<ErroresDelPanel>(SIN_ERRORES)

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
    setPanel(nuevo)
  }

  async function guardar(datos: DatosDeAltaDeUsuario): Promise<void> {
    setGuardando(true)
    setErrores(SIN_ERRORES)
    try {
      const nuevo = await api.crearUsuario(datos)
      setListado((anterior) => conUsuarioNuevo(anterior, nuevo))
      setPanel({ modo: 'cerrado' })
    } catch (error: unknown) {
      if (!(error instanceof SesionTerminada)) setErrores(erroresDelPanel(error))
    } finally {
      setGuardando(false)
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
              <TablaDeUsuarios usuarios={listado.usuarios} />
            </section>
          ) : null}
        </div>
        {panel.modo === 'cerrado' ? null : (
          <PanelDeUsuario
            key="alta"
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
