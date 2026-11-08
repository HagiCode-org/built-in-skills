# Session Data

Use this reference when an agent runs inside a HagiCode session and the user asks about their own projects, proposals, chat sessions, vaults, scheduled plans or installed skills.
Read-only inspection comes first. Change state only when the user asked for that change in the conversation.

## Runtime variables

A HagiCode session can give you four variables. Each one is defined here, once:

| Variable | Carries |
| --- | --- |
| `HAGI_API_BASE_URL` | Address of the backend that started the session. `hagi` reads it when no `--base-url` is given. |
| `HAGI_VERSION` | Version of the HagiCode server that started the session. |
| `HAGI_DEPLOYMENT_TYPE` | Deployment type of that server. |
| `HAGI_API_LANG` | The user's effective AI language, `zh-CN` or `en-US`. `hagi` sends it as `Accept-Language`. |

The server adds them to an agent run only when all of these hold:

- the built-in `hagi` skill is installed and enabled;
- the run is on Claude Code, Pi, OpenCode, GitHub Copilot or omp, the agent CLIs that load built-in skills at launch;
- the value is one the server can determine. A value it cannot determine is left out, and the run still starts.

A value the user already set in the environment is kept, not replaced.
The variables carry facts about the server and the language only. They never carry a token or a file path.

If a variable you rely on is absent, say that it is absent and ask the user. Do not guess a value, install software, or retry in a loop.

## Connection

Run `hagi` with no `--base-url` flag and no token when `HAGI_API_BASE_URL` is set; the variable is enough.

- Pass `--base-url <url>` only when the user gives you an address.
- If the CLI exits with code `2` and says no backend base URL is configured, the variable is missing from this session. Tell the user, and ask for the address. Do not guess one.
- Use `--json` for every command whose output you will read or summarize.

## Choosing the runner

1. If `hagi` is on `PATH`, run `hagi ...`.
2. Otherwise, if `node --version` reports 24 or newer, run `npx @hagicode/cli ...`.
3. If neither is available, say that the CLI cannot run here and why. Continue without inventing data, and do not install Node.js or the CLI unless the user asks.

## Read-only commands

Run these freely to answer questions. Each list or get command is safe to repeat.

### Projects

```bash
hagi project list --json
hagi project repositories --id <project-id> --json
```

`project repositories` lists one project's repositories. Its paths are the only values a proposal's repository scope may name.

### Proposals

```bash
hagi proposal list --json
hagi proposal list --project-id <project-id> --active-only --json
hagi proposal get --session-id <session-id> --json
hagi proposal messages --session-id <session-id> --last 1 --json
```

`proposal get` and `proposal messages` only read. `proposal get --wait` polls the status until it settles and changes nothing.

### Vaults

```bash
hagi vault list --json
hagi vault files list --id <vault-id> --path <relative-dir> --json
hagi vault files preview --id <vault-id> --path <relative-file> --json
```

`vault files preview` reads one file. Preview only the files the user's question needs.

### Chat sessions

```bash
hagi chat list --json
hagi chat list --project-id <project-id> --active-only --json
```

### HagiTasks

```bash
hagi hagitask list --json
hagi hagitask schema --task-id <task-id> --json
hagi hagitask get --session-id <session-id> --json
hagi hagitask messages --session-id <session-id> --last 1 --json
```

Read the schema before creating a HagiTask session. Its `parameters` give the input keys, and `inputSchema` is the JSON Schema the input must satisfy.

### Scheduled plans

```bash
hagi plan list --json
hagi plan get --id <plan-id> --json
```

### Sagas

```bash
hagi saga list --project-id <project-id> --json
hagi saga status <saga-id> --project-id <project-id> --json
hagi saga items <saga-id> --project-id <project-id> --json
```

These queries read the selected project's Saga files without initializing or repairing them, refreshing runtime status,
or executing acceptance commands. Status is a fresh `saga-status/2` observation; its `updatedAt` is not the stored
execution heartbeat in `runtime/status.json`. `init` installs resources and `new` creates a Saga, so run either only
when the user explicitly asks for that change. Contract and lifecycle operations remain with the installed Saga tool.

