import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

vi.mock('axios', () => ({
  default: {
    create: () => ({
      defaults: { headers: { common: {} } },
      get: vi.fn(() => new Promise(() => {})),
      post: vi.fn(() => new Promise(() => {})),
    }),
  },
}))

describe('App mobile smoke', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it("renders login first and hides dashboard modules before role/filiere selection", () => {
    render(<App />)
    expect(screen.getByText(/MADAVOLA Mobile OR \/ PIERRE \/ BOIS/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Se connecter' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Acteurs' })).not.toBeInTheDocument()
  })
})
