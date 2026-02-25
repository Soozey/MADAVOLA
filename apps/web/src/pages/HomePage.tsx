import { useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { getRoleLabel, getRoleProfile } from '../config/rbac'
import { useSession } from '../contexts/SessionContext'
import './SessionSetup.css'

type QuickAction = {
  label: string
  path: string
  hint: string
}

export default function HomePage() {
  const navigate = useNavigate()
  const { selectedRole, selectedFiliere } = useSession()

  useEffect(() => {
    if (!selectedRole || !selectedFiliere) return
    window.history.pushState({ homeGuard: true }, '', window.location.href)
    const onPopState = () => {
      const shouldExit = window.confirm('Quitter l’accueil ? OK = revenir au choix filière, Annuler = rester.')
      if (shouldExit) {
        navigate('/select-filiere', { replace: true })
        return
      }
      window.history.pushState({ homeGuard: true }, '', window.location.href)
    }
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [navigate, selectedRole, selectedFiliere])

  const actions = useMemo(() => {
    if (!selectedRole) return []
    const role = getRoleProfile(selectedRole).menuRole
    const map: Record<string, QuickAction[]> = {
      orpailleur: [
        { label: 'Déclarer une production', path: '/lots', hint: 'Créer un lot et générer le QR.' },
        { label: 'Vendre un lot', path: '/transactions', hint: 'Paiement puis transfert de propriété.' },
        { label: 'Voir ma carte', path: '/ma-carte', hint: 'Consulter votre carte et statut.' },
      ],
      collecteur: [
        { label: 'Acheter un lot', path: '/transactions', hint: 'Scanner ou sélectionner un lot.' },
        { label: 'Consolider des lots', path: '/trades', hint: 'Regrouper pour préparer la vente.' },
        { label: 'Suivre mes documents', path: '/documents', hint: 'Factures et pièces associées.' },
      ],
      commune: [
        { label: 'Traiter les demandes', path: '/actors', hint: 'Valider ou refuser les inscriptions.' },
        { label: 'Voir le tableau communal', path: '/dashboard/commune', hint: 'Recettes et activité locale.' },
        { label: 'Voir les notifications', path: '/notifications', hint: 'Demandes en attente et alertes.' },
      ],
      commune_agent: [
        { label: 'Traiter les demandes', path: '/actors', hint: 'Valider ou refuser les inscriptions.' },
        { label: 'Voir le tableau communal', path: '/dashboard/commune', hint: 'Recettes et activité locale.' },
        { label: 'Voir les notifications', path: '/notifications', hint: 'Demandes en attente et alertes.' },
      ],
      controleur: [
        { label: 'Scanner un QR', path: '/verify', hint: 'Vérification instantanée terrain.' },
        { label: 'Créer un contrôle', path: '/inspections', hint: 'OK, suspect ou infraction.' },
        { label: 'Suivre les sanctions', path: '/penalties', hint: 'Amendes, blocages, saisies.' },
      ],
      police: [
        { label: 'Scanner un QR', path: '/verify', hint: 'Vérification instantanée terrain.' },
        { label: 'Créer un contrôle', path: '/inspections', hint: 'OK, suspect ou infraction.' },
        { label: 'Suivre les sanctions', path: '/penalties', hint: 'Amendes, blocages, saisies.' },
      ],
      gendarmerie: [
        { label: 'Scanner un QR', path: '/verify', hint: 'Vérification instantanée terrain.' },
        { label: 'Créer un contrôle', path: '/inspections', hint: 'OK, suspect ou infraction.' },
        { label: 'Suivre les sanctions', path: '/penalties', hint: 'Amendes, blocages, saisies.' },
      ],
      comptoir_operator: [
        { label: 'Réceptionner des lots', path: '/lots', hint: 'Contrôle et intégration au stock.' },
        { label: 'Préparer un dossier export', path: '/exports', hint: 'Sélection lots et documents.' },
        { label: 'Suivre les pièces', path: '/documents', hint: 'Vérifier la complétude des dossiers.' },
      ],
      comptoir_compliance: [
        { label: 'Préparer un dossier export', path: '/exports', hint: 'Sélection lots et documents.' },
        { label: 'Suivre les pièces', path: '/documents', hint: 'Vérifier la complétude des dossiers.' },
        { label: 'Voir les alertes', path: '/notifications', hint: 'Anomalies et étapes en attente.' },
      ],
      comptoir_director: [
        { label: 'Préparer un dossier export', path: '/exports', hint: 'Sélection lots et documents.' },
        { label: 'Suivre les transactions', path: '/transactions', hint: 'Contrôle des paiements et transferts.' },
        { label: 'Voir les rapports', path: '/reports', hint: 'Volumes, valeurs, conformité.' },
      ],
      admin: [
        { label: 'Ouvrir le tableau de bord', path: '/dashboard', hint: 'Vue synthèse plateforme.' },
        { label: 'Gérer les acteurs', path: '/actors', hint: 'Validation, statuts et rôles.' },
        { label: 'Ouvrir les diagnostics', path: '/ops-coverage', hint: 'Contrôle API ↔ UI.' },
      ],
      dirigeant: [
        { label: 'Ouvrir la vue nationale', path: '/dashboard/national', hint: 'Indicateurs macro.' },
        { label: 'Voir les rapports', path: '/reports', hint: 'Production, ventes, export.' },
        { label: 'Voir les alertes', path: '/notifications', hint: 'Anomalies et points bloquants.' },
      ],
    }
    return map[role] || [
      { label: 'Déclarer / consulter des lots', path: '/lots', hint: 'Créer et suivre vos lots.' },
      { label: 'Suivre les transactions', path: '/transactions', hint: 'Paiements et transferts.' },
      { label: 'Voir les notifications', path: '/notifications', hint: 'Messages importants.' },
    ]
  }, [selectedRole])

  if (!selectedRole || !selectedFiliere) {
    return <div className="loading">Préparation de la session...</div>
  }

  const roleLabel = getRoleLabel(selectedRole)

  return (
    <div>
      <h1>Accueil</h1>
      <p>
        Rôle choisi: <strong>{roleLabel}</strong> | Filière choisie: <strong>{selectedFiliere}</strong>
      </p>

      <div className="home-grid">
        <section className="home-block">
          <h3>Action principale</h3>
          <p style={{ marginBottom: 12, color: 'var(--text-secondary)' }}>
            Démarrage rapide pour votre travail du jour.
          </p>
          <button className="btn-primary" onClick={() => navigate(actions[0].path)}>
            {actions[0].label}
          </button>
          <p style={{ marginTop: 10, color: 'var(--text-secondary)' }}>{actions[0].hint}</p>
        </section>

        <section className="home-block">
          <h3>Étapes rapides</h3>
          <ul className="home-list">
            {actions.slice(1).map((action) => (
              <li key={action.path}>
                <button
                  type="button"
                  className="btn-secondary"
                  style={{ marginRight: 8 }}
                  onClick={() => navigate(action.path)}
                >
                  {action.label}
                </button>
                {action.hint}
              </li>
            ))}
          </ul>
        </section>

        <section className="home-block">
          <h3>Besoin d’aide ?</h3>
          <ul className="home-list">
            <li>Le bouton principal vous mène à l’action prioritaire.</li>
            <li>“Modifier profil” permet de changer rôle/filière.</li>
            <li>Les autres modules restent accessibles via “Afficher tous les modules”.</li>
          </ul>
        </section>
      </div>
    </div>
  )
}
