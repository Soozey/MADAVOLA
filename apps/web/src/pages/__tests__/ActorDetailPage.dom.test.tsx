import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import ActorDetailPage from '../ActorDetailPage'

const getActorMock = vi.fn()
const getActorAuthorizationsMock = vi.fn()
const createActorAuthorizationMock = vi.fn()

vi.mock('../../lib/api', () => ({
  api: {
    getActor: (...args: unknown[]) => getActorMock(...args),
    getActorAuthorizations: (...args: unknown[]) => getActorAuthorizationsMock(...args),
    createActorAuthorization: (...args: unknown[]) => createActorAuthorizationMock(...args),
  },
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

describe('ActorDetailPage wiring', () => {
  it('renders actor details and authorizations list', async () => {
    getActorMock.mockResolvedValue({
      id: 12,
      nom: 'Rakoto',
      prenoms: 'Jean',
      email: 'rakoto@example.com',
      telephone: '0340000000',
      region_code: '01',
      district_code: '0101',
      commune_code: '010101',
      status: 'active',
    })
    getActorAuthorizationsMock.mockResolvedValue([
      {
        id: 1,
        filiere: 'BOIS',
        authorization_type: 'exploitant',
        numero: 'AUTH-1',
        status: 'active',
        valid_from: '2026-01-01T00:00:00Z',
        valid_to: '2026-12-31T00:00:00Z',
      },
    ])

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/actors/12']}>
          <Routes>
            <Route path="/actors/:id" element={<ActorDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    )

    expect(await screen.findByText('Acteur #12')).toBeInTheDocument()
    expect(await screen.findByText(/AUTH-1/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Ajouter autorisation/i })).toBeInTheDocument()
  })
})

