"use client";

/**
 * StatCard — single KPI tile on the admin dashboard.
 *
 * AC-030.23–27:
 *  - Renders `label` and `value` props.
 *  - Positive trend (> 0) → green "↑ N%" badge with data-trend="positive".
 *  - Negative trend (< 0) → red  "↓ N%" badge with data-trend="negative".
 *  - Zero / absent trend  → no badge rendered.
 *  - Accessible: region role with aria-label, optional aria-live.
 */

import React from "react";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface StatCardProps {
  /** Display label, e.g. "Total Users". */
  label: string;
  /** Primary displayed value — number or pre-formatted string. */
  value: number | string;
  /**
   * Percentage change (positive = up, negative = down).
   * Omit or set to 0 to hide the trend badge.
   */
  trend?: number;
  /**
   * When true the value container carries `aria-live="polite"` for
   * screen-reader announcements of dynamic updates.
   */
  live?: boolean;
  className?: string;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  trend,
  live,
  className = "",
}) => {
  const hasTrend = typeof trend === "number" && trend !== 0;
  const trendDirection = hasTrend
    ? trend! > 0
      ? "positive"
      : "negative"
    : null;

  return (
    <article
      role="region"
      aria-label={label}
      className={`stat-card ${className}`.trim()}
    >
      <p className="stat-card__label">{label}</p>

      <p
        className="stat-card__value"
        {...(live ? { "aria-live": "polite" } : {})}
      >
        {value}
      </p>

      {hasTrend && (
        <span
          data-testid="trend-badge"
          data-trend={trendDirection!}
          className={
            trendDirection === "positive" ? "trend-positive" : "trend-negative"
          }
          aria-label={`${trendDirection === "positive" ? "Up" : "Down"} ${Math.abs(trend!)} percent`}
        >
          {trendDirection === "positive" ? "↑" : "↓"}&nbsp;{Math.abs(trend!)}%
        </span>
      )}
    </article>
  );
};
