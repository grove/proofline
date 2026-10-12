"""Benchmark-only transport: one Codex sandbox, with private scoring inputs denied."""
import json
import os
from pathlib import Path
import sys
import tomllib
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
    scratch_path = Path(scratch).resolve()
    runtime = next((parent for parent in scratch_path.parents
                    if (parent / "repository.git").is_dir()
                    and (parent / "workspace/.git").is_file()), None)
    if runtime is not None:
        # Git cannot traverse the denied executions ancestor; rebind relative paths per invocation.
        git = Path('/Library/Developer/CommandLineTools/usr/bin/git')
        if not git.is_file():
            git = Path('/usr/bin/git')
        binaries = runtime / 'scratch/transport-git'
        binaries.mkdir(parents=True, exist_ok=True)
        wrapper = binaries / 'git'
        wrapper.write_text(f'#!{sys.executable}\nimport os,sys\n'
            f'os.environ["GIT_DIR"]=os.path.relpath({str(runtime / "repository.git")!r})\n'
            f'os.environ["GIT_WORK_TREE"]=os.path.relpath({str(runtime / "workspace")!r})\n'
            f'os.execv({str(git)!r},[{str(git)!r},*sys.argv[1:]])\n')
        wrapper.chmod(0o755)
        for index, value in enumerate(result):
            if value.startswith("shell_environment_policy.set="):
                environment = tomllib.loads(value)["shell_environment_policy"]["set"]
                environment.pop('GIT_DIR', None)
                environment.pop('GIT_WORK_TREE', None)
                environment['PATH'] = os.pathsep.join((str(binaries), str(Path(sys.executable).resolve().parent), environment['PATH']))
                result[index] = "shell_environment_policy.set=" + toml(environment)
                break
        else:
            raise ValueError("Missing declared shell environment")
        result[-1:-1] = ["-c", "allow_login_shell=false", "-c", "developer_instructions=" + json.dumps(
            'Use git from PATH; this transport binds it to the candidate workspace from any cwd. '
            'Absolute Git discovery may fail under the protected executions-root profile.')]
    return [executable, "--no-daemon", *result[:-1], "-c", "default_permissions=s3_p2p",
            "-c", "permissions.s3_p2p=" + toml(profile(scratch, blocked)), "-"]


def launch(executable, args, blocked, records, preferences=None):
    if preferences is not None and args != ["--version"]:
        args = list(args)
        for key, value in preferences.items():
            if key not in {"model", "model_reasoning_effort"}:
                raise ValueError("Only declared model preferences can be overridden")
            for index, arg in enumerate(args):
                if arg.startswith(key + "=") and index and args[index - 1] == "-c":
                    args[index] = key + "=" + toml(value)
                    break
            else:
                args[-1:-1] = ["-c", key + "=" + toml(value)]
    argv = command(executable, args, blocked)
    (Path(records) / (uuid.uuid4().hex + ".json")).write_text(
        json.dumps({"requested_argv": args, "effective_argv": argv}, indent=2) + "\n")
    os.execv(executable, argv)
