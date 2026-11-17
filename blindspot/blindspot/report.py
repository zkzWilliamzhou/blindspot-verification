"""Human and machine readable renderers for a blindspot report."""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from .hashing import canonical_bytes

_BAR = "=" * 72
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_terminal(text: str) -> str:
    """Prevent captured bytes from emitting terminal control sequences."""
    return _CONTROL.sub("", text)


def render_json(report: Dict[str, Any]) -> str:
    return json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def render_text(report: Dict[str, Any]) -> str:
    d = report.get("delta") or {}
    c = report.get("capture") or {}
    o = report.get("observation") or {}
    degs = report.get("degradations") or []
    lines = [
        _BAR,
        f"  blindspot  {report.get('report_id', '')}",
        f"  {report.get('created_at', '')}",
        _BAR,
        f"  command given : {report.get('original_command', '')}",
        f"  clean command : {report.get('clean_command', '')}",
        "",
    ]
    if not d:
        lines += [
            "  MODE          : static inspection only (command NOT executed)",
            "  VERDICT       : NOT MEASURED",
            "",
            "  Use `blindspot run '<command>'` to capture ground truth and measure the delta.",
        ]
    else:
        lines += [
            f"  VERDICT       : {d.get('verdict', 'UNKNOWN')}",
            f"  real exit     : {d.get('true_exit_code')}",
            f"  agent saw exit: {d.get('observed_exit_code')}",
            f"  stdout        : {d.get('stdout_bytes_true')} bytes real / {d.get('stdout_bytes_seen')} bytes seen",
            f"  stderr        : {d.get('stderr_bytes_true')} bytes real / {d.get('stderr_bytes_seen')} bytes seen",
            "",
            "  why:",
        ]
        for r in d.get("reasons", []):
            lines.append(f"    - {r}")
    lines += ["", "  observation-degrading constructs:"]
    if not degs:
        lines.append("    (none detected)")
    for g in degs:
        lines.append(
            f"    [{g.get('severity',''):8}] {g.get('kind',''):20} "
            f"{'replayable' if g.get('supported') else 'NOT replayed'}  {g.get('span','')[:60]}"
        )
    if d.get("hidden_stdout_excerpt"):
        lines += ["", "  hidden stdout (what the agent never saw):"]
        lines += ["    " + x for x in d["hidden_stdout_excerpt"].splitlines()]
    if d.get("hidden_stderr_excerpt"):
        lines += ["", "  hidden stderr:"]
        lines += ["    " + x for x in d["hidden_stderr_excerpt"].splitlines()]
    if report.get("refusals"):
        lines += ["", "  refusals (command was NOT executed):"]
        lines += ["    - " + x for x in report["refusals"]]
    if o.get("unsimulated"):
        lines += ["", "  unsimulated constructs:"]
        lines += ["    - " + x for x in o["unsimulated"]]
    if o.get("approximations"):
        lines += ["", "  approximations:"]
        lines += ["    - " + x for x in o["approximations"]]
    if report.get("limitations"):
        lines += ["", "  limitations:"]
        lines += ["    - " + x for x in report["limitations"]]
    if c.get("timed_out"):
        lines += ["", "  NOTE: the real command timed out; ground truth is partial."]
    lines += ["", _BAR]
    return sanitize_terminal("\n".join(lines))


def render_sarif(report: Dict[str, Any]) -> str:
    """Minimal SARIF 2.1.0 so CI can annotate misleading observation channels."""
    d = report.get("delta") or {}
    verdict = d.get("verdict", "UNKNOWN")
    level = "error" if verdict == "MISLEADING" else ("warning" if verdict == "DEGRADED" else "none")
    result = {
        "ruleId": "blindspot/observation-fidelity",
        "level": level,
        "message": {"text": "; ".join(d.get("reasons", [])) or "observation is faithful"},
        "properties": {
            "verdict": verdict,
            "originalCommand": report.get("original_command", ""),
            "trueExitCode": d.get("true_exit_code"),
            "observedExitCode": d.get("observed_exit_code"),
            "reportId": report.get("report_id", ""),
        },
    }
    return json.dumps({
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "blindspot", "version": report.get("tool_version", ""),
                                 "rules": [{"id": "blindspot/observation-fidelity"}]}},
            "results": [result],
        }],
    }, sort_keys=True, separators=(",", ":"))


def report_bytes(report: Dict[str, Any]) -> bytes:
    return canonical_bytes(report)
