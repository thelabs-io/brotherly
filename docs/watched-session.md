# Brotherly Watch - Spec

> Created: 2026-06-24 - feature branch `feat/watched-session`

## Goal

A "watched session" mode: on the Mac, open a visible Terminal.app window running a
real `claude` session that Chris (on z2) can message over the agent-bbs, and that
can reply and do work - all while Matt watches the live window. This is the
cross-machine, human-visible companion to brotherly's existing approval queue.

This loop's deliverable is the **reusable minimal foundation** for that mode, proven
end-to-end with a machine check plus screenshots. The brotherly TUI approval flow
that triggers it is **out of scope** here (next loop).

## Test target

- Test machine `mm` = the Mac Mini (`chris@mm.lan`, macOS 26.4, on the LAN at
  `192.168.86.44`). `claude` is at `/Users/chris/.local/bin/claude` and supports
  `--session-id <uuid>` (verified 2026-06-24).
- `chris` is logged in at the mm console and `screencapture` is present, so the live
  window is screenshot-able over SSH.
- z2 has a Wayland session with `grim`, so the z2 side is screenshot-able too.

## Architecture (no SSH-key / authorized_keys changes required)

z2 -> mm SSH already works unrestricted. mm -> z2 has no usable general route (the
default key is denied; the brotherly key is `command="brotherly-notify",restrict`).
**Therefore both bridge directions are driven from z2.** The agent-bbs inbox for the
mm session lives on z2; two persistent-SSH streams bridge it to mm:

```
Chris on z2:  inbox-send <uuid> "PING ..."   (writes z2:~/.claude/inbox/<uuid>.jsonl)
   down-bridge (z2):  tail -n0 -F z2:inbox/<uuid>.jsonl | ssh mm "cat >> mm:inbox/<uuid>.jsonl"
   mm claude Monitor: command tail -F mm:inbox/<uuid>.jsonl | command grep -v '"from": "<uuid>"'
       -> agent receives live, does the task, appends reply to mm:outbox/<uuid>.jsonl
   up-bridge (z2):    ssh mm "tail -n0 -F mm:outbox/<uuid>.jsonl" >> z2:inbox/<reply-target>.jsonl
   z2 test/Chris:     sees the reply land in <reply-target> inbox
```

- Deterministic id: z2 generates the UUID and launches `claude --session-id <uuid>`,
  so both sides know the address up front (no register-back round trip).
- The down-bridge's `tail -F` holds the z2 inbox file, so `inbox-send` sees the
  target as **active** (lsof predicate) and just appends - never triggers
  resume-to-deliver. No `--no-resume` needed.
- Raw byte streams via `cat >>` / redirect - no JSON re-escaping across SSH.

## Components (files)

On z2 (kept, in this repo):
- `scripts/brotherly-watch-launch` - generate uuid; prep mm (mkdir inbox/outbox,
  drop a tiny `bbs-reply` helper); open the Mac window; start both bridges; print the
  uuid and the `inbox-send <uuid> "..."` line for Chris.
- `scripts/brotherly-watch-bridge` - the two persistent-SSH bridge streams for a uuid
  (started by launch; also runnable standalone for the transport test).
- `scripts/brotherly-watch-test` - the Tier-1 machine check (sentinel round-trip).

On mm (created per-session under `~/.brotherly/watch/`, no real install):
- `<uuid>.outbox.jsonl` - the agent's reply outbox (up-bridge tails this).
- `bbs-reply` - 3-line helper the agent calls to append a reply line to its outbox.
- mm's local inbox `~/.claude/inbox/<uuid>.jsonl` is fed by the down-bridge.

The Mac launcher (osascript) is piped to mm over SSH (`ssh mm 'bash -s'`), so nothing
persistent is installed on mm.

## Exit condition

**Tier 1 - machine check (`brotherly-watch-test`, drives the loop, pass/fail):**
1. Launch a watched session on mm with a known uuid and a prompt that says: when a
   `PING <token>` arrives, write `/tmp/brotherly-proof-<token>.txt` containing the
   token, then reply `PONG <token>` via `bbs-reply`.
2. From z2, `inbox-send <uuid> "PING <token> ..."` (from a throwaway reply-target id).
3. Within 60s: `PONG <token>` appears in the reply-target inbox on z2 **AND**
   `/tmp/brotherly-proof-<token>.txt` on mm contains `<token>`.
4. Exit 0 on both, 1 otherwise. Script tears down the bridges + window on exit.

**Tier 2 - acceptance demo (screenshots, final human proof):**
- mm: screenshot of the Terminal.app window showing the PING received and the agent
  acting + replying (`ssh mm screencapture -x`).
- z2: screenshot (`grim`) showing the PONG landed.

## Demo-only choices (documented, not for the Matt-facing mode)

- The spawned session runs with broad permissions so it can act unattended on Chris's
  own Mac for the test. The **eventual** Matt-facing mode uses a constrained allowlist
  - that human-in-the-loop approval is brotherly's whole value-add, and is a later loop.

## Out of scope (this loop)

- The brotherly TUI request-type + approval flow that triggers a watched session.
- A purpose-built, command-restricted bridge key for Matt's machine (the test uses
  Chris's existing z2 -> mm access).
- Reconnect/robustness hardening of the bridges beyond what the demo needs.
- Cross-machine clock/retention/delivery guarantees (agent-bbs deferred items).

## Verification (end-to-end)

`scripts/brotherly-watch-test` returns 0, and two screenshots are captured showing the
live exchange on both machines.
