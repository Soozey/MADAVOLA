import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import './DashboardPage.css'

export default function VerifyEntryPage() {
  const [kind, setKind] = useState<'actor' | 'lot' | 'invoice'>('actor')
  const [value, setValue] = useState('')
  const navigate = useNavigate()

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const id = value.trim()
    if (!id) return
    if (kind === 'invoice') {
      navigate(`/verify/invoice/${encodeURIComponent(id)}`)
      return
    }
    if (/^\d+$/.test(id)) {
      navigate(`/verify/${kind}/${id}`)
    }
  }

  return (
    <div className="dashboard">
      <h1>Verification QR</h1>
      <p className="role-hint">
        Controle terrain: verification acteur, lot ou facture.
      </p>
      <div className="card" style={{ maxWidth: 420 }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="kind">Type</label>
            <select id="kind" value={kind} onChange={(e) => setKind(e.target.value as any)}>
              <option value="actor">Acteur</option>
              <option value="lot">Lot</option>
              <option value="invoice">Facture</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="verify-id">{kind === 'invoice' ? 'Numero ou ID facture' : `ID ${kind}`}</label>
            <input
              type="text"
              id="verify-id"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={kind === 'invoice' ? 'INV-00000001 ou 1' : '1'}
              pattern={kind === 'invoice' ? undefined : '[0-9]+'}
            />
          </div>
          <button type="submit" className="btn-primary">
            Verifier
          </button>
        </form>
      </div>
    </div>
  )
}
