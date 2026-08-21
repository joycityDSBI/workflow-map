import axios from 'axios'
import { getToken } from './auth'
import { GraphData } from '@/types'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
})

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('wfmap_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

export const authApi = {
  login: (username: string, password: string) =>
    api.post('/api/v1/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  me: () => api.get('/api/v1/auth/me'),
}

export const graphApi = {
  getGraph: () => api.get<GraphData>('/api/v1/graph'),
}

export const objectsApi = {
  list: (status?: string) => api.get('/api/v1/objects', { params: status ? { status } : {} }),
  approve: (id: string) => api.post(`/api/v1/review/${id}/approve`),
  reject: (id: string, reason: string) => api.post(`/api/v1/review/${id}/reject`, { reason }),
}
