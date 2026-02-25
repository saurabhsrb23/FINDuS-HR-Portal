import api from "./api";
import type {
  CandidateComparison,
  ChatMessage,
  ChatResponse,
  GeneratedJD,
  GenerateJDRequest,
  MatchScore,
  ParsedResumeFields,
  RankingResult,
  RejectionEmail,
  ResumeSummary,
  ResumeOptimizer,
} from "@/types/ai";

export const aiAPI = {
  // ── Candidate ──────────────────────────────────────────────────────────────
  parseResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<ParsedResumeFields>("/ai/parse-resume", form);
  },

  optimizeResume: (refresh = false) =>
    api.get<ResumeOptimizer>("/ai/optimize-resume", { params: { refresh } }),

  getMyResumeSummary: (refresh = false) =>
    api.get<ResumeSummary>("/ai/my-resume-summary", { params: { refresh } }),

  chat: (messages: ChatMessage[], context?: string) =>
    api.post<ChatResponse>("/ai/chat", { messages, context }),

  // ── HR ─────────────────────────────────────────────────────────────────────
  getResumeSummary: (candidateId: string, refresh = false) =>
    api.get<ResumeSummary>(`/ai/resume-summary/${candidateId}`, {
      params: { refresh },
    }),

  getMatchScore: (applicationId: string, refresh = false) =>
    api.get<MatchScore>(`/ai/match-score/${applicationId}`, {
      params: { refresh },
    }),

  enqueueMatchScore: (applicationId: string) =>
    api.post(`/ai/match-score/${applicationId}/enqueue`),

  compareCandidates: (applicationIds: string[]) =>
    api.post<CandidateComparison>("/ai/compare-candidates", {
      application_ids: applicationIds,
    }),

  queueRanking: (jobId: string) =>
    api.post(`/ai/rank-applicants/${jobId}`),

  getRanking: (jobId: string) =>
    api.get<RankingResult>(`/ai/rank-applicants/${jobId}`),

  generateJD: (data: GenerateJDRequest) =>
    api.post<GeneratedJD>("/ai/generate-jd", data),

  draftRejectionEmail: (applicationId: string, reason?: string) =>
    api.post<RejectionEmail>("/ai/rejection-email", {
      application_id: applicationId,
      reason,
    }),
};
