/**
 * AC-012.x — Thread detail and reply tree tests
 *
 * AC-012.1  Fetching a thread by ID returns thread + replies array
 * AC-012.2  Reply tree includes nested replies (parentReplyId linkage)
 * AC-012.3  Non-existent thread → 404
 * AC-012.4  Thread with hidden status is still returned (visibility enforcement is UI/server concern)
 * AC-012.5  Empty replies array is returned for thread with no replies
 */

import { server } from "./mocks/server";
import { http, HttpResponse } from "msw";
import { discussionApi } from "@/lib/api/discussionApi";
import { resetRateLimits, SEED_THREAD, SEED_REPLY, SEED_REPLY_NESTED } from "./mocks/handlers";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  server.resetHandlers();
  resetRateLimits();
});
afterAll(() => server.close());

describe("AC-012.x — Thread detail and reply tree", () => {
  describe("AC-012.1 — Thread detail response shape", () => {
    it("returns thread object with complete shape", async () => {
      const result = await discussionApi.getThread("thread-1");

      expect(result.thread).toMatchObject({
        id: "thread-1",
        title: expect.any(String),
        body: expect.any(String),
        category: expect.any(String),
        authorId: expect.any(String),
        status: expect.any(String),
        replyCount: expect.any(Number),
        createdAt: expect.any(String),
        updatedAt: expect.any(String),
      });
    });

    it("returns replies array alongside thread", async () => {
      const result = await discussionApi.getThread("thread-1");
      expect(Array.isArray(result.replies)).toBe(true);
    });
  });

  describe("AC-012.2 — Reply tree nesting", () => {
    it("includes both top-level and nested replies", async () => {
      const { replies } = await discussionApi.getThread("thread-1");

      const topLevel = replies.filter((r) => r.parentReplyId === null);
      const nested = replies.filter((r) => r.parentReplyId !== null);

      expect(topLevel.length).toBeGreaterThan(0);
      expect(nested.length).toBeGreaterThan(0);
    });

    it("nested reply's parentReplyId matches a top-level reply id", async () => {
      const { replies } = await discussionApi.getThread("thread-1");

      const topLevelIds = new Set(
        replies.filter((r) => r.parentReplyId === null).map((r) => r.id),
      );
      const nested = replies.filter((r) => r.parentReplyId !== null);

      for (const nestedReply of nested) {
        expect(topLevelIds.has(nestedReply.parentReplyId!)).toBe(true);
      }
    });

    it("replies include complete shape", async () => {
      const { replies } = await discussionApi.getThread("thread-1");
      const reply = replies[0];

      expect(reply).toMatchObject({
        id: expect.any(String),
        threadId: expect.any(String),
        body: expect.any(String),
        authorId: expect.any(String),
        status: expect.any(String),
        createdAt: expect.any(String),
        updatedAt: expect.any(String),
      });
      expect("parentReplyId" in reply).toBe(true);
    });
  });

  describe("AC-012.3 — Non-existent thread", () => {
    it("throws ApiClientError 404 for missing threadId", async () => {
      await expect(discussionApi.getThread("thread-not-found")).rejects.toMatchObject({
        statusCode: 404,
        body: expect.objectContaining({ message: expect.any(String) }),
      });
    });
  });

  describe("AC-012.4 — Hidden thread access", () => {
    it("returns thread with hidden status (enforcement is server/UI layer concern)", async () => {
      const result = await discussionApi.getThread("thread-hidden");
      expect(result.thread.status).toBe("hidden");
    });
  });

  describe("AC-012.5 — Thread with no replies", () => {
    it("returns empty replies array gracefully", async () => {
      server.use(
        http.get("/api/threads/:threadId", ({ params }) => {
          const { threadId } = params as { threadId: string };
          return HttpResponse.json({
            thread: { ...SEED_THREAD, id: threadId, replyCount: 0 },
            replies: [],
          });
        }),
      );

      const result = await discussionApi.getThread("thread-empty");
      expect(result.replies).toHaveLength(0);
      expect(result.thread.replyCount).toBe(0);
    });
  });
});
