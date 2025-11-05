export class LocalStore<T = unknown> {
  private name_: string;
  get name() {
    return this.name_;
  }

  constructor(name: string) {
    this.name_ = name;
  }

  set(key: keyof T, value: T[keyof T]) {
    localStorage.setItem(this.key(key), JSON.stringify(value));
  }

  get(key: keyof T): T[keyof T] | undefined {
    const value = localStorage.getItem(this.key(key));
    if (typeof value !== "string") return undefined;
    return JSON.parse(value);
  }

  delete(key: keyof T) {
    localStorage.removeItem(this.key(key));
  }

  private key(key: keyof T): string {
    return `${this.name}:${key as string}`;
  }

  clear() {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key?.startsWith(this.name_)) continue;
      localStorage.removeItem(key);
    }
  }
}
