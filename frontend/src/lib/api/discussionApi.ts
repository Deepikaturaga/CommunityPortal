/**
 * Discussion & Moderation API client
 *
 * Auth transport: HTTP-only secure cookies (credentials: "include").
 * Never stores tokens in localStorage.
 * All errors are surfaced as typed ApiError / ValidationError objects.
 */
import type {
  CreateThreadRequest,
  CreateReplyRequest,
  Thread,
  Reply,
  ThreadListResponse,
  ReplyTreeResponse,
  ModerationRequest,
  ModerationResponse,
  ApiError,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";

// ─── HTTP helpers ────────────────────────────────────────────────────────────

class ApiClientError extends Error {
  constructor(
    public readonly statusCode: number,
    public readonly body: ApiError,
  ) {
    super(body.message);
    this.name = "ApiClientError";
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    ...init,
    credentials: "include", // HTTP-only cookie auth
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
  });

  if (!res.ok) {
    let body: ApiError;
    try {
      body = (await res.json()) as ApiError;
    } catch {
      body = {
        statusCode: res.status,
        error: res.statusText,
        message: res.statusText,
      };
    }
    throw new ApiClientError(res.status, body);
  }

  // 204 No Content
  if (res.status === 204) return undefined as unknown as T;

  return (await res.json()) as T;
}

function json(body: unknown): RequestInit {
  return { body: JSON.stringify(body) };
}

// ─── Discussion API ──────────────────────────────────────────────────────────

export const discussionApi = {
  /**
   * List threads with optional pagination and category filter.
   * AC-011.x
   */
  listThreads(params?: {
    page?: number;
    pageSize?: number;
    category?: string;
  }): Promise<ThreadListResponse> {
    const qs = new URLSearchParams();
    if (params?.page !== undefined) qs.set("page", String(params.page));
    if (params?.pageSize !== undefined)
      qs.set("pageSize", String(params.pageSize));
    if (params?.category) qs.set("category", params.category);
    const query = qs.toString() ? `?${qs.toString()}` : "";
    return request<ThreadListResponse>(`/threads${query}`);
  },

  /**
   * Fetch a single thread with its reply tree.
   * AC-012.x
   */
  getThread(threadId: string): Promise<ReplyTreeResponse> {
    return request<ReplyTreeResponse>(`/threads/${threadId}`);
  },

  /**
   * Create a new discussion thread.
   * AC-009.x
   */
  createThread(body: CreateThreadRequest): Promise<Thread> {
    return request<Thread>("/threads", {
      method: "POST",
      ...json(body),
    });
  },

  /**
   * Create a reply to a thread (top-level or nested).
   * AC-010.x
   */
  createReply(body: CreateReplyRequest): Promise<Reply> {
    return request<Reply>("/replies", {
      method: "POST",
      ...json(body),
    });
  },
};

// ─── Moderation API ──────────────────────────────────────────────────────────

export const moderationApi = {
  /**
   * Apply a moderation action to a thread or reply.
   * Requires moderator/admin role – enforced server-side.
   * AC-013.x, AC-014.x
   */
  moderate(body: ModerationRequest): Promise<ModerationResponse> {
    return request<ModerationResponse>("/moderation/actions", {
      method: "POST",
      ...json(body),
    });
  },
};

// Re-export error class for use in tests / components
export { ApiClientError };
export type { Thread, Reply, ThreadListResponse, ReplyTreeResponse };
