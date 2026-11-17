"""Typed data model for blindspot.

Every object here is deliberately plain data. No behaviour lives in this module,
which keeps the on-disk envelope stable and easy for other tools to consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from . import SCHEMA_VERSION, TOOL_NAME, __version__


def to_dict(obj: Any) -> Any:
    """Recursively convert dataclasses to plain dicts."""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_dict(v) for k, v in asdict(obj).items()}
    if isinstance(obj, (list, tuple)):
        return [to_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj


@dataclass(frozen=True)
class Degradation:
    """One construct in a shell command that degrades the agent's observation."""

    kind: str
    detail: str
    span: str
    severity: str  # info | warning | critical
    supported: bool  # can replay.py faithfully reconstruct this?
    args: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return to_dict(self)


@dataclass
class CleanCommand:
    """The command derived from the original with degradations removed."""

    original: str
    clean: str
    segments: List[List[str]]
    degradations: List[Degradation]
    refusals: List[str]  # reasons we will not execute the derived command

    def as_dict(self) -> Dict[str, Any]:
        return to_dict(self)


@dataclass
class Capture:
    """Ground truth from exactly one real execution of the clean command."""

    command: str
    cwd: str
    stdout: bytes
    stderr: bytes
    exit_code: int
    signal: Optional[int]
    duration_ms: int
    stdout_sha256: str
    stderr_sha256: str
    stdout_truncated: bool
    stderr_truncated: bool
    timed_out: bool
    output_cap_bytes: int
    env_allowlist: List[str]
    env_digest: str  # sha256 over all non-allowlisted NAME=VALUE pairs (values never stored)
    network_denied: bool
    network_backend: str
    platform: str
    redactions: int = 0

    def as_dict(self, redact=None) -> Dict[str, Any]:
        """Serialize with redaction applied to stored text (digests stay raw)."""
        out = to_dict(self)
        so = self.stdout.decode("utf-8", errors="replace")
        se = self.stderr.decode("utf-8", errors="replace")
        if redact is not None:
            so, n1 = redact(so)
            se, n2 = redact(se)
            out["redactions"] = n1 + n2
        out["stdout"] = so
        out["stderr"] = se
        return out


@dataclass
class Observation:
    """What the agent would have seen, reconstructed from ground truth."""

    stdout: bytes
    stderr: bytes
    exit_code: int
    applied: List[str]
    unsimulated: List[str]
    approximations: List[str]

    def as_dict(self, redact=None) -> Dict[str, Any]:
        out = to_dict(self)
        so = self.stdout.decode("utf-8", errors="replace")
        se = self.stderr.decode("utf-8", errors="replace")
        if redact is not None:
            so, _ = redact(so)
            se, _ = redact(se)
        out["stdout"] = so
        out["stderr"] = se
        return out


FAILURE_MARKERS = (
    "FAILED", "failed", "FAIL", "ERROR", "Error", "error:", "Traceback",
    "AssertionError", "panic:", "fatal:", "non-zero", "exited with", "RED",
)


@dataclass
class Delta:
    """Measured difference between ground truth and the agent's observation."""

    verdict: str  # FAITHFUL | DEGRADED | MISLEADING
    reasons: List[str]
    true_exit_code: int
    observed_exit_code: int
    exit_code_laundered: bool
    hidden_stdout_lines: int
    hidden_stderr_lines: int
    hidden_failure_markers: List[str]
    false_green: bool
    false_red: bool
    first_divergence_byte: Optional[int]
    stdout_bytes_true: int
    stdout_bytes_seen: int
    stderr_bytes_true: int
    stderr_bytes_seen: int
    hidden_stdout_excerpt: str
    hidden_stderr_excerpt: str

    def as_dict(self) -> Dict[str, Any]:
        return to_dict(self)


@dataclass
class Report:
    """The canonical, shareable envelope."""

    schema_version: str = SCHEMA_VERSION
    tool: str = TOOL_NAME
    tool_version: str = __version__
    report_id: str = ""
    created_at: str = ""
    original_command: str = ""
    clean_command: str = ""
    degradations: List[Degradation] = field(default_factory=list)
    refusals: List[str] = field(default_factory=list)
    capture: Optional[Dict[str, Any]] = None
    observation: Optional[Dict[str, Any]] = None
    delta: Optional[Dict[str, Any]] = None
    limitations: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return to_dict(self)
