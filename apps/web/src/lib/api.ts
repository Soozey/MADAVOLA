import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

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

    // Intercepteur pour gérer les erreurs 401
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
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

  async getActors(params?: { role?: string; commune_code?: string; page?: number; page_size?: number }) {
    const response = await this.client.get('/actors', { params })
    return response.data
  }

  async createActor(data: any) {
    const response = await this.client.post('/actors', data)
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

  async getTerritories() {
    const regions = await this.client.get('/territories/regions')
    return regions.data
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
}

export const api = new ApiClient()
