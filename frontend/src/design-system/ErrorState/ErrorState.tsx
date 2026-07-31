import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@ds/Button";

// ---------------------------------------------------------------------------
// Icon
// ---------------------------------------------------------------------------
function AlertTriangleIcon({ className }: { className?: string }) {
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
      <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface ErrorStateProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Short headline */
  title?: string;
  /** Detailed error message (avoid leaking internal details) */
  description?: string;
  /** Correlation ID for support (never full stack trace) */
  correlationId?: string;
  /** Override default icon */
  icon?: React.ReactNode;
  /** Primary CTA (e.g. "Retry") */
  actionLabel?: string;
  onAction?: () => void;
  /** Secondary CTA (e.g. "Go back") */
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
const ErrorState: React.FC<ErrorStateProps> = ({
  title = "Something went wrong",
  description = "An unexpected error occurred. Please try again or contact support if the problem persists.",
  correlationId,
  icon,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  className,
  ...props
}) => (
  <div
    role="alert"
    aria-live="assertive"
    className={cn(
      "flex flex-col items-center justify-center gap-4 py-16 px-6 text-center",
      className
    )}
    {...props}
  >
    <span className="text-destructive">
      {icon ?? <AlertTriangleIcon className="opacity-70" />}
    </span>

    <div className="space-y-1">
      <p className="text-base font-semibold text-foreground">{title}</p>
      {description && (
        <p className="text-sm text-muted-foreground max-w-sm">{description}</p>
      )}
      {correlationId && (
        <p className="text-xs text-muted-foreground font-mono mt-1">
          Error ID: {correlationId}
        </p>
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

ErrorState.displayName = "ErrorState";

export { ErrorState };
