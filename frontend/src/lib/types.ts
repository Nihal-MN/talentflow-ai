/**
 * API types — mirrors the backend Pydantic schemas (backend/app/schemas/).
 * Kept hand-written and small on purpose: one file to audit, no codegen step.
 */

// ── Errors & health ─────────────────────────────────────────────────────────

export interface ErrorBody {
  code: string;
  message: string;
  detail?: unknown;
}

export interface ErrorResponse {
  error: ErrorBody;
}

export interface Counts {
  candidates: number;
  jobs: number;
  open_jobs: number;
  applications: number;
}

export interface Health {
  status: "ok" | "degraded";
  app: string;
  version: string;
  time: string;
  database: {
    status: "ok" | "error";
    dialect: string;
    latency_ms: number | null;
    detail: string | null;
  };
  ai: {
    mode: "auto" | "openai" | "mock";
    provider: string;
    model: string;
    embedding_model: string;
    api_key_configured: boolean;
    misconfigured: boolean;
  };
  counts: Counts;
}

// ── Jobs ────────────────────────────────────────────────────────────────────

export interface JobBrief {
  id: number;
  title: string;
  company: string;
  location: string | null;
  status: string;
  seniority: string | null;
  employment_type: string;
  domain: string | null;
}

export interface Requirement {
  id: number;
  kind: "must_have" | "preferred";
  category: string;
  label: string;
  normalized_skill: string | null;
  min_years: number | null;
  keywords: string[];
  order_index: number;
}

export interface JobListItem {
  id: number;
  title: string;
  company: string;
  location: string | null;
  status: string;
  seniority: string | null;
  employment_type: string;
  domain: string | null;
  extraction_method: string;
  created_at: string;
  must_have_count: number;
  preferred_count: number;
  applications_count: number;
}

export interface JobApplicationBrief {
  id: number;
  candidate_id: number;
  candidate_name: string;
  candidate_headline: string | null;
  stage: string;
  updated_at: string;
}

export interface JobDetail extends JobListItem {
  source: string;
  extraction_model: string | null;
  description_text: string;
  requirements: Requirement[];
  applications: JobApplicationBrief[];
}

// ── Candidates ──────────────────────────────────────────────────────────────

export interface Experience {
  id: number;
  company: string | null;
  title: string | null;
  location: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  description: string | null;
}

export interface Education {
  id: number;
  institution: string | null;
  degree: string | null;
  field_of_study: string | null;
  start_year: number | null;
  end_year: number | null;
}

export interface Skill {
  id: number;
  name: string;
  normalized_name: string;
  category: string;
  evidence: string | null;
}

export interface Certification {
  id: number;
  name: string;
  issuer: string | null;
  year: number | null;
}

export interface CandidateBrief {
  id: number;
  full_name: string;
  headline: string | null;
  location: string | null;
  years_experience: number | null;
}

export interface ApplicationBrief {
  id: number;
  job_id: number;
  job_title: string;
  stage: Stage;
  updated_at: string;
}

export interface CandidateListItem {
  id: number;
  full_name: string;
  headline: string | null;
  location: string | null;
  years_experience: number | null;
  extraction_method: string;
  created_at: string;
  skills: string[];
  applications_count: number;
}

export interface CandidateDetail extends CandidateBrief {
  email: string | null;
  phone: string | null;
  summary: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  website_url: string | null;
  resume_filename: string | null;
  resume_text: string | null;
  extraction_method: string;
  extraction_model: string | null;
  created_at: string;
  experiences: Experience[];
  educations: Education[];
  skills: Skill[];
  certifications: Certification[];
  applications: ApplicationBrief[];
  notes: Note[];
  tags: Tag[];
}

export interface Note {
  id: number;
  candidate_id: number;
  job_id: number | null;
  author: string;
  body: string;
  created_at: string;
}

export interface Tag {
  id: number;
  name: string;
  color: string;
}

export interface TagUsage extends Tag {
  usage_count: number;
}

// ── Pipeline ────────────────────────────────────────────────────────────────

export type Stage =
  | "NEW"
  | "SCREENING"
  | "SHORTLISTED"
  | "INTERVIEW"
  | "OFFER"
  | "HIRED"
  | "REJECTED";

export interface StageEvent {
  id: number;
  from_stage: string | null;
  to_stage: string;
  note: string | null;
  created_at: string;
}

export interface Application {
  id: number;
  candidate_id: number;
  job_id: number;
  stage: Stage;
  created_at: string;
  updated_at: string;
  candidate: CandidateBrief;
  job: JobBrief;
  screening_questions_count: number;
  stage_events: StageEvent[];
}

export interface Activity {
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  job_id: number;
  job_title: string;
  from_stage: string | null;
  to_stage: string;
  note: string | null;
  at: string;
}

// ── Matching ────────────────────────────────────────────────────────────────

export interface Evidence {
  snippet: string;
  source: string;
  match_type: "lexical" | "computed" | "semantic";
  detail: string | null;
}

export type RequirementStatus = "met" | "partial" | "missing" | "unknown" | "advisory";

export interface RequirementEvaluation {
  requirement_id: number;
  kind: "must_have" | "preferred";
  category: string;
  label: string;
  status: RequirementStatus;
  reason: string;
  skill: string | null;
  similarity: number | null;
  evidence: Evidence[];
}

export interface CoverageCounts {
  met: number;
  partial: number;
  missing: number;
  unknown: number;
  advisory: number;
  total: number;
}

export interface MatchResult {
  candidate_id: number;
  candidate_name: string;
  job_id: number;
  job_title: string;
  application_id: number | null;
  stage: string | null;
  composite_score: number | null;
  components: Record<string, number | null>;
  weights_used: Record<string, number>;
  formula: string;
  coverage: { must_have: CoverageCounts; preferred: CoverageCounts };
  semantic_similarity: number | null;
  engine_version: string;
  generated_at: string;
  requirements: RequirementEvaluation[];
}

// ── Screening ───────────────────────────────────────────────────────────────

export interface ScreeningQuestion {
  id: number;
  application_id: number;
  category: "technical" | "experience" | "gap_probe" | "behavioral" | string;
  question: string;
  rationale: string | null;
  source: string;
  order_index: number;
  created_at: string;
}

export interface ScreeningListItem {
  application_id: number;
  candidate_id: number;
  candidate_name: string;
  job_id: number;
  job_title: string;
  stage: Stage;
  source: string;
  question_count: number;
  created_at: string | null;
}
