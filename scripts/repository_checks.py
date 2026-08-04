"""Repository-level checks that do not depend on either application."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_NAMES = {
    ".editorconfig",
    ".gitignore",
    ".nvmrc",
    ".python-version",
    "Makefile",
}
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
LOCAL_PATHS = (
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
    re.compile(r"/(?:Users|home)/[^/\s]+/"),
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)


def repository_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


def is_text(path: Path) -> bool:
    return path.name in TEXT_NAMES or path.suffix.lower() in TEXT_SUFFIXES


def check_markdown_link(source: Path, target: str) -> str | None:
    clean = target.strip().strip("<>").split(maxsplit=1)[0]
    if not clean or clean.startswith(("#", "http://", "https://", "mailto:")):
        return None
    clean = clean.split("#", 1)[0].split("?", 1)[0]
    if not clean:
        return None
    destination = (source.parent / clean).resolve()
    if not destination.exists():
        return f"{source.relative_to(ROOT)}: broken relative link {target!r}"
    return None


def main() -> int:
    problems: list[str] = []
    files = repository_files()
    for path in files:
        if not path.is_file() or not is_text(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            problems.append(f"{path.relative_to(ROOT)}: not valid UTF-8")
            continue
        relative = path.relative_to(ROOT)
        if content and not content.endswith("\n"):
            problems.append(f"{relative}: missing final newline")
        for number, line in enumerate(content.splitlines(), start=1):
            if line.rstrip(" \t") != line and path.suffix.lower() != ".md":
                problems.append(f"{relative}:{number}: trailing whitespace")
        for pattern in LOCAL_PATHS:
            if pattern.search(content):
                problems.append(
                    f"{relative}: contains a machine-specific absolute path"
                )
        for pattern in SECRET_PATTERNS:
            if pattern.search(content):
                problems.append(f"{relative}: contains likely secret material")
        if path.suffix.lower() == ".md":
            for match in MARKDOWN_LINK.finditer(content):
                issue = check_markdown_link(path, match.group(1))
                if issue:
                    problems.append(issue)
        if path.suffix.lower() == ".json":
            try:
                json.loads(content)
            except json.JSONDecodeError as exc:
                problems.append(f"{relative}: invalid JSON: {exc}")
        if path.suffix.lower() == ".toml":
            try:
                tomllib.loads(content)
            except tomllib.TOMLDecodeError as exc:
                problems.append(f"{relative}: invalid TOML: {exc}")

    if problems:
        print("Repository checks failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print(f"Repository checks passed for {len(files)} visible files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
