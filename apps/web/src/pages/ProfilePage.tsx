import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../contexts/AuthContext'
import { api } from '../lib/api'
import { getErrorMessage } from '../lib/apiErrors'
import './DashboardPage.css'

function cinDigits(value: string): string {
  return (value || '').replace(/\D/g, '').slice(0, 12)
}

function formatCin(value: string): string {
  const digits = cinDigits(value)
  if (!digits) return ''
  return digits.replace(/(\d{3})(?=\d)/g, '$1 ').trim()
}

async function cropIdentityPhoto(file: File): Promise<File> {
  try {
    const bitmap = await createImageBitmap(file)
    const sourceRatio = bitmap.width / bitmap.height
    const targetRatio = 35 / 45
    let sx = 0
    let sy = 0
    let sw = bitmap.width
    let sh = bitmap.height
    if (sourceRatio > targetRatio) {
      sw = Math.round(bitmap.height * targetRatio)
      sx = Math.round((bitmap.width - sw) / 2)
    } else if (sourceRatio < targetRatio) {
      sh = Math.round(bitmap.width / targetRatio)
      sy = Math.round((bitmap.height - sh) / 2)
    }
    const canvas = document.createElement('canvas')
    canvas.width = 700
    canvas.height = 900
    const ctx = canvas.getContext('2d')
    if (!ctx) return file
    ctx.drawImage(bitmap, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height)
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.92))
    if (!blob) return file
    return new File([blob], `profile-${Date.now()}.jpg`, { type: 'image/jpeg' })
  } catch {
    return file
  }
}

