import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()

  const isActive = (path: string) => location.pathname === path

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside
        style={{
          width: '250px',
          backgroundColor: '#1a1a1a',
          padding: '20px',
          color: 'white',
        }}
      >
        <h2 style={{ marginBottom: '30px' }}>MADAVOLA</h2>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <Link
            to="/dashboard"
            style={{
              padding: '10px',
              borderRadius: '4px',
              textDecoration: 'none',
              color: isActive('/dashboard') ? '#fff' : '#aaa',
              backgroundColor: isActive('/dashboard') ? '#333' : 'transparent',
            }}
          >
            Dashboard
          </Link>
          <Link
            to="/actors"
            style={{
              padding: '10px',
              borderRadius: '4px',
              textDecoration: 'none',
              color: isActive('/actors') ? '#fff' : '#aaa',
              backgroundColor: isActive('/actors') ? '#333' : 'transparent',
            }}
          >
            Acteurs
          </Link>
          <Link
            to="/lots"
            style={{
              padding: '10px',
              borderRadius: '4px',
              textDecoration: 'none',
              color: isActive('/lots') ? '#fff' : '#aaa',
              backgroundColor: isActive('/lots') ? '#333' : 'transparent',
            }}
          >
            Lots
          </Link>
          <Link
            to="/transactions"
            style={{
              padding: '10px',
              borderRadius: '4px',
              textDecoration: 'none',
              color: isActive('/transactions') ? '#fff' : '#aaa',
              backgroundColor: isActive('/transactions') ? '#333' : 'transparent',
            }}
          >
            Transactions
          </Link>
        </nav>
        <div style={{ marginTop: 'auto', paddingTop: '30px' }}>
          <div style={{ marginBottom: '10px', fontSize: '14px' }}>
            {user?.nom} {user?.prenoms}
          </div>
          <button
            onClick={logout}
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#d32f2f',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Déconnexion
          </button>
        </div>
      </aside>
      <main style={{ flex: 1, padding: '20px', backgroundColor: '#f5f5f5' }}>
        <Outlet />
      </main>
    </div>
  )
}
