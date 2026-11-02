# OpenSpec workflow behind `hagi proposal`

Use this reference when a user asks what a `hagi proposal` command does on the OpenSpec side, which stage it starts, where it stops, or how to follow a run until it settles.

Source of these facts: `ProposalSessionGrain` in `repos/hagicode-core` (`PCode.Orleans/Grains/ProposalSessionGrain.cs`, `ProposalSessionHandler.cs`) and the `openspec-v1-*` stage prompts (`new`, `explore`, `ff`, `apply`, `archive`). The command descriptions come from `hagi proposal <command> --help`. When these change, update this file.

## Stage map

Each command starts at most one stage. "Does not" lists what the command must not be assumed to do.

| Command | Starts | Does not |
| --- | --- | --- |
| `proposal create` | no stage; creates the session | generate or execute |
| `proposal optimize-description` | no stage; rewrites the title, description and name in one backend step | generate |
| `proposal generate` | planning stages: `new`, then `explore` when explore mode is on, then `ff` | implement, execute or archive |
| `proposal annotate` | no stage; submits review notes, which return the session to planning | execute |
| `proposal execute` | implementation stage: `apply` | archive, or commit code |
| `proposal archive` | archive stage: `archive` | complete the session |
| `proposal complete` | no stage; marks the session completed through its own endpoint | start any stage |
| `proposal status` | no stage; sets the status directly with a read-before-write merge | start any stage |
| `proposal send` | no stage; sends a follow-up message on the active session | start a stage by itself, except as noted under "Who drives each step" |
| `proposal get` | no stage; reads one session, and with `--wait` polls until its status settles | change the session |
| `proposal messages` | no stage; reads the session's messages | change the session |

Explore mode is chosen with `--enable-explore-mode` or `--disable-explore-mode` on `proposal generate`.

A command returning means the request was accepted and the stage was queued. It does not mean the stage finished. Follow the run with `proposal get` (see "Who drives each step").

## Boundaries of each stage

- **Planning** (`generate`) writes the proposal artifacts. It implements no source files. The next step is `annotate` or `execute`, and the user chooses which.
- **Implementation** (`execute`) implements the change. It skips tasks that are not implementation, such as archiving or committing, and reports them as out of scope. It does not archive.
- **Archive** (`archive`) archives the change. It does not implement anything.

No command starts the next stage on its own. An agent that has finished one lifecycle command runs the next command only when the user asked for that step.

## Two kinds of commit

Two different things are called "commit" in this workflow. Neither replaces the other.

- **Archive commit.** The archive stage may make one commit, only in the MonoSpecs repository that holds `openspec/`, and only when the project's option to commit on archive is on. The backend runs it inside the archive stage. It never covers code repositories, and the agent does not run it as a command.
- **Super Commit.** A separate session that commits the uncommitted changes in a code repository. It is started with `hagi hagitask create --prompt-id auto-compose-commit.<locale>`, and the agent starts it only on request. See [super-commit.md](super-commit.md).

After `proposal execute`, the code changes are still uncommitted. The archive commit does not commit them. To commit code, use Super Commit, and only when the user asks.

## Confirm a stage before moving on

1. Take the session id from the command's `--json` output.
2. Pass that same id to the next command.
3. Treat the suggested next command in the output as a suggestion. Do not run it unless the user asked for that step.

The repositories a proposal may change are listed in [Repository scope](proposal-flow.md#repository-scope). Read that section; this file does not restate it.

## Who drives each step

Every step is one of five kinds:

- **Agent-issued command**: the agent runs it, and only when the user asked for that step.
- **AI run inside the backend**: the backend runs an AI agent for the stage. The agent does not run it by hand.
- **Automatic**: the backend moves the status with no command.
- **Needs a person**: the run stops until a person answers or decides.
- **Needs monitoring**: the agent follows the run with `proposal get --wait` and reports the result.

| Step | Kind | Notes |
| --- | --- | --- |
| `proposal create` | agent-issued command | creates the session |
| `proposal optimize-description` | agent-issued command | moves Init to Optimizing |
| Optimizing to Drafting | automatic | when the optimization finishes |
| `proposal generate` | agent-issued command | starts the planning run, an AI run inside the backend |
| Planning run (Openspecing) | AI run inside the backend, needs monitoring | Openspecing |
| Openspecing to Reviewing | automatic | when planning ends |
| `proposal annotate` | agent-issued command | moves Reviewing back to Openspecing |
| `proposal execute` | agent-issued command | moves Reviewing to Executing, and starts the implementation run |
| Implementation run (Executing) | AI run inside the backend, needs monitoring | Executing |
| Run asks a question | needs a person | Executing moves to WaitingForReply |
| A person answers | needs a person | WaitingForReply moves back to Executing |
| Executing to ExecutionCompleted | automatic | when the implementation run ends |
| `proposal archive` | agent-issued command | moves ExecutionCompleted to Archiving |
| Archiving to Archived | automatic | when the archive run ends |
| `proposal complete` | agent-issued command | marks the session completed |
| `proposal status` | agent-issued command | sets the status directly |
| `proposal send` | agent-issued command | on a session in ExecutionCompleted or Completed, it starts a new execution run; see the warning below |
| `proposal get --wait` | needs monitoring | reads the status until it settles |
| `proposal messages` | agent-issued command | reads the messages, for example the final result |

Status moves, and who causes each one:

| From | To | Trigger |
| --- | --- | --- |
| Init | Optimizing | agent runs `optimize-description` |
| Optimizing | Drafting | automatic |
| Drafting | Openspecing | agent runs `generate` |
| Openspecing | Reviewing | automatic when planning ends |
| Reviewing | Openspecing | agent runs `annotate` |
| Reviewing | Executing | agent runs `execute` |
| Executing | WaitingForReply | the run asks a question |
| WaitingForReply | Executing | a person answers |
| Executing | ExecutionCompleted | automatic when the implementation run ends |
| ExecutionCompleted | Archiving | agent runs `archive` |
| ExecutionCompleted | Executing | agent runs `send` (a new execution run) |
| Archiving | Archived | automatic when the archive run ends |

Only the moves labelled with a command are caused by the agent. The rest are caused by the backend, or wait for a person.

### Warnings

- `proposal send` on a session in **ExecutionCompleted** or **Completed** starts a new execution run. Use it only when the user asks to run again.
- `proposal annotate` on a session in **Reviewing** returns it to planning. The session goes back to Openspecing and is planned again. Use it only when the user asks for revisions.

### The monitoring rule

After any start command (`generate`, `execute`, `archive`), follow the run:

```bash
hagi proposal get --session-id <id> --wait --json
```

Read the `status` and the `wait` object in the output:

- **Openspecing, Executing or Archiving**: the run is still going. The wait ends on its own at the timeout.
- **WaitingForReply**: a person must answer. Tell the user; waiting longer does not help.
- **Reviewing, ExecutionCompleted or Archived**: the stage has settled.
- **Timeout (exit code `31`)**: report the last status to the user. Do not retry in a loop.

A returned start command accepts the request. It does not prove the run succeeded. Confirm the outcome from the settled status and, when the result matters, from `proposal messages`.

Other options of the monitoring commands:

- `--timeout <seconds>`, `--interval <seconds>`, `--grace <seconds>`: only with `--wait`. `--interval` must be less than `--timeout`.
- `proposal messages --session-id <id> --last <n>`: reads the n newest messages. `--json` prints the list unchanged.
