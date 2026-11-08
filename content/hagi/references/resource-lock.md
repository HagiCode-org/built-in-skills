# Resource lock

`hagi agent lock` lets several agents take turns on one shared resource, for example a game server that only one agent may deploy to or test on at a time. The lock is a fair queue held by the backend. It is cooperative: it cannot stop an action that is already running on the remote resource, so every agent has to follow the protocol below.

Every command is `hagi agent lock <verb>`. There is no top-level `hagi lock`. When the package is not installed, replace `hagi` with `npx @hagicode/cli`.

## Numbers

| Number | Value | Meaning |
| --- | --- | --- |
| Feedback timeout | 10 minutes | A holder that sends no heartbeat for 10 minutes loses the lock. Stopping the heartbeat alone releases the lock after this time. |
| Maximum hold | 24 hours | Absolute, counted from the grant. The lock is taken back at the cap even when heartbeats keep arriving. |
| Heartbeat interval | 2 minutes (120 s) | How often `heartbeat` renews. One lost beat is survivable. |
| Claim window | 30 seconds | After a handoff the new holder must confirm (status, renew or acquire) within 30 s, or the lock moves on. A watcher confirms at once. |
| Waiter TTL | 60 seconds | A queued owner that is not polling for 60 s is dropped from the queue. |
| Default wait timeout | 900 seconds | `acquire --wait` gives up after this long. Change it with `--timeout <seconds>`. |

`--lease-seconds` can request a shorter feedback timeout (30 to 600 seconds, never more than 10 minutes).

## Addressing and owner

- Name the lock with `--lock-id <id>` (for example `eu-1/duckov`) or with the pair `--server <name> --game <name>`, which means `<server>/<game>`. Do not mix the two forms.
- The owner is **your own session ID**: pass it as `--owner <id>`, for example `--owner sess-7f2c`. When `--owner` is absent the CLI reads `HAGI_LOCK_OWNER`, then `HAGI_SESSION_ID`. With none of the three it exits `2` and makes no request. The CLI never invents an owner ID.
- Use the same owner ID for every command about one lock. Two agents that share one owner ID act as one owner, and nothing detects that.

```bash
hagi agent lock acquire --lock-id eu-1/duckov --owner sess-7f2c
hagi agent lock acquire --server eu-1 --game duckov --owner sess-7f2c --label "deploy test build" --json
```

## Commands

| Command | Use |
| --- | --- |
| `hagi agent lock acquire` | Take the lock or join the queue. Without `--wait` it is one call and exits `0` for both `Holding` and `Queued`. With `--wait` it waits for the turn and exits `0` only when you hold the lock. It has no force option. Options: `--wait`, `--timeout <seconds>`, `--lease-seconds <n>`, `--label <text>`. |
| `hagi agent lock status` | Read your own state: `Holding`, `Queued`, `Expired`, `Requisitioned` or `None`. Exit `0` for all of them. `--wait-seconds <n>` is a long poll (the server caps it at 25). |
| `hagi agent lock heartbeat` | Keep a held lock alive. Long-running and quiet on success; run it under a watcher. Options: `--epoch <n>`, `--interval <seconds>`, `--lease-seconds <n>`, `--verbose`. |
| `hagi agent lock renew` | One renewal, a single heartbeat. Prefer `heartbeat`. Options: `--epoch <n>`, `--lease-seconds <n>`. |
| `hagi agent lock release` | Give the lock back or leave the queue. Exit `0` whether or not something was released. Option: `--epoch <n>`. |
| `hagi agent lock requisition` | Emergency take that displaces the holder. Only on an explicit user order (rules 6 and 7). Requires `--reason <text>`; option `--label <text>`. |
| `hagi agent lock list` | List locks that have a holder or a queue. Option: `--prefix <text>`. |

Every command except `list` also takes `--lock-id`, `--server`, `--game` and `--owner`; all seven take the shared `--json` option. The answers carry the expected-time windows: when the lock is valid until, the hard cap, the check-in window and, for a queued owner, the turn window. Times are server times; they are guidance for when to expect something, not wake-up schedules. An epoch identifies one grant; the `acquire` answer prints it, and `heartbeat` reads it itself when `--epoch` is omitted.

## Exit codes

| Exit code | Meaning |
| --- | --- |
| `0` | Success. For `acquire --wait`: you hold the lock (your turn). For `heartbeat`: it was stopped by SIGINT or SIGTERM (the lock is not released). |
| `2` | Usage error: missing owner, conflicting lock addressing, a bad number, `--timeout` without `--wait`. No request was sent. |
| `20` / `21` / `23` / `24` / `29` | Backend refusal: invalid argument (for example a bad lock ID, owner or reason), unauthenticated, permission denied, not found, conflict. |
| `30` | `acquire --wait` was interrupted (the queue entry is released), or the backend refused the operation. |
| `31` | Wait timeout: `acquire --wait` reached `--timeout` without the turn. The queue entry it created was released. |
| `32` | `LOCK_LOST`: the lock is no longer yours (lease expired, taken back at the 24-hour cap, stale epoch, not the holder, or requisitioned). Stop using the resource at once. Distinct from `31`. Printed by `heartbeat`, `renew`, and by `acquire --wait` when the queue entry was dropped. |
| `40` / `50` | Other HTTP 4xx / HTTP 5xx equivalent. |
| `60` | Transport failure. A watcher retries these itself and never treats them as loss. |
| `70` | Unknown error. |

## The watcher protocol

A watcher is a long-running command whose output lines reach you as notifications. Use a Monitor that runs the command. Where there is no Monitor, run the same command as a background process whose output you read, or in a background sub-agent that reports back. State the rule in terms of what the watcher must do; the provider's tool is a detail.

