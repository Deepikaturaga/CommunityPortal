/**
 * AC-015.x — Rate limiting tests (VER-020)
 *
 * AC-015.1  Thread creation is rate-limited; exceeding the limit → generic 429 "Too Many Requests"
 * AC-015.2  Reply creation is rate-limited; exceeding the limit → generic 429
 * AC-015.3  Rate-limit response body contains ONLY generic message (no retry-after details
 *           that could aid abuse, and no stack traces — OWASP A05)
 * AC-015.4  Requests within the rate-limit window succeed
 * AC-015.5  Rate-limit is per-resource-type (thread RL does not affect reply RL)
 * AC-015.6  ApiClientError with statusCode 429 is properly surfaced to the caller
 */

import { server } from "./mocks/server";
import { discussionApi, ApiClientError } from "@/lib/api/discussionApi";
import {
  resetRateLimits,
  THREAD_RATE_LIMIT,
  REPLY_RATE_LIMIT,
} from "./mocks/handlers";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  server.resetHandlers();
  resetRateLimits();
});
afterAll(() => server.close());

const VALID_THREAD = {
  title: "Rate limit test thread",
  body: "Body of rate-limit test thread.",
  category: "general" as const,
};

const VALID_REPLY = {
  threadId: "thread-1",
  body: "Rate limit test reply.",
};

describe("AC-015.x — Rate limiting", () => {
  describe("AC-015.1 — Thread creation rate limit", () => {
    it(`allows up to ${THREAD_RATE_LIMIT} thread creations`, async () => {
      for (let i = 0; i < THREAD_RATE_LIMIT; i++) {
        const result = await discussionApi.createThread(VALID_THREAD);
        expect(result.id).toBeDefined();
      }
    });

    it(`returns 429 on the ${THREAD_RATE_LIMIT + 1}th thread creation`, async () => {
      // Exhaust the limit
      for (let i = 0; i < THREAD_RATE_LIMIT; i++) {
        await discussionApi.createThread(VALID_THREAD);
      }

      await expect(discussionApi.createThread(VALID_THREAD)).rejects.toMatchObject({
        statusCode: 429,
      });
    });

    it("rate-limited thread creation throws ApiClientError", async () => {
      for (let i = 0; i < THREAD_RATE_LIMIT; i++) {
        await discussionApi.createThread(VALID_THREAD);
      }

      let thrown: unknown;
      try {
        await discussionApi.createThread(VALID_THREAD);
      } catch (e) {
        thrown = e;
      }
      expect(thrown).toBeInstanceOf(ApiClientError);
    });
  });

  describe("AC-015.2 — Reply creation rate limit", () => {
    it(`allows up to ${REPLY_RATE_LIMIT} reply creations`, async () => {
      for (let i = 0; i < REPLY_RATE_LIMIT; i++) {
        const result = await discussionApi.createReply(VALID_REPLY);
        expect(result.id).toBeDefined();
      }
    });

    it(`returns 429 on the ${REPLY_RATE_LIMIT + 1}th reply creation`, async () => {
      for (let i = 0; i < REPLY_RATE_LIMIT; i++) {
        await discussionApi.createReply(VALID_REPLY);
      }

      await expect(discussionApi.createReply(VALID_REPLY)).rejects.toMatchObject({
        statusCode: 429,
      });
    });
  });

  describe("AC-015.3 — Generic 429 response body (OWASP A05)", () => {
    it("rate-limit response body is generic — no retry-after timing or internal details", async () => {
      for (let i = 0; i < THREAD_RATE_LIMIT; i++) {
        await discussionApi.createThread(VALID_THREAD);
      }

      let thrown: ApiClientError | null = null;
      try {
        await discussionApi.createThread(VALID_THREAD);
      } catch (e) {
        if (e instanceof ApiClientError) thrown = e;
      }

      expect(thrown).not.toBeNull();
      expect(thrown!.statusCode).toBe(429);

      const { error: errField, message } = thrown!.body;

      // Must be the generic HTTP status phrase — no retry window, no user ID, no quota info
      expect(message).toBe("Too Many Requests");
      expect(errField).toBe("Too Many Requests");

      // Must not contain sensitive detail
      expect(message).not.toMatch(/retry/i);
      expect(message).not.toMatch(/window/i);
      expect(message).not.toMatch(/quota/i);
      expect(message).not.toMatch(/limit/i);
      expect(message).not.toMatch(/user/i);
    });

    it("rate-limit response body for replies is also generic", async () => {
      for (let i = 0; i < REPLY_RATE_LIMIT; i++) {
        await discussionApi.createReply(VALID_REPLY);
      }

      let thrown: ApiClientError | null = null;
      try {
        await discussionApi.createReply(VALID_REPLY);
      } catch (e) {
        if (e instanceof ApiClientError) thrown = e;
      }

      expect(thrown).not.toBeNull();
      expect(thrown!.statusCode).toBe(429);
      expect(thrown!.body.message).toBe("Too Many Requests");
    });
  });

  describe("AC-015.4 — Requests within the window succeed", () => {
    it("first thread creation is never rate-limited", async () => {
      const result = await discussionApi.createThread(VALID_THREAD);
      expect(result.status).toBe("visible");
    });

    it("first reply creation is never rate-limited", async () => {
      const result = await discussionApi.createReply(VALID_REPLY);
      expect(result.status).toBe("visible");
    });
  });

  describe("AC-015.5 — Rate limits are per resource type", () => {
    it("exhausting thread RL does not affect reply RL", async () => {
      // Exhaust thread limit
      for (let i = 0; i < THREAD_RATE_LIMIT; i++) {
        await discussionApi.createThread(VALID_THREAD);
      }
      // Thread RL is now exhausted
      await expect(discussionApi.createThread(VALID_THREAD)).rejects.toMatchObject({
        statusCode: 429,
      });

      // Reply RL is still fresh
      const reply = await discussionApi.createReply(VALID_REPLY);
      expect(reply.id).toBeDefined();
    });

    it("exhausting reply RL does not affect thread RL", async () => {
      // Exhaust reply limit
      for (let i = 0; i < REPLY_RATE_LIMIT; i++) {
        await discussionApi.createReply(VALID_REPLY);
      }
      await expect(discussionApi.createReply(VALID_REPLY)).rejects.toMatchObject({
        statusCode: 429,
      });

      // Thread RL is still fresh
      const thread = await discussionApi.createThread(VALID_THREAD);
      expect(thread.id).toBeDefined();
    });
  });

  describe("AC-015.6 — ApiClientError propagation", () => {
    it("surfaced 429 error has correct statusCode, error, and message properties", async () => {
      for (let i = 0; i < THREAD_RATE_LIMIT; i++) {
        await discussionApi.createThread(VALID_THREAD);
      }

      let thrown: ApiClientError | null = null;
      try {
        await discussionApi.createThread(VALID_THREAD);
      } catch (e) {
        if (e instanceof ApiClientError) thrown = e;
      }

      expect(thrown).toBeInstanceOf(ApiClientError);
      expect(thrown!.statusCode).toBe(429);
      expect(thrown!.body).toMatchObject({
        statusCode: 429,
        error: "Too Many Requests",
        message: "Too Many Requests",
      });
      expect(thrown!.message).toBe("Too Many Requests"); // Error.message
    });
  });
});
