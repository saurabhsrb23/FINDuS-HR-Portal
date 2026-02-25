"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { chatAPI } from "@/lib/chatAPI";
import type { ConversationOut, MessageOut } from "@/types/chat";

const WS_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8001")
    : "ws://localhost:8001";

export function useChat(activeConversationId?: string) {
  const [conversations, setConversations] = useState<ConversationOut[]>([]);
  const [messages, setMessages] = useState<MessageOut[]>([]);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  const [connected, setConnected] = useState(false);
  const [unreadTotal, setUnreadTotal] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const typingTimersRef = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const lastTypingSentRef = useRef(0);
  const activeConvRef = useRef(activeConversationId);
  activeConvRef.current = activeConversationId;

  const refreshInbox = useCallback(async () => {
    try {
      const data = await chatAPI.getInbox();
      setConversations(data);
      const total = data.reduce((s, c) => s + c.unread_count, 0);
      setUnreadTotal(total);
    } catch {
      // ignore
    }
  }, []);

  const loadMessages = useCallback(
    async (convId: string, beforeId?: string) => {
      try {
        const msgs = await chatAPI.getMessages(convId, beforeId);
        if (beforeId) {
          setMessages((prev) => [...msgs, ...prev]);
        } else {
          setMessages(msgs);
        }
      } catch {
        // ignore
      }
    },
    []
  );

  const sendMessage = useCallback(
    async (convId: string, content: string, replyToId?: string) => {
      // Optimistic message
      const tempId = `temp-${Date.now()}`;
      const token = sessionStorage.getItem("token");
      // Decode user id from token (JWT payload)
      let senderId = "";
      let senderName = "You";
      try {
        const payloadB64 = token?.split(".")[1] ?? "";
        const payload = JSON.parse(atob(payloadB64));
        senderId = payload.sub ?? "";
        senderName = payload.full_name ?? "You";
      } catch {
        // ignore
      }

      const optimistic: MessageOut = {
        id: tempId,
        conversation_id: convId,
        sender_id: senderId,
        sender_name: senderName,
        sender_role: "unknown",
        content,
        message_type: "text",
        file_url: null,
        file_name: null,
        file_size: null,
        reply_to: replyToId ? { id: replyToId, sender_name: "", content: null, message_type: "text" } : null,
        is_edited: false,
        edited_at: null,
        is_deleted: false,
        reactions: [],
        read_by_count: 0,
        is_read: false,
        created_at: new Date().toISOString(),
      };

      if (activeConvRef.current === convId) {
        setMessages((prev) => [...prev, optimistic]);
      }

      try {
        const real = await chatAPI.sendMessage({
          conversation_id: convId,
          content,
          reply_to_id: replyToId,
        });
        // Replace temp with real
        if (activeConvRef.current === convId) {
          setMessages((prev) =>
            prev.map((m) => (m.id === tempId ? real : m))
          );
        }
        setConversations((prev) =>
          prev.map((c) =>
            c.id === convId
              ? { ...c, last_message: real, unread_count: 0 }
              : c
          )
        );
      } catch {
        // Remove optimistic on error
        setMessages((prev) => prev.filter((m) => m.id !== tempId));
      }
    },
    []
  );

  const sendTyping = useCallback(
    (convId: string) => {
      const now = Date.now();
      if (now - lastTypingSentRef.current < 2000) return;
      lastTypingSentRef.current = now;
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ type: "typing", conversation_id: convId })
        );
      }
    },
    []
  );

  const markRead = useCallback(async (convId: string) => {
    try {
      await chatAPI.markRead(convId);
      // Send read event via WS too
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({ type: "read", conversation_id: convId })
        );
      }
      setConversations((prev) =>
        prev.map((c) =>
          c.id === convId ? { ...c, unread_count: 0 } : c
        )
      );
    } catch {
      // ignore
    }
  }, []);

  // ── WebSocket lifecycle ────────────────────────────────────────────────────

  const connect = useCallback(() => {
    const token =
      typeof window !== "undefined" ? sessionStorage.getItem("token") : null;
    if (!token) return;

    try {
      const ws = new WebSocket(`${WS_BASE}/ws/chat?token=${token}`);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        if (reconnectTimerRef.current) {
          clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = null;
        }
      };

      ws.onclose = () => {
        setConnected(false);
        wsRef.current = null;
        // Auto-reconnect after 3s
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };

      ws.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data as string);
          handleWsEvent(event);
        } catch {
          // ignore non-JSON
        }
      };
    } catch {
      // ignore connection errors
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function handleWsEvent(event: { event_type: string; payload: Record<string, unknown> }) {
    const { event_type, payload } = event;

    if (event_type === "chat_connected") {
      const unread = (payload.unread as number) ?? 0;
      setUnreadTotal(unread);
      refreshInbox();
      return;
    }

    if (event_type === "new_message") {
      const msg = payload as unknown as MessageOut;
      // Update messages if viewing this conversation
      if (activeConvRef.current === msg.conversation_id) {
        setMessages((prev) => {
          // Avoid duplicates (optimistic already there)
          const exists = prev.some((m) => m.id === msg.id);
          return exists ? prev.map((m) => (m.id === msg.id ? msg : m)) : [...prev, msg];
        });
      }
      // Update inbox
      setConversations((prev) =>
        prev.map((c) =>
          c.id === msg.conversation_id
            ? {
                ...c,
                last_message: msg,
                unread_count:
                  activeConvRef.current === c.id ? 0 : c.unread_count + 1,
              }
            : c
        )
      );
      setUnreadTotal((n) =>
        activeConvRef.current === msg.conversation_id ? n : n + 1
      );
      return;
    }

    if (event_type === "message_edited") {
      const msg = payload as unknown as MessageOut;
      setMessages((prev) => prev.map((m) => (m.id === msg.id ? msg : m)));
      return;
    }

    if (event_type === "message_deleted") {
      const messageId = payload.message_id as string;
      setMessages((prev) =>
        prev.map((m) =>
          m.id === messageId
            ? { ...m, is_deleted: true, content: null }
            : m
        )
      );
      return;
    }

    if (event_type === "reaction_updated") {
      const messageId = payload.message_id as string;
      const reactions = payload.reactions as MessageOut["reactions"];
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? { ...m, reactions } : m))
      );
      return;
    }

    if (event_type === "typing") {
      const convId = payload.conversation_id as string;
      const userName = payload.user_name as string;
      if (activeConvRef.current !== convId) return;

      setTypingUsers((prev) =>
        prev.includes(userName) ? prev : [...prev, userName]
      );
      // Clear after 3s
      if (typingTimersRef.current[userName]) {
        clearTimeout(typingTimersRef.current[userName]);
      }
      typingTimersRef.current[userName] = setTimeout(() => {
        setTypingUsers((prev) => prev.filter((n) => n !== userName));
        delete typingTimersRef.current[userName];
      }, 3000);
      return;
    }
  }

  useEffect(() => {
    connect();
    refreshInbox();

    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      wsRef.current?.close();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Load messages when active conversation changes
  useEffect(() => {
    if (activeConversationId) {
      setMessages([]);
      setTypingUsers([]);
      loadMessages(activeConversationId);
      markRead(activeConversationId);
    }
  }, [activeConversationId, loadMessages, markRead]);

  return {
    conversations,
    messages,
    typingUsers,
    connected,
    unreadTotal,
    loadMessages,
    sendMessage,
    sendTyping,
    markRead,
    refreshInbox,
    setMessages,
  };
}
