"""Fail CI on broken local Markdown links and unsafe repository artifacts."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".venv", "__pycache__", "data", "work"}
EXCLUDED_DATA_CHILDREN = {ROOT / "data" / "generated", ROOT / "data" / "processed"}
UNSAFE_NAMES = {".env", "credentials.json", "secrets.json"}
UNSAFE_SUFFIXES = {".bak", ".pbix", ".pfx", ".key"}
MAX_FILE_BYTES = 10 * 1024 * 1024
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def repository_files() -> list[Path]:
    """Return auditable files while excluding generated and local-only directories."""
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(parent in EXCLUDED_DATA_CHILDREN for parent in path.parents):
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        files.append(path)
    return files


def markdown_link_errors(files: list[Path]) -> list[str]:
    """Find local Markdown links whose target does not exist."""
    errors: list[str] = []
    for document in (path for path in files if path.suffix.lower() == ".md"):
        text = document.read_text(encoding="utf-8")
        for raw_target in LINK_PATTERN.findall(text):
            target = raw_target.strip().strip("<>").split("#", maxsplit=1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (document.parent / unquote(target)).resolve()
            if not resolved.exists():
                errors.append(f"Broken link in {document.relative_to(ROOT)}: {raw_target}")
    return errors


def artifact_errors(files: list[Path]) -> list[str]:
    """Find secrets, binary report files, and oversized tracked candidates."""
    errors: list[str] = []
    for path in files:
        relative = path.relative_to(ROOT)
        if path.name.lower() in UNSAFE_NAMES or path.suffix.lower() in UNSAFE_SUFFIXES:
            errors.append(f"Unsafe repository artifact: {relative}")
        if path.stat().st_size > MAX_FILE_BYTES:
            errors.append(f"File exceeds 10 MB: {relative} ({path.stat().st_size:,} bytes)")
    return errors


def main() -> int:
    """Run repository delivery checks and return a process exit code."""
    files = repository_files()
    errors = markdown_link_errors(files) + artifact_errors(files)
    if errors:
        print("Repository audit failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Repository audit passed for {len(files):,} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
