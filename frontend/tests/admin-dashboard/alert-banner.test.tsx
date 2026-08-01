/**
 * AC-030.32 – AC-030.35  AlertBanner component tests.
 *
 * AC-030.32  Renders one alert row per active alert.
 * AC-030.33  CRITICAL alerts receive visually distinct styling
 *            (data-severity="critical" or class "alert-critical").
 * AC-030.34  Clicking "Acknowledge" calls the onAcknowledge callback with
 *            the correct alert id.
 * AC-030.35  When hasCritical is true, the banner wrapper carries a
 *            data-has-critical="true" attribute for visual callout.
 */

import React from "react";
import { render, screen, within, fireEvent } from "@testing-library/react";
import { AlertBanner } from "../../src/components/admin/dashboard/AlertBanner";
import { makeSystemAlert } from "./fixtures";
import { transformAlerts } from "../../src/app/admin/dashboard/transformers";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const buildActive = (...overrides: Parameters<typeof makeSystemAlert>[0][]) =>
  transformAlerts(overrides.map((o) => makeSystemAlert(o)));

// ---------------------------------------------------------------------------
// AC-030.32 — one row per active alert
// ---------------------------------------------------------------------------

describe("AC-030.32 — row-per-alert rendering", () => {
  it("renders one row for each active alert", () => {
    const { active, hasCritical } = buildActive(
      { severity: "WARNING" },
      { severity: "ERROR" }
    );
    render(<AlertBanner alerts={active} hasCritical={hasCritical} onAcknowledge={jest.fn()} />);
    expect(screen.getAllByTestId("alert-row")).toHaveLength(2);
  });

  it("renders nothing when there are no active alerts", () => {
    render(<AlertBanner alerts={[]} hasCritical={false} onAcknowledge={jest.fn()} />);
    expect(screen.queryAllByTestId("alert-row")).toHaveLength(0);
  });
});

// ---------------------------------------------------------------------------
// AC-030.33 — CRITICAL styling
// ---------------------------------------------------------------------------

describe("AC-030.33 — CRITICAL severity styling", () => {
  it("applies critical indicator to CRITICAL alert rows", () => {
    const { active, hasCritical } = buildActive({ severity: "CRITICAL" });
    render(<AlertBanner alerts={active} hasCritical={hasCritical} onAcknowledge={jest.fn()} />);

    const row = screen.getByTestId("alert-row");
    const isCritical =
      row.getAttribute("data-severity") === "critical" ||
      row.classList.contains("alert-critical");
    expect(isCritical).toBe(true);
  });

  it("does not apply critical indicator to WARNING rows", () => {
    const { active, hasCritical } = buildActive({ severity: "WARNING" });
    render(<AlertBanner alerts={active} hasCritical={hasCritical} onAcknowledge={jest.fn()} />);

    const row = screen.getByTestId("alert-row");
    const isCritical =
      row.getAttribute("data-severity") === "critical" ||
      row.classList.contains("alert-critical");
    expect(isCritical).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// AC-030.34 — acknowledge callback
// ---------------------------------------------------------------------------

describe("AC-030.34 — acknowledge button calls onAcknowledge", () => {
  it("invokes onAcknowledge with the correct id when button is clicked", () => {
    const alert = makeSystemAlert({ id: "alert_ack_test", acknowledged: false });
    const { active, hasCritical } = transformAlerts([alert]);
    const handler = jest.fn();

    render(
      <AlertBanner alerts={active} hasCritical={hasCritical} onAcknowledge={handler} />
    );

    const row = screen.getByTestId("alert-row");
    const ackBtn = within(row).getByRole("button", { name: /acknowledge/i });
    fireEvent.click(ackBtn);

    expect(handler).toHaveBeenCalledTimes(1);
    expect(handler).toHaveBeenCalledWith("alert_ack_test");
  });

  it("does not call onAcknowledge for a different row", () => {
    const a1 = makeSystemAlert({ id: "a1", acknowledged: false });
    const a2 = makeSystemAlert({ id: "a2", acknowledged: false });
    const { active, hasCritical } = transformAlerts([a1, a2]);
    const handler = jest.fn();

    render(
      <AlertBanner alerts={active} hasCritical={hasCritical} onAcknowledge={handler} />
    );

    const rows = screen.getAllByTestId("alert-row");
    const ackBtn = within(rows[0]).getByRole("button", { name: /acknowledge/i });
    fireEvent.click(ackBtn);

    expect(handler).toHaveBeenCalledWith(active[0].id);
    expect(handler).toHaveBeenCalledTimes(1);
  });
});

// ---------------------------------------------------------------------------
// AC-030.35 — hasCritical banner attribute
// ---------------------------------------------------------------------------

describe("AC-030.35 — hasCritical banner wrapper attribute", () => {
  it("sets data-has-critical=true on the wrapper when hasCritical is true", () => {
    const { active, hasCritical } = buildActive({ severity: "CRITICAL" });
    render(
      <AlertBanner alerts={active} hasCritical={hasCritical} onAcknowledge={jest.fn()} />
    );

    const banner = screen.getByTestId("alert-banner");
    expect(banner.getAttribute("data-has-critical")).toBe("true");
  });

  it("sets data-has-critical=false when no critical alerts are active", () => {
    const { active, hasCritical } = buildActive({ severity: "WARNING" });
    render(
      <AlertBanner alerts={active} hasCritical={hasCritical} onAcknowledge={jest.fn()} />
    );

    const banner = screen.getByTestId("alert-banner");
    expect(banner.getAttribute("data-has-critical")).toBe("false");
  });
});
