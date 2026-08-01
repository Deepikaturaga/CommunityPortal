/**
 * KB service layer — orchestrates API calls + local validation before dispatch.
 * This layer is imported by server actions and client hooks alike.
 */
import {
  listKbArticles,
  getKbArticle,
  createKbArticle,
  updateKbArticle,
  deleteKbArticle,
  submitKbArticleForReview,
  approveKbArticle,
  rejectKbArticle,
  publishKbArticle,
  archiveKbArticle,
  listKbRevisions,
  KbApiError,
} from "./api";
import {
  validateCreateArticle,
  validateUpdateArticle,
  validateApproveArticle,
  validateRejectArticle,
  validateSubmitForReview,
  isEditable,
  isAwaitingReview,
  isAwaitingPublish,
  canTransition,
} from "./validation";
import type {
  KbArticle,
  KbListParams,
  KbListResponse,
  CreateKbArticleInput,
  UpdateKbArticleInput,
  ApproveKbArticleInput,
  RejectKbArticleInput,
  SubmitForReviewInput,
  KbRevision,
} from "./types";

// ─── Service result type ──────────────────────────────────────────────────────

export type ServiceResult<T> =
  | { ok: true; data: T }
  | { ok: false; type: "validation" | "api" | "forbidden" | "unknown"; message: string; details?: Record<string, string[]> };

// ─── Article CRUD ─────────────────────────────────────────────────────────────

export async function fetchArticles(
  params: Partial<KbListParams> = {}
): Promise<ServiceResult<KbListResponse>> {
  try {
    const data = await listKbArticles(params);
    return { ok: true, data };
  } catch (err) {
    return toServiceError(err);
  }
}

export async function fetchArticle(
  id: string
): Promise<ServiceResult<KbArticle>> {
  try {
    const data = await getKbArticle(id);
    return { ok: true, data };
  } catch (err) {
    return toServiceError(err);
  }
}

export async function createArticle(
  input: unknown
): Promise<ServiceResult<KbArticle>> {
  const validation = validateCreateArticle(input);
  if (!validation.success) {
    return {
      ok: false,
      type: "validation",
      message: "Invalid article input",
      details: validation.errors,
    };
  }
  try {
    const data = await createKbArticle(validation.data);
    return { ok: true, data };
  } catch (err) {
    return toServiceError(err);
  }
}

export async function updateArticle(
  id: string,
  article: KbArticle,
  input: unknown
): Promise<ServiceResult<KbArticle>> {
  if (!isEditable(article.status)) {
    return {
      ok: false,
      type: "forbidden",
      message: `Article in status "${article.status}" cannot be edited`,
    };
  }
  const validation = validateUpdateArticle(input);
  if (!validation.success) {
    return {
      ok: false,
      type: "validation",
      message: "Invalid update input",
      details: validation.errors,
    };
  }
  try {
    const data = await updateKbArticle(id, validation.data as UpdateKbArticleInput);
    return { ok: true, data };
  } catch (err) {
    return toServiceError(err);
  }
}

export async function removeArticle(
  id: string,
  article: KbArticle
): Promise<ServiceResult<void>> {
  if (!isEditable(article.status)) {
    return {
      ok: false,
      type: "forbidden",
      message: `Article in status "${article.status}" cannot be deleted`,
    };
  }
  try {
    await deleteKbArticle(id);
    return { ok: true, data: undefined };
  } catch (err) {
    return toServiceError(err);
  }
}

// ─── Workflow ─────────────────────────────────────────────────────────────────

export async function submitArticleForReview(
  id: string,
  article: KbArticle,
  input: unknown = {}
): Promise<ServiceResult<KbArticle>> {
  if (!canTransition(article.status, "PENDING_REVIEW")) {
    return {
      ok: false,
      type: "forbidden",
      message: `Cannot submit article with status "${article.status}" for review`,
    };
  }
  const validation = validateSubmitForReview(input);
  if (!validation.success) {
    return {
      ok: false,
      type: "validation",
      message: "Invalid submit input",
      details: validation.errors,
    };
  }
  try {
    const data = await submitKbArticleForReview(id, validation.data as SubmitForReviewInput);
    return { ok: true, data };
  } catch (err) {
    return toServiceError(err);
  }
}

export async function approveArticle(
  id: string,
  article: KbArticle,
  input: unknown = {}
): Promise<ServiceResult<KbArticle>> {
  if (!isAwaitingReview(article.status)) {
    return {
      ok: false,
      type: "forbidden",
      message: `Article must be in PENDING_REVIEW to approve (current: "${article.status}")`,
    };
  }
  const validation = validateApproveArticle(input);
  if (!validation.success) {
    return {
      ok: false,
      type: "validation",
      message: "Invalid approve input",
      details: validation.errors,
    };
  }
  try {
    const data = await approveKbArticle(id, validation.data as ApproveKbArticleInput);
    return { ok: true, data };
  } catch (err) {
    return toServiceError(err);
  }
}

export async function rejectArticle(
  id: string,
  article: KbArticle,
  input: unknown
): Promise<ServiceResult<KbArticle>> {
  const isEligible =
    article.status === "PENDING_REVIEW" || article.status === "APPROVED";
  if (!isEligible) {
    return {
      ok: false,
      type: "forbidden",
      message: `Article in status "${article.status}" cannot be rejected`,
    };
  }
  const validation = validateRejectArticle(input);
  if (!validation.success) {
    return {
      ok: false,
      type: "validation",
      message: "Rejection comment is required",
      details: validation.errors,
    };
  }
  try {
    const data = await rejectKbArticle(id, validation.data as RejectKbArticleInput);
    return { ok: true, data };
  } catch (err) {
    return toServiceError(err);
  }
}

export async function publishArticle(
  id: string,
  article: KbArticle
): Promise<ServiceResult<KbArticle>> {
  if (!isAwaitingPublish(article.status)) {
    return {
      ok: false,
      type: "forbidden",
      message: `Article must be APPROVED to publish (current: "${article.status}")`,
    };
  }
  try {
    const data = await publishKbArticle(id);
    return { ok: true, data };
  } catch (err) {
    return toServiceError(err);
  }
}

export async function archiveArticle(
  id: string,
  article: KbArticle
): Promise<ServiceResult<KbArticle>> {
  if (!canTransition(article.status, "ARCHIVED")) {
    return {
      ok: false,
      type: "forbidden",
      message: `Article in status "${article.status}" cannot be archived`,
    };
  }
  try {
    const data = await archiveKbArticle(id);
    return { ok: true, data };
  } catch (err) {
    return toServiceError(err);
  }
}

// ─── Revisions ────────────────────────────────────────────────────────────────

export async function fetchRevisions(
  articleId: string
): Promise<ServiceResult<KbRevision[]>> {
  try {
    const data = await listKbRevisions(articleId);
    return { ok: true, data };
  } catch (err) {
    return toServiceError(err);
  }
}

// ─── Error normalizer ─────────────────────────────────────────────────────────

function toServiceError(err: unknown): ServiceResult<never> {
  if (err instanceof KbApiError) {
    return {
      ok: false,
      type: "api",
      message: err.apiError.message,
    };
  }
  return {
    ok: false,
    type: "unknown",
    message: err instanceof Error ? err.message : "An unexpected error occurred",
  };
}
