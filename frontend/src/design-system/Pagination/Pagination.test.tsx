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
