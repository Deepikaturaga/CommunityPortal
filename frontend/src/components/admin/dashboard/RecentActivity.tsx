"use client";

/**
 * RecentActivity — scrollable activity-feed widget on the admin dashboard.
 *
 * AC-030.28–31:
 *  - Renders one `data-testid="activity-row"` per item.
 *  - Each row shows typeLabel, description, and a <time> timestamp.
 *  - Empty items → `data-testid="activity-empty"` placeholder.
 *  - loading=true → `data-testid="activity-skeleton"` rows, no real rows.
 */

import React from "react";
import type { TransformedActivityEntry } from "../../../app/admin/dashboard/transformers";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface RecentActivityProps {
  items: TransformedActivityEntry[];
  loading?: boolean;
  /** Number of skeleton rows to render while loading. */
  skeletonCount?: number;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const SkeletonRow: React.FC = () => (
  <li
    data-testid="activity-skeleton"
    className="activity-row activity-row--skeleton"
    aria-hidden="true"
  >
    <span className="activity-row__skeleton-label" />
    <span className="activity-row__skeleton-desc" />
    <span className="activity-row__skeleton-time" />
  </li>
);

interface ActivityRowProps {
  item: TransformedActivityEntry;
}

const ActivityRow: React.FC<ActivityRowProps> = ({ item }) => (
  <li data-testid="activity-row" className="activity-row">
    <span className="activity-row__type">{item.typeLabel}</span>
    <span className="activity-row__description">{item.description}</span>
    <time
      className="activity-row__time"
      dateTime={item.timestamp}
      title={new Date(item.timestamp).toLocaleString()}
    >
      {formatRelativeTime(item.timestamp)}
    </time>
  </li>
);

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const RecentActivity: React.FC<RecentActivityProps> = ({
  items,
  loading = false,
  skeletonCount = 5,
}) => {
  if (loading) {
    return (
      <section aria-label="Recent activity" aria-busy="true">
        <ul className="activity-list">
          {Array.from({ length: skeletonCount }, (_, i) => (
            <SkeletonRow key={i} />
          ))}
        </ul>
      </section>
    );
  }

  if (items.length === 0) {
    return (
      <section aria-label="Recent activity">
        <p data-testid="activity-empty" className="activity-list__empty">
          No recent activity
        </p>
      </section>
    );
  }

  return (
    <section aria-label="Recent activity">
      <ul className="activity-list">
        {items.map((item) => (
          <ActivityRow key={item.id} item={item} />
        ))}
      </ul>
    </section>
  );
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatRelativeTime(isoTimestamp: string): string {
  const diffMs = Date.now() - new Date(isoTimestamp).getTime();
  const diffSec = Math.floor(diffMs / 1_000);

  if (diffSec < 60) return "just now";
  if (diffSec < 3_600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86_400) return `${Math.floor(diffSec / 3_600)}h ago`;
  return `${Math.floor(diffSec / 86_400)}d ago`;
}
