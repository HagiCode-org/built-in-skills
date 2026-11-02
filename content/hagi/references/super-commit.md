# Super Commit through `hagi`

Use this reference when a user asks to commit the uncommitted changes of a code repository, to publish them, or to explain or check a Super Commit run.

Super Commit commits the uncommitted changes in a code repository. It runs as a separate session, not as part of the proposal lifecycle. It creates commits, and with `--need-push` it also publishes them. Treat it as a state-changing action: start it only when the user asked for it.

For what the archive commit does, and how it differs from Super Commit, see [openspec-workflow.md](openspec-workflow.md#two-kinds-of-commit).

## Start it: a prompt, not a preset task

Super Commit is started with a prompt id:

```bash
hagi hagitask create --title <title> --project-id <project-id> --prompt-id auto-compose-commit.en-US --json
```

Use the locale that matches the user's language in place of `en-US`. The prompt id alone marks the session as a Super Commit.

Super Commit is a prompt, not a preset task. It has no preset task id and no schema, so `hagi hagitask schema` does not apply to it. Do not pass `--task-id` or `--input` for it.

Use the name Super Commit in your explanation to the user. The prompt id appears only inside commands.

## Options

Every option below is accepted by `hagi hagitask create`. The CLI checks these rules before any network call, and a violation is a usage error with exit code `2`.

| Option | Meaning |
| --- | --- |
| `--repository-path <path>` | MonoSpecs sub-repository to commit in, for example `repos/cli`. |
| `--need-push` | Publish the commits after they are created. Add it only when the user asked for a push. |
| `--pull-rebase` | Run `git pull --rebase` before the push. It has effect only with `--need-push`, and only when the run stays on the current branch. |
| `--target-branch-mode <mode>` | Which branch the commits go on. Modes are below. |
| `--target-branch-name <name>` | Name of the branch to create. It needs `--target-branch-mode new-custom`. |

Branch modes:

- `current`: commit on the branch that is checked out now.
- `new-custom`: create the branch named by `--target-branch-name` before the first commit. It needs a name. `--target-branch-name` without this mode is a usage error.
- `ai-generated-new`: create a new branch with a name the backend generates, before the first commit.

## Server-owned choices

The Git identity, the co-author trailer and the sign-off setting come from the user's saved server settings. The CLI has no option for them.

Do not invent a flag for them, and do not put them in `--message`. If the user wants a different co-author for a run, tell them that the CLI has no option for it and ask them to change the saved setting.

## Read the result

After the session settles (see "Who drives each step"), read the final message:

```bash
hagi hagitask messages --session-id <id> --last 1
```

The run ends with a result block:

- `## Commits Created`: every planned commit was made, and the push happened if one was requested.
- `## Commits Incomplete`: at least one commit failed, files were left uncommitted, or a requested push was skipped or failed.

Then read these lines:

- `**Commits:**` the commit count, for example `2`, or `1 of 2` when the run is incomplete.
- `**Push:**` the push outcome, for example `pushed to origin/<branch>`, or `skipped (reason)`.
- A numbered list of the commits, without hashes.

Report the result as it is:

- For `## Commits Created`: report the commit count and, if a push was requested, the push outcome.
- For `## Commits Incomplete`: report what was left undone. Do not say the commit succeeded.
- Retry through `hagi hagitask send --session-id <id> --content <text>` only when the user asks for it.

The result contains no commit hashes. To read them, run `git log` in the target repository.

## Explicit request

Starting a Super Commit creates commits in a repository, and with `--need-push` publishes them. So:

- Start one only when the user asked for it in this conversation.
- Add `--need-push` only when the user asked for a push. If the user asks for a Super Commit and does not mention a push, leave `--need-push` out.
- After `hagi proposal execute` and a settled wait, if code changes remain uncommitted, offer a Super Commit and wait for the user's answer. Do not start one.
- Never start one as a side effect of another lifecycle command.

The web Git tab runs the same feature.

## Who drives each step

| Step | Who |
| --- | --- |
| `hagi hagitask create --prompt-id auto-compose-commit.<locale>` | the agent, only on request |
| The commit work | an AI run inside the backend |
| Following the run | the agent, with `hagi hagitask get --session-id <id> --wait --json` |
| Archiving the finished session | automatic, by the default rule `ai-commit-auto-archive` |

Monitor the run with:

```bash
hagi hagitask get --session-id <id> --wait --json
```

Read the `status` and the `wait` object:

- Optimizing, Openspecing, Executing and Archiving mean the run is still going.
- WaitingForReply means a person must answer.
- A timeout (exit code `31`) is reported with the last status. Do not retry in a loop.

The default rule `ai-commit-auto-archive` archives the finished session automatically. So the agent runs no `archive` or `complete` for a Super Commit session. The rule is a user setting and may be off. Do not assume the session is archived: read `status`, and if the status is not Archived, report it as it is.
