/**
 * AC-025: KB Article Publish & Archive
 *
 * VER-002 · Tests APPROVED → PUBLISHED and PUBLISHED → ARCHIVED transitions.
 */
import {
  canTransition,
  isAwaitingPublish,
} from "@/lib/kb/validation";
import {
  publishArticle,
  archiveArticle,
} from "@/lib/kb/service";
import {
  draftArticle,
  pendingArticle,
  approvedArticle,
  publishedArticle,
  archivedArticle,
  rejectedArticle,
  makeArticle,
} from "./fixtures";
import { server, resetArticleStore } from "./msw-handlers";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => { server.resetHandlers(); resetArticleStore(); });
afterAll(() => server.close());

// ─── AC-025.1  Status-transition matrix ───────────────────────────────────────
describe("AC-025.1 canTransition — full matrix", () => {
  // Valid transitions
  const validTransitions: [string, string][] = [
    ["DRAFT", "PENDING_REVIEW"],
    ["PENDING_REVIEW", "APPROVED"],
    ["PENDING_REVIEW", "REJECTED"],
    ["APPROVED", "PUBLISHED"],
    ["APPROVED", "REJECTED"],
    ["PUBLISHED", "ARCHIVED"],
    ["REJECTED", "DRAFT"],
  ];

  for (const [from, to] of validTransitions) {
    it(`allows ${from} → ${to}`, () => {
      expect(canTransition(from as never, to as never)).toBe(true);
    });
  }

  // Invalid transitions
  const invalidTransitions: [string, string][] = [
    ["DRAFT", "APPROVED"],
    ["DRAFT", "PUBLISHED"],
    ["DRAFT", "ARCHIVED"],
    ["DRAFT", "REJECTED"],
    ["PENDING_REVIEW", "DRAFT"],
    ["PENDING_REVIEW", "PUBLISHED"],
    ["APPROVED", "DRAFT"],
    ["APPROVED", "PENDING_REVIEW"],
    ["PUBLISHED", "DRAFT"],
    ["PUBLISHED", "APPROVED"],
    ["ARCHIVED", "DRAFT"],
    ["ARCHIVED", "PUBLISHED"],
  ];

  for (const [from, to] of invalidTransitions) {
    it(`blocks ${from} → ${to}`, () => {
      expect(canTransition(from as never, to as never)).toBe(false);
    });
  }
});

// ─── AC-025.2  Publish — service ──────────────────────────────────────────────
describe("AC-025.2 publishArticle", () => {
  it("transitions APPROVED → PUBLISHED", async () => {
    const result = await publishArticle(approvedArticle.id, approvedArticle);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.status).toBe("PUBLISHED");
      expect(result.data.publishedAt).not.toBeNull();
    }
  });

  it("blocks publish of DRAFT article", async () => {
    const result = await publishArticle(draftArticle.id, draftArticle);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks publish of PENDING_REVIEW article", async () => {
    const result = await publishArticle(pendingArticle.id, pendingArticle);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks publish of already PUBLISHED article", async () => {
    const result = await publishArticle(publishedArticle.id, publishedArticle);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks publish of REJECTED article", async () => {
    const result = await publishArticle(rejectedArticle.id, rejectedArticle);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });
});

// ─── AC-025.3  isAwaitingPublish ──────────────────────────────────────────────
describe("AC-025.3 isAwaitingPublish helper", () => {
  it("returns true only for APPROVED status", () => {
    expect(isAwaitingPublish("APPROVED")).toBe(true);
  });

  it("returns false for all other statuses", () => {
    const others = ["DRAFT", "PENDING_REVIEW", "PUBLISHED", "ARCHIVED", "REJECTED"] as const;
    for (const s of others) {
      expect(isAwaitingPublish(s)).toBe(false);
    }
  });
});

// ─── AC-025.4  Archive — service ──────────────────────────────────────────────
describe("AC-025.4 archiveArticle", () => {
  it("transitions PUBLISHED → ARCHIVED", async () => {
    const result = await archiveArticle(publishedArticle.id, publishedArticle);
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.data.status).toBe("ARCHIVED");
  });

  it("blocks archiving a DRAFT article", async () => {
    const result = await archiveArticle(draftArticle.id, draftArticle);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks archiving a PENDING_REVIEW article", async () => {
    const result = await archiveArticle(pendingArticle.id, pendingArticle);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks archiving an APPROVED article", async () => {
    const result = await archiveArticle(approvedArticle.id, approvedArticle);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks archiving an already ARCHIVED article", async () => {
    const result = await archiveArticle(archivedArticle.id, archivedArticle);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });
});

// ─── AC-025.5  Full publish journey ───────────────────────────────────────────
describe("AC-025.5 APPROVED → PUBLISHED → ARCHIVED journey", () => {
  it("completes the full post-approval lifecycle", async () => {
    // Publish
    const pub = await publishArticle(approvedArticle.id, approvedArticle);
    expect(pub.ok).toBe(true);

    const afterPublish = pub.ok ? pub.data : makeArticle({ status: "PUBLISHED" });

    // Archive
    const arc = await archiveArticle(afterPublish.id, afterPublish);
    expect(arc.ok).toBe(true);
    if (arc.ok) expect(arc.data.status).toBe("ARCHIVED");
  });
});
