import * as React from "react";
import { cn } from "@/lib/utils";
import { Label } from "@ds/Label";

export interface FormFieldProps {
  /** Unique id — wires label htmlFor + control id automatically */
  id: string;
  label: string;
  /** Show required asterisk on label */
  required?: boolean;
  /** Hide label visually (screen-reader accessible) */
  labelSrOnly?: boolean;
  /** Hint text shown below the control */
  hint?: string;
  /** Validation error; presence switches aria-invalid on the wrapped control */
  error?: string;
  /** Additional wrapper className */
  className?: string;
  children: React.ReactNode;
}

/**
 * Wraps any form control with a label, optional hint, and error message.
 * Automatically injects `id`, `aria-describedby`, and `aria-invalid` via
 * React.cloneElement — zero boilerplate in consuming code.
 */
const FormField: React.FC<FormFieldProps> = ({
  id,
  label,
  required,
  labelSrOnly,
  hint,
  error,
  className,
  children,
}) => {
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  // Clone the single child and inject accessibility props
  const control = React.isValidElement(children)
    ? React.cloneElement(children as React.ReactElement<React.HTMLAttributes<HTMLElement>>, {
        id,
        "aria-describedby": describedBy,
        "aria-invalid": error ? true : undefined,
        "aria-required": required || undefined,
      })
    : children;

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label htmlFor={id} required={required} srOnly={labelSrOnly}>
        {label}
      </Label>

      {control}

      {hint && !error && (
        <p id={hintId} className="text-xs text-muted-foreground">
          {hint}
        </p>
      )}

      {error && (
        <p
          id={errorId}
          role="alert"
          aria-live="polite"
          className="text-xs text-destructive font-medium"
        >
          {error}
        </p>
      )}
    </div>
  );
};

FormField.displayName = "FormField";

export { FormField };
