# Implementation Report

**Slice 10 — ESLint, .gitignore, README**

## Generated Files

### `frontend/.storybook/main.ts`
```typescript
import type { StorybookConfig } from "@storybook/react-vite";

const config: StorybookConfig = {
  stories: ["../src/**/*.stories.@(ts|tsx|mdx)"],
  addons: [
    "@storybook/addon-links",
    "@storybook/addon-essentials",
    "@storybook/addon-interactions",
    "@storybook/addon-a11y",
  ],
  framework: {
    name: "@storybook/react-vite",
    options: {},
  },
  docs: {
    autodocs: "tag",
  },
  core: {
    disableTelemetry: true,
  },
};

export default config;

```

### `frontend/.storybook/preview.css`
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }

  :focus-visible {
    outline: 2px solid #2563EB;
    outline-offset: 2px;
  }

  body {
    @apply font-sans text-foreground bg-background antialiased;
  }
}

```

### `frontend/.storybook/preview.ts`
```typescript
import type { Preview } from "@storybook/react";
import "./preview.css";

const preview: Preview = {
  parameters: {
    actions: { argTypesRegex: "^on[A-Z].*" },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    a11y: {
      // axe-core config — run on every story
      config: {
        rules: [
          {
            // colour-contrast is flagged informational in Storybook white canvas;
            // enable for full CI runs
            id: "color-contrast",
            enabled: true,
          },
        ],
      },
    },
    backgrounds: {
      default: "light",
      values: [
        { name: "light", value: "#FFFFFF" },
        { name: "muted", value: "#F8FAFC" },
        { name: "dark", value: "#0F172A" },
      ],
    },
  },
  tags: ["autodocs"],
};

export default preview;

```

### `frontend/eslint.config.js`
```javascript
import js from "@eslint/js";
import tsPlugin from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks";
import jsxA11yPlugin from "eslint-plugin-jsx-a11y";
import storybookPlugin from "eslint-plugin-storybook";

/** @type {import("eslint").Linter.FlatConfig[]} */
export default [
  js.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
      react: reactPlugin,
      "react-hooks": reactHooksPlugin,
      "jsx-a11y": jsxA11yPlugin,
    },
    rules: {
      ...tsPlugin.configs.recommended.rules,
      ...reactPlugin.configs.recommended.rules,
      ...reactHooksPlugin.configs.recommended.rules,
      ...jsxA11yPlugin.configs.recommended.rules,
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off",
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    },
    settings: {
      react: { version: "detect" },
    },
  },
  {
    files: ["src/**/*.stories.{ts,tsx}"],
    plugins: { storybook: storybookPlugin },
    rules: {
      ...storybookPlugin.configs.recommended.rules,
      "react-hooks/rules-of-hooks": "off", // stories sometimes demo hooks inline
    },
  },
  {
    ignores: ["dist/**", "storybook-static/**", "node_modules/**"],
  },
];

```

### `frontend/index.html`
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Design System Shell</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
      rel="stylesheet"
    />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>

```

### `frontend/package.json`
```json
{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc --noEmit && vite build",
    "preview": "vite preview",
    "typecheck": "tsc --noEmit",
    "lint": "eslint src --ext .ts,.tsx --max-warnings 0",
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:a11y": "axe-storybook"
  },
  "dependencies": {
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "tailwind-merge": "^2.5.4"
  },
  "devDependencies": {
    "@storybook/addon-a11y": "^8.4.7",
    "@storybook/addon-essentials": "^8.4.7",
    "@storybook/addon-interactions": "^8.4.7",
    "@storybook/addon-links": "^8.4.7",
    "@storybook/blocks": "^8.4.7",
    "@storybook/react": "^8.4.7",
    "@storybook/react-vite": "^8.4.7",
    "@storybook/test": "^8.4.7",
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.1.0",
    "@testing-library/user-event": "^14.5.2",
    "@types/react": "^18.3.13",
    "@types/react-dom": "^18.3.1",
    "@typescript-eslint/eslint-plugin": "^8.15.0",
    "@typescript-eslint/parser": "^8.15.0",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "axe-storybook-testing": "^0.9.0",
    "eslint": "^9.15.0",
    "eslint-plugin-jsx-a11y": "^6.10.2",
    "eslint-plugin-react": "^7.37.2",
    "eslint-plugin-react-hooks": "^5.0.0",
    "eslint-plugin-storybook": "^0.11.1",
    "jsdom": "^25.0.1",
    "postcss": "^8.4.49",
    "storybook": "^8.4.7",
    "tailwindcss": "^3.4.15",
    "typescript": "^5.7.2",
    "vite": "^6.0.3",
    "vitest": "^2.1.6"
  }
}

```

### `frontend/postcss.config.js`
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

```

### `frontend/src/App.tsx`
```typescript
import {
  Button,
  Badge,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Spinner,
  EmptyState,
  ErrorState,
  PermissionDenied,
  Pagination,
  FormField,
  Input,
  Select,
  Textarea,
} from "@ds/index";
import { useState } from "react";

/**
 * Shell app — acts as a living kitchen-sink for the design system.
 * Not a production page; for Storybook use `npm run storybook`.
 */
