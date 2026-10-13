"""Trusted Git snapshots and frozen candidate identities for local Proofline runs.

Copies tracked Git contents into an isolated repository. Does not mutate the
source worktree, dispatch models, make acceptance judgments, or publish anything.
"""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import subprocess
from checks import host_probe as host


class InputGap(ValueError):
    pass


def git_bytes(repo, *args):
    return subprocess.check_output(["git", "-c", "core.hooksPath=" + os.devnull, *args],
        cwd=repo, stderr=subprocess.PIPE, timeout=30,
        env={"PATH": os.defpath, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
             "GIT_OPTIONAL_LOCKS": "0"})


def capture_base(repo, product):
    """Copy exact tracked blobs/modes, without export-ignore, filters, hooks, or user worktree writes."""
    repo = repo.resolve()
    if git_bytes(repo, "rev-parse", "--show-toplevel").decode().strip() != str(repo):
        raise InputGap("--repo must name the Git repository root")
    if git_bytes(repo, "status", "--porcelain", "--untracked-files=normal"):
        raise InputGap("Source repository has local changes. Preserve them in a separate committed snapshot before delivery.")
    source_commit = git_bytes(repo, "rev-parse", "HEAD").decode().strip()
    entries = git_bytes(repo, "ls-tree", "-rz", "--full-tree", source_commit).split(b"\0")
    product.mkdir()
    links = []
    for entry in filter(None, entries):
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        relative = PurePosixPath(os.fsdecode(raw_path))
        if mode not in {"100644", "100755", "120000"} or kind != "blob":
            raise InputGap("Submodules need a qualified observation path")
        if relative.is_absolute() or any(part in {"..", ".git"} for part in relative.parts):
            raise InputGap("Unsafe Git product path")
        target = product / str(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = git_bytes(repo, "cat-file", "blob", oid)
        if mode == "120000":
            links.append((target, os.fsdecode(raw)))
        else:
            target.write_bytes(raw)
            target.chmod(0o755 if mode == "100755" else 0o644)
    for target, link in links:
        target.symlink_to(link)
    validate_links(product)
    host.git(product, "init", "--quiet", "--template=")
    host.git(product, "add", "--force", "--all")
    host.git(product, "commit", "--quiet", "--allow-empty", "-m", "Frozen Proofline comparison base")
    return source_commit, host.git(product, "rev-parse", "HEAD")


def validate_links(product):
    """Permit only aliases to regular files wholly inside this product snapshot."""
    product = product.resolve()
    for path in product.rglob("*"):
        if not path.is_symlink():
            continue
        try:
            link = Path(os.readlink(path))
            lexical = Path(os.path.abspath(path.parent / link)).relative_to(product.resolve())
            target = path.resolve(strict=True)
            relative = target.relative_to(product.resolve())
        except (OSError, ValueError, RuntimeError) as exc:
            raise InputGap("Symlink escapes the candidate, is missing, or is cyclic") from exc
        if (not target.is_file() or link.is_absolute() or
                any(part.casefold() == ".git" for part in (*lexical.parts, *relative.parts))):
            raise InputGap("Symlinks must be relative aliases to regular product files outside Git metadata")


def freeze(product):
    # Reject unsafe aliases and special files before Git processes model-produced content.
    validate_links(product)
    for path in product.rglob("*"):
        parts = path.relative_to(product).parts
        if parts[0] == ".git":
            continue
        if any(part.casefold() == ".git" for part in parts):
            raise InputGap("Nested Git repositories cannot be frozen as regular product files")
        if not (path.is_file() or path.is_dir()):
            raise InputGap("Candidate introduced a link or special file; its execution boundary is not qualified")
    host.git(product, "add", "--force", "--all")
    host.git(product, "commit", "--quiet", "--allow-empty", "-m", "Frozen Proofline implementation candidate")
    return host.git(product, "rev-parse", "HEAD"), host.git(product, "rev-parse", "HEAD^{tree}")



