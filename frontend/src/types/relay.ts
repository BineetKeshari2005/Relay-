/**
 * Strongly-typed domain models for Relay Technician Interface.
 * Mirrors backend Pydantic models from:
 * - app/reasoning/models.py
 * - app/reasoning/validator.py
 * - app/context/assembled_context.py
 */

export type SupportLevel = "direct" | "inferred" | "insufficient";

export type CertaintyLevel =
  | "supported"
  | "partially_supported"
  | "insufficient_evidence"
  | "conflicting_evidence";

export type ReasoningStatus =
  | "completed"
  | "insufficient_evidence"
  | "needs_information"
  | "conflicting_evidence"
  | "safety_escalation";

export type ProvenanceType =
  | "VERIFIED_COMPANY_DOCUMENT"
  | "MANUFACTURER_DOCUMENT"
  | "HISTORICAL_SERVICE_RECORD"
  | "TECHNICIAN_CONTRIBUTION"
  | "UNVERIFIED"
  | "CONFLICTING";

export type VerificationStatus =
  | "VERIFIED"
  | "PENDING_REVIEW"
  | "REJECTED"
  | "DEPRECATED";

export interface EvidenceClaim {
  claim: string;
  evidence_ids: string[];
  support_level: SupportLevel;
  explanation?: string | null;
}

export interface ReasoningCitation {
  evidence_id: string;
  source: string;
  document_type: string;
  relevant_excerpt: string;
  score?: number | null;
  metadata: Record<string, any>;
  provenance_type?: ProvenanceType | string;
  verification_status?: VerificationStatus | string;
}

export interface RecommendedNextStep {
  step: string;
  evidence_ids: string[];
  rationale: string;
  expected_observation?: string | null;
  safety_constraints: string[];
}

export interface DecisionBranch {
  condition: string;
  if_true_branch: string;
  if_false_branch?: string | null;
  evidence_ids: string[];
  rationale?: string | null;
}

export interface EscalationAssessment {
  should_escalate: boolean;
  reason?: string | null;
  missing_information: string[];
  safety_reason?: string | null;
  recommended_escalation_target?: string | null;
}

export interface ReasoningMetadata {
  provider: string;
  latency_ms: number;
  retrieval_latency_ms: number;
  model_name?: string | null;
  token_usage: Record<string, any>;
}

export interface ReasoningResult {
  status: ReasoningStatus;
  issue_summary: string;
  what_we_know: string[];
  assessment: string;
  evidence_claims: EvidenceClaim[];
  recommended_next_steps: RecommendedNextStep[];
  safety_considerations: string[];
  expected_observations: string[];
  decision_branches: DecisionBranch[];
  clarifying_questions: string[];
  certainty_level: CertaintyLevel;
  uncertainty: Record<string, any>;
  escalation: EscalationAssessment;
  citations: ReasoningCitation[];
  reasoning_metadata: ReasoningMetadata;
  spoken_response?: string | null;
}

export interface ReasoningValidationReport {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}

export interface EvidenceItem {
  document_id: string;
  source: string;
  document_type: string;
  classification: string;
  text: string;
  score?: number | null;
  metadata: Record<string, any>;
  safety_level?: string | null;
  version?: string | null;
  date?: string | null;
  applicability: Record<string, any>;
  provenance_type?: ProvenanceType | string;
  verification_status?: VerificationStatus | string;
  is_technician_contribution?: boolean;
}

export interface RetrievalMetadata {
  provider: string;
  status: string;
  latency_ms: number;
  result_count: number;
  query: string;
}

export interface UncertaintyModel {
  missing_asset: boolean;
  missing_error_code: boolean;
  missing_measurement: boolean;
  insufficient_evidence: boolean;
  conflicting_evidence: boolean;
  ambiguous_query: boolean;
  stale_history: boolean;
  unresolved_asset_reference?: string | null;
  unverified_safety_threshold: boolean;
}

export interface DetectedConflict {
  conflict_type: string;
  sources: string[];
  description: string;
}

export interface SafetyWarningItem {
  warning: string;
  provenance_type: "VERIFIED_FROM_KNOWLEDGE" | "DEMO_RULE";
  source_document_id?: string | null;
  source_reference?: string | null;
  threshold_applied?: string | null;
}