export default function App() {
  const [page, setPage] = useState(1);

  return (
    <main className="min-h-screen bg-muted p-8 space-y-10">
      <h1 className="text-2xl font-bold">Design System Kitchen Sink</h1>

      {/* Buttons */}
      <section aria-labelledby="buttons-heading" className="space-y-3">
        <h2 id="buttons-heading" className="text-lg font-semibold">Buttons</h2>
        <div className="flex flex-wrap gap-2">
          {(["primary","secondary","destructive","ghost","outline","link"] as const).map((v) => (
            <Button key={v} variant={v}>{v}</Button>
          ))}
          <Button loading>Loading</Button>
          <Button disabled>Disabled</Button>
        </div>
      </section>

      {/* Badges */}
      <section aria-labelledby="badges-heading" className="space-y-3">
        <h2 id="badges-heading" className="text-lg font-semibold">Badges</h2>
        <div className="flex flex-wrap gap-2">
          {(["default","secondary","success","destructive","warning","outline","muted"] as const).map((v) => (
            <Badge key={v} variant={v}>{v}</Badge>
          ))}
        </div>
      </section>

      {/* Spinner */}
      <section aria-labelledby="spinner-heading" className="space-y-3">
        <h2 id="spinner-heading" className="text-lg font-semibold">Spinner</h2>
        <div className="flex items-center gap-4">
          {(["xs","sm","md","lg","xl"] as const).map((s) => (
            <Spinner key={s} size={s} label={`Loading ${s}`} />
          ))}
        </div>
      </section>

      {/* Form */}
      <section aria-labelledby="form-heading" className="space-y-3 max-w-sm">
        <h2 id="form-heading" className="text-lg font-semibold">Form fields</h2>
        <FormField id="app-email" label="Email" required>
          <Input type="email" placeholder="you@example.com" />
        </FormField>
        <FormField id="app-role" label="Role">
          <Select placeholder="Choose…">
            <option value="admin">Admin</option>
            <option value="viewer">Viewer</option>
          </Select>
        </FormField>
        <FormField id="app-bio" label="Bio" hint="Optional.">
          <Textarea placeholder="Tell us about yourself…" />
        </FormField>
        <FormField id="app-bad" label="Bad input" error="This field is required.">
          <Input placeholder="Oops" />
        </FormField>
      </section>

      {/* Card */}
      <section aria-labelledby="card-heading" className="space-y-3 max-w-sm">
        <h2 id="card-heading" className="text-lg font-semibold">Card</h2>
        <Card>
          <CardHeader>
            <CardTitle>Sample card</CardTitle>
            <CardDescription>Subtitle / description area.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">Card body content.</p>
          </CardContent>
        </Card>
      </section>

      {/* Pagination */}
      <section aria-labelledby="pagination-heading" className="space-y-3">
        <h2 id="pagination-heading" className="text-lg font-semibold">Pagination (page {page})</h2>
        <Pagination page={page} totalPages={20} onPageChange={setPage} />
      </section>

      {/* Feedback states */}
      <section aria-labelledby="states-heading" className="space-y-6">
        <h2 id="states-heading" className="text-lg font-semibold">Feedback states</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card noPadding>
            <EmptyState title="No items" description="Create one to get started." actionLabel="Create" />
          </Card>
          <Card noPadding>
            <ErrorState title="Load failed" description="Try again." actionLabel="Retry" />
          </Card>
          <Card noPadding>
            <PermissionDenied title="Access denied" description="Contact your admin." actionLabel="Request access" />
          </Card>
        </div>
      </section>
    </main>
  );
}

```

### `frontend/src/design-system/Badge/Badge.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { Badge } from "./Badge";

const meta = {
  title: "Design System/Badge",
  component: Badge,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "secondary", "destructive", "success", "warning", "outline", "muted"],
    },
  },
} satisfies Meta<typeof Badge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { children: "New" } };
export const Secondary: Story = { args: { variant: "secondary", children: "Draft" } };
export const Success: Story = { args: { variant: "success", children: "Active" } };
export const Destructive: Story = { args: { variant: "destructive", children: "Overdue" } };
export const Warning: Story = { args: { variant: "warning", children: "Pending" } };
export const Outline: Story = { args: { variant: "outline", children: "Beta" } };
export const Muted: Story = { args: { variant: "muted", children: "Archived" } };

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      {(["default","secondary","success","destructive","warning","outline","muted"] as const).map(
        (v) => <Badge key={v} variant={v}>{v}</Badge>
      )}
    </div>
  ),
};

```

### `frontend/src/design-system/Badge/Badge.tsx`
```typescript
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground",
        secondary: "bg-secondary text-secondary-foreground border border-border",
        destructive: "bg-destructive text-destructive-foreground",
        success: "bg-success text-success-foreground",
        warning: "bg-warning text-warning-foreground",
        outline: "border border-current text-foreground bg-transparent",
        muted: "bg-muted text-muted-foreground",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant, ...props }, ref) => (
    <span
      ref={ref}
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
);

Badge.displayName = "Badge";

export { Badge, badgeVariants };

```

### `frontend/src/design-system/Badge/index.ts`
```typescript
export { Badge, badgeVariants } from "./Badge";
export type { BadgeProps } from "./Badge";

```

### `frontend/src/design-system/Button/Button.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "./Button";

