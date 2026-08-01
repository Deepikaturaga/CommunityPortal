/**
 * Shared test fixtures and factory helpers for admin-dashboard tests.
 *
 * These types mirror the shapes defined in:
 *   frontend/src/lib/api-client/types.ts  (generated from backend OpenAPI)
 *
 * Do NOT hand-duplicate production DTOs here — only the minimal subset
 * needed to build typed test data.
 */

// ---------------------------------------------------------------------------
// Role / auth fixtures
// ---------------------------------------------------------------------------

export type UserRole = "ADMIN" | "MANAGER" | "VIEWER" | "GUEST";

export interface AuthSession {
  userId: string;
  email: string;
  role: UserRole;
  name: string;
}

export const makeSession = (overrides: Partial<AuthSession> = {}): AuthSession => ({
  userId: "usr_test_001",
  email: "admin@example.com",
  role: "ADMIN",
  name: "Test Admin",
  ...overrides,
});

// ---------------------------------------------------------------------------
// Dashboard stats fixture
// ---------------------------------------------------------------------------

export interface DashboardStats {
  totalUsers: number;
  activeUsers: number;
  totalRevenue: number;
  pendingOrders: number;
  completedOrders: number;
  cancelledOrders: number;
  newSignupsToday: number;
  systemAlerts: number;
}

export const makeDashboardStats = (
  overrides: Partial<DashboardStats> = {}
): DashboardStats => ({
  totalUsers: 1_240,
  activeUsers: 876,
  totalRevenue: 98_540.75,
  pendingOrders: 34,
  completedOrders: 2_105,
  cancelledOrders: 87,
  newSignupsToday: 12,
  systemAlerts: 2,
  ...overrides,
});

// ---------------------------------------------------------------------------
// Recent-activity fixture
// ---------------------------------------------------------------------------

export type ActivityType =
  | "USER_CREATED"
  | "ORDER_PLACED"
  | "ORDER_COMPLETED"
  | "ORDER_CANCELLED"
  | "PAYMENT_RECEIVED"
  | "SYSTEM_ALERT";

export interface ActivityEntry {
  id: string;
  type: ActivityType;
  description: string;
  actor: string;
  timestamp: string; // ISO-8601
  meta?: Record<string, unknown>;
}

let _activitySeq = 0;
export const makeActivityEntry = (
  overrides: Partial<ActivityEntry> = {}
): ActivityEntry => ({
  id: `act_${++_activitySeq}`,
  type: "ORDER_PLACED",
  description: "Order #ORD-9921 placed",
  actor: "customer@example.com",
  timestamp: new Date("2024-06-15T10:30:00Z").toISOString(),
  ...overrides,
});

export const makeActivityFeed = (n = 5): ActivityEntry[] =>
  Array.from({ length: n }, (_, i) =>
    makeActivityEntry({
      id: `act_feed_${i + 1}`,
      timestamp: new Date(
        Date.UTC(2024, 5, 15, 10 - i, 0, 0)
      ).toISOString(),
    })
  );

// ---------------------------------------------------------------------------
// Alert fixture
// ---------------------------------------------------------------------------

export type AlertSeverity = "INFO" | "WARNING" | "ERROR" | "CRITICAL";

export interface SystemAlert {
  id: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  createdAt: string;
  acknowledged: boolean;
}

let _alertSeq = 0;
export const makeSystemAlert = (
  overrides: Partial<SystemAlert> = {}
): SystemAlert => ({
  id: `alert_${++_alertSeq}`,
  severity: "WARNING",
  title: "Disk usage high",
  message: "Disk usage on server-01 exceeds 85 %.",
  createdAt: new Date("2024-06-15T08:00:00Z").toISOString(),
  acknowledged: false,
  ...overrides,
});

// ---------------------------------------------------------------------------
// Chart data fixture (revenue over time)
// ---------------------------------------------------------------------------

export interface RevenueDataPoint {
  date: string; // YYYY-MM-DD
  revenue: number;
}

export const makeRevenueTimeSeries = (days = 7): RevenueDataPoint[] =>
  Array.from({ length: days }, (_, i) => {
    const d = new Date("2024-06-15");
    d.setDate(d.getDate() - (days - 1 - i));
    return {
      date: d.toISOString().slice(0, 10),
      revenue: Math.round(1_000 + Math.random() * 4_000),
    };
  });
