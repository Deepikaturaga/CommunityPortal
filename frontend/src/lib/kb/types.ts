/**
 * KB domain types — single source of truth for the frontend.
 * These mirror the backend OpenAPI contract; no hand-duplicated server DTOs beyond this file.
 */
import { z } from "zod";

// ─── Enums ────────────────────────────────────────────────────────────────────

export const KbStatusSchema = z.enum([
  "DRAFT",
  "PENDING_REVIEW",
  "APPROVED",
  "PUBLISHED",
  "ARCHIVED",
  "REJECTED",
]);
export type KbStatus = z.infer<typeof KbStatusSchema>;

export const KbCategorySchema = z.enum([
  "FAQ",
  "POLICY",
  "PROCEDURE",
  "TECHNICAL",
  "GENERAL",
]);
export type KbCategory = z.infer<typeof KbCategorySchema>;

export const RevisionActionSchema = z.enum(["EDIT", "APPROVE", "REJECT", "PUBLISH", "ARCHIVE"]);
export type RevisionAction = z.infer<typeof RevisionActionSchema>;

// ─── Core Article ─────────────────────────────────────────────────────────────

export const KbArticleSchema = z.object({
  id: z.string().uuid(),
  title: z.string().min(1).max(255),
  slug: z.string().min(1).max(255),
  content: z.string().min(1),
  summary: z.string().max(500).optional(),
  category: KbCategorySchema,
  tags: z.array(z.string()).default([]),
  status: KbStatusSchema,
  version: z.number().int().positive(),
  authorId: z.string().uuid(),
  reviewerId: z.string().uuid().nullable(),
  approvedAt: z.string().datetime().nullable(),
  publishedAt: z.string().datetime().nullable(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});
export type KbArticle = z.infer<typeof KbArticleSchema>;

// ─── Revision ─────────────────────────────────────────────────────────────────

export const KbRevisionSchema = z.object({
  id: z.string().uuid(),
  articleId: z.string().uuid(),
  version: z.number().int().positive(),
  title: z.string().min(1).max(255),
  content: z.string().min(1),
  summary: z.string().max(500).optional(),
  action: RevisionActionSchema,
  actorId: z.string().uuid(),
  comment: z.string().max(1000).optional(),
  createdAt: z.string().datetime(),
});
export type KbRevision = z.infer<typeof KbRevisionSchema>;

// ─── Request / Response DTOs ──────────────────────────────────────────────────

export const CreateKbArticleInputSchema = z.object({
  title: z.string().min(1, "Title is required").max(255),
  content: z.string().min(1, "Content is required"),
  summary: z.string().max(500).optional(),
  category: KbCategorySchema,
  tags: z.array(z.string()).optional(),
});
export type CreateKbArticleInput = z.infer<typeof CreateKbArticleInputSchema>;

export const UpdateKbArticleInputSchema = z.object({
  title: z.string().min(1).max(255).optional(),
  content: z.string().min(1).optional(),
  summary: z.string().max(500).optional(),
  category: KbCategorySchema.optional(),
  tags: z.array(z.string()).optional(),
  comment: z.string().max(1000).optional(),
});
export type UpdateKbArticleInput = z.infer<typeof UpdateKbArticleInputSchema>;

export const ApproveKbArticleInputSchema = z.object({
  comment: z.string().max(1000).optional(),
});
export type ApproveKbArticleInput = z.infer<typeof ApproveKbArticleInputSchema>;

export const RejectKbArticleInputSchema = z.object({
  comment: z.string().min(1, "Rejection reason is required").max(1000),
});
export type RejectKbArticleInput = z.infer<typeof RejectKbArticleInputSchema>;

export const SubmitForReviewInputSchema = z.object({
  comment: z.string().max(1000).optional(),
});
export type SubmitForReviewInput = z.infer<typeof SubmitForReviewInputSchema>;

// ─── List / Pagination ────────────────────────────────────────────────────────

export const KbListParamsSchema = z.object({
  page: z.number().int().positive().optional().default(1),
  pageSize: z.number().int().positive().max(100).optional().default(20),
  status: KbStatusSchema.optional(),
  category: KbCategorySchema.optional(),
  search: z.string().optional(),
  authorId: z.string().uuid().optional(),
});
export type KbListParams = z.infer<typeof KbListParamsSchema>;

export const KbListResponseSchema = z.object({
  items: z.array(KbArticleSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  pageSize: z.number().int().positive(),
  totalPages: z.number().int().nonnegative(),
});
export type KbListResponse = z.infer<typeof KbListResponseSchema>;

// ─── API Error envelope ───────────────────────────────────────────────────────

export const ApiErrorSchema = z.object({
  error: z.string(),
  message: z.string(),
  statusCode: z.number().int(),
  details: z.record(z.unknown()).optional(),
});
export type ApiError = z.infer<typeof ApiErrorSchema>;
