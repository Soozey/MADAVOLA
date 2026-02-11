import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'
import { getVisibleMenuItems, canSeeDashboardNational, canSeeDashboardRegional, canSeeDashboardCommune, ROLE_LABELS } from '../config/rolesMenu'
import './DashboardPage.css'

export default function DashboardPage() {
  const { user } = useAuth()
  const userRoles = user?.roles?.map((r) => r.role) ?? []
  const effectiveRoles = userRoles
  const visibleItems = getVisibleMenuItems(effectiveRoles)
  const showNational = canSeeDashboardNational(effectiveRoles)
  const showRegional = canSeeDashboardRegional(effectiveRoles)
  const showCommune = canSeeDashboardCommune(effectiveRoles)

  const { data: lots, isLoading: lotsLoading } = useQuery({
    queryKey: ['lots'],
    queryFn: () => api.getLots({ page: 1, page_size: 5 }),
  })

  const { data: transactions, isLoading: transactionsLoading } = useQuery({
    queryKey: ['transactions'],
    queryFn: () => api.getTransactions({ page: 1, page_size: 5 }),
  })

  const roleLabels = effectiveRoles.map((r) => ROLE_LABELS[r] || r).join(', ') || 'Aucun rÃ´le'

  return (
    <div className="dashboard">
      <div className="welcome-banner">
        <h2>Bienvenue, {user?.nom} {user?.prenoms}</h2>
        <p>AffichÃ© en tant que : <strong>{roleLabels}</strong>. AccÃ¨s selon les habilitations de ce rÃ´le (menu Ã  gauche).</p>
        <div className="quick-links">
          {showNational && <Link to="/dashboard/national">Vue nationale</Link>}
          {showRegional && <Link to="/dashboard/regional">Vue rÃ©gionale</Link>}
          {showCommune && <Link to="/dashboard/commune">Vue communale</Link>}
          {visibleItems.some((i) => i.path === '/actors') && <Link to="/actors">Acteurs</Link>}
          {visibleItems.some((i) => i.path === '/lots') && <Link to="/lots">Lots</Link>}
          {visibleItems.some((i) => i.path === '/transactions') && <Link to="/transactions">Transactions</Link>}
        </div>
      </div>

      <div className="process-card">
        <h3>Processus mÃ©tier MADAVOLA</h3>
        <ol className="process-steps" style={{ listStyle: 'decimal', paddingLeft: '1.5rem' }}>
          <li style={{ marginBottom: '0.5rem' }}><strong>Inscription acteur</strong> â€” CrÃ©er un acteur (collecteur, opÃ©rateur) avec localisation (RÃ©gion â†’ District â†’ Commune) et point GPS. Validation par la commune si nÃ©cessaire.</li>
          <li style={{ marginBottom: '0.5rem' }}><strong>DÃ©claration de lot</strong> â€” DÃ©clarer un lot (filiÃ¨re, type, quantitÃ©) avec lieu GPS. Le grand livre (ledger) est mis Ã  jour automatiquement.</li>
          <li style={{ marginBottom: '0.5rem' }}><strong>Transaction et paiement</strong> â€” CrÃ©er une transaction (vendeur â†’ acheteur, lots, prix). Initier le paiement ; la facture est gÃ©nÃ©rÃ©e aprÃ¨s confirmation.</li>
          <li><strong>Export / transfert</strong> â€” Exports et transferts de lots selon la filiÃ¨re (or, bois, etc.).</li>
        </ol>
      </div>

      <h1>Tableau de bord</h1>
      
      <div className="dashboard-grid">
        <div className="card profile-card">
          <h2>Profil</h2>
          <div className="profile-info">
            <div className="info-item">
              <span className="info-label">Nom:</span>
              <span className="info-value">{user?.nom} {user?.prenoms}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Email:</span>
              <span className="info-value">{user?.email}</span>
            </div>
            <div className="info-item">
              <span className="info-label">TÃ©lÃ©phone:</span>
              <span className="info-value">{user?.telephone}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Commune:</span>
              <span className="info-value">{user?.commune?.name || 'N/A'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">RÃ´les:</span>
              <span className="info-value">
                {user?.roles.map((r) => r.role).join(', ') || 'Aucun'}
              </span>
            </div>
          </div>
        </div>

        <div className="card stats-card">
          <h2>Statistiques</h2>
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-value">{lots?.total || 0}</div>
              <div className="stat-label">Lots totaux</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{transactions?.total || 0}</div>
              <div className="stat-label">Transactions</div>
            </div>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <h3>Derniers lots</h3>
          {lotsLoading ? (
            <div className="loading">Chargement...</div>
          ) : lots?.items?.length ? (
            <ul className="list">
              {lots.items.map((lot: any) => (
                <li key={lot.id} className="list-item">
                  <div className="list-item-content">
                    <div className="list-item-title">{lot.product_type}</div>
                    <div className="list-item-subtitle">
                      {lot.quantity} {lot.unit} â€¢ {lot.status}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-state">Aucun lot</div>
          )}
        </div>

        <div className="card">
          <h3>DerniÃ¨res transactions</h3>
          {transactionsLoading ? (
            <div className="loading">Chargement...</div>
          ) : transactions?.items?.length ? (
            <ul className="list">
              {transactions.items.map((txn: any) => (
                <li key={txn.id} className="list-item">
                  <div className="list-item-content">
                    <div className="list-item-title">Transaction #{txn.id}</div>
                    <div className="list-item-subtitle">
                      {txn.total_amount} {txn.currency} â€¢ {txn.status}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="empty-state">Aucune transaction</div>
          )}
        </div>
      </div>
    </div>
  )
}
