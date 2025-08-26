export function useId() {
  return `${new Date().valueOf()}-${Math.random()
    .toString(36)
    .substring(2, 15)}`;
}

export function debounce<T extends (...args: any[]) => void>(
  func: T,
  wait: number,
  immediate?: boolean
): T {
  let timeout: number | undefined;
  // @ts-ignore
  return function (...args: Parameters<T>) {
    // @ts-ignore
    const context = this;
    const later = function () {
      timeout = undefined;
      if (!immediate) func.apply(context, args);
    };
    let callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = window.setTimeout(later, wait);
    if (callNow) func.apply(context, args);
  };
}
