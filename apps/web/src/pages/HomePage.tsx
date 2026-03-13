import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getRoleLabel, getRoleProfile } from '../config/rbac'
import { useAuth } from '../contexts/AuthContext'
import { useSession } from '../contexts/SessionContext'
import { api } from '../lib/api'
import './SessionSetup.css'

type QuickAction = {
  label: string
  path: string
  hint: string
}

export default function HomePage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { selectedRole, selectedFiliere } = useSession()
  const [institutionalMessageDraft, setInstitutionalMessageDraft] = useState('')

  const { data: widgets } = useQuery({
    queryKey: ['home-widgets'],
    queryFn: () => api.getHomeWidgets(),
    enabled: !!user,
  })

  const publishMessageMutation = useMutation({
    mutationFn: (message: string) => api.publishInstitutionalMessage(message),
    onSuccess: (data) => {
      setInstitutionalMessageDraft(data?.institutional_message || '')
    },
  })

  const actions = useMemo(() => {
    if (!selectedRole) return []
    const role = getRoleProfile(selectedRole).menuRole
    const map: Record<string, QuickAction[]> = {
      orpailleur: [
        { label: 'Declarer une production', path: '/lots', hint: 'Creer un lot et generer le QR.' },
        { label: 'Vendre un lot', path: '/transactions', hint: 'Paiement puis transfert de propriete.' },
        { label: 'Voir mes cartes OR', path: '/or-compliance', hint: 'Consulter votre carte et statut.' },
      ],
      collecteur: [
        { label: 'Acheter un lot', path: '/transactions', hint: 'Scanner ou selectionner un lot.' },
        { label: 'Consolider des lots', path: '/trades', hint: 'Regrouper pour preparer la vente.' },
        { label: 'Suivre mes documents', path: '/documents', hint: 'Factures et pieces associees.' },
      ],
      commune: [
        { label: 'Traiter les demandes', path: '/actors', hint: 'Valider ou refuser les inscriptions.' },
        { label: 'Voir le tableau communal', path: '/dashboard/commune', hint: 'Recettes et activite locale.' },
        { label: 'Voir les notifications', path: '/notifications', hint: 'Demandes en attente et alertes.' },
      ],
      commune_agent: [
        { label: 'Traiter les demandes', path: '/actors', hint: 'Valider ou refuser les inscriptions.' },
        { label: 'Voir le tableau communal', path: '/dashboard/commune', hint: 'Recettes et activite locale.' },
        { label: 'Voir les notifications', path: '/notifications', hint: 'Demandes en attente et alertes.' },
      ],
      controleur: [
        { label: 'Scanner un QR', path: '/verify', hint: 'Verification instantanee terrain.' },
        { label: 'Creer un controle', path: '/inspections', hint: 'OK, suspect ou infraction.' },
        { label: 'Suivre les sanctions', path: '/penalties', hint: 'Amendes, blocages, saisies.' },
      ],
      police: [
        { label: 'Scanner un QR', path: '/verify', hint: 'Verification instantanee terrain.' },
        { label: 'Creer un controle', path: '/inspections', hint: 'OK, suspect ou infraction.' },
        { label: 'Suivre les sanctions', path: '/penalties', hint: 'Amendes, blocages, saisies.' },
      ],
      gendarmerie: [
        { label: 'Scanner un QR', path: '/verify', hint: 'Verification instantanee terrain.' },
        { label: 'Creer un controle', path: '/inspections', hint: 'OK, suspect ou infraction.' },
        { label: 'Suivre les sanctions', path: '/penalties', hint: 'Amendes, blocages, saisies.' },
      ],
      comptoir_operator: [
        { label: 'Receptionner des lots', path: '/lots', hint: 'Controle et integration au stock.' },
        { label: 'Preparer un dossier export', path: '/exports', hint: 'Selection lots et documents.' },
        { label: 'Suivre les pieces', path: '/documents', hint: 'Verifier la completude des dossiers.' },
      ],
      comptoir_compliance: [
        { label: 'Preparer un dossier export', path: '/exports', hint: 'Selection lots et documents.' },
        { label: 'Suivre les pieces', path: '/documents', hint: 'Verifier la completude des dossiers.' },
        { label: 'Voir les alertes', path: '/notifications', hint: 'Anomalies et etapes en attente.' },
      ],
      comptoir_director: [
        { label: 'Preparer un dossier export', path: '/exports', hint: 'Selection lots et documents.' },
        { label: 'Suivre les transactions', path: '/transactions', hint: 'Controle des paiements et transferts.' },
        { label: 'Voir les rapports', path: '/reports', hint: 'Volumes, valeurs, conformite.' },
      ],
      admin: [
        { label: 'Ouvrir le tableau de bord', path: '/dashboard', hint: 'Vue synthese plateforme.' },
        { label: 'Gerer les acteurs', path: '/actors', hint: 'Validation, statuts et roles.' },
        { label: 'Ouvrir les diagnostics', path: '/ops-coverage', hint: 'Controle API <-> UI.' },
      ],
      dirigeant: [
        { label: 'Ouvrir la vue nationale', path: '/dashboard/national', hint: 'Indicateurs macro.' },
        { label: 'Voir les rapports', path: '/reports', hint: 'Production, ventes, export.' },
        { label: 'Voir les alertes', path: '/notifications', hint: 'Anomalies et points bloquants.' },
      ],
    }
    return map[role] || [
      { label: 'Declarer / consulter des lots', path: '/lots', hint: 'Creer et suivre vos lots.' },
      { label: 'Suivre les transactions', path: '/transactions', hint: 'Paiements et transferts.' },
      { label: 'Voir les notifications', path: '/notifications', hint: 'Messages importants.' },
    ]
  }, [selectedRole])

  if (!selectedRole || !selectedFiliere) {
    return <div className="loading">Preparation de la session...</div>
  }

  const roleLabel = getRoleLabel(selectedRole)
  const userRoleCodes = user?.roles?.map((r) => r.role) || []
  const canPublishInstitutionalMessage = userRoleCodes.some((r) => ['admin', 'dirigeant', 'president', 'pr'].includes(r))

  return (
    <div>
      <h1>Accueil</h1>
      <p>
        Role choisi: <strong>{roleLabel}</strong> | Filiere choisie: <strong>{selectedFiliere}</strong>
      </p>

      {(widgets?.institutional_message || canPublishInstitutionalMessage) && (
        <section className="home-block" style={{ marginBottom: 16 }}>
          <h3>Message institutionnel</h3>
          {widgets?.institutional_message && (
            <p>
              {widgets.institutional_message}
              {widgets?.institutional_message_updated_at ? ` (mis a jour: ${new Date(widgets.institutional_message_updated_at).toLocaleString()})` : ''}
            </p>
          )}
          {canPublishInstitutionalMessage && (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <input
                type="text"
                value={institutionalMessageDraft}
                onChange={(e) => setInstitutionalMessageDraft(e.target.value)}
                placeholder="Publier un message institutionnel"
                style={{ minWidth: 320, flex: 1 }}
              />
              <button
                className="btn-primary"
                onClick={() => publishMessageMutation.mutate(institutionalMessageDraft)}
                disabled={publishMessageMutation.isPending || !institutionalMessageDraft.trim()}
              >
                {publishMessageMutation.isPending ? 'Publication...' : 'Publier'}
              </button>
            </div>
          )}
        </section>
      )}

      <section className="home-block" style={{ marginBottom: 16 }}>
        <h3>Cours de l'or</h3>
        <p>
          {widgets?.gold_price_value != null
            ? `${widgets.gold_price_value} ${widgets.gold_price_currency || 'MGA'} / ${widgets.gold_price_unit || 'g'}`
            : 'Non configure'}
        </p>
        <p style={{ color: 'var(--text-secondary)' }}>
          Source: {widgets?.gold_price_source || 'parametre admin'} | Mise a jour: {widgets?.gold_price_updated_at ? new Date(widgets.gold_price_updated_at).toLocaleString() : '-'}
        </p>
      </section>

      <div className="home-grid">
        <section className="home-block">
          <h3>Action principale</h3>
          <p style={{ marginBottom: 12, color: 'var(--text-secondary)' }}>
            Demarrage rapide pour votre travail du jour.
          </p>
          <button className="btn-primary" onClick={() => navigate(actions[0].path)}>
            {actions[0].label}
          </button>
          <p style={{ marginTop: 10, color: 'var(--text-secondary)' }}>{actions[0].hint}</p>
        </section>

        <section className="home-block">
          <h3>Etapes rapides</h3>
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
          <h3>Besoin d'aide ?</h3>
          <ul className="home-list">
            <li>Le bouton principal vous mene a l'action prioritaire.</li>
            <li>"Mon profil" permet de completer l'identite (CIN, adresse, photo).</li>
            <li>Les autres modules restent accessibles via "Afficher tous les modules".</li>
          </ul>
        </section>
      </div>
    </div>
  )
}
