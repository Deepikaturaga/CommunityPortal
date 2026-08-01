/**
 * MSW v2 handler factory for discussion & moderation endpoints.
 * All handlers are stateless and deterministic for predictable test assertions.
 */
import { http, HttpResponse } from "msw";
import type {
  Thread,
  Reply,
  ThreadListResponse,
  ReplyTreeResponse,
  ModerationResponse,
  ApiError,
} from "../../../src/lib/api/types";

const BASE = "/api";

// ─── Seed data ───────────────────────────────────────────────────────────────

export const SEED_THREAD: Thread = {
  id: "thread-1",
  title: "Test Thread",
  body: "This is the body of the test thread.",
  category: "general",
  authorId: "user-1",
  status: "visible",
  replyCount: 2,
  createdAt: "2024-01-01T10:00:00Z",
  updatedAt: "2024-01-01T10:00:00Z",
};

export const SEED_REPLY: Reply = {
  id: "reply-1",
  threadId: "thread-1",
  body: "This is a reply.",
  authorId: "user-2",
  parentReplyId: null,
  status: "visible",
  createdAt: "2024-01-01T11:00:00Z",
  updatedAt: "2024-01-01T11:00:00Z",
};

export const SEED_REPLY_NESTED: Reply = {
  id: "reply-2",
  threadId: "thread-1",
  body: "This is a nested reply.",
  authorId: "user-3",
  parentReplyId: "reply-1",
  status: "visible",
  createdAt: "2024-01-01T12:00:00Z",
  updatedAt: "2024-01-01T12:00:00Z",
};

// ─── Rate-limit tracker (per-handler, resets between tests via resetRateLimit) ─
let threadCreationCount = 0;
let replyCreationCount = 0;

export const THREAD_RATE_LIMIT = 5; // max threads per "window" in tests
export const REPLY_RATE_LIMIT = 10; // max replies per "window" in tests

export function resetRateLimits(): void {
  threadCreationCount = 0;
  replyCreationCount = 0;
}

// ─── Handlers ────────────────────────────────────────────────────────────────

