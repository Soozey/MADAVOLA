import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useToast } from '../contexts/ToastContext'
import { getApiDetailFromError, getApiErrorMessage } from '../lib/apiErrors'
import './TransactionsPage.css'

type TransactionItemRow = { lot_id: number; quantity: number; unit_price: number }

export default function TransactionsPage() {
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [items, setItems] = useState<TransactionItemRow[]>([{ lot_id: 0, quantity: 0, unit_price: 0 }])
  const [validationError, setValidationError] = useState('')
  const queryClient = useQueryClient()
  const toast = useToast()

  useEffect(() => {
    if (showForm) setValidationError('')
  }, [showForm])

  const { data, isLoading } = useQuery({
    queryKey: ['transactions', page],
    queryFn: () => api.getTransactions({ page, page_size: 20 }),
  })

  const { data: actorsData } = useQuery({
    queryKey: ['actors', 'all'],
    queryFn: () => api.getActors({ page: 1, page_size: 500 }),
  })

  const { data: lotsData } = useQuery({
    queryKey: ['lots', 'all'],
    queryFn: () => api.getLots({ page: 1, page_size: 500 }),
  })

  const actors = actorsData?.items ?? []
  const lots = lotsData?.items ?? []

  const createMutation = useMutation({
    mutationFn: (payload: {
      seller_actor_id: number
      buyer_actor_id: number
      currency: string
      items: { lot_id: number; quantity: number; unit_price: number }[]
    }) => api.createTransaction(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      setShowForm(false)
      setItems([{ lot_id: 0, quantity: 0, unit_price: 0 }])
      toast.success('Transaction créée. Vous pouvez initier le paiement depuis le détail de la transaction.')
    },
  })

  const addLine = () => setItems((prev) => [...prev, { lot_id: 0, quantity: 0, unit_price: 0 }])
  const removeLine = (index: number) =>
    setItems((prev) => (prev.length <= 1 ? prev : prev.filter((_, i) => i !== index)))
  const updateLine = (index: number, field: keyof TransactionItemRow, value: number) =>
    setItems((prev) =>
      prev.map((line, i) => (i === index ? { ...line, [field]: value } : line))
    )

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const seller_actor_id = Number(formData.get('seller_actor_id'))
    const buyer_actor_id = Number(formData.get('buyer_actor_id'))
    const currency = formData.get('currency') as string
    const validItems = items.filter((row) => row.lot_id > 0 && row.quantity > 0 && row.unit_price >= 0)
    if (validItems.length === 0) {
      setValidationError('Ajoutez au moins une ligne avec un lot, une quantité et un prix unitaire.')
      return
    }
    setValidationError('')
    createMutation.mutate({
      seller_actor_id,
      buyer_actor_id,
      currency,
      items: validItems.map((row) => ({
        lot_id: row.lot_id,
        quantity: row.quantity,
        unit_price: row.unit_price,
      })),
    })
  }

  const errorDetail = createMutation.isError ? getApiDetailFromError(createMutation.error) : null
  const errorMessage =
    validationError ||
    (createMutation.isError ? getApiErrorMessage(errorDetail, 'Erreur lors de la création de la transaction.') : '')

  if (isLoading) return <div className="loading">Chargement...</div>

  return (
    <div className="transactions-page">
      <div className="page-header">
        <h1>Transactions</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Annuler' : '+ Nouvelle transaction'}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h2>Créer une transaction</h2>
          <p className="process-label">Étape 3 du processus : enregistrer une vente entre un vendeur et un acheteur (lots, quantités, prix). Le paiement peut être initié ensuite.</p>
          <form onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="seller_actor_id">Vendeur *</label>
                <select id="seller_actor_id" name="seller_actor_id" required>
                  <option value="">— Choisir —</option>
                  {actors.map((a: any) => (
                    <option key={a.id} value={a.id}>
                      {a.nom} {a.prenoms} ({a.email ?? a.telephone})
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="buyer_actor_id">Acheteur *</label>
                <select id="buyer_actor_id" name="buyer_actor_id" required>
                  <option value="">— Choisir —</option>
                  {actors.map((a: any) => (
                    <option key={a.id} value={a.id}>
                      {a.nom} {a.prenoms} ({a.email ?? a.telephone})
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="currency">Devise *</label>
                <select id="currency" name="currency" required>
                  <option value="">Sélectionner...</option>
                  <option value="MGA">MGA</option>
                  <option value="EUR">EUR</option>
                  <option value="USD">USD</option>
                </select>
              </div>
            </div>

            <div className="form-section">
              <div className="form-section-header">
                <label>Lignes de la transaction (lot, quantité, prix unitaire)</label>
                <button type="button" className="btn-secondary" onClick={addLine}>
                  + Ligne
                </button>
              </div>
              {items.map((row, index) => (
                <div key={index} className="form-row items-row">
                  <select
                    value={row.lot_id || ''}
                    onChange={(e) => updateLine(index, 'lot_id', Number(e.target.value))}
                    required
                  >
                    <option value="">— Lot —</option>
                    {lots.map((lot: any) => (
                      <option key={lot.id} value={lot.id}>
                        Lot #{lot.id} – {lot.product_type} ({lot.quantity} {lot.unit})
                      </option>
                    ))}
                  </select>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="Quantité"
                    value={row.quantity || ''}
                    onChange={(e) => updateLine(index, 'quantity', parseFloat(e.target.value) || 0)}
                  />
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="Prix unitaire"
                    value={row.unit_price || ''}
                    onChange={(e) => updateLine(index, 'unit_price', parseFloat(e.target.value) || 0)}
                  />
                  <button type="button" className="btn-secondary" onClick={() => removeLine(index)} disabled={items.length <= 1}>
                    −
                  </button>
                </div>
              ))}
            </div>

            {errorMessage && <div className="alert alert-error">{errorMessage}</div>}
            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Création...' : 'Créer'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Vendeur</th>
                <th>Acheteur</th>
                <th>Montant</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {data?.items?.length ? (
                data.items.map((txn: any) => (
                  <tr key={txn.id}>
                    <td><Link to={`/transactions/${txn.id}`}>{txn.id}</Link></td>
                    <td>{txn.seller_actor_id}</td>
                    <td>{txn.buyer_actor_id}</td>
                    <td>
                      <strong>{txn.total_amount}</strong> {txn.currency}
                    </td>
                    <td>
                      <span className={`status-badge status-${txn.status}`}>{txn.status}</span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5}>
                    <div className="empty-state-rich">
                      <div className="empty-title">Aucune transaction</div>
                      <p className="empty-desc">Les transactions enregistrent les ventes entre un vendeur et un acheteur (lots, quantités, prix). Créez une transaction pour enregistrer une vente ; le paiement peut être initié ensuite.</p>
                      <button type="button" className="btn-primary" onClick={() => setShowForm(true)}>
                        + Créer une transaction
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        {data && data.total_pages > 1 && (
          <div className="pagination">
            <div className="pagination-info">
              Page {data.page} sur {data.total_pages} ({data.total} total)
            </div>
            <div className="pagination-controls">
              <button
                className="btn-secondary"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Précédent
              </button>
              <button
                className="btn-secondary"
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= data.total_pages}
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
