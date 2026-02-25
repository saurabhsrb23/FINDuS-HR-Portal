"use client";

import { useEffect, useState } from "react";
import { adminAPI } from "@/lib/adminAPI";
import type { CompanyListItem } from "@/types/admin";

function Badge({ active, label }: { active: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        active
          ? "bg-emerald-900/50 text-emerald-400 border border-emerald-700"
          : "bg-gray-800 text-gray-500 border border-gray-700"
      }`}
    >
      {label}
    </span>
  );
}

export default function AdminCompaniesPage() {
  const [companies, setCompanies] = useState<CompanyListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [updating, setUpdating] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const res = await adminAPI.listCompanies(page);
      setCompanies(res.items ?? []);
      setTotal(res.total ?? 0);
    } catch {
      setError("Failed to load companies");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [page]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleStatus(
    id: string,
    update: { is_verified?: boolean; is_active?: boolean }
  ) {
    setUpdating(id);
    setError("");
    try {
      await adminAPI.updateCompanyStatus(id, update);
      await load();
    } catch {
      setError("Failed to update company");
    } finally {
      setUpdating(null);
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / 20));

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Company Management</h1>
        <p className="text-gray-400 text-sm mt-1">
          {total.toLocaleString()} companies registered
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Company</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Industry</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">HR Email</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Verified</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Active</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Joined</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b border-gray-800/50">
                  {Array.from({ length: 7 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-gray-800 rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : companies.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                  No companies found
                </td>
              </tr>
            ) : (
              companies.map((c) => (
                <tr
                  key={c.id}
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div>
                      <p className="text-white font-medium">{c.name}</p>
                      {c.website && (
                        <p className="text-gray-500 text-xs truncate max-w-[160px]">
                          {c.website}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-300">{c.industry ?? "—"}</td>
                  <td className="px-4 py-3 text-gray-300">{c.hr_email ?? "—"}</td>
                  <td className="px-4 py-3">
                    <Badge active={c.is_verified} label={c.is_verified ? "Verified" : "Pending"} />
                  </td>
                  <td className="px-4 py-3">
                    <Badge active={c.is_active} label={c.is_active ? "Active" : "Suspended"} />
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {new Date(c.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1.5">
                      {!c.is_verified && (
                        <button
                          onClick={() => handleStatus(c.id, { is_verified: true })}
                          disabled={updating === c.id}
                          className="text-xs px-2 py-1 rounded bg-emerald-900/40 text-emerald-400 border border-emerald-800 hover:bg-emerald-900/70 disabled:opacity-50 transition-colors"
                        >
                          Verify
                        </button>
                      )}
                      {c.is_active ? (
                        <button
                          onClick={() => handleStatus(c.id, { is_active: false })}
                          disabled={updating === c.id}
                          className="text-xs px-2 py-1 rounded bg-red-900/40 text-red-400 border border-red-800 hover:bg-red-900/70 disabled:opacity-50 transition-colors"
                        >
                          Suspend
                        </button>
                      ) : (
                        <button
                          onClick={() => handleStatus(c.id, { is_active: true })}
                          disabled={updating === c.id}
                          className="text-xs px-2 py-1 rounded bg-sky-900/40 text-sky-400 border border-sky-800 hover:bg-sky-900/70 disabled:opacity-50 transition-colors"
                        >
                          Restore
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-gray-400">
        <span>
          Page {page} of {totalPages} · {total} results
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1.5 bg-gray-900 border border-gray-700 rounded-lg disabled:opacity-40 hover:bg-gray-800 transition-colors"
          >
            Prev
          </button>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1.5 bg-gray-900 border border-gray-700 rounded-lg disabled:opacity-40 hover:bg-gray-800 transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
