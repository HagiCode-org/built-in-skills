# Saga commands

Saga files are project-local. Select exactly one project with `--path <directory>` or `--project-id <id>` for every
Saga command. A local `--path` is resolved on the CLI host and does not read backend configuration or make API calls.

## Initialize managed resources

Run `init` before creating a Saga:

```bash
hagi saga init --path "./My Project"
hagi saga init --path "./My Project" --force --json
```

Initialization installs the bundled prompts, Saga tool, and ignore template under `.hagicode/sagas`. It does not repair
or overwrite existing Saga contracts, metadata, or runtime records.

By default, differing managed resources are preserved as conflicts while missing nonconflicting resources are still
installed. The command prints each file's `created`, `unchanged`, `merged`, `replaced`, or `conflict` outcome and exits
with code `4` if any conflicts remain. Use `--force` to replace differing managed resources with the bundled versions;
identical resources remain untouched. Forced initialization never discards custom `.gitignore` entries.

The `.gitignore` rule `*/runtime/` is merged as a separate exact line. Existing bytes, line endings, and entries are
preserved; LF and CRLF files are supported, and repeated initialization does not append duplicate rules.

Before writing, initialization checks that managed directories and files are not redirected, that resource targets are
regular files, and that writes will not replace unsafe hard-linked resources. Refused targets are reported as operation
failures rather than followed outside the selected project. Exact resources are not rewritten on repeat runs, preserving
their modes and modification times.

With `--json`, stdout contains the installation root, `force` setting, per-file `path`/`outcome` entries, and any
conflicts. A conflict report is still emitted before the command reports the code-4 error on stderr.

## Create and inspect Sagas

After initialization, `new <saga-id>` invokes the installed canonical Saga tool. IDs must match
`^[a-z0-9][a-z0-9-]{0,62}$`: one to 63 lowercase letters, digits, or hyphens, beginning with a letter or digit. The
reserved names are `prompts`, `tools`, `archive`, `runtime`, `amendments`, and `revisions`. Invalid IDs are usage errors
(code `2`). An existing active path or an archive entry whose name ends in `-<saga-id>` is a collision; creation is
refused with code `30` and neither Saga is changed.

The `--json` result identifies the Saga directory and includes the metadata written by the canonical tool; child human
output is not embedded:

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

The human result shows the next prompt command. From the project root, it has this form:

```bash
node .hagicode/sagas/tools/saga.mjs instructions demo goal
```

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
unreadable existing data is reported instead of being repaired. The CLI owns initialization, canonical creation, and
these queries only. Contract validation, lifecycle mutations, and Saga execution remain owned by the installed project
tool and HagiTask preset.
