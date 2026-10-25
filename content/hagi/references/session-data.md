# Session Data

Use this reference when an agent runs inside a HagiCode session and the user asks about their own projects, proposals, chat sessions, vaults, scheduled plans or installed skills.
Read-only inspection comes first. Change state only when the user asked for that change in the conversation.

## Connection

A HagiCode session sets `HAGI_API_BASE_URL` to the address of the backend that started the session.
Run `hagi` with no `--base-url` flag and no token; the variable is enough.

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
```

### Proposals

```bash
hagi proposal list --json
hagi proposal list --project-id <project-id> --active-only --json
```

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

### Scheduled plans

```bash
hagi plan list --json
hagi plan get --id <plan-id> --json
```

### Skills

```bash
hagi skills local list --json
hagi skills gallery search --query <keyword> --json
hagi skills gallery detail --id <gallery-id> --source <source> --json
hagi skills trusted list --json
```

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
| `autotask` | `create`, `send` |
| `plan` | `create`, `update`, `enable`, `disable`, `delete`, `run` |
| `skills` | `local uninstall`, `gallery install`, `trusted upsert`, `trusted delete`, `trusted reset` |

A `send` or `run` starts agent work, and `execute` and `generate` start it too. Treat those as changes of the same kind.

## Failure handling

| Exit code | Meaning | What to tell the user |
| --- | --- | --- |
| `2` | No base URL, or a usage error | The session did not provide `HAGI_API_BASE_URL`, or the command was malformed. Name the missing piece. |
| `21` / `23` | Unauthorized / forbidden | The backend rejected the request. Report the code; do not try a token. |
| `24` | Not found | Name the id that was not found and suggest a `list` command to find the right one. |
| `60` | Transport or connection failure | Say the backend is unreachable at the named base URL. Do not retry in a loop, and do not guess another address. |
| other non-zero | HTTP or unknown error | Quote the error message and stop. |

When a command fails, report the failure. Do not fill the gap with guesses about the user's data.
