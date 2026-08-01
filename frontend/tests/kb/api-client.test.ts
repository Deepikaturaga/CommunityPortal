/**
 * KB API client — integration tests (VER-002, VER-004, VER-010)
 *
 * Tests the raw API client layer in isolation to verify HTTP transport,
 * credential forwarding, error handling, and Zod response parsing.
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
} from "@/lib/kb/api";
import { draftArticle, pendingArticle, approvedArticle, publishedArticle } from "./fixtures";
import { server, resetArticleStore } from "./msw-handlers";
import { http, HttpResponse } from "msw";

const BASE = "http://localhost:4000";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => { server.resetHandlers(); resetArticleStore(); });
afterAll(() => server.close());

// ─── List ─────────────────────────────────────────────────────────────────────
describe("KB API client — listKbArticles", () => {
  it("returns a parsed KbListResponse", async () => {
    const res = await listKbArticles();
    expect(Array.isArray(res.items)).toBe(true);
    expect(typeof res.total).toBe("number");
  });

  it("passes query params correctly", async () => {
    let captured = "";
    server.use(
      http.get(`${BASE}/api/kb`, ({ request }) => {
        captured = new URL(request.url).search;
        return HttpResponse.json({ items: [], total: 0, page: 1, pageSize: 20, totalPages: 0 });
      })
    );
    await listKbArticles({ status: "PUBLISHED", page: 2, pageSize: 5 });
    expect(captured).toContain("status=PUBLISHED");
    expect(captured).toContain("page=2");
    expect(captured).toContain("pageSize=5");
  });
});

// ─── Get ──────────────────────────────────────────────────────────────────────
describe("KB API client — getKbArticle", () => {
  it("returns the requested article", async () => {
    const article = await getKbArticle(draftArticle.id);
    expect(article.id).toBe(draftArticle.id);
  });

  it("throws KbApiError on 404", async () => {
    await expect(getKbArticle("00000000-0000-0000-0000-000000000000")).rejects.toBeInstanceOf(KbApiError);
  });
});

// ─── Create ───────────────────────────────────────────────────────────────────
describe("KB API client — createKbArticle", () => {
  it("creates and returns a new article", async () => {
    const article = await createKbArticle({
      title: "API Test Article",
      content: "Content",
      category: "TECHNICAL",
    });
    expect(article.title).toBe("API Test Article");
    expect(article.status).toBe("DRAFT");
  });
});

// ─── Update ───────────────────────────────────────────────────────────────────
describe("KB API client — updateKbArticle", () => {
  it("patches and returns the updated article", async () => {
    const updated = await updateKbArticle(draftArticle.id, { title: "Patched" });
    expect(updated.title).toBe("Patched");
    expect(updated.version).toBe(draftArticle.version + 1);
  });

  it("throws KbApiError on 404", async () => {
    await expect(updateKbArticle("00000000-0000-0000-0000-000000000000", { title: "X" })).rejects.toBeInstanceOf(KbApiError);
  });
});

// ─── Delete ───────────────────────────────────────────────────────────────────
describe("KB API client — deleteKbArticle", () => {
  it("resolves without error on successful delete", async () => {
    await expect(deleteKbArticle(draftArticle.id)).resolves.toBeUndefined();
  });

  it("throws KbApiError on 404", async () => {
    await expect(deleteKbArticle("00000000-0000-0000-0000-000000000000")).rejects.toBeInstanceOf(KbApiError);
  });
});

// ─── Workflow transitions ─────────────────────────────────────────────────────
describe("KB API client — workflow endpoints", () => {
  it("submitKbArticleForReview transitions to PENDING_REVIEW", async () => {
    const article = await submitKbArticleForReview(draftArticle.id);
    expect(article.status).toBe("PENDING_REVIEW");
  });

  it("approveKbArticle transitions to APPROVED", async () => {
    const article = await approveKbArticle(pendingArticle.id);
    expect(article.status).toBe("APPROVED");
  });

  it("rejectKbArticle transitions to REJECTED", async () => {
    const article = await rejectKbArticle(pendingArticle.id, { comment: "Needs work" });
    expect(article.status).toBe("REJECTED");
  });

  it("publishKbArticle transitions to PUBLISHED", async () => {
    const article = await publishKbArticle(approvedArticle.id);
    expect(article.status).toBe("PUBLISHED");
  });

  it("archiveKbArticle transitions to ARCHIVED", async () => {
    const article = await archiveKbArticle(publishedArticle.id);
    expect(article.status).toBe("ARCHIVED");
  });
});

// ─── Error handling ───────────────────────────────────────────────────────────
describe("KB API client — error handling", () => {
  it("throws KbApiError with correct statusCode and message", async () => {
    server.use(
      http.get(`${BASE}/api/kb/:id`, () => {
        return HttpResponse.json(
          { error: "FORBIDDEN", message: "Access denied", statusCode: 403 },
          { status: 403 }
        );
      })
    );
    let err: KbApiError | null = null;
    try {
      await getKbArticle(draftArticle.id);
    } catch (e) {
      err = e as KbApiError;
    }
    expect(err).toBeInstanceOf(KbApiError);
    expect(err?.statusCode).toBe(403);
    expect(err?.message).toBe("Access denied");
  });

  it("KbApiError carries the full ApiError envelope", async () => {
    server.use(
      http.post(`${BASE}/api/kb`, () => {
        return HttpResponse.json(
          { error: "CONFLICT", message: "Slug already exists", statusCode: 409 },
          { status: 409 }
        );
      })
    );
    let err: KbApiError | null = null;
    try {
      await createKbArticle({ title: "Dup", content: "C", category: "FAQ" });
    } catch (e) {
      err = e as KbApiError;
    }
    expect(err?.apiError.error).toBe("CONFLICT");
  });
});

// ─── Revisions ────────────────────────────────────────────────────────────────
describe("KB API client — listKbRevisions", () => {
  it("returns a revision array for a known article", async () => {
    const revisions = await listKbRevisions(draftArticle.id);
    expect(Array.isArray(revisions)).toBe(true);
    expect(revisions.length).toBeGreaterThan(0);
  });
});
