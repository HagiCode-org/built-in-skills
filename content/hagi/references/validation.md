# Validation

Run the smallest relevant set after changes.
Documentation-only updates do not require the full code validation stack, but cross-links and package metadata assumptions still need confirmation.

## Documentation and skill checks

Confirm these paths resolve and link correctly:

- `repos/cli/README.md`
- `repos/cli/skills/README.md`
- `repos/cli/skills/hagi/SKILL.md`
- `repos/cli/skills/hagi/agents/openai.yaml`
- `repos/cli/skills/hagi/references/*.md`

Check that every command named in the references is registered: the `hagi` help output after a build lists the same families and subcommands.

## Maintainer validation commands

When command behavior, metadata, or packaging changes are involved, run the smallest relevant subset:

```bash
cd repos/cli
npm run build
npm run typecheck
npm test
node ./dist/cli.js --help
node ./dist/cli.js proposal --help
```

If only a specific command changed, also verify that command's help directly.

## Package publish-surface check

Run this only when `package.json`, publish contents, or release metadata changed:

```bash
cd repos/cli
npm run pack:check
```

The npm tarball ships `dist` and `README.md` only (`package.json` `files`), so `skills/**` is not in the package. The skill reaches users through the repository and the server's built-in skill copy, not through npm. Change `files` only if that decision changes.
