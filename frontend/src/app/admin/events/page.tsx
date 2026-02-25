"use client";

import { useEffect, useState } from "react";
import { adminAPI, getAdminSession } from "@/lib/adminAPI";
import type { PlatformEventItem } from "@/types/admin";

const EVENT_TYPES = [
  "admin_login",
  "admin_account_locked",
  "admin_created",
  "admin_updated",
  "admin_deleted",
  "user_deactivated",
  "company_status_updated",
  "announcement_sent",
  "groq_api_call",
  "error",
];

const ACTOR_ROLES = ["elite_admin", "admin", "superadmin"];

export default function AdminEventsPage() {
  const [events, setEvents] = useState<PlatformEventItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [eventType, setEventType] = useState("");
  const [actorRole, setActorRole] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const session = getAdminSession();
  const canExport = session?.role !== "elite_admin";

  async function load() {
    setLoading(true);
    setError("");
    try {
      const res = await adminAPI.listEvents({
        event_type: eventType || undefined,
        actor_role: actorRole || undefined,
        page,
        page_size: 50,
      });
      setEvents(res.items);
      setTotal(res.total);
    } catch {
      setError("Failed to load events");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setPage(1);
  }, [eventType, actorRole]);

  useEffect(() => {
    load();
  }, [page, eventType, actorRole]); // eslint-disable-line react-hooks/exhaustive-deps

  function exportCSV() {
    const headers = [
      "id",
      "event_type",
      "actor_role",
      "target_type",
      "target_id",
      "ip_address",
      "created_at",
    ];
    const rows = events.map((e) =>
      [
        e.id,
        e.event_type,
        e.actor_role ?? "",
        e.target_type ?? "",
        e.target_id ?? "",
        e.ip_address ?? "",
        e.created_at,
      ].join(",")
    );
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `platform-events-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  const totalPages = Math.max(1, Math.ceil(total / 50));

  const eventTypeColors: Record<string, string> = {
    admin_login: "text-emerald-400",
    admin_account_locked: "text-red-400",
    admin_created: "text-indigo-400",
    admin_updated: "text-sky-400",
    admin_deleted: "text-rose-400",
    user_deactivated: "text-amber-400",
    company_status_updated: "text-purple-400",
    announcement_sent: "text-teal-400",
    error: "text-red-300",
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Platform Event Log</h1>
          <p className="text-gray-400 text-sm mt-1">
            {total.toLocaleString()} events recorded
          </p>
        </div>
        {canExport && (
          <button
            onClick={exportCSV}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 rounded-lg text-sm font-medium transition-colors"
          >
            Export CSV
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <select
          value={eventType}
          onChange={(e) => setEventType(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Event Types</option>
          {EVENT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          value={actorRole}
          onChange={(e) => setActorRole(e.target.value)}
          className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Roles</option>
          {ACTOR_ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="p-3 rounded-lg bg-red-900/30 border border-red-700 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Events list */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Time</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Event Type</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Actor Role</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Target</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Details</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">IP</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i} className="border-b border-gray-800/50">
                  {Array.from({ length: 6 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-gray-800 rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : events.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                  No events found
                </td>
              </tr>
            ) : (
              events.map((e) => (
                <tr
                  key={e.id}
                  className="border-b border-gray-800/50 hover:bg-gray-800/20 transition-colors"
                >
                  <td className="px-4 py-2.5 text-gray-400 whitespace-nowrap text-xs">
                    {new Date(e.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`font-mono text-xs ${
                        eventTypeColors[e.event_type] ?? "text-gray-300"
                      }`}
                    >
                      {e.event_type}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-gray-400 text-xs capitalize">
                    {e.actor_role ?? "—"}
                  </td>
                  <td className="px-4 py-2.5 text-gray-400 text-xs">
                    {e.target_type
                      ? `${e.target_type}: ${e.target_id?.slice(0, 8) ?? ""}…`
                      : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-gray-500 text-xs max-w-[200px] truncate">
                    {e.details ? JSON.stringify(e.details) : "—"}
                  </td>
                  <td className="px-4 py-2.5 text-gray-500 text-xs font-mono">
                    {e.ip_address ?? "—"}
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
          Page {page} of {totalPages} · {total} events
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
