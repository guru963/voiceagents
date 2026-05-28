import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// Attach auth token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Global error handling
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const agentApi = {
  list: () => api.get('/agents/'),
  get: (id: string) => api.get(`/agents/${id}`),
  create: (data: any) => api.post('/agents/', data),
  delete: (id: string) => api.delete(`/agents/${id}`),
  uploadKB: (id: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/agents/${id}/knowledge`, form)
  },
}

export const tokenApi = {
  create: (agentId: string, userName: string) =>
    api.post('/tokens/', { agent_id: agentId, user_name: userName }),
}

export const callApi = {
  list: (agentId?: string) =>
    api.get('/calls/', { params: agentId ? { agent_id: agentId } : {} }),
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
}

export const appointmentApi = {
  list: (month?: string) =>
    api.get('/appointments/', { params: month ? { month } : {} }),
  create: (data: any) => api.post('/appointments/', data),
  delete: (id: string) => api.delete(`/appointments/${id}`),
  updateStatus: (id: string, status: string) =>
    api.patch(`/appointments/${id}`, { status }),
}

export default api
