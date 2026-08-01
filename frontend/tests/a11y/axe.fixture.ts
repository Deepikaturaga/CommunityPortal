/**
 * axe.fixture.ts
 *
 * Shared Playwright fixture that injects axe-core into every page under test
 * and exposes a typed `checkA11y` helper used by all accessibility specs.
 *
 * Depends on:  @axe-core/playwright  (see package.json)
 * Aligns with: TASK-060 / VER-022
 */

import { test as base, expect, Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// ── Types ────────────────────────────────────────────────────────────────────

export interface A11yFixtures {
  /** Run an axe scan and assert zero critical/serious violations. */
  checkA11y: (options?: CheckA11yOptions) => Promise<void>;
}

export interface CheckA11yOptions {
  /** CSS selector to scope the scan (default: whole document). */
  include?: string[];
  /** CSS selectors to exclude from the scan. */
  exclude?: string[];
  /**
   * Axe rule overrides.
   * E.g. `{ "color-contrast": { enabled: false } }` to temporarily skip a rule
   * while a design fix is in progress.  Suppression MUST be justified in a
   * companion comment and tracked in the backlog.
   */
  rules?: Record<string, { enabled: boolean }>;
  /**
   * Violation impact levels that cause the test to fail.
   * Default: ["critical", "serious"]  — aligns with VER-022 acceptance criteria.
   */
  failOn?: Array<"minor" | "moderate" | "serious" | "critical">;
}

// ── Fixture definition ────────────────────────────────────────────────────────

export const test = base.extend<A11yFixtures>({
  checkA11y: async ({ page }, use) => {
    const checker = async (options: CheckA11yOptions = {}) => {
      const {
        include = [],
        exclude = [],
        rules = {},
        failOn = ["critical", "serious"],
      } = options;

      let builder = new AxeBuilder({ page });

      if (include.length) builder = builder.include(include);
      if (exclude.length) builder = builder.exclude(exclude);
      if (Object.keys(rules).length) builder = builder.withRules(Object.keys(rules));

      // Apply per-rule enable/disable overrides
      for (const [ruleId, cfg] of Object.entries(rules)) {
        if (!cfg.enabled) {
          builder = builder.disableRules([ruleId]);
        }
      }

      const results = await builder.analyze();

      // Filter to only the severity levels that should fail the build
      const failures = results.violations.filter(
        (v) => v.impact && (failOn as string[]).includes(v.impact),
      );

      if (failures.length > 0) {
        const summary = failures
          .map(
            (v) =>
              `[${v.impact?.toUpperCase()}] ${v.id}: ${v.description}\n` +
              v.nodes
                .slice(0, 3)
                .map((n) => `  • ${n.html}`)
                .join("\n"),
          )
          .join("\n\n");

        throw new Error(
          `Found ${failures.length} axe violation(s) at impact ` +
            `[${failOn.join(", ")}]:\n\n${summary}`,
        );
      }

      // Attach full results to the Playwright report (visible in HTML reporter)
      await attachAxeResults(page, results);
    };

    await use(checker);
  },
});

export { expect };

// ── Internal helpers ──────────────────────────────────────────────────────────

async function attachAxeResults(
  page: Page,
  results: Awaited<ReturnType<AxeBuilder["analyze"]>>,
) {
  // Attach as JSON so the Playwright HTML reporter surfaces it under "Attachments"
  const payload = JSON.stringify(
    {
      violations: results.violations,
      incomplete: results.incomplete,
      passes: results.passes.length,
      inapplicable: results.inapplicable.length,
      timestamp: new Date().toISOString(),
      url: page.url(),
    },
    null,
    2,
  );

  // testInfo is not directly available here; callers may attach via page fixture.
  // We write to a custom property so specs can optionally forward it.
  (page as unknown as { _axeResults?: string })._axeResults = payload;
}
