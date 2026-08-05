"""Development-only private local media storage with managed-key confinement."""

from __future__ import annotations

import asyncio
import hashlib
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.modules.media.domain import validate_managed_key
from app.modules.media.storage import (
    MediaObjectExistsError,
    MediaObjectMissingError,
    MediaObjectTooLargeError,
    MediaStorageError,
    StoredObject,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

MAXIMUM_LIST_PAGE = 1_000


class LocalMediaStorage:
    """Private single-host adapter for explicit nonproduction use only."""

    def __init__(self, root: Path) -> None:
        """Resolve and initialize one dedicated private media root."""
        if not root.is_absolute():
            msg = "media root must be absolute"
            raise ValueError(msg)
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if root.is_symlink():
            msg = "media root must not be a link"
            raise ValueError(msg)
        self._root = root.resolve(strict=True)
        self._set_private_mode(self._root, directory=True)

    async def write_quarantine(
        self, key: str, chunks: AsyncIterator[bytes], *, maximum_bytes: int
    ) -> StoredObject:
        """Stream to a new private quarantine object under an independent hard cap."""
        path = self._prepare_new_path(key, required_namespace="quarantine")
        digest = hashlib.sha256()
        written = 0
        try:
            with path.open("xb", buffering=0) as target:
                self._set_private_mode(path, directory=False)
                async for chunk in chunks:
                    if not chunk:
                        continue
                    written += len(chunk)
                    if written > maximum_bytes:
                        self._raise_storage_error()
                    digest.update(chunk)
                    await asyncio.to_thread(target.write, chunk)
                await asyncio.to_thread(target.flush)
                await asyncio.to_thread(os.fsync, target.fileno())
        except FileExistsError as error:
            raise MediaObjectExistsError from error
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        if written == 0:
            path.unlink(missing_ok=True)
            raise MediaStorageError
        return StoredObject(key, written, digest.hexdigest(), datetime.now(UTC))

    async def put_immutable(
        self, key: str, content: bytes, *, checksum_sha256: str
    ) -> StoredObject:
        """Create a complete immutable variant only when its checksum agrees."""
        if hashlib.sha256(content).hexdigest() != checksum_sha256:
            raise MediaStorageError
        path = self._prepare_new_path(key, required_namespace="variants")
        try:
            with path.open("xb", buffering=0) as target:
                self._set_private_mode(path, directory=False)
                await asyncio.to_thread(target.write, content)
                await asyncio.to_thread(target.flush)
                await asyncio.to_thread(os.fsync, target.fileno())
        except FileExistsError as error:
            raise MediaObjectExistsError from error
        return StoredObject(key, len(content), checksum_sha256, datetime.now(UTC))

    async def promote(self, source_key: str, target_key: str) -> StoredObject:
        """Atomically rename quarantine into the private original namespace."""
        source = self._existing_path(source_key, required_namespace="quarantine")
        target = self._prepare_new_path(target_key, required_namespace="originals")
        if target.exists():
            raise MediaObjectExistsError
        try:
            await asyncio.to_thread(os.replace, source, target)
        except FileNotFoundError as error:
            raise MediaObjectMissingError from error
        self._set_private_mode(target, directory=False)
        return await asyncio.to_thread(self._object_facts, target_key, target)

    async def read(self, key: str, *, maximum_bytes: int) -> bytes:
        """Read one bounded regular managed object."""
        path = self._existing_path(key)
        if path.stat().st_size > maximum_bytes:
            raise MediaStorageError
        content = await asyncio.to_thread(path.read_bytes)
        if len(content) > maximum_bytes:
            raise MediaStorageError
        return content

    async def stat(self, key: str) -> StoredObject | None:
        """Return verified object facts or absence without reflecting a path."""
        try:
            path = self._existing_path(key)
        except MediaObjectMissingError:
            return None
        return await asyncio.to_thread(self._object_facts, key, path)

    async def delete(self, key: str) -> None:
        """Idempotently remove one exact managed object."""
        try:
            path = self._existing_path(key)
        except MediaObjectMissingError:
            return
        await asyncio.to_thread(path.unlink, missing_ok=True)

    async def list_managed(
        self, prefix: str, *, cursor: str | None, limit: int
    ) -> tuple[tuple[StoredObject, ...], str | None]:
        """List one closed namespace page for reconciliation only."""
        if prefix not in {"quarantine/", "originals/", "variants/"}:
            raise MediaStorageError
        if limit < 1 or limit > MAXIMUM_LIST_PAGE:
            raise MediaStorageError
        root = self._root / prefix.rstrip("/")
        if not root.exists():
            return (), None
        keys = sorted(
            path.relative_to(self._root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and not path.is_symlink()
        )
        start = (
            0
            if cursor is None
            else next((index + 1 for index, key in enumerate(keys) if key == cursor), len(keys))
        )
        selected = keys[start : start + limit]
        facts = tuple(
            await asyncio.gather(
                *(
                    asyncio.to_thread(self._object_facts, key, self._existing_path(key))
                    for key in selected
                )
            )
        )
        next_cursor = selected[-1] if start + limit < len(keys) and selected else None
        return facts, next_cursor

    def _prepare_new_path(self, key: str, *, required_namespace: str) -> Path:
        path = self._candidate_path(key, required_namespace=required_namespace)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._assert_no_links(path.parent)
        for parent in path.parents:
            if parent == self._root.parent:
                break
            self._set_private_mode(parent, directory=True)
        return path

    def _existing_path(self, key: str, *, required_namespace: str | None = None) -> Path:
        path = self._candidate_path(key, required_namespace=required_namespace)
        self._assert_no_links(path.parent)
        if not path.exists() or path.is_symlink() or not path.is_file():
            raise MediaObjectMissingError
        if not path.resolve(strict=True).is_relative_to(self._root):
            raise MediaStorageError
        return path

    def _candidate_path(self, key: str, *, required_namespace: str | None = None) -> Path:
        validate_managed_key(key)
        if required_namespace is not None and not key.startswith(f"{required_namespace}/"):
            raise MediaStorageError
        path = self._root.joinpath(*key.split("/"))
        if not path.parent.resolve(strict=False).is_relative_to(self._root):
            raise MediaStorageError
        return path

    def _assert_no_links(self, path: Path) -> None:
        current = path
        while current != self._root:
            if current.exists() and current.is_symlink():
                raise MediaStorageError
            if not current.is_relative_to(self._root):
                raise MediaStorageError
            current = current.parent

    @staticmethod
    def _object_facts(key: str, path: Path) -> StoredObject:
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                size += len(chunk)
                digest.update(chunk)
        modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        return StoredObject(key, size, digest.hexdigest(), modified)

    @staticmethod
    def _set_private_mode(path: Path, *, directory: bool) -> None:
        try:
            path.chmod(0o700 if directory else 0o600)
        except OSError as error:
            raise MediaStorageError from error

    @staticmethod
    def _raise_storage_error() -> None:
        raise MediaObjectTooLargeError
