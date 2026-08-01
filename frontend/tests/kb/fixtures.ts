/**
 * Shared KB test fixtures — deterministic, UUID-stable article objects.
 * Import these in any KB test file instead of constructing articles inline.
 */
import type { KbArticle, KbRevision } from "@/lib/kb/types";

export const AUTHOR_ID = "aaaaaaaa-0000-4000-8000-000000000001";
export const REVIEWER_ID = "bbbbbbbb-0000-4000-8000-000000000002";
export const OTHER_USER_ID = "cccccccc-0000-4000-8000-000000000003";

export const NOW = "2024-06-01T12:00:00.000Z";
export const LATER = "2024-06-02T09:00:00.000Z";

// ─── Article factories ────────────────────────────────────────────────────────

export function makeArticle(
  overrides: Partial<KbArticle> = {}
): KbArticle {
  return {
    id: "article-id-0001-0000-000000000001",
    title: "How to reset your password",
    slug: "how-to-reset-your-password",
    content: "Navigate to the login page and click Forgot Password…",
    summary: "Password reset guide",
    category: "FAQ",
    tags: ["password", "account"],
    status: "DRAFT",
    version: 1,
    authorId: AUTHOR_ID,
    reviewerId: null,
    approvedAt: null,
    publishedAt: null,
    createdAt: NOW,
    updatedAt: NOW,
    ...overrides,
  };
}

export const draftArticle = makeArticle({ status: "DRAFT" });

export const pendingArticle = makeArticle({
  id: "article-id-0002-0000-000000000002",
  status: "PENDING_REVIEW",
  reviewerId: REVIEWER_ID,
  version: 2,
  updatedAt: LATER,
});

export const approvedArticle = makeArticle({
  id: "article-id-0003-0000-000000000003",
  status: "APPROVED",
  reviewerId: REVIEWER_ID,
  approvedAt: LATER,
  version: 3,
  updatedAt: LATER,
});

export const publishedArticle = makeArticle({
  id: "article-id-0004-0000-000000000004",
  status: "PUBLISHED",
  reviewerId: REVIEWER_ID,
  approvedAt: LATER,
  publishedAt: LATER,
  version: 4,
  updatedAt: LATER,
});

export const archivedArticle = makeArticle({
  id: "article-id-0005-0000-000000000005",
  status: "ARCHIVED",
  reviewerId: REVIEWER_ID,
  approvedAt: LATER,
  publishedAt: LATER,
  version: 5,
  updatedAt: LATER,
});

export const rejectedArticle = makeArticle({
  id: "article-id-0006-0000-000000000006",
  status: "REJECTED",
  version: 2,
  updatedAt: LATER,
});

// ─── Revision factory ─────────────────────────────────────────────────────────

export function makeRevision(
  overrides: Partial<KbRevision> = {}
): KbRevision {
  return {
    id: "revision-id-0001-0000-000000000001",
    articleId: draftArticle.id,
    version: 1,
    title: draftArticle.title,
    content: draftArticle.content,
    summary: draftArticle.summary,
    action: "EDIT",
    actorId: AUTHOR_ID,
    comment: undefined,
    createdAt: NOW,
    ...overrides,
  };
}

// ─── List response factory ────────────────────────────────────────────────────

export function makeListResponse(
  items: KbArticle[] = [draftArticle],
  overrides: { page?: number; pageSize?: number; total?: number } = {}
) {
  const total = overrides.total ?? items.length;
  const pageSize = overrides.pageSize ?? 20;
  const page = overrides.page ?? 1;
  return {
    items,
    total,
    page,
    pageSize,
    totalPages: Math.ceil(total / pageSize),
  };
}
