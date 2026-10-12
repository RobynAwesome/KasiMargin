# KasiMargin brand and themes

Owner instruction, October 13: the supplied Sculpted Ribbon Emblem is KasiMargin's logo; its colours should define light and dark modes. The original 1254 × 1254 PNG is copied unchanged to `kasimargin/web/assets/kasimargin-ribbon-emblem.png`. SHA-256: `826227e7159120d085efb88b5f953606458a0ebd9ce683bb43ed8646a79e2be9`.

## Visual direction

Light mode uses warm ivory and soft white, deep green text, a teal primary action, a lime cash card and an orange introductory accent. Dark mode uses deep blue and slate surfaces, pale mint text, mint/teal controls, a forest cash card and amber introductory accents. The same logo remains visible on both backgrounds. The shared ribbon gradient uses orange, lime, teal and blue; these are chosen interface colours inspired by the supplied artwork, not an asserted exact pixel extraction.

Colour is assigned by role. Cash cards have a distinct emphasis, HOLD states use amber, and errors use warm red. Written status, warnings and unknown values remain the source of meaning. Rainbow gradients are limited to a small decorative header line; ordinary text stays a solid readable colour.

## Existing components and token coverage

The former demo had one light palette and literal colours across fields, cards, warnings and buttons. Those colours now come from the two `:root` token sets in `style.css`: page, surface, input, text, muted text, action, outline, focus, cash, status, HOLD and error. Typography, spacing and financial calculations keep their existing hierarchy and behaviour.

The header uses the supplied mark with a readable text wordmark. The opening section displays the full supplied emblem. The README uses that same tracked PNG as its opening graphic and documents both palettes.

## Mode selector

| Property | Behaviour |
|---|---|
| Interface | Native Light / Dark buttons inside a labelled Colour mode group |
| Selected mode | `aria-pressed="true"` and contrasting fill |
| First visit | Follow `prefers-color-scheme` |
| Remembered choice | Only `light` or `dark` under browser-local `kasimargin-theme` |
| Initialization | External `theme.js` sets the root theme before the stylesheet is rendered |
| Keyboard | Native button focus and Enter/Space activation; visible focus ring |
| Hover | Surface emphasis on unselected buttons |
| During a calculation/save | Controls follow the existing disabled state; theme does not mutate the financial request |
| Storage unavailable | Catch storage failures; switching still works for the current page |
| Calculated result | Switching mode preserves the current records and result |

The preference is not sent to the server. It does not save merchant inputs or imply human approval. The CSP continues to allow only local scripts/styles; initialization uses an external script rather than inline script exceptions.

## Contrast and scope

Core text pairs were calculated from their CSS colours against the [W3C minimum text contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). Measured ratios for body text, secondary text, primary action, cash, status, HOLD and error text exceed 4.5:1 in both palettes. The light field outline was darkened after the initial measurement. Placeholder text uses the tested secondary-text token at full opacity.

This is a bounded colour/keyboard review, not a complete accessibility audit. Decorative brand colours are not used as ordinary text colours. The supplied logo is unchanged; its image lettering is accompanied by a readable text wordmark and descriptive alternative text.

## README source and boundaries

The formatting reference was the Local OneDrive Introduction-to-MCP `README.md`, inspected in full. Its opening graphic/badges, purpose, capabilities, state tables, quick start, repository layout, roadmap, design-system and privacy/license structure inform KasiMargin's document. No copied readiness score, production assertion, ecosystem implementation or platform grant is adopted. KasiMargin's headings and status rows describe only its own implementation and receipts.

Source populations remain separate. That Local formatting reference is not a Cloud/Drive parity claim. The original source artwork and parent repository are preserved. This change adds brand presentation and mode behaviour; it makes no financial, model-performance or economic promotion.
