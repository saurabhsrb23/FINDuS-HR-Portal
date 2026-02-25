"use client";

import { useEffect, useState } from "react";
import { chatAPI } from "@/lib/chatAPI";
import { getAdminSession } from "@/lib/adminAPI";
import type { AdminConversationOut, AdminReportOut, MessageOut } from "@/types/chat";

type Tab = "conversations" | "reports";

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    pending: "bg-yellow-900/40 text-yellow-400",
    reviewed: "bg-green-900/40 text-green-400",
    dismissed: "bg-gray-800 text-gray-400",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${map[status] ?? "bg-gray-800 text-gray-400"}`}>
      {status}
    </span>
  );
}

export default function AdminChatPage() {
  const [tab, setTab] = useState<Tab>("conversations");
  const [conversations, setConversations] = useState<AdminConversationOut[]>([]);
  const [reports, setReports] = useState<AdminReportOut[]>([]);
  const [stats, setStats] = useState<{ messages_today: number; unanswered_count: number } | null>(null);
  const [selectedConv, setSelectedConv] = useState<string | null>(null);
  const [convMessages, setConvMessages] = useState<MessageOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const session = getAdminSession();
  const canDelete = session?.role === "superadmin";
  const canManage = session?.role === "admin" || session?.role === "superadmin";

  useEffect(() => {
    loadData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  async function loadData() {
    setLoading(true);
    try {
      const [convData, reportData, statsData] = await Promise.all([
        chatAPI.adminListConversations(),
        chatAPI.adminGetReports(),
        chatAPI.adminGetStats(),
      ]);
      setConversations(convData.items);
      setReports(reportData.items);
      setStats(statsData);
    } catch (e: unknown) {
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  async function handleViewConv(convId: string) {
    setSelectedConv(convId);
    try {
      const msgs = await chatAPI.adminGetConversationMessages(convId);
      setConvMessages(msgs);
    } catch {
      setConvMessages([]);
    }
  }

  async function handleDeleteMessage(msgId: string) {
    if (!confirm("Permanently delete this message?")) return;
    try {
      await chatAPI.adminDeleteMessage(msgId);
      setConvMessages((prev) => prev.filter((m) => m.id !== msgId));
    } catch {
      // ignore
    }
  }

  async function handleUpdateReport(reportId: string, status: "reviewed" | "dismissed") {
    try {
      await chatAPI.adminUpdateReport(reportId, status);
      setReports((prev) =>
        prev.map((r) => (r.id === reportId ? { ...r, status } : r))
      );
    } catch {
      // ignore
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-800 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Chat Monitor</h1>
          <p className="text-gray-400 text-sm mt-0.5">Oversee conversations, reports, and moderation</p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      <div className="px-6 py-6 space-y-6">
        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-xl px-4 py-3 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Stats cards */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-gray-400 text-xs">Total Conversations</p>
              <p className="text-white text-2xl font-bold mt-1">{conversations.length}</p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-gray-400 text-xs">Messages Today</p>
              <p className="text-white text-2xl font-bold mt-1">{stats.messages_today}</p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-gray-400 text-xs">Unanswered</p>
              <p className="text-white text-2xl font-bold mt-1">{stats.unanswered_count}</p>
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <p className="text-gray-400 text-xs">Pending Reports</p>
              <p className="text-white text-2xl font-bold mt-1">
                {reports.filter((r) => r.status === "pending").length}
              </p>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-900 rounded-xl p-1 w-fit">
          {(["conversations", "reports"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                tab === t
                  ? "bg-indigo-600 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {t}
              {t === "reports" && reports.filter((r) => r.status === "pending").length > 0 && (
                <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-red-600 text-white rounded-full">
                  {reports.filter((r) => r.status === "pending").length}
                </span>
              )}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <svg className="w-8 h-8 animate-spin text-indigo-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : tab === "conversations" ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Conversation list */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-800">
                <p className="text-sm font-medium text-gray-300">All Conversations</p>
              </div>
              <div className="divide-y divide-gray-800 max-h-[600px] overflow-y-auto">
                {conversations.length === 0 ? (
                  <p className="text-center text-gray-500 text-sm py-8">No conversations</p>
                ) : (
                  conversations.map((conv) => (
                    <button
                      key={conv.id}
                      onClick={() => handleViewConv(conv.id)}
                      className={`w-full flex items-start gap-3 px-4 py-3 hover:bg-gray-800 transition-colors text-left ${
                        selectedConv === conv.id ? "bg-gray-800 border-l-2 border-indigo-500" : ""
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-white text-sm font-medium truncate">
                            {conv.title ?? `${conv.type} conversation`}
                          </span>
                          {conv.has_reports && (
                            <span className="flex-shrink-0 w-2 h-2 bg-red-500 rounded-full" title="Has reports" />
                          )}
                        </div>
                        <div className="flex items-center gap-3 text-xs text-gray-500">
                          <span className="capitalize">{conv.type}</span>
                          <span>{conv.participant_count} participants</span>
                          <span>{conv.message_count} messages</span>
                        </div>
                        <p className="text-xs text-gray-600 mt-0.5">{timeAgo(conv.created_at)}</p>
                      </div>
                      <svg className="w-4 h-4 text-gray-600 flex-shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  ))
                )}
              </div>
            </div>

            {/* Message viewer */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-800">
                <p className="text-sm font-medium text-gray-300">
                  {selectedConv ? "Conversation Messages" : "Select a conversation"}
                </p>
              </div>
              <div className="max-h-[600px] overflow-y-auto p-4 space-y-3">
                {!selectedConv ? (
                  <p className="text-center text-gray-600 text-sm py-8">
                    Click a conversation to view messages
                  </p>
                ) : convMessages.length === 0 ? (
                  <p className="text-center text-gray-600 text-sm py-8">No messages</p>
                ) : (
                  convMessages.map((msg) => (
                    <div
                      key={msg.id}
                      className="flex items-start gap-2 group"
                    >
                      <div className="w-7 h-7 rounded-full bg-indigo-800 text-indigo-200 text-xs flex items-center justify-center flex-shrink-0 font-medium">
                        {msg.sender_name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-baseline gap-2">
                          <span className="text-xs font-medium text-gray-300">{msg.sender_name}</span>
                          <span className="text-xs text-gray-600">{timeAgo(msg.created_at)}</span>
                        </div>
                        <p className={`text-sm mt-0.5 break-words ${msg.is_deleted ? "text-gray-600 italic" : "text-gray-200"}`}>
                          {msg.is_deleted
                            ? "Message deleted"
                            : msg.message_type === "file"
                            ? `📎 ${msg.file_name}`
                            : msg.content}
                        </p>
                      </div>
                      {canDelete && !msg.is_deleted && (
                        <button
                          onClick={() => handleDeleteMessage(msg.id)}
                          className="opacity-0 group-hover:opacity-100 p-1 text-red-500 hover:bg-red-900/30 rounded transition-opacity"
                          title="Delete message"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        ) : (
          /* Reports tab */
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-800">
              <p className="text-sm font-medium text-gray-300">Message Reports</p>
            </div>
            {reports.length === 0 ? (
              <p className="text-center text-gray-500 text-sm py-12">No reports</p>
            ) : (
              <div className="divide-y divide-gray-800">
                {reports.map((report) => (
                  <div key={report.id} className="px-5 py-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-medium text-gray-200">
                            {report.reporter_name}
                          </span>
                          <StatusBadge status={report.status} />
                          <span className="text-xs text-gray-600">{timeAgo(report.created_at)}</span>
                        </div>
                        <p className="text-sm text-gray-400 mb-1">
                          <span className="text-gray-500">Message: </span>
                          {report.message_content ?? "Deleted"}
                        </p>
                        <p className="text-sm text-gray-300">
                          <span className="text-gray-500">Reason: </span>
                          {report.reason}
                        </p>
                      </div>
                      {canManage && report.status === "pending" && (
                        <div className="flex gap-2 flex-shrink-0">
                          <button
                            onClick={() => handleUpdateReport(report.id, "reviewed")}
                            className="px-3 py-1.5 rounded-lg bg-green-900/40 hover:bg-green-800/60 text-green-400 text-xs font-medium transition-colors"
                          >
                            Reviewed
                          </button>
                          <button
                            onClick={() => handleUpdateReport(report.id, "dismissed")}
                            className="px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 text-xs font-medium transition-colors"
                          >
                            Dismiss
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
