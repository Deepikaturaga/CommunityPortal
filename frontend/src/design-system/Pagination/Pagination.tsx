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
