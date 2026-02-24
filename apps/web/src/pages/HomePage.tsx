import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getRoleLabel } from '../config/rbac'
import { useSession } from '../contexts/SessionContext'
import './SessionSetup.css'

export default function HomePage() {
  const navigate = useNavigate()
  const { selectedRole, selectedFiliere } = useSession()

  useEffect(() => {
    if (!selectedRole || !selectedFiliere) return

    // Garde l'application maitre du retour navigateur sur /home.
    window.history.pushState({ homeGuard: true }, '', window.location.href)

    const onPopState = () => {
      const shouldExit = window.confirm('Quitter la page Accueil ? OK = revenir au choix filiere, Annuler = rester.')
      if (shouldExit) {
        navigate('/select-filiere', { replace: true })
        return
      }
      window.history.pushState({ homeGuard: true }, '', window.location.href)
    }

    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [navigate, selectedRole, selectedFiliere])

  if (!selectedRole || !selectedFiliere) {
    return <div className="loading">Preparation de la session...</div>
  }

  return (
    <div>
      <h1>Accueil</h1>
      <p>
        Role choisi: <strong>{getRoleLabel(selectedRole)}</strong> | Filiere choisie:{' '}
        <strong>{selectedFiliere}</strong>
      </p>

      <div className="home-grid">
        <section className="home-block">
          <h3>Session</h3>
          <ul className="home-list">
            <li>Le menu lateral applique le filtrage RBAC.</li>
            <li>Utilisez "Modifier profil" pour changer role/filiere.</li>
            <li>Utilisez "Changer filiere" pour conserver le role actif.</li>
          </ul>
        </section>

        <section className="home-block">
          <h3>Parcours recommande</h3>
          <ul className="home-list">
            <li>1. Acteurs: creation/validation.</li>
            <li>2. Lots: declaration + QR.</li>
            <li>3. Transactions/Trades: paiement puis transfert.</li>
            <li>4. Export/Controle: validation et traçabilite.</li>
          </ul>
        </section>
      </div>
    </div>
  )
}
