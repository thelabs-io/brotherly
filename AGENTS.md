# Agent Instructions

## For Local Agents with Access to Coderoo MCP Tools

**It is crucial to start each session with: `mcp__coderoo__start_session()` using the correct arguments.**
Read the conditions below **very carefully**. Starting the session with the wrong `agent` or `role` specified can be **CATASTROPHIC**.

**agent** and/or **role**
- If you are not explicitly told to use a specific value for "agent" or "role", use "orchestrator" as the `role`.
- If the user instructs you to start the session "as" a role, use that for the `role` argument value.

**agent_runtime**
- If you are operating within an agentic programming CLI client (Claude Code, Codex, Copilot CLI, Cursor Agent CLI, or Gemini) specify the appropriate name as the `agent_runtime` value. The value can be one of these:
  - claude
  - codex
  - copilot
  - cursor
  - gemini

Your `start_session` call will look like this:
```
mcp__coderoo__start_session(
    project_path: "/storage/Projects/brotherly",
    agent_runtime: "<cli_client_name | api_name>",
    role: "<role>",
    task: "<task_name_if_mentioned>"
)
```

## For Cloud Agents Without Access to Coderoo MCP Tools

Instead of `start_session`, run `echo $START_SESSION` for instructions on how to proceed.

## Important Memories

- Use `get_instructions` on demand for special conditions. Keep the names of available instruction sets in mind so that you know when to request them.
- **NEVER** call `task_get` or read the task description directly after calling `start_session` with a `task` provided. The `start_session` response contains all task info already, so getting the task or reading its description is a waste of tokens!

## Project-Specific Notes

- **Target platform:** macOS (M4 Mac Mini) for TUI, Arch Linux (z2) for notifications
- **TUI framework:** Textual (Python)
- **Queue format:** JSON files in `~/.brotherly/queue/`
- **Notifications:** SSH to z2 (`zara2stra.duckdns.org:22440`) for SMS + GNOME notifications
- **Key constraint:** Chris has no sudo access on Matt's machine - all privileged operations go through Matt's approval

## Testing

**Test Commands:**
```bash
pytest tests/ -v
```
