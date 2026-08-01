/**
 * AC-030.18 – AC-030.22  Middleware role-guard tests.
 *
 * The middleware enforces route protection at the edge before any Server
 * Component executes.  Tests cover:
 *
 * AC-030.18  Requests to /admin/* without a valid session cookie are
 *            redirected to /login.
 * AC-030.19  Requests with an expired token are redirected to /login.
 * AC-030.20  VIEWER / GUEST sessions are redirected to /403.
 * AC-030.21  ADMIN and MANAGER sessions are allowed through (NextResponse.next).
 * AC-030.22  Non-admin routes are not affected by the guard.
 */

import { NextRequest, NextResponse } from "next/server";
import { adminMiddlewareGuard } from "../../src/middleware/adminGuard";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Build a minimal NextRequest to an admin path, optionally with a session
 * cookie value (base64-encoded JSON).
 */
function makeRequest(
  pathname: string,
  sessionPayload?: Record<string, unknown> | null
): NextRequest {
  const url = `http://localhost:3000${pathname}`;
  const req = new NextRequest(url);
  if (sessionPayload !== null && sessionPayload !== undefined) {
    // Simulate a signed cookie value – the guard reads it via next/headers.
    // In tests we inject the raw JSON; the production verifier is mocked.
    const encoded = Buffer.from(JSON.stringify(sessionPayload)).toString(
      "base64"
    );
    req.cookies.set("session", encoded);
  }
  return req;
}

const adminSession = (role: string) => ({ userId: "u1", role, email: "t@t.com" });

// ---------------------------------------------------------------------------
// AC-030.18 — no session cookie → /login
// ---------------------------------------------------------------------------

describe("AC-030.18 — no session redirects to /login", () => {
  it("redirects unauthenticated request for /admin/dashboard", async () => {
    const req = makeRequest("/admin/dashboard");
    // Remove any auto-set cookie
    req.cookies.delete("session");

    const res = await adminMiddlewareGuard(req);

    expect(res).toBeInstanceOf(NextResponse);
    expect(res.status).toBe(307);
    expect(res.headers.get("location")).toContain("/login");
  });
});

// ---------------------------------------------------------------------------
// AC-030.19 — expired token → /login
// ---------------------------------------------------------------------------

describe("AC-030.19 — expired token redirects to /login", () => {
  it("treats an expired session as unauthenticated", async () => {
    const expiredPayload = {
      ...adminSession("ADMIN"),
      exp: Math.floor(Date.now() / 1_000) - 3_600, // expired 1 hour ago
    };
    const req = makeRequest("/admin/dashboard", expiredPayload);
    const res = await adminMiddlewareGuard(req);

    expect(res.status).toBe(307);
    expect(res.headers.get("location")).toContain("/login");
  });
});

// ---------------------------------------------------------------------------
// AC-030.20 — low-privilege roles → /403
// ---------------------------------------------------------------------------

describe("AC-030.20 — under-privileged roles redirect to /403", () => {
  const deniedRoles = ["VIEWER", "GUEST"];

  test.each(deniedRoles)(
    "role %s is redirected to /403 for /admin/dashboard",
    async (role) => {
      const req = makeRequest("/admin/dashboard", adminSession(role));
      const res = await adminMiddlewareGuard(req);

      expect(res.status).toBe(307);
      expect(res.headers.get("location")).toContain("/403");
    }
  );
});

// ---------------------------------------------------------------------------
// AC-030.21 — authorised roles are allowed through
// ---------------------------------------------------------------------------

describe("AC-030.21 — authorised roles produce NextResponse.next()", () => {
  const allowedRoles = ["ADMIN", "MANAGER"];

  test.each(allowedRoles)(
    "role %s passes middleware for /admin/dashboard",
    async (role) => {
      const req = makeRequest("/admin/dashboard", adminSession(role));
      const res = await adminMiddlewareGuard(req);

      // A "next" response has no Location header and returns 200.
      expect(res.headers.get("location")).toBeNull();
      expect(res.status).toBe(200);
    }
  );
});

// ---------------------------------------------------------------------------
// AC-030.22 — non-admin routes are unaffected
// ---------------------------------------------------------------------------

describe("AC-030.22 — non-admin routes bypass the guard", () => {
  const publicPaths = ["/", "/login", "/about", "/api/health"];

  test.each(publicPaths)(
    "path %s is passed through without authentication check",
    async (path) => {
      // No session cookie → guard should not redirect these public paths
      const req = makeRequest(path);
      req.cookies.delete("session");

      const res = await adminMiddlewareGuard(req);

      expect(res.headers.get("location")).toBeNull();
      expect(res.status).toBe(200);
    }
  );
});
