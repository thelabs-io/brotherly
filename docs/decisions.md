# Technical Decisions

## ADR-001: Textual for TUI

**Decision:** Use Textual (Python) for the terminal UI.

**Rationale:** Rich, modern TUI framework with CSS-like styling. Produces beautiful interfaces with minimal code. Good documentation and active development.

## ADR-002: JSON Queue Files

**Decision:** Use individual JSON files per queued task rather than a database.

**Rationale:** Simple, inspectable, no dependencies. Easy to debug by looking at files directly. Queue volume is extremely low (maybe a few tasks per week).

## ADR-003: SSH-based Notifications

**Decision:** Notify Chris by SSHing from Matt's machine to z2 and running local commands.

**Rationale:** Chris already has SSH access configured between the machines. Using `send-sms` and `notify-send` on z2 leverages existing infrastructure rather than building new notification channels.

## ADR-004: No Root Access for Chris

**Decision:** Chris operates without sudo/root on Matt's machine. All privileged operations go through the approval queue.

**Rationale:** Trust and transparency. Matt can see exactly what will run before it executes. Chris can't access Matt's personal files.
