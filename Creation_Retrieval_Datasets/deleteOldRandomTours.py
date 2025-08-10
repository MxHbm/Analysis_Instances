#!/usr/bin/env python3
"""
Clean all files inside target subfolders (e.g., 'input', 'output') across a tree,
fast and safely, using multithreading. By default, keeps the directories and
removes only files (recursively). Optionally prunes now-empty dirs.

Usage examples:
  python clean_subfolders.py /path/to/root
  python clean_subfolders.py . --targets input output --prune-empty-dirs --yes
  python clean_subfolders.py "C:\projects\myrepo" --workers 32

This script is OS-safe and skips symlinks by default.
"""
import argparse
import concurrent.futures as futures
import os
import sys
import stat
from pathlib import Path
from typing import Iterable, List, Tuple

def human_bytes(n: int) -> str:
    units = ["B","KB","MB","GB","TB"]
    i = 0
    f = float(n)
    while f >= 1024 and i < len(units)-1:
        f /= 1024.0
        i += 1
    return f"{f:.1f} {units[i]}"

def add_write_permission(p: Path) -> None:
    try:
        mode = os.stat(p, follow_symlinks=False).st_mode
        os.chmod(p, mode | stat.S_IWRITE)
    except Exception:
        pass  # best-effort

def unlink_file(p: Path, *, dry: bool=False, include_symlinks: bool=False) -> Tuple[bool,int,str]:
    """Return (deleted?, bytes_freed, message)"""
    try:
        if not p.exists() and not p.is_symlink():
            return (False, 0, f"skip: missing {p}")
        if p.is_dir():
            return (False, 0, f"skip: directory {p}")
        if p.is_symlink() and not include_symlinks:
            return (False, 0, f"skip: symlink {p}")
        size = 0
        try:
            size = p.stat().st_size
        except Exception:
            pass
        if dry:
            return (True, size, f"dry-run: {p}")
        add_write_permission(p)
        p.unlink(missing_ok=True)
        return (True, size, f"deleted: {p}")
    except Exception as e:
        return (False, 0, f"error: {p} -> {e}")

def iter_target_dirs(root: Path, targets: List[str], case_insensitive: bool=True) -> Iterable[Path]:
    targets_set = set(t.lower() if case_insensitive else t for t in targets)
    for dirpath, dirnames, _filenames in os.walk(root):
        base = os.path.basename(dirpath)
        if (base.lower() if case_insensitive else base) in targets_set:
            yield Path(dirpath)

def iter_files_under(d: Path, include_symlinks: bool=False) -> Iterable[Path]:
    # Fast recursive scandir
    stack = [d]
    while stack:
        cur = stack.pop()
        try:
            with os.scandir(cur) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            if include_symlinks and not entry.is_dir(follow_symlinks=False):
                                yield Path(entry.path)
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                        else:
                            yield Path(entry.path)
                    except Exception:
                        continue
        except Exception:
            continue

def prune_empty_dirs(d: Path) -> int:
    """Remove empty subdirectories under d. Returns count removed."""
    removed = 0
    for dirpath, dirnames, filenames in os.walk(d, topdown=False):
        if dirnames or filenames:
            continue
        try:
            Path(dirpath).rmdir()
            removed += 1
        except Exception:
            pass
    return removed

def main():
    ap = argparse.ArgumentParser(description="Delete files inside target subfolders across a tree using multithreading.")
    ap.add_argument("root", type=Path, help="Root directory to scan")
    ap.add_argument("--targets", nargs="+", default=["input","output"],
                    help="Names of subfolders whose contents will be deleted (default: input output)")
    ap.add_argument("--workers", type=int, default=max(4, min(32, (os.cpu_count() or 4)*5)),
                    help="Number of threads (default: IO-friendly heuristic)")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be deleted, do not delete")
    ap.add_argument("--include-symlinks", action="store_true", help="Also delete symlinked files")
    ap.add_argument("--prune-empty-dirs", action="store_true", help="After deleting files, remove now-empty dirs under each target")
    ap.add_argument("--yes", action="store_true", help="Do not prompt for confirmation")
    args = ap.parse_args()

    root = args.root.resolve()
    if not root.exists() or not root.is_dir():
        print(f"Error: root '{root}' does not exist or is not a directory.", file=sys.stderr)
        sys.exit(2)

    target_dirs = list(iter_target_dirs(root, args.targets))
    if not target_dirs:
        print("No target directories found.", file=sys.stderr)
        sys.exit(0)

    print(f"Root: {root}")
    print(f"Targets: {', '.join(args.targets)} (case-insensitive match)")
    print(f"Found {len(target_dirs)} target directories.")
    for td in target_dirs[:10]:
        print(f"  - {td}")
    if len(target_dirs) > 10:
        print(f"  ... (+{len(target_dirs)-10} more)")

    if not args.yes and not args.dry_run:
        reply = input("Proceed with deletion? [y/N] ").strip().lower()
        if reply not in ("y","yes"):
            print("Aborted.")
            sys.exit(0)

    # Collect files
    files = []
    for td in target_dirs:
        files.extend(iter_files_under(td, include_symlinks=args.include_symlinks))

    total = len(files)
    if total == 0:
        print("No files to delete.")
        sys.exit(0)
    print(f"Deleting {total} files using {args.workers} threads{' (dry-run)' if args.dry_run else ''}...")

    deleted = 0
    freed = 0
    with futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for ok, bytes_freed, msg in ex.map(lambda p: unlink_file(p, dry=args.dry_run, include_symlinks=args.include_symlinks), files):
            if ok:
                deleted += 1
                freed += bytes_freed

    print(f"Done. {'Would have deleted' if args.dry_run else 'Deleted'} {deleted}/{total} files; space {'would free' if args.dry_run else 'freed'} ≈ {human_bytes(freed)}.")

    if args.prune_empty_dirs:
        total_removed = 0
        for td in target_dirs:
            total_removed += prune_empty_dirs(td)
        print(f"Pruned {total_removed} empty directories under targets.")

if __name__ == "__main__":
    main()

# Call like this: python deleteOldRandomTours.py C:\Users\mahu123a\Documents\Data\RandomDataGeneration
# Template Call py .\clean_subfolders.py "C:\path\to\your\root" --dry-run

