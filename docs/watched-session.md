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
  `--session-id <uuid>` (verified 2026-06-24). NOTE: `claude` is on PATH only via an
  INTERACTIVE shell (`zsh -ic`) - it lives in `~/.local/bin`, added by `.zshrc`.
- `chris` is logged in at the mm console. `screencapture` over SSH FAILS
  (`could not create image from display`) - an SSH context has no GUI display - so mm
  captures must run INSIDE the GUI session: either the watched session screencapturing
  its own Terminal, or a `.command` opened via `/usr/bin/open`. Terminal also needs a
  one-time Screen Recording (TCC) grant (granted 2026-06-25).
- z2 runs GNOME 50 / Wayland, where `grim` does NOT work (it needs the wlroots
  screencopy protocol, absent in Mutter) and `org.gnome.Shell.Screenshot` is locked
  down. The z2 side is captured via the xdg-desktop-portal Screenshot API
  (`scripts/brotherly-screenshot-z2`, which falls back to `grim` on wlroots).

## Prerequisite: claude auth on mm

`claude` on mm must be authenticated with the **Max subscription** (never the metered
API). One-time setup: run `claude setup-token` on mm and save the printed token to
`~/.brotherly/watch/oauth-token` (mode 600). The generated `run.command` exports it as
`CLAUDE_CODE_OAUTH_TOKEN`; the launcher refuses to start if the file is absent. A
long-lived token (vs copying z2's `credentials.json`) avoids refresh-token rotation
conflicts between the two always-on machines.

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
- `scripts/brotherly-watch-test` - the Tier-1 machine check (sentinel round-trip);
  also captures best-effort tier-2 demo screenshots of both machines.
- `scripts/brotherly-watch-stop` - teardown for a uuid (bridge + mm window + files).
- `scripts/brotherly-screenshot-z2` - best-effort z2 desktop capture for the demo
  (xdg-desktop-portal on GNOME/Wayland; `grim` fallback on wlroots).

On mm (created per-session under `~/.brotherly/watch/`, no real install):
- `<uuid>.outbox.jsonl` - the agent's reply outbox (up-bridge tails this).
- `bbs-reply` - 3-line helper the agent calls to append a reply line to its outbox.
- mm's local inbox `~/.claude/inbox/<uuid>.jsonl` is fed by the down-bridge.

The Mac window is opened with `/usr/bin/open <uuid>-run.command` (a generated `.command`
scp'd to mm) - NOT osascript/AppleEvents, which Terminal blocks under TCC (AppleEvent
timeout -1712). Only small per-session files are dropped on mm; nothing persistent is
installed.

## Exit condition

**Tier 1 - machine check (`brotherly-watch-test`, drives the loop, pass/fail):**
1. Launch a watched session on mm with a known uuid and a prompt that says: when a
   `PING <token>` arrives, write `/tmp/brotherly-proof-<token>.txt` containing the
   token, then reply `PONG <token>` via `bbs-reply`.
2. From z2, `inbox-send <uuid> "PING <token> ..."` (from a throwaway reply-target id).
3. Within 60s: `PONG <token>` appears in the reply-target inbox on z2 **AND**
   `/tmp/brotherly-proof-<token>.txt` on mm contains `<token>`.
4. Exit 0 on both, 1 otherwise. Script tears down the bridges + window on exit.

**Tier 2 - acceptance demo (screenshots, final human proof) - DONE 2026-06-25:**
- mm: the watched session screencaptures its OWN Terminal window (on `CAPTURE <token>`
  it runs `/usr/sbin/screencapture`); the test pulls the PNG back to z2. `ssh mm
  screencapture` can't be used - an SSH context has no GUI display.
- z2: `scripts/brotherly-screenshot-z2` (xdg-desktop-portal; `grim` fallback).
- `brotherly-watch-test` captures both as a best-effort step that never gates pass/fail;
  shots land in `~/.brotherly/watch/shots/`.

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
