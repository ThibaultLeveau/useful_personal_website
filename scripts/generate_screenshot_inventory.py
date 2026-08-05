"""Generate the deterministic M14 inventory for repository screenshot evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT / "docs" / "evidence"
OUTPUT = EVIDENCE_ROOT / "M14" / "screenshots" / "inventory.json"
VIEWPORT = re.compile(r"(?:^|-)(320|360|390|768|1024|1280|1440|1920)(?:-|$)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metadata(path: Path) -> dict[str, object]:
    relative = path.relative_to(ROOT).as_posix()
    stem = path.stem.lower()
    width = VIEWPORT.search(stem)
    theme = "light" if "-light" in stem else "dark" if "-dark" in stem else None
    milestone = path.relative_to(EVIDENCE_ROOT).parts[0]
    return {
        "path": relative,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "milestone": milestone,
        "journey": path.stem,
        "viewport_css_width": int(width.group(1)) if width else None,
        "zoom_percent": 400
        if "zoom-400" in stem or "400-percent-zoom" in stem
        else None,
        "theme": theme,
        "browser": None,
        "device": "emulated_css_viewport" if width else None,
        "device_pixel_ratio": None,
        "fixture": "fictional_demo" if milestone == "M13" else None,
        "captured_at_utc": None,
        "reviewer": None,
        "sanitization_status": "documented_synthetic"
        if milestone == "M13"
        else "unrecorded",
    }


def rendered_inventory() -> str:
    screenshots = sorted(
        path
        for path in EVIDENCE_ROOT.rglob("*.png")
        if OUTPUT.parent not in path.parents
    )
    items = [metadata(path) for path in screenshots]
    payload = {
        "schema_version": "1.0",
        "generated_by": "scripts/generate_screenshot_inventory.py",
        "count": len(items),
        "limitations": [
            "Historical milestone screenshots predate the M14 candidate and are not candidate-specific captures.",
            "Null capture, browser, device, reviewer, fixture, or sanitization fields are not inferred without durable source evidence.",
            "This integrity inventory does not replace the physical accessibility acceptance matrix.",
        ],
        "items": items,
    }
    return json.dumps(payload, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the committed inventory differs from current screenshot evidence",
    )
    arguments = parser.parse_args()
    rendered = rendered_inventory()
    if arguments.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print("Screenshot inventory is stale; regenerate it with this script.")
            return 1
        print("Screenshot inventory is current.")
        return 0

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as target:
        target.write(rendered)
    print(
        f"Wrote {len(json.loads(rendered)['items'])} screenshot records to "
        f"{OUTPUT.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
