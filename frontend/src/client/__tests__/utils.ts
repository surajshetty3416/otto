/**
 * Test utilities for client tests
 */
import { expect } from "vitest";
import type { Call } from "../call";
import { framework } from "../api";

/**
 * Wait for a Call to complete (either success or failure)
 */
export async function waitForCall<T>(call: Call<any, T>): Promise<T> {
  return await call.promise!;
}

/**
 * Generate a random string with optional prefix
 */
export function randomString(prefix = "test"): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substring(7)}`;
}

/**
 * Assert that a call succeeded
 */
export function expectCallSuccess(call: Call<any, any>): void {
  expect(call.loading).toBe(false);
  expect(call.failed).toBe(false);
  expect(call.data).toBeDefined();
  expect(call.error).toBeUndefined();
}

/**
 * Assert that a call failed
 */
export function expectCallException(call: Call<any, any>): void {
  expect(call.loading).toBe(false);
  expect(call.failed).toBe(true);
  expect(call.exception).toBeDefined();
  expect(call.exception?.type).toBeDefined();
  expect(call.exception?.traceback).toBeDefined();
}

/**
 * Wait for a condition to be true with timeout
 */
export async function waitFor(
  condition: () => boolean,
  timeout = 5000,
  interval = 50
): Promise<void> {
  const startTime = Date.now();
  while (!condition()) {
    if (Date.now() - startTime > timeout) {
      throw new Error("Timeout waiting for condition");
    }
    await new Promise((resolve) => setTimeout(resolve, interval));
  }
}

/**
 * Sleep for a specified number of milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Test data factory for creating test documents
 */
export const testData = {
  /**
   * Create test data for OttoFeedback
   */
  feedback: (overrides?: Partial<any>) => ({
    comment: randomString("feedback"),
    value: Math.floor(Math.random() * 5) + 1,
    ...overrides,
  }),

  /**
   * Create test data for OttoScrapbook
   */
  scrapbook: (overrides?: Partial<any>) => ({
    content: randomString("scrapbook_content"),
    ...overrides,
  }),
};

/**
 * Cleanup helper - stores document names for cleanup
 */
export class TestCleanup {
  private docsToClean: Array<{ doctype: string; name: string }> = [];

  /**
   * Register a document for cleanup
   */
  register(doctype: string, name: string): void {
    this.docsToClean.push({ doctype, name });
  }

  /**
   * Clean up all registered documents
   */
  async cleanup(framework: any): Promise<void> {
    for (const { doctype, name } of this.docsToClean) {
      try {
        await framework.delete_doc(doctype, name).promise;
      } catch (error) {
        // Ignore errors during cleanup (document might already be deleted)
        console.warn(`Failed to cleanup ${doctype} ${name}:`, error);
      }
    }
    this.docsToClean = [];
  }

  /**
   * Get count of registered documents
   */
  get count(): number {
    return this.docsToClean.length;
  }
}

export async function beforeEachCb() {
  await framework.login(
    import.meta.env.VITE_TEST_USERNAME,
    import.meta.env.VITE_TEST_PASSWORD
  );
}

export async function afterEachCb() {
  await framework.logout();
}
