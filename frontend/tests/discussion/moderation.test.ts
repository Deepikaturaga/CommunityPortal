/**
 * AC-013.x — Moderation action tests
 *
 * AC-013.1  Required fields (resourceType, resourceId, action) are enforced
 * AC-013.2  resourceType must be 'thread' or 'reply'; invalid → 422
 * AC-013.3  action must be 'hide', 'delete', or 'flag'; invalid → 422
 * AC-013.4  Valid hide action on thread → 200 with ModerationResponse shape
 * AC-013.5  Valid delete action on reply → 200 with ModerationResponse shape
 * AC-013.6  Valid flag action → 200 with ModerationResponse shape
 * AC-013.7  optional reason field is accepted
 */

import { server } from "./mocks/server";
import { http, HttpResponse } from "msw";
import { moderationApi } from "@/lib/api/discussionApi";
import { resetRateLimits } from "./mocks/handlers";

// Simulate moderator role via custom header (the real app uses cookies;
// the MSW handler checks x-user-role to simulate role-based responses)
function withModeratorRole(): RequestInit {
  return {}; // in real usage the cookie carries the role; MSW default grants moderator
}

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  server.resetHandlers();
  resetRateLimits();
});
afterAll(() => server.close());

// Helper: override MSW to simulate moderator role header
function useModerator(): void {
  server.use(
    http.post("/api/moderation/actions", async ({ request }) => {
      // Grant moderator for all tests in this describe unless overridden
      const body = await request.json() as Record<string, unknown>;
      const { resourceType, resourceId, action, reason } = body;

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

      return HttpResponse.json(
        {
          resourceType,
          resourceId,
          action,
          moderatorId: "moderator-1",
          performedAt: new Date().toISOString(),
          ...(reason ? { reason } : {}),
        },
        { status: 200 },
      );
    }),
  );
}

describe("AC-013.x — Moderation actions", () => {
  beforeEach(() => useModerator());

  describe("AC-013.1 — Required fields validation", () => {
    it("returns 422 when resourceType is missing", async () => {
      await expect(
        moderationApi.moderate({
          // @ts-expect-error intentionally omitting required field
          resourceId: "thread-1",
          action: "hide",
        }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "resourceType" }),
          ]),
        }),
      });
    });

    it("returns 422 when resourceId is missing", async () => {
      await expect(
        moderationApi.moderate({
          resourceType: "thread",
          // @ts-expect-error intentionally omitting required field
          action: "hide",
        }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "resourceId" }),
          ]),
        }),
      });
    });

    it("returns 422 when action is missing", async () => {
      await expect(
        moderationApi.moderate({
          resourceType: "thread",
          resourceId: "thread-1",
          // @ts-expect-error intentionally omitting required field
          action: undefined,
        }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "action" }),
          ]),
        }),
      });
    });
  });

  describe("AC-013.2 — resourceType enum validation", () => {
    it("returns 422 for invalid resourceType", async () => {
      await expect(
        moderationApi.moderate({
          // @ts-expect-error intentionally invalid enum
          resourceType: "comment",
          resourceId: "resource-1",
          action: "hide",
        }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "resourceType" }),
          ]),
        }),
      });
    });
  });

  describe("AC-013.3 — action enum validation", () => {
    it("returns 422 for invalid action", async () => {
      await expect(
        moderationApi.moderate({
          resourceType: "thread",
          resourceId: "thread-1",
          // @ts-expect-error intentionally invalid enum
          action: "ban",
        }),
      ).rejects.toMatchObject({
        statusCode: 422,
        body: expect.objectContaining({
          details: expect.arrayContaining([
            expect.objectContaining({ field: "action" }),
          ]),
        }),
      });
    });
  });

  describe("AC-013.4 — Hide thread action", () => {
    it("returns 200 with ModerationResponse shape on hide", async () => {
      const result = await moderationApi.moderate({
        resourceType: "thread",
        resourceId: "thread-1",
        action: "hide",
      });

      expect(result).toMatchObject({
        resourceType: "thread",
        resourceId: "thread-1",
        action: "hide",
        moderatorId: expect.any(String),
        performedAt: expect.any(String),
      });
    });
  });

  describe("AC-013.5 — Delete reply action", () => {
    it("returns 200 with ModerationResponse shape on delete", async () => {
      const result = await moderationApi.moderate({
        resourceType: "reply",
        resourceId: "reply-1",
        action: "delete",
      });

      expect(result).toMatchObject({
        resourceType: "reply",
        resourceId: "reply-1",
        action: "delete",
        moderatorId: expect.any(String),
        performedAt: expect.any(String),
      });
    });
  });

  describe("AC-013.6 — Flag action", () => {
    it("returns 200 with ModerationResponse shape on flag", async () => {
      const result = await moderationApi.moderate({
        resourceType: "thread",
        resourceId: "thread-1",
        action: "flag",
      });

      expect(result).toMatchObject({
        resourceType: "thread",
        resourceId: "thread-1",
        action: "flag",
        moderatorId: expect.any(String),
        performedAt: expect.any(String),
      });
    });
  });

  describe("AC-013.7 — Optional reason field", () => {
    it("accepts an optional reason without error", async () => {
      const result = await moderationApi.moderate({
        resourceType: "thread",
        resourceId: "thread-1",
        action: "hide",
        reason: "Violates community guidelines",
      });
      expect(result.action).toBe("hide");
    });
  });
});
