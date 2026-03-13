import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import DocumentsPage from '../DocumentsPage'

const getDocumentsMock = vi.fn()
const getDocumentMock = vi.fn()
const uploadDocumentMock = vi.fn()

vi.mock('../../lib/api', () => ({
  api: {
    getDocuments: (...args: unknown[]) => getDocumentsMock(...args),
    getDocument: (...args: unknown[]) => getDocumentMock(...args),
    uploadDocument: (...args: unknown[]) => uploadDocumentMock(...args),
  },
}))

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { id: 1 } }),
}))

vi.mock('../../contexts/ToastContext', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}))

describe('DocumentsPage wiring', () => {
  it('renders list from /documents', async () => {
    getDocumentsMock.mockResolvedValue([
      {
        id: 99,
        doc_type: 'piece_identite',
        owner_actor_id: 1,
        original_filename: 'cin.pdf',
        sha256: 'abc',
        related_entity_type: 'actor',
        related_entity_id: '1',
      },
    ])
    getDocumentMock.mockResolvedValue({
      id: 99,
      doc_type: 'piece_identite',
      owner_actor_id: 1,
      original_filename: 'cin.pdf',
      sha256: 'abc',
      storage_path: '/tmp/cin.pdf',
    })

    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    render(
      <QueryClientProvider client={qc}>
        <DocumentsPage />
      </QueryClientProvider>
    )

    expect(await screen.findByText('Documents')).toBeInTheDocument()
    expect(await screen.findByText(/cin.pdf/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Voir/i })).toBeInTheDocument()
  })
})

