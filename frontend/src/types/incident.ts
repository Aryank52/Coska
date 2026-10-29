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