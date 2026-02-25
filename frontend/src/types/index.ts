/**
 * FindUs — shared TypeScript interfaces for all domain entities.
 * Keep this file as the single source of truth for frontend types.
 */

// ─── Primitives ───────────────────────────────────────────────────────────────

export type UUID = string;
export type ISODateString = string; // "2024-01-01T00:00:00Z"

// ─── Enumerations ─────────────────────────────────────────────────────────────

export type UserRole = "candidate" | "recruiter" | "hr_manager" | "admin";

export type ApplicationStatus =
  | "applied"
  | "screening"
  | "interview_scheduled"
  | "interview_completed"
  | "offer_sent"
  | "hired"
  | "rejected"
  | "withdrawn";

export type JobStatus = "draft" | "published" | "paused" | "closed" | "archived";

export type NotificationType =
  | "application_update"
  | "interview_reminder"
  | "message_received"
  | "offer_received"
  | "system";

export type PlatformEventType =
  | "user_registered"
  | "job_posted"
  | "application_submitted"
  | "interview_scheduled"
  | "offer_extended"
  | "hire_completed";

export type ChatMessageRole = "user" | "assistant" | "system";

// ─── User ─────────────────────────────────────────────────────────────────────

export interface User {
  id: UUID;
  email: string;
  full_name: string;
  role: UserRole;
  avatar_url: string | null;
  phone: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface UserProfile extends User {
  bio: string | null;
  location: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  skills: string[];
  years_of_experience: number | null;
}

// ─── Admin User ───────────────────────────────────────────────────────────────

export interface AdminUser {
  id: UUID;
  email: string;
  full_name: string;
  is_superadmin: boolean;
  permissions: string[];
  last_login_at: ISODateString | null;
  created_at: ISODateString;
}

// ─── Candidate ────────────────────────────────────────────────────────────────

export interface Candidate {
  id: UUID;
  user_id: UUID;
  user: Pick<User, "id" | "email" | "full_name" | "avatar_url">;
  resume_url: string | null;
  resume_parsed_at: ISODateString | null;
  headline: string | null;
  summary: string | null;
  skills: string[];
  education: EducationEntry[];
  experience: ExperienceEntry[];
  ai_score: number | null; // 0–100
  created_at: ISODateString;
  updated_at: ISODateString;
}

export interface EducationEntry {
  institution: string;
  degree: string;
  field_of_study: string | null;
  start_year: number;
  end_year: number | null;
  gpa: number | null;
}

export interface ExperienceEntry {
  company: string;
  title: string;
  location: string | null;
  start_date: ISODateString;
  end_date: ISODateString | null;
  is_current: boolean;
  description: string | null;
}

// ─── Job ──────────────────────────────────────────────────────────────────────

export interface Job {
  id: UUID;
  title: string;
  department: string | null;
  location: string;
  is_remote: boolean;
  employment_type: "full_time" | "part_time" | "contract" | "internship";
  description: string;
  requirements: string[];
  nice_to_have: string[];
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  status: JobStatus;
  posted_by_id: UUID;
  posted_by: Pick<User, "id" | "full_name">;
  application_count: number;
  published_at: ISODateString | null;
  closes_at: ISODateString | null;
  created_at: ISODateString;
  updated_at: ISODateString;
}

// ─── Application ──────────────────────────────────────────────────────────────

export interface Application {
  id: UUID;
  job_id: UUID;
  job: Pick<Job, "id" | "title" | "department" | "location">;
  candidate_id: UUID;
  candidate: Pick<Candidate, "id" | "headline" | "ai_score"> & {
    user: Pick<User, "id" | "full_name" | "email" | "avatar_url">;
  };
  status: ApplicationStatus;
  cover_letter: string | null;
  ai_summary: string | null;
  ai_match_score: number | null; // 0–100
  recruiter_notes: string | null;
  interview_scheduled_at: ISODateString | null;
  offer_salary: number | null;
  rejection_reason: string | null;
  applied_at: ISODateString;
  updated_at: ISODateString;
}

// ─── Chat / AI Conversation ───────────────────────────────────────────────────

export interface ChatMessage {
  id: UUID;
  conversation_id: UUID;
  role: ChatMessageRole;
  content: string;
  tokens_used: number | null;
  metadata: Record<string, unknown> | null;
  created_at: ISODateString;
}

export interface Conversation {
  id: UUID;
  user_id: UUID;
  title: string | null;
  messages: ChatMessage[];
  created_at: ISODateString;
  updated_at: ISODateString;
}

// ─── Notification ─────────────────────────────────────────────────────────────

export interface Notification {
  id: UUID;
  user_id: UUID;
  type: NotificationType;
  title: string;
  body: string;
  is_read: boolean;
  action_url: string | null;
  metadata: Record<string, unknown> | null;
  created_at: ISODateString;
}

// ─── Platform Event (audit log) ───────────────────────────────────────────────

export interface PlatformEvent {
  id: UUID;
  event_type: PlatformEventType;
  actor_id: UUID | null;
  actor_email: string | null;
  target_id: UUID | null;
  target_type: string | null;
  payload: Record<string, unknown>;
  ip_address: string | null;
  created_at: ISODateString;
}

// ─── API response wrappers ────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string | { msg: string; type: string }[];
  status_code: number;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
}

export interface AuthState {
  user: User | null;
  token: string | null;
  is_authenticated: boolean;
  is_loading: boolean;
}

// ─── Dashboard / Analytics ────────────────────────────────────────────────────

export interface DashboardStats {
  total_jobs: number;
  active_jobs: number;
  total_applications: number;
  applications_this_week: number;
  interviews_scheduled: number;
  hires_this_month: number;
  avg_time_to_hire_days: number;
}

export interface ApplicationStatusBreakdown {
  status: ApplicationStatus;
  count: number;
}
