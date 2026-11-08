# CLI Usage

Use the published package contract first.
The repository exists to build and maintain `@hagicode/cli`, but normal command execution should start from the package surface rather than the source tree.

## Installation paths

### Zero-install

```bash
npx @hagicode/cli --help
npx @hagicode/cli project list --json
```

### Project-local install

```bash
npm install @hagicode/cli
npx @hagicode/cli proposal list --json
```

### Optional global install

```bash
npm install -g @hagicode/cli
hagi --help
```

## Quick start

When `@hagicode/cli` is already available on `PATH`, these examples work as `hagi ...`.
For one-off execution, replace `hagi` with `npx @hagicode/cli`.

```bash
hagi --help
hagi project list --json
hagi proposal list --json
hagi saga list --path .
hagi chat list --json
hagi hagitask list --json
hagi hagitask create --title "Auto commit" --project-id <project-id> --prompt-id auto-compose-commit.en-US
```

## Shared runtime flags

Every command family supports the same runtime flags:

- `--base-url <url>`
- `--token <token>`
- `--lang <lang>`
- `--json`

Example:

```bash
hagi --base-url https://api.example.com --token "$HAGI_TOKEN" project list --json
```

Saga commands using `--path` accept these flags but do not read backend configuration or contact the backend.

## Environment variables

Backend operations resolve runtime settings centrally before accessing the API.
Explicit flags always override environment variables.

