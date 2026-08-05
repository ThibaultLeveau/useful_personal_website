"""Regenerate the committed TypeScript client with the pinned OCI image."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (ROOT / "frontend" / "src" / "generated" / "api").resolve()
EXPECTED_OUTPUT = OUTPUT
GENERATOR_IMAGE = (
    "openapitools/openapi-generator-cli@"
    "sha256:868b97eb4e5080d2cdfd5b3eeaa4d52e4bbb7c56f14e234b08b0b0bc4f38a78f"
)
NULL_MODEL = """/* tslint:disable */
/* eslint-disable */
/** OpenAPI 3.1 null-only schema omitted by the pinned generator. */
export type Null = null;

export function NullFromJSON(json: any): Null {
  return NullFromJSONTyped(json, false);
}

export function NullFromJSONTyped(json: any, _ignoreDiscriminator: boolean): Null {
  return json === null ? null : null;
}

export function NullToJSON(_value?: Null | null): null {
  return null;
}

export function NullToJSONTyped(
  _value?: Null | null,
  _ignoreDiscriminator: boolean = false,
): null {
  return null;
}
"""


def patch_typescript_fetch_runtime() -> None:
    """Apply strict-TypeScript fixes missing from generator 7.17.0."""
    runtime = OUTPUT / "src" / "runtime.ts"
    content = runtime.read_text(encoding="utf-8")
    base_paths = (
        'export const BASE_PATH = "http://localhost".replace(/\\/+$/, "");',
        'export const BASE_PATH = "/".replace(/\\/+$/, "");',
    )
    for base_path in base_paths:
        if base_path in content:
            content = content.replace(base_path, 'export const BASE_PATH = "";', 1)
            break
    else:
        raise RuntimeError("Pinned runtime template changed; unexpected BASE_PATH")
    replacements = {
        "set config(configuration: Configuration) {": (
            "set config(configuration: ConfigurationParameters) {"
        ),
        '...preMiddlewares: Array<Middleware["pre"]>': (
            '...preMiddlewares: Array<NonNullable<Middleware["pre"]>>'
        ),
        '...postMiddlewares: Array<Middleware["post"]>': (
            '...postMiddlewares: Array<NonNullable<Middleware["post"]>>'
        ),
        """      credentials: this.configuration.credentials,
    };""": """      ...(this.configuration.credentials === undefined
        ? {}
        : { credentials: this.configuration.credentials }),
    };""",
        """          response: response ? response.clone() : undefined,
            })) || response;""": """          ...(response === undefined ? {} : { response: response.clone() }),
            })) || response;""",
        "    public cause: Error,": "    public override cause: Error,",
    }
    for original, replacement in replacements.items():
        if original not in content:
            raise RuntimeError(
                f"Pinned runtime template changed; missing pattern: {original!r}"
            )
        content = content.replace(original, replacement, 1)
    runtime.write_text(content, encoding="utf-8", newline="\n")


def remove_unused_index_suppressions() -> None:
    for index in OUTPUT.rglob("index.ts"):
        content = index.read_text(encoding="utf-8")
        marker = "/* eslint-disable */\n"
        if marker not in content:
            raise RuntimeError(f"Expected generated suppression in {index}")
        index.write_text(content.replace(marker, "", 1), encoding="utf-8", newline="\n")


def add_null_model() -> None:
    """Supply the null-only model referenced but omitted by generator 7.17.0."""
    models = OUTPUT / "src" / "models"
    (models / "Null.ts").write_text(NULL_MODEL, encoding="utf-8", newline="\n")
    index = models / "index.ts"
    content = index.read_text(encoding="utf-8")
    marker = 'export * from "./NavigationReplaceRequest";\n'
    if marker not in content:
        raise RuntimeError(
            "Pinned model index changed; Null export insertion point is missing"
        )
    index.write_text(
        content.replace(marker, f'{marker}export * from "./Null";\n', 1),
        encoding="utf-8",
        newline="\n",
    )


def _decoder_entries(body: str) -> list[str]:
    """Split one formatted generated object literal into top-level properties."""
    entries: list[str] = []
    current: list[str] = []
    for line in body.splitlines(keepends=True):
        if line.startswith("    ") and not line.startswith("      ") and current:
            entries.append("".join(current))
            current = []
        current.append(line)
    if current:
        entries.append("".join(current))
    return entries


def patch_exact_optional_model_decoders() -> None:
    """Omit absent optional fields instead of assigning explicit undefined values."""
    for model in sorted((OUTPUT / "src" / "models").glob("*.ts")):
        content = model.read_text(encoding="utf-8")
        interface_match = re.search(
            r"export interface (?P<name>[A-Za-z0-9_]+) \{", content
        )
        if interface_match is None:
            continue
        interface_name = interface_match.group("name")
        optional_names = set(
            re.findall(r"^  (?P<name>[A-Za-z0-9_]+)\?:", content, re.MULTILINE)
        )
        if not optional_names:
            continue
        function_marker = f"export function {interface_name}FromJSONTyped("
        function_start = content.find(function_marker)
        if function_start < 0:
            raise RuntimeError(f"Missing generated decoder in {model}")
        return_start = content.find("  return {\n", function_start)
        return_end = content.find("  };\n}", return_start)
        if return_start < 0 or return_end < 0:
            raise RuntimeError(f"Unexpected generated decoder object in {model}")
        body_start = return_start + len("  return {\n")
        body = content[body_start:return_end]
        patched_entries: list[str] = []
        for entry in _decoder_entries(body):
            property_match = re.match(
                r"    (?P<name>[A-Za-z0-9_]+):(?P<value>[\s\S]*),\n$", entry
            )
            if (
                property_match is None
                or property_match.group("name") not in optional_names
            ):
                patched_entries.append(entry)
                continue
            property_name = property_match.group("name")
            expression = property_match.group("value").strip()
            json_key_match = re.search(r'json\["(?P<key>[^"]+)"\]', expression)
            if json_key_match is None:
                raise RuntimeError(
                    f"Optional decoder field has no JSON source in {model}"
                )
            json_key = json_key_match.group("key")
            patched_entries.append(
                f'    ...(json["{json_key}"] == null\n'
                "      ? {}\n"
                "      : {\n"
                f"          {property_name}: ({expression}) as NonNullable<"
                f'{interface_name}["{property_name}"]>,\n'
                "        }),\n"
            )
        patched = content[:body_start] + "".join(patched_entries) + content[return_end:]
        model.write_text(patched, encoding="utf-8", newline="\n")


def patch_required_value_decoder() -> None:
    """Repair generator 7.17's required-property collision with its value parameter."""
    model = OUTPUT / "src" / "models" / "StatisticItem.ts"
    content = model.read_text(encoding="utf-8")
    original = """    ...(json["value"] == null
      ? {}
      : {
          value: (json["value"]) as NonNullable<StatisticItem["value"]>,
        }),
"""
    replacement = """    value: json["value"],
"""
    if content.count(original) != 1:
        raise RuntimeError(
            "Pinned StatisticItem decoder changed; required value repair is unsafe"
        )
    model.write_text(
        content.replace(original, replacement), encoding="utf-8", newline="\n"
    )


