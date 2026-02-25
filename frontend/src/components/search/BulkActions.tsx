"use client";

import { useState } from "react";
import type { TalentPoolResponse } from "@/types/search";

interface Props {
  selectedCount: number;
  onClearSelection: () => void;
  onExportCsv: () => Promise<void>;
  onAddToPool: (poolId: string, notes?: string) => Promise<void>;
  pools: TalentPoolResponse[];
  onCreatePool: (name: string) => Promise<TalentPoolResponse | null>;
  exporting?: boolean;
}

export default function BulkActions({
  selectedCount,
  onClearSelection,
  onExportCsv,
  onAddToPool,
  pools,
  onCreatePool,
  exporting,
}: Props) {
  const [showPoolMenu, setShowPoolMenu] = useState(false);
  const [newPoolName, setNewPoolName] = useState("");
  const [creatingPool, setCreatingPool] = useState(false);
  const [addingToPool, setAddingToPool] = useState<string | null>(null);

  if (selectedCount === 0) return null;

  async function handleAddToPool(poolId: string) {
    setAddingToPool(poolId);
    await onAddToPool(poolId);
    setAddingToPool(null);
    setShowPoolMenu(false);
  }

  async function handleCreateAndAdd() {
    const name = newPoolName.trim();
    if (!name) return;
    setCreatingPool(true);
    const pool = await onCreatePool(name);
    if (pool) {
      await onAddToPool(pool.id);
    }
    setNewPoolName("");
    setCreatingPool(false);
    setShowPoolMenu(false);
  }

  return (
    <div className="flex items-center gap-3 bg-indigo-600 text-white px-4 py-2.5 rounded-lg text-sm shadow-lg">
      <span className="font-semibold">
        {selectedCount} selected
      </span>
      <button
        onClick={onClearSelection}
        className="text-indigo-200 hover:text-white transition-colors text-xs"
      >
        Clear
      </button>
      <div className="w-px h-4 bg-indigo-400" />

      {/* Export CSV */}
      <button
        onClick={onExportCsv}
        disabled={exporting}
        className="flex items-center gap-1.5 bg-white/10 hover:bg-white/20 disabled:opacity-50 px-3 py-1.5 rounded-md transition-colors"
      >
        {exporting ? (
          <span className="animate-spin">⟳</span>
        ) : (
          <span>⬇</span>
        )}
        Export CSV
      </button>

      {/* Add to talent pool */}
      <div className="relative">
        <button
          onClick={() => setShowPoolMenu((v) => !v)}
          className="flex items-center gap-1.5 bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-md transition-colors"
        >
          <span>★</span>
          Add to Pool
          <span className="text-xs">▾</span>
        </button>

        {showPoolMenu && (
          <div className="absolute top-full mt-2 right-0 w-64 bg-white text-gray-800 rounded-xl shadow-xl border border-gray-200 z-50">
            <div className="p-3 border-b border-gray-100">
              <p className="text-xs font-semibold text-gray-600 mb-2">
                Existing pools
              </p>
              {pools.length === 0 ? (
                <p className="text-xs text-gray-400">No pools yet</p>
              ) : (
                <ul className="space-y-1 max-h-40 overflow-y-auto">
                  {pools.map((p) => (
                    <li key={p.id}>
                      <button
                        onClick={() => handleAddToPool(p.id)}
                        disabled={addingToPool === p.id}
                        className="w-full text-left text-sm px-2 py-1.5 hover:bg-indigo-50 rounded-md disabled:opacity-50 flex items-center justify-between"
                      >
                        <span className="truncate">{p.name}</span>
                        <span className="text-xs text-gray-400 ml-1 flex-shrink-0">
                          {p.candidate_count} 👥
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="p-3">
              <p className="text-xs font-semibold text-gray-600 mb-2">
                Create new pool
              </p>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Pool name"
                  value={newPoolName}
                  onChange={(e) => setNewPoolName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleCreateAndAdd();
                  }}
                  className="flex-1 border border-gray-300 rounded-md px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-400"
                />
                <button
                  onClick={handleCreateAndAdd}
                  disabled={!newPoolName.trim() || creatingPool}
                  className="px-2 py-1.5 bg-indigo-600 text-white text-xs rounded-md hover:bg-indigo-700 disabled:opacity-50"
                >
                  {creatingPool ? "…" : "+"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
