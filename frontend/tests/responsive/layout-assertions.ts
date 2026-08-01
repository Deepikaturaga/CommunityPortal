/**
 * layout-assertions.ts
 *
 * Reusable layout-integrity helpers for TASK-061 / NFR-019.
 *
 * These utilities check that the core structural elements of the page
 * are visible and not clipped/overlapping at each breakpoint, without
 * coupling test files to implementation details.
 */

import { Page, expect } from "@playwright/test";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface LayoutCheckOptions {
  /**
   * Assert that the element is visible and its bounding box fits within the
   * viewport width (i.e. no horizontal overflow that would cause a scrollbar).
   */
  noHorizontalOverflow?: boolean;
  /**
   * Assert that no two elements in `selectors` overlap each other.
   * Useful for confirming stack / reflow happened correctly.
   */
  noOverlappingElements?: string[];
  /**
   * Assert that each selector resolves to exactly one visible element.
   */
  visibleSelectors?: string[];
  /**
   * Assert that each selector is NOT visible (e.g. desktop nav hidden on mobile).
   */
  hiddenSelectors?: string[];
}

// ── Core assertions ───────────────────────────────────────────────────────────

/**
 * Assert that the page body does not exceed the viewport width.
 * A scrollWidth > clientWidth means content is clipping off-screen.
 */
export async function assertNoHorizontalScroll(page: Page): Promise<void> {
  const overflow = await page.evaluate(() => {
    return document.documentElement.scrollWidth >
      document.documentElement.clientWidth;
  });
  expect(
    overflow,
    "Page has horizontal scroll — content overflows viewport width",
  ).toBe(false);
}

/**
 * Assert that every selector in `selectors` maps to a visible element.
 */
export async function assertVisible(
  page: Page,
  selectors: string[],
): Promise<void> {
  for (const sel of selectors) {
    await expect(
      page.locator(sel).first(),
      `Expected "${sel}" to be visible`,
    ).toBeVisible();
  }
}

/**
 * Assert that every selector in `selectors` maps to a hidden / absent element.
 */
export async function assertHidden(
  page: Page,
  selectors: string[],
): Promise<void> {
  for (const sel of selectors) {
    await expect(
      page.locator(sel).first(),
      `Expected "${sel}" to be hidden`,
    ).toBeHidden();
  }
}

/**
 * Assert that no two elements in `selectors` have overlapping bounding boxes.
 * Only checks the first match of each selector.
 */
export async function assertNoOverlap(
  page: Page,
  selectors: string[],
): Promise<void> {
  const boxes = await Promise.all(
    selectors.map(async (sel) => {
      const box = await page.locator(sel).first().boundingBox();
      return { sel, box };
    }),
  );

  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i]!;
      const b = boxes[j]!;
      if (!a.box || !b.box) continue; // element not rendered — skip

      const overlaps =
        a.box.x < b.box.x + b.box.width &&
        a.box.x + a.box.width > b.box.x &&
        a.box.y < b.box.y + b.box.height &&
        a.box.y + a.box.height > b.box.y;

      expect(
        overlaps,
        `Elements "${a.sel}" and "${b.sel}" overlap at this viewport`,
      ).toBe(false);
    }
  }
}

/**
 * Convenience wrapper: run all enabled layout checks in one call.
 */
export async function runLayoutChecks(
  page: Page,
  opts: LayoutCheckOptions,
): Promise<void> {
  if (opts.noHorizontalOverflow) {
    await assertNoHorizontalScroll(page);
  }
  if (opts.visibleSelectors?.length) {
    await assertVisible(page, opts.visibleSelectors);
  }
  if (opts.hiddenSelectors?.length) {
    await assertHidden(page, opts.hiddenSelectors);
  }
  if (opts.noOverlappingElements?.length) {
    await assertNoOverlap(page, opts.noOverlappingElements);
  }
}
