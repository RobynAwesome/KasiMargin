# KasiMargin synthetic demo and submission checks

Prepared 18 October 2026. This is a recording/review guide, not a submission receipt.

## Deadline and delivery

Official [Week 2 rules](https://dev.to/page/hacktoberfest-week2-2026-10-12-contest-rules) re-read on October 18: end of entry period October 18, 23:59 PDT = **October 19, 08:59 SAST**. Internal calendar target remains October 18, 23:59 SAST. The Day 6 event requires a working demo, documentation, repository, findings and a published DEV article. An article draft, video file or passing CI alone does not complete it.

## Suggested short recording

| Time | Show | Say |
| --- | --- | --- |
| 0:00–0:15 | Welcome with the two starting choices | “A busy day does not always mean money to spend. This is KasiMargin, a local prototype for an owner-operated business.” |
| 0:15–0:50 | Two R50 cash sales, a R50 card sale and R20 cash expense | “These are fictional barber records. Sales are R150, including R50 by card. Card sales are not a confirmed bank balance.” |
| 0:50–1:10 | Correct one cash sale from R50 to R60; reload day | “Correct the amount without deleting its history. The daily record remains after reload. Sales are now R160.” |
| 1:10–1:40 | Separate money check with a complete synthetic example and an example missing evidence | “The money check needs counted or cleared cash and payments still due. A missing answer stays unknown. It does not approve spending.” |
| 1:40–2:10 | Explanation controls and redacted Gemma comparison | “Gemma runs locally and selects allowed explanations. The program supplies the figures and required warnings. We measured 21 completed synthetic calls, not customer benefit. A slow cold call may fall back.” |
| 2:10–2:25 | Limits and code link | “The barber walkthrough is next after submission. We have not measured willingness to pay. The repository includes setup, tests and technical evidence.” |

Do not present a previously recorded model output as live inference. If inference is shown live, retain the displayed model/fallback status and actual wait; disclose cuts or speed changes. Do not show private raw responses, machine details, personal paths, account screens or merchant records.

## Freeze and review checklist

- Review the browser save/correction/reload path using a separate synthetic database.
- Verify rapid submits, an uncertain response and unchanged retries; preserve errors and limits.
- Run the Python suite, TypeScript/build/helper tests and diff checks; verify provider checks at the exact pushed head.
- Review the public demo for readable text and accurate narration. Supply a publicly accessible video or deployment link and test it signed out.
- Review `DEV-SUBMISSION-DRAFT.md` against actual code and evidence. Remove unresolved placeholders before publication.
- Confirm the author, actual collaborators and any required DEV handles; do not copy the separate GOA team into this entry by assumption.
- Review project lineage, model terms and owner-supplied assets; no claim of organiser acceptance or individual eligibility follows from this checklist.
- Robyn reviews landing and final article publication. Preserve the exact code head, video hash, public URLs, publication time and observed submission response.

No calendar task is marked complete until its corresponding delivery evidence exists. The barber session is deferred until after hand-in by Robyn on October 18 and remains unrun. Robyn also confirmed a solo KasiMargin entry on October 18.

## Prepared recording

The [captioned MP4](demo/KasiMargin-synthetic-demo.mp4) is 97.24 seconds, H.264, 1280×1000, 2,763,961 bytes, with no audio. It records actual browser interaction with an isolated synthetic database. Captions are presentation overlays, not product features. The normal explanation is shown; no live model call is represented. All 2431 frames decoded successfully; four sampled frames were visually inspected. Human playback review is still pending.

An unauthenticated HEAD request to the [public review-branch video](https://raw.githubusercontent.com/RobynAwesome/KasiMargin/refs/heads/codex/terra-context-plan/docs/demo/KasiMargin-synthetic-demo.mp4) returned HTTP 200 with the expected byte length. GitHub serves it as `application/octet-stream`, so some browsers download it. That response is download-availability evidence, not a signed-out streaming-player test or a challenge submission receipt. [Recording/test receipt](receipts/submission-preparation-2026-10-18.json).
