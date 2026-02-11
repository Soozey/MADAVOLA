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

  async refreshToken(refreshToken: string) {
    const response = await this.client.post('/auth/refresh', { refresh_token: refreshToken })
    return response.data
  }

  async getActors(params?: { role?: string; commune_code?: string; status?: string; page?: number; page_size?: number }) {
    const response = await this.client.get('/actors', { params })
    return response.data
  }

  async createActor(data: any) {
    const response = await this.client.post('/actors', data)
    return response.data
  }

  async updateActorStatus(actorId: number, status: 'active' | 'rejected') {
    const response = await this.client.patch(`/actors/${actorId}/status`, { status })
    return response.data
  }

  async getActor(actorId: number) {
    const response = await this.client.get(`/actors/${actorId}`)
    return response.data
  }

  async getLots(params?: { owner_actor_id?: number; status?: string; page?: number; page_size?: number }) {
    const response = await this.client.get('/lots', { params })
    return response.data
  }

  async createLot(data: any) {
    const response = await this.client.post('/lots', data)
    return response.data
  }

  async getLot(lotId: number) {
    const response = await this.client.get(`/lots/${lotId}`)
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

  async createTransaction(data: any) {
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

  // Exports (dossiers export)
  async getExports(params?: { status?: string; date_from?: string; date_to?: string; created_by_actor_id?: number }) {
    const response = await this.client.get('/exports', { params })
    return response.data
  }

  async createExport(data: { destination?: string; total_weight?: number }) {
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

  async linkLotsToExport(exportId: number, lots: { lot_id: number; quantity_in_export: number }[]) {
    const response = await this.client.post(`/exports/${exportId}/lots`, lots)
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

  async createPenalty(data: { violation_case_id: number; penalty_type: string; amount?: number }) {
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

  async getRegions() {
    const response = await this.client.get('/territories/regions')
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

  async getAuditLogs(params?: { actor_id?: number; entity_type?: string }) {
    const response = await this.client.get('/audit', { params })
    return response.data
  }

  async getInspections(params?: { page?: number; page_size?: number }) {
    const response = await this.client.get('/inspections', { params })
    return response.data
  }

  /** Vérification publique (sans auth) pour scan QR par contrôleur */
  async getVerifyActor(actorId: number) {
    const response = await this.client.get(`/verify/actor/${actorId}`)
    return response.data
  }
}

export const api = new ApiClient()
