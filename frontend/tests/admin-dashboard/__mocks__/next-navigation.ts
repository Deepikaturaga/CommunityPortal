/**
 * Manual mock for next/navigation used across admin-dashboard tests.
 * Jest automatically resolves this when `moduleNameMapper` maps
 * "next/navigation" → "<rootDir>/tests/admin-dashboard/__mocks__/next-navigation.ts"
 * (see jest.config.ts).
 */

export const useRouter = jest.fn(() => ({
  push: jest.fn(),
  replace: jest.fn(),
  prefetch: jest.fn(),
  back: jest.fn(),
  refresh: jest.fn(),
}));

export const usePathname = jest.fn(() => "/admin/dashboard");

export const useSearchParams = jest.fn(() => new URLSearchParams());

export const redirect = jest.fn((url: string) => {
  throw new Error(`NEXT_REDIRECT:${url}`);
});

export const notFound = jest.fn(() => {
  throw new Error("NEXT_NOT_FOUND");
});
