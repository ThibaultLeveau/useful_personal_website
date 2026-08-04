"""Versioned CommonMark validation, rendering, sanitization, and reading-time policy."""

from __future__ import annotations

import hashlib
import html
import math
import re
import unicodedata
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlsplit

import nh3
from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml
from mdit_py_plugins.tasklists import tasklists_plugin

if TYPE_CHECKING:
    from markdown_it.token import Token

POLICY_NAME = "upw-commonmark"
POLICY_VERSION = "1.0.0"
MAXIMUM_SOURCE_CHARACTERS = 100_000
MAXIMUM_SOURCE_LINES = 4_000
MAXIMUM_TOKENS = 12_000
MAXIMUM_NESTING_DEPTH = 64
MAXIMUM_TABLE_CELLS = 2_000
WORDS_PER_MINUTE = 225
MAXIMUM_READING_MINUTES = 240
MAXIMUM_TCP_PORT = 65_535
_LANGUAGES = frozenset(
    {
        "bash",
        "css",
        "diff",
        "html",
        "http",
        "javascript",
        "json",
        "jsx",
        "markdown",
        "plaintext",
        "python",
        "shell",
        "sql",
        "text",
        "toml",
        "tsx",
        "typescript",
        "xml",
        "yaml",
    }
)
_CONTROL_OR_BIDI = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u202a-\u202e\u2066-\u2069]")
_WORD = re.compile(r"[^\W_]+(?:['\u2019-][^\W_]+)*", re.UNICODE)
_HEADING_SEGMENT = re.compile(r"[^a-z0-9]+")
_LANGUAGE = re.compile(r"^[a-z0-9+-]{1,32}$")


class ContentPolicyError(ValueError):
    """Stable field-addressable controlled-content rejection."""

    def __init__(self, *, code: str, line: int | None = None) -> None:
        """Capture a stable issue code and optional one-based source line."""
        super().__init__("controlled content is invalid")
        self.code = code
        self.line = line


@dataclass(frozen=True, slots=True)
class SafeRenderedContent:
    """Sanitized HTML carrying its exact source-policy provenance."""

    html: str
    policy_name: str
    policy_version: str
    source_checksum: str


@dataclass(frozen=True, slots=True)
class ContentDocument:
    """Canonical source plus deterministic safe derivations."""

    source: str
    rendered: SafeRenderedContent
    visible_text: str
    reading_minutes: int


def _markdown(*, task_lists: bool) -> MarkdownIt:
    parser = MarkdownIt(
        "commonmark",
        {
            "html": True,
            "linkify": False,
            "typographer": False,
        },
    ).enable(["table", "strikethrough"])
    parser.validateLink = lambda _url: True  # type: ignore[assignment]  # policy validates all URLs.
    if task_lists:
        parser.use(tasklists_plugin, enabled=False, label=True)
    return parser


def _canonical_source(value: str) -> str:
    source = unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    if not source or not source.strip():
        raise ContentPolicyError(code="empty_source")
    if len(source) > MAXIMUM_SOURCE_CHARACTERS:
        raise ContentPolicyError(code="source_too_large")
    if source.count("\n") + 1 > MAXIMUM_SOURCE_LINES:
        raise ContentPolicyError(code="too_many_lines")
    if _CONTROL_OR_BIDI.search(source):
        raise ContentPolicyError(code="unsafe_control_character")
    return source


def _all_tokens(tokens: list[Token]) -> list[tuple[Token, int | None]]:
    flattened: list[tuple[Token, int | None]] = []
    for token in tokens:
        line = token.map[0] + 1 if token.map else None
        flattened.append((token, line))
        flattened.extend((child, line) for child in token.children or ())
    return flattened


def _decoded_url(value: str) -> str:
    decoded = html.unescape(value)
    for _ in range(3):
        next_value = unquote(decoded)
        if next_value == decoded:
            break
        decoded = next_value
    return unicodedata.normalize("NFKC", decoded)


def _validate_url(value: str, *, line: int | None) -> None:
    decoded = _decoded_url(value)
    if not decoded or _CONTROL_OR_BIDI.search(decoded) or "\\" in decoded:
        raise ContentPolicyError(code="unsafe_url", line=line)
    if decoded.startswith("/") and not decoded.startswith("//"):
        return
    parsed = urlsplit(decoded)
    try:
        port = parsed.port
    except ValueError as error:
        raise ContentPolicyError(code="unsafe_url", line=line) from error
    if (
        parsed.scheme.casefold() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or (port is not None and not 1 <= port <= MAXIMUM_TCP_PORT)
    ):
        raise ContentPolicyError(code="unsafe_url", line=line)


