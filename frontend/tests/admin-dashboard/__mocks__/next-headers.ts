/**
 * Manual mock for next/headers (cookies / headers helpers used in server
 * components and middleware).
 */

export const cookies = jest.fn(() => ({
  get: jest.fn((name: string) => ({ name, value: "" })),
  getAll: jest.fn(() => []),
  has: jest.fn(() => false),
  set: jest.fn(),
  delete: jest.fn(),
}));

export const headers = jest.fn(() => ({
  get: jest.fn((_name: string) => null),
  has: jest.fn(() => false),
  entries: jest.fn(() => [][Symbol.iterator]()),
}));
