import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@ds/Button";

// ---------------------------------------------------------------------------
// Icon — padlock
// ---------------------------------------------------------------------------
function LockIcon({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      width="48"
      height="48"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface PermissionDeniedProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Headline – keep it user-friendly, not technical */
  title?: string;
  /** Body copy explaining next steps */
  description?: string;
  /** CTA, e.g. "Request access" */
  actionLabel?: string;
  onAction?: () => void;
  /** Secondary CTA, e.g. "Go back" */
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
  /** Override default icon */
  icon?: React.ReactNode;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
const PermissionDenied: React.FC<PermissionDeniedProps> = ({
  title = "Access denied",
  description = "You don't have permission to view this page. Contact your administrator to request access.",
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  icon,
  className,
  ...props
}) => (
  <div
    role="alert"
    aria-live="polite"
    className={cn(
      "flex flex-col items-center justify-center gap-4 py-16 px-6 text-center",
      className
    )}
    {...props}
  >
    <span className="text-muted-foreground">
      {icon ?? <LockIcon className="opacity-50" />}
    </span>

    <div className="space-y-1">
      <p className="text-base font-semibold text-foreground">{title}</p>
      {description && (
        <p className="text-sm text-muted-foreground max-w-sm">{description}</p>
      )}
    </div>

    {(actionLabel || secondaryActionLabel) && (
      <div className="flex items-center gap-2 mt-2">
        {actionLabel && (
          <Button variant="primary" size="sm" onClick={onAction}>
            {actionLabel}
          </Button>
        )}
        {secondaryActionLabel && (
          <Button variant="secondary" size="sm" onClick={onSecondaryAction}>
            {secondaryActionLabel}
          </Button>
        )}
      </div>
    )}
  </div>
);

PermissionDenied.displayName = "PermissionDenied";

export { PermissionDenied };
