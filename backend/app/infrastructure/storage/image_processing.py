"""Bounded Pillow decoder and metadata-stripping responsive image encoder."""

from __future__ import annotations

import asyncio
import hashlib
import warnings
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from app.modules.media.domain import (
    MAXIMUM_IMAGE_DIMENSION,
    MAXIMUM_IMAGE_PIXELS,
    MAXIMUM_UPLOAD_BYTES,
    VARIANT_WIDTHS,
    MediaFormat,
    MediaValidationError,
    ProcessedImage,
    ProcessedVariant,
    VariantPurpose,
)

PROCESSING_TIMEOUT_SECONDS = 30
MAXIMUM_PARALLEL_PROCESSORS = 2
MINIMUM_WEBP_HEADER_BYTES = 12
WEBP_QUALITY = 85
JPEG_QUALITY = 88
_CONTENT_TYPES = {
    "image/jpeg": MediaFormat.JPEG,
    "image/png": MediaFormat.PNG,
    "image/webp": MediaFormat.WEBP,
}


@dataclass(frozen=True, slots=True)
class _DecodedImage:
    format: MediaFormat
    width: int
    height: int
    alpha: bool
    image: Image.Image


class PillowImageProcessor:
    """Validate one image and create the closed responsive rendition catalog."""

    def __init__(self) -> None:
        """Limit CPU/decode concurrency independently of request concurrency."""
        self._semaphore = asyncio.Semaphore(MAXIMUM_PARALLEL_PROCESSORS)

    async def process(self, content: bytes, *, declared_content_type: str | None) -> ProcessedImage:
        """Decode and re-encode within the frozen processing budget."""
        if not content or len(content) > MAXIMUM_UPLOAD_BYTES:
            raise MediaValidationError(path="file", code="invalid_size")
        async with self._semaphore:
            try:
                async with asyncio.timeout(PROCESSING_TIMEOUT_SECONDS):
                    return await asyncio.to_thread(
                        self._process_sync, content, declared_content_type
                    )
            except TimeoutError as error:
                raise MediaValidationError(path="file", code="processing_timeout") from error

    @classmethod
    def _process_sync(cls, content: bytes, declared_content_type: str | None) -> ProcessedImage:
        detected_by_magic = cls._magic_format(content)
        if (
            declared_content_type is not None
            and _CONTENT_TYPES.get(declared_content_type.casefold()) is not detected_by_magic
        ):
            raise MediaValidationError(path="file", code="content_type_mismatch")
        cls._validate_exact_container(content, detected_by_magic)
        decoded = cls._decode(content, expected=detected_by_magic)
        variants = cls._variants(decoded)
        return ProcessedImage(
            detected_format=decoded.format,
            width=decoded.width,
            height=decoded.height,
            byte_size=len(content),
            checksum_sha256=hashlib.sha256(content).hexdigest(),
            variants=variants,
        )

    @staticmethod
    def _magic_format(content: bytes) -> MediaFormat:
        if content.startswith(b"\xff\xd8\xff"):
            return MediaFormat.JPEG
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return MediaFormat.PNG
        if (
            len(content) >= MINIMUM_WEBP_HEADER_BYTES
            and content[:4] == b"RIFF"
            and content[8:12] == b"WEBP"
        ):
            return MediaFormat.WEBP
        raise MediaValidationError(path="file", code="unsupported_format")

    @staticmethod
    def _validate_exact_container(content: bytes, image_format: MediaFormat) -> None:
        if image_format is MediaFormat.JPEG and not content.endswith(b"\xff\xd9"):
            raise MediaValidationError(path="file", code="invalid_container")
        if image_format is MediaFormat.PNG and not content.endswith(
            b"\x00\x00\x00\x00IEND\xaeB\x60\x82"
        ):
            raise MediaValidationError(path="file", code="invalid_container")
        if image_format is MediaFormat.WEBP:
            declared_size = int.from_bytes(content[4:8], "little") + 8
            if declared_size != len(content):
                raise MediaValidationError(path="file", code="invalid_container")

    @staticmethod
    def _decode(content: bytes, *, expected: MediaFormat) -> _DecodedImage:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                Image.MAX_IMAGE_PIXELS = MAXIMUM_IMAGE_PIXELS
                with Image.open(BytesIO(content)) as source:
                    if source.format is None:
                        raise MediaValidationError(path="file", code="decode_failed")
                    detected = MediaFormat(source.format.casefold())
                    frames = getattr(source, "n_frames", 1)
                    if (
                        detected is not expected
                        or frames != 1
                        or getattr(source, "is_animated", False)
                    ):
                        raise MediaValidationError(path="file", code="invalid_image_sequence")
                    width, height = source.size
                    if (
                        width < 1
                        or height < 1
                        or width > MAXIMUM_IMAGE_DIMENSION
                        or height > MAXIMUM_IMAGE_DIMENSION
                        or width * height > MAXIMUM_IMAGE_PIXELS
                    ):
                        raise MediaValidationError(path="file", code="invalid_dimensions")
                    source.load()
                    normalized = ImageOps.exif_transpose(source)
                    alpha = normalized.mode in {"RGBA", "LA"} or (
                        normalized.mode == "P" and "transparency" in normalized.info
                    )
                    converted = normalized.convert("RGBA" if alpha else "RGB")
        except (UnidentifiedImageError, OSError, SyntaxError) as error:
            raise MediaValidationError(path="file", code="decode_failed") from error
        return _DecodedImage(detected, converted.width, converted.height, alpha, converted)

    @classmethod
    def _variants(cls, decoded: _DecodedImage) -> tuple[ProcessedVariant, ...]:
        widths = tuple(width for width in VARIANT_WIDTHS if width <= decoded.width)
        if not widths:
            widths = (decoded.width,)
        output: list[ProcessedVariant] = []
        for width in widths:
            height = max(1, round(decoded.height * width / decoded.width))
            resized = decoded.image.resize((width, height), Image.Resampling.LANCZOS)
            output.append(
                cls._encode(
                    resized,
                    purpose=VariantPurpose.RESPONSIVE_WEBP,
                    image_format=MediaFormat.WEBP,
                )
            )
            output.append(
                cls._encode(
                    resized,
                    purpose=VariantPurpose.RESPONSIVE_FALLBACK,
                    image_format=MediaFormat.PNG if decoded.alpha else MediaFormat.JPEG,
                )
            )
        return tuple(output)

    @staticmethod
    def _encode(
        image: Image.Image, *, purpose: VariantPurpose, image_format: MediaFormat
    ) -> ProcessedVariant:
        target = BytesIO()
        if image_format is MediaFormat.WEBP:
            image.save(target, format="WEBP", quality=WEBP_QUALITY, method=4, exact=True)
        elif image_format is MediaFormat.PNG:
            image.save(target, format="PNG", optimize=True)
        else:
            image.convert("RGB").save(
                target, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True
            )
        content = target.getvalue()
        if not content or len(content) > MAXIMUM_UPLOAD_BYTES:
            raise MediaValidationError(path="file", code="variant_size_exceeded")
        return ProcessedVariant(
            purpose=purpose,
            format=image_format,
            width=image.width,
            height=image.height,
            content=content,
            checksum_sha256=hashlib.sha256(content).hexdigest(),
        )
