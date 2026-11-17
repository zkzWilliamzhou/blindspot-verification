"""Canonical serialization and content addressing.

The canonical form is shared by report IDs, receipt hashes and the chain.
Changing it changes every stored digest, so it is intentionally small and
versioned in `SCHEMA_VERSION`.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any, Dict, Iterable


def canonical_bytes(obj: Any) -> bytes:
    """Deterministic UTF-8 JSON encoding. No whitespace, sorted keys."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False, default=str,
    ).encode("utf-8")


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def digest_obj(obj: Any) -> str:
    return digest(canonical_bytes(obj))


def file_digest(path: str, chunk: int = 1 << 16) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return "sha256:" + h.hexdigest()


def stream_digest_and_head(fh, cap: int):
    """Hash the entire stream, then return its first `cap` bytes.

    Returns (digest, head_bytes, truncated). This module owns every SHA-256
    computation in the package, so callers never import hashlib themselves.
    """
    fh.seek(0)
    h = hashlib.sha256()
    total = 0
    while True:
        block = fh.read(1 << 16)
        if not block:
            break
        h.update(block)
        total += len(block)
    fh.seek(0)
    return "sha256:" + h.hexdigest(), fh.read(cap), total > cap


def tree_digest(root: str, excludes: Iterable[str] = ()) -> str:
    """Content digest of a directory tree, used for provenance of the run.

    Only regular files are included. Symlinks are recorded by their target
    string, never followed. Ordering is by relative POSIX path.
    """
    excl = set(excludes)
    entries = []
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        rel_dir = os.path.relpath(dirpath, root)
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in excl and os.path.join(rel_dir, d) not in excl
        )
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if rel in excl or any(rel.startswith(e.rstrip("/") + "/") for e in excl):
                continue
            if os.path.islink(full):
                entries.append([rel, "symlink", os.readlink(full)])
            elif os.path.isfile(full):
                entries.append([rel, "file", os.path.getsize(full), file_digest(full)])
    return digest(canonical_bytes(entries))


def hmac_hex(key: bytes, payload: bytes) -> str:
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def load_key(key_path: str) -> bytes | None:
    """Optional HMAC key. Absence is a supported, documented mode."""
    try:
        with open(key_path, "rb") as fh:
            key = fh.read()
        return key if len(key) >= 16 else None
    except OSError:
        return None
