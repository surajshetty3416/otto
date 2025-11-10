import { markRaw, onUnmounted, reactive, type Reactive } from "vue";
import { assert, isMacOS } from "./utils";

type Action = keyof typeof DEFAULT_SHORTCUTS;
type Callback = (e: KeyboardEvent) => void;
type Shortcuts = Record<Action, string[]>;

const DEFAULT_SHORTCUTS = {
  "new-chat": [isMacOS() ? "meta+shift+o" : "ctrl+shift+o"],
};

function getShorcuts(): Shortcuts {
  return DEFAULT_SHORTCUTS;
}

class Manager {
  current: Reactive<Set<string>>;
  private callbacks: Map<Action, Callback[]>;
  private actions: Map<string, Action[]>;
  private last: string;

  constructor() {
    this.current = reactive(new Set());
    this.callbacks = new Map();
    this.actions = new Map();
    this.last = "";
    this.addlisteners();
    onUnmounted(() => this.removelisteners());
    return markRaw(this);
  }

  private addlisteners() {
    console.log("addlisteners");
    window.addEventListener("keydown", this.keydown.bind(this));
    window.addEventListener("keyup", this.keyup.bind(this));
  }

  private removelisteners() {
    window.removeEventListener("keydown", this.keydown.bind(this));
    window.removeEventListener("keyup", this.keyup.bind(this));
  }

  private keydown(e: KeyboardEvent) {
    this.current.add(e.key.toLowerCase());
    const key = getBind(this.current);
    for (const action of this.actions.get(key) ?? []) {
      for (const callback of this.callbacks.get(action) ?? []) {
        callback(e);
      }
    }
  }

  private keyup(e: KeyboardEvent) {
    this.current.delete(e.key.toLowerCase());
    /*
     * there is a weird bug on macos where keyup is not fired for a key if it's
     * meta is held down, and so the the current does not get cleared this words
     * on the assumption that no one is holding down the same binds for more
     * then 250ms.
     */
    this.last = getBind(this.current);
    setTimeout(this.antilinger.bind(this), 250);
  }

  private antilinger() {
    if (this.last !== getBind(this.current)) return;
    this.current.clear();
  }

  register() {
    for (const [action, shortcuts] of Object.entries(getShorcuts())) {
      for (const s of shortcuts) {
        const bind = s.split("+").sort().join("+");
        if (!this.actions.has(bind)) this.actions.set(bind, []);
        assert(isAction(action), "type check");
        this.actions.get(bind)?.push(action);
      }
    }
  }

  on(action: Action, callback: Callback) {
    if (!this.callbacks.has(action)) this.callbacks.set(action, []);
    this.callbacks.get(action)?.push(callback);
  }

  off(action: Action, callback: Callback) {
    if (!this.callbacks.has(action)) return;
    const callbacks = this.callbacks.get(action);
    this.callbacks.set(action, callbacks?.filter((c) => c !== callback) ?? []);
  }
}

export function getBind(current: Set<string>) {
  return Array.from(current).sort().join("+");
}

export function isAction(key: string): key is Action {
  return key in DEFAULT_SHORTCUTS;
}

export default new Manager();
