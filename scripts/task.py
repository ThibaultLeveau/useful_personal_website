"""Cross-platform root task runner."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*command: str) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def require_workspace(name: str) -> Path:
    workspace = ROOT / name
    if not workspace.is_dir():
        raise SystemExit(
            f"{name}/ has not been dispatched yet; run only the foundation tasks "
            "available for the current milestone."
        )
    return workspace


def doctor() -> None:
    expected_python = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
    expected_node = (ROOT / ".nvmrc").read_text(encoding="utf-8").strip()
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    print(f"Expected Python: {expected_python}")
    print(f"Expected Node: {expected_node}")
    print(f"Expected package manager: {package['packageManager'].split('+', 1)[0]}")
    run(sys.executable, "-m", "uv", "--version")
    run("node", "--version")
    run("corepack", "--version")
    run("pnpm", "--version")


def backend_check() -> None:
    require_workspace("backend")
    run(sys.executable, "-m", "uv", "run", "--frozen", "ruff", "check", "backend")
    run(
        sys.executable,
        "-m",
        "uv",
        "run",
        "--frozen",
        "ruff",
        "format",
        "--check",
        "backend",
    )
    run(
        sys.executable,
        "-m",
        "uv",
        "run",
        "--frozen",
        "mypy",
        "--config-file",
        "backend/pyproject.toml",
        "backend",
    )
    run(sys.executable, "-m", "uv", "run", "--frozen", "pytest", "backend")


def frontend_check() -> None:
    require_workspace("frontend")
    run("pnpm", "--dir", "frontend", "lint")
    run("pnpm", "--dir", "frontend", "typecheck")
    run("pnpm", "--dir", "frontend", "test", "--run")
    run("pnpm", "--dir", "frontend", "build")


def verify() -> None:
    run(sys.executable, "scripts/repository_checks.py")
    run("git", "diff", "--check")
    run(sys.executable, "-m", "uv", "lock", "--check")


def api_generate() -> None:
    run(sys.executable, "scripts/generate_api_client.py")


def api_check() -> None:
    run(
        sys.executable,
        "-m",
        "uv",
        "run",
        "--frozen",
        "python",
        "scripts/export_openapi.py",
    )
    run(sys.executable, "scripts/validate_openapi.py")
    frontend_check()


def seed_demo() -> None:
    backend = require_workspace("backend")
    result = subprocess.run(
        (
            sys.executable,
            "-m",
            "uv",
            "run",
            "--project",
            "..",
            "--frozen",
            "python",
            "-m",
            "app.commands.seed_demo",
        ),
        cwd=backend,
        check=False,
    )
    if result.returncode:
        raise SystemExit(result.returncode)


COMMANDS = {
    "doctor": doctor,
    "repo-check": lambda: run(sys.executable, "scripts/repository_checks.py"),
    "verify": verify,
    "backend-check": backend_check,
    "frontend-check": frontend_check,
    "api-generate": api_generate,
    "api-check": api_check,
    "seed-demo": seed_demo,
}


def help_text() -> None:
    print("Available tasks:")
    print("  doctor          show and verify the pinned local tools")
    print("  repo-check      validate repository hygiene and documentation links")
    print("  verify          run all currently available foundation checks")
    print("  backend-check   lint, format-check, type-check, and test backend/")
    print("  frontend-check  lint, type-check, test, and build frontend/")
    print("  api-generate    export OpenAPI and regenerate the typed client")
    print("  api-check       validate the contract and compiled client boundary")
    print("  seed-demo       explicitly converge fictional non-production site content")


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    if command == "help":
        help_text()
        return 0
    action = COMMANDS.get(command)
    if action is None:
        print(f"Unknown task: {command}", file=sys.stderr)
        help_text()
        return 2
    action()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