const meta = {
  title: "Design System/Button",
  component: Button,
  tags: ["autodocs"],
  parameters: {
    layout: "centered",
  },
  argTypes: {
    variant: {
      control: "select",
      options: ["primary", "secondary", "destructive", "ghost", "link", "outline"],
    },
    size: {
      control: "select",
      options: ["xs", "sm", "md", "lg", "xl", "icon"],
    },
    loading: { control: "boolean" },
    disabled: { control: "boolean" },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: { variant: "primary", children: "Primary button" },
};

export const Secondary: Story = {
  args: { variant: "secondary", children: "Secondary button" },
};

export const Destructive: Story = {
  args: { variant: "destructive", children: "Delete item" },
};

export const Ghost: Story = {
  args: { variant: "ghost", children: "Ghost button" },
};

export const Link: Story = {
  args: { variant: "link", children: "Link button" },
};

export const Outline: Story = {
  args: { variant: "outline", children: "Outline button" },
};

export const Loading: Story = {
  args: { variant: "primary", children: "Saving…", loading: true },
};

export const Disabled: Story = {
  args: { variant: "primary", children: "Cannot click", disabled: true },
};

export const Small: Story = {
  args: { variant: "primary", children: "Small", size: "sm" },
};

export const Large: Story = {
  args: { variant: "primary", children: "Large", size: "lg" },
};

export const WithLeftIcon: Story = {
  args: {
    variant: "primary",
    children: "Add item",
    leftIcon: (
      <svg
        aria-hidden="true"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path d="M12 5v14M5 12h14" strokeLinecap="round" />
      </svg>
    ),
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-3">
      {(
        ["primary", "secondary", "destructive", "ghost", "outline", "link"] as const
      ).map((v) => (
        <Button key={v} variant={v}>
          {v.charAt(0).toUpperCase() + v.slice(1)}
        </Button>
      ))}
    </div>
  ),
};

```

### `frontend/src/design-system/Button/Button.test.tsx`
```typescript
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "@ds/Button";

describe("Button", () => {
  it("renders its label", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: /click me/i })).toBeInTheDocument();
  });

  it("calls onClick when clicked", async () => {
    const handler = vi.fn();
    render(<Button onClick={handler}>Go</Button>);
    await userEvent.click(screen.getByRole("button"));
    expect(handler).toHaveBeenCalledOnce();
  });

  it("is disabled when the disabled prop is set", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("shows loading spinner and disables button when loading", () => {
    render(<Button loading>Save</Button>);
    const btn = screen.getByRole("button");
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute("aria-busy", "true");
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("does not fire onClick while loading", async () => {
    const handler = vi.fn();
    render(<Button loading onClick={handler}>Save</Button>);
    await userEvent.click(screen.getByRole("button"));
    expect(handler).not.toHaveBeenCalled();
  });

  it("applies variant class for destructive", () => {
    const { container } = render(<Button variant="destructive">Delete</Button>);
    expect(container.firstChild).toHaveClass("bg-destructive");
  });
});

```

### `frontend/src/design-system/Button/Button.tsx`
```typescript
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";
import { cn } from "@/lib/utils";
import { Spinner } from "@ds/Spinner";

// ---------------------------------------------------------------------------
// Variant map
// ---------------------------------------------------------------------------
const buttonVariants = cva(
  // base styles applied to every button
  [
    "inline-flex items-center justify-center gap-2 whitespace-nowrap",
    "rounded-md font-medium transition-colors",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    "disabled:pointer-events-none disabled:opacity-50",
    "select-none",
  ],
  {
    variants: {
      variant: {
        primary: [
          "bg-primary text-primary-foreground",
          "hover:bg-primary-hover active:bg-primary-active",
        ],
        secondary: [
          "bg-secondary text-secondary-foreground border border-border",
          "hover:bg-secondary-hover active:bg-secondary-active",
        ],
        destructive: [
          "bg-destructive text-destructive-foreground",
          "hover:bg-destructive-hover",
        ],
        ghost: [
          "bg-transparent text-foreground",
          "hover:bg-secondary hover:text-secondary-foreground",
        ],
        link: [
          "bg-transparent text-primary underline-offset-4 hover:underline",
          "p-0 h-auto",
        ],
        outline: [
          "border border-primary text-primary bg-transparent",
          "hover:bg-primary hover:text-primary-foreground",
        ],
      },
      size: {
        xs: "h-7 px-2.5 text-xs",
        sm: "h-8 px-3 text-sm",
        md: "h-9 px-4 text-sm",
        lg: "h-10 px-5 text-base",
        xl: "h-12 px-6 text-base",
        icon: "h-9 w-9 p-0",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** Show a loading spinner and disable the button */
  loading?: boolean;
  /** Icon rendered before the label */
  leftIcon?: React.ReactNode;
  /** Icon rendered after the label */
  rightIcon?: React.ReactNode;
  /** Render as a different element (e.g. anchor) */
  asChild?: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      loading = false,
      leftIcon,
      rightIcon,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        disabled={isDisabled}
        aria-busy={loading || undefined}
        aria-disabled={isDisabled || undefined}
        {...props}
      >
        {loading ? (
          <Spinner
            size="sm"
            aria-hidden="true"
            className={variant === "primary" ? "text-white" : "text-current"}
          />
        ) : (
          leftIcon && <span aria-hidden="true">{leftIcon}</span>
        )}
        {children && <span>{children}</span>}
        {!loading && rightIcon && (
          <span aria-hidden="true">{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button, buttonVariants };

```

### `frontend/src/design-system/Button/index.ts`
```typescript
export { Button, buttonVariants } from "./Button";
export type { ButtonProps } from "./Button";

```

### `frontend/src/design-system/Card/Card.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "./Card";
import { Button } from "@ds/Button";

const meta = {
  title: "Design System/Card",
  component: Card,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-80"><S /></div>],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card>
      <CardHeader>
        <CardTitle>Card title</CardTitle>
        <CardDescription>Optional description text.</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-foreground">Card body content goes here.</p>
      </CardContent>
      <CardFooter>
        <Button size="sm">Action</Button>
        <Button size="sm" variant="secondary">Cancel</Button>
      </CardFooter>
    </Card>
  ),
};

export const Highlighted: Story = {
  render: () => (
    <Card highlighted>
      <CardContent>
        <p className="text-sm">This card is highlighted (e.g. selected).</p>
      </CardContent>
    </Card>
  ),
};

export const Borderless: Story = {
  render: () => (
    <Card borderless className="bg-muted">
      <CardContent>
        <p className="text-sm">No border, muted background.</p>
      </CardContent>
    </Card>
  ),
};

```

### `frontend/src/design-system/Card/Card.tsx`
```typescript
import * as React from "react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Card root
// ---------------------------------------------------------------------------
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Remove default padding */
  noPadding?: boolean;
  /** Remove the border */
  borderless?: boolean;
  /** Highlight state (e.g. selected row) */
  highlighted?: boolean;
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, noPadding, borderless, highlighted, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-lg bg-background shadow-sm",
        !borderless && "border border-border",
        !noPadding && "p-6",
        highlighted && "ring-2 ring-primary",
        className
      )}
      {...props}
    />
  )
);
Card.displayName = "Card";

// ---------------------------------------------------------------------------
// Card sub-components
// ---------------------------------------------------------------------------
const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex flex-col gap-1.5 pb-4", className)}
      {...props}
    />
  )
);
CardHeader.displayName = "CardHeader";

