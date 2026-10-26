# built-in-skills

Built-in skills that ship with the HagiCode server release.

Built-in skills are bundled with each server release. Clients cannot install, update, or remove them, so every change to this set goes through a release.

This repository is the only place the built-in skill content is maintained. The release build (`repos/hagibuild`) verifies it and packages it, and the server's local development configuration reads it directly.

## Layout

```
content/                          publishable content only
  <slug>/SKILL.md                 one folder per skill, named by its slug
  <slug>/...                      supporting files of that skill
  built-in-skills.lock.json       one lock entry per skill folder
  .claude-plugin/plugin.json      Claude Code plugin manifest (bundle-level)
  .gitattributes                  "* -text", so bytes are hashed as stored
scripts/built_in_skills.py        maintenance tool (standard library only)
tests/test_built_in_skills.py     tests for the tool
```

Everything outside `content/` stays out of release packages. Only `content/` is the publishable unit.

Current skills: `hagi`, `impeccable`, `ponytail`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`, `ponytail-review`, `systematic-debugging`, `vercel-react-best-practices`, `verification-before-completion`, `visualise`.

## Trimmed upstream copies

Two skills are copies of an upstream folder with the upstream authoring files left out. Everything that is kept is byte-for-byte as upstream at the lock entry's `ref`, except the one local edit listed for `systematic-debugging`.

- `systematic-debugging` (`obra/superpowers`, `skills/systematic-debugging`, MIT): left out `CREATION-LOG.md` and `test-academic.md`, `test-pressure-1.md`, `test-pressure-2.md`, `test-pressure-3.md`. Local edit to `SKILL.md`, because the upstream text points at skills of the `superpowers` plugin: the line that says to use `superpowers:test-driven-development` is removed (that skill is not built in), and `superpowers:verification-before-completion` is written as `verification-before-completion` (built in, so it loads whatever prefix the agent CLI adds). Reapply both when recopying from upstream.
- `vercel-react-best-practices` (`vercel-labs/agent-skills`, `skills/react-best-practices`, MIT per the `license` field in its `SKILL.md`): left out `README.md`. The folder is named after the `name` in its `SKILL.md`, not after the upstream folder, so Claude Code lists it as `hagi:vercel-react-best-practices`.

## The `hagi` skill

`hagi` is the agent skill for the `hagi` CLI. It is copied from the `HagiCode-org/cli` repository, path `skills/hagi/`, which is the only place it is edited. `content/hagi/` is a byte-for-byte copy of that folder at the commit named in its lock entry. Claude Code lists it as `hagi:hagi`.

Do not edit `content/hagi/` here. To change it: edit `repos/cli/skills/hagi/`, commit in the CLI repository, recopy the folder, and set the lock entry's `ref` to that commit and `contentHash` to the output of `hash hagi`.

## Lock file

`content/built-in-skills.lock.json` has `schemaVersion: 1` and a `skills` list. Each entry records:

- `slug`: equal to the skill folder name
- `version`: the upstream or HagiCode version of the skill
- `source`: `{"type": "github", "repository", "ref", "path"}` for a skill taken from a Git repository, or `{"type": "local", "path"}`
- `contentHash`: the content hash of the folder, computed as described below

The lock file JSON schema is [built-in-skills-lock.schema.json](../hagibuild/schemas/built-in-skills-lock.schema.json). It lives in the Build Tools repository because `schemas/` is copied into every release package.

## Content hash

The hash of a skill folder is `sha256:<hex>`, computed as follows:

1. List every regular file under the skill folder, with its path relative to that folder in POSIX form (`/` separators), sorted by that path.
2. Take the SHA-256 of each file's bytes as stored. No line-ending normalisation.
3. Write, for each file in that order, the text `<relative path> TAB <file sha256 hex> LF` as UTF-8.
4. The content hash is the SHA-256 of that text.

The lock file and `.gitattributes` at the bundle root belong to no skill and are not hashed. Dot-prefixed bundle-level entries such as `.claude-plugin/plugin.json` are not skills and are checked by their own rules.

Any byte change to a skill file changes its hash, including line endings. A CRLF conversion counts as drift.

## Updating a skill

1. Change the files in `content/<slug>/`.
2. Run `python3 scripts/built_in_skills.py hash <slug>` and copy the printed `sha256:` value into that skill's `contentHash`. Do not compute it by hand.
3. Update `version` and `source` in the same entry when the skill's origin changes.
4. Run `python3 scripts/built_in_skills.py verify`. It exits non-zero and names each offending slug and kind when anything drifts. It also checks the front matter of every `SKILL.md`: the file must start with a `---` line, close it with a later `---` line, and give top-level `name:` and `description:` keys a non-empty value (inline, quoted, or a `>` or `|` block with at least one indented line). A bad front matter stops the release build too, which names the slug before any package is produced.
5. Run `python3 -m unittest discover -s tests -v`.

Verify reports these kinds of problem:

| Kind | Meaning |
| --- | --- |
| `missing-lock-entry` | A skill folder has no lock entry |
| `orphan-lock-entry` | A lock entry has no folder |
| `hash-drift` | The folder hash differs from the recorded `contentHash` |
| `missing-skill-md` | A skill folder has no `SKILL.md` |
| `invalid-front-matter` | A `SKILL.md` lacks a front matter block, has it unclosed, or lacks or leaves empty its `name` or `description` |
| `lock-invalid` | The lock file is missing, not JSON, has the wrong schema, or an entry is malformed or duplicated |
| `bundle-entry-invalid` | `.claude-plugin/plugin.json` is missing or does not name the `hagi` plugin with `"skills": "./"` |

## The `visualise` skill

`visualise` is installed from HagiCode's own repository, `HagiCode-org/skills-visualise`, not from the upstream `bentossell/visualise`. Its folder holds that repository's `SKILL.md` and `references/` only. Its `README.md` and git metadata are not copied.

Status: until the edits in `HagiCode-org/skills-visualise` are committed, the lock entry for `visualise` still names the upstream repository. Once they are committed, the entry names `HagiCode-org/skills-visualise` at a commit that holds the installed files.

To update `visualise`:

1. Commit the change in `HagiCode-org/skills-visualise`. The lock `ref` must name a commit that contains the files being copied.
2. Copy `SKILL.md` and `references/` from that commit into `content/visualise/`. Read them with `git show` or a clean checkout, not the working tree. Leave out `README.md` and `.git`.
3. Set the `visualise` lock entry to `source` `{"type": "github", "repository": "HagiCode-org/skills-visualise", "path": ".", "ref": "<full commit>"}`, `version` to the short commit hash, and `contentHash` to the output of `hash visualise`.
4. Run `verify`.

## Consumers

- **Release build** (`repos/hagibuild`): `pybuild/built_in_skills.py` verifies this folder and stages it into each package as `lib/Resources/BuiltInSkills/`. It reads the folder from `project.builtInSkillsDirectory` in its `configuration.yaml`, which defaults to `../built-in-skills/content`. A build needs this repository checked out beside `repos/hagibuild`.
- **Server, local development** (`repos/hagicode-core`): `BuiltInSkills:SourceRoot` in `src/PCode.Web/appsettings.Development.yml` reads this folder directly in `Source` mode. Production and the packaged server read the copy in the release package, not this folder.

## License

The files HagiCode wrote in this repository (the script, the tests, the lock file, the plugin manifest and the documentation) are under the MIT License in `LICENSE`.

The skill folders under `content/` that were copied from other projects keep the license of their source. `THIRD-PARTY-NOTICES.md` lists each source, its license and its copyright holder. The upstream license file, and for `impeccable` its `NOTICE.md`, sits inside the skill folder, because only skill folders are copied into a release package. The lock hash covers those files.

Added files that are not in the upstream folder: `LICENSE` in `impeccable`, the six `ponytail*` folders, `systematic-debugging` and `verification-before-completion`; `NOTICE.md` in `impeccable`; `LICENSE-NOTICE.md` in `vercel-react-best-practices`. `hagi` and `visualise` are not edited here, so their license statements are only in `THIRD-PARTY-NOTICES.md`.

Not yet done: the release build copies only skill folders, the lock file and the plugin manifest, so `THIRD-PARTY-NOTICES.md` and `LICENSE` do not reach a release package.

## Working on this repository

Do not edit a `contentHash` by hand; take the value from the `hash` command. See `AGENTS.md` for the notes for coding agents.
