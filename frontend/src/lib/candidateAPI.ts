import api from "./api";
import type {
  CandidateProfile,
  ProfileStrength,
  SalaryBenchmark,
} from "@/types/candidate";

export const candidateAPI = {
  getProfile: () => api.get<CandidateProfile>("/candidates/profile"),

  updateProfile: (data: Partial<CandidateProfile>) =>
    api.patch<CandidateProfile>("/candidates/profile", data),

  uploadResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<CandidateProfile>("/candidates/profile/resume", form);
  },

  getStrength: () =>
    api.get<ProfileStrength>("/candidates/profile/strength"),

  addWorkExperience: (data: object) =>
    api.post("/candidates/profile/work-experiences", data),
  deleteWorkExperience: (id: string) =>
    api.delete(`/candidates/profile/work-experiences/${id}`),

  addEducation: (data: object) =>
    api.post("/candidates/profile/educations", data),
  deleteEducation: (id: string) =>
    api.delete(`/candidates/profile/educations/${id}`),

  addCertification: (data: object) =>
    api.post("/candidates/profile/certifications", data),
  deleteCertification: (id: string) =>
    api.delete(`/candidates/profile/certifications/${id}`),

  addProject: (data: object) =>
    api.post("/candidates/profile/projects", data),
  deleteProject: (id: string) =>
    api.delete(`/candidates/profile/projects/${id}`),

  addSkill: (data: object) =>
    api.post("/candidates/profile/skills", data),
  deleteSkill: (id: string) =>
    api.delete(`/candidates/profile/skills/${id}`),

  getSalaryBenchmark: (params?: { role?: string; location?: string }) =>
    api.get<SalaryBenchmark[]>("/candidates/salary-benchmark", { params }),

  // HR: download a specific candidate's resume
  getCandidateResumeUrl: (candidateId: string) =>
    api.get<{ resume_url: string; resume_filename: string }>(
      `/candidates/${candidateId}/resume-download`
    ),
};
