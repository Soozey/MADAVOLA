import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react'
import { AppRole, Filiere } from '../config/rbac'
import { useAuth } from './AuthContext'
import { extractActiveRoles, pickPrimaryRole, resolveFiliereForRole } from '../utils/sessionDefaults'

const ROLE_STORAGE_KEY = 'selectedRole'
const FILIERE_STORAGE_KEY = 'selectedFiliere'

interface SessionContextType {
  selectedRole: AppRole | null
  selectedFiliere: Filiere | null
  setSelectedRole: (role: AppRole | null) => void
  setSelectedFiliere: (filiere: Filiere | null) => void
  changeProfile: () => void
  changeFiliere: () => void
  resetSession: () => void
}

const SessionContext = createContext<SessionContextType | undefined>(undefined)

function readStoredRole(): AppRole | null {
  const value = localStorage.getItem(ROLE_STORAGE_KEY)
  return (value as AppRole) || null
}

function readStoredFiliere(): Filiere | null {
  const value = localStorage.getItem(FILIERE_STORAGE_KEY)
  return (value as Filiere) || null
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [selectedRole, setSelectedRoleState] = useState<AppRole | null>(() => readStoredRole())
  const [selectedFiliere, setSelectedFiliereState] = useState<Filiere | null>(() => readStoredFiliere())

  const setSelectedRole = (role: AppRole | null) => {
    setSelectedRoleState(role)
    if (role) {
      localStorage.setItem(ROLE_STORAGE_KEY, role)
      return
    }
    localStorage.removeItem(ROLE_STORAGE_KEY)
  }

  const setSelectedFiliere = (filiere: Filiere | null) => {
    setSelectedFiliereState(filiere)
    if (filiere) {
      localStorage.setItem(FILIERE_STORAGE_KEY, filiere)
      return
    }
    localStorage.removeItem(FILIERE_STORAGE_KEY)
  }

  const changeProfile = () => {
    setSelectedRole(null)
    setSelectedFiliere(null)
    localStorage.removeItem(ROLE_STORAGE_KEY)
    localStorage.removeItem(FILIERE_STORAGE_KEY)
  }

  const changeFiliere = () => {
    setSelectedFiliere(null)
    localStorage.removeItem(FILIERE_STORAGE_KEY)
  }

  const resetSession = () => {
    setSelectedRole(null)
    setSelectedFiliere(null)
    localStorage.removeItem(ROLE_STORAGE_KEY)
    localStorage.removeItem(FILIERE_STORAGE_KEY)
  }

  useEffect(() => {
    if (!user) {
      return
    }
    const activeRoles = extractActiveRoles(user.roles)
    const storedRole = readStoredRole()
    const selectedRoleIsValid = !!selectedRole && activeRoles.includes(selectedRole)
    const storedRoleIsValid = !!storedRole && activeRoles.includes(storedRole)

    if (selectedRole && !selectedRoleIsValid) {
      setSelectedRole(null)
    }
    if (storedRole && !storedRoleIsValid) {
      localStorage.removeItem(ROLE_STORAGE_KEY)
    }

    let nextRole: AppRole | null = (selectedRoleIsValid ? selectedRole : null) as AppRole | null
    if (!nextRole && storedRoleIsValid) {
      nextRole = storedRole as AppRole
    }
    if (!nextRole && activeRoles.length === 1) {
      nextRole = pickPrimaryRole(user.roles, null) as AppRole | null
    }

    if (nextRole !== selectedRole) {
      setSelectedRole(nextRole)
    }

    if (!nextRole) {
      if (selectedFiliere) {
        setSelectedFiliere(null)
      }
      return
    }

    const nextFiliere = resolveFiliereForRole(nextRole, selectedFiliere || readStoredFiliere())
    if (nextFiliere !== selectedFiliere) {
      setSelectedFiliere(nextFiliere)
    }
  }, [user, selectedRole, selectedFiliere])

  const value = useMemo(
    () => ({
      selectedRole,
      selectedFiliere,
      setSelectedRole,
      setSelectedFiliere,
      changeProfile,
      changeFiliere,
      resetSession,
    }),
    [selectedRole, selectedFiliere]
  )

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const context = useContext(SessionContext)
  if (!context) {
    throw new Error('useSession must be used within SessionProvider')
  }
  return context
}
