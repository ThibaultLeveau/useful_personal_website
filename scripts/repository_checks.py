"""Repository-level checks that do not depend on either application."""

from __future__ import annotations

import csv
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
OWNER_DECISION_IDS = {
    "analytics_error_reporting",
    "backup_recovery_ownership",
    "contact_audit_retention",
    "hostname_trusted_origins",
    "legal_privacy_identity",
    "monitoring_incident_routing",
    "production_object_storage",
}
ACCESSIBILITY_ROW_IDS = {f"AT-{number:03}" for number in range(1, 14)}
ACCESSIBILITY_FIELDS = {
    "assistive_technology",
    "browser",
    "criteria",
    "defect_id",
    "device",
    "executed_at_utc",
    "executor",
    "finding",
    "id",
    "input",
    "journey",
    "platform",
    "result",
    "retest_evidence",
    "theme",
    "tool_versions",
    "viewport",
}


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


def check_release_acceptance(problems: list[str]) -> None:
    owner_path = ROOT / "docs/evidence/M14/prerequisites/owner-decisions.json"
    try:
        owner = json.loads(owner_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        problems.append("M14 owner decision record is missing")
        return
    except json.JSONDecodeError:
        return
    decisions = owner.get("decisions", [])
    ids = {decision.get("id") for decision in decisions}
    if ids != OWNER_DECISION_IDS or len(decisions) != len(OWNER_DECISION_IDS):
        problems.append(
            "M14 owner decision record does not contain the exact required decisions"
        )
    accepted = 0
    for decision in decisions:
        status = decision.get("status")
        if status not in {"pending", "accepted"}:
            problems.append(
                f"M14 owner decision {decision.get('id')!r} has invalid status"
            )
        if status == "accepted":
            accepted += 1
            required = ("decision", "approved_by", "approved_at_utc", "evidence")
            if any(not decision.get(field) for field in required):
                problems.append(
                    f"M14 owner decision {decision.get('id')!r} lacks acceptance evidence"
                )
    expected_overall = (
        "accepted" if accepted == len(OWNER_DECISION_IDS) else "pending_owner_input"
    )
    if owner.get("overall_status") != expected_overall:
        problems.append(
            "M14 owner decision overall status does not match its decisions"
        )

    matrix_path = ROOT / "docs/evidence/M14/accessibility/wcag-2.2-aa-matrix.csv"
    try:
        with matrix_path.open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source)
            rows = list(reader)
    except FileNotFoundError:
        problems.append("M14 accessibility matrix is missing")
        return
    if set(reader.fieldnames or ()) != ACCESSIBILITY_FIELDS:
        problems.append(
            "M14 accessibility matrix fields do not match the recording contract"
        )
    ids = {row.get("id") for row in rows}
    if ids != ACCESSIBILITY_ROW_IDS or len(rows) != len(ACCESSIBILITY_ROW_IDS):
        problems.append(
            "M14 accessibility matrix does not contain the exact required rows"
        )
    for row in rows:
        result = row.get("result")
        if result not in {"NOT_RUN", "PASS", "FAIL", "BLOCKED"}:
            problems.append(
                f"M14 accessibility row {row.get('id')!r} has invalid result"
            )
        if result == "PASS":
            required = ("tool_versions", "device", "executor", "executed_at_utc")
            if any(not row.get(field) for field in required):
                problems.append(
                    f"M14 accessibility row {row.get('id')!r} lacks pass evidence"
                )
        if result == "FAIL" and (not row.get("finding") or not row.get("defect_id")):
            problems.append(
                f"M14 accessibility row {row.get('id')!r} lacks defect evidence"
            )
        if result == "BLOCKED" and not row.get("finding"):
            problems.append(
                f"M14 accessibility row {row.get('id')!r} lacks blocker evidence"
            )


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

    screenshot_inventory = subprocess.run(
        [sys.executable, "scripts/generate_screenshot_inventory.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if screenshot_inventory.returncode:
        problems.append(
            screenshot_inventory.stdout.strip() or screenshot_inventory.stderr.strip()
        )
    check_release_acceptance(problems)

    if problems:
        print("Repository checks failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print(f"Repository checks passed for {len(files)} visible files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
