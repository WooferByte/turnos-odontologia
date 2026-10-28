// Pantalla de bloqueos (design B16): una carga al montar (bloqueos, profesionales y sillones en paralelo). El estado
// se deriva de lo que respondió la API; la pantalla no evalúa reglas, solo exige los campos obligatorios.
import { useEffect, useMemo, useRef, useState } from 'react'
import { EntradaRechazada, RecursoInexistente, SesionTerminada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { Aviso } from '../../shared/componentes/Aviso'
import { IconoInfo } from '../../shared/iconos/IconoInfo'
import { crearApiHorario, type Profesional } from '../horario/apiHorario'
import { crearApiBloqueos, type Bloqueo, type NuevoBloqueo, type Sillon, type TurnoAfectado } from './apiBloqueos'
import { FORMULARIO_VACIO, FormularioDeBloqueo, type ValoresDelFormulario } from './FormularioDeBloqueo'
import { aUtc } from '../../shared/horaDelConsultorio'
import { ListaDeBloqueos } from './ListaDeBloqueos'
import {
  MENSAJE_CARGANDO,
  MENSAJE_ELIMINADO,
  MENSAJE_FORMULARIO_INCOMPLETO,
  MENSAJE_NOTA_DE_BLOQUEOS,
  MENSAJE_RN_AG_17,
  MENSAJE_SIN_BLOQUEOS,
  MENSAJE_SIN_CONEXION,
  mensajeDeRechazo,
  subtituloDeBloqueos,
  tituloDelAviso,
  type Accion,
} from './mensajes'
import { TurnosAfectados } from './TurnosAfectados'

interface Lista {
  tipo: 'lista'
  zona: string
  bloqueos: readonly Bloqueo[]
  profesionales: readonly Profesional[]
  sillones: readonly Sillon[]
}

type Carga = { tipo: 'cargando' } | { tipo: 'sin-conexion' } | Lista

type AvisoDePantalla =
  | { tipo: 'creado'; turnos: readonly TurnoAfectado[] }
  | { tipo: 'eliminado' }
  | { tipo: 'error'; mensaje: string }

/** Orden de la API (`inicio`, `id`); sirve solo si la lista no se pudo volver a pedir tras un alta. */
function enOrden(bloqueos: readonly Bloqueo[]): Bloqueo[] {
  return [...bloqueos].sort((a, b) => Date.parse(a.inicio) - Date.parse(b.inicio) || a.id - b.id)
}

export function PaginaBloqueos() {
  const { pedidoDelPanel } = useSesionDelPanel()
  const api = useMemo(() => crearApiBloqueos(pedidoDelPanel), [pedidoDelPanel])
  const apiHorario = useMemo(() => crearApiHorario(pedidoDelPanel), [pedidoDelPanel])
  const [carga, setCarga] = useState<Carga>({ tipo: 'cargando' })
  const [recarga, setRecarga] = useState(0)
  const [valores, setValores] = useState<ValoresDelFormulario>(FORMULARIO_VACIO)
  const [creando, setCreando] = useState(false)
  const [eliminando, setEliminando] = useState<number | null>(null)
  const [aviso, setAviso] = useState<AvisoDePantalla | null>(null)
  const peticion = useRef(0)
  const creandoAhora = useRef(false)
  const eliminandoAhora = useRef(false)

  useEffect(() => {
    const mia = ++peticion.current
    const vigente = () => peticion.current === mia
    Promise.all([api.listarBloqueos(), apiHorario.listarProfesionales(), api.listarSillones()])
      .then(([lista, profesionales, sillones]) => {
        if (vigente()) {
          setCarga({ tipo: 'lista', zona: lista.zona_horaria, bloqueos: lista.bloqueos, profesionales, sillones })
        }
      })
      .catch((error: unknown) => {
        // Si la sesión terminó, el proveedor ya llevó al inicio de sesión: la pantalla no muestra nada más.
        if (vigente() && !(error instanceof SesionTerminada)) setCarga({ tipo: 'sin-conexion' })
      })
    return () => {
      peticion.current += 1
    }
  }, [api, apiHorario, recarga])

  function reintentar(): void {
    setAviso(null)
    setCarga({ tipo: 'cargando' })
    setRecarga((n) => n + 1)
  }

  function conLista(cambio: (lista: Lista) => Lista): void {
    setCarga((anterior) => (anterior.tipo === 'lista' ? cambio(anterior) : anterior))
  }

  /** Vuelve a pedir la lista de bloqueos (la API ya la ordena); si falla, la pantalla sigue con lo que tenía. */
  function pedirBloqueos(): void {
    api.listarBloqueos().then(
      (lista) => conLista((anterior) => ({ ...anterior, zona: lista.zona_horaria, bloqueos: lista.bloqueos })),
      () => undefined,
    )
  }

  /** El profesional o el sillón elegido ya no está: se vuelven a pedir las dos listas de recursos. */
  function pedirRecursos(): void {
    Promise.all([apiHorario.listarProfesionales(), api.listarSillones()]).then(
      ([profesionales, sillones]) => conLista((anterior) => ({ ...anterior, profesionales, sillones })),
      () => undefined,
    )
  }

  function cambiar(cambio: Partial<ValoresDelFormulario>): void {
    setValores((anterior) => ({ ...anterior, ...cambio }))
    setAviso((anterior) => (anterior?.tipo === 'error' ? null : anterior))
  }

  function mostrarRechazo(error: unknown, accion: Accion): void {
    setAviso({ tipo: 'error', mensaje: mensajeDeRechazo(error, accion) })
  }

  async function crear(lista: Lista): Promise<void> {
    if (creandoAhora.current) return
    const recurso = Number(valores.recurso)
    const sinRecurso = valores.alcance !== 'consultorio' && !puedeElegirse(lista, valores, recurso)
    if (sinRecurso || valores.desde === '' || valores.hasta === '' || valores.motivo.trim() === '') {
      setAviso({ tipo: 'error', mensaje: MENSAJE_FORMULARIO_INCOMPLETO })
      return
    }
    const nuevo: NuevoBloqueo = {
      inicio: aUtc(valores.desde, lista.zona),
      fin: aUtc(valores.hasta, lista.zona),
      motivo: valores.motivo,
      ...(valores.alcance === 'profesional' ? { profesional_id: recurso } : {}),
      ...(valores.alcance === 'sillon' ? { sillon_id: recurso } : {}),
    }
    creandoAhora.current = true
    setCreando(true)
    setAviso(null)
    try {
      const creado = await api.crearBloqueo(nuevo)
      setValores(FORMULARIO_VACIO)
      const { turnos_afectados: turnos, ...bloqueo } = creado
      setAviso({ tipo: 'creado', turnos })
      conLista((anterior) => ({ ...anterior, bloqueos: enOrden([...anterior.bloqueos, bloqueo]) }))
      pedirBloqueos()
    } catch (error: unknown) {
      if (error instanceof SesionTerminada) return
      mostrarRechazo(error, 'crear')
      if (error instanceof EntradaRechazada && error.codigos.includes('RN-GL-04')) pedirRecursos()
    } finally {
      creandoAhora.current = false
      setCreando(false)
    }
  }

  async function eliminar(id: number): Promise<void> {
    if (eliminandoAhora.current) return
    eliminandoAhora.current = true
    setEliminando(id)
    setAviso(null)
    try {
      await api.eliminarBloqueo(id)
      conLista((anterior) => ({ ...anterior, bloqueos: anterior.bloqueos.filter((b) => b.id !== id) }))
      setAviso({ tipo: 'eliminado' })
    } catch (error: unknown) {
      if (error instanceof SesionTerminada) return
      mostrarRechazo(error, 'eliminar')
      if (error instanceof RecursoInexistente) pedirBloqueos()
    } finally {
      eliminandoAhora.current = false
      setEliminando(null)
    }
  }

  const lista = carga.tipo === 'lista' ? carga : null
  const profesionalesActivos = lista?.profesionales.filter((p) => p.activo) ?? []
  const sillonesActivos = lista?.sillones.filter((s) => s.activo) ?? []
  const hastaInvalido = aviso?.tipo === 'error' && aviso.mensaje === MENSAJE_RN_AG_17
  // Un recurso que ya no está entre los activos se ve como «sin elegir» (derivado, no guardado).
  const valoresVistos =
    lista !== null && valores.recurso !== '' && !puedeElegirse(lista, valores, Number(valores.recurso))
      ? { ...valores, recurso: '' }
      : valores

  return (
    <section aria-labelledby="titulo-bloqueos">
      <div className="barra-de-pantalla">
        <div>
          <h1 id="titulo-bloqueos">Bloqueos</h1>
          {lista === null ? null : <p className="subtitulo-de-pantalla">{subtituloDeBloqueos(lista.zona)}</p>}
        </div>
      </div>
      <p className="nota-informativa nota-de-horario">
        <IconoInfo />
        {MENSAJE_NOTA_DE_BLOQUEOS}
      </p>
      {carga.tipo === 'cargando' ? <p>{MENSAJE_CARGANDO}</p> : null}
      {carga.tipo === 'sin-conexion' ? (
        <Aviso mensaje={MENSAJE_SIN_CONEXION} titulo={tituloDelAviso(MENSAJE_SIN_CONEXION)}>
          <button type="button" className="boton-secundario" onClick={reintentar}>
            Reintentar
          </button>
        </Aviso>
      ) : null}
      {lista === null ? null : (
        <div className="pantalla-de-bloqueos">
          <div className="columna-del-alta">
            <FormularioDeBloqueo
              valores={valoresVistos}
              profesionales={profesionalesActivos}
              sillones={sillonesActivos}
              enviando={creando}
              hastaInvalido={hastaInvalido}
              onCambiar={cambiar}
              onEnviar={() => void crear(lista)}
            />
            {aviso?.tipo === 'creado' ? <TurnosAfectados turnos={aviso.turnos} zonaHoraria={lista.zona} /> : null}
            {aviso?.tipo === 'eliminado' ? (
              <p role="status" className="aviso-exito">
                {MENSAJE_ELIMINADO}
              </p>
            ) : null}
            {aviso?.tipo === 'error' ? (
              <Aviso mensaje={aviso.mensaje} titulo={tituloDelAviso(aviso.mensaje)} />
            ) : null}
          </div>
          <section className="tarjeta" aria-labelledby="titulo-bloqueos-cargados">
            <div className="tarjeta-encabezado">
              <h2 id="titulo-bloqueos-cargados">Bloqueos cargados</h2>
            </div>
            {lista.bloqueos.length === 0 ? (
              <p className="sin-bloqueos">{MENSAJE_SIN_BLOQUEOS}</p>
            ) : (
              <ListaDeBloqueos
                bloqueos={lista.bloqueos}
                zonaHoraria={lista.zona}
                profesionales={lista.profesionales}
                sillones={lista.sillones}
                eliminando={eliminando}
                onEliminar={(id) => void eliminar(id)}
              />
            )}
          </section>
        </div>
      )}
    </section>
  )
}

/** El recurso elegido existe entre los activos del alcance elegido. */
function puedeElegirse(lista: Lista, valores: ValoresDelFormulario, recurso: number): boolean {
  if (valores.alcance === 'profesional') return lista.profesionales.some((p) => p.activo && p.id === recurso)
  if (valores.alcance === 'sillon') return lista.sillones.some((s) => s.activo && s.id === recurso)
  return false
}
