import { useEffect, useMemo, useRef, useState } from 'react'
import axios from 'axios'
import { MobileRoleSelector } from './features/rbac/MobileRoleSelector'
import type { FiliereCode, RbacRole } from './features/rbac/types'

type VerifyKind = 'actor' | 'lot' | 'invoice'
type TabKey = 'actors' | 'lots' | 'trades' | 'exports' | 'transports' | 'transformations' | 'verify' | 'notifications'
type EntryStep = 'login' | 'role' | 'filiere' | 'dashboard'
type TerritoryOption = { code: string; name: string }
type CardRequestKind = 'kara_orpailleur' | 'collector_collecteur' | 'collector_bijoutier'

const API_BASE_URL =
  (import.meta as any).env?.VITE_API_URL ||
  ((import.meta as any).env?.DEV ? '/api/v1' : 'http://localhost:8000/api/v1')

const STORAGE_TOKEN_KEY = 'mobile_access_token'
const STORAGE_ROLE_KEY = 'mobile_selected_role'
const STORAGE_FILIERE_KEY = 'mobile_selected_filiere'

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: 'actors', label: 'Acteurs' },
  { key: 'lots', label: 'Lots' },
  { key: 'trades', label: 'Transactions' },
  { key: 'exports', label: 'Exportations' },
  { key: 'transports', label: 'Transport' },
  { key: 'transformations', label: 'Transformation' },
  { key: 'verify', label: 'Scan' },
  { key: 'notifications', label: 'Notifications' },
]

