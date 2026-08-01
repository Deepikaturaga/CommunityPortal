/**
 * AC-026: KB Article Listing & Filtering
 *
 * VER-010 · Tests pagination, filter parameters, search, and list response shape.
 */
import { fetchArticles, fetchArticle } from "@/lib/kb/service";
import {
  draftArticle,
  pendingArticle,
  approvedArticle,
  publishedArticle,
  makeListResponse,
  makeArticle,
} from "./fixtures";
import { server, resetArticleStore, articleStore } from "./msw-handlers";
import { http, HttpResponse } from "msw";
import { KbListResponseSchema, KbArticleSchema } from "@/lib/kb/types";

const BASE = "http://localhost:4000";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => { server.resetHandlers(); resetArticleStore(); });
afterAll(() => server.close());

// ─── AC-026.1  List response schema ───────────────────────────────────────────
describe("AC-026.1 KbListResponseSchema validation", () => {
  it("validates a well-formed list response", () => {
    const raw = makeListResponse([draftArticle]);
    const result = KbListResponseSchema.safeParse(raw);
    expect(result.success).toBe(true);
  });

  it("validates a response with multiple items", () => {
    const raw = makeListResponse([draftArticle, pendingArticle, approvedArticle]);
    const result = KbListResponseSchema.safeParse(raw);
    expect(result.success).toBe(true);
    if (result.success) expect(result.data.items).toHaveLength(3);
  });

  it("validates an empty list response", () => {
    const raw = makeListResponse([]);
    const result = KbListResponseSchema.safeParse(raw);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.items).toHaveLength(0);
      expect(result.data.total).toBe(0);
    }
  });

  it("rejects response with missing total field", () => {
    const { total: _, ...noTotal } = makeListResponse([draftArticle]) as Record<string, unknown>;
    expect(KbListResponseSchema.safeParse(noTotal).success).toBe(false);
  });

  it("computes totalPages correctly", () => {
    const raw = makeListResponse(
      Array.from({ length: 5 }, (_, i) =>
        makeArticle({ id: `id-${i}`, slug: `slug-${i}` })
      ),
      { total: 50, pageSize: 10 }
    );
    const result = KbListResponseSchema.safeParse(raw);
    expect(result.success).toBe(true);
    if (result.success) expect(result.data.totalPages).toBe(5);
  });
});

// ─── AC-026.2  fetchArticles — default (no filters) ──────────────────────────
describe("AC-026.2 fetchArticles — default", () => {
  it("returns all articles", async () => {
    const result = await fetchArticles();
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.items.length).toBeGreaterThan(0);
      expect(typeof result.data.total).toBe("number");
      expect(typeof result.data.page).toBe("number");
      expect(typeof result.data.pageSize).toBe("number");
    }
  });
});

// ─── AC-026.3  fetchArticles — status filter ──────────────────────────────────
describe("AC-026.3 fetchArticles — status filter", () => {
  it("returns only PUBLISHED articles when filtered", async () => {
    server.use(
      http.get(`${BASE}/api/kb`, ({ request }) => {
        const url = new URL(request.url);
        const status = url.searchParams.get("status");
        const items = Object.values(articleStore).filter(
          (a) => !status || a.status === status
        );
        return HttpResponse.json(makeListResponse(items));
      })
    );
    const result = await fetchArticles({ status: "PUBLISHED" });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.items.every((a) => a.status === "PUBLISHED")).toBe(true);
    }
  });

  it("returns only DRAFT articles when filtered", async () => {
    server.use(
      http.get(`${BASE}/api/kb`, ({ request }) => {
        const url = new URL(request.url);
        const status = url.searchParams.get("status");
        const items = Object.values(articleStore).filter(
          (a) => !status || a.status === status
        );
        return HttpResponse.json(makeListResponse(items));
      })
    );
    const result = await fetchArticles({ status: "DRAFT" });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.items.every((a) => a.status === "DRAFT")).toBe(true);
    }
  });
});

