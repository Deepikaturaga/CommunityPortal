/**
 * playwright.config.ts
 *
 * Root Playwright configuration for accessibility (TASK-060) and
 * responsive (TASK-061) test suites.
 *
 * Projects:
 *   smoke         — infrastructure validation; no app required (VER-023)
 *   setup         — one-time login; saves storageState for auth tests
 *   a11y          — axe-core scans on all screens (depends on setup)
 *   responsive    — layout integrity at all breakpoints (depends on setup)
 *
 * Environment variables:
 *   BASE_URL            application URL (default: http://localhost:5173)
 *   TEST_USER_EMAIL     login email for the seeded test user
 *   TEST_USER_PASSWORD  login password  ← required; never commit a value
 *   CI                  set by CI runners; enables retries + reporter options
 */

import { defineConfig, devices } from "@playwright/test";
import path from "path";

const BASE_URL = process.env["BASE_URL"] ?? "http://localhost:5173";
const AUTH_STATE = path.join(__dirname, "tests/a11y/.auth/user.json");

export default defineConfig({
  // ── Discover tests ─────────────────────────────────────────────────────────
  testDir: "./tests",
  testMatch: ["**/*.spec.ts"],

  // ── Global timeouts ────────────────────────────────────────────────────────
  timeout: 30_000,
  expect: { timeout: 5_000 },

  // ── Parallelism ────────────────────────────────────────────────────────────
  // Each worker gets its own browser context; auth state is read-only shared.
  fullyParallel: true,
  workers: process.env["CI"] ? 2 : undefined,

  // ── Retries (flake-tolerance) ──────────────────────────────────────────────
  retries: process.env["CI"] ? 2 : 0,

  // ── Reporters ─────────────────────────────────────────────────────────────
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
    // Emit JUnit XML for CI artifact collection (e.g. GitHub Actions test-results)
    ["junit", { outputFile: "playwright-report/junit.xml" }],
  ],

  // ── Shared browser settings ────────────────────────────────────────────────
  use: {
    baseURL: BASE_URL,
    // Capture screenshot + trace on first failure only (keeps artifact size bounded)
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    trace: "on-first-retry",
  },

  // ── Projects ───────────────────────────────────────────────────────────────
  projects: [
    // 0. Smoke / infrastructure validation — no live app required (VER-023).
    //    Validates that the test harness configuration, fixture exports, and
    //    shared utilities are structurally sound without a running server.
    {
      name: "smoke",
      testMatch: /tests\/validation\/smoke\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },

    // 1. Setup project: authenticate once and persist session
    {
      name: "setup",
      testMatch: /auth\.setup\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },

    // 2. Accessibility scans — Chromium only (axe is engine-agnostic but we
    //    run one primary engine to keep CI times predictable; extend here to
    //    add Firefox/WebKit if required by acceptance criteria).
    {
      name: "a11y-chromium",
      testMatch: /tests\/a11y\/accessibility.*\.spec\.ts/,
      dependencies: ["setup"],
      use: {
        ...devices["Desktop Chrome"],
        // storageState for auth screens is applied per-describe in the spec
      },
    },

    // 3. Responsive layout tests — one project per canonical viewport so
    //    Playwright labels results clearly in the HTML report.
    {
      name: "responsive-mobile",
      testMatch: /tests\/responsive\/responsive\.spec\.ts/,
      dependencies: ["setup"],
      use: {
        ...devices["iPhone 12"],
        storageState: AUTH_STATE,
      },
    },
    {
      name: "responsive-tablet",
      testMatch: /tests\/responsive\/responsive\.spec\.ts/,
      dependencies: ["setup"],
      use: {
        ...devices["iPad (gen 7)"],
        storageState: AUTH_STATE,
      },
    },
    {
      name: "responsive-desktop",
      testMatch: /tests\/responsive\/responsive\.spec\.ts/,
      dependencies: ["setup"],
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1280, height: 800 },
        storageState: AUTH_STATE,
      },
    },
  ],

  // ── Web server (optional local dev startup) ────────────────────────────────
  // Uncomment and adjust the command if you want `playwright test` to start the
  // dev server automatically.  In CI, prefer starting the server in a prior step.
  //
  // webServer: {
  //   command: "pnpm run dev",
  //   url: BASE_URL,
  //   reuseExistingServer: !process.env["CI"],
  //   timeout: 60_000,
  // },
});
