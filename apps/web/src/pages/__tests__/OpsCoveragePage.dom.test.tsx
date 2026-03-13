import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import OpsCoveragePage from '../OpsCoveragePage'

vi.mock('../../lib/api', () => ({
  api: {
    getHealth: vi.fn().mockResolvedValue({ status: 'ok' }),
    getReady: vi.fn().mockResolvedValue({ status: 'ready' }),
    listAdminConfigs: vi.fn().mockResolvedValue([]),
    listPaymentProviders: vi.fn().mockResolvedValue([]),
    listPayments: vi.fn().mockResolvedValue([]),
    listTaxes: vi.fn().mockResolvedValue([]),
    listTaxEvents: vi.fn().mockResolvedValue([]),
    listLocalMarketValues: vi.fn().mockResolvedValue([]),
    getTerritoryVersions: vi.fn().mockResolvedValue([]),
    getRolesWithPermission: vi.fn().mockResolvedValue({ roles: [] }),
    importTerritoryVersion: vi.fn().mockResolvedValue({}),
    createAdminConfig: vi.fn().mockResolvedValue({}),
    getAdminConfig: vi.fn().mockResolvedValue({}),
    patchAdminConfig: vi.fn().mockResolvedValue({}),
    deleteAdminConfig: vi.fn().mockResolvedValue({}),
    listAdminActorRoles: vi.fn().mockResolvedValue([]),
    assignAdminActorRole: vi.fn().mockResolvedValue({}),
    patchAdminRole: vi.fn().mockResolvedValue({}),
    deleteAdminRole: vi.fn().mockResolvedValue({}),
    createPaymentProvider: vi.fn().mockResolvedValue({}),
    patchPaymentProvider: vi.fn().mockResolvedValue({}),
    initiatePayment: vi.fn().mockResolvedValue({}),
    getPayment: vi.fn().mockResolvedValue({}),
    getPaymentStatus: vi.fn().mockResolvedValue({}),
    sendPaymentWebhook: vi.fn().mockResolvedValue({}),
    createFee: vi.fn().mockResolvedValue({}),
    getFee: vi.fn().mockResolvedValue({}),
    createLocalMarketValue: vi.fn().mockResolvedValue({}),
    createTaxEvent: vi.fn().mockResolvedValue({}),
    patchTaxStatus: vi.fn().mockResolvedValue({}),
    getGeoPoint: vi.fn().mockResolvedValue({}),
    getTerritoryVersion: vi.fn().mockResolvedValue({}),
    createOrLegalVersion: vi.fn().mockResolvedValue({}),
    getActiveOrLegalVersion: vi.fn().mockResolvedValue({}),
    createOrTestCertificate: vi.fn().mockResolvedValue({}),
    createOrTransportEvent: vi.fn().mockResolvedValue({}),
    patchOrTransportArrival: vi.fn().mockResolvedValue({}),
    createOrTransformationFacility: vi.fn().mockResolvedValue({}),
    createOrTransformationEvent: vi.fn().mockResolvedValue({}),
    createOrExportValidation: vi.fn().mockResolvedValue({}),
    createOrForexRepatriation: vi.fn().mockResolvedValue({}),
  },
}))

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { id: 1 } }),
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

describe('OpsCoveragePage smoke', () => {
  it('renders key ops sections', async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <OpsCoveragePage />
      </QueryClientProvider>
    )
    expect(await screen.findByText('Couverture Ops')).toBeInTheDocument()
    expect(screen.getByText('Configuration admin')).toBeInTheDocument()
    expect(screen.getByText(/Endpoints avances regime OR/)).toBeInTheDocument()
  })
})
