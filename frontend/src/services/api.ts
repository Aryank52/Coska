import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Incidents
export const getIncidents = () => api.get('/incidents').then(r => r.data)
export const getIncident = (id: string) => api.get(`/incidents/${id}`).then(r => r.data)
export const createIncident = (data: any) => api.post('/incidents', data).then(r => r.data)
export const investigateIncident = (id: string, autoApprove = false) => 
  api.post(`/incidents/${id}/investigate`, { auto_approve: autoApprove }).then(r => r.data)
export const getIncidentTimeline = (id: string) => api.get(`/incidents/${id}/timeline`).then(r => r.data)
export const getIncidentEvidence = (id: string) => api.get(`/incidents/${id}/evidence`).then(r => r.data)
export const getIncidentHypotheses = (id: string) => api.get(`/incidents/${id}/hypotheses`).then(r => r.data)
export const getIncidentRootCause = (id: string) => api.get(`/incidents/${id}/root-cause`).then(r => r.data)
export const getIncidentRemediation = (id: string) => api.get(`/incidents/${id}/remediation`).then(r => r.data)
export const getIncidentActions = (id: string) => api.get(`/incidents/${id}/actions`).then(r => r.data)
export const applyFix = (id: string) => api.post(`/incidents/${id}/apply-fix`).then(r => r.data)
export const verifyIncident = (id: string) => api.post(`/incidents/${id}/verify`).then(r => r.data)
export const getVerificationReport = (id: string) => api.get(`/incidents/${id}/report`).then(r => r.data)

// Health
export const healthCheck = () => api.get('/health').then(r => r.data)
export const aiHealthCheck = () => api.get('/health/ai').then(r => r.data)
export const tavilyHealthCheck = () => api.get('/health/tavily').then(r => r.data)
export const sandboxHealthCheck = () => api.get('/health/sandbox').then(r => r.data)