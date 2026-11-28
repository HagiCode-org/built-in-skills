# Session Data

Use this reference when an agent runs inside a HagiCode session and the user asks about their own projects, proposals, chat sessions, vaults, scheduled plans or installed skills.
Read-only inspection comes first. Change state only when the user asked for that change in the conversation.

## Runtime variables

A HagiCode session can give you nine variables. Each one is defined here, once:

| Variable | Carries |
| --- | --- |
| `HAGI_API_BASE_URL` | Address of the backend that started the session. `hagi` reads it when no `--base-url` is given. |
| `HAGI_VERSION` | Version of the HagiCode server that started the session. |
| `HAGI_DEPLOYMENT_TYPE` | Deployment type of that server. |
| `HAGI_API_LANG` | The user's effective AI language, `zh-CN` or `en-US`. `hagi` sends it as `Accept-Language`. |
| `HAGI_SESSION_ID` | The HagiCode session ID of this run. It is your own session ID: `hagi saga claim` and `hagi saga session create` use it when `--session` or `--master` is absent. |
| `HAGI_PROJECT_ID` | ID of the project this session belongs to. |
| `HAGI_PROJECT_NAME` | Name of that project. |
| `HAGI_PROJECT_PATH` | Root path of that project on the machine that runs the agent. |
| `HAGI_WORKING_DIRECTORY` | Working directory of this run. |

The server adds them to an agent run whether or not the built-in `hagi` skill is enabled, and whichever agent CLI runs it.
Each variable is added only when the server can determine its value. A value it cannot determine is left out, with a
warning, and the run still starts.

A value the user already set in the environment is kept, not replaced.
The variables carry no secret: never a token, a credential or an API key. `HAGI_PROJECT_PATH` and `HAGI_WORKING_DIRECTORY`
are file system paths, and anyone who can read the session can read them.

