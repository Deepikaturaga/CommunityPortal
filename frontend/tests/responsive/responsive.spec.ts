/**
 * responsive.spec.ts
 *
 * Cross-viewport layout integrity tests — TASK-061 / NFR-019.
 *
 * For each entry in RESPONSIVE_MATRIX the test:
 *   1. Sets the viewport to the target breakpoint.
 *   2. Navigates to the route.
 *   3. Asserts no horizontal scroll, correct visibility of responsive
 *      elements, and no bounding-box overlaps.
 *
 * Acceptance criteria (NFR-019):
 *   No layout breakage at mobile (375 px), tablet (768 px), or desktop
 *   (1280 px) viewport widths.
 */

import { test, expect } from "@playwright/test";
import { VIEWPORTS, ViewportKey } from "../a11y/viewports";
import { RESPONSIVE_MATRIX } from "./responsive-matrix";
import { runLayoutChecks } from "./layout-assertions";

const BASE_URL = process.env["BASE_URL"] ?? "http://localhost:5173";

for (const screen of RESPONSIVE_MATRIX) {
  for (const [vpKey, layoutOpts] of Object.entries(screen.viewports) as [
    ViewportKey,
    NonNullable<(typeof screen.viewports)[ViewportKey]>,
  ][]) {
    const vp = VIEWPORTS[vpKey];

    test.describe(
      `[${screen.screenId}] ${screen.path} @ ${vp.label} (${vp.width}×${vp.height})`,
      () => {
        test.use({
          viewport: { width: vp.width, height: vp.height },
          deviceScaleFactor: vp.deviceScaleFactor ?? 1,
          isMobile: vp.isMobile ?? false,
          hasTouch: vp.hasTouch ?? false,
          ...(screen.requiresAuth
            ? { storageState: "tests/a11y/.auth/user.json" }
            : {}),
        });

        test("layout integrity", async ({ page }) => {
          await page.goto(`${BASE_URL}${screen.path}`);

          if (screen.waitForSelector) {
            await page.waitForSelector(screen.waitForSelector, {
              timeout: 10_000,
            });
          }

          await runLayoutChecks(page, layoutOpts);
        });
      },
    );
  }
}

export { expect };
