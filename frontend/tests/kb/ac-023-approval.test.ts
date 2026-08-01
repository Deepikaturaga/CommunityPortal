/**
 * AC-023: KB Article Approval Flow
 *
 * VER-004 · Tests submit-for-review, approve, and reject transitions.
 */
import {
  validateApproveArticle,
  validateRejectArticle,
  validateSubmitForReview,
  canTransition,
  isAwaitingReview,
} from "@/lib/kb/validation";
import {
  submitArticleForReview,
  approveArticle,
  rejectArticle,
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

// ─── AC-023.1  Submit for review — validation ─────────────────────────────────
describe("AC-023.1 validateSubmitForReview", () => {
  it("accepts empty object (comment is optional)", () => {
    expect(validateSubmitForReview({}).success).toBe(true);
  });

  it("accepts optional comment", () => {
    expect(validateSubmitForReview({ comment: "Ready for review" }).success).toBe(true);
  });

  it("rejects comment exceeding 1000 chars", () => {
    const result = validateSubmitForReview({ comment: "x".repeat(1001) });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("comment");
  });
});

// ─── AC-023.2  Submit for review — transitions ────────────────────────────────
describe("AC-023.2 submitArticleForReview transitions", () => {
  it("transitions DRAFT → PENDING_REVIEW", async () => {
    const result = await submitArticleForReview(
      draftArticle.id, draftArticle, {}
    );
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.data.status).toBe("PENDING_REVIEW");
  });

  it("blocks submit for PENDING_REVIEW article", async () => {
    const result = await submitArticleForReview(
      pendingArticle.id, pendingArticle, {}
    );
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks submit for APPROVED article", async () => {
    const result = await submitArticleForReview(
      approvedArticle.id, approvedArticle, {}
    );
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks submit for PUBLISHED article", async () => {
    const result = await submitArticleForReview(
      publishedArticle.id, publishedArticle, {}
    );
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks submit for ARCHIVED article", async () => {
    const result = await submitArticleForReview(
      archivedArticle.id, archivedArticle, {}
    );
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("REJECTED article can be re-submitted after going back to DRAFT", () => {
    // REJECTED → DRAFT is a valid transition
    expect(canTransition("REJECTED", "DRAFT")).toBe(true);
    // Then DRAFT → PENDING_REVIEW
    expect(canTransition("DRAFT", "PENDING_REVIEW")).toBe(true);
  });
});

// ─── AC-023.3  Approve — validation ──────────────────────────────────────────
describe("AC-023.3 validateApproveArticle", () => {
  it("accepts empty object", () => {
    expect(validateApproveArticle({}).success).toBe(true);
  });

  it("accepts optional comment", () => {
    expect(validateApproveArticle({ comment: "LGTM" }).success).toBe(true);
  });

  it("rejects comment exceeding 1000 chars", () => {
    const result = validateApproveArticle({ comment: "x".repeat(1001) });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("comment");
  });
});

// ─── AC-023.4  Approve — transitions ─────────────────────────────────────────
describe("AC-023.4 approveArticle transitions", () => {
  it("transitions PENDING_REVIEW → APPROVED", async () => {
    const result = await approveArticle(pendingArticle.id, pendingArticle, {});
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.status).toBe("APPROVED");
      expect(result.data.reviewerId).not.toBeNull();
      expect(result.data.approvedAt).not.toBeNull();
    }
  });

  it("blocks approval of DRAFT article", async () => {
    const result = await approveArticle(draftArticle.id, draftArticle, {});
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks approval of already APPROVED article", async () => {
    const result = await approveArticle(approvedArticle.id, approvedArticle, {});
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks approval of PUBLISHED article", async () => {
    const result = await approveArticle(publishedArticle.id, publishedArticle, {});
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("isAwaitingReview returns true only for PENDING_REVIEW", () => {
    expect(isAwaitingReview("PENDING_REVIEW")).toBe(true);
    expect(isAwaitingReview("DRAFT")).toBe(false);
    expect(isAwaitingReview("APPROVED")).toBe(false);
    expect(isAwaitingReview("PUBLISHED")).toBe(false);
  });
});

// ─── AC-023.5  Reject — validation ───────────────────────────────────────────
describe("AC-023.5 validateRejectArticle", () => {
  it("accepts a rejection comment", () => {
    const result = validateRejectArticle({ comment: "Needs more detail" });
    expect(result.success).toBe(true);
  });

  it("requires a rejection comment", () => {
    const result = validateRejectArticle({});
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("comment");
  });

  it("requires a non-empty rejection comment", () => {
    const result = validateRejectArticle({ comment: "" });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("comment");
  });

  it("rejects comment exceeding 1000 chars", () => {
    const result = validateRejectArticle({ comment: "x".repeat(1001) });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("comment");
  });
});

// ─── AC-023.6  Reject — transitions ──────────────────────────────────────────
describe("AC-023.6 rejectArticle transitions", () => {
  it("transitions PENDING_REVIEW → REJECTED", async () => {
    const result = await rejectArticle(
      pendingArticle.id, pendingArticle, { comment: "Incomplete" }
    );
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.data.status).toBe("REJECTED");
  });

  it("transitions APPROVED → REJECTED", async () => {
    const result = await rejectArticle(
      approvedArticle.id, approvedArticle, { comment: "Found errors" }
    );
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.data.status).toBe("REJECTED");
  });

  it("blocks rejection of DRAFT article", async () => {
    const result = await rejectArticle(
      draftArticle.id, draftArticle, { comment: "Not ready" }
    );
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks rejection without a comment", async () => {
    const result = await rejectArticle(
      pendingArticle.id, pendingArticle, {}
    );
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.type).toBe("validation");
      expect(result.details).toHaveProperty("comment");
    }
  });

  it("blocks rejection of PUBLISHED article", async () => {
    const result = await rejectArticle(
      publishedArticle.id, publishedArticle, { comment: "Pull back" }
    );
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });
});

// ─── AC-023.7  Full approval journey ─────────────────────────────────────────
describe("AC-023.7 full approval journey (DRAFT → PENDING_REVIEW → APPROVED)", () => {
  it("completes in sequence", async () => {
    // Step 1: submit
    const submit = await submitArticleForReview(
      draftArticle.id, draftArticle, { comment: "Please review" }
    );
    expect(submit.ok).toBe(true);

    // Step 2: approve (use the updated article from step 1)
    const afterSubmit = submit.ok ? submit.data : makeArticle({ status: "PENDING_REVIEW" });
    const approve = await approveArticle(
      afterSubmit.id, afterSubmit, { comment: "Approved!" }
    );
    expect(approve.ok).toBe(true);
    if (approve.ok) {
      expect(approve.data.status).toBe("APPROVED");
    }
  });
});
