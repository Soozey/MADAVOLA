import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { getErrorMessage } from '../lib/apiErrors'
import { extractActiveRoles } from '../utils/sessionDefaults'
import './LoginPage.css'

export default function LoginPage() {
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const profile = await login(identifier, password)
      const activeRoles = extractActiveRoles(profile?.roles || [])
      if (profile?.must_change_password) {
        navigate('/change-password', { replace: true })
      } else if (activeRoles.length > 1) {
        navigate('/select-role', { replace: true })
      } else {
        navigate('/home', { replace: true })
      }
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Identifiant ou mot de passe incorrect.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <form onSubmit={handleSubmit} className="login-form" data-testid="login-form">
        <div className="login-header">
          <h1>MADAVOLA</h1>
          <p className="login-subtitle">
            Plateforme de gestion de transactions pour les filières OR / PIERRE / BOIS à Madagascar
          </p>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        <div className="form-group">
          <label htmlFor="identifier">Email ou Téléphone</label>
          <input
            type="text"
            id="identifier"
            data-testid="login-identifier"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            required
            placeholder="admin@madavola.mg ou 0340000000"
          />
          <span className="form-hint">Format téléphone : 03XXXXXXXX (10 chiffres)</span>
        </div>
        <div className="form-group">
          <label htmlFor="password">Mot de passe</label>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type={showPassword ? 'text' : 'password'}
              id="password"
              data-testid="login-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="********"
              style={{ flex: 1 }}
            />
            <button type="button" className="btn-secondary" onClick={() => setShowPassword((v) => !v)}>
              {showPassword ? 'Masquer' : 'Afficher'}
            </button>
          </div>
        </div>
        <button type="submit" className="btn-primary" data-testid="login-submit" disabled={loading} style={{ width: '100%' }}>
          {loading ? 'Connexion...' : 'Se connecter'}
        </button>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => navigate('/signup')}
          style={{ width: '100%', marginTop: 10 }}
        >
          S'inscrire
        </button>
      </form>
    </div>
  )
}
