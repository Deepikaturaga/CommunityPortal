/**
 * AC-030.10 – AC-030.13  Activity-feed data-accuracy tests.
 *
 * Tests cover the `transformActivityFeed` helper that normalises raw API
 * activity entries into display-ready props, including relative-time
 * formatting, type-to-label mapping, and truncation.
 *
 * AC-030.10  Activity entries are sorted newest-first.
 * AC-030.11  Each entry exposes a human-readable `typeLabel`.
 * AC-030.12  Descriptions longer than 120 chars are truncated with "…".
 * AC-030.13  At most MAX_FEED_ITEMS entries are returned when the API sends
 *            more.
 */

import {
  transformActivityFeed,
  MAX_FEED_ITEMS,
  ACTIVITY_LABELS,
} from "../../src/app/admin/dashboard/transformers";
import { makeActivityEntry, makeActivityFeed, type ActivityType } from "./fixtures";

// ---------------------------------------------------------------------------
// AC-030.10 — newest-first ordering
// ---------------------------------------------------------------------------

describe("AC-030.10 — newest-first ordering", () => {
  it("sorts entries with the most recent timestamp first", () => {
    const unsorted = [
      makeActivityEntry({ id: "a1", timestamp: "2024-06-15T08:00:00Z" }),
      makeActivityEntry({ id: "a2", timestamp: "2024-06-15T12:00:00Z" }),
      makeActivityEntry({ id: "a3", timestamp: "2024-06-15T10:00:00Z" }),
    ];

    const result = transformActivityFeed(unsorted);

    expect(result[0].id).toBe("a2"); // 12:00 → newest
    expect(result[1].id).toBe("a3"); // 10:00
    expect(result[2].id).toBe("a1"); // 08:00 → oldest
  });

  it("preserves single-entry feeds without error", () => {
    const feed = [makeActivityEntry({ id: "only" })];
    expect(transformActivityFeed(feed)).toHaveLength(1);
  });
});

// ---------------------------------------------------------------------------
// AC-030.11 — typeLabel mapping
// ---------------------------------------------------------------------------

describe("AC-030.11 — human-readable typeLabel", () => {
  const typeCases: ActivityType[] = [
    "USER_CREATED",
    "ORDER_PLACED",
    "ORDER_COMPLETED",
    "ORDER_CANCELLED",
    "PAYMENT_RECEIVED",
    "SYSTEM_ALERT",
  ];

  test.each(typeCases)(
    "type %s maps to a non-empty label",
    (type) => {
      const entry = makeActivityEntry({ type });
      const [result] = transformActivityFeed([entry]);
      expect(typeof result.typeLabel).toBe("string");
      expect(result.typeLabel.length).toBeGreaterThan(0);
    }
  );

  it("ACTIVITY_LABELS covers all known activity types", () => {
    const knownTypes: ActivityType[] = [
      "USER_CREATED",
      "ORDER_PLACED",
      "ORDER_COMPLETED",
      "ORDER_CANCELLED",
      "PAYMENT_RECEIVED",
      "SYSTEM_ALERT",
    ];
    knownTypes.forEach((t) => {
      expect(ACTIVITY_LABELS).toHaveProperty(t);
    });
  });
});

// ---------------------------------------------------------------------------
// AC-030.12 — description truncation
// ---------------------------------------------------------------------------

describe("AC-030.12 — description truncation", () => {
  it("leaves descriptions ≤ 120 chars untouched", () => {
    const short = "A".repeat(120);
    const [result] = transformActivityFeed([
      makeActivityEntry({ description: short }),
    ]);
    expect(result.description).toBe(short);
    expect(result.description.endsWith("…")).toBe(false);
  });

  it("truncates descriptions > 120 chars and appends ellipsis", () => {
    const long = "B".repeat(200);
    const [result] = transformActivityFeed([
      makeActivityEntry({ description: long }),
    ]);
    expect(result.description).toHaveLength(121); // 120 + "…"
    expect(result.description.endsWith("…")).toBe(true);
  });

  it("truncates at exactly 121 chars (boundary)", () => {
    const boundary = "C".repeat(121);
    const [result] = transformActivityFeed([
      makeActivityEntry({ description: boundary }),
    ]);
    expect(result.description.endsWith("…")).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// AC-030.13 — MAX_FEED_ITEMS cap
// ---------------------------------------------------------------------------

describe("AC-030.13 — feed size cap", () => {
  it(`returns at most ${MAX_FEED_ITEMS} entries when API sends more`, () => {
    const oversized = makeActivityFeed(MAX_FEED_ITEMS + 10);
    const result = transformActivityFeed(oversized);
    expect(result.length).toBeLessThanOrEqual(MAX_FEED_ITEMS);
  });

  it("returns all entries when feed is below the cap", () => {
    const small = makeActivityFeed(3);
    expect(transformActivityFeed(small)).toHaveLength(3);
  });

  it("returns an empty array for an empty feed", () => {
    expect(transformActivityFeed([])).toEqual([]);
  });

  it("MAX_FEED_ITEMS is a positive integer", () => {
    expect(typeof MAX_FEED_ITEMS).toBe("number");
    expect(MAX_FEED_ITEMS).toBeGreaterThan(0);
    expect(Number.isInteger(MAX_FEED_ITEMS)).toBe(true);
  });
});
