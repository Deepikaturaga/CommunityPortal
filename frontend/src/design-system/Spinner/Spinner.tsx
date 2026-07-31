import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const spinnerVariants = cva("animate-spin rounded-full border-2 border-current border-t-transparent", {
  variants: {
    size: {
      xs: "h-3 w-3",
      sm: "h-4 w-4",
      md: "h-5 w-5",
      lg: "h-6 w-6",
      xl: "h-8 w-8",
    },
  },
  defaultVariants: { size: "md" },
});

export interface SpinnerProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof spinnerVariants> {
  /** Accessible label; defaults to "Loading" */
  label?: string;
}

const Spinner = React.forwardRef<HTMLSpanElement, SpinnerProps>(
  ({ size, className, label = "Loading", "aria-hidden": ariaHidden, ...props }, ref) => {
    const hidden = ariaHidden === true || ariaHidden === "true";
    return (
      <span
        ref={ref}
        role={hidden ? undefined : "status"}
        aria-label={hidden ? undefined : label}
        aria-hidden={hidden || undefined}
        className={cn("inline-flex items-center justify-center", className)}
        {...props}
      >
        <span className={cn(spinnerVariants({ size }))} />
      </span>
    );
  }
);

Spinner.displayName = "Spinner";

export { Spinner, spinnerVariants };
