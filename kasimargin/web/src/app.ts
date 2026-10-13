import type {CashBasis, DataClass, DecisionPayload, DecisionResult, FinancialRequest, Fixture, Money, Theme} from "./types.js";

type Elements = {
  scenario: HTMLSelectElement; model: HTMLSelectElement; "data-class": HTMLSelectElement;
  "scenario-description": HTMLParagraphElement; "quick-fields": HTMLDivElement;
  "request-json": HTMLTextAreaElement; "apply-json": HTMLButtonElement;
  calculate: HTMLButtonElement; save: HTMLButtonElement; download: HTMLButtonElement;
  error: HTMLParagraphElement; "receipt-state": HTMLParagraphElement;
  "result-content": HTMLDivElement; "empty-state": HTMLParagraphElement;
  margin: HTMLElement; headroom: HTMLElement; status: HTMLDivElement;
  "cash-basis": HTMLDListElement; explanation: HTMLParagraphElement; "model-state": HTMLParagraphElement;
};
function $<K extends keyof Elements>(id: K): Elements[K] {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Missing interface element: ${id}`);
  return element as Elements[K];
}
const themeButtons = [...document.querySelectorAll<HTMLButtonElement>("[data-theme-choice]")];
function applyTheme(theme: Theme, remember = false): void {
  document.documentElement.dataset.theme = theme;
  themeButtons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.themeChoice === theme)));
  if (remember) { try { localStorage.setItem("kasimargin-theme", theme); } catch { /* Switching still works. */ } }
}
for (const button of themeButtons) button.addEventListener("click", () => {
  const choice = button.dataset.themeChoice;
  if (choice === "light" || choice === "dark") applyTheme(choice, true);
});
applyTheme(document.documentElement.dataset.theme === "dark" ? "dark" : "light");
let cases: Fixture[] = [], current: FinancialRequest | null = null;
let lastResult: DecisionResult | null = null, lastPayload: DecisionPayload | null = null;
let editorDirty = false, revision = 0;
const fields = [["performance","recorded_sales_cents","Recorded sales"],["performance","attributable_costs_cents","Attributable costs"],["cash_position","verified_cash_cents","Current cash"],["cash_position","minimum_buffer_cents","Protected buffer"],["cash_position","due_liabilities_cents","Unpaid due liabilities"],["cash_position","committed_spend_cents","Other committed spending"]] as const;
function message(error: unknown): string { return error instanceof Error ? error.message : "The local request failed."; }
async function json<T>(response: Response): Promise<T> {
  const value: unknown = await response.json();
  if (!response.ok) {
    const detail = typeof value === "object" && value !== null && "error" in value && typeof value.error === "string" ? value.error : "The local request failed.";
    throw new Error(detail);
  }
  // Types document successful server responses. The Python runtime gate validates financial data.
  return value as T;
}
function amount(cents: Money): string {
  if (cents === null) return "Unknown";
  if (!Number.isSafeInteger(cents)) return "See exact cents in JSON";
  const sign = cents < 0 ? "−" : "", value = Math.abs(cents);
  return `${sign}R${Math.floor(value / 100).toLocaleString("en-ZA")}.${String(value % 100).padStart(2,"0")}`;
}
function decimal(cents: Money): string {
  if (cents === null) return "";
  if (!Number.isSafeInteger(cents)) throw new Error("This value exceeds the browser’s exact input range. Use the Python CLI.");
  return `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2,"0")}`;
}
function readMoney(text: string): Money {
  if (!text.trim()) return null;
  if (!/^\d+(\.\d{1,2})?$/.test(text)) throw new Error("Use a non-negative rand amount with at most two cents digits.");
  const [whole, fraction = ""] = text.split(".");
  const cents = BigInt(whole) * 100n + BigInt(fraction.padEnd(2,"0"));
  if (cents > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error("Amount exceeds this browser demo’s exact range.");
  return Number(cents);
}
function invalidate(): void {
  revision += 1; lastResult = lastPayload = null;
  $("result-content").hidden = true; $("empty-state").hidden = false; $("receipt-state").textContent = "";
}
function syncEditor(): void { $("request-json").value = JSON.stringify(current,null,2); editorDirty = false; }
function showFields(): void {
  if (!current) return;
  $("quick-fields").replaceChildren();
  for (const [group,key,label] of fields) {
    const record = current[group] as unknown as Record<string, unknown>;
    if (!Object.hasOwn(record,key)) continue;
    const value = record[key];
    if (value !== null && typeof value !== "number") throw new Error("Money fields must contain integer cents or null.");
    const wrapper = document.createElement("div"), caption = document.createElement("label"), input = document.createElement("input");
    input.id = key; input.inputMode = "decimal"; input.placeholder = "Unknown"; input.value = decimal(value);
    caption.htmlFor = key; caption.textContent = `${label} · R`;
    input.addEventListener("input", () => {
      invalidate();
      try { record[key] = readMoney(input.value); input.setCustomValidity(""); $("error").textContent = ""; syncEditor(); }
      catch (error) { input.setCustomValidity(message(error)); $("error").textContent = message(error); }
    });
    wrapper.append(caption,input); $("quick-fields").append(wrapper);
  }
}
function choose(): void {
  const item = cases[Number($("scenario").value)];
  if (!item) return;
  current = structuredClone(item.input); $("data-class").value = "SYNTHETIC";
  $("scenario-description").textContent = `${item.scenario}. Example data only.`;
  $("error").textContent = ""; invalidate(); showFields(); syncEditor();
}
async function run(saveReceipt = false): Promise<void> {
  $("error").textContent = "";
  if (editorDirty) { $("error").textContent = "Apply the edited record before calculating."; return; }
  if (!current || ![...$("quick-fields").querySelectorAll<HTMLInputElement>("input")].every(input => input.reportValidity())) return;
  if (saveReceipt && (!lastPayload || !lastResult)) return;
  const payload: DecisionPayload = {input: structuredClone(current), model: $("model").value || null, save_receipt:false, data_class: $("data-class").value as DataClass};
  const requestRevision = revision;
  const controls = [...document.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement | HTMLButtonElement>("input,select,textarea,button")];
  controls.forEach(control => control.disabled = true);
  try {
    if (saveReceipt && lastPayload && lastResult) {
      const response = await fetch("/api/receipt", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({input:lastPayload.input,result:lastResult,data_class:lastPayload.data_class})});
      const saved = await json<{receipt_filename:string}>(response);
      if (revision === requestRevision) $("receipt-state").textContent = `Saved to local-data/decisions/${saved.receipt_filename}. Human review is not yet recorded.`;
      return;
    }
    const response = await fetch("/api/decision", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
    const result = await json<DecisionResult>(response);
    if (revision !== requestRevision) return;
    lastResult = result; lastPayload = payload;
    $("result-content").hidden = false; $("empty-state").hidden = true;
    $("margin").textContent = amount(result.summary.operating_margin_cents); $("headroom").textContent = amount(result.summary.cash_headroom_cents);
    const hold = result.summary.status !== "CALCULATED";
    $("status").className = `status${hold ? " hold" : ""}`;
    $("status").textContent = hold ? "Hold the decision. Missing or disputed records prevent a headroom calculation." : `Calculated from confirmed inputs through ${result.summary.horizon_end}.`;
    $("cash-basis").replaceChildren();
    const basisLabels: ReadonlyArray<readonly [keyof Pick<CashBasis,"verified_cash_cents" | "due_liabilities_cents" | "committed_spend_cents" | "minimum_buffer_cents">, string]> = [["verified_cash_cents","Confirmed current cash"],["due_liabilities_cents","Less: unpaid due liabilities"],["committed_spend_cents","Less: other committed spending"],["minimum_buffer_cents","Less: protected buffer"]];
    for (const [key,label] of basisLabels) {
      const term = document.createElement("dt"), definition = document.createElement("dd"); term.textContent = label; definition.textContent = amount(result.summary.cash_basis[key]); $("cash-basis").append(term,definition);
    }
    $("explanation").textContent = result.explanation;
    const inference = result.inference;
    $("model-state").textContent = inference.status === "ADMITTED" ? `Local ${inference.model} selection admitted; figures supplied by the calculation engine. Digest: ${inference.digest}` : inference.status === "NOT_REQUESTED" ? "Deterministic baseline. No model was requested." : `Deterministic fallback: ${inference.reason}. No model output was admitted.`;
    $("receipt-state").textContent = "Not saved. Review the result before saving or exporting.";
  } catch (error) { invalidate(); $("error").textContent = message(error); }
  finally { controls.forEach(control => control.disabled = false); }
}
$("scenario").addEventListener("change",choose);
for (const id of ["model","data-class"] as const) $(id).addEventListener("change",invalidate);
$("request-json").addEventListener("input", () => { editorDirty = true; invalidate(); });
$("apply-json").addEventListener("click", async () => {
  try {
    const response = await fetch("/api/validate", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({raw_json:$("request-json").value})});
    current = await json<FinancialRequest>(response); invalidate(); showFields(); syncEditor(); $("error").textContent = "";
  } catch (error) { $("error").textContent = message(error); }
});
$("calculate").addEventListener("click", () => void run()); $("save").addEventListener("click", () => void run(true));
$("download").addEventListener("click", () => {
  if (!lastResult || !lastPayload) return;
  const blob = new Blob([JSON.stringify({data_class:lastPayload.data_class,input:lastPayload.input,result:lastResult},null,2)],{type:"application/json"});
  const url = URL.createObjectURL(blob), link = document.createElement("a"); link.href = url; link.download = "kasimargin-decision.json"; link.click(); URL.revokeObjectURL(url);
});
void fetch("/api/fixtures").then(response => json<Fixture[]>(response)).then(items => {
  cases = items; cases.forEach((item,index) => {const option = document.createElement("option"); option.value = String(index); option.textContent = item.scenario; $("scenario").append(option);}); choose();
}).catch(error => { $("error").textContent = message(error); });
