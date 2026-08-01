"use client";

/**
 * AlertBanner — active system-alerts list on the admin dashboard.
 *
 * AC-030.32–35:
 *  - Renders one `data-testid="alert-row"` per active alert.
 *  - CRITICAL rows carry `data-severity="critical"` + class `alert-critical`.
 *  - Acknowledge button calls `onAcknowledge(alert.id)`.
 *  - Wrapper carries `data-has-critical="true|false"`.
 */

import React from "react";
import type { SystemAlert } from "../../../app/admin/dashboard/transformers";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface AlertBannerProps {
  alerts: SystemAlert[];
  hasCritical: boolean;
  onAcknowledge: (alertId: string) => void;
}

// ---------------------------------------------------------------------------
// Sub-component
// ---------------------------------------------------------------------------

interface AlertRowProps {
  alert: SystemAlert;
  onAcknowledge: (id: string) => void;
}

const AlertRow: React.FC<AlertRowProps> = ({ alert, onAcknowledge }) => {
  const isCritical = alert.severity === "CRITICAL";

  return (
    <li
      data-testid="alert-row"
      data-severity={alert.severity.toLowerCase()}
      className={`alert-row alert-row--${alert.severity.toLowerCase()}${isCritical ? " alert-critical" : ""}`}
      role="alert"
    >
      <div className="alert-row__content">
        <strong className="alert-row__title">{alert.title}</strong>
        <p className="alert-row__message">{alert.message}</p>
      </div>

      <button
        type="button"
        className="alert-row__ack-btn"
        onClick={() => onAcknowledge(alert.id)}
        aria-label={`Acknowledge: ${alert.title}`}
      >
        Acknowledge
      </button>
    </li>
  );
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export const AlertBanner: React.FC<AlertBannerProps> = ({
  alerts,
  hasCritical,
  onAcknowledge,
}) => {
  if (alerts.length === 0) {
    return null;
  }

  return (
    <div
      data-testid="alert-banner"
      data-has-critical={String(hasCritical)}
      className={`alert-banner${hasCritical ? " alert-banner--critical" : ""}`}
      aria-live="assertive"
      aria-atomic="false"
    >
      <ul className="alert-banner__list">
        {alerts.map((alert) => (
          <AlertRow
            key={alert.id}
            alert={alert}
            onAcknowledge={onAcknowledge}
          />
        ))}
      </ul>
    </div>
  );
};
