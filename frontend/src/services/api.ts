import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

if (!import.meta.env.VITE_API_BASE_URL && import.meta.env.PROD) {
  console.error('[COSKA] VITE_API_BASE_URL is not set in production. Please configure VITE_API_BASE_URL environment variable.')
}

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

export const getApiBaseUrl = () => API_BASE_URL

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

// Demo, Judge Mode & RAG
export const getDemoScenarios = () => api.get('/demo/scenarios').then(r => r.data)
export const runDemoScenario = (scenarioId: string, autoApprove = true) => 
  api.post('/demo/run', { scenario_id: scenarioId, auto_approve: autoApprove }).then(r => r.data)
export const searchRAG = (query: string) => api.get(`/rag/search?q=${encodeURIComponent(query)}`).then(r => r.data)
export const getIncidentGraph = (id: string) => api.get(`/incidents/${id}/graph`).then(r => r.data)
export const getInvestigationState = (id: string) => api.get(`/incidents/${id}/state`).then(r => r.data)

// Enhanced API
export const getIncidentIntelligence = (id: string, useAI = false) => 
  api.get(`/incidents/${id}/intelligence`, { params: { use_ai: useAI } }).then(r => r.data)

export const searchKnowledgeBase = (data: { query: string; top_k?: number; include_trace?: boolean }) => 
  api.post('/rag/search', data).then(r => r.data)

export const listKnowledgeDocuments = () => api.get('/rag/documents').then(r => r.data)
export const getKnowledgeDocument = (id: string) => api.get(`/rag/documents/${id}`).then(r => r.data)
export const listKnowledgeCategories = () => api.get('/rag/categories').then(r => r.data)

export const getEvidenceGraph = (id: string) => api.get(`/incidents/${id}/evidence-graph`).then(r => r.data)

export const getServiceMap = () => api.get('/service-map').then(r => r.data)
export const getServiceStatusOverview = () => api.get('/service-map/status').then(r => r.data)
export const getBlastRadius = (serviceId: string) => api.get(`/service-map/blast-radius/${serviceId}`).then(r => r.data)
export const updateServiceStatus = (serviceId: string, status: string) => 
  api.post(`/service-map/status/${serviceId}`, { status }).then(r => r.data)

export const createInvestigationPlan = (data: { incident_id: string; auto_execute?: boolean }) => 
  api.post('/planner/plan', data).then(r => r.data)
export const executeInvestigationPlan = (data: { incident_id: string; auto_execute?: boolean }) => 
  api.post('/planner/execute', data).then(r => r.data)

export const getHypothesisDecisions = (incidentId: string, hypothesisId: string) => 
  api.get(`/incidents/${incidentId}/hypotheses/${hypothesisId}/decisions`).then(r => r.data)

export const getVerificationReceipt = (id: string) => api.get(`/incidents/${id}/verification-receipt`).then(r => r.data)
export const getIncidentReport = (id: string, format: 'json' | 'markdown' = 'json') => 
  api.get(`/incidents/${id}/report`, { params: { format } }).then(r => r.data)

export const getDemoScenario = (scenarioId: string) => api.get(`/demo/scenarios/${scenarioId}`).then(r => r.data)
export const runDemoScenarioById = (scenarioId: string, autoApprove = false) => 
  api.post(`/demo/scenarios/${scenarioId}/run`, { auto_approve: autoApprove }).then(r => r.data)
export const resetDemoData = () => api.post('/demo/reset').then(r => r.data)