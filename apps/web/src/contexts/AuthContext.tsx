import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from '../lib/api'

interface User {
  id: number
  nom: string
  prenoms: string | null
  email: string
  telephone: string
  cin?: string | null
  cin_date_delivrance?: string | null
  date_naissance?: string | null
  adresse_text?: string | null
  photo_profile_url?: string | null
  roles: Array<{ role: string; status: string }>
  filieres?: string[]
  primary_role?: string | null
  must_change_password?: boolean
  region: { id?: number; code: string; name: string } | null
  district?: { id?: number; code: string; name: string } | null
  commune: { id?: number; code: string; name: string } | null
  fokontany?: { id?: number; code: string; name: string } | null
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (identifier: string, password: string) => Promise<User | null>
  logout: () => Promise<void>
  refreshUser: () => Promise<User | null>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      refreshUser().finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (identifier: string, password: string) => {
    const tokens = await api.login(identifier, password)
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    return refreshUser()
  }

  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      try {
        await api.logout(refreshToken)
      } catch {
        // best effort logout
      }
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('selectedRole')
    localStorage.removeItem('selectedFiliere')
    setUser(null)
  }

  const refreshUser = async () => {
    try {
      const userData = await api.getMe()
      setUser(userData)
      return userData
    } catch (error) {
      console.error('Failed to fetch user:', error)
      await logout()
      return null
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
