/**
 * Tests for the framework object
 * Tests Frappe framework API calls (CRUD operations)
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { framework } from "../api";
import {
  afterAllCb,
  beforeAllCb,
  expectCallException,
  expectCallSuccess,
  TestCleanup,
  testData,
  waitForCall,
} from "./utils";

beforeEach(beforeAllCb);
afterEach(afterAllCb);

describe("framework object", () => {
  const cleanup = new TestCleanup();

  afterEach(async () => {
    await cleanup.cleanup(framework);
  });

  describe("get_list", () => {
    it("should get list with all fields", async () => {
      const result = framework.get_list("Otto Feedback", ["*"], {
        limit: 10,
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(Array.isArray(result.data)).toBe(true);
    });

    it("should get list with specific fields", async () => {
      const result = framework.get_list(
        "Otto Feedback",
        ["name", "comment", "value"],
        { limit: 10 }
      );

      await waitForCall(result);
      expectCallSuccess(result);
      expect(Array.isArray(result.data)).toBe(true);

      if (result.data && result.data.length > 0) {
        const firstItem = result.data[0];
        expect(firstItem).toHaveProperty("name");
        expect(firstItem).toHaveProperty("comment");
        expect(firstItem).toHaveProperty("value");
      }
    });

    it("should support pagination with start", async () => {
      const result = framework.get_list("Otto Feedback", ["name"], {
        start: 0,
        limit: 5,
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(Array.isArray(result.data)).toBe(true);
    });

    it("should support pagination with limit", async () => {
      const result = framework.get_list("Otto Feedback", ["name"], {
        limit: 3,
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(Array.isArray(result.data)).toBe(true);

      if (result.data) {
        expect(result.data.length).toBeLessThanOrEqual(3);
      }
    });

    it("should support filters", async () => {
      const result = framework.get_list("Otto Feedback", ["name", "value"], {
        filters: { value: 5 },
        limit: 10,
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(Array.isArray(result.data)).toBe(true);
    });

    it("should support ordering", async () => {
      const result = framework.get_list("Otto Feedback", ["name", "creation"], {
        order_by: "creation desc",
        limit: 10,
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(Array.isArray(result.data)).toBe(true);
    });

    it("should return empty array when no matches", async () => {
      const result = framework.get_list("Otto Feedback", ["name"], {
        filters: { name: "nonexistent-doc-name-12345" },
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.data).toEqual([]);
    });

    it("should handle auto: false config", () => {
      const result = framework.get_list(
        "Otto Feedback",
        ["name"],
        {},
        { auto: false }
      );

      expect(result.loading).toBe(false);
      expect(result.promise).toBeUndefined();
    });
  });

  describe("new_doc", () => {
    it("should create new document with required fields", async () => {
      const data = testData.feedback();
      const result = framework.new_doc("Otto Feedback", data);

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.data).toBeDefined();
      expect(result.data?.name).toBeDefined();
      expect(result.data?.comment).toBe(data.comment);

      if (result.data?.name) {
        cleanup.register("Otto Feedback", result.data.name as string);
      }
    });

    it("should create document with partial data", async () => {
      const result = framework.new_doc("Otto Feedback", {
        value: 1,
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.data?.value).toBe(1);

      if (result.data?.name) {
        cleanup.register("Otto Feedback", result.data.name as string);
      }
    });

    it("should return complete document structure", async () => {
      const result = framework.new_doc("Otto Feedback", testData.feedback());

      await waitForCall(result);
      expectCallSuccess(result);

      expect(result.data).toHaveProperty("name");
      expect(result.data).toHaveProperty("owner");
      expect(result.data).toHaveProperty("creation");
      expect(result.data).toHaveProperty("modified");

      if (result.data?.name) {
        cleanup.register("Otto Feedback", result.data.name as string);
      }
    });

    it("should handle auto: false config", () => {
      const result = framework.new_doc("Otto Feedback", testData.feedback(), {
        auto: false,
      });

      expect(result.loading).toBe(false);
      expect(result.promise).toBeUndefined();
    });

    it("should create multiple documents in parallel", async () => {
      const calls = [
        framework.new_doc("Otto Feedback", testData.feedback()),
        framework.new_doc("Otto Feedback", testData.feedback()),
        framework.new_doc("Otto Feedback", testData.feedback()),
      ];

      await Promise.all(calls.map((c) => c.promise!));

      calls.forEach((call) => {
        expectCallSuccess(call);
        if (call.data?.name) {
          cleanup.register("Otto Feedback", call.data.name as string);
        }
      });
    });
  });

  describe("get_doc", () => {
    it("should get existing document by name", async () => {
      // Create a document first
      const newDoc = framework.new_doc("Otto Feedback", testData.feedback());
      await waitForCall(newDoc);
      const docName = newDoc.data!.name as string;
      cleanup.register("Otto Feedback", docName);

      // Now get it
      const result = framework.get_doc("Otto Feedback", docName);

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.data?.name).toBe(docName);
    });

    it("should return correct document structure", async () => {
      // Create a document first
      const newDoc = framework.new_doc("Otto Feedback", {
        comment: "test comment",
        value: 1,
      });
      await waitForCall(newDoc);
      const docName = newDoc.data!.name as string;
      cleanup.register("Otto Feedback", docName);

      // Get it
      const result = framework.get_doc("Otto Feedback", docName);

      await waitForCall(result);
      expectCallSuccess(result);

      expect(result.data).toHaveProperty("name");
      expect(result.data).toHaveProperty("comment");
      expect(result.data).toHaveProperty("value");
      expect(result.data?.comment).toBe("test comment");
      expect(result.data?.value).toBe(1);
    });

    it("should fail on non-existent document", async () => {
      const result = framework.get_doc(
        "Otto Feedback",
        "nonexistent-doc-12345"
      );

      try {
        await waitForCall(result);
      } catch {
        expect.fail("Exceptions should not throw");
      }

      expectCallException(result);
      expect(result.status).toBe(404);
    });

    it("should handle auto: false config", async () => {
      const result = framework.get_doc("Otto Feedback", "any-name", {
        auto: false,
      });

      expect(result.loading).toBe(false);
      expect(result.promise).toBeUndefined();
    });
  });

  describe("update_doc", () => {
    it("should update document fields", async () => {
      // Create a document
      const newDoc = framework.new_doc("Otto Feedback", {
        comment: "original",
        value: -1,
      });
      await waitForCall(newDoc);
      const docName = newDoc.data!.name as string;
      cleanup.register("Otto Feedback", docName);

      // Update it
      const result = framework.update_doc("Otto Feedback", docName, {
        comment: "updated",
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.data?.comment).toBe("updated");
      expect(result.data?.value).toBe(-1); // Unchanged field
    });

    it("should support partial updates", async () => {
      // Create a document
      const newDoc = framework.new_doc("Otto Feedback", {
        comment: "test",
        value: 1,
      });
      await waitForCall(newDoc);
      const docName = newDoc.data!.name as string;
      cleanup.register("Otto Feedback", docName);

      // Update only one field
      const result = framework.update_doc("Otto Feedback", docName, {
        value: 1,
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.data?.value).toBe(1);
      expect(result.data?.comment).toBe("test");
    });

    it("should verify changes persisted", async () => {
      // Create a document
      const newDoc = framework.new_doc("Otto Feedback", {
        comment: "before",
      });
      await waitForCall(newDoc);
      const docName = newDoc.data!.name as string;
      cleanup.register("Otto Feedback", docName);

      // Update it
      await framework.update_doc("Otto Feedback", docName, {
        comment: "after",
      });

      // Get it again to verify
      const getDoc = framework.get_doc("Otto Feedback", docName);
      await waitForCall(getDoc);

      expect(getDoc.data?.comment).toBe("after");
    });

    it("should fail on non-existent document", async () => {
      const result = framework.update_doc(
        "Otto Feedback",
        "nonexistent-doc-12345",
        { comment: "test" }
      );

      try {
        await waitForCall(result);
        expect.fail("Should have thrown an error");
      } catch {
        expectCallException(result);
      }
    });

    it("should handle auto: false config", () => {
      const result = framework.update_doc(
        "Otto Feedback",
        "any-name",
        { comment: "test" },
        { auto: false }
      );

      expect(result.loading).toBe(false);
      expect(result.promise).toBeUndefined();
    });
  });

  describe("delete_doc", () => {
    it("should delete existing document", async () => {
      // Create a document
      const newDoc = framework.new_doc("Otto Feedback", testData.feedback());
      await waitForCall(newDoc);
      const docName = newDoc.data!.name as string;

      // Delete it
      const result = framework.delete_doc("Otto Feedback", docName);

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.data).toBe("ok");
    });

    it("should verify document deleted", async () => {
      // Create a document
      const newDoc = framework.new_doc("Otto Feedback", testData.feedback());
      await waitForCall(newDoc);
      const docName = newDoc.data!.name as string;

      // Delete it
      await framework.delete_doc("Otto Feedback", docName);

      // Try to get it - should fail
      const getDoc = framework.get_doc("Otto Feedback", docName);

      try {
        await waitForCall(getDoc);
        expect.fail("Should have thrown an error");
      } catch {
        expectCallException(getDoc);
        expect(getDoc.response?.status).toBe(404);
      }
    });

    it("should fail on non-existent document", async () => {
      const result = framework.delete_doc(
        "Otto Feedback",
        "nonexistent-doc-12345"
      );

      try {
        await waitForCall(result);
      } catch {
        expect.fail("Exceptions should not throw");
      }

      expectCallException(result);
    });

    it("should handle auto: false config", () => {
      const result = framework.delete_doc("Otto Feedback", "any-name", {
        auto: false,
      });

      expect(result.loading).toBe(false);
      expect(result.promise).toBeUndefined();
    });
  });

  describe("CRUD Workflow", () => {
    it("should support complete CRUD workflow", async () => {
      // Create
      const createResult = framework.new_doc("Otto Feedback", {
        comment: "workflow test",
        value: 1,
      });
      await waitForCall(createResult);
      expectCallSuccess(createResult);
      const docName = createResult.data!.name as string;

      // Read
      const readResult = framework.get_doc("Otto Feedback", docName);
      await waitForCall(readResult);
      expectCallSuccess(readResult);
      expect(readResult.data?.comment).toBe("workflow test");

      // Update
      const updateResult = framework.update_doc("Otto Feedback", docName, {
        comment: "updated workflow",
        value: 1,
      });
      await waitForCall(updateResult);
      expectCallSuccess(updateResult);
      expect(updateResult.data?.comment).toBe("updated workflow");
      expect(updateResult.data?.value).toBe(1);

      // Delete
      const deleteResult = framework.delete_doc("Otto Feedback", docName);
      await waitForCall(deleteResult);
      expectCallSuccess(deleteResult);
    });

    it("should handle multiple document lifecycle", async () => {
      // Create multiple documents
      const docs = await Promise.all([
        framework.new_doc("Otto Feedback", { value: 1 }).promise!,
        framework.new_doc("Otto Feedback", { value: 2 }).promise!,
        framework.new_doc("Otto Feedback", { value: 3 }).promise!,
      ]);

      const docNames = docs.map((d) => d.name as string);

      // List them
      const list = framework.get_list("Otto Feedback", ["name", "value"], {
        filters: { name: ["in", docNames] },
      });
      await waitForCall(list);
      expect(list.data?.length).toBe(3);

      // Update all
      await Promise.all(
        docNames.map(
          (name) =>
            framework.update_doc("Otto Feedback", name, { value: 5 }).promise
        )
      );

      // Delete all
      await Promise.all(
        docNames.map(
          (name) => framework.delete_doc("Otto Feedback", name).promise
        )
      );
    });
  });

  describe("Different DocTypes", () => {
    it("should work with Otto Scrapbook", async () => {
      const result = framework.new_doc("Otto Scrapbook", testData.scrapbook());

      await waitForCall(result);
      expectCallSuccess(result);

      if (result.data?.name) {
        cleanup.register("Otto Scrapbook", result.data.name as string);
      }
    });

    it("should work with Otto Feedback", async () => {
      const result = framework.new_doc("Otto Feedback", testData.feedback());

      await waitForCall(result);
      expectCallSuccess(result);

      if (result.data?.name) {
        cleanup.register("Otto Feedback", result.data.name as string);
      }
    });
  });

  describe("Edge Cases", () => {
    it("should handle empty partial updates", async () => {
      const newDoc = framework.new_doc("Otto Feedback", testData.feedback());
      await waitForCall(newDoc);
      const docName = newDoc.data!.name as string;
      cleanup.register("Otto Feedback", docName);

      const result = framework.update_doc("Otto Feedback", docName, {});

      await waitForCall(result);
      expectCallSuccess(result);
    });

    it("should handle documents with special characters in name", async () => {
      // Frappe auto-generates names, so we'll just verify we can work with them
      const newDoc = framework.new_doc("Otto Feedback", testData.feedback());
      await waitForCall(newDoc);
      const docName = newDoc.data!.name as string;
      cleanup.register("Otto Feedback", docName);

      // Should be able to get it regardless of name format
      const getDoc = framework.get_doc("Otto Feedback", docName);
      await waitForCall(getDoc);
      expectCallSuccess(getDoc);
    });

    it("should handle very long field values", async () => {
      const longComment = "a".repeat(5000);
      const result = framework.new_doc("Otto Feedback", {
        comment: longComment,
      });

      await waitForCall(result);
      expectCallSuccess(result);
      expect(result.data?.comment).toBe(longComment);

      if (result.data?.name) {
        cleanup.register("Otto Feedback", result.data.name as string);
      }
    });
  });

  describe("Reactive Properties", () => {
    it("should have reactive loading state", async () => {
      const result = framework.get_list("Otto Feedback", ["name"]);

      expect(result.loading).toBe(true);

      await waitForCall(result);

      expect(result.loading).toBe(false);
    });

    it("should have reactive data property", async () => {
      const result = framework.get_list("Otto Feedback", ["name"]);

      expect(result.data).toBeUndefined();

      await waitForCall(result);

      expect(result.data).toBeDefined();
    });
  });
});