def patch_discriminated_union_encoders() -> None:
    """Remove generator-added camelCase discriminators from strict wire JSON."""
    pattern = re.compile(
        r"return Object\.assign\(\{\}, (?P<encoder>\w+ToJSON\(value\)), \{.*?"
        r'blockType: "[^"]+",?.*?\} as const\);',
        re.DOTALL,
    )
    for name in ("Block.ts", "Definition.ts", "Definition1.ts"):
        model = OUTPUT / "src" / "models" / name
        content = model.read_text(encoding="utf-8")
        patched, count = pattern.subn(r"return \g<encoder>;", content)
        if count != 19:
            raise RuntimeError(
                f"Pinned {name} discriminator encoder changed; expected 19 repairs, got {count}"
            )
        model.write_text(patched, encoding="utf-8", newline="\n")


def patch_media_upload_form() -> None:
    """Repair generator 7.17's OpenAPI 3.1 multipart file and form selection."""
    api = OUTPUT / "src" / "apis" / "MediaApi.ts"
    content = api.read_text(encoding="utf-8")
    if content.count("  file: string;\n") != 1:
        raise RuntimeError(
            "Pinned media upload file type changed; Blob repair is unsafe"
        )
    content = content.replace("  file: string;\n", "  file: Blob;\n", 1)
    original = """    const consumes: runtime.Consume[] = [{ contentType: "multipart/form-data" }];
    // @ts-ignore: canConsumeForm may be unused
    const canConsumeForm = runtime.canConsumeForm(consumes);

    let formParams: { append(param: string, value: any): any };
    let useForm = false;
    if (useForm) {
      formParams = new FormData();
    } else {
      formParams = new URLSearchParams();
    }
"""
    replacement = "    const formParams = new FormData();\n"
    if content.count(original) != 1:
        raise RuntimeError(
            "Pinned media multipart form selection changed; repair is unsafe"
        )
    api.write_text(
        content.replace(original, replacement, 1), encoding="utf-8", newline="\n"
    )


def format_generated_client() -> None:
    subprocess.run(
        [
            "node",
            str(ROOT / "node_modules" / "prettier" / "bin" / "prettier.cjs"),
            "--write",
            str(OUTPUT),
        ],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "export_openapi.py")],
        cwd=ROOT,
        check=True,
    )
    if OUTPUT != EXPECTED_OUTPUT or ROOT not in OUTPUT.parents:
        raise RuntimeError("Refusing to clean an unexpected generated-client path")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    generator_user = (
        ["--user", f"{os.getuid()}:{os.getgid()}"]
        if hasattr(os, "getuid") and hasattr(os, "getgid")
        else []
    )
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            *generator_user,
            "--volume",
            f"{ROOT}:/local",
            GENERATOR_IMAGE,
            "generate",
            "--config",
            "/local/openapi-generator-config.yaml",
        ],
        cwd=ROOT,
        check=True,
    )
    for child in OUTPUT.iterdir():
        if child.name == "src":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    format_generated_client()
    patch_typescript_fetch_runtime()
    add_null_model()
    patch_exact_optional_model_decoders()
    patch_required_value_decoder()
    patch_discriminated_union_encoders()
    patch_media_upload_form()
    remove_unused_index_suppressions()
    format_generated_client()
    print(f"Generated client at {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
