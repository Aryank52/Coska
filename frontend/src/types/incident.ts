export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type IncidentStatus = 
  | 'RECEIVED'
  | 'TRIAGING'
  | 'COLLECTING_EVIDENCE'
  | 'BUILDING_TIMELINE'
  | 'GENERATING_HYPOTHESES'
  | 'INVESTIGATING'
  | 'RESEARCHING'
  | 'ROOT_CAUSE_IDENTIFIED'
  | 'REMEDIATION_PROPOSED'
  | 'AWAITING_APPROVAL'
  | 'APPLYING_FIX'
  | 'VERIFYING'
  | 'RESOLVED'
  | 'INSUFFICIENT_EVIDENCE'
  | 'INVESTIGATION_BLOCKED'
  | 'REMEDIATION_FAILED'
  | 'VERIFICATION_FAILED'

export type SourceType = 'LOG' | 'REPOSITORY' | 'CONFIG' | 'DEPLOYMENT' | 'RUNTIME' | 'WEB' | 'TEST'

export type HypothesisStatus = 'ACTIVE' | 'WEAKENED' | 'REJECTED' | 'SUPPORTED'

export type Verdict = 'VERIFIED' | 'FAILED' | 'UNVERIFIED' | 'INSUFFICIENT_EVIDENCE'

export type RemediationType = 
  | 'CONFIGURATION_CHANGE'
  | 'CODE_CHANGE'
  | 'DEPENDENCY_CHANGE'
  | 'SAFE_ROLLBACK'
  | 'FEATURE_FLAG_CHANGE'

export interface Incident {
  id: string
  service: string
  severity: Severity
  description: string
  logs?: string
  deployment?: string
  repository?: string
  metadata: Record<string, any>
  status: IncidentStatus
  created_at: string
  updated_at: string
}

export interface IncidentResponse extends Incident {}

export interface IncidentCreate {
  service: string
  severity: Severity
  description: string
  logs?: string
  deployment?: string
  repository?: string
  metadata?: Record<string, any>
}

export interface Evidence {
  id: string
  incident_id: string
  source_type: SourceType
  claim: string
  reference: string
  timestamp: string
  confidence: number
  related_component?: string
  raw_data?: Record<string, any>
}

export interface Hypothesis {
  id: string
  incident_id: string
  title: string
  description: string
  supporting_evidence_ids: string[]
  contradicting_evidence_ids: string[]
  confidence: number
  next_investigation_action?: string
  status: HypothesisStatus
  created_at: string
  updated_at: string
}

export interface Remediation {
  id: string
  incident_id: string
  hypothesis_id: string
  type: RemediationType
  description: string
  exact_change: string
  expected_effect: string
  risk: string
  blast_radius: string
  rollback_plan: string
  created_at: string
}

export interface VerificationResult {
  id: string
  incident_id: string
  remediation_id: string
  baseline_test: string
  post_fix_tests: string
  health_check: string
  control_test: string
  verdict: Verdict
  evidence_count: number
  model: string
  details: Record<string, any>
  created_at: string
}

export interface AgentAction {
  id: string
  incident_id: string
  step: string
  tool?: string
  timestamp: string
  duration_ms: number
  status: string
  summary: string
  input_data: Record<string, any>
  output_data: Record<string, any>
  error?: string
}

export interface TimelineEvent {
  timestamp: string
  event_type: string
  title: string
  description: string
  source_type: SourceType
  evidence_ids: string[]
  severity: string
}

export interface RootCause {
  root_cause: string
  confidence: number
  supporting_evidence_ids: string[]
  contradicting_evidence_ids: string[]
  rejected_hypotheses: Array<{ id: string; reason: string }>
  uncertainty: string | null
  recommended_remediation: {
    description: string
    exact_change: string
    expected_effect: string
    risk: string
    blast_radius: string
    rollback_plan: string
  }
}

export interface VerificationReport {
  incident_id: string
  remediation_id: string
  baseline_test: { success: boolean; stdout: string; stderr: string; exit_code: number }
  post_fix_tests: { success: boolean; stdout: string; stderr: string; exit_code: number }
  health_check: { success: boolean; stdout: string; stderr: string; exit_code: number }
  control_test: { success: boolean; stdout: string; stderr: string; exit_code: number }
  verdict: Verdict
  evidence_count: number
  model: string
  details: Record<string, any>
}

