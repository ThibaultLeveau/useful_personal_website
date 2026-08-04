"""Deterministic, idempotent, and production-refusing demo seed contracts."""

# mypy: disable-error-code="arg-type,method-assign,no-untyped-call,no-untyped-def,var-annotated"
# ruff: noqa: ANN001, ANN202, ARG001, ARG002, D103, EM101, PT018, SLF001, TC002

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.commands import seed_demo
from app.modules.navigation.domain import FooterTree, NavigationTree

NOW = datetime(2026, 8, 4, 12, tzinfo=UTC)


def test_demo_values_trees_and_catalog_are_deterministic() -> None:
    profile = seed_demo._profile_values()
    settings = seed_demo._settings_values()
    empty_navigation = NavigationTree(id=uuid4(), items=(), version=7)
    empty_footer = FooterTree(id=uuid4(), copyright_text=None, columns=(), version=4)
    navigation = seed_demo._navigation(empty_navigation)
    footer = seed_demo._footer(empty_footer)
    categories, skills = seed_demo._skill_catalog(NOW)

    assert profile.full_name and "Fictional" in profile.full_name
    assert settings.website_name and "Fictional" in settings.website_name
    assert [item.href for item in navigation.items] == ["/", "/about", "/skills"]
    assert footer.columns[0].items[1].href == "/skills"
    assert len(categories) == 2 and len(skills) == 5
    assert {item.slug for item in skills if item.visible} == {
        "python",
        "api-design",
        "accessible-interfaces",
        "design-systems",
    }
    assert seed_demo._navigation_matches(navigation, seed_demo._navigation(navigation))
    assert seed_demo._footer_matches(footer, seed_demo._footer(footer))
    assert seed_demo._skill_catalog_matches(categories, skills, categories, skills)
    assert not seed_demo._skill_catalog_matches(
        categories, skills, categories, (replace(skills[0], name="Changed"), *skills[1:])
    )


class _Categories:
    def __init__(self, values=()) -> None:
        self.values = values
        self.added = []
        self.deleted = []

    async def list_all(self, *, for_update=False):
        return self.values

    async def add(self, value) -> None:
        self.added.append(value)

    async def delete(self, value) -> None:
        self.deleted.append(value)


class _Skills:
    def __init__(self, values=()) -> None:
        self.values = values
        self.added = []
        self.deleted = []

    async def list_by_category(self, _category_id, *, for_update=False):
        return self.values

    async def add(self, value) -> None:
        self.added.append(value)

    async def delete(self, value) -> None:
        self.deleted.append(value)


class _CatalogUow:
    def __init__(self, categories=(), skills=()) -> None:
        self.categories = _Categories(categories)
        self.skills = _Skills(skills)


async def test_demo_catalog_convergence_is_idempotent_and_replaces_drift() -> None:
    categories, skills = seed_demo._skill_catalog(NOW)
    current = _CatalogUow(categories, skills[:3])
    changed = await seed_demo._converge_skill_catalog(current, categories, skills)
    assert changed
    assert len(current.categories.deleted) == 2
    assert len(current.skills.deleted) == 6
    assert current.categories.added == list(categories)
    assert current.skills.added == list(skills)

    exact = _CatalogUow(categories)
    exact.skills.values = tuple(item for item in skills if item.category_id == categories[0].id)

    async def by_category(category_id, *, for_update=False):
        return tuple(item for item in skills if item.category_id == category_id)

    exact.skills.list_by_category = by_category
    assert not await seed_demo._converge_skill_catalog(exact, categories, skills)


class _Runtime:
    session_factory = object()

    def __init__(self) -> None:
        self.disposed = False

    async def dispose(self) -> None:
        self.disposed = True


async def test_demo_operator_refuses_production_requires_database_and_reports(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    assert await seed_demo._run() == seed_demo.EXIT_PRODUCTION_REFUSED
    assert "production" in capsys.readouterr().err

    monkeypatch.setenv("APP_ENVIRONMENT", "development")
    monkeypatch.delenv("APP_DATABASE_URL", raising=False)
    assert await seed_demo._run() == seed_demo.EXIT_INVALID_INPUT
    assert "APP_DATABASE_URL" in capsys.readouterr().err

    runtime = _Runtime()
    monkeypatch.setenv("APP_DATABASE_URL", "postgresql+asyncpg://runtime:synthetic@db/site")
    monkeypatch.setattr(seed_demo, "create_database_runtime", lambda _config: runtime)
    monkeypatch.setattr(
        seed_demo,
        "seed_demo",
        lambda _factory: _result(),
    )
    assert await seed_demo._run() == 0
    assert "changed=5" in capsys.readouterr().out
    assert runtime.disposed


async def _result():
    return seed_demo.DemoSeedResult(
        profile_id=uuid4(),
        settings_id=uuid4(),
        navigation_id=uuid4(),
        footer_id=uuid4(),
        changed_aggregates=5,
        navigation_items=3,
        footer_columns=1,
        footer_items=2,
        skill_categories=2,
        skills=5,
    )


def test_demo_main_converts_expected_operator_failures(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    async def invalid() -> int:
        raise RuntimeError("synthetic")

    monkeypatch.setattr(seed_demo, "_run", invalid)
    assert seed_demo.main([]) == seed_demo.EXIT_INVALID_INPUT
    assert "without applying partial content" in capsys.readouterr().err