def _validate_tokens(tokens: list[Token]) -> None:
    flattened = _all_tokens(tokens)
    if len(flattened) > MAXIMUM_TOKENS:
        raise ContentPolicyError(code="too_many_tokens")
    if max((token.level for token, _line in flattened), default=0) > MAXIMUM_NESTING_DEPTH:
        raise ContentPolicyError(code="content_too_deep")
    if (
        sum(token.type in {"td_open", "th_open"} for token, _line in flattened)
        > MAXIMUM_TABLE_CELLS
    ):
        raise ContentPolicyError(code="table_too_large")
    for token, line in flattened:
        if token.type in {"html_block", "html_inline"}:
            raise ContentPolicyError(code="raw_html", line=line)
        if token.type == "image":
            raise ContentPolicyError(code="media_unavailable", line=line)
        if token.type == "link_open":
            href = token.attrGet("href")
            _validate_url(href if isinstance(href, str) else "", line=line)


def _heading_id(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return _HEADING_SEGMENT.sub("-", ascii_value.casefold()).strip("-") or "section"


def _install_render_rules(parser: MarkdownIt) -> None:
    def heading_open(
        _renderer: object,
        tokens: list[Token],
        index: int,
        _options: dict[str, Any],
        env: dict[str, Any],
    ) -> str:
        token = tokens[index]
        level = min(int(token.tag[1:]) + 1, 6)
        token.tag = f"h{level}"
        base = _heading_id(tokens[index + 1].content)
        counts = env.setdefault("heading_counts", {})
        count = int(counts.get(base, 0)) + 1
        counts[base] = count
        identifier = base if count == 1 else f"{base}-{count}"
        return f'<{token.tag} id="{identifier}">'

    def heading_close(
        _renderer: object,
        tokens: list[Token],
        index: int,
        _options: dict[str, Any],
        _env: dict[str, Any],
    ) -> str:
        token = tokens[index]
        token.tag = f"h{min(int(token.tag[1:]) + 1, 6)}"
        return f"</{token.tag}>\n"

    def fence(_renderer: object, tokens: list[Token], index: int, *_args: object) -> str:
        token = tokens[index]
        candidate = token.info.strip().split(maxsplit=1)[0].casefold() if token.info.strip() else ""
        language = candidate if _LANGUAGE.fullmatch(candidate) and candidate in _LANGUAGES else ""
        attribute = f' class="language-{language}"' if language else ""
        return f"<pre><code{attribute}>{escapeHtml(token.content)}</code></pre>\n"

    parser.add_render_rule("heading_open", heading_open)
    parser.add_render_rule("heading_close", heading_close)
    parser.add_render_rule("fence", fence)
    parser.add_render_rule(
        "table_open",
        lambda *_args: (
            '<div class="content-table-scroll" role="region" '
            'aria-label="Scrollable content table"><table>'
        ),
    )
    parser.add_render_rule("table_close", lambda *_args: "</table></div>\n")


_CLEANER = nh3.Cleaner(
    tags={
        "a",
        "blockquote",
        "br",
        "code",
        "div",
        "em",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "input",
        "label",
        "li",
        "ol",
        "p",
        "pre",
        "s",
        "strong",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "ul",
    },
    clean_content_tags={"iframe", "math", "object", "script", "style", "svg", "template"},
    attributes={
        "a": {"href", "title"},
        "div": {"aria-label"},
        "h2": {"id"},
        "h3": {"id"},
        "h4": {"id"},
        "h5": {"id"},
        "h6": {"id"},
        "input": {"checked", "disabled"},
    },
    allowed_classes={
        "code": {f"language-{language}" for language in _LANGUAGES},
        "div": {"content-table-scroll"},
        "input": {"task-list-item-checkbox"},
        "li": {"task-list-item"},
        "ul": {"contains-task-list"},
    },
    tag_attribute_values={
        "div": {"role": {"region"}},
        "input": {"type": {"checkbox"}},
    },
    link_rel="noopener noreferrer",
    strip_comments=True,
    url_relative="pass_through",
    url_schemes={"https"},
)


def _visible_text(tokens: list[Token]) -> str:
    values: list[str] = []
    for token in tokens:
        if token.type in {"fence", "code_block"}:
            values.append(token.content)
        elif token.type == "inline":
            values.extend(
                child.content
                for child in token.children or ()
                if child.type in {"text", "code_inline"}
            )
    return "\n".join(value for value in values if value)


def parse_content(value: str) -> ContentDocument:
    """Validate one source and derive deterministic sanitized output."""
    source = _canonical_source(value)
    validator = _markdown(task_lists=False)
    tokens = validator.parse(source)
    _validate_tokens(tokens)
    renderer = _markdown(task_lists=True)
    _install_render_rules(renderer)
    rendered = _CLEANER.clean(renderer.render(source, {"heading_counts": {}}))
    checksum = hashlib.sha256(source.encode()).hexdigest()
    visible_text = _visible_text(tokens)
    word_count = len(_WORD.findall(visible_text))
    minutes = min(MAXIMUM_READING_MINUTES, max(1, math.ceil(word_count / WORDS_PER_MINUTE)))
    return ContentDocument(
        source=source,
        rendered=SafeRenderedContent(
            html=rendered,
            policy_name=POLICY_NAME,
            policy_version=POLICY_VERSION,
            source_checksum=checksum,
        ),
        visible_text=visible_text,
        reading_minutes=minutes,
    )
