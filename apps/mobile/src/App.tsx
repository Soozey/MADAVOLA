import { useMemo, useState } from 'react'
import axios from 'axios'

type VerifyKind = 'actor' | 'lot' | 'invoice'

const API_BASE_URL =
  (import.meta as any).env?.VITE_API_URL ||
  ((import.meta as any).env?.DEV ? '/api/v1' : 'http://localhost:8000/api/v1')

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('mobile_access_token') || '')
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [verifyKind, setVerifyKind] = useState<VerifyKind>('actor')
  const [verifyValue, setVerifyValue] = useState('')
  const [verifyResult, setVerifyResult] = useState<any>(null)
  const [lotForm, setLotForm] = useState({ product_type: 'or_brut', quantity: '1', unit: 'g', lat: '-18.8792', lon: '47.5079' })
  const [message, setMessage] = useState('')

  const client = useMemo(() => {
    const c = axios.create({ baseURL: API_BASE_URL })
    if (token) c.defaults.headers.common.Authorization = `Bearer ${token}`
    return c
  }, [token])

  const login = async () => {
    setMessage('')
    try {
      const { data } = await client.post('/auth/login', { identifier, password })
      setToken(data.access_token)
      localStorage.setItem('mobile_access_token', data.access_token)
      setMessage('Connecte.')
    } catch (e: any) {
      setMessage(e?.response?.data?.detail?.message || 'Echec login')
    }
  }

  const verify = async () => {
    setMessage('')
    setVerifyResult(null)
    try {
      if (verifyKind === 'invoice') {
        const { data } = await client.get(`/verify/invoice/${encodeURIComponent(verifyValue)}`)
        setVerifyResult(data)
        return
      }
      const { data } = await client.get(`/verify/${verifyKind}/${verifyValue}`)
      setVerifyResult(data)
    } catch (e: any) {
      setMessage(e?.response?.data?.detail?.message || 'Verification echouee')
    }
  }

  const createLot = async () => {
    setMessage('')
    try {
      if (!token) {
        setMessage('Connectez-vous d abord')
        return
      }
      const me = await client.get('/auth/me')
      const geo = await client.post('/geo-points', {
        lat: Number(lotForm.lat),
        lon: Number(lotForm.lon),
        accuracy_m: 10,
        source: 'mobile',
      })
      const { data } = await client.post('/lots', {
        filiere: 'OR',
        product_type: lotForm.product_type,
        quantity: Number(lotForm.quantity),
        unit: lotForm.unit,
        declare_geo_point_id: geo.data.id,
        declared_by_actor_id: me.data.id,
      })
      setMessage(`Lot #${data.id} cree. Recu ${data.declaration_receipt_number || '-'}`)
    } catch (e: any) {
      setMessage(e?.response?.data?.detail?.message || 'Creation lot echouee')
    }
  }

  return (
    <div className="container">
      <div className="card">
        <h1 className="title">MADAVOLA Mobile</h1>
        <small>MVP terrain: login, verification QR acteur/lot/facture, declaration lot.</small>
      </div>

      <div className="card">
        <h2 className="title">Connexion</h2>
        <div className="row">
          <input placeholder="email ou telephone" value={identifier} onChange={(e) => setIdentifier(e.target.value)} />
          <input placeholder="mot de passe" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button onClick={login}>Se connecter</button>
          {token && <span className="badge">Session active</span>}
        </div>
      </div>

      <div className="card">
        <h2 className="title">Verification</h2>
        <div className="row">
          <select value={verifyKind} onChange={(e) => setVerifyKind(e.target.value as VerifyKind)}>
            <option value="actor">Acteur</option>
            <option value="lot">Lot</option>
            <option value="invoice">Facture</option>
          </select>
          <input placeholder={verifyKind === 'invoice' ? 'INV-00000001 ou 1' : 'ID numerique'} value={verifyValue} onChange={(e) => setVerifyValue(e.target.value)} />
          <button onClick={verify}>Verifier</button>
        </div>
        {verifyResult && <pre>{JSON.stringify(verifyResult, null, 2)}</pre>}
      </div>

      <div className="card">
        <h2 className="title">Declarer production (Lot)</h2>
        <div className="row">
          <input placeholder="type produit" value={lotForm.product_type} onChange={(e) => setLotForm((p) => ({ ...p, product_type: e.target.value }))} />
          <input placeholder="quantite" value={lotForm.quantity} onChange={(e) => setLotForm((p) => ({ ...p, quantity: e.target.value }))} />
          <select value={lotForm.unit} onChange={(e) => setLotForm((p) => ({ ...p, unit: e.target.value }))}>
            <option value="g">g</option>
            <option value="kg">kg</option>
            <option value="akotry">akotry</option>
          </select>
          <input placeholder="latitude" value={lotForm.lat} onChange={(e) => setLotForm((p) => ({ ...p, lat: e.target.value }))} />
          <input placeholder="longitude" value={lotForm.lon} onChange={(e) => setLotForm((p) => ({ ...p, lon: e.target.value }))} />
          <button onClick={createLot}>Creer lot</button>
        </div>
      </div>

      {message && <div className="card"><strong>{message}</strong></div>}
    </div>
  )
}
