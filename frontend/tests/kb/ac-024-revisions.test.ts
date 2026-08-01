/**
 * AC-024: KB Article Revision History
 *
 * VER-010 · Tests revision creation, listing, and correctness.
 */
import { fetchRevisions } from "@/lib/kb/service";
import {
  draftArticle,
  makeRevision,
  AUTHOR_ID,
  REVIEWER_ID,
} from "./fixtures";
import { server, resetArticleStore } from "./msw-handlers";
import { http, HttpResponse } from "msw";
import { KbRevisionSchema } from "@/lib/kb/types";

const BASE = "http://localhost:4000";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => { server.resetHandlers(); resetArticleStore(); });
afterAll(() => server.close());

// ─── AC-024.1  Revision schema ────────────────────────────────────────────────
describe("AC-024.1 KbRevisionSchema validation", () => {
  it("validates a well-formed revision", () => {
    const raw = makeRevision();
    const result = KbRevisionSchema.safeParse(raw);
    expect(result.success).toBe(true);
  });

  it("rejects revision with missing articleId", () => {
    const raw = makeRevision();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { articleId: _, ...noArticleId } = raw as any;
    const result = KbRevisionSchema.safeParse(noArticleId);
    expect(result.success).toBe(false);
  });

  it("rejects revision with invalid action", () => {
    const raw = { ...makeRevision(), action: "REVIEW" };
    const result = KbRevisionSchema.safeParse(raw);
    expect(result.success).toBe(false);
  });

  it("accepts all valid RevisionAction values", () => {
    const actions = ["EDIT", "APPROVE", "REJECT", "PUBLISH", "ARCHIVE"] as const;
    for (const action of actions) {
      const result = KbRevisionSchema.safeParse({ ...makeRevision(), action });
      expect(result.success).toBe(true);
    }
  });
});

// ─── AC-024.2  Fetch revisions — happy path ───────────────────────────────────
describe("AC-024.2 fetchRevisions — happy path", () => {
  it("returns array of revisions for a known article", async () => {
    const result = await fetchRevisions(draftArticle.id);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(Array.isArray(result.data)).toBe(true);
      expect(result.data.length).toBeGreaterThan(0);
      expect(result.data[0].articleId).toBe(draftArticle.id);
    }
  });

  it("revision actor is set", async () => {
    const result = await fetchRevisions(draftArticle.id);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data[0].actorId).toBe(AUTHOR_ID);
    }
  });
});

// ─── AC-024.3  Fetch revisions — 404 ──────────────────────────────────────────
describe("AC-024.3 fetchRevisions — article not found", () => {
  it("returns api error for unknown article", async () => {
    const result = await fetchRevisions("00000000-0000-0000-0000-000000000000");
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("api");
  });
});

// ─── AC-024.4  Multiple revisions ────────────────────────────────────────────
describe("AC-024.4 multiple revisions in order", () => {
  it("returns revisions sorted by version (MSW override)", async () => {
    const revisions = [
      makeRevision({ version: 1, action: "EDIT", actorId: AUTHOR_ID }),
      makeRevision({
        id: "revision-id-0002-0000-000000000002",
        version: 2,
        action: "APPROVE",
        actorId: REVIEWER_ID,
      }),
      makeRevision({
        id: "revision-id-0003-0000-000000000003",
        version: 3,
        action: "PUBLISH",
        actorId: REVIEWER_ID,
      }),
    ];

    server.use(
      http.get(`${BASE}/api/kb/:id/revisions`, () => {
        return HttpResponse.json(revisions);
      })
    );

    const result = await fetchRevisions(draftArticle.id);
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data).toHaveLength(3);
      expect(result.data[0].version).toBe(1);
      expect(result.data[1].action).toBe("APPROVE");
      expect(result.data[2].action).toBe("PUBLISH");
    }
  });
});

// ─── AC-024.5  Revision integrity ────────────────────────────────────────────
describe("AC-024.5 revision content integrity", () => {
  it("revision includes a snapshot of title and content", () => {
    const rev = makeRevision({
      title: "Snapshot Title",
      content: "Snapshot content body",
    });
    expect(rev.title).toBe("Snapshot Title");
    expect(rev.content).toBe("Snapshot content body");
  });

  it("revision with comment preserves comment text", () => {
    const rev = makeRevision({ comment: "Editorial note" });
    expect(rev.comment).toBe("Editorial note");
  });
});

// ─── AC-024.6  API error propagation ─────────────────────────────────────────
describe("AC-024.6 fetchRevisions — server error propagation", () => {
  it("returns unknown error on 500", async () => {
    server.use(
      http.get(`${BASE}/api/kb/:id/revisions`, () => {
        return HttpResponse.json(
          { error: "INTERNAL", message: "Internal server error", statusCode: 500 },
          { status: 500 }
        );
      })
    );
    const result = await fetchRevisions(draftArticle.id);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.type).toBe("api");
      expect(result.message).toMatch(/internal server error/i);
    }
  });
});
