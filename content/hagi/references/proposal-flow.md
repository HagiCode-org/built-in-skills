# Proposal Flow

Treat the proposal lifecycle as explicit, non-interactive backend actions.
One CLI command maps to one backend action.
Do not imply hidden chaining between `create`, `optimize-description`, `generate`, `annotate`, `execute`, `archive`, and `complete`.

## Configuration first

Confirm the backend target before discussing proposal commands:

- `--base-url <url>` or `HAGI_API_BASE_URL`
- `--token <token>` or `HAGI_API_TOKEN`
- `--lang <lang>` or `HAGI_API_LANG`
- `--json` for automation and machine-readable output

## Explicit lifecycle sequence

Use this order when explaining or validating proposal flows:

1. `proposal list`
2. `proposal create`
3. `proposal optimize-description` (optional)
4. `proposal generate`
5. `proposal annotate` (optional review loop)
6. `proposal execute`
7. `proposal archive`
8. `proposal complete`
9. `proposal send` for follow-up conversation on the active session

`proposal status` sets the session status directly and is not part of the sequence above.

Which stage each command starts, and what it leaves behind, is in [`openspec-workflow.md`](openspec-workflow.md).

Between two lifecycle commands, follow the run with `hagi proposal get --session-id <id> --wait --json` and wait until the status settles. A returned command only accepts the request. Read [`openspec-workflow.md`](openspec-workflow.md#who-drives-each-step) for what each status means.

After `proposal execute` settles and the code changes are still uncommitted, a Super Commit can commit them. Start it only when the user asks; see [`super-commit.md`](super-commit.md).

The CLI may suggest a next command, but it does not call later lifecycle APIs automatically.

## Repository scope

Every proposal names the repositories it may edit (writable) and the repositories it may only read (read-only). Both lists are always present, and an empty list is written as `none`.

1. Run `project repositories` for the proposal's project first:

   ```bash
   npx @hagicode/cli project repositories --id <project-id> --json
   ```

   Every `path` in that output (for example `repos/cli`) is a candidate. The human-readable output prints the same paths in its Path column.

2. Begin `--chief-complaint` with a `Repository scope` section. Its `Writable repositories:` and `Read-only repositories:` lists hold paths taken from step 1, one `- ` entry per line. An empty list is written as `- none`. The chief complaint text follows after a blank line.

3. Run `proposal create` with that chief complaint.

The scope is a text convention inside the chief complaint, not a structured field the CLI sends. `proposal create` has no scope flags: do not invent `--writable-repo` or `--readonly-repo`.

Where the scope comes from, in this order:

- The user's request names the writable and read-only repositories. Check each path against the step 1 list.
- Otherwise, the session's own repository scope, when the session states one. Name that scope with the action and its target before running `proposal create`.
- Otherwise, ask the user and show the step 1 repositories as the choices. Wait for the answer.

Rules:

- A path that is not in the step 1 list is asked about, never corrected or guessed.
- Never widen the writable list as a precaution, and never leave the `Repository scope` section out.
- When the project lists no repositories, the project root `.` is the only candidate: write `- .` as the writable entry and `- none` for read-only. Ask the user only if the request implies something else.

Worked example. The project has three repositories, and the user asks for a change to the CLI that only reads the core API:

```json
{
  "projectId": "proj-1",
  "name": "HagiCode",
  "isMonoSpecs": true,
  "hasError": false,
  "repositories": [
    { "name": "cli", "path": "repos/cli", "displayName": "CLI", "type": "library", "branch": "main", "isValidGitRepo": true },
    { "name": "hagicode-core", "path": "repos/hagicode-core", "displayName": "Core", "type": "backend", "branch": "main", "isValidGitRepo": true },
    { "name": "web", "path": "repos/web", "displayName": "Web", "type": "frontend", "branch": "main", "isValidGitRepo": true }
  ]
}
```

```bash
npx @hagicode/cli proposal create \
  --project-id proj-1 \
  --chief-complaint "Repository scope
Writable repositories:
- repos/cli
Read-only repositories:
- repos/hagicode-core

Add CLI completion for session workflows" \
  --default-title \
  --json
```

When the change touches only one repository and reads nothing else, the read-only list is written as `none`:

```bash
npx @hagicode/cli proposal create \
  --project-id proj-1 \
  --chief-complaint "Repository scope
Writable repositories:
- repos/web
Read-only repositories:
- none

Tighten the settings page copy" \
  --default-title \
  --json
```

## Published package examples

List sessions:

```bash
npx @hagicode/cli proposal list --json
```

Create a proposal session. The chief complaint begins with the `Repository scope` section; see [Repository scope](#repository-scope):

```bash
npx @hagicode/cli proposal create \
  --project-id <project-id> \
  --chief-complaint "Repository scope
Writable repositories:
- repos/cli
Read-only repositories:
- none

Add CLI completion for session workflows" \
  --default-title \
  --json
```

Optimize the description explicitly:

```bash
npx @hagicode/cli proposal optimize-description \
  --session-id <session-id> \
  --description "Improve the proposal framing" \
  --optimization-direction "Focus on implementation risk" \
  --json
```

Generate the proposal body:

```bash
npx @hagicode/cli proposal generate \
  --session-id <session-id> \
  --enable-explore-mode \
  --json
```

Submit annotations from a file or stdin:

```bash
npx @hagicode/cli proposal annotate --session-id <session-id> --input annotations.json
cat annotations.json | npx @hagicode/cli proposal annotate --session-id <session-id> --input - --json
```

Execute, archive, complete, or continue the session:

```bash
npx @hagicode/cli proposal execute --session-id <session-id> --json
npx @hagicode/cli proposal archive --session-id <session-id> --hero-id <hero-id>
npx @hagicode/cli proposal status --session-id <session-id> --status Reviewing
npx @hagicode/cli proposal complete --session-id <session-id>
npx @hagicode/cli proposal send --session-id <session-id> --content "Please continue"
```

## Session metadata

`proposal create` accepts `--metadata key=value` (repeatable) and `--metadata-json <file|->` (a JSON object of string values; `-` reads stdin). Use them to mark the sessions of one orchestrated run: a master marker on the orchestrator and worker markers on each proposal, so the run can find its sessions again.

```bash
MASTER_ID=$(hagi chat create --title "Batch master" --project-id <project-id> --metadata role=master --metadata batch=2026-11-07 --json | json_field '.session.sessionId')

hagi proposal create \
  --project-id <project-id> \
  --chief-complaint "Repository scope
Writable repositories:
- repos/web
Read-only repositories:
- none

Tighten the settings page copy" \
  --default-title \
  --metadata role=worker \
  --metadata master="$MASTER_ID" \
  --json
```

- Keys: 1 to 64 characters matching `^[a-z][a-z0-9._-]{0,63}$`. Values: 1 to 512 characters with no control characters. At most 16 entries. The backend checks these and its message is shown as it is.
- Each key appears once across both options. A repeat, a missing `=`, or a non-string JSON value exits `2` with no request sent.
- Metadata is write-once and visible to every reader of the session. Do not put secrets in it.
- The output `session` object carries `userMetadata` when the session has entries. Read it to confirm the markers were stored.

## Validation focus

After each lifecycle step:

- inspect JSON output or the suggested next command
- confirm the session identifier used by the next command
- check exit codes when the caller needs scripting guarantees
- switch to `repos/cli` maintainer workflows only if package-level behavior is insufficient
