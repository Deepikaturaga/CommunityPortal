// jest.config.ts
import type { Config } from "jest";

const config: Config = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  rootDir: ".",
  roots: ["<rootDir>/src", "<rootDir>/tests"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  transform: {
    "^.+\\.(ts|tsx)$": [
      "ts-jest",
      {
        tsconfig: {
          jsx: "react-jsx",
          strict: true,
          esModuleInterop: true,
          moduleResolution: "node",
          module: "commonjs",
          types: ["jest", "@testing-library/jest-dom"],
        },
      },
    ],
  },
  // Runs after the test framework (jest-circus) is installed in the environment.
  // Used to extend expect with @testing-library/jest-dom matchers.
  setupFilesAfterFramework: ["<rootDir>/tests/setup.ts"],
  testMatch: ["**/*.test.ts", "**/*.test.tsx"],
  globals: {},
  collectCoverageFrom: [
    "src/lib/kb/**/*.ts",
    "src/components/kb/**/*.tsx",
    "!**/*.d.ts",
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};

export default config;
