"""Claude Code hook adapter (one integration, explicitly scoped).

This module ONLY understands the Claude Code hook JSON shape. It performs
static inspection and never executes the command from inside a hook. Claiming
universality across agents would be false, so we do not.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from .parse import parse_command
from .report import sanitize_terminal


def _command_from(payload: Dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or "")
    return ""


def _message(parsed) -> str:
    critical = [d for d in parsed.degradations if d.severity == "critical"]
    if not critical:
        return ""
    bits = [
        "blindspot: this command degrades your observation channel.",
        "The shell result you are about to read may not be the real result:",
    ]
    for d in critical:
        bits.append(f"  - {d.kind}: {d.detail}  [{d.span}]")
    bits.append(
        "Run `blindspot run '<command>'` to see the full ground truth and the exact delta. "
        "Do not state success based on the filtered output."
    )
    return sanitize_terminal("\n".join(bits))


def handle(payload: Dict[str, Any], strict: bool = False) -> Tuple[int, str, str]:
    """Return (exit_code, stdout, stderr) following Claude Code hook conventions."""
    event = payload.get("hook_event_name", "")
    tool = payload.get("tool_name", "")
    if event == "PreToolUse" and tool in ("Bash", "Shell", "shell"):
        cmd = _command_from(payload)
        if not cmd.strip():
            return 0, "", ""
        parsed = parse_command(cmd)
        msg = _message(parsed)
        if not msg:
            return 0, "", ""
        if strict:
            # Exit 2 blocks the tool call; stderr is fed back to the agent.
            return 2, "", msg
        out = json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": msg,
            }
        }, separators=(",", ":"))
        return 0, out, ""
    if event == "PostToolUse":
        # Passive by design. A PostToolUse hook cannot undo an executed command,
        # so we never pretend it can.
        return 0, "", ""
    return 0, "", ""
