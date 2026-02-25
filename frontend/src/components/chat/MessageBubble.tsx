"use client";

import { useState } from "react";
import type { MessageOut } from "@/types/chat";

interface MessageBubbleProps {
  message: MessageOut;
  currentUserId: string;
  onReact: (messageId: string, emoji: string) => void;
  onReply: (message: MessageOut) => void;
  onEdit?: (messageId: string, newContent: string) => void;
  onDelete?: (messageId: string) => void;
  onReport?: (messageId: string, reason: string) => void;
}

const QUICK_EMOJIS = ["👍", "❤️", "😂", "😮", "😢", "🙏"];

function formatTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatSize(bytes: number | null) {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function MessageBubble({
  message,
  currentUserId,
  onReact,
  onReply,
  onEdit,
  onDelete,
  onReport,
}: MessageBubbleProps) {
  const isSent = message.sender_id === currentUserId;
  const [showActions, setShowActions] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editValue, setEditValue] = useState(message.content ?? "");
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [reportModal, setReportModal] = useState(false);
  const [reportReason, setReportReason] = useState("");

  function saveEdit() {
    if (editValue.trim() && onEdit) {
      onEdit(message.id, editValue.trim());
    }
    setEditMode(false);
  }

  function submitReport() {
    if (reportReason.length >= 10 && onReport) {
      onReport(message.id, reportReason);
    }
    setReportModal(false);
    setReportReason("");
  }

  if (message.is_deleted) {
    return (
      <div className={`flex ${isSent ? "justify-end" : "justify-start"} my-1 px-4`}>
        <span className="text-xs text-gray-400 italic px-3 py-1.5">
          Message deleted
        </span>
      </div>
    );
  }

  return (
    <div
      className={`flex ${isSent ? "justify-end" : "justify-start"} my-1 px-4 group`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => { setShowActions(false); setShowEmojiPicker(false); }}
    >
      <div className={`max-w-xs lg:max-w-md xl:max-w-lg relative`}>
        {/* Sender name (received only) */}
        {!isSent && (
          <p className="text-xs text-gray-500 mb-0.5 ml-1">{message.sender_name}</p>
        )}

        {/* Reply preview */}
        {message.reply_to && (
          <div
            className={`text-xs rounded-t-lg px-3 py-1.5 border-l-2 mb-0.5 ${
              isSent
                ? "bg-blue-700/50 border-blue-300 text-blue-100"
                : "bg-gray-200 border-gray-400 text-gray-600"
            }`}
          >
            <span className="font-medium">{message.reply_to.sender_name}</span>
            <p className="truncate opacity-80">{message.reply_to.content ?? "File"}</p>
          </div>
        )}

        {/* Bubble */}
        <div
          className={`rounded-2xl px-3 py-2 ${
            isSent
              ? "bg-blue-600 text-white rounded-br-sm"
              : "bg-gray-100 text-gray-900 rounded-bl-sm"
          }`}
        >
          {/* File attachment */}
          {message.message_type === "file" && message.file_url && (
            <a
              href={message.file_url}
              download={message.file_name ?? "file"}
              className={`flex items-center gap-2 text-sm underline ${
                isSent ? "text-blue-100" : "text-blue-600"
              }`}
            >
              <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="truncate max-w-[200px]">{message.file_name}</span>
              <span className="text-xs opacity-70 flex-shrink-0">{formatSize(message.file_size)}</span>
            </a>
          )}

          {/* Image */}
          {message.message_type === "image" && message.file_url && (
            <img
              src={message.file_url}
              alt={message.file_name ?? "image"}
              className="max-w-full rounded-lg max-h-48 object-contain"
            />
          )}

          {/* Text content (or edit mode) */}
          {message.message_type === "text" && (
            editMode ? (
              <div className="space-y-1.5">
                <textarea
                  className={`w-full text-sm rounded p-1 resize-none bg-transparent border ${
                    isSent ? "border-blue-400 text-white" : "border-gray-300 text-gray-900"
                  }`}
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  rows={2}
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); saveEdit(); }
                    if (e.key === "Escape") setEditMode(false);
                  }}
                />
                <div className="flex gap-1">
                  <button onClick={saveEdit} className="text-xs px-2 py-0.5 bg-white/20 rounded hover:bg-white/30">Save</button>
                  <button onClick={() => setEditMode(false)} className="text-xs px-2 py-0.5 opacity-70 hover:opacity-100">Cancel</button>
                </div>
              </div>
            ) : (
              <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>
            )
          )}
        </div>

        {/* Timestamp + read receipt */}
        <div className={`flex items-center gap-1 mt-0.5 ${isSent ? "justify-end" : "justify-start"}`}>
          <span className="text-xs text-gray-400">{formatTime(message.created_at)}</span>
          {message.is_edited && <span className="text-xs text-gray-400 italic">(edited)</span>}
          {isSent && (
            <span className={`text-xs ${message.read_by_count > 0 ? "text-blue-400" : "text-gray-400"}`}>
              {message.read_by_count > 0 ? "✓✓" : "✓"}
            </span>
          )}
        </div>

        {/* Reactions */}
        {message.reactions.length > 0 && (
          <div className={`flex flex-wrap gap-1 mt-1 ${isSent ? "justify-end" : "justify-start"}`}>
            {message.reactions.map((r) => (
              <button
                key={r.emoji}
                onClick={() => onReact(message.id, r.emoji)}
                className={`text-xs px-1.5 py-0.5 rounded-full border transition-colors ${
                  r.reacted
                    ? "bg-blue-100 border-blue-300 text-blue-700"
                    : "bg-gray-100 border-gray-200 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {r.emoji} {r.count}
              </button>
            ))}
          </div>
        )}

        {/* Hover action bar */}
        {showActions && !editMode && (
          <div
            className={`absolute ${isSent ? "right-0 -top-8" : "left-0 -top-8"} flex items-center gap-0.5 bg-white border border-gray-200 rounded-full shadow-md px-1 py-0.5 z-10`}
          >
            {/* Quick emoji reactions */}
            {showEmojiPicker ? (
              <>
                {QUICK_EMOJIS.map((e) => (
                  <button
                    key={e}
                    onClick={() => { onReact(message.id, e); setShowEmojiPicker(false); }}
                    className="w-7 h-7 text-sm hover:bg-gray-100 rounded-full flex items-center justify-center"
                  >
                    {e}
                  </button>
                ))}
                <button onClick={() => setShowEmojiPicker(false)} className="w-5 h-5 text-xs text-gray-400 hover:text-gray-600">✕</button>
              </>
            ) : (
              <>
                <button onClick={() => setShowEmojiPicker(true)} className="w-7 h-7 text-sm hover:bg-gray-100 rounded-full flex items-center justify-center" title="React">😊</button>
                <button onClick={() => onReply(message)} className="w-7 h-7 hover:bg-gray-100 rounded-full flex items-center justify-center text-gray-500" title="Reply">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" /></svg>
                </button>
                {isSent && onEdit && message.message_type === "text" && (
                  <button onClick={() => setEditMode(true)} className="w-7 h-7 hover:bg-gray-100 rounded-full flex items-center justify-center text-gray-500" title="Edit">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                  </button>
                )}
                {isSent && onDelete && (
                  <button onClick={() => onDelete(message.id)} className="w-7 h-7 hover:bg-red-50 rounded-full flex items-center justify-center text-red-400" title="Delete">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                )}
                {!isSent && onReport && (
                  <button onClick={() => setReportModal(true)} className="w-7 h-7 hover:bg-yellow-50 rounded-full flex items-center justify-center text-yellow-500" title="Report">
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                  </button>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Report modal */}
      {reportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-5 w-full max-w-sm shadow-xl">
            <h3 className="font-semibold text-gray-900 mb-3">Report Message</h3>
            <textarea
              className="w-full border rounded-lg p-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Describe the issue (min 10 characters)…"
              rows={3}
              value={reportReason}
              onChange={(e) => setReportReason(e.target.value)}
            />
            <div className="flex gap-2 mt-3">
              <button
                onClick={submitReport}
                disabled={reportReason.length < 10}
                className="flex-1 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm py-2 rounded-lg"
              >
                Report
              </button>
              <button
                onClick={() => setReportModal(false)}
                className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm py-2 rounded-lg"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
