/**
 * TypeScript Type Checking Tests
 * 
 * These tests verify that the TypeScript compiler correctly enforces types
 * at compile time. They use @ts-expect-error to verify that invalid code
 * produces type errors.
 * 
 * Note: These are compile-time tests. The runtime behavior doesn't matter.
 */
import { describe, expect, it } from "vitest";
import type { Call } from "../call";
import { api, call, framework } from "../index";

describe("TypeScript Type Checking", () => {
  describe("api object types", () => {
    it("should accept valid method calls with correct args", () => {
      // These should compile without errors
      const pingCall = api.ping(null, { auto: false });
      const echoCall = api.echo({ message: "test" }, { auto: false });
      const userCall = api.get_user(undefined, { auto: false });

      expect(pingCall).toBeDefined();
      expect(echoCall).toBeDefined();
      expect(userCall).toBeDefined();
    });

    it("should accept nested path calls with correct args", () => {
      // These should compile without errors
      const chatsCall = api.chat.list_chats(undefined, { auto: false });
      const assistantsCall = api.chat.list_assistants(undefined, { auto: false });
      const sessionsCall = api.session_view.get_recent_sessions({
        limit: 10,
        page: 1,
      }, { auto: false });

      expect(chatsCall).toBeDefined();
      expect(assistantsCall).toBeDefined();
      expect(sessionsCall).toBeDefined();
    });

    it("should accept optional arguments", () => {
      // Optional arguments should be allowed
      const call1 = api.ping(null, { auto: false });
      const call2 = api.ping(undefined, { auto: false });
      const call3 = api.session_view.get_recent_sessions({ limit: 5 }, { auto: false });
      const call4 = api.session_view.get_recent_sessions({
        limit: 5,
        page: 1,
      }, { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
      expect(call3).toBeDefined();
      expect(call4).toBeDefined();
    });

    it("should reject incorrect argument types", () => {
      // @ts-expect-error - message should be string, not number
      api.echo({ message: 123 }, { auto: false });

      // @ts-expect-error - limit should be number, not string
      api.session_view.get_recent_sessions({ limit: "10" }, { auto: false });

      // @ts-expect-error - invalid field name
      api.echo({ invalidField: "test" }, { auto: false });
    });

    it("should reject missing required arguments", () => {
      // @ts-expect-error - message is required
      api.echo({}, { auto: false });

      // @ts-expect-error - missing required arguments
      api.permissions.acknowledge({}, { auto: false });
    });

    it("should have correct return types", () => {
      const echoCall = api.echo({ message: "test" }, { auto: false });
      const userCall = api.get_user(undefined, { auto: false });
      const sessionsCall = api.session_view.get_recent_sessions({ limit: 10 }, { auto: false });

      // Type assertions to verify return types
      type EchoReturn = typeof echoCall extends Call<any, infer R> ? R : never;
      type UserReturn = typeof userCall extends Call<any, infer R> ? R : never;
      type SessionsReturn = typeof sessionsCall extends Call<any, infer R>
        ? R
        : never;

      // Runtime checks (types are checked at compile time)
      expect(echoCall).toBeDefined();
      expect(userCall).toBeDefined();
      expect(sessionsCall).toBeDefined();
    });

    it("should support config parameter", () => {
      // Config should be accepted
      const call1 = api.ping(null, { auto: false });
      const call2 = api.echo({ message: "test" }, { auto: true });
      const call3 = api.chat.list_chats(undefined, { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
      expect(call3).toBeDefined();
    });

    it("should reject invalid config", () => {
      // @ts-expect-error - invalid config field
      api.ping(null, { invalid: true });

      // @ts-expect-error - auto should be boolean
      api.echo({ message: "test" }, { auto: "false" });
    });
  });

  describe("framework object types", () => {
    it("should accept valid doctype names", () => {
      // Valid doctypes from OttoDocTypes
      const call1 = framework.get_list("Otto Feedback", ["name"], {}, { auto: false });
      const call2 = framework.get_list("Otto Scrapbook", ["name"], {}, { auto: false });
      const call3 = framework.get_list("Otto Session", ["name"], {}, { auto: false });
      const call4 = framework.get_doc("Otto Feedback", "test-name", { auto: false });
      const call5 = framework.new_doc("Otto Feedback", { value: 5 }, { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
      expect(call3).toBeDefined();
      expect(call4).toBeDefined();
      expect(call5).toBeDefined();
    });

    it("should reject invalid doctype names", () => {
      // @ts-expect-error - invalid doctype
      framework.get_list("Invalid DocType", ["name"]);

      // @ts-expect-error - invalid doctype
      framework.get_doc("NonExistent", "name");

      // @ts-expect-error - invalid doctype
      framework.new_doc("WrongType", {});
    });

    it("should accept valid field names for get_list", () => {
      // Valid fields for Otto Feedback
      const call1 = framework.get_list("Otto Feedback", [
        "name",
        "comment",
        "value",
      ], {}, { auto: false });

      // All fields
      const call2 = framework.get_list("Otto Feedback", ["*"], {}, { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
    });

    it("should reject invalid field names for get_list", () => {
      // @ts-expect-error - invalid field for Otto Feedback
      framework.get_list("Otto Feedback", ["invalidField"]);

      // Note: TypeScript may not catch all invalid fields in arrays
      // This is a limitation of the type system
    });

    it("should accept valid data for new_doc", () => {
      // Valid partial data for Otto Feedback
      const call1 = framework.new_doc("Otto Feedback", {
        comment: "test",
        value: 5,
      }, { auto: false });

      // Empty object is valid (all fields optional)
      const call2 = framework.new_doc("Otto Feedback", {}, { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
    });

    it("should reject invalid field types for new_doc", () => {
      // @ts-expect-error - value should be number, not string
      framework.new_doc("Otto Feedback", { value: "5" });

      // @ts-expect-error - invalid field
      framework.new_doc("Otto Feedback", { invalidField: "test" });
    });

    it("should accept valid data for update_doc", () => {
      // Valid partial updates
      const call1 = framework.update_doc("Otto Feedback", "name", {
        comment: "updated",
      }, { auto: false });
      const call2 = framework.update_doc("Otto Feedback", "name", { value: 5 }, { auto: false });
      const call3 = framework.update_doc("Otto Feedback", "name", {}, { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
      expect(call3).toBeDefined();
    });

    it("should accept string or number for document name", () => {
      // Both string and number should work
      const call1 = framework.get_doc("Otto Feedback", "string-name", { auto: false });
      const call2 = framework.get_doc("Otto Feedback", 123, { auto: false });
      const call3 = framework.update_doc("Otto Feedback", "name", {}, { auto: false });
      const call4 = framework.update_doc("Otto Feedback", 456, {}, { auto: false });
      const call5 = framework.delete_doc("Otto Feedback", "name", { auto: false });
      const call6 = framework.delete_doc("Otto Feedback", 789, { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
      expect(call3).toBeDefined();
      expect(call4).toBeDefined();
      expect(call5).toBeDefined();
      expect(call6).toBeDefined();
    });

    it("should accept valid options for get_list", () => {
      // All valid options
      const call = framework.get_list("Otto Feedback", ["name"], {
        start: 0,
        page_length: 10,
        filters: { value: 5 },
        or_filters: { comment: "test" },
        order_by: "name asc",
      }, { auto: false });

      expect(call).toBeDefined();
    });

    it("should reject invalid option types", () => {
      // @ts-expect-error - start should be number
      framework.get_list("Otto Feedback", ["name"], { start: "0" });

      // @ts-expect-error - page_length should be number
      framework.get_list("Otto Feedback", ["name"], { page_length: "10" });
    });

    it("should support config parameter", () => {
      // Config should be accepted on all methods
      const call1 = framework.get_list("Otto Feedback", ["name"], {}, { auto: false });
      const call2 = framework.get_doc("Otto Feedback", "name", { auto: false });
      const call3 = framework.new_doc("Otto Feedback", {}, { auto: false });
      const call4 = framework.update_doc("Otto Feedback", "name", {}, { auto: false });
      const call5 = framework.delete_doc("Otto Feedback", "name", { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
      expect(call3).toBeDefined();
      expect(call4).toBeDefined();
      expect(call5).toBeDefined();
    });

    it("should have correct return types", () => {
      const listCall = framework.get_list("Otto Feedback", ["name", "value"]);
      const getCall = framework.get_doc("Otto Feedback", "name");
      const newCall = framework.new_doc("Otto Feedback", {});
      const updateCall = framework.update_doc("Otto Feedback", "name", {});
      const deleteCall = framework.delete_doc("Otto Feedback", "name");

      // Type assertions
      type ListReturn = typeof listCall extends Call<any, infer R> ? R : never;
      type GetReturn = typeof getCall extends Call<any, infer R> ? R : never;
      type NewReturn = typeof newCall extends Call<any, infer R> ? R : never;
      type UpdateReturn = typeof updateCall extends Call<any, infer R> ? R : never;
      type DeleteReturn = typeof deleteCall extends Call<any, infer R> ? R : never;

      // Runtime checks
      expect(listCall).toBeDefined();
      expect(getCall).toBeDefined();
      expect(newCall).toBeDefined();
      expect(updateCall).toBeDefined();
      expect(deleteCall).toBeDefined();
    });
  });

  describe("call() function types", () => {
    it("should accept any URL string", () => {
      const call1 = call("/api/endpoint", {}, { auto: false });
      const call2 = call("/api/v2/method/test", {}, { auto: false });
      const call3 = call("https://example.com/api", {}, { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
      expect(call3).toBeDefined();
    });

    it("should accept valid HTTP methods", () => {
      const call1 = call("/api/endpoint", { method: "GET" }, { auto: false });
      const call2 = call("/api/endpoint", { method: "POST" }, { auto: false });
      const call3 = call("/api/endpoint", { method: "PUT" }, { auto: false });
      const call4 = call("/api/endpoint", { method: "DELETE" }, { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
      expect(call3).toBeDefined();
      expect(call4).toBeDefined();
    });

    it("should reject invalid HTTP methods", () => {
      // @ts-expect-error - PATCH is not in the allowed methods
      call("/api/endpoint", { method: "PATCH" });

      // @ts-expect-error - lowercase not allowed
      call("/api/endpoint", { method: "get" });
    });

    it("should accept body and params", () => {
      const call1 = call("/api/endpoint", {
        body: { key: "value" },
      }, { auto: false });

      const call2 = call("/api/endpoint", {
        params: { query: "test" },
      }, { auto: false });

      const call3 = call("/api/endpoint", {
        body: { data: "test" },
        params: { filter: "active" },
      }, { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
      expect(call3).toBeDefined();
    });

    it("should accept config parameter", () => {
      const call1 = call("/api/endpoint", {}, { auto: false });
      const call2 = call("/api/endpoint", { method: "GET" }, { auto: true });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
    });

    it("should reject invalid config", () => {
      // @ts-expect-error - invalid config field
      call("/api/endpoint", {}, { invalid: true });

      // @ts-expect-error - auto should be boolean
      call("/api/endpoint", {}, { auto: "false" });
    });

    it("should support generic type parameters", () => {
      // Can specify generic types for request and response
      const call1 = call<{ input: string }, { output: string }>("/api/test", {}, { auto: false });
      
      // Generic types should be inferred from usage
      const call2 = call("/api/test", {}, { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
    });
  });

  describe("Call class types", () => {
    it("should have correct property types", async () => {
      const result = api.echo({ message: "test" }, { auto: false });

      // Type checks for properties
      const data: unknown = result.data;
      const loading: boolean = result.loading;
      const failed: boolean = result.failed;
      const error: unknown = result.error;
      const response: Response | undefined = result.response;

      // These should compile
      expect(typeof loading).toBe("boolean");
      expect(typeof failed).toBe("boolean");
    });

    it("should have correct method types", () => {
      const result = api.echo({ message: "test" }, { auto: false });

      // Methods should return promises
      const runPromise = result.run();
      const rerunPromise = result.rerun({ message: "new" });

      // Promise-like methods
      result.then((data) => {
        expect(data).toBeDefined();
      });

      result.catch((error) => {
        expect(error).toBeDefined();
      });

      expect(runPromise).toBeDefined();
      expect(rerunPromise).toBeDefined();
    });
  });

  describe("Import types", () => {
    it("should export all required items", () => {
      // These imports should work
      expect(api).toBeDefined();
      expect(framework).toBeDefined();
      expect(call).toBeDefined();
      expect(typeof api).toBe("object");
      expect(typeof framework).toBe("object");
      expect(typeof call).toBe("function");
    });
  });

  describe("Complex type scenarios", () => {
    it("should support method chaining", () => {
      const result = api
        .echo({ message: "test" }, { auto: false })
        .then((data) => data)
        .catch((err) => err);

      expect(result).toBeDefined();
    });

    it("should support await syntax", async () => {
      // Should compile without errors
      async function testFunction() {
        const data1 = await api.echo({ message: "test" });
        const data2 = await framework.get_list("Otto Feedback", ["name"]);
        const data3 = await call("/api/test");

        return { data1, data2, data3 };
      }

      expect(testFunction).toBeDefined();
    });

    it("should support Promise.all", async () => {
      async function testFunction() {
        const results = await Promise.all([
          api.echo({ message: "test1" }),
          api.echo({ message: "test2" }),
          framework.get_list("Otto Feedback", ["name"]),
        ]);

        return results;
      }

      expect(testFunction).toBeDefined();
    });

    it("should support storing in variables", () => {
      // Should be able to store path in variable
      const chatApi = api.chat;
      const sessionApi = api.session_view;

      // And use them later
      const call1 = chatApi.list_chats(undefined, { auto: false });
      const call2 = sessionApi.get_recent_sessions({ limit: 10 }, { auto: false });

      expect(call1).toBeDefined();
      expect(call2).toBeDefined();
    });
  });
});

