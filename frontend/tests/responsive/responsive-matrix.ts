/**
 * responsive-matrix.ts
 *
 * Per-screen, per-viewport layout expectations for TASK-061 / NFR-019.
 *
 * Each entry describes what structural elements MUST be visible, MUST be
 * hidden, and MUST NOT overlap at the given viewport for a given screen.
 *
 * Convention for selectors: prefer `data-testid` attributes over
 * CSS classes (which are implementation details).
 *
 * ┌──────────────────────────────────────────────────────────────────────────┐
 * │  TODO (upstream phases 020-031):                                         │
 * │  Update selectors once real `data-testid` attributes are defined in the  │
 * │  component library.                                                      │
 * └──────────────────────────────────────────────────────────────────────────┘
 */

import type { ViewportKey } from "../a11y/viewports";
import type { LayoutCheckOptions } from "./layout-assertions";

export interface ScreenLayout {
  screenId: string;
  path: string;
  requiresAuth?: boolean;
  waitForSelector?: string;
  /** Keyed by viewport label. Omit a key to skip that viewport. */
  viewports: Partial<Record<ViewportKey, LayoutCheckOptions>>;
}

export const RESPONSIVE_MATRIX: ScreenLayout[] = [
  // ── Home / Landing ─────────────────────────────────────────────────────────
  {
    screenId: "home",
    path: "/",
    waitForSelector: "main",
    viewports: {
      mobile: {
        noHorizontalOverflow: true,
        visibleSelectors: [
          '[data-testid="mobile-menu-button"]',
          '[data-testid="hero-heading"]',
        ],
        hiddenSelectors: ['[data-testid="desktop-nav"]'],
        noOverlappingElements: [
          '[data-testid="hero-heading"]',
          '[data-testid="hero-cta"]',
        ],
      },
      tablet: {
        noHorizontalOverflow: true,
        visibleSelectors: ['[data-testid="hero-heading"]'],
      },
      desktop: {
        noHorizontalOverflow: true,
        visibleSelectors: [
          '[data-testid="desktop-nav"]',
          '[data-testid="hero-heading"]',
        ],
        hiddenSelectors: ['[data-testid="mobile-menu-button"]'],
      },
    },
  },

  // ── Login ──────────────────────────────────────────────────────────────────
  {
    screenId: "login",
    path: "/login",
    waitForSelector: "form",
    viewports: {
      mobile: {
        noHorizontalOverflow: true,
        visibleSelectors: ["form"],
        noOverlappingElements: [
          '[data-testid="email-input"]',
          '[data-testid="password-input"]',
          '[data-testid="submit-button"]',
        ],
      },
      tablet: {
        noHorizontalOverflow: true,
        visibleSelectors: ["form"],
      },
      desktop: {
        noHorizontalOverflow: true,
        visibleSelectors: ["form"],
      },
    },
  },

  // ── Dashboard ─────────────────────────────────────────────────────────────
  {
    screenId: "dashboard",
    path: "/dashboard",
    requiresAuth: true,
    waitForSelector: '[data-testid="dashboard-heading"]',
    viewports: {
      mobile: {
        noHorizontalOverflow: true,
        visibleSelectors: [
          '[data-testid="dashboard-heading"]',
          '[data-testid="mobile-sidebar-toggle"]',
        ],
        hiddenSelectors: ['[data-testid="sidebar"]'],
      },
      tablet: {
        noHorizontalOverflow: true,
        visibleSelectors: ['[data-testid="dashboard-heading"]'],
      },
      desktop: {
        noHorizontalOverflow: true,
        visibleSelectors: [
          '[data-testid="dashboard-heading"]',
          '[data-testid="sidebar"]',
        ],
        hiddenSelectors: ['[data-testid="mobile-sidebar-toggle"]'],
      },
    },
  },

  // ── Feature list ──────────────────────────────────────────────────────────
  {
    screenId: "feature-list",
    path: "/items", // TODO: confirm from TASK-048
    requiresAuth: true,
    waitForSelector: '[data-testid="item-list"]',
    viewports: {
      mobile: {
        noHorizontalOverflow: true,
        visibleSelectors: ['[data-testid="item-list"]'],
      },
      tablet: {
        noHorizontalOverflow: true,
        visibleSelectors: ['[data-testid="item-list"]'],
      },
      desktop: {
        noHorizontalOverflow: true,
        visibleSelectors: ['[data-testid="item-list"]'],
      },
    },
  },

  // ── Reports ───────────────────────────────────────────────────────────────
  {
    screenId: "reports",
    path: "/reports",
    requiresAuth: true,
    waitForSelector: '[data-testid="reports-container"]',
    viewports: {
      mobile: {
        noHorizontalOverflow: true,
        visibleSelectors: ['[data-testid="reports-container"]'],
      },
      desktop: {
        noHorizontalOverflow: true,
        visibleSelectors: ['[data-testid="reports-container"]'],
      },
    },
  },
];
