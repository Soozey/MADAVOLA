import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ExportsPage from '../ExportsPage'

const getExportsMock = vi.fn()
const createExportMock = vi.fn()
const updateExportStatusMock = vi.fn()
const getLotsMock = vi.fn()
const getOrExportChecklistMock = vi.fn()
const linkLotsToExportMock = vi.fn()
const submitExportMock = vi.fn()
const validateExportStepMock = vi.fn()
const verifyOrExportChecklistItemMock = vi.fn()
const getExportMock = vi.fn()
const getAllCommunesMock = vi.fn()

vi.mock('../../lib/api', () => ({
  api: {
    getExports: (...args: unknown[]) => getExportsMock(...args),
    createExport: (...args: unknown[]) => createExportMock(...args),
    updateExportStatus: (...args: unknown[]) => updateExportStatusMock(...args),
    getLots: (...args: unknown[]) => getLotsMock(...args),
    getOrExportChecklist: (...args: unknown[]) => getOrExportChecklistMock(...args),
    linkLotsToExport: (...args: unknown[]) => linkLotsToExportMock(...args),
    submitExport: (...args: unknown[]) => submitExportMock(...args),
    validateExportStep: (...args: unknown[]) => validateExportStepMock(...args),
    verifyOrExportChecklistItem: (...args: unknown[]) => verifyOrExportChecklistItemMock(...args),
    getExport: (...args: unknown[]) => getExportMock(...args),
    getAllCommunes: (...args: unknown[]) => getAllCommunesMock(...args),
  },
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

describe('ExportsPage wiring', () => {
  it('loads export detail from /exports/{id}', async () => {
    getExportsMock.mockResolvedValue([{ id: 5, dossier_number: 'EXP-5', status: 'draft', created_by_actor_id: 1 }])
    getLotsMock.mockResolvedValue({ items: [] })
    getOrExportChecklistMock.mockResolvedValue([])
    getAllCommunesMock.mockResolvedValue([])
    getExportMock.mockResolvedValue({
      id: 5,
      dossier_number: 'EXP-5',
      status: 'draft',
      destination: 'EU',
      destination_country: 'FR',
      transport_mode: 'air',
      total_weight: 10,
      declared_value: 5000,
      sealed_qr: null,
    })

    const user = userEvent.setup()
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <ExportsPage />
      </QueryClientProvider>
    )

    expect(await screen.findByText('Dossiers export')).toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: /Voir detail/i }))
    expect(await screen.findByText(/Detail dossier export #5/)).toBeInTheDocument()
    expect(await screen.findByText(/Destination/)).toBeInTheDocument()
  })
})