### Skills

```bash
hagi skills local list --json
hagi skills gallery search --query <keyword> --json
hagi skills gallery detail --id <gallery-id> --source <source> --json
hagi skills trusted list --json
```

`hagi skills local list --json` returns one item per installed skill. Read these fields from each item:

- `origin`: `user` for a skill the user installed, `built-in` for a skill the server ships. An item with no `origin` is a user skill.
- `builtIn.enabled`: whether a built-in skill is on. It is present only for built-in skills. For user skills, availability does not apply.
- `builtIn.version`: the version the release recorded for a built-in skill. It may be absent.
- `managedInstallMetadata.version`: the version of a user skill installed through the gallery, when recorded.

## State-changing commands

Run these only when the user has asked for that action in this conversation.
First name the action and its target (the id, the title or the name), then run it.
A question such as "what is in my plan" is not a request to run, enable, disable or delete it.

| Family | Commands that change state |
| --- | --- |
| `project` | `create`, `update`, `delete` |
| `proposal` | `create`, `optimize-description`, `generate`, `annotate`, `execute`, `archive`, `status`, `complete`, `send` |
| `vault` | `create`, `update`, `delete` (`delete --delete-local-files` also removes files) |
| `chat` | `create`, `archive`, `delete`, `send` |
| `hagitask` | `create`, `send` |
| `plan` | `create`, `update`, `enable`, `disable`, `delete`, `run` |
| `saga` | `init`, `new` |
| `skills` | `local enable`, `local disable`, `local uninstall`, `gallery install`, `trusted upsert`, `trusted delete`, `trusted reset` |

A `send` or `run` starts agent work, and `execute` and `generate` start it too. Treat those as changes of the same kind.

A `send` with Steer (`--steer`, or `HAGI_SEND_STEER` set in the calling shell) inserts its text into a running turn. The result says which happened: `steered` means a running task took it, and `queued` means no running task did, so it went out as the next message. `HAGI_SEND_STEER` belongs to the calling shell; the backend does not set it inside agent sessions.

`hagitask create` with a Super Commit prompt (`--prompt-id auto-compose-commit.<locale>`) creates commits in a code repository, and with `--need-push` publishes them. Start it only when the user asked for it in this conversation, and add `--need-push` only when the user asked for a push. See [`super-commit.md`](super-commit.md).

`skills local enable` and `skills local disable` change whether a built-in skill loads. The change applies to agent runs that start afterwards; a run already in progress keeps its skills. Built-in skills cannot be uninstalled through the CLI.

Before `proposal create`, the proposal's repository scope is settled. Take the writable and read-only repositories from the user's request, or infer them from the session's repository scope when the session states one. When neither gives the scope, ask the user and offer the project's repositories from `project repositories --id <project-id> --json` as the choices. Do not guess the scope, and do not widen the writable list. The scope is written into the chief complaint as a `Repository scope` section; see [`proposal-flow.md`](proposal-flow.md#repository-scope).

When you name the action and its target before running `proposal create`, name its repository scope too.

## Failure handling

| Exit code | Meaning | What to tell the user |
| --- | --- | --- |
| `2` | No base URL, or a usage error | The session did not provide `HAGI_API_BASE_URL`, or the command was malformed. Name the missing piece. |
| `21` / `23` | Unauthorized / forbidden | The backend rejected the request. Report the code; do not try a token. |
| `24` | Not found | Name the id that was not found and suggest a `list` command to find the right one. |
| `30` | Operation failed: the backend refused a change and returned a result with `succeeded` false, for example `skills local enable` or `disable` on a name that is not a built-in skill | Quote the backend message from the output and stop. Nothing changed. |
| `60` | Transport or connection failure | Say the backend is unreachable at the named base URL. Do not retry in a loop, and do not guess another address. |
| other non-zero | HTTP or unknown error | Quote the error message and stop. |

When a command fails, report the failure. Do not fill the gap with guesses about the user's data.
