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

Saga commands using `--path` accept these flags but do not read backend configuration or contact the backend, except `saga session create`, which calls the backend to find the registered project.

## Environment variables

Backend operations resolve runtime settings centrally before accessing the API.
Explicit flags always override environment variables.

| Variable | Purpose |
| --- | --- |
| `HAGI_API_BASE_URL` | Backend base URL, used when `--base-url` is not given. Overrides the config file. |
| `HAGI_API_TOKEN` | Bearer token attached as `Authorization: Bearer <token>`. |
| `HAGI_API_LANG` | Shared `Accept-Language` header value. |
| `HAGI_SESSION_ID` | Your own HagiCode session ID. Fallback for `--session` (`saga claim`, `saga mark`, the lock commands) and for `--master` (`saga session create`) when the flag is absent or blank. An explicit flag wins. |
| `HAGI_PROJECT_ID`, `HAGI_PROJECT_NAME`, `HAGI_PROJECT_PATH`, `HAGI_WORKING_DIRECTORY` | Set by HagiCode for an agent run, not read by the CLI. `HAGI_PROJECT_PATH` and `HAGI_WORKING_DIRECTORY` are file system paths. See [Session data](session-data.md#runtime-variables). |
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
settings do not affect that local operation. The one exception is `saga session create`, which calls the backend even with `--path`.

## Command overview

```text
hagi
|-- project   list | repositories | create | update | delete
|   `-- monospecs show | init | set | validate | reload | clone | remove-checkout
|-- proposal  list | create | optimize-description | generate | annotate | execute | archive | status | complete | send | get | messages | answer
|-- saga      init | new | list | status | items | mark | claim | assert-owner | release | freeze | check | tick | block | set-status | amend | archive | session create | session list | log append
|-- vault     list | create | update | delete
|   `-- files list | preview
|-- chat      list | get | messages | create | archive | delete | send
|-- hagitask  list | schema | create | send | get | messages | answer
|-- plan      list | get | create | update | enable | disable | delete | run
|-- skills    local list | enable | disable
|-- hero      list [--json]
|-- usage     limits [--provider] [--wait-until-above <percent> --max-wait <seconds> --jitter-seconds <seconds>]
`-- agent     lock acquire | status | renew | heartbeat | release | requisition | list
```

## Saga commands

Each command requires exactly one nonempty project selector:

- `--path <directory>` resolves a local directory on the CLI host. Relative paths use the current working directory. This
  selector does not read backend configuration or make API calls, except in `saga session create`, which looks up the
  registered project through the backend. Shared backend flags do not change its behavior otherwise.
- `--project-id <id>` reads the project list through the configured backend. Its project path must be a directory available
  on the machine running the CLI; the CLI does not execute filesystem operations remotely.

Missing, empty, or conflicting selectors exit `2` before backend access or file writes. Paths with spaces should be quoted.
Shared `--base-url`, `--token`, `--lang`, and `--json` options are accepted.

```bash
hagi saga init --path "./My Project"
hagi saga method run --json
hagi saga new demo --path "./My Project" --json
hagi saga list --path "./My Project"
hagi saga status demo --project-id <project-id> --json
hagi saga items demo --path "./My Project" --json
hagi saga claim demo --path "./My Project" --session orchestrator-1 --json
hagi saga mark demo --path "./My Project" --session orchestrator-1 --json
hagi saga check demo --path "./My Project" --phase run --json
hagi saga tick demo T1 --path "./My Project" --token "$SAGA_EXECUTION_TOKEN" --json
hagi saga session create --saga demo --path "./My Project" --title "T1 implementation" --role implementation --master orchestrator-1 --item T1 --json
```

`saga session create` takes its execution token from `SAGA_EXECUTION_TOKEN` only; `--token` is refused. It creates a Worker
chat session and records it in `runtime/sessions.md`. See [`saga.md`](saga.md#worker-sessions) for its metadata, record and exit codes.

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

`project monospecs` manages a project's MonoSpecs configuration (`monospecs.yaml`) and the local checkouts of its repositories. The CLI only sends requests; the backend reads and writes files and runs Git on its own host. To edit `.hagicode/monospecs.yaml` directly in a project root instead (initialize it, add repositories from URLs, reorder them by activity), use the built-in `monospecs` skill; no CLI call is needed for that.

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
- `proposal messages --pending-question` prints only the pending question of the session, from the same read; it exits `24` when none is pending. `proposal answer` answers that question. See [Answering a pending question](#answering-a-pending-question).
- Which stage each command starts, and how to follow a run, is in [openspec-workflow.md](openspec-workflow.md).

## Chat reads and message paging

`chat get` is a plain read using the shared session summary: JSON is `{ session }`. It does not start or wait for work. There is no chat `--wait` or `chat answer` command; proposal/HagiTask wait and answer behavior is unchanged.

```bash
hagi chat get --session-id <session-id> --json
hagi chat messages --session-id <session-id> --json
hagi chat messages --session-id <session-id> --page 2 --page-size 50 --order desc --json
hagi proposal get --session-id <session-id> --json
hagi proposal messages --session-id <session-id> --page 2 --page-size 50 --order desc --json
```

- `chat messages`, `proposal messages`, and `hagitask messages` share paging. Without flags: page 1, descending, page size omitted (backend default **50**, maximum **200**).
- `--page` and `--page-size` accept positive safe integers. `--order` accepts only `asc` or `desc`; ascending pages are not locally reversed. Partial paging options keep the other defaults.
- `--last <n>` requests one descending page of n newest messages, subject to the backend's 200-message cap. It cannot mix with any explicit `--page`, `--page-size`, or `--order`, even their default values. Invalid/conflicting options fail before a backend call.
- JSON retains every returned message and actual `page`, `pageSize`, `totalCount`, and `totalPages`, including clamping. No automatic page merging or complete-history guarantee. `--pending-question` still searches only the requested page with the same read.

For fresh-thread recovery, pass the explicit existing HagiCode session ID, not a provider thread ID or an assumed `HAGI_SESSION_ID`. Use the session's `chat` or `proposal` get/messages commands and older pages to recover the task, decisions, latest instructions, and remaining authorized work. Reuse the existing connection; use `hagi` on PATH or `npx @hagicode/cli` only with Node.js 24+. Report exact retrieval blockers without guessing context, credentials, or a backend address. Do not create another session, self-send, answer, or trigger a lifecycle action just to continue. Stay within the current stage and repository authorization; report readiness when no authorized work remains. See [session-data.md](session-data.md#recovering-context-in-a-fresh-provider-thread).

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

Scope flags of `hagitask create` build the request `scope` (repositories, vaults, projects). They replace the removed `targets`, `targetScopes` and `derived.targetScopeMarkdown` input keys and the removed request fields `outputVaultId`, `referenceVaultIds`, `editableVaultIds` and `targetProjects`; the backend rejects those keys by name.

- `--repository [<selection id>=]<path>:<read|write>`: explicit repository, repeatable. Without a selection id the task must have exactly one repository selection (read from the schema, one call); with several, pass the id, for example `--repository targetRepositories=repos/web:write`. The usage error lists the ids.
- `--all-repositories [<selection id>=]<read|write>`: every repository of the project for a selection. It cannot be combined with `--repository` on the same selection.
- `--project <project id>:<read|write>`: another project, repeatable.
- `--output-vault-id <id>`, `--reference-vault-id <ids...>`, `--editable-vault-id <ids...>`: vault roles in `scope.vaults`.
- A top-level `scope` key in the `--input` file is the request scope. It cannot be combined with any scope flag (exit `2`, no request). The CLI sends the rest of the input unchanged.
- Usage errors (exit `2`) name the flag and the value and send no request: an access other than `read` or `write`, an empty path or project id, a repeated path in one selection, a conflicting selection, or a missing or ambiguous selection id.
- `create --json` also prints the built `scope` at the top level (`null` when none was built).

Example: `hagi hagitask create --title "Refactor auth" --project-id <id> --task-id <task-id> --repository repos/web:write --repository repos/cli:read --reference-vault-id vault-docs --project <other-project-id>:read --json`. `hagi hagitask answer` answers the pending question of a HagiTask session, as described in [Answering a pending question](#answering-a-pending-question).

## Answering a pending question

When an agent asks the user a question, the session stops at `WaitingForReply`. Four steps follow, for `proposal` and `hagitask` alike:

```bash
hagi proposal get --session-id <session-id> --wait --json                 # 1. wait: settles at WaitingForReply; the output names the pending question
hagi proposal messages --session-id <session-id> --pending-question       # 2. read the question: header, numbered options, single or multi-select, custom answer, state
hagi proposal answer --session-id <session-id> --option staging           # 3. answer: --option (label or 1-based number), --text, --input <file|->, or --reject
hagi proposal get --session-id <session-id> --wait --json                 # 4. wait again for the run to continue
```

- `answer` reads the newest messages once, finds the pending question, checks the answer against it, and sends one request. It never retries. `--option` repeats for a multi-select question; a label that is a number goes through `--input`. `--question <n>` addresses one question (default 1). A prompt with several questions is answered with `--input`, a JSON document such as `{"answers":[{"question":1,"options":["staging"]},{"question":2,"text":["a note"]}]}`; `--input` cannot be combined with `--option`, `--text`, `--question` or `--reject`.
- Exit codes: `0` accepted (`delivered` or `resumed`); `35` the answer was refused, by the CLI before sending or by the backend, with the reason printed; `36` the question was already answered or is no longer open; `24` no pending question, or the message or question was not found. A usage error exits `2` before any request.
- A secret question's answer never appears in the output, the `--json` result or an error message.
- `messages --pending-question --json` prints `{ sessionId, messageId, userQuestion }`. `wait.pendingQuestion` in the `--wait --json` output names the question at `WaitingForReply`; the five existing `wait` fields do not change.
- **`answer` changes session state.** Run it only on an explicit user request or an explicit Saga instruction. Never answer on your own judgment: when a question is pending and nobody has asked you to answer it, tell the user and wait.

Super Commit is a prompt, not a preset task, so it has no schema and takes no `--input`. Start it with a prompt id:

```bash
hagi hagitask create --title "Commit the CLI changes" --project-id <project-id> --prompt-id auto-compose-commit.en-US --json
```

Start one only when the user asked for it. See [super-commit.md](super-commit.md) for its options, its result and when to start it.

- `schema` (human view) lists the target scope, commands and parameters, with each required parameter marked `yes`, then the requirements, scenes, endpoint and an example command. `--json` adds the input JSON Schema and the example request body.
- `create` needs `--title`, `--project-id`, and either `--task-id` or `--prompt-id`. `--input <file|->` needs `--task-id`. The input must be a JSON object. The CLI does not check its keys; the backend does, and it rejects a key that the schema does not list and a missing required value. A rejection is printed unchanged and no session is reported.
- `create --json` prints `{ session, presetTaskId, promptId, scope, requested }`, where `scope` is the built scope (or `null`). Read the session id from `session.sessionId`. `requested` carries `heroId` or `heroName` when a Hero was given, and `session.chatHero` names the Hero the backend bound when it returns one.
- `create --hero <name-or-id>` picks the Hero. A GUID is sent as `heroId`; any other value is sent as `heroName` (trimmed, matched without regard to case). Give `--hero` or `--hero-id`, not both: that is a usage error (exit `2`) and sends nothing. A blank value is also exit `2`. An unknown name, or both fields in one request, fails with the backend's message and creates no session. Needs a backend that includes the `hero_name` field; an older backend ignores the name and runs its default Hero.

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
|-- create   --input <file|-> [--name <name>] [--hero-id <id>] [--disabled] [--window-start <instant>] [--window-end <instant>] [--first-at <instant>] [--every <duration>] [--time-zone <iana>]
|-- update   --id <id> [--input <file|->] [--name <name>] [--hero-id <id>] [--enabled | --disabled] [--window-start <instant>] [--window-end <instant>] [--first-at <instant>] [--every <duration>] [--time-zone <iana>]
|-- enable   --id <id>
|-- disable  --id <id>
|-- delete   --id <id>
`-- run      --id <id> [--background]
```

- `create` enables the plan unless the document sets `enabled` or `--disabled` is passed.
- `update`, `enable` and `disable` read the current plan and send it back whole, so unchanged fields are kept. `update --input` replaces each top-level key it contains as a whole value.
- Interval schedule flags (`--window-start`, `--window-end`, `--first-at`, `--every`, `--time-zone`) build an `interval` schedule on `create` and `update`. Instants need a UTC offset (`Z` or `+hh:mm`), `--every` takes `<n>m`, `<n>h` or `<n>d` and the minimum is 5 minutes. A bad value, or a missing flag, exits `2` with no backend call. On `update` of an interval plan, each flag replaces only its field; on any other plan all four are required. The backend checks order rules and prints each problem by field.
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

An interval plan that fires every 3 hours on 14 November, Los Angeles time (eight runs, from 00:00 to 21:00):

```bash
hagi plan create --input release-watch.json \
  --window-start 2026-11-14T00:00-08:00 --window-end 2026-11-14T23:59-08:00 \
  --first-at 2026-11-14T00:00-08:00 --every 3h --time-zone America/Los_Angeles
hagi plan update --id "$PLAN_ID" --every 2h --json
```

The README's `## Plan Commands` section has a recurring HagiTask example and the full `update`, `enable`, `disable` and `delete` workflow, and its "Interval plans" subsection lists the flags.

## Skills commands

`skills local list` shows each installed skill with its origin (`user` or `built-in`), its enabled state for built-in skills (`yes` or `no`, shown as `-` for user skills), its version, scope, agents and path. `--json` returns the same data with the `origin` and `builtIn` fields.

```bash
hagi skills local list
hagi skills local list --json
hagi skills local enable --skill-name hagi
hagi skills local disable --skill-name hagi --json
```

- `enable` and `disable` take `--skill-name` and change one built-in skill. They apply to agent runs that start afterwards.

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

## Hero commands

`hagi hero list` reads the Heroes the backend supports now and prints the ones a chat can run with: enabled, and neither built in nor read only. These are the Heroes `--hero <name-or-id>` accepts. It is read-only.

```bash
hagi hero list --json
```

- `--json` prints `{ heroes: [{ heroId, name, executorType }] }`. The human view prints one line per Hero: name, `heroId`, executor type.
- An empty list means no Hero can run a chat right now. Do not pick a Hero for the user in that case.

## Usage commands

`hagi usage limits` reads the backend's Token Monitor usage: each provider's limit windows, with the remaining percent and the reset time of each. It is read-only and reads quota only from the backend, never from local files.

```bash
hagi usage limits --json
hagi usage limits --provider claude --json
hagi usage limits --provider claude --wait-until-above 10 --max-wait 480 --json
```

- `--provider <id>` keeps one provider, for example `claude` or `codex`.
- `--wait-until-above <percent>` waits until every short window (six hours or less) of `--provider` is above that remaining percent. It requires `--provider`. Weekly windows are reported but never hold the wait. The wait sleeps toward the blocking window's reset, re-reads at least every 5 minutes, and stops after `--max-wait` seconds (default `1800`, at most `21600`; `0` checks once). A read that fails is retried three times, 30 seconds apart, within the same limit.
- `--jitter-seconds <seconds>` (default `120`, at most `3600`; `0` disables) sets a random delay after a wait that ended `ready`, so runs that waited on the same reset do not start together. It applies only with `--wait-until-above`.
- `--max-wait` and `--jitter-seconds` without `--wait-until-above` are refused with exit `2` before any backend call.
- The JSON output has `state` (`ready`, `low`, or `unknown`; `null` for a plain read that has figures), `reason`, `windows` (each with `provider`, `kind`, `remainingPercent`, `resetsAtUtc`, `minutesToReset`, `windowMinutes`, `watched`) and `guard`, which is `null` for a plain read and otherwise holds `state`, `thresholdPercent`, `waitedSeconds`, `jitterSeconds`, `checkedAtUtc` and `blockers`.
- Low quota is a successful reading: `ready` and `low` both exit `0`, so a shell chain does not stop on low quota. Read `state` (or `guard.state`) from `--json`, or the first word of the text (`READY`, `LOW`), to tell them apart. Only an unusable reading exits `34`.
- The text output begins `READY`, `LOW`, `UNAVAILABLE` for a wait, and `READ` or `UNAVAILABLE` for a plain read. It names the blocking windows and their reset times, or the reason.

The saga orchestrator runs this wait before every Worker it dispatches; see [`saga.md`](saga.md).

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
| `34` | Quota unavailable: `hagi usage limits` could not read a usable figure, either on a plain read or after a wait's retries. Nothing is known about the quota, so none is claimed. Low quota is not this code: it exits `0` |
| `35` | Answer refused: `proposal answer` or `hagitask answer` found the answer invalid, by its own checks or by the backend (`invalid`, with its reason). Nothing was changed |
| `36` | Question already answered or no longer open: `proposal answer` or `hagitask answer` found it answered or cancelled. Nothing was changed by this call |
| `40` | Other HTTP 4xx |
| `50` | HTTP 5xx |
| `60` | Transport or connection failure |
| `70` | Unknown error |
