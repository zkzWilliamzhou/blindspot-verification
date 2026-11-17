"""The measurement contract.

This module is deliberately deep: one small interface (`inspect_command`,
`measure_command`) hides parsing, single-execution capture, observation
replay, delta measurement, redaction and envelope construction. The CLI only
parses arguments and renders. Callers never assemble the pipeline themselves.

The interface IS the test surface: tests/golden_check.py exercises this module
through the CLI across a fixed scenario matrix, and the audit harness probes it
from ten directions.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .capture import CaptureError, run_clean
from .delta import measure
from .hashing import digest_obj
from .model import Report
from .parse import parse_command
from .redact import redact_text
from .replay import reconstruct

STANDARD_LIMITATIONS = [
    "The agent's view is RECONSTRUCTED from one real execution by replaying the recorded "
    "filters over the captured bytes. It is not a second execution.",
    "Constructs outside the supported replay set are reported as unsimulated, never guessed.",
    "The local ledger is tamper-EVIDENT, not tamper-proof. A process with write access can "
    "replace the whole directory, the head, or the key.",
    "This tool measures observation fidelity. It does not verify correctness, intent, "
    "test quality, or business requirements.",
    "No external witness or timestamp authority is used; wall-clock times are local.",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _redact_strings(obj):
    """Secrets can appear in the command line itself, not only in output."""
    if isinstance(obj, str):
        return redact_text(obj)[0]
    if isinstance(obj, list):
        return [_redact_strings(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _redact_strings(v) for k, v in obj.items()}
    return obj


def _build_report(parsed, capture, observation, delta, limitations: List[str]) -> dict:
    report = Report(
        created_at=_now(),
        original_command=parsed.original,
        clean_command=parsed.clean,
        degradations=[d.as_dict() for d in parsed.degradations],
        refusals=list(parsed.refusals),
        capture=capture.as_dict(redact=redact_text) if capture else None,
        observation=observation.as_dict(redact=redact_text) if observation else None,
        delta=delta.as_dict() if delta else None,
        limitations=STANDARD_LIMITATIONS + limitations,
    )
    # The report_id is computed over the REDACTED body so the stored file,
    # the ledger entry and the CLI output all describe the same object.
    body = _redact_strings(report.as_dict())
    body.pop("report_id", None)
    body["report_id"] = digest_obj(body)
    return body


def inspect_command(command: str, allow_destructive: bool = False) -> dict:
    """Static analysis only. Never executes anything."""
    parsed = parse_command(command, allow_destructive=allow_destructive)
    return _build_report(parsed, None, None, None, [])


def measure_command(
    command: str,
    *,
    root: str,
    cwd: Optional[str] = None,
    timeout: int = 30,
    max_output: int = 1_000_000,
    max_bytes: int = 0,
    deny_net: bool = False,
    allow_destructive: bool = False,
) -> Tuple[Optional[dict], Optional[str]]:
    """Return (report, error).

    `error` is a refusal string when the command was NOT executed, or a
    capture error string when execution could not be started. A report is
    still returned for refusals so the caller can show the static analysis.
    """
    parsed = parse_command(command, allow_destructive=allow_destructive)
    if parsed.refusals:
        report = _build_report(parsed, None, None, None, [
            "The command was NOT executed. Static analysis only is shown above.",
        ])
        return report, "; ".join(parsed.refusals)

    try:
        capture = run_clean(
            parsed.clean,
            root=root,
            cwd=cwd,
            timeout=timeout,
            max_output=max_output,
            deny_net=deny_net,
        )
    except CaptureError as exc:
        return None, str(exc)

    observation = reconstruct(capture, parsed, max_bytes)
    delta = measure(capture, observation)
    limitations = list(observation.unsimulated) + list(observation.approximations)
    if capture.timed_out:
        limitations.append("The real command timed out; the recorded ground truth is incomplete.")
    if capture.stdout_truncated or capture.stderr_truncated:
        limitations.append("Ground truth was capped by --max-output; full digests still cover raw bytes.")
    if capture.network_backend == "none":
        limitations.append("Network was not disabled (use --deny-net on Linux to enforce isolation).")
    if os.name != "posix":
        limitations.append("Non-POSIX platform: process-group kill and resource limits are unavailable.")
    return _build_report(parsed, capture, observation, delta, limitations), None
