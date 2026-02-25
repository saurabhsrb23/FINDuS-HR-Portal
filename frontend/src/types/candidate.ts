export interface WorkExperience {
  id: string;
  company_name: string;
  job_title: string;
  employment_type: "full_time" | "part_time" | "contract" | "internship" | "freelance";
  location: string | null;
  is_current: boolean;
  start_date: string | null;
  end_date: string | null;
  description: string | null;
  achievements: string[] | null;
}

export interface Education {
  id: string;
  institution: string;
  degree: string | null;
  field_of_study: string | null;
  grade: string | null;
  start_year: number | null;
  end_year: number | null;
  is_current: boolean;
  description: string | null;
}

export interface Certification {
  id: string;
  name: string;
  issuing_org: string | null;
  issue_date: string | null;
  expiry_date: string | null;
  credential_id: string | null;
  credential_url: string | null;
}

export interface Project {
  id: string;
  title: string;
  description: string | null;
  tech_stack: string[] | null;
  project_url: string | null;
  repo_url: string | null;
  start_date: string | null;
  end_date: string | null;
}

export interface CandidateSkill {
  id: string;
  skill_name: string;
  proficiency: number;
  years_exp: number | null;
}

export interface CandidateProfile {
  id: string;
  user_id: string;
  full_name: string | null;
  phone: string | null;
  location: string | null;
  headline: string | null;
  summary: string | null;
  avatar_url: string | null;
  resume_url: string | null;
  resume_filename: string | null;
  desired_role: string | null;
  desired_salary_min: number | null;
  desired_salary_max: number | null;
  desired_location: string | null;
  open_to_remote: boolean;
  notice_period_days: number | null;
  years_of_experience: number | null;
  profile_strength: number;
  created_at: string;
  updated_at: string;
  work_experiences: WorkExperience[];
  educations: Education[];
  certifications: Certification[];
  projects: Project[];
  skills: CandidateSkill[];
}

export interface ProfileStrength {
  score: number;
  breakdown: Record<string, number>;
  tips: string[];
}

export interface SalaryBenchmark {
  role: string;
  location: string;
  min_salary: number;
  median_salary: number;
  max_salary: number;
  currency: string;
  source: string;
}
