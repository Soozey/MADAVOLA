import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { getErrorMessage } from '../lib/apiErrors'
import './LoginPage.css'

type RoleOption = { code: string; label: string; filiere: 'OR' | 'PIERRE' | 'BOIS' }

const ROLE_OPTIONS: RoleOption[] = [
  { code: 'orpailleur', label: 'Orpailleur', filiere: 'OR' },
  { code: 'collecteur', label: 'Collecteur local', filiere: 'OR' },
  { code: 'pierre_exploitant', label: 'Petit exploitant pierre', filiere: 'PIERRE' },
  { code: 'bois_exploitant', label: 'Petit exploitant bois', filiere: 'BOIS' },
]

export default function SignupPage() {
  const navigate = useNavigate()
  const [nom, setNom] = useState('')
  const [prenoms, setPrenoms] = useState('')
  const [telephone, setTelephone] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [role, setRole] = useState<RoleOption['code']>('orpailleur')
  const [regionCode, setRegionCode] = useState('')
  const [districtCode, setDistrictCode] = useState('')
  const [communeCode, setCommuneCode] = useState('')
  const [regions, setRegions] = useState<Array<{ code: string; name: string }>>([])
  const [districts, setDistricts] = useState<Array<{ code: string; name: string }>>([])
  const [communes, setCommunes] = useState<Array<{ code: string; name: string }>>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const selectedRole = useMemo(() => ROLE_OPTIONS.find((r) => r.code === role) || ROLE_OPTIONS[0], [role])

  useEffect(() => {
    api.getRegions().then(setRegions).catch(() => setRegions([]))
  }, [])

  useEffect(() => {
    if (!regionCode) {
      setDistricts([])
      setDistrictCode('')
      return
    }
    api.getDistricts(regionCode).then((rows) => {
      setDistricts(rows)
      if (!rows.some((r: any) => r.code === districtCode)) setDistrictCode('')
    }).catch(() => setDistricts([]))
  }, [regionCode])

  useEffect(() => {
    if (!districtCode) {
      setCommunes([])
      setCommuneCode('')
      return
    }
    api.getCommunes(districtCode).then((rows) => {
      setCommunes(rows)
      if (!rows.some((r: any) => r.code === communeCode)) setCommuneCode('')
    }).catch(() => setCommunes([]))
  }, [districtCode])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)
    try {
      const geo = await api.createGeoPoint({
        lat: -18.8792,
        lon: 47.5079,
        accuracy_m: 50,
        source: 'signup_web',
      })
      await api.createActor({
        type_personne: 'physique',
        nom: nom.trim(),
        prenoms: prenoms.trim() || undefined,
        telephone: telephone.trim(),
        email: email.trim() || undefined,
        password,
        region_code: regionCode,
        district_code: districtCode,
        commune_code: communeCode,
        geo_point_id: geo.id,
        roles: [selectedRole.code],
        filieres: [selectedRole.filiere],
      })
      setSuccess('Inscription enregistree. Connectez-vous pour continuer.')
      window.setTimeout(() => navigate('/login'), 900)
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Echec de l'inscription."))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <form onSubmit={handleSubmit} className="login-form">
        <div className="login-header">
          <h1>Inscription MADAVOLA</h1>
          <p className="login-subtitle">Choisissez votre role une seule fois a l'inscription.</p>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        <div className="form-group">
          <label>Role</label>
          <select value={role} onChange={(e) => setRole(e.target.value as RoleOption['code'])}>
            {ROLE_OPTIONS.map((item) => (
              <option key={item.code} value={item.code}>
                {item.label}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Nom</label>
          <input value={nom} onChange={(e) => setNom(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Prenoms</label>
          <input value={prenoms} onChange={(e) => setPrenoms(e.target.value)} />
        </div>
        <div className="form-group">
          <label>Telephone</label>
          <input value={telephone} onChange={(e) => setTelephone(e.target.value)} required placeholder="0340000000" />
        </div>
        <div className="form-group">
          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>Mot de passe</label>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ flex: 1 }}
            />
            <button type="button" className="btn-secondary" onClick={() => setShowPassword((v) => !v)}>
              {showPassword ? 'Masquer' : 'Afficher'}
            </button>
          </div>
        </div>
        <div className="form-group">
          <label>Region</label>
          <select value={regionCode} onChange={(e) => setRegionCode(e.target.value)} required>
            <option value="">Selectionner</option>
            {regions.map((region) => (
              <option key={region.code} value={region.code}>{region.name}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>District</label>
          <select value={districtCode} onChange={(e) => setDistrictCode(e.target.value)} required>
            <option value="">Selectionner</option>
            {districts.map((district) => (
              <option key={district.code} value={district.code}>{district.name}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label>Commune</label>
          <select value={communeCode} onChange={(e) => setCommuneCode(e.target.value)} required>
            <option value="">Selectionner</option>
            {communes.map((commune) => (
              <option key={commune.code} value={commune.code}>{commune.name}</option>
            ))}
          </select>
        </div>
        <button type="submit" className="btn-primary" disabled={loading} style={{ width: '100%' }}>
          {loading ? 'Inscription...' : "S'inscrire"}
        </button>
        <p style={{ marginTop: 12, textAlign: 'center' }}>
          <Link to="/login">Deja inscrit ? Se connecter</Link>
        </p>
      </form>
    </div>
  )
}