export default function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const [loading, setLoading] = useState(false)
  const [photoBusy, setPhotoBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [form, setForm] = useState({
    nom: '',
    prenoms: '',
    date_naissance: '',
    adresse_text: '',
    cin: '',
    cin_date_delivrance: '',
    commune_code: '',
    fokontany_code: '',
  })

  const { data: me, refetch: refetchMe } = useQuery({
    queryKey: ['profile', 'me', user?.id],
    queryFn: () => api.getMe(),
    enabled: !!user?.id,
  })
  const { data: regions = [] } = useQuery({
    queryKey: ['profile', 'regions'],
    queryFn: () => api.getRegions(),
  })
  const { data: districts = [] } = useQuery({
    queryKey: ['profile', 'districts', me?.region?.code],
    queryFn: () => api.getDistricts(me?.region?.code || ''),
    enabled: !!me?.region?.code,
  })
  const { data: communes = [] } = useQuery({
    queryKey: ['profile', 'communes', me?.district?.code],
    queryFn: () => api.getCommunes(me?.district?.code || ''),
    enabled: !!me?.district?.code,
  })
  const { data: fokontany = [] } = useQuery({
    queryKey: ['profile', 'fokontany', form.commune_code],
    queryFn: () => api.getFokontany(form.commune_code),
    enabled: !!form.commune_code,
  })

  useEffect(() => {
    if (!me) return
    setForm({
      nom: me.nom || '',
      prenoms: me.prenoms || '',
      date_naissance: me.date_naissance || '',
      adresse_text: me.adresse_text || '',
      cin: formatCin(me.cin || ''),
      cin_date_delivrance: me.cin_date_delivrance || '',
      commune_code: me.commune?.code || '',
      fokontany_code: me.fokontany?.code || '',
    })
  }, [me])

  const regionLabel = useMemo(() => {
    if (!me?.region?.code) return '-'
    const row = regions.find((r: any) => r.code === me.region.code)
    return row ? `${row.code} - ${row.name}` : me.region.code
  }, [regions, me?.region?.code])

  const districtLabel = useMemo(() => {
    if (!me?.district?.code) return '-'
    const row = districts.find((r: any) => r.code === me.district.code)
    return row ? `${row.code} - ${row.name}` : me.district.code
  }, [districts, me?.district?.code])

  const photoUrl = me?.photo_profile_url
    ? String(me.photo_profile_url).startsWith('/api/')
      ? me.photo_profile_url
      : `/api${me.photo_profile_url}`
    : ''

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    const cin = cinDigits(form.cin)
    if (cin && cin.length !== 12) {
      setError('CIN invalide: 12 chiffres requis.')
      return
    }
    setLoading(true)
    try {
      await api.patchMe({
        nom: form.nom.trim() || undefined,
        prenoms: form.prenoms.trim() || undefined,
        date_naissance: form.date_naissance || undefined,
        adresse_text: form.adresse_text.trim() || undefined,
        cin: cin || undefined,
        cin_date_delivrance: form.cin_date_delivrance || undefined,
        commune_code: form.commune_code || undefined,
        fokontany_code: form.fokontany_code || undefined,
      })
      await Promise.all([refetchMe(), refreshUser()])
      setSuccess('Profil mis a jour.')
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Mise a jour du profil impossible.'))
    } finally {
      setLoading(false)
    }
  }

  const onUploadPhoto = async (file: File | null) => {
    if (!file || !user?.id) return
    setError('')
    setSuccess('')
    if (!file.type.startsWith('image/')) {
      setError('Format image invalide.')
      return
    }
    setPhotoBusy(true)
    try {
      const cropped = await cropIdentityPhoto(file)
      await api.uploadActorPhoto(user.id, cropped)
      await Promise.all([refetchMe(), refreshUser()])
      setSuccess('Photo mise a jour.')
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Upload photo impossible.'))
    } finally {
      setPhotoBusy(false)
    }
  }

  return (
    <div className="dashboard">
      <h1>Mon profil</h1>
      <p className="dashboard-subtitle">Informations d'identite utilisees pour les cartes OR et les documents officiels.</p>

      {error && <p className="error">{error}</p>}
      {success && <p className="success">{success}</p>}

      <div className="home-grid" style={{ gridTemplateColumns: 'minmax(300px, 420px) minmax(320px, 1fr)' }}>
        <section className="card">
          <h2>Photo d'identite</h2>
          <p className="process-label">Recadrage automatique au ratio 35x45 mm.</p>
          <div style={{ margin: '12px 0' }}>
            {photoUrl ? (
              <img src={photoUrl} alt="Photo profil" style={{ width: 140, height: 180, objectFit: 'cover', borderRadius: 8, border: '1px solid #dbe6f7' }} />
            ) : (
              <div style={{ width: 140, height: 180, borderRadius: 8, border: '1px solid #dbe6f7', display: 'grid', placeItems: 'center', color: '#6b7b95' }}>
                Aucune photo
              </div>
            )}
          </div>
          <label className="btn-secondary" style={{ cursor: photoBusy ? 'not-allowed' : 'pointer', opacity: photoBusy ? 0.7 : 1 }}>
            {photoBusy ? 'Upload...' : "Changer la photo"}
            <input
              type="file"
              accept="image/*"
              style={{ display: 'none' }}
              disabled={photoBusy}
              onChange={(e) => onUploadPhoto(e.target.files?.[0] || null)}
            />
          </label>
          <div className="profile-info" style={{ marginTop: 16 }}>
            <div className="info-item"><span className="info-label">Region:</span><span className="info-value">{regionLabel}</span></div>
            <div className="info-item"><span className="info-label">District:</span><span className="info-value">{districtLabel}</span></div>
          </div>
        </section>

        <section className="card">
          <h2>Informations personnelles</h2>
          <form onSubmit={onSubmit}>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="nom">Nom *</label>
                <input id="nom" value={form.nom} onChange={(e) => setForm((p) => ({ ...p, nom: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label htmlFor="prenoms">Prenoms</label>
                <input id="prenoms" value={form.prenoms} onChange={(e) => setForm((p) => ({ ...p, prenoms: e.target.value }))} />
              </div>
              <div className="form-group">
                <label htmlFor="date_naissance">Date de naissance</label>
                <input id="date_naissance" type="date" value={form.date_naissance} onChange={(e) => setForm((p) => ({ ...p, date_naissance: e.target.value }))} />
              </div>
              <div className="form-group">
                <label htmlFor="cin">CIN (12 chiffres)</label>
                <input
                  id="cin"
                  value={form.cin}
                  onChange={(e) => setForm((p) => ({ ...p, cin: formatCin(e.target.value) }))}
                  placeholder="000 000 000 000"
                  inputMode="numeric"
                />
              </div>
              <div className="form-group">
                <label htmlFor="cin_date_delivrance">Date de delivrance CIN</label>
                <input id="cin_date_delivrance" type="date" value={form.cin_date_delivrance} onChange={(e) => setForm((p) => ({ ...p, cin_date_delivrance: e.target.value }))} />
              </div>
              <div className="form-group">
                <label htmlFor="commune_code">Commune</label>
                <select
                  id="commune_code"
                  value={form.commune_code}
                  onChange={(e) => setForm((p) => ({ ...p, commune_code: e.target.value, fokontany_code: '' }))}
                >
                  <option value="">Selectionner</option>
                  {communes.map((c: any) => (
                    <option key={c.code} value={c.code}>{c.code} - {c.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="fokontany_code">Fokontany</label>
                <select
                  id="fokontany_code"
                  value={form.fokontany_code}
                  onChange={(e) => setForm((p) => ({ ...p, fokontany_code: e.target.value }))}
                  disabled={!form.commune_code}
                >
                  <option value="">Selectionner</option>
                  {fokontany.map((f: any) => (
                    <option key={f.code || f.name} value={f.code || ''}>{f.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label htmlFor="adresse_text">Adresse (commune/fokontany + adresse libre)</label>
                <textarea
                  id="adresse_text"
                  value={form.adresse_text}
                  onChange={(e) => setForm((p) => ({ ...p, adresse_text: e.target.value }))}
                  rows={3}
                />
              </div>
            </div>
            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={loading}>
                {loading ? 'Enregistrement...' : 'Enregistrer'}
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  )
}
