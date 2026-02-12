"""Script header parser — extracts title and description from comment blocks."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ScriptHeader:
    """Parsed metadata from a script's comment header."""

    title: str
    description: str
    body_start_line: int  # first line of actual code (0-indexed)


def parse_script_header(script_path: Path) -> ScriptHeader:
    """Parse title and description from a script's leading comment block.

    Format:
        #!/bin/bash
        # Title goes here
        #
        # Description in **markdown** follows.
        # Can span multiple lines.
        #
        # --- (optional explicit delimiter)

        actual code starts here

    Rules:
        - Shebang (#!) is skipped
        - First # line = title
        - Subsequent # lines = description (markdown)
        - ``# ---`` explicitly ends the header
        - Without delimiter, header ends at first non-comment non-blank line
        - Blank # lines (just ``#``) become blank lines in description
        - No header at all → filename stem as title, empty description
    """
    lines = script_path.read_text().splitlines()
    title = ""
    desc_lines: list[str] = []
    line_idx = 0

    # Skip shebang
    if lines and lines[0].startswith("#!"):
        line_idx = 1

    # Find title: first # comment line
    while line_idx < len(lines):
        line = lines[line_idx]
        stripped = line.strip()
        if stripped.startswith("#") and not stripped.startswith("#!"):
            title = _strip_comment(stripped)
            line_idx += 1
            break
        elif stripped == "":
            # Skip blank lines between shebang and first comment
            line_idx += 1
        else:
            # Non-comment, non-blank — no header
            break

    if not title:
        return ScriptHeader(
            title=script_path.stem,
            description="",
            body_start_line=line_idx,
        )

    # Collect description lines
    while line_idx < len(lines):
        line = lines[line_idx]
        stripped = line.strip()

        # Explicit delimiter ends header
        if stripped == "# ---":
            line_idx += 1
            break

        # Comment line — part of description
        if stripped.startswith("#"):
            desc_lines.append(_strip_comment(stripped))
            line_idx += 1
            continue

        # Bare # (just the hash)
        if stripped == "#":
            desc_lines.append("")
            line_idx += 1
            continue

        # Blank line ends header (unless we haven't seen any description yet)
        if stripped == "":
            break

        # Non-comment line ends header
        break

    # Strip leading/trailing blank lines from description
    while desc_lines and desc_lines[0] == "":
        desc_lines.pop(0)
    while desc_lines and desc_lines[-1] == "":
        desc_lines.pop()

    # Skip blank lines after header to get to actual code
    while line_idx < len(lines) and lines[line_idx].strip() == "":
        line_idx += 1

    return ScriptHeader(
        title=title,
        description="\n".join(desc_lines),
        body_start_line=line_idx,
    )


def _strip_comment(line: str) -> str:
    """Strip comment prefix from a line: '# text' → 'text', '#' → ''."""
    if line == "#":
        return ""
    if line.startswith("# "):
        return line[2:]
    if line.startswith("#"):
        return line[1:]
    return line
