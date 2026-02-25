// Search API client — mirrors backend /api/v1/search/*

import api from "./api";
import type {
  BulkExportRequest,
  SavedSearchCreate,
  SavedSearchResponse,
  SearchCandidateRequest,
  SearchResult,
  TalentPoolAddCandidates,
  TalentPoolCreate,
  TalentPoolResponse,
} from "@/types/search";

export const searchAPI = {
  // ── Candidate search ────────────────────────────────────────────────────
  searchCandidates: (filters: SearchCandidateRequest) =>
    api.post<SearchResult>("/api/v1/search/candidates", filters),

  // ── Saved searches ──────────────────────────────────────────────────────
  createSavedSearch: (data: SavedSearchCreate) =>
    api.post<SavedSearchResponse>("/api/v1/search/saved", data),

  listSavedSearches: () =>
    api.get<SavedSearchResponse[]>("/api/v1/search/saved"),

  deleteSavedSearch: (searchId: string) =>
    api.delete<void>(`/api/v1/search/saved/${searchId}`),

  // ── Talent pools ────────────────────────────────────────────────────────
  createTalentPool: (data: TalentPoolCreate) =>
    api.post<TalentPoolResponse>("/api/v1/search/pools", data),

  listTalentPools: () =>
    api.get<TalentPoolResponse[]>("/api/v1/search/pools"),

  addToTalentPool: (poolId: string, data: TalentPoolAddCandidates) =>
    api.post<{ added: number; pool_id: string }>(
      `/api/v1/search/pools/${poolId}/candidates`,
      data
    ),

  // ── Bulk CSV export ─────────────────────────────────────────────────────
  exportCsv: async (data: BulkExportRequest): Promise<void> => {
    const response = await api.post<Blob>("/api/v1/search/export/csv", data, {
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "candidates.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
