/**
 * screen-inventory.ts
 *
 * Canonical list of application routes that must be scanned for accessibility
 * (TASK-060 / VER-022) and layout integrity (TASK-061 / NFR-019).
 *
 * ┌──────────────────────────────────────────────────────────────────────────┐
 * │  TODO (upstream phases 020-031):                                         │
 * │  Fill each entry's `path` with the real application route once the       │
 * │  corresponding page component is implemented.  Remove any stub entries   │
 * │  that map to pages not yet built.                                        │
 * └──────────────────────────────────────────────────────────────────────────┘
 */

export interface Screen {
  /** Unique identifier used as test-case label and report key. */
  id: string;
  /** Application-relative path (e.g. "/dashboard"). */
  path: string;
  /**
   * Phase / task that produced this screen.
   * Used to skip screens whose upstream tasks haven't landed yet.
   */
  phase: string;
  /**
   * When true the route requires authentication.
   * The test harness will authenticate via storageState before navigating.
   */
  requiresAuth?: boolean;
  /**
   * Optional CSS selector for a landmark / heading that must be visible
   * before axe runs, confirming the page has fully hydrated.
   */
  waitForSelector?: string;
  /**
   * Selectors to exclude from the axe scan for this specific screen
   * (e.g. third-party widgets with known vendor violations).
   * Every entry must have a tracking comment with a backlog reference.
   */
  axeExclude?: string[];
}

/**
 * Master screen inventory.
 *
 * Ordered by approximate user journey (unauthenticated → authenticated →
 * admin) so that test reports follow a logical narrative.
 */
export const SCREENS: Screen[] = [
  // ── Public / unauthenticated ──────────────────────────────────────────────
  {
    id: "home",
    path: "/",
    phase: "TASK-025",
    waitForSelector: "main",
  },
  {
    id: "login",
    path: "/login",
    phase: "TASK-025",
    waitForSelector: "form",
  },
  {
    id: "register",
    path: "/register",
    phase: "TASK-025",
    waitForSelector: "form",
  },
  {
    id: "forgot-password",
    path: "/forgot-password",
    phase: "TASK-025",
    waitForSelector: "form",
  },

  // ── Authenticated core ────────────────────────────────────────────────────
  {
    id: "dashboard",
    path: "/dashboard",
    phase: "TASK-038",
    requiresAuth: true,
    waitForSelector: '[data-testid="dashboard-heading"]',
  },
  {
    id: "profile",
    path: "/profile",
    phase: "TASK-043",
    requiresAuth: true,
    waitForSelector: '[data-testid="profile-form"]',
  },
  {
    id: "settings",
    path: "/settings",
    phase: "TASK-043",
    requiresAuth: true,
    waitForSelector: '[data-testid="settings-panel"]',
  },

  // ── Feature screens (TASK-048, TASK-055, TASK-057) ────────────────────────
  // TODO: add real paths once phases 020-031 are merged.
  {
    id: "feature-list",
    path: "/items", // TODO: confirm route from TASK-048
    phase: "TASK-048",
    requiresAuth: true,
    waitForSelector: '[data-testid="item-list"]',
  },
  {
    id: "feature-detail",
    path: "/items/1", // TODO: replace with seeded fixture ID from TASK-048
    phase: "TASK-048",
    requiresAuth: true,
    waitForSelector: '[data-testid="item-detail"]',
  },
  {
    id: "notifications",
    path: "/notifications",
    phase: "TASK-055",
    requiresAuth: true,
    waitForSelector: '[data-testid="notification-list"]',
  },
  {
    id: "reports",
    path: "/reports",
    phase: "TASK-057",
    requiresAuth: true,
    waitForSelector: '[data-testid="reports-container"]',
  },
];

/** Screens that do NOT require authentication. */
export const PUBLIC_SCREENS = SCREENS.filter((s) => !s.requiresAuth);

/** Screens that require authentication. */
export const AUTH_SCREENS = SCREENS.filter((s) => s.requiresAuth);
