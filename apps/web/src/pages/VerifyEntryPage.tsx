import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import './DashboardPage.css'

export default function VerifyEntryPage() {
  const [actorId, setActorId] = useState('')
  const navigate = useNavigate()

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const id = actorId.trim()
    if (id && /^\d+$/.test(id)) {
      navigate(`/verify/actor/${id}`)
    }
  }

  return (
    <div className="dashboard">
      <h1>Vérification acteur (QR)</h1>
      <p className="role-hint">
        Scannez le QR code d&apos;un acteur pour vérifier son identité, ou saisissez l&apos;ID acteur ci‑dessous.
      </p>
      <div className="card" style={{ maxWidth: 400 }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="actor-id">ID acteur</label>
            <input
              type="text"
              id="actor-id"
              value={actorId}
              onChange={(e) => setActorId(e.target.value)}
              placeholder="ex: 1"
              pattern="[0-9]+"
            />
          </div>
          <button type="submit" className="btn-primary">
            Vérifier
          </button>
        </form>
      </div>
    </div>
  )
}
