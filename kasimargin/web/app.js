"use strict";
const $ = id => document.getElementById(id);
const themeButtons = [...document.querySelectorAll("[data-theme-choice]")];
function applyTheme(theme, remember = false) {
  document.documentElement.dataset.theme = theme;
  themeButtons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.themeChoice === theme)));
  if (remember) { try { localStorage.setItem("kasimargin-theme", theme); } catch { /* The choice still works without storage. */ } }
}
themeButtons.forEach(button => button.addEventListener("click", () => applyTheme(button.dataset.themeChoice, true)));
applyTheme(document.documentElement.dataset.theme || "light");
let cases = [], current, lastResult, lastPayload, editorDirty = false;
let revision = 0;
const fields = [["performance","recorded_sales_cents","Recorded sales"],["performance","attributable_costs_cents","Attributable costs"],["cash_position","verified_cash_cents","Current cash"],["cash_position","minimum_buffer_cents","Protected buffer"],["cash_position","due_liabilities_cents","Unpaid due liabilities"],["cash_position","committed_spend_cents","Other committed spending"]];
function amount(cents) {
  if (cents === null) return "Unknown";
  if (!Number.isSafeInteger(cents)) return "See exact cents in JSON";
  const sign = cents < 0 ? "−" : "", value = Math.abs(cents);
  return `${sign}R${Math.floor(value / 100).toLocaleString("en-ZA")}.${String(value % 100).padStart(2,"0")}`;
}
function decimal(cents) {
  if (cents === null) return "";
  if (!Number.isSafeInteger(cents)) throw new Error("This value exceeds the browser’s exact input range. Use the Python CLI.");
  return `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2,"0")}`;
}
function readMoney(text) {
  if (!text.trim()) return null;
  if (!/^\d+(\.\d{1,2})?$/.test(text)) throw new Error("Use a non-negative rand amount with at most two cents digits.");
  const [whole, fraction=""] = text.split(".");
  const cents = BigInt(whole) * 100n + BigInt(fraction.padEnd(2,"0"));
  if (cents > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error("Amount exceeds this browser demo’s exact range.");
  return Number(cents);
}
function invalidate() {
  revision += 1;
  lastResult = lastPayload = null;
  $("result-content").hidden = true; $("empty-state").hidden = false;
  $("receipt-state").textContent = "";
}
function syncEditor() { $("request-json").value = JSON.stringify(current,null,2); editorDirty = false; }
function showFields() {
  $("quick-fields").replaceChildren();
  for (const [group,key,label] of fields) {
    if (!Object.hasOwn(current[group],key)) continue;
    const wrapper = document.createElement("div"), caption = document.createElement("label"), input = document.createElement("input");
    input.id = key; input.inputMode = "decimal"; input.placeholder = "Unknown"; input.value = decimal(current[group][key]);
    caption.htmlFor = key; caption.textContent = `${label} · R`;
    input.addEventListener("input", () => { invalidate(); try { current[group][key] = readMoney(input.value); input.setCustomValidity(""); $("error").textContent=""; syncEditor(); } catch(error) {input.setCustomValidity(error.message); $("error").textContent=error.message;} });
    wrapper.append(caption,input); $("quick-fields").append(wrapper);
  }
}
function choose() {
  const item = cases[Number($("scenario").value)]; current = structuredClone(item.input);
  $("data-class").value = "SYNTHETIC"; $("scenario-description").textContent = `${item.scenario}. Example data only.`;
  $("error").textContent=""; invalidate(); showFields(); syncEditor();
}
async function run(saveReceipt=false) {
  $("error").textContent="";
  if (editorDirty) { $("error").textContent="Apply the edited record before calculating."; return; }
  if (![...$("quick-fields").querySelectorAll("input")].every(input => input.reportValidity())) return;
  if (saveReceipt && !lastPayload) return;
  const payload = saveReceipt ? {input:lastPayload.input, result:lastResult, data_class:lastPayload.data_class} : {input:structuredClone(current), model:$("model").value || null, save_receipt:false, data_class:$("data-class").value};
  const requestRevision = revision;
  const controls = [...document.querySelectorAll("input,select,textarea,button")];
  controls.forEach(control => control.disabled = true);
  try {
    const response = await fetch(saveReceipt ? "/api/receipt" : "/api/decision",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    const result = await response.json(); if (!response.ok) throw new Error(result.error || "Calculation failed.");
    if (revision !== requestRevision) return;
    if (saveReceipt) { $("receipt-state").textContent=`Saved to local-data/decisions/${result.receipt_filename}. Human review is not yet recorded.`; return; }
    lastResult = result; lastPayload = structuredClone(payload); lastPayload.save_receipt=false;
    $("result-content").hidden=false; $("empty-state").hidden=true;
    $("margin").textContent=amount(result.summary.operating_margin_cents); $("headroom").textContent=amount(result.summary.cash_headroom_cents);
    const hold=result.summary.status!=="CALCULATED";
    $("status").className=`status${hold ? " hold" : ""}`;
    $("status").textContent=hold ? "Hold the decision. Missing or disputed records prevent a headroom calculation." : `Calculated from confirmed inputs through ${result.summary.horizon_end}.`;
    $("cash-basis").replaceChildren();
    for (const [key,label] of [["verified_cash_cents","Confirmed current cash"],["due_liabilities_cents","Less: unpaid due liabilities"],["committed_spend_cents","Less: other committed spending"],["minimum_buffer_cents","Less: protected buffer"]]) {
      const term=document.createElement("dt"), definition=document.createElement("dd"); term.textContent=label; definition.textContent=amount(result.summary.cash_basis[key]); $("cash-basis").append(term,definition);
    }
    $("explanation").textContent=result.explanation;
    $("model-state").textContent=result.inference.status === "ADMITTED" ? `Local ${result.inference.model} selection admitted; figures supplied by the calculation engine. Digest: ${result.inference.digest}` : result.inference.status === "NOT_REQUESTED" ? "Deterministic baseline. No model was requested." : `Deterministic fallback: ${result.inference.reason}. No model output was admitted.`;
    $("receipt-state").textContent=saveReceipt ? `Saved to local-data/decisions/${result.receipt_filename}. Human review is not yet recorded.` : "Not saved. Review the result before saving or exporting.";
  } catch(error) { invalidate(); $("error").textContent=error.message; }
  finally { controls.forEach(control => control.disabled = false); }
}
$("scenario").addEventListener("change",choose);
for (const id of ["model","data-class"]) $(id).addEventListener("change",invalidate);
$("request-json").addEventListener("input",()=>{editorDirty=true;invalidate();});
$("apply-json").addEventListener("click",async()=>{try {const response=await fetch("/api/validate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({raw_json:$("request-json").value})}); const value=await response.json(); if(!response.ok)throw new Error(value.error); current=value; invalidate(); showFields(); syncEditor(); $("error").textContent="";} catch(error) {$("error").textContent=error.message;}});
$("calculate").addEventListener("click",()=>run()); $("save").addEventListener("click",()=>run(true));
$("download").addEventListener("click",()=>{if(!lastResult)return; const blob=new Blob([JSON.stringify({data_class:lastPayload.data_class,input:lastPayload.input,result:lastResult},null,2)],{type:"application/json"}), url=URL.createObjectURL(blob), link=document.createElement("a"); link.href=url; link.download="kasimargin-decision.json"; link.click(); URL.revokeObjectURL(url);});
fetch("/api/fixtures").then(response=>{if(!response.ok)throw new Error("Could not load examples.");return response.json();}).then(items=>{cases=items; cases.forEach((item,index)=>{const option=document.createElement("option");option.value=index;option.textContent=item.scenario;$("scenario").append(option);});choose();}).catch(error=>{$("error").textContent=error.message;});
