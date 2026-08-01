/**
 * accessibility-responsive.spec.ts
 *
 * Axe-core scans at every canonical viewport (mobile / tablet / desktop).
 *
 * This supplements accessibility.spec.ts (desktop-only baseline) to catch
 * violations that are viewport-dependent — e.g. a hamburger menu that is
 * present only on mobile, or a modal that reflows differently on tablet.
 *
 * Acceptance criteria (TASK-060 / VER-022):
 *   Zero critical/serious axe violations at every defined breakpoint.
 */

import { test } from "./axe.fixture";
import { SCREENS } from "./screen-inventory";
import { VIEWPORT_LIST } from "./viewports";

const BASE_URL = process.env["BASE_URL"] ?? "http://localhost:5173";

for (const viewport of VIEWPORT_LIST) {
  test.describe(`Accessibility — all screens @ ${viewport.label} (${viewport.width}×${viewport.height})`, () => {
    test.use({
      viewport: { width: viewport.width, height: viewport.height },
      deviceScaleFactor: viewport.deviceScaleFactor ?? 1,
      isMobile: viewport.isMobile ?? false,
      hasTouch: viewport.hasTouch ?? false,
      // Auth screens reuse the cached session; public screens need no state.
      // Playwright merges storageState per-project; when a test in this group
      // does NOT need auth the storageState is simply ignored (no cookies are
      // sent to routes that don't require it).
      storageState: "tests/a11y/.auth/user.json",
    });

    for (const screen of SCREENS) {
      test(`[${screen.id}] ${screen.path}`, async ({ page, checkA11y }) => {
        await page.goto(`${BASE_URL}${screen.path}`);

        if (screen.waitForSelector) {
          await page.waitForSelector(screen.waitForSelector, {
            timeout: 10_000,
          });
        }

        await checkA11y({
          exclude: screen.axeExclude,
          failOn: ["critical", "serious"],
        });
      });
    }
  });
}
