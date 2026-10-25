# Third-party notices

The skill folders under `content/` come from other projects. Each keeps the license of its source. The license of this repository (`LICENSE`, MIT) covers only the files HagiCode wrote here.

Sources and revisions are in `content/built-in-skills.lock.json`. This file records the license of each source as it was checked on 2026-10-25. It is not legal advice.

## Sources

| Skill folder(s) | Source repository | License | Copyright | License file shipped in the skill folder |
| --- | --- | --- | --- | --- |
| `impeccable` | `pbakaus/impeccable` | Apache-2.0 | Not stated in the license text | `LICENSE`, `NOTICE.md` |
| `ponytail`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`, `ponytail-review` | `dietrichgebert/ponytail` | MIT | 2026 DietrichGebert | `LICENSE` in each folder |
| `systematic-debugging`, `verification-before-completion` | `obra/superpowers` | MIT | 2025 Jesse Vincent | `LICENSE` in each folder |
| `vercel-react-best-practices` | `vercel-labs/agent-skills` | MIT, as declared (see below) | Not stated upstream | `LICENSE-NOTICE.md` |
| `visualise` | `HagiCode-org/skills-visualise`, itself taken from `bentossell/visualise` | MIT, as declared (see below) | Not stated upstream | None |
| `hagi` | `HagiCode-org/cli`, path `skills/hagi` | `AGPL-3.0-or-later` in the CLI's `package.json` | HagiCode | None |

The license files in the table are the upstream files at the revision recorded in the lock file, copied unchanged. They were added to the skill folders by HagiCode and are not part of the upstream folders; the lock hash covers them.

## impeccable

Apache License 2.0. `content/impeccable/LICENSE` is the full text. `content/impeccable/NOTICE.md` is the upstream third-party notice: the `ios.md` and `android.md` files under `reference/` are distilled from `ehmo/platform-design-skills` (MIT, author ehmo). Both files are in the folder we ship.

## ponytail

MIT. The six `ponytail*` folders each hold the upstream `LICENSE`, which names the copyright holder.

## superpowers

MIT. The two folders each hold the upstream `LICENSE`, which names the copyright holder.

`systematic-debugging` has a local edit and left out some upstream files; see `README.md`, section "Trimmed upstream copies".

## vercel-react-best-practices

Upstream declares MIT in the `license` field of `SKILL.md` and in the License section of its `README.md`. The upstream repository has no license file and no copyright line, so none is reproduced here. `content/vercel-react-best-practices/LICENSE-NOTICE.md` records this. The standard MIT permission text is below for reference.

## visualise

`HagiCode-org/skills-visualise` and `bentossell/visualise` both state MIT in their `README.md`. Neither has a license file or a copyright line. The folder holds only `SKILL.md` and `references/`, so nothing in it carries that statement; this file is the record.

## hagi

`hagi` is HagiCode's own skill, copied from `HagiCode-org/cli`. That repository's `package.json` declares `AGPL-3.0-or-later` and has no license file. This repository does not edit the folder, so the license cannot be added here. Whether the built-in distribution of this skill is meant to be under that license is for the owner of the CLI repository to confirm.

## MIT permission text

Applies to the sources marked "as declared" that name no copyright holder. Shown without a copyright line because none exists upstream.

> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
