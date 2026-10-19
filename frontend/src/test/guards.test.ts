import { readdirSync, readFileSync, statSync } from 'node:fs'
import { basename, join } from 'node:path'
import { describe, expect, it } from 'vitest'

const RAIZ_SRC = join(import.meta.dirname, '..')
const ESTE_ARCHIVO = basename(import.meta.filename)

function archivosDeSrc(carpeta: string): string[] {
  return readdirSync(carpeta).flatMap((nombre) => {
    const ruta = join(carpeta, nombre)
    return statSync(ruta).isDirectory() ? archivosDeSrc(ruta) : [ruta]
  })
}

function fuentes(): { ruta: string; texto: string }[] {
  return archivosDeSrc(RAIZ_SRC)
    .filter((ruta) => basename(ruta) !== ESTE_ARCHIVO)
    .map((ruta) => ({ ruta, texto: readFileSync(ruta, 'utf8') }))
}

function archivosQueCoinciden(patron: RegExp): string[] {
  return fuentes()
    .filter(({ texto }) => patron.test(texto))
    .map(({ ruta }) => ruta)
}

describe('guards del frontend', () => {
  it('regla 8: no hay any en src', () => {
    expect(archivosQueCoinciden(/:\s*any\b|\bas\s+any\b|<any>|\bany\[\]/)).toEqual([])
  })

  it('regla 6: no hay vi.mock ni stubs de fetch', () => {
    const patron = /\bvi\.(mock|doMock|fn|useFakeTimers|stubGlobal)\s*\(/
    expect(archivosQueCoinciden(patron)).toEqual([])
  })

  it('F7: no hay localStorage ni dangerouslySetInnerHTML', () => {
    expect(archivosQueCoinciden(/localStorage|dangerouslySetInnerHTML/)).toEqual([])
  })

  it('F4: no hay archivos barrel index.ts', () => {
    const barrels = archivosDeSrc(RAIZ_SRC).filter((ruta) => /^index\.tsx?$/.test(basename(ruta)))
    expect(barrels).toEqual([])
  })
})
