"""Provider-neutral controlled media storage results and errors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


class MediaStorageError(Exception):
    """Controlled storage failure without provider or path details."""


class MediaObjectExistsError(MediaStorageError):
    """An immutable managed key already exists."""


class MediaObjectMissingError(MediaStorageError):
    """A required managed key is absent."""


class MediaObjectTooLargeError(MediaStorageError):
    """A stream exceeded its independent configured hard cap."""


@dataclass(frozen=True, slots=True)
class StoredObject:
    """Safe managed object facts."""

    key: str
    byte_size: int
    checksum_sha256: str
    last_modified: datetime
