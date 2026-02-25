import api from "./api";
import type {
  Application,
  ApplicationListItem,
  JobAlert,
  JobSearchResponse,
} from "@/types/application";

export const applicationAPI = {
  searchJobs: (params?: {
    q?: string;
    location?: string;
    job_type?: string;
    salary_min?: number;
    page?: number;
    limit?: number;
  }) => api.get<JobSearchResponse>("/jobs/search", { params }),

  getJobDetail: (jobId: string) =>
    api.get<JobSearchResponse["items"][0]>(`/jobs/${jobId}/detail`),

  apply: (jobId: string, data: { cover_letter?: string; answers?: { question_id: string; answer_text?: string }[] }) =>
    api.post<Application>(`/jobs/${jobId}/apply`, data),

  getMyApplications: () =>
    api.get<ApplicationListItem[]>("/candidates/applications"),

  getApplicationDetail: (appId: string) =>
    api.get<Application>(`/candidates/applications/${appId}`),

  withdraw: (appId: string) =>
    api.delete(`/candidates/applications/${appId}`),

  getRecommendations: (limit = 10) =>
    api.get<JobSearchResponse["items"]>("/candidates/recommendations", { params: { limit } }),

  createAlert: (data: { title: string; keywords?: string; location?: string; job_type?: string; salary_min?: number }) =>
    api.post<JobAlert>("/candidates/alerts", data),

  getAlerts: () => api.get<JobAlert[]>("/candidates/alerts"),

  deleteAlert: (alertId: string) =>
    api.delete(`/candidates/alerts/${alertId}`),
};
