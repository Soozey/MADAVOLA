import { useEffect, useMemo, useState } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { useSession } from '../contexts/SessionContext'
import { getVisibleMenuItems, MENU_ITEMS, type MenuItem } from '../config/rolesMenu'
import { getRoleLabel, getRoleProfile } from '../config/rbac'
import { api } from '../lib/api'
import './Layout.css'

export default function Layout() {
  const { user, logout } = useAuth()
  const { selectedRole, selectedFiliere, changeProfile, changeFiliere, resetSession } = useSession()
  const location = useLocation()
  const navigate = useNavigate()
  const [showAllModules, setShowAllModules] = useState(false)

  const userRoles = user?.roles?.map((r) => r.role) ?? []
  const isAdmin = userRoles.includes('admin')
  const selectedMenuRole = selectedRole ? getRoleProfile(selectedRole).menuRole : null
  const effectiveRoles = isAdmin && selectedMenuRole ? [selectedMenuRole] : userRoles
  const staticMenuItems = getVisibleMenuItems(effectiveRoles)
  const { data: selectedRolePermissions = [] } = useQuery({
    queryKey: ['rbac', 'permissions', selectedRole],
    queryFn: async () => {
      if (!selectedRole) return []
      const out = await api.getRbacPermissions(selectedRole)
      return out.permissions || []
    },
    enabled: !!selectedRole,
  })
  const inferredPaths = new Set<string>()
  const permissionMap: Array<{ match: (p: string) => boolean; paths: string[] }> = [
    { match: (p) => p.includes('admin_commune') || p.includes('card_'), paths: ['/actors', '/notifications', '/or-compliance'] },
    { match: (p) => p.includes('declare_lot') || p.startsWith('lot_'), paths: ['/lots'] },
    { match: (p) => p.includes('trade') || p.includes('transaction'), paths: ['/transactions', '/trades'] },
    { match: (p) => p.includes('export') || p.includes('douane') || p.includes('gue'), paths: ['/exports'] },
    { match: (p) => p.includes('transport'), paths: ['/transports'] },
    { match: (p) => p.includes('transform') || p.includes('lapidaire') || p.includes('raffinerie'), paths: ['/transformations'] },
    { match: (p) => p.includes('controle') || p.includes('inspection') || p.includes('profil_controleur'), paths: ['/inspections', '/violations', '/verify'] },
    { match: (p) => p.includes('audit'), paths: ['/audit'] },
    { match: (p) => p.includes('message') || p.includes('contact'), paths: ['/messages'] },
    { match: (p) => p.includes('market') || p.includes('offre'), paths: ['/marketplace'] },
    { match: (p) => p.includes('dashboard') || p.includes('lecture_seule') || p.includes('report'), paths: ['/dashboard', '/reports'] },
  ]
  for (const permission of selectedRolePermissions) {
    for (const rule of permissionMap) {
      if (rule.match(permission)) {
        for (const path of rule.paths) inferredPaths.add(path)
      }
    }
  }
  inferredPaths.add('/home')
  inferredPaths.add('/notifications')
  const inferredItems = MENU_ITEMS.filter((item) => inferredPaths.has(item.path))
  const menuItems: MenuItem[] = staticMenuItems.length > 0 ? staticMenuItems : inferredItems
  const financePaths = new Set(['/transactions', '/trades', '/invoices', '/ledger'])
  const roleForUx = selectedMenuRole || effectiveRoles[0] || ''
  const dailyPaths = useMemo(() => {
    const map: Record<string, string[]> = {
      orpailleur: ['/lots', '/transactions', '/or-compliance', '/notifications'],
      collecteur: ['/lots', '/trades', '/transactions', '/notifications'],
      commune: ['/actors', '/dashboard/commune', '/notifications'],
      commune_agent: ['/actors', '/dashboard/commune', '/notifications'],
      police: ['/verify', '/inspections', '/violations', '/notifications'],
      gendarmerie: ['/verify', '/inspections', '/violations', '/notifications'],
      controleur: ['/verify', '/inspections', '/violations', '/notifications'],
      comptoir_operator: ['/lots', '/exports', '/documents', '/notifications'],
      comptoir_compliance: ['/lots', '/exports', '/documents', '/notifications'],
      comptoir_director: ['/lots', '/exports', '/documents', '/notifications'],
      admin: menuItems.map((item) => item.path),
      dirigeant: menuItems.map((item) => item.path),
    }
    const defaults = ['/lots', '/transactions', '/notifications']
    return new Set(map[roleForUx] || defaults)
  }, [menuItems, roleForUx])
  const dailyItems = menuItems.filter((item) => dailyPaths.has(item.path))
  const otherItems = menuItems.filter((item) => !dailyPaths.has(item.path))
  const displayedItems = showAllModules ? menuItems : dailyItems
  const financeItems = displayedItems.filter((item) => financePaths.has(item.path))
  const coreItems = displayedItems.filter((item) => !financePaths.has(item.path))

  useEffect(() => {
    const path = location.pathname
    const allowedPaths = menuItems.map((item) => item.path)
    const isAllowed =
      path === '/' ||
      path === '/home' ||
      path === '/dashboard' ||
      path === '/profile' ||
      path === '/ma-carte' ||
      allowedPaths.some((p) => path === p || path.startsWith(p + '/'))
    if (!isAllowed && menuItems.length > 0) {
      navigate('/home', { replace: true })
    }
  }, [location.pathname, menuItems, navigate])

  const isActive = (path: string) => {
    if (path === '/dashboard') return location.pathname === '/dashboard' || location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  const handleChangeProfile = () => {
    changeProfile()
    navigate('/select-role')
  }

  const handleOpenProfile = () => {
    navigate('/profile')
  }

  const handleChangeFiliere = () => {
    changeFiliere()
    navigate('/select-filiere')
  }

  const handleResetSession = () => {
    resetSession()
    navigate('/select-role')
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>MADAVOLA</h2>
        </div>
        <nav className="sidebar-nav">
          <Link to="/home" className={`nav-link ${isActive('/home') ? 'active' : ''}`}>
            <span>{'>'}</span>
            Accueil
          </Link>
          <div className="nav-section-title">{showAllModules ? 'Modules' : 'Tâches du jour'}</div>
          {coreItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-link ${isActive(item.path) ? 'active' : ''}`}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          ))}
          {financeItems.length > 0 && (
            <>
              <div className="nav-section-title">Finance</div>
              {financeItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`nav-link ${isActive(item.path) ? 'active' : ''}`}
                >
                  <span>{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </>
          )}
          {otherItems.length > 0 && (
            <button
              type="button"
              className="nav-toggle-btn"
              onClick={() => setShowAllModules((v) => !v)}
            >
              {showAllModules ? 'Masquer modules avancés' : 'Afficher tous les modules'}
            </button>
          )}
        </nav>
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-name">{user?.nom} {user?.prenoms}</div>
            <div className="user-email">{user?.email}</div>
            <div className="user-roles">{userRoles.length ? userRoles.join(', ') : 'Aucun role'}</div>
            <div className="user-session">
              {selectedRole ? getRoleLabel(selectedRole) : 'Role non defini'} |{' '}
              {selectedFiliere ?? 'Filiere non definie'}
            </div>
          </div>
          <button onClick={handleOpenProfile} className="btn-secondary session-action-btn">
            Mon profil
          </button>
          <button onClick={handleChangeProfile} className="btn-secondary session-action-btn">
            Changer role
          </button>
          <button onClick={handleChangeFiliere} className="btn-secondary session-action-btn">
            Changer filiere
          </button>
          <button onClick={handleResetSession} className="btn-secondary session-action-btn">
            Reinitialiser session
          </button>
          <button onClick={logout} className="btn-danger" style={{ width: '100%' }}>
            Deconnexion
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
