/**
 * Dashboard data transformers.
 *
 * Pure functions that map raw API response shapes → typed component-prop
 * objects.  No framework imports; fully unit-testable in isolation.
 */

// ---------------------------------------------------------------------------
// Types (mirrored from generated API client for transformer usage)
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

export interface DashboardStatCardProps {
  totalUsers: number;
  activeUsers: number;
  revenueDisplay: string;       // formatted to 2 d.p.
  pendingOrders: number;
  completedOrders: number;
  cancelledOrders: number;
  newSignupsToday: number;
  systemAlerts: number;
  activeUserRatio: number;      // [0, 1]
  orderCompletionRate: number;  // [0, 1]
}

// ---------------------------------------------------------------------------
// transformDashboardStats
// ---------------------------------------------------------------------------

/**
 * AC-030.5–9: Maps raw stats → StatCard props.
 *
 * - Revenue is formatted to exactly 2 decimal places.
 * - Ratios are computed with zero-division safety (→ 0 not NaN/Infinity).
 * - activeUserRatio is clamped to [0, 1].
 */
export function transformDashboardStats(
  stats: DashboardStats
): DashboardStatCardProps {
  const activeUserRatio =
    stats.totalUsers === 0
      ? 0
      : Math.min(1, stats.activeUsers / stats.totalUsers);

  const totalOrders =
    stats.completedOrders + stats.cancelledOrders + stats.pendingOrders;

  const orderCompletionRate =
    totalOrders === 0 ? 0 : stats.completedOrders / totalOrders;

  return {
    totalUsers: stats.totalUsers,
    activeUsers: stats.activeUsers,
    revenueDisplay: stats.totalRevenue.toFixed(2),
    pendingOrders: stats.pendingOrders,
    completedOrders: stats.completedOrders,
    cancelledOrders: stats.cancelledOrders,
    newSignupsToday: stats.newSignupsToday,
    systemAlerts: stats.systemAlerts,
    activeUserRatio,
    orderCompletionRate,
  };
}

// ---------------------------------------------------------------------------
// Activity-feed types and transformer
// ---------------------------------------------------------------------------

export type ActivityType =
  | "USER_CREATED"
  | "ORDER_PLACED"
  | "ORDER_COMPLETED"
  | "ORDER_CANCELLED"
  | "PAYMENT_RECEIVED"
  | "SYSTEM_ALERT";

/** Human-readable label for each activity type. */
export const ACTIVITY_LABELS: Record<ActivityType, string> = {
  USER_CREATED: "New user",
  ORDER_PLACED: "Order placed",
  ORDER_COMPLETED: "Order completed",
  ORDER_CANCELLED: "Order cancelled",
  PAYMENT_RECEIVED: "Payment received",
  SYSTEM_ALERT: "System alert",
};

/** Maximum entries shown in the activity feed widget. */
export const MAX_FEED_ITEMS = 20;

/** Maximum character length for a description before truncation. */
const MAX_DESCRIPTION_LENGTH = 120;

export interface RawActivityEntry {
  id: string;
  type: ActivityType;
  description: string;
  actor: string;
  timestamp: string;
  meta?: Record<string, unknown>;
}

export interface TransformedActivityEntry extends RawActivityEntry {
  typeLabel: string;
}

/**
 * AC-030.10–13: Sorts newest-first, maps type → label, truncates long
 * descriptions, and caps at MAX_FEED_ITEMS.
 */
export function transformActivityFeed(
  entries: RawActivityEntry[]
): TransformedActivityEntry[] {
  return [...entries]
    .sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
    .slice(0, MAX_FEED_ITEMS)
    .map((entry) => ({
      ...entry,
      typeLabel: ACTIVITY_LABELS[entry.type] ?? entry.type,
      description:
        entry.description.length > MAX_DESCRIPTION_LENGTH
          ? entry.description.slice(0, MAX_DESCRIPTION_LENGTH) + "…"
          : entry.description,
    }));
}

// ---------------------------------------------------------------------------
// Alert types and transformer
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

export interface TransformedAlerts {
  active: SystemAlert[];
  dismissed: SystemAlert[];
  hasCritical: boolean;
}

const SEVERITY_ORDER: Record<AlertSeverity, number> = {
  CRITICAL: 0,
  ERROR: 1,
  WARNING: 2,
  INFO: 3,
};

/**
 * AC-030.14–17: Splits alerts into active/dismissed, sorts by severity,
 * and computes the hasCritical flag.
 */
export function transformAlerts(alerts: SystemAlert[]): TransformedAlerts {
  const active = alerts
    .filter((a) => !a.acknowledged)
    .sort(
      (a, b) =>
        SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
    );

  const dismissed = alerts.filter((a) => a.acknowledged);

  const hasCritical = active.some((a) => a.severity === "CRITICAL");

  return { active, dismissed, hasCritical };
}
