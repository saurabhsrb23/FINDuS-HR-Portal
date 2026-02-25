export interface ParsedResumeFields {
  full_name: string | null;
  phone: string | null;
  location: string | null;
  headline: string | null;
  summary: string | null;
  years_of_experience: number | null;
  skills: string[];
  work_experiences: {
    company_name: string;
    job_title: string;
    start_date: string | null;
    end_date: string | null;
    is_current: boolean;
    description: string | null;
  }[];
  educations: {
    institution: string;
    degree: string | null;
    field_of_study: string | null;
    start_year: number | null;
    end_year: number | null;
  }[];
}

export interface ResumeSummary {
  candidate_id: string;
  summary: string;
  strengths: string[];
  experience_years: number | null;
  top_skills: string[];
  cached: boolean;
}

export interface MatchScore {
  application_id: string;
  score: number;
  grade: "A" | "B" | "C" | "D" | "F";
  matched_skills: string[];
  missing_skills: string[];
  summary: string;
  cached: boolean;
}

export interface CandidateComparison {
  candidates: {
    name: string;
    score: number;
    top_skills: string[];
    pros: string[];
    cons: string[];
  }[];
  recommendation: string;
}

export interface RankingResult {
  job_id: string;
  ranked: {
    rank: number;
    application_id: string;
    score: number;
    reason: string;
  }[];
  total: number;
}

export interface GenerateJDRequest {
  role: string;
  department?: string;
  keywords: string[];
  experience_years?: number;
  location?: string;
  job_type?: string;
}

export interface GeneratedJD {
  title: string;
  description: string;
  requirements: string;
  responsibilities: string;
  benefits: string;
}

export interface RejectionEmail {
  subject: string;
  body: string;
}

export interface ResumeOptimizer {
  overall_score: number;
  ats_score: number;
  impact_score: number;
  tips: string[];
  strong_sections: string[];
  weak_sections: string[];
  cached: boolean;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
  tokens_used: number;
}
