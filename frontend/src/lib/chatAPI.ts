// Chat API client — Module 9
import axios from "axios";
import type {
  AdminConversationOut,
  AdminReportOut,
  ConversationOut,
  MessageCreate,
  MessageOut,
} from "@/types/chat";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

function chatAxios() {
  const token =
    typeof window !== "undefined" ? sessionStorage.getItem("token") : null;
  return axios.create({
    baseURL: BASE,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    withCredentials: true,
  });
}

export const chatAPI = {
  // ── Conversations ──────────────────────────────────────────────────────────
  getInbox: async (): Promise<ConversationOut[]> => {
    const { data } = await chatAxios().get<ConversationOut[]>("/chat/conversations");
    return data;
  },

  createOrGetConversation: async (payload: {
    participant_id?: string;
    type?: string;
    title?: string;
    company_id?: string;
  }): Promise<ConversationOut> => {
    const { data } = await chatAxios().post<ConversationOut>(
      "/chat/conversations",
      payload
    );
    return data;
  },

  getMessages: async (
    conversationId: string,
    beforeId?: string,
    limit = 50
  ): Promise<MessageOut[]> => {
    const params: Record<string, string | number> = { limit };
    if (beforeId) params.before_id = beforeId;
    const { data } = await chatAxios().get<MessageOut[]>(
      `/chat/conversations/${conversationId}/messages`,
      { params }
    );
    return data;
  },

  markRead: async (conversationId: string): Promise<void> => {
    await chatAxios().post(`/chat/conversations/${conversationId}/read`);
  },

  // ── Messages ───────────────────────────────────────────────────────────────
  sendMessage: async (payload: MessageCreate): Promise<MessageOut> => {
    const { data } = await chatAxios().post<MessageOut>("/chat/messages", payload);
    return data;
  },

  editMessage: async (messageId: string, content: string): Promise<MessageOut> => {
    const { data } = await chatAxios().patch<MessageOut>(
      `/chat/messages/${messageId}`,
      { content }
    );
    return data;
  },

  deleteMessage: async (messageId: string): Promise<void> => {
    await chatAxios().delete(`/chat/messages/${messageId}`);
  },

  reactToMessage: async (
    messageId: string,
    emoji: string
  ): Promise<import("@/types/chat").ReactionOut[]> => {
    const { data } = await chatAxios().post<import("@/types/chat").ReactionOut[]>(
      `/chat/messages/${messageId}/reactions`,
      { emoji }
    );
    return data;
  },

  // kept for compatibility
  addReaction: async (messageId: string, emoji: string): Promise<void> => {
    await chatAxios().post(`/chat/messages/${messageId}/reactions`, { emoji });
  },

  searchUsers: async (query: string): Promise<{ id: string; full_name: string; role: string }[]> => {
    const { data } = await chatAxios().get("/chat/users/search", { params: { q: query } });
    return data;
  },

  getOrCreateDirect: async (participantId: string): Promise<import("@/types/chat").ConversationOut> => {
    const { data } = await chatAxios().post<import("@/types/chat").ConversationOut>(
      "/chat/conversations",
      { participant_id: participantId, type: "direct" }
    );
    return data;
  },

  reportMessage: async (messageId: string, reason: string): Promise<void> => {
    await chatAxios().post(`/chat/messages/${messageId}/report`, { reason });
  },

  uploadFile: async (
    file: File
  ): Promise<{
    file_url: string;
    file_name: string;
    file_size: number;
    message_type: string;
  }> => {
    const form = new FormData();
    form.append("file", file);
    const { data } = await chatAxios().post("/chat/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  getUnreadCount: async (): Promise<number> => {
    const { data } = await chatAxios().get<{ unread: number }>("/chat/unread");
    return data.unread;
  },

  // ── Admin ──────────────────────────────────────────────────────────────────
  adminListConversations: async (
    page = 1
  ): Promise<{ items: AdminConversationOut[]; total: number }> => {
    const { data } = await chatAxios().get("/admin/chat/conversations", {
      params: { page, page_size: 50 },
      headers: {
        Authorization: `Bearer ${
          typeof window !== "undefined"
            ? sessionStorage.getItem("admin_token") ?? ""
            : ""
        }`,
      },
    });
    return data;
  },

  adminGetConversationMessages: async (
    conversationId: string
  ): Promise<MessageOut[]> => {
    const { data } = await chatAxios().get<MessageOut[]>(
      `/admin/chat/conversations/${conversationId}/messages`,
      {
        headers: {
          Authorization: `Bearer ${
            typeof window !== "undefined"
              ? sessionStorage.getItem("admin_token") ?? ""
              : ""
          }`,
        },
      }
    );
    return data;
  },

  adminDeleteMessage: async (messageId: string): Promise<void> => {
    await chatAxios().delete(`/admin/chat/messages/${messageId}`, {
      headers: {
        Authorization: `Bearer ${
          typeof window !== "undefined"
            ? sessionStorage.getItem("admin_token") ?? ""
            : ""
        }`,
      },
    });
  },

  adminBanUser: async (
    userId: string,
    reason: string,
    bannedUntil?: string
  ): Promise<void> => {
    await chatAxios().post(
      "/admin/chat/bans",
      { user_id: userId, reason, banned_until: bannedUntil ?? null },
      {
        headers: {
          Authorization: `Bearer ${
            typeof window !== "undefined"
              ? sessionStorage.getItem("admin_token") ?? ""
              : ""
          }`,
        },
      }
    );
  },

  adminGetReports: async (
    page = 1
  ): Promise<{ items: AdminReportOut[]; total: number }> => {
    const { data } = await chatAxios().get("/admin/chat/reports", {
      params: { page, page_size: 50 },
      headers: {
        Authorization: `Bearer ${
          typeof window !== "undefined"
            ? sessionStorage.getItem("admin_token") ?? ""
            : ""
        }`,
      },
    });
    return data;
  },

  adminUpdateReport: async (
    reportId: string,
    status: "reviewed" | "dismissed"
  ): Promise<void> => {
    await chatAxios().patch(
      `/admin/chat/reports/${reportId}`,
      { status },
      {
        headers: {
          Authorization: `Bearer ${
            typeof window !== "undefined"
              ? sessionStorage.getItem("admin_token") ?? ""
              : ""
          }`,
        },
      }
    );
  },

  adminGetStats: async (): Promise<{
    messages_today: number;
    unanswered_count: number;
  }> => {
    const { data } = await chatAxios().get("/admin/chat/stats", {
      headers: {
        Authorization: `Bearer ${
          typeof window !== "undefined"
            ? sessionStorage.getItem("admin_token") ?? ""
            : ""
        }`,
      },
    });
    return data;
  },
};
