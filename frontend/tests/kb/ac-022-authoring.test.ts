/**
 * AC-022: KB Article Authoring
 *
 * VER-002 · Tests authoring flows: create, edit, delete, slug generation,
 * content-change detection, and validation of required fields.
 */
import {
  validateCreateArticle,
  validateUpdateArticle,
  slugify,
  hasContentChanged,
} from "@/lib/kb/validation";
import {
  createArticle,
  updateArticle,
  removeArticle,
} from "@/lib/kb/service";
import {
  draftArticle,
  rejectedArticle,
  makeArticle,
} from "./fixtures";
import { server, resetArticleStore } from "./msw-handlers";

// ─── MSW lifecycle ────────────────────────────────────────────────────────────
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => { server.resetHandlers(); resetArticleStore(); });
afterAll(() => server.close());

// ─── AC-022.1  Create validation — happy path ─────────────────────────────────
describe("AC-022.1 createKbArticle input validation — valid inputs", () => {
  it("accepts a complete valid article", () => {
    const result = validateCreateArticle({
      title: "Onboarding Guide",
      content: "Welcome to the team!",
      category: "PROCEDURE",
      tags: ["hr", "onboarding"],
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.title).toBe("Onboarding Guide");
      expect(result.data.category).toBe("PROCEDURE");
    }
  });

  it("defaults tags to empty array when omitted", () => {
    const result = validateCreateArticle({
      title: "T",
      content: "C",
      category: "FAQ",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.tags).toEqual([]);
    }
  });

  it("accepts optional summary", () => {
    const result = validateCreateArticle({
      title: "T",
      content: "C",
      category: "TECHNICAL",
      summary: "Short summary",
    });
    expect(result.success).toBe(true);
  });
});

// ─── AC-022.2  Create validation — invalid inputs ────────────────────────────
describe("AC-022.2 createKbArticle input validation — invalid inputs", () => {
  it("rejects missing title", () => {
    const result = validateCreateArticle({ content: "C", category: "FAQ" });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("title");
  });

  it("rejects empty title", () => {
    const result = validateCreateArticle({ title: "", content: "C", category: "FAQ" });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("title");
  });

  it("rejects missing content", () => {
    const result = validateCreateArticle({ title: "T", category: "FAQ" });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("content");
  });

  it("rejects invalid category", () => {
    const result = validateCreateArticle({ title: "T", content: "C", category: "INVALID" });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("category");
  });

  it("rejects title exceeding 255 characters", () => {
    const result = validateCreateArticle({
      title: "A".repeat(256),
      content: "C",
      category: "FAQ",
    });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("title");
  });

  it("rejects summary exceeding 500 characters", () => {
    const result = validateCreateArticle({
      title: "T",
      content: "C",
      category: "FAQ",
      summary: "S".repeat(501),
    });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("summary");
  });
});

// ─── AC-022.3  Slug generation ────────────────────────────────────────────────
describe("AC-022.3 slugify utility", () => {
  it("lowercases and hyphenates", () => {
    expect(slugify("Hello World")).toBe("hello-world");
  });

  it("strips special characters", () => {
    expect(slugify("What is OAuth 2.0?")).toBe("what-is-oauth-20");
  });

  it("trims leading/trailing hyphens", () => {
    expect(slugify("  --Test--  ")).toBe("test");
  });

  it("collapses multiple spaces", () => {
    expect(slugify("A   B   C")).toBe("a-b-c");
  });
});

// ─── AC-022.4  Content-change detection ──────────────────────────────────────
describe("AC-022.4 hasContentChanged", () => {
  const base = { title: "T", content: "C", summary: "S" };

  it("returns true when title changes", () => {
    expect(hasContentChanged(base, { title: "T2" })).toBe(true);
  });

  it("returns true when content changes", () => {
    expect(hasContentChanged(base, { content: "C2" })).toBe(true);
  });

  it("returns true when summary changes", () => {
    expect(hasContentChanged(base, { summary: "S2" })).toBe(true);
  });

  it("returns false when only tags change", () => {
    expect(hasContentChanged(base, { tags: ["new"] })).toBe(false);
  });

  it("returns false when no relevant fields change", () => {
    expect(hasContentChanged(base, {})).toBe(false);
  });
});

// ─── AC-022.5  Service — createArticle (integration via MSW) ─────────────────
describe("AC-022.5 service.createArticle", () => {
  it("creates a new article and returns it", async () => {
    const result = await createArticle({
      title: "New FAQ Entry",
      content: "Detailed explanation",
      category: "FAQ",
    });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.title).toBe("New FAQ Entry");
      expect(result.data.status).toBe("DRAFT");
    }
  });

  it("returns validation error when title is missing", async () => {
    const result = await createArticle({ content: "C", category: "FAQ" });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.type).toBe("validation");
      expect(result.details).toHaveProperty("title");
    }
  });
});

// ─── AC-022.6  Service — updateArticle ───────────────────────────────────────
describe("AC-022.6 service.updateArticle", () => {
  it("updates a DRAFT article", async () => {
    const result = await updateArticle(draftArticle.id, draftArticle, {
      title: "Updated Title",
    });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.title).toBe("Updated Title");
      expect(result.data.version).toBe(draftArticle.version + 1);
    }
  });

  it("updates a REJECTED article", async () => {
    const result = await updateArticle(rejectedArticle.id, rejectedArticle, {
      content: "Fixed content",
    });
    expect(result.ok).toBe(true);
  });

  it("blocks update of a PENDING_REVIEW article", async () => {
    const pending = makeArticle({ status: "PENDING_REVIEW" });
    const result = await updateArticle(pending.id, pending, { title: "X" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });

  it("blocks update of a PUBLISHED article", async () => {
    const published = makeArticle({ status: "PUBLISHED" });
    const result = await updateArticle(published.id, published, { title: "X" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });
});

// ─── AC-022.7  Update validation ─────────────────────────────────────────────
describe("AC-022.7 validateUpdateArticle", () => {
  it("accepts partial updates", () => {
    expect(validateUpdateArticle({ title: "New title" }).success).toBe(true);
    expect(validateUpdateArticle({ content: "New content" }).success).toBe(true);
    expect(validateUpdateArticle({}).success).toBe(true);
  });

  it("rejects empty title on update", () => {
    const result = validateUpdateArticle({ title: "" });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("title");
  });

  it("rejects invalid category on update", () => {
    const result = validateUpdateArticle({ category: "BOGUS" });
    expect(result.success).toBe(false);
    if (!result.success) expect(result.errors).toHaveProperty("category");
  });
});

// ─── AC-022.8  Service — removeArticle ───────────────────────────────────────
describe("AC-022.8 service.removeArticle", () => {
  it("deletes a DRAFT article", async () => {
    const result = await removeArticle(draftArticle.id, draftArticle);
    expect(result.ok).toBe(true);
  });

  it("deletes a REJECTED article", async () => {
    const result = await removeArticle(rejectedArticle.id, rejectedArticle);
    expect(result.ok).toBe(true);
  });

  it("blocks deletion of a PUBLISHED article", async () => {
    const published = makeArticle({ status: "PUBLISHED" });
    const result = await removeArticle(published.id, published);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe("forbidden");
  });
});
