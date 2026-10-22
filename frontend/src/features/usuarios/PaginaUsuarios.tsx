// Pantalla de usuarios (design U18): una sola petición al montar. El estado del listado se deriva de lo que
// respondió la API; la pantalla no evalúa reglas.
import { useEffect, useMemo, useState } from 'react'
import { PermisoInsuficiente, SesionTerminada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { Aviso } from '../../shared/componentes/Aviso'
import { crearApiUsuarios, type Usuario } from './apiUsuarios'
import {
  MENSAJE_CARGANDO,
  MENSAJE_SIN_CONEXION,
  MENSAJE_SIN_PERMISO_DE_LECTURA,
  SUBTITULO_DE_PANTALLA,
  textoDelContador,
  tituloDelAviso,
} from './mensajes'
import { TablaDeUsuarios } from './TablaDeUsuarios'

type Listado =
  | { tipo: 'cargando' }
  | { tipo: 'lista'; usuarios: readonly Usuario[] }
  | { tipo: 'sin-conexion' }
  | { tipo: 'sin-permiso' }

export function PaginaUsuarios() {
  const { pedidoDelPanel } = useSesionDelPanel()
  const api = useMemo(() => crearApiUsuarios(pedidoDelPanel), [pedidoDelPanel])
  const [listado, setListado] = useState<Listado>({ tipo: 'cargando' })
  const [recarga, setRecarga] = useState(0)

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

  return (
    <section aria-labelledby="titulo-usuarios">
      <div className="barra-de-pantalla">
        <div>
          <h1 id="titulo-usuarios">Usuarios</h1>
          <p className="subtitulo-de-pantalla">{SUBTITULO_DE_PANTALLA}</p>
        </div>
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
      </div>
    </section>
  )
}
