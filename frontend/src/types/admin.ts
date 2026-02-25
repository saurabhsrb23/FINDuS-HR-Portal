// Admin portal TypeScript types

export type AdminRole = "elite_admin" | "admin" | "superadmin";

export interface AdminTokenResponse {
  access_token: string;
  token_type: string;
  admin_id: string;
  role: AdminRole;
  full_name: string;
}

export interface AdminSession {
  admin_id: string;
  role: AdminRole;
  full_name: string;
  token: string;
}

export interface AdminUserResponse {
  id: string;
  email: string;
  full_name: string;
  role: AdminRole;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface AdminUserCreate {
  email: string;
  password: string;
  pin: string;
  full_name: string;
  role: AdminRole;
}

export interface AdminUserUpdate {
  full_name?: string;
  role?: AdminRole;
  is_active?: boolean;
  pin?: string;
}

export interface PlatformOverview {
  total_users: number;
  total_candidates: number;
  total_hr_users: number;
  total_jobs: number;
  active_jobs: number;
  total_applications: number;
  total_companies: number;
  active_ws_connections: number;
  platform_events_today: number;
}

export interface MonitoringMetrics {
  active_ws_connections: number;
  db_latency_ms: number;
  redis_connected_clients: number;
  redis_used_memory_mb: number;
  redis_hit_rate: number;
  groq_calls_today: number;
  error_events_today: number;
  uptime_seconds: number;
}

export interface UserListItem {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface UserListResponse {
  items: UserListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface CompanyListItem {
  id: string;
  name: string;
  website: string | null;
  industry: string | null;
  is_verified: boolean;
  is_active: boolean;
  hr_email: string | null;
  created_at: string;
}

export interface CompanyStatusUpdate {
  is_verified?: boolean;
  is_active?: boolean;
}

export interface PlatformEventItem {
  id: string;
  event_type: string;
  actor_id: string | null;
  actor_role: string | null;
  target_id: string | null;
  target_type: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface PlatformEventListResponse {
  items: PlatformEventItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface AnnouncementRequest {
  message: string;
  target_role?: string | null;
}
