import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FILIERES, Filiere, getRoleProfile } from '../config/rbac'
import { useSession } from '../contexts/SessionContext'
import './SessionSetup.css'

export default function FiliereSelectPage() {
  const navigate = useNavigate()
  const { selectedRole, selectedFiliere, setSelectedFiliere } = useSession()
  const [draftFiliere, setDraftFiliere] = useState<Filiere | null>(selectedFiliere ?? FILIERES[0])

  const allowedFilieres = useMemo(() => {
    if (!selectedRole) return FILIERES
    return getRoleProfile(selectedRole).supportedFilieres
  }, [selectedRole])

  useEffect(() => {
    if (!draftFiliere && allowedFilieres.length > 0) {
      setDraftFiliere(allowedFilieres[0])
    }
  }, [allowedFilieres, draftFiliere])

  const handleValidate = () => {
    if (!draftFiliere) return
    setSelectedFiliere(draftFiliere)
    navigate('/home')
  }

  return (
    <div className="session-page">
      <div className="session-card">
        <h1 className="session-title">Choisir votre filiere</h1>
        <p className="session-subtitle">
          Etape B - Selection filiere (OR / PIERRE / BOIS), puis redirection vers le home specifique.
        </p>

        <div className="choice-grid">
          {allowedFilieres.map((filiere) => (
            <button
              key={filiere}
              type="button"
              data-testid={`filiere-choice-${String(filiere).toLowerCase()}`}
              className={`choice-card ${draftFiliere === filiere ? 'active' : ''}`}
              onClick={() => setDraftFiliere(filiere)}
            >
              <div className="choice-card-title">{filiere}</div>
              <div className="choice-card-subtitle">Filiere active pour cette session</div>
            </button>
          ))}
        </div>

        <div className="session-actions">
          <button className="btn-secondary" onClick={() => navigate('/select-role')}>
            Retour
          </button>
          <button className="btn-primary" data-testid="filiere-validate" onClick={handleValidate} disabled={!draftFiliere}>
            Valider
          </button>
        </div>
      </div>
    </div>
  )
}
