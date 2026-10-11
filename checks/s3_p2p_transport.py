"""Benchmark-only transport: one Codex sandbox, with private scoring inputs denied."""
import json
import os
from pathlib import Path
import uuid

from checks.host_probe import ROOT, toml


def profile(scratch, blocked):
    scratch = Path(scratch).resolve()
    executions = (Path.home() / ".p2p/executions").resolve()
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).resolve()
    filesystem = {":root": "read", str(ROOT): "deny", str(codex_home): "deny",
                  str(Path.home() / ".codex/RTK.md"): "read", str(executions): "deny"}
    if scratch.is_relative_to(executions):
        filesystem[str(executions / scratch.relative_to(executions).parts[0])] = "read"
    return {"filesystem": {**filesystem, str(scratch): "write",
            str(scratch / ".git"): "read",
            **{str(Path(path).resolve()): "deny" for path in blocked}},
            "network": {"enabled": False}}


def command(executable, args, blocked):
    if args == ["--version"]:
        return [executable, "--no-daemon", *args]
    if not args or args[0] != "exec":
        raise ValueError("Only the declared P2P exec transport is supported")
    expected = {"sandbox_workspace_write.network_access=false",
                "sandbox_workspace_write.exclude_slash_tmp=true",
                "sandbox_workspace_write.exclude_tmpdir_env_var=true"}
    result, removed = [], set()
    index = 0
    scratch = None
    sandbox = False
    while index < len(args):
        value = args[index]
        if value == "--sandbox":
            if sandbox or args[index + 1] != "workspace-write":
                raise ValueError("Unexpected legacy sandbox")
            sandbox = True
            index += 2
            continue
        if value == "-c":
            config = args[index + 1]
            if config.startswith(("sandbox", "permissions.", "default_permissions=")):
                if config not in expected or config in removed:
                    raise ValueError("Unexpected permission configuration")
                removed.add(config)
                index += 2
                continue
        if value == "-C":
            scratch = args[index + 1]
        result.append(value)
        index += 1
    if not sandbox or removed != expected or scratch is None or result[-1] != "-":
        raise ValueError("Incomplete declared P2P transport")
    return [executable, "--no-daemon", *result[:-1], "-c", "default_permissions=s3_p2p",
            "-c", "permissions.s3_p2p=" + toml(profile(scratch, blocked)), "-"]


def launch(executable, args, blocked, records):
    argv = command(executable, args, blocked)
    (Path(records) / (uuid.uuid4().hex + ".json")).write_text(
        json.dumps({"requested_argv": args, "effective_argv": argv}, indent=2) + "\n")
    os.execv(executable, argv)
