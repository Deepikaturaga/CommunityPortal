/**
 * AC-030.28 – AC-030.31  RecentActivity list component tests.
 *
 * AC-030.28  Renders one row per entry supplied in the `items` prop.
 * AC-030.29  Each row displays the typeLabel, description, and a formatted
 *            relative timestamp.
 * AC-030.30  An empty feed renders the empty-state placeholder message.
 * AC-030.31  A loading state renders a skeleton and suppresses content.
 */

import React from "react";
import { render, screen, within } from "@testing-library/react";
import { RecentActivity } from "../../src/components/admin/dashboard/RecentActivity";
import { makeActivityFeed, makeActivityEntry } from "./fixtures";
import {
  transformActivityFeed,
  ACTIVITY_LABELS,
} from "../../src/app/admin/dashboard/transformers";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const buildItems = (n = 3) => transformActivityFeed(makeActivityFeed(n));

// ---------------------------------------------------------------------------
// AC-030.28 — one row per item
// ---------------------------------------------------------------------------

describe("AC-030.28 — row-per-item rendering", () => {
  it("renders exactly N rows for N items", () => {
    render(<RecentActivity items={buildItems(4)} />);
    // Each row must carry data-testid="activity-row"
    expect(screen.getAllByTestId("activity-row")).toHaveLength(4);
  });

  it("renders one row for a single-item feed", () => {
    const items = transformActivityFeed([makeActivityEntry({ id: "only" })]);
    render(<RecentActivity items={items} />);
    expect(screen.getAllByTestId("activity-row")).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// AC-030.29 — row content: typeLabel + description + timestamp
// ---------------------------------------------------------------------------

describe("AC-030.29 — row content accuracy", () => {
  it("displays typeLabel and description in each row", () => {
    const raw = [
      makeActivityEntry({
        id: "r1",
        type: "ORDER_PLACED",
        description: "Order #ORD-9921 placed",
      }),
    ];
    const items = transformActivityFeed(raw);
    render(<RecentActivity items={items} />);

    const row = screen.getByTestId("activity-row");
    expect(within(row).getByText(ACTIVITY_LABELS.ORDER_PLACED)).toBeInTheDocument();
    expect(within(row).getByText(/Order #ORD-9921 placed/)).toBeInTheDocument();
  });

  it("each row includes a time element for the timestamp", () => {
    render(<RecentActivity items={buildItems(2)} />);
    const rows = screen.getAllByTestId("activity-row");
    rows.forEach((row) => {
      // A <time> element or an element with role="time" should be present
      const timeEl =
        row.querySelector("time") ??
        within(row).queryByRole("time");
      expect(timeEl).not.toBeNull();
    });
  });
});

// ---------------------------------------------------------------------------
// AC-030.30 — empty state
// ---------------------------------------------------------------------------

describe("AC-030.30 — empty state", () => {
  it("renders the empty-state message when items is an empty array", () => {
    render(<RecentActivity items={[]} />);
    expect(screen.queryAllByTestId("activity-row")).toHaveLength(0);
    // Component must render a descriptive empty-state text
    expect(
      screen.getByTestId("activity-empty") ||
      screen.getByText(/no recent activity/i)
    ).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// AC-030.31 — loading skeleton
// ---------------------------------------------------------------------------

describe("AC-030.31 — loading skeleton suppresses content", () => {
  it("renders skeleton elements when loading=true", () => {
    render(<RecentActivity items={[]} loading />);
    expect(screen.getAllByTestId("activity-skeleton").length).toBeGreaterThan(0);
  });

  it("does not render real rows while loading", () => {
    render(<RecentActivity items={buildItems(3)} loading />);
    expect(screen.queryAllByTestId("activity-row")).toHaveLength(0);
  });
});
