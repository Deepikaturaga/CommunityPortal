/**
 * MSW v2 request handlers for the KB API.
 * Import `server` in tests that exercise the API client or service layer.
 */
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import {
  draftArticle,
  pendingArticle,
  approvedArticle,
  publishedArticle,
  archivedArticle,
  rejectedArticle,
  makeListResponse,
  makeRevision,
} from "./fixtures";
import type { KbArticle } from "@/lib/kb/types";

const BASE = "http://localhost:4000";

// Mutable store so tests can mutate state across calls
export let articleStore: Record<string, KbArticle> = {};

export function resetArticleStore() {
  articleStore = {
    [draftArticle.id]: { ...draftArticle },
    [pendingArticle.id]: { ...pendingArticle },
    [approvedArticle.id]: { ...approvedArticle },
    [publishedArticle.id]: { ...publishedArticle },
    [archivedArticle.id]: { ...archivedArticle },
    [rejectedArticle.id]: { ...rejectedArticle },
  };
}

resetArticleStore();

export const handlers = [
  // LIST
  http.get(`${BASE}/api/kb`, () => {
    const items = Object.values(articleStore);
    return HttpResponse.json(makeListResponse(items));
  }),

  // GET
  http.get(`${BASE}/api/kb/:id`, ({ params }) => {
    const article = articleStore[params.id as string];
    if (!article) {
      return HttpResponse.json(
        { error: "NOT_FOUND", message: "Article not found", statusCode: 404 },
        { status: 404 }
      );
    }
    return HttpResponse.json(article);
  }),

  // CREATE
  http.post(`${BASE}/api/kb`, async ({ request }) => {
    const body = (await request.json()) as Partial<KbArticle>;
    const id = `article-new-${Date.now()}`;
    const now = new Date().toISOString();
    const created: KbArticle = {
      id,
      title: body.title ?? "Untitled",
      slug: (body.title ?? "untitled").toLowerCase().replace(/\s+/g, "-"),
      content: body.content ?? "",
      summary: body.summary,
      category: body.category ?? "GENERAL",
      tags: body.tags ?? [],
      status: "DRAFT",
      version: 1,
      authorId: "aaaaaaaa-0000-4000-8000-000000000001",
      reviewerId: null,
      approvedAt: null,
      publishedAt: null,
      createdAt: now,
      updatedAt: now,
    };
    articleStore[id] = created;
    return HttpResponse.json(created, { status: 201 });
  }),

  // UPDATE
  http.patch(`${BASE}/api/kb/:id`, async ({ params, request }) => {
    const article = articleStore[params.id as string];
    if (!article) {
      return HttpResponse.json(
        { error: "NOT_FOUND", message: "Article not found", statusCode: 404 },
        { status: 404 }
      );
    }
    const body = (await request.json()) as Partial<KbArticle>;
    const updated = {
      ...article,
      ...body,
      version: article.version + 1,
      updatedAt: new Date().toISOString(),
    };
    articleStore[params.id as string] = updated;
    return HttpResponse.json(updated);
  }),

  // DELETE
  http.delete(`${BASE}/api/kb/:id`, ({ params }) => {
    const article = articleStore[params.id as string];
    if (!article) {
      return HttpResponse.json(
        { error: "NOT_FOUND", message: "Article not found", statusCode: 404 },
        { status: 404 }
      );
    }
    delete articleStore[params.id as string];
    return new HttpResponse(null, { status: 204 });
  }),

  // SUBMIT FOR REVIEW
  http.post(`${BASE}/api/kb/:id/submit`, ({ params }) => {
    const article = articleStore[params.id as string];
    if (!article) {
      return HttpResponse.json(
        { error: "NOT_FOUND", message: "Article not found", statusCode: 404 },
        { status: 404 }
      );
    }
    const updated = { ...article, status: "PENDING_REVIEW" as const, updatedAt: new Date().toISOString() };
    articleStore[params.id as string] = updated;
    return HttpResponse.json(updated);
  }),

  // APPROVE
  http.post(`${BASE}/api/kb/:id/approve`, ({ params }) => {
    const article = articleStore[params.id as string];
    if (!article) {
      return HttpResponse.json(
        { error: "NOT_FOUND", message: "Article not found", statusCode: 404 },
        { status: 404 }
      );
    }
    const now = new Date().toISOString();
    const updated = {
      ...article,
      status: "APPROVED" as const,
      reviewerId: "bbbbbbbb-0000-4000-8000-000000000002",
      approvedAt: now,
      updatedAt: now,
    };
    articleStore[params.id as string] = updated;
    return HttpResponse.json(updated);
  }),

  // REJECT
  http.post(`${BASE}/api/kb/:id/reject`, ({ params }) => {
    const article = articleStore[params.id as string];
    if (!article) {
      return HttpResponse.json(
        { error: "NOT_FOUND", message: "Article not found", statusCode: 404 },
        { status: 404 }
      );
    }
    const updated = { ...article, status: "REJECTED" as const, updatedAt: new Date().toISOString() };
    articleStore[params.id as string] = updated;
    return HttpResponse.json(updated);
  }),

  // PUBLISH
  http.post(`${BASE}/api/kb/:id/publish`, ({ params }) => {
    const article = articleStore[params.id as string];
    if (!article) {
      return HttpResponse.json(
        { error: "NOT_FOUND", message: "Article not found", statusCode: 404 },
        { status: 404 }
      );
    }
    const now = new Date().toISOString();
    const updated = { ...article, status: "PUBLISHED" as const, publishedAt: now, updatedAt: now };
    articleStore[params.id as string] = updated;
    return HttpResponse.json(updated);
  }),

  // ARCHIVE
  http.post(`${BASE}/api/kb/:id/archive`, ({ params }) => {
    const article = articleStore[params.id as string];
    if (!article) {
      return HttpResponse.json(
        { error: "NOT_FOUND", message: "Article not found", statusCode: 404 },
        { status: 404 }
      );
    }
    const updated = { ...article, status: "ARCHIVED" as const, updatedAt: new Date().toISOString() };
    articleStore[params.id as string] = updated;
    return HttpResponse.json(updated);
  }),

  // REVISIONS
  http.get(`${BASE}/api/kb/:id/revisions`, ({ params }) => {
    const article = articleStore[params.id as string];
    if (!article) {
      return HttpResponse.json(
        { error: "NOT_FOUND", message: "Article not found", statusCode: 404 },
        { status: 404 }
      );
    }
    return HttpResponse.json([makeRevision({ articleId: params.id as string })]);
  }),
];

export const server = setupServer(...handlers);
