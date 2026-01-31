import axios from 'axios'
import { mockIncidentService } from './mockApi'

// Check if we should use mock data
// Supports: VITE_USE_MOCK env var, VITE_FE_ONLY env var, or 'mock' mode
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true' || 
                 import.meta.env.VITE_FE_ONLY === 'true' ||
                 import.meta.env.MODE === 'mock'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Real API service
const realIncidentService = {
  async create(incidentData) {
    const response = await api.post('/api/incidents', incidentData)
    return response.data
  },

  async getAll(params = {}) {
    const response = await api.get('/api/incidents', { params })
    return response.data
  },

  async getById(id) {
    const response = await api.get(`/api/incidents/${id}`)
    return response.data
  },

  async update(id, updateData) {
    const response = await api.patch(`/api/incidents/${id}`, updateData)
    return response.data
  },
}

// Export the appropriate service based on environment
export const incidentService = USE_MOCK ? mockIncidentService : realIncidentService

// Log which mode we're using
if (USE_MOCK) {
  console.log('🔧 Using MOCK API service (frontend-only mode)')
  console.log('   Run with backend: npm run dev')
  console.log('   Run mock mode: npm run dev:mock')
} else {
  console.log('🌐 Using REAL API service')
  console.log('   Make sure backend is running on http://localhost:8000')
}

export default api