export const handlers = [
  // GET /api/threads  (AC-011.x — list + pagination)
  http.get(`${BASE}/threads`, ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get("page") ?? "1", 10);
    const pageSize = parseInt(url.searchParams.get("pageSize") ?? "20", 10);
    const category = url.searchParams.get("category");

    const allThreads: Thread[] = [
      SEED_THREAD,
      {
        ...SEED_THREAD,
        id: "thread-2",
        title: "Second Thread",
        category: "help",
      },
    ];

    const filtered = category
      ? allThreads.filter((t) => t.category === category)
      : allThreads;

    const start = (page - 1) * pageSize;
    const items = filtered.slice(start, start + pageSize);

    const body: ThreadListResponse = {
      items,
      total: filtered.length,
      page,
      pageSize,
    };
    return HttpResponse.json(body, { status: 200 });
  }),

  // GET /api/threads/:id  (AC-012.x — thread detail + reply tree)
  http.get(`${BASE}/threads/:threadId`, ({ params }) => {
    const { threadId } = params as { threadId: string };

    if (threadId === "thread-not-found") {
      const err: ApiError = {
        statusCode: 404,
        error: "Not Found",
        message: "Thread not found",
      };
      return HttpResponse.json(err, { status: 404 });
    }

    if (threadId === "thread-hidden") {
      const body: ReplyTreeResponse = {
        thread: { ...SEED_THREAD, id: "thread-hidden", status: "hidden" },
        replies: [],
      };
      return HttpResponse.json(body, { status: 200 });
    }

    const body: ReplyTreeResponse = {
      thread: { ...SEED_THREAD, id: threadId },
      replies: [SEED_REPLY, SEED_REPLY_NESTED],
    };
    return HttpResponse.json(body, { status: 200 });
  }),

  // POST /api/threads  (AC-009.x — thread creation + rate limiting AC-015.x)
  http.post(`${BASE}/threads`, async ({ request }) => {
    // Rate-limit check
    if (threadCreationCount >= THREAD_RATE_LIMIT) {
      // Generic 429 — no sensitive detail (OWASP: information exposure)
      return HttpResponse.json(
        { statusCode: 429, error: "Too Many Requests", message: "Too Many Requests" } as ApiError,
        { status: 429 },
      );
    }

    let body: unknown;
    try {
      body = await request.json();
    } catch {
      return HttpResponse.json(
        { statusCode: 400, error: "Bad Request", message: "Invalid JSON" } as ApiError,
        { status: 400 },
      );
    }

    const { title, body: postBody, category } = body as Record<string, unknown>;

    // Validate required fields (AC-009.1)
    const missingFields: string[] = [];
    if (!title || typeof title !== "string" || title.trim().length === 0)
      missingFields.push("title");
    if (!postBody || typeof postBody !== "string" || (postBody as string).trim().length === 0)
      missingFields.push("body");
    if (!category) missingFields.push("category");

    if (missingFields.length > 0) {
      return HttpResponse.json(
        {
          statusCode: 422,
          error: "Unprocessable Entity",
          message: "Validation failed",
          details: missingFields.map((f) => ({ field: f, message: `${f} is required` })),
        },
        { status: 422 },
      );
    }

    // Validate title length (AC-009.2)
    if ((title as string).length > 200) {
      return HttpResponse.json(
        {
          statusCode: 422,
          error: "Unprocessable Entity",
          message: "Validation failed",
          details: [{ field: "title", message: "title must be ≤200 characters" }],
        },
        { status: 422 },
      );
    }

    // Validate category enum (AC-009.3)
    const validCategories = ["general", "announcements", "help", "feedback", "off-topic"];
    if (!validCategories.includes(category as string)) {
      return HttpResponse.json(
        {
          statusCode: 422,
          error: "Unprocessable Entity",
          message: "Validation failed",
          details: [{ field: "category", message: "Invalid category" }],
        },
        { status: 422 },
      );
    }

    threadCreationCount++;

    const thread: Thread = {
      id: `thread-new-${threadCreationCount}`,
      title: title as string,
      body: postBody as string,
      category: category as Thread["category"],
      authorId: "user-current",
      status: "visible",
      replyCount: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    return HttpResponse.json(thread, { status: 201 });
  }),

  // POST /api/replies  (AC-010.x — reply creation + rate limiting AC-015.x)
  http.post(`${BASE}/replies`, async ({ request }) => {
    // Rate-limit check
    if (replyCreationCount >= REPLY_RATE_LIMIT) {
      return HttpResponse.json(
        { statusCode: 429, error: "Too Many Requests", message: "Too Many Requests" } as ApiError,
        { status: 429 },
      );
    }

    let body: unknown;
    try {
      body = await request.json();
    } catch {
      return HttpResponse.json(
        { statusCode: 400, error: "Bad Request", message: "Invalid JSON" } as ApiError,
        { status: 400 },
      );
    }

    const { threadId, body: replyBody, parentReplyId } = body as Record<string, unknown>;

    // Validate required fields (AC-010.1)
    const missingFields: string[] = [];
    if (!threadId || typeof threadId !== "string") missingFields.push("threadId");
    if (!replyBody || typeof replyBody !== "string" || (replyBody as string).trim().length === 0)
      missingFields.push("body");

    if (missingFields.length > 0) {
      return HttpResponse.json(
        {
          statusCode: 422,
          error: "Unprocessable Entity",
          message: "Validation failed",
          details: missingFields.map((f) => ({ field: f, message: `${f} is required` })),
        },
        { status: 422 },
      );
    }

    // Validate body length (AC-010.2)
    if ((replyBody as string).length > 10_000) {
      return HttpResponse.json(
        {
          statusCode: 422,
          error: "Unprocessable Entity",
          message: "Validation failed",
          details: [{ field: "body", message: "body must be ≤10000 characters" }],
        },
        { status: 422 },
      );
    }

    // Validate thread exists (AC-010.3)
    if (threadId === "thread-not-found") {
      return HttpResponse.json(
        { statusCode: 404, error: "Not Found", message: "Thread not found" } as ApiError,
        { status: 404 },
      );
    }

    replyCreationCount++;

    const reply: Reply = {
      id: `reply-new-${replyCreationCount}`,
      threadId: threadId as string,
      body: replyBody as string,
      authorId: "user-current",
      parentReplyId: (parentReplyId as string | null | undefined) ?? null,
      status: "visible",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    return HttpResponse.json(reply, { status: 201 });
  }),

  // POST /api/moderation/actions  (AC-013.x, AC-014.x)
  http.post(`${BASE}/moderation/actions`, async ({ request }) => {
    // Check moderator auth header (simulated via x-user-role)
    const role = request.headers.get("x-user-role");

    if (!role || !["moderator", "admin"].includes(role)) {
      return HttpResponse.json(
        { statusCode: 403, error: "Forbidden", message: "Insufficient permissions" } as ApiError,
        { status: 403 },
      );
    }

    let body: unknown;
    try {
      body = await request.json();
    } catch {
      return HttpResponse.json(
        { statusCode: 400, error: "Bad Request", message: "Invalid JSON" } as ApiError,
        { status: 400 },
      );
    }

    const { resourceType, resourceId, action } = body as Record<string, unknown>;

    // Validate required fields (AC-013.1)
    const missingFields: string[] = [];
    if (!resourceType) missingFields.push("resourceType");
    if (!resourceId) missingFields.push("resourceId");
    if (!action) missingFields.push("action");

    if (missingFields.length > 0) {
      return HttpResponse.json(
        {
          statusCode: 422,
          error: "Unprocessable Entity",
          message: "Validation failed",
          details: missingFields.map((f) => ({ field: f, message: `${f} is required` })),
        },
        { status: 422 },
      );
    }

    // Validate resourceType (AC-013.2)
    if (!["thread", "reply"].includes(resourceType as string)) {
      return HttpResponse.json(
        {
          statusCode: 422,
          error: "Unprocessable Entity",
          message: "Validation failed",
          details: [{ field: "resourceType", message: "resourceType must be thread or reply" }],
        },
        { status: 422 },
      );
    }

    // Validate action (AC-013.3)
    if (!["hide", "delete", "flag"].includes(action as string)) {
      return HttpResponse.json(
        {
          statusCode: 422,
          error: "Unprocessable Entity",
          message: "Validation failed",
          details: [{ field: "action", message: "action must be hide, delete, or flag" }],
        },
        { status: 422 },
      );
    }

    const resp: ModerationResponse = {
      resourceType: resourceType as "thread" | "reply",
      resourceId: resourceId as string,
      action: action as ModerationResponse["action"],
      moderatorId: "moderator-1",
      performedAt: new Date().toISOString(),
    };
    return HttpResponse.json(resp, { status: 200 });
  }),
];
