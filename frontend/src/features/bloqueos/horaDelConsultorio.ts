// Hora del consultorio (design B15, RN-GL-01): la pantalla escribe y muestra fechas en la zona del consultorio
// y la API habla en UTC. Solo `Intl`, sin dependencias.

const FECHA_LOCAL = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/

interface Partes {
  anio: number
  mes: number
  dia: number
  hora: number
  minuto: number
}

function partesEn(instante: number, zona: string): Partes {
  const formato = new Intl.DateTimeFormat('en-US', {
    timeZone: zona,
    hourCycle: 'h23',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
  const valores = new Map(formato.formatToParts(new Date(instante)).map((p) => [p.type, Number(p.value)]))
  const leer = (tipo: Intl.DateTimeFormatPartTypes): number => valores.get(tipo) ?? 0
  return { anio: leer('year'), mes: leer('month'), dia: leer('day'), hora: leer('hour'), minuto: leer('minute') }
}

/** Desfase de la zona en ese instante, en milisegundos (hora local menos UTC). */
function desfaseEn(instante: number, zona: string): number {
  const p = partesEn(instante, zona)
  return Date.UTC(p.anio, p.mes - 1, p.dia, p.hora, p.minuto) - Math.floor(instante / 60000) * 60000
}

/** `aaaa-mm-ddThh:mm` del consultorio (valor de un `datetime-local`) a ISO en UTC con `Z`. */
export function aUtc(fechaHoraLocal: string, zona: string): string {
  const coincidencia = FECHA_LOCAL.exec(fechaHoraLocal)
  if (coincidencia === null) throw new RangeError(`Fecha y hora local inválida: ${fechaHoraLocal}`)
  const [anio, mes, dia, hora, minuto] = coincidencia.slice(1).map(Number)
  const comoUtc = Date.UTC(anio ?? 0, (mes ?? 1) - 1, dia ?? 1, hora ?? 0, minuto ?? 0)
  // Se calcula el desfase una vez y se repite con el instante resultante: acierta también cerca de un cambio de hora.
  const primero = comoUtc - desfaseEn(comoUtc, zona)
  const instante = comoUtc - desfaseEn(primero, zona)
  return new Date(instante).toISOString().replace('.000Z', 'Z')
}

function dosCifras(n: number): string {
  return String(n).padStart(2, '0')
}

/** ISO en UTC a `dd/mm/aaaa hh:mm` en la zona del consultorio. */
export function aLocal(utc: string, zona: string): string {
  const p = partesEn(Date.parse(utc), zona)
  return `${dosCifras(p.dia)}/${dosCifras(p.mes)}/${p.anio} ${dosCifras(p.hora)}:${dosCifras(p.minuto)}`
}
