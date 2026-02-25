"use client";

import { useEffect, useState } from "react";
import { adminAPI } from "@/lib/adminAPI";
import { getAdminSession } from "@/lib/adminAPI";
import type { UserListItem } from "@/types/admin";

type Tab = "candidates" | "hr";

function StatusBadge({ active }: { active: boolean }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        active
          ? "bg-emerald-900/50 text-emerald-400 border border-emerald-700"
          : "bg-red-900/50 text-red-400 border border-red-700"
      }`}
    >
      {active ? "Active" : "Inactive"}
    </span>
  );
}

export default function AdminUsersPage() {
  const [tab, setTab] = useState<Tab>("candidates");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [deactivating, setDeactivating] = useState<string | null>(null);

  const session = getAdminSession();
  const canDeactivate =
    session?.role === "admin" || session?.role === "superadmin";

  async function load() {
    setLoading(true);
    setError("");
    try {
      const fn =
        tab === "candidates" ? adminAPI.listCandidates : adminAPI.listHrUsers;
      const res = await fn(search || undefined, page);
      setUsers(res.items);
      setTotal(res.total);
    } catch {
      setError("Failed to load users");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setPage(1);
  }, [tab, search]);

  useEffect(() => {
    load();
  }, [tab, page]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleDeactivate(userId: string, email: string) {
    if (!confirm(`Deactivate ${email}?`)) return;
    setDeactivating(userId);
    try {
      await adminAPI.deactivateUser(userId);
      await load();
    } catch {
      setError("Failed to deactivate user");
    } finally {
      setDeactivating(null);
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / 20));

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">User Management</h1>
        <p className="text-gray-400 text-sm mt-1">
          {total.toLocaleString()} users total
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1 w-fit">
        {(["candidates", "hr"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${
              tab === t
                ? "bg-indigo-600 text-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {t === "hr" ? "HR Users" : "Candidates"}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Search by name or email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
          className="flex-1 max-w-sm bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          onClick={load}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          Search
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Name</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Email</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Role</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Status</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Verified</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Joined</th>
              {canDeactivate && (
                <th className="text-left px-4 py-3 text-gray-400 font-medium">Action</th>
              )}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-b border-gray-800/50">
                  {Array.from({ length: canDeactivate ? 7 : 6 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-gray-800 rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : users.length === 0 ? (
              <tr>
                <td
                  colSpan={canDeactivate ? 7 : 6}
                  className="px-4 py-8 text-center text-gray-500"
                >
                  No users found
                </td>
              </tr>
            ) : (
              users.map((u) => (
                <tr
                  key={u.id}
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
                >
                  <td className="px-4 py-3 text-white font-medium">{u.full_name}</td>
                  <td className="px-4 py-3 text-gray-300">{u.email}</td>
                  <td className="px-4 py-3">
                    <span className="text-gray-300 capitalize">{u.role.replace("_", " ")}</span>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge active={u.is_active} />
                  </td>
                  <td className="px-4 py-3">
                    <span className={u.is_verified ? "text-emerald-400" : "text-gray-500"}>
                      {u.is_verified ? "✓" : "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  {canDeactivate && (
                    <td className="px-4 py-3">
                      {u.is_active && (
                        <button
                          onClick={() => handleDeactivate(u.id, u.email)}
                          disabled={deactivating === u.id}
                          className="text-xs text-red-400 hover:text-red-300 disabled:opacity-50 border border-red-800 hover:border-red-600 px-2 py-1 rounded transition-colors"
                        >
                          {deactivating === u.id ? "…" : "Deactivate"}
                        </button>
                      )}
                    </td>
                  )}
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
