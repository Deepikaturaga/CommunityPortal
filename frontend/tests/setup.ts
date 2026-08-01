/**
 * Global Jest setup — runs after the test framework is installed in the VM.
 * Configures @testing-library/jest-dom matchers and global mocks.
 */

import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Silence noisy React warnings in test output
// ---------------------------------------------------------------------------
const originalError = console.error.bind(console);
beforeAll(() => {
  jest.spyOn(console, "error").mockImplementation((...args: unknown[]) => {
    const msg = typeof args[0] === "string" ? args[0] : "";
    // Suppress known React/Next.js test-env warnings
    if (
      msg.includes("Warning: ReactDOM.render") ||
      msg.includes("Warning: An update to") ||
      msg.includes("Error: Not implemented")
    ) {
      return;
    }
    originalError(...args);
  });
});

afterAll(() => {
  jest.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// Reset all mocks between tests (prevent state bleed)
// ---------------------------------------------------------------------------
afterEach(() => {
  jest.clearAllMocks();
});
