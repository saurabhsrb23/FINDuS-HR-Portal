"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import BulkActions from "@/components/search/BulkActions";
import CandidateCard from "@/components/search/CandidateCard";
import CandidateTable from "@/components/search/CandidateTable";
import FilterPanel from "@/components/search/FilterPanel";
import { searchAPI } from "@/lib/searchAPI";
import type {
  CandidateSearchItem,
  SavedSearchResponse,
  SearchCandidateRequest,
  SearchResult,
  SortBy,
  TalentPoolResponse,
} from "@/types/search";
import { SORT_BY_LABELS } from "@/types/search";

type ViewMode = "card" | "table";

const DEFAULT_FILTERS: SearchCandidateRequest = {
  query: null,
  skills: [],
  skill_match: "AND",
  education_tier: "any",
  work_preference: "any",
  sort_by: "relevance",
  page_size: 20,
};

export default function SearchPage() {
  const [filters, setFilters] = useState<SearchCandidateRequest>(DEFAULT_FILTERS);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [viewMode, setViewMode] = useState<ViewMode>("card");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Saved searches
  const [savedSearches, setSavedSearches] = useState<SavedSearchResponse[]>([]);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [saving, setSaving] = useState(false);

  // Talent pools
  const [pools, setPools] = useState<TalentPoolResponse[]>([]);

  // Infinite scroll / pagination
  const [cursors, setCursors] = useState<string[]>([]); // cursor stack
  const [allCandidates, setAllCandidates] = useState<CandidateSearchItem[]>([]);

  const [exporting, setExporting] = useState(false);

  // Load saved searches + pools on mount
  useEffect(() => {
    searchAPI.listSavedSearches().then((r) => setSavedSearches(r.data)).catch(() => {});
    searchAPI.listTalentPools().then((r) => setPools(r.data)).catch(() => {});
  }, []);

  // ── Search ──────────────────────────────────────────────────────────────────

  async function doSearch(newFilters: SearchCandidateRequest, append = false) {
    setLoading(true);
    setError(null);
    try {
      const res = await searchAPI.searchCandidates(newFilters);
      const data = res.data;
      if (append) {
        setAllCandidates((prev) => [...prev, ...data.candidates]);
      } else {
        setAllCandidates(data.candidates);
        setSelectedIds(new Set());
      }
      setResult(data);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Search failed. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  function handleSearch() {
    const fresh = { ...filters, cursor: null };
    setCursors([]);
    setFilters(fresh);
    doSearch(fresh, false);
  }

  function handleLoadMore() {
    if (!result?.next_cursor) return;
    const next = { ...filters, cursor: result.next_cursor };
    setCursors((prev) => [...prev, result.next_cursor!]);
    setFilters(next);
    doSearch(next, true);
  }

  // ── Selection ───────────────────────────────────────────────────────────────

  function toggleSelect(id: string) {
    setSelectedIds((prev) => {
      const s = new Set(prev);
      if (s.has(id)) s.delete(id);
      else s.add(id);
      return s;
    });
  }

  function toggleAll() {
    if (allCandidates.every((c) => selectedIds.has(c.id))) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(allCandidates.map((c) => c.id)));
    }
  }

  // ── Saved searches ──────────────────────────────────────────────────────────

  async function handleSaveSearch() {
    const name = saveName.trim();
    if (!name) return;
    setSaving(true);
    try {
      const res = await searchAPI.createSavedSearch({
        name,
        filters: filters as Record<string, unknown>,
      });
      setSavedSearches((prev) => [res.data, ...prev]);
      setSaveDialogOpen(false);
      setSaveName("");
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteSavedSearch(id: string) {
    await searchAPI.deleteSavedSearch(id).catch(() => {});
    setSavedSearches((prev) => prev.filter((s) => s.id !== id));
  }

  function handleLoadSavedSearch(saved: SavedSearchResponse) {
    const f = { ...DEFAULT_FILTERS, ...saved.filters } as SearchCandidateRequest;
    setFilters(f);
    doSearch(f, false);
  }

  // ── Talent pools ─────────────────────────────────────────────────────────────

  async function handleAddToPool(poolId: string) {
    const ids = Array.from(selectedIds);
    await searchAPI.addToTalentPool(poolId, { candidate_ids: ids }).catch(() => {});
    searchAPI.listTalentPools().then((r) => setPools(r.data)).catch(() => {});
  }

  async function handleCreatePool(name: string): Promise<TalentPoolResponse | null> {
    try {
      const res = await searchAPI.createTalentPool({ name });
      setPools((prev) => [res.data, ...prev]);
      return res.data;
    } catch {
      return null;
    }
  }

  // ── Export CSV ───────────────────────────────────────────────────────────────

  async function handleExportCsv() {
    setExporting(true);
    await searchAPI.exportCsv({ candidate_ids: Array.from(selectedIds) }).catch(() => {});
    setExporting(false);
  }

  // ── Sort change ───────────────────────────────────────────────────────────────

  function handleSortChange(sort: SortBy) {
    const updated = { ...filters, sort_by: sort, cursor: null };
    setCursors([]);
    setFilters(updated);
    doSearch(updated, false);
  }

  // ── Render ────────────────────────────────────────────────────────────────────

  return (
    <div className="flex h-full">
      {/* Filter sidebar */}
      <FilterPanel
        filters={filters}
        onChange={setFilters}
        onSearch={handleSearch}
        loading={loading}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Toolbar */}
        <header className="flex-shrink-0 bg-white border-b border-gray-200 px-6 py-3">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-lg font-bold text-gray-900">Find Candidates</h1>
              {result && (
                <p className="text-xs text-gray-500 mt-0.5">
                  {result.total.toLocaleString()} results
                  {result.cached && (
                    <span className="ml-1 text-indigo-400">(cached)</span>
                  )}
                </p>
              )}
            </div>

            <div className="flex items-center gap-3 flex-wrap">
              {/* Sort */}
              <select
                value={filters.sort_by ?? "relevance"}
                onChange={(e) => handleSortChange(e.target.value as SortBy)}
                className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              >
                {(Object.keys(SORT_BY_LABELS) as SortBy[]).map((s) => (
                  <option key={s} value={s}>
                    {SORT_BY_LABELS[s]}
                  </option>
                ))}
              </select>

              {/* View toggle */}
              <div className="flex rounded-lg border border-gray-300 overflow-hidden text-sm">
                <button
                  onClick={() => setViewMode("card")}
                  className={`px-3 py-1.5 transition-colors ${
                    viewMode === "card"
                      ? "bg-indigo-600 text-white"
                      : "bg-white text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  ⊞ Cards
                </button>
                <button
                  onClick={() => setViewMode("table")}
                  className={`px-3 py-1.5 transition-colors ${
                    viewMode === "table"
                      ? "bg-indigo-600 text-white"
                      : "bg-white text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  ≡ Table
                </button>
              </div>

              {/* Save search */}
              <button
                onClick={() => setSaveDialogOpen(true)}
                className="border border-gray-300 rounded-md px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
              >
                ✦ Save Search
              </button>
            </div>
          </div>

          {/* Saved searches chips */}
          {savedSearches.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {savedSearches.map((s) => (
                <span
                  key={s.id}
                  className="inline-flex items-center gap-1 bg-gray-100 text-gray-700 text-xs px-2.5 py-1 rounded-full hover:bg-gray-200 transition-colors"
                >
                  <button
                    onClick={() => handleLoadSavedSearch(s)}
                    className="hover:text-indigo-700"
                  >
                    {s.name}
                  </button>
                  <button
                    onClick={() => handleDeleteSavedSearch(s.id)}
                    className="text-gray-400 hover:text-red-500 font-bold leading-none"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Bulk actions bar */}
          {selectedIds.size > 0 && (
            <div className="mt-2">
              <BulkActions
                selectedCount={selectedIds.size}
                onClearSelection={() => setSelectedIds(new Set())}
                onExportCsv={handleExportCsv}
                onAddToPool={handleAddToPool}
                pools={pools}
                onCreatePool={handleCreatePool}
                exporting={exporting}
              />
            </div>
          )}
        </header>

        {/* Results area */}
        <div className="flex-1 overflow-y-auto">
          {/* Error */}
          {error && (
            <div className="m-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Loading skeleton */}
          {loading && allCandidates.length === 0 && (
            <div className="p-4 grid grid-cols-1 gap-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div
                  key={i}
                  className="h-32 bg-gray-100 rounded-xl animate-pulse"
                />
              ))}
            </div>
          )}

          {/* Empty state (not loading, no results, search was run) */}
          {!loading && result && allCandidates.length === 0 && (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <p className="text-4xl mb-3">🔍</p>
              <p className="font-medium text-gray-600">No candidates match your criteria</p>
              <p className="text-sm mt-1">Try broadening your filters</p>
            </div>
          )}

          {/* Initial empty state */}
          {!loading && !result && (
            <div className="flex flex-col items-center justify-center h-64 text-gray-400">
              <p className="text-5xl mb-4">👥</p>
              <p className="font-medium text-gray-600">Search for candidates</p>
              <p className="text-sm mt-1">Use the filters on the left and click Search</p>
            </div>
          )}

          {/* Card view */}
          {viewMode === "card" && allCandidates.length > 0 && (
            <div className="p-4 grid grid-cols-1 xl:grid-cols-2 gap-3">
              {allCandidates.map((c) => (
                <CandidateCard
                  key={c.id}
                  candidate={c}
                  selected={selectedIds.has(c.id)}
                  onToggleSelect={toggleSelect}
                />
              ))}
            </div>
          )}

          {/* Table view */}
          {viewMode === "table" && allCandidates.length > 0 && (
            <CandidateTable
              candidates={allCandidates}
              selectedIds={selectedIds}
              onToggleSelect={toggleSelect}
              onToggleAll={toggleAll}
            />
          )}

          {/* Load more */}
          {result?.next_cursor && !loading && (
            <div className="flex justify-center py-6">
              <button
                onClick={handleLoadMore}
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                Load more
              </button>
            </div>
          )}

          {/* Loading more indicator */}
          {loading && allCandidates.length > 0 && (
            <div className="flex justify-center py-6">
              <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
      </div>

      {/* Save search dialog */}
      {saveDialogOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-6 w-96">
            <h2 className="font-bold text-gray-900 text-lg mb-4">Save Search</h2>
            <input
              type="text"
              placeholder="Give this search a name…"
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSaveSearch();
                if (e.key === "Escape") setSaveDialogOpen(false);
              }}
              autoFocus
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setSaveDialogOpen(false)}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSearch}
                disabled={!saveName.trim() || saving}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-lg disabled:opacity-50"
              >
                {saving ? "Saving…" : "Save"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
