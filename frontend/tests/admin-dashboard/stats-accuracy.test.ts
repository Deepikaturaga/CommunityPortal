/**
 * AC-030.5 – AC-030.9  Data-accuracy tests for dashboard stat cards.
 *
 * We test the *transformation layer* (`transformDashboardStats`) that maps
 * raw API responses into the props consumed by the StatCard components.
 * This is framework-agnostic pure-function testing — no rendering required.
 *
 * AC-030.5  All numeric KPIs are passed through without mutation.
 * AC-030.6  Revenue is formatted to two decimal places as a display string.
 * AC-030.7  User-activity ratio (activeUsers / totalUsers) is computed and
 *           clamped to [0, 1].
 * AC-030.8  Order completion rate is computed correctly.
 * AC-030.9  Zero-division edge cases produce 0 (not NaN or Infinity).
 */

import {
  transformDashboardStats,
  type DashboardStatCardProps,
} from "../../src/app/admin/dashboard/transformers";
import { makeDashboardStats } from "./fixtures";

// ---------------------------------------------------------------------------
// AC-030.5 — raw KPIs are forwarded unchanged
// ---------------------------------------------------------------------------

describe("AC-030.5 — raw KPI pass-through", () => {
  it("preserves totalUsers, pendingOrders, and systemAlerts verbatim", () => {
    const stats = makeDashboardStats({
      totalUsers: 500,
      pendingOrders: 10,
      systemAlerts: 3,
    });
    const result: DashboardStatCardProps = transformDashboardStats(stats);

    expect(result.totalUsers).toBe(500);
    expect(result.pendingOrders).toBe(10);
    expect(result.systemAlerts).toBe(3);
  });

  it("preserves newSignupsToday", () => {
    const stats = makeDashboardStats({ newSignupsToday: 7 });
    expect(transformDashboardStats(stats).newSignupsToday).toBe(7);
  });
});

// ---------------------------------------------------------------------------
// AC-030.6 — revenue display formatting
// ---------------------------------------------------------------------------

describe("AC-030.6 — revenue formatting", () => {
  it("formats an integer revenue to two decimal places", () => {
    const stats = makeDashboardStats({ totalRevenue: 12_000 });
    expect(transformDashboardStats(stats).revenueDisplay).toBe("12000.00");
  });

  it("rounds a long decimal to two places", () => {
    const stats = makeDashboardStats({ totalRevenue: 1_234.5678 });
    expect(transformDashboardStats(stats).revenueDisplay).toBe("1234.57");
  });

  it("handles zero revenue", () => {
    const stats = makeDashboardStats({ totalRevenue: 0 });
    expect(transformDashboardStats(stats).revenueDisplay).toBe("0.00");
  });
});

// ---------------------------------------------------------------------------
// AC-030.7 — active-user ratio
// ---------------------------------------------------------------------------

describe("AC-030.7 — active-user ratio", () => {
  it("computes ratio correctly for normal values", () => {
    const stats = makeDashboardStats({ totalUsers: 1_000, activeUsers: 750 });
    expect(transformDashboardStats(stats).activeUserRatio).toBeCloseTo(0.75);
  });

  it("clamps ratio to 1 when activeUsers > totalUsers (data inconsistency)", () => {
    const stats = makeDashboardStats({ totalUsers: 100, activeUsers: 150 });
    expect(transformDashboardStats(stats).activeUserRatio).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// AC-030.8 — order completion rate
// ---------------------------------------------------------------------------

describe("AC-030.8 — order completion rate", () => {
  it("computes completion rate from completed / (completed + cancelled + pending)", () => {
    const stats = makeDashboardStats({
      completedOrders: 80,
      cancelledOrders: 10,
      pendingOrders: 10,
    });
    // 80 / 100 = 0.80
    expect(transformDashboardStats(stats).orderCompletionRate).toBeCloseTo(0.8);
  });

  it("returns 1 when all orders are completed", () => {
    const stats = makeDashboardStats({
      completedOrders: 50,
      cancelledOrders: 0,
      pendingOrders: 0,
    });
    expect(transformDashboardStats(stats).orderCompletionRate).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// AC-030.9 — zero-division edge cases
// ---------------------------------------------------------------------------

describe("AC-030.9 — zero-division safety", () => {
  it("returns 0 for activeUserRatio when totalUsers is 0", () => {
    const stats = makeDashboardStats({ totalUsers: 0, activeUsers: 0 });
    const result = transformDashboardStats(stats);
    expect(result.activeUserRatio).toBe(0);
    expect(Number.isFinite(result.activeUserRatio)).toBe(true);
  });

  it("returns 0 for orderCompletionRate when total orders is 0", () => {
    const stats = makeDashboardStats({
      completedOrders: 0,
      cancelledOrders: 0,
      pendingOrders: 0,
    });
    const result = transformDashboardStats(stats);
    expect(result.orderCompletionRate).toBe(0);
    expect(Number.isFinite(result.orderCompletionRate)).toBe(true);
  });
});
