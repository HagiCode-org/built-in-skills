# UI Components Reference

Patterns for interactive explainers, comparisons, data records, metric cards, and steppers. All use HTML mode.

## Core aesthetic

Flat, clean surfaces on the host background. Minimal 0.5px borders. Generous whitespace. No gradients, no shadows except focus rings.

## Tokens

- Borders: `0.5px solid var(--color-border-tertiary)` (or `-secondary` for emphasis)
- Corner radius: `var(--border-radius-md)` for most, `var(--border-radius-lg)` for cards
- Cards: `--background` fill, 0.5px border, radius-lg, padding `1rem 1.25rem`
- Spacing: rem for vertical rhythm, px for internal gaps (8px, 12px, 16px)

## Pre-styled form elements

Inputs, selects, buttons, and range sliders are pre-styled. Write bare tags. Override only specific properties.

Buttons that trigger `sendPrompt` should append a ↗ arrow.

## Metric cards

For summary numbers:
```html
<div style="background: var(--color-background-secondary); border-radius: var(--border-radius-md); padding: 1rem;">
  <p style="font-size: 13px; color: var(--color-text-secondary); margin: 0 0 2px;">Label</p>
  <p style="font-size: 24px; font-weight: 500; margin: 0;">$3,870</p>
</div>
```
Use in grids of 2-4: `display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px;`

No border on metric cards — secondary bg differentiates them.

## Interactive explainer

Sliders, buttons, live state displays. No card wrapper — whitespace is the container.

```html
<div style="display: flex; align-items: center; gap: 12px; margin: 0 0 1.5rem;">
  <label style="font-size: 14px; color: var(--color-text-secondary);">Years</label>
  <input type="range" min="1" max="40" value="20" style="flex: 1;" oninput="update(this.value)"/>
  <span style="font-size: 14px; font-weight: 500; min-width: 24px;" id="out">20</span>
</div>
<div style="display: flex; align-items: baseline; gap: 8px;">
  <span style="font-size: 14px; color: var(--color-text-secondary);">£1,000 →</span>
  <span style="font-size: 24px; font-weight: 500;" id="result">£3,870</span>
</div>
```

## Comparison layout

Side-by-side cards:
```html
<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px;">
  <div style="background: var(--color-background-primary); border: 0.5px solid var(--color-border-tertiary); border-radius: var(--border-radius-lg); padding: 1rem 1.25rem;">
    <p style="font-weight: 500; font-size: 15px; margin: 0 0 12px;">Option A</p>
  </div>
  <div style="...same...">
    <p style="font-weight: 500; font-size: 15px; margin: 0 0 12px;">Option B</p>
  </div>
</div>
```

Recommended option: a heavier `border: 2px solid var(--foreground)` (the only exception to the 0.5px rule) and a text badge that says "Recommended": `background: var(--color-background-secondary); color: var(--color-text-primary); font-size: 12px; padding: 4px 12px;`. There is no accent colour; the stroke weight and the label carry the emphasis.

## Data record / card

Wrap in a single raised card:
```html
<div style="background: var(--color-background-primary); border-radius: var(--border-radius-lg); border: 0.5px solid var(--color-border-tertiary); padding: 1rem 1.25rem;">
  <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
    <div style="width: 44px; height: 44px; border-radius: 50%; background: var(--color-background-secondary); display: flex; align-items: center; justify-content: center; font-weight: 500; font-size: 14px; color: var(--color-text-primary);">MR</div>
    <div>
      <p style="font-weight: 500; font-size: 15px; margin: 0;">Name</p>
      <p style="font-size: 13px; color: var(--color-text-secondary); margin: 0;">Role</p>
    </div>
  </div>
</div>
```

## Stepper (for cyclic processes)

For event loops, Krebs cycle, GC — anything where last stage feeds back to first. Don't draw as ring diagrams.

```html
<div id="step-content" style="min-height: 200px; padding: 1rem 0;"></div>
<div style="display: flex; align-items: center; justify-content: space-between; padding-top: 12px; border-top: 0.5px solid var(--color-border-tertiary);">
  <button onclick="prev()">← Previous</button>
  <div style="display: flex; gap: 6px;" id="dots"></div>
  <button onclick="next()">Next →</button>
</div>
<script>
const steps = [{ title: 'Step 1', content: '...' }, /* ... */];
let current = 0;
function render() {
  document.getElementById('step-content').innerHTML =
    `<h3 style="font-size:16px;font-weight:500;margin:0 0 8px">${steps[current].title}</h3>
     <p style="font-size:14px;color:var(--color-text-secondary);margin:0">${steps[current].content}</p>`;
  document.getElementById('dots').innerHTML = steps.map((_, i) =>
    `<div style="width:8px;height:8px;border-radius:50%;background:${i===current?'var(--foreground)':'var(--border)'}"></div>`
  ).join('');
}
function next() { current = (current + 1) % steps.length; render(); }
function prev() { current = (current - 1 + steps.length) % steps.length; render(); }
render();
</script>
```

## Mockup presentation

Contained mockups (mobile, chat threads, modals) → wrap in background surface:
```html
<div style="background: var(--color-background-secondary); border-radius: var(--border-radius-lg); padding: 2rem; display: flex; justify-content: center;">
  <!-- mockup -->
</div>
```

For modals, use faux viewport (NOT position: fixed). The scrim mixes the foreground into transparent, so it darkens in light mode and lightens in dark mode:
```html
<div style="min-height: 400px; background: color-mix(in srgb, var(--foreground) 45%, transparent); display: flex; align-items: center; justify-content: center; border-radius: var(--border-radius-lg);">
  <div style="background: var(--color-background-primary); border-radius: var(--border-radius-lg); padding: 2rem; max-width: 400px; width: 100%;">
    <!-- content -->
  </div>
</div>
```

## Grid overflow fix

Use `minmax(0, 1fr)` instead of plain `1fr` to prevent children from pushing past container.
