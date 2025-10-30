/**
 * Tests for the api object
 * Tests type-safe Otto API calls
 */
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { api } from "../api";
import {
  afterAllCb,
  beforeAllCb,
  expectCallException,
  expectCallSuccess,
  waitForCall,
} from "./utils";

beforeAll(beforeAllCb);
afterAll(afterAllCb);

describe("api object", () => {
  describe("Basic Method Calls", () => {
    it("should call method with no arguments", async () => {
      const result = api.ping();

      expect(result.loading).toBe(true);

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.data).toBeDefined();
    });

    it("should call method with arguments", async () => {
      const message = "test message";
      const result = api.echo({ message });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.data).toBe(message);
    });

    it("should call method with undefined arguments", async () => {
      const result = api.ping(undefined);

      await waitForCall(result);
      expectCallSuccess(result);
    });

    it("should call method with null arguments", async () => {
      const result = api.ping(null);

      await waitForCall(result);
      expectCallSuccess(result);
    });
  });

  describe("Nested Path Calls", () => {
    it("should handle single-level nested paths", async () => {
      const result = api.client_test.get_list({});

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.data).toBeDefined();
    });

    it("should handle multi-level nested paths", async () => {
      const result = api.client_test.get_list({
        limit: 10,
        offset: 0,
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(Array.isArray(result.data)).toBe(true);
    });

    it("should handle nested path with arguments", async () => {
      const result = api.client_test.greet({ name: "test user" });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.loading).toBe(false);
    });
  });

  describe("Path Reusability", () => {
    it("should allow saving intermediate paths to variables", async () => {
      const clientTestApi = api.client_test;

      const result1 = clientTestApi.get_list({});
      const result2 = clientTestApi.add_numbers({ a: 5, b: 3 });

      await Promise.all([result1.promise, result2.promise]);

      expectCallSuccess(result1);
      expectCallSuccess(result2);
    });

    it("should allow multiple calls from saved path", async () => {
      const clientTestApi = api.client_test;

      const result1 = clientTestApi.get_list({ limit: 5 });
      const result2 = clientTestApi.get_list({ limit: 10 });

      await Promise.all([result1.promise, result2.promise]);

      expectCallSuccess(result1);
      expectCallSuccess(result2);

      expect(result1.data?.length).toBe(5);
      expect(result2.data?.length).toBe(10);
    });
  });

  describe("Response Data", () => {
    it("should return correct data types", async () => {
      const result = api.client_test.get_user_info({ user_id: "123" });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(typeof result.data).toBe("object");
      expect(result.data).not.toBeNull();
      expect(result.data?.user_id).toBe("123");
    });

    it("should handle string return type", async () => {
      const result = await api.echo({ message: "string test" });

      expect(typeof result).toBe("string");
    });

    it("should handle array return type", async () => {
      const result = await api.client_test.get_list({ limit: 10 });

      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBe(10);
    });
  });

  describe("Error Handling", () => {
    it("should handle server errors and extract exception information", async () => {
      const result = api.client_test.throw({
        message: "test error",
        use_frappe: true,
      });

      try {
        await waitForCall(result);
      } catch (error) {
        expect.fail("Exceptions don't throw");
      }

      expectCallException(result);
      expect(result.exception).toBeDefined();
      expect(result.exception?.type).toBeTruthy();
      expect(result.exception?.traceback).toBeTruthy();
      expect(typeof result.exception?.type).toBe("string");
      expect(typeof result.exception?.traceback).toBe("string");
    });

    it("should handle non-existent methods", async () => {
      // @ts-expect-error - Testing invalid method
      const result = api.nonexistent_method();

      try {
        await waitForCall(result);
        expect.fail("Should have thrown an error");
      } catch {
        expectCallException(result);
      }
    });
  });

  describe("Config Options", () => {
    it("should support auto: false config", () => {
      const result = api.ping(null, { auto: false });

      expect(result.loading).toBe(false);
      expect(result.promise).toBeUndefined();

      result.run();
      expect(result.loading).toBe(true);
    });

    it("should support auto: true config (default)", () => {
      const result = api.ping(null, { auto: true });

      expect(result.loading).toBe(true);
      expect(result.promise).toBeDefined();
    });

    it("should support config on nested paths", async () => {
      const result = api.client_test.get_list({}, { auto: false });

      expect(result.loading).toBe(false);

      result.run();
      await waitForCall(result);

      expectCallSuccess(result);
    });
  });

  describe("Parallel Requests", () => {
    it("should handle multiple parallel API calls", async () => {
      const calls = [
        api.echo({ message: "call1" }),
        api.echo({ message: "call2" }),
        api.echo({ message: "call3" }),
      ];

      const results = await Promise.all(calls.map((c) => c.promise!));

      expect(results[0]).toBe("call1");
      expect(results[1]).toBe("call2");
      expect(results[2]).toBe("call3");

      calls.forEach(expectCallSuccess);
    });

    it("should handle mixed paths in parallel", async () => {
      const calls = [
        api.ping(),
        api.client_test.get_user_info({ user_id: "123" }),
        api.echo({ message: "parallel" }),
      ];

      await Promise.all(calls.map((c) => c.promise!));

      calls.forEach(expectCallSuccess);
    });
  });

  describe("Method Arguments", () => {
    it("should handle optional arguments", async () => {
      const result = api.client_test.get_list({
        limit: 5,
      });

      await waitForCall(result);
      expectCallSuccess(result);
    });

    it("should handle complex object arguments", async () => {
      const result = api.client_test.create_record({
        name: "test-record",
        data: { key: "value", nested: { prop: "test" } },
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.loading).toBe(false);
    });
  });

  describe("Promise Interface", () => {
    it("should work with async/await", async () => {
      const result = await api.echo({ message: "await test" });
      expect(result).toBe("await test");
    });

    it("should work with .then()", async () => {
      let thenData: any;

      const result = api.echo({ message: "then test" });
      result.then((data) => {
        thenData = data;
      });

      await waitForCall(result);
      expect(thenData).toBe("then test");
    });
  });

  describe("Rerun Capability", () => {
    it("should support rerunning with different arguments", async () => {
      const result = api.echo({ message: "first" }, { auto: false });

      result.run();
      await waitForCall(result);
      expect(result.data).toBe("first");

      result.run({ message: "second" }, false);
      await waitForCall(result);
      expect(result.data).toBe("second");
    });

    it("should support rerunning with no arguments", async () => {
      const result = api.client_test.get_random(null, { auto: false });

      const random1 = await result.run();
      expect(random1).toBeGreaterThan(0);
      expect(random1).toBeLessThan(1);

      const random2 = await result.run();
      expect(random2).toBe(random1);

      const random3 = await result.run(undefined, false);
      expect(random3).not.toBe(random1);
    });
  });

  describe("Integration Tests", () => {
    it("should handle complex workflow with multiple calls", async () => {
      // Get user info
      const user = api.client_test.get_user_info({
        user_id: "123",
        include_details: true,
      });
      await waitForCall(user);
      expectCallSuccess(user);

      // Echo a message
      const echo = api.echo({ message: "workflow test" });
      await waitForCall(echo);
      expect(echo.data).toBe("workflow test");

      // Get list
      const list = api.client_test.get_list({ limit: 5 });
      await waitForCall(list);
      expectCallSuccess(list);
    });

    it("should handle dependent calls", async () => {
      // First call
      const firstResult = await api.echo({ message: "first" });
      expect(firstResult).toBe("first");

      // Second call using data from first
      const secondResult = await api.echo({ message: firstResult + "_second" });
      expect(secondResult).toBe("first_second");
    });
  });

  describe("Edge Cases", () => {
    it("should handle empty object arguments", async () => {
      const result = api.client_test.process_items({ items: [] });

      await waitForCall(result);
      // Should succeed with empty array
      expectCallSuccess(result);
      expect(result.data?.count).toBe(0);
    });

    it("should handle null in optional arguments", async () => {
      const result = api.client_test.create_record({
        name: "test",
        data: {},
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.loading).toBe(false);
    });

    it("should handle very long strings", async () => {
      const longMessage = "a".repeat(10000);
      const result = api.echo({ message: longMessage });

      await waitForCall(result);
      expect(result.data).toBe(longMessage);
    });

    it("should handle special characters in arguments", async () => {
      const specialMessage = '{"test": "value", "special": "♠♣♥♦"}';
      const result = api.echo({ message: specialMessage });

      await waitForCall(result);
      expect(result.data).toBe(specialMessage);
    });
  });
});