OpenCode is the one provider with a different route. An OpenCode server that HagiCode starts receives the session and project
variables for each run, and each session gets its own server. An attached OpenCode server, one that HagiCode did not start,
receives none of these variables, so `HAGI_SESSION_ID` may be absent there: say so and ask the user for the session ID.

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
hagi chat get --session-id <session-id> --json
hagi chat messages --session-id <session-id> --json
```

`chat get` only reads, returning `{ session }` in JSON or the shared human summary. It does not wait or start work. There is no chat `--wait` or `chat answer` command.

### Recovering context in a fresh provider thread

Use the **explicit existing HagiCode session ID** from the continuation instructions, not either provider's thread ID or an assumed `HAGI_SESSION_ID` (user-set environment values are retained). Do not create a replacement session.

```bash
hagi chat get --session-id <session-id> --json
hagi chat messages --session-id <session-id> --json
hagi chat messages --session-id <session-id> --page 2 --page-size 50 --order desc --json
hagi proposal get --session-id <session-id> --json
hagi proposal messages --session-id <session-id> --json
hagi proposal messages --session-id <session-id> --page 2 --page-size 50 --order desc --json
```

Use `chat` for chats and `proposal` for proposals, not both. Recover the task, decisions, latest user instructions, and remaining authorized work before acting. Reuse the existing connection configuration and the runner rules above (`hagi` on PATH, otherwise `npx @hagicode/cli` with Node.js 24+). If a required read fails or the runtime/configuration is absent, report the exact blocker. Never invent context, credentials, or a backend address or install tools as a workaround.

All three message readers (`chat`, `proposal`, `hagitask`) default to page 1, descending, with page size omitted: backend default **50**, maximum **200**. `--page` and `--page-size` must be positive safe integers; `--order` accepts `asc` or `desc`. `--last <n>` requests one descending page subject to the 200-message cap, not complete history, and cannot mix with any explicit paging option. JSON preserves the returned messages and actual `page`, `pageSize`, `totalCount`, and `totalPages`, including clamping. Read further pages only as needed; the CLI does not merge them or promise a snapshot while history changes. `--pending-question` searches only the requested page.

Continue only work already authorized for the current stage and repository scope. If no authorized work remains, report readiness. Do not send a message to this same session, answer a question, or invoke a lifecycle command merely to make yourself continue; recovery reads do not grant new authorization.

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
or executing acceptance commands. Status is a fresh `saga-status/2` observation: its counts and items come from the Saga
files, and its `state` and `note` may come from a valid stored state in `runtime/status.json` (a stored `running` only
when the files also derive `running`). Its `updatedAt` is not the stored execution heartbeat in `runtime/status.json`. `init` installs resources and `new` creates a Saga, so run either only
when the user explicitly asks for that change. Contract and lifecycle operations run through `hagi saga` with the execution token rules in `references/saga.md`.

### Skills

```bash
hagi skills local list --json
```

`hagi skills local list --json` returns one item per installed skill. Read these fields from each item:

- `origin`: `user` for a skill the user installed, `built-in` for a skill the server ships, `self-evolution` for a Self Evolution skill. An item with no `origin` is a user skill.
- `builtIn.enabled`: whether a built-in skill is on. It is present only for built-in skills. For user skills, availability does not apply.
- `builtIn.version`: the version the release recorded for a built-in skill. It may be absent.
- `selfEvolution.enabled`, `selfEvolution.status` and `selfEvolution.version`: present only for Self Evolution skills. `status` is `ready`, `invalid` (not loadable), `conflict` or `flagged`.
- `managedInstallMetadata.version`: the version of a user skill, when recorded.

## State-changing commands

Run these only when the user has asked for that action in this conversation.
First name the action and its target (the id, the title or the name), then run it.
A question such as "what is in my plan" is not a request to run, enable, disable or delete it.

| Family | Commands that change state |
| --- | --- |
| `project` | `create`, `update`, `delete` |
| `proposal` | `create`, `optimize-description`, `generate`, `annotate`, `execute`, `archive`, `status`, `complete`, `send`, `answer` |
| `vault` | `create`, `update`, `delete` (`delete --delete-local-files` also removes files) |
| `chat` | `create`, `archive`, `delete`, `send` |
| `hagitask` | `create`, `send`, `answer` |
| `plan` | `create`, `update`, `enable`, `disable`, `delete`, `run` |
| `saga` | `init`, `new`, `session create` |
| `skills` | `local enable`, `local disable` |

A `send` or `run` starts agent work, and `execute` and `generate` start it too. Treat those as changes of the same kind.

`answer` changes state too: it answers the session's pending question, and the run continues from the answer. Run `proposal answer` or `hagitask answer` only when the user explicitly asks for that answer in the conversation, or when an explicit Saga instruction says to. Never answer a pending question on your own judgment. Reading the question with `messages --pending-question` changes nothing and is always safe.

`saga session create` creates a chat session for a Saga Worker and records it in the Saga's `runtime/sessions.md`. Creating a Worker changes state, so run it only when the user or a Saga run explicitly asks for it. It takes the execution token from `SAGA_EXECUTION_TOKEN` only, and with `--path` it calls the backend to find the project. See [`saga.md`](saga.md#worker-sessions).

A `send` with Steer (`--steer`, or `HAGI_SEND_STEER` set in the calling shell) inserts its text into a running turn. The result says which happened: `steered` means a running task took it, and `queued` means no running task did, so it went out as the next message. `HAGI_SEND_STEER` belongs to the calling shell; the backend does not set it inside agent sessions.

`hagitask create` with a Super Commit prompt (`--prompt-id auto-compose-commit.<locale>`) creates commits in a code repository, and with `--need-push` publishes them. Start it only when the user asked for it in this conversation, and add `--need-push` only when the user asked for a push. See [`super-commit.md`](super-commit.md).

`skills local enable` and `skills local disable` change whether one built-in or Self Evolution skill loads. The change applies to agent runs that start afterwards; a run already in progress keeps its skills. Built-in and Self Evolution skills cannot be uninstalled, edited or deleted through the CLI.

Before `proposal create`, the proposal's repository scope is settled. Take the writable and read-only repositories from the user's request, or infer them from the session's repository scope when the session states one. When neither gives the scope, ask the user and offer the project's repositories from `project repositories --id <project-id> --json` as the choices. Do not guess the scope, and do not widen the writable list. The scope is written into the chief complaint as a `Repository scope` section; see [`proposal-flow.md`](proposal-flow.md#repository-scope).

When you name the action and its target before running `proposal create`, name its repository scope too.

## Failure handling

| Exit code | Meaning | What to tell the user |
| --- | --- | --- |
| `2` | No base URL, or a usage error | The session did not provide `HAGI_API_BASE_URL`, or the command was malformed. Name the missing piece. |
| `21` / `23` | Unauthorized / forbidden | The backend rejected the request. Report the code; do not try a token. |
| `24` | Not found | Name the id that was not found and suggest a `list` command to find the right one. For `answer` and `messages --pending-question`, it also means no question is pending: read the messages again before answering. |
| `35` | Answer refused, by the CLI or the backend | Quote the reason the output names (for example an unknown option or a value too long). Nothing changed. Ask the user for a valid answer; do not retry the same answer. |
| `36` | Question already answered or no longer open | Read the messages again and report the state. Do not answer it again. |
| `30` | Operation failed: the backend refused a change and returned a result with `succeeded` false, for example `skills local enable` or `disable` on a name that is neither a built-in nor a Self Evolution skill | Quote the backend message from the output and stop. Nothing changed. |
| `60` | Transport or connection failure | Say the backend is unreachable at the named base URL. Do not retry in a loop, and do not guess another address. |
| other non-zero | HTTP or unknown error | Quote the error message and stop. |

When a command fails, report the failure. Do not fill the gap with guesses about the user's data.
