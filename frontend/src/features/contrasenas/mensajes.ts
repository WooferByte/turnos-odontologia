// Textos fijos de las pantallas de contraseñas y el único lugar que decide qué mensaje corresponde a cada
// rechazo (design K14, como U19 de C-09). No se muestra el `detail` de la API ni ninguna contraseña.
import { EntradaRechazada, PermisoInsuficiente, ReglaRechazada } from '../../shared/api/errores'
import {
  MENSAJE_CONTRASENA_FUERA_DE_RANGO,
  MENSAJE_SIN_CONEXION,
  MENSAJE_SIN_PERMISO_DE_ESCRITURA,
  SIN_ERRORES,
  type ErroresDelPanel,
} from '../usuarios/mensajes'

export const AYUDA_DE_LARGO = 'De 10 caracteres a 72 bytes.'
export const NOTA_DE_RESTABLECER = 'Al guardar se cierran todas las sesiones de este usuario.'
export const MENSAJE_RESTABLECER_LA_PROPIA = 'Tu propia contraseña se cambia desde «Mi contraseña» (RN-AU-10).'
export const MENSAJE_REVISAR_DATOS = 'Revisá los datos.'

export function avisoDeRestablecida(email: string): string {
  return `Contraseña restablecida. Se cerraron las sesiones de ${email}.`
}

/** Lo que el panel de restablecer muestra después de un rechazo: debajo del campo o en el aviso del panel. */
export function erroresDeRestablecimiento(error: unknown): ErroresDelPanel {
  if (error instanceof PermisoInsuficiente) return { ...SIN_ERRORES, aviso: MENSAJE_SIN_PERMISO_DE_ESCRITURA }
  if (error instanceof ReglaRechazada && error.codigo === 'RN-AU-10') {
    return { ...SIN_ERRORES, aviso: MENSAJE_RESTABLECER_LA_PROPIA }
  }
  if (error instanceof EntradaRechazada) {
    const esLargo = (e: { campo: string | null; codigo: string | null }) =>
      e.campo === 'contrasena' && e.codigo === 'RN-AU-07'
    const largo = error.errores.some(esLargo)
    const soloElLargo = error.errores.length > 0 && error.errores.every(esLargo)
    return {
      ...SIN_ERRORES,
      contrasena: largo ? MENSAJE_CONTRASENA_FUERA_DE_RANGO : null,
      aviso: soloElLargo ? null : MENSAJE_REVISAR_DATOS,
    }
  }
  return { ...SIN_ERRORES, aviso: MENSAJE_SIN_CONEXION }
}

export const MENSAJE_ACTUAL_INCORRECTA = 'La contraseña actual no es correcta (RN-AU-09).'
export const MENSAJE_REPETICION_DISTINTA = 'Las contraseñas nuevas no coinciden.'
export const MENSAJE_SIN_PERMISO_PARA_CAMBIAR = 'Tu usuario no tiene permiso para cambiar la contraseña (RN-AU-05).'
export const AVISO_DE_CAMBIADA = 'Contraseña cambiada. Tus otras sesiones se cerraron.'

/** Lo que «Mi contraseña» muestra: debajo de cada campo y en el aviso de la pantalla. */
export interface ErroresDeMiContrasena {
  actual: string | null
  nueva: string | null
  repeticion: string | null
  aviso: string | null
}

export const SIN_ERRORES_DE_MI_CONTRASENA: ErroresDeMiContrasena = {
  actual: null,
  nueva: null,
  repeticion: null,
  aviso: null,
}

/** Un `422` `RN-AU-09` (actual incorrecta), un `RN-AU-07` de la nueva, un `403` o una caída de red (K14). */
export function erroresDeCambioPropio(error: unknown): ErroresDeMiContrasena {
  if (error instanceof PermisoInsuficiente) {
    return { ...SIN_ERRORES_DE_MI_CONTRASENA, aviso: MENSAJE_SIN_PERMISO_PARA_CAMBIAR }
  }
  if (error instanceof EntradaRechazada) {
    if (error.codigo === 'RN-AU-09') return { ...SIN_ERRORES_DE_MI_CONTRASENA, actual: MENSAJE_ACTUAL_INCORRECTA }
    const esLargo = (e: { campo: string | null; codigo: string | null }) =>
      e.campo === 'contrasena_nueva' && e.codigo === 'RN-AU-07'
    const largo = error.errores.some(esLargo)
    const soloElLargo = error.errores.length > 0 && error.errores.every(esLargo)
    return {
      ...SIN_ERRORES_DE_MI_CONTRASENA,
      nueva: largo ? MENSAJE_CONTRASENA_FUERA_DE_RANGO : null,
      aviso: soloElLargo ? null : MENSAJE_REVISAR_DATOS,
    }
  }
  return { ...SIN_ERRORES_DE_MI_CONTRASENA, aviso: MENSAJE_SIN_CONEXION }
}