const CardTitle = React.forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn("text-lg font-semibold leading-none tracking-tight", className)}
      {...props}
    />
  )
);
CardTitle.displayName = "CardTitle";

const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  )
);
CardDescription.displayName = "CardDescription";

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("", className)} {...props} />
  )
);
CardContent.displayName = "CardContent";

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex items-center gap-2 pt-4", className)}
      {...props}
    />
  )
);
CardFooter.displayName = "CardFooter";

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter };

```

### `frontend/src/design-system/Card/index.ts`
```typescript
export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "./Card";
export type { CardProps } from "./Card";

```

### `frontend/src/design-system/EmptyState/EmptyState.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { EmptyState } from "./EmptyState";

const meta = {
  title: "Design System/EmptyState",
  component: EmptyState,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-[480px] border border-border rounded-lg"><S /></div>],
} satisfies Meta<typeof EmptyState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { title: "No results found" },
};

export const WithDescription: Story = {
  args: {
    title: "No items yet",
    description: "Create your first item to get started.",
  },
};

export const WithAction: Story = {
  args: {
    title: "No projects",
    description: "Get started by creating a new project.",
    actionLabel: "Create project",
    onAction: () => alert("Create project"),
  },
};

export const WithBothActions: Story = {
  args: {
    title: "Inbox zero 🎉",
    description: "You've handled everything. Check back later.",
    actionLabel: "Refresh",
    secondaryActionLabel: "Go to archive",
  },
};

export const CustomIcon: Story = {
  args: {
    title: "No files uploaded",
    description: "Drag and drop files here, or click to browse.",
    actionLabel: "Browse files",
    icon: (
      <svg
        aria-hidden="true"
        width="48"
        height="48"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.5}
        className="opacity-40"
      >
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
    ),
  },
};

```

### `frontend/src/design-system/EmptyState/EmptyState.tsx`
```typescript
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

```

### `frontend/src/design-system/EmptyState/index.ts`
```typescript
export { EmptyState } from "./EmptyState";
export type { EmptyStateProps } from "./EmptyState";

```

### `frontend/src/design-system/ErrorState/ErrorState.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { ErrorState } from "./ErrorState";

const meta = {
  title: "Design System/ErrorState",
  component: ErrorState,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-[480px] border border-border rounded-lg"><S /></div>],
} satisfies Meta<typeof ErrorState>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: {} };

export const WithRetry: Story = {
  args: {
    title: "Failed to load data",
    description: "We could not fetch the resource. Check your connection and try again.",
    actionLabel: "Retry",
    onAction: () => alert("Retry"),
  },
};

export const WithCorrelationId: Story = {
  args: {
    title: "Unexpected error",
    description: "Our team has been notified. Please quote the error ID when contacting support.",
    correlationId: "err_01J9ABCDEF",
    actionLabel: "Retry",
    secondaryActionLabel: "Contact support",
  },
};

export const NetworkError: Story = {
  args: {
    title: "Network error",
    description: "No internet connection detected.",
    actionLabel: "Try again",
  },
};

```

### `frontend/src/design-system/ErrorState/ErrorState.tsx`
```typescript
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

```

### `frontend/src/design-system/ErrorState/index.ts`
```typescript
export { ErrorState } from "./ErrorState";
export type { ErrorStateProps } from "./ErrorState";

```

### `frontend/src/design-system/FormField/FormField.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { FormField } from "./FormField";
import { Input } from "@ds/Input";
import { Select } from "@ds/Select";
import { Textarea } from "@ds/Textarea";

const meta = {
  title: "Design System/FormField",
  component: FormField,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-80"><S /></div>],
} satisfies Meta<typeof FormField>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    id: "email",
    label: "Email address",
    children: <Input type="email" placeholder="you@example.com" />,
  },
};

export const WithHint: Story = {
  args: {
    id: "username",
    label: "Username",
    hint: "Must be 3–20 characters, letters and numbers only.",
    children: <Input placeholder="cool_name42" />,
  },
};

export const WithError: Story = {
  args: {
    id: "password",
    label: "Password",
    required: true,
    error: "Password must be at least 8 characters.",
    children: <Input type="password" defaultValue="abc" />,
  },
};

export const WithSelect: Story = {
  args: {
    id: "role",
    label: "Role",
    required: true,
    children: (
      <Select placeholder="Choose a role…">
        <option value="admin">Admin</option>
        <option value="editor">Editor</option>
      </Select>
    ),
  },
};

export const WithTextarea: Story = {
  args: {
    id: "bio",
    label: "Bio",
    hint: "Tell us a bit about yourself.",
    children: <Textarea placeholder="I am…" />,
  },
};

export const FullForm: Story = {
  render: () => (
    <form
      className="flex flex-col gap-4"
      onSubmit={(e) => e.preventDefault()}
      noValidate
    >
      <FormField id="f-email" label="Email" required>
        <Input type="email" placeholder="you@example.com" />
      </FormField>
      <FormField id="f-role" label="Role" required>
        <Select placeholder="Choose…">
          <option value="admin">Admin</option>
          <option value="viewer">Viewer</option>
        </Select>
      </FormField>
      <FormField id="f-bio" label="Bio" hint="Optional.">
        <Textarea placeholder="Say something…" />
      </FormField>
      <FormField id="f-error" label="Bad field" error="This field is required.">
        <Input placeholder="Oops" />
      </FormField>
    </form>
  ),
};

