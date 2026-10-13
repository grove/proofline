"""Native command execution receipts for the bounded runner.

This is host-observed sandbox evidence, not a model verifier.
"""
import json
from pathlib import Path
import subprocess
import sys

from checks import host_probe as host


def write_record(path, record):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.replace(path)


def oracle_runner(codex, inputs, private, receipts):
    def run(argv, *, cwd, timeout, **unused):
        scratch = Path(cwd).resolve()
        command = host.sandbox_argv(codex, inputs, scratch, private)
        command = command[:command.index("--") + 1] + [str(Path(sys.executable).resolve()),
            "-I", "-B", "-c", "import json,os,sys; a=json.loads(sys.argv[1]); os.execv(a[0],a)",
            json.dumps(argv, ensure_ascii=True)]
        receipt = host.run_command(command, scratch, timeout,
                                   env={"PATH": "/usr/bin:/bin", "TMPDIR": str(scratch)})
        receipts.append(receipt)
        if receipt.get("error") or receipt["timed_out"] or any(
                receipt.get(key) for key in ("stdout_truncated", "stderr_truncated")):
            raise OSError("Sandboxed check observation unavailable")
        return subprocess.CompletedProcess(argv, receipt["exit_code"],
                                           receipt["stdout"], receipt["stderr"])
    return run
