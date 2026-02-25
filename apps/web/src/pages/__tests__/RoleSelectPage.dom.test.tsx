import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import RoleSelectPage from '../RoleSelectPage'
import { SessionProvider } from '../../contexts/SessionContext'

const getRbacFilieresMock = vi.fn()
const getRbacRolesMock = vi.fn()
const getRbacPermissionsMock = vi.fn()

vi.mock('../../lib/api', () => ({
  api: {
    getRbacFilieres: (...args: unknown[]) => getRbacFilieresMock(...args),
    getRbacRoles: (...args: unknown[]) => getRbacRolesMock(...args),
    getRbacPermissions: (...args: unknown[]) => getRbacPermissionsMock(...args),
  },
}))

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <MemoryRouter initialEntries={['/select-role']}>
          <Routes>
            <Route path="/select-role" element={<RoleSelectPage />} />
            <Route path="/select-filiere" element={<div>filiere-page</div>} />
            <Route path="/home" element={<div>home-page</div>} />
          </Routes>
        </MemoryRouter>
      </SessionProvider>
    </QueryClientProvider>
  )
}

describe('RoleSelectPage UX', () => {
  it('filters roles by search/category and navigates after selection', async () => {
    getRbacFilieresMock.mockResolvedValue([
      { code: 'OR', label: 'OR' },
      { code: 'PIERRE', label: 'PIERRE' },
      { code: 'BOIS', label: 'BOIS' },
    ])
    const allRows = [
      { code: 'orpailleur', label: 'Orpailleur', description: 'terrain', category: 'Acteurs terrain', actor_type: 'USAGER', filiere_scope: ['OR'], tags: [], is_active: true, display_order: 1 },
      { code: 'com_admin', label: 'Com Admin', description: 'admin', category: 'Export et regulation', actor_type: 'AGENT_ETAT', filiere_scope: ['OR'], tags: ['com'], is_active: true, display_order: 2 },
    ]
    getRbacRolesMock.mockImplementation(async (params?: { category?: string; search?: string }) => {
      let rows = [...allRows]
      if (params?.category) rows = rows.filter((r) => r.category === params.category)
      if (params?.search) {
        const q = String(params.search).toLowerCase()
        rows = rows.filter((r) => `${r.code} ${r.label} ${r.description}`.toLowerCase().includes(q))
      }
      return rows
    })
    getRbacPermissionsMock.mockResolvedValue({ role: 'orpailleur', permissions: ['auth.login', 'lot.create'] })

    const user = userEvent.setup()
    renderPage()

    expect(await screen.findByText('Choisir votre role')).toBeInTheDocument()
    expect(await screen.findByText('Orpailleur')).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Filtrer par categorie'), 'Acteurs terrain')
    expect(await screen.findByText('Orpailleur')).toBeInTheDocument()
    expect(screen.queryByText('Com Admin')).not.toBeInTheDocument()

    await user.clear(screen.getByLabelText('Rechercher un role'))
    await user.type(screen.getByLabelText('Rechercher un role'), 'orp')
    expect(await screen.findByText('Orpailleur')).toBeInTheDocument()

    await user.click(screen.getByText('Orpailleur'))
    expect(await screen.findByText('filiere-page')).toBeInTheDocument()
  }, 15000)

  it('navigates immediately when clicking Choisir on a role row', async () => {
    getRbacFilieresMock.mockResolvedValue([
      { code: 'OR', label: 'OR' },
      { code: 'PIERRE', label: 'PIERRE' },
      { code: 'BOIS', label: 'BOIS' },
    ])
    getRbacRolesMock.mockResolvedValue([
      { code: 'acteur', label: 'Acteur', description: 'terrain', category: 'Administration', actor_type: 'USAGER', filiere_scope: ['OR'], tags: [], is_active: true, display_order: 1 },
    ])
    getRbacPermissionsMock.mockResolvedValue({ role: 'acteur', permissions: ['auth.login'] })

    const user = userEvent.setup()
    renderPage()

    expect(await screen.findByText('Choisir votre role')).toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: 'Choisir' }))
    expect(await screen.findByText('filiere-page')).toBeInTheDocument()
  })

  it('navigates immediately when clicking the role row itself', async () => {
    getRbacFilieresMock.mockResolvedValue([
      { code: 'OR', label: 'OR' },
      { code: 'PIERRE', label: 'PIERRE' },
      { code: 'BOIS', label: 'BOIS' },
    ])
    getRbacRolesMock.mockResolvedValue([
      { code: 'acteur', label: 'Acteur', description: 'terrain', category: 'Administration', actor_type: 'USAGER', filiere_scope: ['OR'], tags: [], is_active: true, display_order: 1 },
    ])
    getRbacPermissionsMock.mockResolvedValue({ role: 'acteur', permissions: ['auth.login'] })

    const user = userEvent.setup()
    renderPage()

    expect(await screen.findByText('Choisir votre role')).toBeInTheDocument()
    await user.click(await screen.findByTestId('role-row-acteur'))
    expect(await screen.findByText('filiere-page')).toBeInTheDocument()
  })
})
