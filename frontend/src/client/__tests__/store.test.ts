/**
 * Tests for the Store class
 * Tests IndexedDB-based client-side storage with TTL support
 *
 * Note: All Store instances share a single IndexedDB object store ("common")
 * and differentiate data using the store name field in each item.
 */
import { describe, expect, it } from "vitest";
import { Store } from "../store";
import { sleep } from "./utils";

describe("Store", () => {
  describe("Basic Operations", () => {
    it("should create a store with a name", () => {
      const store = new Store<string>("test-store");
      expect(store.name).toBe("test-store");
    });

    it("should set and get a value with string key", async () => {
      const store = new Store<string>("test-store");
      await store.set("key1", "value1");
      const value = await store.get("key1");
      expect(value).toBe("value1");
    });

    it("should set and get a value with numeric key", async () => {
      const store = new Store<string>("test-store");
      await store.set(123, "value123");
      const value = await store.get(123);
      expect(value).toBe("value123");
    });

    it("should return undefined for non-existent key", async () => {
      const store = new Store<string>("test-store");
      const value = await store.get("non-existent");
      expect(value).toBeUndefined();
    });

    it("should overwrite existing value", async () => {
      const store = new Store<string>("test-store");
      await store.set("key1", "value1");
      await store.set("key1", "value2");
      const value = await store.get("key1");
      expect(value).toBe("value2");
    });

    it("should delete a value", async () => {
      const store = new Store<string>("test-store");
      await store.set("key1", "value1");
      await store.delete("key1");
      const value = await store.get("key1");
      expect(value).toBeUndefined();
    });

    it("should clear all values", async () => {
      const store = new Store<string>("test-store");
      await store.set("key1", "value1");
      await store.set("key2", "value2");
      await store.set("key3", "value3");
      await store.clear();

      const value1 = await store.get("key1");
      const value2 = await store.get("key2");
      const value3 = await store.get("key3");

      expect(value1).toBeUndefined();
      expect(value2).toBeUndefined();
      expect(value3).toBeUndefined();
    });

    it("should clear only items from target store, not other stores", async () => {
      const store1 = new Store<string>("store-1");
      const store2 = new Store<string>("store-2");

      // Set values in both stores
      await store1.set("key1", "value1-store1");
      await store1.set("key2", "value2-store1");
      await store2.set("key1", "value1-store2");
      await store2.set("key2", "value2-store2");

      // Clear only store1
      await store1.clear();

      // Verify store1 is cleared
      const store1Value1 = await store1.get("key1");
      const store1Value2 = await store1.get("key2");
      expect(store1Value1).toBeUndefined();
      expect(store1Value2).toBeUndefined();

      // Verify store2 is unchanged
      const store2Value1 = await store2.get("key1");
      const store2Value2 = await store2.get("key2");
      expect(store2Value1).toBe("value1-store2");
      expect(store2Value2).toBe("value2-store2");
    });

    it("should isolate same keys across different stores", async () => {
      const userStore = new Store<{ name: string; role: string }>("users");
      const productStore = new Store<{ name: string; price: number }>(
        "products"
      );
      const sessionStore = new Store<{ name: string; token: string }>(
        "sessions"
      );

      // Set same key "item-1" in all three stores with different values
      await userStore.set("item-1", { name: "Alice", role: "admin" });
      await productStore.set("item-1", { name: "Laptop", price: 999.99 });
      await sessionStore.set("item-1", {
        name: "Session-ABC",
        token: "xyz-token-123",
      });

      // Retrieve from each store
      const userValue = await userStore.get("item-1");
      const productValue = await productStore.get("item-1");
      const sessionValue = await sessionStore.get("item-1");

      // Verify each store returns its own value
      expect(userValue).toEqual({ name: "Alice", role: "admin" });
      expect(productValue).toEqual({ name: "Laptop", price: 999.99 });
      expect(sessionValue).toEqual({
        name: "Session-ABC",
        token: "xyz-token-123",
      });

      // Update one store's value
      await productStore.set("item-1", { name: "Desktop", price: 1499.99 });

      // Verify only the updated store changed
      const userValueAfter = await userStore.get("item-1");
      const productValueAfter = await productStore.get("item-1");
      const sessionValueAfter = await sessionStore.get("item-1");

      expect(userValueAfter).toEqual({ name: "Alice", role: "admin" });
      expect(productValueAfter).toEqual({ name: "Desktop", price: 1499.99 });
      expect(sessionValueAfter).toEqual({
        name: "Session-ABC",
        token: "xyz-token-123",
      });

      // Delete from one store
      await sessionStore.delete("item-1");

      // Verify only the deleted store's value is gone
      const userValueFinal = await userStore.get("item-1");
      const productValueFinal = await productStore.get("item-1");
      const sessionValueFinal = await sessionStore.get("item-1");

      expect(userValueFinal).toEqual({ name: "Alice", role: "admin" });
      expect(productValueFinal).toEqual({ name: "Desktop", price: 1499.99 });
      expect(sessionValueFinal).toBeUndefined();
    });
  });

  describe("Data Types", () => {
    it("should store and retrieve strings", async () => {
      const store = new Store<string>("test-store");
      await store.set("key", "hello world");
      const value = await store.get("key");
      expect(value).toBe("hello world");
    });

    it("should store and retrieve numbers", async () => {
      const store = new Store<number>("test-store");
      await store.set("key", 42);
      const value = await store.get("key");
      expect(value).toBe(42);
    });

    it("should store and retrieve objects", async () => {
      interface TestObject {
        name: string;
        age: number;
        active: boolean;
      }
      const store = new Store<TestObject>("test-store");
      const obj = { name: "Alice", age: 30, active: true };
      await store.set("key", obj);
      const value = await store.get("key");
      expect(value).toEqual(obj);
    });

    it("should store and retrieve arrays", async () => {
      const store = new Store<number[]>("test-store");
      const arr = [1, 2, 3, 4, 5];
      await store.set("key", arr);
      const value = await store.get("key");
      expect(value).toEqual(arr);
    });

    it("should store and retrieve complex nested objects", async () => {
      interface ComplexObject {
        id: string;
        metadata: {
          created: Date;
          tags: string[];
          nested: {
            level: number;
            data: Record<string, any>;
          };
        };
        items: Array<{ name: string; value: number }>;
        config: Map<string, string>;
        optional?: string;
      }

      const store = new Store<ComplexObject>("test-store");
      const complexObj: ComplexObject = {
        id: "test-123",
        metadata: {
          created: new Date("2025-01-01"),
          tags: ["tag1", "tag2", "tag3"],
          nested: {
            level: 3,
            data: {
              key1: "value1",
              key2: 42,
              key3: true,
              key4: null,
              key5: [1, 2, 3],
            },
          },
        },
        items: [
          { name: "item1", value: 100 },
          { name: "item2", value: 200 },
          { name: "item3", value: 300 },
        ],
        config: new Map([
          ["setting1", "value1"],
          ["setting2", "value2"],
        ]),
        optional: "optional-value",
      };

      await store.set("complex", complexObj);
      const value = await store.get("complex");

      expect(value).toBeDefined();
      expect(value?.id).toBe("test-123");
      expect(value?.metadata.created).toEqual(new Date("2025-01-01"));
      expect(value?.metadata.tags).toEqual(["tag1", "tag2", "tag3"]);
      expect(value?.metadata.nested.level).toBe(3);
      expect(value?.metadata.nested.data.key1).toBe("value1");
      expect(value?.metadata.nested.data.key2).toBe(42);
      expect(value?.metadata.nested.data.key3).toBe(true);
      expect(value?.metadata.nested.data.key4).toBe(null);
      expect(value?.metadata.nested.data.key5).toEqual([1, 2, 3]);
      expect(value?.items).toHaveLength(3);
      expect(value?.items[0]).toEqual({ name: "item1", value: 100 });
      expect(value?.config).toEqual(complexObj.config);
      expect(value?.optional).toBe("optional-value");
    });

    it("should store and retrieve null values", async () => {
      const store = new Store<string | null>("test-store");
      await store.set("key", null);
      const value = await store.get("key");
      expect(value).toBe(null);
    });

    it("should store and retrieve boolean values", async () => {
      const store = new Store<boolean>("test-store");
      await store.set("key1", true);
      await store.set("key2", false);

      const value1 = await store.get("key1");
      const value2 = await store.get("key2");

      expect(value1).toBe(true);
      expect(value2).toBe(false);
    });
  });

  describe("TTL (Time To Live)", () => {
    it("should respect TTL and return undefined after expiration", async () => {
      const store = new Store<string>("test-store");
      await store.set("key1", "value1", 100); // 100ms TTL

      // Should be available immediately
      const value1 = await store.get("key1");
      expect(value1).toBe("value1");

      // Wait for TTL to expire
      await sleep(150);

      // Should be undefined after TTL
      const value2 = await store.get("key1");
      expect(value2).toBeUndefined();
    });

    it("should not expire items without TTL", async () => {
      const store = new Store<string>("test-store");
      await store.set("key1", "value1"); // No TTL

      await sleep(200);

      const value = await store.get("key1");
      expect(value).toBe("value1");
    });

    it("should handle TTL of 0 as no expiration", async () => {
      const store = new Store<string>("test-store");
      await store.set("key1", "value1", 0);

      await sleep(100);

      const value = await store.get("key1");
      expect(value).toBe("value1");
    });

    it("should handle negative TTL as 0 (no expiration)", async () => {
      const store = new Store<string>("test-store");
      await store.set("key1", "value1", -100);

      await sleep(100);

      const value = await store.get("key1");
      expect(value).toBe("value1");
    });

    it("should update TTL when overwriting value", async () => {
      const store = new Store<string>("test-store");
      await store.set("key1", "value1", 50); // 50ms TTL

      await sleep(30);

      // Overwrite with new TTL
      await store.set("key1", "value2", 200); // 200ms TTL

      await sleep(100); // Total 130ms, should still be valid

      const value = await store.get("key1");
      expect(value).toBe("value2");
    });
  });

  describe("Edge Cases", () => {
    it("should handle empty string as key", async () => {
      const store = new Store<string>("test-store");
      await store.set("", "empty-key-value");
      const value = await store.get("");
      expect(value).toBe("empty-key-value");
    });

    it("should handle empty string as value", async () => {
      const store = new Store<string>("test-store");
      await store.set("key", "");
      const value = await store.get("key");
      expect(value).toBe("");
    });

    it("should handle zero as key", async () => {
      const store = new Store<string>("test-store");
      await store.set(0, "zero-key-value");
      const value = await store.get(0);
      expect(value).toBe("zero-key-value");
    });

    it("should handle special characters in keys", async () => {
      const store = new Store<string>("test-store");
      const specialKey = "key!@#$%^&*()_+-={}[]|\\:;\"'<>?,./";
      await store.set(specialKey, "special-value");
      const value = await store.get(specialKey);
      expect(value).toBe("special-value");
    });

    it("should handle unicode characters", async () => {
      const store = new Store<string>("test-store");
      await store.set("emoji", "🎉🚀😀");
      await store.set("chinese", "你好世界");
      await store.set("arabic", "مرحبا بالعالم");

      expect(await store.get("emoji")).toBe("🎉🚀😀");
      expect(await store.get("chinese")).toBe("你好世界");
      expect(await store.get("arabic")).toBe("مرحبا بالعالم");
    });

    it("should handle very large values", async () => {
      const store = new Store<string>("test-store");
      const largeValue = "x".repeat(1000000); // 1MB string
      await store.set("large", largeValue);
      const value = await store.get("large");
      expect(value).toBe(largeValue);
    });

    it("should delete non-existent key without error", async () => {
      const store = new Store<string>("test-store");
      await expect(store.delete("non-existent")).resolves.toBeUndefined();
    });

    it("should clear empty store without error", async () => {
      const store = new Store<string>("test-store");
      await expect(store.clear()).resolves.toBeUndefined();
    });
  });

  describe("Concurrent Operations", () => {
    it("should handle concurrent reads", async () => {
      const store = new Store<string>("test-store");
      await store.set("key", "value");

      const promises = Array(10)
        .fill(0)
        .map(() => store.get("key"));

      const results = await Promise.all(promises);

      results.forEach((result) => {
        expect(result).toBe("value");
      });
    });

    it("should handle concurrent writes to different keys", async () => {
      const store = new Store<string>("test-store");

      const promises = Array(10)
        .fill(0)
        .map((_, i) => store.set(`key-${i}`, `value-${i}`));

      await Promise.all(promises);

      for (let i = 0; i < 10; i++) {
        const value = await store.get(`key-${i}`);
        expect(value).toBe(`value-${i}`);
      }
    });

    it("should handle concurrent writes to same key", async () => {
      const store = new Store<number>("test-store");

      const promises = Array(10)
        .fill(0)
        .map((_, i) => store.set("counter", i));

      await Promise.all(promises);

      const value = await store.get("counter");
      // One of the values should have been written
      expect(value).toBeGreaterThanOrEqual(0);
      expect(value).toBeLessThan(10);
    });

    it("should handle mixed operations", async () => {
      const store = new Store<string>("test-store");

      // Set initial values
      await store.set("key1", "value1");
      await store.set("key2", "value2");

      const promises = [
        store.get("key1"),
        store.set("key3", "value3"),
        store.get("key2"),
        store.delete("key1"),
        store.set("key4", "value4"),
        store.get("key3"),
      ];

      await Promise.all(promises);

      const value1 = await store.get("key1");
      const value2 = await store.get("key2");
      const value3 = await store.get("key3");
      const value4 = await store.get("key4");

      expect(value1).toBeUndefined(); // deleted
      expect(value2).toBe("value2");
      expect(value3).toBe("value3");
      expect(value4).toBe("value4");
    });
  });
});
