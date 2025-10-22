/**
 * Database makes use of "logical" store as opposed to an explicit
 * separate IDBObjectStore for each store. This is mainly to avoid
 * issues from upgrade blocking when multiple stores are opened.
 */
const DB_NAME = "otto";
const DB_STORE_NAME = "common";

export type Key = string | number;

export interface Item<T> {
  store: string;
  key: Key;
  value: T;
  timestamp: number; // milliseconds
  ttl?: number; // milliseconds
}

export class Store<T> {
  private _name: string;
  private _db?: IDBDatabase;

  constructor(name: string) {
    this._name = name;
  }

  get name() {
    return this._name;
  }

  private async getDb(): Promise<IDBDatabase> {
    if (this._db) return this._db;
    this._db = await openDb();
    return this._db;
  }

  private async getStore(mode: IDBTransactionMode): Promise<IDBObjectStore> {
    const db = await this.getDb();
    const trx = db.transaction(DB_STORE_NAME, mode);
    return trx.objectStore(DB_STORE_NAME);
  }

  private makeKey(key: Key): string {
    // "Composite" key cause not actually separate stores
    return `${this.name}:${key}`;
  }

  async get(key: Key): Promise<T | undefined> {
    const store = await this.getStore("readonly");
    const compositeKey = this.makeKey(key);
    const req = store.get(compositeKey);
    return new Promise((res, rej) => {
      req.onsuccess = () => {
        if (!isItem<T>(req.result)) {
          res(undefined);
          return;
        }

        if (
          req.result.ttl &&
          Date.now() - req.result.timestamp > req.result.ttl
        ) {
          res(undefined);
          return;
        }

        res(req.result.value);
      };
      req.onerror = () => rej(req.error);
    });
  }

  async set(key: Key, value: T, ttl?: number): Promise<Key> {
    const store = await this.getStore("readwrite");
    const compositeKey = this.makeKey(key);
    const item: Item<T> = {
      store: this.name,
      key: compositeKey,
      value,
      timestamp: Date.now(),
      ttl: Math.max(ttl ?? 0, 0),
    };
    const req = store.put(item);
    return new Promise((res, rej) => {
      req.onsuccess = () => res(key); // Return original key, not composite
      req.onerror = () => rej(req.error);
    });
  }

  async delete(key: Key): Promise<void> {
    const store = await this.getStore("readwrite");
    const compositeKey = this.makeKey(key);
    const req = store.delete(compositeKey);
    return new Promise((res, rej) => {
      req.onsuccess = () => res();
      req.onerror = () => rej(req.error);
    });
  }

  async clear(): Promise<void> {
    const store = await this.getStore("readwrite");
    const index = store.index("store");
    const range = IDBKeyRange.only(this.name);
    const req = index.openCursor(range);

    return new Promise((res, rej) => {
      req.onsuccess = () => {
        const cursor = req.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        } else {
          res();
        }
      };
      req.onerror = () => rej(req.error);
    });
  }
}

async function openDb(): Promise<IDBDatabase> {
  return new Promise((res, rej) => {
    const openreq = window.indexedDB.open(DB_NAME);

    openreq.onerror = () => rej(openreq.error);

    openreq.onsuccess = () => {
      const db = openreq.result;

      // If store doesn't exist, we need to upgrade
      if (!db.objectStoreNames.contains(DB_STORE_NAME)) {
        const version = db.version;
        db.close();

        // Reopen with incremented version to trigger upgrade
        const upgradereq = window.indexedDB.open(DB_NAME, version + 1);

        upgradereq.onerror = () => rej(upgradereq.error);
        upgradereq.onsuccess = () => res(upgradereq.result);

        upgradereq.onupgradeneeded = (e) => {
          const db = (e.target as IDBOpenDBRequest).result;
          if (!db.objectStoreNames.contains(DB_STORE_NAME)) {
            const store = db.createObjectStore(DB_STORE_NAME, {
              keyPath: "key",
            });
            store.createIndex("store", "store", { unique: false });
          }
        };
      } else {
        res(db);
      }
    };

    openreq.onupgradeneeded = (e) => {
      const db = (e.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(DB_STORE_NAME)) {
        const store = db.createObjectStore(DB_STORE_NAME, { keyPath: "key" });
        store.createIndex("store", "store", { unique: false });
      }
    };
  });
}

function isItem<T>(v: any): v is Item<T> {
  if (typeof v !== "object" || v === null) return false;
  return (
    typeof v.timestamp === "number" &&
    (typeof v.key === "string" || typeof v.key === "number") &&
    (typeof v.ttl === "undefined" || typeof v.ttl === "number") &&
    Object.hasOwn(v, "value")
  );
}
