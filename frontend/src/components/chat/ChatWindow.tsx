"use client";

import { useEffect, useRef, useState } from "react";
import type { ConversationOut, MessageOut } from "@/types/chat";
import { MessageBubble } from "./MessageBubble";
import { MessageInput } from "./MessageInput";
import { TypingIndicator } from "./TypingIndicator";
import { chatAPI } from "@/lib/chatAPI";

interface ChatWindowProps {
  conversation: ConversationOut | null;
  messages: MessageOut[];
  typingUsers: string[];
  currentUserId: string;
  onSendMessage: (
    content: string,
    replyToId?: string,
    fileData?: { file_url: string; file_name: string; file_size: number; message_type: string }
  ) => void;
  onTyping: () => void;
  onEditMessage: (messageId: string, content: string) => void;
  onDeleteMessage: (messageId: string) => void;
  onReact: (messageId: string, emoji: string) => void;
}

export function ChatWindow({
  conversation,
  messages,
  typingUsers,
  currentUserId,
  onSendMessage,
  onTyping,
  onEditMessage,
  onDeleteMessage,
  onReact,
}: ChatWindowProps) {
  const [replyTo, setReplyTo] = useState<MessageOut | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const prevMsgCount = useRef(0);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > prevMsgCount.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
    prevMsgCount.current = messages.length;
  }, [messages.length]);

  // Scroll on initial load
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "auto" });
  }, [conversation?.id]);

  async function handleReport(messageId: string, reason: string) {
    try {
      await chatAPI.reportMessage(messageId, reason);
    } catch {
      // ignore
    }
  }

  if (!conversation) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 text-gray-400">
        <svg
          className="w-20 h-20 mb-4 opacity-20"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        <p className="text-base font-medium">Select a conversation</p>
        <p className="text-sm mt-1">Choose from the list or start a new chat</p>
      </div>
    );
  }

  function getTitle(): string {
    if (conversation!.type === "direct") {
      return conversation!.other_participant?.name ?? "Direct Message";
    }
    return conversation!.title ?? (conversation!.type === "broadcast" ? "Broadcast" : "Group Chat");
  }

  function getSubtitle(): string {
    if (conversation!.type === "direct") {
      const role = conversation!.other_participant?.role ?? "";
      return role.replace("_", " ");
    }
    return `${conversation!.participant_count} participants`;
  }

  function getAvatarLetter(): string {
    return getTitle().charAt(0).toUpperCase();
  }

  // Group consecutive messages from same sender
  function isSameSenderAsPrev(idx: number): boolean {
    if (idx === 0) return false;
    const prev = messages[idx - 1];
    const curr = messages[idx];
    if (!prev || !curr) return false;
    if (prev.sender_id !== curr.sender_id) return false;
    // Within 5 minutes
    const diff = new Date(curr.created_at).getTime() - new Date(prev.created_at).getTime();
    return diff < 5 * 60 * 1000;
  }

  // Date separator
  function shouldShowDate(idx: number): boolean {
    if (idx === 0) return true;
    const prev = messages[idx - 1];
    const curr = messages[idx];
    if (!prev || !curr) return false;
    return (
      new Date(prev.created_at).toDateString() !== new Date(curr.created_at).toDateString()
    );
  }

  function formatDateLabel(iso: string): string {
    const d = new Date(iso);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    if (d.toDateString() === today.toDateString()) return "Today";
    if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
    return d.toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" });
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-white">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 bg-white shadow-sm flex-shrink-0">
        <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
          {conversation.type === "broadcast" ? (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
            </svg>
          ) : conversation.type === "group" ? (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          ) : (
            getAvatarLetter()
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-900 text-sm truncate">{getTitle()}</p>
          <p className="text-xs text-gray-500 capitalize">{getSubtitle()}</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 py-16">
            <svg className="w-12 h-12 mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-sm">No messages yet. Say hello!</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={msg.id}>
              {shouldShowDate(idx) && (
                <div className="flex items-center gap-3 my-4">
                  <div className="flex-1 border-t border-gray-100" />
                  <span className="text-xs text-gray-400 px-2">{formatDateLabel(msg.created_at)}</span>
                  <div className="flex-1 border-t border-gray-100" />
                </div>
              )}
              <MessageBubble
                message={msg}
                currentUserId={currentUserId}
                onReply={(m) => setReplyTo(m)}
                onEdit={onEditMessage}
                onDelete={onDeleteMessage}
                onReact={onReact}
                onReport={handleReport}
              />
            </div>
          ))
        )}

        {/* Typing indicator */}
        {typingUsers.length > 0 && (
          <TypingIndicator names={typingUsers} />
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <MessageInput
        conversationId={conversation.id}
        replyTo={replyTo}
        onCancelReply={() => setReplyTo(null)}
        onSend={(content, replyToId, fileData) => {
          onSendMessage(content, replyToId, fileData);
          setReplyTo(null);
        }}
        onTyping={onTyping}
        disabled={conversation.is_archived}
      />
    </div>
  );
}
