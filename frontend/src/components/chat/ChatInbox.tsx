"use client";

import { useState } from "react";
import type { ConversationOut } from "@/types/chat";

interface ChatInboxProps {
  conversations: ConversationOut[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  currentUserId: string;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "now";
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d`;
  return new Date(iso).toLocaleDateString();
}

function truncate(text: string | null, max = 50): string {
  if (!text) return "";
  return text.length > max ? text.slice(0, max) + "…" : text;
}

export function ChatInbox({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  currentUserId,
}: ChatInboxProps) {
  const [search, setSearch] = useState("");

  const filtered = conversations.filter((c) => {
    const name =
      c.type === "direct"
        ? (c.other_participant?.name ?? "")
        : (c.title ?? "Group");
    return name.toLowerCase().includes(search.toLowerCase());
  });

  function getConvName(c: ConversationOut): string {
    if (c.type === "direct") return c.other_participant?.name ?? "Unknown";
    return c.title ?? (c.type === "broadcast" ? "Broadcast" : "Group Chat");
  }

  function getConvInitial(c: ConversationOut): string {
    return getConvName(c).charAt(0).toUpperCase();
  }

  function getAvatarColor(c: ConversationOut): string {
    const colors = [
      "bg-blue-500",
      "bg-green-500",
      "bg-purple-500",
      "bg-orange-500",
      "bg-pink-500",
      "bg-teal-500",
    ];
    const name = getConvName(c);
    const idx = name.charCodeAt(0) % colors.length;
    return colors[idx] ?? "bg-blue-500";
  }

  function getLastMsg(c: ConversationOut): string {
    const m = c.last_message;
    if (!m) return "No messages yet";
    if (m.is_deleted) return "Message deleted";
    if (m.message_type === "file") return `📎 ${m.file_name ?? "File"}`;
    if (m.message_type === "image") return "🖼 Image";
    const prefix =
      m.sender_id === currentUserId ? "You: " : `${m.sender_name.split(" ")[0]}: `;
    return prefix + truncate(m.content, 45);
  }

  return (
    <div className="flex flex-col h-full bg-white border-r border-gray-200">
      {/* Header */}
      <div className="px-4 py-4 border-b border-gray-100">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-gray-900 text-base">Messages</h2>
          <button
            onClick={onNewChat}
            className="w-8 h-8 rounded-full bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center transition-colors"
            title="New conversation"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search conversations…"
            className="w-full pl-9 pr-3 py-2 text-sm bg-gray-100 rounded-full border-0 focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <svg className="w-12 h-12 mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-sm">
              {search ? "No conversations found" : "No conversations yet"}
            </p>
            {!search && (
              <button
                onClick={onNewChat}
                className="mt-2 text-sm text-blue-600 hover:underline"
              >
                Start a new chat
              </button>
            )}
          </div>
        ) : (
          filtered.map((conv) => {
            const active = conv.id === activeId;
            return (
              <button
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors text-left border-b border-gray-50 ${
                  active ? "bg-blue-50 border-l-2 border-l-blue-500" : ""
                }`}
              >
                {/* Avatar */}
                <div className={`w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center text-white font-semibold text-sm ${getAvatarColor(conv)}`}>
                  {conv.type === "broadcast" ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
                    </svg>
                  ) : conv.type === "group" ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  ) : (
                    getConvInitial(conv)
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1">
                    <span className={`text-sm font-medium truncate ${active ? "text-blue-700" : "text-gray-900"}`}>
                      {getConvName(conv)}
                    </span>
                    <span className="text-xs text-gray-400 flex-shrink-0">
                      {conv.last_message ? timeAgo(conv.last_message.created_at) : ""}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-1 mt-0.5">
                    <p className="text-xs text-gray-500 truncate">{getLastMsg(conv)}</p>
                    {conv.unread_count > 0 && (
                      <span className="flex-shrink-0 min-w-[1.25rem] h-5 px-1.5 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center font-medium">
                        {conv.unread_count > 99 ? "99+" : conv.unread_count}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
