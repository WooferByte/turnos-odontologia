// Errores que el cliente HTTP levanta (design F12). Cada uno lleva el código RN cuando la API lo dio,
// para que los tests y las pantallas decidan por el código y no por el texto.

export class ErrorDeApi extends Error {
  readonly codigo: string | null

  constructor(mensaje: string, codigo: string | null) {
    super(mensaje)
    this.name = new.target.name
    this.codigo = codigo
  }
}

/** 401 del login: email inexistente, contraseña incorrecta o usuario inactivo (RN-AU-04). */
export class CredencialesRechazadas extends ErrorDeApi {}

/** 422: la API rechazó la forma de la entrada. */
export class EntradaRechazada extends ErrorDeApi {}

/** La sesión ya no sirve (RN-AU-03): hay que iniciar sesión de nuevo. */
export class SesionTerminada extends ErrorDeApi {}

/** Sin respuesta, error de red, 5xx o cuerpo ilegible. */
export class SinConexion extends ErrorDeApi {}
