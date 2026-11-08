# Local Development

This document is maintainer-only.
Use it when you are editing or validating the CLI source tree inside `repos/cli`.
Normal users should stay on the published package path.

## Working directory rule

Always change into `repos/cli` before running install, build, or test commands.
Do not run npm commands at the monorepo root.

```bash
cd repos/cli
```

## Development modes

### Source-level development

Use the TypeScript entrypoint directly while changing behavior:

```bash
cd repos/cli
pnpm run dev proposal list --json
pnpm run dev chat list --json
```

### Release-style verification

Build the local distribution and run the bundled CLI:

```bash
cd repos/cli
pnpm run build
node ./dist/cli.js --help
node ./dist/cli.js proposal --help
```

## Repository map

Inspect these areas when implementation details matter:

- `src/commands/` - command registration, flags, and request shaping
- `src/runtime/` - API runtime, shared context, and error handling
- `src/formatters/` - human-readable and JSON output formatting
- `buildTools/` - gRPC stub generation and DTO type generation scripts
- `scripts/verify-package.mjs` - publish-surface verification

## API client generation

The CLI calls the backend over gRPC-Web (`<base-url>/grpc`). The stubs in `src/generated/grpc` come from the proto contracts in `repos/hagicode-core/protos`.
Use these commands when a proto changes:

```bash
cd repos/cli
pnpm run generate:grpc
pnpm run generate:grpc:check
```

`HAGICODE_PROTO_DIR` points generation at another checkout of the protos.

The DTO types in `src/generated/api/models` are committed and maintained by hand (types only, no REST client). They are no longer
generated: the backend's OpenAPI document now lists only the retained REST routes, so regenerating from it would delete the
types of every removed route. When a proto DTO changes, edit or add the matching type there.

## Saga asset bundle

The Saga resources are owned by this repository. `resources/saga/` contains the six method prompt files,
`install/gitignore.template`, and `manifest.json`; there is no standalone Saga tool and no sync step. Keep the bytes raw:
do not render templates or normalize line endings. The manifest uses schema version `2` with two maps: `install` lists
`install/gitignore.template`, and `methods` maps each method name (`goal`, `research`, `acceptance`, `plan`, `run`,
`amend`) to the digest of `prompts/<name>.md`. Paths are sorted POSIX relative paths and every digest is lowercase
SHA-256. The manifest does not hash itself. Only that template is installed into a project, as `.hagicode/sagas/.gitignore`;
the methods are read from the package with `hagi saga method`.

The template must not be named `.gitignore` inside the package: npm renames a packaged `.gitignore` to `.npmignore` on
install, so the rule would be missing from the installed CLI. `tests/runtime/saga/assets.test.ts` fails if a dot-named
ignore file appears in the bundle.

After editing a prompt, update its digest in `manifest.json`. `tests/runtime/saga/assets.test.ts` fails on any mismatch
between the files and the manifest, and `pnpm run pack:check` verifies the published contents.

## Release automation

GitHub workflows under `.github/workflows/` handle release drafting and npm publishing.
For a stable release dry run, use:

```bash
cd repos/cli
version="$(pnpm run --silent publish:verify-release -- v0.1.0)"
npm version --no-git-tag-version "$version"
pnpm run build
pnpm run typecheck
pnpm test
pnpm run pack:check
```