### 1. Acquire, read the windows, start the heartbeat watcher

```bash
hagi agent lock acquire --lock-id eu-1/duckov --owner sess-7f2c --label "deploy test build"
```

Read the status and the windows in the answer.

- `Holding`: start the heartbeat watcher **before any work**, and keep it running while you use the resource.

  ```bash
  hagi agent lock heartbeat --lock-id eu-1/duckov --owner sess-7f2c --epoch 7
  ```

  It beats at once, then every 2 minutes. It prints one start line, then nothing while all is well. It prints a line, and exits `32`, when the lock is lost. It warns once when the backend has been unreachable for over 60 seconds and again on recovery, says "may already be lost" when the lease deadline passed during an outage, and warns 30 minutes and 5 minutes before the 24-hour cap. `--verbose` adds one line per beat. A transport error is never reported as loss.
- `Queued`: start a continuous wait watcher and carry on with other work, or stop. Do not sleep until the window and then check.

  ```bash
  hagi agent lock acquire --lock-id eu-1/duckov --owner sess-7f2c --wait
  ```

  It prints one line when your position changes, and exits `0` when the turn comes (start the heartbeat watcher then), `31` on timeout (default 900 s), `32` if the entry was dropped. Pass `--timeout <seconds>` for a different limit.

### 2. Finish: stop the heartbeat, then release

When all tasks are done, stop the heartbeat watcher, then release:

```bash
hagi agent lock release --lock-id eu-1/duckov --owner sess-7f2c --epoch 7
```

Stopping the heartbeat watcher (SIGINT or SIGTERM) exits `0` and does not release. Stopping alone also ends the hold, because the backend releases the lock after 10 minutes without feedback, but `release` hands the resource over at once.

### 3. Loss and recovery

When a watcher reports that the lock was lost, stop using the resource immediately. Retrying does not extend the 24-hour cap or the 10-minute timeout.

When you lose track of whether you hold the lock (for example after your context was compacted), run `acquire` again with the same owner. It is safe: the first acquire stays valid (same epoch, same 24-hour clock) and the answer gives the windows. It does **not** refresh the lease, so it is not a heartbeat. Then check that the heartbeat watcher is running, and start it if it is not.

## The seven rules for the agent

1. After an `acquire`, read the windows in the answer. If the status is `Holding`, start the heartbeat watcher (a Monitor running `hagi agent lock heartbeat ...`) before doing any work. Where Monitor is not available, run the same command as a background process or in a background sub-agent whose output you read.
2. If the status is `Queued`, start a continuous wait watcher (a Monitor, or a sub-agent, running `hagi agent lock acquire --wait ...`) and carry on with other work or stop. Do not sleep until the window and then check: the waiter TTL (60 s) would drop your queue entry and the claim window (30 s) would take back a handoff nobody noticed. The window is a guide to when to expect the turn, not a wake-up schedule.
3. When all tasks are done, stop the heartbeat watcher and then release the lock. Stopping the heartbeat alone is enough, because the backend releases the lock after 10 minutes without feedback, but `release` hands the resource over at once.
4. When a watcher reports that the lock was lost, stop using the resource immediately. The 24-hour cap and the 10-minute timeout are not extended by retrying.
5. If you lose track of whether you hold a lock (for example after your context is compacted), call `acquire` again with the same owner: it is safe, and the answer gives the windows. Then check that the heartbeat watcher is running.
6. Never requisition unless the user has explicitly told you to force-take the lock. Your own judgment that something is urgent is not enough, and nothing is a requisition without an explicit user order. In every other case, call `acquire` and wait in the queue.
7. When the user does order a requisition, run `requisition` with a reason that quotes the request, start the heartbeat watcher, and tell the user which owner was displaced. When you are the one displaced, stop using the resource immediately, tell the user, queue again only if your task still needs the resource, and never requisition back.

## Requisition

`requisition` takes the lock at once. It is its own command; `acquire` has no force option and `acquire --wait` never requisitions.

```bash
hagi agent lock requisition --lock-id eu-1/duckov --owner sess-7f2c --reason "User order: 'take the duckov lock now, the demo starts in five minutes'"
```

- Run it only after the user has explicitly ordered a forced take (rule 6). Quote the order in `--reason` (1 to 200 characters). The displaced agent is shown the reason and the backend logs it.
- The answer prints the new epoch, the valid-until time and the windows. Start the heartbeat watcher at once (rule 7), then tell the user which owner was displaced.
- If you already hold the lock, nothing changes. Waiters keep their order. The displaced owner is not queued again.
- When you are displaced, your next heartbeat prints the requester, the time and the reason, and exits `32`. A status read shows `Requisitioned` for 10 minutes, then `None`. Stop at once, tell the user, queue again with `acquire` only if the task still needs the resource, and never requisition back.
- A displaced agent may keep using the resource until its next heartbeat, up to 2 minutes. The lock cannot stop work that is already running on the remote resource.

## Failure handling

| Situation | What happens |
| --- | --- |
| Holder crashes, or stops its heartbeat without releasing | After 10 minutes the lock goes to the head of the queue; the old owner reads `Expired`. |
| You never started a heartbeat watcher | The lock is released after 10 minutes; your next check-in reports loss. |
| The heartbeat watcher dies while you live | Same as above. Check the watcher after a long step. |
| The backend is unreachable | The heartbeat retries with 1 to 10 s backoff and warns after 60 s. It never reports loss by itself; the 10-minute timeout bounds the damage. |
| You sleep instead of watching in the queue | The waiter TTL (60 s) removes your entry; the next call reads `Expired` and you queue again at the back. |
| A slow old holder acts after being replaced | The epoch makes its renew and release fail; the new holder is unaffected. |
