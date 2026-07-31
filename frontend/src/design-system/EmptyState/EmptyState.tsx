import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@ds/Button";

// ---------------------------------------------------------------------------
// Icon
// ---------------------------------------------------------------------------
function EmptyIcon({ className }: { className?: string }) {
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
      <circle cx="12" cy="12" r="10" />
      <path d="M9 10h.01M15 10h.01M9.5 15a3.5 3.5 0 0 0 5 0" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Headline */
  title?: string;
  /** Supporting body copy */
  description?: string;
  /** Override the default illustration */
  icon?: React.ReactNode;
  /** CTA button label */
  actionLabel?: string;
  /** CTA click handler */
  onAction?: () => void;
  /** Secondary CTA */
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
const EmptyState: React.FC<EmptyStateProps> = ({
  title = "Nothing here yet",
  description,
  icon,
  actionLabel,
  onAction,
  secondaryActionLabel,
  onSecondaryAction,
  className,
  ...props
}) => (
  <div
    role="status"
    aria-live="polite"
    className={cn(
      "flex flex-col items-center justify-center gap-4 py-16 px-6 text-center",
      className
    )}
    {...props}
  >
    <span className="text-muted-foreground">
      {icon ?? <EmptyIcon className="opacity-40" />}
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

EmptyState.displayName = "EmptyState";

export { EmptyState };
