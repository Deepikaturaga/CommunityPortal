/**
 * AC-030.1 – AC-030.4  Role-based access control tests for the admin dashboard.
 *
 * Strategy:
 *  - The dashboard page is a Next.js Server Component that calls `getSession()`
 *    (reads the HTTP-only auth cookie via `next/headers`) and redirects
 *    unauthenticated / under-privileged visitors.
 *  - We unit-test the *access-gate logic* in isolation; the integration path
 *    through middleware is covered by middleware.test.ts.
 *
 * AC-030.1  Unauthenticated requests are redirected to /login.
 * AC-030.2  VIEWER role is denied and redirected to /403.
 * AC-030.3  GUEST  role is denied and redirected to /403.
 * AC-030.4  ADMIN and MANAGER roles are granted access (no redirect thrown).
 */

import {
  checkDashboardAccess,
  DASHBOARD_REQUIRED_ROLES,
} from "../../src/app/admin/dashboard/access";
import { makeSession, type UserRole } from "./fixtures";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Invoke checkDashboardAccess and catch any NEXT_REDIRECT throws. */
async function tryAccess(role: UserRole | null): Promise<string | null> {
  const session = role ? makeSession({ role }) : null;
  try {
    await checkDashboardAccess(session);
    return null; // no redirect → access granted
  } catch (err: unknown) {
    if (err instanceof Error && err.message.startsWith("NEXT_REDIRECT:")) {
      return err.message.replace("NEXT_REDIRECT:", "");
    }
    throw err; // re-throw unexpected errors
  }
}

// ---------------------------------------------------------------------------
// AC-030.1 — unauthenticated
// ---------------------------------------------------------------------------

describe("AC-030.1 — unauthenticated access", () => {
  it("redirects to /login when no session exists", async () => {
    const dest = await tryAccess(null);
    expect(dest).toBe("/login");
  });
});

// ---------------------------------------------------------------------------
// AC-030.2 / AC-030.3 — insufficient privilege
// ---------------------------------------------------------------------------

describe("AC-030.2 / AC-030.3 — insufficient privilege", () => {
  const deniedRoles: UserRole[] = ["VIEWER", "GUEST"];

  test.each(deniedRoles)(
    "role %s is redirected to /403",
    async (role) => {
      const dest = await tryAccess(role);
      expect(dest).toBe("/403");
    }
  );
});

// ---------------------------------------------------------------------------
// AC-030.4 — authorised roles
// ---------------------------------------------------------------------------

describe("AC-030.4 — authorised roles are granted access", () => {
  const allowedRoles: UserRole[] = ["ADMIN", "MANAGER"];

  test.each(allowedRoles)(
    "role %s passes without redirect",
    async (role) => {
      const dest = await tryAccess(role);
      expect(dest).toBeNull();
    }
  );
});

// ---------------------------------------------------------------------------
// Contract: DASHBOARD_REQUIRED_ROLES export is stable
// ---------------------------------------------------------------------------

describe("DASHBOARD_REQUIRED_ROLES contract", () => {
  it("exports exactly ADMIN and MANAGER", () => {
    expect(DASHBOARD_REQUIRED_ROLES).toEqual(
      expect.arrayContaining(["ADMIN", "MANAGER"])
    );
    expect(DASHBOARD_REQUIRED_ROLES).toHaveLength(2);
  });
});
