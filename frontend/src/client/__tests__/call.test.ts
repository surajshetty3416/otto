/**
 * Tests for the call() function
 * Tests the low-level HTTP call wrapper
 */
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { call } from "../index";
import {
  afterAllCb,
  beforeAllCb,
  expectCallSuccess,
  waitForCall,
} from "./utils";

beforeAll(beforeAllCb);
afterAll(afterAllCb);

describe("call() function", () => {
  describe("Constructor and Initialization", () => {
    it("should initialize with correct default state", async () => {
      const res = call<undefined, { data: string }>(
        "/api/v2/method/otto.api.ping",
        { method: "POST" },
        { auto: false }
      );

      expect(res.loading).toBe(false);
      expect(res.failed).toBe(false);
      expect(res.data).toBeUndefined();
      expect(res.error).toBeUndefined();
      expect(res.exception).toBeUndefined();
      expect(res.response).toBeUndefined();
      expect(res.promise).toBeUndefined();

      const data = await res;
      expect(data.data).toBe("pong");
    });

    it("should auto-execute when auto is not false", async () => {
      const res = call("/api/v2/method/otto.api.ping", { method: "POST" });

      expect(res.loading).toBe(true);
      expect(res.promise).toBeDefined();

      await waitForCall(res);
      expectCallSuccess(res);
    });

    it("should accept body parameter", async () => {
      const body = { message: "test" };
      const res = call<undefined, { data: string }>(
        "/api/v2/method/otto.api.echo",
        { method: "POST", body },
        { auto: false }
      );

      res.run();
      await waitForCall(res);

      expect(res.data?.data).toBe("test");
    });
  });
});
