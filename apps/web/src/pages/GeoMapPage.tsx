import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
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

type LotGeo = {
  lotId: number
  filiere: string
  status: string
  quantity: number
  unit: string
  lat: number
  lon: number
  geoPointId: number
}

export default function GeoMapPage() {
  const [filiere, setFiliere] = useState<'OR' | 'PIERRE' | 'BOIS'>('OR')
  const [bcmmLayers, setBcmmLayers] = useState<BcmmLayerState>(createDefaultBcmmLayerState)

  const { data: lotMarkers = [], isLoading, refetch } = useQuery({
    queryKey: ['geo-map', filiere],
    queryFn: async (): Promise<LotGeo[]> => {
      const lotsRes = await api.getLots({ page: 1, page_size: 120, status: 'available' })
      const lotsRaw = (((lotsRes as any)?.items || []) as any[])
      const lots = lotsRaw.filter((l: any) => l.filiere === filiere && Number(l.declare_geo_point_id) > 0)
      const geoIds = Array.from(new Set(lots.map((l: any) => Number(l.declare_geo_point_id))))
      const geoEntries = await Promise.all(
        geoIds.map(async (id) => {
          try {
            const point = await api.getGeoPoint(id)
            return [id, point] as const
          } catch {
            return null
          }
        })
      )
      const geoMap = new Map<number, any>()
      geoEntries.forEach((entry) => {
        if (entry) geoMap.set(entry[0], entry[1])
      })
      return lots
        .map((lot: any) => {
          const gp = geoMap.get(Number(lot.declare_geo_point_id))
          if (!gp) return null
          return {
            lotId: lot.id,
            filiere: lot.filiere,
            status: lot.status,
            quantity: Number(lot.quantity || 0),
            unit: lot.unit,
            geoPointId: Number(lot.declare_geo_point_id),
            lat: Number(gp.lat),
            lon: Number(gp.lon),
          } satisfies LotGeo
        })
        .filter(Boolean) as LotGeo[]
    },
  })

  const center = useMemo<[number, number]>(() => {
    if (!lotMarkers.length) return [-18.8792, 47.5079]
    const first = lotMarkers[0]
    return [first.lat, first.lon]
  }, [lotMarkers])

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1>Carte Operationnelle</h1>
      </div>
      <p className="dashboard-subtitle">Cartographie des lots par filiere (OpenStreetMap/Leaflet), avec acces detail geo-point.</p>

      <div className="card">
        <div className="form-actions">
          <button type="button" className={`btn-secondary ${filiere === 'OR' ? 'active' : ''}`} onClick={() => setFiliere('OR')}>OR</button>
          <button type="button" className={`btn-secondary ${filiere === 'PIERRE' ? 'active' : ''}`} onClick={() => setFiliere('PIERRE')}>PIERRE</button>
          <button type="button" className={`btn-secondary ${filiere === 'BOIS' ? 'active' : ''}`} onClick={() => setFiliere('BOIS')}>BOIS</button>
          <button type="button" className="btn-primary" onClick={() => refetch()}>Rafraichir</button>
        </div>
      </div>

      <div className="card">
        <h2>Couches BCMM / FTM</h2>
        <p className="dashboard-subtitle">Source: GeoServer BCMM (WMS)</p>
        <BcmmLayerControls layers={bcmmLayers} onChange={setBcmmLayers} />
      </div>

      <div className="card">
        {isLoading ? (
          <div className="loading">Chargement carte...</div>
        ) : (
          <>
            <p>{lotMarkers.length} lots geolocalises affiches.</p>
            <MapContainer center={center} zoom={7} style={{ height: 460, width: '100%' }} scrollWheelZoom>
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <BcmmWmsLayers layers={bcmmLayers} />
              {lotMarkers.map((m) => (
                <Marker key={`${m.lotId}-${m.geoPointId}`} position={[m.lat, m.lon]} icon={defaultIcon}>
                  <Popup>
                    <div>
                      <div><strong>Lot #{m.lotId}</strong></div>
                      <div>{m.filiere} | {m.quantity} {m.unit}</div>
                      <div>Statut: {m.status}</div>
                      <div>
                        <Link to={`/geo-points/${m.geoPointId}`}>GeoPoint #{m.geoPointId}</Link>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </>
        )}
      </div>
    </div>
  )
}
