# Preview Gate

Read this before the step named in a command's gate paragraph. This file is the one place that defines the preview's content, its values, how it is drawn, and how the user confirms it. A command's gate paragraph names its gate step and the step the gate must precede. It does not restate these rules.

## When the gate applies

Fourteen commands are gated.

- **Data commands** (the preview shows data the command gathered in this run): `extract`, `document` (Scan mode only), `optimize`, `audit`, `critique`.
- **Interface-changing commands** (the preview shows the plan the command wrote in this run): `overdrive`, `bolder`, `quieter`, `colorize`, `animate`, `delight`, `typeset`, `layout`, `distill`.

No preview is required for:

- `document` in Seed mode, because no project data has been scanned.
- Any command not listed above (`harden`, `polish`, `adapt`, `clarify`, `onboard`, `shape`, `init`, `live`, `generate`, `visualize`).

`audit` and `critique` do not change the project. For them the preview sits inside the report, and the confirmation is the question asked after the report that chooses follow-up commands (see Confirmation).

## Values

Every value in a preview carries one of these labels:

- **measured**: read by a tool or a run in this session (for example bundle size, LCP).
- **extracted**: read from the project files in this run (colors, font sizes, counts of repeated patterns).
- **current**: what the code has now.
- **proposed**: what the command's own plan would change. Always labeled `proposed`.
- **assessed**: a rating the command judged (for example the overdrive axes, audit dimension scores). Always labeled `assessed`, and never drawn on the same scale as measured values.
- **computed**: a value calculated from listed values in the same preview (for example a contrast ratio from two colors).

Rules:

- Do not invent or estimate a measurement. If a metric was not measured, omit it or label it `not measured`. Do not draw a placeholder bar.
- When a preview shows both current and proposed values, distinguish them visibly: solid marks for current, outlined or hatched marks for proposed, and a legend line that names each.
- Plot at most 10 rows. Sort by rank, highest first. Fold the rest into one aggregated bar labeled `other (N)`. The text table or the report still lists the full set.
- If there is nothing to show (for example `extract` finds no pattern used 3 or more times), say so in one line and continue the command's normal flow without a preview and without a question.

## What each command previews

### Data commands

| Command | Preview shows | Source of values |
|---|---|---|
| `extract` | One horizontal bar per candidate pattern, its length the occurrence count. A vertical line at 3 uses. Candidates below 3 are hatched and labeled `below 3`. | Pattern counts from Step 2 (extracted). |
| `document` (Scan mode) | A swatch strip of the extracted colors, each labeled with its role and value. A stepped bar ramp for the type scale. Short bars for the spacing steps and the radii steps. | Step 2 auto-extraction (extracted). |
| `optimize` | One bar per measured metric (LCP, INP, CLS, and bundle size where measured), with a tick at its budget: LCP 2.5 s, INP 200 ms, CLS 0.1. Unmeasured metrics are omitted or labeled `not measured`. | Measured in this run. |
| `audit` | Five bars for the dimension scores, each scaled 0 to 4. The total out of 20 with its rating band. A P0 to P3 count strip. Values identical to the Audit Health Score table. | Assessed scores; counts from the findings. |
| `critique` | One bar per scored heuristic, scaled 0 to 4, with the total. Values identical to the Design Health Score table. Heuristics scored `n/a` are left out. | Assessed scores. |

### Interface-changing commands

Every item comes from the plan the command wrote in this run. Do not show a change the plan does not contain.

| Command | Preview shows | Labels |
|---|---|---|
| `overdrive` | One row per direction (2 or 3). Four bars per row: ambition, performance cost, browser-support risk, complexity. | assessed |
| `bolder` | The one planned move, beside the existing type, motif and density values it reuses, and the value it turns up. | current, proposed |
| `quieter` | Paired current and planned bars for color saturation, visual weight, motion and element count. | current, proposed |
| `colorize` | One row per role: its current swatch and its proposed swatch, the OKLCH values, and the text-on-canvas contrast ratio before and after. | current, proposed, computed |
| `animate` | A timeline with one bar per planned motion, labeled with its duration and easing, and a marker for the budget the plan states. | proposed |
| `delight` | A simple map of the surface with numbered markers at each planned moment. | proposed |
| `typeset` | The type scale as stepped bars, current beside proposed, with sizes and weights. | current, proposed |
| `layout` | The spacing scale and section rhythm as stepped bars, current beside proposed. | current, proposed |
| `distill` | One bar per element group the plan removes or merges, with counts, and a count of what stays. | current, proposed |

## Drawing the preview

- Draw one SVG fragment in a single `visualizer` fence. The client renders the fence into the chat, as the `visualise` skill describes.
- The SVG starts with `<svg`, carries a `viewBox` (width 680), a `<title>` element, and an `aria-label` on the root element.
- No `<script>`, no event attributes, and no external resource: no `<image>` or `@import` pointing outside, no font or stylesheet link.
- Flat fills only: no gradients, shadows, blur or glow.
- Chrome and text use the host theme variables through inline style, for example `style="fill: var(--foreground)"`. Use the variable names in the `visualise` skill's design-system reference, and do not hard-code a palette. Do not put `var()` in a presentation attribute such as `fill="var(--foreground)"`; it does not work there.
- Project values (extracted or proposed colors) may appear only as fills that encode data, such as swatches. They are never used for text or chrome.
- Label every bar or marker with its value. A reader must be able to read the figures without the drawing.
- If the client cannot render a `visualizer` fence, or you know the preview will not display, present the same values as a Markdown text table in place of the SVG. The figures and the question are the same either way.

## Confirmation

After the preview, ask one question with Ask User Question. Tie its wording to the actual data or plan, for example `Extract these 4 candidates?` or `Apply this palette?`.

- Offer at least three options: **Proceed**, **Adjust**, **Stop**. Each option's description says what happens next.
- The question is the last thing in the message. Write the report or the preview first. Prose emitted after a structured question is withheld until the user answers.
- If Ask User Question is not available or returns an error, ask the same question in chat and wait for the reply.

Answers:

- **Proceed**: run the acting step with exactly the data or plan that was shown.
- **Adjust** with a named change: revise the data, plan or scope, rebuild the preview, and ask again.
- **Stop**, or no answer: do not run the acting step. Leave the project files unchanged, and say so in one line.

Exceptions:

- **`overdrive`**: its existing direction question is the confirmation, so do not add a second one. The options are the 2 or 3 directions plus **Stop**. Each direction option carries its description and trade-offs, as that command's Propose Before Building step requires. Only the chosen direction is built.
- **`audit` and `critique`**: they change nothing, so there is no Proceed gate before the report. The question asked after the report chooses which recommended follow-up commands to run. For `audit`, that is the one Ask User Question described in its own file. For `critique`, its existing Ask the User questions are the confirmation, and its rules still apply, including the `Questions skipped: <reason>` line. Run none of the follow-up commands yourself.