| Variable | Purpose |
| --- | --- |
| `HAGI_API_BASE_URL` | Backend base URL, used when `--base-url` is not given. Overrides the config file. |
| `HAGI_API_TOKEN` | Bearer token attached as `Authorization: Bearer <token>`. |
| `HAGI_API_LANG` | Shared `Accept-Language` header value. |
| `HAGI_SEND_STEER` | Turns Steer on (`1`, `true`, `yes`, `on`) or off (`0`, `false`, `no`, `off`) for `chat`, `proposal` and `hagitask send`. Any other value exits with code `2`. See [Steer for send commands](#steer-for-send-commands). |

## Config file

The base URL can also be stored in a local config file:

```json
{ "baseUrl": "https://api.example.com", "steer": false }
```

The file is `$XDG_CONFIG_HOME/hagi/config.json`, or `~/.config/hagi/config.json` when `XDG_CONFIG_HOME` is unset. The `steer` key must be `true` or `false`; any other value exits with code `2` and names the file.

Base URL precedence, highest first: `--base-url`, then `HAGI_API_BASE_URL`, then `baseUrl` in the config file.
There is no default. When none of the three is set, a backend operation exits with code `2` and names all three sources.
The local Saga selector `--path` is the exception: it does not read this file, so malformed, unreachable, or absent backend
settings do not affect that local operation.

## Command overview

```text
hagi
|-- project   list | repositories | create | update | delete
|   `-- monospecs show | init | set | validate | reload | clone | remove-checkout
|-- proposal  list | create | optimize-description | generate | annotate | execute | archive | status | complete | send | get | messages
|-- saga      init | new | list | status | items
|-- vault     list | create | update | delete
|   `-- files list | preview
|-- chat      list | create | archive | delete | send
|-- hagitask  list | schema | create | send | get | messages
|-- plan      list | get | create | update | enable | disable | delete | run
|-- skills    local list | enable | disable | uninstall
|             gallery search | detail | install
|             trusted list | upsert | delete | reset
`-- agent     lock acquire | status | renew | heartbeat | release | requisition | list
```

## Saga commands

Each command requires exactly one nonempty project selector:

- `--path <directory>` resolves a local directory on the CLI host. Relative paths use the current working directory. This
  selector does not read backend configuration or make API calls, and shared backend flags do not change its behavior.
- `--project-id <id>` reads the project list through the configured backend. Its project path must be a directory available
  on the machine running the CLI; the CLI does not execute filesystem operations remotely.

Missing, empty, or conflicting selectors exit `2` before backend access or file writes. Paths with spaces should be quoted.
Shared `--base-url`, `--token`, `--lang`, and `--json` options are accepted.

```bash
hagi saga init --path "./My Project"
hagi saga new demo --path "./My Project" --json
hagi saga list --path "./My Project"
hagi saga status demo --project-id <project-id> --json
hagi saga items demo --path "./My Project" --json
```

For offline use, invoke an installed package or a package already present in the `npx` cache. An uncached
`npx @hagicode/cli` command may need network access to download the package; the local `--path` operation itself does not
need backend access.

## Project repositories

`project repositories --id <project-id>` is read-only. It reads the same aggregation snapshot as `project list` and prints one project's repositories: name, path relative to the project root (for example `repos/cli`), display name, type and branch, with the project's MonoSpecs flag. The `path` values are the ones a proposal's `Repository scope` names.

```bash
npx @hagicode/cli project repositories --id <project-id> --json
```

An unknown project id exits with code `24` and prints no list.

## MonoSpecs commands

`project monospecs` manages a project's MonoSpecs configuration (`monospecs.yaml`) and the local checkouts of its repositories. The CLI only sends requests; the backend reads and writes files and runs Git on its own host.

- `show --id <id>` prints the document: version, repo directory, config path, commit-when-archive, and one row per repository with its local Git state. A repository that is not a valid Git checkout is marked `missing or not a Git repository`. `--yaml` adds the YAML preview; `--json` emits the same fields plus `code` and `metadata`.
- `init --id <id>` initializes the configuration; an already initialized project returns its document.
- `set --id <id>` changes the document. Options: `--version`, `--repo-directory`, `--commit-when-archive <true|false>`, repeatable `--add-repository <path>` and `--remove-repository <path>`, `--clone`. `--url`, `--name`, `--display-name` and `--type` require exactly one `--add-repository`. `--clone` needs at least one addition. The CLI reads the document, applies the change and saves the complete document; it strips local Git state fields before saving. Duplicate additions and unknown removals fail before any save.
- `validate --id <id>` validates the configuration. It exits `30` when the backend reports it invalid, after printing every error.
- `reload --id <id>` rereads `monospecs.yaml` on the backend host and refreshes Git state.
- `clone --id <id>` clones missing repositories. Repeat `--path <path>` to select some; `--include-optional` adds optional repositories when no `--path` is given. Every result row is printed; any `failed` row exits `30`.
- `remove-checkout --id <id> --path <path>` deletes one configured repository's local checkout. Dirty, unpushed or no-upstream checkouts are refused (exit `29`); the hint suggests `--force` when the refusal can be overridden. The configuration file is not changed.

Only configured repositories can be cloned or removed, and the backend confines paths to the project root. Exit codes: `2` usage (no request sent), `20` backend validation with field errors, `24` project not found, `29` conflict, `30` invalid configuration or failed clone.

```bash
hagi project monospecs show --id <project-id> --json
hagi project monospecs set --id <project-id> --add-repository repos/api --url <git-url> --clone
hagi project monospecs remove-checkout --id <project-id> --path repos/api --force
```

## Proposal commands

`proposal get` reads one proposal session. With `--wait` it polls until the status settles, so a stage can be followed without guessing. `proposal messages` reads its messages, newest first.

```bash
hagi proposal get --session-id <session-id> --wait --timeout 900 --json
hagi proposal messages --session-id <session-id> --last 1 --json
```

- `--wait` settles on any status other than Optimizing, Openspecing, Executing or Archiving. WaitingForReply counts as settled, because a person must answer.
- `--timeout`, `--interval` and `--grace` are seconds and need `--wait`. `--interval` must be less than `--timeout`. A timeout exits `31`.
- Which stage each command starts, and how to follow a run, is in [openspec-workflow.md](openspec-workflow.md).

## Session metadata

`chat create` and `proposal create` take write-once metadata entries. An orchestrator marks the sessions it starts with them, for example a master marker and worker markers, and finds them again through `userMetadata`.

```bash
hagi chat create --title "Master" --project-id <project-id> --metadata role=master --metadata batch=2026-11-07 --json
hagi chat create --title "Worker 1" --project-id <project-id> --metadata role=worker --metadata master=<master-session-id> --json
printf '{"role":"worker","master":"<master-session-id>"}' | hagi chat create --title "Worker 2" --project-id <project-id> --metadata-json - --json
hagi proposal create --project-id <project-id> --chief-complaint "<text>" --default-title --metadata role=worker --metadata master=<master-session-id> --json
```

- `--metadata key=value` is repeatable. The text is split at the first `=`, so a value may contain `=`.
- `--metadata-json <file|->` reads a JSON object of string values from a file, or from stdin with `-`. It is repeatable.
- A key may appear once across both options. A missing `=`, an empty key, a repeated key, or JSON that is not an object of string values exits `2` before any request is sent.
- Backend limits: at most 16 entries; a key of 1 to 64 characters matching `^[a-z][a-z0-9._-]{0,63}$`; a value of 1 to 512 characters with no control characters. The backend's message is printed as it is, and the session is not created.
- Write-once: the entries are set at creation and cannot be changed later. Do not put secrets in them: every reader of the session can see them.
- Output: `--json` of `chat create`, `chat list`, `proposal create` and `proposal get` carries `userMetadata` (an object of string values) when the session has entries. The human output adds one `userMetadata` line, keys sorted. A session without entries has no `userMetadata` field.

## HagiTask commands

A HagiTask is a preset task with a structured input. Use the schema-first flow: list the tasks, read one task's schema, write the input file from the schema, then create the session.

```bash
hagi hagitask list --json
hagi hagitask schema --task-id <task-id>
hagi hagitask schema --task-id <task-id> --json
hagi hagitask create --title "<title>" --project-id <project-id> --task-id <task-id> --input input.json --json
hagi hagitask get --session-id <session-id> --wait --json
hagi hagitask messages --session-id <session-id> --last 1 --json
hagi hagitask send --session-id <session-id> --content "Retry with a smaller diff"
```

`hagi hagitask get` and `hagi hagitask messages` take the same options as the proposal commands above.

Super Commit is a prompt, not a preset task, so it has no schema and takes no `--input`. Start it with a prompt id:

```bash
hagi hagitask create --title "Commit the CLI changes" --project-id <project-id> --prompt-id auto-compose-commit.en-US --json
```

Start one only when the user asked for it. See [super-commit.md](super-commit.md) for its options, its result and when to start it.

- `schema` (human view) lists the target scope, commands and parameters, with each required parameter marked `yes`, then the requirements, scenes, endpoint and an example command. `--json` adds the input JSON Schema and the example request body.
- `create` needs `--title`, `--project-id`, and either `--task-id` or `--prompt-id`. `--input <file|->` needs `--task-id`. The input must be a JSON object. The CLI does not check its keys; the backend does, and it rejects a key that the schema does not list and a missing required value. A rejection is printed unchanged and no session is reported.
- `create --json` prints `{ session, presetTaskId, promptId, requested }`. Read the session id from `session.sessionId`.

Example `input.json` for a task with one required input:

```json
{
  "inputs": {
    "commitScope": "cli"
  }
}
```

Migration: `hagi hagitask create` and `hagi hagitask send` replace the former `autotask` commands. There is no alias, so `hagi autotask` fails as an unknown command.

## Steer for send commands

`hagi chat send`, `hagi proposal send` and `hagi hagitask send` have two delivery modes. A normal send waits behind the running turn, as before. A Steer inserts the text into the running turn through one `SteerSession` call. Steer is off by default.

Options: `--steer` requests Steer for one call; `--no-steer` forces a normal send for one call. Without either flag, the first set source decides: `HAGI_SEND_STEER` (values above), then the `steer` config key, then `false`. `--no-steer` overrides `HAGI_SEND_STEER=1`.

Outcomes:

- `steered`: a running task took the message. It is not proof the text was used; the backend can requeue it when the run ends.
- `queued`: no running task took it, so it was sent as the next message. Exit code `0`. An idle session also answers `queued`, and the message then starts a run at once, so do not read `queued` as "waiting".

```bash
hagi chat send --session-id <session-id> --content "Check the diff" --steer --json
```

The `--json` output keeps `sessionId`, `message` and `requested`, and adds a `steer` object: `{ requested, source, effective, outcome?, messageId?, reason? }`. `source` is `flag`, `env`, `config` or `default`. On the Steer path `message` is `Steered` or `Queued`. `reason` appears only when Steer was requested but not used.

Conflicts and fallback:

- `--steer` with `--mode` or `--executor-type` exits with code `2` and sends nothing.
- Steer from `HAGI_SEND_STEER` or the config file, combined with `--mode` or `--executor-type`, sends a normal message with those options and sets `reason`.
- Steer from `HAGI_SEND_STEER` or the config file, against a backend without `SteerSession`, sends a normal message with the reason `the backend does not support Steer`. An explicit `--steer` returns the backend error instead.

A queued Steer is always sent in `Edit` mode. To keep another mode, use `--no-steer --mode <mode>`.

For unattended session-to-session messages, set `HAGI_SEND_STEER=1` in the orchestrator's environment. Use `--no-steer` on a single call that must take the normal queue.

## Plan commands

Scheduled plans save a proposal or HagiTask input with a schedule and, for HagiTask plans, an agent pool.

```text
hagi plan
|-- list
|-- get      --id <id>
|-- create   --input <file|-> [--name <name>] [--hero-id <id>] [--disabled]
|-- update   --id <id> [--input <file|->] [--name <name>] [--hero-id <id>] [--enabled | --disabled]
|-- enable   --id <id>
|-- disable  --id <id>
|-- delete   --id <id>
`-- run      --id <id> [--background]
```

- `create` enables the plan unless the document sets `enabled` or `--disabled` is passed.
- `update`, `enable` and `disable` read the current plan and send it back whole, so unchanged fields are kept. `update --input` replaces each top-level key it contains as a whole value.
- `run` creates a session now and waits for it. `run --background` returns `{ planId, accepted: true }` once the backend accepts the run, before the session exists.
- A manual run does not change the plan's state or next run time, and works for disabled and completed plans.

A one-time proposal plan document for `plan create --input`:

```json
{
  "type": "proposal",
  "name": "Weekly triage",
  "enabled": true,
  "schedule": { "mode": "once", "runAt": "2026-06-12T10:30:00Z" },
  "payload": {
    "title": "Weekly triage",
    "chiefComplaint": "Triage the open issues and propose the next sprint",
    "projectId": "<project-id>"
  }
}
```

The README's `## Plan Commands` section has a recurring HagiTask example and the full `update`, `enable`, `disable` and `delete` workflow.

## Skills commands

`skills local list` shows each installed skill with its origin (`user` or `built-in`), its enabled state for built-in skills (`yes` or `no`, shown as `-` for user skills), its version, scope, agents and path. `--json` returns the same data with the `origin` and `builtIn` fields.

```bash
hagi skills local list
hagi skills local list --json
hagi skills local enable --skill-name hagi
hagi skills local disable --skill-name hagi --json
```

- `enable` and `disable` take `--skill-name` and change one built-in skill. They apply to agent runs that start afterwards.
- `uninstall` removes a user skill. Built-in skills cannot be uninstalled; use `disable` to stop one from loading.
- Skill recommendation and install progress streaming are not part of the CLI. `skills gallery search`, `detail` and `install` are the discovery and install path.
- `skills gallery detail` adds skills.sh audit ratings. `--json` keeps the detail fields and adds `audit: { providers: [...] }`, one entry per provider with `provider` and, when supplied, `risk`, `alerts`, `score` and `analyzedAt`. Human output appends one `skills.sh audit (<provider>)` line per provider, with `--` for missing values. If the audit fails or has no data, the command still exits `0` and `audit.providers` is `[]`. A detail failure fails the command as before. The audit never changes the install command preview or installability.

## Agent lock commands

`hagi agent lock` takes turns on a shared resource with other agents. The full protocol, the numbers and the seven agent rules are in [`resource-lock.md`](resource-lock.md); read it before using these commands. There is no top-level `hagi lock`.

```bash
hagi agent lock acquire --lock-id eu-1/duckov --owner sess-7f2c
hagi agent lock acquire --server eu-1 --game duckov --owner sess-7f2c --wait --timeout 900
hagi agent lock status --lock-id eu-1/duckov --owner sess-7f2c --json
hagi agent lock heartbeat --lock-id eu-1/duckov --owner sess-7f2c --epoch 7
hagi agent lock renew --lock-id eu-1/duckov --owner sess-7f2c --epoch 7
hagi agent lock release --lock-id eu-1/duckov --owner sess-7f2c --epoch 7
hagi agent lock requisition --lock-id eu-1/duckov --owner sess-7f2c --reason "User order: take the lock now"
hagi agent lock list --prefix eu-1/
```

- Name the lock with `--lock-id <id>` or with `--server <name> --game <name>` (not both forms). The owner is your own session ID, passed as `--owner`; without it the CLI reads `HAGI_LOCK_OWNER`, then `HAGI_SESSION_ID`, and otherwise exits `2`.
- `acquire` takes `--wait`, `--timeout <seconds>` (default 900, needs `--wait`), `--lease-seconds <n>` and `--label <text>`. Without `--wait` it exits `0` for `Holding` and `Queued`. With `--wait` it exits `0` only when the owner holds the lock, `31` on timeout and `32` when the queue entry was dropped.
- `status` takes `--wait-seconds <n>`. `renew` and `heartbeat` take `--epoch <n>` and `--lease-seconds <n>`; `heartbeat` also takes `--interval <seconds>` (default 120) and `--verbose`. `release` takes `--epoch <n>`. `requisition` requires `--reason <text>` and takes `--label <text>`. `list` takes `--prefix <text>`.
- `heartbeat` is long-running and quiet on success. Run it under a watcher; it exits `32` when the lock is lost and `0` when stopped, without releasing.
- Timing: 10-minute feedback timeout, 24-hour maximum hold, 2-minute heartbeat interval, 30-second claim window, 60-second waiter TTL.
- Never run `requisition` unless the user explicitly ordered a forced take.

## Exit codes

Stable non-zero exits used by the CLI. The HTTP numbers are the equivalents of the gRPC status the backend answered with:

| Exit code | Meaning |
| --- | --- |
| `2` | CLI usage or validation failure |
| `20` | HTTP 400 |
| `21` | HTTP 401 |
| `23` | HTTP 403 |
| `24` | HTTP 404 |
| `29` | HTTP 409 |
| `30` | Operation failed: the backend returned a refusal, for example `skills local enable` or `disable` on a name that is not a built-in skill, an invalid MonoSpecs configuration, or a failed MonoSpecs clone |
| `31` | Wait timed out: `--wait` on `proposal get`, `hagitask get` or `agent lock acquire` reached `--timeout` before the session settled. The last status is printed. Not a success, and not a backend error |
| `32` | Lock lost: a `hagi agent lock` command learned that the owner no longer holds the lock (expired, taken back at the 24-hour cap, stale epoch, requisitioned). Stop using the resource. Distinct from `31` |
| `40` | Other HTTP 4xx |
| `50` | HTTP 5xx |
| `60` | Transport or connection failure |
| `70` | Unknown error |
