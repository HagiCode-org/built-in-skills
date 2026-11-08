# Saga commands

Saga files are project-local. Select exactly one project with `--path <directory>` or `--project-id <id>` for every
Saga command. A local `--path` is resolved on the CLI host and does not read backend configuration or make API calls.
The one exception is `session create` (see [Worker sessions](#worker-sessions)), which calls the backend even with `--path`
to find the registered project.

## Initialize managed resources

Run `init` before creating a Saga:

```bash
hagi saga init --path "./My Project"
hagi saga init --path "./My Project" --json
```

Initialization installs only the ignore rule under `.hagicode/sagas/.gitignore`. It creates no `prompts/` directory and
never installs method prompts into the project: the six bundled method prompts are read from the CLI package with
`hagi saga method <name>` (see [Published methods](#published-methods)). It does not repair or overwrite existing Saga
contracts, metadata, or runtime records.

Existing project-local `prompts/` files from an earlier installation are left in place. Initialization does not read,
compare, replace, or report them, so it never flags them as outdated or as conflicts. `--force` is still accepted, so
existing scripts keep working, but it changes nothing: no managed resource can be replaced or conflict any more. The
command prints each file's `created`, `unchanged`, or `merged` outcome and exits `0`. Forced initialization never discards custom `.gitignore` entries.

The `.gitignore` rule `**/runtime/` is merged as a separate exact line. Existing bytes, line endings, and entries are
preserved; LF and CRLF files are supported, and repeated initialization does not append duplicate rules.

Before writing, initialization checks that managed directories and files are not redirected, that resource targets are
regular files, and that writes will not replace unsafe hard-linked resources. Refused targets are reported as operation
failures rather than followed outside the selected project. Exact resources are not rewritten on repeat runs, preserving
their modes and modification times.

With `--json`, stdout contains the installation root, the `force` setting, per-file `path`/`outcome` entries, and an
empty `conflicts` array. The `files` array holds only the `.gitignore` entry.

## Published methods

The six method prompts (`goal`, `research`, `acceptance`, `plan`, `run`, `amend`) ship inside the installed CLI package,
not in the project. Read one with:

```bash
hagi saga method run
hagi saga method run --json
```

Plain output prints the method bytes unchanged. `--json` prints `{ "name", "sha256", "content" }`, where `sha256` is the
lowercase SHA-256 of the same bytes. The command takes no `--path` or `--project-id`, reads no backend or project file,
writes nothing, and works before a project has any Saga files. An unknown name, or a selector flag, exits `2`. Before
returning any method, the CLI verifies every bundled resource against `resources/saga/manifest.json`; a missing or
modified resource exits `30`, names the file, and prints no method content.

`freeze` records the six digests in a `methods:` section of `contract.lock`, for revision 1 and for every later
revision. The CLI computes the digests itself. A repeat freeze on an unchanged contract leaves the lock untouched,
including a lock written before this section existed, and `revisions/rN.lock` keeps its own section byte for byte.

`check --phase run --json` adds `methods: { "recorded", "drift": [{ "name", "recorded", "current" }] }` when a lock exists.
`recorded` is `false` for a lock without the section, and then `drift` is empty. Drift means the installed CLI's method
differs from the one the Saga was frozen under, which is expected after a CLI upgrade. It is a notice only: it never adds
an error, never changes the exit code, and never writes a file. Human output prints one `notice:` line per drifted method.
`execute` tells the user which methods changed and continues only after confirmation; a changed digest is not treated as
tampering. The plan phase never reports methods.

Project-local `prompts/` files are no longer used by any command. `execute` leaves them in place, ignores them, and says in
its report that they may be deleted.

## Create and inspect Sagas

`new <saga-id>` creates the Saga natively: it reserves `<saga-id>/` with an exclusive directory creation and writes
`saga.json` with `id`, `createdAt`, and `method`. It writes no runtime file. IDs must
match `^[a-z0-9][a-z0-9-]{0,62}$`: one to 63 lowercase letters, digits, or hyphens, beginning with a letter or digit. The
reserved names are `prompts`, `tools`, `archive`, `runtime`, `amendments`, and `revisions`. Invalid IDs are usage errors
(code `2`). An existing active path or an archive entry whose name ends in `-<saga-id>` is a collision; creation is
refused with code `30` and neither Saga is changed. Concurrent creations of one ID leave exactly one Saga.

The `--json` result identifies the Saga directory and includes the metadata written to `saga.json`:

```json
{
  "id": "demo",
  "directory": "/path/to/My Project/.hagicode/sagas/demo",
  "metadata": {
    "id": "demo",
    "createdAt": "2026-01-01T00:00:00Z",
    "method": 1
  }
}
```

The human result names `hagi saga method goal` as the way to read the planning method, and the four planning files to
write: `goal.md`, `research.md`, `acceptance.md`, and `progress.md`. `status` gives the same direction for the next artifact,
for example `hagi saga method research`.

Then inspect the Saga with the read-only commands:

```bash
hagi saga new demo --path "./My Project" --json
hagi saga status demo --path "./My Project" --json
hagi saga list --path "./My Project"
hagi saga items demo --path "./My Project" --json
```

### Query payloads and read-only behavior

`list --json` returns `{ "sagas": [...] }`; each row contains `sagaId`, `state`, `revision`, `counts`, `openAmendments`,
and `updatedAt`. `items <saga-id> --json` returns `{ "sagaId": "...", "items": [...] }`, with each item carrying its
canonical `id`, `title`, `state`, `cmd`, and `note`.

`status <saga-id> --json` returns the `saga-status/2` projection directly, with `schema`, `sagaId`, `revision`, `state`,
`updatedAt`, `note`, `artifacts`, `nextArtifact`, `counts`, `openAmendments`, and `items`. It derives this view from the
Saga files; `updatedAt` is the time of this observation, not the execution heartbeat in `runtime/status.json`. The query
does not refresh or rewrite that stored status, and its default `note` is empty rather than a cached execution note.

All three queries are strictly read-only: they do not initialize or repair resources, create runtime files, run the Saga
tool, or execute acceptance commands. Missing optional draft files use canonical empty-data behavior; malformed or
unreadable existing data is reported instead of being repaired. ## Execution ownership and the token

`claim`, `assert-owner`, and `release` manage `runtime/execute.lock`. Every mutating command (`freeze`, `tick`, `block`,
`set-status`, `amend`, `archive`, `release`, `assert-owner`) reads the execution token from `--token <token>` or, when
that flag is absent, from `SAGA_EXECUTION_TOKEN`. The exception is `session create`, which reads only `SAGA_EXECUTION_TOKEN`.

```bash
hagi saga claim demo --path "./My Project" --session orchestrator-1
hagi saga assert-owner demo --path "./My Project" --token "$SAGA_EXECUTION_TOKEN"
hagi saga release demo --path "./My Project" --token "$SAGA_EXECUTION_TOKEN" --workers-settled --json
```

- `claim --session <id>` creates the lock exclusively and returns the token once, in the human output and as `token` in
  JSON. A second claim is refused with code `1` and names the owning session. A lock is never taken over because of its
  age, and a refused claim changes no file.
- While a lock exists, a mutating command needs the holder's token. A missing or different token is refused with exit
  code `1` and changes no file. Without a lock, mutating commands run under their own gates, so a Saga created before ownership stays runnable.
- `assert-owner` exits `0` when no lock exists or the token matches, and `1` otherwise.
- `release` removes the lock only for the holder, with `--workers-settled`, and only when `runtime/status.json` records
  `paused` or `done`. Any other case exits `1` and keeps the lock.
- `status`, `items`, `list`, and `check` need no token and never write.
- With `--project-id`, the root `--token` is the backend bearer token, so `--token` is rejected with `--project-id` as a
  usage error (code `2`) that explains the rule. Pass the execution token through `SAGA_EXECUTION_TOKEN` instead. An execution token is never sent to the backend.

## Plan check and freeze

```bash
hagi saga check demo --path "./My Project" --phase plan
hagi saga check demo --path "./My Project" --phase run --json
hagi saga freeze demo --path "./My Project" --token "$SAGA_EXECUTION_TOKEN" --json
```

`check --phase plan` passes when `goal.md`, `research.md`, `acceptance.md`, and `progress.md` exist, `progress.md` has at
least one active item, every active item has an acceptance `cmd:`, and every acceptance entry names an active item.
`check --phase run` is the default; it adds the frozen-contract hash comparison, the amendment and open-question gates,
and the proof of every ticked item (an evidence file and a `Status: PASS` or `状态: PASS` report). Any other `--phase`
value is a usage error (code `2`). Checks write nothing.

`freeze` writes `contract.lock` revision 1 for a valid first contract, including the `methods:` section. A repeat on an unchanged contract exits `0`, reports
the existing revision, and leaves the lock bytes intact. After a contract change, freeze writes revision N+1 only when an
amendment is merged into `rN+1` and no frozen item disappeared without a superseded row. The previous lock moves to
`revisions/rN.lock`, each ticked item whose acceptance command changed is reopened, and its evidence and report move to
`runtime/history/rN/`. Every refusal (open question, unmerged amendment, plan mismatch, tampered contract, removed item)
lists each reason, exits `1`, and writes nothing.

## Worker sessions

Set `SAGA_EXECUTION_TOKEN` to the token that `claim` printed, then create a Worker and record it:

```bash
hagi saga session create --saga demo --path "./My Project" --title "T1 implementation" --role implementation --master orchestrator-1 --item T1 --json
```

- The command creates one ordinary chat session in the project and appends one line to `runtime/sessions.md`. It sends
  no message and does not archive the session; `hagi chat archive --session-id <id>` stays a separate step.
- Required and nonblank: `--saga <id>`, `--title <title>`, `--role implementation|verification`, and `--master <session-id>`
  (the orchestrator's own session ID). `--item <id>` is optional. `--saga` and `--item` are identifiers: a path separator
  or a traversal segment is a usage error (code `2`). Exactly one of `--path <directory>` or `--project-id <id>` is
  required.
- The execution token comes only from `SAGA_EXECUTION_TOKEN`, which must be set and nonempty. `--token` is refused with
  either selector as a usage error (code `2`), because the root `--token` is the backend bearer token and must never carry
  the execution token. A missing token is also code `2`, and no request is sent.
- `--path` calls the backend: the command lists the registered projects and takes the one whose real path equals the
  root. Projects whose path is missing on this host are skipped. Zero matches, or several, is a refusal (code `1`) that
  names the path or the matching IDs, and creates nothing. `--project-id` looks the project up directly.
- After the project and the Saga are resolved, the owner check of `assert-owner` runs with the token. A Saga without a lock
  still passes once a token is set. A wrong token is a refusal (code `1`), and an unknown Saga is code `24`.
- The new session's `userMetadata` holds `saga.id` (the Saga), `saga.role` (always `worker`), `saga.worker` (the `--role`
  value), `saga.master` (the `--master` value), and `saga.item` only when `--item` is given. The backend checks the key
  format (`^[a-z][a-z0-9._-]{0,63}$`), at most 16 entries, and value length (1 to 512 characters). The metadata is
  write-once and readable by everyone who can read the session, so it groups Workers and is not a security boundary. The
  token never appears in it. Workers created before this command carry no `saga.*` metadata and are not backfilled.
- The record is one line, `- <session-id> | <UTC time> | <role> | <item or -> | <title>`, appended after earlier content
  in `<root>/.hagicode/sagas/<saga>/runtime/sessions.md`. The file and `runtime/` are created when missing. Whitespace in
  the title, line breaks included, collapses to single spaces. A symbolic link or a redirected `runtime/` is refused
  before the session is created.
- If the append fails after the session was created, the command exits `1` and names the created session ID, in the
  human output and as `session.sessionId` in `--json` with `ok` false.
- `--json` success is one object: `{ "sagaId": "demo", "command": "session create", "ok": true, "session": { "sessionId": "...", "userMetadata": { ... } }, "record": "<path to sessions.md>" }`.
- Exit codes: `0` created and recorded; `1` refused, or the record failed after creation; `2` usage error; `24` Saga not found.

## Items, amendments, and archive

```bash
hagi saga tick demo T1 --path "./My Project" --token "$SAGA_EXECUTION_TOKEN" --json
hagi saga block demo T2 "tests keep failing" --path "./My Project" --token "$SAGA_EXECUTION_TOKEN"
hagi saga amend demo "Add retry" "Retry twice on timeout" --path "./My Project" --token "$SAGA_EXECUTION_TOKEN"
hagi saga archive demo --path "./My Project" --token "$SAGA_EXECUTION_TOKEN" --json
```

- `tick` marks an active item done in `progress.md` as `- [x] <id> <title> | evidence/<id>.log`. It needs a PASS report at
  `runtime/reports/<id>.md`, the evidence file, and a passing run check; otherwise it exits `1` and keeps `progress.md`.
  A successful tick clears that item's blocker. Item IDs containing a path separator or `.`/`..` are refused before any
  file access.
- `block` records a reason for an active item in `runtime/blocked.json`. An unknown item is refused. An empty reason is a
  usage error (code `2`).
- `amend` appends the next numbered file, `amendments/<NNN>-<slug>.md`, with an empty `merged-in:` header; the new
  amendment is open until the contract merges it. An empty title is a usage error (code `2`).
- `archive` moves a finished Saga (every active item done, no open amendment) to `archive/<date>-<saga-id>`. Use
  `--force` to archive unfinished work. An existing destination is refused even with `--force`.

## Status snapshot

```bash
hagi saga set-status demo --state paused --note "freeze refused" --path "./My Project" --token "$SAGA_EXECUTION_TOKEN" --json
```

`set-status --state` accepts `draft`, `planned`, `running`, `paused`, or `done`; any other value (or a missing value) is a
usage error (code `2`) and writes no file. The snapshot is the same `saga-status/2` projection that `status` reports, with
only `state` and `note` replaced. `planned` and `running` require the plan check to pass. `done` requires every active
item to be done with its evidence and PASS report, a frozen and unchanged contract, no open amendment, and no undecided
research question. A refusal exits `1`, lists its reasons, and leaves the stored `runtime/status.json` unchanged. The file
is replaced atomically, so a concurrent reader always sees a complete document.

## Exit codes and JSON

| Code | Meaning |
|------|---------|
| `0` | Success. |
| `1` | Refusal or failed check. Every reason is printed; nothing was changed. |
| `2` | Usage error: bad selector, missing or invalid argument, or `--token` with `--project-id` (with either selector for `session create`). |
| `4` | Reserved. `init` no longer produces conflicts, so no current command returns it. |
| `24` | Saga or project not found. |
| `30` | Operation failed, including a `new` collision. |

Write and check commands accept `--json`. Success and refusal write one object to stdout:

```json
{ "sagaId": "demo", "command": "tick", "ok": true, "itemId": "T1", "evidence": "evidence/T1.log" }
{ "sagaId": "demo", "command": "tick", "ok": false, "errors": ["no PASS report for T1: runtime/reports/T1.md must contain \"Status: PASS\""] }
```

Human output prints a one-line outcome and one line per refusal reason.

## Quota guard in a run

The `run` method reads quota before every Worker it creates, with `hagi usage limits --wait-until-above <threshold> --provider <P> --max-wait 480 --json`. `<threshold>` defaults to `10`, and `<P>` is the provider the Worker spends. The read waits at most 480 seconds per call, then the orchestrator runs it again, and a dispatch that has waited six hours in total on quota pauses the Saga with the provider, remaining percent and reset time as the reason.

- Exit `0` with `guard.state` `ready`: the Worker is dispatched.
- Exit `0` with `guard.state` `low`: the Worker is held, which is not a failure and not a pause. The orchestrator records the reading and reads again.
- Exit `34`: no usable figure. The orchestrator logs `quota unknown`, dispatches, and reads again before the next Worker.
- Any other exit code pauses the Saga the same way a failed check does.

Which provider a Worker spends follows its hero's executor. The run's options may carry `<provider-hints>`, pairs `<key>=<provider>` separated by commas, where `<key>` is a hero id or a Worker role (`implementation`, `verification`, `tuning`) and `<provider>` is a provider id such as `claude` or `codex`. For each Worker the orchestrator uses the hint for its hero id first, then the hint for its role, then the run's default `<provider>` (`claude` unless the run says otherwise). It uses the id exactly as written. The run's starter should write one hint for every hero whose executor is not the default provider, so a Worker of such a hero is read against the window it will actually spend. A missing or wrong hint reads the wrong window, so it costs an unnecessary hold or a `quota unknown` record, not a stalled run.

Every heartbeat note and every dispatch or held-dispatch log line carries the reading it was made on: the provider, the remaining percent, the reset time and the seconds waited. A worker that stops because its provider's quota is exhausted is not a failed verification: it is not counted and not given to a tuning worker, and it is re-dispatched unchanged after the quota read for its own provider returns `ready`. The command itself is documented in [`cli-usage.md`](cli-usage.md#usage-commands).

## Runtime ignore precondition

Before any command writes a file under a Saga's `runtime/` directory (`claim`, `set-status`, `tick`, `block`, `session create`,
and a `freeze` that moves history), it makes sure `.hagicode/sagas/.gitignore` ignores runtime directories. An existing
`**/runtime/` line is kept byte for byte; otherwise `**/runtime/` is appended with the file's line endings.
If the ignore file cannot be written, the command stops before `runtime/` is created.

## Read-only projection and ownership

Every write and check command is implemented by the CLI and never executes a separate tool. The CLI installs only the ignore rule and reads the method prompts from its own package; there is no installed tool to run.
