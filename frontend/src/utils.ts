import { unref } from "vue";

import {
  isReactive,
  isRef,
  ref,
  toRef,
  watch,
  type Reactive,
  type Ref,
} from "vue";

/**
 * Compares two objects for deep equality with configurable depth.
 *
 * @param obj1 - First object to compare
 * @param obj2 - Second object to compare
 * @param depth - Maximum depth for recursive comparison (default: 1)
 * @returns Boolean indicating whether the objects are equal
 *
 * @example
 * ```ts
 * // Simple comparison
 * isEqual({a: 1}, {a: 1}); // true
 *
 * // Deep comparison with tracking changes
 * const changes = [];
 * const result = isEqual({a: {b: 1}}, {a: {b: 2}}, 2, changes);
 * // result: false
 * // changes: [{ key: 'b', obj1: 1, obj2: 2 }]
 * ```
 */
export function isEqual(obj1: any, obj2: any, depth: number = 1): boolean {
  if (obj1 === obj2) return true;
  if (!obj1 || !obj2) return false;

  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);

  if (keys1.length !== keys2.length) return false;

  for (const key of keys1) {
    if (!Object.prototype.hasOwnProperty.call(obj2, key)) {
      return false;
    }

    // If we've reached max depth, just compare equality
    if (depth < 1 && obj1[key] !== obj2[key]) {
      return false;
    }

    // Direct comparison for primitive values
    if (
      (typeof obj1[key] !== "object" || obj1[key] === null) &&
      obj1[key] !== obj2[key]
    ) {
      return false;
    }

    // Recursively check with reduced depth
    if (!isEqual(obj1[key], obj2[key], depth - 1)) {
      return false;
    }
  }

  return true;
}

/**
 * A composable that tracks whether a reactive object has been modified from its initial state.
 *
 * @param value - The reactive object to track for changes. Can be a Ref, Reactive.
 * @returns An object containing:
 *   - isDirty: A ref boolean indicating if the value has changed from its initial state
 *   - update: A function to reset the initial state to the current value
 *
 * @example
 * ```ts
 * const task = ref({ name: 'Task 1', completed: false });
 * const { isDirty, update } = useDirty(task);
 *
 * // After changes
 * task.value.completed = true;
 * console.log(isDirty.value); // true
 *
 * // After saving
 * update();
 * console.log(isDirty.value); // false
 * ```
 */
export function useDirty<T extends object>(value: Ref<T> | Reactive<T>) {
  if (!isRef(value) && !isReactive(value)) {
    throw new Error("useDirty requires a Ref or Reactive value");
  }

  const valueRef = isRef(value) ? value : toRef(value);
  let initial = JSON.parse(JSON.stringify(unref(valueRef)));
  const isDirty = ref(false);

  // Watch for changes in the value
  watch(
    () => valueRef.value,
    (newValue) => {
      isDirty.value = !isEqual(newValue, initial);
    },
    { deep: true, immediate: true }
  );

  // Function to update the initial value
  function update() {
    initial = JSON.parse(JSON.stringify(unref(valueRef)));
    isDirty.value = false;
  }

  return {
    isDirty,
    update,
  };
}

/**
 * A composable that provides resizable UI elements with persistent storage.
 *
 * @param type - The dimension to resize: "height" or "width"
 * @param initial - The initial size in pixels
 * @param localStorageKey - Key to store the size value in localStorage
 * @param threshold - Minimum size in pixels (default: 100)
 * @param reverse - Whether to reverse the direction of resizing (default: false)
 * @returns An object containing:
 *   - value: A ref with the current size
 *   - resize: Function to start resizing (attach to mousedown event)
 *   - isResizing: A ref boolean indicating if currently resizing
 *   - reset: Function to reset the size to initial value
 *
 * @example
 * ```ts
 * // For a resizable panel width
 * const {
 *   value: panelWidth,
 *   resize: resizePanelWidth,
 *   isResizing: isResizingPanelWidth,
 *   reset: resetPanelWidth
 * } = useResizer("width", 300, "panel-width");
 *
 * // In template
 * // <div :style="{ width: `${panelWidth}px` }">...</div>
 * // <div @mousedown="resizePanelWidth" class="resizer" @dblclick="resetPanelWidth"></div>
 * ```
 */
export function useResizer(
  type: "height" | "width",
  initial: number,
  localStorageKey: string,
  threshold: number = 100,
  reverse: boolean = false
) {
  const value = ref(Number(localStorage.getItem(localStorageKey) ?? initial));
  const isResizing = ref(false);
  const startClient = ref(0);
  const startValue = ref(0);

  function resize(e: MouseEvent) {
    isResizing.value = true;

    if (type === "height") {
      startClient.value = e.clientY;
      startValue.value = value.value;
    } else {
      startClient.value = e.clientX;
      startValue.value = value.value;
    }

    document.addEventListener("mousemove", update);
    document.addEventListener("mouseup", stopResizing);

    // Prevent text selection during drag
    e.preventDefault();
  }

  function update(e: MouseEvent) {
    if (!isResizing.value) return;

    let diff = e.clientY - startClient.value;
    if (type === "width") diff = e.clientX - startClient.value;
    if (reverse) diff = -diff;

    const newValue = startValue.value - diff;
    if (newValue < threshold) return;
    value.value = newValue;
  }

  function stopResizing() {
    isResizing.value = false;
    document.removeEventListener("mousemove", update);
    document.removeEventListener("mouseup", stopResizing);
    localStorage.setItem(localStorageKey, value.value.toString());
  }

  function reset() {
    value.value = initial;
    localStorage.setItem(localStorageKey, initial.toString());
  }

  return {
    value,
    resize,
    isResizing,
    reset,
  };
}

/**
 * Asserts that a condition is truthy, throwing an error with the provided message if it's not.
 * Also logs detailed information about the failed assertion to the console.
 *
 * To be used as a sanity check, not to handle errors.
 *
 * @param condition - The condition to check
 * @param message - Error message to display if the assertion fails
 * @throws Error to stop execution
 */
export function assert(condition: unknown, message: string): asserts condition {
  if (condition) return;

  console.groupCollapsed(`%cAssertion Failed [${message}]`, "color: red");
  console.log("message", message);
  console.log("condition", condition);
  console.groupEnd();

  throw new Error(message);
}

export function ui(str: string): string {
  return `<user>${str.trim()}</user>`;
}

export function isUi(str: string): boolean {
  return str.startsWith("<user>") && str.endsWith("</user>");
}

export function deUi(str: string): string {
  return str.replace("<user>", "").replace("</user>", "");
}