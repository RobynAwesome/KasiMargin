# Barber walkthrough: prepared, not executed

Prepared 17 October 2026. The owner reports an available barber and an in-person English visit. Participant identity, precise location, real financial records and raw responses remain private. No consent or outcome is recorded by this document.

## Before starting

Allow about 15–20 minutes if the barber is comfortable and trade permits. Ask permission without making participation a condition of the visit or haircut. Explain: “I am testing an early tool for keeping track of a working day. We are testing the tool, not you. You can skip anything or stop. We can use made-up numbers, and I won't record customer details.” Obtain agreement before taking notes. Audio, photographs and real receipts require separate specific permission; none is needed for this synthetic walkthrough.

Confirm comfortable English and whether the available device is suitable. The current app runs on the developer's laptop. Bring that laptop if practical; do not imply the barber can already use it on their own phone. If only the printed/story sheet is available, label it a concept interview, not an app usability test. Never expose the local development server or change firewall settings to improvise phone access.

Record an anonymous participant code, date, consent scope, device, exact application commit, test condition and any assistance in the private worksheet. Keep the participant's identity separate from observations.

## Start with their day

Ask, without suggesting the answer:

- “How do you keep track when someone pays for a haircut?”
- “What do you check at the end of the day?”
- “When do you lose track or have to work something out again?”
- “What would be useful to see immediately, and what would just get in the way?”

Record their routine and words. A preference for cash, paper, phone or conversation is an observation to preserve, not a design defect to correct.

## Try the actual prototype

Use a synthetic case. First let the barber explore the current example and cash-check flow without coaching. Record whether they can start, find the next action, understand an unknown result and correct an entry. Ask what information they had to prepare before the tool became useful. If a feature does not exist, say so; do not simulate a successful save or future capture experience as an implemented feature.

Then show this story to review the proposed daily record separately:

| Event | Amount |
| --- | --- |
| Cash float at opening | R100 |
| Two haircuts paid in cash | R50 each |
| One haircut paid by card; settlement not checked | R50 |
| Business purchase paid in cash | R20 |
| Cash counted at closing | R180 |

Ask: “What would you want the tool to show?” Then ask which money is recorded sales, which is in the drawer, and what still needs checking. The expected synthetic reading is R150 recorded sales and R180 counted cash. The card payment is not automatically spendable cash. Profit needs costs; headroom needs confirmed cash, obligations and reserve. The expected drawer calculation assumes complete cash movements.

Introduce a mistake: one cash haircut was R60, not R50. Ask how they would correct it and what should happen to the closing cash discrepancy. The app must retain a correction trail when that feature is implemented; today this is a concept probe. Do not teach the answer until the first response is recorded.

## Separate the AI comparison

Only if time and interest permit, use the matched cases and alternating order in [OPERATOR-COMPARISON.md](OPERATOR-COMPARISON.md). Record exact admitted model output/selection and digest. A deterministic fallback is a baseline condition, not evidence the model helped. A long cold load is a usability observation; do not make the barber wait simply to obtain a favourable demonstration.

For each task, note completion, errors, assistance, time and the person's own explanation. Separate unaided performance from the debrief. One person supports a feasibility observation, not a general benefit estimate.

## Close without leading

Ask what they would keep, remove or change, and where it could fit in their day. Ask whether they would choose to use it again and why. If discussing payment, ask what would need to improve before they would consider paying and how they would compare it with their current method. Do not invent a price anchor or record polite interest as a purchase. No payment is collected.

Offer to show them what you recorded and correct it. Explain what will remain private and what anonymous findings may be reported. Preserve refusals, confusion and “not useful” findings. Write a redacted result only after the session; if interrupted, record the completed portion and leave the rest unrun.

The private worksheet is `local-data/operator-comparison/barber-2026-10-17.md`. This preparation does not establish consent, attendance, task success, comprehension benefit or market demand.
