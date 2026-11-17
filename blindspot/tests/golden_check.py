"""Behavior-freeze gate.

Records an exact, normalized behavioral signature of blindspot across a fixed
scenario matrix. The architecture pass is FORBIDDEN to alter this file or the
baseline. If `--check` reports any difference, the refactor changed behaviour
and must be rejected.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(ROOT, "tests", "golden", "baseline.json")

FIXTURE = """\
import sys
print("FAILED tests/test_a.py::test_one - AssertionError: expected 2, got 3")
print("FAILED tests/test_b.py::test_two - AssertionError: expected 2, got 3")
print("collected 3 items")
print("OK")
print("E: detail on stderr", file=sys.stderr)
sys.exit(1)
"""

# (label, command template, extra flags)
SCENARIOS = [
    ("plain", "python3 {p}", []),
    ("tail1", "python3 {p} | tail -1", []),
    ("head2", "python3 {p} | head -2", []),
    ("grep_ok", "python3 {p} | grep OK", []),
    ("wc_l", "python3 {p} | wc -l", []),
    ("launder", "python3 {p} || true", []),
    ("stderr_null", "python3 {p} 2>/dev/null", []),
    ("stdout_null", "python3 {p} >/dev/null", []),
    ("merged", "python3 {p} 2>&1 | grep OK", []),
    ("capped", "python3 {p}", ["--max-bytes", "40"]),
    ("strict", "python3 {p} | tail -1", ["--strict"]),
    ("unsupported", "python3 {p} | sed -n 1p", []),
    ("echo_ok", "echo hello", []),
    ("pipefail", "set -o pipefail; python3 {p} | tail -1", []),
]


def _normalize(value, td):
    if isinstance(value, str):
        return value.replace(td, "<ROOT>")
    if isinstance(value, dict):
        return {k: _normalize(v, td) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v, td) for v in value]
    return value


def signature():
    out = {}
    with tempfile.TemporaryDirectory(prefix="blindspot-golden-") as td:
        p = os.path.join(td, "fixture.py")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(FIXTURE)
        env = dict(os.environ, PYTHONPATH=ROOT)
        for label, template, flags in SCENARIOS:
            cmd = template.format(p=p)
            argv = [sys.executable, "-m", "blindspot", "--root", td,
                    "run", cmd, "--json"] + flags
            try:
                r = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=60)
            except subprocess.TimeoutExpired:
                out[label] = {"__error__": "timeout"}
                continue
            try:
                obj = json.loads(r.stdout)
            except ValueError:
                out[label] = {"__error__": "invalid json", "stderr": r.stderr[-300:]}
                continue
            keep = {
                "rc": r.returncode,
                "clean_command": obj.get("clean_command"),
                "refusals": obj.get("refusals"),
                "degradations": [
                    {k: d.get(k) for k in ("kind", "span", "severity", "supported", "args")}
                    for d in obj.get("degradations", [])
                ],
                "delta": None if not obj.get("delta") else {
                    k: obj["delta"].get(k) for k in (
                        "verdict", "reasons", "true_exit_code", "observed_exit_code",
                        "exit_code_laundered", "hidden_stdout_lines", "hidden_stderr_lines",
                        "hidden_failure_markers", "false_green", "false_red",
                        "first_divergence_byte", "stdout_bytes_true", "stdout_bytes_seen",
                        "stderr_bytes_true", "stderr_bytes_seen",
                        "hidden_stdout_excerpt", "hidden_stderr_excerpt",
                    )
                },
                "observation": None if not obj.get("observation") else {
                    k: obj["observation"].get(k) for k in ("applied", "unsimulated", "approximations")
                },
                "capture": None if not obj.get("capture") else {
                    k: obj["capture"].get(k) for k in (
                        "exit_code", "timed_out", "stdout_truncated", "stderr_truncated",
                        "network_backend", "stdout_sha256", "stderr_sha256",
                    )
                },
            }
            out[label] = _normalize(keep, td)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    sig = signature()
    if args.freeze:
        os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
        with open(BASELINE, "w", encoding="utf-8") as fh:
            json.dump(sig, fh, sort_keys=True, indent=2, ensure_ascii=False)
        print(f"froze {len(sig)} scenarios -> {BASELINE}")
        return 0
    if args.check:
        try:
            with open(BASELINE, "r", encoding="utf-8") as fh:
                expected = json.load(fh)
        except OSError:
            print("no baseline; run --freeze before the architecture pass")
            return 2
        diffs = [k for k in sorted(set(expected) | set(sig)) if expected.get(k) != sig.get(k)]
        if diffs:
            print("BEHAVIOR CHANGED in: " + ", ".join(diffs))
            for k in diffs[:3]:
                print(f"  [{k}] expected={json.dumps(expected.get(k), sort_keys=True)[:400]}")
                print(f"  [{k}] actual  ={json.dumps(sig.get(k), sort_keys=True)[:400]}")
            return 1
        print(f"behavior unchanged across {len(sig)} frozen scenarios")
        return 0
    print(json.dumps(sig, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
