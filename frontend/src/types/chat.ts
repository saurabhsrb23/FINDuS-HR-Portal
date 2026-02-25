// Chat TypeScript types — Module 9

export type MessageType = "text" | "file" | "image" | "system";
export type ConversationType = "direct" | "group" | "broadcast";

export interface ReactionOut {
  emoji: string;
  count: number;
  reacted: boolean;
}

export interface ReplyPreview {
  id: string;
  sender_name: string;
  content: string | null;
  message_type: string;
}

export interface MessageOut {
  id: string;
  conversation_id: string;
  sender_id: string;
  sender_name: string;
  sender_role: string;
  content: string | null;
  message_type: MessageType;
  file_url: string | null;
  file_name: string | null;
  file_size: number | null;
  reply_to: ReplyPreview | null;
  is_edited: boolean;
  edited_at: string | null;
  is_deleted: boolean;
  reactions: ReactionOut[];
  read_by_count: number;
  is_read: boolean;
  created_at: string;
}

export interface ConversationOut {
  id: string;
  type: ConversationType;
  title: string | null;
  is_archived: boolean;
  participant_count: number;
  unread_count: number;
  last_message: MessageOut | null;
  other_participant: { id: string; name: string; role: string } | null;
  created_at: string;
  updated_at: string;
}

export interface MessageCreate {
  conversation_id: string;
  content?: string;
  message_type?: MessageType;
  file_url?: string;
  file_name?: string;
  file_size?: number;
  reply_to_id?: string;
}

export interface AdminConversationOut {
  id: string;
  type: string;
  title: string | null;
  participant_count: number;
  message_count: number;
  has_reports: boolean;
  created_at: string;
}

export interface AdminReportOut {
  id: string;
  message_id: string;
  message_content: string | null;
  reporter_name: string;
  reason: string;
  status: string;
  created_at: string;
}

export interface ChatWsEvent {
  event_type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}
