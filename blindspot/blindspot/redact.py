"""Deterministic secret scrubbing for stored evidence.

Redaction is applied only to *stored text*. Raw digests always cover the
unredacted bytes, and replay works on the raw bytes in memory. That keeps
integrity verifiable without persisting credentials.

This is a best-effort filter, not a secret scanner. It will not catch every
encoding. The threat model says so explicitly.
"""

from __future__ import annotations

import re
from typing import Tuple

_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED:AWS_KEY]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "[REDACTED:GITHUB_TOKEN]"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "[REDACTED:SLACK_TOKEN]"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
     "[REDACTED:PRIVATE_KEY]"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
     "[REDACTED:JWT]"),
    (re.compile(r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|pwd|client[_-]?secret)\b\s*[:=]\s*[\"']?[^\s\"'&,;]{4,}"),
     "[REDACTED:ASSIGNMENT]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]{8,}"),
     "Authorization: Bearer [REDACTED:BEARER]"),
    (re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s:/@]+:[^\s/@]+@"),
     "[REDACTED:URL_CREDENTIALS]@"),
]

_PLACEHOLDER = "[REDACTED]"


def redact_text(text: str) -> Tuple[str, int]:
    """Return (redacted_text, number_of_replacements)."""
    count = 0
    out = text
    for pattern, replacement in _PATTERNS:
        out, n = pattern.subn(replacement, out)
        count += n
    return out, count


def scrub_env_value(name: str, value: str) -> str:
    """Never store plaintext values of sensitive-looking variables."""
    upper = name.upper()
    if any(t in upper for t in ("KEY", "TOKEN", "SECRET", "PASS", "CREDENTIAL", "AUTH")):
        return _PLACEHOLDER
    return value
