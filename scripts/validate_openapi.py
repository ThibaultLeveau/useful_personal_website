"""Validate the cross-cutting API conventions needed for client generation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs" / "api" / "openapi.json"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def main() -> int:
    document: dict[str, Any] = json.loads(SCHEMA.read_text(encoding="utf-8"))
    problems: list[str] = []
    if not str(document.get("openapi", "")).startswith("3.1."):
        problems.append("OpenAPI must use the accepted 3.1 contract")
    if document.get("servers") != [{"url": "/", "description": "Same-origin API"}]:
        problems.append("OpenAPI must declare exactly the same-origin server")

    operation_ids: set[str] = set()
    paths = document.get("paths")
    if not isinstance(paths, dict) or not paths:
        problems.append("OpenAPI must expose at least one path")
        paths = {}
    for path, path_item in paths.items():
        if not path.startswith("/api/v1/"):
            problems.append(f"Unversioned path: {path}")
        if not isinstance(path_item, dict):
            problems.append(f"Invalid path item: {path}")
            continue
        for method, operation in path_item.items():
            if method not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id:
                problems.append(f"{method.upper()} {path}: missing operationId")
            elif operation_id in operation_ids:
                problems.append(f"Duplicate operationId: {operation_id}")
            else:
                operation_ids.add(operation_id)
            responses = operation.get("responses", {})
            typed_successes = [
                response
                for status, response in responses.items()
                if str(status).startswith("2")
                and "application/json" in response.get("content", {})
            ]
            binary_successes = [
                response
                for status, response in responses.items()
                if str(status).startswith("2")
                and any(
                    media_type in {"image/jpeg", "image/png", "image/webp"}
                    and media.get("schema") == {"type": "string", "format": "binary"}
                    for media_type, media in response.get("content", {}).items()
                )
            ]
            if not typed_successes and not binary_successes:
                problems.append(f"{operation_id}: missing typed JSON success response")
            for status, response in responses.items():
                if str(status).startswith(("4", "5")):
                    schema = (
                        response.get("content", {})
                        .get("application/json", {})
                        .get("schema")
                    )
                    if schema != {"$ref": "#/components/schemas/ErrorEnvelope"}:
                        problems.append(
                            f"{operation_id}: {status} must use ErrorEnvelope"
                        )

    if problems:
        print("OpenAPI validation failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print(f"OpenAPI validation passed for {len(operation_ids)} operations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
