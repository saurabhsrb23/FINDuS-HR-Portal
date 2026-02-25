"use client";

import { useRef, useState } from "react";
import type { MessageOut } from "@/types/chat";
import { chatAPI } from "@/lib/chatAPI";

interface MessageInputProps {
  conversationId: string;
  replyTo: MessageOut | null;
  onCancelReply: () => void;
  onSend: (
    content: string,
    replyToId?: string,
    fileData?: { file_url: string; file_name: string; file_size: number; message_type: string }
  ) => void;
  onTyping: () => void;
  disabled?: boolean;
}

const EMOJI_LIST = [
  "😀","😂","😊","❤️","👍","🙏","💪","🔥","✅","🎉",
  "😢","😮","🤔","👏","💡","✨","🚀","⭐","😍","🤝",
];

export function MessageInput({
  conversationId,
  replyTo,
  onCancelReply,
  onSend,
  onTyping,
  disabled,
}: MessageInputProps) {
  const [text, setText] = useState("");
  const [showEmoji, setShowEmoji] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [filePreview, setFilePreview] = useState<{
    name: string;
    size: number;
    data?: { file_url: string; file_name: string; file_size: number; message_type: string };
  } | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleTextChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setText(e.target.value);
    onTyping();
    // Auto-resize
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
    }
  }

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const result = await chatAPI.uploadFile(file);
      setFilePreview({ name: file.name, size: file.size, data: result });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Upload failed";
      alert(msg);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function handleSend() {
    if (filePreview?.data) {
      onSend("", replyTo?.id, filePreview.data);
      setFilePreview(null);
    } else if (text.trim()) {
      onSend(text.trim(), replyTo?.id);
      setText("");
      if (textareaRef.current) textareaRef.current.style.height = "auto";
    }
    setShowEmoji(false);
  }

  const canSend = !disabled && !uploading && (text.trim().length > 0 || !!filePreview?.data);

  return (
    <div className="border-t border-gray-200 bg-white">
      {/* Reply preview */}
      {replyTo && (
        <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 border-b border-blue-100">
          <div className="flex-1 text-xs">
            <span className="font-medium text-blue-700">{replyTo.sender_name}</span>
            <p className="text-gray-500 truncate">{replyTo.content ?? "File"}</p>
          </div>
          <button
            onClick={onCancelReply}
            className="text-gray-400 hover:text-gray-600 p-0.5"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* File preview */}
      {filePreview && (
        <div className="flex items-center gap-2 px-4 py-2 bg-gray-50 border-b border-gray-200">
          <svg className="w-4 h-4 text-blue-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-sm text-gray-700 flex-1 truncate">{filePreview.name}</span>
          <span className="text-xs text-gray-400">{Math.round(filePreview.size / 1024)} KB</span>
          <button onClick={() => setFilePreview(null)} className="text-red-400 hover:text-red-600">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      <div className="flex items-end gap-2 px-3 py-3">
        {/* File attach */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading || disabled}
          className="text-gray-400 hover:text-blue-500 p-1.5 rounded-full hover:bg-gray-100 flex-shrink-0 disabled:opacity-40"
          title="Attach file"
        >
          {uploading ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
          )}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf,image/jpeg,image/png,image/gif,image/webp"
          className="hidden"
          onChange={handleFileSelect}
        />

        {/* Emoji picker */}
        <div className="relative flex-shrink-0">
          <button
            onClick={() => setShowEmoji((v) => !v)}
            className="text-gray-400 hover:text-yellow-500 p-1.5 rounded-full hover:bg-gray-100"
            title="Emoji"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
          {showEmoji && (
            <div className="absolute bottom-10 left-0 bg-white border border-gray-200 rounded-xl shadow-xl p-2 z-20 w-56">
              <div className="grid grid-cols-5 gap-1">
                {EMOJI_LIST.map((e) => (
                  <button
                    key={e}
                    onClick={() => {
                      setText((t) => t + e);
                      setShowEmoji(false);
                      textareaRef.current?.focus();
                    }}
                    className="w-9 h-9 text-lg hover:bg-gray-100 rounded-lg flex items-center justify-center"
                  >
                    {e}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Text area */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={handleTextChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Type a message… (Enter to send, Shift+Enter for newline)"
          maxLength={2000}
          rows={1}
          className="flex-1 resize-none rounded-2xl border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 max-h-30 overflow-y-auto"
          style={{ lineHeight: "1.5" }}
        />

        {/* Character counter */}
        {text.length > 1800 && (
          <span className="text-xs text-red-400 flex-shrink-0">{2000 - text.length}</span>
        )}

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={!canSend}
          className="flex-shrink-0 w-9 h-9 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-full flex items-center justify-center transition-colors"
          title="Send (Enter)"
        >
          <svg className="w-4 h-4 rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
    </div>
  );
}
