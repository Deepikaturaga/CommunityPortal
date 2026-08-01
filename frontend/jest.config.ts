import type { Config } from "jest";
import nextJest from "next/jest.js";

const createJestConfig = nextJest({
  // Points to the Next.js app root so next/jest loads next.config.js + .env
  dir: "./",
});

const customConfig: Config = {
  displayName: "frontend",
  testEnvironment: "jsdom",

  // ── Test discovery ──────────────────────────────────────────────────────
  testMatch: [
    "<rootDir>/tests/**/*.test.{ts,tsx}",
    "<rootDir>/src/**/*.test.{ts,tsx}",
  ],

  // ── Coverage ────────────────────────────────────────────────────────────
  collectCoverageFrom: [
    "src/app/admin/dashboard/**/*.{ts,tsx}",
    "src/components/admin/dashboard/**/*.{ts,tsx}",
    "src/middleware/**/*.{ts,tsx}",
    "!**/*.d.ts",
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 85,
      lines: 85,
      statements: 85,
    },
  },

  // ── Module aliases ───────────────────────────────────────────────────────
  moduleNameMapper: {
    "^next/navigation$":
      "<rootDir>/tests/admin-dashboard/__mocks__/next-navigation.ts",
    "^next/headers$":
      "<rootDir>/tests/admin-dashboard/__mocks__/next-headers.ts",
    "^@/(.*)$": "<rootDir>/src/$1",
    "\\.module\\.(css|scss|sass)$": "identity-obj-proxy",
    "\\.(css|scss|sass)$": "identity-obj-proxy",
  },

  // ── Setup ────────────────────────────────────────────────────────────────
  setupFilesAfterEnv: ["<rootDir>/tests/setup.ts"],
};

export default createJestConfig(customConfig);
