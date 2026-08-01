/**
 * KB validation helpers — pure functions, no I/O.
 * Used server-side in route handlers and client-side before form submission.
 */
import { z } from "zod";
import {
  CreateKbArticleInputSchema,
  UpdateKbArticleInputSchema,
  ApproveKbArticleInputSchema,
  RejectKbArticleInputSchema,
  SubmitForReviewInputSchema,
  KbArticle,
  KbStatus,
  CreateKbArticleInput,
  UpdateKbArticleInput,
} from "./types";

// ─── Generic parse helpers ────────────────────────────────────────────────────

export type ValidationResult<T> =
  | { success: true; data: T }
  | { success: false; errors: Record<string, string[]> };

function parseSchema<T>(
  schema: z.ZodSchema<T>,
  input: unknown
): ValidationResult<T> {
  const result = schema.safeParse(input);
  if (result.success) {
    return { success: true, data: result.data };
  }
  const errors: Record<string, string[]> = {};
  for (const issue of result.error.issues) {
    const path = issue.path.join(".") || "_";
    if (!errors[path]) errors[path] = [];
    errors[path].push(issue.message);
  }
  return { success: false, errors };
}

// ─── Public validators ────────────────────────────────────────────────────────

export function validateCreateArticle(
  input: unknown
): ValidationResult<CreateKbArticleInput> {
  return parseSchema(CreateKbArticleInputSchema, input);
}

export function validateUpdateArticle(
  input: unknown
): ValidationResult<UpdateKbArticleInput> {
  return parseSchema(UpdateKbArticleInputSchema, input);
}

export function validateApproveArticle(input: unknown) {
  return parseSchema(ApproveKbArticleInputSchema, input);
}

export function validateRejectArticle(input: unknown) {
  return parseSchema(RejectKbArticleInputSchema, input);
}

export function validateSubmitForReview(input: unknown) {
  return parseSchema(SubmitForReviewInputSchema, input);
}

// ─── Business-rule guards ─────────────────────────────────────────────────────

/** Status transitions allowed by the KB workflow. */
const ALLOWED_TRANSITIONS: Record<KbStatus, KbStatus[]> = {
  DRAFT: ["PENDING_REVIEW"],
  PENDING_REVIEW: ["APPROVED", "REJECTED"],
  APPROVED: ["PUBLISHED", "REJECTED"],
  PUBLISHED: ["ARCHIVED"],
  ARCHIVED: [],
  REJECTED: ["DRAFT"],
};

export function canTransition(from: KbStatus, to: KbStatus): boolean {
  return ALLOWED_TRANSITIONS[from]?.includes(to) ?? false;
}

export function assertTransition(from: KbStatus, to: KbStatus): void {
  if (!canTransition(from, to)) {
    throw new Error(
      `Invalid KB status transition: ${from} → ${to}`
    );
  }
}

/**
 * Returns true if the article is editable by authors.
 * Only DRAFT and REJECTED articles may be edited.
 */
export function isEditable(status: KbStatus): boolean {
  return status === "DRAFT" || status === "REJECTED";
}

/**
 * Returns true if the article is awaiting reviewer action.
 */
export function isAwaitingReview(status: KbStatus): boolean {
  return status === "PENDING_REVIEW";
}

/**
 * Returns true if the article is awaiting publish action.
 */
export function isAwaitingPublish(status: KbStatus): boolean {
  return status === "APPROVED";
}

/**
 * Returns the next required status after approval.
 * Approved articles must be published before being visible.
 */
export function nextStatusAfterApproval(): KbStatus {
  return "PUBLISHED";
}

/**
 * Derive a slug from a title (used client-side for preview).
 */
export function slugify(title: string): string {
  return title
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/**
 * Checks whether an article has a meaningful content change vs current.
 */
export function hasContentChanged(
  current: Pick<KbArticle, "title" | "content" | "summary">,
  update: UpdateKbArticleInput
): boolean {
  if (update.title !== undefined && update.title !== current.title) return true;
  if (update.content !== undefined && update.content !== current.content)
    return true;
  if (update.summary !== undefined && update.summary !== current.summary)
    return true;
  return false;
}
