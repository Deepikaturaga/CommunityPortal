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
