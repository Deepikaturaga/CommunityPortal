/**
 * AC-030.14 – AC-030.17  System-alert accuracy and severity tests.
 *
 * AC-030.14  `transformAlerts` preserves all fields verbatim (no mutation).
 * AC-030.15  Alerts are sorted: CRITICAL → ERROR → WARNING → INFO.
 * AC-030.16  Acknowledged alerts are separated from unacknowledged ones.
 * AC-030.17  `hasCritical` flag is true iff at least one unacknowledged
 *            CRITICAL alert exists.
 */

import {
  transformAlerts,
  type TransformedAlerts,
} from "../../src/app/admin/dashboard/transformers";
import { makeSystemAlert } from "./fixtures";

// ---------------------------------------------------------------------------
// AC-030.14 — field preservation
// ---------------------------------------------------------------------------

describe("AC-030.14 — alert field preservation", () => {
  it("passes all fields through without mutation", () => {
    const alert = makeSystemAlert({
      id: "alert_preserved",
      severity: "ERROR",
      title: "DB connection pool exhausted",
      message: "Pool size 50/50.",
      acknowledged: false,
    });

    const { active } = transformAlerts([alert]);
    const result = active[0];

    expect(result.id).toBe("alert_preserved");
    expect(result.severity).toBe("ERROR");
    expect(result.title).toBe("DB connection pool exhausted");
    expect(result.message).toBe("Pool size 50/50.");
    expect(result.acknowledged).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// AC-030.15 — severity ordering
// ---------------------------------------------------------------------------

describe("AC-030.15 — severity sort order (CRITICAL first)", () => {
  it("sorts unacknowledged alerts CRITICAL → ERROR → WARNING → INFO", () => {
    const alerts = [
      makeSystemAlert({ id: "i1", severity: "INFO", acknowledged: false }),
      makeSystemAlert({ id: "c1", severity: "CRITICAL", acknowledged: false }),
      makeSystemAlert({ id: "w1", severity: "WARNING", acknowledged: false }),
      makeSystemAlert({ id: "e1", severity: "ERROR", acknowledged: false }),
    ];

    const { active } = transformAlerts(alerts);

    expect(active[0].severity).toBe("CRITICAL");
    expect(active[1].severity).toBe("ERROR");
    expect(active[2].severity).toBe("WARNING");
    expect(active[3].severity).toBe("INFO");
  });

  it("preserves relative order within the same severity", () => {
    const alerts = [
      makeSystemAlert({ id: "w1", severity: "WARNING", acknowledged: false }),
      makeSystemAlert({ id: "w2", severity: "WARNING", acknowledged: false }),
    ];
    const { active } = transformAlerts(alerts);
    expect(active[0].id).toBe("w1");
    expect(active[1].id).toBe("w2");
  });
});

// ---------------------------------------------------------------------------
// AC-030.16 — acknowledged separation
// ---------------------------------------------------------------------------

describe("AC-030.16 — acknowledged vs active separation", () => {
  it("puts acknowledged:false in active and acknowledged:true in dismissed", () => {
    const alerts = [
      makeSystemAlert({ id: "act", acknowledged: false }),
      makeSystemAlert({ id: "dis", acknowledged: true }),
    ];

    const result: TransformedAlerts = transformAlerts(alerts);

    expect(result.active.map((a) => a.id)).toContain("act");
    expect(result.active.map((a) => a.id)).not.toContain("dis");
    expect(result.dismissed.map((a) => a.id)).toContain("dis");
    expect(result.dismissed.map((a) => a.id)).not.toContain("act");
  });

  it("returns empty arrays when input is empty", () => {
    const result = transformAlerts([]);
    expect(result.active).toEqual([]);
    expect(result.dismissed).toEqual([]);
  });

  it("handles all-acknowledged list", () => {
    const alerts = [
      makeSystemAlert({ acknowledged: true }),
      makeSystemAlert({ acknowledged: true }),
    ];
    const result = transformAlerts(alerts);
    expect(result.active).toHaveLength(0);
    expect(result.dismissed).toHaveLength(2);
  });
});

// ---------------------------------------------------------------------------
// AC-030.17 — hasCritical flag
// ---------------------------------------------------------------------------

describe("AC-030.17 — hasCritical flag", () => {
  it("is true when at least one unacknowledged CRITICAL alert exists", () => {
    const alerts = [
      makeSystemAlert({ severity: "CRITICAL", acknowledged: false }),
      makeSystemAlert({ severity: "WARNING", acknowledged: false }),
    ];
    expect(transformAlerts(alerts).hasCritical).toBe(true);
  });

  it("is false when CRITICAL alert is acknowledged", () => {
    const alerts = [
      makeSystemAlert({ severity: "CRITICAL", acknowledged: true }),
    ];
    expect(transformAlerts(alerts).hasCritical).toBe(false);
  });

  it("is false when no alerts exist", () => {
    expect(transformAlerts([]).hasCritical).toBe(false);
  });

  it("is false when only WARNING/ERROR/INFO are active", () => {
    const alerts = [
      makeSystemAlert({ severity: "ERROR", acknowledged: false }),
      makeSystemAlert({ severity: "WARNING", acknowledged: false }),
    ];
    expect(transformAlerts(alerts).hasCritical).toBe(false);
  });
});
