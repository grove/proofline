"""Trusted Git/working-tree snapshots and frozen identities for local Proofline runs.

Copies selected contents into an isolated repository. Does not mutate the
source worktree, dispatch models, make acceptance judgments, or publish anything.
"""
from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import stat
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
        if relative.is_absolute() or any(part == ".." or part.casefold() == ".git" for part in relative.parts):
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
    host.git(product, "-c", "gc.auto=0", "-c", "maintenance.auto=false",
             "commit", "--quiet", "--allow-empty", "-m", "Frozen Proofline comparison base")
    return source_commit, host.git(product, "rev-parse", "HEAD")


def _working_files(repo, product=None):
    """Read tracked and non-ignored untracked paths without following directory aliases."""
    indexed = git_bytes(repo, "ls-files", "--stage", "-z").split(b"\0")
    if any(entry.startswith(b"160000 ") for entry in indexed):
        raise InputGap("Submodules need a qualified observation path")
    # Git omits untracked FIFOs/devices from ls-files; reject rather than silently skip them.
    ignored = set(filter(None, git_bytes(repo, "ls-files", "--others", "--ignored",
                                       "--exclude-standard", "--directory", "-z").split(b"\0")))
    for root, directories, files in os.walk(repo, followlinks=False):
        if any(name.casefold() == ".git" and (Path(root) != repo or name != ".git")
               for name in directories + files):
            raise InputGap("Nested Git repositories cannot be captured as regular product files")
        directories[:] = [name for name in directories if name.casefold() != ".git" and
                          os.fsencode(str((Path(root) / name).relative_to(repo)) + "/") not in ignored]
        for name in files:
            path = Path(root) / name
            mode = path.lstat().st_mode
            if not (stat.S_ISREG(mode) or stat.S_ISLNK(mode)):
                try:
                    git_bytes(repo, "check-ignore", "--quiet", "--", str(path.relative_to(repo)))
                except subprocess.CalledProcessError as error:
                    if error.returncode != 1:
                        raise
                    raise InputGap("Only regular files and safe relative aliases are supported") from error
    paths = sorted(set(filter(None, git_bytes(repo, "ls-files", "--cached", "--others",
                                            "--exclude-standard", "-z").split(b"\0"))))
    entries = []
    for raw in paths:
        relative = PurePosixPath(os.fsdecode(raw))
        if relative.is_absolute() or any(part in {"..", "."} or part.casefold() == ".git"
                                         for part in relative.parts):
            raise InputGap("Unsafe working-tree path")
        directory = os.open(repo, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in relative.parts[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                os.close(directory)
                directory = child
            name = relative.name
            info = os.stat(name, dir_fd=directory, follow_symlinks=False)
            entry = {"path": str(relative), "mode": stat.S_IMODE(info.st_mode)}
            target = product / str(relative) if product else None
            if stat.S_ISLNK(info.st_mode):
                link = os.readlink(name, dir_fd=directory)
                entry.update(kind="symlink", target=link)
                if target:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.symlink_to(link)
                    if stat.S_IMODE(target.lstat().st_mode) != entry["mode"]:
                        target.chmod(entry["mode"], follow_symlinks=False)
            elif stat.S_ISREG(info.st_mode):
                descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                with os.fdopen(descriptor, "rb") as stream:
                    opened = os.fstat(stream.fileno())
                    if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                        raise InputGap("Working-tree file changed during snapshot")
                    data = stream.read()
                entry.update(kind="file", sha256=host.sha256(data))
                if target:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    target.chmod(entry["mode"])
            else:
                raise InputGap("Only regular files and safe relative aliases are supported")
            entries.append(entry)
        except FileNotFoundError:
            # Tracked deletions belong to the current working candidate, not HEAD.
            if product and (product / str(relative)).exists():
                raise InputGap("Working-tree file disappeared during snapshot")
        finally:
            os.close(directory)
    return entries


def capture_worktree(repo, product):
    """Copy current working bytes; never use the source index as a staging area."""
    repo = repo.resolve()
    if git_bytes(repo, "rev-parse", "--show-toplevel").decode().strip() != str(repo):
        raise InputGap("--repo must name the Git repository root")
    product.mkdir()
    before = _working_files(repo, product)
    validate_links(product)
    if before != _working_files(repo):
        raise InputGap("Working tree changed during snapshot; pause edits and retry")
    host.git(product, "init", "--quiet", "--template=")
    commit, tree = freeze(product)
    return {"policy": "current tracked files plus non-ignored untracked files; tracked deletions omitted",
            "entries": before, "candidate_commit": commit, "candidate_tree": tree}


def validate_links(product):
    """Permit direct relative file/directory aliases without following any symlink hop."""
    product = product.resolve()
    links = [path for path in product.rglob("*") if path.is_symlink()]
    for path in links:
        directory = os.open(product, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            link = os.readlink(path)
            parts = path.relative_to(product).parent.parts + tuple(part or "." for part in link.split("/"))
            if Path(link).is_absolute() or any(part.casefold() == ".git" for part in parts):
                raise ValueError("Absolute or Git metadata target")
            relative = []
            info = os.fstat(directory)
            for index, part in enumerate(parts):
                if part == "..":
                    if not relative:
                        raise ValueError("Out-of-tree traversal")
                    relative.pop()
                elif part != ".":
                    relative.append(part)
                info = os.stat(part, dir_fd=directory, follow_symlinks=False)
                if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                    raise ValueError("Symlink hop or special target")
                # Validate literal components before '..' can cancel them; never resolve a link chain.
                if index < len(parts) - 1:
                    child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                    os.close(directory)
                    directory = child
        except (OSError, ValueError, RuntimeError) as exc:
            raise InputGap("Symlink escapes the candidate, is missing, cyclic, or traverses an unsafe target") from exc
        finally:
            os.close(directory)
        target = product.joinpath(*relative)
        if stat.S_ISDIR(info.st_mode) and any(alias.is_relative_to(target) for alias in links):
            raise InputGap("Directory aliases cannot contain nested aliases or cycles")


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
    # Background packing would change the Git bytes after the candidate is frozen.
    host.git(product, "-c", "gc.auto=0", "-c", "maintenance.auto=false",
             "commit", "--quiet", "--allow-empty", "-m", "Frozen Proofline implementation candidate")
    return host.git(product, "rev-parse", "HEAD"), host.git(product, "rev-parse", "HEAD^{tree}")



