/**
 * viewports.ts
 *
 * Canonical breakpoint definitions shared by both the accessibility scan matrix
 * (TASK-060) and the responsive layout tests (TASK-061 / NFR-019).
 *
 * Keep in sync with the Tailwind / CSS custom-property breakpoints defined in
 * the application source (frontend/src/styles/breakpoints.ts or equivalent).
 */

export interface Viewport {
  /** Human-readable label used in test titles and report columns. */
  label: string;
  width: number;
  height: number;
  /**
   * Playwright device-scale-factor.  1 = standard display.
   * Use 2 for HiDPI / Retina where pixel-perfect layout matters.
   */
  deviceScaleFactor?: number;
  /** True when this viewport represents a touch/pointer device. */
  isMobile?: boolean;
  hasTouch?: boolean;
}

/**
 * Three-tier breakpoint matrix used by NFR-019.
 *
 * mobile  → 375 × 812   (iPhone 12 / SE reference)
 * tablet  → 768 × 1024  (iPad portrait reference)
 * desktop → 1280 × 800  (standard laptop / CI headless default)
 *
 * Add further rows here to extend coverage without touching test files.
 */
export const VIEWPORTS = {
  mobile: {
    label: "mobile",
    width: 375,
    height: 812,
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 2,
  },
  tablet: {
    label: "tablet",
    width: 768,
    height: 1024,
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 2,
  },
  desktop: {
    label: "desktop",
    width: 1280,
    height: 800,
    isMobile: false,
    hasTouch: false,
    deviceScaleFactor: 1,
  },
} as const satisfies Record<string, Viewport>;

export type ViewportKey = keyof typeof VIEWPORTS;

/** Ordered list for parameterised tests (most constrained → widest). */
export const VIEWPORT_LIST: Viewport[] = [
  VIEWPORTS.mobile,
  VIEWPORTS.tablet,
  VIEWPORTS.desktop,
];
