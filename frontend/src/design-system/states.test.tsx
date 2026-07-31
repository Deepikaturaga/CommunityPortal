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
