import { useAuth } from '../contexts/AuthContext'
import { QRCodeSVG } from 'qrcode.react'
import './DashboardPage.css'

export default function MaCartePage() {
  const { user } = useAuth()
  if (!user) return <div className="dashboard"><p className="error">Non connecté.</p></div>

  const verifyUrl = typeof window !== 'undefined' ? `${window.location.origin}/verify/actor/${user.id}` : ''

  return (
    <div className="dashboard">
      <h1>Ma carte</h1>
      <p className="dashboard-subtitle">Carte orpailleur / collecteur. Présentez ce QR code aux contrôleurs pour vérification.</p>
      <div className="card carte-qr-card">
        <div className="carte-qr-header">
          <h2>MADAVOLA</h2>
          <p className="carte-actor-name">{user.nom} {user.prenoms}</p>
          <p className="carte-actor-id">Acteur #{user.id}</p>
          {user.commune?.name && <p className="carte-commune">Commune : {user.commune.name}</p>}
        </div>
        <div className="carte-qr-code">
          <QRCodeSVG value={verifyUrl} size={200} level="M" includeMargin />
        </div>
        <p className="carte-qr-hint">Scanner ce code pour vérifier l&apos;identité</p>
      </div>
    </div>
  )
}
