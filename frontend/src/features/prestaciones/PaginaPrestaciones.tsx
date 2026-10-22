// Pantalla de prestaciones (design T7): una sola petición al montar. El estado del listado se deriva de
// lo que respondió la API; la pantalla no evalúa reglas.
import { useEffect, useMemo, useState } from 'react'
import { RecursoInexistente, SesionTerminada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { cambiosEntre, crearApiPrestaciones, type DatosDeAlta, type Prestacion } from './apiPrestaciones'
import {
  avisoDeAccionDeFila,
  erroresDelPanel,
  MENSAJE_CARGANDO,
  MENSAJE_LISTA_VACIA,
  MENSAJE_PRESTACION_INEXISTENTE,
  MENSAJE_SIN_CONEXION,
  SIN_ERRORES,
  SUBTITULO_DE_PANTALLA,
  textoDelContador,
  tituloDelAviso,
  type ErroresDelPanel,
} from './mensajes'
import { Aviso } from '../../shared/componentes/Aviso'
import { IconoMas } from '../../shared/iconos/IconoMas'
import { PanelDePrestacion } from './PanelDePrestacion'
import { TablaDePrestaciones } from './TablaDePrestaciones'

type Listado =
  | { tipo: 'cargando' }
  | { tipo: 'lista'; prestaciones: readonly Prestacion[] }
  | { tipo: 'sin-conexion' }

type Panel = { modo: 'cerrado' } | { modo: 'alta' } | { modo: 'edicion'; prestacion: Prestacion }

const SIN_OCUPADAS: ReadonlySet<number> = new Set()

function conPrestacionNueva(listado: Listado, nueva: Prestacion): Listado {
  return listado.tipo === 'lista' ? { tipo: 'lista', prestaciones: [...listado.prestaciones, nueva] } : listado
}

function conPrestacionReemplazada(listado: Listado, nueva: Prestacion): Listado {
  return listado.tipo === 'lista'
    ? { tipo: 'lista', prestaciones: listado.prestaciones.map((p) => (p.id === nueva.id ? nueva : p)) }
    : listado
}

export function PaginaPrestaciones() {
  const { pedidoDelPanel } = useSesionDelPanel()
  const api = useMemo(() => crearApiPrestaciones(pedidoDelPanel), [pedidoDelPanel])
  const [listado, setListado] = useState<Listado>({ tipo: 'cargando' })
  const [recarga, setRecarga] = useState(0)
  const [panel, setPanel] = useState<Panel>({ modo: 'cerrado' })
  const [guardando, setGuardando] = useState(false)
  const [errores, setErrores] = useState<ErroresDelPanel>(SIN_ERRORES)
  const [avisoDeTabla, setAvisoDeTabla] = useState<string | null>(null)
  const [ocupadas, setOcupadas] = useState<ReadonlySet<number>>(SIN_OCUPADAS)

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

  function abrirPanel(nuevo: Panel): void {
    setErrores(SIN_ERRORES)
    setAvisoDeTabla(null)
    setPanel(nuevo)
  }

  /** La prestación ya no existe (404): se cierra el panel, se avisa y se vuelve a pedir la lista. */
  function prestacionInexistente(): void {
    setPanel({ modo: 'cerrado' })
    setAvisoDeTabla(MENSAJE_PRESTACION_INEXISTENTE)
    setRecarga((n) => n + 1)
  }

  async function guardar(datos: DatosDeAlta): Promise<void> {
    if (panel.modo === 'cerrado') return
    const cambios =
      panel.modo === 'edicion' ? cambiosEntre(panel.prestacion, { ...datos, activa: panel.prestacion.activa }) : null
    if (cambios !== null && Object.keys(cambios).length === 0) {
      abrirPanel({ modo: 'cerrado' })
      return
    }
    setGuardando(true)
    setErrores(SIN_ERRORES)
    try {
      if (panel.modo === 'edicion' && cambios !== null) {
        const editada = await api.editarPrestacion(panel.prestacion.id, cambios)
        setListado((anterior) => conPrestacionReemplazada(anterior, editada))
      } else {
        const nueva = await api.crearPrestacion(datos)
        setListado((anterior) => conPrestacionNueva(anterior, nueva))
      }
      setPanel({ modo: 'cerrado' })
    } catch (error: unknown) {
      if (error instanceof RecursoInexistente) prestacionInexistente()
      else if (!(error instanceof SesionTerminada)) setErrores(erroresDelPanel(error))
    } finally {
      setGuardando(false)
    }
  }

  async function cambiarActiva(prestacion: Prestacion): Promise<void> {
    setAvisoDeTabla(null)
    setOcupadas((anteriores) => new Set(anteriores).add(prestacion.id))
    try {
      const editada = await api.editarPrestacion(prestacion.id, { activa: !prestacion.activa })
      setListado((anterior) => conPrestacionReemplazada(anterior, editada))
    } catch (error: unknown) {
      if (error instanceof RecursoInexistente) prestacionInexistente()
      else if (!(error instanceof SesionTerminada)) setAvisoDeTabla(avisoDeAccionDeFila(error))
    } finally {
      setOcupadas((anteriores) => {
        const restantes = new Set(anteriores)
        restantes.delete(prestacion.id)
        return restantes
      })
    }
  }

  return (
    <section aria-labelledby="titulo-prestaciones">
      <div className="barra-de-pantalla">
        <div>
          <h1 id="titulo-prestaciones">Prestaciones</h1>
          <p className="subtitulo-de-pantalla">{SUBTITULO_DE_PANTALLA}</p>
        </div>
        <button type="button" className="boton-primario" onClick={() => abrirPanel({ modo: 'alta' })}>
          <IconoMas />
          Nueva prestación
        </button>
      </div>
      <div className="pantalla-con-panel">
        <div className="zona-de-tabla">
          {avisoDeTabla === null ? null : <Aviso mensaje={avisoDeTabla} titulo={tituloDelAviso(avisoDeTabla)} />}
          {listado.tipo === 'cargando' ? <p>{MENSAJE_CARGANDO}</p> : null}
          {listado.tipo === 'sin-conexion' ? (
            <Aviso mensaje={MENSAJE_SIN_CONEXION} titulo={tituloDelAviso(MENSAJE_SIN_CONEXION)}>
              <button type="button" className="boton-secundario" onClick={reintentar}>
                Reintentar
              </button>
            </Aviso>
          ) : null}
          {listado.tipo === 'lista' && listado.prestaciones.length === 0 ? <p>{MENSAJE_LISTA_VACIA}</p> : null}
          {listado.tipo === 'lista' && listado.prestaciones.length > 0 ? (
            <section className="tarjeta" aria-labelledby="titulo-listado">
              <div className="tarjeta-encabezado">
                <h2 id="titulo-listado">Listado general</h2>
                <span className="insignia-contador">{textoDelContador(listado.prestaciones.length)}</span>
              </div>
              <TablaDePrestaciones
                prestaciones={listado.prestaciones}
                ocupadas={ocupadas}
                editandoId={panel.modo === 'edicion' ? panel.prestacion.id : null}
                onEditar={(prestacion) => abrirPanel({ modo: 'edicion', prestacion })}
                onCambiarActiva={(prestacion) => void cambiarActiva(prestacion)}
              />
            </section>
          ) : null}
        </div>
        {panel.modo === 'cerrado' ? null : (
          <PanelDePrestacion
            key={panel.modo === 'edicion' ? panel.prestacion.id : 'alta'}
            prestacion={panel.modo === 'edicion' ? panel.prestacion : null}
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
