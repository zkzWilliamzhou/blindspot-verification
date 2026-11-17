"""Ground-truth capture.

The clean command is executed exactly ONCE. We never re-run side-effecting
work to obtain a second observation. Everything the agent "sees" is derived
later by replay.py from these captured bytes.

Safety properties are enforced here, not promised in the README.
"""

from __future__ import annotations

import os
import platform
import resource
import shlex
import signal
import shutil
import subprocess
import tempfile
import time
from typing import Dict, List, Optional

from .hashing import digest, digest_obj, stream_digest_and_head
from .model import Capture
from .redact import scrub_env_value

_ENV_ALLOWLIST = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TERM", "PYTHONIOENCODING")
_POSIX = os.name == "posix"


class CaptureError(RuntimeError):
    """Raised when a requested safety property cannot be honoured."""


def _confine(root: str, cwd: Optional[str]) -> str:
    """Resolve cwd and guarantee it stays inside the project root."""
    root_real = os.path.realpath(os.path.abspath(root))
    if not os.path.isdir(root_real):
        raise CaptureError(f"project root does not exist: {root}")
    target = os.path.realpath(os.path.abspath(cwd or root))
    try:
        if os.path.commonpath([root_real, target]) != root_real:
            raise CaptureError("cwd escapes the project root")
    except ValueError:
        raise CaptureError("cwd is on a different drive than the project root")
    if not os.path.isdir(target):
        raise CaptureError("cwd is not a directory")
    return target


def _scrub_env(workdir: str) -> tuple[Dict[str, str], str, List[str]]:
    """Minimal deterministic environment; digest everything else, store nothing."""
    env = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TZ": "UTC",
        "TERM": "dumb",
        "HOME": workdir,
        "TMPDIR": workdir,
    }
    hidden: Dict[str, str] = {}
    for name, value in sorted(os.environ.items()):
        if name in _ENV_ALLOWLIST:
            continue
        hidden[name] = digest(value.encode("utf-8", errors="replace"))
        # scrub_env_value is applied where a value might otherwise be printed.
        scrub_env_value(name, value)
    return env, digest_obj(hidden), sorted(_ENV_ALLOWLIST)


def _limits(max_output: int, timeout: int):
    """Apply POSIX resource limits in the child before exec."""
    def apply():
        if not _POSIX:
            return
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (timeout + 2, timeout + 4))
            # FSIZE bounds disk exhaustion only. It must NOT be tied to
            # --max-output: we hash the full raw stream and cap only what we
            # store. A small cap here would silently destroy ground truth.
            resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 28, 1 << 28))
            resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
            if hasattr(resource, "RLIMIT_AS"):
                resource.setrlimit(resource.RLIMIT_AS, (1 << 30, 1 << 30))
            if hasattr(resource, "RLIMIT_NPROC"):
                resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        except (OSError, ValueError):
            pass
    return apply if _POSIX else None


def _network_prefix(deny_net: bool) -> tuple[str, str]:
    """Return (prefix, backend). Never claim isolation we did not enforce."""
    if not deny_net:
        return "", "none"
    if not _POSIX or not shutil.which("unshare"):
        raise CaptureError(
            "--deny-net requires Linux 'unshare -n'; refusing to run with network enabled"
        )
    probe = subprocess.run(
        ["unshare", "-n", "true"], stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, timeout=5, check=False,
    )
    if probe.returncode != 0:
        raise CaptureError(
            "'unshare -n' is unavailable in this environment; refusing to run with network enabled"
        )
    return "unshare -n -- bash -c ", "unshare -n"


def run_clean(
    clean: str,
    *,
    root: str,
    cwd: Optional[str] = None,
    timeout: int = 30,
    max_output: int = 1_000_000,
    deny_net: bool = False,
) -> Capture:
    """Execute the clean command once and capture truth at the OS boundary."""
    if not clean.strip():
        raise CaptureError("empty clean command")
    confined = _confine(root, cwd)
    prefix, backend = _network_prefix(deny_net)
    # With unshare, the clean command becomes a single quoted argument to the
    # inner bash so `VAR=value cmd` assignment prefixes survive intact.
    full = prefix + shlex.quote(clean) if prefix else clean

    with tempfile.TemporaryDirectory(prefix="blindspot-run-") as td:
        env, env_digest, allowlist = _scrub_env(td)
        out_f = tempfile.TemporaryFile()
        err_f = tempfile.TemporaryFile()
        started = time.monotonic()
        timed_out = False
        sig = None
        argv = ["bash", "-c", full] if _POSIX else ["cmd", "/c", full]
        try:
            proc = subprocess.Popen(
                argv,
                cwd=confined,
                env=env,
                stdout=out_f,
                stderr=err_f,
                stdin=subprocess.DEVNULL,
                start_new_session=_POSIX,
                preexec_fn=_limits(max_output, timeout),
            )
        except OSError as exc:
            out_f.close()
            err_f.close()
            raise CaptureError(f"could not start command: {exc}") from exc

        try:
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            rc = 124
            sig = signal.SIGKILL
            try:
                if _POSIX:
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
            except OSError:
                pass
            proc.wait(timeout=5)
        duration_ms = int((time.monotonic() - started) * 1000)

        stdout_hash, stdout, stdout_trunc = stream_digest_and_head(out_f, max_output)
        stderr_hash, stderr, stderr_trunc = stream_digest_and_head(err_f, max_output)
        out_f.close()
        err_f.close()

    return Capture(
        command=clean,
        cwd=os.path.relpath(confined, os.path.abspath(root)).replace(os.sep, "/") or ".",
        stdout=stdout,
        stderr=stderr,
        exit_code=rc,
        signal=sig,
        duration_ms=duration_ms,
        stdout_sha256=stdout_hash,
        stderr_sha256=stderr_hash,
        stdout_truncated=stdout_trunc,
        stderr_truncated=stderr_trunc,
        timed_out=timed_out,
        output_cap_bytes=max_output,
        env_allowlist=allowlist,
        env_digest=env_digest,
        network_denied=deny_net,
        network_backend=backend,
        platform=platform.platform(),
    )
