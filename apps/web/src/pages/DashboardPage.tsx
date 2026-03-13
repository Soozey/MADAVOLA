import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useSession } from '../contexts/SessionContext'
import { api } from '../lib/api'
import {
  getVisibleMenuItems,
  canSeeDashboardNational,
  canSeeDashboardRegional,
  canSeeDashboardCommune,
  ROLE_LABELS,
} from '../config/rolesMenu'
import { getRoleProfile } from '../config/rbac'
import './DashboardPage.css'

type DashboardLot = {
  id: number
  product_type: string
  quantity: number
  unit: string
  status: string
}

type DashboardTxn = {
  id: number
  total_amount: number
  currency: string
  status: string
}

type Paginated<T> = {
  items: T[]
  total: number
}

export default function DashboardPage() {
  const { user } = useAuth()
  const { selectedRole } = useSession()
  const userRoles = user?.roles?.map((r) => r.role) ?? []
  const isAdmin = userRoles.includes('admin')
  const selectedMenuRole = selectedRole ? getRoleProfile(selectedRole).menuRole : null
  const effectiveRoles = isAdmin && selectedMenuRole ? [selectedMenuRole] : userRoles
  const visibleItems = getVisibleMenuItems(effectiveRoles)
  const showNational = canSeeDashboardNational(effectiveRoles)
  const showRegional = canSeeDashboardRegional(effectiveRoles)
  const showCommune = canSeeDashboardCommune(effectiveRoles)

  const { data: lots, isLoading: lotsLoading } = useQuery<Paginated<DashboardLot>>({
    queryKey: ['lots'],
    queryFn: () => api.getLots({ page: 1, page_size: 5 }),
  })

  const { data: transactions, isLoading: transactionsLoading } = useQuery<Paginated<DashboardTxn>>({
    queryKey: ['transactions'],
    queryFn: () => api.getTransactions({ page: 1, page_size: 5 }),
  })

  const roleLabels = effectiveRoles.map((r) => ROLE_LABELS[r] || r).join(', ') || 'Aucun role'

  return (
    <div className="dashboard">
      <div className="welcome-banner">
        <h2>Bienvenue, {user?.nom} {user?.prenoms}</h2>
        <p>
          Affiche en tant que : <strong>{roleLabels}</strong>. Acces selon les habilitations du role actif
          (menu a gauche).
        </p>
        <div className="quick-links">
          {showNational && <Link to="/dashboard/national">Vue nationale</Link>}
          {showRegional && <Link to="/dashboard/regional">Vue regionale</Link>}
          {showCommune && <Link to="/dashboard/commune">Vue communale</Link>}
          {visibleItems.some((i) => i.path === '/actors') && <Link to="/actors">Acteurs</Link>}
          {visibleItems.some((i) => i.path === '/lots') && <Link to="/lots">Lots</Link>}
          {visibleItems.some((i) => i.path === '/transactions') && <Link to="/transactions">Transactions</Link>}
        </div>
      </div>

      <div className="process-card">
        <h3>Processus metier MADAVOLA</h3>
        <ol className="process-steps" style={{ listStyle: 'decimal', paddingLeft: '1.5rem' }}>
          <li style={{ marginBottom: '0.5rem' }}>
            <strong>Inscription acteur</strong> - Creer un acteur (collecteur, operateur) avec localisation
            (Region - District - Commune) et point GPS. Validation par la commune si necessaire.
          </li>
          <li style={{ marginBottom: '0.5rem' }}>
            <strong>Declaration de lot</strong> - Declarer un lot (filiere, type, quantite) avec lieu GPS.
            Le grand livre est mis a jour automatiquement.
          </li>
          <li style={{ marginBottom: '0.5rem' }}>
            <strong>Transaction et paiement</strong> - Creer une transaction (vendeur vers acheteur, lots, prix).
            Initier le paiement; la facture est generee apres confirmation.
          </li>
          <li>
            <strong>Exportation / transfert</strong> - Exportations et transferts de lots selon la filiere
            (OR, PIERRE, BOIS).
          </li>
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
              <span className="info-label">Telephone:</span>
              <span className="info-value">{user?.telephone}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Commune:</span>
              <span className="info-value">{user?.commune?.name || 'N/A'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Roles:</span>
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
              {lots.items.map((lot) => (
                <li key={lot.id} className="list-item">
                  <div className="list-item-content">
                    <div className="list-item-title">{lot.product_type}</div>
                    <div className="list-item-subtitle">
                      {lot.quantity} {lot.unit} - {lot.status}
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
          <h3>Dernieres transactions</h3>
          {transactionsLoading ? (
            <div className="loading">Chargement...</div>
          ) : transactions?.items?.length ? (
            <ul className="list">
              {transactions.items.map((txn) => (
                <li key={txn.id} className="list-item">
                  <div className="list-item-content">
                    <div className="list-item-title">Transaction #{txn.id}</div>
                    <div className="list-item-subtitle">
                      {txn.total_amount} {txn.currency} - {txn.status}
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

