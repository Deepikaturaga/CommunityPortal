/**
 * AC-030.23 – AC-030.27  StatCard component rendering tests.
 *
 * Tests the <StatCard> client component that renders a single KPI tile on
 * the dashboard.  Coverage:
 *
 * AC-030.23  Renders the supplied `label` and `value` props.
 * AC-030.24  Renders a positive trend badge (green, "↑ N%") when trend > 0.
 * AC-030.25  Renders a negative trend badge (red, "↓ N%") when trend < 0.
 * AC-030.26  Omits the trend badge when trend is undefined.
 * AC-030.27  Component is accessible: has a labelled region and no violations
 *            on the critical attributes.
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { StatCard } from "../../src/components/admin/dashboard/StatCard";

// ---------------------------------------------------------------------------
// AC-030.23 — label and value are rendered
// ---------------------------------------------------------------------------

describe("AC-030.23 — label and value rendering", () => {
  it("displays the label text", () => {
    render(<StatCard label="Total Users" value={1240} />);
    expect(screen.getByText("Total Users")).toBeInTheDocument();
  });

  it("displays the numeric value", () => {
    render(<StatCard label="Active Users" value={876} />);
    expect(screen.getByText("876")).toBeInTheDocument();
  });

  it("displays a string value", () => {
    render(<StatCard label="Revenue" value="$98,540.75" />);
    expect(screen.getByText("$98,540.75")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// AC-030.24 — positive trend badge
// ---------------------------------------------------------------------------

describe("AC-030.24 — positive trend badge", () => {
  it("shows an upward arrow badge for positive trend", () => {
    render(<StatCard label="Signups" value={12} trend={15} />);
    const badge = screen.getByTestId("trend-badge");
    expect(badge).toBeInTheDocument();
    expect(badge.textContent).toMatch(/↑/);
    expect(badge.textContent).toMatch(/15/);
  });

  it("applies green/positive styling class", () => {
    render(<StatCard label="Signups" value={12} trend={5} />);
    const badge = screen.getByTestId("trend-badge");
    // The component must carry a data-trend attribute or a recognisable class.
    expect(
      badge.classList.contains("trend-positive") ||
      badge.getAttribute("data-trend") === "positive"
    ).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// AC-030.25 — negative trend badge
// ---------------------------------------------------------------------------

describe("AC-030.25 — negative trend badge", () => {
  it("shows a downward arrow badge for negative trend", () => {
    render(<StatCard label="Cancellations" value={87} trend={-8} />);
    const badge = screen.getByTestId("trend-badge");
    expect(badge.textContent).toMatch(/↓/);
    expect(badge.textContent).toMatch(/8/);
  });

  it("applies red/negative styling class", () => {
    render(<StatCard label="Cancellations" value={87} trend={-8} />);
    const badge = screen.getByTestId("trend-badge");
    expect(
      badge.classList.contains("trend-negative") ||
      badge.getAttribute("data-trend") === "negative"
    ).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// AC-030.26 — no trend badge when undefined
// ---------------------------------------------------------------------------

describe("AC-030.26 — no trend when prop is absent", () => {
  it("does not render a trend badge when trend is not supplied", () => {
    render(<StatCard label="Alerts" value={2} />);
    expect(screen.queryByTestId("trend-badge")).not.toBeInTheDocument();
  });

  it("does not render a trend badge when trend is 0", () => {
    render(<StatCard label="Alerts" value={2} trend={0} />);
    expect(screen.queryByTestId("trend-badge")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// AC-030.27 — accessibility basics
// ---------------------------------------------------------------------------

describe("AC-030.27 — accessibility", () => {
  it("renders inside an element with a descriptive aria-label or role", () => {
    render(<StatCard label="Total Users" value={1240} />);
    // The card should be a landmark or have an accessible name
    const region =
      screen.queryByRole("region") ??
      screen.queryByRole("article") ??
      screen.queryByLabelText("Total Users");
    expect(region).not.toBeNull();
  });

  it("value element has an aria-live region for dynamic updates", () => {
    const { container } = render(<StatCard label="Orders" value={34} live />);
    const liveEl = container.querySelector("[aria-live]");
    expect(liveEl).not.toBeNull();
  });
});
