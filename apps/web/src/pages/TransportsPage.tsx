import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export default function TransportsPage() {
  const [transportId, setTransportId] = useState('')
  const [lotId, setLotId] = useState('')
  const [scanResult, setScanResult] = useState<any>(null)
  const [selectedOrigin, setSelectedOrigin] = useState('')
  const [selectedDestination, setSelectedDestination] = useState('')
  const [selectedTransporter, setSelectedTransporter] = useState('')
  const [selectedLotForCreate, setSelectedLotForCreate] = useState('')
  const [quantity, setQuantity] = useState('1')
  const [vehicleRef, setVehicleRef] = useState('')

  const { data: communes = [] } = useQuery({
    queryKey: ['territories', 'communes-all', 'transports'],
    queryFn: () => api.getAllCommunes(),
  })
  const { data: actors = [] } = useQuery({
    queryKey: ['actors', 'transports'],
    queryFn: async () => {
      const data = await api.getActors()
      return Array.isArray(data) ? data : data?.items ?? []
    },
  })
  const { data: lots = [] } = useQuery({
    queryKey: ['lots', 'transports'],
    queryFn: async () => {
      const data = await api.getLots()
      return Array.isArray(data) ? data : data?.items ?? []
    },
  })

  const createMutation = useMutation({
    mutationFn: async (payload: any) => api.createTransport(payload),
  })

  const verifyMutation = useMutation({
    mutationFn: async (payload: { transportId: number; lotId: number }) => api.verifyTransportScan(payload.transportId, payload.lotId),
    onSuccess: (data) => setScanResult(data),
  })

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!selectedOrigin || !selectedDestination) return
    createMutation.mutate({
      transporter_actor_id: Number(selectedTransporter),
      origin: selectedOrigin,
      destination: selectedDestination,
      vehicle_ref: vehicleRef || '',
      depart_at: new Date().toISOString(),
      items: [
        {
          lot_id: Number(selectedLotForCreate),
          quantity: Number(quantity),
        },
      ],
    })
  }

  return (
    <div className="lots-page">
      <div className="page-header">
        <h1>Transports BOIS</h1>
      </div>

      <div className="card form-card">
        <h2>Creer un transport</h2>
        <form onSubmit={handleCreate}>
          <div className="form-grid">
            <div className="form-group">
              <label>Transporteur *</label>
              <select value={selectedTransporter} onChange={(e) => setSelectedTransporter(e.target.value)} required>
                <option value="">-- Choisir --</option>
                {actors.map((actor: any) => (
                  <option key={actor.id} value={actor.id}>{actor.id} - {actor.nom}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Lot *</label>
              <select value={selectedLotForCreate} onChange={(e) => setSelectedLotForCreate(e.target.value)} required>
                <option value="">-- Choisir --</option>
                {lots.map((lot: any) => (
                  <option key={lot.id} value={lot.id}>#{lot.id} - {lot.filiere} - {lot.quantity} {lot.unit}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Quantite *</label>
              <input value={quantity} onChange={(e) => setQuantity(e.target.value)} type="number" step="0.0001" min="0.0001" required />
            </div>
            <div className="form-group">
              <label>Origine (commune) *</label>
              <select value={selectedOrigin} onChange={(e) => setSelectedOrigin(e.target.value)} required>
                <option value="">-- Choisir --</option>
                {communes.map((commune: any) => (
                  <option key={`origin-${commune.code}`} value={commune.code}>
                    {commune.code} - {commune.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Destination (commune) *</label>
              <select value={selectedDestination} onChange={(e) => setSelectedDestination(e.target.value)} required>
                <option value="">-- Choisir --</option>
                {communes.map((commune: any) => (
                  <option key={`destination-${commune.code}`} value={commune.code}>
                    {commune.code} - {commune.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Vehicule</label>
              <input value={vehicleRef} onChange={(e) => setVehicleRef(e.target.value)} />
            </div>
          </div>
          <div className="form-actions">
            <button
              className="btn-primary"
              type="submit"
              disabled={!selectedOrigin || !selectedDestination || !selectedTransporter || !selectedLotForCreate || Number(quantity) <= 0}
            >
              Creer transport
            </button>
          </div>
        </form>
        {createMutation.data && <p>Transport cree: ID {createMutation.data.id} - QR {createMutation.data.qr_code}</p>}
      </div>

      <div className="card form-card">
        <h2>Scan controle transport</h2>
        <div className="form-grid">
          <div className="form-group"><label>Transport ID</label><input value={transportId} onChange={(e) => setTransportId(e.target.value)} /></div>
          <div className="form-group"><label>Lot ID</label><input value={lotId} onChange={(e) => setLotId(e.target.value)} /></div>
        </div>
        <div className="form-actions">
          <button
            className="btn-primary"
            type="button"
            onClick={() => verifyMutation.mutate({ transportId: Number(transportId), lotId: Number(lotId) })}
            disabled={!transportId || !lotId}
          >
            Verifier
          </button>
        </div>
        {scanResult && <pre>{JSON.stringify(scanResult, null, 2)}</pre>}
      </div>
    </div>
  )
}
