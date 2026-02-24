import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AccountOpsPage from '../AccountOpsPage'

const getActorKycMock = vi.fn()
const getActorWalletsMock = vi.fn()
const getAllCommunesMock = vi.fn()
const getCommuneProfileMock = vi.fn()

vi.mock('../../lib/api', () => ({
  api: {
    getActorKyc: (...args: unknown[]) => getActorKycMock(...args),
    getActorWallets: (...args: unknown[]) => getActorWalletsMock(...args),
    getAllCommunes: (...args: unknown[]) => getAllCommunesMock(...args),
    getCommuneProfile: (...args: unknown[]) => getCommuneProfileMock(...args),
    createActorKyc: vi.fn().mockResolvedValue({}),
    createActorWallet: vi.fn().mockResolvedValue({}),
    patchCommuneProfile: vi.fn().mockResolvedValue({}),
  },
}))

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 42,
      commune: { id: 7 },
      roles: [{ role: 'commune_agent' }],
    },
  }),
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

describe('AccountOpsPage wiring', () => {
  it('renders dedicated KYC/Wallet/Commune profile sections', async () => {
    getActorKycMock.mockResolvedValue([{ id: 1, pieces: ['cin_recto.jpg'], note: 'ok' }])
    getActorWalletsMock.mockResolvedValue([{ id: 2, provider: 'mobile_money', account_ref: '0340000000', is_primary: true }])
    getAllCommunesMock.mockResolvedValue([{ id: 7, code: 'C0007', name: 'Commune Test' }])
    getCommuneProfileMock.mockResolvedValue({
      commune_id: 7,
      mobile_money_account_ref: '0340000000',
      receiver_name: 'Receveur',
      receiver_phone: '0340000001',
      active: true,
    })

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <AccountOpsPage />
      </QueryClientProvider>
    )

    expect(await screen.findByText(/KYC, wallets et profil commune/i)).toBeInTheDocument()
    expect(await screen.findByText(/#1/i)).toBeInTheDocument()
    expect(await screen.findByText(/#2/i)).toBeInTheDocument()
    expect(await screen.findByText(/Profil actuel:/i)).toBeInTheDocument()
  })
})
