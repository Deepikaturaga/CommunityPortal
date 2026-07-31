import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Render a leading icon inside the input */
  leftAddon?: React.ReactNode;
  /** Render a trailing icon/button inside the input */
  rightAddon?: React.ReactNode;
  /** Highlight as invalid (maps to aria-invalid) */
  invalid?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, leftAddon, rightAddon, invalid, type = "text", ...props }, ref) => (
    <div className="relative flex items-center w-full">
      {leftAddon && (
        <span
          aria-hidden="true"
          className="pointer-events-none absolute left-3 flex items-center text-muted-foreground"
        >
          {leftAddon}
        </span>
      )}
      <input
        ref={ref}
        type={type}
        aria-invalid={invalid || undefined}
        className={cn(
          "peer flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm",
          "placeholder:text-muted-foreground",
          "transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0",
          "disabled:cursor-not-allowed disabled:opacity-50",
          invalid && "border-destructive focus-visible:ring-destructive",
          leftAddon && "pl-9",
          rightAddon && "pr-9",
          className
        )}
        {...props}
      />
      {rightAddon && (
        <span className="absolute right-3 flex items-center text-muted-foreground">
          {rightAddon}
        </span>
      )}
    </div>
  )
);

Input.displayName = "Input";

export { Input };