export interface SafetyContext {
  safety_level: string;
  safety_documents: string[];
  safety_warnings: string[];
  warning_items: SafetyWarningItem[];
  threshold_sources: Record<string, string>;
  safety_evidence_ids: string[];
  mandatory_loto: boolean;
  high_pressure_hazard: boolean;
}

export interface ExtractedQueryFacts {
  raw_query: string;
  asset_reference?: string | null;
  asset_model?: string | null;
  error_code?: string | null;
  measurements: Record<string, any>;
  is_repeat_issue: boolean;
  observations: string[];
}

export interface AssembledContext {
  session_id?: string | null;
  technician_query: string;
  query_facts: ExtractedQueryFacts;
  asset?: any | null;
  asset_id?: string | null;
  asset_model?: string | null;
  error_code?: string | null;
  measurements: Record<string, any>;
  measurement_provenance: Record<string, string>;
  observations: string[];
  relevant_service_history: any[];
  conversation_context: any[];
  evidence: EvidenceItem[];
  safety_context: SafetyContext;
  uncertainty: UncertaintyModel;
  missing_information: string[];
  conflicts: DetectedConflict[];
  retrieval_metadata: RetrievalMetadata;
}

export interface AnalyzeRequest {
  query: string;
  session_id?: string;
  asset_id?: string;
  top_k?: number;
}

export interface AnalyzeResponse {
  context: AssembledContext;
  reasoning: ReasoningResult;
  validation_report: ReasoningValidationReport;
  client_latency_ms?: number;
}

export interface ConversationTurnUI {
  id: string;
  timestamp: string;
  query: string;
  response: AnalyzeResponse;
  client_latency_ms: number;
  is_voice?: boolean;
  voice_latency_ms?: number;
}

export interface TechnicianContribution {
  id?: string;
  contribution_id?: string;
  contributor_id?: string;
  technician_id?: string;
  contributor_name?: string | null;
  asset_id?: string | null;
  session_id?: string | null;
  error_code?: string | null;
  title: string;
  observation?: string;
  observed_symptom: string;
  discovered_cause: string;
  action_taken: string;
  outcome?: string | null;
  provenance_type: ProvenanceType;
  verification_status: VerificationStatus;
  status_note?: string | null;
  created_at: string;
  tags: string[];
}

export interface ContributionCreateRequest {
  title: string;
  observation?: string;
  symptom?: string;
  observed_symptom?: string;
  suspected_cause?: string;
  discovered_cause?: string;
  action_taken: string;
  outcome?: string;
  technician_id?: string;
  contributor_id?: string;
  contributor_name?: string;
  asset_id?: string;
  session_id?: string;
  error_code?: string;
  tags?: string[];
}

export interface EquipmentAsset {
  asset_id: string;
  model: string;
  serial_number?: string;
  manufacturer?: string;
  installation_date?: string;
  location?: string;
  status: string;
  specifications?: Record<string, any>;
  operating_parameters?: Record<string, any>;
  last_service_date?: string;
  current_observations?: string[];
}

export interface ServiceRecordItem {
  record_id: string;
  asset_id: string;
  date: string;
  technician_id?: string;
  error_code?: string;
  description: string;
  action_taken: string;
  parts_replaced?: string[];
}

export interface ConversationTurnItem {
  turn_number: number;
  speaker: string;
  utterance: string;
  timestamp: string;
  referenced_evidence?: string[];
}

export interface SessionDetailResponse {
  session: {
    session_id: string;
    asset_id: string;
    technician_id: string;
    start_time: string;
    status: string;
    current_issue?: string;
    active_error_code?: string;
    measurements?: Record<string, any>;
    notes?: string[];
  };
  asset: EquipmentAsset;
  service_history: ServiceRecordItem[];
  recent_turns: ConversationTurnItem[];
}

export interface SearchRequestParams {
  query: string;
  asset_id?: string;
  asset_model?: string;
  error_code?: string;
  document_type?: string;
  top_k?: number;
  alpha?: number;
}

export interface SearchResultItemModel {
  id: string;
  text: string;
  score?: number | null;
  metadata: Record<string, any>;
}

export interface SearchAPIResponseModel {
  provider: string;
  status: string;
  query: string;
  results: SearchResultItemModel[];
  latency_ms: number;
  result_count: number;
}

export interface RetrievalHealthResponseModel {
  provider: string;
  status: string;
  index: string;
  configured: boolean;
  default_alpha: number;
  error?: string | null;
}

