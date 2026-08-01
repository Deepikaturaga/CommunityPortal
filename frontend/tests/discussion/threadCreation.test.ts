/**
 * AC-009.x — Thread creation validation tests
 *
 * AC-009.1  Required fields (title, body, category) are enforced; missing fields → 422
 * AC-009.2  Title length ≤ 200 chars; exceeding → 422 with field-level error
 * AC-009.3  Category must be one of the allowed enum values; invalid → 422
 * AC-009.4  Valid request → 201 with Thread response shape
 * AC-009.5  Unauthenticated request → 401 (cookie-based auth)
 */

import { server } from "./mocks/server";
import { http, HttpResponse } from "msw";
import { discussionApi, ApiClientError } from "@/lib/api/discussionApi";
import { resetRateLimits } from "./mocks/handlers";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  server.resetHandlers();
  resetRateLimits();
});
afterAll(() => server.close());

describe("AC-009.x — Thread creation", () => {
  describe("AC-009.1 — Required fields validation", () => {
    it("returns 422 when title is missing", async () => {
      await expect(
        // @ts-expect-error intentionally omitting required field
        discussionApi.createThread({ body: "Some body", category: "general" }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "title" }),
          ]),
        }),
      });
    });

    it("returns 422 when body is missing", async () => {
      await expect(
        // @ts-expect-error intentionally omitting required field
        discussionApi.createThread({ title: "A Title", category: "general" }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "body" }),
          ]),
        }),
      });
    });

    it("returns 422 when category is missing", async () => {
      await expect(
        // @ts-expect-error intentionally omitting required field
        discussionApi.createThread({ title: "A Title", body: "Some body" }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "category" }),
          ]),
        }),
      });
    });

    it("returns 422 when title is empty string", async () => {
      await expect(
        discussionApi.createThread({
          title: "   ",
          body: "Some body",
          category: "general",
        }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "title" }),
          ]),
        }),
      });
    });

    it("returns 422 when body is empty string", async () => {
      await expect(
        discussionApi.createThread({
          title: "A Title",
          body: "   ",
          category: "general",
        }),
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

  describe("AC-009.2 — Title length validation", () => {
    it("returns 422 when title exceeds 200 characters", async () => {
      const longTitle = "a".repeat(201);
      await expect(
        discussionApi.createThread({
          title: longTitle,
          body: "Some body",
          category: "general",
        }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "title" }),
          ]),
        }),
      });
    });

    it("accepts title of exactly 200 characters", async () => {
      const maxTitle = "a".repeat(200);
      const result = await discussionApi.createThread({
        title: maxTitle,
        body: "Some body",
        category: "general",
      });
      expect(result.id).toBeDefined();
      expect(result.title).toBe(maxTitle);
    });
  });

  describe("AC-009.3 — Category enum validation", () => {
    it("returns 422 for an invalid category", async () => {
      await expect(
        discussionApi.createThread({
          title: "A Title",
          body: "Some body",
          // @ts-expect-error intentionally invalid enum value
          category: "invalid-category",
        }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "category" }),
          ]),
        }),
      });
    });

    it.each(["general", "announcements", "help", "feedback", "off-topic"] as const)(
      "accepts valid category '%s'",
      async (category) => {
        const result = await discussionApi.createThread({
          title: "A Title",
          body: "Some body",
          category,
        });
        expect(result.category).toBe(category);
      },
    );
  });

  describe("AC-009.4 — Successful thread creation response shape", () => {
    it("returns 201 with complete Thread shape on valid request", async () => {
      const result = await discussionApi.createThread({
        title: "Hello World",
        body: "My first thread.",
        category: "general",
      });

      expect(result).toMatchObject({
        id: expect.any(String),
        title: "Hello World",
        body: "My first thread.",
        category: "general",
        authorId: expect.any(String),
        status: "visible",
        replyCount: 0,
        createdAt: expect.any(String),
        updatedAt: expect.any(String),
      });
    });
  });

  describe("AC-009.5 — Authentication required", () => {
    it("returns 401 when cookie session is missing", async () => {
      server.use(
        http.post("/api/threads", () =>
          HttpResponse.json(
            { statusCode: 401, error: "Unauthorized", message: "Authentication required" },
            { status: 401 },
          ),
        ),
      );

      await expect(
        discussionApi.createThread({
          title: "A Title",
          body: "Some body",
          category: "general",
        }),
      ).rejects.toMatchObject({ statusCode: 401 });
    });
  });
});
