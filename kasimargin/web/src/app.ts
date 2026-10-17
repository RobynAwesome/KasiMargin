import type {CashBasis, DataClass, DecisionPayload, DecisionResult, FinancialRequest, Fixture, Money, Theme} from "./types.js";
import {readMoney} from "./money.js";
import {transactionDraft, transactionLabels, ownDay, southAfricaInput, fromSouthAfricaInput} from "./transactions.js";
import {recordChecks, resultMessage} from "./presentation.js";

type Elements = {
  scenario: HTMLSelectElement; model: HTMLSelectElement; "data-class": HTMLSelectElement;
  "scenario-description": HTMLParagraphElement; "cash-fields": HTMLDivElement; "bills-fields": HTMLDivElement;
  "reserve-fields": HTMLDivElement; "performance-fields": HTMLDivElement;
  "request-json": HTMLTextAreaElement; "apply-json": HTMLButtonElement;
  calculate: HTMLButtonElement; save: HTMLButtonElement; download: HTMLButtonElement;
  error: HTMLParagraphElement; "receipt-state": HTMLParagraphElement;
  "result-content": HTMLDivElement; "empty-state": HTMLParagraphElement;
  margin: HTMLElement; headroom: HTMLElement; status: HTMLDivElement;
  "cash-basis": HTMLDListElement; explanation: HTMLParagraphElement; "model-state": HTMLParagraphElement;
  "record-review": HTMLDivElement; "record-snapshot": HTMLInputElement; "record-horizon": HTMLInputElement;
  "cash-confirmed": HTMLInputElement; "performance-confirmed": HTMLInputElement;
  "transaction-form": HTMLFormElement; "transaction-kind": HTMLSelectElement; "transaction-amount": HTMLInputElement;
  "transaction-reference": HTMLInputElement; "transaction-note": HTMLInputElement; "transaction-time": HTMLInputElement;
  "transaction-confirmed": HTMLInputElement; "clear-transaction": HTMLButtonElement;
  "transaction-list": HTMLUListElement; "transaction-count": HTMLParagraphElement; "transaction-feedback": HTMLParagraphElement;
  "working-state": HTMLParagraphElement; "next-check": HTMLParagraphElement; "check-source": HTMLParagraphElement;
  "context-state": HTMLParagraphElement; "model-detail": HTMLParagraphElement;
  "start-example": HTMLButtonElement; "start-own": HTMLButtonElement;
  welcome: HTMLElement; journey: HTMLElement; "entry-panel": HTMLDivElement; results: HTMLElement;
  "previous-step": HTMLButtonElement; "next-step": HTMLButtonElement; "back-home": HTMLButtonElement;
  "edit-answers": HTMLButtonElement; "count-now": HTMLButtonElement; "review-totals": HTMLDivElement;
  "example-banner": HTMLParagraphElement; "source-badge": HTMLSpanElement; "example-picker": HTMLDetailsElement;
  "record-checks": HTMLUListElement; "margin-card": HTMLElement; "cash-caption": HTMLSpanElement;
  "other-checks": HTMLUListElement; "more-checks": HTMLDetailsElement; "more-checks-label": HTMLElement;
  "resume-check": HTMLButtonElement; "welcome-feedback": HTMLParagraphElement; "replace-draft": HTMLDivElement;
  "replace-confirm": HTMLButtonElement; "replace-cancel": HTMLButtonElement;
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
let step = 0;
let started = false, pendingStart: string | null = null;
const fields = [
  ["performance","recorded_sales_cents","Sales for the period", "Include unpaid sales on credit. Payments for older sales aren’t new sales.","performance-fields"],
  ["performance","attributable_costs_cents","Cost of those sales", "Include the cost of what was sold and the business costs for that same period.","performance-fields"],
  ["cash_position","verified_cash_cents","Business money available now", "Add your counted cash and cleared business balances. Leave blank while you check.","cash-fields"],
  ["cash_position","minimum_buffer_cents","Money to keep aside", "Leave blank if you’re unsure. Enter 0 only if you’ve chosen to keep nothing aside.","reserve-fields"],
  ["cash_position","due_liabilities_cents","Bills still to pay", "For example, supplier bills or rent due before the time above. Leave out bills already paid.","bills-fields"],
  ["cash_position","committed_spend_cents","Other money you’ve promised", "For example, a delivery you’ve agreed to pay for. Don’t include the same money in bills above.","bills-fields"],
] as const;
function moneyInputs(): HTMLInputElement[] { return [...document.querySelectorAll<HTMLInputElement>(".guided-fields input")]; }
function showStep(next: number, focus = true): void {
  step = Math.max(0,Math.min(2,next));
  $("entry-panel").hidden = false; $("results").hidden = true;
  document.querySelectorAll<HTMLElement>("[data-step]").forEach(panel => panel.hidden = Number(panel.dataset.step) !== step);
  document.querySelectorAll<HTMLButtonElement>("[data-go-step]").forEach(button => {
    if (Number(button.dataset.goStep) === step) button.setAttribute("aria-current","step"); else button.removeAttribute("aria-current");
  });
  $("previous-step").hidden = step === 0; $("next-step").hidden = step === 2; $("calculate").hidden = step !== 2;
  $("next-step").textContent = step === 0 ? "Next: payments ahead →" : "Next: keep aside & review →";
  showTotals();
  if (focus) document.querySelector<HTMLElement>(`[data-step="${step}"] h2`)?.focus();
}
function showTotals(): void {
  if (!current) return;
  $("review-totals").replaceChildren();
  const list = document.createElement("dl");
  for (const [key,label] of [["verified_cash_cents","Money now"],["due_liabilities_cents","Bills still to pay"],["committed_spend_cents","Other money promised"]] as const) {
    const value = current.cash_position[key];
    const term = document.createElement("dt"), definition = document.createElement("dd");
    term.textContent = label; definition.textContent = value === undefined ? "From your itemised record" : amount(value); list.append(term,definition);
  }
  $("review-totals").append(list);
}
function checkInputs(inputs: HTMLInputElement[]): boolean {
  for (const input of inputs) if (!input.validity.valid) {
    const panel = input.closest<HTMLElement>("[data-step]"); if (panel) showStep(Number(panel.dataset.step));
    let parent = input.parentElement;
    while (parent) { if (parent instanceof HTMLDetailsElement) parent.open = true; parent = parent.parentElement; }
    input.reportValidity(); input.focus(); return false;
  }
  return true;
}
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
  $("results").hidden = true; $("entry-panel").hidden = false;
}
function syncEditor(): void { $("request-json").value = JSON.stringify(current,null,2); editorDirty = false; }
function showFields(): void {
  if (!current) return;
  for (const id of ["cash-fields","bills-fields","reserve-fields","performance-fields"] as const) $(id).replaceChildren();
  for (const [group,key,label,help,destination] of fields) {
    const record = current[group] as unknown as Record<string, unknown>;
    if (!Object.hasOwn(record,key)) continue;
    const value = record[key];
    if (value !== null && typeof value !== "number") throw new Error("Money fields must contain integer cents or null.");
    const wrapper = document.createElement("div"), caption = document.createElement("label"), input = document.createElement("input");
    input.id = key; input.inputMode = "decimal"; input.placeholder = "Leave blank if unsure"; input.value = decimal(value);
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
        syncEditor(); showTotals();
      }
      catch (error) { input.setCustomValidity(message(error)); $("error").textContent = message(error); }
    });
    wrapper.append(caption,input,hint);
    const zeroLabels: Record<string,string> = {due_liabilities_cents:"No bills to pay",committed_spend_cents:"No other money promised"};
    if (zeroLabels[key]) {
      const zero = document.createElement("button"); zero.type = "button"; zero.className = "text-button"; zero.textContent = zeroLabels[key];
      zero.addEventListener("click", () => { input.value = "0"; input.dispatchEvent(new Event("input",{bubbles:true})); }); wrapper.append(zero);
    }
    $(destination).append(wrapper);
  }
  if (current.schema_version === "kasimargin-input-v2") {
    const note = document.createElement("p"); note.className = "hint";
    note.textContent = "This record has individual bills and linked payments. Their amounts are worked out from that list; they aren’t blank or zero. Review the itemised record in Technical tools on the next step.";
    $("bills-fields").append(note);
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
  if (editorDirty || !checkInputs(moneyInputs())) {
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
    current = ownDay(); $("data-class").value = "OPERATOR_ATTESTED";
    $("scenario-description").textContent = "Your day, your records. Start with what you know; leave anything uncertain blank.";
  } else {
  const item = cases[Number($("scenario").value)];
  if (!item) return;
  current = structuredClone(item.input); $("data-class").value = "SYNTHETIC";
  $("scenario-description").textContent = `${item.scenario}. Example data only.`;
  }
  $("error").textContent = ""; $("transaction-feedback").textContent = ""; invalidate(); showFields(); showReview(); showTransactions(); syncEditor(); clearTransaction();
  showSource(); showStep(0,false);
}
function showSource(): void {
  const example = $("data-class").value === "SYNTHETIC";
  $("example-banner").hidden = !example; $("example-picker").hidden = !example;
  $("source-badge").textContent = example ? "Practice figures" : "Your figures";
  $("count-now").hidden = example;
}
async function run(saveReceipt = false): Promise<void> {
  $("error").textContent = "";
  if (editorDirty) { $("error").textContent = "Apply the edited record before calculating."; return; }
  if (transactionDirty) { $("error").textContent = "Add your transaction to this day, or clear the entry, before calculating."; return; }
  if (!current || !checkInputs(moneyInputs())) return;
  if (!checkInputs([$("record-snapshot"), $("record-horizon")])) return;
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
      if (revision === requestRevision) $("receipt-state").textContent = `Copy saved on this computer. File: ${saved.receipt_filename}. Choose Download to keep a copy in your downloads too.`;
      return;
    }
    const response = await post("/api/decision", payload);
    const result = await json<DecisionResult>(response);
    if (revision !== requestRevision) return;
    lastResult = result; lastPayload = payload;
    $("results").hidden = false; $("entry-panel").hidden = true;
    $("result-content").hidden = false; $("empty-state").hidden = true;
    $("margin").textContent = amount(result.summary.operating_margin_cents); $("headroom").textContent = result.summary.cash_headroom_cents === null ? "Still checking" : amount(result.summary.cash_headroom_cents);
    $("margin-card").hidden = result.summary.operating_margin_cents === null;
    const hold = result.summary.status !== "CALCULATED";
    $("status").className = `status${hold ? " hold" : ""}`;
    const through = new Intl.DateTimeFormat("en-ZA", {timeZone:"Africa/Johannesburg",dateStyle:"medium",timeStyle:"short"}).format(new Date(result.summary.horizon_end));
    const wording = resultMessage(result.summary);
    $("status").textContent = wording.title; $("next-check").textContent = wording.next;
    $("cash-caption").textContent = `Payments due before ${through}, South African time. ${payload.data_class === "SYNTHETIC" ? "Practice figures only." : hold ? "Some figures still need checking." : "Based on figures you checked."}`;
    $("record-checks").replaceChildren();
    $("other-checks").replaceChildren(); $("more-checks").open = false;
    if (result.summary.protected_cash_deficit_cents) {
      const deficit = document.createElement("li"); deficit.textContent = `Shortfall: ${amount(result.summary.protected_cash_deficit_cents)}. This is how much the recorded payments and money kept aside exceed your cash.`; $("record-checks").append(deficit);
    }
    const checks = recordChecks(result.summary);
    checks.forEach((check,index) => {
      const item = document.createElement("li"), text = document.createElement("p"), change = document.createElement("button");
      text.textContent = check.text; change.type = "button"; change.className = "text-button"; change.textContent = "Review this →"; change.setAttribute("aria-label",`${check.text} Review this`);
      change.addEventListener("click", () => {
        showStep(check.step);
        const target = check.target ? document.getElementById(check.target) : null;
        if (target instanceof HTMLDetailsElement) target.open = true;
        if (target) { let parent = target.parentElement; while (parent) { if (parent instanceof HTMLDetailsElement) parent.open = true; parent = parent.parentElement; } target.focus(); target.scrollIntoView({block:"center"}); }
      });
      item.append(text,change);
      (index === 0 || !hold ? $("record-checks") : $("other-checks")).append(item);
    });
    const additional = $("other-checks").children.length;
    $("more-checks").hidden = additional === 0; $("more-checks-label").textContent = `${additional} other thing${additional === 1 ? "" : "s"} to check`;
    $("cash-basis").replaceChildren();
    const basisLabels: ReadonlyArray<readonly [keyof Pick<CashBasis,"verified_cash_cents" | "due_liabilities_cents" | "committed_spend_cents" | "minimum_buffer_cents">, string]> = [["verified_cash_cents","Business money now"],["due_liabilities_cents","Less: bills still to pay"],["committed_spend_cents","Less: other money promised"],["minimum_buffer_cents","Less: money kept aside"]];
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
    document.getElementById("result-heading")?.focus();
  } catch (error) { invalidate(); $("error").textContent = message(error); }
  finally { controls.forEach(control => control.disabled = false); $("working-state").textContent = ""; }
}
$("scenario").addEventListener("change",choose);
function start(value: string): void {
  if (editorDirty || transactionDirty) { $("error").textContent = "Add or clear your transaction, and apply any full-record edits, before switching days."; $("error").scrollIntoView({block:"center"}); return; }
  $("scenario").value = value; choose(); $("welcome").hidden = true; $("journey").hidden = false; showStep(0);
  started = true; $("resume-check").hidden = false; $("replace-draft").hidden = true; pendingStart = null;
}
for (const [id,value] of [["start-example","0"],["start-own","own"]] as const) $(id).addEventListener("click", () => {
  if (started) { pendingStart = value; $("replace-draft").hidden = false; $("replace-confirm").focus(); return; }
  start(value);
});
$("resume-check").addEventListener("click", () => { $("welcome").hidden = true; $("journey").hidden = false; $("replace-draft").hidden = true; showStep(step); });
$("replace-confirm").addEventListener("click", () => { if (pendingStart !== null) start(pendingStart); });
$("replace-cancel").addEventListener("click", () => { pendingStart = null; $("replace-draft").hidden = true; $("resume-check").focus(); });
$("back-home").addEventListener("click", () => { $("welcome").hidden = false; $("journey").hidden = true; document.getElementById("welcome-heading")?.focus(); });
$("previous-step").addEventListener("click", () => showStep(step-1));
$("next-step").addEventListener("click", () => { if (checkInputs([...document.querySelectorAll<HTMLInputElement>(`[data-step="${step}"] input`)])) showStep(step+1); });
document.querySelectorAll<HTMLButtonElement>("[data-go-step]").forEach(button => button.addEventListener("click", () => showStep(Number(button.dataset.goStep))));
$("edit-answers").addEventListener("click", () => showStep(0));
$("count-now").addEventListener("click", () => {
  if (!current) return;
  $("record-snapshot").value = southAfricaInput(new Date().toISOString()); $("record-snapshot").dispatchEvent(new Event("input",{bubbles:true}));
});
for (const id of ["model","data-class"] as const) $(id).addEventListener("change", () => { invalidate(); showSource(); });
$("request-json").addEventListener("input", () => { editorDirty = true; invalidate(); });
$("apply-json").addEventListener("click", async () => {
  try {
    const response = await post("/api/validate", {raw_json:$("request-json").value});
    current = await json<FinancialRequest>(response); invalidate(); showFields(); showReview(); showTransactions(); syncEditor(); clearTransaction(); showTotals(); $("error").textContent = "";
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
function runCheck(save = false): void { void run(save).catch(error => { $("error").textContent = message(error); }); }
$("calculate").addEventListener("click", () => runCheck()); $("save").addEventListener("click", () => runCheck(true));
$("download").addEventListener("click", () => {
  if (!lastResult || !lastPayload) return;
  const blob = new Blob([JSON.stringify({data_class:lastPayload.data_class,input:lastPayload.input,result:lastResult},null,2)],{type:"application/json"});
  const url = URL.createObjectURL(blob), link = document.createElement("a"); link.href = url; link.download = "kasimargin-decision.json"; link.click(); URL.revokeObjectURL(url);
});
void fetch("/api/fixtures").then(response => json<Fixture[]>(response)).then(items => {
  cases = items; cases.forEach((item,index) => {const option = document.createElement("option"); option.value = String(index); option.textContent = item.scenario; $("scenario").append(option);});
  const own = document.createElement("option"); own.value = "own"; own.textContent = "My own day · blank figures"; $("scenario").prepend(own); $("scenario").value = "own"; choose();
  $("start-own").disabled = false; $("start-example").disabled = false; $("welcome-feedback").textContent = "";
}).catch(() => { $("welcome-feedback").textContent = "We couldn’t load this check. Make sure the local app is running, then reload this page. Your figures have not been sent."; });
