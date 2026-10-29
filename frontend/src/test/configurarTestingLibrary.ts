import { configure } from '@testing-library/react'

// findBy* y waitFor esperan 1 s por defecto; en una máquina cargada no alcanza.
configure({ asyncUtilTimeout: 5_000 })