// ─── AC-026.4  fetchArticles — category filter ────────────────────────────────
describe("AC-026.4 fetchArticles — category filter", () => {
  it("returns only FAQ articles", async () => {
    server.use(
      http.get(`${BASE}/api/kb`, ({ request }) => {
        const url = new URL(request.url);
        const category = url.searchParams.get("category");
        const items = Object.values(articleStore).filter(
          (a) => !category || a.category === category
        );
        return HttpResponse.json(makeListResponse(items));
      })
    );
    const result = await fetchArticles({ category: "FAQ" });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.items.every((a) => a.category === "FAQ")).toBe(true);
    }
  });
});

// ─── AC-026.5  fetchArticles — search ────────────────────────────────────────
describe("AC-026.5 fetchArticles — search parameter", () => {
  it("passes search param to the API and returns filtered results", async () => {
    const matchingArticle = makeArticle({
      id: "search-match-id",
      slug: "search-match",
      title: "SAML Single Sign-On Setup",
    });

    server.use(
      http.get(`${BASE}/api/kb`, ({ request }) => {
        const url = new URL(request.url);
        const search = url.searchParams.get("search")?.toLowerCase();
        const items = search
          ? Object.values({ ...articleStore, [matchingArticle.id]: matchingArticle }).filter(
              (a) => a.title.toLowerCase().includes(search)
            )
          : Object.values(articleStore);
        return HttpResponse.json(makeListResponse(items));
      })
    );

    const result = await fetchArticles({ search: "SAML" });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.items.some((a) => a.title.includes("SAML"))).toBe(true);
    }
  });
});

// ─── AC-026.6  fetchArticles — pagination ────────────────────────────────────
describe("AC-026.6 fetchArticles — pagination", () => {
  it("passes page and pageSize to the API", async () => {
    let capturedPage: string | null = null;
    let capturedPageSize: string | null = null;

    server.use(
      http.get(`${BASE}/api/kb`, ({ request }) => {
        const url = new URL(request.url);
        capturedPage = url.searchParams.get("page");
        capturedPageSize = url.searchParams.get("pageSize");
        return HttpResponse.json(makeListResponse([]));
      })
    );

    await fetchArticles({ page: 3, pageSize: 10 });
    expect(capturedPage).toBe("3");
    expect(capturedPageSize).toBe("10");
  });
});

// ─── AC-026.7  fetchArticle — single ─────────────────────────────────────────
describe("AC-026.7 fetchArticle by ID", () => {
  it("returns the article for a known ID", async () => {
    const result = await fetchArticle(draftArticle.id);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.id).toBe(draftArticle.id);
      expect(result.data.title).toBe(draftArticle.title);
    }
  });

  it("returns api error for unknown ID", async () => {
    const result = await fetchArticle("00000000-dead-beef-0000-000000000000");
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("api");
  });
});

// ─── AC-026.8  KbArticleSchema ────────────────────────────────────────────────
describe("AC-026.8 KbArticleSchema validation", () => {
  it("validates publishedArticle fixture", () => {
    const result = KbArticleSchema.safeParse(publishedArticle);
    expect(result.success).toBe(true);
  });

  it("rejects article with invalid status", () => {
    const raw = { ...draftArticle, status: "CANCELLED" };
    expect(KbArticleSchema.safeParse(raw).success).toBe(false);
  });

  it("rejects article with non-UUID authorId", () => {
    const raw = { ...draftArticle, authorId: "not-a-uuid" };
    expect(KbArticleSchema.safeParse(raw).success).toBe(false);
  });

  it("rejects article with negative version", () => {
    const raw = { ...draftArticle, version: -1 };
    expect(KbArticleSchema.safeParse(raw).success).toBe(false);
  });
});

// ─── AC-026.9  authorId filter ────────────────────────────────────────────────
describe("AC-026.9 fetchArticles — authorId filter", () => {
  it("passes authorId to the API", async () => {
    let capturedAuthorId: string | null = null;
    server.use(
      http.get(`${BASE}/api/kb`, ({ request }) => {
        const url = new URL(request.url);
        capturedAuthorId = url.searchParams.get("authorId");
        return HttpResponse.json(makeListResponse([]));
      })
    );
    await fetchArticles({ authorId: "aaaaaaaa-0000-4000-8000-000000000001" });
    expect(capturedAuthorId).toBe("aaaaaaaa-0000-4000-8000-000000000001");
  });
});
