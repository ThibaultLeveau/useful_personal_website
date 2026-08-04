"""Static import checks for the modular-monolith dependency direction."""

from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

APP_ROOT = Path(__file__).parents[1] / "app"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.add(node.module)
    return imported


def _forbidden_prefixes(path: Path) -> tuple[str, ...]:
    relative = path.relative_to(APP_ROOT)
    top_level = relative.parts[0]
    if top_level == "common":
        return ("app.api", "app.infrastructure")
    if top_level == "modules":
        return ("app.api", "app.infrastructure", "fastapi", "sqlalchemy")
    if top_level == "api":
        return ("app.infrastructure.database", "sqlalchemy")
    if relative == Path("config.py"):
        return ("app.api", "app.infrastructure")
    return ()


def test_imports_follow_inward_dependency_direction() -> None:
    """Common/domain-capability code cannot depend on transport or adapters."""
    violations: list[str] = []
    for path in sorted(APP_ROOT.rglob("*.py")):
        prefixes = _forbidden_prefixes(path)
        violations.extend(
            f"{path.relative_to(APP_ROOT)} imports {imported}"
            for imported in sorted(_imported_modules(path))
            if any(imported == prefix or imported.startswith(f"{prefix}.") for prefix in prefixes)
        )

    assert violations == []


def test_capability_ports_are_importable_typed_protocol_contracts() -> None:
    """Keep every inward adapter seam discoverable and fully annotated at runtime."""
    modules = (
        "api_access",
        "audit",
        "blog",
        "contacts",
        "experiences",
        "identity",
        "media",
        "navigation",
        "pages",
        "profile",
        "projects",
        "settings",
        "skills",
    )
    contracts: list[type[object]] = []
    for capability in modules:
        module = importlib.import_module(f"app.modules.{capability}.ports")
        contracts.extend(
            value
            for name, value in inspect.getmembers(module, inspect.isclass)
            if value.__module__ == module.__name__
            and not name.startswith("_")
            and getattr(value, "_is_protocol", False)
        )

    assert len(contracts) >= 30
    for contract in contracts:
        operations = [
            value.fget if isinstance(value, property) else value
            for name, value in contract.__dict__.items()
            if (callable(value) or isinstance(value, property))
            and (not name.startswith("_") or name == "__call__")
        ]
        assert operations or inspect.get_annotations(contract)
        assert all(
            "return" in inspect.get_annotations(operation)  # type: ignore[arg-type]
            for operation in operations
        )
