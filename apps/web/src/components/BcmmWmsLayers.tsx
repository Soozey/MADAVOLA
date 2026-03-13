import { WMSTileLayer } from 'react-leaflet'

export const BCMM_WMS_URL =
  (import.meta.env.VITE_BCMM_WMS_URL as string | undefined) ??
  'http://bcmm.mg:8080/geoserver/bcmm/wms'

export type BcmmLayerKey =
  | 'titres'
  | 'carres'
  | 'zones_protegees'
  | 'zones_sensibles'
  | 'regions'
  | 'districts'
  | 'communes'
  | 'fokontany'
  | 'carte100'

type BcmmLayerDefinition = {
  key: BcmmLayerKey
  label: string
  attribution: string
}

const BCMM_LAYERS: readonly BcmmLayerDefinition[] = [
  { key: 'titres', label: 'Permis minier', attribution: '© BCMM' },
  { key: 'carres', label: 'Carres', attribution: '© BCMM' },
  { key: 'zones_protegees', label: 'Zones protegees', attribution: '© BCMM' },
  { key: 'zones_sensibles', label: 'Zones sensibles', attribution: '© BCMM' },
  { key: 'regions', label: 'Regions', attribution: '© FTM' },
  { key: 'districts', label: 'Districts', attribution: '© FTM' },
  { key: 'communes', label: 'Communes', attribution: '© FTM' },
  { key: 'fokontany', label: 'Fokontany', attribution: '© FTM' },
  { key: 'carte100', label: 'Carte 100', attribution: '© FTM' },
]

export type BcmmLayerState = Record<BcmmLayerKey, boolean>

export function createDefaultBcmmLayerState(): BcmmLayerState {
  return {
    titres: false,
    carres: false,
    zones_protegees: false,
    zones_sensibles: false,
    regions: true,
    districts: false,
    communes: false,
    fokontany: false,
    carte100: false,
  }
}

export function createAllBcmmLayerState(visible: boolean): BcmmLayerState {
  return {
    titres: visible,
    carres: visible,
    zones_protegees: visible,
    zones_sensibles: visible,
    regions: visible,
    districts: visible,
    communes: visible,
    fokontany: visible,
    carte100: visible,
  }
}

export function BcmmLayerControls({
  layers,
  onChange,
}: {
  layers: BcmmLayerState
  onChange: (next: BcmmLayerState) => void
}) {
  const toggle = (key: BcmmLayerKey) => {
    onChange({ ...layers, [key]: !layers[key] })
  }

  return (
    <div>
      <div className="form-actions">
        <button type="button" className="btn-secondary" onClick={() => onChange(createAllBcmmLayerState(true))}>
          Tout afficher
        </button>
        <button type="button" className="btn-secondary" onClick={() => onChange(createAllBcmmLayerState(false))}>
          Tout masquer
        </button>
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
          gap: '8px 12px',
          marginTop: '8px',
        }}
      >
        {BCMM_LAYERS.map((layer) => (
          <label key={layer.key} style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input type="checkbox" checked={layers[layer.key]} onChange={() => toggle(layer.key)} />
            <span>{layer.label}</span>
          </label>
        ))}
      </div>
    </div>
  )
}

export function BcmmWmsLayers({ layers }: { layers: BcmmLayerState }) {
  return (
    <>
      {BCMM_LAYERS.filter((layer) => layers[layer.key]).map((layer, index) => (
        <WMSTileLayer
          key={layer.key}
          url={BCMM_WMS_URL}
          layers={layer.key}
          format="image/png"
          transparent
          styles=""
          zIndex={200 + index}
          attribution={layer.attribution}
        />
      ))}
    </>
  )
}
