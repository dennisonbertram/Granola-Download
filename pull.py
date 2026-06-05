#!/usr/bin/env python3
"""One-command Granola backup: refresh token -> download -> rename.

Granola's WorkOS refresh tokens are single-use and rotate on every use, so a
token saved in config.json goes stale as soon as the Granola app refreshes its
own session. This script always re-extracts a fresh token from the live app
storage first, so "pull" just works.

Usage:
    python3 pull.py [OUTPUT_DIR] [-- <extra download_transcripts.py args>]

Defaults OUTPUT_DIR to ./transcripts_output. Extra args after `--` are passed
through to granola/download_transcripts.py (e.g. --overwrite).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable  # run children with the same interpreter (the repo venv)


def _run(label, cmd):
    print(f"\n=== {label} ===", flush=True)
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        sys.exit(f"[pull] step failed: {label} (exit {result.returncode})")


def main():
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        i = argv.index("--")
        extra = argv[i + 1:]
        argv = argv[:i]
    output_dir = argv[0] if argv else "transcripts_output"

    # 1. Fresh credentials from the live Granola app storage.
    _run("extract token", [PY, str(ROOT / "extract_config.py")])

    # 2. Download (skips already-downloaded docs unless --overwrite passed).
    _run("download transcripts",
         [PY, str(ROOT / "granola" / "download_transcripts.py"), output_dir, *extra])

    # 3. Rename freshly downloaded ID folders to readable names (idempotent).
    print("\n=== rename folders ===", flush=True)
    sys.path.insert(0, str(ROOT / "granola"))
    import rename_folders  # noqa: E402  (stdlib-only, safe import)
    renamed = rename_folders.rename_all(output_dir)
    print(f"renamed {len(renamed)} new folder(s)")
    for n in renamed:
        print(" ", n)

    print("\n[pull] done.")


if __name__ == "__main__":
    main()