```

### `frontend/src/design-system/FormField/FormField.test.tsx`
```typescript
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { FormField } from "@ds/FormField";
import { Input } from "@ds/Input";

describe("FormField", () => {
  it("renders label associated with the control", () => {
    render(
      <FormField id="email" label="Email address">
        <Input />
      </FormField>
    );
    const label = screen.getByText(/email address/i);
    expect(label).toHaveAttribute("for", "email");
    expect(screen.getByRole("textbox")).toHaveAttribute("id", "email");
  });

  it("shows required asterisk on label", () => {
    render(
      <FormField id="name" label="Full name" required>
        <Input />
      </FormField>
    );
    expect(screen.getByText("*")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveAttribute("aria-required", "true");
  });

  it("shows hint text and wires aria-describedby", () => {
    render(
      <FormField id="user" label="Username" hint="3-20 chars">
        <Input />
      </FormField>
    );
    const hint = screen.getByText(/3-20 chars/i);
    expect(hint).toHaveAttribute("id", "user-hint");
    expect(screen.getByRole("textbox")).toHaveAttribute("aria-describedby", "user-hint");
  });

  it("shows error and marks aria-invalid", () => {
    render(
      <FormField id="pwd" label="Password" error="Too short">
        <Input />
      </FormField>
    );
    const error = screen.getByRole("alert");
    expect(error).toHaveTextContent("Too short");
    expect(screen.getByRole("textbox")).toHaveAttribute("aria-invalid", "true");
  });

  it("hides hint when error is present", () => {
    render(
      <FormField id="x" label="Field" hint="Some hint" error="Required">
        <Input />
      </FormField>
    );
    expect(screen.queryByText(/some hint/i)).not.toBeInTheDocument();
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});

```

### `frontend/src/design-system/FormField/FormField.tsx`
```typescript
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

```

### `frontend/src/design-system/FormField/index.ts`
```typescript
export { FormField } from "./FormField";
export type { FormFieldProps } from "./FormField";

```

### `frontend/src/design-system/Input/Input.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { Input } from "./Input";

const meta = {
  title: "Design System/Input",
  component: Input,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-72"><S /></div>],
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { placeholder: "Enter text…" } };
export const Filled: Story = { args: { defaultValue: "john@example.com", type: "email" } };
export const Invalid: Story = { args: { invalid: true, defaultValue: "bad-email", "aria-describedby": "err-1" } };
export const Disabled: Story = { args: { disabled: true, placeholder: "Disabled" } };
export const WithLeftAddon: Story = {
  args: {
    placeholder: "Search…",
    leftAddon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
    ),
  },
};
export const Password: Story = { args: { type: "password", placeholder: "Password" } };

```

### `frontend/src/design-system/Input/Input.tsx`
```typescript
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

```

### `frontend/src/design-system/Input/index.ts`
```typescript
export { Input } from "./Input";
export type { InputProps } from "./Input";

```

### `frontend/src/design-system/Label/Label.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { Label } from "./Label";

const meta = {
  title: "Design System/Label",
  component: Label,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
} satisfies Meta<typeof Label>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { children: "Email address", htmlFor: "email" } };
export const Required: Story = { args: { children: "Full name", htmlFor: "name", required: true } };
export const SrOnly: Story = { args: { children: "Hidden label", htmlFor: "hidden", srOnly: true } };

```

### `frontend/src/design-system/Label/Label.tsx`
```typescript
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

```

### `frontend/src/design-system/Label/index.ts`
```typescript
export { Label } from "./Label";
export type { LabelProps } from "./Label";

```

### `frontend/src/design-system/Pagination/Pagination.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { Pagination } from "./Pagination";

const meta = {
  title: "Design System/Pagination",
  component: Pagination,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  argTypes: {
    page: { control: { type: "number", min: 1 } },
    totalPages: { control: { type: "number", min: 1 } },
    siblingCount: { control: { type: "number", min: 0, max: 3 } },
    disabled: { control: "boolean" },
  },
} satisfies Meta<typeof Pagination>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: { page: 3, totalPages: 10, onPageChange: () => {} },
};

export const FewPages: Story = {
  args: { page: 1, totalPages: 3, onPageChange: () => {} },
};

export const LastPage: Story = {
  args: { page: 10, totalPages: 10, onPageChange: () => {} },
};

export const Disabled: Story = {
  args: { page: 5, totalPages: 10, onPageChange: () => {}, disabled: true },
};

export const Interactive: Story = {
  render: () => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const [page, setPage] = useState(1);
    return (
      <div className="flex flex-col gap-4 items-center">
        <p className="text-sm text-muted-foreground">Current page: {page}</p>
        <Pagination page={page} totalPages={20} onPageChange={setPage} />
      </div>
    );
  },
};

```

### `frontend/src/design-system/Pagination/Pagination.test.tsx`
```typescript
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Pagination } from "@ds/Pagination";

