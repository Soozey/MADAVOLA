import { FormEvent, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import { getErrorMessage } from '../lib/apiErrors'
import { useToast } from '../contexts/ToastContext'
import './DashboardPage.css'

export default function OpsCoveragePage() {
  const { user } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [configKey, setConfigKey] = useState('demo.key')
  const [configValue, setConfigValue] = useState('demo')
  const [selectedConfigId, setSelectedConfigId] = useState('')
  const [actorId, setActorId] = useState('')
  const [roleCode, setRoleCode] = useState('acteur')
  const [roleRecordId, setRoleRecordId] = useState('')
  const [providerCode, setProviderCode] = useState('mvola')
  const [providerName, setProviderName] = useState('MVola')
  const [paymentId, setPaymentId] = useState('')
  const [paymentExternalRef, setPaymentExternalRef] = useState('')
  const [geoPointId, setGeoPointId] = useState('')
  const [feeId, setFeeId] = useState('')
  const [versionTag, setVersionTag] = useState('')
  const [versionFile, setVersionFile] = useState<File | null>(null)
  const [taxId, setTaxId] = useState('')
  const [taxEventType, setTaxEventType] = useState('EXPORT_DTSPM')
  const [taxEventId, setTaxEventId] = useState('')
  const [taxBaseAmount, setTaxBaseAmount] = useState('100000')
  const [taxAssietteMode, setTaxAssietteMode] = useState<'manual' | 'fob_export' | 'local_market_value' | 'fixed_amount'>('fob_export')
  const [marketValueSubstance, setMarketValueSubstance] = useState('OR')
  const [marketValueUnit, setMarketValueUnit] = useState('kg')
  const [marketValueAmount, setMarketValueAmount] = useState('500000')
  const [marketValueLegalRef, setMarketValueLegalRef] = useState('Arrete Mines - valeur locale OR')
  const [permissionCode, setPermissionCode] = useState('auth.login')
  const [payloadOutput, setPayloadOutput] = useState<unknown>(null)

  const { data: health } = useQuery({ queryKey: ['ops', 'health'], queryFn: () => api.getHealth() })
  const { data: ready } = useQuery({ queryKey: ['ops', 'ready'], queryFn: () => api.getReady() })
  const { data: configs = [] } = useQuery({ queryKey: ['ops', 'configs'], queryFn: () => api.listAdminConfigs() })
  const { data: providers = [] } = useQuery({ queryKey: ['ops', 'providers'], queryFn: () => api.listPaymentProviders() })
  const { data: payments = [] } = useQuery({ queryKey: ['ops', 'payments'], queryFn: () => api.listPayments() })
  const { data: taxes = [] } = useQuery({ queryKey: ['ops', 'taxes'], queryFn: () => api.listTaxes() })
  const { data: taxEvents = [] } = useQuery({ queryKey: ['ops', 'tax-events'], queryFn: () => api.listTaxEvents() })
  const { data: localMarketValues = [] } = useQuery({ queryKey: ['ops', 'local-market-values'], queryFn: () => api.listLocalMarketValues({ filiere: 'OR' }) })
  const { data: territoryVersions = [] } = useQuery({ queryKey: ['ops', 'territory-versions'], queryFn: () => api.getTerritoryVersions() })
  const { data: rolesWithPermission } = useQuery({
    queryKey: ['ops', 'roles-perm', permissionCode],
    queryFn: () => api.getRolesWithPermission(permissionCode),
    enabled: !!permissionCode,
  })

  const runAction = async (fn: () => Promise<unknown>, invalidateKeys: string[] = []) => {
    try {
      const out = await fn()
      setPayloadOutput(out)
      for (const key of invalidateKeys) {
        queryClient.invalidateQueries({ queryKey: ['ops', key] })
      }
      toast.success('Operation executee.')
    } catch (err) {
      toast.error(getErrorMessage(err, 'Operation impossible'))
    }
  }

  const actorIdNum = Number(actorId || 0)

  const importMutation = useMutation({
    mutationFn: () => api.importTerritoryVersion(versionTag, versionFile as File),
    onSuccess: (out) => {
      setPayloadOutput(out)
      queryClient.invalidateQueries({ queryKey: ['ops', 'territory-versions'] })
      toast.success('Import territoire lance.')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Import impossible')),
  })

  const handleImport = (e: FormEvent) => {
    e.preventDefault()
    if (!versionTag || !versionFile) return
    importMutation.mutate()
  }

  return (
    <div className="dashboard">
      <h1>Couverture Ops</h1>
      <p className="dashboard-subtitle">Ecran de couverture des endpoints admin/ops orientes utilisateur encore manquants.</p>

      <div className="dashboard-grid">
        <div className="card">
          <h2>Sante / Disponibilite</h2>
          <p>health: {JSON.stringify(health)}</p>
          <p>ready: {JSON.stringify(ready)}</p>
        </div>

        <div className="card">
          <h2>Aide permissions RBAC</h2>
          <input value={permissionCode} onChange={(e) => setPermissionCode(e.target.value)} />
          <pre>{JSON.stringify(rolesWithPermission, null, 2)}</pre>
        </div>
      </div>

      <div className="card">
        <h2>Configuration admin</h2>
        <div className="form-grid">
          <div className="form-group">
            <label>Cle</label>
            <input value={configKey} onChange={(e) => setConfigKey(e.target.value)} />
          </div>
          <div className="form-group">
            <label>Valeur</label>
            <input value={configValue} onChange={(e) => setConfigValue(e.target.value)} />
          </div>
          <div className="form-group">
            <label>ID configuration</label>
            <input value={selectedConfigId} onChange={(e) => setSelectedConfigId(e.target.value)} />
          </div>
        </div>
        <div className="form-actions">
          <button className="btn-secondary" onClick={() => runAction(() => api.createAdminConfig({ key: configKey, value: configValue }), ['configs'])}>Creer</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.getAdminConfig(Number(selectedConfigId || 0)))}>Voir par ID</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.patchAdminConfig(Number(selectedConfigId || 0), { value: configValue }), ['configs'])}>Modifier</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.deleteAdminConfig(Number(selectedConfigId || 0)), ['configs'])}>Supprimer</button>
        </div>
        <pre>{JSON.stringify(configs, null, 2)}</pre>
      </div>

      <div className="card">
        <h2>Roles admin acteur</h2>
        <div className="form-grid">
          <div className="form-group"><label>ID acteur</label><input value={actorId} onChange={(e) => setActorId(e.target.value)} /></div>
          <div className="form-group"><label>Code role</label><input value={roleCode} onChange={(e) => setRoleCode(e.target.value)} /></div>
          <div className="form-group"><label>ID enregistrement role</label><input value={roleRecordId} onChange={(e) => setRoleRecordId(e.target.value)} /></div>
        </div>
        <div className="form-actions">
          <button className="btn-secondary" onClick={() => runAction(() => api.listAdminActorRoles(actorIdNum))}>Lister roles admin</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.assignAdminActorRole(actorIdNum, { role: roleCode }))}>Assigner role</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.patchAdminRole(Number(roleRecordId || 0), { status: 'inactive' }))}>Modifier role</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.deleteAdminRole(Number(roleRecordId || 0)))}>Supprimer role</button>
        </div>
      </div>

      <div className="card">
        <h2>Fournisseurs de paiement / Paiements / Frais / Taxes</h2>
        <div className="form-grid">
          <div className="form-group"><label>Code fournisseur</label><input value={providerCode} onChange={(e) => setProviderCode(e.target.value)} /></div>
          <div className="form-group"><label>Nom fournisseur</label><input value={providerName} onChange={(e) => setProviderName(e.target.value)} /></div>
          <div className="form-group"><label>ID paiement</label><input value={paymentId} onChange={(e) => setPaymentId(e.target.value)} /></div>
          <div className="form-group"><label>Reference externe</label><input value={paymentExternalRef} onChange={(e) => setPaymentExternalRef(e.target.value)} /></div>
          <div className="form-group"><label>ID frais</label><input value={feeId} onChange={(e) => setFeeId(e.target.value)} /></div>
          <div className="form-group"><label>ID taxe</label><input value={taxId} onChange={(e) => setTaxId(e.target.value)} /></div>
          <div className="form-group"><label>Type evenement fiscal</label><input value={taxEventType} onChange={(e) => setTaxEventType(e.target.value)} /></div>
          <div className="form-group"><label>Reference evenement</label><input value={taxEventId} onChange={(e) => setTaxEventId(e.target.value)} /></div>
          <div className="form-group"><label>Base fiscale</label><input value={taxBaseAmount} onChange={(e) => setTaxBaseAmount(e.target.value)} /></div>
          <div className="form-group">
            <label>Assiette</label>
            <select value={taxAssietteMode} onChange={(e) => setTaxAssietteMode(e.target.value as any)}>
              <option value="manual">manual</option>
              <option value="fob_export">fob_export</option>
              <option value="local_market_value">local_market_value</option>
              <option value="fixed_amount">fixed_amount</option>
            </select>
          </div>
          <div className="form-group"><label>Substance valeur locale</label><input value={marketValueSubstance} onChange={(e) => setMarketValueSubstance(e.target.value)} /></div>
          <div className="form-group"><label>Unite valeur locale</label><input value={marketValueUnit} onChange={(e) => setMarketValueUnit(e.target.value)} /></div>
          <div className="form-group"><label>Valeur locale/unite</label><input value={marketValueAmount} onChange={(e) => setMarketValueAmount(e.target.value)} /></div>
          <div className="form-group"><label>Reference legale valeur locale</label><input value={marketValueLegalRef} onChange={(e) => setMarketValueLegalRef(e.target.value)} /></div>
        </div>
        <div className="form-actions">
          <button className="btn-secondary" onClick={() => runAction(() => api.createPaymentProvider({ code: providerCode, name: providerName, enabled: true }), ['providers'])}>Creer fournisseur</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.patchPaymentProvider(Number((providers[0] as { id?: number } | undefined)?.id || 0), { name: providerName }), ['providers'])}>Modifier fournisseur #1</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.initiatePayment({ provider_code: providerCode, payer_actor_id: user?.id || 0, payee_actor_id: user?.id || 0, amount: 1000, currency: 'MGA', external_ref: paymentExternalRef || undefined }), ['payments'])}>Initier paiement</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.getPayment(Number(paymentId || 0)))}>Voir paiement</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.getPaymentStatus(paymentExternalRef))}>Statut par reference</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.sendPaymentWebhook(providerCode, { external_ref: paymentExternalRef, status: 'success' }))}>Test webhook</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.createFee({ fee_type: 'ops_fee', actor_id: user?.id || 0, commune_id: 1, amount: 1000 }), ['fees'])}>Creer frais</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.getFee(Number(feeId || 0)))}>Voir frais</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.createLocalMarketValue({
            filiere: 'OR',
            substance: marketValueSubstance,
            unit: marketValueUnit,
            value_per_unit: Number(marketValueAmount || 0),
            currency: 'MGA',
            legal_reference: marketValueLegalRef,
            version_tag: `ops-${Date.now()}`,
            effective_from: new Date().toISOString(),
          }), ['local-market-values'])}>Creer valeur locale</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.createTaxEvent({
            taxable_event_type: taxEventType,
            taxable_event_id: taxEventId || `OPS-${Date.now()}`,
            base_amount: Number(taxBaseAmount || 0),
            currency: 'MGA',
            assiette_mode: taxAssietteMode,
            substance: marketValueSubstance,
            transformed: taxEventType === 'EXPORT_DTSPM',
            transformation_origin: taxEventType === 'EXPORT_DTSPM' ? 'national_refinery' : undefined,
          }), ['taxes', 'tax-events'])}>Creer evenement taxe</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.patchTaxStatus(Number(taxId || 0), { status: 'VOID' }), ['taxes'])}>Modifier statut taxe</button>
        </div>
        <pre>{JSON.stringify({ providers, payments, taxes, taxEvents, localMarketValues }, null, 2)}</pre>
      </div>

      <div className="card">
        <h2>Geo / Versions territoire + import</h2>
        <div className="form-grid">
          <div className="form-group"><label>ID point geo</label><input value={geoPointId} onChange={(e) => setGeoPointId(e.target.value)} /></div>
          <div className="form-group"><label>Tag version</label><input value={versionTag} onChange={(e) => setVersionTag(e.target.value)} /></div>
          <div className="form-group">
            <label>Fichier version (.xlsx)</label>
            <input type="file" onChange={(e) => setVersionFile(e.target.files?.[0] ?? null)} />
          </div>
        </div>
        <div className="form-actions">
          <button className="btn-secondary" onClick={() => runAction(() => api.getGeoPoint(Number(geoPointId || 0)))}>Voir point geo</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.getTerritoryVersion(versionTag))}>Voir version territoire</button>
        </div>
        <form onSubmit={handleImport}>
          <button className="btn-secondary" type="submit" disabled={importMutation.isPending || !versionTag || !versionFile}>Importer territoire</button>
        </form>
        <pre>{JSON.stringify(territoryVersions, null, 2)}</pre>
      </div>

      <div className="card">
        <h2>Endpoints avances regime OR</h2>
        <div className="form-actions">
          <button className="btn-secondary" onClick={() => runAction(() => api.createOrLegalVersion({ version_tag: `ops-${Date.now()}`, effective_from: new Date().toISOString(), payload_json: '{}' }))}>POST /or/legal-versions</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.getActiveOrLegalVersion({ filiere: 'OR', legal_key: 'dtspm' }))}>GET /or/legal-versions/active</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.createOrTestCertificate({ lot_id: 1, gross_weight: 1, purity: 0.9 }))}>POST /or/test-certificates</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.createOrTransportEvent({ lot_id: 1, transporter_actor_id: user?.id || 0, depart_actor_id: user?.id || 0, arrival_actor_id: user?.id || 0, depart_geo_point_id: 1 }))}>POST /or/transport-events</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.patchOrTransportArrival(1, { arrival_geo_point_id: 1 }))}>PATCH /or/transport-events/:id/arrival</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.createOrTransformationFacility({ facility_type: 'raffinerie', operator_actor_id: user?.id || 0, autorisation_ref: 'OPS', valid_from: new Date().toISOString(), valid_to: new Date(Date.now() + 86400000).toISOString() }))}>POST /or/transformation-facilities</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.createOrTransformationEvent({ lot_input_id: 1, facility_id: 1, quantity_input: 1, quantity_output: 0.9, perte_declared: 0.1, output_product_type: 'or_affine', output_unit: 'g' }))}>POST /or/transformation-events</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.createOrExportValidation({ export_id: 1, validator_role: 'com', decision: 'approved' }))}>POST /or/export-validations</button>
          <button className="btn-secondary" onClick={() => runAction(() => api.createOrForexRepatriation({ export_id: 1, amount: 1 }))}>POST /or/forex-repatriations</button>
        </div>
      </div>

      {payloadOutput !== null && (
        <div className="card">
          <h2>Derniere reponse</h2>
          <pre>{JSON.stringify(payloadOutput, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

