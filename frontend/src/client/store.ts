export const db = { opendb };

export type Key = string | number;

export interface Item<T> {
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

  private async getdb(): Promise<IDBDatabase> {
    if (this._db) return this._db;
    this._db = await opendb(this.name);
    return this._db;
  }

  private async getstore(mode: IDBTransactionMode): Promise<IDBObjectStore> {
    const db = await this.getdb();
    const trx = db.transaction(this.name, mode);
    return trx.objectStore(this.name);
  }

  async get(key: Key): Promise<T | undefined> {
    const store = await this.getstore("readonly");
    const req = store.get(key);
    return new Promise((res, rej) => {
      req.onsuccess = () => {
        if (!isItem(req.result)) res(undefined);

        if (
          req.result.ttl &&
          Date.now() - req.result.timestamp > req.result.ttl
        ) {
          res(undefined);
        }

        res(req.result.value);
      };
      req.onerror = () => rej(req.error);
    });
  }

  async set(key: Key, value: T, ttl?: number): Promise<Key> {
    const store = await this.getstore("readwrite");
    const item: Item<T> = {
      key: key,
      value,
      timestamp: Date.now(),
      ttl: Math.max(ttl ?? 0, 0),
    };
    const req = store.put(item);
    return new Promise((res, rej) => {
      req.onsuccess = () => res(req.result as Key);
      req.onerror = () => rej(req.error);
    });
  }

  async delete(key: Key): Promise<void> {
    const store = await this.getstore("readwrite");
    const req = store.delete(key);
    return new Promise((res, rej) => {
      req.onsuccess = () => res(req.result);
      req.onerror = () => rej(req.error);
    });
  }

  async clear(): Promise<void> {
    const store = await this.getstore("readwrite");
    const req = store.clear();
    return new Promise((res, rej) => {
      req.onsuccess = () => res(req.result);
      req.onerror = () => rej(req.error);
    });
  }
}

async function opendb(name: string): Promise<IDBDatabase> {
  const openreq = window.indexedDB.open("otto", 1);
  return new Promise((res, rej) => {
    openreq.onerror = () => rej(openreq.error);
    openreq.onsuccess = () => res(openreq.result);
    openreq.onupgradeneeded = (e) => {
      // @ts-ignore
      const db: IDBDatabase = e.target.result;
      db.createObjectStore(name, { keyPath: "key" });
    };
  });
}

function isItem<T>(v: any): v is Item<T> {
  if (typeof v !== "object" || v === null) return false;
  return (
    typeof v.timestamp === "number" &&
    typeof v.key === "string" &&
    (typeof v.ttl === "undefined" || typeof v.ttl === "number") &&
    Object.hasOwn(v, "value")
  );
}
