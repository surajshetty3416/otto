import { deUi, isUi } from "../utils";

export function duration(seconds: number): string {
  if (!seconds || seconds === 0) return "0s";

  // Hours, minutes and seconds
  if (seconds >= 3600) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = (seconds % 60).toFixed(1);
    return `${hours}h ${minutes}m ${remainingSeconds}s`;
  }

  // Minutes and seconds
  if (seconds >= 60) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = (seconds % 60).toFixed(2);
    return `${minutes}m ${remainingSeconds}s`;
  }

  // Seconds with milliseconds as decimal
  if (seconds >= 1) {
    return `${seconds.toFixed(3)}s`;
  }

  // Milliseconds
  if (seconds >= 0.001) {
    return `${Math.round(seconds * 1000_000) / 1000}ms`;
  }

  // Microseconds
  return `${Math.round(seconds * 1000_000_000) / 1000}μs`;
}

export function date(value: string | Date | undefined): string {
  // TODO: If just showing timestring, format time better
  value ??= new Date(1710633600000);

  // Convert string to Date if needed
  const dateObj = typeof value === "string" ? new Date(value) : value;

  // Get current date for comparison
  const now = new Date();

  // Check if date is today
  const isToday =
    dateObj.getDate() === now.getDate() &&
    dateObj.getMonth() === now.getMonth() &&
    dateObj.getFullYear() === now.getFullYear();

  // Check if date is in the same month and year
  const isSameMonthAndYear =
    dateObj.getMonth() === now.getMonth() &&
    dateObj.getFullYear() === now.getFullYear();

  // Check if date is in the same year
  const isSameYear = dateObj.getFullYear() === now.getFullYear();

  // Format time (hours and minutes)
  const hours = dateObj.getHours().toString().padStart(2, "0");
  const minutes = dateObj.getMinutes().toString().padStart(2, "0");
  const seconds = dateObj.getSeconds().toString().padStart(2, "0");
  const timeStr = `${hours}:${minutes}:${seconds}`;

  // If it's today, just return the time
  if (isToday) {
    const milliseconds = dateObj.getMilliseconds().toString().padStart(3, "0");
    return `Today, ${timeStr}.${milliseconds}`;
  }

  // Format date parts
  const day = dateObj.getDate();
  const month = dateObj.toLocaleString("default", { month: "short" });
  const year = dateObj.getFullYear();

  // If same month and year, show day and time
  if (isSameMonthAndYear || isSameYear) {
    return `${month} ${day}, ${timeStr}`;
  }

  // Otherwise show full date and time
  return `${month} ${day} ${year}, ${timeStr}`;
}

export function json(value: unknown): string {
  if (typeof value !== "string") {
    try {
      return json(JSON.stringify(value));
    } catch {
      // TODO: handle non JSON value
      return String(value);
    }
  }

  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return String(value);
  }
}

/**
 * Parses the reasons string and returns an array of strings.
 * @param reasons - The reasons string to parse.
 * @param defaultReason - The default reason to return if the reasons string is not valid or is empty.
 * @returns An array of strings.
 */
export function reasons(reasons?: string, defaultReason?: string): string[] {
  const defaultReasons = defaultReason ? [defaultReason] : [];
  if (!reasons) return defaultReasons;

  const parsed = JSON.parse(reasons);
  if (!Array.isArray(parsed) || parsed.length === 0) return defaultReasons;

  const filtered = parsed.filter((reason) => typeof reason === "string");
  if (filtered.length === 0) return defaultReasons;

  return filtered;
}

export function argType(type: string): string {
  const argTypes: Record<string, string> = {
    str: "String",
    int: "Integer",
    float: "Float",
    bool: "Boolean",
    list: "List",
    dict: "Dictionary",
    unknown: "Unknown",
  };

  return argTypes[type] || "Unknown";
}

export function error(error: unknown): string {
  if (!(error instanceof Error) || !isUi(error.message)) {
    return "Something went wrong";
  }

  return deUi(error.message);
}

export default { duration, date, json, reasons, argType, error };
