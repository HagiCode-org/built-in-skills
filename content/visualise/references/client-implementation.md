# Client Implementation Guide

The renderer that makes this skill work. This guide describes the contract a client implements. It is a guide to the shape of the feature, not code to copy.

## Architecture

```
Model writes a ```visualizer fence
        ↓
Client waits for the closing fence, then builds a srcdoc
(CSP, injected variables, helper classes, the visual, bootstrap script)
        ↓
Sandboxed iframe: sandbox="allow-scripts" only, no allow-same-origin
        ↓
Frame posts height messages; host sets the iframe height
        ↓
Frame posts sendPrompt messages; host sends them to chat
        ↓
Host posts theme messages when the mode or theme changes
```

`mermaid` fences never reach the frame. The host's Mermaid renderer draws them.

## Why messages, not contentDocument

The frame has an opaque origin, so the parent cannot read `iframe.contentDocument` (it is `null`) and cannot write into the frame's document. Content goes in through `srcdoc`. Everything else crosses by `postMessage`, in both directions.

## Frame document (srcdoc)

Build the srcdoc once per visual content:

1. A CSP `<meta http-equiv="Content-Security-Policy">` as the first element (see CSP below).
2. A `:root` block with the injected variables, each set to a concrete colour or length.
3. The helper classes (`t`, `ts`, `th`, `box`, `node`, `arr`, `leader`, `tone-surface`, `tone-outline`) and the derived tones, defined with `color-mix()` from the injected values. The frame owns these definitions; visuals only use them.
4. The visual fragment from the fence.
5. The bootstrap script, last.

The frame background is transparent; the host card supplies the surface.

Set `srcdoc` as a property. Do not assemble the host page's markup by concatenating the visual into it, so the content cannot break out of the host document.

A bootstrap script of this shape defines `sendPrompt`, reports height and applies theme messages:

```html
<script>
  window.sendPrompt = (text) => parent.postMessage({ type: 'sendPrompt', text }, '*');
  new ResizeObserver(() => parent.postMessage(
    { type: 'height', height: document.body.scrollHeight }, '*')).observe(document.body);
  window.addEventListener('message', (event) => {
    if (event.source !== parent || event.data?.type !== 'theme') return;
    // write event.data.variables onto document.documentElement.style, without reloading
  });
</script>
```

The frame posts to `'*'` because its origin is opaque. The host checks `event.source` instead.

## Messages

| Direction | Message | Meaning |
|-----------|---------|---------|
| frame to host | `{ type: "height", height }` | Content height. The host sets the iframe height within a minimum and a maximum. |
| frame to host | `{ type: "sendPrompt", text }` | Send `text` to the chat as if the user typed it. |
| host to frame | `{ type: "theme", variables }` | Resolved values after the mode or theme changes. The frame rewrites `:root` and keeps its state. |

The host accepts a message only when `event.source` is its own frame's `contentWindow`, and validates the payload:

- `height`: a finite number, clamped to the minimum and maximum.
- `sendPrompt`: a non-empty string within a length limit. Ignore it when no session is open.
- Any other type or shape: ignore it.

There is no link bridge, so a visual cannot open a URL by itself.

## Host sketch

```tsx
const srcdoc = useMemo(() => buildSrcdoc(content, resolvedVars), [content]);
// The srcdoc carries the values at build time; later theme changes go by message.

useEffect(() => {
  const onMessage = (event: MessageEvent) => {
    if (event.source !== iframeRef.current?.contentWindow) return;
    const msg = event.data;
    if (msg?.type === 'height' && Number.isFinite(msg.height)) {
      setHeight(Math.min(Math.max(msg.height, MIN_HEIGHT), MAX_HEIGHT));
    }
    if (msg?.type === 'sendPrompt' && typeof msg.text === 'string'
        && msg.text.trim() && msg.text.length <= MAX_PROMPT) {
      onSendPrompt(msg.text);
    }
  };
  window.addEventListener('message', onMessage);
  return () => window.removeEventListener('message', onMessage);
}, [onSendPrompt]);

useEffect(() => {
  iframeRef.current?.contentWindow?.postMessage({ type: 'theme', variables: resolvedVars }, '*');
}, [resolvedVars]);

return <iframe ref={iframeRef} srcDoc={srcdoc} title={title} sandbox="allow-scripts"
  style={{ width: '100%', height, border: 'none', display: 'block', background: 'transparent' }} />;
```

## Injected values

Resolve each colour token through a probe element after the theme's classes and variables are applied (on the next animation frame). Set `color: var(--token)` on the probe and read its computed `color`. Raw token text can be a channel triple or an `oklch()` string depending on the theme, so do not inject it directly. Send `--radius` as a length.

Re-resolve when the mode or the active theme id changes. Two themes can share one mode, so a mode check alone is not enough. Do not decide the theme from `prefers-color-scheme`; the host theme decides.

## Closing fence and placeholders

Scan the raw message text, not the rendered markdown, because the markdown parser cannot tell an open fence from a closed one. A `visualizer` fence is closed only when a closing fence of the same or longer marker has arrived.

- Open fence while the message streams: show a loading placeholder, no frame.
- Open fence in a final message: show it as a code block.
- Closed fence with empty content: show an error state with a view-source control.

## CSP for the iframe

Set this as the first element of the srcdoc:

```
default-src 'none';
script-src 'unsafe-inline' https://cdnjs.cloudflare.com https://esm.sh https://cdn.jsdelivr.net https://unpkg.com;
style-src 'unsafe-inline';
img-src data:;
font-src data:;
connect-src 'none';
form-action 'none';
frame-src 'none';
```

Keep the script allowlist identical to the CDN allowlist in SKILL.md, and test that the two match. The sandbox without `allow-same-origin`, `allow-popups` or `allow-top-navigation` already blocks navigation and popups.

## Optional: MCP server wrapper

Only if you need this to work with clients you don't control:

```typescript
import { Server } from '@modelcontextprotocol/sdk/server';
import { z } from 'zod';
import fs from 'fs';

const server = new Server({ name: 'inline-visualizer', version: '1.0.0' });

server.tool('visualizer_read_me', {
  modules: z.array(z.enum(['design-system', 'diagrams', 'components', 'charts'])),
}, async ({ modules }) => {
  const docs = modules.map(m =>
    fs.readFileSync(`./references/${m}.md`, 'utf-8')).join('\n\n---\n\n');
  return { content: [{ type: 'text', text: docs }] };
});

server.tool('render_visual', {
  title: z.string(),
  widget_code: z.string(),
}, async ({ title, widget_code }) => ({
  content: [{ type: 'resource', resource: {
    uri: `visual://${title}`, mimeType: 'text/html', text: widget_code
  }}]
}));

server.listen();
```
