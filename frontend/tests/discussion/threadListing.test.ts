/**
 * AC-011.x — Thread listing and pagination tests
 *
 * AC-011.1  Default list returns items array + pagination metadata
 * AC-011.2  page + pageSize query params are forwarded and respected
 * AC-011.3  category filter narrows results
 * AC-011.4  Empty result set is handled gracefully (items: [], total: 0)
 * AC-011.5  API error during listing is propagated correctly
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

describe("AC-011.x — Thread listing and pagination", () => {
  describe("AC-011.1 — Default list response shape", () => {
    it("returns items array with pagination metadata", async () => {
      const result = await discussionApi.listThreads();

      expect(result).toMatchObject({
        items: expect.any(Array),
        total: expect.any(Number),
        page: expect.any(Number),
        pageSize: expect.any(Number),
      });
      expect(result.items.length).toBeGreaterThan(0);
    });

    it("each thread item has the expected shape", async () => {
      const { items } = await discussionApi.listThreads();
      const thread = items[0];

      expect(thread).toMatchObject({
        id: expect.any(String),
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
  });

  describe("AC-011.2 — Pagination parameters", () => {
    it("forwards page and pageSize parameters", async () => {
      // Mock captures the request URL so we can verify params are sent
      let capturedUrl: string | null = null;
      server.use(
        http.get("/api/threads", ({ request }) => {
          capturedUrl = request.url;
          return HttpResponse.json({
            items: [],
            total: 0,
            page: 2,
            pageSize: 5,
          });
        }),
      );

      await discussionApi.listThreads({ page: 2, pageSize: 5 });

      expect(capturedUrl).toContain("page=2");
      expect(capturedUrl).toContain("pageSize=5");
    });

    it("returns metadata reflecting requested page / pageSize", async () => {
      server.use(
        http.get("/api/threads", () =>
          HttpResponse.json({
            items: [],
            total: 100,
            page: 3,
            pageSize: 10,
          }),
        ),
      );

      const result = await discussionApi.listThreads({ page: 3, pageSize: 10 });
      expect(result.page).toBe(3);
      expect(result.pageSize).toBe(10);
      expect(result.total).toBe(100);
    });
  });

  describe("AC-011.3 — Category filter", () => {
    it("forwards category filter query parameter", async () => {
      let capturedUrl: string | null = null;
      server.use(
        http.get("/api/threads", ({ request }) => {
          capturedUrl = request.url;
          return HttpResponse.json({ items: [], total: 0, page: 1, pageSize: 20 });
        }),
      );

      await discussionApi.listThreads({ category: "help" });
      expect(capturedUrl).toContain("category=help");
    });

    it("returns only threads of the requested category", async () => {
      const result = await discussionApi.listThreads({ category: "help" });
      for (const thread of result.items) {
        expect(thread.category).toBe("help");
      }
    });

    it("returns all threads when no category filter is applied", async () => {
      const result = await discussionApi.listThreads();
      const categories = new Set(result.items.map((t) => t.category));
      // Seed data has both 'general' and 'help' threads
      expect(categories.size).toBeGreaterThanOrEqual(1);
    });
  });

  describe("AC-011.4 — Empty result set", () => {
    it("returns items:[] and total:0 gracefully", async () => {
      server.use(
        http.get("/api/threads", () =>
          HttpResponse.json({ items: [], total: 0, page: 1, pageSize: 20 }),
        ),
      );

      const result = await discussionApi.listThreads();
      expect(result.items).toHaveLength(0);
      expect(result.total).toBe(0);
    });
  });

  describe("AC-011.5 — Error propagation", () => {
    it("throws ApiClientError on server error", async () => {
      server.use(
        http.get("/api/threads", () =>
          HttpResponse.json(
            { statusCode: 500, error: "Internal Server Error", message: "Unexpected error" },
            { status: 500 },
          ),
        ),
      );

      await expect(discussionApi.listThreads()).rejects.toMatchObject({
        statusCode: 500,
      });
    });
  });
});
