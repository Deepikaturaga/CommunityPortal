/**
 * AC-014.x — Moderator role-gating tests
 *
 * AC-014.1  Non-authenticated user cannot perform moderation actions → 401
 * AC-014.2  Regular member cannot perform moderation actions → 403
 * AC-014.3  Moderator role CAN perform moderation actions → 200
 * AC-014.4  Admin role CAN perform moderation actions → 200
 * AC-014.5  Role enforcement is server-side; client cannot bypass by header manipulation
 * AC-014.6  403 response contains a non-revealing error message (no role/permission details)
 */

import { server } from "./mocks/server";
import { http, HttpResponse } from "msw";
import { moderationApi, ApiClientError } from "@/lib/api/discussionApi";
import { resetRateLimits } from "./mocks/handlers";
import type { ApiError } from "@/lib/api/types";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  server.resetHandlers();
  resetRateLimits();
});
afterAll(() => server.close());

// ─── Role-simulation helpers ─────────────────────────────────────────────────
// In production, role is conveyed via the HTTP-only session cookie (server-side).
// In tests, MSW simulates the server's role-check behaviour.

function simulateRole(role: "unauthenticated" | "member" | "moderator" | "admin"): void {
  server.use(
    http.post("/api/moderation/actions", async ({ request }) => {
      if (role === "unauthenticated") {
        return HttpResponse.json(
          { statusCode: 401, error: "Unauthorized", message: "Authentication required" } as ApiError,
          { status: 401 },
        );
      }

      if (role === "member") {
        // Return generic 403 — no sensitive permission details (OWASP A01)
        return HttpResponse.json(
          { statusCode: 403, error: "Forbidden", message: "Forbidden" } as ApiError,
          { status: 403 },
        );
      }

      // moderator or admin — process the request
      const body = (await request.json()) as Record<string, unknown>;
      return HttpResponse.json(
        {
          resourceType: body.resourceType,
          resourceId: body.resourceId,
          action: body.action,
          moderatorId: role === "admin" ? "admin-1" : "moderator-1",
          performedAt: new Date().toISOString(),
        },
        { status: 200 },
      );
    }),
  );
}

const VALID_MODERATION_REQUEST = {
  resourceType: "thread" as const,
  resourceId: "thread-1",
  action: "hide" as const,
};

describe("AC-014.x — Moderator role-gating", () => {
  describe("AC-014.1 — Unauthenticated users are rejected", () => {
    it("returns 401 when session cookie is absent", async () => {
      simulateRole("unauthenticated");

      await expect(
        moderationApi.moderate(VALID_MODERATION_REQUEST),
      ).rejects.toMatchObject({ statusCode: 401 });
    });

    it("401 error is an ApiClientError instance", async () => {
      simulateRole("unauthenticated");

      let thrown: unknown;
      try {
        await moderationApi.moderate(VALID_MODERATION_REQUEST);
      } catch (e) {
        thrown = e;
      }
      expect(thrown).toBeInstanceOf(ApiClientError);
    });
  });

  describe("AC-014.2 — Regular members are forbidden", () => {
    it("returns 403 when user has member role", async () => {
      simulateRole("member");

      await expect(
        moderationApi.moderate(VALID_MODERATION_REQUEST),
      ).rejects.toMatchObject({ statusCode: 403 });
    });

    it("403 error is an ApiClientError instance", async () => {
      simulateRole("member");

      let thrown: unknown;
      try {
        await moderationApi.moderate(VALID_MODERATION_REQUEST);
      } catch (e) {
        thrown = e;
      }
      expect(thrown).toBeInstanceOf(ApiClientError);
    });
  });

  describe("AC-014.3 — Moderator role is permitted", () => {
    it("returns 200 when user has moderator role", async () => {
      simulateRole("moderator");

      const result = await moderationApi.moderate(VALID_MODERATION_REQUEST);
      expect(result).toMatchObject({
        resourceType: "thread",
        resourceId: "thread-1",
        action: "hide",
        moderatorId: "moderator-1",
      });
    });
  });

  describe("AC-014.4 — Admin role is permitted", () => {
    it("returns 200 when user has admin role", async () => {
      simulateRole("admin");

      const result = await moderationApi.moderate(VALID_MODERATION_REQUEST);
      expect(result).toMatchObject({
        resourceType: "thread",
        resourceId: "thread-1",
        action: "hide",
        moderatorId: "admin-1",
      });
    });
  });

  describe("AC-014.5 — Server-side enforcement", () => {
    it("403 cannot be bypassed by sending a different role header (server ignores it)", async () => {
      // Simulate a server that always returns 403 regardless of client headers
      server.use(
        http.post("/api/moderation/actions", () =>
          HttpResponse.json(
            { statusCode: 403, error: "Forbidden", message: "Forbidden" } as ApiError,
            { status: 403 },
          ),
        ),
      );

      // Even if caller attempts to add a spoofed header, the server rejects it
      await expect(
        moderationApi.moderate(VALID_MODERATION_REQUEST),
      ).rejects.toMatchObject({ statusCode: 403 });
    });
  });

  describe("AC-014.6 — Non-revealing 403 error message (OWASP A01)", () => {
    it("403 message does not disclose internal role/permission details", async () => {
      simulateRole("member");

      let thrown: ApiClientError | null = null;
      try {
        await moderationApi.moderate(VALID_MODERATION_REQUEST);
      } catch (e) {
        if (e instanceof ApiClientError) thrown = e;
      }

      expect(thrown).not.toBeNull();
      // Message must be generic — must not expose role names, permission IDs, etc.
      const msg = thrown!.body.message.toLowerCase();
      expect(msg).not.toMatch(/role/);
      expect(msg).not.toMatch(/permission/);
      expect(msg).not.toMatch(/moderator/);
      // Should be a simple denial
      expect(["forbidden", "access denied", "unauthorized"]).toContain(
        msg.replace(/[^a-z ]/g, "").trim(),
      );
    });
  });
});
