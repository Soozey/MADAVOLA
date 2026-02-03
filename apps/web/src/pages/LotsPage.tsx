import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export default function LotsPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading } = useQuery({
    queryKey: ['lots', page],
    queryFn: () => api.getLots({ page, page_size: 20 }),
  })

  if (isLoading) return <div>Chargement...</div>

  return (
    <div>
      <h1 style={{ marginBottom: '30px' }}>Lots</h1>
      <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '20px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #ddd' }}>
              <th style={{ padding: '10px', textAlign: 'left' }}>ID</th>
              <th style={{ padding: '10px', textAlign: 'left' }}>Filière</th>
              <th style={{ padding: '10px', textAlign: 'left' }}>Type</th>
              <th style={{ padding: '10px', textAlign: 'left' }}>Quantité</th>
              <th style={{ padding: '10px', textAlign: 'left' }}>Unité</th>
              <th style={{ padding: '10px', textAlign: 'left' }}>Statut</th>
            </tr>
          </thead>
          <tbody>
            {data?.items?.map((lot: any) => (
              <tr key={lot.id} style={{ borderBottom: '1px solid #eee' }}>
                <td style={{ padding: '10px' }}>{lot.id}</td>
                <td style={{ padding: '10px' }}>{lot.filiere}</td>
                <td style={{ padding: '10px' }}>{lot.product_type}</td>
                <td style={{ padding: '10px' }}>{lot.quantity}</td>
                <td style={{ padding: '10px' }}>{lot.unit}</td>
                <td style={{ padding: '10px' }}>{lot.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {data && (
          <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              Page {data.page} sur {data.total_pages} ({data.total} total)
            </div>
            <div>
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                style={{ marginRight: '10px', padding: '8px 16px' }}
              >
                Précédent
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= data.total_pages}
                style={{ padding: '8px 16px' }}
              >
                Suivant
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
