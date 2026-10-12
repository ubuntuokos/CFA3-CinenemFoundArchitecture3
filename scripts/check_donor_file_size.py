#!/usr/bin/env python3
"""Fail-closed pre-upload and CI guard for newly added/modified donor data files."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LIMIT_BYTES = 996147
DATA_SUFFIXES = {
    ".json", ".jsonl", ".ndjson", ".csv", ".tsv", ".db", ".sqlite",
    ".sqlite3", ".parquet", ".yaml", ".yml", ".xml", ".txt", ".toml",
}

def is_donor_data(path):
    """Match donor data/indices, excluding Python code, policies and prose docs."""
    normalized = Path(path).as_posix().lower()
    filename = Path(normalized).name
    if Path(filename).suffix not in DATA_SUFFIXES:
        return False
    if "/policies/" in "/" + normalized or normalized.startswith("docs/"):
        return False
    if "donor" in filename or "donor" in normalized.split("/"):
        return True
    if filename.startswith("cfa3-source-lifecycle-"):
        return True
    return False

def validate_changed_files(paths, root=ROOT, limit=LIMIT_BYTES):
    """Only new/modified paths are gated; untouched historical files are retained."""
    root = Path(root).resolve()
    issues = []
    checked = []
    for name in sorted(set(paths)):
        if not is_donor_data(name):
            continue
        path = root / name
        try:
            if not path.is_file() or not path.resolve().is_relative_to(root):
                raise OSError("missing, non-file, or outside repository")
            size = path.stat().st_size
        except OSError as error:
            issues.append(f"{name}: cannot measure donor data file ({error})")
            continue
        checked.append((name, size))
        if size > limit:
            issues.append(
                f"{name}: {size} bytes exceeds {limit} bytes; "
                "STOP/BLOCKER: split and preserve all data before upload"
            )
    return issues, checked

def changed_paths(base=None, staged=False):
    if bool(base) == bool(staged):
        raise ValueError("provide exactly one of --base or --staged")
    command = ["git", "diff", "--name-only", "-z", "--diff-filter=AMR"]
    if staged:
        command.append("--cached")
    else:
        command.append(f"{base}...HEAD")
    result = subprocess.run(command, cwd=ROOT, capture_output=True, check=True)
    return [name.decode("utf-8") for name in result.stdout.split(b"\0") if name]

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--base", help="Git base revision to diff against HEAD")
    selection.add_argument("--staged", action="store_true",
                           help="Check staged changes before git push/upload")
    args = parser.parse_args(argv)
    try:
        files = changed_paths(base=args.base, staged=args.staged)
        errors, checked = validate_changed_files(files)
    except (OSError, subprocess.CalledProcessError, UnicodeError, ValueError) as error:
        print(f"DONOR_FILE_SIZE_FAIL: unable to enumerate changes: {error}",
              file=sys.stderr)
        return 1
    for name, size in checked:
        print(f"DONOR_FILE_SIZE_CHECK: {name}: {size}/{LIMIT_BYTES} bytes")
    for error in errors:
        print("DONOR_FILE_SIZE_FAIL:", error, file=sys.stderr)
    if errors:
        return 1
    print(f"DONOR_FILE_SIZE_PASS: {len(checked)} changed donor data files checked; "
          "unchanged historical files preserved (not a deduplication or publication PASS)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
