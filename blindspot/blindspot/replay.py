"""Reconstruct what the agent would have seen.

The ground truth is captured ONCE by capture.py. Every degrading construct is
then replayed as a real subprocess over those captured bytes. Nothing is
invented: `tail`, `grep`, `head` etc. are the actual binaries, given argv and
bytes. Constructs outside the supported set are reported as unsimulated.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from typing import List

from .model import Capture, CleanCommand, Observation

_FILTER_ENV = {
    "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
    "LC_ALL": "C",
    "LANG": "C",
}


def _truncate(data: bytes, cap: int) -> bytes:
    if cap <= 0 or len(data) <= cap:
        return data
    head = int(cap * 0.5)
    tail = cap - head
    marker = b"\n... [blindspot: %d bytes omitted by output cap] ...\n" % (len(data) - cap)
    return data[:head] + marker + data[-tail:]


def reconstruct(capture: Capture, parsed: CleanCommand, max_bytes: int = 0) -> Observation:
    """Apply the recorded degradations to ground truth, deterministically."""
    stdout = capture.stdout
    stderr = capture.stderr
    observed_exit = capture.exit_code
    applied: List[str] = []
    unsimulated: List[str] = []
    approximations: List[str] = []
    kinds = {d.kind for d in parsed.degradations}

    if "stream_merged" in kinds:
        stdout = stdout + b"\n" + stderr
        stderr = b""
        applied.append("stream_merged")
        approximations.append(
            "stdout/stderr interleaving cannot be recovered without a PTY; "
            "streams are concatenated in capture order"
        )

    last_filter_exit = 0
    if parsed.segments:
        with tempfile.TemporaryDirectory(prefix="blindspot-replay-") as td:
            for argv in parsed.segments:
                try:
                    proc = subprocess.run(
                        argv,
                        input=stdout,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=5,
                        cwd=td,
                        env=_FILTER_ENV,
                        check=False,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    unsimulated.append(f"filter {' '.join(argv)!r} could not be replayed: {exc}")
                    continue
                stdout = proc.stdout
                last_filter_exit = proc.returncode
                applied.append("pipe " + " ".join(argv))
                if proc.stderr:
                    stderr += b"\n[filter stderr]\n" + proc.stderr

    if "stderr_suppressed" in kinds:
        stderr = b""
        applied.append("stderr_suppressed")
    if "stdout_suppressed" in kinds:
        stdout = b""
        applied.append("stdout_suppressed")

    # A POSIX pipeline without pipefail reports the LAST stage's status.
    if "pipefail_absent" in kinds and parsed.segments:
        observed_exit = last_filter_exit
        applied.append("shell reported the last pipeline stage's exit status")
    if "exit_laundered" in kinds:
        observed_exit = 0
        applied.append("exit status replaced with success")

    for d in parsed.degradations:
        if not d.supported:
            unsimulated.append(f"{d.kind}: {d.detail}")

    if max_bytes > 0 and len(stdout) > max_bytes:
        stdout = _truncate(stdout, max_bytes)
        applied.append(f"output capped at {max_bytes} bytes")
        approximations.append(
            "the harness output cap is simulated with a head/tail window; "
            "real harnesses may use different truncation policies"
        )

    return Observation(stdout, stderr, observed_exit, applied, unsimulated, approximations)
