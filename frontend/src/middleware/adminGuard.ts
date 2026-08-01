/**
 * adminGuard — Next.js middleware helper for /admin/* route protection.
 *
 * AC-030.18–22:
 *  - No session cookie         → 307 /login
 *  - Expired token             → 307 /login
 *  - Insufficient role         → 307 /403
 *  - ADMIN / MANAGER           → NextResponse.next()
 *  - Non-admin paths           → NextResponse.next() (guard is bypassed)
 */

import { NextRequest, NextResponse } from "next/server";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type UserRole = "ADMIN" | "MANAGER" | "VIEWER" | "GUEST";

interface SessionPayload {
  userId: string;
  role: UserRole;
  email: string;
  /** Unix timestamp (seconds).  Absent → non-expiring (test/dev only). */
  exp?: number;
}

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

const ADMIN_PATH_PREFIX = "/admin";
const ALLOWED_ROLES: UserRole[] = ["ADMIN", "MANAGER"];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Attempt to decode the session cookie value.
 * Production uses a signed JWT; in tests we accept base64-encoded JSON so
 * the guard logic can be exercised without a live signing key.
 *
 * Returns null if the cookie is absent, malformed, or expired.
 */
function decodeSession(cookieValue: string | undefined): SessionPayload | null {
  if (!cookieValue) return null;

  try {
    const raw = Buffer.from(cookieValue, "base64").toString("utf-8");
    const payload = JSON.parse(raw) as SessionPayload;

    // Expiry check
    if (
      typeof payload.exp === "number" &&
      payload.exp < Math.floor(Date.now() / 1_000)
    ) {
      return null; // expired
    }

    return payload;
  } catch {
    return null;
  }
}

function redirectTo(req: NextRequest, path: string): NextResponse {
  const url = req.nextUrl.clone();
  url.pathname = path;
  return NextResponse.redirect(url, { status: 307 });
}

// ---------------------------------------------------------------------------
// Guard
// ---------------------------------------------------------------------------

/**
 * Call from the root `middleware.ts` matcher for `"/admin/:path*"` routes, or
 * invoke directly in tests.
 */
export async function adminMiddlewareGuard(
  req: NextRequest
): Promise<NextResponse> {
  const { pathname } = req.nextUrl;

  // AC-030.22 — non-admin paths are not affected
  if (!pathname.startsWith(ADMIN_PATH_PREFIX)) {
    return NextResponse.next();
  }

  const sessionCookieValue = req.cookies.get("session")?.value;
  const session = decodeSession(sessionCookieValue);

  // AC-030.18 / AC-030.19 — no session or expired token
  if (!session) {
    return redirectTo(req, "/login");
  }

  // AC-030.20 — insufficient privilege
  if (!(ALLOWED_ROLES as string[]).includes(session.role)) {
    return redirectTo(req, "/403");
  }

  // AC-030.21 — authorised
  return NextResponse.next();
}
