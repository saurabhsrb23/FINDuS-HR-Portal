// Search module TypeScript types — mirrors backend schemas/search.py

export type SortBy =
  | "relevance"
  | "experience"
  | "match_score"
  | "recently_active"
  | "profile_strength";

export type SkillMatchMode = "AND" | "OR";

export type EducationTier = "any" | "undergraduate" | "postgraduate" | "phd";

export type WorkPreference = "any" | "remote" | "onsite" | "hybrid";

// ── Filter request ────────────────────────────────────────────────────────────

export interface SkillFilter {
  skill: string;
  min_years?: number | null;
}

export interface SearchCandidateRequest {
  query?: string | null;
  skills?: SkillFilter[];
  skill_match?: SkillMatchMode;
  experience_min?: number | null;
  experience_max?: number | null;
  location?: string | null;
  notice_period_max_days?: number | null;
  ctc_min?: number | null;
  ctc_max?: number | null;
  education_tier?: EducationTier;
  profile_strength_min?: number | null;
  work_preference?: WorkPreference;
  last_active_days?: number | null;
  job_id?: string | null;
  match_score_min?: number | null;
  cursor?: string | null;
  page_size?: number;
  sort_by?: SortBy;
}

// ── Response types ────────────────────────────────────────────────────────────

export interface SkillResult {
  skill_name: string;
  proficiency: number;
  years_exp: number | null;
  matched: boolean;
}

export interface CandidateSearchItem {
  id: string;
  user_id: string;
  full_name: string | null;
  headline: string | null;
  location: string | null;
  years_of_experience: number | null;
  profile_strength: number;
  notice_period_days: number | null;
  desired_salary_min: number | null;
  desired_salary_max: number | null;
  open_to_remote: boolean;
  skills: SkillResult[];
  education_summary: string | null;
  last_active: string | null;
  match_score: number | null;
  ai_summary_snippet: string | null;
  resume_filename: string | null;
}

export interface SearchResult {
  total: number;
  candidates: CandidateSearchItem[];
  next_cursor: string | null;
  page_size: number;
  cached: boolean;
}

// ── Saved search ──────────────────────────────────────────────────────────────

export interface SavedSearchCreate {
  name: string;
  filters: Record<string, unknown>;
}

export interface SavedSearchResponse {
  id: string;
  name: string;
  filters: Record<string, unknown>;
  created_at: string;
}

// ── Talent pool ───────────────────────────────────────────────────────────────

export interface TalentPoolCreate {
  name: string;
}

export interface TalentPoolResponse {
  id: string;
  name: string;
  candidate_count: number;
  created_at: string;
}

export interface TalentPoolAddCandidates {
  candidate_ids: string[];
  notes?: string | null;
}

// ── Bulk export ───────────────────────────────────────────────────────────────

export interface BulkExportRequest {
  candidate_ids: string[];
}

// ── UI helpers ────────────────────────────────────────────────────────────────

export const EDUCATION_TIER_LABELS: Record<EducationTier, string> = {
  any: "Any",
  undergraduate: "Undergraduate (B.Tech / B.Sc)",
  postgraduate: "Postgraduate (M.Tech / MBA)",
  phd: "PhD / Doctorate",
};

export const WORK_PREFERENCE_LABELS: Record<WorkPreference, string> = {
  any: "Any",
  remote: "Remote",
  onsite: "On-site",
  hybrid: "Hybrid",
};

export const SORT_BY_LABELS: Record<SortBy, string> = {
  relevance: "Relevance",
  experience: "Experience (High to Low)",
  match_score: "AI Match Score",
  recently_active: "Recently Active",
  profile_strength: "Profile Strength",
};
