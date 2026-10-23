// Pantalla de horario (design H15): una carga al montar (profesionales y después el horario del elegido). El estado
// se deriva de lo que respondió la API; la pantalla no evalúa reglas.
import { useEffect, useMemo, useRef, useState } from 'react'
import { SesionTerminada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { Aviso } from '../../shared/componentes/Aviso'
import { crearApiHorario, type HorarioDelProfesional, type Profesional } from './apiHorario'
import {
  etiquetaDelProfesional,
  MENSAJE_CARGANDO,
  MENSAJE_NOTA_DE_HORARIO,
  MENSAJE_SIN_CONEXION,
  MENSAJE_SIN_PROFESIONALES,
  subtituloDeHorario,
  tituloDelAviso,
} from './mensajes'
import { SemanaDeHorario } from './SemanaDeHorario'

type Carga =
  | { tipo: 'cargando' }
  | { tipo: 'sin-conexion' }
  | { tipo: 'sin-profesionales' }
  | { tipo: 'lista'; horario: HorarioDelProfesional }

/** El primer profesional activo o, si ninguno lo está, el primero de la lista (D267). */
function elegidoPorDefecto(profesionales: readonly Profesional[]): Profesional | undefined {
  return profesionales.find((p) => p.activo) ?? profesionales[0]
}

export function PaginaHorario() {
  const { pedidoDelPanel } = useSesionDelPanel()
  const api = useMemo(() => crearApiHorario(pedidoDelPanel), [pedidoDelPanel])
  const [carga, setCarga] = useState<Carga>({ tipo: 'cargando' })
  const [profesionales, setProfesionales] = useState<readonly Profesional[]>([])
  const [elegido, setElegido] = useState<number | null>(null)
  const [recarga, setRecarga] = useState(0)
  const peticion = useRef(0)

  useEffect(() => {
    const mia = ++peticion.current
    const vigente = () => peticion.current === mia
    api
      .listarProfesionales()
      .then(async (lista) => {
        const primero = elegidoPorDefecto(lista)
        if (primero === undefined) {
          if (vigente()) setCarga({ tipo: 'sin-profesionales' })
          return
        }
        const horario = await api.obtenerHorario(primero.id)
        if (!vigente()) return
        setProfesionales(lista)
        setElegido(primero.id)
        setCarga({ tipo: 'lista', horario })
      })
      .catch((error: unknown) => {
        // Si la sesión terminó, el proveedor ya llevó al inicio de sesión: la pantalla no muestra nada más.
        if (vigente() && !(error instanceof SesionTerminada)) setCarga({ tipo: 'sin-conexion' })
      })
    return () => {
      peticion.current += 1
    }
  }, [api, recarga])

  function reintentar(): void {
    setCarga({ tipo: 'cargando' })
    setRecarga((n) => n + 1)
  }

  function elegir(id: number): void {
    const mia = ++peticion.current
    setElegido(id)
    setCarga({ tipo: 'cargando' })
    api.obtenerHorario(id).then(
      (horario) => {
        if (peticion.current === mia) setCarga({ tipo: 'lista', horario })
      },
      (error: unknown) => {
        if (peticion.current === mia && !(error instanceof SesionTerminada)) setCarga({ tipo: 'sin-conexion' })
      },
    )
  }

  return (
    <section aria-labelledby="titulo-horario">
      <div className="barra-de-pantalla">
        <div>
          <h1 id="titulo-horario">Horario de atención</h1>
          {carga.tipo === 'lista' ? (
            <p className="subtitulo-de-pantalla">{subtituloDeHorario(carga.horario.zona_horaria)}</p>
          ) : null}
        </div>
        <div className="controles-de-horario">
          <div className="selector-de-profesional">
            <label htmlFor="selector-profesional">Profesional</label>
            <select
              id="selector-profesional"
              value={elegido ?? ''}
              onChange={(evento) => elegir(Number(evento.target.value))}
            >
              {profesionales.map((profesional) => (
                <option key={profesional.id} value={profesional.id}>
                  {etiquetaDelProfesional(profesional)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
      <p className="nota-informativa">{MENSAJE_NOTA_DE_HORARIO}</p>
      {carga.tipo === 'cargando' ? <p>{MENSAJE_CARGANDO}</p> : null}
      {carga.tipo === 'sin-profesionales' ? <p>{MENSAJE_SIN_PROFESIONALES}</p> : null}
      {carga.tipo === 'sin-conexion' ? (
        <Aviso mensaje={MENSAJE_SIN_CONEXION} titulo={tituloDelAviso(MENSAJE_SIN_CONEXION)}>
          <button type="button" className="boton-secundario" onClick={reintentar}>
            Reintentar
          </button>
        </Aviso>
      ) : null}
      {carga.tipo === 'lista' ? <SemanaDeHorario franjas={carga.horario.franjas} /> : null}
    </section>
  )
}