describe("Pagination", () => {
  it("renders navigation landmark", () => {
    render(<Pagination page={3} totalPages={10} onPageChange={vi.fn()} />);
    expect(screen.getByRole("navigation", { name: /pagination/i })).toBeInTheDocument();
  });

  it("returns null when totalPages <= 1", () => {
    const { container } = render(
      <Pagination page={1} totalPages={1} onPageChange={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("marks current page with aria-current=page", () => {
    render(<Pagination page={3} totalPages={5} onPageChange={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Page 3" })).toHaveAttribute(
      "aria-current",
      "page"
    );
  });

  it("disables Prev button on first page", () => {
    render(<Pagination page={1} totalPages={5} onPageChange={vi.fn()} />);
    expect(screen.getByRole("button", { name: /previous page/i })).toBeDisabled();
  });

  it("disables Next button on last page", () => {
    render(<Pagination page={5} totalPages={5} onPageChange={vi.fn()} />);
    expect(screen.getByRole("button", { name: /next page/i })).toBeDisabled();
  });

  it("calls onPageChange with next page when Next is clicked", async () => {
    const handler = vi.fn();
    render(<Pagination page={3} totalPages={10} onPageChange={handler} />);
    await userEvent.click(screen.getByRole("button", { name: /next page/i }));
    expect(handler).toHaveBeenCalledWith(4);
  });

  it("calls onPageChange with prev page when Prev is clicked", async () => {
    const handler = vi.fn();
    render(<Pagination page={3} totalPages={10} onPageChange={handler} />);
    await userEvent.click(screen.getByRole("button", { name: /previous page/i }));
    expect(handler).toHaveBeenCalledWith(2);
  });

  it("does not call onPageChange when disabled", async () => {
    const handler = vi.fn();
    render(
      <Pagination page={3} totalPages={10} onPageChange={handler} disabled />
    );
    await userEvent.click(screen.getByRole("button", { name: /next page/i }));
    expect(handler).not.toHaveBeenCalled();
  });
});

```

### `frontend/src/design-system/Pagination/Pagination.tsx`
```typescript
import * as React from "react";
import { cn } from "@/lib/utils";

export interface PaginationProps {
  /** Current page (1-based) */
  page: number;
  /** Total number of pages */
  totalPages: number;
  /** Called with the new page number when user navigates */
  onPageChange: (page: number) => void;
  /** Max page buttons to show (excluding prev/next) */
  siblingCount?: number;
  /** Additional className for the nav element */
  className?: string;
  /** Disable all controls (e.g. during loading) */
  disabled?: boolean;
}

// ---------------------------------------------------------------------------
// Range helper
// ---------------------------------------------------------------------------
function range(start: number, end: number): number[] {
  return Array.from({ length: end - start + 1 }, (_, i) => start + i);
}

const DOTS = "…" as const;

function usePaginationRange(
  page: number,
  totalPages: number,
  siblingCount: number
): Array<number | typeof DOTS> {
  if (totalPages <= 0) return [];

  const totalPageNumbers = siblingCount * 2 + 5; // first + last + current ± siblings + 2×DOTS

  if (totalPageNumbers >= totalPages) {
    return range(1, totalPages);
  }

  const leftSiblingIndex = Math.max(page - siblingCount, 1);
  const rightSiblingIndex = Math.min(page + siblingCount, totalPages);

  const showLeftDots = leftSiblingIndex > 2;
  const showRightDots = rightSiblingIndex < totalPages - 1;

  const firstPageIndex = 1;
  const lastPageIndex = totalPages;

  if (!showLeftDots && showRightDots) {
    const leftItemCount = 3 + 2 * siblingCount;
    return [...range(firstPageIndex, leftItemCount), DOTS, lastPageIndex];
  }

  if (showLeftDots && !showRightDots) {
    const rightItemCount = 3 + 2 * siblingCount;
    return [firstPageIndex, DOTS, ...range(totalPages - rightItemCount + 1, lastPageIndex)];
  }

  return [
    firstPageIndex,
    DOTS,
    ...range(leftSiblingIndex, rightSiblingIndex),
    DOTS,
    lastPageIndex,
  ];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
const Pagination: React.FC<PaginationProps> = ({
  page,
  totalPages,
  onPageChange,
  siblingCount = 1,
  className,
  disabled = false,
}) => {
  const paginationRange = usePaginationRange(page, totalPages, siblingCount);

  if (totalPages <= 1) return null;

  const isPrev = page > 1;
  const isNext = page < totalPages;

  const btnBase = cn(
    "inline-flex items-center justify-center h-8 min-w-[2rem] px-2 rounded-md text-sm",
    "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
    "disabled:pointer-events-none disabled:opacity-50"
  );

  return (
    <nav
      role="navigation"
      aria-label="Pagination"
      className={cn("flex items-center gap-1", className)}
    >
      {/* Previous */}
      <button
        className={cn(btnBase, "border border-border hover:bg-secondary gap-1 px-3")}
        onClick={() => onPageChange(page - 1)}
        disabled={!isPrev || disabled}
        aria-label="Previous page"
      >
        <svg
          aria-hidden="true"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
        >
          <path d="m15 18-6-6 6-6" />
        </svg>
        <span className="sr-only sm:not-sr-only">Prev</span>
      </button>

      {/* Page buttons */}
      {paginationRange.map((item, idx) =>
        item === DOTS ? (
          <span
            key={`dots-${idx}`}
            aria-hidden="true"
            className="inline-flex items-center justify-center h-8 w-8 text-sm text-muted-foreground"
          >
            {DOTS}
          </span>
        ) : (
          <button
            key={item}
            onClick={() => onPageChange(item)}
            disabled={disabled}
            aria-label={`Page ${item}`}
            aria-current={item === page ? "page" : undefined}
            className={cn(
              btnBase,
              item === page
                ? "bg-primary text-primary-foreground font-semibold"
                : "border border-border hover:bg-secondary"
            )}
          >
            {item}
          </button>
        )
      )}

      {/* Next */}
      <button
        className={cn(btnBase, "border border-border hover:bg-secondary gap-1 px-3")}
        onClick={() => onPageChange(page + 1)}
        disabled={!isNext || disabled}
        aria-label="Next page"
      >
        <span className="sr-only sm:not-sr-only">Next</span>
        <svg
          aria-hidden="true"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
        >
          <path d="m9 18 6-6-6-6" />
        </svg>
      </button>
    </nav>
  );
};

Pagination.displayName = "Pagination";

export { Pagination };

```

### `frontend/src/design-system/Pagination/index.ts`
```typescript
export { Pagination } from "./Pagination";
export type { PaginationProps } from "./Pagination";

```

### `frontend/src/design-system/PermissionDenied/PermissionDenied.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { PermissionDenied } from "./PermissionDenied";

const meta = {
  title: "Design System/PermissionDenied",
  component: PermissionDenied,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-[480px] border border-border rounded-lg"><S /></div>],
} satisfies Meta<typeof PermissionDenied>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: {} };

export const WithAction: Story = {
  args: {
    title: "Insufficient permissions",
    description: "You need the 'Admin' role to manage users.",
    actionLabel: "Request access",
    onAction: () => alert("Request sent"),
  },
};

export const WithBothActions: Story = {
  args: {
    title: "Members only",
    description: "This area is restricted to team members.",
    actionLabel: "Join team",
    secondaryActionLabel: "Go back",
    onSecondaryAction: () => history.back(),
  },
};

export const CustomTitle: Story = {
  args: {
    title: "Subscription required",
    description: "Upgrade to a Pro plan to access this feature.",
    actionLabel: "Upgrade now",
  },
};

```

### `frontend/src/design-system/PermissionDenied/PermissionDenied.tsx`
```typescript
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

```

### `frontend/src/design-system/PermissionDenied/index.ts`
```typescript
export { PermissionDenied } from "./PermissionDenied";
export type { PermissionDeniedProps } from "./PermissionDenied";

```

### `frontend/src/design-system/Select/Select.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { Select } from "./Select";

const meta = {
  title: "Design System/Select",
  component: Select,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-64"><S /></div>],
} satisfies Meta<typeof Select>;

export default meta;
type Story = StoryObj<typeof meta>;

const options = (
  <>
    <option value="admin">Admin</option>
    <option value="editor">Editor</option>
    <option value="viewer">Viewer</option>
  </>
);

export const Default: Story = { args: { children: options, defaultValue: "editor" } };
export const WithPlaceholder: Story = {
  args: { children: options, placeholder: "Choose a role…" },
};
export const Invalid: Story = { args: { children: options, invalid: true } };
export const Disabled: Story = { args: { children: options, disabled: true, defaultValue: "viewer" } };

```

### `frontend/src/design-system/Select/Select.tsx`
```typescript
import * as React from "react";
import { cn } from "@/lib/utils";

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {
  /** Options passed as children (option/optgroup elements) */
  children: React.ReactNode;
  /** Highlight as invalid */
  invalid?: boolean;
  /** Placeholder option shown when no value is selected */
  placeholder?: string;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, invalid, placeholder, children, ...props }, ref) => (
    <div className="relative w-full">
      <select
        ref={ref}
        aria-invalid={invalid || undefined}
        className={cn(
          "peer flex h-9 w-full appearance-none rounded-md border border-input",
          "bg-background px-3 py-1 pr-9 text-sm shadow-sm",
          "transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0",
          "disabled:cursor-not-allowed disabled:opacity-50",
          invalid && "border-destructive focus-visible:ring-destructive",
          className
        )}
        {...props}
      >
        {placeholder && (
          <option value="" disabled hidden>
            {placeholder}
          </option>
        )}
        {children}
      </select>
      {/* Chevron icon */}
      <span
        aria-hidden="true"
        className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2.5}
          strokeLinecap="round"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </span>
    </div>
  )
);

Select.displayName = "Select";

export { Select };

```

### `frontend/src/design-system/Select/index.ts`
```typescript
export { Select } from "./Select";
export type { SelectProps } from "./Select";

```

### `frontend/src/design-system/Spinner/Spinner.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { Spinner } from "./Spinner";

const meta = {
  title: "Design System/Spinner",
  component: Spinner,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  argTypes: {
    size: { control: "select", options: ["xs", "sm", "md", "lg", "xl"] },
  },
} satisfies Meta<typeof Spinner>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: {} };
export const Small: Story = { args: { size: "sm" } };
export const Large: Story = { args: { size: "xl" } };
export const Custom: Story = {
  args: { size: "lg", label: "Fetching data…", className: "text-primary" },
};

```

### `frontend/src/design-system/Spinner/Spinner.tsx`
```typescript
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

```

### `frontend/src/design-system/Spinner/index.ts`
```typescript
export { Spinner, spinnerVariants } from "./Spinner";
export type { SpinnerProps } from "./Spinner";

```

### `frontend/src/design-system/Textarea/Textarea.stories.tsx`
```typescript
import type { Meta, StoryObj } from "@storybook/react";
import { Textarea } from "./Textarea";

const meta = {
  title: "Design System/Textarea",
  component: Textarea,
  tags: ["autodocs"],
  parameters: { layout: "centered" },
  decorators: [(S) => <div className="w-80"><S /></div>],
} satisfies Meta<typeof Textarea>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = { args: { placeholder: "Enter a description…" } };
export const Filled: Story = { args: { defaultValue: "Lorem ipsum dolor sit amet." } };
export const Invalid: Story = { args: { invalid: true, defaultValue: "Too short" } };
export const Disabled: Story = { args: { disabled: true, placeholder: "Read only" } };
export const NoResize: Story = { args: { resize: "none", placeholder: "Cannot resize" } };

```

### `frontend/src/design-system/Textarea/Textarea.tsx`
```typescript
import * as React from "react";
import { cn } from "@/lib/utils";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Highlight as invalid */
  invalid?: boolean;
  /** Resize behaviour */
  resize?: "none" | "vertical" | "horizontal" | "both";
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, invalid, resize = "vertical", ...props }, ref) => (
    <textarea
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(
        "flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm",
        "placeholder:text-muted-foreground",
        "transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0",
        "disabled:cursor-not-allowed disabled:opacity-50",
        invalid && "border-destructive focus-visible:ring-destructive",
        resize === "none" && "resize-none",
        resize === "vertical" && "resize-y",
        resize === "horizontal" && "resize-x",
        resize === "both" && "resize",
        className
      )}
      {...props}
    />
  )
);

