import * as React from "react";
import { cn } from "@/lib/utils";

export interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  /** Show a required asterisk */
  required?: boolean;
  /** Visually hide the label (still readable by screen readers) */
  srOnly?: boolean;
}

const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, required, srOnly, children, ...props }, ref) => (
    <label
      ref={ref}
      className={cn(
        "text-sm font-medium leading-none text-foreground",
        "peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
        srOnly && "sr-only",
        className
      )}
      {...props}
    >
      {children}
      {required && (
        <span
          aria-hidden="true"
          className="ml-0.5 text-destructive"
          title="Required"
        >
          *
        </span>
      )}
    </label>
  )
);

Label.displayName = "Label";

export { Label };
