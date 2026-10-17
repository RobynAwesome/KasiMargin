import type {Money} from "./types.js";

export function readMoney(text: string): Money {
  if (!text.trim()) return null;
  if (!/^\d+(\.\d{1,2})?$/.test(text)) throw new Error("Use a positive rand amount or zero, with at most two cents digits.");
  const [whole, fraction = ""] = text.split(".");
  const cents = BigInt(whole) * 100n + BigInt(fraction.padEnd(2,"0"));
  if (cents > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error("This amount needs the exact-cents CLI. It is too large for the browser.");
  return Number(cents);
}
