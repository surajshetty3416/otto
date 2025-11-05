export type WatcherCallback = (response: Response) => any; // return value ignored

export interface WatcherConfig {
  name?: string;
  status?: number;
}

class Watcher {
  private callbacks: {
    callback: WatcherCallback;
    config?: WatcherConfig;
  }[] = [];

  add(callback: WatcherCallback, config?: WatcherConfig) {
    this.callbacks.push({ callback, config });
  }

  remove(callback: WatcherCallback | string) {
    this.callbacks = this.callbacks.filter((c) => {
      if (typeof callback === "string") {
        return c.config?.name !== callback;
      }

      return c.callback !== callback;
    });
  }

  async run(response: Response) {
    for (const { callback, config } of this.callbacks) {
      if (!this.test(response, config)) continue;
      callback(response);
    }
  }

  private test(response: Response, config?: WatcherConfig) {
    if (!config) return true;

    return response.status === config.status;
  }
}

export const watcher = new Watcher();
