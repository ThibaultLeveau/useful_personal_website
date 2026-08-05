"""Canonical CommonMark policy and malicious-corpus proofs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.common.content_policy import (
    MAXIMUM_SOURCE_CHARACTERS,
    POLICY_NAME,
    POLICY_VERSION,
    ContentPolicyError,
    parse_content,
)

CORPUS = Path(__file__).parents[1] / "fixtures" / "content_policy_corpus.json"


@pytest.mark.parametrize(
    ("source", "fragment"),
    [
        ("**strong** and *emphasis* and ~~removed~~", "<s>removed</s>"),
        ("<https://example.test/path>", 'href="https://example.test/path"'),
        ("[Internal](/projects)", 'href="/projects"'),
        ("- [x] shipped\n- [ ] queued", 'type="checkbox"'),
        ("```python\nprint('<safe>')\n```", "&lt;safe&gt;"),
        ("| A | B |\n| - | - |\n| 1 | 2 |", 'aria-label="Scrollable content table"'),
    ],
)
def test_supported_commonmark_is_preserved(source: str, fragment: str) -> None:
    """Every approved extension survives the canonical safe renderer."""
    document = parse_content(source)
    assert fragment in document.rendered.html
    assert document.rendered.policy_name == POLICY_NAME
    assert document.rendered.policy_version == POLICY_VERSION
    assert len(document.rendered.source_checksum) == 64
    assert document.reading_minutes == 1


def test_headings_are_demoted_and_receive_collision_safe_ids() -> None:
    """Article body headings cannot compete with the route h1 or collide."""
    document = parse_content("# Repeat\n\n## Repeat\n\n# Résumé")
    assert '<h2 id="repeat">Repeat</h2>' in document.rendered.html
    assert '<h3 id="repeat-2">Repeat</h3>' in document.rendered.html
    assert '<h2 id="resume">Résumé</h2>' in document.rendered.html
    assert "<h1" not in document.rendered.html


def test_source_export_normalization_checksum_and_reading_time_are_deterministic() -> None:
    """Reloading canonical source preserves every deterministic derivation."""
    source = "# Café\r\n\r\n" + "word " * 226
    first = parse_content(source)
    second = parse_content(first.source)
    assert "\r" not in first.source
    assert first == second
    assert first.reading_minutes == 2
    assert "Café" in first.visible_text


def test_unknown_fence_language_degrades_to_plain_escaped_code() -> None:
    """Unknown code labels never become attacker-selected CSS or executable HTML."""
    document = parse_content("```evil\n</code><script>boom()</script>\n```")
    assert "language-evil" not in document.rendered.html
    assert "&lt;script&gt;boom()&lt;/script&gt;" in document.rendered.html
    assert "<script>" not in document.rendered.html


def test_parser_limits_fail_closed() -> None:
    """Documents beyond the frozen source bound fail before parsing."""
    with pytest.raises(ContentPolicyError, match="controlled content") as captured:
        parse_content("x" * (MAXIMUM_SOURCE_CHARACTERS + 1))
    assert captured.value.code == "source_too_large"


def test_comparison_characters_are_text_not_false_positive_html() -> None:
    """AST validation preserves ordinary comparison prose."""
    document = parse_content("Latency stayed < 50 ms and throughput > 100 requests.")
    assert "Latency stayed &lt; 50 ms" in document.rendered.html


def test_malicious_corpus_is_rejected_with_stable_codes() -> None:
    """Every reviewed malicious fixture fails with its expected issue code."""
    cases = json.loads(CORPUS.read_text(encoding="utf-8"))
    assert len(cases) >= 12
    for case in cases:
        with pytest.raises(ContentPolicyError) as captured:
            parse_content(case["source"])
        assert captured.value.code == case["code"], case["name"]


def test_sanitizer_output_has_no_executable_or_remote_media_surface() -> None:
    """Escaped code stays visible while executable/browser-fetch surfaces stay absent."""
    document = parse_content(
        "# Safe\n\n[External](https://example.test)\n\n```html\n<img src=x onerror=alert(1)>\n```"
    )
    lowered = document.rendered.html.casefold()
    assert "<img" not in lowered
    assert "&lt;img src=x onerror=alert(1)&gt;" in lowered
    assert "<script" not in lowered
    assert "javascript:" not in lowered
    assert 'rel="noopener noreferrer"' in lowered
