// Los tres roles del panel (RN-AU-02) y sus etiquetas (D308): una sola fuente para la pantalla de usuarios y
// el indicador del encabezado.

export type Rol = 'odontologo' | 'recepcionista' | 'dueno'

/** En el orden fijo de la API: `odontologo`, `recepcionista`, `dueno` (D306). */
export const ROLES: readonly Rol[] = ['odontologo', 'recepcionista', 'dueno']

export function esRol(valor: unknown): valor is Rol {
  return ROLES.some((rol) => rol === valor)
}

const NOMBRES_DE_ROL: Record<Rol, string> = {
  odontologo: 'Odontólogo',
  recepcionista: 'Recepcionista',
  dueno: 'Dueño',
}

export function nombreDelRol(rol: Rol): string {
  return NOMBRES_DE_ROL[rol]
}
