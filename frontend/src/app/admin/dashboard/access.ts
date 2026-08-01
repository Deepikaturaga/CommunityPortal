/**
 * Dashboard access-gate.
 *
 * Centralises the RBAC check for the admin dashboard Server Component.
 * Called at the top of the page before any data fetching occurs.
 *
 * Roles allowed: ADMIN, MANAGER
 * - No session   → redirect /login
 * - Insufficient → redirect /403
 * - Authorised   → return void (no throw)
 */

import { redirect } from "next/navigation";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type UserRole = "ADMIN" | "MANAGER" | "VIEWER" | "GUEST";

export interface AuthSession {
  userId: string;
  email: string;
  role: UserRole;
  name: string;
}

// ---------------------------------------------------------------------------
// Contract export — consumed by tests and other guards
// ---------------------------------------------------------------------------

/** The roles that may access the admin dashboard. */
export const DASHBOARD_REQUIRED_ROLES: UserRole[] = ["ADMIN", "MANAGER"];

// ---------------------------------------------------------------------------
// Guard
// ---------------------------------------------------------------------------

/**
 * Throws a Next.js redirect for unauthorised callers.
 * Returns void for authorised sessions.
 *
 * @param session  The resolved session, or null if unauthenticated.
 */
export async function checkDashboardAccess(
  session: AuthSession | null
): Promise<void> {
  if (!session) {
    redirect("/login");
  }

  if (!(DASHBOARD_REQUIRED_ROLES as string[]).includes(session.role)) {
    redirect("/403");
  }
}
