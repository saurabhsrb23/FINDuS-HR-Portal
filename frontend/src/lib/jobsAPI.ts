/**
 * Jobs API client — wraps all /jobs and /analytics/jobs endpoints.
 */

import { api } from "@/lib/api";
import type {
  AnalyticsSummary,
  Job,
  JobCreate,
  JobListResponse,
  JobQuestion,
  JobQuestionCreate,
  JobQuestionUpdate,
  JobSkill,
  JobSkillCreate,
  JobStatus,
  JobType,
  JobUpdate,
  PipelineStage,
  PipelineStageCreate,
  PipelineStageReorderItem,
  PipelineStageUpdate,
} from "@/types/job";

// ── Job CRUD ─────────────────────────────────────────────────────────────────

export async function createJob(data: JobCreate): Promise<Job> {
  const res = await api.post<Job>("/jobs", data);
  return res.data;
}

export interface ListJobsParams {
  status?: JobStatus;
  job_type?: JobType;
  search?: string;
  page?: number;
  page_size?: number;
}

export async function listJobs(
  params: ListJobsParams = {}
): Promise<JobListResponse> {
  const res = await api.get<JobListResponse>("/jobs", { params });
  return res.data;
}

export async function getJob(jobId: string): Promise<Job> {
  const res = await api.get<Job>(`/jobs/${jobId}`);
  return res.data;
}

export async function updateJob(jobId: string, data: JobUpdate): Promise<Job> {
  const res = await api.put<Job>(`/jobs/${jobId}`, data);
  return res.data;
}

export async function deleteJob(jobId: string): Promise<void> {
  await api.delete(`/jobs/${jobId}`);
}

// ── Status transitions ────────────────────────────────────────────────────────

export async function publishJob(jobId: string): Promise<Job> {
  const res = await api.post<Job>(`/jobs/${jobId}/publish`);
  return res.data;
}

export async function pauseJob(jobId: string): Promise<Job> {
  const res = await api.post<Job>(`/jobs/${jobId}/pause`);
  return res.data;
}

export async function closeJob(jobId: string): Promise<Job> {
  const res = await api.post<Job>(`/jobs/${jobId}/close`);
  return res.data;
}

export async function cloneJob(jobId: string): Promise<Job> {
  const res = await api.post<Job>(`/jobs/${jobId}/clone`);
  return res.data;
}

// ── Skills ────────────────────────────────────────────────────────────────────

export async function addSkill(
  jobId: string,
  data: JobSkillCreate
): Promise<JobSkill> {
  const res = await api.post<JobSkill>(`/jobs/${jobId}/skills`, data);
  return res.data;
}

export async function removeSkill(
  jobId: string,
  skillId: string
): Promise<void> {
  await api.delete(`/jobs/${jobId}/skills/${skillId}`);
}

// ── Questions ─────────────────────────────────────────────────────────────────

export async function addQuestion(
  jobId: string,
  data: JobQuestionCreate
): Promise<JobQuestion> {
  const res = await api.post<JobQuestion>(`/jobs/${jobId}/questions`, data);
  return res.data;
}

export async function updateQuestion(
  jobId: string,
  questionId: string,
  data: JobQuestionUpdate
): Promise<JobQuestion> {
  const res = await api.put<JobQuestion>(
    `/jobs/${jobId}/questions/${questionId}`,
    data
  );
  return res.data;
}

export async function deleteQuestion(
  jobId: string,
  questionId: string
): Promise<void> {
  await api.delete(`/jobs/${jobId}/questions/${questionId}`);
}

export async function reorderQuestions(
  jobId: string,
  questionIds: string[]
): Promise<JobQuestion[]> {
  const res = await api.post<JobQuestion[]>(
    `/jobs/${jobId}/questions/reorder`,
    { question_ids: questionIds }
  );
  return res.data;
}

// ── Pipeline stages ───────────────────────────────────────────────────────────

export async function getPipeline(jobId: string): Promise<PipelineStage[]> {
  const res = await api.get<PipelineStage[]>(`/jobs/${jobId}/pipeline`);
  return res.data;
}

export async function addPipelineStage(
  jobId: string,
  data: PipelineStageCreate
): Promise<PipelineStage> {
  const res = await api.post<PipelineStage>(`/jobs/${jobId}/pipeline`, data);
  return res.data;
}

export async function updatePipelineStage(
  jobId: string,
  stageId: string,
  data: PipelineStageUpdate
): Promise<PipelineStage> {
  const res = await api.put<PipelineStage>(
    `/jobs/${jobId}/pipeline/${stageId}`,
    data
  );
  return res.data;
}

export async function deletePipelineStage(
  jobId: string,
  stageId: string
): Promise<void> {
  await api.delete(`/jobs/${jobId}/pipeline/${stageId}`);
}

export async function reorderPipeline(
  jobId: string,
  items: PipelineStageReorderItem[]
): Promise<PipelineStage[]> {
  const res = await api.post<PipelineStage[]>(
    `/jobs/${jobId}/pipeline/reorder`,
    items
  );
  return res.data;
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const res = await api.get<AnalyticsSummary>("/analytics/jobs/summary");
  return res.data;
}

// ── Applicants (HR) ───────────────────────────────────────────────────────────

export interface HRApplicant {
  id: string;
  job_id: string;
  candidate_id: string;
  status: string;
  cover_letter: string | null;
  resume_url: string | null;
  hr_notes: string | null;
  rating: number | null;
  timeline: Array<{ status: string; timestamp: string; note: string }> | null;
  applied_at: string;
  updated_at: string;
  candidate_name: string | null;
  candidate_email: string | null;
  candidate_headline: string | null;
  candidate_location: string | null;
  candidate_years_exp: number | null;
  candidate_skills: string[];
  answers: Array<{ id: string; question_id: string; answer_text: string | null }>;
}

export async function getJobApplicants(jobId: string): Promise<HRApplicant[]> {
  const res = await api.get<HRApplicant[]>(`/jobs/${jobId}/applications`);
  return res.data;
}

export async function updateApplicationStatus(
  appId: string,
  status: string,
  note?: string,
): Promise<void> {
  await api.patch(`/applications/${appId}/status`, { status, note });
}
