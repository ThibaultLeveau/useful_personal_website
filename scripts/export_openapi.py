"""Export the canonical OpenAPI document deterministically."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
OUTPUT = ROOT / "docs" / "api" / "openapi.json"


def main() -> int:
    sys.path.insert(0, str(BACKEND))
    from app.main import create_app

    schema = create_app().openapi()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    OUTPUT.write_text(serialized, encoding="utf-8", newline="\n")
    print(
        f"Exported {len(schema.get('paths', {}))} paths to {OUTPUT.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
