"""Local, tamper-evident, append-only evidence history.

It is not tamper-proof. A local chain with no external anchor can be replaced
wholesale by a process with write access. `verify` detects editing, deletion,
reordering and truncation of recorded entries -- nothing more.
See docs/THREAT_MODEL.md.
"""

from __future__ import annotations

import fcntl
import json
import os
from typing import Any, Dict, List, Optional

from .hashing import canonical_bytes, digest_obj, hmac_hex, load_key

GENESIS = "sha256:" + "0" * 64


class Ledger:
    def __init__(self, root: str):
        self.dir = os.path.join(os.path.abspath(root), ".blindspot")
        self.path = os.path.join(self.dir, "ledger.jsonl")
        self.head_path = os.path.join(self.dir, "head.json")
        self.lock_path = os.path.join(self.dir, "lock")
        self.key_path = os.path.join(self.dir, "key")
        self.last_path = os.path.join(self.dir, "last-report.json")

    def init(self, with_key: bool = False) -> str:
        os.makedirs(self.dir, exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as fh:
                fh.write("")
        if not os.path.exists(self.head_path):
            self._write_head({
                "schema_version": "1.0", "seq": 0, "chain": GENESIS,
                "report_id": "", "hmac": None,
            })
        if with_key and not os.path.exists(self.key_path):
            key = os.urandom(32)
            fd = os.open(self.key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "wb") as fh:
                fh.write(key)
        return self.dir

    def _write_head(self, head: Dict[str, Any]) -> None:
        tmp = self.head_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(head, sort_keys=True, separators=(",", ":")))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.head_path)

    def _read_head(self) -> Dict[str, Any]:
        try:
            with open(self.head_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {"schema_version": "1.0", "seq": 0, "chain": GENESIS,
                    "report_id": "", "hmac": None}

    def _key(self) -> Optional[bytes]:
        return load_key(self.key_path)

    def append(self, report: Dict[str, Any]) -> Dict[str, Any]:
        self.init()
        with open(self.lock_path, "a+") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            head = self._read_head()
            seq = int(head.get("seq", 0)) + 1
            prev = head.get("chain", GENESIS)
            report_id = report.get("report_id", "")
            entry = {
                "seq": seq,
                "prev": prev,
                "report_id": report_id,
                "created_at": report.get("created_at", ""),
                "verdict": (report.get("delta") or {}).get("verdict", "UNKNOWN"),
            }
            entry["entry_hash"] = digest_obj(entry)
            chain = digest_obj({"prev": prev, "entry_hash": entry["entry_hash"]})
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            new_head = {
                "schema_version": "1.0",
                "seq": seq,
                "chain": chain,
                "report_id": report_id,
                "hmac": None,
            }
            key = self._key()
            if key:
                new_head["hmac"] = hmac_hex(key, canonical_bytes({
                    "seq": seq, "chain": chain, "report_id": report_id,
                }))
            self._write_head(new_head)
            tmp = self.last_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            os.replace(tmp, self.last_path)
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        return entry

    def last_report(self) -> Optional[Dict[str, Any]]:
        try:
            with open(self.last_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None

    def verify(self) -> Dict[str, Any]:
        issues: List[str] = []
        entries: List[Dict[str, Any]] = []
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, 1):
                    if not line.strip():
                        continue
                    try:
                        entries.append(json.loads(line))
                    except ValueError:
                        issues.append(f"line {lineno}: malformed JSON")
        except OSError as exc:
            return {
                "ok": False, "entries": 0,
                "issues": [f"ledger unreadable: {exc}"],
                "warnings": [], "head": None, "anchored_externally": False,
            }

        prev = GENESIS
        expected_seq = 1
        chain = GENESIS
        for e in entries:
            if e.get("seq") != expected_seq:
                issues.append(f"seq {e.get('seq')}: expected {expected_seq} (gap or reorder)")
            if e.get("prev") != prev:
                issues.append(f"seq {e.get('seq')}: broken prev link")
            body = {k: e.get(k) for k in ("seq", "prev", "report_id", "created_at", "verdict")}
            if e.get("entry_hash") != digest_obj(body):
                issues.append(f"seq {e.get('seq')}: entry_hash mismatch (content edited)")
            chain = digest_obj({"prev": prev, "entry_hash": e.get("entry_hash")})
            prev = chain
            expected_seq += 1

        head = self._read_head()
        if head.get("seq") != len(entries):
            issues.append(
                f"head seq {head.get('seq')} does not match {len(entries)} entries "
                "(truncation or rollback)"
            )
        if head.get("chain") != chain:
            issues.append("head chain does not match recomputed chain")
        key = self._key()
        if key:
            want = hmac_hex(key, canonical_bytes({
                "seq": head.get("seq"), "chain": head.get("chain"),
                "report_id": head.get("report_id"),
            }))
            if head.get("hmac") != want:
                issues.append("head HMAC invalid (head replaced or key changed)")
        warnings: List[str] = []
        if not key:
            warnings.append(
                "no HMAC key configured: replacing the head file cannot be detected. "
                "Run `blindspot init --key` for authenticated heads."
            )

        return {
            "ok": not issues,
            "entries": len(entries),
            "issues": issues,
            "warnings": warnings,
            "head": head,
            "anchored_externally": False,
        }
