"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useChat } from "@/hooks/useChat";
import { ChatInbox } from "@/components/chat/ChatInbox";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { chatAPI } from "@/lib/chatAPI";
import type { ConversationOut, MessageOut } from "@/types/chat";

// ── New chat modal ────────────────────────────────────────────────────────────

interface UserSuggestion {
  id: string;
  full_name: string;
  role: string;
}

interface NewChatModalProps {
  onClose: () => void;
  onCreated: (conv: ConversationOut) => void;
}

function NewChatModal({ onClose, onCreated }: NewChatModalProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<UserSuggestion[]>([]);
  const [searching, setSearching] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (!query.trim()) { setResults([]); return; }
    timerRef.current = setTimeout(async () => {
      setSearching(true);
      setError(null);
      try {
        const data = await chatAPI.searchUsers(query);
        setResults(data);
      } catch {
        setResults([]);
      } finally {
        setSearching(false);
      }
    }, 350);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [query]);

  async function handleSelect(userId: string) {
    if (selecting) return;
    setSelecting(true);
    setError(null);
    try {
      const conv = await chatAPI.getOrCreateDirect(userId);
      onCreated(conv);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Failed to open conversation. Please try again.";
      setError(msg);
    } finally {
      setSelecting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">New Conversation</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-5">
          <div className="relative">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              autoFocus
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by name or email…"
              className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          {error && (
            <p className="mt-2 text-xs text-red-500 text-center">{error}</p>
          )}

          <div className="mt-3 max-h-64 overflow-y-auto">
            {searching && (
              <p className="text-center text-sm text-gray-400 py-6">Searching…</p>
            )}
            {!searching && results.length === 0 && query.trim() && (
              <p className="text-center text-sm text-gray-400 py-6">No users found</p>
            )}
            {results.map((u) => (
              <button
                key={u.id}
                onClick={() => handleSelect(u.id)}
                disabled={selecting}
                className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-gray-50 rounded-xl transition-colors text-left disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <div className="w-9 h-9 rounded-full bg-blue-100 text-blue-700 font-semibold text-sm flex items-center justify-center flex-shrink-0">
                  {selecting ? (
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                  ) : (
                    u.full_name.charAt(0).toUpperCase()
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{u.full_name}</p>
                  <p className="text-xs text-gray-500 capitalize">{u.role.replace("_", " ")}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function MessagesPage() {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [showNewChat, setShowNewChat] = useState(false);

  // Decode current user from token
  const [currentUserId, setCurrentUserId] = useState("");

  useEffect(() => {
    try {
      const token = sessionStorage.getItem("token") ?? "";
      const payload = JSON.parse(atob(token.split(".")[1] ?? ""));
      setCurrentUserId(payload.sub ?? "");
    } catch {
      // ignore
    }
  }, []);

  const {
    conversations,
    messages,
    typingUsers,
    connected,
    sendMessage,
    sendTyping,
    refreshInbox,
    setMessages,
  } = useChat(activeId ?? undefined);

  const activeConv = conversations.find((c) => c.id === activeId) ?? null;

  function handleSelectConv(id: string) {
    setActiveId(id);
  }

  async function handleNewChatCreated(conv: ConversationOut) {
    setShowNewChat(false);
    await refreshInbox();
    setActiveId(conv.id);
  }

  async function handleSendMessage(
    content: string,
    replyToId?: string,
    fileData?: { file_url: string; file_name: string; file_size: number; message_type: string }
  ) {
    if (!activeId) return;
    if (fileData) {
      try {
        const msg = await chatAPI.sendMessage({
          conversation_id: activeId,
          content: content || undefined,
          file_url: fileData.file_url,
          file_name: fileData.file_name,
          file_size: fileData.file_size,
          message_type: fileData.message_type as "file" | "image",
          reply_to_id: replyToId,
        });
        setMessages((prev) => [...prev, msg]);
      } catch {
        // ignore
      }
    } else {
      await sendMessage(activeId, content, replyToId);
    }
  }

  async function handleEditMessage(messageId: string, content: string) {
    try {
      const updated = await chatAPI.editMessage(messageId, content);
      setMessages((prev) => prev.map((m) => (m.id === messageId ? updated : m)));
    } catch {
      // ignore
    }
  }

  async function handleDeleteMessage(messageId: string) {
    try {
      await chatAPI.deleteMessage(messageId);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId ? { ...m, is_deleted: true, content: null } : m
        )
      );
    } catch {
      // ignore
    }
  }

  async function handleReact(messageId: string, emoji: string) {
    try {
      const updated = await chatAPI.reactToMessage(messageId, emoji);
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? { ...m, reactions: updated } : m))
      );
    } catch {
      // ignore
    }
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-200 bg-white flex-shrink-0">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-bold text-gray-900">Messages</h1>
          <span
            className={`w-2 h-2 rounded-full ${connected ? "bg-green-400" : "bg-gray-300"}`}
            title={connected ? "Connected" : "Disconnected"}
          />
        </div>
      </div>

      {/* Split panel */}
      <div className="flex flex-1 min-h-0">
        {/* Inbox — fixed width */}
        <div className="w-80 flex-shrink-0 min-h-0">
          <ChatInbox
            conversations={conversations}
            activeId={activeId}
            onSelect={handleSelectConv}
            onNewChat={() => setShowNewChat(true)}
            currentUserId={currentUserId}
          />
        </div>

        {/* Chat thread */}
        <ChatWindow
          conversation={activeConv}
          messages={messages}
          typingUsers={typingUsers}
          currentUserId={currentUserId}
          onSendMessage={handleSendMessage}
          onTyping={() => activeId && sendTyping(activeId)}
          onEditMessage={handleEditMessage}
          onDeleteMessage={handleDeleteMessage}
          onReact={handleReact}
        />
      </div>

      {showNewChat && (
        <NewChatModal
          onClose={() => setShowNewChat(false)}
          onCreated={handleNewChatCreated}
        />
      )}
    </div>
  );
}
