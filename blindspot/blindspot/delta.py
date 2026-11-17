"""Measure the gap between ground truth and the agent's observation."""

from __future__ import annotations

from collections import Counter
from typing import List

from .model import FAILURE_MARKERS, Capture, Delta, Observation


def _lines(data: bytes) -> List[str]:
    return data.decode("utf-8", errors="replace").splitlines()


def _markers(text: str) -> List[str]:
    return sorted({m for m in FAILURE_MARKERS if m in text})


def _first_divergence(a: bytes, b: bytes):
    limit = min(len(a), len(b))
    for i in range(limit):
        if a[i] != b[i]:
            return i
    return limit if len(a) != len(b) else None


def _excerpt(lines: List[str], n: int = 12) -> str:
    chunk = lines[:n]
    text = "\n".join(chunk)
    if len(lines) > n:
        text += f"\n... ({len(lines) - n} more hidden lines)"
    return text


def measure(capture: Capture, observation: Observation) -> Delta:
    true_out, true_err = _lines(capture.stdout), _lines(capture.stderr)
    seen_out, seen_err = _lines(observation.stdout), _lines(observation.stderr)

    hidden_out = list((Counter(true_out) - Counter(seen_out)).elements())
    hidden_err = list((Counter(true_err) - Counter(seen_err)).elements())

    true_text = "\n".join(true_out + true_err)
    seen_text = "\n".join(seen_out + seen_err)
    true_markers, seen_markers = _markers(true_text), _markers(seen_text)
    hidden_markers = [m for m in true_markers if m not in seen_markers]

    laundered = capture.exit_code != observation.exit_code
    false_green = (
        observation.exit_code == 0
        and not seen_markers
        and (capture.exit_code != 0 or bool(true_markers))
    )
    false_red = (
        observation.exit_code != 0
        and capture.exit_code == 0
        and not true_markers
    )

    reasons: List[str] = []
    if false_green:
        reasons.append("the agent's view looks successful while the real run failed")
    if false_red:
        reasons.append("the agent's view looks failed while the real run succeeded")
    if laundered and not false_green and not false_red:
        reasons.append(
            f"real exit status {capture.exit_code} was reported as {observation.exit_code}"
        )
    if hidden_out:
        reasons.append(f"{len(hidden_out)} stdout line(s) never reached the agent")
    if hidden_err:
        reasons.append(f"{len(hidden_err)} stderr line(s) never reached the agent")
    if hidden_markers:
        reasons.append("hidden failure markers: " + ", ".join(hidden_markers))
    if capture.timed_out:
        reasons.append("the command timed out; ground truth is partial")
    if capture.stdout_truncated or capture.stderr_truncated:
        reasons.append("ground truth itself was capped by --max-output")

    if false_green or false_red:
        verdict = "MISLEADING"
    elif laundered or hidden_out or hidden_err or hidden_markers:
        verdict = "DEGRADED"
    else:
        verdict = "FAITHFUL"
    if not reasons:
        reasons.append("the observation faithfully represents the real execution")

    return Delta(
        verdict=verdict,
        reasons=reasons,
        true_exit_code=capture.exit_code,
        observed_exit_code=observation.exit_code,
        exit_code_laundered=laundered,
        hidden_stdout_lines=len(hidden_out),
        hidden_stderr_lines=len(hidden_err),
        hidden_failure_markers=hidden_markers,
        false_green=false_green,
        false_red=false_red,
        first_divergence_byte=_first_divergence(capture.stdout, observation.stdout),
        stdout_bytes_true=len(capture.stdout),
        stdout_bytes_seen=len(observation.stdout),
        stderr_bytes_true=len(capture.stderr),
        stderr_bytes_seen=len(observation.stderr),
        hidden_stdout_excerpt=_excerpt(hidden_out),
        hidden_stderr_excerpt=_excerpt(hidden_err),
    )
