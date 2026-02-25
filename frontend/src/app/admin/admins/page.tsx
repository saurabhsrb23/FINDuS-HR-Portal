"use client";

import { useEffect, useState } from "react";
import { adminAPI, getAdminSession } from "@/lib/adminAPI";
import type { AdminRole, AdminUserResponse } from "@/types/admin";
import { useRouter } from "next/navigation";

const ROLE_LABEL: Record<AdminRole, string> = {
  elite_admin: "Elite Admin (View-Only)",
  admin: "Admin",
  superadmin: "Superadmin",
};

function extractErrorMsg(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })
    ?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { msg?: string }) => d.msg ?? "Validation error")
      .join(", ");
  }
  return typeof detail === "string" ? detail : "Request failed";
}

export default function AdminAdminsPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [session, setSession] = useState<ReturnType<typeof getAdminSession>>(null);

  useEffect(() => {
    setMounted(true);
    const s = getAdminSession();
    setSession(s);
    if (s && s.role !== "superadmin") {
      router.replace("/admin/dashboard");
    }
  }, [router]);

  const [admins, setAdmins] = useState<AdminUserResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{ id: string; email: string } | null>(null);
  const [deleteText, setDeleteText] = useState("");

  // Create form
  const [form, setForm] = useState({
    email: "",
    password: "",
    pin: "",
    full_name: "",
    role: "admin" as AdminRole,
  });
  const [creating, setCreating] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await adminAPI.listAdmins();
      setAdmins(data);
    } catch {
      setError("Failed to load admin users");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (form.pin.length !== 6) {
      setError("PIN must be exactly 6 digits");
      return;
    }
    setCreating(true);
    setError("");
    try {
      await adminAPI.createAdmin(form);
      setShowCreate(false);
      setForm({ email: "", password: "", pin: "", full_name: "", role: "admin" });
      await load();
    } catch (err: unknown) {
      setError(extractErrorMsg(err));
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete() {
    if (!confirmDelete || deleteText !== "DELETE") return;
    setDeleting(confirmDelete.id);
    try {
      await adminAPI.deleteAdmin(confirmDelete.id);
      setConfirmDelete(null);
      setDeleteText("");
      await load();
    } catch (err: unknown) {
      setError(extractErrorMsg(err));
    } finally {
      setDeleting(null);
    }
  }

  if (!mounted || session?.role !== "superadmin") {
    return null;
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Admin User Management</h1>
          <p className="text-gray-400 text-sm mt-1">Superadmin only — manage portal access</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors"
        >
          + New Admin
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <h2 className="text-white font-semibold text-lg mb-4">Create Admin User</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <input
                required
                placeholder="Full Name"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <input
                required
                type="email"
                placeholder="Email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <input
                required
                type="password"
                placeholder="Password (min 8 chars)"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <input
                required
                placeholder="6-digit PIN"
                maxLength={6}
                value={form.pin}
                onChange={(e) => setForm({ ...form, pin: e.target.value.replace(/\D/g, "") })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value as AdminRole })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="elite_admin">Elite Admin (View-Only)</option>
                <option value="admin">Admin</option>
              </select>
              <p className="text-gray-500 text-xs">Superadmin cannot be created via API</p>
              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  {creating ? "Creating…" : "Create"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete confirmation modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900 border border-red-800 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <h2 className="text-white font-semibold text-lg mb-2">Delete Admin User</h2>
            <p className="text-gray-300 text-sm mb-4">
              Type <span className="text-red-400 font-mono font-bold">DELETE</span> to confirm
              removing <strong>{confirmDelete.email}</strong>.
            </p>
            <input
              value={deleteText}
              onChange={(e) => setDeleteText(e.target.value)}
              placeholder="Type DELETE"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 mb-4"
            />
            <div className="flex gap-3">
              <button
                onClick={handleDelete}
                disabled={deleteText !== "DELETE" || !!deleting}
                className="flex-1 bg-red-700 hover:bg-red-600 disabled:opacity-40 text-white py-2 rounded-lg text-sm font-medium transition-colors"
              >
                {deleting ? "Deleting…" : "Delete"}
              </button>
              <button
                onClick={() => { setConfirmDelete(null); setDeleteText(""); }}
                className="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
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
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Last Login</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <tr key={i} className="border-b border-gray-800/50">
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-gray-800 rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : admins.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No admin users found
                </td>
              </tr>
            ) : (
              admins.map((a) => (
                <tr
                  key={a.id}
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
                >
                  <td className="px-4 py-3 text-white font-medium">{a.full_name}</td>
                  <td className="px-4 py-3 text-gray-300">{a.email}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded border ${
                        a.role === "superadmin"
                          ? "bg-purple-900/50 text-purple-300 border-purple-700"
                          : a.role === "admin"
                          ? "bg-indigo-900/50 text-indigo-300 border-indigo-700"
                          : "bg-gray-800 text-gray-400 border-gray-700"
                      }`}
                    >
                      {ROLE_LABEL[a.role]}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs ${a.is_active ? "text-emerald-400" : "text-red-400"}`}
                    >
                      {a.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {a.last_login_at
                      ? new Date(a.last_login_at).toLocaleString()
                      : "Never"}
                  </td>
                  <td className="px-4 py-3">
                    {a.id !== session?.admin_id && a.role !== "superadmin" && (
                      <button
                        onClick={() => setConfirmDelete({ id: a.id, email: a.email })}
                        className="text-xs text-red-400 hover:text-red-300 border border-red-800 hover:border-red-600 px-2 py-1 rounded transition-colors"
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
