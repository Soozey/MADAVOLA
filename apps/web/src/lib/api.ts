import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'

// En dev, utiliser le proxy Vite (/api → localhost:8000) pour éviter CORS et erreurs de connexion
const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? '/api/v1' : 'http://localhost:8000/api/v1')

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Intercepteur pour ajouter le token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token')
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Intercepteur 401 : tenter refresh token avant de rediriger vers login
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config
        const isRefreshRequest = originalRequest?.url?.includes?.('/auth/refresh')
        if (error.response?.status === 401 && !originalRequest._retry && !isRefreshRequest) {
          originalRequest._retry = true
          const refresh = localStorage.getItem('refresh_token')
          if (refresh) {
            try {
              const data = await this.refreshToken(refresh)
              localStorage.setItem('access_token', data.access_token)
              localStorage.setItem('refresh_token', data.refresh_token)
              if (originalRequest.headers) originalRequest.headers.Authorization = `Bearer ${data.access_token}`
              return this.client(originalRequest)
            } catch (_) {
              // refresh échoué : déconnexion
            }
          }
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  async login(identifier: string, password: string) {
    const response = await this.client.post('/auth/login', {
      identifier,
      password,
    })
    return response.data
  }

  async getMe() {
    const response = await this.client.get('/auth/me')
    return response.data
  }

  async patchMe(data: {
    nom?: string
    prenoms?: string
    date_naissance?: string
    adresse_text?: string
    cin?: string
    cin_date_delivrance?: string
    commune_code?: string
    fokontany_code?: string
  }) {
    const response = await this.client.patch('/auth/me', data)
    return response.data
  }

  async changePassword(currentPassword: string, newPassword: string) {
    const response = await this.client.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
    return response.data
  }

  async refreshToken(refreshToken: string) {
    const response = await this.client.post('/auth/refresh', { refresh_token: refreshToken })
    return response.data
  }

  async getActors(params?: { role?: string; filiere?: string; commune_code?: string; status?: string; page?: number; page_size?: number }) {
    const response = await this.client.get('/actors', { params })
    return response.data
  }

  async createActor(data: {
    type_personne: string
    nom: string
    prenoms?: string
    cin?: string
    nif?: string
    stat?: string
    rccm?: string
    telephone: string
    email?: string
    password: string
    region_code: string
    district_code: string
    commune_code: string
    fokontany_code?: string
    geo_point_id: number
    roles: string[]
    filieres: string[]
  }) {
    const response = await this.client.post('/actors', data)
    return response.data
  }

  async updateActorStatus(actorId: number, status: 'active' | 'rejected') {
    const response = await this.client.patch(`/actors/${actorId}/status`, { status })
    return response.data
  }

  async getActorRoles(actorId: number) {
    const response = await this.client.get(`/actors/${actorId}/roles`)
    return response.data
  }

  async getActor(actorId: number) {
    const response = await this.client.get(`/actors/${actorId}`)
    return response.data
  }
  async uploadActorPhoto(actorId: number, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post(`/actors/${actorId}/photo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }

  async getActorKyc(actorId: number) {
    const response = await this.client.get(`/actors/${actorId}/kyc`)
    return response.data
  }

  async createActorKyc(actorId: number, data: { pieces: string[]; note?: string }) {
    const response = await this.client.post(`/actors/${actorId}/kyc`, data)
    return response.data
  }

  async getActorWallets(actorId: number) {
    const response = await this.client.get(`/actors/${actorId}/wallets`)
    return response.data
  }

  async createActorWallet(
    actorId: number,
    data: { provider: 'mobile_money' | 'bank' | 'card'; operator_name?: string; account_ref: string; is_primary?: boolean }
  ) {
    const response = await this.client.post(`/actors/${actorId}/wallets`, data)
    return response.data
  }

  async getCommuneProfile(communeId: number) {
    const response = await this.client.get(`/actors/communes/${communeId}/profile`)
    return response.data
  }

  async patchCommuneProfile(
    communeId: number,
    data: { mobile_money_account_ref?: string; receiver_name?: string; receiver_phone?: string; active?: boolean }
  ) {
    const response = await this.client.patch(`/actors/communes/${communeId}/profile`, data)
    return response.data
  }

  async getLots(params?: { owner_actor_id?: number; status?: string; page?: number; page_size?: number }) {
    const response = await this.client.get('/lots', { params })
    return response.data
  }

  async createLot(data: Record<string, unknown>) {
    const response = await this.client.post('/lots', data)
    return response.data
  }
  async splitLot(lotId: number, quantities: number[]) {
    const response = await this.client.post(`/lots/${lotId}/split`, { quantities })
    return response.data
  }
  async consolidateLots(data: { lot_ids: number[]; product_type: string; unit: string; declare_geo_point_id: number }) {
    const response = await this.client.post('/lots/consolidate', data)
    return response.data
  }

  async getCatalogProducts(params?: { filiere?: string; sous_filiere?: string }) {
    const response = await this.client.get('/catalog/products', { params })
    return response.data
  }
  async getEssences(params?: { categorie?: string }) {
    const response = await this.client.get('/catalog/essences', { params })
    return response.data
  }
  async createEssence(data: {
    code_essence: string
    nom: string
    categorie: 'A_protegee' | 'B_artisanale' | 'C_autre'
    export_autorise?: boolean
    requires_cites?: boolean
    rules_json?: Record<string, unknown>
    status?: string
  }) {
    const response = await this.client.post('/catalog/essences', data)
    return response.data
  }
  async updateEssence(essenceId: number, data: Record<string, unknown>) {
    const response = await this.client.put(`/catalog/essences/${essenceId}`, data)
    return response.data
  }
  async deleteEssence(essenceId: number) {
    const response = await this.client.delete(`/catalog/essences/${essenceId}`)
    return response.data
  }

  async createCatalogProduct(data: {
    code: string
    nom: string
    famille?: string
    filiere?: string
    sous_filiere: string
    allowed_units: string[]
    required_attributes: string[]
    export_restricted?: boolean
    export_rules?: Record<string, unknown>
  }) {
    const response = await this.client.post('/catalog/products', data)
    return response.data
  }

  async updateCatalogProduct(productId: number, data: Record<string, unknown>) {
    const response = await this.client.put(`/catalog/products/${productId}`, data)
    return response.data
  }

  async deleteCatalogProduct(productId: number) {
    const response = await this.client.delete(`/catalog/products/${productId}`)
    return response.data
  }

  async getActorAuthorizations(actorId: number, params?: { filiere?: string }) {
    const response = await this.client.get(`/actors/${actorId}/authorizations`, { params })
    return response.data
  }

  async createActorAuthorization(actorId: number, data: {
    filiere?: string
    authorization_type: string
    numero: string
    valid_from: string
    valid_to: string
    status?: string
    notes?: string
  }) {
    const response = await this.client.post(`/actors/${actorId}/authorizations`, data)
    return response.data
  }

  async getLot(lotId: number) {
    const response = await this.client.get(`/lots/${lotId}`)
    return response.data
  }
  async patchLotWoodClassification(
    lotId: number,
    data: {
      wood_classification?: 'LEGAL_EXPORTABLE' | 'LEGAL_NON_EXPORTABLE' | 'ILLEGAL' | 'A_DETRUIRE'
      cites_laf_status?: 'not_required' | 'required' | 'pending' | 'approved' | 'rejected'
      cites_ndf_status?: 'not_required' | 'required' | 'pending' | 'approved' | 'rejected'
      cites_international_status?: 'not_required' | 'required' | 'pending' | 'approved' | 'rejected'
      destruction_status?: 'pending' | 'approved' | 'validated' | 'rejected' | 'destroyed'
      destruction_evidence_urls?: string[]
      notes?: string
    }
  ) {
    const response = await this.client.patch(`/lots/${lotId}/wood-classification`, data)
    return response.data
  }

  async getTransactions(params?: {
    seller_actor_id?: number
    buyer_actor_id?: number
    status?: string
    page?: number
    page_size?: number
  }) {
    const response = await this.client.get('/transactions', { params })
    return response.data
  }

  async createTrade(data: {
    seller_actor_id: number
    buyer_actor_id: number
    currency?: string
    items: Array<{ lot_id: number; quantity: number; unit_price: number }>
  }) {
    const response = await this.client.post('/trades', data)
    return response.data
  }

  async payTrade(
    tradeId: number,
    data: { payment_mode?: 'mobile_money' | 'cash_declared'; provider_code?: string; external_ref?: string; idempotency_key?: string }
  ) {
    const response = await this.client.post(`/trades/${tradeId}/pay`, data)
    return response.data
  }

  async confirmTrade(tradeId: number) {
    const response = await this.client.post(`/trades/${tradeId}/confirm`)
    return response.data
  }
  async createTransport(data: {
    transporter_actor_id: number
    origin: string
    destination: string
    vehicle_ref?: string
    depart_at: string
    arrivee_estimee_at?: string
    notes?: string
    items: Array<{ lot_id: number; quantity: number }>
  }) {
    const response = await this.client.post('/transports', data)
    return response.data
  }
  async verifyTransportScan(transportId: number, lotId: number) {
    const response = await this.client.post(`/transports/${transportId}/scan_verify`, { lot_id: lotId })
    return response.data
  }
  async createTransformation(data: {
    operation_type: string
    input_lot_ids: number[]
    outputs: Array<{ quantity: number; unit: string; wood_form: string }>
    notes?: string
  }) {
    const response = await this.client.post('/transformations', data)
    return response.data
  }
  async requestApproval(data: {
    filiere: string
    workflow_type: string
    entity_type: string
    entity_id: number
    reference_texte?: string
    legal_todo?: string
  }) {
    const response = await this.client.post('/approvals', data)
    return response.data
  }
  async decideApproval(approvalId: number, data: { decision: 'approved' | 'rejected'; decision_notes?: string; reference_texte?: string }) {
    const response = await this.client.post(`/approvals/${approvalId}/decide`, data)
    return response.data
  }
  async getApprovals(params?: { filiere?: string; status?: string }) {
    const response = await this.client.get('/approvals', { params })
    return response.data
  }

  async createTransaction(data: Record<string, unknown>) {
    const response = await this.client.post('/transactions', data)
    return response.data
  }

  async getTransaction(transactionId: number) {
    const response = await this.client.get(`/transactions/${transactionId}`)
    return response.data
  }

  async initiateTransactionPayment(
    transactionId: number,
    data: { provider_code: string; external_ref?: string; idempotency_key?: string }
  ) {
    const response = await this.client.post(`/transactions/${transactionId}/initiate-payment`, data)
    return response.data
  }

  async getTransactionPayments(transactionId: number) {
    const response = await this.client.get(`/transactions/${transactionId}/payments`)
    return response.data
  }
  async finalizeTransaction(transactionId: number) {
    const response = await this.client.post(`/transactions/${transactionId}/finalize`)
    return response.data
  }

  // Exports (dossiers export)
  async getExports(params?: { status?: string; date_from?: string; date_to?: string; created_by_actor_id?: number }) {
    const response = await this.client.get('/exports', { params })
    return response.data
  }

  async createExport(data: { destination?: string; destination_commune_id?: number; destination_country?: string; transport_mode?: string; total_weight?: number; declared_value?: number }) {
    const response = await this.client.post('/exports', data)
    return response.data
  }

  async getExport(exportId: number) {
    const response = await this.client.get(`/exports/${exportId}`)
    return response.data
  }

  async updateExportStatus(exportId: number, status: string) {
    const response = await this.client.patch(`/exports/${exportId}/status`, { status })
    return response.data
  }

  async submitExport(exportId: number) {
    const response = await this.client.post(`/exports/${exportId}/submit`, { status: 'submitted' })
    return response.data
  }

  async validateExportStep(
    exportId: number,
    data: { step_code: 'mines' | 'douanes'; decision: 'approved' | 'rejected'; notes?: string; seal_number?: string; pv_document_id?: number }
  ) {
    const response = await this.client.post(`/exports/${exportId}/validate`, data)
    return response.data
  }

  async linkLotsToExport(exportId: number, lots: { lot_id: number; quantity_in_export: number }[]) {
    const response = await this.client.post(`/exports/${exportId}/lots`, lots)
    return response.data
  }
  async getOrExportChecklist(exportId: number) {
    const response = await this.client.get(`/or/exports/${exportId}/checklist`)
    return response.data
  }
  async verifyOrExportChecklistItem(exportId: number, checklist_item_id: number) {
    const response = await this.client.post(`/or/exports/${exportId}/checklist/verify`, { checklist_item_id })
    return response.data
  }

  // Factures
  async getInvoices(params?: { transaction_id?: number }) {
    const response = await this.client.get('/invoices', { params })
    return response.data
  }

  async getInvoice(invoiceId: number) {
    const response = await this.client.get(`/invoices/${invoiceId}`)
    return response.data
  }

  // Documents
  async getDocuments(params?: {
    owner_actor_id?: number
    related_entity_type?: string
    related_entity_id?: string
    doc_type?: string
  }) {
    const response = await this.client.get('/documents', { params })
    return response.data
  }

  async getDocument(documentId: number) {
    const response = await this.client.get(`/documents/${documentId}`)
    return response.data
  }
  async downloadDocumentFile(documentId: number): Promise<{ blob: Blob; filename: string }> {
    const response = await this.client.get(`/documents/${documentId}/download`, { responseType: 'blob' })
    const disposition = (response.headers['content-disposition'] || response.headers['Content-Disposition'] || '') as string
    const match = disposition.match(/filename="?([^";]+)"?/)
    return {
      blob: response.data as Blob,
      filename: match?.[1] || `document-${documentId}`,
    }
  }

  async uploadDocument(data: {
    doc_type: string
    owner_actor_id: number
    related_entity_type?: string
    related_entity_id?: string
    file: File
  }) {
    const formData = new FormData()
    formData.append('doc_type', data.doc_type)
    formData.append('owner_actor_id', String(data.owner_actor_id))
    if (data.related_entity_type) formData.append('related_entity_type', data.related_entity_type)
    if (data.related_entity_id) formData.append('related_entity_id', data.related_entity_id)
    formData.append('file', data.file)
    const response = await this.client.post('/documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }

  // Grand livre (ledger)
  async getLedgerEntries(params?: { actor_id?: number; lot_id?: number }) {
    const response = await this.client.get('/ledger', { params })
    return response.data
  }

  async getLedgerBalance(params?: { actor_id?: number }) {
    const response = await this.client.get('/ledger/balance', { params })
    return response.data
  }

  // Pénalités & Violations
  async getPenalties(params?: { violation_case_id?: number }) {
    const response = await this.client.get('/penalties', { params })
    return response.data
  }

  async createPenalty(data: { violation_case_id: number; penalty_type: string; amount?: number; action_on_lot?: string; seized_to_actor_id?: number }) {
    const response = await this.client.post('/penalties', data)
    return response.data
  }

  async getViolations(params?: { inspection_id?: number }) {
    const response = await this.client.get('/violations', { params })
    return response.data
  }

  async createViolation(data: { inspection_id: number; violation_type: string; legal_basis_ref?: string }) {
    const response = await this.client.post('/violations', data)
    return response.data
  }

  async createInspection(data: {
    inspected_actor_id?: number
    inspected_lot_id?: number
    inspected_invoice_id?: number
    result: string
    reason_code?: string
    notes?: string
    geo_point_id?: number
  }) {
    const response = await this.client.post('/inspections', data)
    return response.data
  }

  /** Régions (alias de getRegions pour compatibilité) */
  async getTerritories() {
    return this.getRegions()
  }

  async getDistricts(regionCode: string) {
    const response = await this.client.get('/territories/districts', {
      params: { region_code: regionCode },
    })
    return response.data
  }

  async getCommunes(districtCode: string) {
    const response = await this.client.get('/territories/communes', {
      params: { district_code: districtCode },
    })
    return response.data
  }

  async getAllCommunes() {
    const response = await this.client.get('/territories/communes-all')
    return response.data
  }

  async getFokontany(communeCode: string) {
    const response = await this.client.get('/territories/fokontany', {
      params: { commune_code: communeCode },
    })
    return response.data
  }

  async createGeoPoint(data: { lat: number; lon: number; accuracy_m?: number; source?: string }) {
    const response = await this.client.post('/geo-points', data)
    return response.data
  }

  // Référentiel des rôles (niveau, institution, acronyme)
  async getRoleReferential() {
    const response = await this.client.get('/roles/referential')
    return response.data
  }
  async getRolesWithPermission(permission: string) {
    const response = await this.client.get('/rbac/roles-with-permission', { params: { permission } })
    return response.data
  }
  async getRbacFilieres() {
    const response = await this.client.get('/rbac/filieres')
    return response.data
  }

  async getRbacRoles(params?: {
    filiere?: string
    include_common?: boolean
    search?: string
    category?: string
    actor_type?: 'USAGER' | 'AGENT_ETAT' | 'OPERATEUR_PRIVE' | 'TRANSVERSAL'
    active_only?: boolean
    for_current_actor?: boolean
  }) {
    const response = await this.client.get('/rbac/roles', { params })
    return response.data
  }
  async getRbacPermissions(role: string) {
    const response = await this.client.get('/rbac/permissions', { params: { role } })
    return response.data
  }

  async getOrTariffs() {
    const response = await this.client.get('/or-compliance/tariffs')
    return response.data
  }

  async createOrTariff(data: {
    card_type: string
    commune_id?: number
    amount: number
    min_amount?: number
    max_amount?: number
    effective_from: string
    effective_to?: string
  }) {
    const response = await this.client.post('/or-compliance/tariffs', data)
    return response.data
  }

  async createKaraCard(data: {
    actor_id: number
    commune_id: number
    cin: string
    nationality?: string
    residence_verified?: boolean
    tax_compliant?: boolean
    zone_allowed?: boolean
    public_order_clear?: boolean
    notes?: string
  }) {
    const response = await this.client.post('/or-compliance/kara-cards', data)
    return response.data
  }

  async getKaraCards(params?: { actor_id?: number; status?: string; commune_id?: number }) {
    const response = await this.client.get('/or-compliance/kara-cards', { params })
    return response.data
  }

  async decideKaraCard(cardId: number, decision: 'approved' | 'rejected' | 'suspended' | 'withdrawn', notes?: string) {
    const response = await this.client.patch(`/or-compliance/kara-cards/${cardId}/decision`, { decision, notes })
    return response.data
  }

  async createCollectorCard(data: { actor_id: number; issuing_commune_id: number; notes?: string }) {
    const response = await this.client.post('/or-compliance/collector-cards', data)
    return response.data
  }

  async getCollectorCards(params?: { actor_id?: number; status?: string; commune_id?: number }) {
    const response = await this.client.get('/or-compliance/collector-cards', { params })
    return response.data
  }
  async getMyOrCards() {
    const response = await this.client.get('/or-compliance/cards/my')
    return response.data
  }
  async requestCard(data: {
    card_type: 'kara_bolamena' | 'collector_card' | 'bijoutier_card'
    actor_id: number
    commune_id: number
    cin?: string
    notes?: string
  }) {
    const response = await this.client.post('/or-compliance/cards/request', data)
    return response.data
  }
  async validateCard(cardId: number, data: { card_type: 'kara_bolamena' | 'collector_card' | 'bijoutier_card'; decision: string; notes?: string }) {
    const response = await this.client.post(`/or-compliance/cards/${cardId}/validate`, {
      decision: data.decision,
      notes: data.notes,
    }, {
      params: { card_type: data.card_type },
    })
    return response.data
  }
  async renderCard(cardId: number, params: { card_type: 'kara_bolamena' | 'collector_card' | 'bijoutier_card'; side: 'front' | 'back' }) {
    const response = await this.client.get(`/or-compliance/cards/${cardId}/render`, { params })
    return response.data
  }
  async getCommuneCardQueue(params?: { status?: string; commune_id?: number }) {
    const response = await this.client.get('/or-compliance/cards/commune-queue', { params })
    return response.data
  }

  async attachCollectorDocument(cardId: number, docType: string, documentId: number) {
    const response = await this.client.post(`/or-compliance/collector-cards/${cardId}/documents`, {
      doc_type: docType,
      document_id: documentId,
    })
    return response.data
  }

  async verifyCollectorDocument(cardId: number, docType: string, documentId: number) {
    const response = await this.client.post(`/or-compliance/collector-cards/${cardId}/verify-document`, {
      doc_type: docType,
      document_id: documentId,
    })
    return response.data
  }

  async decideCollectorCard(cardId: number, decision: 'approved' | 'rejected' | 'suspended' | 'withdrawn', notes?: string) {
    const response = await this.client.patch(`/or-compliance/collector-cards/${cardId}/decision`, { decision, notes })
    return response.data
  }

  async submitCollectorAffiliation(data: {
    collector_card_id: number
    affiliate_actor_id: number
    affiliate_type: 'comptoir' | 'bijouterie'
    agreement_ref: string
    signed_at: string
  }) {
    const response = await this.client.post('/or-compliance/collector-affiliations', data)
    return response.data
  }

  async createComptoirLicense(data: { actor_id: number; cahier_des_charges_ref?: string }) {
    const response = await this.client.post('/or-compliance/comptoir-licenses', data)
    return response.data
  }

  async patchComptoirLicense(licenseId: number, data: {
    status?: string
    dtspm_status?: string
    fx_repatriation_status?: string
    notes?: string
  }) {
    const response = await this.client.patch(`/or-compliance/comptoir-licenses/${licenseId}`, data)
    return response.data
  }

  async runComplianceReminders(thresholds: string = '30,7,1') {
    const response = await this.client.post(`/or-compliance/reminders/run?thresholds=${encodeURIComponent(thresholds)}`)
    return response.data
  }

  async getComplianceNotifications(params?: { actor_id?: number }) {
    const response = await this.client.get('/or-compliance/notifications', { params })
    return response.data
  }

  // Dashboards par niveau (habilitations selon rôle)
  async getDashboardNational(params?: { date_from?: string; date_to?: string }) {
    const response = await this.client.get('/dashboards/national', { params })
    return response.data
  }

  async getDashboardRegional(
    regionId: number,
    params?: { date_from?: string; date_to?: string }
  ) {
    const response = await this.client.get('/dashboards/regional', {
      params: { region_id: regionId, ...params },
    })
    return response.data
  }

  async getDashboardCommune(
    communeId: number,
    params?: { date_from?: string; date_to?: string }
  ) {
    const response = await this.client.get('/dashboards/commune', {
      params: { commune_id: communeId, ...params },
    })
    return response.data
  }

  async getHomeWidgets() {
    const response = await this.client.get('/dashboards/home-widgets')
    return response.data
  }

  async publishInstitutionalMessage(message: string) {
    const response = await this.client.post('/dashboards/institutional-message', { message })
    return response.data
  }

  async getRegions() {
    const response = await this.client.get('/territories/regions')
    return response.data
  }

  async getActiveTerritoryVersion() {
    const response = await this.client.get('/territories/active')
    return response.data
  }

  async getReportNational(params?: { date_from?: string; date_to?: string }) {
    const response = await this.client.get('/reports/national', { params })
    return response.data
  }

  async getReportCommune(communeId: number, params?: { date_from?: string; date_to?: string }) {
    const response = await this.client.get('/reports/commune', {
      params: { commune_id: communeId, ...params },
    })
    return response.data
  }

  async getReportActor(actorId: number, params?: { date_from?: string; date_to?: string }) {
    const response = await this.client.get('/reports/actor', {
      params: { actor_id: actorId, ...params },
    })
    return response.data
  }

  async getDtspmBreakdown(baseAmount: number, currency: string = 'MGA') {
    const response = await this.client.get('/taxes/dtspm/breakdown', {
      params: { base_amount: baseAmount, currency },
    })
    return response.data
  }

  async getAuditLogs(params?: { actor_id?: number; entity_type?: string }) {
    const response = await this.client.get('/audit', { params })
    return response.data
  }
  async getAuditStockCoherence(params?: { actor_id?: number; lot_id?: number; include_coherent?: boolean }) {
    const response = await this.client.get('/audit/stock-coherence', { params })
    return response.data
  }

  async getFees(params?: { actor_id?: number }) {
    const response = await this.client.get('/fees', { params })
    return response.data
  }
  async createFee(data: {
    fee_type: string
    actor_id: number
    commune_id: number
    amount: number
    currency?: string
  }) {
    const response = await this.client.post('/fees', data)
    return response.data
  }
  async getFee(feeId: number) {
    const response = await this.client.get(`/fees/${feeId}`)
    return response.data
  }

  async updateFeeStatus(feeId: number, status: 'pending' | 'paid' | 'cancelled') {
    const response = await this.client.patch(`/fees/${feeId}/status`, { status })
    return response.data
  }

  async initiateFeePayment(
    feeId: number,
    data: { provider_code: string; external_ref?: string; idempotency_key?: string }
  ) {
    const response = await this.client.post(`/fees/${feeId}/initiate-payment`, data)
    return response.data
  }
  async markFeePaid(feeId: number, data?: { payment_ref?: string }) {
    const response = await this.client.post(`/fees/${feeId}/mark-paid`, data || {})
    return response.data
  }

  async getInspections(params?: { page?: number; page_size?: number }) {
    const response = await this.client.get('/inspections', { params })
    return response.data
  }

  async getGeoPoint(geoPointId: number) {
    const response = await this.client.get(`/geo-points/${geoPointId}`)
    return response.data
  }

  async transferLot(lotId: number, data: { new_owner_actor_id: number; payment_request_id: number }) {
    const response = await this.client.post(`/lots/${lotId}/transfer`, data)
    return response.data
  }

  async getNotifications(params?: { actor_id?: number }) {
    const response = await this.client.get('/notifications', { params })
    return response.data
  }

  async runExpiryReminders(thresholds: string = '30,7,1') {
    const response = await this.client.post(`/notifications/run-expiry-reminders?thresholds=${encodeURIComponent(thresholds)}`)
    return response.data
  }

  async getEmergencyAlerts(
    params?: { status?: string; target_service?: 'police' | 'gendarmerie' | 'both' | 'bianco' | 'environnement' | 'institutionnel' }
  ) {
    const response = await this.client.get('/emergency-alerts', { params })
    return response.data
  }

  async createEmergencyAlert(data: {
    title: string
    message: string
    severity?: 'medium' | 'high' | 'critical'
    target_service?: 'police' | 'gendarmerie' | 'both' | 'bianco' | 'environnement' | 'institutionnel'
    filiere?: string
    role_code?: string
    geo_point_id?: number
  }) {
    const response = await this.client.post('/emergency-alerts', data)
    return response.data
  }

  async updateEmergencyAlertStatus(alertId: number, status: 'acknowledged' | 'resolved' | 'rejected') {
    const response = await this.client.patch(`/emergency-alerts/${alertId}/status`, { status })
    return response.data
  }

  /** Vérification publique (sans auth) pour scan QR par contrôleur */
  async getVerifyActor(actorId: number) {
    const response = await this.client.get(`/verify/actor/${actorId}`)
    return response.data
  }

  async getVerifyLot(lotId: number) {
    const response = await this.client.get(`/verify/lot/${lotId}`)
    return response.data
  }

  async getVerifyInvoice(invoiceRef: string) {
    const response = await this.client.get(`/verify/invoice/${invoiceRef}`)
    return response.data
  }
  async getVerifyCard(cardRef: string | number) {
    const response = await this.client.get(`/verify/card/${cardRef}`)
    return response.data
  }

  async listContactRequests(params?: { status?: string }) {
    const response = await this.client.get('/messages/contacts', { params })
    return response.data
  }

  async createContactRequest(targetActorId: number) {
    const response = await this.client.post('/messages/contacts', { target_actor_id: targetActorId })
    return response.data
  }

  async decideContactRequest(contactId: number, decision: 'accepted' | 'rejected') {
    const response = await this.client.post(`/messages/contacts/${contactId}/decision`, { decision })
    return response.data
  }

  async listMessages(params?: { with_actor_id?: number }) {
    const response = await this.client.get('/messages', { params })
    return response.data
  }

  async sendMessage(data: { receiver_actor_id: number; body: string }) {
    const response = await this.client.post('/messages', data)
    return response.data
  }

  async listMarketplaceOffers(params?: {
    offer_type?: 'sell' | 'buy'
    filiere?: string
    commune_id?: number
    min_price?: number
    max_price?: number
    min_quantity?: number
    max_quantity?: number
    status?: 'active' | 'closed' | 'cancelled'
  }) {
    const response = await this.client.get('/marketplace/offers', { params })
    return response.data
  }

  async createMarketplaceOffer(data: {
    offer_type: 'sell' | 'buy'
    filiere: string
    lot_id?: number
    product_type: string
    quantity: number
    unit: string
    unit_price: number
    currency?: string
    location_commune_id?: number
    expires_at?: string
    notes?: string
  }) {
    const response = await this.client.post('/marketplace/offers', data)
    return response.data
  }

  async closeMarketplaceOffer(offerId: number) {
    const response = await this.client.post(`/marketplace/offers/${offerId}/close`)
    return response.data
  }

  async logout(refreshToken: string) {
    const response = await this.client.post('/auth/logout', { refresh_token: refreshToken })
    return response.data
  }

  async getHealth() {
    const response = await this.client.get('/health')
    return response.data
  }
  async getReady() {
    const response = await this.client.get('/ready')
    return response.data
  }

  async listAdminConfigs(params?: { key?: string }) {
    const response = await this.client.get('/admin/config', { params })
    return response.data
  }
  async getAdminConfig(configId: number) {
    const response = await this.client.get(`/admin/config/${configId}`)
    return response.data
  }
  async createAdminConfig(data: { key: string; value?: string; description?: string }) {
    const response = await this.client.post('/admin/config', data)
    return response.data
  }
  async patchAdminConfig(configId: number, data: { value?: string; description?: string }) {
    const response = await this.client.patch(`/admin/config/${configId}`, data)
    return response.data
  }
  async deleteAdminConfig(configId: number) {
    const response = await this.client.delete(`/admin/config/${configId}`)
    return response.data
  }
  async listAdminActorRoles(actorId: number) {
    const response = await this.client.get(`/admin/actors/${actorId}/roles`)
    return response.data
  }
  async assignAdminActorRole(actorId: number, data: { role: string; valid_from?: string; valid_to?: string }) {
    const response = await this.client.post(`/admin/actors/${actorId}/roles`, data)
    return response.data
  }
  async patchAdminRole(roleId: number, data: { status?: string; valid_from?: string; valid_to?: string }) {
    const response = await this.client.patch(`/admin/roles/${roleId}`, data)
    return response.data
  }
  async deleteAdminRole(roleId: number) {
    const response = await this.client.delete(`/admin/roles/${roleId}`)
    return response.data
  }

  async listPaymentProviders() {
    const response = await this.client.get('/payment-providers')
    return response.data
  }
  async createPaymentProvider(data: { code: string; name: string; enabled?: boolean; config_json?: string }) {
    const response = await this.client.post('/payment-providers', data)
    return response.data
  }
  async patchPaymentProvider(providerId: number, data: { name?: string; enabled?: boolean; config_json?: string }) {
    const response = await this.client.patch(`/payment-providers/${providerId}`, data)
    return response.data
  }

  async listPayments(params?: { payer_actor_id?: number; payee_actor_id?: number; status?: string }) {
    const response = await this.client.get('/payments', { params })
    return response.data
  }
  async initiatePayment(data: {
    provider_code: string
    payer_actor_id: number
    payee_actor_id: number
    fee_id?: number
    transaction_id?: number
    amount: number
    currency: string
    external_ref?: string
    idempotency_key?: string
  }) {
    const response = await this.client.post('/payments/initiate', data)
    return response.data
  }
  async getPayment(paymentId: number) {
    const response = await this.client.get(`/payments/${paymentId}`)
    return response.data
  }
  async getPaymentStatus(externalRef: string) {
    const response = await this.client.get(`/payments/status/${encodeURIComponent(externalRef)}`)
    return response.data
  }
  async sendPaymentWebhook(providerCode: string, data: { external_ref: string; status: string; operator_ref?: string }) {
    const response = await this.client.post(`/payments/webhooks/${providerCode}`, data)
    return response.data
  }

  async listTaxes(params?: { taxable_event_type?: string; taxable_event_id?: string; status?: string }) {
    const response = await this.client.get('/taxes', { params })
    return response.data
  }
  async listTaxEvents(params?: { taxable_event_type?: string; status?: string; lot_id?: number }) {
    const response = await this.client.get('/taxes/events', { params })
    return response.data
  }
  async getTaxEvent(eventId: number) {
    const response = await this.client.get(`/taxes/events/${eventId}`)
    return response.data
  }
  async listLocalMarketValues(params?: { filiere?: string; substance?: string; status?: string }) {
    const response = await this.client.get('/taxes/local-market-values', { params })
    return response.data
  }
  async createLocalMarketValue(data: {
    filiere?: string
    substance: string
    region_code?: string
    commune_code?: string
    unit: string
    value_per_unit: number
    currency?: string
    legal_reference: string
    version_tag: string
    effective_from: string
    effective_to?: string
    status?: 'active' | 'inactive'
  }) {
    const response = await this.client.post('/taxes/local-market-values', data)
    return response.data
  }
  async createTaxEvent(data: {
    taxable_event_type: string
    taxable_event_id: string
    base_amount?: number
    currency?: string
    filiere?: string
    region_code?: string
    assiette_mode?: 'manual' | 'fob_export' | 'local_market_value' | 'fixed_amount'
    period_key?: string
    reference_transaction?: string
    substance?: string
    quantity?: number
    unit?: string
    local_market_value_id?: number
    local_market_value_override?: number
    lot_id?: number
    export_id?: number
    transaction_id?: number
    payer_actor_id?: number
    payer_role_code?: string
    transformed?: boolean
    transformation_origin?: 'national_refinery' | 'other'
    unpaid_upstream_dtspm?: boolean
    legal_key?: string
    commune_beneficiary_id?: number
    region_beneficiary_id?: number
    province_beneficiary_id?: number
  }) {
    const response = await this.client.post('/taxes/events', data)
    return response.data
  }
  async patchTaxStatus(taxId: number, data: { status: 'DUE' | 'PAID' | 'VOID'; payment_request_id?: number }) {
    const response = await this.client.patch(`/taxes/${taxId}/status`, data)
    return response.data
  }

  async importTerritoryVersion(versionTag: string, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post(`/territories/import?version_tag=${encodeURIComponent(versionTag)}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }
  async getTerritoryVersions() {
    const response = await this.client.get('/territories/versions')
    return response.data
  }
  async getTerritoryVersion(versionTag: string) {
    const response = await this.client.get(`/territories/versions/${encodeURIComponent(versionTag)}`)
    return response.data
  }

  async createOrProductionLog(data: {
    card_id: number
    log_date: string
    zone_name: string
    quantity_gram: number
    notes?: string
  }) {
    const response = await this.client.post('/or-compliance/kara-production-logs', data)
    return response.data
  }
  async submitCollectorSemiAnnualReport(cardId: number, data: { period_label: string; report_payload_json: string }) {
    const response = await this.client.post(
      `/or-compliance/collector-cards/${cardId}/semiannual-reports?period_label=${encodeURIComponent(data.period_label)}&report_payload_json=${encodeURIComponent(data.report_payload_json)}`
    )
    return response.data
  }

  async createOrLegalVersion(data: {
    filiere?: string
    legal_key?: string
    version_tag: string
    effective_from: string
    effective_to?: string
    payload_json: string
    status?: string
  }) {
    const response = await this.client.post('/or/legal-versions', data)
    return response.data
  }
  async getActiveOrLegalVersion(params?: { filiere?: string; legal_key?: string }) {
    const response = await this.client.get('/or/legal-versions/active', { params })
    return response.data
  }
  async createOrTestCertificate(data: { lot_id: number; gross_weight: number; purity: number }) {
    const response = await this.client.post('/or/test-certificates', data)
    return response.data
  }
  async createOrTransportEvent(data: {
    lot_id: number
    transporter_actor_id: number
    depart_actor_id: number
    arrival_actor_id: number
    depart_geo_point_id: number
    laissez_passer_document_id?: number
  }) {
    const response = await this.client.post('/or/transport-events', data)
    return response.data
  }
  async patchOrTransportArrival(eventId: number, data: { arrival_geo_point_id: number; status?: string }) {
    const response = await this.client.patch(`/or/transport-events/${eventId}/arrival`, data)
    return response.data
  }
  async createOrTransformationFacility(data: {
    facility_type: string
    operator_actor_id: number
    autorisation_ref: string
    valid_from: string
    valid_to: string
    capacity_declared?: number
    status?: string
  }) {
    const response = await this.client.post('/or/transformation-facilities', data)
    return response.data
  }
  async createOrTransformationEvent(data: {
    lot_input_id: number
    facility_id: number
    quantity_input: number
    quantity_output: number
    perte_declared: number
    justificatif?: string
    output_product_type: string
    output_unit: string
  }) {
    const response = await this.client.post('/or/transformation-events', data)
    return response.data
  }
  async createOrExportValidation(data: { export_id: number; validator_role: string; decision: string; notes?: string }) {
    const response = await this.client.post('/or/export-validations', data)
    return response.data
  }
  async createOrForexRepatriation(data: {
    export_id: number
    amount: number
    currency?: string
    proof_document_id?: number
    status?: string
  }) {
    const response = await this.client.post('/or/forex-repatriations', data)
    return response.data
  }
}

export type RbacFiliereOut = { code: string; label: string }
export type RbacRoleOut = {
  code: string
  label: string
  description: string
  category: string
  actor_type: 'USAGER' | 'AGENT_ETAT' | 'OPERATEUR_PRIVE' | 'TRANSVERSAL'
  filiere_scope: string[]
  tags: string[]
  is_active: boolean
  display_order: number
}

export const api = new ApiClient()
