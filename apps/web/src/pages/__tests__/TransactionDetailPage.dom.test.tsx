import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import TransactionDetailPage from '../TransactionDetailPage'

const getTransactionMock = vi.fn()
const getTransactionPaymentsMock = vi.fn()
const getInvoicesMock = vi.fn()
const initiateTransactionPaymentMock = vi.fn()

vi.mock('../../lib/api', () => ({
  api: {
    getTransaction: (...args: unknown[]) => getTransactionMock(...args),
    getTransactionPayments: (...args: unknown[]) => getTransactionPaymentsMock(...args),
    getInvoices: (...args: unknown[]) => getInvoicesMock(...args),
    initiateTransactionPayment: (...args: unknown[]) => initiateTransactionPaymentMock(...args),
  },
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

describe('TransactionDetailPage wiring', () => {
  it('renders payments from /transactions/{id}/payments', async () => {
    getTransactionMock.mockResolvedValue({
      id: 12,
      seller_actor_id: 3,
      buyer_actor_id: 4,
      total_amount: 10000,
      currency: 'MGA',
      status: 'pending_payment',
      items: [],
    })
    getTransactionPaymentsMock.mockResolvedValue([
      { payment_request_id: 41, payment_id: 80, status: 'pending', external_ref: 'txn-12-ref' },
    ])
    getInvoicesMock.mockResolvedValue([])
    initiateTransactionPaymentMock.mockResolvedValue({})

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/transactions/12']}>
          <Routes>
            <Route path="/transactions/:id" element={<TransactionDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    )

    expect(await screen.findByText('Transaction #12')).toBeInTheDocument()
    expect(await screen.findByText(/Historique des paiements/i)).toBeInTheDocument()
    expect(screen.getByText(/Demande #41/)).toBeInTheDocument()
    expect(getTransactionPaymentsMock).toHaveBeenCalledWith(12)
  })
})

