import { Navigate, useLocation } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'
import { useAuth } from '../contexts/AuthContext'
import { extractActiveRoles, pickPrimaryRole, resolveFiliereForRole } from '../utils/sessionDefaults'

export function SessionGuard({ children }: { children: React.ReactNode }) {
  const { selectedRole, selectedFiliere } = useSession()
  const { user, loading } = useAuth()
  const location = useLocation()
  const path = location.pathname

  const isRoleRoute = path === '/select-role'
  const isFiliereRoute = path === '/select-filiere'
  const isPasswordRoute = path === '/change-password'
  const storedRole = localStorage.getItem('selectedRole')
  const storedFiliere = localStorage.getItem('selectedFiliere')
  const availableRoles = extractActiveRoles(user?.roles || [])
  const hasMultipleRoles = availableRoles.length > 1
  const selectedRoleIsValid = !!selectedRole && availableRoles.includes(selectedRole)
  const storedRoleIsValid = !!storedRole && availableRoles.includes(storedRole)
  const normalizedSelectedRole = selectedRoleIsValid ? selectedRole : null
  const normalizedStoredRole = storedRoleIsValid ? storedRole : null
  const derivedRole = hasMultipleRoles
    ? null
    : pickPrimaryRole(user?.roles || [], normalizedSelectedRole || normalizedStoredRole)
  const effectiveRole = normalizedSelectedRole || (normalizedStoredRole as typeof selectedRole) || derivedRole
  const effectiveFiliere = selectedFiliere || (storedFiliere as typeof selectedFiliere) || resolveFiliereForRole(effectiveRole, storedFiliere)

  if (loading) {
    return <div className="loading">Chargement...</div>
  }

  if (user?.must_change_password) {
    if (!isPasswordRoute) {
      return <Navigate to="/change-password" replace />
    }
    return <>{children}</>
  }

  if (isPasswordRoute) {
    return <Navigate to="/home" replace />
  }

  if (hasMultipleRoles && !normalizedSelectedRole && !normalizedStoredRole && !isRoleRoute) {
    return <Navigate to="/select-role" replace />
  }

  if (!effectiveRole && !isRoleRoute) {
    return <Navigate to="/select-role" replace />
  }

  if (effectiveRole && !effectiveFiliere && !isFiliereRoute && !isRoleRoute) {
    return <Navigate to="/select-filiere" replace />
  }

  if (!effectiveRole && isFiliereRoute) {
    return <Navigate to="/select-role" replace />
  }

  if (isRoleRoute && effectiveRole && effectiveFiliere) {
    return <Navigate to="/home" replace />
  }

  return <>{children}</>
}
