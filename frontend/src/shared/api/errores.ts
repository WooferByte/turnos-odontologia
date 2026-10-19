// Errores que el cliente HTTP levanta (design F12, T6). Cada uno lleva el código RN cuando la API lo dio,
// para que los tests y las pantallas decidan por el código y no por el texto.

export class ErrorDeApi extends Error {
  readonly codigo: string | null

  constructor(mensaje: string, codigo: string | null) {
    super(mensaje)
    this.name = new.target.name
    this.codigo = codigo
  }
}

/** Un error de campo de un `422` (`errores` de `application/problem+json`). */
export interface ErrorDeCampo {
  campo: string | null
  codigo: string | null
  mensaje: string
}

/** 401 del login: email inexistente, contraseña incorrecta o usuario inactivo (RN-AU-04). */
export class CredencialesRechazadas extends ErrorDeApi {}

/** 422: la API rechazó la entrada. `codigos` y `errores` vienen del cuerpo `problem+json` (vacíos si no los hay). */
export class EntradaRechazada extends ErrorDeApi {
  readonly codigos: readonly string[]
  readonly errores: readonly ErrorDeCampo[]

  constructor(
    mensaje: string,
    codigo: string | null,
    codigos: readonly string[] = [],
    errores: readonly ErrorDeCampo[] = [],
  ) {
    super(mensaje, codigo)
    this.codigos = codigos
    this.errores = errores
  }
}

/** 403 `RN-AU-05`: la sesión es válida pero el rol no alcanza (D205). */
export class PermisoInsuficiente extends ErrorDeApi {}

/** 409: una regla de negocio rechazó la petición (por ejemplo `RN-AG-15`). */
export class ReglaRechazada extends ErrorDeApi {}

/** 404 `RN-GL-04`: el recurso de la URL no existe. */
export class RecursoInexistente extends ErrorDeApi {}

/** La sesión ya no sirve (RN-AU-03): hay que iniciar sesión de nuevo. */
export class SesionTerminada extends ErrorDeApi {}

/** Sin respuesta, error de red, 5xx o cuerpo ilegible. */
export class SinConexion extends ErrorDeApi {}
