# October 18 submission preparation and save recovery

Actor: Codex Forge, `I_AM_STATELESS_RENTER_NOT_LANDLORD`; existing scoped task role, no RTC seat. Base: `3ad087ecac9eb4f0b52b55eea6892747fbf589ad` on `codex/terra-context-plan`. Dedicated local checkout only; OneDrive source preserved.

## Observed problem and change

Browser entry and correction handlers previously generated new IDs and idempotency keys on every submit. A second tap or a retry after a committed request lost its response could therefore bypass server idempotency by looking like a new operation.

The browser now blocks overlapping submits, retains an uncertain request's identity and content within the live page, rejects attempts to change that pending content, and permits an unchanged retry. A definite HTTP 4xx rejection releases the pending request for correction; transport/5xx/unrecognised-success responses remain uncertain. Both sale entry and correction use the same helper. Controls lock while a save and its review reload are pending. A successful write followed by a failed review reload is described as saved with review unavailable, rather than prompting another entry.

No financial calculation, server admission, model gate or canonical protocol was weakened or redefined. Retry memory is not durable across page reload/close; the user must check the stored day after an interrupted page. The application remains an early local prototype.

## Validation

- 70 Python tests pass.
- Strict TypeScript check/build and 12 Node helper tests pass, including rapid submits, a committed request with lost response, unchanged retry identity, changed pending money, correction revision, definite rejection and unrecognised acknowledgement.
- `compileall` and `git diff --check` pass.
- Isolated Playwright browser test used a separate synthetic SQLite database and receipt destination. It entered two cash sales, one card sale and cash spending, corrected one cash sale, and verified page reload persistence. Two immediate submit events created one record. A server commit followed by an aborted response retained a retry; changed content was blocked, and unchanged retry created no duplicate. Five current records remained, with R185 synthetic recorded sales after the additional R25 recovery test.
- Desktop light and 390px dark screenshots were inspected. The narrow page had no horizontal overflow. No browser page errors were captured.

Interactive browser and native UI tools failed to initialize with `failed to write kernel assets` / OS error 3. The bundled Playwright version first requested absent browser revision 1234; using the already installed revision 1228 explicitly allowed the isolated software test to run. These are tool startup failures, not successful UI-tool executions. Raw logs, database, test script and fast technical recording stay private under ignored `local-data/submission-2026-10-18/`.

## Calendar, deadline and human evidence

Live Google Calendar Day 5 and Day 6 descriptions were re-read. Day 6 requires demo, documentation, repository, findings and a published DEV article. The official contest rules were re-read: October 18, 23:59 PDT = October 19, 08:59 SAST. Internal target remains October 18, 23:59 SAST.

Robyn confirmed on October 18 that the barber walkthrough did not occur and should follow hand-in. Consent, unaided comprehension, device fit, repeat use and willingness to pay remain unobserved. The article does not claim a first-user result. Neither the local tests nor the model evaluation substitutes for that experiment.

## Prepared deliverables and remaining boundaries

The [article draft](../DEV-SUBMISSION-DRAFT.md) follows the official template and links code/evidence. The [demo runbook](../DEMO-RUNBOOK.md) covers the recording story, limitations and public-delivery requirements. The standard explanation is used in the UI demonstration; the prior actual Gemma evaluation is identified as prior technical evidence, not new live inference. The optional model's eligibility against the contest's core-AI requirement remains an organiser decision.

Final demo review, public video URL, author/collaborator confirmation, owner landing/publication, observed submission response and field evidence remain separate completion states. No public article, deployment, paid service, merchant contact or task-completion flag was created by this preparation. Exact pushed-head provider checks must be recorded after delivery.
