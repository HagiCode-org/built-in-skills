# Charts Reference

Data visualization using Chart.js or inline SVG. Use HTML mode. Colours come only from the injected variables (see design-system.md).

## Chart.js setup

```html
<div style="position: relative; height: 300px;">
  <canvas id="chart"></canvas>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
const ctx = document.getElementById('chart').getContext('2d');
const style = getComputedStyle(document.documentElement);
const textSecondary = style.getPropertyValue('--color-text-secondary').trim();
const borderDefault = style.getPropertyValue('--color-border-tertiary').trim();
const series = style.getPropertyValue('--foreground').trim();

new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Q1', 'Q2', 'Q3', 'Q4'],
    datasets: [{
      label: 'Revenue',
      data: [12, 19, 8, 15],
      backgroundColor: series,
      borderRadius: 4,
      borderSkipped: false,
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: textSecondary, font: { size: 12 } } }
    },
    scales: {
      x: { grid: { display: false }, ticks: { color: textSecondary, font: { size: 12 } }, border: { color: borderDefault } },
      y: { grid: { color: borderDefault }, ticks: { color: textSecondary, font: { size: 12 } }, border: { display: false } }
    }
  }
});
</script>
```

## Critical rules

- Wrap canvas in container with explicit height and `position: relative`
- Set `responsive: true` and `maintainAspectRatio: false`
- Read the injected CSS variables for every colour — never hardcode one. Chart.js takes plain colour strings and cannot evaluate `color-mix()`
- Tell data series apart with line style, point shape and labels (see Series styling)
- `borderRadius: 4` on bars
- Hide x-axis grid, show y-axis grid in border color
- Font size 12px for all chart text

## Series styling

Use the foreground and muted tones, and tell series apart by line style and point shape rather than hue:

| Series | Colour | Line | Point |
|--------|--------|------|-------|
| 1 | `--foreground` | solid | circle |
| 2 | `--muted-foreground` | solid | square |
| 3 | `--foreground` | dashed (`borderDash: [6, 4]`) | triangle |
| 4 | `--muted-foreground` | dashed | diamond |

Read these with `getPropertyValue`, as in the setup above. For an area fill, Chart.js cannot take a `color-mix()` value, so either skip the fill and keep the line, or use a plain colour string.

## Chart type selection

| Data shape | Type | Notes |
|-----------|------|-------|
| Categories + values | Bar | Horizontal if labels are long |
| Time series | Line | `tension: 0.3` for smooth curves |
| Parts of whole | Doughnut | `cutout: '60%'` — not pie |
| Two variables | Scatter | Add trend line if correlation is the point |

## Combining with metrics

Metric cards above, chart below:
```html
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 20px;">
  <!-- metric cards -->
</div>
<div style="position: relative; height: 280px;">
  <canvas id="chart"></canvas>
</div>
```

## Inline SVG charts (no library)

For simple visualizations without a library:

**Horizontal bar:**
```svg
<svg width="100%" viewBox="0 0 680 80">
  <text class="ts" x="40" y="30">Category A</text>
  <rect x="160" y="16" width="360" height="20" rx="4" style="fill: var(--muted-foreground)" opacity="0.8"/>
  <text class="ts" x="530" y="30">72%</text>
</svg>
```

**Sparkline:**
```svg
<svg width="120" height="32" viewBox="0 0 120 32">
  <polyline points="0,28 20,20 40,24 60,12 80,16 100,4 120,8"
    fill="none" style="stroke: var(--foreground)" stroke-width="1.5" stroke-linecap="round"/>
</svg>
```

## D3.js

For complex custom visualizations (force graphs, maps, treemaps):
```html
<div id="viz"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<script>
const svg = d3.select('#viz').append('svg')
  .attr('width', '100%').attr('viewBox', '0 0 680 400');
</script>
```

Use D3 only when Chart.js can't handle the layout. For standard charts, Chart.js is simpler.

## Number formatting

Round everything displayed:
- Counts: `value.toLocaleString()`
- Currency: `Intl.NumberFormat` with currency option
- Percentages: `Math.round(value) + '%'`
- Set `step` on range sliders for clean values