// Enhanced types
export interface IncidentIntelligence {
  service: string
  severity: Severity
  symptoms: string[]
  components: string[]
  environment: string
  error_types: string[]
  probable_causes: string[]
  timestamps: string[]
  configuration_values: Record<string, string>
  suspected_dependencies: string[]
  business_impact: string
  keywords: string[]
  technical_entities: string[]
  extraction_method: string
  metadata?: Record<string, any>
}

export interface RAGDocument {
  id: string
  title: string
  category: string
  source: string
  summary: string
  content: string
  tags: string[]
  relevance_score: number
  snippet: string
  matched_terms: string[]
  match_reason: string
}

export interface RAGSearchResult {
  documents: RAGDocument[]
  query: string
  query_tokens: string[]
  trace: Record<string, any>
}

export interface EvidenceGraphNode {
  id: string
  type: string
  label: string
  data: Record<string, any>
  position?: { x: number; y: number }
}

export interface EvidenceGraphEdge {
  id: string
  source: string
  target: string
  type: string
  weight: number
  label: string
  metadata: Record<string, any>
}

export interface EvidenceGraph {
  incident_id: string
  nodes: EvidenceGraphNode[]
  edges: EvidenceGraphEdge[]
  metadata: Record<string, any>
  layout: string
}

export interface ServiceNode {
  id: string
  name: string
  type: string
  status: 'healthy' | 'degraded' | 'critical' | 'unknown'
  metadata: Record<string, any>
  position?: { x: number; y: number }
}

export interface ServiceEdge {
  id: string
  source: string
  target: string
  type: 'critical' | 'degraded' | 'optional'
  protocol: string
  latency_ms?: number
  metadata: Record<string, any>
}

export interface ServiceMap {
  services: ServiceNode[]
  dependencies: ServiceEdge[]
  metadata: Record<string, any>
}

export interface BlastRadius {
  affected_service: string
  direct_dependencies: string[]
  transitive_dependencies: string[]
  impacted_services: Array<{
    service_id: string
    service_name: string
    impact_level: string
    dependency_type: string
    path: string
  }>
  severity: string
  error_increase_percent: number
  transaction_impact_percent: number
  estimated_recovery_time_seconds: number
  metadata: Record<string, any>
}

export interface DemoScenario {
  id: string
  name: string
  description: string
  category: string
  incident: Record<string, any>
  expected_root_cause: string
  expected_remediation: Record<string, any>
  expected_verification: Record<string, any>
  difficulty: string
  estimated_duration_seconds: number
  tags: string[]
}

export interface InvestigationPlan {
  incident_id: string
  goal: string
  steps: Array<{
    step_id: number
    type: string
    description: string
    tool_name?: string
    tool_input?: Record<string, any>
    rag_query?: string
    reasoning: string
    expected_outcome: string
    depends_on: number[]
    completed: boolean
    result?: Record<string, any>
    error?: string
  }>
  current_step_index: number
  created_at: string
  updated_at: string
  status: string
  total_budget: number
  tool_budget: number
  step_budget: number
  time_budget_seconds: number
  tools_used: number
  steps_executed: number
  rag_queries: number
  tavily_queries: number
}

export interface PlanResult {
  success: boolean
  completed_steps: number
  total_steps: number
  root_cause?: Record<string, any>
  remediation?: Record<string, any>
  verification?: Record<string, any>
  final_state: string
  trace: Record<string, any>[]
}

export interface HypothesisDecision {
  hypothesis_id: string
  decision_type: string
  confidence_before: number
  confidence_after: number
  evidence_considered: string[]
  reasoning: string
  alternative_considered?: string
  next_validation_step?: string
  timestamp: string
}

export interface VerificationReceipt {
  incident_id: string
  service: string
  timestamp: string
  root_cause: string | null
  root_cause_confidence: number | null
  remediation: Record<string, any> | null
  verification: Record<string, any> | null
  evidence_count: number
  hypotheses_count: number
  ai_provider: string
  knowledge_sources: any[]
  tavily_usage: string
  final_determination: string
}

export interface IncidentReport {
  executive_summary: {
    incident_id: string
    service: string
    severity: string
    status: string
    description: string
    created_at: string
    resolved_at: string | null
  }
  incident_timeline: any[]
  affected_services: string[]
  evidence: any[]
  competing_hypotheses: any[]
  root_cause: any
  remediation: any
  verification: any
  knowledge_sources: any[]
  external_research: any[]
  lessons_learned: string[]
  recommended_prevention: string[]
}