import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'
import { getErrorMessage } from '../lib/apiErrors'
import './LoginPage.css'

export default function ChangePasswordPage() {
  const navigate = useNavigate()
  const { refreshUser } = useAuth()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPasswords, setShowPasswords] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    if (newPassword !== confirmPassword) {
      setError('La confirmation du nouveau mot de passe ne correspond pas.')
      return
    }
    setLoading(true)
    try {
      await api.changePassword(currentPassword, newPassword)
      await refreshUser()
      setSuccess('Mot de passe mis a jour. Redirection...')
      window.setTimeout(() => navigate('/home', { replace: true }), 400)
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Impossible de changer le mot de passe.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <form onSubmit={handleSubmit} className="login-form">
        <div className="login-header">
          <h1>Securite du compte</h1>
          <p className="login-subtitle">Premier acces: vous devez changer votre mot de passe avant de continuer.</p>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}
        <div className="form-group">
          <button type="button" className="btn-secondary" onClick={() => setShowPasswords((v) => !v)}>
            {showPasswords ? 'Masquer les mots de passe' : 'Afficher les mots de passe'}
          </button>
        </div>
        <div className="form-group">
          <label htmlFor="currentPassword">Mot de passe actuel</label>
          <input
            id="currentPassword"
            type={showPasswords ? 'text' : 'password'}
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="newPassword">Nouveau mot de passe</label>
          <input
            id="newPassword"
            type={showPasswords ? 'text' : 'password'}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            minLength={8}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="confirmPassword">Confirmer le nouveau mot de passe</label>
          <input
            id="confirmPassword"
            type={showPasswords ? 'text' : 'password'}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            minLength={8}
            required
          />
        </div>
        <button type="submit" className="btn-primary" disabled={loading} style={{ width: '100%' }}>
          {loading ? 'Mise a jour...' : 'Mettre a jour le mot de passe'}
        </button>
      </form>
    </div>
  )
}
