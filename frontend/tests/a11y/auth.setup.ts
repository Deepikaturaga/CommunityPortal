/**
 * auth.setup.ts
 *
 * Playwright global-setup that logs in once and saves the authenticated
 * storage state to `tests/a11y/.auth/user.json`.
 *
 * Referenced by `playwright.config.ts` as a `setup` project dependency so
 * all authenticated tests reuse the cached session without re-authenticating
 * on every spec.
 *
 * Environment variables (set in .env.test or CI secrets — never committed):
 *   TEST_USER_EMAIL    login email for the test user
 *   TEST_USER_PASSWORD password for the test user
 *   BASE_URL           override the base URL (default: http://localhost:5173)
 */

import { chromium, FullConfig } from "@playwright/test";
import path from "path";

export const AUTH_STATE_PATH = path.join(
  __dirname,
  ".auth",
  "user.json",
);

async function globalSetup(_config: FullConfig) {
  const baseURL =
    process.env["BASE_URL"] ?? "http://localhost:5173";
  const email =
    process.env["TEST_USER_EMAIL"] ?? "testuser@example.local";
  const password = process.env["TEST_USER_PASSWORD"] ?? "";

  if (!password) {
    throw new Error(
      "TEST_USER_PASSWORD environment variable is required for authenticated a11y / responsive tests.",
    );
  }

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto(`${baseURL}/login`);
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole("button", { name: /sign in|log in/i }).click();

  // Wait until the app signals a successful login (adjust selector to match
  // the real post-login landing page introduced by upstream phases).
  await page.waitForURL(`${baseURL}/dashboard`, { timeout: 15_000 });

  await context.storageState({ path: AUTH_STATE_PATH });
  await browser.close();
}

export default globalSetup;
