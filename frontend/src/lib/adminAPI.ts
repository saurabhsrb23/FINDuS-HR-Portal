// Admin portal API client
import axios from "axios";
import type {
  AdminTokenResponse,
  AdminUserCreate,
  AdminUserResponse,
  AdminUserUpdate,
  AnnouncementRequest,
  CompanyStatusUpdate,
  MonitoringMetrics,
  PlatformEventListResponse,
  PlatformOverview,
  UserListResponse,
} from "@/types/admin";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

function adminAxios() {
  const token =
    typeof window !== "undefined"
      ? sessionStorage.getItem("admin_token")
      : null;
  return axios.create({
    baseURL: BASE,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    withCredentials: true,
  });
}

export const adminAPI = {
  // ── Auth ──────────────────────────────────────────────────────────────────
  login: async (
    email: string,
    password: string,
    pin: string
  ): Promise<AdminTokenResponse> => {
    const { data } = await adminAxios().post<AdminTokenResponse>(
      "/admin/login",
      { email, password, pin }
    );
    return data;
  },

  verifyPin: async (pin: string): Promise<{ verified: boolean }> => {
    const { data } = await adminAxios().post<{ verified: boolean }>(
      `/admin/verify-pin?pin=${pin}`
    );
    return data;
  },

  // ── Platform ──────────────────────────────────────────────────────────────
  getPlatformOverview: async (): Promise<PlatformOverview> => {
    const { data } = await adminAxios().get<PlatformOverview>(
      "/admin/platform/overview"
    );
    return data;
  },

  getMonitoring: async (): Promise<MonitoringMetrics> => {
    const { data } = await adminAxios().get<MonitoringMetrics>(
      "/admin/monitoring"
    );
    return data;
  },

  // ── Users ─────────────────────────────────────────────────────────────────
  listCandidates: async (
    search?: string,
    page = 1
  ): Promise<UserListResponse> => {
    const params: Record<string, string | number> = { page, page_size: 20 };
    if (search) params.search = search;
    const { data } = await adminAxios().get<UserListResponse>(
      "/admin/users/candidates",
      { params }
    );
    return data;
  },

  listHrUsers: async (
    search?: string,
    page = 1
  ): Promise<UserListResponse> => {
    const params: Record<string, string | number> = { page, page_size: 20 };
    if (search) params.search = search;
    const { data } = await adminAxios().get<UserListResponse>(
      "/admin/users/hr",
      { params }
    );
    return data;
  },

  deactivateUser: async (userId: string): Promise<void> => {
    await adminAxios().put(`/admin/users/${userId}/deactivate`);
  },

  // ── Companies ─────────────────────────────────────────────────────────────
  listCompanies: async (page = 1) => {
    const { data } = await adminAxios().get("/admin/companies", {
      params: { page, page_size: 20 },
    });
    return data;
  },

  updateCompanyStatus: async (
    companyId: string,
    update: CompanyStatusUpdate
  ): Promise<void> => {
    await adminAxios().patch(`/admin/companies/${companyId}`, update);
  },

  // ── Admin users ───────────────────────────────────────────────────────────
  listAdmins: async (): Promise<AdminUserResponse[]> => {
    const { data } = await adminAxios().get<AdminUserResponse[]>(
      "/admin/admins"
    );
    return data;
  },

  createAdmin: async (
    payload: AdminUserCreate
  ): Promise<AdminUserResponse> => {
    const { data } = await adminAxios().post<AdminUserResponse>(
      "/admin/admins",
      payload
    );
    return data;
  },

  updateAdmin: async (
    adminId: string,
    payload: AdminUserUpdate
  ): Promise<AdminUserResponse> => {
    const { data } = await adminAxios().put<AdminUserResponse>(
      `/admin/admins/${adminId}`,
      payload
    );
    return data;
  },

  deleteAdmin: async (adminId: string): Promise<void> => {
    await adminAxios().delete(`/admin/admins/${adminId}?confirmation=DELETE`);
  },

  // ── Events ────────────────────────────────────────────────────────────────
  listEvents: async (
    params: {
      event_type?: string;
      actor_role?: string;
      page?: number;
      page_size?: number;
    } = {}
  ): Promise<PlatformEventListResponse> => {
    const { data } = await adminAxios().get<PlatformEventListResponse>(
      "/admin/events",
      { params: { page: 1, page_size: 50, ...params } }
    );
    return data;
  },

  // ── Announcements ─────────────────────────────────────────────────────────
  sendAnnouncement: async (payload: AnnouncementRequest): Promise<void> => {
    await adminAxios().post("/admin/announcements", payload);
  },
};

// Store admin session in sessionStorage
export function saveAdminSession(data: AdminTokenResponse): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem("admin_token", data.access_token);
  sessionStorage.setItem("admin_role", data.role);
  sessionStorage.setItem("admin_name", data.full_name);
  sessionStorage.setItem("admin_id", data.admin_id);
}

export function getAdminSession() {
  if (typeof window === "undefined") return null;
  const token = sessionStorage.getItem("admin_token");
  if (!token) return null;
  return {
    token,
    role: sessionStorage.getItem("admin_role") as string,
    full_name: sessionStorage.getItem("admin_name") as string,
    admin_id: sessionStorage.getItem("admin_id") as string,
  };
}

export function clearAdminSession(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem("admin_token");
  sessionStorage.removeItem("admin_role");
  sessionStorage.removeItem("admin_name");
  sessionStorage.removeItem("admin_id");
}
