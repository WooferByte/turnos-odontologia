// Pantalla de la agenda del día (design A13): un pedido por cambio de día, con una bandera de vigencia por pedido
// para que solo se muestre la respuesta del último. El estado se deriva de lo que respondió la API; la pantalla
// no evalúa reglas.
import { useEffect, useMemo, useState } from 'react'
import { PermisoInsuficiente, SesionTerminada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { Aviso } from '../../shared/componentes/Aviso'
import { IconoFlecha } from '../../shared/iconos/IconoFlecha'
import { crearApiAgenda, type TurnoDeLaAgenda } from './apiAgenda'
import {
  MENSAJE_CARGANDO,
  MENSAJE_SIN_CONEXION,
  MENSAJE_SIN_PERMISO_PARA_VER,
  MENSAJE_SIN_TURNOS,
  diaCompacto,
  nombreDelDia,
  subtituloDeAgenda,
  sumarDias,
  textoDelContador,
  tituloDelAviso,
} from './mensajes'
import { TablaDeTurnos } from './TablaDeTurnos'

type Carga = { tipo: 'cargando' } | { tipo: 'sin-conexion' } | { tipo: 'sin-permiso' } | { tipo: 'dia' }

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

  function pedirDia(fecha: string | undefined): void {
    setCarga({ tipo: 'cargando' })
    setPedido((anterior) => ({ fecha, numero: anterior.numero + 1 }))
  }

  return (
    <section aria-labelledby="titulo-agenda">
      <div className="barra-de-pantalla">
        <div>
          <h1 id="titulo-agenda">Agenda del día</h1>
          {dia === null ? null : <p className="subtitulo-de-pantalla">{subtituloDeAgenda(dia.zona)}</p>}
        </div>
      </div>
      {dia === null ? null : (
        <div className="tarjeta barra-de-fecha">
          <div className="barra-de-fecha-izquierda">
            <button type="button" className="boton-secundario" onClick={() => pedirDia(sumarDias(dia.fecha, -1))}>
              <IconoFlecha hacia="izquierda" />
              <span className="texto-del-boton">Día anterior</span>
            </button>
            <input
              type="date"
              className="selector-de-fecha"
              aria-label="Fecha de la agenda"
              value={dia.fecha}
              onChange={(e) => {
                if (e.target.value !== '') pedirDia(e.target.value)
              }}
            />
            <p className="nombre-del-dia">
              {nombreDelDia(dia.fecha)}
              <span className="dia-compacto" aria-hidden="true">
                {diaCompacto(dia.fecha)}
              </span>
            </p>
            <button type="button" className="boton-secundario" onClick={() => pedirDia(sumarDias(dia.fecha, 1))}>
              <span className="texto-del-boton">Día siguiente</span>
              <IconoFlecha hacia="derecha" />
            </button>
          </div>
          <button type="button" className="boton-secundario" onClick={() => pedirDia(undefined)}>
            Hoy
          </button>
        </div>
      )}
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
            <TablaDeTurnos turnos={dia.turnos} zonaHoraria={dia.zona} />
          )}
        </section>
      ) : null}
    </section>
  )
}
