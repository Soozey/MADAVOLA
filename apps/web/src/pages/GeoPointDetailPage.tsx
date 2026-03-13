import { Link, useParams } from 'react-router-dom'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet'
import L from 'leaflet'
import { api } from '../lib/api'
import {
  BcmmLayerControls,
  BcmmWmsLayers,
  createDefaultBcmmLayerState,
  type BcmmLayerState,
} from '../components/BcmmWmsLayers'

const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

export default function GeoPointDetailPage() {
  const { id } = useParams<{ id: string }>()
  const geoId = Number(id)
  const [bcmmLayers, setBcmmLayers] = useState<BcmmLayerState>(createDefaultBcmmLayerState)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['geo-point', geoId],
    queryFn: () => api.getGeoPoint(geoId),
    enabled: Number.isFinite(geoId) && geoId > 0,
  })

  if (!Number.isFinite(geoId) || geoId <= 0) {
    return (
      <div className="dashboard">
        <p className="error">ID geo-point invalide.</p>
      </div>
    )
  }
  if (isLoading) return <div className="loading">Chargement...</div>
  if (isError || !data) {
    return (
      <div className="dashboard">
        <p className="error">Geo-point introuvable ou acces refuse.</p>
      </div>
    )
  }

  const lat = Number(data.lat)
  const lon = Number(data.lon)

  return (
    <div className="dashboard">
      <h1>GeoPoint #{data.id}</h1>
      <p className="dashboard-subtitle">
        <Link to="/actors">Retour acteurs</Link>
      </p>
      <div className="card">
        <div className="profile-info">
          <div className="info-item"><span className="info-label">Latitude</span><span className="info-value">{lat}</span></div>
          <div className="info-item"><span className="info-label">Longitude</span><span className="info-value">{lon}</span></div>
          <div className="info-item"><span className="info-label">Precision</span><span className="info-value">{data.accuracy_m} m</span></div>
          <div className="info-item"><span className="info-label">Source</span><span className="info-value">{data.source}</span></div>
        </div>
      </div>
      <div className="card">
        <h2>Carte</h2>
        <BcmmLayerControls layers={bcmmLayers} onChange={setBcmmLayers} />
        <MapContainer center={[lat, lon]} zoom={13} style={{ height: 360, width: '100%' }} scrollWheelZoom>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <BcmmWmsLayers layers={bcmmLayers} />
          <Marker position={[lat, lon]} icon={defaultIcon}>
            <Popup>GeoPoint #{data.id}</Popup>
          </Marker>
        </MapContainer>
      </div>
    </div>
  )
}
