import { useNavigate } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'
import './SessionSetup.css'

export default function SplashPage() {
  const navigate = useNavigate()
  const { selectedRole, selectedFiliere } = useSession()

  const handleContinue = () => {
    if (!selectedRole) {
      navigate('/select-role')
      return
    }
    if (!selectedFiliere) {
      navigate('/select-filiere')
      return
    }
    navigate('/home')
  }

  return (
    <div className="session-page">
      <div className="session-card">
        <h1 className="session-title">MADAVOLA</h1>
        <p className="session-subtitle">
          Plateforme de demonstration multi roles et multi filieres.
        </p>
        <div className="session-actions">
          <button className="btn-primary" onClick={handleContinue}>
            Continuer
          </button>
        </div>
      </div>
    </div>
  )
}
