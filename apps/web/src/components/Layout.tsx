import { useEffect } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { getVisibleMenuItems } from '../config/rolesMenu'
import './Layout.css'

export default function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const userRoles = user?.roles?.map((r) => r.role) ?? []
  const effectiveRoles = userRoles
  const menuItems = getVisibleMenuItems(effectiveRoles)

  // Si la page actuelle n'est pas dans le menu du rÃ´le affichÃ©, rediriger vers le tableau de bord
  useEffect(() => {
    const path = location.pathname
    const allowedPaths = menuItems.map((item) => item.path)
    const isAllowed =
      path === '/' ||
      path === '/dashboard' ||
      allowedPaths.some((p) => path === p || path.startsWith(p + '/'))
    if (!isAllowed && menuItems.length > 0) {
      navigate('/dashboard', { replace: true })
    }
  }, [location.pathname, menuItems, navigate])

  const isActive = (path: string) => {
    if (path === '/dashboard') return location.pathname === '/dashboard' || location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <h2>MADAVOLA</h2>
        </div>
        <nav className="sidebar-nav">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-link ${isActive(item.path) ? 'active' : ''}`}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-name">{user?.nom} {user?.prenoms}</div>
            <div className="user-email">{user?.email}</div>
            <div className="user-roles">
              {userRoles.length ? userRoles.join(', ') : 'Aucun rÃ´le'}
            </div>
          </div>
          <button onClick={logout} className="btn-danger" style={{ width: '100%' }}>
            DÃ©connexion
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
