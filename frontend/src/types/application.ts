export type ApplicationStatus =
  | "applied"
  | "screening"
  | "interview"
  | "offer"
  | "hired"
  | "rejected"
  | "withdrawn";

export interface TimelineEvent {
  status: ApplicationStatus;
  timestamp: string;
  note: string;
}

export interface ApplicationAnswer {
  id: string;
  question_id: string;
  answer_text: string | null;
}

export interface Application {
  id: string;
  job_id: string;
  candidate_id: string;
  status: ApplicationStatus;
  cover_letter: string | null;
  resume_url: string | null;
  timeline: TimelineEvent[] | null;
  applied_at: string;
  updated_at: string;
  answers: ApplicationAnswer[];
}

export interface ApplicationListItem {
  id: string;
  job_id: string;
  status: ApplicationStatus;
  applied_at: string;
  updated_at: string;
  job_title: string | null;
  company_name: string | null;
  job_location: string | null;
}

export interface JobAlert {
  id: string;
  title: string;
  keywords: string | null;
  location: string | null;
  job_type: string | null;
  salary_min: number | null;
  is_active: boolean;
  last_sent_at: string | null;
  created_at: string;
}

export interface JobSearchResult {
  id: string;
  title: string;
  company_name: string | null;
  location: string | null;
  job_type: string | null;
  salary_min: number | null;
  salary_max: number | null;
  status: string;
  created_at: string;
  description: string | null;
  skills: { skill_name: string; is_required: boolean }[];
}

export interface JobSearchResponse {
  items: JobSearchResult[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}
