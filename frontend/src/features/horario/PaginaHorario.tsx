// Pantalla de horario (design H15): una carga al montar (profesionales y después el horario del elegido). El estado
// se deriva de lo que respondió la API; la pantalla no evalúa reglas, solo exige las dos horas de cada franja.
import { useEffect, useMemo, useRef, useState } from 'react'
import { EntradaRechazada, RecursoInexistente, SesionTerminada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { Aviso } from '../../shared/componentes/Aviso'
import { IconoGuardar } from '../../shared/iconos/IconoGuardar'
import { IconoInfo } from '../../shared/iconos/IconoInfo'
import { crearApiHorario, type HorarioDelProfesional, type Profesional } from './apiHorario'
import {
  aEditables,
  aFranjas,
  clavesInformadas,
  enOrdenDelCuerpo,
  estaIncompleta,
  mismasFranjas,
  type FranjaEditable,
  type Marca,
} from './edicion'
import {
  etiquetaDelProfesional,
  MENSAJE_CARGANDO,
  MENSAJE_GUARDADO,
  MENSAJE_NOTA_DE_HORARIO,
  MENSAJE_SIN_CONEXION,
  MENSAJE_SIN_PROFESIONALES,
  mensajeDeRechazo,
  subtituloDeHorario,
  tituloDelAviso,
} from './mensajes'
import { SemanaDeHorario } from './SemanaDeHorario'

interface Lista {
  tipo: 'lista'
  /** Lo último que devolvió la API: con esto se compara para saber si hay cambios. */
  horario: HorarioDelProfesional
  editables: readonly FranjaEditable[]
  marcas: ReadonlyMap<number, Marca>
}

type Carga = { tipo: 'cargando' } | { tipo: 'sin-conexion' } | { tipo: 'sin-profesionales' } | Lista

type AvisoDePantalla = { tipo: 'guardado' } | { tipo: 'error'; mensaje: string }

const SIN_MARCAS: ReadonlyMap<number, Marca> = new Map()

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
  const [guardando, setGuardando] = useState(false)
  const [aviso, setAviso] = useState<AvisoDePantalla | null>(null)
  const peticion = useRef(0)
  const claves = useRef(0)
  const enVuelo = useRef(false)

  function conHorario(horario: HorarioDelProfesional): Lista {
    return {
      tipo: 'lista',
      horario,
      editables: aEditables(horario.franjas, () => ++claves.current),
      marcas: SIN_MARCAS,
    }
  }

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
        setCarga(conHorario(horario))
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
    setAviso(null)
    setCarga({ tipo: 'cargando' })
    setRecarga((n) => n + 1)
  }

  /** Cambiar de profesional descarta lo editado sin preguntar (design H15). */
  function elegir(id: number): void {
    const mia = ++peticion.current
    setAviso(null)
    setElegido(id)
    setCarga({ tipo: 'cargando' })
    api.obtenerHorario(id).then(
      (horario) => {
        if (peticion.current === mia) setCarga(conHorario(horario))
      },
      (error: unknown) => {
        if (peticion.current === mia && !(error instanceof SesionTerminada)) setCarga({ tipo: 'sin-conexion' })
      },
    )
  }

  function editar(cambio: (lista: Lista) => Lista): void {
    setAviso(null)
    setCarga((anterior) => (anterior.tipo === 'lista' ? cambio(anterior) : anterior))
  }

  function sinMarca(marcas: ReadonlyMap<number, Marca>, clave: number): ReadonlyMap<number, Marca> {
    const restantes = new Map(marcas)
    restantes.delete(clave)
    return restantes
  }

  function agregar(dia: number): void {
    const nueva: FranjaEditable = { clave: ++claves.current, dia_semana: dia, inicio: '', fin: '' }
    editar((lista) => ({ ...lista, editables: [...lista.editables, nueva] }))
  }

  function quitar(clave: number): void {
    editar((lista) => ({
      ...lista,
      editables: lista.editables.filter((f) => f.clave !== clave),
      marcas: sinMarca(lista.marcas, clave),
    }))
  }

  function cambiar(clave: number, campo: 'inicio' | 'fin', valor: string): void {
    editar((lista) => ({
      ...lista,
      editables: lista.editables.map((f) => (f.clave === clave ? { ...f, [campo]: valor } : f)),
      marcas: sinMarca(lista.marcas, clave),
    }))
  }

  /** El profesional ya no existe (404): se avisa y se vuelve a pedir la lista de profesionales. */
  function profesionalInexistente(mensaje: string): void {
    setAviso({ tipo: 'error', mensaje })
    setCarga({ tipo: 'cargando' })
    setRecarga((n) => n + 1)
  }

  async function guardar(): Promise<void> {
    if (carga.tipo !== 'lista' || elegido === null || enVuelo.current) return
    setAviso(null)
    const incompletas = new Map<number, Marca>(
      carga.editables.filter(estaIncompleta).map((f) => [f.clave, 'incompleta']),
    )
    if (incompletas.size > 0) {
      setCarga({ ...carga, marcas: incompletas })
      return
    }
    const enviadas = enOrdenDelCuerpo(carga.editables)
    const cuerpo = aFranjas(enviadas)
    if (mismasFranjas(cuerpo, carga.horario.franjas)) return
    enVuelo.current = true
    setGuardando(true)
    setCarga({ ...carga, marcas: SIN_MARCAS })
    try {
      const guardado = await api.reemplazarHorario(elegido, cuerpo)
      setCarga(conHorario(guardado))
      setAviso({ tipo: 'guardado' })
    } catch (error: unknown) {
      if (error instanceof SesionTerminada) return
      const mensaje = mensajeDeRechazo(error)
      if (error instanceof RecursoInexistente) {
        profesionalInexistente(mensaje)
        return
      }
      const informadas = error instanceof EntradaRechazada ? clavesInformadas(error.errores, enviadas) : []
      if (informadas.length > 0) {
        const marcas = new Map<number, Marca>(informadas.map((clave) => [clave, 'invalida']))
        setCarga((anterior) => (anterior.tipo === 'lista' ? { ...anterior, marcas } : anterior))
      } else {
        setAviso({ tipo: 'error', mensaje })
      }
    } finally {
      enVuelo.current = false
      setGuardando(false)
    }
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
              disabled={guardando}
              onChange={(evento) => elegir(Number(evento.target.value))}
            >
              {profesionales.map((profesional) => (
                <option key={profesional.id} value={profesional.id}>
                  {etiquetaDelProfesional(profesional)}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            className="boton-primario"
            disabled={guardando || carga.tipo !== 'lista'}
            onClick={() => void guardar()}
          >
            <IconoGuardar />
            Guardar horario
          </button>
        </div>
      </div>
      <p className="nota-informativa nota-de-horario">
        <IconoInfo />
        {MENSAJE_NOTA_DE_HORARIO}
      </p>
      {aviso?.tipo === 'guardado' ? (
        <p role="status" className="aviso-exito">
          {MENSAJE_GUARDADO}
        </p>
      ) : null}
      {aviso?.tipo === 'error' ? <Aviso mensaje={aviso.mensaje} titulo={tituloDelAviso(aviso.mensaje)} /> : null}
      {carga.tipo === 'cargando' ? <p>{MENSAJE_CARGANDO}</p> : null}
      {carga.tipo === 'sin-profesionales' ? <p>{MENSAJE_SIN_PROFESIONALES}</p> : null}
      {carga.tipo === 'sin-conexion' ? (
        <Aviso mensaje={MENSAJE_SIN_CONEXION} titulo={tituloDelAviso(MENSAJE_SIN_CONEXION)}>
          <button type="button" className="boton-secundario" onClick={reintentar}>
            Reintentar
          </button>
        </Aviso>
      ) : null}
      {carga.tipo === 'lista' ? (
        <section className="tarjeta" aria-labelledby="titulo-semana">
          <div className="tarjeta-encabezado">
            <h2 id="titulo-semana">Semana</h2>
          </div>
          <SemanaDeHorario
            editables={carga.editables}
            marcas={carga.marcas}
            onAgregar={agregar}
            onQuitar={quitar}
            onCambiar={cambiar}
          />
        </section>
      ) : null}
    </section>
  )
}
