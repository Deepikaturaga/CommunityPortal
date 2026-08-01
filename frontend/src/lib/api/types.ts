// ─── Domain types shared across discussion & moderation ─────────────────────
// These mirror the backend OpenAPI contract; do NOT hand-duplicate server enums.

export type ThreadCategory =
  | "general"
  | "announcements"
  | "help"
  | "feedback"
  | "off-topic";

export type ModerationAction = "hide" | "delete" | "flag";

export type ModerationStatus = "visible" | "hidden" | "deleted" | "flagged";

export type UserRole = "member" | "moderator" | "admin";

// ─── Request / Response shapes ───────────────────────────────────────────────

export interface CreateThreadRequest {
  title: string;
  body: string;
  category: ThreadCategory;
}

export interface CreateReplyRequest {
  threadId: string;
  body: string;
  parentReplyId?: string;
}

export interface Thread {
  id: string;
  title: string;
  body: string;
  category: ThreadCategory;
  authorId: string;
  status: ModerationStatus;
  replyCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface Reply {
  id: string;
  threadId: string;
  body: string;
  authorId: string;
  parentReplyId: string | null;
  status: ModerationStatus;
  createdAt: string;
  updatedAt: string;
}

export interface ThreadListResponse {
  items: Thread[];
  total: number;
  page: number;
  pageSize: number;
}

export interface ReplyTreeResponse {
  thread: Thread;
  replies: Reply[];
}

export interface ModerationRequest {
  resourceType: "thread" | "reply";
  resourceId: string;
  action: ModerationAction;
  reason?: string;
}

export interface ModerationResponse {
  resourceType: "thread" | "reply";
  resourceId: string;
  action: ModerationAction;
  moderatorId: string;
  performedAt: string;
}

// ─── Error envelope ──────────────────────────────────────────────────────────

export interface ApiError {
  statusCode: number;
  error: string;
  message: string;
}

export interface ValidationError extends ApiError {
  statusCode: 422;
  details: Array<{ field: string; message: string }>;
}
