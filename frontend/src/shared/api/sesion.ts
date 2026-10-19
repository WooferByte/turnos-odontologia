// Sesión del panel en el navegador (design F7, D219): el access vive solo en memoria y el refresh en
// sessionStorage bajo una clave versionada. Cada acceso al almacenamiento va en try/catch: si no está
// disponible, la sesión vive solo en memoria.

export const CLAVE_DE_SESION = 'turnos.sesion.v1'

export interface Almacenamiento {
  getItem(clave: string): string | null
  setItem(clave: string, valor: string): void
  removeItem(clave: string): void
}

export interface Sesion {
  access(): string | null
  refresh(): string | null
  guardar(access: string, refresh: string): void
  guardarAccess(access: string): void
  borrar(): void
}

function almacenamientoDelNavegador(): Almacenamiento | null {
  try {
    return globalThis.sessionStorage
  } catch {
    return null
  }
}

function leerRefresh(almacenamiento: Almacenamiento | null): string | null {
  try {
    const crudo = almacenamiento?.getItem(CLAVE_DE_SESION) ?? null
    if (crudo === null) return null
    const valor: unknown = JSON.parse(crudo)
    if (typeof valor === 'object' && valor !== null && 'refresh' in valor && typeof valor.refresh === 'string') {
      return valor.refresh
    }
    return null
  } catch {
    return null
  }
}

export function crearSesion(almacenamiento: Almacenamiento | null = almacenamientoDelNavegador()): Sesion {
  let access: string | null = null
  let refresh: string | null = leerRefresh(almacenamiento)

  function persistirRefresh(): void {
    try {
      if (refresh === null) {
        almacenamiento?.removeItem(CLAVE_DE_SESION)
      } else {
        almacenamiento?.setItem(CLAVE_DE_SESION, JSON.stringify({ refresh }))
      }
    } catch {
      // Almacenamiento bloqueado: la sesión sigue en memoria.
    }
  }

  return {
    access: () => access,
    refresh: () => refresh,
    guardar: (accessNuevo, refreshNuevo) => {
      access = accessNuevo
      refresh = refreshNuevo
      persistirRefresh()
    },
    guardarAccess: (accessNuevo) => {
      access = accessNuevo
    },
    borrar: () => {
      access = null
      refresh = null
      persistirRefresh()
    },
  }
}
