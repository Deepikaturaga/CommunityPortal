/**
 * MSW v2 Node server for Jest tests.
 * Import and call setup/teardown in test files.
 */
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
