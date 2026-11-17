"""blindspot command line interface."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from typing import List, Optional

from . import __version__, pipeline
from .hooks import handle as hook_handle
from .ledger import Ledger
from .report import render_json, render_sarif, render_text

EXIT_OK = 0
EXIT_MISLEADING = 1
EXIT_ERROR = 2


def _emit(report: dict, args) -> None:
    if args.sarif:
        print(render_sarif(report))
    elif args.json:
        print(render_json(report))
    else:
        print(render_text(report))


def cmd_init(args) -> int:
    path = Ledger(args.root).init(with_key=args.key)
    print(f"initialized {path}" + (" (HMAC key generated, mode 0600)" if args.key else ""))
    return EXIT_OK


def cmd_inspect(args) -> int:
    report = pipeline.inspect_command(
        args.command, allow_destructive=args.allow_destructive
    )
    print(render_json(report) if args.json else render_text(report))
    return EXIT_OK


def cmd_run(args) -> int:
    try:
        Ledger(args.root).init()  # creates the project root and .blindspot/
    except OSError as exc:
        print(f"blindspot: cannot initialize project root: {exc}", file=sys.stderr)
        return EXIT_ERROR

    report, error = pipeline.measure_command(
        args.command,
        root=args.root,
        cwd=args.cwd,
        timeout=args.timeout,
        max_output=args.max_output,
        max_bytes=args.max_bytes,
        deny_net=args.deny_net,
        allow_destructive=args.allow_destructive,
    )
    if report is None:
        print(f"blindspot: {error}", file=sys.stderr)
        return EXIT_ERROR
    if error:
        _emit(report, args)
        print("\nrefused to execute: " + error, file=sys.stderr)
        return EXIT_ERROR

    try:
        Ledger(args.root).append(report)
    except OSError as exc:
        print(f"blindspot: could not write ledger: {exc}", file=sys.stderr)
        return EXIT_ERROR
    _emit(report, args)

    verdict = report["delta"]["verdict"]
    if verdict == "MISLEADING":
        return EXIT_MISLEADING
    if verdict == "DEGRADED" and args.strict:
        return EXIT_MISLEADING
    return EXIT_OK


def cmd_diff(args) -> int:
    report = Ledger(args.root).last_report()
    if not report:
        print("blindspot: no report stored yet; run `blindspot run ...` first", file=sys.stderr)
        return EXIT_ERROR
    print(render_json(report) if args.json else render_text(report))
    return EXIT_OK


def cmd_verify(args) -> int:
    result = Ledger(args.root).verify()
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
          if args.json else _verify_text(result))
    return EXIT_OK if result["ok"] else EXIT_MISLEADING


def _verify_text(result) -> str:
    lines = [
        "=" * 60,
        f"  ledger verify: {'OK' if result['ok'] else 'FAILED'}",
        f"  entries: {result['entries']}",
        f"  externally anchored: {result['anchored_externally']}",
        "=" * 60,
    ]
    if result["issues"]:
        lines.append("  issues:")
        lines += ["    - " + i for i in result["issues"]]
    else:
        lines.append("  no integrity issues detected")
    for w in result.get("warnings", []):
        lines.append("  warning: " + w)
    return "\n".join(lines)


_DEMO_SCRIPT = '''\
import sys
print("FAILED tests/test_a.py::test_one - AssertionError: expected 2, got 3")
print("FAILED tests/test_b.py::test_two - AssertionError: expected 2, got 3")
print("FAILED tests/test_c.py::test_three - AssertionError: expected 2, got 3")
print("collected 4 items")
print("OK")
sys.exit(1)
'''


def cmd_demo(args) -> int:
    """Self-contained 30-second demonstration. Synthetic by design."""
    with tempfile.TemporaryDirectory(prefix="blindspot-demo-") as td:
        script = os.path.join(td, "fake_tests.py")
        with open(script, "w", encoding="utf-8") as fh:
            fh.write(_DEMO_SCRIPT)
        cmd = f"python3 {script} | tail -1"
        print("SYNTHETIC DEMO — a fake test runner prints 3 failures then a final 'OK'.")
        print(f"Agent runs: {cmd}\n")
        inner = argparse.Namespace(
            command=cmd, root=td, cwd=None, timeout=15, max_output=100000,
            deny_net=False, max_bytes=0, strict=False, allow_destructive=False,
            json=args.json, sarif=False,
        )
        rc = cmd_run(inner)
        print("\nThe agent saw one line: 'OK' and exit status 0.")
        print("The real run exited 1 and reported three failures.")
        return rc


def cmd_hook(args) -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        print("blindspot: invalid hook JSON on stdin", file=sys.stderr)
        return EXIT_ERROR
    code, out, err = hook_handle(payload, strict=args.strict)
    if out:
        sys.stdout.write(out)
    if err:
        sys.stderr.write(err)
    return code


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="blindspot",
        description="Measure what an AI coding agent's shell command hid from it.",
        epilog="Not a test runner, CI replacement, sandbox, AI detector, or proof system.",
    )
    p.add_argument("--version", action="version", version=f"blindspot {__version__}")
    p.add_argument("--root", default=None, help="project root (default: cwd)")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--json", action="store_true", help="machine-readable JSON")
        sp.add_argument("--sarif", action="store_true", help="SARIF 2.1.0 output")

    i = sub.add_parser("init", help="initialize .blindspot/")
    i.add_argument("--key", action="store_true", help="generate an HMAC key (mode 0600)")
    i.set_defaults(func=cmd_init)

    ins = sub.add_parser("inspect", help="static analysis only, never executes")
    ins.add_argument("command")
    ins.add_argument("--allow-destructive", action="store_true")
    common(ins)
    ins.set_defaults(func=cmd_inspect)

    r = sub.add_parser("run", help="execute once, capture truth, report the delta")
    r.add_argument("command")
    r.add_argument("--timeout", type=int, default=30)
    r.add_argument("--max-output", type=int, default=1_000_000)
    r.add_argument("--max-bytes", type=int, default=0,
                   help="simulate a harness output cap (0 disables)")
    r.add_argument("--deny-net", action="store_true", help="require Linux unshare -n")
    r.add_argument("--strict", action="store_true", help="fail on any degradation")
    r.add_argument("--allow-destructive", action="store_true")
    r.add_argument("--cwd", default=None)
    common(r)
    r.set_defaults(func=cmd_run)

    d = sub.add_parser("diff", help="show the most recent report")
    common(d)
    d.set_defaults(func=cmd_diff)

    v = sub.add_parser("verify", help="check ledger integrity")
    v.add_argument("--json", action="store_true")
    v.set_defaults(func=cmd_verify)

    dm = sub.add_parser("demo", help="self-contained synthetic demo")
    dm.add_argument("--json", action="store_true")
    dm.set_defaults(func=cmd_demo)

    h = sub.add_parser("hook", help="Claude Code hook adapter (reads JSON on stdin)")
    h.add_argument("--strict", action="store_true", help="block critical degradations (exit 2)")
    h.set_defaults(func=cmd_hook)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "root", None) is None:
        args.root = os.getcwd()
    if not hasattr(args, "sarif"):
        args.sarif = False
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
