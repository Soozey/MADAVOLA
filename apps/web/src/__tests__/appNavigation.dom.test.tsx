import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import App from '../App'

const getMeMock = vi.fn()
const getRbacRolesMock = vi.fn()
const getRbacFilieresMock = vi.fn()
const getRbacPermissionsMock = vi.fn()

vi.mock('../lib/api', () => ({
  api: {
    getMe: (...args: unknown[]) => getMeMock(...args),
    getRbacRoles: (...args: unknown[]) => getRbacRolesMock(...args),
    getRbacFilieres: (...args: unknown[]) => getRbacFilieresMock(...args),
    getRbacPermissions: (...args: unknown[]) => getRbacPermissionsMock(...args),
  },
}))

const AUTH_USER = {
  id: 1,
  nom: 'Admin',
  prenoms: 'Demo',
  email: 'admin@example.com',
  telephone: '0340000000',
  roles: [{ role: 'admin', status: 'active' }],
  region: null,
  commune: null,
}

describe('App smoke navigation', () => {
  const renderApp = () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    })
    return render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    )
  }

  beforeEach(() => {
    localStorage.clear()
    window.history.pushState({}, '', '/')
    localStorage.setItem('access_token', 'test-token')
    getMeMock.mockResolvedValue(AUTH_USER)
    getRbacFilieresMock.mockResolvedValue([
      { code: 'OR', label: 'OR' },
      { code: 'PIERRE', label: 'PIERRE' },
      { code: 'BOIS', label: 'BOIS' },
    ])
    getRbacRolesMock.mockResolvedValue([
      { code: 'orpailleur', label: 'Orpailleur', description: 'Role OR', actor_type: 'USAGER', filiere_scope: ['OR'], category: 'OR', tags: [], is_active: true, display_order: 1 },
      { code: 'collecteur', label: 'Collecteur', description: 'Role OR', actor_type: 'USAGER', filiere_scope: ['OR'], category: 'OR', tags: [], is_active: true, display_order: 2 },
      { code: 'bois_exploitant', label: 'Bois Exploitant', description: 'Role BOIS', actor_type: 'USAGER', filiere_scope: ['BOIS'], category: 'BOIS', tags: [], is_active: true, display_order: 3 },
    ])
    getRbacPermissionsMock.mockResolvedValue({ role: 'orpailleur', permissions: ['auth.login'] })
  })

  it('navigates role -> home with persisted filiere', async () => {
    const user = userEvent.setup()
    renderApp()

    expect(await screen.findByText('Choisir votre role')).toBeInTheDocument()
    await user.click(await screen.findByText('Orpailleur'))
    expect(await screen.findByText('Choisir votre filiere')).toBeInTheDocument()
    await user.click(screen.getByTestId('filiere-validate'))

    expect(await screen.findByRole('heading', { name: 'Accueil' })).toBeInTheDocument()
    expect(screen.getByText(/Fili[eè]re choisie:/i)).toHaveTextContent('OR')
  })

  it.each(['OR', 'PIERRE', 'BOIS'] as const)(
    'loads home with persisted filiere %s',
    async (filiere) => {
      localStorage.setItem('selectedRole', 'orpailleur')
      localStorage.setItem('selectedFiliere', filiere)
      window.history.pushState({}, '', '/home')

      renderApp()
      expect(await screen.findByRole('heading', { name: 'Accueil' })).toBeInTheDocument()
      expect(screen.getByText(/Fili[eè]re choisie:/i)).toHaveTextContent(filiere)
    }
  )
})
