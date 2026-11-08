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

## Repository scope rule check

The repository scope rule for `proposal create` must appear in three files. Each one is checked on its own, and one file that still has the rule does not stand in for another:

- `SKILL.md` carries the core rule: the writable and read-only lists, and the `project repositories` query.
- `references/proposal-flow.md` carries the `Repository scope` section: the query step, the `Writable repositories:` and `Read-only repositories:` lists, and the example that begins its chief complaint with that section.
- `references/session-data.md` carries the state-changing rule: the scope is taken from the user or the session, and the agent asks when neither gives it instead of guessing.

Run this from `repos/cli` after editing any of the three:

```bash
grep -n "Repository scope" skills/hagi/SKILL.md skills/hagi/references/proposal-flow.md
grep -n "Read-only repositories" skills/hagi/SKILL.md skills/hagi/references/proposal-flow.md
grep -n "project repositories" skills/hagi/SKILL.md skills/hagi/references/proposal-flow.md skills/hagi/references/session-data.md
grep -n "ask the user" skills/hagi/SKILL.md skills/hagi/references/proposal-flow.md skills/hagi/references/session-data.md
```

Each of the three files must match the lines listed for it above. A file that is missing a match fails the check, and it is fixed in the skill folder, not by copying the rule from another file.

Confirm also that no skill file names `--writable-repo` or `--readonly-repo`, and that every `proposal create` example passes a chief complaint that begins with the `Repository scope` section.

## HagiTask command check

The `hagitask` command group must appear in the README and in each skill file that lists command families, and no file may document the retired `autotask` command. Run this from `repos/cli`:

```bash
for f in README.md skills/hagi/SKILL.md skills/hagi/references/cli-usage.md skills/hagi/references/session-data.md skills/hagi/references/super-commit.md skills/hagi/references/openspec-workflow.md; do
  grep -q "hagitask" "$f" && echo "ok   hagitask in $f" || echo "FAIL hagitask missing from $f"
done
grep -rniE "autotask|auto-task" README.md skills --exclude=validation.md | grep -vi "migrat" || echo "ok   no autotask command documented"
```

Each file must print `ok`. The last grep lists only the migration notes (lines that say "migrat"), so any other match is a stale `autotask` reference and fails the check. This file is excluded from that grep because it names the pattern itself.

## Workflow and Super Commit check

Run this from `repos/cli` after editing `references/openspec-workflow.md`, `references/super-commit.md`, or any file that links them. Each line must print `ok`.

1. Both references exist and are linked from `SKILL.md` and `skills/README.md`:

```bash
for f in skills/hagi/references/openspec-workflow.md skills/hagi/references/super-commit.md; do
  [ -f "$f" ] && echo "ok   exists $f" || echo "FAIL missing $f"
done
for f in skills/hagi/SKILL.md skills/README.md; do
  for t in openspec-workflow.md super-commit.md; do
    grep -q "$t" "$f" && echo "ok   $f links $t" || echo "FAIL $f does not link $t"
  done
done
```

2. No README or skill file shows the retired `--task-id compose-commit` form. This check does not scan this file, which names the pattern itself. The id may remain as test data in `tests/commands/hagitask.test.ts`, the one allowed place, and that file is outside this scan:

```bash
grep -rn --exclude=validation.md -e "--task-id compose-commit" README.md skills
status=$?
if [ "$status" -eq 0 ]; then
  echo "FAIL retired compose-commit example found above"
elif [ "$status" -eq 1 ]; then
  echo "ok   no --task-id compose-commit in README.md or skills"
else
  echo "FAIL grep could not run"
fi
```

3. Every option the two references name is registered in the built CLI. Build first (`pnpm run build`), then run:

```bash
check() {
  local command="$1"; shift
  for option in "$@"; do
    node ./dist/cli.js $command --help | grep -q -- "$option" && echo "ok   $command $option" || echo "FAIL $command $option is missing"
  done
}
check "proposal get" --session-id --wait --timeout --interval --grace --json
check "proposal messages" --session-id --last --json
check "hagitask get" --session-id --wait --timeout --interval --grace --json
check "hagitask messages" --session-id --last --json
check "hagitask create" --prompt-id --repository-path --need-push --pull-rebase --target-branch-mode --target-branch-name
```

4. Both references have a "Who drives each step" section and both name `--wait`. Each count must be at least `1`:

```bash
grep -c "Who drives each step" skills/hagi/references/openspec-workflow.md skills/hagi/references/super-commit.md
grep -l -- "--wait" skills/hagi/references/openspec-workflow.md skills/hagi/references/super-commit.md
```

## Built-in copy consistency check

The embedded skill exists twice: `repos/cli/skills/hagi` is the only place it is edited, and `repos/built-in-skills/content/hagi` is the copy the server ships as the built-in `hagi` skill. Run this from the monorepo root to confirm the two match:

```bash
diff -r repos/cli/skills/hagi repos/built-in-skills/content/hagi
```

The expected result is no output, which means the folders are identical. Any output names a file that differs, is missing from one side, or is extra on one side.

- If the check reports a difference, fix it by editing only `repos/cli/skills/hagi`. Never edit the bundle copy by hand.
- Refreshing the bundle copy and its content hash is a separate follow-up in the bundle repository. It is not part of a CLI change, and a skill change leaves the check reporting differences until that follow-up runs.
- After the repository scope edit, the bundle copy must be recopied from `repos/cli/skills/hagi` and its hash refreshed. Doing that needs write access to `repos/built-in-skills`. Until then, sessions that load the built-in `hagi` skill run the older text, with no `project repositories` guidance.
- In a standalone CLI checkout the bundle is not beside the CLI. Replace `repos/built-in-skills/content/hagi` with the path to the `content/hagi` folder of a checked-out built-in skills bundle, for example `<path-to-built-in-skills>/content/hagi`.

## Maintainer validation commands

When command behavior, metadata, or packaging changes are involved, run the smallest relevant subset:

```bash
cd repos/cli
pnpm run build
pnpm run typecheck
pnpm test
node ./dist/cli.js --help
node ./dist/cli.js proposal --help
```

If only a specific command changed, also verify that command's help directly.

## Saga Worker session command

Run this when `src/commands/saga/session.ts`, the Saga runtime helpers (`project.ts`, `safeWrite.ts`, `sessionRecord.ts`),
the run prompt or these references changed:

```bash
cd repos/cli
pnpm exec vitest run tests/commands/saga-session-create.test.ts tests/runtime/saga/appendContained.test.ts tests/runtime/saga/project.test.ts tests/runtime/saga/sessionRecord.test.ts
pnpm exec vitest run tests/runtime/saga/assets.test.ts tests/docs
node ./dist/cli.js saga session create --help
```

The command test covers argument validation, token rejection, selector matching, the `saga.*` metadata, the `sessions.md`
append and the failed-record report. The help check prints the parameters, the metadata keys and the metadata limits.

## Package publish-surface check

Run this when `package.json`, publish contents, or release metadata changed. The Saga asset check and the package check
are offline:

```bash
cd repos/cli
pnpm exec vitest run tests/runtime/saga/assets.test.ts
pnpm run pack:check
```

The npm tarball ships `dist`, `README.md`, `skills/**`, and only
the allowlisted Saga resources, including the `install/gitignore.template` file that becomes `.gitignore` in a project. `pack:check` verifies the actual package
contents and rejects source maps or unexpected resource files.
