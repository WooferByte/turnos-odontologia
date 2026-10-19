// Pantalla de prestaciones (design T7): una sola petición al montar. El estado del listado se deriva de
// lo que respondió la API; la pantalla no evalúa reglas.
import { useEffect, useMemo, useState } from 'react'
import { SesionTerminada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { crearApiPrestaciones, type DatosDeAlta, type Prestacion } from './apiPrestaciones'
import {
  erroresDelPanel,
  MENSAJE_CARGANDO,
  MENSAJE_LISTA_VACIA,
  MENSAJE_SIN_CONEXION,
  SIN_ERRORES,
  type ErroresDelPanel,
} from './mensajes'
import { PanelDePrestacion } from './PanelDePrestacion'
import { TablaDePrestaciones } from './TablaDePrestaciones'

type Listado =
  | { tipo: 'cargando' }
  | { tipo: 'lista'; prestaciones: readonly Prestacion[] }
  | { tipo: 'sin-conexion' }

type Panel = { modo: 'cerrado' } | { modo: 'alta' }

export function PaginaPrestaciones() {
  const { pedidoDelPanel } = useSesionDelPanel()
  const api = useMemo(() => crearApiPrestaciones(pedidoDelPanel), [pedidoDelPanel])
  const [listado, setListado] = useState<Listado>({ tipo: 'cargando' })
  const [recarga, setRecarga] = useState(0)
  const [panel, setPanel] = useState<Panel>({ modo: 'cerrado' })
  const [guardando, setGuardando] = useState(false)
  const [errores, setErrores] = useState<ErroresDelPanel>(SIN_ERRORES)

  useEffect(() => {
    let vigente = true
    api.listarPrestaciones().then(
      (prestaciones) => {
        if (vigente) setListado({ tipo: 'lista', prestaciones })
      },
      (error: unknown) => {
        // Si la sesión terminó, el proveedor ya llevó al inicio de sesión: la pantalla no muestra nada más.
        if (vigente && !(error instanceof SesionTerminada)) setListado({ tipo: 'sin-conexion' })
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

  function abrirAlta(): void {
    setErrores(SIN_ERRORES)
    setPanel({ modo: 'alta' })
  }

  function cerrarPanel(): void {
    setErrores(SIN_ERRORES)
    setPanel({ modo: 'cerrado' })
  }

  async function guardarAlta(datos: DatosDeAlta): Promise<void> {
    setGuardando(true)
    setErrores(SIN_ERRORES)
    try {
      const nueva = await api.crearPrestacion(datos)
      setListado((anterior) =>
        anterior.tipo === 'lista' ? { tipo: 'lista', prestaciones: [...anterior.prestaciones, nueva] } : anterior,
      )
      setPanel({ modo: 'cerrado' })
    } catch (error: unknown) {
      if (!(error instanceof SesionTerminada)) setErrores(erroresDelPanel(error))
    } finally {
      setGuardando(false)
    }
  }

  return (
    <section aria-labelledby="titulo-prestaciones">
      <div className="barra-de-pantalla">
        <h1 id="titulo-prestaciones">Prestaciones</h1>
        <button type="button" className="boton-primario" onClick={abrirAlta}>
          Nueva prestación
        </button>
      </div>
      <div className="pantalla-con-panel">
        <div className="zona-de-tabla">
          {listado.tipo === 'cargando' ? <p>{MENSAJE_CARGANDO}</p> : null}
          {listado.tipo === 'sin-conexion' ? (
            <div role="alert" className="aviso aviso-error">
              <p>{MENSAJE_SIN_CONEXION}</p>
              <button type="button" className="boton-secundario" onClick={reintentar}>
                Reintentar
              </button>
            </div>
          ) : null}
          {listado.tipo === 'lista' && listado.prestaciones.length === 0 ? <p>{MENSAJE_LISTA_VACIA}</p> : null}
          {listado.tipo === 'lista' && listado.prestaciones.length > 0 ? (
            <TablaDePrestaciones prestaciones={listado.prestaciones} />
          ) : null}
        </div>
        {panel.modo === 'cerrado' ? null : (
          <PanelDePrestacion
            guardando={guardando}
            errores={errores}
            onGuardar={(datos) => void guardarAlta(datos)}
            onCancelar={cerrarPanel}
          />
        )}
      </div>
    </section>
  )
}
