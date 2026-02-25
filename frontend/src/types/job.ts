// Job module TypeScript types — mirrors backend schemas/job.py

export type JobStatus = "draft" | "active" | "paused" | "closed";
export type JobType =
  | "full_time"
  | "part_time"
  | "contract"
  | "internship"
  | "remote";
export type QuestionType = "text" | "yes_no" | "multiple_choice" | "rating";

// ── Skills ──────────────────────────────────────────────────────────────────

export interface JobSkill {
  id: string;
  skill_name: string;
  is_required: boolean;
}

export interface JobSkillCreate {
  skill_name: string;
  is_required?: boolean;
}

// ── Questions ───────────────────────────────────────────────────────────────

export interface JobQuestion {
  id: string;
  question_text: string;
  question_type: QuestionType;
  options: string[] | null;
  is_required: boolean;
  display_order: number;
}

export interface JobQuestionCreate {
  question_text: string;
  question_type?: QuestionType;
  options?: string[] | null;
  is_required?: boolean;
  display_order?: number;
}

export interface JobQuestionUpdate {
  question_text?: string;
  question_type?: QuestionType;
  options?: string[] | null;
  is_required?: boolean;
  display_order?: number;
}

// ── Pipeline ─────────────────────────────────────────────────────────────────

export interface PipelineStage {
  id: string;
  stage_name: string;
  stage_order: number;
  color: string;
  is_default: boolean;
}

export interface PipelineStageCreate {
  stage_name: string;
  color?: string;
}

export interface PipelineStageUpdate {
  stage_name?: string;
  color?: string;
}

export interface PipelineStageReorderItem {
  id: string;
  stage_order: number;
}

// ── Job CRUD ─────────────────────────────────────────────────────────────────

export interface JobCreate {
  title: string;
  description?: string;
  requirements?: string;
  location?: string;
  job_type?: JobType;
  department?: string;
  salary_min?: number;
  salary_max?: number;
  currency?: string;
  experience_years_min?: number;
  experience_years_max?: number;
  deadline?: string; // ISO datetime string
}

export interface JobUpdate extends Partial<JobCreate> {}

export interface Job {
  id: string;
  title: string;
  description: string | null;
  requirements: string | null;
  location: string | null;
  job_type: JobType;
  department: string | null;
  salary_min: number | null;
  salary_max: number | null;
  currency: string;
  experience_years_min: number | null;
  experience_years_max: number | null;
  status: JobStatus;
  posted_by: string | null;
  company_id: string | null;
  published_at: string | null;
  closed_at: string | null;
  archived_at: string | null;
  deadline: string | null;
  views_count: number;
  applications_count: number;
  created_at: string;
  updated_at: string;
  skills: JobSkill[];
  questions: JobQuestion[];
  pipeline_stages: PipelineStage[];
}

export interface JobListItem {
  id: string;
  title: string;
  location: string | null;
  job_type: JobType;
  department: string | null;
  status: JobStatus;
  views_count: number;
  applications_count: number;
  created_at: string;
  published_at: string | null;
  deadline: string | null;
  skills: JobSkill[];
}

export interface JobListResponse {
  items: JobListItem[];
  total: number;
  page: number;
  page_size: number;
}

// ── Analytics ────────────────────────────────────────────────────────────────

export interface JobCountByStatus {
  draft: number;
  active: number;
  paused: number;
  closed: number;
}

export interface JobCountByType {
  full_time: number;
  part_time: number;
  contract: number;
  internship: number;
  remote: number;
}

export interface AnalyticsSummary {
  total_jobs: number;
  active_jobs: number;
  total_applications: number;
  total_views: number;
  by_status: JobCountByStatus;
  by_type: JobCountByType;
  top_jobs: JobListItem[];
}

// ── UI helpers ───────────────────────────────────────────────────────────────

export const JOB_TYPE_LABELS: Record<JobType, string> = {
  full_time: "Full Time",
  part_time: "Part Time",
  contract: "Contract",
  internship: "Internship",
  remote: "Remote",
};

export const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  draft: "Draft",
  active: "Active",
  paused: "Paused",
  closed: "Closed",
};

export const JOB_STATUS_COLORS: Record<JobStatus, string> = {
  draft: "bg-gray-100 text-gray-700",
  active: "bg-green-100 text-green-700",
  paused: "bg-yellow-100 text-yellow-700",
  closed: "bg-red-100 text-red-700",
};
