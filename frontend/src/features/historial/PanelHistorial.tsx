// Panel lateral «Historial del turno» (design G2, G3, G5, G6, G9): un solo pedido por apertura, con una bandera de
// vigencia por pedido para que solo se muestre la última respuesta (y ninguna después de cerrar). El estado se
// deriva de lo que respondió la API; la pantalla no reordena ni evalúa reglas.
import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { PermisoInsuficiente, RecursoInexistente, SesionTerminada } from '../../shared/api/errores'
import { useSesionDelPanel } from '../../shared/api/ProveedorDeSesion'
import { Aviso } from '../../shared/componentes/Aviso'
import { fechaLocal, horaLocal } from '../../shared/horaDelConsultorio'
import { IconoCerrar } from '../../shared/iconos/IconoCerrar'
import { IconoReloj } from '../../shared/iconos/IconoReloj'
import type { TurnoDeLaAgenda } from '../agenda/apiAgenda'
import { nombreDelDia, tituloDelAviso } from '../agenda/mensajes'
import { crearApiHistorial, type EventoDelHistorial } from './apiHistorial'
import {
  MENSAJE_CARGANDO,
  MENSAJE_SIN_CONEXION,
  MENSAJE_SIN_EVENTOS,
  MENSAJE_SIN_PERMISO,
  MENSAJE_SOLO_LECTURA,
  MENSAJE_TURNO_INEXISTENTE,
  TITULO_DEL_PANEL,
  cuandoOcurrio,
  detalleDelCancelado,
  detalleDelCreado,
  detalleDelReprogramado,
  textoDelActor,
  tituloDelEvento,
} from './mensajes'

type Carga =
  | { tipo: 'cargando' }
  | { tipo: 'eventos'; eventos: readonly EventoDelHistorial[] }
  | { tipo: 'inexistente' }
  | { tipo: 'sin-permiso' }
  | { tipo: 'sin-conexion' }

interface Propiedades {
  turno: TurnoDeLaAgenda
  zonaHoraria: string
  onCerrar(): void
}

export function PanelHistorial({ turno, zonaHoraria, onCerrar }: Propiedades) {
  const idTitulo = useId()
  const titulo = useRef<HTMLHeadingElement>(null)
  const { pedidoDelPanel } = useSesionDelPanel()
  const api = useMemo(() => crearApiHistorial(pedidoDelPanel), [pedidoDelPanel])
  const [carga, setCarga] = useState<Carga>({ tipo: 'cargando' })
  // Distingue dos pedidos iguales seguidos («Reintentar»).
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    let vigente = true
    api.obtenerHistorial(turno.id).then(
      (eventos) => {
        if (vigente) setCarga({ tipo: 'eventos', eventos })
      },
      (error: unknown) => {
        // Si la sesión terminó, el proveedor ya llevó al inicio de sesión: la pantalla no muestra nada más.
        if (!vigente || error instanceof SesionTerminada) return
        if (error instanceof RecursoInexistente) setCarga({ tipo: 'inexistente' })
        else setCarga({ tipo: error instanceof PermisoInsuficiente ? 'sin-permiso' : 'sin-conexion' })
      },
    )
    return () => {
      vigente = false
    }
  }, [api, turno.id, intento])

  // Al abrir (y al pasar a otro turno, que remonta el panel) el foco va al título (design G9).
  useEffect(() => {
    titulo.current?.focus()
  }, [])

  function reintentar(): void {
    setCarga({ tipo: 'cargando' })
    setIntento((anterior) => anterior + 1)
  }

  const dia = nombreDelDia(fechaLocal(turno.inicio, zonaHoraria))
  const horario = `${horaLocal(turno.inicio, zonaHoraria)} – ${horaLocal(turno.fin, zonaHoraria)}`

  return (
    <aside aria-labelledby={idTitulo} className="panel-lateral panel-de-historial">
      <header className="panel-encabezado">
        <div>
          <h2 id={idTitulo} ref={titulo} tabIndex={-1}>
            <IconoReloj />
            {TITULO_DEL_PANEL}
          </h2>
          <p className="panel-subtitulo">
            {turno.paciente.nombre} {turno.paciente.apellido} · {turno.prestacion.nombre}
          </p>
          <p className="panel-subtitulo">
            {dia}, {horario}
          </p>
        </div>
        <button type="button" className="boton-cerrar" aria-label="Cerrar" onClick={onCerrar}>
          <IconoCerrar />
        </button>
      </header>
      <div className="panel-cuerpo">
        <p className="nota-de-solo-lectura">{MENSAJE_SOLO_LECTURA}</p>
        {carga.tipo === 'cargando' ? <p>{MENSAJE_CARGANDO}</p> : null}
        {carga.tipo === 'inexistente' ? (
          <Aviso mensaje={MENSAJE_TURNO_INEXISTENTE} titulo={tituloDelAviso(MENSAJE_TURNO_INEXISTENTE)} />
        ) : null}
        {carga.tipo === 'sin-permiso' ? (
          <Aviso mensaje={MENSAJE_SIN_PERMISO} titulo={tituloDelAviso(MENSAJE_SIN_PERMISO)} />
        ) : null}
        {carga.tipo === 'sin-conexion' ? (
          <Aviso mensaje={MENSAJE_SIN_CONEXION} titulo={tituloDelAviso(MENSAJE_SIN_CONEXION)}>
            <button type="button" className="boton-secundario" onClick={reintentar}>
              Reintentar
            </button>
          </Aviso>
        ) : null}
        {carga.tipo === 'eventos' ? (
          carga.eventos.length === 0 ? (
            <p className="historial-vacio">{MENSAJE_SIN_EVENTOS}</p>
          ) : (
            <ol className="linea-de-tiempo">
              {carga.eventos.map((evento) => {
                const detalle =
                  evento.tipo === 'creado'
                    ? detalleDelCreado(evento.despues, zonaHoraria)
                    : evento.tipo === 'cancelado'
                      ? detalleDelCancelado(evento.antes, evento.despues)
                      : null
                const cambios =
                  evento.tipo === 'reprogramado' ? detalleDelReprogramado(evento.antes, evento.despues, zonaHoraria) : []
                return (
                  <li key={evento.id} className="evento-del-historial">
                    <h3>{tituloDelEvento(evento.tipo)}</h3>
                    <p className="cifras">{cuandoOcurrio(evento.ocurrido_en, zonaHoraria)}</p>
                    <p>{textoDelActor(evento.actor_tipo, evento.actor_id)}</p>
                    {detalle === null ? null : <p className="evento-detalle">{detalle}</p>}
                    {cambios.map((linea) => (
                      <p key={linea} className="evento-detalle">
                        {linea}
                      </p>
                    ))}
                    {evento.motivo === null ? null : <p className="evento-detalle">Motivo: {evento.motivo}</p>}
                  </li>
                )
              })}
            </ol>
          )
        ) : null}
        <div className="panel-pie">
          <button type="button" className="boton-secundario" onClick={onCerrar}>
            Cerrar
          </button>
        </div>
      </div>
    </aside>
  )
}