export default function App() {
  const [activeTab, setActiveTab] = useState<TabKey>('actors')
  const [token, setToken] = useState(localStorage.getItem(STORAGE_TOKEN_KEY) || '')
  const [entryStep, setEntryStep] = useState<EntryStep>('login')
  const [selectedRole, setSelectedRole] = useState<string>(localStorage.getItem(STORAGE_ROLE_KEY) || '')
  const [selectedFiliere, setSelectedFiliere] = useState<FiliereCode | ''>(
    (localStorage.getItem(STORAGE_FILIERE_KEY) as FiliereCode | null) || ''
  )
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState<'success' | 'error' | ''>('')
  const [debug, setDebug] = useState<any>(null)
  const cameraInputRef = useRef<HTMLInputElement | null>(null)

  const [me, setMe] = useState<any>(null)
  const [actors, setActors] = useState<any[]>([])
  const [lots, setLots] = useState<any[]>([])
  const [entryRoles, setEntryRoles] = useState<RbacRole[]>([])
  const [entryRolesLoading, setEntryRolesLoading] = useState(false)
  const [entryRolesError, setEntryRolesError] = useState('')
  const [rolePermissions, setRolePermissions] = useState<string[]>([])
  const [permissionsLoading, setPermissionsLoading] = useState(false)
  const [rbacRoles, setRbacRoles] = useState<RbacRole[]>([])
  const [roleSearch, setRoleSearch] = useState('')
  const [roleCategory, setRoleCategory] = useState('all')
  const [roleActorType, setRoleActorType] = useState('all')
  const [catalogProducts, setCatalogProducts] = useState<any[]>([])
  const [essences, setEssences] = useState<any[]>([])
  const [regions, setRegions] = useState<TerritoryOption[]>([])
  const [districts, setDistricts] = useState<TerritoryOption[]>([])
  const [communes, setCommunes] = useState<TerritoryOption[]>([])
  const [fokontany, setFokontany] = useState<TerritoryOption[]>([])
  const [territoriesLoading, setTerritoriesLoading] = useState(false)
  const [notifications, setNotifications] = useState<any[]>([])
  const [emergencyAlerts, setEmergencyAlerts] = useState<any[]>([])
  const [myOrCards, setMyOrCards] = useState<any>({ kara_cards: [], collector_cards: [] })
  const [myFees, setMyFees] = useState<any[]>([])
  const [communeCardQueue, setCommuneCardQueue] = useState<any[]>([])
  const [cardRequestKind, setCardRequestKind] = useState<CardRequestKind>('kara_orpailleur')
  const [cardCin, setCardCin] = useState('')
  const [contextLoading, setContextLoading] = useState(false)
  const [emergencyForm, setEmergencyForm] = useState<any>({
    title: 'Alerte terrain',
    message: '',
    target_service: 'both',
    severity: 'high',
    filiere: 'OR',
    lat: '',
    lon: '',
  })

  const [actorForm, setActorForm] = useState<any>({
    filiere: 'OR',
    role: 'acteur',
    nom: 'Mobile User',
    prenoms: 'Test',
    email: `mobile.${Date.now()}@example.com`,
    telephone: `0349${String(Date.now()).slice(-6)}`,
    password: 'secret123',
    region_code: '',
    district_code: '',
    commune_code: '',
    fokontany_code: '',
    lat: '-18.8792',
    lon: '47.5079',
  })

  const [lotForm, setLotForm] = useState<any>({
    filiere: 'OR',
    sous_filiere: 'GEMME',
    product_catalog_id: '',
    wood_essence_id: '',
    wood_form: 'grume',
    product_type: 'or_brut',
    unit: 'g',
    quantity: '1',
    volume_m3: '',
    lat: '-18.8792',
    lon: '47.5079',
    attr_key: '',
    attr_value: '',
  })

  const [tradeForm, setTradeForm] = useState<any>({ seller_actor_id: '', buyer_actor_id: '', lot_id: '', quantity: '1', unit_price: '1000', trade_id: '' })
  const [exportForm, setExportForm] = useState<any>({ destination: 'EU', export_id: '', lot_id: '', qty: '1', step_code: 'mines', decision: 'approved', seal_number: '' })
  const [transportForm, setTransportForm] = useState<any>({ transporter_actor_id: '', lot_id: '', quantity: '1', origin: 'A', destination: 'B', transport_id: '', verify_lot_id: '' })
  const [transformationForm, setTransformationForm] = useState<any>({ input_lot_ids: '', outputs: '1:m3:planche', operation_type: 'sciage' })
  const [verifyKind, setVerifyKind] = useState<VerifyKind>('actor')
  const [verifyValue, setVerifyValue] = useState('')

  const client = useMemo(() => {
    const c = axios.create({ baseURL: API_BASE_URL })
    if (token) c.defaults.headers.common.Authorization = `Bearer ${token}`
    return c
  }, [token])

  const showError = (e: any, fallback: string) => {
    setMessageType('error')
    setMessage(e?.response?.data?.detail?.message || fallback)
    setDebug(null)
  }
  const showSuccess = (text: string) => {
    setMessageType('success')
    setMessage(text)
  }

  const isInvalidTokenError = (error: any) => {
    const raw = error?.response?.data?.detail?.message || error?.response?.data?.detail || error?.message || ''
    const normalized = String(raw).toLowerCase()
    return normalized.includes('token_invalide') || normalized.includes('token_invalid') || normalized.includes('token_manquant')
  }

  const clearAuthSession = (reason?: string) => {
    setToken('')
    setMe(null)
    setSelectedRole('')
    setSelectedFiliere('')
    setRolePermissions([])
    localStorage.removeItem(STORAGE_TOKEN_KEY)
    localStorage.removeItem(STORAGE_ROLE_KEY)
    localStorage.removeItem(STORAGE_FILIERE_KEY)
    setEntryStep('login')
    if (reason) {
      setMessageType('error')
      setMessage(reason)
    }
  }

  const loadEntryRoles = async () => {
    if (!token) return
    setEntryRolesLoading(true)
    setEntryRolesError('')
    try {
      const requestParams = {
        include_common: true,
        active_only: true,
        for_current_actor: true,
        actor_type: roleActorType !== 'all' ? roleActorType : undefined,
        category: roleCategory !== 'all' ? roleCategory : undefined,
        search: roleSearch.trim() || undefined,
      }
      let { data } = await client.get('/rbac/roles', {
        params: {
          ...requestParams,
        },
      })
      // Fallback strict demo: si aucun role remonte avec filtre RBAC utilisateur,
      // on recharge le catalogue actif sans for_current_actor pour ne pas bloquer l'entree.
      if (!Array.isArray(data) || data.length === 0) {
        const fallback = await client.get('/rbac/roles', {
          params: {
            ...requestParams,
            for_current_actor: false,
          },
        })
        data = fallback.data
      }
      setEntryRoles(Array.isArray(data) ? data : [])
    } catch (e: any) {
      if (isInvalidTokenError(e)) {
        clearAuthSession('Session invalide/expiree. Veuillez vous reconnecter.')
        return
      }
      setEntryRolesError(e?.response?.data?.detail?.message || 'Impossible de charger les roles')
      setEntryRoles([])
    } finally {
      setEntryRolesLoading(false)
    }
  }

  const loadRolePermissions = async (roleCode: string) => {
    if (!token || !roleCode) {
      setRolePermissions([])
      return
    }
    setPermissionsLoading(true)
    try {
      const { data } = await client.get('/rbac/permissions', { params: { role: roleCode } })
      setRolePermissions(Array.isArray(data?.permissions) ? data.permissions : [])
    } catch (e: any) {
      if (isInvalidTokenError(e)) {
        clearAuthSession('Session invalide/expiree. Veuillez vous reconnecter.')
        return
      }
      setRolePermissions([])
    } finally {
      setPermissionsLoading(false)
    }
  }

  const hasModuleAccess = (tab: TabKey) => {
    if (selectedRole === 'admin' || selectedRole === 'dirigeant') return true
    if (rolePermissions.length === 0) return true // retrocompatibilite roles legacy
    const ruleMap: Record<TabKey, string[]> = {
      actors: ['admin_commune', 'supervision_territoriale', 'card_validate_commune', 'card_validate_com'],
      lots: ['pierre_declare_lot', 'bois_declare_lot', 'admin_filiere_or', 'admin_filiere_mines', 'admin_filiere_bois'],
      trades: ['pierre_trade', 'bois_trade', 'admin_filiere_or', 'admin_filiere_mines', 'admin_filiere_bois'],
      exports: ['controle_export', 'gue_export', 'export_or_workflow', 'pierre_export', 'bois_export'],
      transports: ['transport_or', 'bois_transport', 'profil_controleur'],
      transformations: ['pierre_transform', 'bois_transform', 'poinconnage_raffinerie'],
      verify: ['profil_controleur', 'audit_logs', 'controle_export'],
      notifications: ['lecture_seule', 'dashboard_national', 'dashboard_regional', 'admin_commune'],
    }
    return ruleMap[tab].some((p) => rolePermissions.includes(p))
  }

  const visibleTabs = (() => {
    const filtered = TABS.filter((t) => hasModuleAccess(t.key))
    return filtered.length > 0 ? filtered : TABS
  })()
  const canValidateCommune = (me?.roles || []).some((r: any) => ['admin', 'dirigeant', 'commune', 'commune_agent', 'com', 'com_admin', 'com_agent'].includes(r.role))

  const refreshContext = async () => {
    if (!token) return
    setContextLoading(true)
    try {
      const meRes = await client.get('/auth/me')
      setMe(meRes.data)
      const [actorsRes, lotsRes, notifRes, emergencyRes] = await Promise.all([
        client.get('/actors', { params: { page: 1, page_size: 100 } }).catch(() => ({ data: [] })),
        client.get('/lots', { params: { page: 1, page_size: 100 } }).catch(() => ({ data: { items: [] } })),
        client.get('/notifications', { params: { actor_id: meRes.data.id } }).catch(() => ({ data: [] })),
        client.get('/emergency-alerts').catch(() => ({ data: [] })),
      ])
      const [cardsRes, feesRes, queueRes] = await Promise.all([
        client.get('/or-compliance/cards/my').catch(() => ({ data: { kara_cards: [], collector_cards: [] } })),
        client.get('/fees', { params: { actor_id: meRes.data.id } }).catch(() => ({ data: [] })),
        client.get('/or-compliance/cards/commune-queue', { params: { status: 'pending', commune_id: meRes.data?.commune?.id } }).catch(() => ({ data: [] })),
      ])
      const actorsData = Array.isArray(actorsRes.data) ? actorsRes.data : actorsRes.data.items || []
      const lotsData = Array.isArray(lotsRes.data) ? lotsRes.data : lotsRes.data.items || []
      setActors(actorsData)
      setLots(lotsData)
      setNotifications(notifRes.data || [])
      setEmergencyAlerts(emergencyRes.data || [])
      setMyOrCards(cardsRes.data || { kara_cards: [], collector_cards: [] })
      setMyFees(Array.isArray(feesRes.data) ? feesRes.data : [])
      setCommuneCardQueue(Array.isArray(queueRes.data) ? queueRes.data : [])
    } catch (e: any) {
      if (isInvalidTokenError(e)) {
        clearAuthSession('Session invalide/expiree. Veuillez vous reconnecter.')
        return
      }
    } finally {
      setContextLoading(false)
    }
  }

  const loadFiliereCatalog = async (filiere: string) => {
    try {
      const [rolesRes, productRes, essenceRes] = await Promise.all([
        client.get('/rbac/roles', {
          params: {
            filiere,
            include_common: false,
            active_only: true,
            for_current_actor: true,
            actor_type: roleActorType !== 'all' ? roleActorType : undefined,
          },
        }),
        client.get('/catalog/products', { params: { filiere } }).catch(() => ({ data: [] })),
        client.get('/catalog/essences').catch(() => ({ data: [] })),
      ])
      setRbacRoles(rolesRes.data || [])
      setCatalogProducts(productRes.data || [])
      setEssences(essenceRes.data || [])
      const firstRole = rolesRes.data?.[0]?.code
      if (firstRole) setActorForm((p: any) => ({ ...p, role: firstRole }))
    } catch (e: any) {
      if (isInvalidTokenError(e)) {
        clearAuthSession('Session invalide/expiree. Veuillez vous reconnecter.')
      }
    }
  }

  const loadTerritories = async (nextRegionCode?: string, nextDistrictCode?: string, nextCommuneCode?: string) => {
    if (!token) return
    setTerritoriesLoading(true)
    try {
      const { data: regionsData } = await client.get('/territories/regions')
      const regionList: TerritoryOption[] = Array.isArray(regionsData) ? regionsData : []
      setRegions(regionList)
      const regionCode = nextRegionCode || actorForm.region_code || regionList[0]?.code || ''
      if (!regionCode) {
        setDistricts([])
        setCommunes([])
        setFokontany([])
        setActorForm((p: any) => ({ ...p, region_code: '', district_code: '', commune_code: '', fokontany_code: '' }))
        return
      }

      const { data: districtsData } = await client.get('/territories/districts', { params: { region_code: regionCode } })
      const districtList: TerritoryOption[] = Array.isArray(districtsData) ? districtsData : []
      setDistricts(districtList)
      const districtCode = nextDistrictCode || actorForm.district_code || districtList[0]?.code || ''

      const communeList: TerritoryOption[] =
        districtCode
          ? (await client.get('/territories/communes', { params: { district_code: districtCode } })).data || []
          : []
      setCommunes(Array.isArray(communeList) ? communeList : [])
      const communeCode = nextCommuneCode || actorForm.commune_code || (communeList[0]?.code ?? '')

      const fokontanyList: TerritoryOption[] =
        communeCode
          ? (await client.get('/territories/fokontany', { params: { commune_code: communeCode } })).data || []
          : []
      setFokontany(Array.isArray(fokontanyList) ? fokontanyList : [])

      const fokontanyCode = actorForm.fokontany_code || (fokontanyList[0]?.code ?? '')
      setActorForm((p: any) => ({
        ...p,
        region_code: regionCode,
        district_code: districtCode,
        commune_code: communeCode,
        fokontany_code: fokontanyCode,
      }))
    } catch (e: any) {
      if (isInvalidTokenError(e)) {
        clearAuthSession('Session invalide/expiree. Veuillez vous reconnecter.')
        return
      }
      setRegions([])
      setDistricts([])
      setCommunes([])
      setFokontany([])
    } finally {
      setTerritoriesLoading(false)
    }
  }

  useEffect(() => {
    refreshContext()
    loadFiliereCatalog(actorForm.filiere)
    loadEntryRoles()
    loadTerritories()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  useEffect(() => {
    loadFiliereCatalog(actorForm.filiere)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [actorForm.filiere, roleActorType])

  useEffect(() => {
    if (!token) {
      setEntryStep('login')
      return
    }
    if (selectedRole && selectedFiliere) {
      setEntryStep('dashboard')
      loadRolePermissions(selectedRole)
      return
    }
    if (!selectedRole) {
      setEntryStep('role')
      return
    }
    setEntryStep('filiere')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, selectedRole, selectedFiliere])

  useEffect(() => {
    if (entryStep === 'role' && token) {
      loadEntryRoles()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entryStep, roleSearch, roleCategory, roleActorType])

  useEffect(() => {
    if (entryStep === 'dashboard') {
      window.history.pushState({ madavolaStep: 'dashboard' }, '')
    }
  }, [entryStep])

  useEffect(() => {
    const onPop = () => {
      if (entryStep === 'dashboard') {
        setEntryStep('filiere')
        return
      }
      if (entryStep === 'filiere') {
        setEntryStep('role')
      }
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [entryStep])

  const login = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      const { data } = await client.post('/auth/login', { identifier, password })
      setToken(data.access_token)
      localStorage.setItem(STORAGE_TOKEN_KEY, data.access_token)
      const storedRole = localStorage.getItem(STORAGE_ROLE_KEY) || ''
      const storedFiliere = (localStorage.getItem(STORAGE_FILIERE_KEY) as FiliereCode | null) || ''
      setSelectedRole(storedRole)
      setSelectedFiliere(storedFiliere)
      setEntryStep(storedRole ? (storedFiliere ? 'dashboard' : 'filiere') : 'role')
      showSuccess('Connexion reussie.')
    } catch (e: any) {
      showError(e, 'Echec de connexion')
    }
  }

  const logout = () => {
    clearAuthSession()
    showSuccess('Deconnexion effectuee.')
  }

  const createActor = async () => {
    if (!token) return showError(null, "Connectez-vous d'abord")
    if (!actorForm.region_code || !actorForm.district_code || !actorForm.commune_code) {
      return showError(null, 'Veuillez selectionner Region, District et Commune')
    }
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      const geo = await client.post('/geo-points', {
        lat: Number(actorForm.lat),
        lon: Number(actorForm.lon),
        accuracy_m: 10,
        source: 'mobile',
      })
      const payload = {
        type_personne: 'physique',
        nom: actorForm.nom,
        prenoms: actorForm.prenoms,
        email: actorForm.email,
        telephone: actorForm.telephone,
        password: actorForm.password,
        region_code: actorForm.region_code,
        district_code: actorForm.district_code,
        commune_code: actorForm.commune_code,
        fokontany_code: actorForm.fokontany_code || undefined,
        geo_point_id: geo.data.id,
        roles: [actorForm.role],
        filieres: [actorForm.filiere],
      }
      const { data } = await client.post('/actors', payload)
      showSuccess(`Acteur cree #${data.id}`)
      await refreshContext()
    } catch (e: any) {
      showError(e, "Echec de creation de l'acteur")
    }
  }

  const createCardRequest = async () => {
    if (!token || !me?.id || !me?.commune?.id) return showError(null, 'Profil incomplet: commune requise')
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      let data
      if (cardRequestKind === 'kara_orpailleur') {
        data = (await client.post('/or-compliance/kara-cards', {
          actor_id: me.id,
          commune_id: me.commune.id,
          cin: cardCin || me.cin || 'CIN_NON_RENSEIGNE',
          nationality: 'mg',
          residence_verified: true,
          tax_compliant: true,
          zone_allowed: true,
          public_order_clear: true,
        })).data
      } else {
        data = (await client.post('/or-compliance/collector-cards', {
          actor_id: me.id,
          issuing_commune_id: me.commune.id,
          notes: cardRequestKind === 'collector_bijoutier' ? 'demande_bijoutier' : 'demande_collecteur',
        })).data
      }
      setDebug(data)
      showSuccess(`Demande carte enregistree (#${data.id})`)
      await refreshContext()
    } catch (e: any) {
      showError(e, 'Echec de demande de carte')
    }
  }

  const markFeePaid = async (feeId: number) => {
    setMessage('')
    setMessageType('')
    try {
      await client.post(`/fees/${feeId}/mark-paid`, { payment_ref: `mobile-${Date.now()}` })
      showSuccess(`Frais #${feeId} marque paye`)
      await refreshContext()
    } catch (e: any) {
      showError(e, 'Echec mise a jour paiement')
    }
  }

  const decideCard = async (cardType: string, cardId: number, decision: 'approved' | 'rejected') => {
    setMessage('')
    setMessageType('')
    try {
      if (cardType === 'kara_bolamena') {
        await client.patch(`/or-compliance/kara-cards/${cardId}/decision`, { decision, notes: 'decision_commune_mobile' })
      } else {
        await client.patch(`/or-compliance/collector-cards/${cardId}/decision`, { decision, notes: 'decision_commune_mobile' })
      }
      showSuccess(`Decision enregistree pour ${cardType} #${cardId}`)
      await refreshContext()
    } catch (e: any) {
      showError(e, 'Echec validation carte')
    }
  }

  const createLot = async () => {
    if (!token) return showError(null, "Connectez-vous d'abord")
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      const meRes = await client.get('/auth/me')
      const geo = await client.post('/geo-points', {
        lat: Number(lotForm.lat),
        lon: Number(lotForm.lon),
        accuracy_m: 10,
        source: 'mobile',
      })
      const attributes: Record<string, string> = {}
      if (lotForm.attr_key && lotForm.attr_value) attributes[lotForm.attr_key] = lotForm.attr_value
      const payload: any = {
        filiere: lotForm.filiere,
        product_type: lotForm.product_type,
        quantity: Number(lotForm.quantity),
        unit: lotForm.unit,
        declare_geo_point_id: geo.data.id,
        declared_by_actor_id: meRes.data.id,
      }
      if (lotForm.filiere === 'PIERRE') {
        payload.sous_filiere = lotForm.sous_filiere
        if (lotForm.product_catalog_id) payload.product_catalog_id = Number(lotForm.product_catalog_id)
        payload.attributes = attributes
      }
      if (lotForm.filiere === 'BOIS') {
        payload.wood_essence_id = Number(lotForm.wood_essence_id)
        payload.wood_form = lotForm.wood_form
        if (lotForm.volume_m3) payload.volume_m3 = Number(lotForm.volume_m3)
      }
      const { data } = await client.post('/lots', payload)
      showSuccess(`Lot cree #${data.id}`)
      await refreshContext()
    } catch (e: any) {
      showError(e, 'Echec de creation du lot')
    }
  }

  const createTrade = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      const { data } = await client.post('/trades', {
        seller_actor_id: Number(tradeForm.seller_actor_id),
        buyer_actor_id: Number(tradeForm.buyer_actor_id),
        currency: 'MGA',
        items: [{ lot_id: Number(tradeForm.lot_id), quantity: Number(tradeForm.quantity), unit_price: Number(tradeForm.unit_price) }],
      })
      setTradeForm((p: any) => ({ ...p, trade_id: String(data.id) }))
      showSuccess(`Transaction creee #${data.id}`)
    } catch (e: any) {
      showError(e, 'Echec de creation de la transaction')
    }
  }

  const payTrade = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      const { data } = await client.post(`/trades/${Number(tradeForm.trade_id)}/pay`, { payment_mode: 'cash_declared' })
      showSuccess(`Transaction payee - statut=${data.status}`)
    } catch (e: any) {
      showError(e, 'Echec du paiement de la transaction')
    }
  }

  const confirmTrade = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      const { data } = await client.post(`/trades/${Number(tradeForm.trade_id)}/confirm`)
      showSuccess(`Transaction confirmee - statut=${data.status}`)
      await refreshContext()
    } catch (e: any) {
      showError(e, 'Echec de confirmation de la transaction')
    }
  }

  const createExport = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      const { data } = await client.post('/exports', { destination: exportForm.destination, total_weight: 1 })
      setExportForm((p: any) => ({ ...p, export_id: String(data.id) }))
      showSuccess(`Exportation creee #${data.id}`)
      await refreshContext()
    } catch (e: any) {
      showError(e, "Echec de creation de l'exportation")
    }
  }

  const linkExportLot = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      await client.post(`/exports/${Number(exportForm.export_id)}/lots`, [
        { lot_id: Number(exportForm.lot_id), quantity_in_export: Number(exportForm.qty) },
      ])
      showSuccess('Lot lie au dossier export')
    } catch (e: any) {
      showError(e, 'Echec du lien lot-export')
    }
  }

  const submitExport = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      await client.post(`/exports/${Number(exportForm.export_id)}/submit`, { status: 'submitted' })
      showSuccess('Dossier soumis')
      await refreshContext()
    } catch (e: any) {
      showError(e, 'Echec de soumission du dossier export')
    }
  }

  const validateExport = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      await client.post(`/exports/${Number(exportForm.export_id)}/validate`, {
        step_code: exportForm.step_code,
        decision: exportForm.decision,
        seal_number: exportForm.step_code === 'douanes' && exportForm.decision === 'approved' ? exportForm.seal_number || undefined : undefined,
      })
      showSuccess('Validation export enregistree')
      await refreshContext()
    } catch (e: any) {
      showError(e, 'Echec de validation export')
    }
  }

  const createTransport = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      const { data } = await client.post('/transports', {
        transporter_actor_id: Number(transportForm.transporter_actor_id),
        origin: transportForm.origin,
        destination: transportForm.destination,
        depart_at: new Date().toISOString(),
        items: [{ lot_id: Number(transportForm.lot_id), quantity: Number(transportForm.quantity) }],
      })
      setTransportForm((p: any) => ({ ...p, transport_id: String(data.id) }))
      showSuccess(`Transport cree #${data.id}`)
    } catch (e: any) {
      showError(e, 'Echec de creation du transport')
    }
  }

  const verifyTransport = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      const { data } = await client.post(`/transports/${Number(transportForm.transport_id)}/scan_verify`, { lot_id: Number(transportForm.verify_lot_id) })
      setDebug(data)
      showSuccess(`Controle transport: ${data.result || 'ok'}`)
    } catch (e: any) {
      showError(e, 'Echec de verification du transport')
    }
  }

  const createTransformation = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      const input_lot_ids = String(transformationForm.input_lot_ids).split(',').map((x) => Number(x.trim())).filter((x) => Number.isFinite(x) && x > 0)
      const outputs = String(transformationForm.outputs).split(',').map((token) => {
        const [quantity, unit, wood_form] = token.trim().split(':')
        return { quantity: Number(quantity), unit: unit || 'm3', wood_form: wood_form || 'planche' }
      })
      const { data } = await client.post('/transformations', {
        operation_type: transformationForm.operation_type,
        input_lot_ids,
        outputs,
      })
      setDebug(data)
      showSuccess(`Transformation #${data.event_id}`)
      await refreshContext()
    } catch (e: any) {
      showError(e, 'Echec de transformation')
    }
  }

  const verify = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      let data
      if (verifyKind === 'invoice') {
        data = (await client.get(`/verify/invoice/${encodeURIComponent(verifyValue)}`)).data
      } else if (verifyKind === 'actor') {
        data = (await client.get(`/verify/actor/${verifyValue}`)).data
      } else {
        data = (await client.get(`/verify/lot/${verifyValue}`)).data
      }
      setDebug(data)
    } catch (e: any) {
      showError(e, 'Echec de verification')
    }
  }

  const runNotifications = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      const { data } = await client.post('/notifications/run-expiry-reminders?thresholds=30,7,1')
      showSuccess(`Rappels executes : ${data.created_notifications}`)
      await refreshContext()
    } catch (e: any) {
      showError(e, "Echec d'execution des rappels")
    }
  }

  const sendEmergencyAlert = async () => {
    setMessage('')
    setMessageType('')
    setDebug(null)
    try {
      let geoPointId: number | undefined
      if (emergencyForm.lat && emergencyForm.lon) {
        const geo = await client.post('/geo-points', {
          lat: Number(emergencyForm.lat),
          lon: Number(emergencyForm.lon),
          accuracy_m: 20,
          source: 'mobile_emergency',
        })
        geoPointId = geo.data.id
      }
      const { data } = await client.post('/emergency-alerts', {
        title: emergencyForm.title,
        message: emergencyForm.message,
        target_service: emergencyForm.target_service,
        severity: emergencyForm.severity,
        filiere: emergencyForm.filiere,
        geo_point_id: geoPointId,
      })
      showSuccess(`Alerte d'urgence envoyee #${data.id}`)
      setEmergencyForm((p: any) => ({ ...p, message: '', lat: '', lon: '' }))
      await refreshContext()
    } catch (e: any) {
      showError(e, "Echec d'envoi de l'alerte d'urgence")
    }
  }

  const continueFromRole = () => {
    if (!selectedRole) {
      setMessageType('error')
      setMessage('Selectionnez un role pour continuer.')
      return
    }
    localStorage.setItem(STORAGE_ROLE_KEY, selectedRole)
    setEntryStep('filiere')
  }

  const continueFromFiliere = async () => {
    if (!selectedRole || !selectedFiliere) {
      setMessageType('error')
      setMessage('Selectionnez un role et une filiere.')
      return
    }
    localStorage.setItem(STORAGE_ROLE_KEY, selectedRole)
    localStorage.setItem(STORAGE_FILIERE_KEY, selectedFiliere)
    setActorForm((p: any) => ({ ...p, filiere: selectedFiliere, role: selectedRole }))
    setLotForm((p: any) => ({ ...p, filiere: selectedFiliere }))
    await loadRolePermissions(selectedRole)
    setActiveTab('actors')
    setEntryStep('dashboard')
  }

  return (
    <div className="container">
      <div className="card">
        <h1 className="title">MADAVOLA Mobile OR / PIERRE / BOIS</h1>
        <small>Branchement mobile des workflows utilisateur (session, acteurs, lots, transactions, exportations, transports, transformations, scan, notifications).</small>
      </div>

      {entryStep === 'login' && (
        <div className="card">
          <h2 className="title">Connexion</h2>
          <div className="row">
            <input placeholder="email ou telephone" value={identifier} onChange={(e) => setIdentifier(e.target.value)} />
            <input placeholder="mot de passe" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <button onClick={login}>Se connecter</button>
          </div>
        </div>
      )}

      {entryStep === 'role' && (
        <div className="card">
          <h2 className="title">Etape 1 - Choisir votre role</h2>
          <small>Source unique: API RBAC.</small>
          <div className="row" style={{ marginTop: 8 }}>
            <MobileRoleSelector
              filiere={(selectedFiliere || 'OR') as FiliereCode}
              onFiliereChange={() => undefined}
              selectedRole={selectedRole}
              onRoleSelect={(roleCode) => setSelectedRole(roleCode)}
              roles={entryRoles}
              search={roleSearch}
              onSearchChange={setRoleSearch}
              category={roleCategory}
              onCategoryChange={setRoleCategory}
              actorType={roleActorType}
              onActorTypeChange={setRoleActorType}
              showFiliereSelect={false}
            />
            {entryRolesLoading && <small>Chargement des roles...</small>}
            {entryRolesError && <small style={{ color: '#a12a22' }}>{entryRolesError}</small>}
            {!entryRolesLoading && !entryRolesError && entryRoles.length === 0 && (
              <small>Aucun role disponible pour votre compte.</small>
            )}
            <button onClick={continueFromRole} disabled={!selectedRole}>
              Continuer
            </button>
            <button className="secondary" onClick={logout}>
              Se deconnecter
            </button>
          </div>
        </div>
      )}

      {entryStep === 'filiere' && (
        <div className="card">
          <h2 className="title">Etape 2 - Choisir votre filiere</h2>
          <div className="row">
            <select value={selectedFiliere} onChange={(e) => setSelectedFiliere(e.target.value as FiliereCode)}>
              <option value="">Selectionner</option>
              <option value="OR">OR</option>
              <option value="PIERRE">PIERRE</option>
              <option value="BOIS">BOIS</option>
            </select>
            <button onClick={continueFromFiliere} disabled={!selectedRole || !selectedFiliere || permissionsLoading}>
              {permissionsLoading ? 'Chargement...' : 'Continuer'}
            </button>
            <button className="secondary" onClick={() => setEntryStep('role')}>
              Retour au role
            </button>
          </div>
        </div>
      )}

      {entryStep === 'dashboard' && (
        <div className="card">
          <div className="row">
            <span className="badge">
              Session #{me?.id || '-'} | Role: {selectedRole || '-'} | Filiere: {selectedFiliere || '-'}
            </span>
            {contextLoading && <small>Chargement des donnees...</small>}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <button className="secondary" onClick={() => setEntryStep('role')}>Changer role</button>
              <button className="secondary" onClick={() => setEntryStep('filiere')}>Changer filiere</button>
            </div>
            <button className="secondary" onClick={logout}>Se deconnecter</button>
          </div>
        </div>
      )}

      {entryStep === 'dashboard' && (
        <div className="card">
          <div className="tabs" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10 }}>
            {(visibleTabs.length ? visibleTabs : TABS).map((t) => (
              <button
                key={t.key}
                className={`${activeTab === t.key ? '' : 'secondary'} ${t.key === 'verify' ? 'scan-cta' : ''}`}
                onClick={() => setActiveTab(t.key)}
              >
                {t.label}
              </button>
            ))}
          </div>
          {visibleTabs.length === 0 && (
            <small>Aucun module autorise pour ce role.</small>
          )}
        </div>
      )}

      {entryStep === 'dashboard' && activeTab === 'actors' && (
        <div className="card">
          <h2 className="title">Creer acteur</h2>
          <div className="row">
            <MobileRoleSelector
              filiere={actorForm.filiere as FiliereCode}
              onFiliereChange={(next) => setActorForm((p: any) => ({ ...p, filiere: next }))}
              selectedRole={actorForm.role}
              onRoleSelect={(roleCode) => setActorForm((p: any) => ({ ...p, role: roleCode }))}
              roles={rbacRoles}
              search={roleSearch}
              onSearchChange={setRoleSearch}
              category={roleCategory}
              onCategoryChange={setRoleCategory}
              actorType={roleActorType}
              onActorTypeChange={setRoleActorType}
            />
            <select
              value={actorForm.region_code}
              onChange={async (e) => {
                const regionCode = e.target.value
                setActorForm((p: any) => ({ ...p, region_code: regionCode, district_code: '', commune_code: '', fokontany_code: '' }))
                await loadTerritories(regionCode, '', '')
              }}
            >
              <option value="">Region</option>
              {regions.map((r) => <option key={r.code} value={r.code}>{r.name}</option>)}
            </select>
            <select
              value={actorForm.district_code}
              onChange={async (e) => {
                const districtCode = e.target.value
                setActorForm((p: any) => ({ ...p, district_code: districtCode, commune_code: '', fokontany_code: '' }))
                await loadTerritories(actorForm.region_code, districtCode, '')
              }}
              disabled={!actorForm.region_code}
            >
              <option value="">District</option>
              {districts.map((d) => <option key={d.code} value={d.code}>{d.name}</option>)}
            </select>
            <select
              value={actorForm.commune_code}
              onChange={async (e) => {
                const communeCode = e.target.value
                setActorForm((p: any) => ({ ...p, commune_code: communeCode, fokontany_code: '' }))
                await loadTerritories(actorForm.region_code, actorForm.district_code, communeCode)
              }}
              disabled={!actorForm.district_code}
            >
              <option value="">Commune</option>
              {communes.map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
            <select
              value={actorForm.fokontany_code}
              onChange={(e) => setActorForm((p: any) => ({ ...p, fokontany_code: e.target.value }))}
              disabled={!actorForm.commune_code}
            >
              <option value="">Fokontany (optionnel)</option>
              {fokontany.map((f) => <option key={f.code || f.name} value={f.code || ''}>{f.name}</option>)}
            </select>
            {territoriesLoading && <small>Chargement des territoires...</small>}
            <input value={actorForm.nom} onChange={(e) => setActorForm((p: any) => ({ ...p, nom: e.target.value }))} placeholder="Nom" />
            <input value={actorForm.prenoms} onChange={(e) => setActorForm((p: any) => ({ ...p, prenoms: e.target.value }))} placeholder="Prenoms" />
            <input value={actorForm.email} onChange={(e) => setActorForm((p: any) => ({ ...p, email: e.target.value }))} placeholder="Email" />
            <input value={actorForm.telephone} onChange={(e) => setActorForm((p: any) => ({ ...p, telephone: e.target.value }))} placeholder="Telephone" />
            <input value={actorForm.password} onChange={(e) => setActorForm((p: any) => ({ ...p, password: e.target.value }))} placeholder="Mot de passe" />
            <button onClick={createActor}>Creer acteur</button>
          </div>

          <h2 className="title" style={{ marginTop: 16 }}>Demande carte OR (acteur)</h2>
          <div className="row">
            <select value={cardRequestKind} onChange={(e) => setCardRequestKind(e.target.value as CardRequestKind)}>
              <option value="kara_orpailleur">Carte orpailleur (Kara)</option>
              <option value="collector_collecteur">Carte collecteur</option>
              <option value="collector_bijoutier">Carte collecteur (bijoutier)</option>
            </select>
            <input value={cardCin} onChange={(e) => setCardCin(e.target.value)} placeholder="CIN (orpailleur)" />
            <button onClick={createCardRequest}>Soumettre la demande</button>
          </div>

          <h2 className="title" style={{ marginTop: 16 }}>Mes frais</h2>
          <ul>
            {myFees.filter((f: any) => f.status === 'pending').length === 0 && <li>Aucun frais en attente.</li>}
            {myFees.filter((f: any) => f.status === 'pending').map((f: any) => (
              <li key={f.id}>
                #{f.id} {f.fee_type} {f.amount} {f.currency}
                <button className="secondary" style={{ marginLeft: 8 }} onClick={() => markFeePaid(f.id)}>Marquer paye</button>
              </li>
            ))}
          </ul>

          <h2 className="title" style={{ marginTop: 16 }}>Mes cartes</h2>
          <ul>
            {(myOrCards.kara_cards || []).map((c: any) => <li key={`k-${c.id}`}>Kara #{c.id} | {c.status}</li>)}
            {(myOrCards.collector_cards || []).map((c: any) => <li key={`c-${c.id}`}>Collecteur #{c.id} | {c.status}</li>)}
            {(myOrCards.kara_cards || []).length === 0 && (myOrCards.collector_cards || []).length === 0 && <li>Aucune carte.</li>}
          </ul>

          {canValidateCommune && (
            <>
              <h2 className="title" style={{ marginTop: 16 }}>Validation commune</h2>
              <ul>
                {communeCardQueue.length === 0 && <li>Aucune demande en attente.</li>}
                {communeCardQueue.map((q: any) => (
                  <li key={`${q.card_type}-${q.card_id}`}>
                    {q.card_type} #{q.card_id} | acteur={q.actor_name || q.actor_id} | frais={q.fee_status || '-'}
                    <button style={{ marginLeft: 8 }} onClick={() => decideCard(q.card_type, q.card_id, 'approved')}>Valider</button>
                    <button className="secondary" style={{ marginLeft: 8 }} onClick={() => decideCard(q.card_type, q.card_id, 'rejected')}>Refuser</button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      {entryStep === 'dashboard' && activeTab === 'lots' && (
        <div className="card">
          <h2 className="title">Declarer lot</h2>
          <div className="row">
            <select value={lotForm.filiere} onChange={(e) => setLotForm((p: any) => ({ ...p, filiere: e.target.value }))}>
              <option value="OR">OR</option>
              <option value="PIERRE">PIERRE</option>
              <option value="BOIS">BOIS</option>
            </select>
            {lotForm.filiere === 'PIERRE' && (
              <>
                <select value={lotForm.sous_filiere} onChange={(e) => setLotForm((p: any) => ({ ...p, sous_filiere: e.target.value }))}>
                  <option value="GEMME">GEMME</option>
                  <option value="INDUSTRIELLE">INDUSTRIELLE</option>
                </select>
                <select value={lotForm.product_catalog_id} onChange={(e) => setLotForm((p: any) => ({ ...p, product_catalog_id: e.target.value }))}>
                  <option value="">Produit catalog</option>
                  {(catalogProducts || []).map((p: any) => <option key={p.id} value={p.id}>{p.code} - {p.nom}</option>)}
                </select>
                <input placeholder="Attribut cle" value={lotForm.attr_key} onChange={(e) => setLotForm((p: any) => ({ ...p, attr_key: e.target.value }))} />
                <input placeholder="Attribut valeur" value={lotForm.attr_value} onChange={(e) => setLotForm((p: any) => ({ ...p, attr_value: e.target.value }))} />
              </>
            )}
            {lotForm.filiere === 'BOIS' && (
              <>
                <select value={lotForm.wood_essence_id} onChange={(e) => setLotForm((p: any) => ({ ...p, wood_essence_id: e.target.value }))}>
                  <option value="">Essence</option>
                  {(essences || []).map((e: any) => <option key={e.id} value={e.id}>{e.code_essence} - {e.nom}</option>)}
                </select>
                <select value={lotForm.wood_form} onChange={(e) => setLotForm((p: any) => ({ ...p, wood_form: e.target.value }))}>
                  <option value="tronc">tronc</option>
                  <option value="grume">grume</option>
                  <option value="billon">billon</option>
                  <option value="planche">planche</option>
                  <option value="lot_scie">lot_scie</option>
                  <option value="produit_fini">produit_fini</option>
                </select>
                <input placeholder="volume m3" value={lotForm.volume_m3} onChange={(e) => setLotForm((p: any) => ({ ...p, volume_m3: e.target.value }))} />
              </>
            )}
            <input placeholder="type produit" value={lotForm.product_type} onChange={(e) => setLotForm((p: any) => ({ ...p, product_type: e.target.value }))} />
            <input placeholder="quantite" value={lotForm.quantity} onChange={(e) => setLotForm((p: any) => ({ ...p, quantity: e.target.value }))} />
            <input placeholder="unite" value={lotForm.unit} onChange={(e) => setLotForm((p: any) => ({ ...p, unit: e.target.value }))} />
            <button onClick={createLot}>Creer lot</button>
            {lots.length === 0 && <small>Aucun lot disponible.</small>}
          </div>
        </div>
      )}

      {entryStep === 'dashboard' && activeTab === 'trades' && (
        <div className="card">
          <h2 className="title">Parcours transaction</h2>
          <div className="row">
            <select value={tradeForm.seller_actor_id} onChange={(e) => setTradeForm((p: any) => ({ ...p, seller_actor_id: e.target.value }))}>
              <option value="">Vendeur</option>
              {actors.map((a: any) => <option key={a.id} value={a.id}>{a.id} - {a.nom}</option>)}
            </select>
            <select value={tradeForm.buyer_actor_id} onChange={(e) => setTradeForm((p: any) => ({ ...p, buyer_actor_id: e.target.value }))}>
              <option value="">Acheteur</option>
              {actors.map((a: any) => <option key={a.id} value={a.id}>{a.id} - {a.nom}</option>)}
            </select>
            <select value={tradeForm.lot_id} onChange={(e) => setTradeForm((p: any) => ({ ...p, lot_id: e.target.value }))}>
              <option value="">Lot</option>
              {lots.map((l: any) => <option key={l.id} value={l.id}>#{l.id} {l.filiere} {l.quantity} {l.unit}</option>)}
            </select>
            <input placeholder="Quantite" value={tradeForm.quantity} onChange={(e) => setTradeForm((p: any) => ({ ...p, quantity: e.target.value }))} />
            <input placeholder="Prix unitaire" value={tradeForm.unit_price} onChange={(e) => setTradeForm((p: any) => ({ ...p, unit_price: e.target.value }))} />
            <button onClick={createTrade}>Creer transaction</button>
            <input placeholder="ID transaction" value={tradeForm.trade_id} onChange={(e) => setTradeForm((p: any) => ({ ...p, trade_id: e.target.value }))} />
            <button onClick={payTrade}>Payer la transaction</button>
            <button onClick={confirmTrade}>Confirmer la transaction</button>
            {actors.length === 0 && <small>Aucun acteur disponible.</small>}
          </div>
        </div>
      )}

      {entryStep === 'dashboard' && activeTab === 'exports' && (
        <div className="card">
          <h2 className="title">Parcours exportation</h2>
          <div className="row">
            <input placeholder="Destination" value={exportForm.destination} onChange={(e) => setExportForm((p: any) => ({ ...p, destination: e.target.value }))} />
            <button onClick={createExport}>Creer le dossier exportation</button>
            <input placeholder="ID exportation" value={exportForm.export_id} onChange={(e) => setExportForm((p: any) => ({ ...p, export_id: e.target.value }))} />
            <select value={exportForm.lot_id} onChange={(e) => setExportForm((p: any) => ({ ...p, lot_id: e.target.value }))}>
              <option value="">Lot</option>
              {lots.map((l: any) => <option key={l.id} value={l.id}>#{l.id} {l.filiere}</option>)}
            </select>
            <input placeholder="Quantite export" value={exportForm.qty} onChange={(e) => setExportForm((p: any) => ({ ...p, qty: e.target.value }))} />
            <button onClick={linkExportLot}>Lier le lot</button>
            <button onClick={submitExport}>Soumettre</button>
            <select value={exportForm.step_code} onChange={(e) => setExportForm((p: any) => ({ ...p, step_code: e.target.value }))}>
              <option value="mines">mines</option>
              <option value="douanes">douanes</option>
            </select>
            <select value={exportForm.decision} onChange={(e) => setExportForm((p: any) => ({ ...p, decision: e.target.value }))}>
              <option value="approved">approved</option>
              <option value="rejected">rejected</option>
            </select>
            <input placeholder="Numero de scelle" value={exportForm.seal_number} onChange={(e) => setExportForm((p: any) => ({ ...p, seal_number: e.target.value }))} />
            <button onClick={validateExport}>Valider l'etape</button>
          </div>
        </div>
      )}

      {entryStep === 'dashboard' && activeTab === 'transports' && (
        <div className="card">
          <h2 className="title">Transport BOIS</h2>
          <div className="row">
            <input placeholder="ID acteur transporteur" value={transportForm.transporter_actor_id} onChange={(e) => setTransportForm((p: any) => ({ ...p, transporter_actor_id: e.target.value }))} />
            <select value={transportForm.lot_id} onChange={(e) => setTransportForm((p: any) => ({ ...p, lot_id: e.target.value }))}>
              <option value="">Lot</option>
              {lots.map((l: any) => <option key={l.id} value={l.id}>#{l.id} {l.filiere}</option>)}
            </select>
            <input placeholder="Quantite" value={transportForm.quantity} onChange={(e) => setTransportForm((p: any) => ({ ...p, quantity: e.target.value }))} />
            <input placeholder="Origine" value={transportForm.origin} onChange={(e) => setTransportForm((p: any) => ({ ...p, origin: e.target.value }))} />
            <input placeholder="Destination" value={transportForm.destination} onChange={(e) => setTransportForm((p: any) => ({ ...p, destination: e.target.value }))} />
            <button onClick={createTransport}>Creer le transport</button>
            <input placeholder="ID transport" value={transportForm.transport_id} onChange={(e) => setTransportForm((p: any) => ({ ...p, transport_id: e.target.value }))} />
            <input placeholder="ID lot a verifier" value={transportForm.verify_lot_id} onChange={(e) => setTransportForm((p: any) => ({ ...p, verify_lot_id: e.target.value }))} />
            <button className="verify-cta" onClick={verifyTransport}>Verifier le scan</button>
          </div>
        </div>
      )}

      {entryStep === 'dashboard' && activeTab === 'transformations' && (
        <div className="card">
          <h2 className="title">Transformation</h2>
          <div className="row">
            <input placeholder="Operation" value={transformationForm.operation_type} onChange={(e) => setTransformationForm((p: any) => ({ ...p, operation_type: e.target.value }))} />
            <input placeholder="IDs lots entree (12,13)" value={transformationForm.input_lot_ids} onChange={(e) => setTransformationForm((p: any) => ({ ...p, input_lot_ids: e.target.value }))} />
            <input placeholder="Sorties (2:m3:planche,1:m3:lot_scie)" value={transformationForm.outputs} onChange={(e) => setTransformationForm((p: any) => ({ ...p, outputs: e.target.value }))} />
            <button onClick={createTransformation}>Lancer la transformation</button>
          </div>
        </div>
      )}

      {entryStep === 'dashboard' && activeTab === 'verify' && (
        <div className="card">
          <h2 className="title">Scan et verification</h2>
          <div className="row">
            <select value={verifyKind} onChange={(e) => setVerifyKind(e.target.value as VerifyKind)}>
              <option value="actor">Acteur</option>
              <option value="lot">Lot</option>
              <option value="invoice">Facture</option>
            </select>
            <div className="camera-inline">
              <input placeholder="ID / Reference" value={verifyValue} onChange={(e) => setVerifyValue(e.target.value)} />
              <button
                type="button"
                className="secondary camera-btn"
                title="Ouvrir la camera"
                onClick={() => cameraInputRef.current?.click()}
              >
                📷
              </button>
            </div>
            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              style={{ display: 'none' }}
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (!file) return
                showSuccess(`Image capturee (${file.name}). Appuyez sur "Verifier" pour lancer le controle.`)
              }}
            />
            <button className="verify-cta" onClick={verify}>Verifier</button>
          </div>
        </div>
      )}

      {entryStep === 'dashboard' && activeTab === 'notifications' && (
        <div className="card">
          <h2 className="title">Notifications</h2>
          <div className="row">
            <button onClick={runNotifications}>Lancer les rappels</button>
            <button className="secondary" onClick={refreshContext}>Rafraichir</button>
          </div>
          {(notifications || []).length > 0 ? <pre>{JSON.stringify(notifications, null, 2)}</pre> : <small>Aucune notification.</small>}
          <h3>Alerte d'urgence Police/Gendarmerie</h3>
          <div className="row">
            <input placeholder="Titre" value={emergencyForm.title} onChange={(e) => setEmergencyForm((p: any) => ({ ...p, title: e.target.value }))} />
            <input placeholder="Message urgence" value={emergencyForm.message} onChange={(e) => setEmergencyForm((p: any) => ({ ...p, message: e.target.value }))} />
            <select value={emergencyForm.target_service} onChange={(e) => setEmergencyForm((p: any) => ({ ...p, target_service: e.target.value }))}>
              <option value="both">Police + Gendarmerie</option>
              <option value="police">police</option>
              <option value="gendarmerie">gendarmerie</option>
            </select>
            <select value={emergencyForm.severity} onChange={(e) => setEmergencyForm((p: any) => ({ ...p, severity: e.target.value }))}>
              <option value="medium">Moyenne</option>
              <option value="high">Haute</option>
              <option value="critical">Critique</option>
            </select>
            <select value={emergencyForm.filiere} onChange={(e) => setEmergencyForm((p: any) => ({ ...p, filiere: e.target.value }))}>
              <option value="OR">OR</option>
              <option value="PIERRE">PIERRE</option>
              <option value="BOIS">BOIS</option>
            </select>
            <input placeholder="latitude (optionnel)" value={emergencyForm.lat} onChange={(e) => setEmergencyForm((p: any) => ({ ...p, lat: e.target.value }))} />
            <input placeholder="longitude (optionnel)" value={emergencyForm.lon} onChange={(e) => setEmergencyForm((p: any) => ({ ...p, lon: e.target.value }))} />
            <button className="alert-cta" onClick={sendEmergencyAlert} disabled={!String(emergencyForm.message || '').trim()}>Envoyer l'alerte</button>
          </div>
          {(emergencyAlerts || []).length > 0 && <pre>{JSON.stringify(emergencyAlerts, null, 2)}</pre>}
        </div>
      )}

      {message && (
        <div className={`banner ${messageType === 'error' ? 'banner-error' : 'banner-success'}`} role="alert">
          {message}
        </div>
      )}
      {debug && (import.meta as any).env?.DEV && (
        <div className="card">
          <pre>{JSON.stringify(debug, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

