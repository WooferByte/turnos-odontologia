// Pantalla de la agenda del día (design A13): un pedido por cambio de día, con una bandera de vigencia por pedido
// para que solo se muestre la respuesta del último. El estado se deriva de lo que respondió la API; la pantalla
// no evalúa reglas.
import { useEffect, useMemo, useRef, useState } from 'react'
import { EntradaRechazada, PermisoInsuficiente, SesionTerminada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { Aviso } from '../../shared/componentes/Aviso'
import { AvisoDeExito } from '../../shared/componentes/AvisoDeExito'
import { fechaLocal } from '../../shared/horaDelConsultorio'
import { IconoFlecha } from '../../shared/iconos/IconoFlecha'
import { IconoMas } from '../../shared/iconos/IconoMas'
import type { Prestacion } from '../prestaciones/apiPrestaciones'
import {
  crearApiAgenda,
  type EstadoDeAsistencia,
  type EstadoDeCancelacion,
  type NuevoTurno,
  type ReprogramacionDeTurno,
  type TurnoDeLaAgenda,
} from './apiAgenda'
import {
  MENSAJE_ASISTENCIA_REGISTRADA,
  MENSAJE_CARGANDO,
  MENSAJE_SIN_CONEXION,
  MENSAJE_SIN_PERMISO_PARA_VER,
  MENSAJE_SIN_TURNOS,
  MENSAJE_TURNO_CANCELADO,
  MENSAJE_TURNO_CREADO,
  MENSAJE_TURNO_REPROGRAMADO,
  diaCompacto,
  mensajeDeCancelacion,
  mensajeDeCreacion,
  mensajeDeReprogramacion,
  nombreDelDia,
  subtituloDeAgenda,
  sumarDias,
  textoDelContador,
  tituloDelAviso,
} from './mensajes'
import { PanelHistorial } from '../historial/PanelHistorial'
import { PanelAsistencia } from './PanelAsistencia'
import { PanelCancelar } from './PanelCancelar'
import { PanelNuevoTurno } from './PanelNuevoTurno'
import { PanelReprogramar } from './PanelReprogramar'
import { TablaDeTurnos } from './TablaDeTurnos'

type Carga = { tipo: 'cargando' } | { tipo: 'sin-conexion' } | { tipo: 'sin-permiso' } | { tipo: 'dia' }

/** Un solo panel lateral a la vez (design G2). */
type Panel =
  | { tipo: 'ninguno' }
  | { tipo: 'nuevo-turno' }
  | { tipo: 'historial'; turno: TurnoDeLaAgenda }
  | { tipo: 'reprogramar'; turno: TurnoDeLaAgenda }
  | { tipo: 'cancelar'; turno: TurnoDeLaAgenda }
  | { tipo: 'asistencia'; turno: TurnoDeLaAgenda }

const SIN_PANEL: Panel = { tipo: 'ninguno' }

interface Dia {
  fecha: string
  zona: string
  turnos: readonly TurnoDeLaAgenda[]
}

interface Pedido {
  /** Sin `fecha`, la API devuelve el día de hoy del consultorio. */
  fecha: string | undefined
  /** Distingue dos pedidos iguales seguidos («Reintentar», «Hoy» estando en hoy). */
  numero: number
}

export function PaginaAgenda() {
  const { pedidoDelPanel } = useSesionDelPanel()
  const api = useMemo(() => crearApiAgenda(pedidoDelPanel), [pedidoDelPanel])
  const [pedido, setPedido] = useState<Pedido>({ fecha: undefined, numero: 0 })
  const [carga, setCarga] = useState<Carga>({ tipo: 'cargando' })
  const [dia, setDia] = useState<Dia | null>(null)
  const [panel, setPanel] = useState<Panel>(SIN_PANEL)
  const [prestaciones, setPrestaciones] = useState<readonly Prestacion[] | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [errorDelPanel, setErrorDelPanel] = useState<string | null>(null)
  /** El aviso de éxito de la última acción («Turno creado.», «Turno reprogramado.»); `null` si no hay. */
  const [exito, setExito] = useState<string | null>(null)
  const enCurso = useRef(false)
  const pedidoDePrestaciones = useRef(0)
  const zonaDeTabla = useRef<HTMLDivElement>(null)
  /** El botón de la fila que recupera el foco cuando se cierra su panel (design G9, M12). */
  const focoAlCerrar = useRef<string | null>(null)

  useEffect(() => {
    let vigente = true
    api.obtenerAgenda(pedido.fecha).then(
      (agenda) => {
        if (!vigente) return
        setDia({ fecha: agenda.fecha, zona: agenda.zona_horaria, turnos: agenda.turnos })
        setCarga({ tipo: 'dia' })
      },
      (error: unknown) => {
        // Si la sesión terminó, el proveedor ya llevó al inicio de sesión: la pantalla no muestra nada más.
        if (!vigente || error instanceof SesionTerminada) return
        setCarga({ tipo: error instanceof PermisoInsuficiente ? 'sin-permiso' : 'sin-conexion' })
      },
    )
    return () => {
      vigente = false
    }
  }, [api, pedido])

  useEffect(() => {
    if (panel.tipo !== 'ninguno' || focoAlCerrar.current === null) return
    const boton = zonaDeTabla.current?.querySelector<HTMLElement>(focoAlCerrar.current)
    focoAlCerrar.current = null
    boton?.focus()
  }, [panel])

  function pedirDia(fecha: string | undefined): void {
    setCarga({ tipo: 'cargando' })
    setPedido((anterior) => ({ fecha, numero: anterior.numero + 1 }))
  }

  /** Cambio de día pedido por la persona: el aviso de éxito ya no corresponde. */
  function ir(fecha: string | undefined): void {
    setExito(null)
    // El turno del historial, de la reprogramación o de la cancelación ya no está a la vista: se cierra sin pedir nada.
    setPanel((actual) => (actual.tipo === 'nuevo-turno' || actual.tipo === 'ninguno' ? actual : SIN_PANEL))
    pedirDia(fecha)
  }

  /** Las prestaciones activas se piden al abrir el panel (no en cascada con la agenda) y cuando una referencia falló. */
  function pedirPrestaciones(): void {
    const mio = ++pedidoDePrestaciones.current
    api.obtenerPrestacionesActivas().then(
      (activas) => {
        if (pedidoDePrestaciones.current === mio) setPrestaciones(activas)
      },
      (error: unknown) => {
        if (pedidoDePrestaciones.current !== mio || error instanceof SesionTerminada) return
        setErrorDelPanel(mensajeDeCreacion(error))
      },
    )
  }

  function abrirPanel(): void {
    setErrorDelPanel(null)
    setPrestaciones(null)
    setPanel({ tipo: 'nuevo-turno' })
    pedirPrestaciones()
  }

  function verHistorial(turno: TurnoDeLaAgenda): void {
    pedidoDePrestaciones.current += 1
    setPanel({ tipo: 'historial', turno })
  }

  function cerrarHistorial(turno: TurnoDeLaAgenda): void {
    focoAlCerrar.current = `[data-turno-id="${turno.id}"]`
    setPanel(SIN_PANEL)
  }

  function abrirReprogramar(turno: TurnoDeLaAgenda): void {
    pedidoDePrestaciones.current += 1
    setErrorDelPanel(null)
    setPanel({ tipo: 'reprogramar', turno })
  }

  function cerrarReprogramar(turno: TurnoDeLaAgenda): void {
    focoAlCerrar.current = `[data-reprogramar-id="${turno.id}"]`
    setPanel(SIN_PANEL)
  }

  function abrirCancelar(turno: TurnoDeLaAgenda): void {
    pedidoDePrestaciones.current += 1
    setErrorDelPanel(null)
    setPanel({ tipo: 'cancelar', turno })
  }

  function cerrarCancelar(turno: TurnoDeLaAgenda): void {
    focoAlCerrar.current = `[data-cancelar-id="${turno.id}"]`
    setPanel(SIN_PANEL)
  }

  function abrirAsistencia(turno: TurnoDeLaAgenda): void {
    pedidoDePrestaciones.current += 1
    setErrorDelPanel(null)
    setPanel({ tipo: 'asistencia', turno })
  }

  function cerrarAsistencia(turno: TurnoDeLaAgenda): void {
    focoAlCerrar.current = `[data-asistencia-id="${turno.id}"]`
    setPanel(SIN_PANEL)
  }

  function cerrarPanel(): void {
    pedidoDePrestaciones.current += 1
    setPanel(SIN_PANEL)
  }

  async function crear(nuevo: NuevoTurno, zona: string): Promise<void> {
    if (enCurso.current) return
    enCurso.current = true
    setEnviando(true)
    setErrorDelPanel(null)
    try {
      const creado = await api.crearTurno(nuevo)
      cerrarPanel()
      setExito(MENSAJE_TURNO_CREADO)
      pedirDia(fechaLocal(creado.inicio, zona))
    } catch (error: unknown) {
      if (error instanceof SesionTerminada) return
      setErrorDelPanel(mensajeDeCreacion(error))
      if (error instanceof EntradaRechazada && error.codigos.includes('RN-GL-04')) pedirPrestaciones()
    } finally {
      enCurso.current = false
      setEnviando(false)
    }
  }

  async function reprogramar(turno: TurnoDeLaAgenda, cambio: ReprogramacionDeTurno, zona: string): Promise<void> {
    if (enCurso.current) return
    enCurso.current = true
    setEnviando(true)
    setErrorDelPanel(null)
    try {
      const movido = await api.reprogramarTurno(turno.id, cambio)
      cerrarPanel()
      setExito(MENSAJE_TURNO_REPROGRAMADO)
      pedirDia(fechaLocal(movido.inicio, zona))
    } catch (error: unknown) {
      if (error instanceof SesionTerminada) return
      setErrorDelPanel(mensajeDeReprogramacion(error))
    } finally {
      enCurso.current = false
      setEnviando(false)
    }
  }

  /** El turno no se mueve: la recarga es del mismo día a la vista (design X10). */
  async function cancelarElTurno(turno: TurnoDeLaAgenda, estado: EstadoDeCancelacion): Promise<void> {
    if (enCurso.current) return
    enCurso.current = true
    setEnviando(true)
    setErrorDelPanel(null)
    // El «Turno cancelado.» de una cancelación anterior no debe quedar junto al rechazo de esta.
    setExito(null)
    try {
      await api.cancelarTurno(turno.id, estado)
      cerrarPanel()
      setExito(MENSAJE_TURNO_CANCELADO)
      pedirDia(dia?.fecha)
    } catch (error: unknown) {
      if (error instanceof SesionTerminada) return
      setErrorDelPanel(mensajeDeCancelacion(error))
    } finally {
      enCurso.current = false
      setEnviando(false)
    }
  }

  /** Como la cancelación, el turno no se mueve: la recarga es del mismo día a la vista (design W12). */
  async function registrarAsistencia(turno: TurnoDeLaAgenda, estado: EstadoDeAsistencia): Promise<void> {
    if (enCurso.current) return
    enCurso.current = true
    setEnviando(true)
    setErrorDelPanel(null)
    setExito(null)
    try {
      await api.marcarAsistencia(turno.id, estado)
      cerrarPanel()
      setExito(MENSAJE_ASISTENCIA_REGISTRADA)
      pedirDia(dia?.fecha)
    } finally {
      enCurso.current = false
      setEnviando(false)
    }
  }

  return (
    <section aria-labelledby="titulo-agenda">
      <div className="barra-de-pantalla barra-de-agenda">
        <div>
          <h1 id="titulo-agenda">Agenda del día</h1>
          {dia === null ? null : <p className="subtitulo-de-pantalla">{subtituloDeAgenda(dia.zona)}</p>}
        </div>
        <button type="button" className="boton-primario" disabled={dia === null} onClick={abrirPanel}>
          <IconoMas />
          Nuevo turno
        </button>
      </div>
      <div className="pantalla-con-panel pantalla-de-agenda">
        <div className="zona-de-tabla" ref={zonaDeTabla}>
          {dia === null ? null : (
            <div className="tarjeta barra-de-fecha">
              <div className="barra-de-fecha-izquierda">
                <button type="button" className="boton-secundario" onClick={() => ir(sumarDias(dia.fecha, -1))}>
                  <IconoFlecha hacia="izquierda" />
                  <span className="texto-del-boton">Día anterior</span>
                </button>
                <input
                  type="date"
                  className="selector-de-fecha"
                  aria-label="Fecha de la agenda"
                  value={dia.fecha}
                  onChange={(e) => {
                    if (e.target.value !== '') ir(e.target.value)
                  }}
                />
                <p className="nombre-del-dia-de-agenda">
                  <span className="dia-largo">{nombreDelDia(dia.fecha)}</span>
                  <span className="dia-compacto" aria-hidden="true">
                    {diaCompacto(dia.fecha)}
                  </span>
                </p>
                <button type="button" className="boton-secundario" onClick={() => ir(sumarDias(dia.fecha, 1))}>
                  <span className="texto-del-boton">Día siguiente</span>
                  <IconoFlecha hacia="derecha" />
                </button>
              </div>
              <button type="button" className="boton-secundario" onClick={() => ir(undefined)}>
                Hoy
              </button>
            </div>
          )}
          {exito === null ? null : <AvisoDeExito mensaje={exito} />}
          {carga.tipo === 'cargando' ? <p>{MENSAJE_CARGANDO}</p> : null}
          {carga.tipo === 'sin-conexion' ? (
            <Aviso mensaje={MENSAJE_SIN_CONEXION} titulo={tituloDelAviso(MENSAJE_SIN_CONEXION)}>
              <button type="button" className="boton-secundario" onClick={() => pedirDia(pedido.fecha)}>
                Reintentar
              </button>
            </Aviso>
          ) : null}
          {carga.tipo === 'sin-permiso' ? (
            <Aviso mensaje={MENSAJE_SIN_PERMISO_PARA_VER} titulo={tituloDelAviso(MENSAJE_SIN_PERMISO_PARA_VER)} />
          ) : null}
          {carga.tipo === 'dia' && dia !== null ? (
            <section className="tarjeta" aria-labelledby="titulo-turnos-del-dia">
              <div className="tarjeta-encabezado">
                <h2 id="titulo-turnos-del-dia">Turnos</h2>
                <span className="insignia-contador">{textoDelContador(dia.turnos.length)}</span>
              </div>
              {dia.turnos.length === 0 ? (
                <p className="sin-turnos">{MENSAJE_SIN_TURNOS}</p>
              ) : (
                <TablaDeTurnos
                  turnos={dia.turnos}
                  zonaHoraria={dia.zona}
                  turnoSeleccionadoId={panel.tipo === 'nuevo-turno' || panel.tipo === 'ninguno' ? null : panel.turno.id}
                  onRegistrarAsistencia={abrirAsistencia}
                  onReprogramar={abrirReprogramar}
                  onCancelar={abrirCancelar}
                  onVerHistorial={verHistorial}
                />
              )}
            </section>
          ) : null}
        </div>
        {panel.tipo === 'nuevo-turno' ? (
          <PanelNuevoTurno
            prestaciones={prestaciones}
            fechaInicial={dia?.fecha ?? ''}
            zonaHoraria={dia?.zona ?? ''}
            enviando={enviando}
            error={errorDelPanel}
            onCrear={(nuevo) => void crear(nuevo, dia?.zona ?? '')}
            onCancelar={cerrarPanel}
          />
        ) : null}
        {panel.tipo === 'reprogramar' ? (
          <PanelReprogramar
            key={panel.turno.id}
            turno={panel.turno}
            zonaHoraria={dia?.zona ?? ''}
            enviando={enviando}
            error={errorDelPanel}
            onReprogramar={(cambio) => void reprogramar(panel.turno, cambio, dia?.zona ?? '')}
            onCancelar={() => cerrarReprogramar(panel.turno)}
          />
        ) : null}
        {panel.tipo === 'cancelar' ? (
          <PanelCancelar
            key={panel.turno.id}
            turno={panel.turno}
            zonaHoraria={dia?.zona ?? ''}
            enviando={enviando}
            error={errorDelPanel}
            onCancelarTurno={(estado) => void cancelarElTurno(panel.turno, estado)}
            onVolver={() => cerrarCancelar(panel.turno)}
          />
        ) : null}
        {panel.tipo === 'asistencia' ? (
          <PanelAsistencia
            key={panel.turno.id}
            turno={panel.turno}
            zonaHoraria={dia?.zona ?? ''}
            enviando={enviando}
            onRegistrar={(estado) => void registrarAsistencia(panel.turno, estado)}
            onVolver={() => cerrarAsistencia(panel.turno)}
          />
        ) : null}
        {panel.tipo === 'historial' ? (
          <PanelHistorial
            key={panel.turno.id}
            turno={panel.turno}
            zonaHoraria={dia?.zona ?? ''}
            onCerrar={() => cerrarHistorial(panel.turno)}
          />
        ) : null}
      </div>
    </section>
  )
}
