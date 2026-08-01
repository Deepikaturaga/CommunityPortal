/**
 * KB API client — thin fetch wrapper that consumes the generated OpenAPI contract.
 * All requests are credentialed (HTTP-only cookies; no localStorage tokens).
 */
import {
  KbArticle,
  KbArticleSchema,
  KbListResponse,
  KbListResponseSchema,
  KbListParams,
  CreateKbArticleInput,
  UpdateKbArticleInput,
  ApproveKbArticleInput,
  RejectKbArticleInput,
  SubmitForReviewInput,
  KbRevision,
  KbRevisionSchema,
  ApiError,
} from "./types";
import { z } from "zod";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:4000";

// ─── Transport ────────────────────────────────────────────────────────────────

class KbApiError extends Error {
  constructor(
    public readonly statusCode: number,
    public readonly apiError: ApiError
  ) {
    super(apiError.message);
    this.name = "KbApiError";
  }
}

async function apiFetch<T>(
  schema: z.ZodSchema<T>,
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(init.headers ?? {}),
    },
  });

  const body: unknown = await res.json();

  if (!res.ok) {
    const error = body as ApiError;
    throw new KbApiError(res.status, error);
  }

  return schema.parse(body);
}

// ─── CRUD ─────────────────────────────────────────────────────────────────────

export async function listKbArticles(
  params: Partial<KbListParams> = {}
): Promise<KbListResponse> {
  const qs = new URLSearchParams();
  if (params.page) qs.set("page", String(params.page));
  if (params.pageSize) qs.set("pageSize", String(params.pageSize));
  if (params.status) qs.set("status", params.status);
  if (params.category) qs.set("category", params.category);
  if (params.search) qs.set("search", params.search);
  if (params.authorId) qs.set("authorId", params.authorId);
  return apiFetch(KbListResponseSchema, `/api/kb?${qs.toString()}`);
}

export async function getKbArticle(id: string): Promise<KbArticle> {
  return apiFetch(KbArticleSchema, `/api/kb/${id}`);
}

export async function createKbArticle(
  input: CreateKbArticleInput
): Promise<KbArticle> {
  return apiFetch(KbArticleSchema, "/api/kb", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function updateKbArticle(
  id: string,
  input: UpdateKbArticleInput
): Promise<KbArticle> {
  return apiFetch(KbArticleSchema, `/api/kb/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export async function deleteKbArticle(id: string): Promise<void> {
  const url = `${BASE_URL}/api/kb/${id}`;
  const res = await fetch(url, { method: "DELETE", credentials: "include" });
  if (!res.ok) {
    const body = (await res.json()) as ApiError;
    throw new KbApiError(res.status, body);
  }
}

// ─── Workflow transitions ─────────────────────────────────────────────────────

export async function submitKbArticleForReview(
  id: string,
  input: SubmitForReviewInput = {}
): Promise<KbArticle> {
  return apiFetch(KbArticleSchema, `/api/kb/${id}/submit`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function approveKbArticle(
  id: string,
  input: ApproveKbArticleInput = {}
): Promise<KbArticle> {
  return apiFetch(KbArticleSchema, `/api/kb/${id}/approve`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function rejectKbArticle(
  id: string,
  input: RejectKbArticleInput
): Promise<KbArticle> {
  return apiFetch(KbArticleSchema, `/api/kb/${id}/reject`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function publishKbArticle(id: string): Promise<KbArticle> {
  return apiFetch(KbArticleSchema, `/api/kb/${id}/publish`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function archiveKbArticle(id: string): Promise<KbArticle> {
  return apiFetch(KbArticleSchema, `/api/kb/${id}/archive`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

// ─── Revisions ────────────────────────────────────────────────────────────────

export async function listKbRevisions(articleId: string): Promise<KbRevision[]> {
  return apiFetch(z.array(KbRevisionSchema), `/api/kb/${articleId}/revisions`);
}

export { KbApiError };
