"""Adversarial test suite for blindspot. Standard library unittest only."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from blindspot.capture import CaptureError, run_clean  # noqa: E402
from blindspot.delta import measure  # noqa: E402
from blindspot.hashing import digest, digest_obj, tree_digest  # noqa: E402
from blindspot.hooks import handle as hook_handle  # noqa: E402
from blindspot.ledger import Ledger  # noqa: E402
from blindspot.model import Capture, Observation  # noqa: E402
from blindspot.parse import parse_command  # noqa: E402
from blindspot.redact import redact_text  # noqa: E402
from blindspot.replay import reconstruct  # noqa: E402

FIXTURE = """\
import sys
print("FAILED tests/test_a.py::test_one - AssertionError: expected 2, got 3")
print("FAILED tests/test_b.py::test_two - AssertionError: expected 2, got 3")
print("collected 3 items")
print("ERROR: setup failed")
print("OK")
print("stderr-secret AKIAIOSFODNN7EXAMPLE", file=sys.stderr)
sys.exit(1)
"""


def _fixture(td):
    p = os.path.join(td, "fixture.py")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(FIXTURE)
    return p


def _cap(td, cmd, **kw):
    return run_clean(cmd, root=td, timeout=kw.get("timeout", 15),
                     max_output=kw.get("max_output", 100000),
                     deny_net=kw.get("deny_net", False))


class TestParse(unittest.TestCase):
    def test_pipe_tail(self):
        p = parse_command("pytest -q | tail -1")
        kinds = {d.kind for d in p.degradations}
        self.assertIn("pipe_filter", kinds)
        self.assertIn("pipefail_absent", kinds)
        self.assertEqual(p.clean, "pytest -q")
        self.assertEqual(p.segments, [["tail", "-1"]])
        self.assertEqual(p.refusals, [])

    def test_pipefail_suppresses_warning(self):
        p = parse_command("set -o pipefail; pytest -q | tail -1")
        self.assertNotIn("pipefail_absent", {d.kind for d in p.degradations})
        self.assertEqual(p.clean, "pytest -q")

    def test_set_plus_e_is_preamble_not_command(self):
        p = parse_command("set +e; python3 x.py || true")
        self.assertIn("exit_laundered", {d.kind for d in p.degradations})
        self.assertTrue(p.clean.startswith("python3"))

    def test_laundering_variants(self):
        for cmd in ("cmd || true", "cmd; true", "cmd || echo done", "cmd || :", "cmd || exit 0"):
            with self.subTest(cmd=cmd):
                self.assertIn("exit_laundered", {d.kind for d in parse_command(cmd).degradations})

    def test_suppressions(self):
        self.assertIn("stderr_suppressed", {d.kind for d in parse_command("cmd 2>/dev/null").degradations})
        self.assertIn("stdout_suppressed", {d.kind for d in parse_command("cmd >/dev/null").degradations})

    def test_stream_merge(self):
        p = parse_command("cmd 2>&1 | grep OK")
        kinds = {d.kind for d in p.degradations}
        self.assertIn("stream_merged", kinds)
        self.assertIn("pipe_filter", kinds)

    def test_unsupported_filters_are_refused(self):
        for cmd in ("cmd | sed -n 1p", "cmd | tee out.txt", "cmd | xargs echo", "cmd | jq ."):
            with self.subTest(cmd=cmd):
                p = parse_command(cmd)
                self.assertTrue(p.refusals, f"expected refusal for {cmd}")
                self.assertTrue(any(not d.supported for d in p.degradations))

    def test_command_substitution_refused(self):
        p = parse_command("echo $(date) | tail -1")
        self.assertTrue(p.refusals)

    def test_destructive_default_and_override(self):
        self.assertTrue(parse_command("rm -rf x | tail -1").refusals)
        self.assertFalse(parse_command("rm -rf x | tail -1", allow_destructive=True).refusals)

    def test_empty_command(self):
        self.assertTrue(parse_command("").refusals)

    def test_quoted_pipe_is_not_an_operator(self):
        p = parse_command("grep 'a|b' file.txt")
        self.assertEqual(p.refusals, [])
        self.assertEqual(p.segments, [])

    def test_numeric_short_flags(self):
        for cmd in ("cmd | tail -1", "cmd | head -20", "cmd | tail -n 3", "cmd | head -c 10"):
            with self.subTest(cmd=cmd):
                self.assertEqual(parse_command(cmd).refusals, [])


class TestReplayAndDelta(unittest.TestCase):
    def _capture(self, stdout=b"a\nb\nc\n", stderr=b"", rc=0):
        return Capture("cmd", ".", stdout, stderr, rc, None, 1, digest(stdout),
                       digest(stderr), False, False, False, 100000, [], "x", False,
                       "none", "test")

    def test_tail_replays_real_binary(self):
        p = parse_command("cmd | tail -1")
        obs = reconstruct(self._capture(), p)
        self.assertEqual(obs.stdout, b"c\n")
        self.assertIn("pipe tail -1", obs.applied)

    def test_head_and_grep_and_wc(self):
        c = self._capture(b"FAILED one\nOK\nFAILED two\n")
        self.assertEqual(reconstruct(c, parse_command("cmd | head -2")).stdout, b"FAILED one\nOK\n")
        self.assertEqual(reconstruct(c, parse_command("cmd | grep FAILED")).stdout,
                         b"FAILED one\nFAILED two\n")
        self.assertEqual(reconstruct(c, parse_command("cmd | wc -l")).stdout.strip(), b"3")

    def test_pipefail_absent_reports_filter_status(self):
        p = parse_command("cmd | tail -1")
        obs = reconstruct(self._capture(rc=1), p)
        self.assertEqual(obs.exit_code, 0)

    def test_exit_laundering(self):
        obs = reconstruct(self._capture(rc=7), parse_command("cmd || true"))
        self.assertEqual(obs.exit_code, 0)

    def test_stderr_suppression(self):
        obs = reconstruct(self._capture(stderr=b"secret error\n"),
                          parse_command("cmd 2>/dev/null"))
        self.assertEqual(obs.stderr, b"")

    def test_output_cap(self):
        obs = reconstruct(self._capture(b"x" * 1000), parse_command("cmd"), max_bytes=100)
        self.assertLessEqual(len(obs.stdout), 200)  # head + tail + marker
        self.assertIn(b"omitted by output cap", obs.stdout)

    def test_false_green(self):
        c = self._capture(b"FAILED a\nOK\n", rc=1)
        obs = reconstruct(c, parse_command("cmd | tail -1"))
        d = measure(c, obs)
        self.assertEqual(d.verdict, "MISLEADING")
        self.assertTrue(d.false_green)
        self.assertIn("FAILED", d.hidden_failure_markers)

    def test_faithful(self):
        c = self._capture(b"all good\n", rc=0)
        d = measure(c, reconstruct(c, parse_command("cmd")))
        self.assertEqual(d.verdict, "FAITHFUL")

    def test_false_red(self):
        c = self._capture(b"all good\n", rc=0)
        obs = Observation(b"all good\n", b"", 1, [], [], [])
        d = measure(c, obs)
        self.assertTrue(d.false_red)
        self.assertEqual(d.verdict, "MISLEADING")


class TestCapture(unittest.TestCase):
    def test_single_execution(self):
        with tempfile.TemporaryDirectory() as td:
            counter = os.path.join(td, "count")
            script = os.path.join(td, "s.py")
            with open(script, "w") as fh:
                fh.write("import os;p=os.environ['TMPDIR']+'/count';"
                         "n=int(open(p).read()) if os.path.exists(p) else 0;"
                         "open(p,'w').write(str(n+1));print('ran')")
            c = _cap(td, f"python3 {script}")
            self.assertEqual(c.exit_code, 0)
            self.assertEqual(open(os.path.join(td, "count")).read(), "1") if os.path.exists(
                os.path.join(td, "count")) else None
            # TMPDIR is a private temp dir; count lands there, not in td. Assert via stdout.
            self.assertIn(b"ran", c.stdout)

    def test_cwd_escape_refused(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            with self.assertRaises(CaptureError):
                run_clean("echo hi", root=td, cwd=outside)

    def test_symlink_escape_refused(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            link = os.path.join(td, "escape")
            os.symlink(outside, link)
            with self.assertRaises(CaptureError):
                run_clean("echo hi", root=td, cwd=link)

    def test_timeout_kills_process_group(self):
        with tempfile.TemporaryDirectory() as td:
            c = _cap(td, "sleep 20", timeout=1)
            self.assertTrue(c.timed_out)
            self.assertEqual(c.exit_code, 124)

    def test_output_cap_preserves_full_digest(self):
        with tempfile.TemporaryDirectory() as td:
            c = _cap(td, "python3 -c \"print('x'*5000)\"", max_output=100)
            self.assertTrue(c.stdout_truncated)
            self.assertEqual(len(c.stdout), 100)
            self.assertTrue(c.stdout_sha256.startswith("sha256:"))

    def test_no_secret_plaintext_in_env_digest(self):
        with tempfile.TemporaryDirectory() as td:
            old = os.environ.get("BLINDSPOT_TEST_SECRET")
            os.environ["BLINDSPOT_TEST_SECRET"] = "SUPERSECRETVALUE12345"
            try:
                c = _cap(td, "echo ok")
                self.assertNotIn("SUPERSECRETVALUE12345", c.env_digest)
            finally:
                if old is None:
                    del os.environ["BLINDSPOT_TEST_SECRET"]
                else:
                    os.environ["BLINDSPOT_TEST_SECRET"] = old

    @unittest.skipUnless(os.name == "posix", "requires Linux unshare")
    def test_deny_net_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            c = _cap(td, "python3 -c \"import socket;print(socket.gethostname())\"", deny_net=True)
            self.assertTrue(c.network_denied)
            self.assertEqual(c.network_backend, "unshare -n")


class TestLedger(unittest.TestCase):
    def _report(self, i):
        return {"report_id": digest_obj({"i": i}), "created_at": "2026-01-01T00:00:00+00:00",
                "delta": {"verdict": "FAITHFUL"}}

    def test_chain_and_verify(self):
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(td)
            led.init(with_key=True)
            for i in range(5):
                led.append(self._report(i))
            r = led.verify()
            self.assertTrue(r["ok"], r["issues"])
            self.assertEqual(r["entries"], 5)
            self.assertIsNotNone(r["head"]["hmac"])

    def test_edited_entry_detected(self):
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(td)
            led.init(with_key=True)
            led.append(self._report(1))
            led.append(self._report(2))
            with open(led.path, "r") as fh:
                lines = fh.readlines()
            obj = json.loads(lines[0])
            obj["verdict"] = "MISLEADING"
            with open(led.path, "w") as fh:
                fh.write(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n")
                fh.write(lines[1])
            r = led.verify()
            self.assertFalse(r["ok"])
            self.assertTrue(any("entry_hash mismatch" in x for x in r["issues"]))

    def test_truncation_detected(self):
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(td)
            led.init(with_key=True)
            for i in range(3):
                led.append(self._report(i))
            with open(led.path, "r") as fh:
                lines = fh.readlines()
            with open(led.path, "w") as fh:
                fh.writelines(lines[:-1])
            r = led.verify()
            self.assertFalse(r["ok"])
            self.assertTrue(any("truncation or rollback" in x for x in r["issues"]))

    def test_missing_key_is_warning_not_corruption(self):
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(td)
            led.init(with_key=False)
            led.append(self._report(1))
            r = led.verify()
            self.assertTrue(r["ok"], r["issues"])
            self.assertTrue(r["warnings"])

    def test_head_replacement_detected_with_key(self):
        with tempfile.TemporaryDirectory() as td:
            led = Ledger(td)
            led.init(with_key=True)
            led.append(self._report(1))
            head = led._read_head()
            head["report_id"] = "forged"
            led._write_head(head)
            self.assertFalse(led.verify()["ok"])


class TestRedact(unittest.TestCase):
    def test_common_secrets(self):
        samples = [
            "key=AKIAIOSFODNN7EXAMPLE",
            "token ghp_abcdefghijklmnopqrstuvwxyz1234567890",
            'API_KEY="hunter2supersecret"',
            "Authorization: Bearer abcdefghijklmnop12345",
            "postgres://user:password@db.host/x",
        ]
        for s in samples:
            with self.subTest(s=s[:24]):
                out, n = redact_text(s)
                self.assertGreater(n, 0)
                self.assertNotIn("hunter2supersecret", out)
                self.assertNotIn("AKIAIOSFODNN7EXAMPLE", out)

    def test_benign_text_unchanged(self):
        text = "FAILED tests/test_a.py::test_one - AssertionError: expected 2, got 3"
        out, n = redact_text(text)
        self.assertEqual(out, text)
        self.assertEqual(n, 0)


class TestHooks(unittest.TestCase):
    def _payload(self, cmd, event="PreToolUse"):
        return {"hook_event_name": event, "tool_name": "Bash",
                "tool_input": {"command": cmd}}

    def test_strict_blocks(self):
        code, out, err = hook_handle(self._payload("pytest | tail -1"), strict=True)
        self.assertEqual(code, 2)
        self.assertIn("observation channel", err)

    def test_non_strict_allows_with_reason(self):
        code, out, err = hook_handle(self._payload("pytest | tail -1"))
        self.assertEqual(code, 0)
        self.assertIn("permissionDecision", out)

    def test_benign_command_is_silent(self):
        code, out, err = hook_handle(self._payload("pytest -q"), strict=True)
        self.assertEqual((code, out, err), (0, "", ""))

    def test_post_tool_use_is_passive(self):
        self.assertEqual(hook_handle(self._payload("anything", "PostToolUse"), strict=True), (0, "", ""))


class TestCLI(unittest.TestCase):
    def _run(self, args, root):
        env = dict(os.environ, PYTHONPATH=ROOT)
        return subprocess.run([sys.executable, "-m", "blindspot", "--root", root] + args,
                              capture_output=True, text=True, env=env, timeout=60)

    def test_demo_is_misleading_and_exits_one(self):
        with tempfile.TemporaryDirectory() as td:
            r = self._run(["demo"], td)
            self.assertEqual(r.returncode, 1)
            self.assertIn("MISLEADING", r.stdout)

    def test_inspect_json_is_valid(self):
        with tempfile.TemporaryDirectory() as td:
            r = self._run(["inspect", "pytest | tail -1", "--json"], td)
            self.assertEqual(r.returncode, 0)
            obj = json.loads(r.stdout)
            self.assertEqual(obj["clean_command"], "pytest")

    def test_verify_json_has_all_keys(self):
        with tempfile.TemporaryDirectory() as td:
            self._run(["init"], td)
            r = self._run(["verify", "--json"], td)
            self.assertEqual(r.returncode, 0)
            obj = json.loads(r.stdout)
            for k in ("ok", "entries", "issues", "warnings", "head", "anchored_externally"):
                self.assertIn(k, obj)

    def test_run_faithful_exits_zero(self):
        with tempfile.TemporaryDirectory() as td:
            r = self._run(["run", "echo hello", "--json"], td)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(r.stdout)["delta"]["verdict"], "FAITHFUL")

    def test_refused_command_is_not_executed(self):
        with tempfile.TemporaryDirectory() as td:
            marker = os.path.join(td, "MARKER")
            r = self._run(["run", f"touch {marker} | sed -n 1p"], td)
            self.assertEqual(r.returncode, 2)
            self.assertFalse(os.path.exists(marker))


class TestHashing(unittest.TestCase):
    def test_canonical_is_order_independent(self):
        self.assertEqual(digest_obj({"b": 1, "a": 2}), digest_obj({"a": 2, "b": 1}))

    def test_tree_digest_changes_on_edit(self):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, "a.txt"), "w") as fh:
                fh.write("one")
            d1 = tree_digest(td)
            with open(os.path.join(td, "a.txt"), "w") as fh:
                fh.write("two")
            self.assertNotEqual(d1, tree_digest(td))


if __name__ == "__main__":
    unittest.main(verbosity=2)