Textarea.displayName = "Textarea";

export { Textarea };

```

### `frontend/src/design-system/Textarea/index.ts`
```typescript
export { Textarea } from "./Textarea";
export type { TextareaProps } from "./Textarea";

```

### `frontend/src/design-system/index.ts`
```typescript
// ─── Primitives ───────────────────────────────────────────────────────────────
export { Button, buttonVariants } from "./Button";
export type { ButtonProps } from "./Button";

export { Spinner, spinnerVariants } from "./Spinner";
export type { SpinnerProps } from "./Spinner";

export { Badge, badgeVariants } from "./Badge";
export type { BadgeProps } from "./Badge";

// ─── Form ─────────────────────────────────────────────────────────────────────
export { Label } from "./Label";
export type { LabelProps } from "./Label";

export { Input } from "./Input";
export type { InputProps } from "./Input";

export { Textarea } from "./Textarea";
export type { TextareaProps } from "./Textarea";

export { Select } from "./Select";
export type { SelectProps } from "./Select";

export { FormField } from "./FormField";
export type { FormFieldProps } from "./FormField";

// ─── Layout ───────────────────────────────────────────────────────────────────
export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "./Card";
export type { CardProps } from "./Card";

// ─── Navigation ───────────────────────────────────────────────────────────────
export { Pagination } from "./Pagination";
export type { PaginationProps } from "./Pagination";

