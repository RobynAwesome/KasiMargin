import type {CashBasis, DataClass, DecisionPayload, DecisionResult, FinancialRequest, Fixture, Money, Theme} from "./types.js";
import {readMoney} from "./money.js";
import {transactionDraft, transactionLabels, ownDay, southAfricaInput, fromSouthAfricaInput} from "./transactions.js";

type Elements = {
  scenario: HTMLSelectElement; model: HTMLSelectElement; "data-class": HTMLSelectElement;
  "scenario-description": HTMLParagraphElement; "quick-fields": HTMLDivElement;
  "request-json": HTMLTextAreaElement; "apply-json": HTMLButtonElement;
  calculate: HTMLButtonElement; save: HTMLButtonElement; download: HTMLButtonElement;
  error: HTMLParagraphElement; "receipt-state": HTMLParagraphElement;
  "result-content": HTMLDivElement; "empty-state": HTMLParagraphElement;
  margin: HTMLElement; headroom: HTMLElement; status: HTMLDivElement;
  "cash-basis": HTMLDListElement; explanation: HTMLParagraphElement; "model-state": HTMLParagraphElement;
  "record-review": HTMLDetailsElement; "record-snapshot": HTMLInputElement; "record-horizon": HTMLInputElement;
  "cash-confirmed": HTMLInputElement; "performance-confirmed": HTMLInputElement;
  "transaction-form": HTMLFormElement; "transaction-kind": HTMLSelectElement; "transaction-amount": HTMLInputElement;
  "transaction-reference": HTMLInputElement; "transaction-note": HTMLInputElement; "transaction-time": HTMLInputElement;
  "transaction-confirmed": HTMLInputElement; "clear-transaction": HTMLButtonElement;
  "transaction-list": HTMLUListElement; "transaction-count": HTMLParagraphElement; "transaction-feedback": HTMLParagraphElement;
  "working-state": HTMLParagraphElement; "next-check": HTMLParagraphElement; "check-source": HTMLParagraphElement;
  "context-state": HTMLParagraphElement; "model-detail": HTMLParagraphElement;
  "start-example": HTMLButtonElement; "start-own": HTMLButtonElement;
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
let editorDirty = false, transactionDirty = false, revision = 0;
const fields = [["performance","recorded_sales_cents","Sales for this period", "Include sales on credit. Keep money collected for older sales separate."],["performance","attributable_costs_cents","Cost of those sales", "Costs matched to the same sales period, even if already paid."],["cash_position","verified_cash_cents","Cash available now", "Count the business money available now. Do not add money customers still owe."],["cash_position","minimum_buffer_cents","Money to keep aside", "Your chosen cash reserve. Leave blank if you have not decided."],["cash_position","due_liabilities_cents","Bills still to pay", "Unpaid amounts due by your plan-through time. Enter 0 only after checking there are none."],["cash_position","committed_spend_cents","Other money promised", "Other commitments for this period. Keep these separate from the bills above."]] as const;
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
let sessionToken: string | null = null;
async function post(path: string, value: unknown): Promise<Response> {
  if (!sessionToken) sessionToken = (await json<{token:string}>(await fetch("/api/session"))).token;
  const response = await fetch(path, {method:"POST", headers:{"Content-Type":"application/json", "X-KasiMargin-Session":sessionToken}, body:JSON.stringify(value)});
  if (response.status === 403) sessionToken = null;
  return response;
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
function invalidate(): void {
  revision += 1; lastResult = lastPayload = null;
  $("result-content").hidden = true; $("empty-state").hidden = false; $("receipt-state").textContent = "";
}
function syncEditor(): void { $("request-json").value = JSON.stringify(current,null,2); editorDirty = false; }
function showFields(): void {
  if (!current) return;
  $("quick-fields").replaceChildren();
  for (const [group,key,label,help] of fields) {
    const record = current[group] as unknown as Record<string, unknown>;
    if (!Object.hasOwn(record,key)) continue;
    const value = record[key];
    if (value !== null && typeof value !== "number") throw new Error("Money fields must contain integer cents or null.");
    const wrapper = document.createElement("div"), caption = document.createElement("label"), input = document.createElement("input");
    input.id = key; input.inputMode = "decimal"; input.placeholder = "Unknown"; input.value = decimal(value);
    caption.htmlFor = key; caption.textContent = `${label} · R`;
    const hint = document.createElement("p"); hint.id = `${key}-help`; hint.className = "field-help"; hint.textContent = help;
    input.setAttribute("aria-describedby", hint.id);
    input.addEventListener("input", () => {
      invalidate();
      try {
        record[key] = readMoney(input.value); input.setCustomValidity(""); $("error").textContent = "";
        if ($("data-class").value === "OPERATOR_ATTESTED" && current) {
          if (group === "cash_position") { current.cash_position.basis_confirmed = false; $("cash-confirmed").checked = false; }
          else { current.performance.complete = false; $("performance-confirmed").checked = false; }
        }
        syncEditor();
      }
      catch (error) { input.setCustomValidity(message(error)); $("error").textContent = message(error); }
    });
    wrapper.append(caption,input,hint); $("quick-fields").append(wrapper);
  }
}
function showReview(): void {
  if (!current) return;
  $("record-snapshot").value = southAfricaInput(current.cash_position.snapshot_at);
  $("record-horizon").value = southAfricaInput(current.cash_position.horizon_end);
  $("record-snapshot").setCustomValidity(""); $("record-horizon").setCustomValidity("");
  $("cash-confirmed").checked = current.cash_position.basis_confirmed;
  $("performance-confirmed").checked = current.performance.complete;
}
function clearTransaction(): void {
  $("transaction-form").reset(); transactionDirty = false;
  if (current) $("transaction-time").value = southAfricaInput(current.cash_position.snapshot_at);
}
function showTransactions(): void {
  $("transaction-list").replaceChildren();
  if (!current) return;
  $("transaction-count").textContent = `${current.transactions.length} recorded transaction${current.transactions.length === 1 ? "" : "s"} in this day. Saving a copy is your choice.`;
  for (const row of current.transactions) {
    const item = document.createElement("li"), body = document.createElement("div"), title = document.createElement("strong"), detail = document.createElement("span"), remove = document.createElement("button");
    title.textContent = `${transactionLabels[row.kind]} · ${amount(row.amount_cents)}`;
    detail.textContent = `${row.reference_id} · ${southAfricaInput(row.timestamp).replace("T"," ")} · ${row.is_confirmed ? "Checked" : "Needs confirmation"}`;
    remove.type = "button"; remove.className = "text-button"; remove.textContent = "Remove";
    remove.setAttribute("aria-label", `Remove transaction ${row.reference_id}`);
    remove.addEventListener("click", () => {
      if (!current) return;
      if (transactionDirty) { $("error").textContent = "Add or clear your current entry before removing another record."; return; }
      const draft = structuredClone(current); draft.transactions = draft.transactions.filter(transaction => transaction.id !== row.id);
      void applyTransactions(draft, "Record removed from this draft. Check any linked obligations before deciding.");
    });
    body.append(title,detail); item.append(body,remove); $("transaction-list").append(item);
  }
}
async function applyTransactions(draft: FinancialRequest, feedback: string): Promise<void> {
  if (editorDirty || ![...$("quick-fields").querySelectorAll<HTMLInputElement>("input")].every(input => input.reportValidity())) {
    $("error").textContent = "Apply your full-record edits and check the amounts before changing transactions."; return;
  }
  invalidate();
  const requestRevision = revision;
  const controls = [...document.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement | HTMLButtonElement>("input,select,textarea,button")];
  controls.forEach(control => control.disabled = true);
  try {
    if ($("data-class").value === "OPERATOR_ATTESTED") draft.cash_position.basis_confirmed = false;
    const reviewed = await json<FinancialRequest>(await post("/api/validate", {raw_json:JSON.stringify(draft)}));
    if (revision !== requestRevision) return;
    current = reviewed; showFields(); showReview(); showTransactions(); syncEditor(); clearTransaction();
    $("error").textContent = ""; $("transaction-feedback").textContent = feedback;
  } catch (error) { $("error").textContent = message(error); }
  finally { controls.forEach(control => control.disabled = false); }
}
function choose(): void {
  if ($("scenario").value === "own") {
    current = ownDay(); $("data-class").value = "OPERATOR_ATTESTED"; $("record-review").open = true;
    $("scenario-description").textContent = "Your day, your records. Start with what you know; leave anything uncertain blank.";
  } else {
  const item = cases[Number($("scenario").value)];
  if (!item) return;
  current = structuredClone(item.input); $("data-class").value = "SYNTHETIC";
  $("scenario-description").textContent = `${item.scenario}. Example data only.`;
  }
  $("error").textContent = ""; $("transaction-feedback").textContent = ""; invalidate(); showFields(); showReview(); showTransactions(); syncEditor(); clearTransaction();
}
async function run(saveReceipt = false): Promise<void> {
  $("error").textContent = "";
  if (editorDirty) { $("error").textContent = "Apply the edited record before calculating."; return; }
  if (transactionDirty) { $("error").textContent = "Add your transaction to this day, or clear the entry, before calculating."; return; }
  if (!current || ![...$("quick-fields").querySelectorAll<HTMLInputElement>("input")].every(input => input.reportValidity())) return;
  if (![$("record-snapshot"), $("record-horizon")].every(input => input.reportValidity())) return;
  if (saveReceipt && (!lastPayload || !lastResult)) return;
  if (!saveReceipt && $("data-class").value === "OPERATOR_ATTESTED") {
    current.cash_position.decision_at = new Date().toISOString(); syncEditor();
  }
  const payload: DecisionPayload = {input: structuredClone(current), model: $("model").value || null, save_receipt:false, data_class: $("data-class").value as DataClass};
  const requestRevision = revision;
  const controls = [...document.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement | HTMLButtonElement>("input,select,textarea,button")];
  controls.forEach(control => control.disabled = true);
  $("working-state").textContent = saveReceipt ? "Saving your local copy…" : payload.model ? "Checking your records and asking the local assistant. This may take a moment…" : "Checking your recorded position…";
  try {
    if (saveReceipt && lastPayload && lastResult) {
      const response = await post("/api/receipt", {input:lastPayload.input,result:lastResult,data_class:lastPayload.data_class});
      const saved = await json<{receipt_filename:string}>(response);
      if (revision === requestRevision) $("receipt-state").textContent = `Saved to local-data/decisions/${saved.receipt_filename}. Human review is not yet recorded.`;
      return;
    }
    const response = await post("/api/decision", payload);
    const result = await json<DecisionResult>(response);
    if (revision !== requestRevision) return;
    lastResult = result; lastPayload = payload;
    $("result-content").hidden = false; $("empty-state").hidden = true;
    $("margin").textContent = amount(result.summary.operating_margin_cents); $("headroom").textContent = amount(result.summary.cash_headroom_cents);
    const hold = result.summary.status !== "CALCULATED";
    $("status").className = `status${hold ? " hold" : ""}`;
    const through = new Intl.DateTimeFormat("en-ZA", {timeZone:"Africa/Johannesburg",dateStyle:"medium",timeStyle:"short"}).format(new Date(result.summary.horizon_end));
    $("status").textContent = hold ? "Let's check a few things. Cash headroom is still unknown (HOLD)." : `Calculated from confirmed inputs through ${through}, South African time.`;
    $("next-check").textContent = hold ? "Let's check the uncertain records first. Your cash headroom will stay unknown until they are resolved." : result.summary.cash_headroom_cents === 0 ? "The recorded cash is already needed for obligations and your buffer. Review those commitments before considering a new purchase." : "Review this cash headroom alongside your recorded obligations and buffer before deciding what to do next.";
    $("cash-basis").replaceChildren();
    const basisLabels: ReadonlyArray<readonly [keyof Pick<CashBasis,"verified_cash_cents" | "due_liabilities_cents" | "committed_spend_cents" | "minimum_buffer_cents">, string]> = [["verified_cash_cents","Confirmed current cash"],["due_liabilities_cents","Less: unpaid due liabilities"],["committed_spend_cents","Less: other committed spending"],["minimum_buffer_cents","Less: protected buffer"]];
    for (const [key,label] of basisLabels) {
      const term = document.createElement("dt"), definition = document.createElement("dd"); term.textContent = label; definition.textContent = amount(result.summary.cash_basis[key]); $("cash-basis").append(term,definition);
    }
    $("explanation").textContent = result.explanation;
    const inference = result.inference;
    $("model-state").textContent = inference.status === "ADMITTED" ? "The local assistant selected these explanation points. The calculation supplied every amount." : inference.status === "NOT_REQUESTED" ? "Calculated explanation. No AI assistant was requested." : "The assistant's answer was unavailable or did not pass the checks. You are seeing the calculated explanation instead.";
    $("model-detail").textContent = inference.status === "ADMITTED" ? `Model: ${inference.model}. Digest: ${inference.digest}` : inference.status === "REJECTED_OR_UNAVAILABLE" ? `Fallback reason: ${inference.reason}` : "Explanation source: deterministic template.";
    $("check-source").textContent = payload.data_class === "SYNTHETIC" ? "Source: a synthetic example. These are not real business records." : "Source: records you supplied. Cash and obligation confirmation are checked separately; no bank balance was independently verified.";
    const contextResult = result.context_check;
    $("context-state").textContent = contextResult?.status === "CONNECTED_READ_ONLY" ? "Context service: connected for a read-only entry check. This is separate from the financial calculation and your approval." : "Context service: not available for this check. The financial calculation remains based on your supplied records; no context-runtime approval is claimed.";
    $("receipt-state").textContent = "Not saved. Review the result before saving or exporting.";
  } catch (error) { invalidate(); $("error").textContent = message(error); }
  finally { controls.forEach(control => control.disabled = false); $("working-state").textContent = ""; }
}
$("scenario").addEventListener("change",choose);
for (const [id,value] of [["start-example","0"],["start-own","own"]] as const) $(id).addEventListener("click", () => {
  if (editorDirty || transactionDirty) { $("error").textContent = "Add or clear your transaction, and apply any full-record edits, before switching days."; $("error").scrollIntoView({block:"center"}); return; }
  $("scenario").value = value; choose(); $("scenario").focus(); $("scenario").scrollIntoView({block:"start"});
});
for (const id of ["model","data-class"] as const) $(id).addEventListener("change",invalidate);
$("request-json").addEventListener("input", () => { editorDirty = true; invalidate(); });
$("apply-json").addEventListener("click", async () => {
  try {
    const response = await post("/api/validate", {raw_json:$("request-json").value});
    current = await json<FinancialRequest>(response); invalidate(); showFields(); showReview(); showTransactions(); syncEditor(); clearTransaction(); $("error").textContent = "";
  } catch (error) { $("error").textContent = message(error); }
});
$("transaction-form").addEventListener("input", () => { transactionDirty = true; invalidate(); });
$("transaction-form").addEventListener("submit", event => {
  event.preventDefault();
  if (!current) return;
  try {
    const row = transactionDraft({id:`transaction-${crypto.randomUUID()}`,kind:$("transaction-kind").value,amount:$("transaction-amount").value,
      reference:$("transaction-reference").value,when:$("transaction-time").value,note:$("transaction-note").value,confirmed:$("transaction-confirmed").checked});
    const draft = structuredClone(current); draft.transactions.push(row);
    void applyTransactions(draft, "Added to this day's draft. Your reviewed sales, costs and cash count have not been changed automatically.");
  } catch (error) { $("error").textContent = message(error); }
});
$("clear-transaction").addEventListener("click", () => { clearTransaction(); invalidate(); $("transaction-feedback").textContent = "Entry cleared. Your recorded transactions are unchanged."; $("error").textContent = ""; });
for (const id of ["record-snapshot","record-horizon"] as const) $(id).addEventListener("input", () => {
  if (!current) return;
  invalidate();
  try {
    current.cash_position[id === "record-snapshot" ? "snapshot_at" : "horizon_end"] = fromSouthAfricaInput($(id).value);
    current.cash_position.basis_confirmed = false; $("cash-confirmed").checked = false; $(id).setCustomValidity(""); syncEditor(); $("error").textContent = "";
  } catch (error) { $(id).setCustomValidity(message(error)); $("error").textContent = message(error); }
});
$("cash-confirmed").addEventListener("change", () => {
  if (!current) return;
  current.cash_position.basis_confirmed = $("cash-confirmed").checked;
  if ("obligations_complete" in current.cash_position) current.cash_position.obligations_complete = $("cash-confirmed").checked;
  if ($("cash-confirmed").checked && !current.cash_position.evidence_refs.length) current.cash_position.evidence_refs = ["operator:local-cash-and-obligation-review"];
  invalidate(); syncEditor();
});
$("performance-confirmed").addEventListener("change", () => { if (current) { current.performance.complete = $("performance-confirmed").checked; invalidate(); syncEditor(); } });
$("calculate").addEventListener("click", () => void run()); $("save").addEventListener("click", () => void run(true));
$("download").addEventListener("click", () => {
  if (!lastResult || !lastPayload) return;
  const blob = new Blob([JSON.stringify({data_class:lastPayload.data_class,input:lastPayload.input,result:lastResult},null,2)],{type:"application/json"});
  const url = URL.createObjectURL(blob), link = document.createElement("a"); link.href = url; link.download = "kasimargin-decision.json"; link.click(); URL.revokeObjectURL(url);
});
void fetch("/api/fixtures").then(response => json<Fixture[]>(response)).then(items => {
  cases = items; cases.forEach((item,index) => {const option = document.createElement("option"); option.value = String(index); option.textContent = item.scenario; $("scenario").append(option);});
  const own = document.createElement("option"); own.value = "own"; own.textContent = "My own day · start with blank records"; $("scenario").prepend(own); $("scenario").value = "0"; choose();
}).catch(error => { $("error").textContent = message(error); });
