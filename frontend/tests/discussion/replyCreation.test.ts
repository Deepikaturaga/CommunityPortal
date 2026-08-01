/**
 * AC-010.x — Reply creation validation tests
 *
 * AC-010.1  Required fields (threadId, body) are enforced; missing → 422
 * AC-010.2  Body length ≤ 10 000 chars; exceeding → 422
 * AC-010.3  threadId must reference an existing thread; invalid → 404
 * AC-010.4  parentReplyId is optional; if provided links nested reply
 * AC-010.5  Valid request → 201 with Reply response shape
 * AC-010.6  Unauthenticated request → 401
 */

import { server } from "./mocks/server";
import { http, HttpResponse } from "msw";
import { discussionApi } from "@/lib/api/discussionApi";
import { resetRateLimits } from "./mocks/handlers";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  server.resetHandlers();
  resetRateLimits();
});
afterAll(() => server.close());

describe("AC-010.x — Reply creation", () => {
  describe("AC-010.1 — Required fields validation", () => {
    it("returns 422 when threadId is missing", async () => {
      await expect(
        // @ts-expect-error intentionally omitting required field
        discussionApi.createReply({ body: "Some reply body" }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "threadId" }),
          ]),
        }),
      });
    });

    it("returns 422 when body is missing", async () => {
      await expect(
        // @ts-expect-error intentionally omitting required field
        discussionApi.createReply({ threadId: "thread-1" }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "body" }),
          ]),
        }),
      });
    });

    it("returns 422 when body is only whitespace", async () => {
      await expect(
        discussionApi.createReply({ threadId: "thread-1", body: "   " }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "body" }),
          ]),
        }),
      });
    });
  });

  describe("AC-010.2 — Body length validation", () => {
    it("returns 422 when body exceeds 10 000 characters", async () => {
      const longBody = "x".repeat(10_001);
      await expect(
        discussionApi.createReply({ threadId: "thread-1", body: longBody }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "body" }),
          ]),
        }),
      });
    });

    it("accepts body of exactly 10 000 characters", async () => {
      const maxBody = "x".repeat(10_000);
      const result = await discussionApi.createReply({
        threadId: "thread-1",
        body: maxBody,
      });
      expect(result.id).toBeDefined();
      expect(result.body).toBe(maxBody);
    });
  });

  describe("AC-010.3 — Thread existence validation", () => {
    it("returns 404 when referenced threadId does not exist", async () => {
      await expect(
        discussionApi.createReply({
          threadId: "thread-not-found",
          body: "Some reply",
        }),
      ).rejects.toMatchObject({ statusCode: 404 });
    });
  });

  describe("AC-010.4 — Nested replies (parentReplyId)", () => {
    it("creates a top-level reply when parentReplyId is omitted", async () => {
      const result = await discussionApi.createReply({
        threadId: "thread-1",
        body: "Top-level reply",
      });
      expect(result.parentReplyId).toBeNull();
    });

    it("creates a nested reply when parentReplyId is provided", async () => {
      const result = await discussionApi.createReply({
        threadId: "thread-1",
        body: "Nested reply",
        parentReplyId: "reply-1",
      });
      expect(result.parentReplyId).toBe("reply-1");
      expect(result.threadId).toBe("thread-1");
    });
  });

  describe("AC-010.5 — Successful reply creation response shape", () => {
    it("returns 201 with complete Reply shape", async () => {
      const result = await discussionApi.createReply({
        threadId: "thread-1",
        body: "Hello from a reply.",
      });

      expect(result).toMatchObject({
        id: expect.any(String),
        threadId: "thread-1",
        body: "Hello from a reply.",
        authorId: expect.any(String),
        parentReplyId: null,
        status: "visible",
        createdAt: expect.any(String),
        updatedAt: expect.any(String),
      });
    });
  });

  describe("AC-010.6 — Authentication required", () => {
    it("returns 401 when cookie session is missing", async () => {
      server.use(
        http.post("/api/replies", () =>
          HttpResponse.json(
            { statusCode: 401, error: "Unauthorized", message: "Authentication required" },
            { status: 401 },
          ),
        ),
      );

      await expect(
        discussionApi.createReply({ threadId: "thread-1", body: "Hello" }),
      ).rejects.toMatchObject({ statusCode: 401 });
    });
  });
});