// ─── Feedback / State ─────────────────────────────────────────────────────────
export { EmptyState } from "./EmptyState";
export type { EmptyStateProps } from "./EmptyState";

export { ErrorState } from "./ErrorState";
export type { ErrorStateProps } from "./ErrorState";

export { PermissionDenied } from "./PermissionDenied";
export type { PermissionDeniedProps } from "./PermissionDenied";

```

### `frontend/src/design-system/states.test.tsx`
```typescript
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { EmptyState } from "@ds/EmptyState";
import { ErrorState } from "@ds/ErrorState";
import { PermissionDenied } from "@ds/PermissionDenied";

describe("EmptyState", () => {
  it("renders with role=status", () => {
    render(<EmptyState title="Nothing here" />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("shows title and description", () => {
    render(<EmptyState title="No items" description="Create one." />);
    expect(screen.getByText("No items")).toBeInTheDocument();
    expect(screen.getByText("Create one.")).toBeInTheDocument();
  });

  it("renders action button when actionLabel given", () => {
    render(<EmptyState title="Empty" actionLabel="Add item" />);
    expect(screen.getByRole("button", { name: /add item/i })).toBeInTheDocument();
  });
});

describe("ErrorState", () => {
  it("renders with role=alert", () => {
    render(<ErrorState title="Oops" />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("shows correlation ID when provided", () => {
    render(<ErrorState correlationId="err_123" />);
    expect(screen.getByText(/err_123/)).toBeInTheDocument();
  });
});

describe("PermissionDenied", () => {
  it("renders with role=alert", () => {
    render(<PermissionDenied />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("shows default title", () => {
    render(<PermissionDenied />);
    expect(screen.getByText(/access denied/i)).toBeInTheDocument();
  });

  it("renders both action buttons when provided", () => {
    render(
      <PermissionDenied
        actionLabel="Request access"
        secondaryActionLabel="Go back"
      />
    );
    expect(
      screen.getByRole("button", { name: /request access/i })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /go back/i })).toBeInTheDocument();
  });
});

```

### `frontend/src/index.css`
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }

  :focus-visible {
    outline: 2px solid #2563EB;
    outline-offset: 2px;
  }

  html {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  body {
    @apply text-foreground bg-background;
    margin: 0;
  }
}

```

### `frontend/src/lib/utils.ts`
```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind classes safely, resolving conflicts with tailwind-merge
 * and conditional classes with clsx.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

```

### `frontend/src/main.tsx`
```typescript
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";

const root = document.getElementById("root");
if (!root) throw new Error("Root element #root not found");

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>
);

```

### `frontend/src/test/setup.ts`
```typescript
import "@testing-library/jest-dom";

```

### `frontend/tailwind.config.ts`
```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
    "./.storybook/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        /* Design tokens — single source of truth */
        primary: {
          DEFAULT: "#2563EB",
          hover: "#1D4ED8",
          active: "#1E40AF",
          foreground: "#FFFFFF",
        },
        secondary: {
          DEFAULT: "#F1F5F9",
          hover: "#E2E8F0",
          active: "#CBD5E1",
          foreground: "#0F172A",
        },
        destructive: {
          DEFAULT: "#DC2626",
          hover: "#B91C1C",
          foreground: "#FFFFFF",
        },
        success: {
          DEFAULT: "#16A34A",
          foreground: "#FFFFFF",
        },
        warning: {
          DEFAULT: "#D97706",
          foreground: "#FFFFFF",
        },
        muted: {
          DEFAULT: "#F8FAFC",
          foreground: "#64748B",
        },
        border: "#E2E8F0",
        input: "#E2E8F0",
        ring: "#2563EB",
        background: "#FFFFFF",
        foreground: "#0F172A",
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        sm: "0.25rem",
        md: "0.375rem",
        lg: "0.5rem",
        xl: "0.75rem",
      },
      boxShadow: {
        focus: "0 0 0 3px rgba(37,99,235,0.35)",
      },
    },
  },
  plugins: [],
};

export default config;

```

### `frontend/tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@ds/*": ["src/design-system/*"]
    }
  },
  "include": ["src", ".storybook"],
  "exclude": ["node_modules", "dist", "storybook-static"]
}

```

### `frontend/vite.config.ts`
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
      "@ds": resolve(__dirname, "src/design-system"),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
  },
});

```