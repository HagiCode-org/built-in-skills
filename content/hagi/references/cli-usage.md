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
hagi chat list --json
hagi autotask create --title "Auto commit" --project-id <project-id> --prompt-id auto-compose-commit.en-US
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

## Environment variables

The CLI resolves runtime settings centrally before every command.
Explicit flags always override environment variables.

| Variable | Purpose |
| --- | --- |
| `HAGI_API_BASE_URL` | Backend base URL, used when `--base-url` is not given. Overrides the config file. |
| `HAGI_API_TOKEN` | Bearer token attached as `Authorization: Bearer <token>`. |
| `HAGI_API_LANG` | Shared `Accept-Language` header value. |

## Config file

The base URL can also be stored in a local config file:

```json
{ "baseUrl": "https://api.example.com" }
```

The file is `$XDG_CONFIG_HOME/hagi/config.json`, or `~/.config/hagi/config.json` when `XDG_CONFIG_HOME` is unset.

Base URL precedence, highest first: `--base-url`, then `HAGI_API_BASE_URL`, then `baseUrl` in the config file.
There is no default. When none of the three is set, the CLI exits with code `2` and names all three sources.

## Command overview

```text
hagi
|-- project   list | create | update | delete
|-- proposal  list | create | optimize-description | generate | annotate | execute | archive | status | complete | send
|-- vault     list | create | update | delete
|   `-- files list | preview
|-- chat      list | create | archive | delete | send
|-- autotask  create | send
|-- plan      list | get | create | update | enable | disable | delete | run
`-- skills    local list | uninstall
              gallery search | detail | install
              trusted list | upsert | delete | reset
```

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

## Exit codes

Stable non-zero exits used by the CLI:

| Exit code | Meaning |
| --- | --- |
| `2` | CLI usage or validation failure |
| `20` | HTTP 400 |
| `21` | HTTP 401 |
| `23` | HTTP 403 |
| `24` | HTTP 404 |
| `29` | HTTP 409 |
| `40` | Other HTTP 4xx |
| `50` | HTTP 5xx |
| `60` | Transport or connection failure |
| `70` | Unknown error |
