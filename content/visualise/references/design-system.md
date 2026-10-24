# Design System Reference

The core design tokens and rules that every visual must follow. Read this once per conversation before generating any visual output.

## Philosophy

- **Seamless**: The visual shouldn't feel embedded from somewhere else. It should look native to the host app.
- **Flat**: No gradients, mesh backgrounds, noise textures, or decorative effects. Clean flat surfaces.
- **Compact**: Show the essential inline. Explain the rest in prose outside the visual.
- **Text goes in your response, visuals go in the output** — all explanatory text, descriptions, and summaries belong in your normal response text. The visual output should contain only the visual element itself.

## Injected variables

The client injects these into the frame as concrete values. Always use them; never write a colour value yourself. The host sets the theme, so the same markup renders correctly in light and dark mode.

**Colours (injected):**
- `--background` — page and card surface (alias `--color-background-primary`)
- `--foreground` — primary text (alias `--color-text-primary`)
- `--muted-foreground` — secondary text, labels (alias `--color-text-secondary`)
- `--border` — default border (alias `--color-border-tertiary`)

**Derived tones (computed in the frame with `color-mix()`):**
- `--color-background-secondary` — surfaces, cards, metric boxes
- `--color-text-tertiary` — hints, placeholders
- `--color-border-secondary` — emphasis borders, arrows, hover states

**Radius (injected):**
- `--radius` — the host's corner radius, a length
- `--border-radius-md` — same as `--radius`, for most elements
- `--border-radius-lg` — radius + 4px, for cards
- `--border-radius-xl` — radius + 8px, for large containers

**Typography (injected):**
- `--font-sans` — default font
- `--font-mono` — code

## Derived tones

To make a tone that is not in the list above, mix the injected values in `color-mix()`:

```css
background: color-mix(in srgb, var(--foreground) 6%, var(--background));
```

Keep the foreground share small (about 5 to 15 percent) so the tone stays neutral in both themes.

## Meaning without colour

Colour is not a signal. Express status, grouping and emphasis with shape, label and line style:

- **Status:** a text label ("Failed", "Done") plus a shape drawn with SVG paths (a check, a cross, a triangle). No emoji.
- **Optional or fallback path:** dashed line (`stroke-dasharray`).
- **Emphasis or recommended option:** a heavier stroke (2px) in `var(--foreground)`, plus a label.
- **Grouping:** `tone-surface` for the group container, `tone-outline` for members.
- **Categories:** a different shape or label, never a different colour.

There is no accent colour in this version. Do not invent one.

## Do not

- Do not write hex, `rgb()`, `hsl()` or named colours.
- Do not use the colour ramps, colour classes, semantic colour variables, tertiary background or primary border variables, or the serif font variable from older versions of this skill. They are no longer injected.
- Do not write dark-mode rules (`prefers-color-scheme` or similar). The host handles the theme.
- Do not put `var()` in SVG presentation attributes such as `fill="var(--foreground)"`; it does not work there. Use `style="fill: var(--foreground)"` or a class.

## SVG Setup

```svg
<svg width="100%" viewBox="0 0 680 H">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
      markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
        stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>
</svg>
```

- viewBox width always 680 (matches container 1:1)
- Set H to fit content: last element bottom + 40px
- Safe area: x=40 to x=640
- Background transparent — no wrapper div
- Arrow marker uses `context-stroke` to inherit line color

### Pre-built SVG classes

**Text:** `t` (14px primary text), `ts` (12px secondary text), `th` (14px bold/500 heading)
**Shapes:** `box` (neutral rect), `node` (clickable with hover), `arr` (arrow line), `leader` (dashed line)
**Tones:** `tone-surface` (surface fill, secondary border, primary text), `tone-outline` (background fill, tertiary border, primary text)

Apply a tone class to the `<g>` that wraps a shape and its text, not to a `<path>`. Tones set fill, stroke and text colour from the injected variables, and dark mode is automatic.

### Font width calibration

- 14px: ~8px per character
- 12px: ~7px per character
- Check: `box_width = max(title_chars × 8, subtitle_chars × 7) + 24`

SVG text never auto-wraps. If a subtitle needs wrapping, it's too long — shorten it.

### Text positioning

Every text inside a box needs `dominant-baseline="central"` with y at the center of its slot.

### viewBox checklist

1. Find lowest element: max(y + height)
2. Set viewBox height = that value + 40
3. Verify rightmost element within x=640
4. Check text-anchor="end" doesn't extend past x=0
5. No negative coordinates

## HTML Rules

- No emoji — use CSS shapes or SVG paths
- No font-size below 11px
- Sentence case always
- No mid-sentence bolding — use `code style` for entity names
- Round every displayed number (Math.round, toFixed, Intl.NumberFormat)
- Text on a tone uses `--foreground` or `--muted-foreground`
- No rounded corners on single-sided borders
