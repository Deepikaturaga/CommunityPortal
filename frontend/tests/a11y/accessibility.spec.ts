/**
 * accessibility.spec.ts
 *
 * Axe-core accessibility audit for every screen in the canonical inventory.
 * Runs at the DESKTOP viewport by default; the responsive axe matrix (each
 * screen × each viewport) lives in accessibility-responsive.spec.ts.
 *
 * Acceptance criteria (TASK-060 / VER-022):
 *   • Zero axe violations at impact "critical" or "serious" on every listed screen.
 *   • Manual audit sign-off tracked via the companion MANUAL_AUDIT_CHECKLIST.md.
 *
 * Test organisation:
 *   Public screens  → no storageState required
 *   Auth screens    → use storageState saved by auth.setup.ts
 */

import { expect } from "@playwright/test";
import { test } from "./axe.fixture";
import { SCREENS, PUBLIC_SCREENS, AUTH_SCREENS } from "./screen-inventory";
import { VIEWPORTS } from "./viewports";

const BASE_URL = process.env["BASE_URL"] ?? "http://localhost:5173";

// ── Helpers ───────────────────────────────────────────────────────────────────

async function navigateAndWait(
  page: Parameters<typeof test>[1] extends infer T
    ? T extends { page: infer P }
      ? P
      : never
    : never,
  screen: (typeof SCREENS)[number],
) {
  await page.goto(`${BASE_URL}${screen.path}`);
  if (screen.waitForSelector) {
    await page.waitForSelector(screen.waitForSelector, { timeout: 10_000 });
  }
}

// ── Public screen scans ───────────────────────────────────────────────────────

test.describe("Accessibility — public screens (desktop)", () => {
  test.use({ viewport: VIEWPORTS.desktop });

  for (const screen of PUBLIC_SCREENS) {
    test(`[${screen.id}] ${screen.path} — no critical/serious violations`, async ({
      page,
      checkA11y,
    }) => {
      await navigateAndWait(page as never, screen);
      await checkA11y({
        exclude: screen.axeExclude,
        failOn: ["critical", "serious"],
      });
    });
  }
});

// ── Authenticated screen scans ────────────────────────────────────────────────

test.describe("Accessibility — authenticated screens (desktop)", () => {
  // Use the cached session produced by auth.setup.ts
  test.use({
    storageState: "tests/a11y/.auth/user.json",
    viewport: VIEWPORTS.desktop,
  });

  for (const screen of AUTH_SCREENS) {
    test(`[${screen.id}] ${screen.path} — no critical/serious violations`, async ({
      page,
      checkA11y,
    }) => {
      await navigateAndWait(page as never, screen);
      await checkA11y({
        exclude: screen.axeExclude,
        failOn: ["critical", "serious"],
      });
    });
  }
});

// ── Smoke check: ensure expect is accessible from the module ─────────────────
export { expect };
